import copy
import json
import random
import re
import shutil
from collections import Counter
from pathlib import Path

import pydantic
import pytest
import yaml
from typer.testing import CliRunner

from kwd.cli import app
from kwd.data import lmrc, pipeline
from kwd.data.config import DataConfig, config_hash, load_data_config
from kwd.data.lmrc import draw_reserve, load_route, select_routes, select_with_reserve
from kwd.data.models import RouteSnapshot, Stop
from kwd.data.pipeline import (
    check_snapshot,
    draw_rho,
    format_stats,
    load_snapshots,
    run_snapshot,
    snapshot_stats,
)
from kwd.data.snapshot import build_snapshot

REPO = Path(__file__).parents[2]
FIX = REPO / "tests" / "fixtures" / "lmrc_mini"
ROUTE_ID = "RouteID_00143bdd-0a6b-49ec-bb35-36593d303e77"
FILES = ("route_data", "actual_sequences", "package_data", "travel_times")
STATIONS = {
    **{f"RouteID_a{i}": "DLA3" for i in range(6)},
    **{f"RouteID_b{i}": "DSE4" for i in range(4)},
}
SHA256 = r"[0-9a-f]{64}"


def clone_raw(raw_dir: Path, stations: dict[str, str]) -> None:
    """Write the four raw files with one copy of the fixture route per id.

    `NaN` stays a float through json, so dumps writes it back as the bare token of the raw data.
    """
    raw_dir.mkdir()
    for name in FILES:
        route = json.loads((FIX / f"{name}.json").read_text(encoding="utf-8"))[ROUTE_ID]
        content = {route_id: copy.deepcopy(route) for route_id in stations}
        if name == "route_data":
            for route_id, station in stations.items():
                content[route_id]["station_code"] = station
        (raw_dir / f"{name}.json").write_text(json.dumps(content), encoding="utf-8")


def make_cfg(**snapshot) -> DataConfig:
    return DataConfig.model_validate(
        {
            "raw_dir": "raw",
            "interim_dir": "interim",
            "selection": {
                "seed": 0,
                "pilot_n": 3,
                "reserve_frac": 0.5,
                "min_stops": 5,
                "max_stops": 20,
            },
            "snapshot": {
                "seed": 0,
                "rho_min": 0.2,
                "rho_max": 0.5,
                "shift_slack_min": 60,
                "min_remaining": 3,
            }
            | snapshot,
        }
    )


@pytest.fixture
def workspace(tmp_path, monkeypatch) -> Path:
    """A working directory holding a small raw data set, so that `interim` stays relative."""
    monkeypatch.chdir(tmp_path)
    clone_raw(tmp_path / "raw", STATIONS)
    return tmp_path


def tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


# --- config --------------------------------------------------------------------------------------


def test_data_yaml_loads():
    cfg = load_data_config(REPO / "configs" / "data.yaml")

    assert cfg.raw_dir == Path("data/raw/lmrc")
    assert cfg.interim_dir == Path("data/interim")
    assert cfg.selection.model_dump() == {
        "seed": 0,
        "pilot_n": 30,
        "reserve_frac": 0.3,
        "min_stops": 80,
        "max_stops": 200,
    }
    assert cfg.snapshot.model_dump() == {
        "seed": 0,
        "rho_min": 0.2,
        "rho_max": 0.5,
        "shift_slack_min": 60,
        "min_remaining": 30,
    }


def data_yaml() -> dict:
    return yaml.safe_load((REPO / "configs" / "data.yaml").read_text(encoding="utf-8"))


def write_yaml(path: Path, content: dict, comment: str = "") -> Path:
    path.write_text(comment + yaml.safe_dump(content), encoding="utf-8")
    return path


@pytest.mark.parametrize("section", [None, "selection", "snapshot"])
def test_config_rejects_unknown_key(tmp_path, section):
    content = data_yaml()
    (content[section] if section else content)["surprise"] = 1

    with pytest.raises(pydantic.ValidationError, match="surprise"):
        load_data_config(write_yaml(tmp_path / "data.yaml", content))


@pytest.mark.parametrize("section, key", [(None, "raw_dir"), ("snapshot", "rho_min")])
def test_config_has_no_hidden_defaults(tmp_path, section, key):
    content = data_yaml()
    del (content[section] if section else content)[key]

    with pytest.raises(pydantic.ValidationError, match=key):
        load_data_config(write_yaml(tmp_path / "data.yaml", content))


