# 13 · Experiment Protocol

> Status: Draft v0.6 · Updated 2026-11-07 · v0.6: lean paper scope (CONTRACT §4 "Reported results"): no F3; T2 = 5 score sets + S1–S5; no AUPRC, no `ALL+`; E5 = station shift only; E6 pooled, per writer in one sentence; gold-type risk and conditional risk in `runs/` only; ε sensitivity one clause. · v0.5: E0 adds a solver sanity check (spec 08 §2.1); per-group CRC runs at every α; F3 and C5 use `α_F3` (§14.0, decided 06/11). · v0.4: T3/F3/E3 name groups `ĉ` explicitly; report fully deferred groups (spec 12 §2.2). · v0.3: per-type risk split into per-group risk by the LLM edit's op type `ĉ` (controlled) and per-type risk by gold `c` (analysis); C5 restated on `ĉ`. · v0.2 adds a human-written test set (E6), error taxonomy (E7), label-robustness checks (V1–V3), two stronger baselines (G1, L6), harm-prevented metric and station shift. Every experiment maps to a claim in `01-research/02-research-questions-and-claims.md`.

## 1. Overview

| ID | Question | Data | Output | Claim |
|---|---|---|---|---|
| E0 | **Pilot / go-no-go** | pilot (~300 items) | go/no-go report | H1, H2 (early) |
| E1 | How often and how badly do LLMs err? | main | T1 | C1, C1', C2 |
| E2 | Which signals predict harm? | main (eval routes) | T2 | C3 |
| E3 | Does CRC hold α? Global vs per-type (groups by `ĉ`); how much harm is prevented? | main, 100 splits | T3 | C4, C5 |
| E4 | Ablation: solver vs LLM signals vs stronger baselines | main | T2, F2 | **C3** |
| E5 | Distribution shift: held-out stations | main | T3 (one shift row) | C6 |
| **E6** | **Do results hold on human-written requests?** | human set (~200) | T2/T3 extra rows | **C7** |
| **E7** | **Which real LLM errors do the signals catch?** | ~100 harmful errors, hand-labeled | T4 | **C3 (anti-circularity)** |
| **V1–V3** | Are harm labels stable? Are signals free of tuning on test data? | main subset | one clause each in Setup | C1 (validity) |

## 2. Models (5 total — see spec 10 §2)

Two **translators** (M1 small open, M2 strong API) — every experiment runs on both. M3 paraphraser, M4 judge, M5 embedding are support models. The former optional medium translator was dropped to cut API cost.

## 3. E0 — Pilot (deadline 2026-11-10)

Pilot benchmark → translate with M1, M2 → label → signals S1–S5, L1, L3 → report:

- `μ` per model × level and per op; parse-error and infeasible rates; non-binding share of harmful errors;
- AUROC (bootstrap 95% CI) of S1–S5 vs L3; oracle max coverage per α;
- **measured cost per item** per model → extrapolate main-run cost; if over budget, reduce main set size or `k` before Phase 3.
- **solver sanity** (spec 08 §2.1): share of pilot routes dropped by the fixed-point filter; for every non-binding gold, `P*.digest == P.digest`. If the second check fails on any item, fix the solver (Task 1.4) before E1 numbers are trusted.

**Go** if both: (1) at levels 2–3, `μ ≥ 3–5%` for at least one translator and clearly above the α values we report; (2) at least one solver signal beats L3 (non-overlapping CI or ≥ +0.05 AUROC).
**Fallbacks:** emphasize M1; harder level-3 compound items; else switch to the backup topic in `MoTaDeTai.md` §6.2.

**Signal freeze:** after E0, solver signals S1–S5 and counter-reading rules (spec 11 §2.1) are **frozen** (record the git commit in `CONTENT.md` §6). Baselines L2, L4–L6 and G1 are designed and tuned on pilot data only and frozen before the main run. No signal changes after looking at main-set or human-set results. This answers "signals were tuned to the benchmark".

## 4. E1 — Error landscape

`μ`; string-level error rate; harmless-error share; non-binding-error share; rule mix R1/R2/R3; mean `delta_cost`, `late_min`. Breakdowns: model × level; model × op; binding vs non-binding gold.

## 5. E2 — Signal quality

On executed items of eval routes (not the fit split): AUROC of each single signal and each score model (AUPRC is computed into `runs/` only); bootstrap CI by route (1,000×). On the non-binding-error subset: recall at 20% defer rate.

## 6. E3 — Risk control and operational value

