#!/usr/bin/env python3
"""What the budget controls captured about U_c1 — and what they prove
cannot be captured.

Four panels from the 2026-07-22 control runs (all Bethe, bare,
T/D = 0.001, insulator-down):

(a) The Mott-pole weight 2W^2 vs the dressed law (U^2-D^2)/4 at
    M_g = 3 and 5 (and the M_h=4 active pair): identical at every
    budget - law + a finite-T offset exhausted exactly at the
    crossover, frozen ~0.05 below it. The exact insulator's death
    region (U ~ 2.0-2.4) shows NO feature at any budget.
(b) The satellite position: finite valley down to U = 1.125, then the
    flight - at the SAME U_x for both budgets.
(c) The residuals: root-plateau quality straight through U_c1^gGA and
    U_c1^DMFT (the smoking gun that the closure carries no death
    mechanism there), ramping only below U_x.
(d) The renormalizer share c(U) of the split-duty bath: what the
    insulator increasingly wants as U falls is an omega-linear
    channel, heading for the flight limit c* ~ 0.4.

Data: data/mg5_insul_bethe_T0.001.txt, data/mh4_insul_bethe_T0.001.txt,
data/mg3_box240_channel_bethe_T0.001.csv (provenance in headers).
"""

from __future__ import annotations

import csv
from pathlib import Path

import common
import figstyle as fs
import matplotlib.pyplot as plt

OUT = common.OUT / "story"
DATA = Path(__file__).parent / "data"
C3 = fs.FRAMEWORK_COLOR["ghost_dmft"]
C5 = "#7b1fa2"
C4 = "#2ca02c"
CCH = "#BA7517"
U_X = (1.100, 1.125)
ENDS = ((2.0, "$U_{c1}^{gGA}$ (Lanata)"), (2.4, "$U_{c1}^{DMFT}$ (exact)"))


def read_pipe(name, cols):
    rows = []
    for line in (DATA / name).open():
        if line.startswith("#") or line.startswith("U |") or "DONE" in line:
            continue
        parts = [p.strip() for p in line.split("|")]
        if len(parts) < len(cols):
            continue
        try:
            rows.append({c: float(parts[i]) for i, c in enumerate(cols)})
        except ValueError:
            continue
    return sorted(rows, key=lambda r: r["U"])


def read_csvfile():
    a, b = [], []
    with (DATA / "mg3_box240_channel_bethe_T0.001.csv").open() as stream:
        for r in csv.DictReader(x for x in stream if not x.startswith("#")):
            row = {k: (float(v) if v else None) for k, v in r.items()
                   if k != "kind"}
            (a if r["kind"] == "mg3box240" else b).append(row)
    return sorted(a, key=lambda r: r["U"]), sorted(b, key=lambda r: r["U"])


def marks(ax, ends=True, ux=True):
    if ux:
        ax.axvspan(U_X[0], U_X[1], color="#d62728", alpha=0.15, lw=0)
    ax.axvline(1.0, color="black", lw=0.7, ls=":")
    if ends:
        for u, _label in ENDS:
            ax.axvline(u, color="#999999", lw=0.9, ls=(0, (5, 3)))


