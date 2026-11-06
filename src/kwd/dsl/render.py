"""Text forms of a parsed EditSet: DSL JSON (inverse of parsing) and plain English (spec 11 G1)."""

import json

from kwd.data.models import RouteSnapshot
from kwd.data.snapshot import clock_str
from kwd.dsl.models import (
    AvoidZoneUntil,
    Deadline,
    DriverEndTime,
    Edit,
    EditSet,
    JsonEditSet,
    Precedence,
    RemoveStop,
    SetTimeWindow,
)


def editset_json_schema() -> dict:
    """JSON schema of what the LLM must write; pasted into the prompt (spec 10 §3)."""
    return JsonEditSet.model_json_schema()


def _clock(p: RouteSnapshot, s: int | None) -> str | None:
    return None if s is None else clock_str(p, s)


def _edit_json(edit: Edit, p: RouteSnapshot) -> dict:
    """One edit as the LLM would write it: display names and local "HH:MM"."""
    data = edit.model_dump()
    for field in ("stop", "before", "after"):
        if field in data:
            data[field] = p.stops[data[field]].name
    for field in ("start", "end", "time"):
        if field in data:
            data[field] = _clock(p, data[field])
    return data


def dump_editset(e: EditSet, p: RouteSnapshot) -> str:
    """DSL JSON of `e`, so that `parse_editset(dump_editset(e, p), p) == e` (spec 06 §7).

    Times are written with `clock_str`, which rounds down to the minute: the round trip is exact
    for times that fall on a local minute, as all parsed times do.
    """
    body: dict = {"edits": [_edit_json(edit, p) for edit in e.edits]}
    if e.confidence is not None:
        body["confidence"] = e.confidence
    return json.dumps(body)


def _sentence(edit: Edit, p: RouteSnapshot) -> str:
    def name(stop_id: str) -> str:
        return p.stops[stop_id].name

    match edit:
        case SetTimeWindow(start=None):
            return f"Deliver to {name(edit.stop)} no later than {clock_str(p, edit.end)}."
        case SetTimeWindow(end=None):
            return f"Deliver to {name(edit.stop)} no earlier than {clock_str(p, edit.start)}."
        case SetTimeWindow():
            start, end = clock_str(p, edit.start), clock_str(p, edit.end)
            return f"Deliver to {name(edit.stop)} between {start} and {end}."
        case Deadline():
            return f"Deliver to {name(edit.stop)} by {clock_str(p, edit.time)}."
        case RemoveStop():
            return f"Do not visit {name(edit.stop)}."
        case Precedence():
            return f"Visit {name(edit.before)} before {name(edit.after)}."
        case DriverEndTime():
            return f"Return to the depot by {clock_str(p, edit.time)}."
        case AvoidZoneUntil():
            return (
                f"Do not arrive at any stop in zone {edit.zone} before {clock_str(p, edit.time)}."
            )
    raise AssertionError(f"unhandled op: {edit.op}")


def render_editset_en(e: EditSet, p: RouteSnapshot) -> str:
    """One English sentence per edit, in the order written (not canonical): input of baseline G1.

    Ops are rendered as written, so `deadline` and `set_time_window` read differently, as the
    LLM phrased them.
    """
    return "\n".join(_sentence(edit, p) for edit in e.edits)
