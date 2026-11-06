"""Turn a raw LMRC route into an in-service snapshot (spec 05 §4).

Times are whole seconds since route departure (spec 04 §5). `travel` is the only place where
travel times are rounded, and `clock_str`/`clock_to_s` the only conversions to the local clock.
"""

import math
import os
import re
from datetime import UTC, datetime
from functools import lru_cache
from itertools import pairwise
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np

from kwd.data.models import RawRoute, RouteSnapshot, Stop
from kwd.data.names import DEPOT_CATEGORY, DEPOT_NAME, assign_names

SECONDS_PER_DAY = 86_400
FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures"

# The data span 2018-07-19 to 2018-08-26, with no daylight saving change: the UTC offset of the
# departure holds for the whole route.
STATION_TIMEZONES = {
    "DAU": "America/Chicago",
    "DBO": "America/New_York",
    "DCH": "America/Chicago",
    "DLA": "America/Los_Angeles",
    "DSE": "America/Los_Angeles",
}


def _station_timezone(station_code: str) -> str:
    try:
        return STATION_TIMEZONES[station_code[:3]]
    except KeyError:
        raise ValueError(f"unknown station: {station_code}") from None


def _parse_utc(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)


def _stop_window(packages: dict, departure: datetime) -> tuple[int, int] | None:
    """Intersect the windows of the packages that have one, in seconds since departure.

    Windows opening before departure stay negative, so that they display the true time. An empty
    intersection counts as no window, since real data can be inconsistent (spec 07 §2).
    """
    windows = [p["time_window"] for p in packages.values()]
    windows = [w for w in windows if w["start_time_utc"] is not None]
    if not windows:
        return None
    start = max(_parse_utc(w["start_time_utc"]) for w in windows)
    end = min(_parse_utc(w["end_time_utc"]) for w in windows)
    if start >= end:
        return None
    return int((start - departure).total_seconds()), int((end - departure).total_seconds())


def _build_stops(raw: RawRoute, seed: int) -> dict[str, Stop]:
    depot_id = raw.actual_order[0]
    named = assign_names([stop for stop in raw.actual_order if stop != depot_id], seed)
    named[depot_id] = (DEPOT_NAME, DEPOT_CATEGORY)
    stops = {}
    for stop_id in sorted(raw.stops):
        packages = raw.packages[stop_id]
        name, category = named[stop_id]
        stops[stop_id] = Stop(
            stop_id=stop_id,
            name=name,
            category=category,
            zone_id=raw.stops[stop_id]["zone_id"],
            lat=raw.stops[stop_id]["lat"],
            lng=raw.stops[stop_id]["lng"],
            service_s=round(sum(p["planned_service_time_seconds"] for p in packages.values())),
            tw=_stop_window(packages, raw.departure_utc),
        )
    return stops


def _round_seconds(matrix: np.ndarray) -> np.ndarray:
    return np.rint(matrix).astype(np.int64)


def _walk(
    stops: dict[str, Stop], order: list[str], leave_first: int, matrix: np.ndarray, index: dict
) -> dict[str, tuple[int, int]]:
    """Drive along `order`, leaving order[0] at `leave_first` (spec 05 §4.1).

    Return stop -> (arrival, departure) for every stop after the first. Arrival is the time the
    vehicle reaches the stop, before any wait for the window to open.
    """
    visits = {}
    t = leave_first
    for previous, stop in pairwise(order):
        arrival = t + int(matrix[index[previous], index[stop]])
        window = stops[stop].tw
        service_start = arrival if window is None else max(arrival, window[0])
        t = service_start + stops[stop].service_s
        visits[stop] = (arrival, t)
    return visits


def _node_index(node_ids: list[str]) -> dict[str, int]:
    return {stop: i for i, stop in enumerate(node_ids)}


