# Know When to Defer — IEEE MOST 2027

Research project: risk-controlled execution of LLM-translated dispatcher edits for last-mile route re-planning.
Start from `docs/CONTENT.md`; implementation plans live in `docs/plans/`.
**Before editing `docs/` or `paper/`, read `docs/CONTRACT.md`.** Locked definitions there change only with the user's explicit approval, a decision-log row in `docs/CONTENT.md`, and the same edit in every file the contract lists.

**Doc drift: report, never fix silently.** If work reveals that `docs/` is wrong, contradicts itself, or no longer matches the code, and the issue matters (it changes a definition, number, rule, claim, test or what the paper reports), stop and tell the user before editing. After approval, fix the source spec (version bump + a decision-log row in `docs/CONTENT.md`), grep `docs/` for the same idea, and use CONTRACT rule 2 if a locked item changes. Typos and formatting may be fixed directly.

**Keep the paper lean.** 8 pages include references, so do not split a number, sub-case or breakdown into its own table row, column, figure panel or sentence unless a claim in `docs/01-research/02-research-questions-and-claims.md` needs it. Default: fold it into an existing metric (e.g. one parse-error rate, not one per error code), keep the detail in `runs/` for reviewers who ask, and add at most one clause of explanation. Propose a separate report only with the claim it serves.

**Paper debts (`debit-last-submit.md`, repo root).** Read it at two moments: (1) **before** drafting or revising any paper section, and (2) **after** a section is finished or when preparing the submission. List every open debt that falls in the scope being written (by section, notation, citation or parameter), and tell the user before acting on it. **Never add, edit, tick or delete a debt without first telling the user what will change and why.** Paid debts are deleted, not ticked; the decision itself goes to the decision log in `docs/CONTENT.md`.

## Project skills (`.claude/skills/`)

Use the matching skill whenever a task falls in one of these areas, even if the request does not name it.
The venue is an **IEEE conference** (IEEEtran `conference`, 8 pages incl. references, double-blind), not a journal or NeurIPS.

| Task                                                                             | Skill                         |
| -------------------------------------------------------------------------------- | ----------------------------- |
| IEEEtran formatting, page limit, IEEE reference style, anonymization             | `ieee-transactions`         |
| Checking current MOST 2027 rules, inspecting the submission PDF (fonts, pages)   | `venue-templates`           |
| Drafting or restructuring paper sections (Intro, Method, Results)                | `ml-paper-writing`          |
| Abstract, title, keywords                                                        | `abstract-and-title`        |
| Polishing any English prose in `paper/`                                        | `unslop-academic-writing`   |
| Code/data availability, anonymous release, seeds, AI-use disclosure              | `reproducibility-statement` |
| Checking that entries in `paper/refs.bib` exist and match metadata             | `citation-verification`     |
| Cleaning `refs.bib` (duplicates, preprint → published, capitalization)        | `bibtex-hygiene`            |
| Searching for related or competing work, novelty checks before any "first" claim | `paper-lookup`              |
| Comparing signals (AUROC CIs, bootstrap, paired tests), reporting results        | `statistical-analysis`      |
| Sample size for pilot / human set, minimum detectable effect                     | `statistical-power`         |
| Logistic-regression risk score, baseline G1, AUROC/AURC computation              | `scikit-learn`              |
| Embeddings for baseline G1 (`bge-small-en-v1.5`, CPU)                          | `sentence-transformers`     |
| Figure F2 and any plot in the paper                                              | `scientific-visualization`  |
| Internal claim–evidence review before supervisor milestones                     | `peer-review`               |

Project rules override skill defaults: never auto-repair LLM output (translation errors are what we measure),
keep API spend within `configs/llm.yaml` budgets, and never commit — suggest a commit message instead.
