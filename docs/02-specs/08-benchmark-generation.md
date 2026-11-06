# 08 · Benchmark Generation

> Status: Draft v0.6 · Updated 2026-11-07 · v0.6: fixed-point filter reported in one sentence of paper §V, no separate §VII limitation. · v0.5: op mix balanced per op and per level instead of per op × level cell; level 3 is half compound, half implicit single-op (§3, §4, decided 07/11). v0.4: snapshots must be solver fixed points (§2.1, decided 06/11). v0.3: `gold_type = op_type(gold)` (spec 06 §5.1) is the only source of gold type `c`; `gold_binding` uses the digest of spec 07 §5 (order + service times). · v0.2: main set ~3,000 items; paraphraser = M3; new §10 human-written test set.

## 1. Purpose

Build a set of dispatcher requests over real LMRC snapshots with **reproducible ground truth**. Key idea: **sample the gold edit first, then write the sentence**, so the label is known by construction. No per-item human labeling is needed.

## 2. Pipeline per item

1. Pick a snapshot `P` (spec 05) that passes the **fixed-point filter** (§2.1).
2. **Sample gold** `e*` (1 op, or 2–3 ops for compound items) from the op mix in §3.
3. **Check** `solve(P, e*)` is feasible; record `gold_binding = (P*.digest != P.digest)`. The digest covers order and service-start times (spec 07 §5), so a gold edit met only by waiting counts as binding.
4. **Verbalize** `e*` → request `q` with a template for the target ambiguity level (§4).
5. **Paraphrase** `q` with an LLM (§5); reject paraphrases that fail the meaning check.
6. Save a `BenchmarkItem`.

### 2.1 Fixed-point filter (decided 2026-11-06)

Keep a snapshot only if `solve(P, ∅).digest == P.digest` (`is_fixed_point`, spec 07 §5): with no edit, the solver returns the current plan unchanged in order and service times.

- **Why:** a non-binding error is defined by `P̂ = P` (paper §III, spec 09 §4), and `gold_binding` by `P*.digest != P.digest`. Both are meaningful only if the solver does not rewrite `P` on its own. `P` is the real LMRC driver order, which the solver can sometimes improve.
- **Measured** 2026-11-06 (throwaway probe of spec 07 §2–§4 on 20 eligible routes, default `dev_weight` = 2 min): 18/20 are fixed points. One failure fixes 9.9 min of lateness on original windows; one shortens travel by 6.8 min. Expect ~10% of routes to fail (95% CI roughly 3–30%).
- **Replacement:** a failing route is replaced by the next route of the same station from the seeded reserve list (spec 05 §3); `ρ` is not redrawn.
- **Report** in `README.md` and in **one sentence** of paper §V: number of routes dropped and how many of them were late on original windows in `P`, so routes already running late are under-represented (no separate §VII limitation).
- **Scope of the guarantee:** calibration and test both come from filtered snapshots, so exchangeability holds and the CRC bound applies to fixed-point snapshots. The filter needs no gold, so a deployed system can apply the same check at request time (if the current plan is not a fixed point, re-plan first or defer), which keeps the bound meaningful in deployment. State this in one clause next to the filter sentence (paper §V).
- Non-binding behaviour **with** an edit is not implied by this filter; it is checked in the pilot (spec 13 E0): for non-binding gold, `P*.digest == P.digest` on every item.

## 3. Gold sampling rules

- **Op mix** (decided 2026-11-07): levels 1 and 2 hold single-op items; level 3 is **half compound** items (2–3 ops) and **half single-op items with an implied intent** (§4). Single-op items are spread evenly over the ops at every level, and compound items draw their ops evenly too. Main set (~3,000 items, levels 20/40/40): ~2,400 single-op items and ~600 compound items (20%).
- **Balance check** (main set): every op has **≥ 250 single-op items** summed over the three levels, and every op × level cell is non-empty with ≥ 3 templates (spec 13 §14.7). Why 250: per-group CRC needs `min_n(0.02) = 49` calibration items per group `ĉ` (spec 12 §2.2), and calibration holds ~35% of the main set (70% × 50%), so ~140 items per op plus room for non-executable outputs. The check holds with 6, 7 or 8 ops (~400 / ~343 / ~300 single-op items per op), so it does not depend on the op list frozen after the pilot. Balance uses the sampled op names `ops` (§7); since `deadline` and `set_time_window` share one group `ĉ`, that group is about twice as large.
- Arguments are realistic and relative to the snapshot:
  - time-window bounds: rounded to 15 min, within `[t_now + 15, shift_end − 30]`;
  - `set_time_window` targets: mostly stops **without** an existing window;
  - `precedence`: pairs where the current order is `after → before` (binding) or already correct (non-binding), per the target mix.
- **Binding mix**: target ~70% binding / ~30% non-binding gold. Non-binding gold is realistic ("just make sure…") and tests whether harm labeling and signals behave sensibly.
- Infeasible gold ⇒ resample (max 20 tries), else skip the snapshot.

## 4. Ambiguity levels

