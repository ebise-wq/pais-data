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
- A chart can carry a `"toggle"` (another PNG with the same layout and a button label). The page
  shows a two-way switch between the two images. Draw both views from one function so they line up.
- Data files show in a collapsed block under each section's charts.
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
