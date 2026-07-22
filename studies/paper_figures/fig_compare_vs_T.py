#!/usr/bin/env python3
"""Observables vs temperature at fixed U/D (Bethe), across methods.

Rows: docc, Z, E_tot/D. Columns: U/D ∈ {1.0, 2.0, 3.2} (the NRG anchor
cuts). Each panel shows the temperature dependence for ghost-DMFT, gGA, and
NRG (thermal exact where available); DMFT-ED (T=0) is drawn as a horizontal
reference line. Reads the registered vs-T slice compare_vs_T.csv.
"""

from __future__ import annotations

import csv
import math

import compare
import figstyle as fs
import matplotlib.pyplot as plt

import common

U_CUTS = (1.0, 2.0, 3.2)
OBS = [("docc", compare.OBS_LABEL["docc"]),
       ("z", compare.OBS_LABEL["z"]),
       ("etot", compare.OBS_LABEL["etot"])]
BUDGET = 3


def _rows():
    out = []
    with (common.BENCH / "compare_vs_T.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            out.append({
                "method": row["method"],
                "budget": int(row["budget"]),
                "t": float(row["T"]),
                "u": float(row["U_over_D"]),
                "branch": row["branch"],
                "z": common.fnum(row["Z"]),
                "docc": common.fnum(row["docc"]),
                "etot": common.fnum(row["etot"]),
                "sumr2": common.fnum(row["sumR2"]),
            })
    return out


def _series(rows, method, u, obs, budget=BUDGET):
    pairs = []
    for row in rows:
        if row["method"] != method or not math.isclose(row["u"], u, rel_tol=1e-6):
            continue
        if method in ("ghost_dmft", "gga_gem", "dmft_ed") and row["budget"] != budget:
            continue
        if method == "gga_gem" and row["branch"] != "up":
            continue
        if method == "ghost_dmft" and row["branch"] not in ("metal",):
            continue
        if (method == "gga_gem" and row["sumr2"] is not None
                and row["sumr2"] > compare.SUMR2_MAX):
            continue
        if row[obs] is not None:
            pairs.append((row["t"], row[obs]))
    pairs.sort()
    return [t for t, _ in pairs], [y for _, y in pairs]


def build() -> None:
    rows = _rows()
    fig, axs = plt.subplots(len(OBS), len(U_CUTS), figsize=(7.6, 6.0),
                            sharex=True)
    for r, (obs, label) in enumerate(OBS):
        for c, u in enumerate(U_CUTS):
            ax = axs[r, c]
            for method in ("ghost_dmft", "gga_gem", "nrg"):
                ts, ys = _series(rows, method, u, obs)
                if ts:
                    ax.plot(ts, ys, "-", marker=compare.METHOD_MARKER.get(method, "^"),
                            ms=3, lw=1.0, color=fs.FRAMEWORK_COLOR[method],
                            label=fs.FRAMEWORK_NAME[method])
            # DMFT-ED (T=0) as a horizontal anchor
            et, ey = _series(rows, "dmft_ed", u, obs)
            if ey:
                ax.axhline(ey[0], ls=(0, (5, 2)), lw=0.9,
                           color=fs.FRAMEWORK_COLOR["dmft_ed"],
                           label=f"{fs.FRAMEWORK_NAME['dmft_ed']} ($T=0$)")
            ax.set_xscale("log")
            ax.grid(alpha=0.25, lw=0.4)
            if r == 0:
                ax.set_title(rf"$U/D={u:g}$", fontsize=9)
            if c == 0:
                ax.set_ylabel(label)
            if r == len(OBS) - 1:
                ax.set_xlabel(r"$T/D$")
    axs[0, 0].legend(fontsize=6.0, loc="best")
    fig.suptitle(
        rf"Bethe $M_g={BUDGET}$: observables vs temperature at fixed $U/D$",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    compare.benchmark_note(fig)
    fs.save(fig, "compare_vs_T_bethe_mg3", compare.outdir("bethe"))


if __name__ == "__main__":
    build()