- {`LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL`} × {global CRC, per-type CRC} × α ∈ {0.01, 0.02, 0.05, 0.10} × 100 splits: coverage, realized joint risk, violation frequency, per-group realized risk (`ĉ`), fully deferred groups (`λ̂_ĉ = −∞`, spec 12 §2.2). Gold-type risk (`c`) and conditional risk go to `runs/` only.
- **Harm prevented** at `α_main` vs "always execute": number of harmful executions avoided, total late minutes avoided, time-window violations avoided, per 1,000 requests; and the **human workload** = defer rate.
- Main text: `α_main` (see §14.0), `ALL` vs `LLM` vs `LEARNED`.

## 7. E4 — Ablation and baselines

- Risk–coverage curves and AURC for: `LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL`. Leave-one-out sets (`ALL − each S`, `ALL − each L`) are computed, and the paper reports them in **one sentence** (which signal costs most when removed).
- Required comparisons:
  1. `ALL` vs `LLM`: does solver feedback add value?
  2. `SOLVER` vs `LEARNED`: hand-built solver signals vs a supervised text classifier (CORA-style learned guardian, P21).
  3. `SOLVER` vs `L6`: structured solver signals vs simply showing the plan change to an LLM judge. If L6 wins, report it honestly: it is still solver feedback and still supports the thesis that plan-level feedback matters.

## 8. E5 — Distribution shift

Calibrate on routes of some stations, test on routes of the held-out stations (closest to deploying at a new depot). One row in T3: realized risk vs α and coverage. Characterize only, no fixes claimed.

The level, op-type and phrasing shifts were dropped on 2026-11-07 (lean paper scope); the human set (E6) is the cross-source shift test.

## 9. E6 — Human-written requests (new)

- Data: ~200 items written by two people (B and C, ~100 each; spec 08 §9), on routes **not** used in main fit/calibration. Tables report the pooled human set; per-writer results go into **one sentence** (does the direction hold for both writers).
- Protocol: score models trained on main fit split; CRC calibrated on main calibration data; **test on the human set** (cross-source shift). Also report AUROC of single signals on the human set.
- Questions: does the signal ranking (AUROC order) match the synthetic set? Does realized risk stay ≤ α or break? Is `μ` higher on human language?
- Small n (expect ~20–40 harmful errors for M1) ⇒ report CIs; claim only direction and magnitude, not fine differences.

## 10. E7 — Error taxonomy (new)

- Sample ~100 harmful executed errors (stratified by translator and level, seed 0) from main **test** routes.
- One annotator labels each with one primary type: `direction_flip`, `wrong_stop`, `missing_part` (compound), `extra_constraint`, `wrong_value` (time off), `other`; a second annotator labels 30 for agreement.
- For each type: share of errors, and which signals catch it (flagged if the item lands in the top 20% risk under `SOLVER`, `LLM`, `ALL`).
- Output: T4 (types × share × caught-by), plus 1–2 short qualitative examples for the paper.

## 11. V1–V3 — Validity and robustness checks (new)

| ID | Check | Pass condition | Where reported |
|---|---|---|---|
| V1 | **Solver-noise floor**: re-solve `P*` and `P̂` for 500 items with 2× time limit and a different first-solution strategy; re-label | label flip rate < 1% | 1 sentence in Setup |
| V2 | **ε sensitivity**: labels and main E3 numbers with ε ∈ {0, 5, 10} min | conclusions unchanged | one clause in Setup |
| V3 | **No test-time tuning**: signal-freeze commit precedes main/human results | commit dates in `paper/RUNS.md` | Setup |

If V1 fails (≥ 1%), raise the solver time limit, or require harm rule R3 (excess cost) to fire in **both** solves; re-run labels before E1.

## 12. Baselines (summary)

Always execute, which equals a feasibility-only validator (≈ ReOpt-LLM; risk `μ`) · L3 verbalized confidence · L4 log-prob · L1 self-consistency only · L5 LLM judge on `(q, ê)` · **L6 LLM judge with plan diff** · **G1 learned guardian (embedding + logistic regression)**. Reference line: oracle (spec 12 §2.4).

## 13. Outputs

All results go to `runs/<run_id>/` (spec 14). `kwd report --run <id>` regenerates every table (LaTeX), figure (PDF) and number macro in `paper/`. No hand-copied numbers.

## 14. Metric definitions

### 14.0 Evaluation design decisions (and why)

