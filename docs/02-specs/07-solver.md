# 07 · Solver: Re-optimize a Snapshot Under Edits

> Status: Draft v0.2 · Updated 2026-11-06 · v0.2: `Plan` times come from one shared walk `schedule()`; `digest()` hashes order **and** service-start times (§5, decided 06/11).

## 1. Purpose

`solve(P, E) -> Plan | Infeasible`: re-sequence the **remaining** stops of snapshot `P` subject to edit set `E`, starting from the vehicle's position at `t_now`, staying close to the current plan. Used for `P̂` (LLM edit), `P*` (gold edit) and for probes (spec 11).

## 2. Model

Single-vehicle TSPTW with OR-Tools routing:

- **Nodes**: current vehicle position (start), remaining stops, depot (end).
- **Time dimension**: transit = travel + service at origin; slack allowed (waiting).
- **Constraints from edits** (all **hard**):
  - `set_time_window` → `CumulVar(stop).SetRange(a, b)`.
  - `remove_stop` → node not in model.
  - `precedence(i, j)` → `CumulVar(i) + service(i) ≤ CumulVar(j)` and same-route.
  - `driver_end_time(t)` → end node cumul `≤ t`.
  - `avoid_zone_until(z, t)` → each stop in `z`: cumul `≥ t`.
  - `service_time(s, m)` → change service at `s` before building transit callback.
- **Original LMRC time windows**: the **end** is **soft**, penalty per minute late (`late_penalty`, default 10/min), since real data can be internally inconsistent. The **start** is a lower bound on service start (`CumulVar(stop).SetMin(tw_start)`): the vehicle waits, exactly as in the baseline walk of spec 05 §4 and in `schedule()` (§5). A lower bound alone never makes a route infeasible.
- **Shift end** is soft (penalty) unless a `driver_end_time` edit makes it hard.

## 3. Objective

```
cost = travel_minutes + late_penalty · lateness_minutes + dev_weight · deviation
```

- `deviation` = number of remaining stops whose position changes vs the current plan, approximated in OR-Tools by a per-arc penalty for arcs not in the current plan (`dev_weight`, default 2 min per changed arc). Purpose: avoid reshuffling the whole route for a small request.
- Reported metrics are computed **outside** the solver from the final sequence (spec 09), not from the solver's internal objective.

## 4. Search and determinism

- Warm start: `ReadAssignmentFromRoutes([current remaining order])`. If the warm start violates new hard constraints, fall back to first-solution strategy `PATH_CHEAPEST_ARC`.
- Local search: `GUIDED_LOCAL_SEARCH`, **fixed time limit** (`time_limit_s`, default 3 s) **and** a solution limit, single worker. Same input ⇒ same output on the same machine; tested.
- If the solver returns no solution within the limit ⇒ `Infeasible(reason="no_solution")`. A quick pre-check catches obviously infeasible edits (e.g. window ends before `t_now`).

## 5. Output

```python
class Plan(BaseModel):
    sequence: list[str]          # remaining stop_ids, in order
    arrival: dict[str, int]      # seconds since departure; time the vehicle reaches the stop, before any wait (as spec 05 §4)
    service_start: dict[str, int]  # seconds since departure; after any wait. Edit constraints and harm R1 are checked on this
    end_time: int                # return to depot
    travel_min: float
    lateness_min: float          # vs original LMRC windows
    changed_positions: int       # vs current plan
    solve_status: str
    solve_time_s: float

class Infeasible(BaseModel):
    reason: str
```

**Times are never read from OR-Tools.** With slack allowed, cumul values are not unique, so two equal plans could get different times. All times in `Plan` come from one shared walk:

`schedule(p, sequence, e) -> (arrival, service_start, end_time)`: leave `current_stop` at `t_now`, drive `sequence` with `travel(p)` (spec 05 §4); `service_start = max(arrival, original tw_start, hard lower bounds of e)` where the hard lower bounds are the `start` of `set_time_window` and the `time` of `avoid_zone_until`; service durations include `service_time` edits; `end_time` = return to depot. `solve` returns `schedule(p, best_sequence, e)`; `current_plan(p) = schedule(p, p.remaining, None)`. With no edit this reproduces `baseline_arrivals` (spec 05) exactly.

The walk serves every stop as early as allowed, so for a fixed order it gives the earliest feasible times; if OR-Tools found the order feasible, this schedule meets every hard upper bound too.

`Plan.digest()` = hash of (`sequence`, `service_start` of each stop rounded to the nearest minute, `end_time` rounded to the nearest minute). Decided 2026-11-06: an edit that keeps the order but makes the vehicle wait (e.g. a later window start on a stop) **changes the plan** and the digest. Used for "plan unchanged" in signals (spec 11 S3, S4), `gold_binding` (spec 08 §2) and `nonbinding_error` (spec 09 §4), so the paper's definition "$\hat{P} = P$" holds literally.

## 6. Performance budget

~3,150 items (main + human) × 2 translators × (1 greedy + k samples + probes) solves, plus `P*` and the V1 re-solves. With k = 4 and ~4 counter-readings ⇒ ~9 solves per item per translator ⇒ ~57k solves × ≤3 s (≈ 48 CPU-hours before caching). Must run in parallel (process pool) and **cache by hash(snapshot_id, canonical EditSet, solver config)**: many samples are identical after canonicalization.

## 7. Acceptance criteria

- [ ] `solve(P, ∅)` returns the current plan (or one with cost ≤ it) for 20 test snapshots.
- [ ] Each edit op has a unit test showing the constraint holds in the returned plan.
- [ ] Hospital example: gold `[15:00, end]` moves the hospital after 15:00; wrong `[start, 15:00]` returns the **unchanged** plan.
- [ ] Determinism test: 3 runs ⇒ identical digests.
- [ ] `current_plan(p).arrival == baseline_arrivals(p)` on the fixtures and 20 real snapshots.
- [ ] Wait-only change: same order, `set_time_window` start later than the stop's current service start ⇒ digest differs from `current_plan`; start earlier than it ⇒ digest equal.
- [ ] Median solve time ≤ 3 s on 150 remaining stops.
