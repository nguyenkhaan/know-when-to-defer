import json
import random

import pytest

from kwd.data.models import RouteSnapshot
from kwd.data.snapshot import clock_str, clock_to_s
from kwd.dsl import (
    AvoidZoneUntil,
    Deadline,
    DriverEndTime,
    Edit,
    EditSet,
    Precedence,
    RemoveStop,
    SetTimeWindow,
    canonical,
    dump_editset,
    equivalent,
    op_type,
    parse_editset,
    render_editset_en,
)


def parse(p: RouteSnapshot, *edits: dict) -> EditSet:
    result = parse_editset(json.dumps({"edits": list(edits)}), p)
    assert isinstance(result, EditSet), result
    return result


def at(p: RouteSnapshot, hhmm: str) -> int:
    return clock_to_s(p, hhmm)


# --- canonical form (spec 06 §5) -----------------------------------------------------------------


def test_canonical_fills_open_bounds(hospital):
    late = EditSet(edits=[SetTimeWindow(stop="HO", start=7200, end=None)])
    assert canonical(late, hospital) == (("set_time_window", "HO", 7200, 16200),)
    early = EditSet(edits=[SetTimeWindow(stop="HO", start=None, end=7200)])
    assert canonical(early, hospital) == (("set_time_window", "HO", 0, 7200),)


def test_open_bound_uses_t_now(mini):
    stop = mini.remaining[0]
    e = EditSet(edits=[Deadline(stop=stop, time=mini.t_now + 600)])
    assert canonical(e, mini) == (("set_time_window", stop, mini.t_now, mini.t_now + 600),)


def test_editset_rejects_meaningless_edits():
    with pytest.raises(ValueError, match="bound"):
        SetTimeWindow(stop="HO", start=None, end=None)
    with pytest.raises(ValueError, match="itself"):
        Precedence(before="HO", after="HO")
    with pytest.raises(ValueError):
        EditSet(edits=[])


def test_deadline_equals_window_end(hospital):
    deadline = parse(hospital, {"op": "deadline", "stop": "Green Valley Hospital", "time": "15:00"})
    window = parse(
        hospital,
        {"op": "set_time_window", "stop": "Green Valley Hospital", "start": None, "end": "3 pm"},
    )
    assert canonical(deadline, hospital) == (("set_time_window", "HO", 0, 7200),)
    assert equivalent(deadline, window, hospital)


def test_hospital_wrong_not_equivalent(hospital):
    gold = parse(
        hospital,
        {"op": "set_time_window", "stop": "Green Valley Hospital", "start": "15:00", "end": None},
    )
    wrong = parse(
        hospital,
        {"op": "set_time_window", "stop": "Green Valley Hospital", "start": None, "end": "15:00"},
    )
    assert canonical(gold, hospital) == (("set_time_window", "HO", 7200, 16200),)
    assert canonical(wrong, hospital) == (("set_time_window", "HO", 0, 7200),)
    assert not equivalent(gold, wrong, hospital)
    assert not equivalent(gold, wrong, hospital, tol_min=60)


def test_windows_on_one_stop_are_intersected(hospital):
    e = EditSet(
        edits=[
            SetTimeWindow(stop="HO", start=3600, end=None),
            Deadline(stop="HO", time=9000),
            SetTimeWindow(stop="HO", start=1800, end=12000),
        ]
    )
    assert canonical(e, hospital) == (("set_time_window", "HO", 3600, 9000),)


def test_empty_intersection_is_kept_for_the_solver(hospital):
    """Conflicting windows are not a parse error: the solver reports them Infeasible (1.4)."""
    e = EditSet(
        edits=[SetTimeWindow(stop="HO", start=7200, end=10800), Deadline(stop="HO", time=3600)]
    )
    assert canonical(e, hospital) == (("set_time_window", "HO", 7200, 3600),)


def test_canonical_sorts_and_drops_duplicates(hospital):
    a = EditSet(
        edits=[RemoveStop(stop="SH"), Precedence(before="SC", after="PH"), RemoveStop(stop="SH")]
    )
    b = EditSet(edits=[Precedence(before="SC", after="PH"), RemoveStop(stop="SH")])
    assert canonical(a, hospital) == canonical(b, hospital)
    assert canonical(a, hospital) == (("precedence", "SC", "PH"), ("remove_stop", "SH"))
    assert equivalent(a, b, hospital)