| Decision | Why |
|---|---|
| **Main α is set from the pilot, not fixed at 0.05.** Grid `{0.01, 0.02, 0.05, 0.10}`; `α_main` = largest grid value ≤ `μ_pilot / 2`, with `μ_pilot` = μ of M1 at levels 2–3 in E0 (default 0.02). Frozen on 10/11. | If `μ ≤ α`, CRC executes everything and the comparison is empty. Choosing α from the pilot (not the main set) keeps it pre-registered. |
| **Per-group CRC at every α; C5 at `α_F3`.** Per-group CRC (spec 12 §2.2) runs on the whole α grid and T3 always has its row at `α_main` (coverage + # fully deferred groups). `α_F3` = smallest grid α with `α ≥ α_main` such that, in the median split, every group `ĉ` has `n_cal ≥ min_n(α)`; `α_F3 = α_main` when `α_main` qualifies. `α_main` is **never** changed for per-group CRC. Decided 06/11. | Below `min_n(α)` a group is fully deferred, so "every group ≤ α" holds trivially and proves nothing. The rule uses only group **counts** (`ĉ` from `ê`), never harm labels, so it does not peek at results. |
| **Operational metric first.** C3 is judged by CRC coverage at `α_main` (what an operator gains) plus a significance test on AUROC; AURC is supporting. | A fixed "AUROC + 0.05" threshold is arbitrary; reviewers care whether automation goes up at the same risk. |
| **Only three primary comparisons**: `ALL` vs `LLM`, `SOLVER` vs `LEARNED`, `SOLVER` vs `L6`. Everything else is descriptive. | Avoids a multiple-comparisons fishing trip across ~15 score sets. |
| **Fit split = 30% of routes** (was 20%). | G1 (learned guardian) needs enough positives (~60–90) to be a fair baseline; with 20% it would be under-trained and look like a straw man. |
| **Human set ~200 items, 2 writers**; tables pool them, per-writer result in one sentence. | ~150 items gives too few harmful errors for any CI; two writers show the result is not one person's style. |
| **Non-executable outputs stay in every denominator.** | Otherwise a model that fails to parse often looks artificially safe. |


Notation per translator model, on a set of `N` items: `x_i = 1` if the LLM output is executable (parsed and feasible), `h_i ∈ {0,1}` harm label (defined when `x_i = 1`), `s_i` risk score (higher = riskier), `d_i = 1` if deferred. Executed = `x_i = 1 and d_i = 0`. Non-executable items are always deferred and **stay in every denominator `N`**.

### 14.1 Error landscape (E1, T1)

| Metric | Formula | Note |
|---|---|---|
| **μ** (base harm rate) | `Σ x_i h_i / N` | primary; harm if we execute everything executable |
| Parse / infeasible rate | `#parse_error / N`, `#infeasible / N` | |
| String error rate | `Σ x_i · 1[ê_i ≢ e*_i] / Σ x_i` | canonical equivalence (spec 06 §5) |
| Harmless-error share | `#(x=1, ê≢e*, h=0) / #(x=1, ê≢e*)` | supports C1 |
| Non-binding share | `#(h=1, P̂=P) / #(h=1)` | supports C1' |

### 14.2 Signal quality (E2, E4, E6, T2, F2)

| Metric | Formula | Note |
|---|---|---|
| **AUROC** | `roc_auc_score(h, s)` on items with `x = 1` | primary for single signals |
| **AURC** | sort executable items by `s` ascending; `r_k` = mean `h` of the first `k`; `AURC = (1/n_x) Σ_k r_k` | primary for score sets; lower is better (P16) |
| Recall@20% (non-binding) | defer the 20% highest-`s` executable items; share of non-binding harmful errors among them | secondary |
| Risk–coverage curve (F2) | for each threshold: coverage `= Σ x(1−d)/N`, joint risk `= Σ x(1−d)h/N` | plotted with always-execute and oracle |

### 14.3 Risk control (E3, E5, E6, T3)

| Metric | Formula | Note |
|---|---|---|
| **Coverage** | `Σ x_i(1−d_i) / N_test` | primary at `α_main` |
| **Realized joint risk** | `Σ x_i(1−d_i)h_i / N_test` | must be ≤ α **on average** over splits |
| Realized conditional risk | `Σ x(1−d)h / Σ x(1−d)` | `runs/` only; not controlled, not in the paper (LTT cut 2026-11-07) |
| Violation frequency | share of the 100 splits with realized joint risk > α | descriptive: CRC bounds the **mean**, not this frequency |
| **Per-group risk** | realized joint risk within group `ĉ` = op type of the LLM edit (denominator: executable items with that `ĉ`) | **controlled** by per-type CRC (spec 12 §2.2); max over groups in T3 |
| Per-type risk (gold) | realized joint risk within gold op type `c` (denominator `N_c`, all items) | `runs/` only (analysis); not in the paper |
| Harm prevented /1k | `1000 · (H_always − H_policy) / N_test`, `H` = # harmful executions; same for late minutes and window violations | C8; one sentence in text |
| Workload | `1 − coverage` | |

### 14.4 Uncertainty and agreement

- Single-sample metrics (AUROC, AURC, μ): 95% CI by **route-level bootstrap**, 1,000 resamples, percentile interval. Differences (e.g. `AUROC_ALL − AUROC_LLM`) bootstrapped as paired differences on the same resample.
- Split-based metrics (coverage, realized risk): mean ± sd over 100 splits.
- Agreement: Cohen's κ. Label stability V1: share of items whose `h` changes.

### 14.5 Primary metric per table

| Output | Primary | Secondary |
|---|---|---|
| T1 | μ by model × level | non-binding share, harmless share, parse/infeasible |
| T2 | AUROC and AURC per score set (`LLM`, `LEARNED`, `L6`, `SOLVER`, `ALL`); AUROC of S1–S5 | recall@20% non-binding (one sentence); human-set column |
| T3 | coverage at `α_main` | mean realized joint risk, violation frequency, max per-group risk (`ĉ`), # fully deferred groups (per-group CRC row always present); one station-shift row and one human row |
| T4 | share of each error type | % caught (top-20% risk) by SOLVER / LLM / ALL |
| F2 | risk–coverage curves | — |

### 14.6 Success criteria per claim (decided before seeing main results)

| Claim | Holds if | If not |
|---|---|---|
| C1 | harmless-error share ≥ 10% of string errors, CI excludes 0 | drop the "string ≠ plan" sentence; keep harm definition |
| C1' | non-binding share ≥ 20% of harmful errors (pooled over models) | report the number, drop "substantial" |
| C2 | μ(level 3) − μ(level 1) > 0 with CI excluding 0, for both translators | report per model |
| **C3** | paired bootstrap CI of `AUROC_ALL − AUROC_LLM` excludes 0 **and** CRC coverage at `α_main` is ≥ 5 percentage points higher for `ALL` than `LLM` (mean over splits), for both translators; `AURC_ALL ≤ AURC_LEARNED` | claim only for the translator(s) where it holds; if L6 beats SOLVER, rephrase as "plan-level feedback" |
| C3' | for ≥ 3 of 5 named error types, SOLVER catches more than LLM | report table without the claim |
| C4 | mean realized joint risk over 100 splits ≤ α + 0.005 (Monte-Carlo slack) | report as a bug; investigate before 22/11 |
| C5 | at `α_F3` (§14.0): with global λ, ≥ 1 group `ĉ` has mean per-group risk > α; with per-type CRC all groups ≤ α + 0.005 | state that a single λ was sufficient; if no grid α qualifies for `α_F3`, report C5 as not testable at this data size |
| C6 | descriptive, station shift only (no threshold) | — |
| C7 | on the human set, `AUROC_ALL > AUROC_LLM` for both translators (point estimate), CI reported; per-writer direction in one sentence | phrase as "direction consistent / inconclusive" |
| C8 | descriptive: harm prevented at `α_main` | — |
| Validity | κ ≥ 0.6 and ≥ 90% "yes" in review; V1 flip rate < 1% | fix generator / solver before E1 |

### 14.7 Is the benchmark good enough? (checked before E1, reported in Benchmark section)

| Property | Check | Target |
|---|---|---|
| Correct labels | human review of 300 items (spec 08 §6) | ≥ 90% "yes", κ ≥ 0.6 |
| Stable labels | V1 | < 1% flips |
| Not trivial | μ of M2 at level 3 | > 0 with CI excluding 0 |
| Graded difficulty | μ by level, both translators | increases from level 1 to 3 |
| Diverse phrasing | ≥ 3 templates per op × level; distinct-bigram ratio of `q` reported for template / paraphrase / human | paraphrase and human ≥ template |
| Close to real language | μ and AUROC ranking on human set vs main (E6) | same direction; gap reported |
| No leakage | route-level splits; human routes disjoint from main and pilot | test passes (spec 12) |
| Enough positives | harmful errors per model in each test half | ≥ 30 for M1; if M2 < 30, M2 results are descriptive |

The paper (§V) reports only κ, % "yes" and the human keep rate; the other checks go to `data/benchmark/main/README.md`.

