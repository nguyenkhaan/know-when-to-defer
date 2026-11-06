# lmrc_mini

One real LMRC route cut down to 12 stops (depot + the first 11 drop-offs of the actual
sequence), in the same four-file layout as the raw data. Used by `tests/data/`.

- Route: `RouteID_00143bdd-0a6b-49ec-bb35-36593d303e77` (station DLA3, score High).
- Positions are renumbered `0..11`. `stops`, `package_data` and both the rows and the columns
  of the travel matrix are cut to the same 12 stops; nothing else was changed.
- The bare `NaN` tokens of the raw files are kept on purpose (they are not valid JSON): the
  tests depend on them. Do not reformat these files with a strict JSON tool.

Rebuild with `uv run python scripts/make_lmrc_fixture.py` (needs `data/raw/lmrc/`).

## Source and license

Amazon Last Mile Routing Research Challenge 2021 dataset (Merchán et al., 2022), from the AWS
Open Data bucket `s3://amazon-last-mile-challenges/almrrc2021/`, training split. Licensed under
[CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/): non-commercial use only,
attribution required. This excerpt was modified as described above.