def test_precedence_direction_matters(hospital):
    a = EditSet(edits=[Precedence(before="SC", after="PH")])
    b = EditSet(edits=[Precedence(before="PH", after="SC")])
    assert not equivalent(a, b, hospital)


def test_canonical_ignores_confidence(hospital):
    a = EditSet(edits=[RemoveStop(stop="SH")], confidence=10)
    b = EditSet(edits=[RemoveStop(stop="SH")], confidence=None)
    assert equivalent(a, b, hospital)


def test_canonical_is_hashable(hospital):
    e = EditSet(edits=[AvoidZoneUntil(zone="B", time=3600), DriverEndTime(time=14400)])
    assert hash(canonical(e, hospital)) == hash(canonical(e, hospital))


@pytest.mark.parametrize(
    ("delta", "tol", "expected"),
    [
        (60, 0, False),
        (60, 1, True),
        (120, 1, False),
        (-60, 1, True),
        (0, 0, True),
    ],
)
def test_equivalent_time_tolerance(hospital, delta, tol, expected):
    a = EditSet(edits=[Deadline(stop="HO", time=7200), DriverEndTime(time=14400)])
    b = EditSet(edits=[Deadline(stop="HO", time=7200 + delta), DriverEndTime(time=14400)])
    assert equivalent(a, b, hospital, tol_min=tol) is expected


def test_tolerance_never_matches_different_stops_or_ops(hospital):
    a = EditSet(edits=[Deadline(stop="HO", time=7200)])
    assert not equivalent(a, EditSet(edits=[Deadline(stop="SC", time=7200)]), hospital, 60)
    assert not equivalent(a, EditSet(edits=[DriverEndTime(time=7200)]), hospital, 60)
    two = EditSet(edits=[Deadline(stop="HO", time=7200), RemoveStop(stop="SH")])
    assert not equivalent(a, two, hospital, 60)


# --- op_type (spec 06 §5.1) ----------------------------------------------------------------------


def test_op_type_deadline_canonical(hospital):
    assert op_type(EditSet(edits=[Deadline(stop="HO", time=7200)]), hospital) == "set_time_window"


def test_op_type_compound(hospital):
    two_windows = EditSet(edits=[Deadline(stop="HO", time=7200), Deadline(stop="SC", time=7200)])
    assert op_type(two_windows, hospital) == "compound"
    assert op_type(EditSet(edits=[RemoveStop(stop="SH")]), hospital) == "remove_stop"
    mixed = EditSet(edits=[RemoveStop(stop="SH"), DriverEndTime(time=14400)])
    assert op_type(mixed, hospital) == "compound"


def test_op_type_counts_canonical_ops(hospital):
    """A deadline and a window on the same stop merge into one op; so do exact duplicates."""
    merged = EditSet(
        edits=[Deadline(stop="HO", time=9000), SetTimeWindow(stop="HO", start=3600, end=None)]
    )
    assert op_type(merged, hospital) == "set_time_window"
    twice = EditSet(edits=[RemoveStop(stop="SH"), RemoveStop(stop="SH")])
    assert op_type(twice, hospital) == "remove_stop"


@pytest.mark.parametrize(
    ("edit", "expected"),
    [
        (SetTimeWindow(stop="HO", start=7200, end=None), "set_time_window"),
        (RemoveStop(stop="HO"), "remove_stop"),
        (Precedence(before="HO", after="SC"), "precedence"),
        (DriverEndTime(time=14400), "driver_end_time"),
        (AvoidZoneUntil(zone="A", time=7200), "avoid_zone_until"),
        (Deadline(stop="HO", time=7200), "set_time_window"),
    ],
)
def test_op_type_single(hospital, edit, expected):
    assert op_type(EditSet(edits=[edit]), hospital) == expected


# --- English rendering --------------------------------------------------------------------------


def test_render_hospital_gold(hospital):
    e = EditSet(edits=[SetTimeWindow(stop="HO", start=7200, end=None)])
    assert (
        render_editset_en(e, hospital) == "Deliver to Green Valley Hospital no earlier than 15:00."
    )


