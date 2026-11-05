# 07 · Solver: Re-optimize a Snapshot Under Edits

> Status: Draft v0.1 · Updated 2026-11-05

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
- **Original LMRC time windows** are **soft**: penalty per minute late (`late_penalty`, default 10/min), since real data can be internally inconsistent.
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
    arrival: dict[str, int]      # seconds since departure
    end_time: int                # return to depot
    travel_min: float
    lateness_min: float          # vs original LMRC windows
    changed_positions: int       # vs current plan
    solve_status: str
    solve_time_s: float

class Infeasible(BaseModel):
    reason: str
```

`Plan.digest()` = hash of `sequence` → cheap equality check used by signals ("plan unchanged").

## 6. Performance budget

~3,150 items (main + human) × 2 translators × (1 greedy + k samples + probes) solves, plus `P*` and the V1 re-solves. With k = 4 and ~4 counter-readings ⇒ ~9 solves per item per translator ⇒ ~57k solves × ≤3 s (≈ 48 CPU-hours before caching). Must run in parallel (process pool) and **cache by hash(snapshot_id, canonical EditSet, solver config)**: many samples are identical after canonicalization.

## 7. Acceptance criteria

- [ ] `solve(P, ∅)` returns the current plan (or one with cost ≤ it) for 20 test snapshots.
- [ ] Each edit op has a unit test showing the constraint holds in the returned plan.
- [ ] Hospital example: gold `[15:00, end]` moves the hospital after 15:00; wrong `[start, 15:00]` returns the **unchanged** plan.
- [ ] Determinism test: 3 runs ⇒ identical digests.
- [ ] Median solve time ≤ 3 s on 150 remaining stops.
