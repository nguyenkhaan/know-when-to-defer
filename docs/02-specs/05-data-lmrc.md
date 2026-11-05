# 05 · Data: LMRC → Route Snapshots

> Status: Draft v0.1 · Updated 2026-11-05
> Source: Amazon Last Mile Routing Research Challenge 2021 (Merchán et al., 2022, ref P20). License CC BY-NC 4.0.
> ⚠️ File and field names below are from the dataset paper and challenge docs; **verify against the downloaded files** and update this spec if they differ.

## 1. Purpose

Turn real LMRC routes into **in-service snapshots** `P`: a route that is partly delivered, with the remaining stops still to be sequenced. Every benchmark item (spec 08) is built on one snapshot.

## 2. Raw data

- Location: AWS Open Data, bucket `s3://amazon-last-mile-challenges/almrrc2021/` (no credentials needed, `--no-sign-request`).
- Use the **training split** (`model_build_inputs/`, 6,112 routes) only; the evaluation split is not needed.
- Expected files and fields:

| File | Fields used |
|---|---|
| `route_data.json` | `station_code`, `date_YYYY_MM_DD`, `departure_time_utc`, `route_score`, `stops{id: lat, lng, type, zone_id}` |
| `package_data.json` | per stop, per package: `time_window.start_time_utc`/`end_time_utc`, `planned_service_time_seconds` |
| `travel_times.json` | `travel_times[route][from_stop][to_stop]` in seconds (intra-route only) |
| `actual_sequences.json` | `actual[stop] = position` (driver's real order) |

## 3. Route selection

Keep routes that satisfy all of:

- `route_score == "High"` (most realistic sequences);
- 80 ≤ number of stops ≤ 200;
- complete travel-time matrix (no missing pairs).

Sample a fixed list of routes with `seed = 0`, stratified by `station_code`. Target: **~300 routes** for the main benchmark, **~30 routes** for the pilot. Save the list to `data/interim/routes_selected.json`.

## 4. Snapshot construction

For each selected route:

1. **Baseline plan** = the actual sequence. Compute arrival times by walking the sequence: `arrival[i+1] = depart[i] + travel(i, i+1)`, `depart[i] = max(arrival[i], tw_start[i]) + service[i]`.
2. **Pick `t_now`**: the departure time from the stop at position `⌊ρ · n⌋`, with `ρ ~ Uniform(0.2, 0.5)` (seeded). Stops up to that position are **done** (frozen); the vehicle is at that stop.
3. **Remaining stops** (typically 50–150) are the editable part.
4. **Stop service time** = sum of `planned_service_time_seconds` over the stop's packages, rounded to minutes.
5. **Stop time window** = intersection of its packages' windows, if any (most stops have none).
6. **Shift end** = baseline return-to-depot time + 60 min (LMRC has no driver shifts). Configurable.
7. **Local clock**: convert UTC → station local time zone (mapping from station-code city prefix, e.g. `DLA`→`America/Los_Angeles`, `DCH`→`America/Chicago`, `DBO`→`America/New_York`, `DSE`→`America/Los_Angeles`, `DAU`→`America/Chicago`; verify the full list).
8. **Display names**: LMRC stop IDs are opaque. Assign each remaining stop a synthetic, unique **name + category** (e.g. `"Mercy Hospital"`, category `hospital`), drawn with a seeded generator from a fixed list of ~10 categories (residence, office, pharmacy, hospital, school, restaurant, shop, warehouse, clinic, gym). Categories give the benchmark realistic indirect references ("the hospital", "the pharmacy on the north side").

## 5. Data model

```python
class Stop(BaseModel):
    stop_id: str            # LMRC id
    name: str               # synthetic display name, unique within route
    category: str
    zone_id: str | None
    lat: float; lng: float
    service_min: int
    tw: tuple[int, int] | None   # minutes since departure; None = no window

class RouteSnapshot(BaseModel):
    snapshot_id: str        # f"{route_id}@{t_now}"
    route_id: str
    station_code: str
    tz: str
    departure_local: str    # "HH:MM", for rendering
    t_now: int              # minutes since departure
    current_stop: str       # vehicle position at t_now
    done: list[str]         # frozen prefix
    remaining: list[str]    # current planned order (= actual order)
    stops: dict[str, Stop]
    depot_id: str
    shift_end: int
    travel_min: str         # path to cached travel-time matrix (minutes, float)
```

Storage: one JSONL file `data/interim/snapshots.jsonl`; travel matrices as `.npy` per route.

## 6. Rendering for humans / LLMs

`render_snapshot(P) -> str` produces a compact table of **remaining** stops: order, name, category, zone, ETA (`HH:MM`), time window if any; plus header lines `Current time`, `Vehicle at`, `Shift ends`. The same renderer is used in prompts (spec 10) and the review UI (spec 08). Keep it under ~4k tokens for 150 stops; drop lat/lng.

## 7. Acceptance criteria

- [ ] `kwd snapshot --config configs/data.yaml` produces snapshots for the selected routes, deterministically (same hash across two runs).
- [ ] Baseline arrival times are monotone; recomputed ETA of the last stop matches the walk within 1 min.
- [ ] Every snapshot has ≥ 30 remaining stops and unique display names.
- [ ] Stats script prints: #routes, stops per route (mean/p10/p90), % stops with time windows (expect ≈ low, consistent with P20 Table 2).
