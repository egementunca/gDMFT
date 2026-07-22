#!/usr/bin/env python3
"""Convergence with bath size at U/D = 2.4 (Bethe, metallic, coldest rows).

docc, Z, E_tot/D vs bath size (M_g / B / N_b) for ghost-DMFT, gGA, DMFT-ED.
Shows every framework marching toward the same value as poles are added —
the "→ exact DMFT as the pole expansion grows" statement, with DMFT-ED
(N_b up to 5) as the exact reference.
"""

from __future__ import annotations

import math

import compare
import figstyle as fs
import matplotlib.pyplot as plt

import common

U = 2.4
OBS = [("docc", compare.OBS_LABEL["docc"]),
       ("etot", compare.OBS_LABEL["etot"]),
       ("z", compare.OBS_LABEL["z"])]


def _value(method, budget, obs):
    for row in common.compare_rows():
        if row["method"] != method or row["budget"] != budget:
            continue
        if not math.isclose(row["u"], U, rel_tol=1e-6):
            continue
        if row["branch"] not in ("metal", "up"):
            continue
        if method != "dmft_ed" and not math.isclose(row["t"], 0.001, rel_tol=1e-6):
            continue
        y = row["u"] * row["docc"] if obs == "epot" else row[obs]
        if y is not None:
            return y
    return None


def build() -> None:
    fig, axs = plt.subplots(1, 3, figsize=(7.2, 2.7))
    plan = [
        ("ghost_dmft", (1, 3)),
        ("gga_gem", (1, 3)),
        ("dmft_ed", (1, 3, 5)),
    ]
    for ax, (obs, label) in zip(axs, OBS, strict=True):
        for method, budgets in plan:
            xs, ys = [], []
            for b in budgets:
                v = _value(method, b, obs)
                if v is not None:
                    xs.append(b)
                    ys.append(v)
            ax.plot(xs, ys, marker=compare.METHOD_MARKER[method], ms=6, lw=1.2,
                    mfc=("none" if method == "dmft_ed" else None),
                    color=fs.FRAMEWORK_COLOR[method],
                    label=fs.FRAMEWORK_NAME[method])
        ax.set_xticks([1, 3, 5])
        ax.set_xlabel(r"bath size ($M_g$ / $B$ / $N_b$)")
        ax.set_ylabel(label)
        ax.grid(alpha=0.25, lw=0.4)
    axs[2].legend(fontsize=6.6, loc="best")
    fig.suptitle(
        r"Convergence with bath size at $U/D=2.4$ (Bethe, metallic, coldest)",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 0.92))
    compare.benchmark_note(fig)
    fs.save(fig, "compare_convergence_bethe_U2.4", compare.outdir("bethe"))


if __name__ == "__main__":
    build()
