"""Rebuild tests/fixtures/lmrc_mini/ from the raw LMRC files.

Takes the first High-score route (in package_data.json order) whose first 12 stops of the
actual sequence include a package with a real time window and a package with a `NaN` one,
then cuts all four raw files down to those 12 stops (depot + 11 drop-offs).

The fixture keeps the bare `NaN` tokens of the raw files so that tests exercise the NaN
handling. The small files are read with plain `json.load` (`NaN` -> float nan) and
json.dumps writes the token back. The big files must be streamed, which turns `NaN` into
None, so `restore_nan` undoes that: the raw files contain no `null` at all, so every None
was a NaN.

Usage (from the repository root):
    uv run python scripts/make_lmrc_fixture.py [raw_dir] [--out tests/fixtures/lmrc_mini]
"""

import argparse
import json
import math
from collections.abc import Iterator
from itertools import pairwise
from pathlib import Path
from typing import Any

import ijson

from kwd.data.jsonstream import NanToNullReader

N_STOPS = 12


def stream(path: Path) -> Iterator[tuple[str, Any]]:
    with path.open("rb") as f:
        yield from ijson.kvitems(NanToNullReader(f), "", use_float=True)


def restore_nan(value: Any) -> Any:
    if value is None:
        return math.nan
    if isinstance(value, dict):
        return {k: restore_nan(v) for k, v in value.items()}
    return value


def has_both_window_kinds(order: list[str], packages: dict) -> bool:
    starts = [p["time_window"]["start_time_utc"] for stop in order for p in packages[stop].values()]
    return any(s is None for s in starts) and any(s is not None for s in starts)


def pick_route(raw: Path, routes: dict, sequences: dict) -> tuple[str, list[str], dict]:
    """Return (route_id, first stops in actual order, packages) of the first suitable route."""
    for route_id, packages in stream(raw / "package_data.json"):
        actual = sequences[route_id]["actual"]
        order = sorted(actual, key=actual.get)[:N_STOPS]
        high = routes[route_id]["route_score"] == "High"
        if high and len(order) == N_STOPS and has_both_window_kinds(order, packages):
            return route_id, order, packages
    raise SystemExit("no suitable route found")


def find_matrix(raw: Path, route_id: str) -> dict:
    for key, matrix in stream(raw / "travel_times.json"):
        if key == route_id:
            return matrix
    raise SystemExit(f"{route_id} not found in travel_times.json")


def write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=1) + "\n", encoding="utf-8", newline="\n")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir", nargs="?", default="data/raw/lmrc", type=Path)
    ap.add_argument("--out", default="tests/fixtures/lmrc_mini", type=Path)
    args = ap.parse_args()
    raw, out = args.raw_dir, args.out

    with (raw / "route_data.json").open(encoding="utf-8") as f:
        routes = json.load(f)
    with (raw / "actual_sequences.json").open(encoding="utf-8") as f:
        sequences = json.load(f)

    route_id, order, packages = pick_route(raw, routes, sequences)
    matrix = find_matrix(raw, route_id)
    route = routes[route_id]
    kept = [stop for stop in route["stops"] if stop in order]  # raw order, not visit order
    if any(matrix[a][b] <= 0 for a, b in pairwise(order)):
        raise SystemExit(f"{route_id} has a zero leg in its first {N_STOPS} stops")

    out.mkdir(parents=True, exist_ok=True)
    trimmed_stops = {stop: route["stops"][stop] for stop in kept}
    write_json(out / "route_data.json", {route_id: {**route, "stops": trimmed_stops}})
    write_json(
        out / "actual_sequences.json",
        {route_id: {"actual": {stop: order.index(stop) for stop in kept}}},
    )
    write_json(
        out / "package_data.json",
        {route_id: {stop: restore_nan(packages[stop]) for stop in kept}},
    )
    write_json(
        out / "travel_times.json",
        {route_id: {a: {b: restore_nan(matrix[a][b]) for b in kept} for a in kept}},
    )
    print(f"{route_id}: {len(kept)} stops -> {out}")


if __name__ == "__main__":
    main()
