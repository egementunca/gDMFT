#!/usr/bin/env python3
"""How the cold insulator branch ends: the pole-flight signature.

Four panels: parameters run away; the demanded second-order scale
V1^2/eps_g diverges with them; the mixing ratio V1/eps_g climbs from
the perturbative regime (~0.1 deep in the insulator) through ~0.56 at
the last root toward V1 = eps_g along the escape; and nothing folds.

The one-run answer to "is U ~ 1.1 a spinodal?": five quantities along the
insulator descent with the parameter boxes lifted (V1, eps_g <= 24
instead of the registered 5, 12). If the branch ended at a fold, s_min of
the residual Jacobian would -> 0 and the root would meet a partner.
Measured instead: the root's parameters run to the box, the demanded
second-order scale V1^2/eps_g diverges WITH them (so this is not a
redundant flat direction with fixed physics), the residual ramps
smoothly, and s_min never shrinks. The branch does not die — the demand
leaves the representable region. Ends between U = 1.125 (last interior
root) and U = 1.100, ~10% above the dressed-weight floor U = D where
2W^2 = (U^2 - D^2)/4 crosses zero.

Data: data/poleflight_bethe_mg3_T0.001.csv (provenance in its header;
generated on the dmft side at db65950). Output: runs/figures/story/.
"""

from __future__ import annotations

import csv
from pathlib import Path

import common
import figstyle as fs
import matplotlib.pyplot as plt

OUT = common.OUT / "story"
SRC = Path(__file__).parent / "data" / "poleflight_bethe_mg3_T0.001.csv"

C_V1 = fs.FRAMEWORK_COLOR["ghost_dmft"]
C_EPS = fs.BRANCH_COLOR["insul"]
C_INV = "#333333"
C_SMIN = "#7F7F7F"
U_FLIGHT = 1.1125          # midpoint of the (1.100, 1.125) bracket
U_FLOOR = 1.0              # (U^2 - D^2)/4 = 0


def load():
    rows = []
    with SRC.open() as stream:
        for line in stream:
            if line.startswith("#"):
                continue
            rows.append(line)
    return sorted(csv.DictReader(rows), key=lambda r: float(r["U"]))


def split(rows, col):
    """(U, val) arrays for the root segment and the no-root descent.

    The last root point is prepended to the no-root arrays so the dashed
    line visibly departs from the root curve instead of floating.
    """
    root = [(float(r["U"]), float(r[col])) for r in rows if r["root"] == "1"]
    flight = [(float(r["U"]), float(r[col])) for r in rows if r["root"] == "0"]
    if root and flight:
        flight.append(min(root))
    return sorted(root), sorted(flight)


def draw(ax, rows, col, color, label):
    root, flight = split(rows, col)
    ax.plot(*zip(*root), color=color, marker="o", ms=3.5, label=label)
    ax.plot(*zip(*flight), color=color, marker="o", ms=3.5, ls=(0, (3, 2)),
            mfc="white", lw=1.1)


def annotate_region(ax, rows, top=False):
    lo = min(float(r["U"]) for r in rows)
    ax.axvspan(lo - 0.02, U_FLIGHT, color="#d62728", alpha=0.05, lw=0)
    ax.axvline(U_FLIGHT, color="#d62728", lw=0.7, alpha=0.5)
    ax.axvline(U_FLOOR, color="black", lw=0.7, ls=":")
    if top:
        ax.text(U_FLIGHT - 0.012, 0.96, "no finite root", rotation=90,
                ha="right", va="top", fontsize=7, color="#d62728",
                transform=ax.get_xaxis_transform())
        ax.text(U_FLOOR - 0.012, 0.04, "weight floor $U=D$", rotation=90,
                ha="right", va="bottom", fontsize=7,
                transform=ax.get_xaxis_transform())


