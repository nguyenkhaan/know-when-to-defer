# Contract — locked definitions for `docs/` and `paper/`

> Locked 2026-11-06 by the user (A). Revised 2026-11-07 through rule 2 (approved by A), three times: (1) lean paper scope (§4 "Reported results"), LTT cut, gold type `c` and conditional risk out of the paper, no F3; (2) harm `cost` in plain minutes, `α_main` from both translators, three primary comparisons with rules, plan-unchanged AUROC, leave-one-city-out shift; (3) DSL rules, R1 amounts, harm magnitudes, T4 fallback, allowlist release. **Re-locked 2026-11-07** once the `docs/` tree was completed.
> Audience: every AI agent and co-author editing `docs/`, `paper/` or code that implements these definitions.
> This file lists **what may not drift**. It does not repeat the details: each row points to its single source of truth.

## 0. Rules

1. **Read this file before editing anything in `docs/` or `paper/`.** If a requested edit would change a locked item, stop and ask the user. Do not change it silently, even to "fix" an inconsistency: report the inconsistency instead.
2. **Changing a locked item** needs all four, in one change:
   1. explicit approval from the user in the conversation;
   2. a new row in the decision log of `docs/CONTENT.md`;
   3. the same edit in **every** file listed in the "Where" column (paper, specs, plans, research docs);
   4. a version bump in each spec touched, and an update of this file.
3. Wording, typos and formatting that keep the meaning are not changes to the contract.
4. Items in §6 are **not yet locked**. They become locked on their decision date through rule 2.
5. Project rules from `CLAUDE.md` still apply: never auto-repair LLM output, keep API spend within `configs/llm.yaml`, never commit (suggest a message).

## 1. Problem and notation (paper §III)

| Item | Locked value | Where |
|---|---|---|
| Current time | `t_now` (paper `$t_{\mathrm{now}}$`), seconds since departure in code | paper §III; spec 05 §4; `kwd.data.models` |
| Plan `P` | real LMRC driver order of the remaining stops; times from `schedule()` | paper §III; spec 05 §4; spec 07 §5 |
| `P̂`, `P*` | `Solve(P, ê)`, `Solve(P, e*)` with the **same** solver config | paper §III; spec 07; spec 09 §6 |
| `ĉ`, `c` | `ĉ = op_type(ê)`, `c = op_type(e*)`; one shared function on the canonical form; ≥ 2 ops ⇒ `compound`. The paper uses only `ĉ`; `c` (`gold_type`) is for generation and `runs/` analysis | paper §III (`ĉ` only); spec 06 §5.1; spec 08 §7 (`gold_type`); spec 12 §2.2 |
| Executable `x` | `x = 0` iff parse error or `Infeasible` (`precheck` or `no_solution`); `x·h = 0`; non-executable stays in every denominator | paper §III; spec 07 §4; spec 09 §3; spec 13 §14 |
| DSL rules | every op is a constraint on the plan, stated on service start ("served"); edits that change problem data are out of scope; the parser rejects every past time (`bad_interval`, by the minute) and never repairs LLM output; the prompt schema is `editset_json_schema()` | spec 06 §3, §4, §6; spec 10 §3; paper §IV (one clause) |

## 2. Harm (contribution C1)

| Item | Locked value | Where |
|---|---|---|
| Harm `h` | R1 ∨ R2 ∨ R3, judged on the plan, never on the JSON; `rule` = first firing in the order R1 > R2 > R3 | paper eq. (1); spec 09 §2, §4 |
| R1 amounts | per-op violation amounts of `check_constraints` (minutes, from `service_start`); a gold constraint on a stop that `P̂` dropped is left to R2 | spec 07 §5; spec 09 §2; paper §III (`V`) |
| Harm magnitudes (C8) | `late_min` = Σ per stop of excess lateness of `P̂` over `P*`; `tw_violations` = windows met by `P*` within τ and missed by `P̂` by more than τ | spec 09 §4; spec 13 §14.3 |
| Tolerances | `τ = 1 min`; `ε = max{5 min, 0.02·cost(P*)}` | paper §III; spec 09 §2; `configs/harm.yaml` |
| `cost` for harm | travel + lateness + overtime past `shift_end`, all in **minutes with weight 1**; no deviation term, no solver penalty weights (those steer the search only) | paper §III; spec 07 §3; spec 09 §2 |
| Plan times | only from `schedule()`; never read from OR-Tools cumuls; original `tw_start` is a lower bound (wait) | spec 07 §2, §5 |
| Digest / "plan unchanged" | hash of order + `service_start` rounded to the minute + `end_time` | spec 07 §5; spec 08 §2; spec 09 §4; spec 11 S3–S4 |
| Non-binding error | `h = 1` and `P̂ = P` (same digest) | paper §III; spec 09 §4 |
| Fixed-point filter | benchmark keeps only snapshots with `solve(P, ∅).digest == P.digest`; replacements from the same station's reserve list | spec 05 §3; spec 07 §5; spec 08 §2.1 |

## 3. Risk control (method, §III–§IV)

