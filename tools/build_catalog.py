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


def view_label(c, key):
    """Label of one view of a chart with "switches": the chosen option of each switch, joined."""
    parts = []
    for labels, i in zip(c["switches"], map(int, key.split(","))):
        if len(labels) > 1:
            parts.append(labels[i])
        elif i:
            parts.append(labels[0])
    return ", ".join(parts)


def views_of(c):
    """All images of a chart as (key, file, label), the default first. A chart can have one "toggle" (one
    row of buttons) or several "switches" with a "views" map {"i,j": file}; a switch with one label is on/off."""
    if c.get("switches"):
        k0 = ",".join("0" for _ in c["switches"])
        return [(k0, c["file"], view_label(c, k0))] + [(k, f, view_label(c, k)) for k, f in c["views"].items()]
    t = c.get("toggle")
    t = [] if not t else (t if isinstance(t, list) else [t])
    return [("0", c["file"], c.get("label", "All"))] + [(str(i + 1), x["file"], x["label"]) for i, x in enumerate(t)]


def switch_specs(c):
    if c.get("switches"):
        return c["switches"]
    v = views_of(c)
    return [[lab for _, _, lab in v]] if len(v) > 1 else []


def toggles(c):
    """The other images of a chart (not the default), as {"file", "label"}."""
    return [{"file": f, "label": lab} for _, f, lab in views_of(c)[1:]]


def wide_of(f):
    """A chart's landscape copy for desktop topic pages: <folder>/wide/<name>."""
    return os.path.join(os.path.dirname(f), "wide", os.path.basename(f))


WIDE_MQ = "(min-width: 800px)"


def solid_of(f):
    """A chart's copy on solid green, for sharing on white pages: <folder>/solid/<name>."""
    return os.path.join(os.path.dirname(f), "solid", os.path.basename(f))


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
        for _, f, _ in views_of(item):
            extra = ([solid_of(f)] if item.get("solid") else []) + \
                    ([wide_of(f)] + ([solid_of(wide_of(f))] if item.get("solid") else []) if item.get("wide") else [])
            for x in extra:
                if not os.path.exists(x):
                    sys.exit(f"Missing chart copy: {x}")
                catalogued.add(x)
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
    """A chart with its title, caption and links; bare=True (overview) shows the image and switches only."""
    f = c["file"]
    script = link(BLOB + c["script"], "Script") if c.get("script") else ""
    solid = c.get("solid")
    wide = c.get("wide") and not bare   # landscape copies on desktop topic pages
    solid_link = link(RAW + solid_of(f), "Solid background", "solid") if solid else ""
    toggle, views = "", ""
    v = views_of(c)
    wide_attrs = ""
    if wide:
        col = lambda fn: e("|".join(fn(x) for _, x, _ in v))
        wide_attrs = (f' data-wide="{col(lambda x: IMG_BASE + wide_of(x))}" data-wraws="{col(lambda x: RAW + wide_of(x))}"'
                      + (f' data-wsolids="{col(lambda x: RAW + solid_of(wide_of(x)))}"' if solid else ""))
    if len(v) > 1:
        # Images with the same layout; the switches pick which one shows.
        col = lambda fn: e("|".join(fn(x) for _, x, _ in v))
        views = (f' data-keys="{e("|".join(k for k, _, _ in v))}" data-views="{col(lambda x: IMG_BASE + x)}"'
                 f' data-paths="{col(lambda x: x)}" data-raws="{col(lambda x: RAW + x)}"'
                 + (f' data-solids="{col(lambda x: RAW + solid_of(x))}"' if solid else ""))
        groups = []
        for i, labels in enumerate(switch_specs(c)):
            if len(labels) > 1:
                b = "".join(f'<button type="button" data-sw="{i}" data-v="{j}" aria-pressed="{"true" if j == 0 else "false"}">{e(l)}</button>'
                            for j, l in enumerate(labels))
                groups.append(f'<div class="toggle" role="group" aria-label="Chart view">{b}</div>')
            else:
                groups.append(f'<button type="button" class="pill" data-sw="{i}" aria-pressed="false"><i></i>{e(labels[0])}</button>')
        toggle = '\n        <div class="switches">' + "".join(groups) + "</div>"
    solid_attr = f' data-solid="{e(RAW + solid_of(f))}"' if solid else ""
    return f"""
      <figure class="chart"{views}{wide_attrs}>{toggle}
        <button class="chart-img" type="button" data-full="{e(IMG_BASE + f)}"{solid_attr} data-title="{e(c['title'])}" aria-label="Open {e(c['title'])} full size">
          {f'<picture><source media="{WIDE_MQ}" srcset="{e(IMG_BASE + wide_of(f))}">' if wide else ""}<img src="{e(IMG_BASE + f)}" alt="{e(c['title'])}" loading="lazy" decoding="async">{"</picture>" if wide else ""}
        </button>{"" if bare else f"""
        <figcaption>
          <h3>{e(c['title'])}</h3>
          <p>{e(c['caption'])}</p>
          <div class="links">
            <span class="path">{e(f)}</span>
            <span class="sep"></span>
            {link(RAW + f, "Full size", "full")}{solid_link}{script}
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


