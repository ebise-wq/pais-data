"""Average yearly publications and interventional trials (2021-2025) vs global DALYs (GBD 2023).

Run from the repo root: python3 analysis/burden_vs_research.py
"""
import csv, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

YEARS = [str(y) for y in range(2021, 2026)]
GBD = "gbd/IHME-GBD_2023_DATA-08b3fc6f-1.csv"
PUBS = "pubmed/pubs_per_year_2026-11-08.csv"
TRIALS = "clinicaltrials/trials_per_year_2026-11-08.csv"
MECFS_DALYS = 25e6  # set by hand: includes post-COVID ME/CFS; not a GBD cause

# repo disease name(s) -> GBD 2023 level-3 cause name
MAP = {
    "Multiple sclerosis": (["Multiple sclerosis"], "Multiple sclerosis"),
    "Rheumatoid arthritis": (["Rheumatoid arthritis"], "Rheumatoid arthritis"),
    "IBD": (["IBD"], "Inflammatory bowel disease"),
    "Psoriasis": (["Psoriasis"], "Psoriasis"),
    "Epilepsy": (["Epilepsy"], "Idiopathic epilepsy"),
    "Schizophrenia": (["Schizophrenia"], "Schizophrenia"),
    "Bipolar disorder": (["Bipolar disorder"], "Bipolar disorder"),
    "Parkinson's disease": (["Parkinson's disease"], "Parkinson's disease"),
    "HIV/AIDS": (["HIV"], "HIV/AIDS"),
    "ALS / motor neuron disease": (["ALS (rare ref.)"], "Motor neuron disease"),
}

def avg_rows(path):
    with open(path) as f:
        return {r["disease"]: sum(int(r[y]) for y in YEARS) / len(YEARS) for r in csv.DictReader(f)}

gbd = {}
with open(GBD) as f:
    for r in csv.DictReader(f):
        if r["measure_id"] == "2" and r["metric_id"] == "1" and r["year"] == "2023":
            gbd[r["cause_name"]] = tuple(float(r[k]) for k in ("val", "lower", "upper"))

pubs, trials = avg_rows(PUBS), avg_rows(TRIALS)
rows = [{"label": "ME/CFS", "gbd_cause": "(set by hand)", "dalys": MECFS_DALYS,
         "dalys_lower": "", "dalys_upper": "",
         "pubs_per_year": pubs["ME/CFS"], "trials_per_year": trials["ME/CFS"]}]
for label, (src, cause) in MAP.items():
    v, lo, hi = gbd[cause]
    rows.append({"label": label, "gbd_cause": cause, "dalys": v, "dalys_lower": lo, "dalys_upper": hi,
                 "pubs_per_year": sum(pubs[s] for s in src), "trials_per_year": sum(trials[s] for s in src)})

def fit(key):
    """Least-squares line in log10-log10 space, excluding ME/CFS."""
    pts = [(math.log10(r["dalys"]), math.log10(r[key])) for r in rows if r["label"] != "ME/CFS"]
    n = len(pts); mx = sum(p[0] for p in pts) / n; my = sum(p[1] for p in pts) / n
    b = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    a = my - b * mx
    ss_res = sum((y - a - b * x) ** 2 for x, y in pts); ss_tot = sum((y - my) ** 2 for _, y in pts)
    return a, b, 1 - ss_res / ss_tot

for key in ("pubs_per_year", "trials_per_year"):
    a, b, r2 = fit(key)
    for r in rows:
        r[key.replace("_per_year", "_expected")] = 10 ** (a + b * math.log10(r["dalys"]))
    print(f"{key}: slope {b:.2f}, R^2 {r2:.2f} (n={len(rows)-1}, ME/CFS excluded)")

