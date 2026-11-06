# 09 · Harm Labeling (Plan-Level Loss)

> Status: Draft v0.5 · Updated 2026-11-07 · v0.5: R1 amounts from `check_constraints` (spec 07 §5); `late_min` summed per stop; V1 without warm start. · v0.4: `cost` in plain minutes (travel + lateness + overtime, weight 1) so that ε in minutes is comparable; `rule` precedence R1 > R2 > R3; `late_min` and `tw_violations` defined (feed C8). · v0.3: ε sensitivity is one clause in the paper's Setup (no appendix in 8 pages). · v0.2: plan digest covers order and service-start times (spec 07 §5), so `nonbinding_error` means the plan is literally unchanged. · This is contribution C1 — keep it simple, precise and reproducible.

## 1. Purpose

Decide `h ∈ {0, 1}` for an **executed** LLM edit by looking at the resulting plan `P̂`, not at the JSON. Uses the gold edit `e*` and the gold plan `P* = solve(P, e*)`. Evaluation-only.

## 2. Definition

`h = 1` iff **any** of:

| Rule | Condition on `P̂` | Example |
|---|---|---|
| R1 · Gold violated | `P̂` breaks a constraint of `e*` (window, precedence, depot time, zone, removed stop still visited) by more than `tol_min` | hospital delivered 14:10, gold says ≥ 15:00 |
| R2 · Wrong stop set | set of visited stops in `P̂` ≠ set in `P*` (LLM removed the wrong stop, or none) | removed "Oak Pharmacy" instead of "Oak Clinic" |
| R3 · Excess cost | `cost(P̂) − cost(P*) > ε` | unrequested constraint forces a big detour |

Else `h = 0`.

- `cost` = `travel_min + lateness_min + overtime_min`, all in minutes with weight 1: lateness against original LMRC windows (by `service_start`), overtime = return to depot past `shift_end`. **No** deviation term and **no** solver penalty weights (those steer the search only, spec 07 §3). Since `cost` is in minutes, `ε` in minutes compares like with like (decided 2026-11-07).
- `ε = max(eps_abs, eps_rel · cost(P*))`, default `eps_abs = 5 min`, `eps_rel = 2%`. Sensitivity for `ε ∈ {0, 5, 10}` min (check V2, spec 13 §11) is one clause in the paper's Setup.
- `tol_min = 1` (rounding).
- R1 checks only constraints of the **gold**, with the amounts of `check_constraints` (spec 07 §5); a gold constraint on a stop that `P̂` dropped is left to R2. Extra constraints the LLM invented matter only through R2/R3.
- If `cost(P̂) < cost(P*)` (heuristic noise), R3 does not fire.

## 3. Non-executions

| LLM output | Label |
|---|---|
| Parse error (spec 06 §4) | `executed = False`, `h = NA`; always deferred |
| `Infeasible` from solver (`precheck` or `no_solution`, spec 07 §4) | `executed = False`, `h = NA`; always deferred |

These items **count in the denominator** of coverage and joint risk (they contribute 0 loss, because they are not executed).

## 4. Auxiliary labels (for analysis)

| Field | Meaning |
|---|---|
| `string_correct` | `canonical(ê) ≡ canonical(e*)` (spec 06 §5) |
| `harmless_error` | `not string_correct and h == 0` |
| `nonbinding_error` | `h == 1 and P̂.digest == P.digest` (plan unchanged in order **and** service times, spec 07 §5; like the hospital case). An edit that only adds waiting is **not** non-binding |
| `rule` | first rule that fires, in the order R1 > R2 > R3; E1 reports the mix of `rule` |
| `delta_cost` | `cost(P̂) − cost(P*)` in minutes (may be negative) |
| `late_min` | `Σ_s max(0, late_s(P̂) − late_s(P*))` over stops visited by both plans, where `late_s` = minutes `service_start` exceeds the stop's tightest upper bound (original window end, or a window/deadline end of `e*`). Not the same as `Plan.lateness_min` (original windows only, enters `cost`) |
| `tw_violations` | number of windows (original or of `e*`) that `P*` meets within `tol_min` but `P̂` misses by more than `tol_min` |

`late_min` and `tw_violations` are measured against `P*`, so summed over executed items they give the harm that a policy lets through; C8 compares this sum with always-execute (spec 13 §14.3).

## 5. Data model

```python
class HarmLabel(BaseModel):
    item_id: str; model: str
    executed: bool
    h: int | None
    rule: Literal["R1","R2","R3"] | None   # first firing rule, R1 > R2 > R3
    string_correct: bool
    harmless_error: bool
    nonbinding_error: bool
    delta_cost: float | None               # None when not executed
    late_min: float | None
    tw_violations: int | None
```

File: `runs/<run_id>/labels.jsonl`.

## 6. Reproducibility

- `P*` and `P̂` are solved with **the same solver config** and cached (spec 07 §6).
- Label generation is a pure function of (snapshot, gold, ê, solver config, harm config). Store the config hash with each label file.
- Stability is measured by check V1 (spec 13 §11): re-solve with 2× `solution_limit`, `warm_start=False` and a different first-solution strategy; label flip rate must be < 1%. ε sensitivity is check V2.

## 7. Acceptance criteria

- [ ] Hospital example ⇒ `h = 1`, `rule = R1`, `nonbinding_error = True`.
- [ ] An item firing R1 and R3 has `rule = R1`; `late_min = 0` and `tw_violations = 0` when `P̂ = P*`.
- [ ] `ê ≡ e*` ⇒ `h = 0` for 100 random items (sanity).
- [ ] Unit test per rule R1–R3, and for parse error / infeasible handling.
- [ ] Table: counts of `string_correct × h` per model (feeds paper T1).