| Level | What changes | Example (`set_time_window(Mercy Hospital, 15:00, null)`) |
|---|---|---|
| 1 · Explicit | exact name, exact time, explicit direction | "Mercy Hospital can only receive deliveries from 3 pm onward." |
| 2 · Indirect | stop referred to by category / position / zone; time relative to now; vague direction words | "The hospital can't take anything for another couple of hours." (t_now = 13:00) |
| 3 · Compound / implicit | 2–3 edits in one message, or intent implied by a reason | "Nobody's at the hospital receiving desk until 3, and the pharmacy needs to come before the school." |

Generator constraints:

- Level 2 references must **resolve to exactly one** remaining stop (e.g. use "the hospital" only if one hospital remains). Checked by a resolver; otherwise fall back to level 1 phrasing.
- Relative times ("in two hours") are computed from `t_now` and rounded as in the gold.
- Level 1 is the control condition; the pilot and main set put **most items in levels 2–3**: target split 20% / 40% / 40%. Level 3 is split half compound, half implicit single-op (§3).

## 5. Paraphrase

- Language: **English** (paper and evaluated LLMs). A Vietnamese variant is a possible extension, not in scope.
- Paraphraser: M3 (spec 10 §2), an LLM **different** from the evaluated models (to avoid "self-paraphrase" bias), temperature 0.9, prompt: *rewrite like a busy dispatcher; keep every fact; do not add facts*.
- **Meaning check**: a judge prompt compares `q` with `q_template` only (*were any facts added, dropped or changed?*). If yes, reject and retry (max 3); keep the template sentence if all fail.
- ⚠️ Do **not** filter paraphrases by whether an LLM can translate them back into `e*`. That would keep only easy items and push `μ` down (selection bias).
- Store both `q_template` and `q` (paraphrased). Experiments use `q`.

## 6. Human review

- Sample **300 items** stratified by op × level.
- Two annotators independently answer: *Does the gold edit exactly capture what the sentence asks? (yes / no / ambiguous)*.
- Report agreement (Cohen's κ) and the % "yes". Items marked "no" by both ⇒ fix the template / generator rule, regenerate.
- A minimal review tool: a script that prints `render_snapshot(P)`, `q`, and `e*` and records the answer in a CSV. No UI work.

## 7. Data model

```python
class BenchmarkItem(BaseModel):
    item_id: str
    snapshot_id: str
    gold: EditSet               # evaluation-only
    gold_binding: bool          # evaluation-only
    ops: list[str]              # raw op names sampled for gold; generation balance only (§3), never used as c
    gold_type: str              # c = op_type(gold, P), spec 06 §5.1; the only gold type used in analysis
    level: Literal[1, 2, 3]
    q_template: str
    q: str
    template_id: str
    paraphraser: str
    seed: int
```

`gold_type` is written by the generator by calling `kwd.dsl.op_type`; no code may derive `c` from `ops` (e.g. a `deadline` item has `ops = ["deadline"]` but `gold_type = "set_time_window"`).

Files: `data/benchmark/{pilot,main}/items.jsonl` + `README.md` (stats, generator config hash).

## 8. Sizes

| Set | Routes | Items | Use |
|---|---|---|---|
| Pilot | ~30 | ~300 | go/no-go (spec 13 E0) |
| Main | ~300 | ~3,000 | all experiments |
| Human | ~40 (held out) | ~200 | E6 realistic-language test (§9) |

Splits are **by route** (spec 12), so items of the same route never straddle calibration and test.

## 9. Human-written test set (E6)

Purpose: check that results hold on language people actually produce, not only on templates and paraphrases.

1. Pick ~40 routes **not** in the main or pilot set; build snapshots; sample ~200 gold edits with the same op mix (§3), including ~50 compound ones.
2. For each gold, make an **intent card** (A writes 6–8 situation templates per op): the snapshot table + a short situation ("the hospital called: their receiving desk opens at 15:00 today"). The gold itself stays hidden.
3. **Two writers**, ~100 requests each: **B** (team member kept blind to templates until done) and **C** (external helper, never sees templates or code). They write: *"Write the message you would type to a routing assistant. Be natural; short, vague or informal is fine."* They must not see templates or paraphrases.
4. **Check**: A (not the writer) reads the snapshot + request (without the card) and marks whether the card is a reasonable reading (`yes / no`). Keep `yes` items; report the keep rate.
5. Store as `data/benchmark/human/items.jsonl` with `level = 0` (human) and `writer_id`.

Card format: a **situation** (what happened in the world, may be in Vietnamese) + a marker on the route table; **no** English sentence stating the edit, so writers cannot copy it. Cost: ~2 h per writer + ~2 h of checking by A. Collect during 11–13/11.

## 10. Acceptance criteria

- [ ] Re-running the generator with the same config reproduces identical `items.jsonl` (template stage; paraphrase cached).
- [ ] Every item: gold feasible, references resolve uniquely, level label consistent with the template used.
- [ ] Stats table: single-op items per op × level, compound items per level, % binding, mean request length; the balance check of §3 passes.
- [ ] Human review done on 300 items with κ and % "yes" reported (target ≥ 90% yes).
- [ ] Human-written set: ≥ 150 kept items (target 200) from 2 writers, keep rate reported per writer.