def toc_html(current=None):
    """Contents bar, collapsed by default: one link per section, with the part after the first comma set small.
    On the overview (current=None) the links jump to the sections and the bar is sticky; on a topic page they
    open the other topic pages, the bar names the current one and does not stick."""
    items = []
    for s in sections:
        main, _, rest = s["title"].partition(", ")
        sub = f' <span class="tsub">{e(rest)}</span>' if rest else ""
        href = f"#{s['id']}" if current is None else page_href(s["id"])
        ext = ' target="_blank" rel="noopener"' if current is not None and PAGE_BASE else ""
        here = ' aria-current="true"' if s is current else ""
        items.append(f'<li><a href="{e(href)}"{ext} data-toc="{e(s["id"])}"{here}>{e(main)}{sub}</a></li>')
    cur = e(short_title(current["title"])) if current else ""
    return f"""<nav class="toc{' toc-static' if current else ''}" id="toc" aria-label="Contents">
  <div class="wrap">
    <button class="toc-btn" type="button" aria-expanded="false" aria-controls="toc-drop">
      <span class="lab">Contents</span><span class="cur">{cur}</span><span class="chev" aria-hidden="true"></span>
    </button>
    <div class="toc-drop" id="toc-drop" hidden><ol class="toc-list">{"".join(items)}</ol></div>
  </div>
</nav>"""

def head(title):
    full = e(CAT['title'] + ' · ' + CAT['subtitle'])
    og = title.replace(" · " + CAT["subtitle"], "")  # topic pages: "<section> · Data & Graphs"
    return (HEAD.replace(f"<title>{full}</title>", f"<title>{e(title)}</title>", 1)
            .replace(f'<meta property="og:title" content="{e(CAT["title"])}">', f'<meta property="og:title" content="{e(og)}">', 1))


