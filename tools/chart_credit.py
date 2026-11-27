"""Credit footer for chart PNGs, the same as the page's downloads.

add_credit(fig, version) ends the source line (the lowest text on the figure) with " · <version>", draws a
thin rule under it, and under that the credit: "Siebe Rozendal" in bold ink, then "How To Solve A Disease?"
in mint and "CC BY 4.0" in muted green. The rule and credit span the same width as the source line's
margin on both sides. If there is no room below the source line, the figure first grows at the bottom and
everything already drawn moves up. Call it last, just before save().

Scripts run from the repo root (python3 -I folder/script.py), so they import this with
sys.path.insert(0, "tools"). The page builds the same credit from catalog.json ("author" and "subtitle").
"""
from matplotlib.lines import Line2D

NAME, PUB, LICENCE = "Siebe Rozendal", "How To Solve A Disease?", "CC BY 4.0"
INK, MINT, MUTED = "#e9efe9", "#9fd8b5", "#a7bdb2"
RULE = 0.15      # inches from the source line's baseline down to the rule
CREDIT = 0.27    # inches from the rule down to the credit's baseline
BOTTOM = 0.2     # inches below the credit's baseline, at least
SIZE = 12        # credit font size (pt); the source lines are 9.5-10.5


def add_credit(fig, version):
    h, w = fig.get_figheight(), fig.get_figwidth()
    src = min(fig.texts, key=lambda t: t.get_position()[1])
    x0 = src.get_position()[0]
    lowest = src.get_position()[1] * h
    strip = max(0.0, BOTTOM + CREDIT + RULE - lowest)
    H = h + strip

    def up(y):
        return (y * h + strip) / H

    for ax in fig.axes:
        p = ax.get_position()
        ax.set_position([p.x0, up(p.y0), p.width, p.height * h / H])
    for t in fig.texts:
        x, y = t.get_position()
        t.set_position((x, up(y)))
    fig.set_figheight(H)

    r = fig.canvas.get_renderer()
    width = lambda t: t.get_window_extent(r).width / (w * fig.dpi)   # in figure fractions
    base = src.get_text()
    src.set_text(base + " · " + version)
    late_ver = x0 + width(src) > 1 - x0          # too long: the version goes at the right of the credit
    if late_ver:
        src.set_text(base)

    b = lowest + strip
    yr, yc = (b - RULE) / H, (b - RULE - CREDIT) / H
    fig.add_artist(Line2D([x0, 1 - x0], [yr, yr], transform=fig.transFigure, color="white", alpha=0.12, lw=0.8))
    x = x0
    for text, color, weight in [(NAME, INK, "semibold"), ("  ·  ", MUTED, "medium"), (PUB, MINT, "medium"),
                                ("  ·  ", MUTED, "medium"), (LICENCE, MUTED, "normal")]:
        t = fig.text(x, yc, text, fontsize=SIZE, color=color, fontweight=weight, va="baseline")
        x += width(t)
    if late_ver:
        fig.text(1 - x0, yc, version, fontsize=9, color=MUTED, alpha=0.6, ha="right", va="baseline")
