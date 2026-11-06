"""Validate raw LLM output against a snapshot (spec 06 §4).

The output is never repaired (CLAUDE.md): anything that is not exactly one JSON object of the
DSL becomes a `ParseError`, and the item is deferred. Two normalizations are part of the language
itself, not repairs: stop names and zones match after `normalize_name` (case, whitespace), and
clock times may be written "15:00", "3:00 PM", "3 pm" or "3pm" (Review Focus #1, #2).
"""

import json
import re

from pydantic import ValidationError

from kwd.data.models import RouteSnapshot
from kwd.data.names import normalize_name
from kwd.data.snapshot import clock_to_s
from kwd.dsl.models import (
    AvoidZoneUntil,
    Deadline,
    DriverEndTime,
    Edit,
    EditSet,
    JsonAvoidZoneUntil,
    JsonDeadline,
    JsonDriverEndTime,
    JsonEdit,
    JsonEditSet,
    JsonPrecedence,
    JsonRemoveStop,
    JsonServiceTime,
    JsonSetTimeWindow,
    ParseError,
    Precedence,
    RemoveStop,
    ServiceTime,
    SetTimeWindow,
)

_CLOCK_24H = re.compile(r"([0-9]{1,2}):([0-9]{2})")
_CLOCK_12H = re.compile(r"([0-9]{1,2})(?::([0-9]{2}))?\s*([ap])\.?m\.?", re.IGNORECASE)


def parse_clock(text: str) -> str | None:
    """Return the local "HH:MM" written as 24-hour or 12-hour text, or None if not a clock time.

    Bare hours ("3", "15"), "15h" and words ("afternoon", "noon") are rejected: they are either
    ambiguous or outside the language, and guessing would repair the LLM output.
    """
    text = text.strip()
    if match := _CLOCK_24H.fullmatch(text):
        hours, minutes = int(match[1]), int(match[2])
        if hours >= 24:
            return None
    elif match := _CLOCK_12H.fullmatch(text):
        hours, minutes = int(match[1]), int(match[2] or 0)
        if not 1 <= hours <= 12:
            return None
        hours = hours % 12 + (12 if match[3].lower() == "p" else 0)
    else:
        return None
    if minutes >= 60:
        return None
    return f"{hours:02d}:{minutes:02d}"


class _Reject(Exception):
    def __init__(self, code: str, detail: str):
        self.error = ParseError(code=code, detail=detail)


def _schema_detail(error: ValidationError) -> str:
    first = error.errors()[0]
    where = ".".join(str(part) for part in first["loc"]) or "<root>"
    return f"{where}: {first['msg']}"


def _clock_fields(edit: JsonEdit) -> dict[str, str | None]:
    if isinstance(edit, JsonSetTimeWindow):
        return {"start": edit.start, "end": edit.end}
    if isinstance(edit, JsonDriverEndTime | JsonAvoidZoneUntil | JsonDeadline):
        return {"time": edit.time}
    return {}


def _check_clocks(edits: list[JsonEdit]) -> None:
    for i, edit in enumerate(edits):
        for field, text in _clock_fields(edit).items():
            if text is not None and parse_clock(text) is None:
                raise _Reject("schema", f"edits.{i}.{field}: not a clock time: {text!r}")


class _Resolver:
    """Turn names and clock text into the ids and seconds of one snapshot."""

    def __init__(self, p: RouteSnapshot):
        self.p = p
        self.stop_by_name = {normalize_name(stop.name): stop.stop_id for stop in p.stops.values()}
        self.remaining = set(p.remaining)
        self.served = {*p.done, p.current_stop} - {p.depot_id}
        zones = {p.stops[stop].zone_id for stop in p.remaining} - {None}
        self.zone_by_name = {normalize_name(zone): zone for zone in zones}

    def stop(self, name: str) -> str:
        stop_id = self.stop_by_name.get(normalize_name(name))
        if stop_id in self.remaining:
            return stop_id
        if stop_id in self.served:
            raise _Reject("done_stop", f"{name!r} was already delivered")
        raise _Reject("unknown_stop", f"{name!r} is not a remaining stop")

    def zone(self, name: str) -> str:
        zone = self.zone_by_name.get(normalize_name(name))
        if zone is None:
            raise _Reject("unknown_zone", f"no remaining stop in zone {name!r}")
        return zone

    def time(self, text: str) -> int:
        """Seconds since departure; a time whose whole minute is over is rejected.

        `t_now` usually falls inside a minute, which the snapshot shows as the current time, so
        that minute is still accepted.
        """
        hhmm = parse_clock(text)
        assert hhmm is not None  # checked by _check_clocks
        seconds = clock_to_s(self.p, hhmm)
        if seconds + 60 <= self.p.t_now:
            raise _Reject("bad_interval", f"{text!r} is before the current time")
        return seconds

    def optional_time(self, text: str | None) -> int | None:
        return None if text is None else self.time(text)

    def edit(self, edit: JsonEdit) -> Edit:
        match edit:
            case JsonSetTimeWindow():
                stop = self.stop(edit.stop)
                start, end = self.optional_time(edit.start), self.optional_time(edit.end)
                if start is not None and end is not None and start > end:
                    raise _Reject("bad_interval", f"window {edit.start}-{edit.end} is empty")
                return SetTimeWindow(stop=stop, start=start, end=end)
            case JsonRemoveStop():
                return RemoveStop(stop=self.stop(edit.stop))
            case JsonPrecedence():
                return Precedence(before=self.stop(edit.before), after=self.stop(edit.after))
            case JsonDriverEndTime():
                return DriverEndTime(time=self.time(edit.time))
            case JsonAvoidZoneUntil():
                return AvoidZoneUntil(zone=self.zone(edit.zone), time=self.time(edit.time))
            case JsonServiceTime():
                return ServiceTime(stop=self.stop(edit.stop), minutes=edit.minutes)
            case JsonDeadline():
                return Deadline(stop=self.stop(edit.stop), time=self.time(edit.time))
        raise AssertionError(f"unhandled op: {edit.op}")


def parse_editset(raw: str, p: RouteSnapshot) -> EditSet | ParseError:
    """Validate one LLM output on snapshot `p`; the first problem found decides the error code.

    All `schema` checks run before any name or time is resolved, so a malformed edit is reported
    as `schema` even when an earlier edit names an unknown stop.
    """
    try:
        data = json.loads(raw)
    except ValueError as error:
        return ParseError(code="invalid_json", detail=str(error))
    try:
        envelope = JsonEditSet.model_validate(data)
        _check_clocks(envelope.edits)
        resolver = _Resolver(p)
        edits = [resolver.edit(edit) for edit in envelope.edits]
    except ValidationError as error:
        return ParseError(code="schema", detail=_schema_detail(error))
    except _Reject as reject:
        return reject.error
    return EditSet(edits=edits, confidence=envelope.confidence)
