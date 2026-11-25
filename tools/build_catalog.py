"""Build the catalog page (docs/index.html) and the catalog section of README.md from catalog.json.

GitHub Pages serves the docs/ folder only, so docs/index.html loads the chart images from
raw.githubusercontent.com (the main branch). The --fragment copy uses relative image paths,
for publishing as an artifact with the PNGs bundled.

Run from the repo root:   python3 -I tools/build_catalog.py
Check only (no writes):    python3 -I tools/build_catalog.py --check
Also write an artifact copy (no <html>/<head> wrapper):  --fragment PATH

Sizes, row counts and "updated" dates are read from the files and from git, so they never
need editing by hand. The script fails if a catalogued file is missing, and lists any chart
or data file in the repo that is not in catalog.json yet.
"""
import csv, datetime, glob, html, json, os, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CAT = json.load(open("catalog.json"))
REPO, BRANCH = CAT["repo"], CAT["branch"]
BLOB = f"https://github.com/{REPO}/blob/{BRANCH}/"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"
TREE = f"https://github.com/{REPO}/tree/{BRANCH}/"
# File types that count as outputs. Anything with these extensions must be in the catalog.
OUTPUT_EXT = (".png", ".svg", ".csv", ".json", ".gz", ".txt")
NOT_OUTPUTS = {"catalog.json", "LICENSE"}
NOT_OUTPUT_DIRS = ("tools/", "docs/", ".claude/", ".github/")


def git_date(paths):
    out = subprocess.run(["git", "log", "-1", "--format=%cs", "--", *paths],
                         capture_output=True, text=True).stdout.strip()
    return out or datetime.date.today().isoformat()


def rows_of(path):
    if path.endswith(".csv"):
        with open(path, newline="", encoding="utf-8") as f:
            return max(sum(1 for _ in csv.reader(f)) - 1, 0)
    if path.endswith(".json"):
        d = json.load(open(path))
        return len(d) if isinstance(d, (list, dict)) else None
    return None


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit in ("B", "KB") else f"{n:.1f} {unit}"
        n /= 1024


def expand(entry):
    files = sorted(glob.glob(entry["file"]))
    if not files:
        sys.exit(f"Missing file in catalog.json: {entry['file']}")
    entry["files"] = files
    entry["size"] = sum(os.path.getsize(f) for f in files)
    r = [rows_of(f) for f in files]
    entry["rows"] = sum(r) if all(x is not None for x in r) else None
    entry["updated"] = git_date(files)
    return entry


def tracked_outputs():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split()
    return {f for f in out if f.endswith(OUTPUT_EXT) and f not in NOT_OUTPUTS
            and not f.startswith(NOT_OUTPUT_DIRS)}


# ---------- gather ----------
sections = CAT["sections"]
catalogued = set()
for s in sections:
    for item in s["charts"] + s["data"]:
        expand(item)
        catalogued.update(item["files"])
        if item.get("toggle"):
            catalogued.update(expand(item["toggle"])["files"])
    for r in [s["readme"], *s.get("extra_readmes", [])]:
        if not os.path.exists(r):
            sys.exit(f"Missing README in catalog.json: {r}")
        catalogued.add(r)

missing = sorted(tracked_outputs() - catalogued)
if missing:
    print("Not in catalog.json yet:\n  " + "\n  ".join(missing))
if "--check" in sys.argv:
    sys.exit(1 if missing else 0)

# Sections with "hidden": true stay in catalog.json (so --check passes) but are left off the page.
sections = [s for s in sections if not s.get("hidden")]
n_charts = sum(1 for s in sections for c in s["charts"] if not c.get("old"))
n_data = sum(len(d["files"]) for s in sections for d in s["data"])
last = max(i["updated"] for s in sections for i in s["charts"] + s["data"])
built = datetime.date.today().isoformat()
version = CAT["page_version"]


def nice_date(iso):
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%b %Y')}"


e = html.escape


# ---------- HTML ----------
def link(href, text, cls=""):
    c = f' class="{cls}"' if cls else ""
    return f'<a{c} href="{e(href)}" target="_blank" rel="noopener">{text}</a>'


IMG_BASE = ""  # prefix for <img src>; set per output below


