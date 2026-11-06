import json

import pytest

from kwd.data.snapshot import clock_str
from kwd.dsl import (
    Deadline,
    EditSet,
    ParseError,
    RemoveStop,
    SetTimeWindow,
    editset_json_schema,
    parse_editset,
)
from kwd.dsl.parse import parse_clock

OPS = {
    "set_time_window",
    "remove_stop",
    "precedence",
    "driver_end_time",
    "avoid_zone_until",
    "service_time",
    "deadline",
}


def raw(*edits: dict, confidence: int | None = None) -> str:
    body: dict = {"edits": list(edits)}
    if confidence is not None:
        body["confidence"] = confidence
    return json.dumps(body)


def window(stop: str, start: str | None, end: str | None) -> dict:
    return {"op": "set_time_window", "stop": stop, "start": start, "end": end}


def error_code(result) -> str:
    assert isinstance(result, ParseError), result
    return result.code


# --- valid input --------------------------------------------------------------------------------


def test_parse_hospital_gold(hospital):
    result = parse_editset(raw(window("An Binh Hospital", "15:00", None), confidence=80), hospital)
    assert result == EditSet(
        edits=[SetTimeWindow(stop="HO", start=2 * 3600, end=None)], confidence=80
    )


def test_parse_every_op(hospital):
    result = parse_editset(
        raw(
            window("An Binh Hospital", None, "16:00"),
            {"op": "remove_stop", "stop": "Thanh Cong Shop"},
            {"op": "precedence", "before": "Nguyen Du School", "after": "Minh Chau Pharmacy"},
            {"op": "driver_end_time", "time": "17:00"},
        ),
        hospital,
    )
    assert isinstance(result, EditSet)
    assert [e.op for e in result.edits] == [
        "set_time_window",
        "remove_stop",
        "precedence",
        "driver_end_time",
    ]
    assert result.edits[2].before == "SC"
    assert result.edits[2].after == "PH"
    assert result.edits[3].time == 4 * 3600
    assert result.confidence is None

    result = parse_editset(
        raw(
            {"op": "avoid_zone_until", "zone": "B", "time": "14:30"},
            {"op": "service_time", "stop": "Minh Chau Pharmacy", "minutes": 12},
            {"op": "deadline", "stop": "Nguyen Du School", "time": "14:00"},
        ),
        hospital,
    )
    assert isinstance(result, EditSet)
    assert result.edits[0].zone == "B"
    assert result.edits[0].time == 5400
    assert result.edits[1].minutes == 12
    assert result.edits[2] == Deadline(stop="SC", time=3600)


def test_parse_keeps_deadline_and_open_bounds(hospital):
    """Parsing resolves names and clocks but does not rewrite ops: that is canonical()'s job."""
    result = parse_editset(
        raw({"op": "deadline", "stop": "An Binh Hospital", "time": "15:00"}), hospital
    )
    assert result == EditSet(edits=[Deadline(stop="HO", time=7200)])
    result = parse_editset(raw(window("An Binh Hospital", None, "15:00")), hospital)
    assert result.edits[0] == SetTimeWindow(stop="HO", start=None, end=7200)


def test_times_keep_departure_seconds(mini):
    # mini departs 09:02:10 local, so 11:00 is 1:57:50 after departure.
    name = mini.stops[mini.remaining[0]].name
    result = parse_editset(raw({"op": "deadline", "stop": name, "time": "11:00"}), mini)
    assert result.edits[0].time == 7070


def test_zone_matches_after_normalization(mini):
    zone = mini.stops[mini.remaining[0]].zone_id  # "A-2.2A"-style id
    result = parse_editset(
        raw({"op": "avoid_zone_until", "zone": f"  {zone.lower()} ", "time": "12:00"}), mini
    )
    assert isinstance(result, EditSet)
    assert result.edits[0].zone == zone


def test_confidence_bounds(hospital):
    edit = {"op": "remove_stop", "stop": "Thanh Cong Shop"}
    assert parse_editset(raw(edit, confidence=0), hospital).confidence == 0
    assert parse_editset(raw(edit, confidence=100), hospital).confidence == 100
    assert error_code(parse_editset(raw(edit, confidence=101), hospital)) == "schema"


# --- one test per reason code (spec 06 §4) -------------------------------------------------------


