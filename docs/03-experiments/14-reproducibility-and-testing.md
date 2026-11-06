# 14 · Reproducibility, Engineering Conventions & Testing

> Status: Draft v0.1 · Updated 2026-11-06

## 1. Runs

- A **run** = one execution of a pipeline step or experiment, identified by `run_id = <YYYYMMDD-HHMM>-<short-name>`.
- Each run folder `runs/<run_id>/` contains: `config.yaml` (fully resolved), `git_commit.txt`, `env.txt` (`uv pip freeze`), outputs, `log.txt`.
- Paper numbers are produced by `kwd report` from a named run. The final run IDs are recorded in `paper/RUNS.md`.

## 2. Configuration

- YAML in `configs/`: `data.yaml`, `bench.yaml`, `solver.yaml`, `llm.yaml`, `harm.yaml`, `signals.yaml`, `risk.yaml`, `exp/e0.yaml … e5.yaml`.
- Every random choice takes a seed from config. No hidden defaults in code: defaults live in the YAML.
- Config hash (`sha256` of the resolved YAML) is stored with every output file.

## 3. Caching

| Cache | Key | Location |
|---|---|---|
| LLM calls | model, prompt version, prompt, temperature, sample idx, seed | `data/cache/llm/` |
| Solver | snapshot id, canonical EditSet, solver config hash | `data/cache/solver/` |

Caches are append-only during the project. Never cache anything keyed on gold for signals.

## 4. Test plan

| Level | What | Examples |
|---|---|---|
| Unit | each module | DSL reason codes; each solver op; harm rules R1–R3; CRC on synthetic data |
| Golden example | the **hospital case**, fixed tiny snapshot (4 stops) checked into `tests/fixtures/` | gold moves hospital to ~15:10; wrong edit leaves plan unchanged; `h = 1`; `S1 = 1`, `S3_flag = 1` |
| Integration | 10-item mini benchmark end-to-end with a **stub LLM** (returns scripted outputs) | `kwd` pipeline runs in < 2 min in CI-like local run |
| Isolation | signals never see gold | import graph test + schema test |
| Determinism | same config ⇒ same outputs | snapshot hash, solver digest, benchmark file hash |

Golden fixture (local clock; departure 13:00, `t_now` = 13:00; service 5 min at every delivery stop; shift ends 17:30). Rebuild with `scripts/make_hospital_fixture.py`, which holds the travel matrix:

| Order | Stop | Category | Zone | ETA | Original window |
|---|---|---|---|---|---|
| 1 | Minh Chau Pharmacy | pharmacy | A | 13:20 | until 14:00 |
| 2 | An Binh Hospital | hospital | A | 14:10 | none |
| 3 | Nguyen Du School | school | B | 14:45 | until 15:00 |
| 4 | Thanh Cong Shop | shop | B | 15:25 | none |

The two original windows are required. Without them the gold edit only makes the vehicle wait at the hospital until 15:00, because waiting costs nothing in the objective (spec 07 §3): the order stays the same, the plan digest does not change, and `S3_flag = 1` cannot hold. With them, an exhaustive check of the 24 orders (`test_hospital_fixture_design`) gives:

| Case | Best order | Cost | Next best |
|---|---|---|---|
| No edit | Pharmacy, Hospital, School, Shop | 180 | 196 |
| Gold: Hospital from 15:00 | Pharmacy, School, Hospital (15:10), Shop | 196 | 206 |
| Wrong: Hospital until 15:00 | unchanged | 180 | 351 |

Request: "An Binh Hospital only accepts deliveries from 3 pm." Gold `set_time_window(An Binh Hospital, 15:00, null)`; wrong `set_time_window(An Binh Hospital, null, 15:00)`.

## 5. Code conventions

- Type hints everywhere; `pydantic` models are the only cross-module data format.
- Pure functions for labeling, signals and CRC (no I/O inside); I/O in `cli.py` / thin wrappers.
- `ruff` for lint/format; `pytest -q` must pass before each commit on main.

## 6. Anonymized release

- Before submission: copy code + benchmark to a clean repo without author names, emails, institution, or git history; host via an anonymous service (e.g. anonymous.4open.science). See `04-delivery/16-submission-checklist.md`.
- Benchmark release includes: items (with gold), snapshots, generator config, license note (LMRC CC BY-NC 4.0 ⇒ non-commercial).

## 7. Paper toolchain

- Write in **VS Code** with the LaTeX Workshop extension. TeX engine: **TinyTeX** installed in the user's home (no sudo, no pacman): `curl -sL "https://yihui.org/tinytex/install-bin-unix.sh" | sh`, then `tlmgr install IEEEtran latexmk booktabs cite xcolor`.
- Build: `latexmk -pdf main.tex` (also bound to LaTeX Workshop "build on save"). Fallback if local TeX fails: Overleaf with the same `paper/` folder.

## 8. Acceptance criteria

- [ ] Fresh clone + `uv sync` + `pytest` passes.
- [ ] `kwd report --run <id>` regenerates all paper tables and figures with no manual steps.
- [ ] `paper/RUNS.md` lists the run ID behind every table and figure.
