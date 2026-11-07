from pathlib import Path

import pytest

from kwd.data.lmrc import load_route
from kwd.data.snapshot import build_snapshot, load_fixture_snapshot
from kwd.dsl import (
    AvoidZoneUntil,
    Deadline,
    DriverEndTime,
    EditSet,
    Precedence,
    RemoveStop,
    SetTimeWindow,
)
from kwd.solver import Infeasible, Plan, SolverConfig, check_constraints, solve

MINI = Path(__file__).parent.parent / "fixtures" / "lmrc_mini"
MINI_ROUTE = "RouteID_00143bdd-0a6b-49ec-bb35-36593d303e77"


def stops_by_category(snapshot) -> dict[str, str]:
    return {snapshot.stops[stop].category: stop for stop in snapshot.remaining}


@pytest.mark.parametrize(
    "make_edit",
    [
        lambda p, s: SetTimeWindow(stop=s["hospital"], start=7200, end=None),
        lambda p, s: RemoveStop(stop=s["shop"]),
        lambda p, s: Precedence(before=s["hospital"], after=s["pharmacy"]),
        lambda p, s: DriverEndTime(time=13_500),
        lambda p, s: AvoidZoneUntil(zone="B", time=7200),
        lambda p, s: Deadline(stop=s["shop"], time=10_800),
    ],
    ids=[
        "set_time_window",
        "remove_stop",
        "precedence",
        "driver_end_time",
        "avoid_zone_until",
        "deadline",
    ],
)
def test_solve_satisfies_each_edit_operation(make_edit):
    snapshot = load_fixture_snapshot("hospital")
    edit = EditSet(edits=[make_edit(snapshot, stops_by_category(snapshot))])

    result = solve(snapshot, edit, SolverConfig())

    assert isinstance(result, Plan)
    assert check_constraints(snapshot, result, edit) == []


@pytest.mark.parametrize(
    "make_edits",
    [
        lambda s: [
            SetTimeWindow(stop=s["hospital"], start=7200, end=10_800),
            Deadline(stop=s["hospital"], time=3600),
        ],
        lambda s: [
            Precedence(before=s["pharmacy"], after=s["hospital"]),
            Precedence(before=s["hospital"], after=s["pharmacy"]),
        ],
    ],
    ids=["empty_merged_window", "precedence_cycle"],
)
def test_conflicting_edits_are_prechecked(make_edits):
    snapshot = load_fixture_snapshot("hospital")
    edit = EditSet(edits=make_edits(stops_by_category(snapshot)))

    result = solve(snapshot, edit, SolverConfig())

    assert isinstance(result, Infeasible)
    assert result.reason == "precheck"


def test_start_node_service_is_not_counted_twice(tmp_path):
    snapshot = build_snapshot(load_route(MINI, MINI_ROUTE), 0.25, 0, travel_dir=tmp_path)
    assert snapshot.stops[snapshot.current_stop].service_s > 0
    baseline = solve(snapshot, None, SolverConfig())
    assert isinstance(baseline, Plan)
    edit = EditSet(edits=[DriverEndTime(time=baseline.end_time)])

    result = solve(snapshot, edit, SolverConfig())

    assert isinstance(result, Plan)
    assert result.end_time <= baseline.end_time


def test_zone_and_window_lower_bounds_are_intersected():
    snapshot = load_fixture_snapshot("hospital")
    pharmacy = stops_by_category(snapshot)["pharmacy"]
    edit = EditSet(
        edits=[
            AvoidZoneUntil(zone="A", time=1800),
            SetTimeWindow(stop=pharmacy, start=0, end=10_800),
        ]
    )

    result = solve(snapshot, edit, SolverConfig())

    assert isinstance(result, Plan)
    assert result.service_start[pharmacy] >= 1800
    assert check_constraints(snapshot, result, edit) == []


def test_constraint_on_removed_stop_is_left_to_harm_rule_r2():
    snapshot = load_fixture_snapshot("hospital")
    hospital = stops_by_category(snapshot)["hospital"]
    edit = EditSet(
        edits=[
            RemoveStop(stop=hospital),
            SetTimeWindow(stop=hospital, start=0, end=10_800),
        ]
    )

    result = solve(snapshot, edit, SolverConfig())

    assert isinstance(result, Plan)
    assert hospital not in result.sequence
    assert check_constraints(snapshot, result, edit) == []


def test_conflicting_zone_and_window_return_precheck_infeasible():
    snapshot = load_fixture_snapshot("hospital")
    hospital = stops_by_category(snapshot)["hospital"]
    edit = EditSet(
        edits=[
            AvoidZoneUntil(zone="A", time=7200),
            SetTimeWindow(stop=hospital, start=0, end=6000),
        ]
    )

    result = solve(snapshot, edit, SolverConfig())

    assert isinstance(result, Infeasible)
    assert result.reason == "precheck"


def test_window_violation_reports_exact_minutes():
    snapshot = load_fixture_snapshot("hospital")
    hospital = stops_by_category(snapshot)["hospital"]
    plan = solve(snapshot, None, SolverConfig())
    assert isinstance(plan, Plan)
    edit = EditSet(
        edits=[SetTimeWindow(stop=hospital, start=plan.service_start[hospital] + 300, end=None)]
    )

    violations = check_constraints(snapshot, plan, edit, tol_min=1)

    assert len(violations) == 1
    assert violations[0].op == "set_time_window"
    assert violations[0].stop == hospital
    assert violations[0].amount_min == 5


def test_constraint_violation_at_tolerance_is_allowed():
    snapshot = load_fixture_snapshot("hospital")
    hospital = stops_by_category(snapshot)["hospital"]
    plan = solve(snapshot, None, SolverConfig())
    assert isinstance(plan, Plan)
    edit = EditSet(
        edits=[SetTimeWindow(stop=hospital, start=plan.service_start[hospital] + 60, end=None)]
    )

    assert check_constraints(snapshot, plan, edit, tol_min=1) == []