def build_snapshot(
    raw: RawRoute,
    rho: float,
    seed: int,
    shift_slack_min: int = 60,
    *,
    travel_dir: Path = Path("data/interim/travel"),
) -> RouteSnapshot:
    """Freeze the route at the departure from position floor(rho * n) and write its matrix.

    `done` holds positions 1..k and never the depot, so k = 0 leaves the vehicle at the depot.
    `travel_dir` should be relative to the repository root, the working directory of every
    pipeline step: `travel_path` is stored in the snapshot and must not hold machine paths.
    """
    if not 0 <= rho < 1:
        raise ValueError(f"{raw.route_id}: rho must be in [0, 1), got {rho}")
    order = raw.actual_order
    k = math.floor(rho * len(order))
    remaining = order[k + 1 :]
    if not remaining:
        raise ValueError(f"{raw.route_id}: rho = {rho} leaves no remaining stop")
    tz = _station_timezone(raw.station_code)

    stops = _build_stops(raw, seed)
    node_ids = sorted(order)
    index = _node_index(node_ids)
    seconds = np.array([[raw.travel_s[a][b] for b in node_ids] for a in node_ids], dtype=np.float64)
    matrix = _round_seconds(seconds)

    visits = _walk(stops, order, 0, matrix, index)
    t_now = visits[order[k]][1] if k else 0
    back_at_depot = visits[order[-1]][1] + int(matrix[index[order[-1]], index[order[0]]])

    travel_path = travel_dir / f"{raw.route_id}.npy"
    travel_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(travel_path, seconds)
    _load_travel.cache_clear()

    return RouteSnapshot(
        snapshot_id=f"{raw.route_id}@{t_now}",
        route_id=raw.route_id,
        station_code=raw.station_code,
        tz=tz,
        departure_local=raw.departure_utc.astimezone(ZoneInfo(tz)).strftime("%H:%M:%S"),
        t_now=t_now,
        current_stop=order[k],
        done=order[1 : k + 1],
        remaining=remaining,
        stops=stops,
        depot_id=order[0],
        shift_end=back_at_depot + shift_slack_min * 60,
        travel_path=travel_path.as_posix(),
        node_ids=node_ids,
    )


@lru_cache(maxsize=8)
def _load_travel(path: str) -> np.ndarray:
    matrix = _round_seconds(np.load(path))
    matrix.setflags(write=False)
    return matrix


def travel(p: RouteSnapshot) -> np.ndarray:
    """Travel times as read-only int64 seconds, rows and columns following `p.node_ids`.

    A relative `travel_path` is resolved against the working directory.
    """
    return _load_travel(os.path.abspath(p.travel_path))


def baseline_arrivals(p: RouteSnapshot) -> dict[str, int]:
    """Arrival time at each remaining stop on the current plan, leaving `current_stop` at t_now."""
    order = [p.current_stop, *p.remaining]
    visits = _walk(p.stops, order, p.t_now, travel(p), _node_index(p.node_ids))
    return {stop: arrival for stop, (arrival, _) in visits.items()}


def _departure_second_of_day(p: RouteSnapshot) -> int:
    hours, minutes, seconds = p.departure_local.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def clock_str(p: RouteSnapshot, s: int) -> str:
    """Local "HH:MM" of a time in seconds since departure, rounded down to the minute."""
    local = _departure_second_of_day(p) + s
    if not 0 <= local < SECONDS_PER_DAY:
        raise ValueError(f"{p.snapshot_id}: {s} s after departure is outside the local day")
    return f"{local // 3600:02d}:{local % 3600 // 60:02d}"


def clock_to_s(p: RouteSnapshot, hhmm: str) -> int:
    """Seconds since departure of a local "HH:MM"; negative if before departure."""
    match = re.fullmatch(r"([0-9]{2}):([0-9]{2})", hhmm)
    if match is None or int(match[1]) >= 24 or int(match[2]) >= 60:
        raise ValueError(f"not a local HH:MM time: {hhmm!r}")
    return int(match[1]) * 3600 + int(match[2]) * 60 - _departure_second_of_day(p)


def load_fixture_snapshot(name: str) -> RouteSnapshot:
    """Load tests/fixtures/<name>.json, with its travel matrix path made absolute."""
    path = FIXTURES_DIR / f"{name}.json"
    p = RouteSnapshot.model_validate_json(path.read_text(encoding="utf-8"))
    return p.model_copy(update={"travel_path": (FIXTURES_DIR / p.travel_path).as_posix()})
