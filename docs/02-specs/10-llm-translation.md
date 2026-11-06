# 10 · LLM Translation

> Status: Draft v0.4 · Updated 2026-11-07 · v0.4: prompt uses `editset_json_schema()` (spec 06 §6). · v0.3: final roster on OpenRouter (§2). v0.2: 5-model roster (medium translator dropped), cost controls, all models via API (no GPU).

## 1. Purpose

Translate `(P, q)` into an `EditSet` `ê` (spec 06), plus the raw material for LLM-side signals: k samples, verbalized confidence, token log-probs.

## 2. Models (5 total)

The machine has no GPU, so open-weight models are called through a hosted API (OpenAI-compatible endpoint).

All API models go through **OpenRouter**, each pinned to one endpoint (`provider.order`, `allow_fallbacks: false`, `require_parameters: true`). Final pick 2026-11-05 (Task 0.3); config: `configs/llm.yaml`; rationale: `docs/superpowers/specs/2026-11-05-model-roster-design.md`.

| ID | Role | Model (OpenRouter id) | Pinned endpoint | Price in / out / cache, USD per 1M | `max_usd` | Notes |
|---|---|---|---|---|---|---|
| M1 | Translator · small open | `qwen/qwen3.5-9b` | `darkbloom/fp4` | 0.08 / 0.13 / 0.04 | 3.0 | thinking off; **logprobs returned**; expected higher `μ` |
| M2 | Translator · strong low-cost | `deepseek/deepseek-v4-flash` | `deepinfra/fp8` | 0.09 / 0.18 / 0.018 | 2.5 | thinking off; logprobs `NA`. Not a frontier model (budget); call it "a strong low-cost API model" in the paper |
| M3 | Paraphraser (spec 08) | `meta-llama/llama-3.3-70b-instruct` | `deepinfra/turbo` | 0.10 / 0.32 / – | 0.5 | used only at benchmark build time |
| M4 | Judge (L2, L5, L6; paraphrase meaning check) | `openai/gpt-oss-120b` | `akashml/fp4` | 0.03 / 0.19 / 0.03 | 2.0 | reasoning effort `low`; called only on executed items |
| M5 | Embedding (G1 baseline, spec 11) | `BAAI/bge-small-en-v1.5` | local CPU (`sentence-transformers`) | 0 | 0 | no API cost |

Total API budget 10 USD: 8 USD allocated above + 2 USD reserve. Qwen2.5-7B (v0.1 proposal) was dropped: its only OpenRouter provider returns no logprobs. A free judge (`nvidia/nemotron-3.5-lightning:free`) was rejected: 1,000 requests/day cannot cover ~22k judge calls in Phase 3–4, and a 3B-active judge would make L5/L6 weak baselines.

Dropped vs v0.1: the optional medium translator (Qwen2.5-14B). Rules: the judge and paraphraser are never the translator of the same row; M3 ≠ M4.

## 3. Prompt (single template, versioned)

```
SYSTEM: You convert a dispatcher's request into route edits.
Output ONLY JSON matching this schema: <editset_json_schema()>
Use stop names exactly as listed. Times are local HH:MM.
Add "confidence": 0-100 = how sure you are the edits match the request.

USER:
<render_snapshot(P)>          # spec 05 §6
Request: "<q>"
```

- No few-shot examples in v0.1 (keeps prompts short); add 2 fixed examples only if the pilot parse-error rate > 10%.
- Store the template under `src/kwd/llm/prompts/translate_v1.txt`; the version string goes into every record.

## 4. Sampling

| Call | Temperature | Count | Use |
|---|---|---|---|
| Greedy | 0 | 1 | the edit `ê` that would be executed |
| Samples | 0.7 | `k = 4` (config) | self-consistency, plan-level disagreement (spec 11) |

- Request JSON mode / structured output when the backend supports it.
- Log-probs: keep the mean token log-prob of the greedy output when the provider returns them.

## 5. Cost controls

| Lever | Setting |
|---|---|
| Main benchmark size | **~3,000 items**, ~300 routes × ~10 items |
| Samples | `k = 4` |
| Prompt order | system + DSL schema + **snapshot first**, request last ⇒ items on the same route share a long prefix ⇒ provider prompt caching applies |
| Snapshot rendering | compact table (≤ ~2.5k tokens for 150 stops): order, name, category, zone, ETA, window; no coordinates |
| Judge calls | only on executed items (parse OK and feasible) |
| Budget guard | `max_usd` per model in `configs/llm.yaml`; `kwd translate` stops when the running estimate exceeds it |
| Pilot | E0 measures real cost per item; extrapolate before the main run (spec 13 §3) |

## 6. Cache and logging

- Cache key: `sha256(model, prompt_version, rendered_prompt, temperature, sample_idx, seed)`. Store on disk (`data/cache/llm/`), never delete during the project.
- Every call logs latency and token counts → cost table for the paper's setup section.

## 7. Data model

```python
class Prediction(BaseModel):
    item_id: str; model: str; prompt_version: str
    greedy_raw: str
    greedy: EditSet | None          # None if parse error
    parse_error: str | None
    samples_raw: list[str]
    samples: list[EditSet | None]
    verbalized_conf: float | None   # 0..1
    mean_logprob: float | None
```

File: `runs/<run_id>/predictions/<model>.jsonl`.

## 8. Acceptance criteria

- [ ] `kwd translate --model <m> --items <file>` is resumable (skips cached items).
- [ ] Parse-error rate reported per model; pilot target < 10%.
- [ ] Re-running with cache hits produces byte-identical output files.
- [ ] Cost/latency summary per model printed at the end; budget guard stops the run when `max_usd` is reached.
