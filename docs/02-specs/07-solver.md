# 07 · Solver: Re-optimize a Snapshot Under Edits

> Status: Draft v0.5 · Updated 2026-11-07 · v0.5: `check_constraints` amounts per op (§5); `changed_positions` defined; sanity test compares the solver objective; `warm_start` switch for V1. · v0.4: search stops on `solution_limit` (deterministic; time limit is only a safety cap); `Infeasible` reasons `precheck` / `no_solution`; shift overtime in the objective and in `Plan`; harm cost uses its own unit weights (spec 09 §2). · v0.3: `service_time` op dropped (spec 06 §3); service durations come only from the snapshot. · v0.2: `Plan` times come from one shared walk `schedule()`; `digest()` hashes order **and** service-start times (§5, decided 06/11); `is_fixed_point` for the benchmark filter (spec 08 §2.1).

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
- **Original LMRC time windows**: the **end** is **soft**, penalty per minute late (`late_penalty`, default 10/min), since real data can be internally inconsistent. The **start** is a lower bound on service start (`CumulVar(stop).SetMin(tw_start)`): the vehicle waits, exactly as in the baseline walk of spec 05 §4 and in `schedule()` (§5). A lower bound alone never makes a route infeasible.
- **Shift end** is soft (penalty per minute of overtime, `shift_penalty`, default 10/min) unless a `driver_end_time` edit makes it hard.

## 3. Objective

```
objective = travel_minutes + late_penalty · lateness_minutes + shift_penalty · overtime_minutes + dev_weight · deviation
```

- `deviation` = number of remaining stops whose position changes vs the current plan, approximated in OR-Tools by a per-arc penalty for arcs not in the current plan (`dev_weight`, default 2 min per changed arc). Purpose: avoid reshuffling the whole route for a small request.
- These weights steer the search only. Harm uses its own `cost` in plain minutes (travel + lateness + overtime, weight 1; spec 09 §2), computed **outside** the solver from `schedule()` times, never from the solver's internal objective.

## 4. Search and determinism

- Warm start (`warm_start=True`, default): `ReadAssignmentFromRoutes([current remaining order])`. If the warm start violates new hard constraints, fall back to the first-solution strategy (`first_solution`, default `PATH_CHEAPEST_ARC`). V1 sets `warm_start=False` so that the other strategy is actually used.
- Local search: `GUIDED_LOCAL_SEARCH`, single worker. The **binding stop is `solution_limit`** (number of solutions explored; its value is set in `configs/solver.yaml` during Task 1.4 so that the median solve on 150 remaining stops takes ≤ 3 s). `time_limit_s` (default 10 s) is only a safety cap. With no wall-clock stop, the same input gives the same output on the same machine, also under parallel load; tested.
- `Plan.solve_status` records which limit stopped the search. Solves stopped by the time cap are logged; their share must be 0 on the main run (otherwise raise `time_limit_s`) and is reported with V1.
- `Infeasible.reason` is one of:
  - `precheck`: the canonical edit (spec 06 §5) is infeasible before any search: an empty window (`start > end` after merging), a precedence cycle, a window or deadline ending before the earliest possible arrival (direct leg from `current_stop`), a `driver_end_time` before the direct return to the depot, or a precedence on a removed stop;
  - `no_solution`: the search found no plan meeting the hard constraints within the limits.
  Both give `x = 0` (non-executable, deferred) and count in the infeasible rate of T1. The `no_solution` share is kept in `runs/` (per model) and, for gold edits, in the benchmark README (resamples, spec 08 §3).

## 5. Output

```python
class Plan(BaseModel):
    sequence: list[str]          # remaining stop_ids, in order
    arrival: dict[str, int]      # seconds since departure; time the vehicle reaches the stop, before any wait (as spec 05 §4)
    service_start: dict[str, int]  # seconds since departure; after any wait. Edit constraints and harm R1 are checked on this
    end_time: int                # return to depot
    travel_min: float
    lateness_min: float          # vs original LMRC windows, from service_start
    overtime_min: float          # return to depot past shift_end
    changed_positions: int       # stops whose index differs from their index in P.remaining after dropping the stops this plan removed
    solve_status: str            # which limit stopped the search (solution_limit / time_limit)
    solve_time_s: float

class Infeasible(BaseModel):
    reason: Literal["precheck", "no_solution"]
    detail: str
```