@pytest.mark.parametrize(
    "text",
    [
        "",
        "not json",
        '{"edits": [',
        '```json\n{"edits": [{"op": "remove_stop", "stop": "Thanh Cong Shop"}]}\n```',
    ],
    ids=["empty", "prose", "truncated", "code_fence"],
)
def test_parse_error_invalid_json(hospital, text):
    """Output that is not pure JSON is rejected, never repaired (CLAUDE.md)."""
    assert error_code(parse_editset(text, hospital)) == "invalid_json"


@pytest.mark.parametrize(
    "body",
    [
        [],
        {"edits": []},
        {"edits": [{"op": "remove_stop", "stop": "Thanh Cong Shop"}] * 5},
        {"edits": [{"op": "teleport", "stop": "Thanh Cong Shop"}]},
        {"edits": [{"stop": "Thanh Cong Shop"}]},
        {"edits": [{"op": "remove_stop"}]},
        {"edits": [{"op": "remove_stop", "stop": "Thanh Cong Shop", "why": "closed"}]},
        {"edits": [{"op": "remove_stop", "stop": "Thanh Cong Shop"}], "note": "x"},
        {"edits": [{"op": "remove_stop", "stop": 3}]},
        {"edits": [window("An Binh Hospital", "25:00", None)]},
        {"edits": [window("An Binh Hospital", None, None)]},
        {
            "edits": [
                {"op": "precedence", "before": "An Binh Hospital", "after": "an binh hospital"}
            ]
        },
        {"edits": [{"op": "service_time", "stop": "An Binh Hospital", "minutes": -5}]},
        {"edits": [{"op": "service_time", "stop": "An Binh Hospital", "minutes": 7.5}]},
        {"edits": [{"op": "remove_stop", "stop": "Thanh Cong Shop"}], "confidence": "high"},
    ],
    ids=[
        "not_object",
        "no_edits",
        "too_many_edits",
        "unknown_op",
        "missing_op",
        "missing_field",
        "extra_field",
        "extra_top_level",
        "stop_not_string",
        "bad_clock",
        "window_without_bounds",
        "self_precedence",
        "negative_minutes",
        "fractional_minutes",
        "bad_confidence",
    ],
)
def test_parse_error_schema(hospital, body):
    assert error_code(parse_editset(json.dumps(body), hospital)) == "schema"


@pytest.mark.parametrize(
    "edit",
    [
        {"op": "remove_stop", "stop": "Binh Hospital"},
        {"op": "remove_stop", "stop": "Depot"},
        {"op": "precedence", "before": "An Binh Hospital", "after": "Nowhere Shop"},
    ],
)
def test_parse_error_unknown_stop(hospital, edit):
    result = parse_editset(raw(edit), hospital)
    assert error_code(result) == "unknown_stop"


@pytest.mark.parametrize("zone", ["C", "A-2", ""])
def test_parse_error_unknown_zone(hospital, zone):
    edit = {"op": "avoid_zone_until", "zone": zone, "time": "15:00"}
    assert error_code(parse_editset(raw(edit), hospital)) == "unknown_zone"


def test_unknown_zone_only_counts_remaining_stops(mini):
    remaining_zones = {mini.stops[s].zone_id for s in mini.remaining}
    done_only = {mini.stops[s].zone_id for s in mini.done} - remaining_zones
    assert done_only, "fixture should have a zone that only done stops use"
    edit = {"op": "avoid_zone_until", "zone": done_only.pop(), "time": "12:00"}
    assert error_code(parse_editset(raw(edit), mini)) == "unknown_zone"


@pytest.mark.parametrize("which", ["first_done", "current_stop"])
def test_parse_error_done_stop(mini, which):
    stop = mini.done[0] if which == "first_done" else mini.current_stop
    edit = {"op": "remove_stop", "stop": mini.stops[stop].name.upper()}
    assert error_code(parse_editset(raw(edit), mini)) == "done_stop"


@pytest.mark.parametrize(
    "edit",
    [
        window("An Binh Hospital", "16:00", "15:00"),
        window("An Binh Hospital", None, "12:30"),
        window("An Binh Hospital", "03:00", None),  # "3" read as 3 am, before now
        {"op": "deadline", "stop": "An Binh Hospital", "time": "12:59"},
        {"op": "driver_end_time", "time": "11:00"},
        {"op": "avoid_zone_until", "zone": "A", "time": "09:00"},
    ],
    ids=[
        "start_after_end",
        "end_before_now",
        "start_before_now",
        "deadline",
        "driver_end",
        "avoid_zone",
    ],
)
def test_parse_error_bad_interval(hospital, edit):
    assert error_code(parse_editset(raw(edit), hospital)) == "bad_interval"