HEAD = f"""<title>{e(CAT['title'] + ' · ' + CAT['subtitle'])}</title>
<meta name="claude:viewport-fit-sides" content="cover">
<meta name="description" content="{e(CAT['tagline'])}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{e(CAT['title'])}">
<meta property="og:title" content="{e(CAT['title'])}">
<meta property="og:description" content="{e('‘' + CAT['subtitle'] + '’ by ' + CAT['author']['name'])}">
<meta property="og:image" content="{e(SITE)}preview.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Scatter plot of papers per year against disease burden for 120 diseases, with ME/CFS and long COVID marked.">
<meta name="twitter:card" content="summary_large_image">
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
.top h1 { font: 700 clamp(3rem, 14vw, 5.2rem)/1 var(--f-display); margin: 0; letter-spacing: -0.02em; text-wrap: balance; }
.top h1 span { color: var(--sunset); }
.top .tagline { color: var(--muted); font-size: 1.15rem; margin: 0.7rem 0 0; max-width: 40ch; text-wrap: balance; }
.top .tagline { font-size: 1.05rem; }
.top .kicker { margin: 0.5rem 0 0; font: 600 clamp(1.3rem, 5vw, 1.7rem)/1.2 var(--f-display); color: var(--ocean); letter-spacing: -0.005em; }
.top .kicker span, .top-sm .kicker-sm span { color: var(--sunset); }
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
.toc-static { position: relative; top: auto; margin-top: 0.6rem; }
/* Topic pages: one reading column, one chart at a time (also on desktop), at the user's request. */
.topic .wrap { max-width: 52rem; }
.topic .charts, .topic .bvr-grid, .topic .fnd-grid2, .topic .pme-panels { grid-template-columns: minmax(0, 1fr) !important; }
/* Portrait charts without a landscape copy: no taller than the screen on desktop. */
@media (min-width: 800px) { .topic .chart:not([data-wide]) .chart-img img { width: auto; max-width: 100%; max-height: 82vh; margin: 0 auto; } }
.topic .gme .dists, .topic .gme .eulers { display: flex !important; flex-direction: column; }
.overview .dl { display: none; }
.dl { position: relative; display: flex; justify-content: flex-end; margin: 0.5rem 0 0; }
.dl-btn { font: 500 0.88rem var(--f-body); color: var(--ocean); background: none; border: 1px solid var(--line);
  border-radius: 999px; padding: 0.3rem 0.85rem; cursor: pointer; }
.dl-btn::before { content: "↓ "; }
.dl-btn[aria-expanded="true"] { border-color: var(--ocean); }
.dl-menu { position: absolute; right: 0; bottom: calc(100% + 6px); z-index: 30; display: grid; min-width: 11rem;
  background: #10302a; border: 1px solid var(--line); border-radius: 10px; padding: 4px; box-shadow: 0 10px 24px rgba(0,0,0,0.35); }
.dl-menu[hidden] { display: none; }
.dl-cover { position: fixed; inset: 0; z-index: 60; display: grid; place-items: center; background: rgba(8, 30, 24, 0.92);
  color: var(--ink); font: 500 1rem var(--f-body); }
.dl-hidden { display: none !important; }
/* Downloads: titles, labels and the lines under them larger than on the page (readable for older eyes) */
.dl-capturing .fnd-bars { --lab: 9.5rem !important; }
.dl-capturing .fnd-lab { font-size: 1.05rem !important; }
.dl-capturing .fnd-v { font-size: 1rem !important; }
.dl-capturing h3 { font-size: 1.65rem !important; line-height: 1.2 !important; }
.dl-capturing .bvr-sub, .dl-capturing .py-sub, .dl-capturing .fnd-sub, .dl-capturing .pme-lede { font-size: 1.05rem !important; }
.dl-capturing .bvr-legend, .dl-capturing .fnd-legend, .dl-capturing .plabel { font-size: 1rem !important; }
.topic .pme-poster.dl-sq .pme-panels { grid-template-columns: 1fr 1fr !important; gap: 18px; }
.dl-capturing { padding-left: 0 !important; padding-right: 0 !important; background: transparent !important; border-color: transparent !important; box-shadow: none !important;
  backdrop-filter: none !important; }
.dl-menu button { font: 500 0.92rem var(--f-body); color: var(--ink); background: none; border: 0; border-radius: 7px;
  padding: 0.5rem 0.7rem; text-align: left; cursor: pointer; }
.dl-menu button:hover { background: var(--raise); }
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
.switches { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.75rem 1rem 0; align-items: center; }
.switches .toggle { margin: 0; }
.pill { display: inline-flex; align-items: center; gap: 0.45rem; font: 500 0.92rem var(--f-body); color: var(--muted);
  background: transparent; border: 1px solid var(--line); border-radius: 999px; padding: 0.4rem 0.85rem; cursor: pointer; }
.pill i { width: 0.7rem; height: 0.7rem; border-radius: 2px; border: 1.5px solid var(--sunset); }
.pill[aria-pressed="true"] { color: var(--ink); border-color: var(--sunset); background: rgba(242, 184, 128, 0.14); }
.pill[aria-pressed="true"] i { background: var(--sunset); }
dialog.lb .lb-solid { margin-left: auto; font-size: 0.92rem; white-space: nowrap; }
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
dialog.lb::backdrop { background: rgba(8, 30, 24, 0.97); }
dialog.lb img { background: var(--bg); display: block; max-width: 100%; max-height: 88vh; width: auto; height: auto; border-radius: 8px; }
dialog.lb .lb-bar { display: flex; justify-content: space-between; gap: 1rem; align-items: center; padding: 0.5rem 0.1rem; color: var(--ink); }
dialog.lb button { font: 500 0.95rem var(--f-body); color: var(--ink); background: var(--raise); border: 1px solid var(--line);
  border-radius: 8px; padding: 0.35rem 0.8rem; cursor: pointer; }
</style>"""