def test_config_rejects_inverted_rho_range(tmp_path):
    content = data_yaml()
    content["snapshot"] |= {"rho_min": 0.5, "rho_max": 0.2}

    with pytest.raises(pydantic.ValidationError, match="rho_min"):
        load_data_config(write_yaml(tmp_path / "data.yaml", content))


def test_config_hash_ignores_yaml_comments(tmp_path):
    plain = load_data_config(write_yaml(tmp_path / "a.yaml", data_yaml()))
    commented = load_data_config(write_yaml(tmp_path / "b.yaml", data_yaml(), "# a comment\n"))
    changed_content = data_yaml()
    changed_content["snapshot"]["seed"] = 1
    changed = load_data_config(write_yaml(tmp_path / "c.yaml", changed_content))

    assert re.fullmatch(SHA256, config_hash(plain))
    assert config_hash(plain) == config_hash(commented)
    assert config_hash(plain) != config_hash(changed)


def test_config_hash_uses_posix_paths():
    resolved = load_data_config(REPO / "configs" / "data.yaml").model_dump(mode="json")

    assert resolved["raw_dir"] == "data/raw/lmrc"


# --- selection -----------------------------------------------------------------------------------


def synthetic_raw(raw_dir: Path, sizes: dict[str, int]) -> dict[str, str]:
    """Write minimal route_data/travel_times; return route id -> station."""
    stations = {f"{code}_{i:02d}": code for code, size in sizes.items() for i in range(size)}
    stops = {"A": {}, "B": {}}
    matrix = {"A": {"A": 0.0, "B": 1.0}, "B": {"A": 1.0, "B": 0.0}}
    route_data = {
        route_id: {"route_score": "High", "station_code": code, "stops": stops}
        for route_id, code in stations.items()
    }
    (raw_dir / "route_data.json").write_text(json.dumps(route_data), encoding="utf-8")
    travel_times = json.dumps(dict.fromkeys(stations, matrix))
    (raw_dir / "travel_times.json").write_text(travel_times, encoding="utf-8")
    return stations


def test_selection_pilot_equals_select_routes(tmp_path, monkeypatch):
    synthetic_raw(tmp_path, {"DAA1": 60, "DBB1": 30, "DCC1": 10})
    bounds = {"min_stops": 2, "max_stops": 2}
    passes = []
    real_eligible = lmrc._eligible_routes

    def counting_eligible(*args):
        passes.append(args)
        return real_eligible(*args)

    expected = select_routes(tmp_path, 20, 7, **bounds)
    monkeypatch.setattr(lmrc, "_eligible_routes", counting_eligible)
    selection = select_with_reserve(tmp_path, 20, 7, 0.3, **bounds)

    assert selection.pilot == expected
    assert len(passes) == 1


def test_selection_honours_exclude(tmp_path):
    stations = synthetic_raw(tmp_path, {"DAA1": 10})
    excluded = sorted(stations)[:8]

    selection = select_with_reserve(tmp_path, 1, 0, 1.0, min_stops=2, max_stops=2, exclude=excluded)

    assert not set(excluded) & {*selection.pilot, *selection.reserve["DAA1"]}


def eligible_of(sizes: dict[str, int]) -> dict[str, str]:
    return {f"{code}_{i:02d}": code for code, size in sizes.items() for i in range(size)}


def test_reserve_per_station():
    eligible = eligible_of({"DAA1": 40, "DBB1": 20, "DCC1": 10, "DDD1": 5})
    quotas = {"DAA1": 5, "DBB1": 4, "DCC1": 3, "DDD1": 0}
    pilot = [f"{code}_{i:02d}" for code, quota in quotas.items() for i in range(quota)]

    reserve = draw_reserve(eligible, pilot, 0, 0.3)

    assert {code: len(routes) for code, routes in reserve.items()} == {
        "DAA1": 2,
        "DBB1": 2,
        "DCC1": 1,
    }
    drawn = [route_id for routes in reserve.values() for route_id in routes]
    assert not set(drawn) & set(pilot)
    assert len(set(drawn)) == len(drawn)
    assert all(
        eligible[route_id] == code for code, routes in reserve.items() for route_id in routes
    )
    assert reserve == draw_reserve(eligible, pilot, 0, 0.3)


