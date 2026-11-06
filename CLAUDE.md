# Know When to Defer — IEEE MOST 2027

Research project: risk-controlled execution of LLM-translated dispatcher edits for last-mile route re-planning.
Start from `docs/CONTENT.md`; implementation plans live in `docs/plans/`.

## Project skills (`.claude/skills/`)

Use the matching skill whenever a task falls in one of these areas, even if the request does not name it.
The venue is an **IEEE conference** (IEEEtran `conference`, 8 pages incl. references, double-blind), not a journal or NeurIPS.

| Task | Skill |
|---|---|
| IEEEtran formatting, page limit, IEEE reference style, anonymization | `ieee-transactions` |
| Checking current MOST 2027 rules, inspecting the submission PDF (fonts, pages) | `venue-templates` |
| Drafting or restructuring paper sections (Intro, Method, Results) | `ml-paper-writing` |
| Abstract, title, keywords | `abstract-and-title` |
| Polishing any English prose in `paper/` | `unslop-academic-writing` |
| Code/data availability, anonymous release, seeds, AI-use disclosure | `reproducibility-statement` |
| Checking that entries in `paper/refs.bib` exist and match metadata | `citation-verification` |
| Cleaning `refs.bib` (duplicates, preprint → published, capitalization) | `bibtex-hygiene` |
| Searching for related or competing work, novelty checks before any "first" claim | `paper-lookup` |
| Comparing signals (AUROC CIs, bootstrap, paired tests), reporting results | `statistical-analysis` |
| Sample size for pilot / human set, minimum detectable effect | `statistical-power` |
| Logistic-regression risk score, baseline G1, AUROC/AURC computation | `scikit-learn` |
| Embeddings for baseline G1 (`bge-small-en-v1.5`, CPU) | `sentence-transformers` |
| Figures F2/F3 and any plot in the paper | `scientific-visualization` |
| Internal claim–evidence review before supervisor milestones | `peer-review` |

Project rules override skill defaults: never auto-repair LLM output (translation errors are what we measure),
keep API spend within `configs/llm.yaml` budgets, and never commit — suggest a commit message instead.
