"""Inspect the downloaded LMRC files and print the facts spec 05 depends on.

Streams the large files (never loads travel_times.json fully: ~1.8 GB) and converts the
non-standard `NaN` tokens used in package_data.json into `null` while reading.

Usage (from the repository root):
    uv run python scripts/inspect_lmrc.py [raw_dir] [--routes N]
"""

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

import ijson


class NanToNullReader:
    """File wrapper that rewrites the bare token `NaN` to `null`, chunk by chunk.

    Holds back a trailing "N"/"Na" so a `NaN` split across chunks is still caught, and never
    returns more than `size` bytes (ijson's C backend drops anything beyond the requested
    size, and the rewrite makes the text longer). Safe here because LMRC never contains the
    text `NaN` inside a JSON string.
    """

    def __init__(self, raw, chunk_size: int = 1 << 20):
        self._raw = raw
        self._chunk = chunk_size
        self._tail = b""  # unconverted bytes that may start a split NaN
        self._out = b""  # converted bytes not yet handed to the caller
        self._eof = False

    def _fill(self, want: int) -> None:
        while not self._out and not self._eof:
            data = self._raw.read(want)
            buf = self._tail + data
            if not data:
                self._eof, self._tail = True, b""
            else:
                if buf.endswith(b"NaN"):
                    keep = 0
                elif buf.endswith(b"Na"):
                    keep = 2
                elif buf.endswith(b"N"):
                    keep = 1
                else:
                    keep = 0
                self._tail, buf = buf[len(buf) - keep :], buf[: len(buf) - keep]
            self._out += buf.replace(b"NaN", b"null")

    def read(self, size: int = -1) -> bytes:
        if size == 0:  # ijson probes with read(0) to detect bytes vs str: consume nothing
            return b""
        want = self._chunk if size is None or size < 0 else size
        self._fill(want)
        out, self._out = self._out[:want], self._out[want:]
        return out


def first_routes(path: Path, n: int, nan_safe: bool = False):
    """Yield (route_id, value) for the first n top-level entries of a large JSON object."""
    with path.open("rb") as f:
        src = NanToNullReader(f) if nan_safe else f
        for i, (key, value) in enumerate(ijson.kvitems(src, "", use_float=True)):
            if i >= n:
                return
            yield key, value


def describe(values, unit=""):
    if not values:
        return "n/a"
    q = statistics.quantiles(values, n=10)
    return (
        f"mean {statistics.mean(values):.1f}{unit}, p10 {q[0]:.0f}{unit}, "
        f"median {statistics.median(values):.0f}{unit}, p90 {q[-1]:.0f}{unit}"
    )


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("raw_dir", nargs="?", default="data/raw/lmrc")
    ap.add_argument("--routes", type=int, default=30, help="routes to sample from big files")
    args = ap.parse_args()
    raw = Path(args.raw_dir)

    print("== route_data.json (full pass)")
    with (raw / "route_data.json").open() as f:
        routes = json.load(f)
    print(f"routes: {len(routes)}")
    rid0, r0 = next(iter(routes.items()))
    print(f"route keys: {sorted(r0)}")
    print(f"stop keys: {sorted(next(iter(r0['stops'].values())))}")
    print(f"example departure: {r0['date_YYYY_MM_DD']} {r0['departure_time_utc']} UTC")
    print(f"route_score: {dict(Counter(r['route_score'] for r in routes.values()))}")
    n_stops = [len(r["stops"]) for r in routes.values()]
    print(f"stops per route: {describe(n_stops)}")
    types = Counter(s["type"] for r in routes.values() for s in r["stops"].values())
    print(f"stop types: {dict(types)}")
    stations = Counter(r["station_code"] for r in routes.values())
    print(f"stations ({len(stations)}): {dict(sorted(stations.items()))}")
    eligible = [
        rid
        for rid, r in routes.items()
        if r["route_score"] == "High" and 80 <= len(r["stops"]) <= 200
    ]
    print(f"eligible (High score, 80-200 stops): {len(eligible)}")

    print("\n== actual_sequences.json (full pass)")
    with (raw / "actual_sequences.json").open() as f:
        seqs = json.load(f)
    s0 = seqs[rid0]
    print(f"keys per route: {sorted(s0)}")
    order = sorted(s0["actual"], key=s0["actual"].get)
    first_type = r0["stops"][order[0]]["type"]
    print(f"position 0 is stop type: {first_type} (expect the station/depot)")
    print(f"positions are 0..n-1: {sorted(s0['actual'].values()) == list(range(len(order)))}")

    print(f"\n== package_data.json (first {args.routes} routes, NaN -> null)")
    tw_share, svc, tw_examples = [], [], []
    for rid, stops in first_routes(raw / "package_data.json", args.routes, nan_safe=True):
        with_tw = 0
        for pkgs in stops.values():
            svc.append(sum(p["planned_service_time_seconds"] for p in pkgs.values()))
            tws = [p["time_window"] for p in pkgs.values() if p["time_window"]["start_time_utc"]]
            if tws:
                with_tw += 1
                if len(tw_examples) < 3:
                    tw_examples.append(tws[0])
        tw_share.append(100 * with_tw / max(len(stops), 1))
    pkg_keys = sorted(next(iter(next(iter(stops.values())).values())))
    print(f"package keys: {pkg_keys}")
    print(f"service seconds per stop: {describe(svc, 's')}")
    print(f"% stops with a time window per route: {describe(tw_share, '%')}")
    print(f"time window examples: {tw_examples}")

    print(f"\n== travel_times.json (first {args.routes} routes, streamed)")
    complete, secs = 0, []
    for rid, mat in first_routes(raw / "travel_times.json", args.routes, nan_safe=True):
        stops = set(routes[rid]["stops"])
        ok = set(mat) == stops and all(set(row) == stops for row in mat.values())
        complete += ok
        secs.extend(v for row in mat.values() for v in row.values() if v)
    print(f"complete square matrices: {complete}/{args.routes}")
    print(f"travel time between stops: {describe(secs, 's')}")


if __name__ == "__main__":
    main()
