"""Link preview image (Open Graph / X card) for the site: docs/preview.png, 1200 x 630.

Title, Substack name and tagline in the middle square (small previews crop to it); behind them the
120-disease scatter (papers per year against disease burden), with ME/CFS in peach and long COVID in
violet at the right edge. Run: python3 -I tools/make_preview.py
"""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager, patheffects

VERSION = 2
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
bg = fig.add_axes([0, 0, 1, 1], zorder=-10); bg.set_axis_off()
bg.imshow(img, extent=[0, 1, 0, 1], aspect="auto", origin="upper")

# Small link previews (Signal, WhatsApp, iMessage) crop the middle 630 x 630 square out of the image,
# so all text sits in that square (x 285-915) and the edges only hold the scatter.
CX = 0.5
fig.text(CX, 1 - 262 / H, cat["title"].replace(" & ", " &\n"), color=INK, fontsize=84, fontweight="bold",
         ha="center", va="baseline", linespacing=0.98)
sub = cat["subtitle"]
t = fig.text(CX, 1 - 345 / H, sub, color=MUTED, fontsize=34, fontweight="medium", ha="center", va="baseline")
fig.canvas.draw()
bb = t.get_window_extent()
t.set_text(sub[:-1]); t.set_ha("left"); t.set_x(bb.x0 / W)  # same spot, question mark in peach
fig.canvas.draw()
fig.text(t.get_window_extent().x1 / W, 1 - 345 / H, "?", color=PEACH, fontsize=34, fontweight="medium", va="baseline")
fig.text(CX, 1 - 410 / H, "Papers, trials and disease burden\nfor ME/CFS, long COVID and 120 others",
         color=INK, fontsize=21, linespacing=1.4, ha="center", va="top", alpha=0.85)
fig.text(CX, 46 / H, cat["author"]["name"], color=FAINT, fontsize=18, ha="center", va="baseline")
fig.text(1 - 22 / W, 18 / H, f"v{VERSION}", color=FAINT, fontsize=11, ha="right", va="baseline", alpha=0.7)

# Scatter over the whole width, dimmed behind the text; ME/CFS and long COVID at the right edge.
L, R, B, T = 40, 1160, 50, 590
ax = fig.add_axes([L / W, B / H, (R - L) / W, (T - B) / H], zorder=-1)
ax.patch.set_alpha(0)
ax.set_axis_off()
ax.set_xscale("log"); ax.set_yscale("log")
x = np.log10([r["d"] for r in dis]); y = np.log10([r["papers"]["n"] for r in dis])
x0, xme = x.min() - 0.05, np.log10(me["d"])
x1 = x0 + (xme - x0) / ((1045 - L) / (R - L))  # ME/CFS lands at x = 1045 px
ax.set_xlim(10 ** x0, 10 ** x1); ax.set_ylim(10 ** (y.min() - 0.15), 10 ** (y.max() + 0.15))
px = L + (x - x0) / (x1 - x0) * (R - L)
alpha = np.interp(np.abs(px - W / 2), [0, 300, 380], [0.10, 0.12, 0.55])
ax.scatter(10 ** x, 10 ** y, s=80, color=MINT, alpha=alpha, lw=0, clip_on=False)
for r, c, name, dy in [(me, PEACH, "ME/CFS", -20), (lc, VIOLET, "Long COVID", 18)]:
    ax.scatter([r["d"]], [r["papers"]["n"]], s=300, color=c, lw=0, zorder=5)
    ax.annotate(name, (r["d"], r["papers"]["n"]), xytext=(0, dy), textcoords="offset points",
                color=c, fontsize=22, fontweight="semibold", ha="center", va="top" if dy < 0 else "bottom", zorder=6,
                path_effects=[patheffects.withStroke(linewidth=5, foreground="#0e2a22")])

fig.savefig("docs/preview.png", dpi=100)
print("wrote docs/preview.png")
