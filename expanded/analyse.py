"""Burden vs research with many more GBD causes: 13 original comparators + the causes in diseases.py.

Run from the repo root: python3 -I expanded/analyse.py
Inputs: expanded/counts_<date>.csv (fetch.py), analysis/plot_data_2021-2025.csv (13 comparators and
ME/CFS), gbd/ (GBD 2023 level 3 and level 4 files).
Outputs (expanded/): burden_vs_research_expanded_2021-2025.csv, fits_2021-2025.csv,
papers_vs_dalys_expanded.png, trials_vs_dalys_expanded.png.
"""
import csv, glob, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from diseases import D

HERE = os.path.dirname(os.path.abspath(__file__))
YEARS = range(2021, 2026)
VERSION = "v7"
GBD_FILES = ["gbd/IHME-GBD_2023_DATA-08b3fc6f-1.csv", "gbd/IHME-GBD_2023_DATA-ff76c2f3-1.csv"]
COUNTS = sorted(glob.glob(os.path.join(HERE, "counts_20??-??-??.csv")))[-1]
MECFS = "All ME/CFS (classic + post-COVID)"

gbd = {}
for p in GBD_FILES:
    for r in csv.DictReader(open(p)):
        if r["measure_id"] == "2" and r["metric_id"] == "1" and r["year"] == "2023":
            gbd[r["cause_name"]] = tuple(float(r[k]) for k in ("val", "lower", "upper"))

rows = []
for r in csv.DictReader(open("analysis/plot_data_2021-2025.csv")):
    if r["kind"] == "comparator":
        rows.append({"label": r["label"], "group": "Infectious" if r["label"] == "HIV/AIDS" else "NCD",
                     "original_13": True, "gbd_causes": r["burden_source"].replace("GBD 2023: ", ""),
                     "dalys": float(r["dalys"]), "dalys_low": float(r["dalys_low"]), "dalys_high": float(r["dalys_high"]),
                     "papers_per_year": float(r["papers_per_year"]), "trials_per_year": float(r["trials_per_year"])})
    elif r["label"] == MECFS:
        me = {"dalys": float(r["dalys"]), "lo": float(r["dalys_low"]), "hi": float(r["dalys_high"]),
              "papers_per_year": float(r["papers_per_year"]), "trials_per_year": float(r["trials_per_year"])}
# Fetched but left out of the comparison: loosely bounded diagnoses whose research is spread across
# many labels, so a title search cannot find most of it (see README).
EXCLUDE = {"Conduct disorder", "Tension-type headache", "Low back pain", "Neck pain"}
for r in csv.DictReader(open(COUNTS)):
    if r["disease"] in EXCLUDE:
        continue
    causes = D[r["disease"]]["gbd"]
    # Several causes (hepatitis B and C: chronic + acute) are summed. Summing the UI bounds overstates the width a bit.
    v = [gbd[c] for c in causes]
    rows.append({"label": r["disease"], "group": r["group"], "original_13": False, "gbd_causes": "; ".join(causes),
                 "dalys": sum(x[0] for x in v), "dalys_low": sum(x[1] for x in v), "dalys_high": sum(x[2] for x in v),
                 "papers_per_year": sum(int(r[f"papers_{y}"]) for y in YEARS) / 5,
                 "trials_per_year": sum(int(r[f"trials_{y}"]) for y in YEARS) / 5})


def fit(pts):
    n = len(pts); mx = sum(x for x, _ in pts) / n; my = sum(y for _, y in pts) / n
    sxx = sum((x - mx) ** 2 for x, _ in pts)
    b = sum((x - mx) * (y - my) for x, y in pts) / sxx
    a = my - b * mx
    res = [y - a - b * x for x, y in pts]
    r2 = 1 - sum(e * e for e in res) / sum((y - my) ** 2 for _, y in pts)
    s = math.sqrt(sum(e * e for e in res) / (n - 2))
    return a, b, r2, s, math.sqrt(s * s / sxx)


def pts_for(subset, key):
    return [(math.log10(r["dalys"]), math.log10(r[key])) for r in subset if r[key] > 0]


def pct(v, p):
    v = sorted(v); k = (len(v) - 1) * p; f = int(k)
    return v[f] + (v[min(f + 1, len(v) - 1)] - v[f]) * (k - f)


