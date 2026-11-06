"""Read, filter and sample routes from the raw LMRC files (spec 05 §2, §3).

`travel_times.json` (1.8 GB) and `package_data.json` (375 MB) are only ever streamed, and never
inside a per-route loop: `select_routes` and `extract_routes` make one pass over each big file
they need, whatever the number of routes. `extract_routes` then leaves one small file per route
in `raw_dir/by_route/`, which `load_route` prefers over the raw files.
"""

import json
import random
from collections import Counter, defaultdict
from collections.abc import Collection, Iterator
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import ijson

from kwd.data.jsonstream import NanToNullReader
from kwd.data.models import RawRoute

ROUTE_DATA = "route_data.json"
ACTUAL_SEQUENCES = "actual_sequences.json"
PACKAGE_DATA = "package_data.json"
TRAVEL_TIMES = "travel_times.json"
BY_ROUTE = "by_route"


def _load_small(path: Path) -> dict:
    """Parse a small raw file. Bare `NaN` becomes None (plain json would give float nan)."""
    with path.open(encoding="utf-8") as f:
        return json.load(f, parse_constant=lambda _: None)


def _stream(path: Path) -> Iterator[tuple[str, Any]]:
    """Yield the top-level (key, value) pairs of a big raw file, `NaN` turned into None."""
    with path.open("rb") as f:
        yield from ijson.kvitems(NanToNullReader(f), "", use_float=True)


def _stream_wanted(path: Path, route_ids: Collection[str]) -> Iterator[tuple[str, Any]]:
    """Yield the entries of `route_ids` in one pass, stopping after the last one is found."""
    pending = set(route_ids)
    for route_id, value in _stream(path):
        if route_id in pending:
            pending.remove(route_id)
            yield route_id, value
            if not pending:
                return
    if pending:
        raise ValueError(f"missing from {path.name}: {sorted(pending)}")


def _is_complete(matrix: dict, stop_ids: set[str]) -> bool:
    """True if the matrix has exactly one value for every ordered pair of stops.

    A value of 0.0 is valid, so cells are compared to None rather than tested for truth.
    """
    return set(matrix) == stop_ids and all(
        set(row) == stop_ids and None not in row.values() for row in matrix.values()
    )


def _eligible_routes(
    raw_dir: Path, min_stops: int, max_stops: int, exclude: Collection[str]
) -> dict[str, str]:
    """Return route id -> station code for the routes passing the filter of spec 05 §3."""
    routes = _load_small(raw_dir / ROUTE_DATA)
    excluded = set(exclude)
    candidates = {
        route_id: set(route["stops"])
        for route_id, route in routes.items()
        if route["route_score"] == "High"
        and min_stops <= len(route["stops"]) <= max_stops
        and route_id not in excluded
    }
    eligible = {}
    for route_id, matrix in _stream(raw_dir / TRAVEL_TIMES):
        stop_ids = candidates.pop(route_id, None)
        if stop_ids is not None and _is_complete(matrix, stop_ids):
            eligible[route_id] = routes[route_id]["station_code"]
        if not candidates:
            break
    return eligible