def chart_card(c):
    f = c["file"]
    script = link(BLOB + c["script"], "Script") if c.get("script") else ""
    toggle, views = "", ""
    t = c.get("toggle")
    if t:
        # Two images with the same layout; the buttons swap which one shows.
        views = (f' data-views="{e(IMG_BASE + f)}|{e(IMG_BASE + t["file"])}"'
                 f' data-paths="{e(f)}|{e(t["file"])}" data-raws="{e(RAW + f)}|{e(RAW + t["file"])}"')
        toggle = f"""
        <div class="toggle" role="group" aria-label="Chart view">
          <button type="button" aria-pressed="true" data-view="0">{e(c.get("label", "All"))}</button>
          <button type="button" aria-pressed="false" data-view="1">{e(t["label"])}</button>
        </div>"""
    return f"""
      <figure class="chart"{views}>{toggle}
        <button class="chart-img" type="button" data-full="{e(IMG_BASE + f)}" data-title="{e(c['title'])}" aria-label="Open {e(c['title'])} full size">
          <img src="{e(IMG_BASE + f)}" alt="{e(c['title'])}" loading="lazy" decoding="async">
        </button>
        <figcaption>
          <h3>{e(c['title'])}</h3>
          <p>{e(c['caption'])}</p>
          <div class="links">
            <span class="path">{e(f)}</span>
            <span class="sep"></span>
            {link(RAW + f, "Full size", "full")}{script}
          </div>
        </figcaption>
      </figure>"""


def data_row(d):
    files = d["files"]
    meta = [f"{d['rows']:,} rows" if d["rows"] is not None else None, human_size(d["size"]),
            f"updated {nice_date(d['updated'])}"]
    meta = " · ".join(m for m in meta if m)
    if len(files) == 1:
        f = files[0]
        name = link(BLOB + f, e(os.path.basename(f)), "fname")
        view = f.endswith((".csv", ".json", ".txt"))
        actions = (link(BLOB + f, "View") if view else "") + link(RAW + f, "Download")
    else:
        name = f'<span class="fname">{e(os.path.basename(d["file"]))}</span>'
        actions = "".join(link(RAW + f, e(os.path.basename(f))) for f in files)
    folder = os.path.dirname(files[0]) + "/"
    script = f' · made by {link(BLOB + d["script"], e(d["script"]))}' if d.get("script") else ""
    return f"""
        <li class="data">
          <div class="data-main">
            <div class="data-name">{name}<span class="folder">{e(folder)}</span></div>
            <p>{e(d['about'])}</p>
            <div class="meta">{meta}{script}</div>
          </div>
          <div class="actions">{actions}</div>
        </li>"""


def section_html(s):
    charts = [c for c in s["charts"] if not c.get("old")]
    old_charts = [c for c in s["charts"] if c.get("old")]
    data = [d for d in s["data"] if not d.get("old")]
    old_data = [d for d in s["data"] if d.get("old")]
    readmes = [s["readme"], *s.get("extra_readmes", [])]
    readme_links = "".join(link(BLOB + r, e(r)) for r in readmes)
    parts = [f"""
  <section id="{e(s['id'])}">
    <header class="sec-head">
      <h2>{e(s['title'])}</h2>
      <div class="sec-links"><span>Notes:</span>{readme_links}</div>
    </header>
    <p class="finding">{e(s['finding'])}</p>"""]
    if charts:
        parts.append('    <div class="charts">' + "".join(chart_card(c) for c in charts) + "\n    </div>")
    if data:
        label = "Data behind these charts" if charts else "Data files"
        parts.append(f'    <details class="datablock"><summary>{label} <span class="count">{len(data)}</span></summary>\n'
                     '    <ul class="datalist">' + "".join(data_row(d) for d in data) + "\n    </ul></details>")
    if old_charts or old_data:
        n = len(old_charts) + len(old_data)
        inner = ""
        if old_charts:
            inner += '<div class="charts old">' + "".join(chart_card(c) for c in old_charts) + "</div>"
        if old_data:
            inner += '<ul class="datalist">' + "".join(data_row(d) for d in old_data) + "</ul>"
        parts.append(f'    <details class="older"><summary>Earlier versions ({n})</summary>{inner}</details>')
    parts.append("  </section>")
    return "\n".join(parts)


nav = "".join(f'<a href="#{e(s["id"])}">{e(s["title"].split(",")[0].split(" (")[0])}</a>' for s in sections)

HEAD = f"""<title>{e(CAT['title'])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(CAT['tagline'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600&family=IBM+Plex+Mono:wght@400;500&display=swap">"""

