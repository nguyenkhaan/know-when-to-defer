import builtins
import copy
import io
import json
import math
from collections import Counter
from datetime import UTC, datetime, timedelta
from itertools import pairwise
from pathlib import Path

import pytest

from kwd.data.lmrc import extract_routes, load_route, select_routes
from kwd.data.models import RouteSnapshot, Stop

FIX = Path(__file__).parent.parent / "fixtures" / "lmrc_mini"
ROUTE_ID = "RouteID_00143bdd-0a6b-49ec-bb35-36593d303e77"
ORDER = ["VE", "TG", "GP", "HT", "AG", "QM", "SF", "BY", "CW", "VW", "JH", "LB"]
FILES = ("route_data", "actual_sequences", "package_data", "travel_times")
BIG_FILES = ("package_data.json", "travel_times.json")


def read_fixture() -> dict[str, dict]:
    """The four fixture files, keyed by name. `NaN` stays a float so that dumps rewrites it."""
    return {name: json.loads((FIX / f"{name}.json").read_text(encoding="utf-8")) for name in FILES}


def clone_routes(route_ids: list[str]) -> dict[str, dict]:
    """Raw data holding one copy of the fixture route under each id."""
    base = read_fixture()
    return {
        name: {rid: copy.deepcopy(content[ROUTE_ID]) for rid in route_ids}
        for name, content in base.items()
    }


def save(raw: dict[str, dict], raw_dir: Path) -> Path:
    for name, content in raw.items():
        (raw_dir / f"{name}.json").write_text(json.dumps(content), encoding="utf-8")
    return raw_dir


def select_all(raw_dir: Path, **kwargs) -> list[str]:
    return select_routes(raw_dir, 100, 0, min_stops=5, max_stops=20, **kwargs)