@pytest.mark.parametrize(
    "quota, expected", [(1, 1), (2, 1), (3, 1), (4, 2), (5, 2), (10, 3), (20, 6)]
)
def test_reserve_count_is_exact_ceiling(quota, expected):
    eligible = eligible_of({"DAA1": 40})
    pilot = [f"DAA1_{i:02d}" for i in range(quota)]

    assert len(draw_reserve(eligible, pilot, 0, 0.3)["DAA1"]) == expected


def test_reserve_size_for_the_pilot_quotas():
    """The quotas of the 30 pilot routes over 16 stations give 18 reserve routes."""
    quotas = [1] * 9 + [2] * 3 + [3] * 2 + [4, 5]
    codes = [f"D{i:03d}" for i in range(len(quotas))]
    eligible = eligible_of(dict.fromkeys(codes, 20))
    pilot = [
        f"{code}_{i:02d}" for code, quota in zip(codes, quotas, strict=True) for i in range(quota)
    ]

    reserve = draw_reserve(eligible, pilot, 0, 0.3)

    assert len(pilot) == 30
    assert sum(len(routes) for routes in reserve.values()) == 18


def test_reserve_keeps_draw_order():
    eligible = eligible_of({"DAA1": 30})
    pilot = [f"DAA1_{i:02d}" for i in range(10)]
    pool = sorted(set(eligible) - set(pilot))

    drawn = draw_reserve(eligible, pilot, 0, 0.5)["DAA1"]

    assert drawn == random.Random("0:reserve:DAA1").sample(pool, 5)
    assert drawn != sorted(drawn)


def test_reserve_does_not_depend_on_eligible_order():
    eligible = eligible_of({"DAA1": 30})
    shuffled = dict(reversed(list(eligible.items())))
    pilot = ["DAA1_03", "DAA1_01"]

    assert draw_reserve(eligible, pilot, 0, 1.0) == draw_reserve(shuffled, pilot, 0, 1.0)


def test_reserve_short_station_returns_fewer():
    eligible = eligible_of({"DAA1": 3})

    assert len(draw_reserve(eligible, ["DAA1_00", "DAA1_01"], 0, 1.0)["DAA1"]) == 1
    assert draw_reserve(eligible, sorted(eligible), 0, 1.0)["DAA1"] == []


def test_draw_rho_in_range_and_independent_of_route_set():
    routes = [f"RouteID_{i}" for i in range(200)]
    rhos = {route_id: draw_rho(route_id, 0, 0.2, 0.5) for route_id in routes}
    random.seed(1)
    state = random.getstate()

    assert all(0.2 <= rho <= 0.5 for rho in rhos.values())
    assert len(set(rhos.values())) == len(routes)
    assert {route_id: draw_rho(route_id, 0, 0.2, 0.5) for route_id in reversed(routes)} == rhos
    assert random.getstate() == state
    assert rhos["RouteID_7"] == random.Random("0:rho:RouteID_7").uniform(0.2, 0.5)
    assert draw_rho("RouteID_7", 1, 0.2, 0.5) != rhos["RouteID_7"]


# --- run_snapshot --------------------------------------------------------------------------------


def test_outputs_byte_identical(workspace):
    cfg = make_cfg()

    run_snapshot(cfg)
    first = tree(workspace / "interim")
    shutil.rmtree(workspace / "interim")
    run_snapshot(cfg)
    second = tree(workspace / "interim")

    assert first == second
    assert {
        "routes_selected.json",
        "snapshots.jsonl",
        "snapshots_reserve.jsonl",
        "snapshots.meta.json",
    } < set(first)
    assert sum(name.startswith("travel/") for name in first) == 5
    assert not [name for name in first if name.endswith(".tmp")]
    for name, content in first.items():
        if not name.endswith(".npy"):
            assert b"\r\n" not in content, name


def test_routes_selected_file_shape(workspace):
    run_snapshot(make_cfg())

    selected = json.loads((workspace / "interim/routes_selected.json").read_text(encoding="utf-8"))

    assert set(selected) == {"pilot", "pilot_reserve"}
    assert selected["pilot"] == sorted(selected["pilot"])
    assert Counter(STATIONS[route_id] for route_id in selected["pilot"]) == {"DLA3": 2, "DSE4": 1}
    assert {code: len(routes) for code, routes in selected["pilot_reserve"].items()} == {
        "DLA3": 1,
        "DSE4": 1,
    }