SCRIPT = """<script>
// Charts: switches pick one of the chart's images (key = chosen option of each switch, e.g. "1,0"). Charts with
// data-wide also have landscape copies, shown on desktop; links and the full-size view follow the shape on screen.
var WIDE = window.matchMedia ? window.matchMedia("(min-width: 800px)") : { matches: false };
document.querySelectorAll(".chart[data-views], .chart[data-wide]").forEach(function (fig) {
  var d = fig.dataset, sp = function (k) { return d[k] ? d[k].split("|") : []; };
  var keys = d.keys ? d.keys.split("|") : ["0"], srcs = d.views ? sp("views") : [fig.querySelector(".chart-img img").getAttribute("src")],
      paths = sp("paths"), raws = sp("raws"), solids = sp("solids"), wides = sp("wide"), wraws = sp("wraws"), wsolids = sp("wsolids");
  var img = fig.querySelector(".chart-img img"), source = fig.querySelector("picture source"), open = fig.querySelector(".chart-img");
  var path = fig.querySelector(".path"), full = fig.querySelector("a.full"), solid = fig.querySelector("a.solid");
  if (!raws.length && full) raws = [full.href];
  if (!solids.length && solid) solids = [solid.href];
  var st = keys[0].split(",").map(Number), btns = fig.querySelectorAll("[data-sw]");
  (WIDE.matches && wides.length ? wides : srcs).slice(1).forEach(function (u) { new Image().src = u; });
  function show() {
    var i = keys.indexOf(st.join(","));
    if (i < 0) return;
    var w = WIDE.matches && wides.length;
    img.src = srcs[i]; if (source) source.srcset = wides[i];
    open.dataset.full = w ? wides[i] : srcs[i];
    var so = w && wsolids.length ? wsolids[i] : solids[i];
    if (so) open.dataset.solid = so;
    if (path && paths[i]) path.textContent = paths[i];
    if (full && raws[i]) full.href = w && wraws.length ? wraws[i] : raws[i];
    if (solid && so) solid.href = so;
    btns.forEach(function (b) {
      var k = +b.dataset.sw, on = b.hasAttribute("data-v") ? st[k] === +b.dataset.v : st[k] === 1;
      b.setAttribute("aria-pressed", on ? "true" : "false");
    });
  }
  btns.forEach(function (b) {
    b.addEventListener("click", function () {
      var k = +b.dataset.sw;
      st[k] = b.hasAttribute("data-v") ? +b.dataset.v : 1 - st[k];
      show();
    });
  });
  if (WIDE.addEventListener) WIDE.addEventListener("change", show);
  show();
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
  if (!secs.length) return;  // topic page: the bar already names the page
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
// ---------- Download: one button per chart (elements with data-dl), with a small menu of formats.
// The chart is rendered by the browser itself (html-to-image, loaded on first use), then placed on the page's
// green glow with a footer. Charts with data-dl-custom call their own exporter in window.DL_CUSTOM instead.
// The page's web fonts (latin subset) as @font-face rules with the font files inlined, so saved images
// render in Inter instead of the device's fallback font. Loaded once, on the first download.
window.dlFonts = function () {
  if (window.dlFonts.p) return window.dlFonts.p;
  var link = document.querySelector('link[href*="fonts.googleapis.com/css2"]');
  var asData = function (u) {
    return fetch(u).then(function (r) { return r.blob(); }).then(function (b) {
      return new Promise(function (ok) { var fr = new FileReader(); fr.onload = function () { ok(fr.result); }; fr.readAsDataURL(b); });
    });
  };
  window.dlFonts.p = !link ? Promise.resolve("") : fetch(link.href).then(function (r) { return r.text(); }).then(function (css) {
    var blocks = css.split("/* ").filter(function (b) { return b.indexOf("latin */") === 0; }).map(function (b) { return b.slice(9); });
    var urls = {}; blocks.forEach(function (b) { (b.match(/url\\((https:[^)]+)\\)/g) || []).forEach(function (m) { urls[m.slice(4, -1)] = 1; }); });
    return Promise.all(Object.keys(urls).map(function (u) { return asData(u).then(function (d) { urls[u] = d; }); })).then(function () {
      return blocks.join(" ").replace(/url\\((https:[^)]+)\\)/g, function (m, u) { return "url(" + urls[u] + ")"; });
    });
  }).catch(function () { return ""; });
  return window.dlFonts.p;
};
// Extra height a chart should add while the square download lays it out (0 otherwise); charts call this.
window.dlExtra = function (el) { var c = el && el.closest(".dl-sq"); return c ? (parseFloat(getComputedStyle(c).getPropertyValue("--dl-extra")) || 0) : 0; };
(function () {
  var roots = document.querySelectorAll("[data-dl]");
  if (!roots.length) return;
  var LIB = "https://cdnjs.cloudflare.com/ajax/libs/html-to-image/1.11.11/html-to-image.min.js", lib = null;
  var FONT = 'Inter, "Helvetica Neue", Arial, sans-serif';
  function load() {
    if (!lib) lib = new Promise(function (ok, no) { var sc = document.createElement("script"); sc.src = LIB; sc.onload = function () { ok(window.htmlToImage); }; sc.onerror = no; document.head.appendChild(sc); });
    return lib;
  }
  function glow(x, w, h) {  // CSS radial-gradient(120% 80% at 10% 0%, ...) of the page
    x.fillStyle = "#0b231c"; x.fillRect(0, 0, w, h); x.save(); x.translate(0.1 * w, 0); x.scale(1.2 * w, 0.8 * h);
    var g = x.createRadialGradient(0, 0, 0, 0, 0, 1);
    [[0, "#1f4d3e"], [0.38, "#12342a"], [0.62, "#0e2a22"], [1, "#0b231c"]].forEach(function (s) { g.addColorStop(s[0], s[1]); });
    x.fillStyle = g; x.fillRect(-1, -1, 2, 2); x.restore();
  }
  function txt(sel) { var n = sel && document.querySelector(sel); return n ? n.textContent.trim() : ""; }
  function save(cv, name) {
    cv.toBlob(function (b) {
      var a = document.createElement("a"); a.href = URL.createObjectURL(b); a.download = name + ".png";
      document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
    }, "image/png");
  }
  function generic(root, fmt) {
    var d = root.dataset, skip = ".dl" + (d.dlSkip ? "," + d.dlSkip : "");
    var title = d.dlTitle || txt(d.dlTitleFrom), sub = txt(d.dlSubFrom);
    var opt = { pixelRatio: 3, backgroundColor: "transparent", cacheBust: false,
      filter: function (n) { return !(n.nodeType === 1 && n.matches && n.matches(skip)); } };
    var wait = function (ms) { return new Promise(function (r) { setTimeout(r, ms); }); };
    var PAD = 24, HEAD = (title ? 36 : 0) + (sub ? 22 : 0) + (title || sub ? 8 : 0);
    function srcWrap(width) {  // the footer's source line, wrapped to the chart's width
      var src = d.dlSource ? "Data: " + d.dlSource + (d.dlVer ? " · " + d.dlVer : "") : "", out = [];
      if (!src) return out;
      var m = document.createElement("canvas").getContext("2d"); m.font = "400 12.5px " + FONT; var cur = "";
      src.split(" ").forEach(function (wd) { var t = cur ? cur + " " + wd : wd; if (m.measureText(t).width > width && cur) { out.push(cur); cur = wd; } else cur = t; });
      out.push(cur); return out;
    }
    var cover = document.createElement("div"); cover.className = "dl-cover"; cover.textContent = "Preparing image…";
    return load().then(function (h2i) {
      // Square: lay the chart out at a fixed width first (the charts redraw on resize), so it fills the square
      // whatever the screen size. The card's own background and border would frame the chart: make them
      // transparent while capturing. A cover hides the brief change.
      var go = function () {
        var css = root.getAttribute("style") || "";
        document.body.appendChild(cover);
        root.classList.add("dl-capturing");
        // left-out parts are hidden on the page too, so the image is sized without them
        var gone = Array.prototype.slice.call(root.querySelectorAll(skip));
        gone.forEach(function (n) { n.classList.add("dl-hidden"); });
        var un = function (v) { root.classList.remove("dl-capturing", "dl-sq"); root.setAttribute("style", css); cover.remove();
          gone.forEach(function (n) { n.classList.remove("dl-hidden"); });
          window.dispatchEvent(new Event("resize")); return v; };
        var ready = wait(60);
        if (fmt === "square") {  // data-dl-square-width: another layout width; class dl-sq lets CSS change the layout
          var swn = +(d.dlSquareWidth || 560), sw = swn + "px"; root.classList.add("dl-sq");
          root.style.width = sw; root.style.maxWidth = "none"; root.style.minWidth = sw; root.style.boxSizing = "content-box";
          window.dispatchEvent(new Event("resize"));
          // second pass: charts that read --dl-extra grow by the height left over in the square
          ready = wait(450).then(function () {
            var side = root.offsetWidth + 2 * PAD, spare = side - PAD - HEAD - (52 + srcWrap(root.offsetWidth).length * 16) - root.offsetHeight - PAD / 2;
            if (spare > 24) { root.style.setProperty("--dl-extra", Math.round(spare) + "px"); window.dispatchEvent(new Event("resize")); return wait(450); }
          });
        }
        return ready.then(function () { return h2i.toCanvas(root, opt); }).then(un, function (e) { un(); throw e; });
      };
      return window.dlFonts().then(function (css) { if (css) opt.fontEmbedCSS = css; else opt.skipFonts = true; return go(); });
    }).then(function (shot) {
      var cw = shot.width / 3, chh = shot.height / 3, pad = PAD, head = HEAD, srcLines = srcWrap(cw), foot = 52 + srcLines.length * 16;
      var w = cw + 2 * pad, h = pad + head + chh + foot, ox = pad, oy = pad + head, S = 3;
      if (fmt === "square") { var side = Math.max(w, h); ox += (side - w) / 2; oy += (side - h) / 2; w = h = side; S = 1600 / side; }
      var cv = document.createElement("canvas"), x = cv.getContext("2d");
      cv.width = Math.round(w * S); cv.height = Math.round(h * S); x.scale(S, S); glow(x, w, h);
      var tx = fmt === "square" ? ox : pad, ty = (fmt === "square" ? oy - head : pad);
      x.textBaseline = "alphabetic";
      if (title) { x.fillStyle = "#e9efe9"; x.font = "700 27px " + FONT; x.fillText(title, tx, ty + 25); ty += 36; }
      if (sub) { x.fillStyle = "#a7bdb2"; x.font = "400 15px " + FONT; x.fillText(sub, tx, ty + 16); }
      x.drawImage(shot, ox, oy, cw, chh);
      var fy = (fmt === "square" ? oy + chh + foot : h);
      x.font = "400 12.5px " + FONT; x.fillStyle = "#7e978b";
      srcLines.forEach(function (l, i) { x.fillText(l, tx, fy - 50 - (srcLines.length - 1 - i) * 16); });
      x.strokeStyle = "rgba(255,255,255,0.12)"; x.beginPath(); x.moveTo(tx, fy - 40); x.lineTo(tx + cw, fy - 40); x.stroke();
      x.font = "600 15px " + FONT; x.fillStyle = "#e9efe9"; x.fillText("Siebe Rozendal", tx, fy - 15);
      var nw = x.measureText("Siebe Rozendal").width; x.font = "500 15px " + FONT; x.fillStyle = "#9fd8b5";
      x.fillText("  ·  How To Solve A Disease?", tx + nw, fy - 15);
      save(cv, d.dl + (fmt === "square" ? "-square" : ""));
    });
  }
  roots.forEach(function (root) {
    var box = document.createElement("div"); box.className = "dl";
    box.innerHTML = '<button type="button" class="dl-btn" aria-expanded="false" aria-haspopup="true">Download</button>' +
      '<div class="dl-menu" role="menu" hidden><button type="button" role="menuitem" data-fmt="square">Square image</button>' +
      '<button type="button" role="menuitem" data-fmt="screen">As on screen</button></div>';
    root.appendChild(box);
    var btn = box.querySelector(".dl-btn"), menu = box.querySelector(".dl-menu");
    function open(o) { menu.hidden = !o; btn.setAttribute("aria-expanded", o ? "true" : "false"); }
    btn.addEventListener("click", function (ev) { ev.stopPropagation(); open(menu.hidden); });
    document.addEventListener("click", function (ev) { if (!box.contains(ev.target)) open(false); });
    menu.querySelectorAll("button").forEach(function (b) {
      b.addEventListener("click", function () {
        open(false); var fmt = b.dataset.fmt, c = root.dataset.dlCustom;
        btn.disabled = true; btn.textContent = "Preparing…";
        var done = function () { btn.disabled = false; btn.textContent = "Download"; };
        Promise.resolve(c && window.DL_CUSTOM && window.DL_CUSTOM[c] ? window.DL_CUSTOM[c](fmt) : generic(root, fmt))
          .then(done, function (e) { done(); alert("Sorry, the image could not be made in this browser."); console.error(e); });
      });
    });
  });
})();
(function () {
  var dlg = document.getElementById("lb");
  if (!dlg || typeof dlg.showModal !== "function") return;
  var img = dlg.querySelector("img"), title = dlg.querySelector(".lb-title"), sol = dlg.querySelector(".lb-solid");
  document.querySelectorAll(".chart-img").forEach(function (b) {
    b.addEventListener("click", function () {
      img.src = b.dataset.full; img.alt = b.dataset.title; title.textContent = b.dataset.title;
      sol.hidden = !b.dataset.solid; if (b.dataset.solid) sol.href = b.dataset.solid;
      dlg.showModal();
    });
  });
  dlg.addEventListener("click", function (ev) { if (ev.target === dlg || ev.target.closest("[data-close]")) dlg.close(); });
})();
</script>"""

