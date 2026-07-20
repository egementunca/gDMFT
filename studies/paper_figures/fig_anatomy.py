#!/usr/bin/env python3
"""F1 — converged gateway/ghost parameters along both branches (Bethe).

 (a) bath couplings V0 (central) and V1 (satellite pair): the order
     parameter anatomy — insulator has V0 -> 0 with V1 ALIVE.
 (b) Σ-pole content: weight W vs the atomic U/(2√2) and position η -> 0.
 (c) satellite bath position ε_g vs the Hubbard-band scale U/2.
 (d) double occupancy D(U) on both branches with ΔD at U*.

Data: v1 bethe m_g=3 bare branches; bath parameters from the registered
lossless raw archive via gdmft.atlas.poles. Port of the old fig_anatomy.py
(coldest T solid, warmest T dashed).
"""

from __future__ import annotations

import math

import common
import figstyle as fs
import matplotlib.pyplot as plt
import numpy as np

CM = {"metal": fs.BRANCH_COLOR["metal"], "insul": fs.BRANCH_COLOR["insul"]}


def series(kind, t, key):
    def value(row, index):
        if key == "docc":
            v = common.fnum(row["double_occupancy"])
        else:
            v = common.pole_params("v1", index)[key]
        return float("nan") if v is None else v

    return common.branch_series("v1", "bethe", 3, "bare", t, kind, value)


def build() -> None:
    ts = [
        t
        for t in common.branch_temperatures("v1", "bethe", 3, "bare", "metal")
        if t > 1e-6
    ]
    t_cold, t_warm = ts[0], ts[-1]
    ustar = common.ustar_curve("v1", "bethe", 3, "bare")
    us = next((u for t, u in ustar if abs(t - t_cold) < 1e-12), None)

    fig, axes = plt.subplots(2, 2, figsize=(7.1, 5.4))
    (ax, bx), (cx, dx) = axes

    for kind in ("metal", "insul"):
        color = CM[kind]
        label_kind = "metal" if kind == "metal" else "insulator"
        for t, ls, lw in ((t_cold, "-", 1.4), (t_warm, "--", 0.9)):
            u_v0, v0 = series(kind, t, "v0")
            u_v1, v1 = series(kind, t, "v1")
            ax.plot(u_v0, v0, ls, lw=lw, color=color,
                    label=f"$V_0$ {label_kind}, $T/D={t:g}$")
            ax.plot(u_v1, v1, ls, lw=lw, color=color, alpha=0.45)
            u_w, w = series(kind, t, "w")
            u_e, eta = series(kind, t, "eta")
            bx.plot(u_w, w, ls, lw=lw, color=color)
            bx.plot(u_e, eta, ls, lw=lw, color=color, alpha=0.45)
            u_g, eps_g = series(kind, t, "eps1")
            cx.plot(u_g, eps_g, ls, lw=lw, color=color)
            u_d, docc = series(kind, t, "docc")
            dx.plot(u_d, docc, ls, lw=lw, color=color,
                    label=f"{label_kind}, $T/D={t:g}$")

    ug = np.linspace(0.5, 3.2, 50)
    bx.plot(ug, ug / (2 * math.sqrt(2)), "k:", lw=0.9)
    bx.annotate(r"$W_{\rm atomic}=U/2\sqrt{2}$", xy=(2.05, 0.83), fontsize=7,
                rotation=13)
    cx.plot(ug, ug / 2, "k:", lw=0.9)
    cx.annotate(r"$U/2$", xy=(2.9, 1.55), fontsize=7)

    for axis in (ax, bx, cx, dx):
        if us:
            axis.axvline(us, color="0.6", lw=0.7, ls=":")
        axis.set_xlim(0.45, 3.25)
        axis.set_xlabel(r"$U/D$")
    if us:
        ax.annotate(r"$U^{*}$", xy=(us + 0.02, ax.get_ylim()[1] * 0.9),
                    fontsize=8, color="0.4")

    ax.set_ylabel(r"$V_0$ (solid tone), $V_1$ (faint)")
    ax.set_title("(a) bath couplings: the order parameter", fontsize=9,
                 loc="left")
    ax.annotate("insulator: $V_0\\to 0$,\n$V_1$ ALIVE", xy=(2.6, 0.62),
                fontsize=7, color=CM["insul"])
    ax.annotate("metal", xy=(0.9, 0.62), fontsize=7, color=CM["metal"])
    ax.legend(fontsize=5.6, frameon=False, loc="upper right")

    bx.set_ylabel(r"$W$ (solid tone), $\eta$ (faint)")
    bx.set_title(r"(b) $\Sigma$-pole content: $\Sigma W^2\to U^2/4$, "
                 r"$\eta\to 0$", fontsize=9, loc="left")

    cx.set_ylabel(r"$\epsilon_g$")
    cx.set_title("(c) satellite bath position", fontsize=9, loc="left")

    dx.set_ylabel(r"$D=\langle n_\uparrow n_\downarrow\rangle$")
    dx.set_title(r"(d) double occupancy, $\Delta D$ at $U^{*}$", fontsize=9,
                 loc="left")
    dx.legend(fontsize=6.5, frameon=False)

    fig.tight_layout()
    fs.save(fig, "fig_anatomy", common.OUT)


if __name__ == "__main__":
    build()