def test_pilot_and_reserve_files_are_separate_and_sorted(workspace):
    run_snapshot(make_cfg())
    selected = json.loads((workspace / "interim/routes_selected.json").read_text(encoding="utf-8"))

    pilot = load_snapshots(workspace / "interim/snapshots.jsonl")
    reserve = load_snapshots(workspace / "interim/snapshots_reserve.jsonl")

    assert [p.route_id for p in pilot] == selected["pilot"]
    assert [p.route_id for p in reserve] == sorted(
        route_id for routes in selected["pilot_reserve"].values() for route_id in routes
    )


def test_snapshot_uses_rho_of_its_route(workspace):
    cfg = make_cfg()
    run_snapshot(cfg)

    for p in load_snapshots(workspace / "interim/snapshots.jsonl"):
        rho = draw_rho(p.route_id, 0, 0.2, 0.5)
        expected = build_snapshot(
            load_route(cfg.raw_dir, p.route_id), rho, 0, 60, travel_dir=Path("interim/travel")
        )
        assert p == expected


def test_meta_has_no_timestamp_or_absolute_path(workspace):
    cfg = make_cfg()

    returned = run_snapshot(cfg)
    text = (workspace / "interim/snapshots.meta.json").read_text(encoding="utf-8")
    meta = json.loads(text)

    assert meta == returned
    assert set(meta) == {"config_hash", "files", "travel"}
    assert meta["config_hash"] == config_hash(cfg)
    assert set(meta["files"]) == {
        "routes_selected.json",
        "snapshots.jsonl",
        "snapshots_reserve.jsonl",
    }
    assert all(re.fullmatch(SHA256, digest) for digest in [*meta["files"].values(), meta["travel"]])
    assert workspace.name not in text
    assert not re.search(r"\b20\d\d-\d\d-\d\d|\d\d:\d\d:\d\d|[A-Za-z]:[\\/]|\\", text)


def test_meta_travel_hash_ignores_stale_matrices(workspace):
    cfg = make_cfg()
    first = run_snapshot(cfg)
    (workspace / "interim/travel/RouteID_stale.npy").write_bytes(b"left over")

    assert run_snapshot(cfg)["travel"] == first["travel"]


def test_meta_travel_hash_detects_changed_matrix(workspace):
    cfg = make_cfg()
    first = run_snapshot(cfg)
    matrices = sorted((workspace / "interim/travel").glob("*.npy"))
    routes = [matrix.stem for matrix in matrices]
    assert pipeline.travel_digest(cfg.interim_dir, routes) == first["travel"]

    matrices[0].write_bytes(matrices[0].read_bytes() + b"x")

    assert pipeline.travel_digest(cfg.interim_dir, routes) != first["travel"]


def test_travel_path_relative_posix(workspace):
    run_snapshot(make_cfg())

    for name in ("snapshots.jsonl", "snapshots_reserve.jsonl"):
        for p in load_snapshots(workspace / "interim" / name):
            assert p.travel_path == f"interim/travel/{p.route_id}.npy"


def absolute_config(path: Path) -> DataConfig:
    return make_cfg().model_copy(update={"interim_dir": path})


def test_absolute_interim_dir_rejected(workspace):
    target = workspace / "elsewhere"

    with pytest.raises(ValueError, match="relative"):
        run_snapshot(absolute_config(target))

    assert not target.exists()
    assert not (workspace / "raw" / "by_route").exists()


def test_rooted_interim_dir_rejected(workspace):
    with pytest.raises(ValueError, match="relative"):
        run_snapshot(absolute_config(Path("/interim")))


def test_min_remaining_enforced(workspace):
    with pytest.raises(ValueError, match="RouteID_[ab][0-9]"):
        run_snapshot(make_cfg(min_remaining=12))

    assert not (workspace / "interim/snapshots.jsonl").exists()
    assert not (workspace / "interim/snapshots_reserve.jsonl").exists()
    assert not (workspace / "interim/snapshots.meta.json").exists()


