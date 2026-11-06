# 04 · Architecture

> Status: Draft v0.2 · Updated 2026-11-07 · v0.2: layout and stack are in use (Python 3.12). Change them only with a stated reason.

## 1. Data flow

```
 [LMRC raw] ──(05 data)──► RouteSnapshot P
                              │
        ┌─────────────────────┴────────────────┐
        ▼ (08 benchmark: build time only)       ▼ (system run time)
  gold e* ─► request q                    request q + P
        │                                      │
        │                                (10 llm) ─► ê  (+ k samples, confidence)
        │                                      │
  (07 solver) P* = solve(P, e*)          (07 solver) P̂ = solve(P, ê)
        │                                      │
        └───────────► (09 harm) h ◄────────────┤
                                               ▼
                                    (11 signals) features ─► score s
                                               │
                                    (12 risk) λ via CRC ─► execute / defer
                                               │
                                    (13 experiments) tables, figures
```

`e*`, `P*` and `h` are **evaluation-only**. Signals (spec 11) must never read them.

## 2. Modules

| Module | Spec | Input | Output |
|---|---|---|---|
| `kwd.data` | 05 | LMRC files | `RouteSnapshot` |
| `kwd.dsl` | 06 | raw JSON | validated `EditSet`; canonical form; equivalence |
| `kwd.solver` | 07 | `RouteSnapshot`, `EditSet` | `Plan` or `Infeasible` |
| `kwd.bench` | 08 | snapshots | `BenchmarkItem` (gold + request text) |
| `kwd.harm` | 09 | `P̂`, `P*`, gold | `HarmLabel` |
| `kwd.llm` | 10 | snapshot + request | `Prediction` (greedy + k samples) |
| `kwd.signals` | 11 | snapshot, request, predictions, solver | `SignalRow` |
| `kwd.risk` | 12 | scores + calibration labels | `λ`, decisions |
| `kwd.eval` | 13 | result tables | metrics, tables, figures |

## 3. Repository layout

```
ieee-most-2027/
├── docs/                 # this spec set
├── src/kwd/              # "know-when-to-defer" package
│   ├── data/ dsl/ solver/ bench/ harm/ llm/ signals/ risk/ eval/
│   └── cli.py            # kwd snapshot | bench | translate | label | signals | risk | report
├── configs/              # YAML per step and per experiment
├── tests/                # pytest, mirrors src/kwd/
├── data/                 # gitignored: raw/ interim/ benchmark/
├── runs/                 # gitignored: one folder per run_id
├── paper/                # LaTeX (IEEEtran, conference)
└── reference-documents/  # reference PDFs (exists)
```

## 4. Stack

| Concern | Choice | Why |
|---|---|---|
| Language | Python 3.12, `uv` | fast, lockfile |
| Solver | Google OR-Tools routing (TSPTW) | open source, precedent in P5 |
| Data models | `pydantic` v2 | DSL schema validation, JSON I/O |
| Tables | `pandas` + JSONL / Parquet | simple, inspectable |
| LLMs | 5-model roster via OpenAI-compatible APIs (spec 10 §2); no GPU on the machine | open-weight model hosted; strong model as upper reference |
| Embeddings | `sentence-transformers` + `bge-small-en-v1.5` on CPU | G1 baseline, no API cost |
| Stats | `numpy`, `scipy`, `scikit-learn` | AUROC, logistic regression |
| Plots | `matplotlib` | vector PDF for LaTeX |
| CLI / config | `typer` + YAML | each step runs standalone |
| Tests | `pytest` | |
| Paper | LaTeX in **VS Code** (LaTeX Workshop) + user-level TeX (TinyTeX), `latexmk` | no system-wide install |

## 5. Design rules

1. **Every step is a CLI command: file in → file out.** Any step can be re-run alone, especially LLM calls.
2. **All LLM calls go through a disk cache** keyed by hash(model, prompt, params). Re-runs cost nothing.
3. **Deterministic solver**: same input → same output (spec 07).
4. **Evaluation isolation**: `kwd.signals` must not import `kwd.harm` nor read `gold` fields. A test enforces this.
5. **Internal time unit**: integer **seconds** since route departure (LMRC service times average ~107 s and legs ~6 min, so rounding to minutes would accumulate errors of the same size as the harm threshold ε). Convert to `HH:MM` local time only when rendering for an LLM or a human; report results in minutes.

## 6. Acceptance criteria

- [ ] `kwd --help` lists every command in §2.
- [ ] The "hospital" example (spec 14 §4) runs end-to-end with one command and yields `h = 1`.
- [ ] Isolation test passes: `kwd.signals` has no dependency on `kwd.harm` or `gold`.
