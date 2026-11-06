# 12 · Risk Control (Threshold Selection)

> Status: Draft v0.7 · Updated 2026-11-07 (v0.7: per-group CRC always runs; E5 split is leave-one-city-out; no default `α_main`. v0.6: LTT cut, conditional risk not controlled and not in the paper; no F3; station-only shift; reference lines = always execute + oracle. v0.5: per-group CRC on every α; F3/C5 at `α_F3`. v0.2: Thm. 1 conditions spelled out in §2.1; oracle bound includes `π`. v0.3: per-type CRC groups by the LLM edit's op type `ĉ`, §2.2. v0.4: `min_n` depends on `α`; outputs split into per-group (`ĉ`) and gold-type (`c`) risk) · CRC is a **tool**, not a contribution. Keep the implementation small and correct.

## 1. Purpose

Choose a threshold `λ` so that executing iff `s ≤ λ` keeps the **joint risk** `E[1{s ≤ λ} · h] ≤ α`, while maximizing coverage.

## 2. Methods

### 2.1 Global CRC (main)

Loss per calibration item: `L_i(λ) = 1{executable_i and s_i ≤ λ} · h_i` (non-executable items: `L_i = 0`), bounded by `B = 1`, non-decreasing in `λ`. Pick:

```
λ̂ = max { λ ∈ grid : ( Σ_i L_i(λ) + 1 ) / (n + 1) ≤ α }
```

(CRC, Angelopoulos et al., Thm. 1, with the parametrization flipped so loss is monotone in the right direction.) Grid = sorted unique calibration scores plus `−∞` (defer all).

Why this satisfies Thm. 1 (paper: conditions and `−∞` in §III; the formula for `λ̂` and the grid in §IV; the continuity argument below stays in this spec, not in the paper):
- Thm. 1 needs `L_i` **non-increasing**, right-continuous, bounded by `B`, and `L_i(λ_max) ≤ α`. Our `L_i` is non-decreasing in `λ`, so the theorem is applied to `θ = −λ` with `B = 1`.
- The most conservative setting is `λ = −∞` (defer all), with loss 0 ≤ α. **The grid must always contain `−∞`.**
- After the flip, `1{s ≤ −θ}` is left- rather than right-continuous. Restricting the grid to calibration scores gives a `λ̂` equal to or stricter than standard CRC run with the rule `s < t`, so the executed set is a subset and the bound still holds. The unit test in §5 is the empirical check of this argument.
- Conditional risk is not monotone in `λ` (CRC Prop. 1), so it is not controlled (§2.3).

### 2.2 Per-op-type CRC (always run; T3 row at `α_main`)

Run §2.1 separately on each group `ĉ` = **op type of the LLM edit `ê`** (decided 2026-11-06). Gives `λ̂_ĉ`. Rationale: a single global `λ` can hide violations concentrated in rare op types (Role-Stratified CRC, P22).

- **Why `ĉ`, not the gold type `c`:** the threshold must be chosen at deployment, where `e*` is unknown. `ĉ` is read from `ê`, so per-group CRC keeps its guarantee `E[L(λ̂_ĉ) | x = 1, ĉ] ≤ α` (`x` is also known at deployment). Grouping by gold `c` would need the answer to pick the threshold.
- Groups exist only for executable items (`x = 1`); non-executable items are always deferred and are not in any group.
- `ĉ = op_type(ê)` (spec 06 §5.1), computed on the canonical form, so `deadline` and `set_time_window` fall in the same group. Compound `ê` (more than one op after canonicalization, including two ops of the same type): group `compound`. (The "riskiest op" option is dropped: it needs per-type risk before grouping.)
- **Sample floor depends on `α`.** Even with zero harmful executions, the rule in §2.1 needs `1/(n+1) ≤ α`, i.e. `n ≥ 1/α − 1`; allowing `k` harmful executions needs `n ≥ (k+1)/α − 1`. Below the floor CRC already returns `−∞`, so the guarantee holds, but the group's coverage is 0. Use `min_n(α) = max(20, ⌈1/α⌉ − 1)`: 99 at α = 0.01, 49 at 0.02, 20 at 0.05 and 0.10. A group with fewer than `min_n(α)` calibration items gets `λ̂_ĉ = −∞` (defer all).
- **Report fully deferred groups** for every (model, score, α): which groups got `−∞` and their share of executable items. Expected size: ~1,050 calibration items per model per split, minus non-executable, over ~6 groups (5 op types after canonicalization + `compound`) ⇒ ~120–170 per group, uneven. At α = 0.01 most groups will be fully deferred; at α = 0.02 small groups are at risk. **Decided 2026-11-06:** per-group CRC runs at every α in the grid; T3 always reports it at `α_main`; claim C5 uses `α_F3` (spec 13 §14.0; one extra T3 row if `α_F3 ≠ α_main`), chosen from group counts only. `α_main` is never changed for per-group CRC.
- **Fallback (decide 2026-11-14, only if ≥ 3 groups are fully deferred at `α_main`):** merge small groups into one group `other`, with the merge decided on the **fit split** (§3), never on calibration. `other` is still a function of `ê`, so the per-group guarantee holds. Default: no merge.
- Per-type risk by **gold** `c` is computed into `runs/` for analysis only; it is not in the paper (spec 13 §14.3).

### 2.3 Conditional risk — not controlled

`P(h = 1 | executed)` is not monotone in `λ`, so CRC does not apply. LTT was **cut** on 2026-11-07 (lean paper scope). Realized conditional risk is written to `runs/` only and is not reported in the paper.

### 2.4 Reference lines

- **Always execute**: risk = `μ`. Identical to a feasibility-only validator (≈ ReOpt-LLM), since non-executable edits are always deferred.
- **Oracle**: defers all non-executable items plus the fewest harmful ones; max coverage = `1 − π − max(0, μ − α)` for joint risk, where `μ = Σ x_i h_i / N` and `π = 1 − Σ x_i / N` (non-executable share; spec 13 §14). Omitting `π` overstates the oracle line in F2.

## 3. Splits

All splits are **by route**.

| Split | Use | Share |
|---|---|---|
| fit | train the score model and G1 (spec 11 §4) | 30% of routes, fixed (seed 0) |
| calibration / test | CRC on remaining routes, **100 random 50/50 splits** (seeds 1–100) | 70% |
| shift (E5) | leave-one-city-out: fit and calibrate on the other 4 cities, test on the held-out city | spec 13 §8 |

## 4. Outputs per (model, score, method, α, split)

`lambda` (per group for per-group CRC), `coverage`, `realized_joint_risk`, `realized_conditional_risk` (`runs/` only), `per_group_risk` (by `ĉ`, controlled), `per_type_risk_gold` (by gold `c`, `runs/` only), `deferred_groups` (groups with `λ̂_ĉ = −∞`), `violated = realized_joint_risk > α`.

`α` grid: `{0.01, 0.02, 0.05, 0.10}` (main text uses `α_main`, chosen from the pilot; spec 13 §14.0). Scores evaluated: `LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL` (spec 11 §4).

Also per configuration at `α_main`: harmful executions avoided, late minutes avoided, time-window violations avoided (per 1,000 requests) vs always-execute (spec 13 §6).

## 5. Acceptance criteria

- [ ] Unit test on synthetic data: with exchangeable data, mean realized joint risk over 1,000 splits ≤ α + 0.005. (CRC bounds the mean; violation frequency is only reported, not tested.)
- [ ] `λ̂ = −∞` (defer all) handled when even the strictest threshold fails.
- [ ] Per-group CRC (groups by `ĉ`) never pools calibration items across groups.
- [ ] Gold types `c` never affect any `λ̂` (they enter only `per_type_risk_gold`).
- [ ] Results file: one row per configuration in §4 (`runs/<run_id>/risk.parquet`).
