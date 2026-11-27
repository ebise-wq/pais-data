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
- For two or more independent switches, a chart carries `"switches"` (a list; each is a list of button
  labels, and a switch with one label is an on/off pill) and `"views"`, a map from the chosen option of each
  switch ("1,0") to its PNG; the default (all zeros) is `"file"`. The trials chart uses this: drug trials /
  all trial types, and a "Commercial sponsor" pill.
- `"solid": true` on a chart means each of its PNGs has a copy on the page's green glow at `<folder>/solid/<name>`
  (charts on the page are transparent). The page links it as "Solid background" under the chart and in the
  full-size view. Chart scripts write both with a `save(fig, path)` helper.
- The build writes `docs/index.html` (overview) and one page per section (`docs/<section id>.html`).
- Topic pages (v28) are one reading column (52rem) with one chart per row, also on desktop, at the
  user's request; side-by-side grids inside fragments are forced to one column there. Charts on desktop
  should be landscape: `"wide": true` on a chart means each of its PNGs (and solid copy) has a landscape
  copy at `<folder>/wide/<name>` (solid: `<folder>/wide/solid/<name>`), shown on topic pages at
  ≥800px via `<picture>`; switches, "Full size", "Solid background" and the full-size view follow the shape
  on screen. The trials chart (all four views) and the sex scatter have wide copies; portrait charts
  without one are capped at 82vh on desktop. Interactive charts draw landscape at ≥700px wide.
- The overview is kept clean at the user's request (v16): each section shows only its title (a link to
  the topic page, with "Open page →" on the same line) and its charts. No findings, chart captions,
  README links, data files, earlier versions or subsection links; those are on the topic pages. PNG
  charts show without their caption card, and the explanation lines inside interactive fragments
  (`bvr-sub`, `fnd-sub`, `fnd-note`, `py-sub`, `pme-lede`, `hint`) are hidden by CSS under `.overview`.
- Brand (v24): the overview's title is "Data & Graphs" (`"title"` in `catalog.json`), very large, with the
  user's Substack name "How To Solve A Disease?" (`"subtitle"`) under it; its question mark takes the
  accent colour.
- Under the overview header: "By Siebe Rozendal" with links to Substack, X and LinkedIn (from `"author"`
  in `catalog.json`) and "Last updated" (the build date).
