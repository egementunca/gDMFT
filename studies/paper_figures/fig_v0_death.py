#!/usr/bin/env python3
"""V0 along the metal: the sqrt(Z) law, and where the branch (not V0) ends.

Supersedes the earlier "V0 death vs Z death" premise (2026-07-22): V0
never reaches 0 on the metal, because the branch ends first — the cold
spinodal kills the metal at finite Z (last basin=metal row: Z = 0.025,
V0 = 0.072 at U = 2.81). There is no death threshold to choose; the
cutoff is the branch's own existence boundary, read from the recorded
basin column (past it the chain records a bound-railed pseudo-family —
W at its cap, dead satellite, soft V0 — which is never plotted here).

(a) V0(U) with the measured law c*sqrt(Z(U)) overlaid (one fitted
    constant c per temperature, quoted on the panel), branch cut at the
    basin flip; the pseudo-tail region is shaded, not drawn.
(b) V0/sqrt(Z) vs U: the law constant, flat at strong coupling
    (0.455 D at T/D = 0.001 to 0.6% over the endgame), with the
    weak-coupling crossover visible at small U.
Bethe m_g=3, bare, v2 (single source).
"""

from __future__ import annotations

import math

import figstyle as fs
import matplotlib.pyplot as plt

import common

LATTICE, MG, DS, GAUGE = "bethe", 3, "v2", "bare"
TS = (0.001, 0.005, 0.01)
V0_COLOR = "#6a51a3"


def metal_series(t):
    """(u, V0, Z) along the metal, cut at the basin flip (recorded column)."""
    rows = common.point_rows(DS)
    entry = common.branch(DS, LATTICE, MG, GAUGE, t, "metal")
    out = []
    if entry is None:
        return out
    first_break = min(entry["breaks"]) if entry.get("breaks") else None
    for pos, idx in enumerate(entry["rows"]):
        r = rows[idx]
        # the branch ends at whichever comes first: the basin flip or a
        # recorded continuity break (prefix cut — the classifier
        # flip-flops in the pseudo-family region, so no filtering)
        if r["basin"] != "metal":
            break
        if first_break is not None and pos >= first_break:
            break
        p = common.pole_params(DS, idx)
        z = common.fnum(r["quasiparticle_weight_pole"])
        if p["v0"] is None or z is None or z <= 0:
            continue
        out.append((float(r["u_over_d"]), p["v0"], z))
    return sorted(out)


def main():
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.6, 3.2))
    for t in TS:
        pts = metal_series(t)
        if not pts:
            continue
        color = fs.shade(V0_COLOR, t, TS)
        us = [u for u, v0, z in pts]
        v0s = [v0 for u, v0, z in pts]
        # law constant c from the strongly correlated end (Z < 0.15)
        end = [(v0, z) for u, v0, z in pts if z < 0.15]
        c = (sum(v0 / math.sqrt(z) for v0, z in end) / len(end)) if end else None
        a.plot(us, v0s, color=color, lw=1.4,
               label=f"V0, T/D = {t:g}" + (f"  (c = {c:.3f})" if c else ""))
        if c is not None:
            a.plot(us, [c * math.sqrt(z) for u, v0, z in pts], color=color,
                   lw=0.9, ls=(0, (3, 2)), alpha=0.8)
        b.plot(us, [v0 / math.sqrt(z) for u, v0, z in pts], color=color,
               lw=1.4, label=f"T/D = {t:g}")
        if t == min(TS):
            a.axvspan(us[-1], 4.0, color="#999999", alpha=0.10, lw=0)
            a.text(us[-1] + 0.05, 0.30, "no metal branch\n(basin flip; "
                   "recorded rows there\nare a railed pseudo-family)",
                   fontsize=6.5, color="#666666", va="top")
            a.plot([us[-1]], [v0s[-1]], marker="o", ms=5, mfc="white",
                   color=color)
            a.annotate(f"branch end: Z = {pts[-1][2]:.3f}, V0 = {v0s[-1]:.3f}",
                       xy=(us[-1], v0s[-1]), xytext=(1.55, 0.115),
                       fontsize=6.5, color="#333333",
                       arrowprops={"arrowstyle": "-", "lw": 0.6,
                                   "color": "#888888"})
    a.set_xlabel(r"$U/D$")
    a.set_ylabel(r"$V_0/D$")
    a.set_xlim(0.4, 4.0)
    a.set_ylim(0, 0.36)
    a.legend(fontsize=6.5, frameon=False)
    a.set_title("V0 follows c·√Z to the branch end — dashed: the law",
                fontsize=8.5, loc="left")
    b.set_xlabel(r"$U/D$")
    b.set_ylabel(r"$V_0/\sqrt{Z}$  $(/D)$")
    b.set_xlim(0.4, 3.0)
    b.legend(fontsize=6.5, frameon=False)
    b.set_title("the constant: T-independent, saturating at the branch end",
                fontsize=8.5, loc="left")
    fig.suptitle("Central coupling on the metal: a law and a branch end, "
                 "not a death (Bethe, $m_g=3$, bare)", fontsize=9.5, y=1.0)
    fig.tight_layout()
    fs.save(fig, "fig_v0_death", common.OUT / "compare")


if __name__ == "__main__":
    main()