def _allocate(pool_sizes: dict[str, int], n: int) -> dict[str, int]:
    """Split n across strata in proportion to their size (largest remainder method).

    Works on exact integers, so remainders tie only when truly equal; ties go to the lower
    station code. Requires n <= sum of the sizes.
    """
    total = sum(pool_sizes.values())
    quotas = {code: n * size // total for code, size in pool_sizes.items()}
    by_remainder = sorted(pool_sizes, key=lambda code: (-(n * pool_sizes[code] % total), code))
    for code in by_remainder[: n - sum(quotas.values())]:
        quotas[code] += 1
    return quotas


def _sample_stratified(eligible: dict[str, str], n: int, seed: int) -> list[str]:
    """Sample n routes stratified by station; independent of dict order and string hashing."""
    if n >= len(eligible):
        return sorted(eligible)
    by_station: dict[str, list[str]] = defaultdict(list)
    for route_id in sorted(eligible):
        by_station[eligible[route_id]].append(route_id)
    quotas = _allocate(Counter(eligible.values()), n)
    rng = random.Random(seed)
    picked = [
        route_id
        for code in sorted(by_station)
        for route_id in rng.sample(by_station[code], quotas[code])
    ]
    return sorted(picked)


def select_routes(
    raw_dir: Path,
    n: int,
    seed: int,
    *,
    min_stops: int = 80,
    max_stops: int = 200,
    exclude: Collection[str] = (),
) -> list[str]:
    """Return a sorted, stratified sample of up to n routes that pass the filter of spec 05 §3.

    Stop counts include the depot. Routes in `exclude` are removed before sampling, which keeps
    the main benchmark disjoint from the pilot. Writes nothing.
    """
    return _sample_stratified(_eligible_routes(raw_dir, min_stops, max_stops, exclude), n, seed)


def _checked_order(route_id: str, routes: dict, sequences: dict) -> list[str]:
    """Return the stops of a route by actual position, or raise if the raw data disagree."""
    if route_id not in routes:
        raise KeyError(f"unknown route: {route_id}")
    stops = routes[route_id]["stops"]
    actual = sequences[route_id]["actual"]
    if set(actual) != set(stops):
        raise ValueError(f"{route_id}: stops in actual sequence differ from route stops")
    if sorted(actual.values()) != list(range(len(actual))):
        raise ValueError(f"{route_id}: positions are not 0..{len(actual) - 1}")
    order = sorted(actual, key=actual.__getitem__)
    if stops[order[0]]["type"] != "Station":
        raise ValueError(f"{route_id}: position 0 is {order[0]}, not a Station")
    return order


def _raw_route(
    route_id: str, route: dict, order: list[str], packages: dict, travel_s: dict
) -> RawRoute:
    departure = f"{route['date_YYYY_MM_DD']} {route['departure_time_utc']}"
    return RawRoute(
        route_id=route_id,
        station_code=route["station_code"],
        departure_utc=datetime.strptime(departure, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC),
        stops=route["stops"],
        packages=packages,
        travel_s=travel_s,
        actual_order=order,
        route_score=route["route_score"],
    )


def load_route(raw_dir: Path, route_id: str) -> RawRoute:
    """Load one route from `by_route/` if extracted, else from the raw files. Writes nothing.

    The fallback scans the big files up to this route, so call `extract_routes` first when
    loading many routes.
    """
    extracted = raw_dir / BY_ROUTE / f"{route_id}.json"
    if extracted.exists():
        return RawRoute.model_validate_json(extracted.read_text(encoding="utf-8"))
    routes = _load_small(raw_dir / ROUTE_DATA)
    order = _checked_order(route_id, routes, _load_small(raw_dir / ACTUAL_SEQUENCES))
    packages = dict(_stream_wanted(raw_dir / PACKAGE_DATA, [route_id]))
    travel_s = dict(_stream_wanted(raw_dir / TRAVEL_TIMES, [route_id]))
    return _raw_route(route_id, routes[route_id], order, packages[route_id], travel_s[route_id])


def _write_atomic(path: Path, text: str) -> None:
    """Write through a temporary file so an interrupted run leaves no truncated route file."""
    tmp = path.with_name(f"{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def extract_routes(raw_dir: Path, route_ids: Collection[str]) -> None:
    """Write `raw_dir/by_route/<route_id>.json` for all routes, in one pass over each big file.

    Sequences are checked before the slow passes begin. Matrices are written as they stream
    by, so only one is held in memory at a time.
    """
    routes = _load_small(raw_dir / ROUTE_DATA)
    sequences = _load_small(raw_dir / ACTUAL_SEQUENCES)
    orders = {route_id: _checked_order(route_id, routes, sequences) for route_id in route_ids}
    if not orders:
        return
    packages = dict(_stream_wanted(raw_dir / PACKAGE_DATA, orders))
    out_dir = raw_dir / BY_ROUTE
    out_dir.mkdir(exist_ok=True)
    for route_id, travel_s in _stream_wanted(raw_dir / TRAVEL_TIMES, orders):
        route = _raw_route(
            route_id, routes[route_id], orders[route_id], packages[route_id], travel_s
        )
        _write_atomic(out_dir / f"{route_id}.json", route.model_dump_json())
