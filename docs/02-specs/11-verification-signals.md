# 11 · Verification Signals & Risk Score

> Status: Draft v0.2 · Updated 2026-11-05 · **Main contribution (C3).** Solver signals are the novelty; LLM signals and the learned guardian are baselines. v0.2 adds L6 and G1. Signal definitions are **frozen after the pilot** (spec 13 §3).

## 1. Purpose

For each item, compute features that predict `h = 1` **without** gold, then combine them into a risk score `s ∈ [0, 1]` (higher = riskier).

**Hard rule:** inputs are only `P`, `q`, the `Prediction` (spec 10) and the solver. Never `gold`, `P*`, `h`.

## 2. Solver-grounded signals (S*)

Let `ê` = greedy edit, `P̂ = solve(P, ê)`, and `ref(ê)` = stops/zones referenced by `ê`.

| ID | Name | Computation | Catches |
|---|---|---|---|
| S1 | `edit_nonbinding` | 1 if the **current plan `P` already satisfies `ê`** (no change needed), else 0 | edits that do nothing, as in the hospital case |
| S2 | `change_magnitude` | `P̂.changed_positions`, `max |Δarrival|` over `ref(ê)`, `Δtravel_min` vs `P` (3 numbers) | no-op or over-reaching edits |
| S3 | `flip_exposes` | Build rule-based **counter-readings** of `ê` (§2.1). 1 if `ê` is non-binding **but** at least one counter-reading is binding (would change the plan), else 0. Also the fraction of counter-readings whose plan differs from `P̂` | direction flips, wrong stop, non-binding errors |
| S4 | `plan_disagreement` | Solve each sampled edit; `1 − share of samples whose plan digest == P̂.digest`; plus mean `|Δcost|` vs `P̂` | ambiguity visible **in plans**, not in JSON |
| S5 | `scope_mismatch` | Stops/categories/zones **mentioned in `q`** (string match on display names, categories, zone words) vs `ref(ê)`: Jaccard distance | wrong stop, missing part of compound request |

### 2.1 Counter-readings (for S3)

Derived from `ê` alone, per op:

| Op | Counter-readings |
|---|---|
| `set_time_window [a, b]` | swap side: `[t_now, a]` ↔ `[b, shift_end]`; shift bound ±60 min |
| `deadline t` | `set_time_window [t, shift_end]` (opposite direction) |
| `precedence(i, j)` | `precedence(j, i)` |
| `remove_stop s` / any stop arg | same op on the 2 most similar stops (same category, then nearest name edit distance) |
| `avoid_zone_until(z, t)` | adjacent zone; `t ± 60` |
| `driver_end_time t`, `service_time` | `t ± 60`; `minutes × 2`, `÷ 2` |

Cap at 4 counter-readings per edit; deterministic order. All solves are cached (spec 07 §6).

Rationale: a mistranslated constraint is often invisible on the current plan; testing the opposite reading makes it visible (Constraint Injection P3 §1; MeetMate P8 evaluates on a longer horizon for the same reason).

## 3. LLM-only signals (L*) — baselines

| ID | Name | Computation |
|---|---|---|
| L1 | `json_consistency` | share of k samples whose canonical form ≡ greedy (spec 06 §5) |
| L2 | `backtranslation_match` | render `ê` to English with a **deterministic template** (e.g. "Deliver to Mercy Hospital before 15:00"); a judge LLM scores 0–100 whether it means the same as `q` |
| L3 | `verbalized_conf` | from the prediction (0–1) |
| L4 | `mean_logprob` | when the provider returns log-probs (expected for M1), else `NA` |
| L5 | `llm_judge` | judge LLM sees `render_snapshot(P)`, `q`, `ê` JSON; outputs P(edit is wrong) 0–100. Mirrors an action-level "guardian" (CORA, P21) without training |
| L6 | `judge_with_diff` | like L5, but the judge also sees a **plan-change summary**: referenced stops' ETA before → after, number of changed positions, Δtravel. A "solver-aware judge": tests whether simply showing solver output to an LLM is enough |

Judge model = M4, never the translator of the same row (spec 10 §2).

## 3b. Learned guardian (G1) — baseline

CORA-style supervised risk model without solver feedback: embed `q` and `render_editset_en(ê)` with M5 (local CPU), concatenate, train logistic regression on the **fit split** to predict `h`. Output `G1 ∈ [0, 1]`.

## 4. Risk score

- Model: **logistic regression** (L2-regularized, standardized features, missing ⇒ median + missing-indicator).
- Trained on the **fit split** only (spec 12 §3), target `h` on executed items.
- Feature sets (all trained the same way):

| Name | Features | Role |
|---|---|---|
| `LLM` | L1–L5 | baseline |
| `LEARNED` | G1 | baseline (supervised guardian) |
| `L6` | L6 alone | baseline / solver-aware judge |
| `SOLVER` | S1–S5 | ours |
| `ALL` | S1–S5 + L1–L5 | ours (main) |
| `ALL+` | `ALL` + L6 + G1 | upper reference |
| `ALL − Sx` / `ALL − Lx` | leave one out | ablation |
| single signals | each alone, raw value | AUROC table |

- Output `s = P(h = 1 | features)`. Parse errors / infeasible ⇒ deferred, no score needed.

## 5. Data model

```python
class SignalRow(BaseModel):
    item_id: str; model: str
    S1: int; S2_changed: int; S2_dmax: float; S2_dtravel: float
    S3_flag: int; S3_frac: float
    S4_disagree: float; S4_dcost: float
    S5_jaccard: float
    L1: float; L2: float | None; L3: float | None; L4: float | None; L5: float | None
    L6: float | None; G1: float | None   # G1 filled after fitting on the fit split
```

File: `runs/<run_id>/signals/<model>.parquet`.

## 6. Acceptance criteria

- [ ] Isolation test: `kwd.signals` cannot access `gold`/`harm` (import check + schema without gold fields).
- [ ] Hospital example: `S1 = 1`, `S3_flag = 1`; L2 judge flags mismatch.
- [ ] All signals computed for 100% of executed items (NA allowed only for L4 on API models).
- [ ] Runtime per item ≤ ~30 s average including solves (with cache and process pool).
