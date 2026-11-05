# 09 · Harm Labeling (Plan-Level Loss)

> Status: Draft v0.1 · Updated 2026-11-05 · This is contribution C1 — keep it simple, precise and reproducible.

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

- `cost` = `travel_min + late_penalty · lateness_min` (spec 07 §3, **without** the deviation term).
- `ε = max(eps_abs, eps_rel · cost(P*))`, default `eps_abs = 5 min`, `eps_rel = 2%`. Report sensitivity for `ε ∈ {0, 5, 10}` min in the appendix of results (not the paper body).
- `tol_min = 1` (rounding).
- R1 checks only constraints of the **gold**; extra constraints the LLM invented matter only through R2/R3.
- If `cost(P̂) < cost(P*)` (heuristic noise), R3 does not fire.

## 3. Non-executions

| LLM output | Label |
|---|---|
| Parse error (spec 06 §4) | `executed = False`, `h = NA`; always deferred |
| `Infeasible` from solver | `executed = False`, `h = NA`; always deferred |

These items **count in the denominator** of coverage and joint risk (they contribute 0 loss, because they are not executed).

## 4. Auxiliary labels (for analysis)

| Field | Meaning |
|---|---|
| `string_correct` | `canonical(ê) ≡ canonical(e*)` (spec 06 §5) |
| `harmless_error` | `not string_correct and h == 0` |
| `nonbinding_error` | `h == 1 and P̂.digest == P.digest` (plan unchanged, like the hospital case) |
| `violation_kind` | which rule fired: R1 / R2 / R3 |
| `delta_cost`, `late_min`, `tw_violations` | magnitude of harm |

## 5. Data model

```python
class HarmLabel(BaseModel):
    item_id: str; model: str
    executed: bool
    h: int | None
    rule: Literal["R1","R2","R3"] | None
    string_correct: bool
    harmless_error: bool
    nonbinding_error: bool
    delta_cost: float | None
    late_min: float | None
```

File: `runs/<run_id>/labels.jsonl`.

## 6. Reproducibility

- `P*` and `P̂` are solved with **the same solver config** and cached (spec 07 §6).
- Label generation is a pure function of (snapshot, gold, ê, solver config, harm config). Store the config hash with each label file.
- Stability is measured by check V1 (spec 13 §11): re-solve with 2× time limit and a different first-solution strategy; label flip rate must be < 1%. ε sensitivity is check V2.

## 7. Acceptance criteria

- [ ] Hospital example ⇒ `h = 1`, `rule = R1`, `nonbinding_error = True`.
- [ ] `ê ≡ e*` ⇒ `h = 0` for 100 random items (sanity).
- [ ] Unit test per rule R1–R3, and for parse error / infeasible handling.
- [ ] Table: counts of `string_correct × h` per model (feeds paper T1).