KEYS = {"papers": "papers_per_year", "trials": "trials_per_year"}
SETS = {
    "Original 13": [r for r in rows if r["original_13"]],
    "All": rows,
    "All except cancers": [r for r in rows if r["group"] != "Cancer"],
    "Non-cancer NCDs": [r for r in rows if r["group"] == "NCD"],
    "Cancers": [r for r in rows if r["group"] == "Cancer"],
    "Infectious + NTD": [r for r in rows if r["group"] in ("Infectious", "NTD")],
    "Maternal/neonatal": [r for r in rows if r["group"] == "Maternal/neonatal"],
}
random.seed(20261111)
fits, fit_rows = {}, []
for metric, key in KEYS.items():
    for sname, sub in SETS.items():
        P = pts_for(sub, key)
        if len(P) < 4:
            continue
        a, b, r2, s, se_b = fit(P)
        fits[(metric, sname)] = (a, b, r2, s)
        row = {"metric": metric, "set": sname, "n": len(P), "intercept_a": round(a, 4), "slope_b": round(b, 4),
               "slope_se": round(se_b, 4), "r2": round(r2, 3), "resid_sd_log10": round(s, 3),
               "mecfs_shortfall": "", "mecfs_shortfall_p5": "", "mecfs_shortfall_p95": "", "mecfs_resid_percentile": ""}
        if sname in ("Original 13", "All", "All except cancers", "Non-cancer NCDs"):
            # ME/CFS shortfall with burden uncertainty (lognormal from the 90% range) and trend uncertainty (bootstrap)
            act = me[key]
            sig = math.log(me["hi"] / me["lo"]) / (2 * 1.6449)
            sims = []
            for _ in range(4000):
                ab, bb, *_ = fit([random.choice(P) for _ in P])
                d = me["dalys"] * math.exp(random.gauss(0, sig))
                sims.append(10 ** (ab + bb * math.log10(d)) / act)
            resid_me = math.log10(act) - (a + b * math.log10(me["dalys"]))
            res = [y - a - b * x for x, y in P]
            row.update(mecfs_shortfall=round(10 ** (a + b * math.log10(me["dalys"])) / act, 1),
                       mecfs_shortfall_p5=round(pct(sims, .05), 1), mecfs_shortfall_p95=round(pct(sims, .95), 1),
                       mecfs_resid_percentile=round(100 * sum(e < resid_me for e in res) / len(res), 1))
        fit_rows.append(row)

