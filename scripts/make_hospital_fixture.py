"""Rebuild tests/fixtures/hospital.json and hospital_travel.npy, the golden case of spec 14 §4.

The numbers live here so that they stay readable: the .npy file is binary. The pharmacy and
school windows are what makes the gold edit reorder the route. Without them, "the hospital
accepts deliveries from 15:00" only makes the vehicle wait there, since waiting costs nothing in
the objective, and the plan digest would not change.

Usage (from the repository root):
    uv run python scripts/make_hospital_fixture.py [--out tests/fixtures]
"""

import argparse
from pathlib import Path

import numpy as np

from kwd.data.models import RouteSnapshot, Stop

SERVICE_S = 300
DEPOT = "DP"
# stop id, name, category, zone, original window in seconds since departure (13:00)
DELIVERIES = [
    ("PH", "Minh Chau Pharmacy", "pharmacy", "A", (0, 3600)),
    ("HO", "An Binh Hospital", "hospital", "A", None),
    ("SC", "Nguyen Du School", "school", "B", (0, 7200)),
    ("SH", "Thanh Cong Shop", "shop", "B", None),
]
# Symmetric, in minutes; satisfies the triangle inequality.
TRAVEL_ORDER = [DEPOT, "PH", "HO", "SC", "SH"]
TRAVEL_MIN = [
    [0, 20, 55, 75, 50],
    [20, 0, 45, 70, 60],
    [55, 45, 0, 30, 20],
    [75, 70, 30, 0, 35],
    [50, 60, 20, 35, 0],
]


def build_stops() -> dict[str, Stop]:
    rows = [(DEPOT, "Depot", "depot", None, None), *DELIVERIES]
    stops = {}
    for i, (stop_id, name, category, zone, window) in enumerate(rows):
        stops[stop_id] = Stop(
            stop_id=stop_id,
            name=name,
            category=category,
            zone_id=zone,
            lat=21.00 + i / 100,
            lng=105.80 + i / 100,
            service_s=0 if stop_id == DEPOT else SERVICE_S,
            tw=window,
        )
    return stops


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="tests/fixtures", type=Path)
    out = ap.parse_args().out

    stops = build_stops()
    node_ids = sorted(stops)
    snapshot = RouteSnapshot(
        snapshot_id="hospital@0",
        route_id="hospital",
        station_code="HOSPITAL",
        tz="Asia/Ho_Chi_Minh",
        departure_local="13:00:00",
        t_now=0,
        current_stop=DEPOT,
        done=[],
        remaining=[stop_id for stop_id, *_ in DELIVERIES],
        stops={stop_id: stops[stop_id] for stop_id in node_ids},
        depot_id=DEPOT,
        shift_end=16200,  # 17:30
        travel_path="hospital_travel.npy",
        node_ids=node_ids,
    )
    position = [TRAVEL_ORDER.index(stop_id) for stop_id in node_ids]
    seconds = np.array(TRAVEL_MIN, dtype=np.float64)[np.ix_(position, position)] * 60

    (out / "hospital.json").write_text(
        snapshot.model_dump_json(indent=1) + "\n", encoding="utf-8", newline="\n"
    )
    np.save(out / snapshot.travel_path, seconds)
    print(f"wrote hospital.json and {snapshot.travel_path} to {out}")


if __name__ == "__main__":
    main()
