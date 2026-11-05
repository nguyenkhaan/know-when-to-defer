# 12 · Risk Control (Threshold Selection)

> Status: Draft v0.1 · Updated 2026-11-05 · CRC is a **tool**, not a contribution. Keep the implementation small and correct.

## 1. Purpose

Choose a threshold `λ` so that executing iff `s ≤ λ` keeps the **joint risk** `E[1{s ≤ λ} · h] ≤ α`, while maximizing coverage.

## 2. Methods

### 2.1 Global CRC (main)

Loss per calibration item: `L_i(λ) = 1{executable_i and s_i ≤ λ} · h_i` (non-executable items: `L_i = 0`), bounded by `B = 1`, non-decreasing in `λ`. Pick:

```
λ̂ = max { λ ∈ grid : ( Σ_i L_i(λ) + 1 ) / (n + 1) ≤ α }
```

(CRC, Angelopoulos et al., Thm. 1, with the parametrization flipped so loss is monotone in the right direction.) Grid = sorted unique calibration scores plus `−∞` (defer all).

### 2.2 Per-op-type CRC (used if `μ` varies across ops)

Run §2.1 separately on each op type `c` (compound items: type = riskiest op, or `compound` as its own type — decide after pilot). Gives `λ̂_c`. Rationale: a single global `λ` can hide violations concentrated in rare op types (Role-Stratified CRC, P22).

### 2.3 Conditional risk with LTT (optional — cut if short on time)

Target `P(h = 1 | executed) ≤ α` with prob. ≥ `1 − δ`. Fixed-sequence testing from strictest λ, binomial p-values (LTT §3.2). **Default: cut** from the submission; keep only if Phase 3 finishes on time (decision by **2026-11-14**).

### 2.4 Reference lines

- **Always execute**: risk = `μ`.
- **Oracle**: defers exactly the harmful items; max coverage = `1 − max(0, μ − α)` for joint risk.
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
