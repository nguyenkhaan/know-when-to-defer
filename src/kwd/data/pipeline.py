"""Raw LMRC routes -> stored snapshots: the logic behind `kwd snapshot` (spec 05 §3-§7).

Not re-exported from `kwd.data`: this module needs `kwd.solver`, which itself imports `kwd.data`.
"""

import hashlib
import json
import random
from collections.abc import Collection
from itertools import pairwise
from pathlib import Path
from statistics import mean, median

import numpy as np

from kwd.data.config import DataConfig, SnapshotConfig, config_hash
from kwd.data.lmrc import BY_ROUTE, RouteSelection, extract_routes, load_route, select_with_reserve
from kwd.data.models import RouteSnapshot
from kwd.data.names import normalize_name
from kwd.data.snapshot import baseline_arrivals, build_snapshot
from kwd.solver import current_plan

SELECTED_FILE = "routes_selected.json"
SNAPSHOTS_FILE = "snapshots.jsonl"
RESERVE_FILE = "snapshots_reserve.jsonl"
META_FILE = "snapshots.meta.json"
TRAVEL_DIR = "travel"
SHIFT_END_TOLERANCE_S = 60
_STATS_FORMAT = """\
routes: {pilot} pilot, {reserve} reserve, {stations} stations
stops per route: mean {stops_mean:.1f}, p10 {stops_p10:.0f}, p90 {stops_p90:.0f}
remaining stops: min {remaining_min}, median {remaining_median:g}, max {remaining_max}
stops with a time window: {window_pct:.1f}% (median per route {window_pct_median:.1f}%)
rho: min {rho_min:.3f}, max {rho_max:.3f}"""


def draw_rho(route_id: str, seed: int, rho_min: float, rho_max: float) -> float:
    """Draw from an RNG of this route alone: replacing a route leaves every other snapshot as is."""
    return random.Random(f"{seed}:rho:{route_id}").uniform(rho_min, rho_max)


def _write_text(path: Path, text: str) -> None:
    """Write with LF endings on every platform, through a temporary file."""
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    tmp.replace(path)


def _sha256(path: Path) -> str:
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def travel_digest(interim_dir: Path, route_ids: Collection[str]) -> str:
    """Hash the (file name, content hash) pairs of these routes' matrices, sorted by name.

    Only the given routes count, so a matrix left over from another selection changes nothing.
    """
    names = sorted(f"{route_id}.npy" for route_id in route_ids)
    pairs = [[name, _sha256(interim_dir / TRAVEL_DIR / name)] for name in names]
    return hashlib.sha256(json.dumps(pairs, separators=(",", ":")).encode()).hexdigest()


def _selection_json(selection: RouteSelection) -> str:
    # `pilot_reserve` leaves room for the `main` and `human` lists of Phase 3.
    body = {"pilot": selection.pilot, "pilot_reserve": selection.reserve}
    return json.dumps(body, indent=2, sort_keys=True) + "\n"


def _extract_missing(raw_dir: Path, route_ids: list[str]) -> None:
    missing = [r for r in route_ids if not (raw_dir / BY_ROUTE / f"{r}.json").exists()]
    if missing:
        extract_routes(raw_dir, missing)


def _build(cfg: DataConfig, route_id: str) -> RouteSnapshot:
    s = cfg.snapshot
    return build_snapshot(
        load_route(cfg.raw_dir, route_id),
        draw_rho(route_id, s.seed, s.rho_min, s.rho_max),
        s.seed,
        s.shift_slack_min,
        travel_dir=cfg.interim_dir / TRAVEL_DIR,
    )


def check_snapshot(p: RouteSnapshot, cfg: SnapshotConfig) -> None:
    """Raise ValueError naming the route unless `p` meets the criteria of spec 05 §7."""
    if len(p.remaining) < cfg.min_remaining:
        raise ValueError(
            f"{p.route_id}: {len(p.remaining)} remaining stops, need {cfg.min_remaining}"
        )
    if not all(a < b for a, b in pairwise(baseline_arrivals(p).values())):
        raise ValueError(f"{p.route_id}: baseline arrivals do not strictly increase")
    if len({normalize_name(stop.name) for stop in p.stops.values()}) != len(p.stops):
        raise ValueError(f"{p.route_id}: display names are not unique")
    gap = current_plan(p).end_time + cfg.shift_slack_min * 60 - p.shift_end
    if abs(gap) > SHIFT_END_TOLERANCE_S:
        raise ValueError(f"{p.route_id}: shift end is {gap} s away from the walked plan")


