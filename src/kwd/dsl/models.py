"""Edit DSL models (spec 06 §3, §6).

Two families share one set of op names and fields:

- `Json*` models describe what the LLM writes: display names and local clock strings. They give
  the JSON schema pasted into the prompt (spec 10) and do the `schema` checks of spec 06 §4.
- `Edit` / `EditSet` hold a parsed edit: `stop_id`s, zone ids from the snapshot, and times in
  whole seconds since departure. `None` keeps an open window side open; `canonical` closes it.

Ops are never rewritten here: a parsed `deadline` stays a `deadline` (canonical form does that).
"""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from kwd.data.names import normalize_name

MAX_EDITS = 4

OPS = (
    "set_time_window",
    "remove_stop",
    "precedence",
    "driver_end_time",
    "avoid_zone_until",
    "deadline",
)

Confidence = Annotated[int, Field(ge=0, le=100, strict=True)]


class _Op(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


def _check_window(start: object, end: object) -> None:
    if start is None and end is None:
        raise ValueError("set_time_window needs at least one bound")


def _check_precedence(before: str, after: str, key=lambda name: name) -> None:
    if key(before) == key(after):
        raise ValueError("precedence relates a stop to itself")


# --- parsed edits: stop ids and seconds since departure ------------------------------------------


class SetTimeWindow(_Op):
    op: Literal["set_time_window"] = "set_time_window"
    stop: str
    start: int | None
    end: int | None

    @model_validator(mode="after")
    def _has_bound(self) -> Self:
        _check_window(self.start, self.end)
        return self


class RemoveStop(_Op):
    op: Literal["remove_stop"] = "remove_stop"
    stop: str


class Precedence(_Op):
    op: Literal["precedence"] = "precedence"
    before: str
    after: str

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        _check_precedence(self.before, self.after)
        return self


class DriverEndTime(_Op):
    op: Literal["driver_end_time"] = "driver_end_time"
    time: int


class AvoidZoneUntil(_Op):
    op: Literal["avoid_zone_until"] = "avoid_zone_until"
    zone: str
    time: int


class Deadline(_Op):
    op: Literal["deadline"] = "deadline"
    stop: str
    time: int


Edit = Annotated[
    SetTimeWindow | RemoveStop | Precedence | DriverEndTime | AvoidZoneUntil | Deadline,
    Field(discriminator="op"),
]


class EditSet(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    edits: list[Edit] = Field(min_length=1, max_length=MAX_EDITS)
    confidence: Confidence | None = None


# --- what the LLM writes: display names and local clock strings ----------------------------------

# Clock fields hold the text as written; `kwd.dsl.parse` checks and converts it, so that a bad
# clock is reported as `schema` like any other malformed field.
Clock = Annotated[str, Field(description="local time, HH:MM (24-hour)")]
StopName = Annotated[str, Field(description="stop name exactly as listed")]


class JsonSetTimeWindow(_Op):
    """Arrive at `stop` within [start, end]; null leaves that side open."""

    op: Literal["set_time_window"]
    stop: StopName
    start: Clock | None
    end: Clock | None

    @model_validator(mode="after")
    def _has_bound(self) -> Self:
        _check_window(self.start, self.end)
        return self


class JsonRemoveStop(_Op):
    """`stop` is not visited."""

    op: Literal["remove_stop"]
    stop: StopName


class JsonPrecedence(_Op):
    """`before` is visited before `after`."""

    op: Literal["precedence"]
    before: StopName
    after: StopName

    @model_validator(mode="after")
    def _distinct(self) -> Self:
        _check_precedence(self.before, self.after, normalize_name)
        return self


class JsonDriverEndTime(_Op):
    """The vehicle is back at the depot by `time`."""

    op: Literal["driver_end_time"]
    time: Clock


class JsonAvoidZoneUntil(_Op):
    """No arrival at any stop in `zone` before `time`."""

    op: Literal["avoid_zone_until"]
    zone: Annotated[str, Field(description="zone exactly as listed")]
    time: Clock


class JsonDeadline(_Op):
    """Arrive at `stop` no later than `time`."""

    op: Literal["deadline"]
    stop: StopName
    time: Clock


JsonEdit = Annotated[
    JsonSetTimeWindow
    | JsonRemoveStop
    | JsonPrecedence
    | JsonDriverEndTime
    | JsonAvoidZoneUntil
    | JsonDeadline,
    Field(discriminator="op"),
]


class JsonEditSet(BaseModel):
    """Route edits for one dispatcher request."""

    model_config = ConfigDict(extra="forbid", frozen=True, title="EditSet")

    edits: list[JsonEdit] = Field(min_length=1, max_length=MAX_EDITS)
    confidence: Confidence | None = Field(
        default=None, description="0-100: how sure you are the edits match the request"
    )


class ParseError(BaseModel):
    """Why an LLM output cannot be executed (spec 06 §4); the item is deferred automatically."""

    model_config = ConfigDict(frozen=True)

    code: Literal[
        "invalid_json", "schema", "unknown_stop", "unknown_zone", "done_stop", "bad_interval"
    ]
    detail: str