# Brand: the Substack's name, with "Data & Graphs" under it. The question mark takes the accent colour.
# Title "Data & Graphs", very large; under it the Substack's name, whose question mark takes the accent colour.
title_html = e(CAT["title"])
sub_html = e(CAT["subtitle"]).replace("?", "<span>?</span>", 1)
FULL_TITLE = f"{CAT['title']} · {CAT['subtitle']}"
def body():
    return f"""<div class="wrap top">
  <h1>{title_html}</h1>
  <p class="kicker">{sub_html}</p>
  <p class="tagline">{e(CAT['tagline'])}</p>
  <p class="byline">By {e(CAT['author']['name'])} · {" · ".join(link(l["url"], e(l["label"])) for l in CAT['author']['links'])}
    <span class="upd">Last updated {nice_date(built)}</span></p>
</div>
{toc_html()}
<main class="wrap overview">
{"".join(section_html(s) for s in sections)}
</main>
<footer class="wrap">
  <span class="stats">{n_charts} charts · {n_data} data files · {link(TREE, "code and data on GitHub")}</span>
  <span class="ver">v{version} · built {built}</span>
</footer>
<dialog class="lb" id="lb" aria-label="Chart full size">
  <div class="lb-bar"><span class="lb-title"></span><a class="lb-solid" target="_blank" rel="noopener" hidden>Solid background</a><button type="button" data-close>Close</button></div>
  <img alt="">
</dialog>
{SCRIPT}"""


def topic_body(s):
    return f"""<div class="topic">
<div class="wrap top top-sm">
  <a class="back" href="index.html">← All topics</a>
  <p class="site">{title_html} <span class="kicker-sm">{sub_html}</span></p>
</div>
{toc_html(s)}
<main class="wrap">
{section_html(s, page=True)}
</main>
<footer class="wrap">
  <span>{link(TREE, "Code and data on GitHub")}</span>
  <span class="ver">v{version} · built {built}</span>
</footer>
<dialog class="lb" id="lb" aria-label="Chart full size">
  <div class="lb-bar"><span class="lb-title"></span><a class="lb-solid" target="_blank" rel="noopener" hidden>Solid background</a><button type="button" data-close>Close</button></div>
  <img alt="">
</dialog>
</div>
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
