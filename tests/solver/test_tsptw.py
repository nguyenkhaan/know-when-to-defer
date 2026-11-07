import shutil
from concurrent.futures import ProcessPoolExecutor
from itertools import pairwise
from pathlib import Path
from statistics import median

import pytest

from kwd.data.lmrc import load_route
from kwd.data.models import RouteSnapshot
from kwd.data.snapshot import baseline_arrivals, build_snapshot, load_fixture_snapshot
from kwd.dsl import EditSet, SetTimeWindow
from kwd.solver import Plan, SolverConfig, current_plan, is_fixed_point, solve, solve_cached

RAW_LMRC = Path("data/raw/lmrc")
LARGE_ROUTE = "RouteID_5059625b-4bf5-4576-b778-da34326ac4dc"


def objective(plan: Plan, cfg: SolverConfig) -> float:
    return (
        plan.travel_min
        + cfg.late_penalty * plan.lateness_min
        + cfg.shift_penalty * plan.overtime_min
        + cfg.dev_weight * plan.changed_positions
    )


def search_objective(snapshot: RouteSnapshot, plan: Plan, cfg: SolverConfig) -> float:
    original_arcs = set(pairwise([snapshot.current_stop, *snapshot.remaining, snapshot.depot_id]))
    plan_arcs = pairwise([snapshot.current_stop, *plan.sequence, snapshot.depot_id])
    changed_arcs = sum(arc not in original_arcs for arc in plan_arcs)
    return (
        plan.travel_min
        + cfg.late_penalty * plan.lateness_min
        + cfg.shift_penalty * plan.overtime_min
        + cfg.dev_weight * changed_arcs
    )


def test_empty_edit_keeps_plan():
    snapshot = load_fixture_snapshot("hospital")
    cfg = SolverConfig()

    before = current_plan(snapshot)
    result = solve(snapshot, None, cfg)

    assert isinstance(result, Plan)
    assert result.arrival == baseline_arrivals(snapshot)
    assert objective(result, cfg) <= objective(before, cfg)
    assert result.digest() == before.digest()
    assert is_fixed_point(snapshot, cfg)


def test_hospital_gold_moves_after_15():
    snapshot = load_fixture_snapshot("hospital")
    hospital = next(s for s in snapshot.remaining if snapshot.stops[s].category == "hospital")
    gold = EditSet(edits=[SetTimeWindow(stop=hospital, start=7200, end=None)])

    result = solve(snapshot, gold, SolverConfig())

    assert isinstance(result, Plan)
    assert result.service_start[hospital] >= 7200


def test_hospital_wrong_keeps_plan():
    snapshot = load_fixture_snapshot("hospital")
    hospital = next(s for s in snapshot.remaining if snapshot.stops[s].category == "hospital")
    wrong = EditSet(edits=[SetTimeWindow(stop=hospital, start=None, end=7200)])

    result = solve(snapshot, wrong, SolverConfig())

    assert isinstance(result, Plan)
    assert result.digest() == current_plan(snapshot).digest()


def test_digest_detects_wait_only_change():
    snapshot = load_fixture_snapshot("hospital")
    pharmacy = next(s for s in snapshot.remaining if snapshot.stops[s].category == "pharmacy")
    before = current_plan(snapshot)
    later = EditSet(edits=[SetTimeWindow(stop=pharmacy, start=1800, end=None)])
    earlier = EditSet(edits=[SetTimeWindow(stop=pharmacy, start=600, end=None)])

    delayed = solve(snapshot, later, SolverConfig())
    unchanged = solve(snapshot, earlier, SolverConfig())

    assert isinstance(delayed, Plan)
    assert delayed.sequence == before.sequence
    assert delayed.digest() != before.digest()
    assert isinstance(unchanged, Plan)
    assert unchanged.digest() == before.digest()


def large_snapshot(tmp_path: Path) -> RouteSnapshot:
    extracted = RAW_LMRC / "by_route" / f"{LARGE_ROUTE}.json"
    if not extracted.exists():
        pytest.skip("extracted LMRC route is not available")
    snapshot = build_snapshot(load_route(RAW_LMRC, LARGE_ROUTE), 0.04, 0, travel_dir=tmp_path)
    assert len(snapshot.remaining) == 150
    return snapshot


def solve_digest(snapshot_json: str) -> tuple[str, str]:
    snapshot = RouteSnapshot.model_validate_json(snapshot_json)
    result = solve(snapshot, None, SolverConfig())
    assert isinstance(result, Plan)
    return result.digest(), result.solve_status


def solve_cached_digest(args: tuple[str, str]) -> str:
    snapshot_json, cache_dir = args
    snapshot = RouteSnapshot.model_validate_json(snapshot_json)
    result = solve_cached(snapshot, None, SolverConfig(), Path(cache_dir))
    assert isinstance(result, Plan)
    return result.digest()


def test_deterministic_on_large_real_snapshot(tmp_path):
    snapshot = large_snapshot(tmp_path)
    sequential = [solve_digest(snapshot.model_dump_json()) for _ in range(3)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        parallel = list(pool.map(solve_digest, [snapshot.model_dump_json()] * 3))

    assert len({digest for digest, _ in sequential + parallel}) == 1
    assert {status for _, status in sequential + parallel} == {"solution_limit"}


def test_solve_time_on_150_remaining_stops(tmp_path):
    snapshot = large_snapshot(tmp_path)
    results = [solve(snapshot, None, SolverConfig()) for _ in range(3)]

    assert all(isinstance(result, Plan) for result in results)
    assert median(result.solve_time_s for result in results if isinstance(result, Plan)) <= 3


def test_solver_cache_reuses_result_without_travel_matrix(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    matrix = tmp_path / "travel.npy"
    shutil.copy(snapshot.travel_path, matrix)
    snapshot = snapshot.model_copy(update={"travel_path": str(matrix)})
    cache_dir = tmp_path / "cache"

    first = solve_cached(snapshot, None, SolverConfig(), cache_dir)
    matrix.unlink()
    second = solve_cached(snapshot, None, SolverConfig(), cache_dir)

    assert second == first
    assert len(list(cache_dir.glob("*.json"))) == 1


def test_solver_cache_allows_concurrent_writers(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    cache_dir = tmp_path / "cache"
    args = [(snapshot.model_dump_json(), str(cache_dir))] * 8

    with ProcessPoolExecutor(max_workers=4) as pool:
        digests = list(pool.map(solve_cached_digest, args))

    assert len(set(digests)) == 1
    assert len(list(cache_dir.glob("*.json"))) == 1


def test_no_edit_never_worsens_search_objective_on_real_snapshots(tmp_path):
    extracted = sorted((RAW_LMRC / "by_route").glob("*.json"))
    if len(extracted) < 20:
        pytest.skip("20 extracted LMRC routes are not available")
    cfg = SolverConfig()
    for route_path in extracted[:20]:
        snapshot = build_snapshot(
            load_route(RAW_LMRC, route_path.stem),
            0.25,
            0,
            travel_dir=tmp_path / route_path.stem,
        )
        before = current_plan(snapshot)
        result = solve(snapshot, None, cfg)

        assert isinstance(result, Plan)
        assert before.arrival == baseline_arrivals(snapshot)
        assert search_objective(snapshot, result, cfg) <= search_objective(snapshot, before, cfg)
