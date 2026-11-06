"""Compact text view of a snapshot, shared by LLM prompts and human review (spec 05 §6)."""

from kwd.data.models import RouteSnapshot
from kwd.data.snapshot import baseline_arrivals, clock_str

MISSING = "-"


def render_snapshot(p: RouteSnapshot) -> str:
    """Header lines plus one row per remaining stop, without coordinates or LMRC stop ids."""
    lines = [
        f"Current time: {clock_str(p, p.t_now)}",
        f"Vehicle at: {p.stops[p.current_stop].name}",
        f"Shift ends: {clock_str(p, p.shift_end)}",
        "#|Stop|Category|Zone|ETA|Window",
    ]
    for position, (stop_id, arrival) in enumerate(baseline_arrivals(p).items(), start=1):
        stop = p.stops[stop_id]
        window = MISSING
        if stop.tw is not None:
            window = f"{clock_str(p, stop.tw[0])}-{clock_str(p, stop.tw[1])}"
        zone = MISSING if stop.zone_id is None else stop.zone_id
        eta = clock_str(p, arrival)
        lines.append(f"{position}|{stop.name}|{stop.category}|{zone}|{eta}|{window}")
    return "\n".join(lines)