def _jsonl(snapshots: list[RouteSnapshot]) -> str:
    return "".join(f"{p.model_dump_json()}\n" for p in snapshots)


def run_snapshot(cfg: DataConfig) -> dict:
    """Select routes, write snapshots of the pilot and its reserve, and return the metadata.

    Run from the repository root: `interim_dir` must be relative, because `travel_path` is stored
    in the snapshots and they must not hold machine paths. Nothing is written if it is not. No
    snapshot file is written unless every snapshot passes `check_snapshot`.
    """
    if cfg.interim_dir.anchor:
        raise ValueError(f"interim_dir must be relative: {cfg.interim_dir}")
    s = cfg.selection
    selection = select_with_reserve(
        cfg.raw_dir,
        s.pilot_n,
        s.seed,
        s.reserve_frac,
        min_stops=s.min_stops,
        max_stops=s.max_stops,
    )
    reserve_ids = sorted(route for routes in selection.reserve.values() for route in routes)
    route_ids = [*selection.pilot, *reserve_ids]

    cfg.interim_dir.mkdir(parents=True, exist_ok=True)
    _write_text(cfg.interim_dir / SELECTED_FILE, _selection_json(selection))
    _extract_missing(cfg.raw_dir, route_ids)

    pilot = [_build(cfg, route_id) for route_id in selection.pilot]
    reserve = [_build(cfg, route_id) for route_id in reserve_ids]
    for p in [*pilot, *reserve]:
        check_snapshot(p, cfg.snapshot)

    _write_text(cfg.interim_dir / SNAPSHOTS_FILE, _jsonl(pilot))
    _write_text(cfg.interim_dir / RESERVE_FILE, _jsonl(reserve))
    meta = {
        "config_hash": config_hash(cfg),
        "files": {
            name: _sha256(cfg.interim_dir / name)
            for name in (SELECTED_FILE, SNAPSHOTS_FILE, RESERVE_FILE)
        },
        "travel": travel_digest(cfg.interim_dir, route_ids),
    }
    _write_text(cfg.interim_dir / META_FILE, json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return meta


def load_snapshots(path: Path) -> list[RouteSnapshot]:
    with path.open(encoding="utf-8") as f:
        return [RouteSnapshot.model_validate_json(line) for line in f]


def snapshot_stats(
    pilot: list[RouteSnapshot], reserve: list[RouteSnapshot], cfg: DataConfig
) -> dict:
    """Stats of spec 05 §7 on the pilot; `stops` counts the depot, window shares do not."""
    stops = [len(p.stops) for p in pilot]
    remaining = [len(p.remaining) for p in pilot]
    deliveries = [[s for stop_id, s in p.stops.items() if stop_id != p.depot_id] for p in pilot]
    windows = [sum(stop.tw is not None for stop in route) for route in deliveries]
    s = cfg.snapshot
    rhos = [draw_rho(p.route_id, s.seed, s.rho_min, s.rho_max) for p in pilot]
    return {
        "pilot": len(pilot),
        "reserve": len(reserve),
        "stations": len({p.station_code for p in pilot}),
        "stops_mean": mean(stops),
        "stops_p10": float(np.percentile(stops, 10)),
        "stops_p90": float(np.percentile(stops, 90)),
        "remaining_min": min(remaining),
        "remaining_median": median(remaining),
        "remaining_max": max(remaining),
        "window_pct": 100 * sum(windows) / sum(len(route) for route in deliveries),
        "window_pct_median": median(
            100 * count / len(route) for count, route in zip(windows, deliveries, strict=True)
        ),
        "rho_min": min(rhos),
        "rho_max": max(rhos),
    }


def format_stats(stats: dict, meta: dict) -> str:
    """The lines `kwd snapshot` prints: nothing that differs between two identical runs."""
    files = meta["files"]
    return "\n".join(
        [
            _STATS_FORMAT.format(**stats),
            f"config: {meta['config_hash']}",
            *(f"{name}: {files[name]}" for name in (SNAPSHOTS_FILE, RESERVE_FILE, SELECTED_FILE)),
            f"travel: {meta['travel']}",
        ]
    )