def checked_snapshot() -> RouteSnapshot:
    raw = load_route(Path("raw"), "RouteID_a0")
    return build_snapshot(raw, 0.3, 0, 60, travel_dir=Path("interim/travel"))


@pytest.mark.usefixtures("workspace")
def test_check_snapshot_accepts_a_good_snapshot():
    check_snapshot(checked_snapshot(), make_cfg().snapshot)


@pytest.mark.usefixtures("workspace")
def test_check_snapshot_rejects_duplicate_names():
    p = checked_snapshot()
    first, second = p.remaining[:2]
    twin = p.stops[second].model_copy(update={"name": f"  {p.stops[first].name.upper()} "})
    p = p.model_copy(update={"stops": p.stops | {second: twin}})

    with pytest.raises(ValueError, match="RouteID_a0.*name"):
        check_snapshot(p, make_cfg().snapshot)


@pytest.mark.usefixtures("workspace")
def test_check_snapshot_rejects_arrivals_not_increasing(monkeypatch):
    p = checked_snapshot()
    monkeypatch.setattr(pipeline, "baseline_arrivals", lambda _p: {"A": 10, "B": 10})

    with pytest.raises(ValueError, match="RouteID_a0.*arrivals"):
        check_snapshot(p, make_cfg().snapshot)


@pytest.mark.usefixtures("workspace")
@pytest.mark.parametrize("offset, accepted", [(60, True), (-60, True), (61, False), (-61, False)])
def test_check_snapshot_shift_end_tolerance(offset, accepted):
    p = checked_snapshot()
    p = p.model_copy(update={"shift_end": p.shift_end + offset})

    if accepted:
        check_snapshot(p, make_cfg().snapshot)
    else:
        with pytest.raises(ValueError, match="RouteID_a0.*shift"):
            check_snapshot(p, make_cfg().snapshot)


def test_existing_routes_not_reextracted(workspace, monkeypatch):
    calls: list[list[str]] = []
    real_extract = pipeline.extract_routes

    def counting_extract(raw_dir, route_ids):
        calls.append(sorted(route_ids))
        real_extract(raw_dir, route_ids)

    monkeypatch.setattr(pipeline, "extract_routes", counting_extract)
    cfg = make_cfg()

    run_snapshot(cfg)
    assert len(calls) == 1 and len(calls[0]) == 5

    run_snapshot(cfg)
    assert len(calls) == 1

    (workspace / "raw/by_route" / f"{calls[0][0]}.json").unlink()
    run_snapshot(cfg)
    assert calls[1:] == [[calls[0][0]]]


def test_load_snapshots_roundtrip(workspace):
    run_snapshot(make_cfg())
    path = workspace / "interim/snapshots.jsonl"

    loaded = load_snapshots(path)

    assert len(loaded) == 3
    assert all(isinstance(p, RouteSnapshot) for p in loaded)
    assert "".join(f"{p.model_dump_json()}\n" for p in loaded) == path.read_text(encoding="utf-8")


def test_load_snapshots_of_empty_file(tmp_path):
    path = tmp_path / "snapshots_reserve.jsonl"
    path.write_text("", encoding="utf-8")

    assert load_snapshots(path) == []


# --- statistics ----------------------------------------------------------------------------------


def handmade(
    route_id: str, station: str, stops: int, windows: int, remaining: int
) -> RouteSnapshot:
    """A snapshot with `stops` delivery stops, of which the first `windows` have a window."""

    def stop(stop_id: str, tw: tuple[int, int] | None) -> Stop:
        return Stop(
            stop_id=stop_id,
            name=stop_id,
            category="shop",
            zone_id=None,
            lat=0.0,
            lng=0.0,
            service_s=60,
            tw=tw,
        )

    ids = [f"S{i:02d}" for i in range(stops)]
    table = {
        stop_id: stop(stop_id, (0, 60) if i < windows else None) for i, stop_id in enumerate(ids)
    }
    return RouteSnapshot(
        snapshot_id=f"{route_id}@0",
        route_id=route_id,
        station_code=station,
        tz="America/Chicago",
        departure_local="09:00:00",
        t_now=0,
        current_stop="DP",
        done=ids[: stops - remaining],
        remaining=ids[stops - remaining :],
        stops={"DP": stop("DP", (0, 60)), **table},
        depot_id="DP",
        shift_end=3600,
        travel_path="unused.npy",
        node_ids=["DP", *ids],
    )