def main():
    mg5 = read_pipe("mg5_insul_bethe_T0.001.txt",
                    ("U", "V0", "v1", "e1", "v2", "e2", "W", "w2", "law", "F"))
    mh4 = read_pipe("mh4_insul_bethe_T0.001.txt",
                    ("U", "v1", "e1", "W1", "eta1", "W2", "eta2", "w2", "law",
                     "F"))
    mg3, ch = read_csvfile()

    fig, ((a, b), (c, d)) = plt.subplots(2, 2, figsize=(8.0, 6.6))

    # (a) weight vs law
    us = [r["U"] for r in mg5 if r["U"] <= 2.6]
    a.plot(us, [(u * u - 1) / 4 for u in us], "k:", lw=1.2,
           label=r"law $(U^2-D^2)/4$")
    a.plot(us, [r["w2"] for r in mg5 if r["U"] <= 2.6], "-", color=C5,
           lw=1.4, label=r"$m_g=5$")
    a.plot([r["U"] for r in mg3], [r["twoW2"] for r in mg3], "o", ms=4,
           mfc="white", color=C3, label=r"$m_g=3$ (box 240)")
    m4 = [r for r in mh4 if r["U"] <= 2.6][::4]
    a.plot([r["U"] for r in m4], [r["w2"] - 2 * 0.3 ** 2 for r in m4], "^",
           ms=4, mfc="white", color=C4, label=r"$m_h=4$ active pair")
    marks(a)
    a.text(2.0, 1.47, ENDS[0][1], fontsize=6.5, ha="center", va="top",
           color="#777777")
    a.text(2.42, 1.32, ENDS[1][1], fontsize=6.5, ha="right", va="top",
           color="#777777")
    a.text(2.2, 0.62, "no feature at any budget\nwhere the exact insulator dies",
           fontsize=7, color="#777777", ha="center")
    a.text(1.112, 1.0, "$U_x$", fontsize=7.5, color="#d62728", ha="center")
    a.set_xlim(0.82, 2.62)
    a.set_ylim(0, 1.55)
    a.set_xlabel("$U/D$")
    a.set_ylabel(r"$2W^2$ (Mott-pole weight)")
    a.legend(fontsize=6.5, loc="upper left")
    a.set_title("(a) the weight law: identical at every budget", fontsize=9,
                loc="left")

    # (b) satellite position
    b.semilogy([r["U"] for r in mg3], [r["eps_g"] for r in mg3], "o-", ms=4,
               mfc="white", color=C3, label=r"$m_g=3$ (box 240)")
    b.semilogy([r["U"] for r in mg5 if r["U"] <= 2.0],
               [r["e1"] for r in mg5 if r["U"] <= 2.0], "-", color=C5,
               lw=1.4, label=r"$m_g=5$, pair 1")
    marks(b, ends=False)
    b.text(1.16, 28, "$U_x$ = same place,\nboth budgets", fontsize=7,
           color="#d62728", ha="left", va="center")
    b.set_xlim(0.82, 2.02)
    b.set_ylabel(r"$\epsilon_g$ (satellite position, raw)")
    b.set_xlabel("$U/D$")
    b.legend(fontsize=6.5, loc="upper right")
    b.set_title("(b) the flight: budget-independent crossover", fontsize=9,
                loc="left")

    # (c) residuals
    c.semilogy([r["U"] for r in mg5], [r["F"] for r in mg5], "-", color=C5,
               lw=1.4, label=r"$m_g=5$")
    c.semilogy([r["U"] for r in mg3], [r["resnorm"] for r in mg3], "o", ms=4,
               mfc="white", color=C3, label=r"$m_g=3$ (box 240)")
    marks(c)
    c.axhspan(6e-7, 3e-5, color="#2ca02c", alpha=0.08, lw=0)
    c.text(3.3, 1.1e-5, "root plateau", fontsize=6.5, color="#2ca02c",
           ha="right")
    c.text(2.2, 6.5e-4, "smooth through both", fontsize=6.5, ha="center",
           color="#777777")
    c.set_xlim(0.82, 4.05)
    c.set_ylim(4e-7, 1e-3)
    c.set_xlabel("$U/D$")
    c.set_ylabel(r"residual $\|F\|$")
    c.legend(fontsize=6.5, loc="lower left")
    c.set_title("(c) plateau straight through the exact death region",
                fontsize=9, loc="left")

    # (d) renormalizer share
    d.plot([r["U"] for r in ch], [r["v1_over_eps"] for r in ch], "s-", ms=5,
           color=CCH, label=r"channel share $c$ (split-duty bath)")
    cstar = [r["v1_over_eps"] ** 2 for r in mg3 if r["U"] <= 1.05]
    d.axhspan(min(cstar), max(cstar), color=C3, alpha=0.12, lw=0)
    d.text(2.95, 0.405, r"flight limit $c^*$ ($m_g=3$, box 240)",
           fontsize=6.5, color=C3, ha="right", va="center")
    marks(d, ends=False)
    d.set_xlim(0.82, 3.1)
    d.set_ylim(0, 0.47)
    d.set_xlabel("$U/D$")
    d.set_ylabel(r"$c$ ($\omega$-linear bath share)")
    d.legend(fontsize=6.5, loc="center right")
    d.set_title("(d) what the insulator increasingly wants", fontsize=9,
                loc="left")

    fig.suptitle("Budget controls, insulator-down (Bethe, bare, $T/D=0.001$): "
                 "what relates to $U_{c1}$ and what provably cannot",
                 fontsize=9.5, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.975))
    fs.save(fig, "fig_story_budget_controls", OUT)


if __name__ == "__main__":
    main()
