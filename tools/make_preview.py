"""Link preview image (Open Graph / X card) for the site: docs/preview.png, 1200 x 630.

Only the 120-disease scatter (papers per year against disease burden), with ME/CFS in peach and long
COVID in violet; the card's own text gives the title and byline (og:title, og:description in
tools/build_catalog.py). Small previews (Signal, WhatsApp, iMessage) crop the middle 630 x 630 square,
so the labels and axis names sit inside it (x 285-915); only dots reach past it.
Run: python3 -I tools/make_preview.py
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager, patheffects

VERSION = 3
W, H = 1200, 630
INK, MUTED, FAINT = "#e9efe9", "#a7bdb2", "#7e978b"
MINT, PEACH, VIOLET = "#9fd8b5", "#f2b880", "#b48cf0"

for f in font_manager.findSystemFonts():
    if "inter" in f.lower():
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Inter"

rows = json.load(open("expanded/burden_interactive_2021-2025.json"))["rows"]
dis = [r for r in rows if r["kind"] == "c"]
me = next(r for r in rows if r["label"].startswith("All ME/CFS"))
lc = next(r for r in rows if r["label"].startswith("Long COVID, incl"))

fig = plt.figure(figsize=(W / 100, H / 100), dpi=100)

# Background: the page's glow, light from the top left.
u, v = np.meshgrid(np.linspace(0, 1, 600), np.linspace(0, 1, 315))
d = np.clip(np.hypot((u - 0.1) / 1.2, v / 0.8), 0, 1)
cols = np.array([matplotlib.colors.to_rgb(c) for c in ("#1f4d3e", "#12342a", "#0e2a22", "#0b231c")])
img = np.stack([np.interp(d, [0, 0.38, 0.62, 1], cols[:, k]) for k in range(3)], axis=-1)
bg = fig.add_axes([0, 0, 1, 1], zorder=-10); bg.set_axis_off()
bg.imshow(img, extent=[0, 1, 0, 1], aspect="auto", origin="upper")

# Scatter: plot area x 200-1000, so ME/CFS (about 3/4 along) and its label stay inside the middle square.
L, R, B, T = 200, 1000, 95, 555
ax = fig.add_axes([L / W, B / H, (R - L) / W, (T - B) / H])
ax.patch.set_alpha(0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xscale("log"); ax.set_yscale("log")
ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
ax.grid(True, color="#ffffff", alpha=0.10, lw=1.2)
x = [r["d"] for r in dis]; y = [r["papers"]["n"] for r in dis]
ax.set_xlim(min(x) / 1.4, max(x) * 1.4); ax.set_ylim(min(y) / 1.5, max(y) * 1.5)
ax.scatter(x, y, s=170, color=MINT, alpha=0.6, lw=0, clip_on=False)
for r, c, name, dy in [(me, PEACH, "ME/CFS", -26), (lc, VIOLET, "Long COVID", 24)]:
    ax.scatter([r["d"]], [r["papers"]["n"]], s=620, color=c, lw=0, zorder=5)
    ax.annotate(name, (r["d"], r["papers"]["n"]), xytext=(0, dy), textcoords="offset points",
                color=c, fontsize=30, fontweight="bold", ha="center", va="top" if dy < 0 else "bottom", zorder=6,
                path_effects=[patheffects.withStroke(linewidth=7, foreground="#0e2a22")])
fig.text(305 / W, 1 - 58 / H, "Papers per year ↑", color=MUTED, fontsize=24, fontweight="medium", va="baseline")
fig.text(895 / W, 40 / H, "Disease burden →", color=MUTED, fontsize=24, fontweight="medium", ha="right", va="baseline")
fig.text(1 - 22 / W, 18 / H, f"v{VERSION}", color=FAINT, fontsize=11, ha="right", va="baseline", alpha=0.7)

fig.savefig("docs/preview.png", dpi=100)
print("wrote docs/preview.png")