def test_snapshot_stats_on_handmade_snapshots():
    cfg = make_cfg()
    pilot = [
        handmade("r1", "DLA3", 4, 1, 3),
        handmade("r2", "DSE4", 9, 0, 5),
        handmade("r3", "DSE4", 19, 3, 11),
    ]
    reserve = [handmade("r4", "DAU1", 49, 49, 40)]
    rhos = [draw_rho(route_id, 0, 0.2, 0.5) for route_id in ("r1", "r2", "r3")]

    stats = snapshot_stats(pilot, reserve, cfg)

    assert stats["pilot"] == 3
    assert stats["reserve"] == 1
    assert stats["stations"] == 2
    assert stats["stops_mean"] == pytest.approx(35 / 3)
    assert stats["stops_p10"] == pytest.approx(6)
    assert stats["stops_p90"] == pytest.approx(18)
    assert (stats["remaining_min"], stats["remaining_median"], stats["remaining_max"]) == (3, 5, 11)
    assert stats["window_pct"] == pytest.approx(12.5)
    assert stats["window_pct_median"] == pytest.approx(300 / 19)
    assert stats["rho_min"] == min(rhos)
    assert stats["rho_max"] == max(rhos)


def test_format_stats_lines():
    stats = {
        "pilot": 30,
        "reserve": 18,
        "stations": 16,
        "stops_mean": 148.24,
        "stops_p10": 105.2,
        "stops_p90": 186.0,
        "remaining_min": 41,
        "remaining_median": 92.5,
        "remaining_max": 150,
        "window_pct": 6.14,
        "window_pct_median": 4.0,
        "rho_min": 0.2031,
        "rho_max": 0.4968,
    }
    meta = {
        "config_hash": "c" * 64,
        "files": {
            "routes_selected.json": "a" * 64,
            "snapshots.jsonl": "b" * 64,
            "snapshots_reserve.jsonl": "d" * 64,
        },
        "travel": "e" * 64,
    }

    assert format_stats(stats, meta).splitlines() == [
        "routes: 30 pilot, 18 reserve, 16 stations",
        "stops per route: mean 148.2, p10 105, p90 186",
        "remaining stops: min 41, median 92.5, max 150",
        "stops with a time window: 6.1% (median per route 4.0%)",
        "rho: min 0.203, max 0.497",
        f"config: {'c' * 64}",
        f"snapshots.jsonl: {'b' * 64}",
        f"snapshots_reserve.jsonl: {'d' * 64}",
        f"routes_selected.json: {'a' * 64}",
        f"travel: {'e' * 64}",
    ]


# --- CLI -----------------------------------------------------------------------------------------


def test_cli_snapshot(workspace):
    cfg = make_cfg()
    write_yaml(workspace / "data.yaml", cfg.model_dump(mode="json"))

    result = CliRunner().invoke(app, ["snapshot", "--config", "data.yaml"])

    assert result.exit_code == 0, result.output
    meta = json.loads((workspace / "interim/snapshots.meta.json").read_text(encoding="utf-8"))
    lines = result.output.splitlines()
    assert len(lines) == 10
    assert lines[0] == "routes: 3 pilot, 2 reserve, 2 stations"
    assert lines[1] == "stops per route: mean 12.0, p10 12, p90 12"
    assert re.fullmatch(r"remaining stops: min \d+, median [\d.]+, max \d+", lines[2])
    assert re.fullmatch(r"stops with a time window: [\d.]+% \(median per route [\d.]+%\)", lines[3])
    assert re.fullmatch(r"rho: min 0\.\d{3}, max 0\.\d{3}", lines[4])
    assert lines[5:] == [
        f"config: {config_hash(cfg)}",
        f"snapshots.jsonl: {meta['files']['snapshots.jsonl']}",
        f"snapshots_reserve.jsonl: {meta['files']['snapshots_reserve.jsonl']}",
        f"routes_selected.json: {meta['files']['routes_selected.json']}",
        f"travel: {meta['travel']}",
    ]


def test_cli_snapshot_requires_config():
    result = CliRunner().invoke(app, ["snapshot"])

    assert result.exit_code != 0
    assert "--config" in result.output
