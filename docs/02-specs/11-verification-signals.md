# 11 · Verification Signals & Risk Score

> Status: Draft v0.7 · Updated 2026-11-07 · v0.7: S5 category lexicon; open bounds stay open in counter-readings; zone distance metric. · v0.6: S2, S3 counter-readings and S5 fully specified (deterministic, ready to freeze on 10/11); L2 uses `render_editset_en`. · v0.5: no counter-reading for the dropped `service_time` op. v0.4: `ALL+` dropped; paper T2 shows the 5 score sets and S1–S5, leave-one-out in one sentence (lean paper scope). · v0.3: "plan unchanged" / digest equality in S3–S4 uses the digest of spec 07 §5 (order + service-start times). · **Main contribution (C3).** Solver signals are the novelty; LLM signals and the learned guardian are baselines. v0.2 adds L6 and G1. Signal definitions are **frozen after the pilot** (spec 13 §3).

## 1. Purpose

For each item, compute features that predict `h = 1` **without** gold, then combine them into a risk score `s ∈ [0, 1]` (higher = riskier).

**Hard rule:** inputs are only `P`, `q`, the `Prediction` (spec 10) and the solver. Never `gold`, `P*`, `h`.

## 2. Solver-grounded signals (S*)

Let `ê` = greedy edit, `P̂ = solve(P, ê)`, and `ref(ê)` = the stops named by `ê` plus the remaining stops of every zone named by `ê` (`driver_end_time` names none). All signals are computed on the canonical form of `ê` (spec 06 §5). Times are compared on `service_start` (spec 07 §5).

| ID | Name | Computation | Catches |
|---|---|---|---|
| S1 | `edit_nonbinding` | 1 if the **current plan `P` already satisfies `ê`** (`check_constraints(P, current_plan(P), ê) == []`, Task 1.4), else 0 | edits that do nothing, as in the hospital case |
| S2 | `change_magnitude` | 3 numbers vs the current plan `P`: `S2_changed` = `P̂.changed_positions`; `S2_dmax` = max `|Δservice_start|` (min) over `ref(ê)` ∩ `P̂`, and `|Δend_time|` if `ê` has `driver_end_time` (0 if empty); `S2_dtravel` = `travel_min(P̂) − travel_min(P)` | no-op or over-reaching edits |
| S3 | `flip_exposes` | Build rule-based **counter-readings** of `ê` (§2.1). `S3_flag` = 1 if `P̂.digest == P.digest` **and** at least one counter-reading gives a different digest (or is `Infeasible`), else 0. `S3_frac` = share of counter-readings whose plan digest differs from `P̂` (`Infeasible` counts as different); 0 if there is none | direction flips, wrong stop, non-binding errors |
| S4 | `plan_disagreement` | Solve each of the k samples; `S4_disagree` = `1 − share of samples whose plan digest == P̂.digest` (parse errors and `Infeasible` count as disagreeing; all k failing ⇒ 1); `S4_dcost` = mean `|cost − cost(P̂)|` (harm `cost` of spec 09 §2, no gold needed) over feasible samples, 0 if none | ambiguity visible **in plans**, not in JSON |
| S5 | `scope_mismatch` | `M` = `mentions(q, P)`: remaining stops whose display name occurs in `q` (after `normalize_name`, whole words), all remaining stops of a category mentioned in `q` (category words = every category name except `residence` and `depot`, plus its name suffixes in `kwd.data.names.SUFFIXES`, e.g. shop/store/market; singular or plural; whole words, case-insensitive), and all remaining stops of a zone id in `q` (whole token, case-insensitive). `S5 = 1 − |M ∩ ref(ê)| / |M ∪ ref(ê)|`; 0 if both are empty | wrong stop, missing part of compound request |

### 2.1 Counter-readings (for S3)

Derived from the canonical `ê` alone. For each op, candidates in this fixed priority order (each replaces that op only; the other ops of a compound `ê` stay):

| Op (canonical) | Counter-readings, in order |
|---|---|
| `set_time_window [a, b]` (also `deadline`) | flip side: `[t_now, a]` if `a > t_now`, then `[b, shift_end]` if `b < shift_end`; same window on the most similar stop; every closed bound `+60` min (a bound equal to `t_now` or `shift_end` is open and stays open) |
| `precedence(i, j)` | `precedence(j, i)`; `precedence(i', j)` with `i'` most similar to `i` |
| `remove_stop s` | remove the most similar stop, then the second most similar |
| `avoid_zone_until(z, t)` | same `t` on the nearest zone; `t + 60`; `t − 60` |
| `driver_end_time t` | `t + 60`; `t − 60` |

- **Most similar stop:** another remaining stop of the same category first, then smallest edit distance between normalized names, ties by `stop_id`.
- **Nearest zone:** the other zone with the smallest Euclidean distance between the mean (lat, lng) of its remaining stops and that of `z`, ties by zone id.
- Times are clipped to `[t_now, shift_end]`; a candidate equal to `ê` after clipping, or with an empty window, is dropped.
- **Cap 4 per `ê`**, taken round-robin over the canonical ops (first candidate of each op, then the second, …), so a compound `ê` probes each part. Deterministic order; all solves are cached (spec 07 §6).

Rationale: a mistranslated constraint is often invisible on the current plan; testing the opposite reading makes it visible (Constraint Injection P3 §1; MeetMate P8 evaluates on a longer horizon for the same reason).

## 3. LLM-only signals (L*) — baselines

| ID | Name | Computation |
|---|---|---|
| L1 | `json_consistency` | share of k samples whose canonical form ≡ greedy (spec 06 §5) |
| L2 | `backtranslation_match` | render `ê` to English with `render_editset_en` (spec 06; e.g. "Deliver to Green Valley Hospital no later than 15:00."); a judge LLM scores 0–100 whether it means the same as `q` |
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
| `ALL − Sx` / `ALL − Lx` | leave one out | ablation; one sentence in the paper |
| single signals | each alone, raw value | S1–S5 in T2; L1–L6, G1 in `runs/` |

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
- [ ] All signals computed for 100% of executed items (NA allowed only for L4 when the provider returns no log-probs, expected for M2).
- [ ] Counter-readings: same `ê` ⇒ same list; at most 4; every time inside `[t_now, shift_end]`; a compound `ê` gets candidates for each of its ops.
- [ ] Runtime per item ≤ ~30 s average including solves (with cache and process pool).
