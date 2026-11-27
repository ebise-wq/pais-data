"""Link preview image (Open Graph / X card) for the site: docs/preview.png, 1200 x 630.

Title and Substack name on the left; on the right the 120-disease scatter (papers per year against
disease burden), with ME/CFS in peach and long COVID in violet. Run: python3 -I tools/make_preview.py
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager, patheffects

VERSION = 1
W, H = 1200, 630
INK, MUTED, FAINT = "#e9efe9", "#a7bdb2", "#7e978b"
MINT, PEACH, VIOLET = "#9fd8b5", "#f2b880", "#b48cf0"

for f in font_manager.findSystemFonts():
    if "inter" in f.lower():
        font_manager.fontManager.addfont(f)
plt.rcParams["font.family"] = "Inter"

cat = json.load(open("catalog.json"))
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
bg = fig.add_axes([0, 0, 1, 1]); bg.set_axis_off()
bg.imshow(img, extent=[0, 1, 0, 1], aspect="auto", origin="upper")

# Text, left.
x0 = 64 / W
fig.text(x0, 1 - 150 / H, cat["title"], color=INK, fontsize=64, fontweight="bold", va="baseline")
sub = cat["subtitle"]
t = fig.text(x0, 1 - 215 / H, sub[:-1], color=MUTED, fontsize=32, fontweight="medium", va="baseline")
fig.canvas.draw()
bb = t.get_window_extent()
fig.text(bb.x1 / W, 1 - 215 / H, "?", color=PEACH, fontsize=32, fontweight="medium", va="baseline")
fig.text(x0, 1 - 330 / H, "Papers, trials and disease burden\nfor ME/CFS, long COVID\nand 120 other diseases.",
         color=INK, fontsize=25, linespacing=1.45, va="top", alpha=0.92)
fig.text(x0, 64 / H, cat["author"]["name"] + "  ·  " + cat["site"].split("//")[1].rstrip("/"),
         color=FAINT, fontsize=19, va="baseline")
fig.text(1 - 22 / W, 18 / H, f"v{VERSION}", color=FAINT, fontsize=11, ha="right", va="baseline", alpha=0.7)

# Scatter, right.
ax = fig.add_axes([735 / W, 110 / H, 405 / W, 400 / H])
ax.patch.set_alpha(0)
for s in ax.spines.values():
    s.set_visible(False)
ax.set_xscale("log"); ax.set_yscale("log")
ax.tick_params(which="both", length=0, labelbottom=False, labelleft=False)
ax.grid(True, color="#ffffff", alpha=0.10, lw=1)
ax.scatter([r["d"] for r in dis], [r["papers"]["n"] for r in dis], s=70, color=MINT, alpha=0.55, lw=0)
for r, c, name, dx, dy, ha in [(me, PEACH, "ME/CFS", 0, -20, "center"), (lc, VIOLET, "Long COVID", 0, 16, "center")]:
    ax.scatter([r["d"]], [r["papers"]["n"]], s=260, color=c, lw=0, zorder=5)
    ax.annotate(name, (r["d"], r["papers"]["n"]), xytext=(dx, dy), textcoords="offset points",
                color=c, fontsize=21, fontweight="semibold", ha=ha, va="top" if dy < 0 else "bottom", zorder=6,
                path_effects=[patheffects.withStroke(linewidth=5, foreground="#0e2a22")])
ax.text(0, 1.03, "Papers per year ↑", transform=ax.transAxes, color=MUTED, fontsize=17, va="bottom")
ax.text(1, -0.04, "Disease burden →", transform=ax.transAxes, color=MUTED, fontsize=17, ha="right", va="top")

fig.savefig("docs/preview.png", dpi=100)
print("wrote docs/preview.png")