**Times are never read from OR-Tools.** With slack allowed, cumul values are not unique, so two equal plans could get different times. All times in `Plan` come from one shared walk:

`schedule(p, sequence, e) -> (arrival, service_start, end_time)`: leave `current_stop` at `t_now`, drive `sequence` with `travel(p)` (spec 05 §4); `service_start = max(arrival, original tw_start, hard lower bounds of e)` where the hard lower bounds are the `start` of `set_time_window` and the `time` of `avoid_zone_until`; service durations are the snapshot's `service_s`; `end_time` = return to depot. `solve` returns `schedule(p, best_sequence, e)`; `current_plan(p) = schedule(p, p.remaining, None)`. With no edit this reproduces `baseline_arrivals` (spec 05) exactly.

The walk serves every stop as early as allowed, so for a fixed order it gives the earliest feasible times; if OR-Tools found the order feasible, this schedule meets every hard upper bound too.

`Plan.digest()` = hash of (`sequence`, `service_start` of each stop rounded to the nearest minute, `end_time` rounded to the nearest minute). Decided 2026-11-06: an edit that keeps the order but makes the vehicle wait (e.g. a later window start on a stop) **changes the plan** and the digest. Used for "plan unchanged" in signals (spec 11 S3, S4), `gold_binding` (spec 08 §2) and `nonbinding_error` (spec 09 §4), so the paper's definition "$\hat{P} = P$" holds literally.

`is_fixed_point(p, cfg) -> bool` = `solve(p, None, cfg).digest() == current_plan(p).digest()`. Benchmark snapshots must pass it (spec 08 §2.1).

`check_constraints(p, plan, e, tol_min=1) -> list[Violation]`, `Violation(op, stop, amount_min)`: one entry per canonical op of `e` (spec 06 §5) whose amount exceeds `tol_min`. Amounts in minutes, from `service_start` (`ss`) and `end_time`, computed without OR-Tools:

| Canonical op | Amount (≤ 0 = satisfied) |
|---|---|
| `set_time_window(s, [a, b])` | `max(a − ss_s, ss_s − b)` |
| `precedence(i, j)` | `ss_i + service_i − ss_j` |
| `driver_end_time(t)` | `end_time − t` |
| `avoid_zone_until(z, t)` | max over the stops of `z` in the plan of `t − ss_s` |
| `remove_stop(s)` | `+∞` if `s` is still in the plan, else 0 |

A constraint on a stop the plan does not visit is skipped: a missing stop is caught by harm rule R2, not R1. Harm R1 uses `V(P̂, e*)` = the largest amount over the ops of `e*` (paper §III); signal S1 is `check_constraints(P, current_plan(P), ê) == []`.

## 6. Performance budget

~3,150 items (main + human) × 2 translators × (1 greedy + k samples + probes) solves, plus `P*` and the V1 re-solves. With k = 4 and ~4 counter-readings ⇒ ~9 solves per item per translator ⇒ ~57k solves × ≤3 s (≈ 48 CPU-hours before caching). Must run in parallel (process pool) and **cache by hash(snapshot_id, canonical EditSet, solver config)**: many samples are identical after canonicalization.

## 7. Acceptance criteria

- [ ] `solve(P, ∅)` never has a higher solver objective (§3) than the current plan (20 test snapshots); on snapshots that pass `is_fixed_point` it returns the current plan exactly. The hospital fixture is a fixed point.
- [ ] Each edit op has a unit test showing the constraint holds in the returned plan.
- [ ] Conflicting edits (empty merged window, precedence cycle) ⇒ `Infeasible(reason="precheck")`, no exception.
- [ ] Hospital example: gold `[15:00, null]` moves the hospital after 15:00; wrong `[null, 15:00]` returns the **unchanged** plan.
- [ ] Determinism test: 3 runs, and 3 runs spread over 4 parallel processes ⇒ identical digests; no solve stopped by the time cap.
- [ ] `current_plan(p).arrival == baseline_arrivals(p)` on the fixtures and 20 real snapshots.
- [ ] Wait-only change: same order, `set_time_window` start later than the stop's current service start ⇒ digest differs from `current_plan`; start earlier than it ⇒ digest equal.
- [ ] Median solve time ≤ 3 s on 150 remaining stops.
