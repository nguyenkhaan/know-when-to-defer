import json
from collections import Counter
from itertools import pairwise, permutations
from pathlib import Path

import numpy as np
import pytest

from kwd.data.lmrc import load_route
from kwd.data.models import RawRoute, RouteSnapshot
from kwd.data.names import assign_names, normalize_name
from kwd.data.render import render_snapshot
from kwd.data.snapshot import (
    baseline_arrivals,
    build_snapshot,
    clock_str,
    clock_to_s,
    load_fixture_snapshot,
    travel,
)

FIX = Path(__file__).parent.parent / "fixtures" / "lmrc_mini"
ROUTE_ID = "RouteID_00143bdd-0a6b-49ec-bb35-36593d303e77"
ORDER = ["VE", "TG", "GP", "HT", "AG", "QM", "SF", "BY", "CW", "VW", "JH", "LB"]


@pytest.fixture
def raw() -> RawRoute:
    return load_route(FIX, ROUTE_ID)


def package(start: str | None, end: str | None, service: float = 100.0) -> dict:
    return {
        "time_window": {"start_time_utc": start, "end_time_utc": end},
        "planned_service_time_seconds": service,
    }


def test_snapshot_freezes_prefix(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    assert len(p.done) == 3
    assert p.done == ORDER[1:4]
    assert p.remaining == ORDER[4:]
    assert p.current_stop == p.done[-1]
    assert set(p.done).isdisjoint(p.remaining)
    assert p.depot_id == "VE"
    assert p.depot_id not in p.done
    assert p.snapshot_id == f"{ROUTE_ID}@{p.t_now}"
    assert p.node_ids == sorted(ORDER)
    assert set(p.stops) == set(ORDER)


def test_rho_zero_starts_at_depot(raw, tmp_path):
    p = build_snapshot(raw, 0.0, 0, travel_dir=tmp_path)
    assert p.done == []
    assert p.current_stop == p.depot_id
    assert p.t_now == 0
    assert p.remaining == ORDER[1:]


@pytest.mark.parametrize("rho", [-0.1, 1.0, 1.5, 0.999])  # 0.999 leaves no remaining stop
def test_invalid_rho(raw, tmp_path, rho):
    with pytest.raises(ValueError, match=ROUTE_ID):
        build_snapshot(raw, rho, 0, travel_dir=tmp_path)


def test_baseline_arrivals_monotone(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    arrivals = baseline_arrivals(p)
    assert list(arrivals) == p.remaining
    assert all(a < b for a, b in pairwise(arrivals.values()))


def test_t_now_matches_walk(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    # Legs rounded to whole seconds, service rounded per stop:
    # VE-TG 1510, TG 185, TG-GP 25, GP 34, GP-HT 37, HT 145.
    assert p.t_now == 1510 + 185 + 25 + 34 + 37 + 145
    # HT-AG 62, with no second service at the current stop.
    assert baseline_arrivals(p)["AG"] == p.t_now + 62


def test_arrivals_agree_for_any_rho(raw, tmp_path):
    full = baseline_arrivals(build_snapshot(raw, 0.0, 0, travel_dir=tmp_path))
    late = baseline_arrivals(build_snapshot(raw, 0.5, 0, travel_dir=tmp_path))
    assert late == {stop: full[stop] for stop in late}


def test_shift_end_includes_return_leg_and_slack(raw, tmp_path):
    # Walk ends leaving LB at 3057; LB-VE is 1756.
    assert build_snapshot(raw, 0.25, 0, travel_dir=tmp_path).shift_end == 3057 + 1756 + 3600
    p = build_snapshot(raw, 0.25, 0, 30, travel_dir=tmp_path)
    assert p.shift_end == 3057 + 1756 + 1800


def test_stop_fields_from_raw_data(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    assert p.stops["TG"].service_s == 185  # 184.8
    assert p.stops["TG"].tw is None
    assert p.stops["TG"].zone_id == "A-2.2A"
    assert p.stops["TG"].lat == raw.stops["TG"]["lat"]
    # 16:00 opens before the 16:02:10 departure; the tighter end is 23:00.
    assert p.stops["QM"].tw == (-130, 25070)


def test_depot_stop(raw, tmp_path):
    depot = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path).stops["VE"]
    assert (depot.name, depot.category) == ("Depot", "depot")
    assert depot.service_s == 0
    assert depot.tw is None
    assert depot.zone_id is None


@pytest.mark.parametrize(
    ("packages", "expected"),
    [
        ([package(None, None)], None),
        (
            [package(None, None), package("2018-07-27 17:00:00", "2018-07-27 19:00:00")],
            (3470, 10670),
        ),
        (
            [
                package("2018-07-27 17:00:00", "2018-07-27 19:00:00"),
                package("2018-07-27 18:00:00", "2018-07-27 20:00:00"),
            ],
            (7070, 10670),
        ),
        (
            [
                package("2018-07-27 17:00:00", "2018-07-27 18:00:00"),
                package("2018-07-27 19:00:00", "2018-07-27 20:00:00"),
            ],
            None,
        ),
        (
            [
                package("2018-07-27 17:00:00", "2018-07-27 18:00:00"),
                package("2018-07-27 18:00:00", "2018-07-27 19:00:00"),
            ],
            None,
        ),
        ([package("2018-07-27 15:00:00", "2018-07-27 17:00:00")], (-3730, 3470)),
    ],
    ids=["none", "mixed", "overlap", "disjoint", "touching", "opens_before_departure"],
)
def test_time_window_intersection(raw, tmp_path, packages, expected):
    raw.packages["TG"] = {f"P{i}": p for i, p in enumerate(packages)}
    assert build_snapshot(raw, 0.25, 0, travel_dir=tmp_path).stops["TG"].tw == expected


def test_service_is_rounded_sum_of_packages(raw, tmp_path):
    raw.packages["TG"] = {
        "P0": package(None, None, 10.3),
        "P1": package(None, None, 20.4),
    }
    assert build_snapshot(raw, 0.25, 0, travel_dir=tmp_path).stops["TG"].service_s == 31


def test_wait_at_window_start(raw, tmp_path):
    # TG opens at 17:00:00, which is 3470 s after departure, and the van arrives at 1510.
    raw.packages["TG"] = {"P0": package("2018-07-27 17:00:00", "2018-07-27 19:00:00", 185.0)}
    arrivals = baseline_arrivals(build_snapshot(raw, 0.0, 0, travel_dir=tmp_path))
    assert arrivals["TG"] == 1510
    assert arrivals["GP"] == 3470 + 185 + 25


@pytest.mark.parametrize(
    ("station", "tz", "local"),
    [
        ("DLA3", "America/Los_Angeles", "09:02:10"),
        ("DSE4", "America/Los_Angeles", "09:02:10"),
        ("DAU1", "America/Chicago", "11:02:10"),
        ("DCH2", "America/Chicago", "11:02:10"),
        ("DBO3", "America/New_York", "12:02:10"),
    ],
)
def test_local_clock(raw, tmp_path, station, tz, local):
    raw.station_code = station
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    assert (p.tz, p.departure_local) == (tz, local)


def test_unknown_station_is_rejected(raw, tmp_path):
    raw.station_code = "DXX1"
    with pytest.raises(ValueError, match="DXX1"):
        build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)


@pytest.mark.parametrize("departure", ["13:00:00", "09:02:10", "00:00:59"])
def test_clock_roundtrip(departure):
    p = load_fixture_snapshot("hospital").model_copy(update={"departure_local": departure})
    for hour in range(24):
        for minute in range(60):
            text = f"{hour:02d}:{minute:02d}"
            assert clock_str(p, clock_to_s(p, text)) == text


def test_clock_keeps_seconds_of_departure():
    p = load_fixture_snapshot("hospital").model_copy(update={"departure_local": "09:02:10"})
    assert clock_to_s(p, "09:02") == -10
    assert clock_to_s(p, "09:03") == 50
    assert clock_str(p, 0) == "09:02"
    assert clock_str(p, 49) == "09:02"
    assert clock_str(p, 50) == "09:03"


@pytest.mark.parametrize("text", ["24:00", "25:10", "12:60", "-1:00", "9:05", "15h", ""])
def test_clock_to_s_rejects_times_outside_the_day(text):
    with pytest.raises(ValueError, match="HH:MM"):
        clock_to_s(load_fixture_snapshot("hospital"), text)


def test_clock_str_does_not_wrap_around():
    p = load_fixture_snapshot("hospital")  # departs 13:00:00
    assert clock_str(p, 11 * 3600 - 1) == "23:59"
    assert clock_str(p, -13 * 3600) == "00:00"
    with pytest.raises(ValueError, match="local day"):
        clock_str(p, 11 * 3600)
    with pytest.raises(ValueError, match="local day"):
        clock_str(p, -13 * 3600 - 1)


def test_travel_is_integer_seconds(raw, tmp_path):
    raw.travel_s["VE"]["TG"] = 2.5
    raw.travel_s["TG"]["VE"] = 3.5
    raw.travel_s["VE"]["GP"] = 0.5
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    matrix = travel(p)
    index = {stop: i for i, stop in enumerate(p.node_ids)}
    assert matrix.dtype == np.int64
    assert matrix.shape == (12, 12)
    assert matrix[index["VE"], index["TG"]] == 2  # np.rint rounds halves to even
    assert matrix[index["TG"], index["VE"]] == 4
    assert matrix[index["VE"], index["GP"]] == 0
    assert matrix[index["AG"], index["QM"]] == 75  # 74.9, and rows follow node_ids
    assert (np.diag(matrix) == 0).all()


def test_npy_keeps_float_seconds(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    stored = np.load(p.travel_path)
    index = {stop: i for i, stop in enumerate(p.node_ids)}
    assert stored.dtype == np.float64
    assert stored[index["AG"], index["QM"]] == 74.9


def test_travel_is_read_only(raw, tmp_path):
    matrix = travel(build_snapshot(raw, 0.25, 0, travel_dir=tmp_path))
    with pytest.raises(ValueError, match="read-only"):
        matrix[0, 0] = 1


def test_travel_sees_rebuilt_matrix(raw, tmp_path):
    first = travel(build_snapshot(raw, 0.25, 0, travel_dir=tmp_path))
    raw.travel_s["VE"]["TG"] += 100
    second = travel(build_snapshot(raw, 0.25, 0, travel_dir=tmp_path))
    assert second.sum() == first.sum() + 100


def test_travel_cache_follows_working_directory(raw, tmp_path, monkeypatch):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    monkeypatch.chdir(tmp_path / "a")
    first = build_snapshot(raw, 0.25, 0)
    total = travel(first).sum()
    monkeypatch.chdir(tmp_path / "b")
    raw.travel_s["VE"]["TG"] += 100
    second = build_snapshot(raw, 0.25, 0)
    assert second.travel_path == first.travel_path
    assert travel(second).sum() == total + 100


def test_travel_path_relative_posix(raw, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    p = build_snapshot(raw, 0.25, 0)
    assert p.travel_path == f"data/interim/travel/{ROUTE_ID}.npy"
    assert (tmp_path / "data" / "interim" / "travel" / f"{ROUTE_ID}.npy").exists()

    p = build_snapshot(raw, 0.25, 0, travel_dir=Path("nested") / "dir")
    assert p.travel_path == f"nested/dir/{ROUTE_ID}.npy"


def test_snapshot_deterministic(raw, tmp_path):
    first = build_snapshot(raw, 0.3, 7, travel_dir=tmp_path).model_dump_json()
    npy = tmp_path / f"{ROUTE_ID}.npy"
    first_bytes = npy.read_bytes()
    assert build_snapshot(raw, 0.3, 7, travel_dir=tmp_path).model_dump_json() == first
    assert npy.read_bytes() == first_bytes


def test_snapshot_roundtrip_json(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    restored = RouteSnapshot.model_validate_json(p.model_dump_json())
    assert restored == p
    assert isinstance(restored.stops["QM"].tw, tuple)


def test_display_names_unique_and_seeded(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    names = [stop.name for stop in p.stops.values()]
    assert len(set(names)) == len(names)
    same = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    assert [stop.name for stop in same.stops.values()] == names
    other = build_snapshot(raw, 0.25, 1, travel_dir=tmp_path)
    assert [stop.name for stop in other.stops.values()] != names


def test_names_independent_of_rho(raw, tmp_path):
    early = build_snapshot(raw, 0.1, 3, travel_dir=tmp_path)
    late = build_snapshot(raw, 0.6, 3, travel_dir=tmp_path)
    assert early.stops == late.stops


def test_names_do_not_depend_on_input_order():
    ids = [f"S{i:03d}" for i in range(50)]
    assert assign_names(ids, 5) == assign_names(list(reversed(ids)), 5)


@pytest.mark.parametrize("seed", range(50))
def test_names_unique_after_normalization(seed):
    ids = [f"S{i:03d}" for i in range(200)]
    named = assign_names(ids, seed)
    assert set(named) == set(ids)
    keys = {normalize_name(name) for name, _ in named.values()}
    assert len(keys) == 200
    assert normalize_name("Depot") not in keys
    assert all(name.isascii() for name, _ in named.values())


def test_normalize_name():
    assert normalize_name("  green   valley\tHOSPITAL ") == normalize_name("Green Valley Hospital")
    assert normalize_name("Valley Hospital") != normalize_name("Green Valley Hospital")


def test_names_share_prefixes_across_categories():
    named = assign_names([f"S{i:03d}" for i in range(200)], 0)
    prefixes = Counter(name.split()[0] for name, _ in named.values())
    assert max(prefixes.values()) > 1
    by_prefix: dict[str, set[str]] = {}
    for name, category in named.values():
        by_prefix.setdefault(name.split()[0], set()).add(category)
    assert any(len(categories) > 1 for categories in by_prefix.values())


def test_category_mix_allows_unique_reference():
    ids = [f"S{i:03d}" for i in range(150)]
    unique_reference = 0
    for seed in range(100):
        counts = Counter(category for _, category in assign_names(ids, seed).values())
        unique_reference += 1 in counts.values()
        assert counts.most_common(1)[0][0] == "residence"
    assert unique_reference >= 90


def test_hospital_fixture_fields():
    p = load_fixture_snapshot("hospital")
    assert p.route_id == "hospital"
    assert p.snapshot_id == "hospital@0"
    assert p.departure_local == "13:00:00"
    assert p.t_now == 0
    assert p.done == []
    assert p.current_stop == p.depot_id
    assert p.tz == "America/Chicago"
    assert p.shift_end == 16200
    assert p.node_ids == sorted(p.stops)
    assert Path(p.travel_path).is_absolute()
    delivery = [p.stops[stop] for stop in p.remaining]
    assert [stop.service_s for stop in delivery] == [300] * 4
    assert [stop.tw for stop in delivery] == [(0, 3600), None, (0, 7200), None]
    assert [stop.zone_id for stop in delivery] == ["A", "A", "B", "B"]
    assert p.stops[p.depot_id].service_s == 0


def test_fixture_file_keeps_relative_travel_path():
    path = FIX.parent / "hospital.json"
    assert json.loads(path.read_text(encoding="utf-8"))["travel_path"] == "hospital_travel.npy"


def test_load_fixture_does_not_depend_on_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert travel(load_fixture_snapshot("hospital")).shape == (5, 5)


def test_hospital_etas():
    p = load_fixture_snapshot("hospital")
    arrivals = baseline_arrivals(p)
    etas = {p.stops[stop].name: clock_str(p, t) for stop, t in arrivals.items()}
    assert etas == {
        "Cedar Pharmacy": "13:20",
        "Green Valley Hospital": "14:10",
        "Lincoln School": "14:45",
        "Harbor Shop": "15:25",
    }


def fixture_cost(p: RouteSnapshot, order: tuple[str, ...], hard: dict) -> float | None:
    """Solver objective of spec 07 §3 for one visiting order, or None if a hard window is missed."""
    matrix = travel(p)
    index = {stop: i for i, stop in enumerate(p.node_ids)}
    path = [p.depot_id, *order, p.depot_id]
    plan_arcs = set(pairwise([p.depot_id, *p.remaining, p.depot_id]))
    t, lateness = 0, 0
    for previous, stop in pairwise(path[:-1]):
        t += int(matrix[index[previous], index[stop]])
        if stop in hard:
            start, end = hard[stop]
            t = max(t, start)
            if t > end:
                return None
        if p.stops[stop].tw is not None:
            start, end = p.stops[stop].tw
            t = max(t, start)
            lateness += max(0, t - end)
        t += p.stops[stop].service_s
    travel_s = sum(int(matrix[index[a], index[b]]) for a, b in pairwise(path))
    new_arcs = sum(arc not in plan_arcs for arc in pairwise(path))
    return travel_s / 60 + 10 * lateness / 60 + 2 * new_arcs


def ranked_orders(p: RouteSnapshot, hard: dict) -> list[tuple[float, list[str]]]:
    costs = ((fixture_cost(p, order, hard), order) for order in permutations(p.remaining))
    ranked = sorted((cost, order) for cost, order in costs if cost is not None)
    return [(cost, [p.stops[stop].name.split()[-1] for stop in order]) for cost, order in ranked]


def test_hospital_fixture_design():
    p = load_fixture_snapshot("hospital")
    hospital = next(s for s in p.remaining if p.stops[s].category == "hospital")
    original = ["Pharmacy", "Hospital", "School", "Shop"]

    no_edit = ranked_orders(p, {})
    assert no_edit[0] == (180, original)
    assert no_edit[1][0] == 196

    gold = ranked_orders(p, {hospital: (clock_to_s(p, "15:00"), p.shift_end)})
    assert gold[0] == (196, ["Pharmacy", "School", "Hospital", "Shop"])
    assert gold[1][0] == 206

    wrong = ranked_orders(p, {hospital: (p.t_now, clock_to_s(p, "15:00"))})
    assert wrong[0] == (180, original)
    assert wrong[1][0] == 351


def test_hospital_gold_reaches_hospital_at_1510():
    p = load_fixture_snapshot("hospital")
    by_name = {stop.name.split()[-1]: stop.stop_id for stop in p.stops.values()}
    gold_order = [by_name[name] for name in ("Pharmacy", "School", "Hospital", "Shop")]
    arrivals = baseline_arrivals(p.model_copy(update={"remaining": gold_order}))
    assert clock_str(p, arrivals[by_name["Hospital"]]) == "15:10"


def test_render_hospital():
    assert render_snapshot(load_fixture_snapshot("hospital")).splitlines() == [
        "Current time: 13:00",
        "Vehicle at: Depot",
        "Shift ends: 17:30",
        "#|Stop|Category|Zone|ETA|Window",
        "1|Cedar Pharmacy|pharmacy|A|13:20|13:00-14:00",
        "2|Green Valley Hospital|hospital|A|14:10|-",
        "3|Lincoln School|school|B|14:45|13:00-15:00",
        "4|Harbor Shop|shop|B|15:25|-",
    ]


def test_render_none_zone_and_window():
    p = load_fixture_snapshot("hospital")
    shop = p.remaining[-1]
    p.stops[shop].zone_id = None
    assert render_snapshot(p).splitlines()[-1] == "4|Harbor Shop|shop|-|15:25|-"


def test_render_only_lists_remaining_stops(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    lines = render_snapshot(p).splitlines()
    assert lines[1] == f"Vehicle at: {p.stops[p.current_stop].name}"
    assert len(lines) == 4 + len(p.remaining)
    assert [line.split("|")[1] for line in lines[4:]] == [p.stops[s].name for s in p.remaining]


def test_render_keeps_raw_zone_and_negative_window(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    row = next(
        line.split("|")
        for line in render_snapshot(p).splitlines()
        if line.startswith("2|")  # QM
    )
    assert row[3] == "A-2.1A"
    assert row[5] == "09:00-16:00"  # 16:00-23:00 UTC, opening before the 09:02 departure


def test_render_has_no_coordinates_or_ids(raw, tmp_path):
    p = build_snapshot(raw, 0.25, 0, travel_dir=tmp_path)
    text = render_snapshot(p)
    cells = {cell for line in text.splitlines() for cell in line.split("|")}
    assert cells.isdisjoint(p.stops)
    for stop in p.stops.values():
        assert str(stop.lat) not in text
        assert str(stop.lng) not in text
