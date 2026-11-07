"""Assign plan-level harm labels to parsed route edits (spec 09)."""

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from kwd.data.models import RouteSnapshot
from kwd.dsl import EditSet, ParseError, canonical, equivalent
from kwd.solver import (
    Infeasible,
    Plan,
    SolverConfig,
    check_constraints,
    current_plan,
    solve_cached,
)


class HarmConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    eps_abs: float = Field(default=5.0, ge=0)
    eps_rel: float = Field(default=0.02, ge=0)
    tol_min: int = Field(default=1, ge=0)


class HarmLabel(BaseModel):
    model_config = ConfigDict(frozen=True)

    item_id: str
    model: str
    executed: bool
    h: int | None
    rule: Literal["R1", "R2", "R3"] | None
    string_correct: bool
    harmless_error: bool
    nonbinding_error: bool
    delta_cost: float | None
    late_min: float | None
    tw_violations: int | None


def _cost(plan: Plan) -> float:
    return plan.travel_min + plan.lateness_min + plan.overtime_min


def _gold_windows(p: RouteSnapshot, gold: EditSet) -> list[tuple[str, int, int]]:
    windows = [
        (stop, bounds[0], bounds[1])
        for stop, details in p.stops.items()
        if (bounds := details.tw) is not None
    ]
    windows.extend(
        (str(op[1]), int(op[2]), int(op[3]))
        for op in canonical(gold, p)
        if op[0] == "set_time_window"
    )
    return windows


def _harm_magnitudes(
    p: RouteSnapshot,
    gold: EditSet,
    gold_plan: Plan,
    pred_plan: Plan,
    tol_min: int,
) -> tuple[float, int]:
    shared = set(gold_plan.sequence) & set(pred_plan.sequence)
    windows = [window for window in _gold_windows(p, gold) if window[0] in shared]
    tightest_upper: dict[str, int] = {}
    for stop, _lower, upper in windows:
        tightest_upper[stop] = min(tightest_upper.get(stop, upper), upper)

    late_min = 0.0
    for stop, upper in tightest_upper.items():
        gold_late = max(0, gold_plan.service_start[stop] - upper) / 60
        pred_late = max(0, pred_plan.service_start[stop] - upper) / 60
        late_min += max(0, pred_late - gold_late)

    tw_violations = 0
    for stop, lower, upper in windows:
        gold_start = gold_plan.service_start[stop]
        pred_start = pred_plan.service_start[stop]
        gold_miss = max(lower - gold_start, gold_start - upper, 0) / 60
        pred_miss = max(lower - pred_start, pred_start - upper, 0) / 60
        if gold_miss <= tol_min and pred_miss > tol_min:
            tw_violations += 1
    return late_min, tw_violations


def _not_executed(item_id: str, model: str, *, string_correct: bool) -> HarmLabel:
    return HarmLabel(
        item_id=item_id,
        model=model,
        executed=False,
        h=None,
        rule=None,
        string_correct=string_correct,
        harmless_error=False,
        nonbinding_error=False,
        delta_cost=None,
        late_min=None,
        tw_violations=None,
    )


def label_item(
    item_id: str,
    model: str,
    p: RouteSnapshot,
    gold: EditSet,
    pred: EditSet | ParseError,
    solver_cfg: SolverConfig,
    harm_cfg: HarmConfig,
    cache_dir: Path,
) -> HarmLabel:
    if isinstance(pred, ParseError):
        return _not_executed(item_id, model, string_correct=False)

    gold_plan = solve_cached(p, gold, solver_cfg, cache_dir)
    pred_plan = solve_cached(p, pred, solver_cfg, cache_dir)
    if isinstance(gold_plan, Infeasible):
        raise TypeError(f"gold edit is infeasible: {gold_plan.reason}: {gold_plan.detail}")
    if isinstance(pred_plan, Infeasible):
        return _not_executed(
            item_id,
            model,
            string_correct=equivalent(pred, gold, p),
        )

    string_correct = equivalent(pred, gold, p)
    delta_cost = _cost(pred_plan) - _cost(gold_plan)
    r1 = bool(check_constraints(p, pred_plan, gold, harm_cfg.tol_min))
    r2 = set(pred_plan.sequence) != set(gold_plan.sequence)
    epsilon = max(harm_cfg.eps_abs, harm_cfg.eps_rel * _cost(gold_plan))
    r3 = delta_cost > epsilon
    rule: Literal["R1", "R2", "R3"] | None
    if r1:
        rule = "R1"
    elif r2:
        rule = "R2"
    elif r3:
        rule = "R3"
    else:
        rule = None
    h = int(rule is not None)
    late_min, tw_violations = _harm_magnitudes(p, gold, gold_plan, pred_plan, harm_cfg.tol_min)
    return HarmLabel(
        item_id=item_id,
        model=model,
        executed=True,
        h=h,
        rule=rule,
        string_correct=string_correct,
        harmless_error=not string_correct and h == 0,
        nonbinding_error=h == 1 and pred_plan.digest() == current_plan(p).digest(),
        delta_cost=delta_cost,
        late_min=late_min,
        tw_violations=tw_violations,
    )
