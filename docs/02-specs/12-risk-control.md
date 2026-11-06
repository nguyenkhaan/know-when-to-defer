# 12 · Risk Control (Threshold Selection)

> Status: Draft v0.3 · Updated 2026-11-06 (v0.2: Thm. 1 conditions spelled out in §2.1; oracle bound includes `π`. v0.3: per-type CRC groups by the LLM edit's op type `ĉ`, §2.2) · CRC is a **tool**, not a contribution. Keep the implementation small and correct.

## 1. Purpose

Choose a threshold `λ` so that executing iff `s ≤ λ` keeps the **joint risk** `E[1{s ≤ λ} · h] ≤ α`, while maximizing coverage.

## 2. Methods

### 2.1 Global CRC (main)

Loss per calibration item: `L_i(λ) = 1{executable_i and s_i ≤ λ} · h_i` (non-executable items: `L_i = 0`), bounded by `B = 1`, non-decreasing in `λ`. Pick:

```
λ̂ = max { λ ∈ grid : ( Σ_i L_i(λ) + 1 ) / (n + 1) ≤ α }
```

(CRC, Angelopoulos et al., Thm. 1, with the parametrization flipped so loss is monotone in the right direction.) Grid = sorted unique calibration scores plus `−∞` (defer all).

Why this satisfies Thm. 1 (state these in the paper, §III):
- Thm. 1 needs `L_i` **non-increasing**, right-continuous, bounded by `B`, and `L_i(λ_max) ≤ α`. Our `L_i` is non-decreasing in `λ`, so the theorem is applied to `θ = −λ` with `B = 1`.
- The most conservative setting is `λ = −∞` (defer all), with loss 0 ≤ α. **The grid must always contain `−∞`.**
- After the flip, `1{s ≤ −θ}` is left- rather than right-continuous. Restricting the grid to calibration scores gives a `λ̂` equal to or stricter than standard CRC run with the rule `s < t`, so the executed set is a subset and the bound still holds. The unit test in §5 is the empirical check of this argument.
- Conditional risk is not monotone in `λ`; CRC Prop. 1 shows CRC can then fail arbitrarily, hence LTT in §2.3.

### 2.2 Per-op-type CRC (used if `μ` varies across ops)

Run §2.1 separately on each group `ĉ` = **op type of the LLM edit `ê`** (decided 2026-11-06). Gives `λ̂_ĉ`. Rationale: a single global `λ` can hide violations concentrated in rare op types (Role-Stratified CRC, P22).

- **Why `ĉ`, not the gold type `c`:** the threshold must be chosen at deployment, where `e*` is unknown. `ĉ` is read from `ê`, so per-group CRC keeps its guarantee `E[L(λ̂_ĉ) | ĉ] ≤ α`. Grouping by gold `c` would need the answer to pick the threshold.
- Groups exist only for executable items (`x = 1`); non-executable items are always deferred and are not in any group.
- Compound `ê` (more than one op): group `compound`. (The "riskiest op" option is dropped: it needs per-type risk before grouping.)
- A group with fewer than `min_n = 20` calibration items gets `λ̂_ĉ = −∞` (defer all).
- Per-type risk by **gold** `c` is still reported, as analysis only (spec 13 §14.3).

### 2.3 Conditional risk with LTT (optional — cut if short on time)

Target `P(h = 1 | executed) ≤ α` with prob. ≥ `1 − δ`. Fixed-sequence testing from strictest λ, binomial p-values (LTT §3.2). **Default: cut** from the submission; keep only if Phase 3 finishes on time (decision by **2026-11-14**).

### 2.4 Reference lines

- **Always execute**: risk = `μ`.
- **Oracle**: defers all non-executable items plus the fewest harmful ones; max coverage = `1 − π − max(0, μ − α)` for joint risk, where `μ = Σ x_i h_i / N` and `π = 1 − Σ x_i / N` (non-executable share; spec 13 §14). Omitting `π` overstates the oracle line in F2.
- **No-calibration threshold**: `s ≤ 0.5`.

## 3. Splits

All splits are **by route**.

| Split | Use | Share |
|---|---|---|
| fit | train the score model and G1 (spec 11 §4) | 30% of routes, fixed (seed 0) |
| calibration / test | CRC on remaining routes, **100 random 50/50 splits** (seeds 1–100) | 70% |
| shift (E5) | calibrate on some op types or levels, test on others | see spec 13 |

## 4. Outputs per (model, score, method, α, split)

`lambda`, `coverage`, `realized_joint_risk`, `realized_conditional_risk`, per-type risk, `violated = realized_joint_risk > α`.

`α` grid: `{0.01, 0.02, 0.05, 0.10}` (main text uses `α_main`, chosen from the pilot; spec 13 §14.0). Scores evaluated: `LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL` (spec 11 §4).

Also per configuration at `α_main`: harmful executions avoided, late minutes avoided, time-window violations avoided (per 1,000 requests) vs always-execute (spec 13 §6).

## 5. Acceptance criteria

- [ ] Unit test on synthetic data: with exchangeable data, mean realized joint risk over 1,000 splits ≤ α + 0.005. (CRC bounds the mean; violation frequency is only reported, not tested.)
- [ ] `λ̂ = −∞` (defer all) handled when even the strictest threshold fails.
- [ ] Per-type CRC never pools calibration items across types.
- [ ] Results file: one row per configuration in §4 (`runs/<run_id>/risk.parquet`).