with open(os.path.join(HERE, "fits_2021-2025.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fit_rows[0].keys()); w.writeheader(); w.writerows(fit_rows)

# per-disease table, trend = fit to "All"
out = []
for r in rows:
    o = {k: r[k] for k in ("label", "group", "original_13", "gbd_causes")}
    o.update(dalys=round(r["dalys"]), dalys_low=round(r["dalys_low"]), dalys_high=round(r["dalys_high"]),
             papers_per_year=r["papers_per_year"], trials_per_year=r["trials_per_year"])
    for metric, key in KEYS.items():
        a, b, *_ = fits[(metric, "All")]
        t = 10 ** (a + b * math.log10(r["dalys"]))
        o[f"{metric}_trend"] = round(t, 1)
        o[f"{metric}_shortfall"] = round(t / r[key], 2) if r[key] > 0 else ""
    out.append(o)
out.sort(key=lambda o: -(o["papers_shortfall"] or 0))
with open(os.path.join(HERE, "burden_vs_research_expanded_2021-2025.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=out[0].keys()); w.writeheader(); w.writerows(out)

for fr in fit_rows:
    print({k: v for k, v in fr.items() if v != ""})
for metric in KEYS:
    srt = sorted([o for o in out if o[f"{metric}_shortfall"] != ""], key=lambda o: -o[f"{metric}_shortfall"])
    print(f"\n{metric}: most below trend")
    for o in srt[:15]:
        print(f'  {o["label"]:45s} {o["group"]:18s} {o["dalys"]/1e6:7.2f}M  actual {o[metric+"_per_year"]:8.1f}  trend {o[metric+"_trend"]:8.1f}  {o[metric+"_shortfall"]:5.1f}x')
    print(f"{metric}: most above trend")
    for o in srt[-6:]:
        print(f'  {o["label"]:45s} {o["group"]:18s} {o["dalys"]/1e6:7.2f}M  actual {o[metric+"_per_year"]:8.1f}  trend {o[metric+"_trend"]:8.1f}  {o[metric+"_shortfall"]:5.2f}x')
    zero = [o["label"] for o in out if o[metric + "_shortfall"] == ""]
    if zero:
        print(f"{metric}: zero counts (left out of fit and plot): {zero}")

# ---------------- plots ----------------
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter, LogLocator, NullFormatter
from matplotlib.lines import Line2D

BG, INK, MUTED, GRID = "#141a24", "#eef1f6", "#a3acba", "#262f3d"
SUNSET = "#f4a582"
COL = {"NCD": "#7fb3d5", "Cancer": "#b4a7d6", "Infectious": "#8fd1c1", "NTD": "#e6c97a", "Maternal/neonatal": "#e89bb0"}
NAME = {"NCD": "Other chronic", "Cancer": "Cancer", "Infectious": "Infection", "NTD": "Tropical (NTD)",
        "Maternal/neonatal": "Maternal/newborn"}
plt.rcParams.update({"font.family": ["Inter", "DejaVu Sans"], "font.size": 13, "text.color": INK,
                     "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelsize": 13, "ytick.labelsize": 13})
SHORT = {"Lower respiratory infections": "Pneumonia & LRI", "Diarrheal diseases": "Diarrhoea",
         "Preterm birth complications": "Preterm birth", "Neonatal encephalopathy": "Birth asphyxia",
         "Pre-eclampsia & hypertensive disorders of pregnancy": "Pre-eclampsia",
         "Alzheimer's & other dementias": "Dementia", "Ischemic heart disease": "Heart disease",
         "Interstitial lung disease & sarcoidosis": "ILD", "Fatty liver disease (NAFLD/MASLD)": "Fatty liver",
         "Varicella & herpes zoster": "Zoster", "Typhoid & paratyphoid": "Typhoid", "Chronic kidney disease": "CKD",
         "Low back pain": "Back pain", "Depressive disorders": "Depression", "Anxiety disorders": "Anxiety",
         "Cardiomyopathy & myocarditis": "Cardiomyopathy", "Rheumatic heart disease": "Rheumatic heart",
         "Gallstones & biliary disease": "Gallstones", "Food-borne trematodiases": "Trematodes",
         "African trypanosomiasis": "Sleeping sickness", "Tension-type headache": "Tension headache",
         "Neonatal sepsis": "Newborn sepsis", "Maternal hemorrhage": "Postpartum bleed", "Hearing loss": "Hearing loss",
         "Peripheral arterial disease": "PAD", "Congenital heart disease": "Congenital heart"}
SPEC = {
    "papers": ("Papers vs disease burden", "Papers per year (2021–25 average)", [10, 100, 1000, 10000], (8, 40000)),
    "trials": ("Trials vs disease burden", "Trials started per year (2021–25 average)", [1, 10, 100, 1000], (0.25, 2000)),
}
XS = (1e4, 3e8)
R, L, U, B = (8, 0, "left", "center"), (-8, 0, "right", "center"), (0, 8, "center", "bottom"), (0, -8, "center", "top")
LABELS = {  # hand-placed labels: (dx, dy, ha, va) in points
    "papers": {"Breast cancer": U, "Multiple sclerosis": L, "Fatty liver": L, "HIV/AIDS": R, "Tuberculosis": L,
               "Malaria": B, "Neonatal encephalopathy": U,
               "Neonatal sepsis": R, "Rheumatic heart disease": (-8, -4, "right", "top"), "Scabies": L,
               },
    "trials": {"Breast cancer": U, "Multiple sclerosis": L, "Crohn's disease": L, "HIV/AIDS": R, "Tuberculosis": L,
               "Malaria": R, "Measles": R, "Typhoid & paratyphoid": L, "Neonatal sepsis": (8, 4, "left", "bottom"),
               "Rheumatic heart disease": L, "Neonatal encephalopathy": U, "Lymphatic filariasis": L,
               "Cystic echinococcosis": L},
}
ME_POS = {"papers": (1.25e8, 24), "trials": (1.25e8, 1.25)}  # label in an empty corner, arrow to the dot
M = 0.055
for metric, key in KEYS.items():
    a, b, r2, s = fits[(metric, "All")]
    a13, b13, r2_13, _ = fits[(metric, "Original 13")]
    title, desc, yticks, ylim = SPEC[metric]
    fig = plt.figure(figsize=(6, 7.4), facecolor=BG)
    AX_L = 0.15; AX_W = 0.955 - AX_L
    ax = fig.add_axes([AX_L, 0.28, AX_W, 0.59])
    ax.plot(XS, [10 ** (a13 + b13 * math.log10(x)) for x in XS], color=MUTED, lw=1.2, ls=(0, (1.5, 2.5)), zorder=1)
    ax.plot(XS, [10 ** (a + b * math.log10(x)) for x in XS], color=INK, lw=1.6, ls=(0, (5, 3)), zorder=1, alpha=.85)
    plot_rows = [r for r in rows if r[key] > 0]
    for r in plot_rows:
        ax.scatter(r["dalys"], r[key], s=34, color=COL[r["group"]], edgecolor=BG, linewidth=0.8, zorder=3, alpha=.95)
        lab = LABELS[metric].get(r["label"]) or LABELS[metric].get(SHORT.get(r["label"]))
        if lab:
            dx, dy, ha, va = lab
            ax.annotate(SHORT.get(r["label"], r["label"]), (r["dalys"], r[key]), xytext=(dx, dy),
                        textcoords="offset points", ha=ha, va=va, fontsize=11, color=COL[r["group"]], zorder=6)
    # ME/CFS
    ax.plot([me["lo"], me["hi"]], [me[key]] * 2, color=SUNSET, lw=3, alpha=.5, zorder=4, solid_capstyle="round")
    ax.scatter(me["dalys"], me[key], s=130, color=SUNSET, edgecolor=BG, linewidth=2, zorder=5)
    fr = next(f for f in fit_rows if f["metric"] == metric and f["set"] == "All")
    tx, ty = ME_POS[metric]
    ax.annotate("ME/CFS", (me["dalys"], me[key]), xytext=(tx, ty), textcoords="data", ha="center", va="bottom",
                fontsize=14, fontweight="bold", color=SUNSET, zorder=7,
                arrowprops=dict(arrowstyle="-", color=SUNSET, lw=1.2, shrinkA=2, shrinkB=7))
    ax.annotate(f'{fr["mecfs_shortfall"]:g}× below', (tx, ty), xytext=(0, -3), textcoords="offset points",
                ha="center", va="top", fontsize=12, color=SUNSET, zorder=7)
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xlim(*XS); ax.set_ylim(*ylim)
    ax.xaxis.set_major_locator(FixedLocator([1e5, 1e6, 1e7, 1e8]))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/1e6:g}M"))
    ax.yaxis.set_major_locator(FixedLocator(yticks))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_minor_locator(LogLocator(base=10, subs=range(2, 10)))
        axis.set_minor_formatter(NullFormatter())
    ax.set_facecolor(BG); ax.grid(True, which="major", color=GRID, lw=1)
    for side in ("top", "right"): ax.spines[side].set_visible(False)
    for side in ("left", "bottom"): ax.spines[side].set_color(MUTED); ax.spines[side].set_linewidth(1.2)
    ax.tick_params(which="major", length=7, width=1.2, color=MUTED, pad=6)
    ax.tick_params(which="minor", length=4, width=1, color=MUTED)
    fig.text(M, 0.95, title, fontsize=20, fontweight="bold", color=INK, va="baseline")
    fig.text(M, 0.913, desc, fontsize=13, color=MUTED, va="baseline")
    fig.text(AX_L + AX_W / 2, 0.198, "Disease burden (DALYs per year)", fontsize=13, color=MUTED, ha="center", va="baseline")
    handles = [Line2D([], [], marker="o", ls="", color=COL[g], markersize=7, label=NAME[g]) for g in COL]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(M - 0.012, 0.085), ncol=3, frameon=False,
               fontsize=10.5, labelcolor=MUTED, handletextpad=0.3, columnspacing=0.9, borderaxespad=0)
    lines_h = [Line2D([], [], color=INK, ls=(0, (5, 3)), lw=1.6, label=f"Trend, n={len(plot_rows)} (R² {r2:.2f})"),
               Line2D([], [], color=MUTED, ls=(0, (1.5, 2.5)), lw=1.2, label=f"Old trend, n=13 (R² {r2_13:.2f})")]
    fig.legend(handles=lines_h, loc="lower left", bbox_to_anchor=(M - 0.012, 0.03), ncol=2, frameon=False,
               fontsize=10.5, labelcolor=MUTED, handletextpad=0.4, columnspacing=1.0, borderaxespad=0)
    fig.text(1 - M, 0.008, VERSION, fontsize=9, color=GRID, ha="right", va="baseline")
    fig.savefig(os.path.join(HERE, f"{metric}_vs_dalys_expanded.png"), dpi=300, facecolor=BG)
