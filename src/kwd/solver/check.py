"""Independent checks of edit constraints on a completed plan (spec 07 §5)."""

import math

from pydantic import BaseModel, ConfigDict

from kwd.data.models import RouteSnapshot
from kwd.dsl import EditSet, canonical
from kwd.solver.tsptw import Plan


class Violation(BaseModel):
    model_config = ConfigDict(frozen=True)

    op: str
    stop: str | None
    amount_min: float


def check_constraints(
    p: RouteSnapshot, plan: Plan, e: EditSet, tol_min: int = 1
) -> list[Violation]:
    """Return canonical constraints violated by more than `tol_min` minutes."""
    violations = []
    present = set(plan.sequence)
    for op in canonical(e, p):
        name = str(op[0])
        stop: str | None = None
        amount_s: float
        if name == "set_time_window":
            stop, start, end = str(op[1]), int(op[2]), int(op[3])
            if stop not in present:
                continue
            served = plan.service_start[stop]
            amount_s = max(start - served, served - end)
        elif name == "precedence":
            before, after = str(op[1]), str(op[2])
            if before not in present or after not in present:
                continue
            stop = before
            amount_s = (
                plan.service_start[before] + p.stops[before].service_s - plan.service_start[after]
            )
        elif name == "driver_end_time":
            amount_s = plan.end_time - int(op[1])
        elif name == "avoid_zone_until":
            zone, lower = str(op[1]), int(op[2])
            relevant = [s for s in plan.sequence if p.stops[s].zone_id == zone]
            amount_s = max((lower - plan.service_start[s] for s in relevant), default=0)
        elif name == "remove_stop":
            stop = str(op[1])
            amount_s = math.inf if stop in present else 0
        else:
            raise AssertionError(f"unhandled canonical op: {name}")
        amount_min = amount_s / 60
        if amount_min > tol_min:
            violations.append(Violation(op=name, stop=stop, amount_min=amount_min))
    return violations
