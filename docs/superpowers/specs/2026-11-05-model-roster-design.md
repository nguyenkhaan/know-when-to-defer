# Model roster and API budget (Task 0.3) — design

> Status: Approved · 2026-11-05 · Decision record for `plans/phase-0-setup.md` Task 0.3 Steps 1–2. Prices taken from the OpenRouter API (`/api/v1/models`, `/endpoints`) on 2026-11-05.

## 1. Intent

Fix the five models (M1–M5) and per-model `max_usd` so that Phase 0b, the pilot (E0) and the main run all fit in a **hard total API budget of 10 USD**, with every API model reached through **OpenRouter** (OpenAI-compatible endpoint).

## 2. Constraints

- Total API spend for the whole project ≤ 10 USD (user decision, 2026-11-05).
- Every API model: OpenAI-compatible, supports `seed` on the pinned provider.
- M1 must return `logprobs` (signal L4, spec 11 §3).
- M3 ≠ M4, and both are from a different model family than M1 and M2 (spec 10 §2).
- Reasoning/thinking is disabled or set to the lowest level, to keep output tokens and cost predictable.

## 3. Approaches considered

| Option | M1 | M2 | Est. main-run cost | Verdict |
|---|---|---|---|---|
| A. Spec default | Qwen2.5-7B-Instruct | frontier (GPT-6-sol / Sonnet 5.5) | > 25 USD | Rejected: over budget; Qwen2.5-7B has a single provider (Phala) **without logprobs** on OpenRouter |
| B. Cheapest | Nemotron 3.5 Lightning | DeepSeek V4 Flash | ~5.5–6 USD | Considered; user preferred to keep a Qwen model as M1 |
| C2. Free judge | — | — (M4 = `nvidia/nemotron-3.5-lightning:free`) | saves ~1.5–2 USD | Rejected: free tier allows 1,000 requests/day vs ~22k judge calls in 12 days; 3B-active judge weakens L5/L6; no `response_format`; may be withdrawn |
| C. NVIDIA large | — | Nemotron 3 Ultra 550B | M2 alone ~9–10 USD | Rejected: more expensive, not cheaper |
| **D. Chosen** | **Qwen3.5-9B** | **DeepSeek V4 Flash** | **~7–8 USD** | User choice: keeps the Qwen family for M1, stays under 10 USD |

## 4. Roster (decided)

| ID | Role | OpenRouter model id | Pinned provider (fallback) | in / out / cache-read, USD per 1M tokens | Settings |
|---|---|---|---|---|---|
| M1 | Translator · small open | `qwen/qwen3.5-9b` | Darkbloom (Parasail) | 0.08 / 0.13 / 0.04 (Parasail: 0.10 / 0.25 / –) | thinking off; `logprobs: true` |
| M2 | Translator · strong (budget) | `deepseek/deepseek-v4-flash` | DeepInfra (GMICloud) | 0.09 / 0.18 / 0.018 | thinking off |
| M3 | Paraphraser | `meta-llama/llama-3.3-70b-instruct` | DeepInfra | 0.10 / 0.32 / – | temperature 0.9 |
| M4 | Judge (L2, L5, L6, paraphrase meaning check) | `openai/gpt-oss-120b` | AkashML (DeepInfra) | 0.03 / 0.19 / 0.03 (DeepInfra: 0.037 / 0.17 / –) | reasoning effort `low` |
| M5 | Embedding (G1) | `BAAI/bge-small-en-v1.5` | local CPU (`sentence-transformers`) | 0 | — |

Families: Qwen (M1), DeepSeek (M2), Llama (M3), OpenAI gpt-oss (M4) — all distinct.

Every request sets `provider: {order: [<pinned>, <fallback>], allow_fallbacks: false, require_parameters: true}`, so OpenRouter never silently routes to a provider without `seed`/`logprobs`. Fallback providers are used only by editing the config, and the provider actually used is logged with each call.

## 5. Budget (`configs/llm.yaml`)

Volume assumptions (spec 10 §5): ~3,500 translated items (pilot 300 + main 3,000 + human 200) × 5 calls × ~3k input tokens ≈ 52M input tokens per translator; judge ≈ 37M input tokens; ~70% of input tokens hit the prompt cache. The cache rate is unverified until the pilot measures it.

| Model | Estimate | `max_usd` |
|---|---|---|
| M1 | ~2.9 | 3.00 |
| M2 | ~2.4 | 2.50 |
| M3 | ~0.4 | 0.50 |
| M4 | ~1.5–2.0 | 2.00 |
| **Allocated** | | **8.00** |
| Reserve (smoke test, reruns, overruns) | | 2.00 |

If the pilot shows the main run will exceed these caps, reduce the main-set size or `k` (spec 13 §3) before touching the reserve.

## 6. Risks

- **Weak M2.** DeepSeek V4 Flash is a strong budget model, not a frontier model. The paper should call M2 "a strong low-cost API model". If M2 makes almost no harmful errors, the results rest on M1 (already planned, phase 0b).
- **Single cheap provider.** If Darkbloom drops out, Parasail costs ~1.5× more and has no cache.
- **Cache rate.** Below ~40% cache hits, M1 + M2 may exceed their caps; the pilot cost report decides.

## 7. Left to the builder (Task 0.3 Steps 3–5)

- `configs/llm.yaml` schema (model id, provider order, params, `max_usd`, prices for the cost estimator).
- `scripts/ping_models.py` checks that each pinned provider returns `seed`-honoring output, M1 returns logprobs, and thinking is actually off (no reasoning tokens billed).
- Update spec 10 §2 and `docs/CONTENT.md` §6 with this roster.