STYLE = """<style>
/* Layout: one reading column. Header, topic chips, then one section per analysis:
   key finding, chart grid, then the data files in a collapsed block. Colours match the charts themselves. */
:root {
  --bg: #141a24; --surface: #1a2230; --raise: #212a3a; --line: #2a3446;
  --ink: #eef1f6; --muted: #a3acba; --faint: #6f7a8c;
  --ocean: #7fb3d5; --sunset: #f4a582;
  --f-display: "Space Grotesk", "Inter", system-ui, sans-serif;
  --f-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 4.5rem; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
body { margin: 0; background: var(--bg); color: var(--ink); font: 400 17px/1.55 var(--f-body);
  -webkit-font-smoothing: antialiased; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px);
  z-index: 10; background: var(--bg); }
a { color: var(--ocean); text-decoration: none; }
a:hover { text-decoration: underline; text-underline-offset: 3px; }
a:focus-visible, button:focus-visible, summary:focus-visible { outline: 2px solid var(--sunset); outline-offset: 3px; border-radius: 4px; }
.wrap { max-width: 1120px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); }

.top { padding-block: 2.75rem 1.5rem; }
.top h1 { font: 600 clamp(2.1rem, 6vw, 3.1rem)/1.05 var(--f-display); margin: 0; letter-spacing: -0.01em; text-wrap: balance; }
.top h1 span { color: var(--sunset); }
.top .tagline { color: var(--muted); font-size: 1.15rem; margin: 0.7rem 0 0; max-width: 40ch; text-wrap: balance; }
.stats { display: flex; flex-wrap: wrap; gap: 0.4rem 1.4rem; margin-top: 1.4rem; font-size: 0.95rem; color: var(--muted);
  font-variant-numeric: tabular-nums; }
.stats b { color: var(--ink); font-weight: 600; }

.nav { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 5; background: color-mix(in srgb, var(--bg) 92%, transparent);
  backdrop-filter: blur(8px); border-bottom: 1px solid var(--line); }
.nav .wrap { display: flex; gap: 0.5rem; overflow-x: auto; padding-block: 0.7rem; scrollbar-width: none; }
.nav .wrap::-webkit-scrollbar { display: none; }
.nav a { flex: none; font-size: 0.92rem; color: var(--ink); background: var(--surface); border: 1px solid var(--line);
  padding: 0.35rem 0.8rem; border-radius: 999px; white-space: nowrap; }
.nav a:hover { border-color: var(--ocean); text-decoration: none; }

main { display: grid; gap: 3.5rem; padding-block: 2.25rem 3rem; }
section { display: grid; gap: 1.25rem; min-width: 0; }
.sec-head { display: grid; gap: 0.35rem; border-top: 1px solid var(--line); padding-top: 1.5rem; }
.sec-head h2 { font: 600 clamp(1.45rem, 3.6vw, 1.85rem)/1.2 var(--f-display); margin: 0; text-wrap: balance; }
.sec-links { display: flex; flex-wrap: wrap; gap: 0.2rem 0.9rem; font: 400 0.85rem/1.5 var(--f-mono); color: var(--faint); }
section:first-child .sec-head { border-top: 0; padding-top: 0; }
.finding { margin: 0; max-width: 68ch; font-size: 1.08rem; color: var(--ink); }

.charts { display: grid; gap: 1.25rem; grid-template-columns: repeat(auto-fill, minmax(min(100%, 420px), 1fr)); align-items: start; }
.chart { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; overflow: hidden;
  display: flex; flex-direction: column; min-width: 0; }
.chart-img { display: block; width: 100%; padding: 0; border: 0; background: var(--bg); cursor: zoom-in; }
.chart-img img { display: block; width: 100%; height: auto; max-width: 100%; }
.chart figcaption { padding: 0.9rem 1rem 1rem; display: grid; gap: 0.35rem; border-top: 1px solid var(--line); flex: 1; align-content: start; }
.chart h3 { margin: 0; font: 600 1.05rem/1.3 var(--f-body); }
.chart p { margin: 0; color: var(--muted); font-size: 0.95rem; }
.links { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.3rem 0.9rem; margin-top: 0.35rem; font-size: 0.92rem; }
.links .path { font: 400 0.78rem/1.4 var(--f-mono); color: var(--faint); overflow-wrap: anywhere; }
.links .sep { flex: 1; }

.datalist { list-style: none; margin: 0; padding: 0; border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.data { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 0.5rem 1.25rem; align-items: start;
  padding: 0.9rem 1rem; background: var(--surface); }
.data + .data { border-top: 1px solid var(--line); }
.data-main { min-width: 0; display: grid; gap: 0.2rem; }
.data-name { display: flex; flex-wrap: wrap; align-items: baseline; gap: 0.2rem 0.6rem; }
.fname { font: 500 0.95rem/1.4 var(--f-mono); color: var(--sunset); overflow-wrap: anywhere; }
a.fname:hover { color: var(--sunset); }
.folder { font: 400 0.78rem/1.4 var(--f-mono); color: var(--faint); }
.data p { margin: 0; color: var(--ink); font-size: 0.97rem; }
.meta { font-size: 0.85rem; color: var(--muted); font-variant-numeric: tabular-nums; }
.meta a { color: var(--muted); text-decoration: underline; text-decoration-color: var(--line); text-underline-offset: 3px; }
.actions { display: flex; flex-wrap: wrap; gap: 0.4rem; justify-content: flex-end; max-width: 22rem; }
.actions a { font-size: 0.88rem; padding: 0.3rem 0.7rem; border: 1px solid var(--line); border-radius: 8px; background: var(--raise); white-space: nowrap; }
.actions a:hover { border-color: var(--ocean); text-decoration: none; }
@media (max-width: 640px) {
  .data { grid-template-columns: 1fr; }
  .actions { justify-content: flex-start; max-width: none; }
}

.datablock { border: 1px solid var(--line); border-radius: 12px; background: var(--surface); }
.datablock > summary { cursor: pointer; padding: 0.8rem 1rem; font-weight: 500; list-style: none;
  display: flex; align-items: center; gap: 0.6rem; }
.datablock > summary::-webkit-details-marker { display: none; }
.datablock > summary::before { content: ""; width: 0.5rem; height: 0.5rem; border-right: 2px solid var(--muted);
  border-bottom: 2px solid var(--muted); transform: rotate(-45deg); transition: transform 0.15s; flex: none; }
.datablock[open] > summary::before { transform: rotate(45deg); }
.datablock .count { font: 500 0.8rem var(--f-mono); color: var(--bg); background: var(--muted); border-radius: 999px; padding: 0.05rem 0.5rem; }
.datablock .datalist { border: 0; border-top: 1px solid var(--line); border-radius: 0 0 12px 12px; }
.toggle { display: flex; gap: 0; margin: 0.75rem 1rem 0; align-self: flex-start; border: 1px solid var(--line);
  border-radius: 999px; padding: 3px; background: var(--bg); }
.toggle button { font: 500 0.92rem var(--f-body); color: var(--muted); background: transparent; border: 0;
  border-radius: 999px; padding: 0.35rem 0.9rem; cursor: pointer; }
.toggle button[aria-pressed="true"] { background: var(--raise); color: var(--ink); box-shadow: inset 0 0 0 1px var(--line); }
.chart[data-views] { background: var(--bg); }
.chart[data-views] figcaption { background: var(--surface); }
.older { border: 1px dashed var(--line); border-radius: 12px; padding: 0.8rem 1rem; }
.older summary { cursor: pointer; color: var(--muted); font-size: 0.95rem; }
.older[open] summary { margin-bottom: 1rem; }
.older > * + * { margin-top: 1rem; }
.charts.old .chart { opacity: 0.85; }

footer { border-top: 1px solid var(--line); padding-block: 1.5rem 2.5rem; color: var(--muted); font-size: 0.92rem;
  display: flex; flex-wrap: wrap; gap: 0.6rem 1.5rem; justify-content: space-between; }
footer code { font: 400 0.85rem var(--f-mono); color: var(--ink); background: var(--surface); padding: 0.1rem 0.35rem; border-radius: 4px; }
footer .ver { color: var(--faint); font: 400 0.78rem var(--f-mono); }

dialog.lb { border: 0; padding: 0; background: transparent; max-width: min(96vw, 1400px); max-height: 94vh; }
dialog.lb::backdrop { background: rgba(8, 11, 17, 0.88); }
dialog.lb img { display: block; max-width: 100%; max-height: 88vh; width: auto; height: auto; border-radius: 8px; }
dialog.lb .lb-bar { display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: 0.5rem 0.1rem; color: var(--ink); }
dialog.lb button { font: 500 0.95rem var(--f-body); color: var(--ink); background: var(--raise); border: 1px solid var(--line);
  border-radius: 8px; padding: 0.35rem 0.8rem; cursor: pointer; }
</style>"""