@pytest.mark.parametrize(
    ("edit", "sentence"),
    [
        (
            SetTimeWindow(stop="HO", start=None, end=7200),
            "Deliver to Green Valley Hospital no later than 15:00.",
        ),
        (
            SetTimeWindow(stop="SC", start=3600, end=7200),
            "Deliver to Lincoln School between 14:00 and 15:00.",
        ),
        (Deadline(stop="PH", time=1800), "Deliver to Cedar Pharmacy by 13:30."),
        (RemoveStop(stop="SH"), "Do not visit Harbor Shop."),
        (Precedence(before="SC", after="PH"), "Visit Lincoln School before Cedar Pharmacy."),
        (DriverEndTime(time=14400), "Return to the depot by 17:00."),
        (AvoidZoneUntil(zone="B", time=5400), "Do not serve any stop in zone B before 14:30."),
    ],
)
def test_render_every_op(hospital, edit, sentence):
    assert render_editset_en(EditSet(edits=[edit]), hospital) == sentence


def test_render_keeps_written_order(hospital):
    e = EditSet(edits=[RemoveStop(stop="SH"), Precedence(before="SC", after="PH")])
    assert render_editset_en(e, hospital) == (
        "Do not visit Harbor Shop.\nVisit Lincoln School before Cedar Pharmacy."
    )


# --- round trip (spec 06 §7) ---------------------------------------------------------------------


def _minute_times(p: RouteSnapshot) -> list[int]:
    """Whole local minutes from the current minute to the shift end (or the end of the day)."""
    first = at(p, clock_str(p, p.t_now))
    last = min(p.shift_end, at(p, "23:59"))
    return list(range(first, last + 1, 60))


def random_edit(rng: random.Random, p: RouteSnapshot) -> Edit:
    times = _minute_times(p)
    stop = rng.choice(p.remaining)
    zones = sorted({p.stops[s].zone_id for s in p.remaining if p.stops[s].zone_id is not None})
    op = rng.choice(
        [
            "set_time_window",
            "remove_stop",
            "precedence",
            "driver_end_time",
            "avoid_zone_until",
            "deadline",
        ]
    )
    if op == "set_time_window":
        start, end = sorted(rng.sample(times, 2))
        bounds = rng.choice([(start, end), (start, None), (None, end)])
        return SetTimeWindow(stop=stop, start=bounds[0], end=bounds[1])
    if op == "remove_stop":
        return RemoveStop(stop=stop)
    if op == "precedence":
        before, after = rng.sample(p.remaining, 2)
        return Precedence(before=before, after=after)
    if op == "driver_end_time":
        return DriverEndTime(time=rng.choice(times))
    if op == "avoid_zone_until":
        return AvoidZoneUntil(zone=rng.choice(zones), time=rng.choice(times))
    return Deadline(stop=stop, time=rng.choice(times))


def random_editset(rng: random.Random, p: RouteSnapshot) -> EditSet:
    edits = [random_edit(rng, p) for _ in range(rng.randint(1, 4))]
    return EditSet(edits=edits, confidence=rng.choice([None, rng.randint(0, 100)]))


@pytest.mark.parametrize("snapshot", ["hospital", "mini"])
def test_roundtrip(request, snapshot):
    p = request.getfixturevalue(snapshot)
    rng = random.Random(0)
    for _ in range(1000):
        e = random_editset(rng, p)
        text = dump_editset(e, p)
        parsed = parse_editset(text, p)
        assert isinstance(parsed, EditSet), (text, parsed)
        assert parsed == e, text
        assert equivalent(parsed, e, p)


def test_dump_uses_names_and_local_clock(hospital):
    e = EditSet(edits=[SetTimeWindow(stop="HO", start=7200, end=None)], confidence=80)
    assert json.loads(dump_editset(e, hospital)) == {
        "edits": [
            {
                "op": "set_time_window",
                "stop": "Green Valley Hospital",
                "start": "15:00",
                "end": None,
            }
        ],
        "confidence": 80,
    }


def test_minute_times_cover_the_shift(hospital):
    times = _minute_times(hospital)
    assert times[0] == 0 and times[-1] == hospital.shift_end
    assert len(times) == 16200 // 60 + 1
