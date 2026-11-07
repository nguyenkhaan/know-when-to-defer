"""Golden example of spec 14 §4, end to end: LLM text -> parser -> solver -> harm label."""

from pathlib import Path

import pytest
import yaml

from kwd.data.snapshot import clock_str, load_fixture_snapshot
from kwd.dsl import EditSet, parse_editset
from kwd.harm import HarmConfig, HarmLabel, label_item
from kwd.solver import Plan, SolverConfig, current_plan, solve

CONFIGS = Path(__file__).parents[1] / "configs"
GOLD_JSON = (
    '{"edits": [{"op": "set_time_window", "stop": "Green Valley Hospital", '
    '"start": "15:00", "end": null}]}'
)
WRONG_JSON = (
    '{"edits": [{"op": "set_time_window", "stop": "Green Valley Hospital", '
    '"start": null, "end": "15:00"}]}'
)


def solver_config() -> SolverConfig:
    raw = yaml.safe_load((CONFIGS / "solver.yaml").read_text(encoding="utf-8"))
    return SolverConfig.model_validate(raw)


def harm_config() -> HarmConfig:
    raw = yaml.safe_load((CONFIGS / "harm.yaml").read_text(encoding="utf-8"))
    return HarmConfig.model_validate(raw)


def parsed(text: str, snapshot) -> EditSet:
    result = parse_editset(text, snapshot)
    assert isinstance(result, EditSet), result
    return result


def label_of(text: str, snapshot, tmp_path: Path) -> HarmLabel:
    return label_item(
        "hospital",
        "stub",
        snapshot,
        parsed(GOLD_JSON, snapshot),
        parsed(text, snapshot),
        solver_config(),
        harm_config(),
        tmp_path / "cache",
    )


@pytest.fixture
def snapshot():
    return load_fixture_snapshot("hospital")


def test_e2e_hospital_wrong_edit_is_harm(snapshot, tmp_path):
    label = label_of(WRONG_JSON, snapshot, tmp_path)

    assert label.executed is True
    assert label.h == 1
    assert label.rule == "R1"
    assert label.nonbinding_error is True
    assert label.string_correct is False
    plan = solve(snapshot, parsed(WRONG_JSON, snapshot), solver_config())
    assert isinstance(plan, Plan)
    assert plan.digest() == current_plan(snapshot).digest()


def test_e2e_hospital_gold_edit_is_harmless(snapshot, tmp_path):
    label = label_of(GOLD_JSON, snapshot, tmp_path)

    assert label.executed is True
    assert label.h == 0
    assert label.rule is None
    assert label.string_correct is True
    assert label.nonbinding_error is False
    assert label.delta_cost == 0


def test_e2e_hospital_gold_plan(snapshot):
    plan = solve(snapshot, parsed(GOLD_JSON, snapshot), solver_config())

    assert isinstance(plan, Plan)
    categories = [snapshot.stops[stop].category for stop in plan.sequence]
    assert categories == ["pharmacy", "school", "hospital", "shop"]
    hospital = next(s for s in plan.sequence if snapshot.stops[s].category == "hospital")
    assert clock_str(snapshot, plan.service_start[hospital]) == "15:10"