SCRIPT = """<script>
document.querySelectorAll(".chart[data-views]").forEach(function (fig) {
  var srcs = fig.dataset.views.split("|"), paths = fig.dataset.paths.split("|"), raws = fig.dataset.raws.split("|");
  var img = fig.querySelector(".chart-img img"), open = fig.querySelector(".chart-img");
  var path = fig.querySelector(".path"), full = fig.querySelector("a.full");
  new Image().src = srcs[1];
  fig.querySelectorAll(".toggle button").forEach(function (b) {
    b.addEventListener("click", function () {
      var i = +b.dataset.view;
      img.src = srcs[i]; open.dataset.full = srcs[i]; path.textContent = paths[i]; full.href = raws[i];
      fig.querySelectorAll(".toggle button").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
    });
  });
});
(function () {
  var dlg = document.getElementById("lb");
  if (!dlg || typeof dlg.showModal !== "function") return;
  var img = dlg.querySelector("img"), title = dlg.querySelector(".lb-title");
  document.querySelectorAll(".chart-img").forEach(function (b) {
    b.addEventListener("click", function () {
      img.src = b.dataset.full; img.alt = b.dataset.title; title.textContent = b.dataset.title;
      dlg.showModal();
    });
  });
  dlg.addEventListener("click", function (ev) { if (ev.target === dlg || ev.target.closest("[data-close]")) dlg.close(); });
})();
</script>"""