def main():
    rows = load()
    for r in rows:
        r["mix"] = float(r["V1"]) / float(r["eps_g"])
    fig, (a1, a2, am, a3) = plt.subplots(
        4, 1, figsize=(4.6, 8.6), sharex=True,
        gridspec_kw={"hspace": 0.16})

    draw(a1, rows, "V1", C_V1, r"$V_1$ (satellite coupling)")
    draw(a1, rows, "eps_g", C_EPS, r"$\epsilon_g$ (satellite position)")
    a1.axhline(24, color="#7F7F7F", lw=0.8, ls=(0, (4, 2)))
    a1.text(1.62, 24, "lifted box (24)", fontsize=7, color="#7F7F7F",
            ha="right", va="bottom")
    for cap in (5, 12):
        a1.axhline(cap, color="#BBBBBB", lw=0.6, ls=":")
    a1.text(1.62, 12.2, "registered caps (5, 12)", fontsize=7,
            color="#999999", ha="right", va="bottom")
    annotate_region(a1, rows)
    a1.set_ylim(0, 26.5)
    a1.set_ylabel("bath parameters (raw)")
    a1.legend(fontsize=7, loc="lower left")
    a1.set_title("The parameters run away...", fontsize=9, loc="left")

    draw(a2, rows, "inv", C_INV, r"$V_1^2/\epsilon_g$")
    a2.axhline(24, color="#7F7F7F", lw=0.8, ls=(0, (4, 2)))
    annotate_region(a2, rows, top=True)
    a2.set_ylim(0, 26.5)
    a2.set_ylabel(r"$V_1^2/\epsilon_g$ (raw)")
    a2.legend(fontsize=7, loc="center left")
    a2.set_title("...the demanded coupling scale diverges with them...",
                 fontsize=9, loc="left")

    draw(am, rows, "mix", "#7b1fa2", r"$V_1/\epsilon_g$ (mixing ratio)")
    am.axhline(1.0, color="#7F7F7F", lw=0.8, ls=(0, (4, 2)))
    am.text(1.62, 1.0, r"$V_1=\epsilon_g$", fontsize=7, color="#7F7F7F",
            ha="right", va="bottom")
    annotate_region(am, rows)
    am.text(1.62, 0.06,
            "deep insulator (registered branch):\n"
            "0.11 at U=4, 0.14 at U=3 — perturbative",
            fontsize=6.5, color="#555555", ha="right", va="bottom")
    am.set_ylim(0, 1.12)
    am.set_ylabel(r"$V_1/\epsilon_g$")
    am.legend(fontsize=7, loc="center left")
    am.set_title("...the satellite leaves the perturbative regime...",
                 fontsize=9, loc="left")

    root, flight = split(rows, "normF")
    a3.semilogy(*zip(*root), color=C_V1, marker="o", ms=3.5,
                label=r"$\|F\|$ (matching residual)")
    a3.semilogy(*zip(*flight), color=C_V1, marker="o", ms=3.5,
                ls=(0, (3, 2)), mfc="white", lw=1.1)
    root, flight = split(rows, "smin")
    a3.semilogy(*zip(*root), color=C_SMIN, marker="s", ms=3,
                label=r"$s_{\min}$ of the Jacobian")
    a3.semilogy(*zip(*flight), color=C_SMIN, marker="s", ms=3,
                ls=(0, (3, 2)), mfc="white", lw=1.1)
    annotate_region(a3, rows)
    a3.text(1.60, 6.5e-5, "root plateau\n(re-eval noise)", fontsize=6.5,
            color=C_V1, ha="right", va="bottom")
    a3.set_ylim(2e-6, 4e-3)
    a3.set_ylabel(r"$\|F\|$,  $s_{\min}$")
    a3.set_xlabel(r"$U/D$")
    a3.legend(fontsize=7, loc="upper right")
    a3.set_title("...while nothing folds: the Jacobian stays regular",
                 fontsize=9, loc="left")

    a3.set_xlim(0.66, 1.65)
    fig.suptitle("How the cold insulator branch ends "
                 r"(Bethe, $m_g=3$, bare, $T/D=0.001$)",
                 fontsize=9.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.985))
    fs.save(fig, "fig_story_poleflight", OUT)


if __name__ == "__main__":
    main()
