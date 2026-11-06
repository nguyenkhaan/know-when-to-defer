"""Canonical form, equivalence and operation type of an EditSet (spec 06 §5).

The canonical form is a sorted tuple of plain tuples, one per op, with ids and seconds only:

    ("set_time_window", stop, start, end)   # both bounds explicit
    ("remove_stop", stop)
    ("precedence", before, after)
    ("driver_end_time", time)
    ("avoid_zone_until", zone, time)

It is hashable, so it can key the solver cache (spec 07 §4).
"""

from kwd.data.models import RouteSnapshot
from kwd.dsl.models import (
    AvoidZoneUntil,
    Deadline,
    DriverEndTime,
    Edit,
    EditSet,
    Precedence,
    RemoveStop,
    SetTimeWindow,
)

COMPOUND = "compound"
WINDOW = "set_time_window"

CanonicalOp = tuple[str | int, ...]


def _op_tuple(edit: Edit, p: RouteSnapshot) -> CanonicalOp:
    """Steps 1-2: explicit bounds, and `deadline` rewritten as a window ending at its time."""
    match edit:
        case SetTimeWindow():
            start = p.t_now if edit.start is None else edit.start
            end = p.shift_end if edit.end is None else edit.end
            return (WINDOW, edit.stop, start, end)
        case Deadline():
            return (WINDOW, edit.stop, p.t_now, edit.time)
        case RemoveStop():
            return ("remove_stop", edit.stop)
        case Precedence():
            return ("precedence", edit.before, edit.after)
        case DriverEndTime():
            return ("driver_end_time", edit.time)
        case AvoidZoneUntil():
            return ("avoid_zone_until", edit.zone, edit.time)
    raise AssertionError(f"unhandled op: {edit.op}")


def _merge_windows(ops: list[CanonicalOp]) -> list[CanonicalOp]:
    """Step 3: one window per stop, the intersection of all windows on it.

    An empty intersection is kept as it is (start > end): the edit is contradictory, and the
    solver reports it as Infeasible rather than the parser hiding it.
    """
    windows: dict[str | int, list[CanonicalOp]] = {}
    for op in ops:
        if op[0] == WINDOW:
            windows.setdefault(op[1], []).append(op)
    merged = [
        (WINDOW, stop, max(op[2] for op in group), min(op[3] for op in group))
        for stop, group in windows.items()
    ]
    return merged + [op for op in ops if op[0] != WINDOW]


def canonical(e: EditSet, p: RouteSnapshot) -> tuple[CanonicalOp, ...]:
    """Canonical form of `e` on snapshot `p` (spec 06 §5, steps 1-4); confidence is ignored."""
    ops = _merge_windows([_op_tuple(edit, p) for edit in e.edits])
    return tuple(sorted(set(ops)))  # step 4: sort, drop exact duplicates


def _close(a: CanonicalOp, b: CanonicalOp, tol_s: int) -> bool:
    if len(a) != len(b):
        return False
    for x, y in zip(a, b, strict=True):
        if isinstance(x, int) and isinstance(y, int):
            if abs(x - y) > tol_s:
                return False
        elif x != y:
            return False
    return True


def equivalent(a: EditSet, b: EditSet, p: RouteSnapshot, tol_min: int = 0) -> bool:
    """Canonical forms equal, with every time within ±`tol_min` minutes (spec 06 §5, step 5).

    Ops are paired in canonical order. Ids and op names must match exactly; only times get the
    tolerance.
    """
    ca, cb = canonical(a, p), canonical(b, p)
    if len(ca) != len(cb):
        return False
    return all(_close(x, y, tol_min * 60) for x, y in zip(ca, cb, strict=True))


def op_type(e: EditSet, p: RouteSnapshot) -> str:
    """Operation type on the canonical form (spec 06 §5.1): the op name, or `compound` for 2+ ops.

    The one function behind both `ĉ = op_type(ê)` (per-group CRC) and `c = op_type(e*)` (gold).
    """
    ops = canonical(e, p)
    return str(ops[0][0]) if len(ops) == 1 else COMPOUND