- Contents (v19): one slim bar under the header, sticky while scrolling and collapsed by default, in
  plain regular-weight text. It names the section in view; tapping it opens the list of sections over
  the page. (A headline number per section, v16-17, and an open list at the top, v18, were dropped at the
  user's request.) Topic pages have the same bar at the top (v25), not sticky, naming the current page; its
  links open the other topic pages. The user may later want search, tags and filters here; keep it simple
  until asked.
- In titles, the part after the first comma ("120 diseases", "2024") is shown small.
- A section can carry `"interactive"` (an HTML fragment plus its JSON data), e.g. the 120-disease
  burden charts in `expanded/burden_interactive.html`. Its CSS classes and ids start with `bvr-` so
  they don't clash with the page. The parts between `<!-- more:start -->` and `<!-- more:end -->`
  (replaced by a link) and between `<!-- page-only:start -->` and `<!-- page-only:end -->` (dropped)
  show on the topic page only. The headline-number boxes were removed at the user's request (v25).
  Its scatter plots use their own exporter (`window.DL_CUSTOM`), which redraws the chart off screen for
  the square version.
  Solid copies and downloads both paint the same glow as the page (light from the top left; `glow()` in
  the chart scripts, `paintBg()` in the fragment).
- Downloads (v29): every interactive chart has one "Download" button (topic pages only) that opens a menu:
  "Square image" (first; 1600 × 1600) or "As on screen". Mark the element to capture with `data-dl="<file
  stem>"`, plus optional `data-dl-skip` (selectors left out, e.g. controls), `data-dl-title` /
  `data-dl-title-from` / `data-dl-sub-from` (a header drawn above), `data-dl-source` and `data-dl-ver` (footer
  line) or `data-dl-custom` (an exporter in `window.DL_CUSTOM`). The page script adds the button, renders the
  element with html-to-image (cdnjs, loaded on first use), and puts it on the page's green glow with
  "Siebe Rozendal · How To Solve A Disease?" under it. No line about the scale or what is hidden. Parts in
  `data-dl-skip` are hidden on the page during the capture (so the image is sized without them); don't
  repeat a legend the chart already labels (e.g. the 131-disease chips). Square lays the element out at
  560px wide first (or `data-dl-square-width`; class `dl-sq` is added so CSS can change the layout, e.g.
  the PAIS diagrams side by side), waits for the charts to redraw, then centres it in the square; the
  120-disease scatter plots redraw to fill it. A cover hides the brief layout change. In a second pass the
  exporter sets `--dl-extra` (the height left over in the square) and fires a resize; charts that draw
  their own height add `window.dlExtra(el)` to it (the 131-disease chart and the funding scatter), so they
  fill the square instead of leaving bands above and below. Text in downloads is a bit larger than on the page
  (titles about 1.65rem; `.dl-capturing` rules in the page CSS; larger canvas header and footer).
  The user's 70-year-old mother should be able to read the labels: in the square download, line and
  disease labels are about 15–17px (131-disease chart, rankings, funding). Inter is embedded in every
  download (`window.dlFonts()` inlines the page's Google Fonts, latin subset). The card's side padding is
  dropped during capture, and the 131-disease chart sizes its label margin from measured label widths.
  The rankings lay out at 700px wide and the funding bars at 720px for the square.
- Y-axis numbers start at the left edge of the chart, in line with the title and other text (user's
  request, v36); the plot starts just after the widest number (measured). Used in the 131-disease
  chart, the funding scatter and the 120-disease scatter plots. Long lists are cut to 15 rows
  in the square image only (user's request): the shortfall rankings show the top 12 plus the 3 other
  groups, the funding bars the largest 15 ("Largest 15 of N shown."); both check for `dl-sq` on their card. Downloads do nothing in
  the claude.ai artifact copy (the viewer blocks them); the buttons are hidden on the overview anyway.
- An interactive with `"overview": false` shows on its topic page only; the overview gets a link line
  (text from `"more"`). With `"overview": {"html": ..., "pick": {"name": "a/b/c", ...}}` the overview
  shows that small fragment instead, given only the picked parts of the data (slash paths into the JSON).
  The Global ME/CFS burden model (`global_burden/`, data about 380 KB, ids `gme-`, styles under `.gme`)
  uses this: `global_burden/overview.html` shows its two distribution charts (CCC, now).
- A section can carry `"subsections"` (same fields as a section, minus interactive). They show at the end
  of its topic page; `docs/<subsection id>.html` redirects there.
  The WHO ICTRP analysis is a subsection of the 120-disease section this way.
- An interactive's `"data"` can be a map `{"name": path}`; the fragment then gets an object of those
  tables (used by `clinicaltrials/per_year_interactive.html`).
- Data files show in a collapsed block under each section's charts on its topic page.
- A data entry with `"hidden": true` is catalogued but not shown: use it for pipeline inputs whose
  contents already appear in another table (e.g. `sex/sex_labels.csv`, `expanded/cleaned_counts_*.csv`).
- Keep the number of files low: add columns or rows to an existing table rather than a new small file,
  put short tables and search strings in the folder README, and never save the same data in two shapes.
- Link preview (v41, user's choice): every page has Open Graph and X card tags. The card title is
  "Data & Graphs · How To Solve A Disease?" (no quotes; the Substack name joined with no-break spaces, so Signal's
  two title lines beside the image break after "·"; topic pages: "<section> · Data & Graphs"), and the
  description, shown under the image, is "by Siebe Rozendal".
  The image, `docs/preview.png` (1200 × 630), is only the 120-disease papers-vs-burden scatter with ME/CFS and
  long COVID labelled, no title text. Small previews in Signal, WhatsApp and iMessage crop the middle
  630 × 630 square, so labels and axis names stay inside it; only dots reach past it.
  Remake it with `python3 -I tools/make_preview.py` if the title, tagline or data change. It works only once
  merged into `main`, since the tags use the Pages URL.
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
- Charts and page use the "Forest glass" style (v21, chosen by the user on 2026-11-26 from twelve mockups):
  deep green page `#0e2a22` with soft light from the top left; charts are saved with a transparent
  background (`savefig(..., transparent=True)`) so the green shows through. Ink `#e9efe9`, muted
  `#a7bdb2`, grid `#ffffff1f`, mint `#9fd8b5` (was ocean), peach `#f2b880` (was sunset), blue
  `#7fb2f0` and violet `#b48cf0` for more categories (the user wants some blue, e.g. "mostly men"; no pale
  lilac). ME/CFS stays peach; long COVID is violet where both appear. Titles in a sans-serif (Inter Tight on the page, Inter in charts),
  never a serif. Sized for phone screens; a small version number in a corner. Transparent PNGs have
  light text, so they don't work on a white background (Substack, X): the solid copies in
  `<folder>/solid/` are for sharing. Scripts that only make old or hidden charts (`expanded/analyse.py`,
  `analysis/burden_vs_research.py`, `analysis/long_covid_trials.py`, `analysis/shortfall_ccc.py`) still
  use the old navy colours; that's fine while their charts stay old or hidden.
- Each folder has a README with method, choices, results and caveats. Update it with the outputs.
