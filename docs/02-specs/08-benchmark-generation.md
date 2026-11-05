# 08 · Benchmark Generation

> Status: Draft v0.2 · Updated 2026-11-05 · v0.2: main set ~3,000 items; paraphraser = M3; new §10 human-written test set.

## 1. Purpose

Build a set of dispatcher requests over real LMRC snapshots with **reproducible ground truth**. Key idea: **sample the gold edit first, then write the sentence**, so the label is known by construction. No per-item human labeling is needed.

## 2. Pipeline per item

1. Pick a snapshot `P` (spec 05).
2. **Sample gold** `e*` (1 op, or 2–3 ops for compound items) from the op mix in §3.
3. **Check** `solve(P, e*)` is feasible; record `gold_binding = (P*.digest != P.digest)`.
4. **Verbalize** `e*` → request `q` with a template for the target ambiguity level (§4).
5. **Paraphrase** `q` with an LLM (§5); reject paraphrases that fail the meaning check.
6. Save a `BenchmarkItem`.

## 3. Gold sampling rules

- Ops are sampled to balance **op type × ambiguity level** (each cell ≥ 100 items in the main set).
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
- Level 1 is the control condition; the pilot and main set put **most items in levels 2–3**: target split 20% / 40% / 40%.

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
    ops: list[str]              # op types in gold
    level: Literal[1, 2, 3]
    q_template: str
    q: str
    template_id: str
    paraphraser: str
    seed: int
```

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
- [ ] Stats table: items per op × level, % binding, mean request length.
- [ ] Human review done on 300 items with κ and % "yes" reported (target ≥ 90% yes).
- [ ] Human-written set: ≥ 150 kept items (target 200) from 2 writers, keep rate reported per writer.
