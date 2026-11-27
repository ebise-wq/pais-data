"""Credit line for chart PNGs.

add_credit(fig, version) writes the credit one line below the lowest text on the figure, with the version
number on the right. If there is no room, it first makes the figure taller at the bottom and moves
everything already drawn up. Call it last, just before savefig. The same text is in catalog.json ("author" > "credit"), which
the catalog page uses for the interactive charts.

Scripts run from the repo root (python3 -I folder/script.py), so they import this with
sys.path.insert(0, "tools").
"""
CREDIT = "Siebe Rozendal • How to Solve A Disease? • CC BY 4.0"
MUTED, GRID = "#a3acba", "#262f3d"
LINE = 0.19       # inches between the lowest existing text line and the credit
BOTTOM = 0.13     # inches from the bottom edge to the credit's baseline, at least


def add_credit(fig, version, margin=0.055, credit=CREDIT):
    h = fig.get_figheight()
    lowest = min([t.get_position()[1] * h for t in fig.texts] + [h])
    strip = max(0.0, BOTTOM + LINE - lowest)
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
    y = (lowest + strip - LINE) / H
    fig.text(margin, y, credit, fontsize=9.5, color=MUTED, va="baseline")
    fig.text(1 - margin, y, version, fontsize=9, color=GRID, ha="right", va="baseline")
