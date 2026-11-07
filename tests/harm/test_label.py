from pathlib import Path

import pytest
import yaml

import kwd.harm.label as harm_label
from kwd.data.snapshot import load_fixture_snapshot
from kwd.dsl import (
    Deadline,
    DriverEndTime,
    EditSet,
    ParseError,
    Precedence,
    RemoveStop,
    SetTimeWindow,
)
from kwd.harm import HarmConfig, label_item
from kwd.solver import SolverConfig, current_plan


def stop_by_category(snapshot, category):
    return next(stop for stop in snapshot.remaining if snapshot.stops[stop].category == category)


def make_label(tmp_path, snapshot, gold, pred, harm_cfg=None):
    return label_item(
        "item-1",
        "test-model",
        snapshot,
        gold,
        pred,
        SolverConfig(),
        harm_cfg or HarmConfig(),
        tmp_path,
    )


def test_harm_config_file_matches_defaults():
    raw = yaml.safe_load(Path("configs/harm.yaml").read_text(encoding="utf-8"))

    assert HarmConfig.model_validate(raw) == HarmConfig()


def test_hospital_is_harm_r1_nonbinding(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    hospital = stop_by_category(snapshot, "hospital")
    gold = EditSet(edits=[SetTimeWindow(stop=hospital, start=7200, end=None)])
    wrong = EditSet(edits=[SetTimeWindow(stop=hospital, start=None, end=7200)])

    label = label_item(
        "hospital-direction",
        "test-model",
        snapshot,
        gold,
        wrong,
        SolverConfig(),
        HarmConfig(),
        tmp_path,
    )

    assert label.executed is True
    assert label.h == 1
    assert label.rule == "R1"
    assert label.nonbinding_error is True


def test_r2_wrong_stop_removed(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    pharmacy = stop_by_category(snapshot, "pharmacy")
    school = stop_by_category(snapshot, "school")
    gold = EditSet(edits=[Deadline(stop=school, time=7200)])
    wrong = EditSet(edits=[RemoveStop(stop=pharmacy)])

    label = make_label(tmp_path, snapshot, gold, wrong)

    assert label.h == 1
    assert label.rule == "R2"


def test_r3_excess_cost(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    pharmacy = stop_by_category(snapshot, "pharmacy")
    shop = stop_by_category(snapshot, "shop")
    gold = EditSet(edits=[DriverEndTime(time=snapshot.shift_end)])
    detour = EditSet(edits=[Precedence(before=shop, after=pharmacy)])

    label = make_label(tmp_path, snapshot, gold, detour)

    assert label.delta_cost is not None and label.delta_cost > 5
    assert label.h == 1
    assert label.rule == "R3"


def test_equivalent_is_harmless(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    school = stop_by_category(snapshot, "school")
    gold = EditSet(edits=[Deadline(stop=school, time=7200)])
    equivalent_window = EditSet(edits=[SetTimeWindow(stop=school, start=None, end=7200)])

    label = make_label(tmp_path, snapshot, gold, equivalent_window)

    assert label.string_correct is True
    assert label.h == 0
    assert label.harmless_error is False


def test_rule_precedence(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    hospital = stop_by_category(snapshot, "hospital")
    pharmacy = stop_by_category(snapshot, "pharmacy")
    shop = stop_by_category(snapshot, "shop")
    gold = EditSet(edits=[SetTimeWindow(stop=hospital, start=7200, end=None)])
    wrong_and_costly = EditSet(
        edits=[
            SetTimeWindow(stop=hospital, start=None, end=3600),
            Precedence(before=shop, after=pharmacy),
        ]
    )

    label = make_label(tmp_path, snapshot, gold, wrong_and_costly)

    assert label.delta_cost is not None and label.delta_cost > 5
    assert label.rule == "R1"


@pytest.mark.parametrize("cost_field", ["travel_min", "lateness_min", "overtime_min"])
def test_cost_in_minutes(cost_field, monkeypatch, tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    hospital = stop_by_category(snapshot, "hospital")
    gold = EditSet(edits=[Deadline(stop=hospital, time=7200)])
    pred = EditSet(edits=[Deadline(stop=hospital, time=7140)])
    gold_plan = current_plan(snapshot)
    pred_plan = gold_plan.model_copy(update={cost_field: getattr(gold_plan, cost_field) + 1})

    def fake_solve_cached(_snapshot, edit, _solver_cfg, _cache_dir):
        return gold_plan if edit == gold else pred_plan

    monkeypatch.setattr(harm_label, "solve_cached", fake_solve_cached)

    label = make_label(tmp_path, snapshot, gold, pred)

    assert label.delta_cost == 1


def test_late_min_and_tw_violations_zero_when_equal_to_gold(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    school = stop_by_category(snapshot, "school")
    gold = EditSet(edits=[Deadline(stop=school, time=7200)])

    label = make_label(tmp_path, snapshot, gold, gold)

    assert label.late_min == 0
    assert label.tw_violations == 0


def test_late_min_and_tw_violations_measure_gold_window(monkeypatch, tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    hospital = stop_by_category(snapshot, "hospital")
    gold = EditSet(edits=[Deadline(stop=hospital, time=4200)])
    pred = EditSet(edits=[Deadline(stop=hospital, time=7200)])
    gold_plan = current_plan(snapshot)
    delayed_service = dict(gold_plan.service_start)
    delayed_service[hospital] += 360
    pred_plan = gold_plan.model_copy(update={"service_start": delayed_service})

    def fake_solve_cached(_snapshot, edit, _solver_cfg, _cache_dir):
        return gold_plan if edit == gold else pred_plan

    monkeypatch.setattr(harm_label, "solve_cached", fake_solve_cached)

    label = make_label(tmp_path, snapshot, gold, pred)

    assert label.late_min == 6
    assert label.tw_violations == 1


def test_parse_error_not_executed(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    school = stop_by_category(snapshot, "school")
    gold = EditSet(edits=[Deadline(stop=school, time=7200)])
    parse_error = ParseError(code="invalid_json", detail="not JSON")

    label = make_label(tmp_path, snapshot, gold, parse_error)

    assert label.executed is False
    assert label.h is None
    assert label.rule is None
    assert label.delta_cost is None


def test_infeasible_not_executed(tmp_path):
    snapshot = load_fixture_snapshot("hospital")
    hospital = stop_by_category(snapshot, "hospital")
    school = stop_by_category(snapshot, "school")
    gold = EditSet(edits=[Deadline(stop=school, time=7200)])
    infeasible = EditSet(edits=[SetTimeWindow(stop=hospital, start=7200, end=3600)])

    label = make_label(tmp_path, snapshot, gold, infeasible)

    assert label.executed is False
    assert label.h is None
    assert label.rule is None
    assert label.delta_cost is None
