# 05 · Data: LMRC → Route Snapshots

> Status: Draft v0.1 · Updated 2026-11-06
> Source: Amazon Last Mile Routing Research Challenge 2021 (Merchán et al., 2022, ref P20). License CC BY-NC 4.0.
> File and field names below were **checked against the live files on 2026-11-05** (first bytes of each file). Remaining checks after the full download: `scripts/inspect_lmrc.py`.

## 1. Purpose

Turn real LMRC routes into **in-service snapshots** `P`: a route that is partly delivered, with the remaining stops still to be sequenced. Every benchmark item (spec 08) is built on one snapshot.

## 2. Raw data

- Location: AWS Open Data, bucket `s3://amazon-last-mile-challenges/almrrc2021/`, also served over public HTTPS (`https://amazon-last-mile-challenges.s3.amazonaws.com/...`). Download with `scripts/download_lmrc.sh` (plain `curl`, resumable; no AWS CLI).
- Use the **training split** (`almrrc2021-data-training/model_build_inputs/`, 6,112 routes) only. Sizes: `travel_times.json` 1.82 GB, `package_data.json` 375 MB, `route_data.json` 79 MB, `actual_sequences.json` 10 MB (total ≈ 2.3 GB).
- Expected files and fields:

| File | Fields used |
|---|---|
| `route_data.json` | `station_code`, `date_YYYY_MM_DD`, `departure_time_utc`, `route_score`, `stops{id: lat, lng, type, zone_id}` |
| `package_data.json` | per stop, per package: `time_window.start_time_utc`/`end_time_utc`, `planned_service_time_seconds` |
| `travel_times.json` | `travel_times[route][from_stop][to_stop]` in seconds (intra-route only) |
| `actual_sequences.json` | `actual[stop] = position` (driver's real order) |
| `invalid_sequence_scores.json` | not used |

Verified formats and gotchas:

- Route keys look like `RouteID_<uuid>`; stop keys are 2-letter codes (`"AD"`); one stop per route has `type = "Station"` (depot), the rest `"Dropoff"`.
- `departure_time_utc` is `"HH:MM:SS"`, the date is in `date_YYYY_MM_DD`. Time windows are strings `"YYYY-MM-DD HH:MM:SS"` (UTC) or **`NaN`** when absent.
- **`package_data.json` and `route_data.json` contain bare `NaN` tokens (invalid JSON).** In `route_data.json` the token is `zone_id`: on every depot and on 6,515 drop-offs. Python's `json` accepts the token but returns `float('nan')`, not `None`, so read with `json.load(f, parse_constant=lambda _: None)`. Streaming parsers (`ijson`) reject it: use `NanToNullReader` from `kwd.data.jsonstream`. Checked 2026-11-06 on the full files: every `NaN` is a bare value (never inside a string), none of the four files contains `null`, and `travel_times.json` and `actual_sequences.json` contain no `NaN`.
- Travel times are in **seconds**, intra-route only, floats with one decimal. The diagonal is `0.0`, and `0.0` also occurs off the diagonal (7,722 cells over all routes, including consecutive stops of the actual sequence), so a zero is a valid travel time, not a missing value.
- The depot is present in `package_data.json` with an empty dict (`"VE": {}`). One stop can hold both packages with a real time window and packages with `NaN`.
- `scan_status` takes the values `DELIVERED`, `DELIVERY_ATTEMPTED` and `REJECTED`. It is not used and routes are not filtered on it.
- **Memory:** never `json.load` `travel_times.json` (1.8 GB ⇒ > 10 GB RAM; the machine has ~15 GB total). Stream it once with `ijson.kvitems` and write one compact file per selected route.

## 3. Route selection

Verified facts (2026-11-05, `scripts/inspect_lmrc.py`): 6,112 routes; `route_score` High 2,718 / Medium 3,292 / Low 102; 148 stops per route on average (p10 105, p90 186); exactly one `Station` per route, at position 0 of the actual sequence; ~6% of stops have a time window (median 4% per route), and many windows are wide (e.g. 16:00–00:00 UTC, the whole shift), so they rarely bind; service ≈ 107 s per stop; legs ≈ 6 min. Checked 2026-11-06 on the full files: the travel matrices of all 6,112 routes are complete, and all actual sequences are consistent with their stops. **2,571 routes pass the filter below** (the matrix condition removes none), far more than the ~370 needed (main + human + pilot). Largest station DLA7 (444), smallest DBO1 (20).


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
4. **Stop service time** = sum of `planned_service_time_seconds` over the stop's packages, rounded to whole seconds.
5. **Stop time window** = intersection of its packages' windows, if any (most stops have none).
6. **Shift end** = baseline return-to-depot time + 60 min (LMRC has no driver shifts). Configurable.
7. **Local clock**: convert UTC → station local time zone. Verified 2026-11-05: 17 stations in 5 cities; map by the 2 letters after `D`:

   | Prefix | City | Stations (routes) | Time zone |
   |---|---|---|---|
   | `DAU` | Austin | DAU1 (214) | `America/Chicago` |
   | `DBO` | Boston | DBO1–3 (929) | `America/New_York` |
   | `DCH` | Chicago | DCH1–4 (1,002) | `America/Chicago` |
   | `DLA` | Los Angeles | DLA3, 4, 5, 7, 8, 9 (2,888) | `America/Los_Angeles` |
   | `DSE` | Seattle | DSE2, 4, 5 (1,079) | `America/Los_Angeles` |

   Example: departure `2018-07-27 16:02:10 UTC` at DLA3 = 09:02 local.
8. **Display names**: LMRC stop IDs are opaque. Assign each remaining stop a synthetic, unique **name + category** (e.g. `"Mercy Hospital"`, category `hospital`), drawn with a seeded generator from a fixed list of ~10 categories (residence, office, pharmacy, hospital, school, restaurant, shop, warehouse, clinic, gym). Categories give the benchmark realistic indirect references ("the hospital", "the pharmacy on the north side").

## 5. Data model

```python
class Stop(BaseModel):
    stop_id: str            # LMRC id
    name: str               # synthetic display name, unique within route
    category: str
    zone_id: str | None
    lat: float; lng: float
    service_s: int          # seconds
    tw: tuple[int, int] | None   # seconds since departure; None = no window

class RouteSnapshot(BaseModel):
    snapshot_id: str        # f"{route_id}@{t_now}"
    route_id: str
    station_code: str
    tz: str
    departure_local: str    # "HH:MM", for rendering
    t_now: int              # seconds since departure
    current_stop: str       # vehicle position at t_now
    done: list[str]         # frozen prefix
    remaining: list[str]    # current planned order (= actual order)
    stops: dict[str, Stop]
    depot_id: str
    shift_end: int
    travel_path: str        # path to cached per-route travel-time matrix (seconds, float)
```

Storage: one JSONL file `data/interim/snapshots.jsonl`; travel matrices as `.npy` per route.

## 6. Rendering for humans / LLMs

`render_snapshot(P) -> str` produces a compact table of **remaining** stops: order, name, category, zone, ETA (`HH:MM`), time window if any; plus header lines `Current time`, `Vehicle at`, `Shift ends`. The same renderer is used in prompts (spec 10) and the review UI (spec 08). Keep it under ~4k tokens for 150 stops; drop lat/lng.

## 7. Acceptance criteria

- [ ] `kwd snapshot --config configs/data.yaml` produces snapshots for the selected routes, deterministically (same hash across two runs).
- [ ] Baseline arrival times are monotone; recomputed ETA of the last stop matches the walk within 1 min.
- [ ] Every snapshot has ≥ 30 remaining stops and unique display names.
- [ ] Stats script prints: #routes, stops per route (mean/p10/p90), % stops with time windows (expect ≈ low, consistent with P20 Table 2).
