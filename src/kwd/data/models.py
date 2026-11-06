"""Data models shared across the pipeline (spec 05 §5)."""

from datetime import datetime

from pydantic import BaseModel


class Stop(BaseModel):
    stop_id: str  # LMRC id
    name: str  # synthetic display name, unique within route
    category: str
    zone_id: str | None
    lat: float
    lng: float
    service_s: int  # seconds
    tw: tuple[int, int] | None  # seconds since departure; None = no window


class RouteSnapshot(BaseModel):
    snapshot_id: str  # f"{route_id}@{t_now}"
    route_id: str
    station_code: str
    tz: str
    departure_local: str  # "HH:MM:SS" local time, read through clock_str and clock_to_s
    t_now: int  # seconds since departure
    current_stop: str  # vehicle position at t_now
    done: list[str]  # frozen prefix
    remaining: list[str]  # current planned order (= actual order)
    stops: dict[str, Stop]
    depot_id: str
    shift_end: int
    travel_path: str  # path to cached per-route travel-time matrix (seconds, float)
    node_ids: list[str]  # row/column order of the travel-time matrix


class RawRoute(BaseModel):
    """One LMRC route as read from the raw files, with `NaN` already turned into None."""

    route_id: str
    station_code: str
    departure_utc: datetime  # timezone-aware, UTC
    stops: dict  # raw route_data stops
    packages: dict  # raw package_data entries; the depot maps to {}
    travel_s: dict[str, dict[str, float]]
    actual_order: list[str]  # sorted by position; element 0 is the depot
    route_score: str
