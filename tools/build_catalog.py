"""Build the catalog site (docs/index.html plus one page per topic, docs/<section id>.html) and the
catalog section of README.md from catalog.json.

A section can carry "interactive": {"html": fragment, "data": json or csv (optional), "charts": n, "more": text}. The
fragment is inserted with its data (placeholder __DATA__ or __BVR_DATA__; a CSV becomes a list of row objects;
"data" can also be {"name": path, ...}, which becomes an object of those); the part between <!-- more:start --> and <!-- more:end --> shows on the
topic page only, replaced on the overview by a link to it. Parts between <!-- page-only:start --> and
<!-- page-only:end --> also show on the topic page only, with nothing in their place. With "overview": false the
whole fragment shows on the topic page only, and the overview gets a link line (its text from "more"); with
"overview": {"html", "pick"} the overview shows that small fragment, given only the picked parts of the data.
A chart's "toggle" can be one alternative image or a list of them.

The overview shows each section's title (a link to its topic page) and charts only; the top is a contents
list of section titles, with a bar pinned to the top once that list scrolls away. Findings, captions, notes and data files are on the topic pages.

A section can carry "subsections": a list of {id, title, readme, finding, charts, data}. They show at the end
of the topic page; the overview gets one link line per subsection. docs/<subsection id>.html redirects there.

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
import csv, datetime, glob, html, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CAT = json.load(open("catalog.json"))
REPO, BRANCH = CAT["repo"], CAT["branch"]
BLOB = f"https://github.com/{REPO}/blob/{BRANCH}/"
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/"
TREE = f"https://github.com/{REPO}/tree/{BRANCH}/"
SITE = CAT["site"]
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
        if isinstance(d, dict) and isinstance(d.get("rows"), list):
            return len(d["rows"])
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


def toggles(c):
    t = c.get("toggle")
    return [] if not t else (t if isinstance(t, list) else [t])


# ---------- gather ----------
sections = CAT["sections"]
catalogued = set()


def units(s):
    """A section and its subsections, which have the same charts/data/readme fields."""
    return [s, *s.get("subsections", [])]


def data_paths(spec):
    d = spec.get("data")
    return [] if not d else list(d.values()) if isinstance(d, dict) else [d]


for s in (u for sec in sections for u in units(sec)):
    for item in s.get("charts", []) + s.get("data", []):
        expand(item)
        catalogued.update(item["files"])
        for t in toggles(item):
            catalogued.update(expand(t)["files"])
    if s.get("interactive"):
        ov = s["interactive"].get("overview")
        for f in [s["interactive"]["html"], *data_paths(s["interactive"]),
                  *([ov["html"]] if isinstance(ov, dict) else [])]:
            if not os.path.exists(f):
                sys.exit(f"Missing interactive file in catalog.json: {f}")
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
n_charts = (sum(1 for s in sections for c in s["charts"] if not c.get("old"))
            + sum(s.get("interactive", {}).get("charts", 0) for s in sections))
# Data entries with "hidden": true (pipeline inputs whose contents are in other tables) stay catalogued
# but are not shown.
n_data = sum(len(d["files"]) for sec in sections for s in units(sec) for d in s.get("data", []) if not d.get("hidden"))
last = max(i["updated"] for sec in sections for s in units(sec) for i in s.get("charts", []) + s.get("data", []))
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


IMG_BASE = ""   # prefix for <img src>; set per output below
PAGE_BASE = ""  # prefix for links to topic pages; absolute in the artifact copy


def page_href(sid):
    return f"{PAGE_BASE}{sid}.html"


def page_link(sid, text, cls=""):
    c = f' class="{cls}"' if cls else ""
    ext = ' target="_blank" rel="noopener"' if PAGE_BASE else ""
    return f'<a{c} href="{e(page_href(sid))}"{ext}>{text}</a>'


def chart_card(c, bare=False):
    """A chart with its title, caption and links; bare=True (overview) shows the image and toggle only."""
    f = c["file"]
    script = link(BLOB + c["script"], "Script") if c.get("script") else ""
    toggle, views = "", ""
    if toggles(c):
        # Images with the same layout; the buttons swap which one shows.
        opts = [(f, c.get("label", "All"))] + [(t["file"], t["label"]) for t in toggles(c)]
        views = (f' data-views="{e("|".join(IMG_BASE + o for o, _ in opts))}"'
                 f' data-paths="{e("|".join(o for o, _ in opts))}" data-raws="{e("|".join(RAW + o for o, _ in opts))}"')
        buttons = "".join(f'\n          <button type="button" aria-pressed="{"true" if i == 0 else "false"}" data-view="{i}">{e(lab)}</button>'
                          for i, (_, lab) in enumerate(opts))
        toggle = f"""
        <div class="toggle" role="group" aria-label="Chart view">{buttons}
        </div>"""
    return f"""
      <figure class="chart"{views}>{toggle}
        <button class="chart-img" type="button" data-full="{e(IMG_BASE + f)}" data-title="{e(c['title'])}" aria-label="Open {e(c['title'])} full size">
          <img src="{e(IMG_BASE + f)}" alt="{e(c['title'])}" loading="lazy" decoding="async">
        </button>{"" if bare else f"""
        <figcaption>
          <h3>{e(c['title'])}</h3>
          <p>{e(c['caption'])}</p>
          <div class="links">
            <span class="path">{e(f)}</span>
            <span class="sep"></span>
            {link(RAW + f, "Full size", "full")}{script}
          </div>
        </figcaption>"""}
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