def test_current_minute_is_not_in_the_past(mini):
    # t_now is in the middle of a minute: that minute itself is still "now".
    now = clock_str(mini, mini.t_now)
    name = mini.stops[mini.remaining[0]].name
    assert isinstance(parse_editset(raw(window(name, now, None)), mini), EditSet)
    hours, minutes = map(int, now.split(":"))
    before = f"{(hours * 60 + minutes - 1) // 60:02d}:{(hours * 60 + minutes - 1) % 60:02d}"
    assert error_code(parse_editset(raw(window(name, before, None)), mini)) == "bad_interval"


def test_point_window_is_allowed(hospital):
    result = parse_editset(raw(window("An Binh Hospital", "15:00", "15:00")), hospital)
    assert result.edits[0] == SetTimeWindow(stop="HO", start=7200, end=7200)


def test_first_error_wins(hospital):
    result = parse_editset(
        raw(
            {"op": "remove_stop", "stop": "Nowhere"},
            {"op": "avoid_zone_until", "zone": "Z", "time": "15:00"},
        ),
        hospital,
    )
    assert error_code(result) == "unknown_stop"
    assert "Nowhere" in result.detail


# --- Review Focus #1 and #2 ----------------------------------------------------------------------


def test_stop_name_normalized(hospital):
    result = parse_editset(raw({"op": "remove_stop", "stop": " an binh HOSPITAL "}), hospital)
    assert result == EditSet(edits=[RemoveStop(stop="HO")])
    result = parse_editset(raw({"op": "remove_stop", "stop": "An  Binh\tHospital"}), hospital)
    assert result == EditSet(edits=[RemoveStop(stop="HO")])
    assert (
        error_code(parse_editset(raw({"op": "remove_stop", "stop": "Binh Hospital"}), hospital))
        == "unknown_stop"
    )


@pytest.mark.parametrize(
    "text", ["15:00", "3:00 PM", "3 pm", "3pm", "3:00pm", " 15:00 ", "3 P.M.", "03:00 pm"]
)
def test_time_formats(hospital, text):
    result = parse_editset(raw(window("An Binh Hospital", text, None)), hospital)
    assert isinstance(result, EditSet), result
    assert result.edits[0].start == 2 * 3600


@pytest.mark.parametrize(
    ("text", "seconds"),
    [("12 pm", -3600), ("12:30 PM", -1800), ("1 pm", 0), ("11:59 pm", 10 * 3600 + 59 * 60)],
)
def test_twelve_hour_edges(hospital, text, seconds):
    # The hospital snapshot departs at 13:00, so noon is in the past.
    edit = window("An Binh Hospital", None, text)
    result = parse_editset(raw(edit), hospital)
    if seconds < 0:
        assert error_code(result) == "bad_interval"
    else:
        assert result.edits[0].end == seconds


@pytest.mark.parametrize(
    "text", ["15h", "afternoon", "3", "15", "13 pm", "0 am", "3:0", "15:00:00", "noon", "3 p m"]
)
def test_time_formats_rejected(hospital, text):
    result = parse_editset(raw(window("An Binh Hospital", text, None)), hospital)
    assert error_code(result) == "schema"


def test_parse_clock():
    assert parse_clock("afternoon") is None
    assert parse_clock("12 am") == "00:00"
    assert parse_clock("12:15 AM") == "00:15"
    assert parse_clock("9:05") == "09:05"


# --- schema exposed to the LLM -------------------------------------------------------------------


def test_json_schema_lists_every_op():
    schema = editset_json_schema()
    text = json.dumps(schema)
    for op in OPS:
        assert f'"{op}"' in text
    assert schema["type"] == "object"
    assert set(schema["properties"]) == {"edits", "confidence"}
    assert schema["required"] == ["edits"]
    assert schema.get("additionalProperties") is False


def test_json_schema_is_valid_json_and_stable():
    assert json.dumps(editset_json_schema(), sort_keys=True) == json.dumps(
        editset_json_schema(), sort_keys=True
    )