| Item | Locked value | Where |
|---|---|---|
| Loss | `L(λ) = x·h·1{s ≤ λ}`, execute iff `x = 1` and `s ≤ λ` | paper §III; spec 12 §2.1 |
| Target | joint risk `E[L(λ)] ≤ α` only. Conditional risk is not controlled (LTT cut 07/11) and not in the paper; written to `runs/` only | paper eq. (2); spec 12 §1, §2.3, §4; spec 13 §14.3 |
| CRC grid | calibration scores plus `−∞`; Thm. 1 applied to `θ = −λ` | paper §III (conditions), §IV (formula for `λ̂` and grid; the continuity argument stays in spec 12); spec 12 §2.1 |
| Per-group CRC | groups by `ĉ` of executable edits; guarantee `E[L(λ_ĉ) \| x = 1, ĉ] ≤ α`; gold `c` never affects any `λ` | paper §III; spec 12 §2.2; `MoTaDeTai.md` §2.3; Task 4.1 |
| Sample floor | `min_n(α) = max(20, ⌈1/α⌉ − 1)`; below it the group defers all; `deferred_groups` always reported | spec 12 §2.2; Task 4.1 |
| Coverage bound | `cov_max = 1 − π − max{0, μ − α}` | paper eq. (3); spec 12 §2.4 |

## 4. Experiments (pre-registered)

| Item | Locked value | Where |
|---|---|---|
| Splits | by route; fit 30% (seed 0); 100 random 50/50 calibration/test splits (seeds 1–100) | spec 12 §3 |
| α grid | `{0.01, 0.02, 0.05, 0.10}` | spec 12 §4; spec 13 §14.0 |
| `α_main` | rule: largest grid value ≤ `min(μ_M1, μ_M2) / 2`, μ over all pilot items; none qualifies ⇒ 0.01 and claims for a translator with `μ ≤ 0.02` are descriptive; one value for both translators; frozen 10/11; **never changed afterwards**, also not for per-group CRC | spec 13 §14.0; Task 2.5 Step 5a |
| `α_F3` | smallest grid α ≥ `α_main` where every group `ĉ` has `n_cal ≥ min_n(α)` in the median split; from counts only; used by C5 (per-group row of T3; extra row if `α_F3 ≠ α_main`) | spec 13 §14.0, §14.6; spec 12 §2.2; Task 4.1 `alpha_f3` |
| Claims ↔ evidence | claim map and success criteria fixed before main results | `01-research/02-research-questions-and-claims.md`; spec 13 §14.6 |
| Signal freeze | solver signals S1–S5 and counter-reading rules (as specified in spec 11 §2, §2.1) frozen after E0 | spec 13 §3; spec 11 §2, §2.1 |
| Primary comparisons | exactly three: `ALL` vs `LLM`, `ALL` vs `LEARNED`, `SOLVER` vs `L6`, each with a pre-registered rule; everything else descriptive | spec 13 §7, §14.0, §14.6 |
| Reported results (lean scope) | Figures F1, F2; tables T1–T4; **no F3**. T2: AUROC/AURC of 5 score sets (`LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL`) + AUROC of S1–S5; leave-one-out and AUROC on the plan-unchanged subset (`P̂ = P`) one sentence each; no `ALL+`, no AUPRC. T3: random, per-group `ĉ`, **one station-shift row** (leave-one-city-out, mean of 5 folds), human row. E6 pooled, per writer one sentence. Gold-type risk `c`, conditional risk, AUPRC: `runs/` only. ε sensitivity and V1–V3: one clause each. Baselines: always execute (= feasibility-only validator), L1–L6, G1; reference line oracle. Limitations: 4 sentences. Page-fit fallback allowed without rule 2: T1 reduced to total rows, then T4 turned into 2 sentences of Results | `01-research/03-paper-outline.md` §2; `01-research/02-research-questions-and-claims.md`; spec 11 §4; spec 12 §2.4, §3; spec 13 §1, §5–§9, §12, §14; Phase 4–5 plans; `CLAUDE.md` ("Keep the paper lean") |

## 5. Paper and venue

| Item | Locked value | Where |
|---|---|---|
| Venue | IEEE MOST 2027; deadline 01/12/2026 (internal 30/11) | spec 16 §1 |
| Format | `IEEEtran` conference; ≤ 8 pages **including references**; all pages numbered | spec 16 §2; `paper/main.tex` |
| Review | double-blind: no names, metadata or identifying links | spec 16 §3 |
| Anonymous release | allowlist only (`src/`, `tests/`, `configs/`, `scripts/` without the smoke script, `pyproject.toml` without authors, `uv.lock`, README, benchmark); no `docs/`, `paper/`, reference PDFs, agent files | Phase 6 Step 6.2; spec 14 §6 |
| Contributions | C1 plan-level harm, C2 benchmark, **C3 solver signals (main)**; CRC is a tool, not a contribution | `00-overview/01-project-brief.md` §3; spec 12 header |
| Title | as in `paper/main.tex` | `paper/main.tex` |

## 6. Not yet locked (decide on the date, then lock via rule 2)

| Item | Decision date | Where |
|---|---|---|
| Final DSL op list (6 ops since 07/11, `service_time` dropped; the pilot may only drop ops) | 08/11 | spec 06 §3; roadmap §2 |
| `α_main` value; signal freeze; main-set size and `k` | 10/11 | spec 13 §3, §14.0 |
| Exchangeability with route-level splits (ask supervisor) | 10/11 | `debit-last-submit.md` §5 |
| Merge small `ĉ` groups into `other` (default no) | 14/11 | spec 12 §2.2; roadmap §2 |
| Solver values: `solution_limit`, `late_penalty`, `shift_penalty`, `dev_weight` (search only, not in harm `cost`) | with Task 1.4 | spec 07 §3–§4; `configs/solver.yaml` |
| Results lock: no new experiments | 22/11 | roadmap §1 |