def load_data(path):
    """JSON as is; CSV as a list of row objects, with numbers parsed and blanks as null."""
    if not path.endswith(".csv"):
        return json.load(open(path))

    def cell(v):
        if v == "":
            return None
        try:
            return float(v) if any(c in v for c in ".eE") else int(v)
        except ValueError:
            return v
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: cell(v) for k, v in r.items()} for r in csv.DictReader(f)]


def interactive_html(s, full):
    spec = s["interactive"]
    frag = open(spec["html"]).read()
    if spec.get("data"):  # optional: some fragments hold their own numbers
        d = spec["data"]
        d = {k: load_data(v) for k, v in d.items()} if isinstance(d, dict) else load_data(d)
        data = json.dumps(d, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
        frag = frag.replace("__BVR_DATA__", data).replace("__DATA__", data)
    if not full:  # the overview: the charts only; the title links to the topic page for the rest
        frag = re.sub(r"<!-- more:start -->.*?<!-- more:end -->", "", frag, flags=re.S)
        frag = re.sub(r"<!-- page-only:start -->.*?<!-- page-only:end -->", "", frag, flags=re.S)
    return frag


def snapshot_html(s):
    """A small overview fragment ("overview": {"html", "pick"}) that gets only the picked parts of the
    interactive's data, given as slash paths into the JSON, so the overview stays light."""
    ov = s["interactive"]["overview"]
    full = load_data(s["interactive"]["data"])

    def walk(path):
        v = full
        for k in path.split("/"):
            v = v[k]
        return v
    data = json.dumps({k: walk(v) for k, v in ov["pick"].items()}, separators=(",", ":"), ensure_ascii=False)
    return open(ov["html"]).read().replace("__DATA__", data.replace("</", "<\\/"))


def readme_links(s):
    return "".join(link(BLOB + r, e(r)) for r in [s["readme"], *s.get("extra_readmes", [])])


def title_html_of(t, tag="h2", href=None):
    """Title with the part after the first comma ("120 diseases") set small."""
    main, _, rest = t.partition(", ")
    inner = e(main) + (f' <span class="tsub">{e(rest)}</span>' if rest else "")
    if href:
        ext = ' target="_blank" rel="noopener"' if PAGE_BASE else ""
        inner = f'<a href="{e(href)}"{ext}>{inner}</a>'
    return f"<{tag}>{inner}</{tag}>"


def section_html(s, page=False):
    if not page:
        return overview_section(s)
    parts = [f"""
  <section id="{e(s['id'])}">
    <header class="sec-head">
      {title_html_of(s['title'])}
      <div class="sec-links"><span>Notes:</span>{readme_links(s)}</div>
    </header>
    <p class="finding">{e(s['finding'])}</p>"""]
    if s.get("interactive"):
        parts.append(interactive_html(s, full=True))
    parts += files_html(s)
    for sub in s.get("subsections", []):
        parts.append(f"""    <div class="subsec" id="{e(sub['id'])}">
    <header class="sec-head">
      {title_html_of(sub['title'], "h3")}
      <div class="sec-links"><span>Notes:</span>{readme_links(sub)}</div>
    </header>
    <p class="finding">{e(sub['finding'])}</p>""")
        parts += files_html(sub)
        parts.append("    </div>")
    parts.append("  </section>")
    return "\n".join(parts)


def overview_section(s):
    """Overview: the title (a link to the topic page) and the charts, nothing else. Findings, captions,
    notes, data files and subsections are on the topic page."""
    href = page_href(s["id"])
    parts = [f"""
  <section id="{e(s['id'])}" class="ov">
    <header class="ov-head">
      {title_html_of(s['title'], href=href)}
      {page_link(s["id"], "Open page →", "open")}
    </header>"""]
    spec = s.get("interactive")
    if spec:
        ov = spec.get("overview", True)
        if ov is True:
            parts.append(interactive_html(s, full=False))
        elif isinstance(ov, dict):
            parts.append(snapshot_html(s))
    charts = [c for c in s.get("charts", []) if not c.get("old")]
    if charts:
        parts.append('    <div class="charts">' + "".join(chart_card(c, bare=True) for c in charts) + "\n    </div>")
    parts.append("  </section>")
    return "\n".join(parts)


def files_html(s):
    """Chart grid, data block and earlier versions of a section or subsection."""
    charts = [c for c in s.get("charts", []) if not c.get("old")]
    old_charts = [c for c in s.get("charts", []) if c.get("old")]
    data = [d for d in s.get("data", []) if not d.get("old") and not d.get("hidden")]
    old_data = [d for d in s.get("data", []) if d.get("old") and not d.get("hidden")]
    parts = []
    if charts:
        parts.append('    <div class="charts">' + "".join(chart_card(c) for c in charts) + "\n    </div>")
    if data:
        label = "Data behind these charts" if charts or s.get("interactive") else "Data files"
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
    return parts


def short_title(t):
    return t.split(",")[0].split(" (")[0]


def toc_items():
    """Overview contents: one link per section, with the part after the first comma set small."""
    items = []
    for s in sections:
        main, _, rest = s["title"].partition(", ")
        sub = f' <span class="tsub">{e(rest)}</span>' if rest else ""
        items.append(f'<li><a href="#{e(s["id"])}" data-toc="{e(s["id"])}">{e(main)}{sub}</a></li>')
    return "".join(items)


toc = toc_items()

def head(title):
    return HEAD.replace(f"<title>{e(CAT['title'] + ' · ' + CAT['subtitle'])}</title>", f"<title>{e(title)}</title>", 1)


HEAD = f"""<title>{e(CAT['title'] + ' · ' + CAT['subtitle'])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(CAT['tagline'])}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Inter+Tight:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">"""

STYLE = """<style>
/* Layout: one reading column. Header, topic chips, then one section per analysis:
   key finding, chart grid, then the data files in a collapsed block. Colours match the charts themselves. */
:root {
  /* Forest glass (v21): deep green with soft light from the top left; cards and charts are see-through.
     --ocean and --sunset keep their names but are now mint and peach. */
  --bg: #0e2a22; --surface: rgba(255, 255, 255, 0.045); --raise: rgba(255, 255, 255, 0.09); --line: rgba(255, 255, 255, 0.11);
  --ink: #e9efe9; --muted: #a7bdb2; --faint: #7e978b;
  --ocean: #9fd8b5; --sunset: #f2b880;
  --f-display: "Inter Tight", "Inter", system-ui, sans-serif;
  --f-body: "Inter", system-ui, -apple-system, "Segoe UI", sans-serif;
  --f-mono: "IBM Plex Mono", ui-monospace, "SFMono-Regular", Menlo, monospace;
  color-scheme: dark;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; scroll-padding-top: 4.5rem; }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
html { background: #0b231c; }
body { margin: 0; background: radial-gradient(120% 80% at 10% 0%, #1f4d3e 0%, #12342a 38%, #0e2a22 62%, #0b231c 100%) fixed; color: var(--ink); font: 400 17px/1.55 var(--f-body);
  -webkit-font-smoothing: antialiased; }
body::before { content: ""; position: fixed; inset: 0 0 auto; height: env(safe-area-inset-top, 0px);
  z-index: 10; background: var(--bg); }
a { color: var(--ocean); text-decoration: none; }
a:hover { text-decoration: underline; text-underline-offset: 3px; }
a:focus-visible, button:focus-visible, summary:focus-visible { outline: 2px solid var(--sunset); outline-offset: 3px; border-radius: 4px; }
.wrap { max-width: 1120px; margin: 0 auto; padding-left: max(16px, env(safe-area-inset-left, 0px));
  padding-right: max(16px, env(safe-area-inset-right, 0px)); }

.top { padding-block: 2.75rem 0; }
.top h1 { font: 700 clamp(1.85rem, 7.2vw, 3.1rem)/1.08 var(--f-display); margin: 0; letter-spacing: -0.02em; text-wrap: balance; }
.top h1 span { color: var(--sunset); }
.top .tagline { color: var(--muted); font-size: 1.15rem; margin: 0.7rem 0 0; max-width: 40ch; text-wrap: balance; }
.top .tagline { font-size: 1.05rem; }
.top .kicker { margin: 0.35rem 0 0; font: 500 clamp(1.15rem, 3.6vw, 1.45rem)/1.2 var(--f-display); color: var(--ocean); letter-spacing: 0.01em; }
.top-sm .site .kicker-sm { font: 500 0.95rem var(--f-body); color: var(--muted); margin-left: 0.3rem; white-space: nowrap; }
.byline { margin: 0.9rem 0 0; font-size: 0.95rem; color: var(--muted); }
.byline a { color: var(--ocean); }
.byline .upd { display: block; margin-top: 0.15rem; color: var(--faint); font-size: 0.88rem; }
/* Contents: one slim bar under the header, sticky while scrolling and collapsed by default. It names the
   section in view; tapping it opens the list of sections over the page. */
.toc { position: sticky; top: env(safe-area-inset-top, 0px); z-index: 20; margin-top: 1.25rem;
  background: color-mix(in srgb, var(--bg) 94%, transparent); backdrop-filter: blur(8px);
  border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); }
.toc .wrap { position: relative; }
.toc-btn { display: flex; align-items: center; gap: 0.6rem; width: 100%; min-height: 44px; padding: 0; border: 0; background: none;
  color: var(--muted); font: 400 0.95rem/1.3 var(--f-body); cursor: pointer; text-align: left; }
.toc-btn .lab { flex: none; color: var(--ink); }
.toc-btn .cur { flex: 1; min-width: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.toc-btn .cur:not(:empty)::before { content: "· "; }
.toc-btn .chev { flex: none; width: 0.45rem; height: 0.45rem; margin: 0 0.3rem 0.2rem; border-right: 1.5px solid var(--muted);
  border-bottom: 1.5px solid var(--muted); transform: rotate(45deg); transition: transform 0.15s; }
.toc-btn[aria-expanded="true"] .chev { transform: rotate(225deg); margin-bottom: -0.1rem; }
.toc-drop { position: absolute; left: 0; right: 0; top: 100%; margin-top: 1px; padding: 0.2rem max(16px, env(safe-area-inset-left, 0px)) 0.5rem;
  background: #10302a; border-bottom: 1px solid var(--line); box-shadow: 0 12px 24px rgba(0, 0, 0, 0.35);
  max-height: calc(100vh - 60px); overflow-y: auto; }
.toc-list { list-style: none; margin: 0; padding: 0; }
.toc-list a { display: block; padding: 0.5rem 0; color: var(--ink); font: 400 0.95rem/1.35 var(--f-body); }
.toc-list li + li a { border-top: 1px solid var(--line); }
.toc-list a:hover { color: var(--ocean); text-decoration: none; }
.toc-list a[aria-current="true"] { color: var(--sunset); }
.toc-list .tsub { font: 400 0.82rem/1.2 var(--f-body); }
.overview { gap: 2.75rem; }
.ov-head { display: grid; grid-template-columns: minmax(0, 1fr) auto; align-items: baseline; gap: 1rem;
  border-top: 1px solid var(--line); padding-top: 1.5rem; }
section.ov:first-child .ov-head { border-top: 0; padding-top: 0; }
.ov-head h2 { font: 600 clamp(1.45rem, 3.6vw, 1.85rem)/1.2 var(--f-display); margin: 0; text-wrap: balance; }
.ov-head h2 a { color: var(--ink); }
.ov-head .open { flex: none; font-size: 0.95rem; white-space: nowrap; }
.tsub { font: 500 0.95rem/1.2 var(--f-body); color: var(--muted); white-space: nowrap; }
/* Overview shows charts only: hide the explanation lines inside the interactive fragments. */
.overview .bvr-sub, .overview .hint, .overview .fnd-sub, .overview .fnd-note, .overview .py-sub, .overview .pme-lede { display: none !important; }
footer .stats { font-variant-numeric: tabular-nums; }

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
.sec-head { position: relative; }
.sec-head .open { justify-self: start; font-size: 0.92rem; padding: 0.3rem 0.8rem; border: 1px solid var(--line);
  border-radius: 999px; background: var(--surface); margin-top: 0.3rem; }
.sec-head .open:hover { border-color: var(--ocean); text-decoration: none; }
.back { font-size: 0.95rem; color: var(--muted); }
.top-sm { padding-block: 1.4rem 0.6rem; }
.top-sm .site { font: 600 1.35rem/1.2 var(--f-display); color: var(--ink); margin: 0.3rem 0 0; }
.top-sm .site span { color: var(--sunset); }
.nav a[aria-current="page"] { border-color: var(--sunset); color: var(--ink); background: var(--raise); }
.bvr-more { font-size: 0.95rem; color: var(--muted); margin: 0; }
.subsec { display: grid; gap: 1.25rem; min-width: 0; margin-top: 1rem; }
.subsec .sec-head h3 { font: 600 clamp(1.25rem, 3.2vw, 1.5rem)/1.2 var(--f-display); margin: 0; text-wrap: balance; }
.finding { margin: 0; max-width: 68ch; font-size: 1.08rem; color: var(--ink); }

.charts { display: grid; gap: 1.25rem; grid-template-columns: repeat(auto-fill, minmax(min(100%, 420px), 1fr)); align-items: start; }
.chart { margin: 0; background: var(--surface); border: 1px solid var(--line); border-radius: 12px; overflow: hidden;
  display: flex; flex-direction: column; min-width: 0; }
.chart-img { display: block; width: 100%; padding: 0; border: 0; background: transparent; cursor: zoom-in; }
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
.chart[data-views] { background: var(--surface); }
.chart[data-views] figcaption { background: transparent; }
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
dialog.lb::backdrop { background: rgba(8, 30, 24, 0.95); }
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
  srcs.slice(1).forEach(function (u) { new Image().src = u; });
  fig.querySelectorAll(".toggle button").forEach(function (b) {
    b.addEventListener("click", function () {
      var i = +b.dataset.view;
      img.src = srcs[i]; open.dataset.full = srcs[i];
      if (path) path.textContent = paths[i];
      if (full) full.href = raws[i];
      fig.querySelectorAll(".toggle button").forEach(function (o) { o.setAttribute("aria-pressed", o === b ? "true" : "false"); });
    });
  });
});
(function () {
  // Contents bar: collapsed list of sections; names the section in view.
  var bar = document.getElementById("toc");
  if (!bar) return;
  var btn = bar.querySelector(".toc-btn"), drop = bar.querySelector(".toc-drop"), cur = bar.querySelector(".cur");
  var links = drop.querySelectorAll("[data-toc]");
  function setOpen(o) { drop.hidden = !o; btn.setAttribute("aria-expanded", o ? "true" : "false"); }
  btn.addEventListener("click", function () { setOpen(drop.hidden); });
  drop.addEventListener("click", function (ev) { if (ev.target.closest("a")) setOpen(false); });
  document.addEventListener("keydown", function (ev) { if (ev.key === "Escape") setOpen(false); });
  document.addEventListener("click", function (ev) { if (!bar.contains(ev.target)) setOpen(false); });
  var secs = [].slice.call(document.querySelectorAll("main.overview > section"));
  function spy() {
    var y = bar.getBoundingClientRect().bottom + 48, id = "";
    secs.forEach(function (sec) { if (sec.getBoundingClientRect().top <= y) id = sec.id; });
    if (secs.length && id && window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2) id = secs[secs.length - 1].id;
    var t = "";
    links.forEach(function (a) {
      var hit = a.dataset.toc === id;
      a.setAttribute("aria-current", hit ? "true" : "false");
      if (hit) t = a.firstChild.textContent.trim();
    });
    cur.textContent = t;
  }
  var raf = 0;
  window.addEventListener("scroll", function () { if (!raf) raf = requestAnimationFrame(function () { raf = 0; spy(); }); }, { passive: true });
  spy();
})();
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

# Brand: the Substack's name, with "Data & Graphs" under it. The question mark takes the accent colour.
title_html = e(CAT["title"]).replace("?", "<span>?</span>", 1)
FULL_TITLE = f"{CAT['title']} · {CAT['subtitle']}"
def body():
    return f"""<div class="wrap top">
  <h1>{title_html}</h1>
  <p class="kicker">{e(CAT['subtitle'])}</p>
  <p class="tagline">{e(CAT['tagline'])}</p>
  <p class="byline">By {e(CAT['author']['name'])} · {" · ".join(link(l["url"], e(l["label"])) for l in CAT['author']['links'])}
    <span class="upd">Last updated {nice_date(built)}</span></p>
</div>
<nav class="toc" id="toc" aria-label="Contents">
  <div class="wrap">
    <button class="toc-btn" type="button" aria-expanded="false" aria-controls="toc-drop">
      <span class="lab">Contents</span><span class="cur"></span><span class="chev" aria-hidden="true"></span>
    </button>
    <div class="toc-drop" id="toc-drop" hidden><ol class="toc-list">{toc}</ol></div>
  </div>
</nav>
<main class="wrap overview">
{"".join(section_html(s) for s in sections)}
</main>
<footer class="wrap">
  <span class="stats">{n_charts} charts · {n_data} data files · {link(TREE, "code and data on GitHub")}</span>
  <span class="ver">v{version} · built {built}</span>
</footer>
<dialog class="lb" id="lb" aria-label="Chart full size">
  <div class="lb-bar"><span class="lb-title"></span><button type="button" data-close>Close</button></div>
  <img alt="">
</dialog>
{SCRIPT}"""


def topic_body(s):
    chips = "".join(f'<a href="{e(page_href(t["id"]))}"{" aria-current=\"page\"" if t is s else ""}>'
                    f'{e(short_title(t["title"]))}</a>' for t in sections)
    return f"""<div class="wrap top top-sm">
  <a class="back" href="index.html">← All topics</a>
  <p class="site">{title_html} <span class="kicker-sm">{e(CAT['subtitle'])}</span></p>
</div>
<nav class="nav" aria-label="Topics"><div class="wrap">{chips}</div></nav>
<main class="wrap">
{section_html(s, page=True)}
</main>
<footer class="wrap">
  <span>{link(TREE, "Code and data on GitHub")}</span>
  <span class="ver">v{version} · built {built}</span>
</footer>
<dialog class="lb" id="lb" aria-label="Chart full size">
  <div class="lb-bar"><span class="lb-title"></span><button type="button" data-close>Close</button></div>
  <img alt="">
</dialog>
{SCRIPT}"""


def document(title, inner):
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{head(title)}
{STYLE}
</head>
<body>
{inner}
</body>
</html>
"""


IMG_BASE, PAGE_BASE = RAW, ""
os.makedirs("docs", exist_ok=True)
open("docs/index.html", "w").write(document(FULL_TITLE, body()))
pages = {"index.html"}
for s in sections:
    open(f"docs/{s['id']}.html", "w").write(document(f"{s['title']} · {FULL_TITLE}", topic_body(s)))
    pages.add(f"{s['id']}.html")
    for sub in s.get("subsections", []):  # old topic pages of what is now a subsection
        target = f"{s['id']}.html#{sub['id']}"
        open(f"docs/{sub['id']}.html", "w").write(
            f'<!doctype html><meta charset="utf-8"><title>{e(sub["title"])}</title>'
            f'<meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}">'
            f'<p>Moved to <a href="{target}">{e(s["title"])}</a>.</p>\n')
        pages.add(f"{sub['id']}.html")
for old in glob.glob("docs/*.html"):  # pages of removed or hidden sections
    if os.path.basename(old) not in pages:
        os.remove(old)
open("docs/.nojekyll", "w").close()
if "--fragment" in sys.argv:
    IMG_BASE, PAGE_BASE = "", SITE
    out = sys.argv[sys.argv.index("--fragment") + 1]
    open(out, "w").write(f"{HEAD}\n{STYLE}\n{body()}\n")


# ---------- README section ----------
def md_section(s, sub_of=None):
    if sub_of:
        lines = [f"#### {s['title']}", "", s["finding"], "", f"Page: {SITE}{sub_of['id']}.html#{s['id']}", ""]
    else:
        lines = [f"### {s['title']}", "", s["finding"], "", f"Page: {SITE}{s['id']}.html", ""]
    charts = [c for c in s.get("charts", []) if not c.get("old")]
    if charts:
        lines.append(" ".join(f'<a href="{c["file"]}"><img src="{c["file"]}" width="260" alt="{c["title"]}"></a>'
                              for c in charts))
        for c in charts:
            for t in toggles(c):
                lines.append(f'\n{c["title"]}, {t["label"].lower()}: [`{t["file"]}`]({t["file"]})')
        lines.append("")
    data = [d for d in s.get("data", []) if not d.get("old") and not d.get("hidden")]
    if data:
        lines += ["| File | What it is | Rows |", "|---|---|---|"]
        for d in data:
            f = d["files"][0] if len(d["files"]) == 1 else d["file"]
            rows = f"{d['rows']:,}" if d["rows"] is not None else ""
            lines.append(f"| [`{f}`]({d['files'][0] if len(d['files']) == 1 else os.path.dirname(f)}) | {d['about']} | {rows} |")
        lines.append("")
    notes = ", ".join(f"[`{r}`]({r})" for r in [s["readme"], *s.get("extra_readmes", [])])
    lines += [f"Notes: {notes}", ""]
    for sub in s.get("subsections", []):
        lines.append(md_section(sub, sub_of=s))
    return "\n".join(lines)


START, END = "<!-- catalog:start -->", "<!-- catalog:end -->"
readme = open("README.md").read()
if START not in readme or END not in readme:
    sys.exit("README.md needs the catalog:start and catalog:end markers.")
gen = (f"{START}\n<!-- Made by tools/build_catalog.py from catalog.json. Do not edit by hand. -->\n\n"
       + "\n".join(md_section(s) for s in sections) + END)
head, rest = readme.split(START, 1)
open("README.md", "w").write(head + gen + rest.split(END, 1)[1])

print(f"Wrote docs/index.html, {len(sections)} topic pages and README.md: {n_charts} charts, {n_data} data files, page v{version}.")
