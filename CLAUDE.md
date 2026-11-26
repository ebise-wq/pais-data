# Working in pais-data

## Branches
- `main` is the only long-lived branch. Each session's work should end up merged into `main`.
- Start new work from the latest `main`. When a session's work is finished and committed, merge it
  into `main` (ask first if the user hasn't said to).
- On 2026-11-25 all session branches were merged into `main` except `ccr-12a2e595-h65a6a`.
  That one holds a single commit (34f0494) that pooled Crohn's and UC into one IBD query. The
  later work replaced it by plotting Crohn's and UC separately, so it was left out on purpose.
  The other old `ccr-*` branches are fully contained in `main` and can be deleted.

## Catalog page
- `docs/index.html` and the catalog section of `README.md` are generated. Do not edit them by hand.
- GitHub Pages serves `docs/` from `main` at https://ebise-wq.github.io/pais-data/ . Pages sees only
  `docs/`, so the page loads chart images from raw.githubusercontent.com on `main`. A new chart
  shows on the page only after it is merged into `main`.
- Every chart and data file must have an entry in `catalog.json` (title, one-line description,
  the script that makes it). Mark superseded items with `"old": true` instead of deleting them.
- After adding or changing outputs, run `python3 -I tools/build_catalog.py` and commit the result.
  `--check` exits non-zero if any chart or data file is missing from the catalog.
- A section with `"hidden": true` stays in `catalog.json` (so `--check` passes) but is left off the
  page and the README. The first 13-disease comparison is hidden this way at the user's request.
- A chart can carry a `"toggle"`: one or a list of other PNGs with the same layout, each with a button
  label. The page shows a switch between them. Draw all views from one function so they line up.
- The build writes `docs/index.html` (overview) and one page per section (`docs/<section id>.html`).
  The overview links to each with "Open page".
- A section can carry `"interactive"` (an HTML fragment plus its JSON data), e.g. the 120-disease
  burden charts in `expanded/burden_interactive.html`. Its CSS classes and ids start with `bvr-` so
  they don't clash with the page. The parts between `<!-- more:start -->` and `<!-- more:end -->`
  (replaced by a link) and between `<!-- page-only:start -->` and `<!-- page-only:end -->` (dropped)
  show on the topic page only. The headline-number boxes are page-only at the user's request.
- A section can carry `"subsections"` (same fields as a section, minus interactive). They show at the end
  of its topic page, with a link line on the overview; `docs/<subsection id>.html` redirects there.
  The WHO ICTRP analysis is a subsection of the 120-disease section this way.
- An interactive's `"data"` can be a map `{"name": path}`; the fragment then gets an object of those
  tables (used by `clinicaltrials/per_year_interactive.html`).
- Data files show in a collapsed block under each section's charts.
- A data entry with `"hidden": true` is catalogued but not shown: use it for pipeline inputs whose
  contents already appear in another table (e.g. `sex/sex_labels.csv`, `expanded/cleaned_counts_*.csv`).
- Keep the number of files low: add columns or rows to an existing table rather than a new small file,
  put short tables and search strings in the folder README, and never save the same data in two shapes.
- Bump `page_version` in `catalog.json` whenever the page changes, so the user can tell which
  version is showing.
- The page is also published as a private claude.ai artifact:
  https://claude.ai/artifact/5uV4e1v6e69pmemxP1HQro . To update it, run the build with
  `--fragment <scratchpad>/pais-catalog.html` and republish that file to this URL with the
  Artifact tool, passing every chart PNG in `files` under its repo path.

## Conventions
- Run scripts from the repo root with `python3 -I <folder>/<script>.py`.
- Put the pull date in data file names (`counts_2026-11-08.csv`). Keep API caches in `cache/`
  folders, which are git-ignored.
- Charts: dark background `#141a24`, ink `#eef1f6`, muted `#a3acba`, ocean `#7fb3d5`, sunset
  `#f4a582`; Inter; sized for phone screens; a small version number in a corner.
- Each folder has a README with method, choices, results and caveats. Update it with the outputs.