def walk(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from walk(item)
    else:
        yield value


def count_opens(monkeypatch) -> Counter:
    """Count opens per file name, whichever of open() or Path.open() the code uses."""
    opens: Counter = Counter()
    real_open = io.open

    def counting_open(file, *args, **kwargs):
        opens[Path(str(file)).name] += 1
        return real_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", counting_open)
    monkeypatch.setattr(io, "open", counting_open)
    return opens


def test_load_route_mini():
    r = load_route(FIX, ROUTE_ID)
    assert r.route_id == ROUTE_ID
    assert r.station_code == "DLA3"
    assert r.route_score == "High"
    assert r.actual_order == ORDER
    assert len(r.actual_order) == 12
    assert r.stops[r.actual_order[0]]["type"] == "Station"
    assert all(r.travel_s[a][b] > 0 for a, b in pairwise(ORDER))
    assert all(r.travel_s[a][a] == 0 for a in ORDER)


def test_load_route_nan_becomes_none():
    r = load_route(FIX, ROUTE_ID)
    depot = r.actual_order[0]
    assert r.stops[depot]["zone_id"] is None
    assert r.packages[depot] == {}
    leaves = [*walk(r.stops), *walk(r.packages)]
    assert not any(isinstance(v, float) and math.isnan(v) for v in leaves)
    windows = [p["time_window"] for pkgs in r.packages.values() for p in pkgs.values()]
    assert any(w["start_time_utc"] is None for w in windows)
    assert any(w["start_time_utc"] is not None for w in windows)


def test_departure_is_utc_aware():
    r = load_route(FIX, ROUTE_ID)
    assert r.departure_utc == datetime(2018, 7, 27, 16, 2, 10, tzinfo=UTC)
    assert r.departure_utc.utcoffset() == timedelta(0)


def break_extra_stop(actual):
    actual["ZZ"] = len(actual)


def break_missing_stop(actual):
    del actual[max(actual, key=actual.get)]


def break_positions_from_one(actual):
    for stop in actual:
        actual[stop] += 1


def break_duplicate_position(actual):
    actual["LB"] = actual["JH"]


def break_depot_not_first(actual):
    actual["VE"], actual["TG"] = actual["TG"], actual["VE"]


@pytest.mark.parametrize(
    "corrupt",
    [
        break_extra_stop,
        break_missing_stop,
        break_positions_from_one,
        break_duplicate_position,
        break_depot_not_first,
    ],
)
def test_load_route_rejects_inconsistent_sequence(tmp_path, corrupt):
    raw = read_fixture()
    corrupt(raw["actual_sequences"][ROUTE_ID]["actual"])
    with pytest.raises(ValueError, match=ROUTE_ID):
        load_route(save(raw, tmp_path), ROUTE_ID)


def test_load_route_unknown_id():
    with pytest.raises(KeyError, match="RouteID_nope"):
        load_route(FIX, "RouteID_nope")


def test_load_route_does_not_write():
    def state():
        return {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in FIX.rglob("*")}

    before = state()
    load_route(FIX, ROUTE_ID)
    assert state() == before


def test_select_routes_filters_and_is_deterministic(tmp_path):
    raw = clone_routes(["R_low", "R_gap", "R_ok"])
    raw["route_data"]["R_low"]["route_score"] = "Low"
    del raw["travel_times"]["R_gap"]["TG"]["GP"]
    save(raw, tmp_path)

    first = select_routes(tmp_path, 3, 0, min_stops=5, max_stops=20)
    assert first == ["R_ok"]
    assert select_routes(tmp_path, 3, 0, min_stops=5, max_stops=20) == first


def drop_cell(matrix):
    del matrix["TG"]["GP"]


def drop_row(matrix):
    del matrix["TG"]


def drop_column(matrix):
    for row in matrix.values():
        del row["GP"]


def nan_cell(matrix):
    matrix["TG"]["GP"] = math.nan


def extra_cell(matrix):
    matrix["TG"]["ZZ"] = 1.0


@pytest.mark.parametrize("corrupt", [drop_cell, drop_row, drop_column, nan_cell, extra_cell])
def test_select_routes_rejects_incomplete_matrix(tmp_path, corrupt):
    raw = clone_routes(["R_bad", "R_ok"])
    corrupt(raw["travel_times"]["R_bad"])
    assert select_all(save(raw, tmp_path)) == ["R_ok"]


def test_select_routes_drops_route_without_matrix(tmp_path):
    raw = clone_routes(["R_bad", "R_ok"])
    del raw["travel_times"]["R_bad"]
    assert select_all(save(raw, tmp_path)) == ["R_ok"]


def test_zero_offdiagonal_is_complete(tmp_path):
    raw = clone_routes(["R_zero"])
    raw["travel_times"]["R_zero"]["TG"]["GP"] = 0.0
    assert select_all(save(raw, tmp_path)) == ["R_zero"]


def test_select_routes_stop_bounds_count_the_depot(tmp_path):
    save(clone_routes(["R"]), tmp_path)
    assert select_routes(tmp_path, 1, 0, min_stops=12, max_stops=12) == ["R"]
    assert select_routes(tmp_path, 1, 0, min_stops=13, max_stops=20) == []
    assert select_routes(tmp_path, 1, 0, min_stops=5, max_stops=11) == []


def synthetic_raw(raw_dir: Path, sizes: dict[str, int]) -> dict[str, str]:
    """Write minimal route_data/travel_times; return route id -> station."""
    stations = {f"{code}_{i:02d}": code for code, size in sizes.items() for i in range(size)}
    stops = {"A": {}, "B": {}}
    matrix = {"A": {"A": 0.0, "B": 1.0}, "B": {"A": 1.0, "B": 0.0}}
    route_data = {
        rid: {"route_score": "High", "station_code": code, "stops": stops}
        for rid, code in stations.items()
    }
    save({"route_data": route_data, "travel_times": dict.fromkeys(stations, matrix)}, raw_dir)
    return stations


def test_select_routes_stratified(tmp_path):
    stations = synthetic_raw(tmp_path, {"DAA1": 60, "DBB1": 30, "DCC1": 10})
    picked = select_routes(tmp_path, 20, 0, min_stops=2, max_stops=2)
    assert Counter(stations[r] for r in picked) == {"DAA1": 12, "DBB1": 6, "DCC1": 2}
    assert picked == sorted(picked)


@pytest.mark.parametrize(
    ("n", "expected"),
    [
        (5, {"DAA1": 3, "DBB1": 1, "DCC1": 1}),  # quotas 2.5 / 1.25 / 1.25
        (3, {"DAA1": 1, "DBB1": 1, "DCC1": 1}),  # quotas 1.5 / 0.75 / 0.75
        (2, {"DAA1": 1, "DBB1": 1}),  # quotas 1 / 0.5 / 0.5: tie goes to the lower code
    ],
)
def test_select_routes_largest_remainder(tmp_path, n, expected):
    stations = synthetic_raw(tmp_path, {"DAA1": 6, "DCC1": 3, "DBB1": 3})
    picked = select_routes(tmp_path, n, 0, min_stops=2, max_stops=2)
    assert Counter(stations[r] for r in picked) == expected


def test_select_routes_does_not_depend_on_file_order(tmp_path):
    synthetic_raw(tmp_path, {"DAA1": 20, "DBB1": 10})
    forward = select_routes(tmp_path, 7, 3, min_stops=2, max_stops=2)

    for name in ("route_data.json", "travel_times.json"):
        path = tmp_path / name
        content = json.loads(path.read_text(encoding="utf-8"))
        path.write_text(json.dumps(dict(reversed(content.items()))), encoding="utf-8")
    assert select_routes(tmp_path, 7, 3, min_stops=2, max_stops=2) == forward


def test_select_routes_seed_changes_sample(tmp_path):
    synthetic_raw(tmp_path, {"DAA1": 50})
    samples = {
        tuple(select_routes(tmp_path, 5, seed, min_stops=2, max_stops=2)) for seed in range(5)
    }
    assert len(samples) > 1


def test_select_routes_exclude(tmp_path):
    stations = synthetic_raw(tmp_path, {"DAA1": 6, "DBB1": 6})
    pilot = select_routes(tmp_path, 4, 0, min_stops=2, max_stops=2)
    main = select_routes(tmp_path, 8, 0, min_stops=2, max_stops=2, exclude=pilot)
    assert len(main) == 8
    assert set(main).isdisjoint(pilot)
    assert set(main) | set(pilot) == set(stations)


def test_select_routes_n_exceeds_pool(tmp_path):
    stations = synthetic_raw(tmp_path, {"DAA1": 3, "DBB1": 2})
    picked = select_routes(tmp_path, 50, 0, min_stops=2, max_stops=2)
    assert picked == sorted(stations)


def test_select_routes_single_pass_and_no_write(tmp_path, monkeypatch):
    save(clone_routes(["R1", "R2", "R3"]), tmp_path)
    before = sorted(tmp_path.iterdir())
    opens = count_opens(monkeypatch)
    select_all(tmp_path)
    assert opens["travel_times.json"] == 1
    assert opens["package_data.json"] == 0
    assert sorted(tmp_path.iterdir()) == before


def test_extract_routes_roundtrip(tmp_path):
    save(clone_routes(["R1", "R2", "R3"]), tmp_path)
    from_raw = {rid: load_route(tmp_path, rid) for rid in ("R1", "R3")}

    extract_routes(tmp_path, ["R3", "R1"])

    written = sorted(p.name for p in (tmp_path / "by_route").iterdir())
    assert written == ["R1.json", "R3.json"]  # no temporary file left behind
    for name in BIG_FILES:
        (tmp_path / name).unlink()  # the reads below must come from by_route/
    assert {rid: load_route(tmp_path, rid) for rid in from_raw} == from_raw


def test_extract_routes_single_pass(tmp_path, monkeypatch):
    save(clone_routes(["R1", "R2", "R3"]), tmp_path)
    opens = count_opens(monkeypatch)
    extract_routes(tmp_path, ["R1", "R2", "R3"])
    assert opens["travel_times.json"] == 1
    assert opens["package_data.json"] == 1


def test_extract_routes_unknown_id(tmp_path):
    save(clone_routes(["R1"]), tmp_path)
    with pytest.raises(KeyError, match="R_nope"):
        extract_routes(tmp_path, ["R1", "R_nope"])


@pytest.mark.parametrize("name", ["package_data", "travel_times"])
def test_extract_routes_missing_from_big_file(tmp_path, name):
    raw = clone_routes(["R1", "R2"])
    del raw[name]["R2"]
    with pytest.raises(ValueError, match="R2"):
        extract_routes(save(raw, tmp_path), ["R1", "R2"])


def test_extract_routes_rejects_inconsistent_sequence_before_writing(tmp_path):
    raw = clone_routes(["R1", "R2"])
    break_positions_from_one(raw["actual_sequences"]["R2"]["actual"])
    with pytest.raises(ValueError, match="R2"):
        extract_routes(save(raw, tmp_path), ["R1", "R2"])
    assert not (tmp_path / "by_route").exists()


def test_snapshot_model_roundtrip():
    stop = {"zone_id": None, "lat": 34.1, "lng": -118.2, "service_s": 107}
    snapshot = RouteSnapshot(
        snapshot_id="R@600",
        route_id="R",
        station_code="DLA3",
        tz="America/Los_Angeles",
        departure_local="09:02",
        t_now=600,
        current_stop="A",
        done=["D", "A"],
        remaining=["B"],
        stops={
            "D": Stop(stop_id="D", name="Depot", category="warehouse", tw=None, **stop),
            "A": Stop(stop_id="A", name="Shop", category="shop", tw=None, **stop),
            "B": Stop(stop_id="B", name="School", category="school", tw=(0, 3600), **stop),
        },
        depot_id="D",
        shift_end=7200,
        travel_path="data/interim/travel/R.npy",
        node_ids=["D", "A", "B"],
    )
    restored = RouteSnapshot.model_validate_json(snapshot.model_dump_json())
    assert restored == snapshot
    assert isinstance(restored.stops["B"].tw, tuple)
    assert restored.stops["A"].tw is None