title_html = e(CAT["title"]).replace("PAIS", "<span>PAIS</span>", 1)
def body():
    return f"""<div class="wrap top">
  <h1>{title_html}</h1>
  <p class="tagline">{e(CAT['tagline'])}</p>
  <div class="stats"><span><b>{n_charts}</b> charts</span><span><b>{n_data}</b> data files</span>
    <span>Last change <b>{nice_date(last)}</b></span><span>{link(TREE, "Code on GitHub")}</span></div>
</div>
<nav class="nav" aria-label="Topics"><div class="wrap">{nav}</div></nav>
<main class="wrap">
{"".join(section_html(s) for s in sections)}
</main>
<footer class="wrap">
  <span>To add a chart or dataset: add it to <code>catalog.json</code>, then run <code>python3 -I tools/build_catalog.py</code>.</span>
  <span class="ver">v{version} · built {built}</span>
</footer>
<dialog class="lb" id="lb" aria-label="Chart full size">
  <div class="lb-bar"><span class="lb-title"></span><button type="button" data-close>Close</button></div>
  <img alt="">
</dialog>
{SCRIPT}"""


IMG_BASE = RAW
standalone = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{HEAD}
{STYLE}
</head>
<body>
{body()}
</body>
</html>
"""
os.makedirs("docs", exist_ok=True)
open("docs/index.html", "w").write(standalone)
open("docs/.nojekyll", "w").close()
if "--fragment" in sys.argv:
    IMG_BASE = ""
    out = sys.argv[sys.argv.index("--fragment") + 1]
    open(out, "w").write(f"{HEAD}\n{STYLE}\n{body()}\n")


# ---------- README section ----------
def md_section(s):
    lines = [f"### {s['title']}", "", s["finding"], ""]
    charts = [c for c in s["charts"] if not c.get("old")]
    if charts:
        lines.append(" ".join(f'<a href="{c["file"]}"><img src="{c["file"]}" width="260" alt="{c["title"]}"></a>'
                              for c in charts))
        for c in charts:
            if c.get("toggle"):
                lines.append(f'\n{c["title"]}, {c["toggle"]["label"].lower()}: [`{c["toggle"]["file"]}`]({c["toggle"]["file"]})')
        lines.append("")
    data = [d for d in s["data"] if not d.get("old")]
    if data:
        lines += ["| File | What it is | Rows |", "|---|---|---|"]
        for d in data:
            f = d["files"][0] if len(d["files"]) == 1 else d["file"]
            rows = f"{d['rows']:,}" if d["rows"] is not None else ""
            lines.append(f"| [`{f}`]({d['files'][0] if len(d['files']) == 1 else os.path.dirname(f)}) | {d['about']} | {rows} |")
        lines.append("")
    notes = ", ".join(f"[`{r}`]({r})" for r in [s["readme"], *s.get("extra_readmes", [])])
    lines += [f"Notes: {notes}", ""]
    return "\n".join(lines)


START, END = "<!-- catalog:start -->", "<!-- catalog:end -->"
readme = open("README.md").read()
if START not in readme or END not in readme:
    sys.exit("README.md needs the catalog:start and catalog:end markers.")
gen = (f"{START}\n<!-- Made by tools/build_catalog.py from catalog.json. Do not edit by hand. -->\n\n"
       + "\n".join(md_section(s) for s in sections) + END)
head, rest = readme.split(START, 1)
open("README.md", "w").write(head + gen + rest.split(END, 1)[1])

print(f"Wrote docs/index.html and README.md: {n_charts} charts, {n_data} data files, page v{version}.")