rows.sort(key=lambda r: -r["dalys"])
with open("analysis/burden_vs_research_2021-2025.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
for r in rows:
    print(f'{r["label"]:28s} {r["dalys"]/1e6:7.2f}M  pubs {r["pubs_per_year"]:7.1f} (exp {r["pubs_expected"]:7.0f})'
          f'  trials {r["trials_per_year"]:6.1f} (exp {r["trials_expected"]:5.0f})')

# --- plot: soft ocean / sunset on dark ---
BG, INK, MUTED, GRID = "#141a24", "#e6e9ef", "#9aa3b2", "#2a3342"
OCEAN, SUNSET = "#7fb3d5", "#f4a582"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK,
                     "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED})

# label offsets (points) where the default would collide
OFFSETS = {
    ("pubs_per_year", "Epilepsy"): (0, 9, "center"),
    ("pubs_per_year", "Parkinson's disease"): (-8, 6, "right"),
    ("pubs_per_year", "Rheumatoid arthritis"): (9, -2, "left"),
    ("pubs_per_year", "IBD"): (-8, -12, "right"),
    ("pubs_per_year", "Psoriasis"): (6, -12, "left"),
    ("pubs_per_year", "Schizophrenia"): (0, 9, "center"),
    ("pubs_per_year", "Bipolar disorder"): (0, 9, "center"),
    ("trials_per_year", "Schizophrenia"): (-10, 6, "right"),
    ("trials_per_year", "Epilepsy"): (0, 9, "center"),
    ("trials_per_year", "IBD"): (7, -12, "left"),
    ("trials_per_year", "Bipolar disorder"): (0, 9, "center"),
    ("pubs_per_year", "ME/CFS"): (-10, -4, "right"),
    ("trials_per_year", "ME/CFS"): (-10, -4, "right"),
}

def panel(ax, key, title, ylabel):
    a, b, r2 = fit(key)
    xs = [5e5, 1e8]
    ax.plot(xs, [10 ** (a + b * math.log10(x)) for x in xs], color=MUTED, lw=1, ls="--", zorder=1)
    for r in rows:
        me = r["label"] == "ME/CFS"
        c = SUNSET if me else OCEAN
        if not me:
            ax.plot([r["dalys_lower"], r["dalys_upper"]], [r[key]] * 2, color=c, lw=1, alpha=.45, zorder=2)
        ax.scatter(r["dalys"], r[key], s=90 if me else 55, color=c, edgecolor=BG, linewidth=2, zorder=3)
        dx, dy, ha = OFFSETS.get((key, r["label"]), (7, 5, "left"))
        ax.annotate(r["label"], (r["dalys"], r[key]), xytext=(dx, dy), textcoords="offset points", ha=ha,
                    fontsize=10 if me else 8.5, color=INK if me else MUTED, fontweight="bold" if me else None)
    me = rows[[r["label"] for r in rows].index("ME/CFS")]
    exp = me[key.replace("_per_year", "_expected")]
    ax.annotate("", xy=(me["dalys"], exp), xytext=(me["dalys"], me[key]),
                arrowprops=dict(arrowstyle="-", color=SUNSET, lw=1, ls=":"))
    ax.text(me["dalys"] * 1.08, (exp * me[key]) ** .5,
            f"{me[key]:.0f}/yr vs ~{exp:.0f}\nexpected from trend", color=SUNSET, fontsize=8.5, va="center")
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(5e5, 1e8)
    lo, hi = ax.get_ylim(); ax.set_ylim(me[key] / 1.8, hi * 1.3)
    ax.set_xlabel("Global DALYs, 2023 (GBD 2023)")
    ax.set_ylabel(ylabel)
    ax.set_title(title, loc="left", color=INK, fontsize=12, pad=10)
    ax.text(0.01, 0.98, f"dashed: log-log fit excl. ME/CFS, n={len(rows)-1}, R²={r2:.2f}",
            transform=ax.transAxes, ha="left", va="top", fontsize=7.5, color=MUTED)
    ax.set_facecolor(BG); ax.grid(True, which="major", color=GRID, lw=.6)
    for s in ax.spines.values(): s.set_color(GRID)
    ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        lambda v, _: f"{v/1e6:g}M"))
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))

fig, axs = plt.subplots(1, 2, figsize=(13, 5.6), facecolor=BG)
panel(axs[0], "pubs_per_year", "PubMed publications per year", "Papers per year, 2021–2025 average (title search)")
panel(axs[1], "trials_per_year", "Interventional trials per year", "Trials started per year, 2021–2025 average")
fig.text(0.01, 0.01, "ME/CFS DALYs set to 25M (incl. post-COVID ME/CFS). Whiskers: GBD 95% UI. "
         "IBD = one category, each study or paper counted once.  v2", color=MUTED, fontsize=7.5)
fig.tight_layout(rect=(0, 0.03, 1, 1))
fig.savefig("analysis/burden_vs_research_2021-2025.png", dpi=160, facecolor=BG)
