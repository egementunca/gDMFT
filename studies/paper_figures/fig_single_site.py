#!/usr/bin/env python3
"""F5 — the single-site story: what each pole budget buys (registered data).

 (a) Bethe Z(U/D): full temperature ladder of the m_g=3 metal (viridis by T,
     v1 bare), the coldest insulator, and the m_g=1 metal at the coldest
     registered T (v2; the exact-T=0 arm was never imported — the
     Brinkman-Rice line marks the T=0 endpoint).
 (b) Bethe docc(U/D) both branches at the coldest T with U*.
 (c) (U/D, T/D) first-order region, both lattices: U*(T) and the metal
     spinodal U_c2(T) from the validated derive pipeline, coexistence
     shading, fresh prof-ruler markers, and the endpoint corridors UPDATED
     per the 2026-07-15 benchmark note: bethe (0.01, 0.015),
     square (0.004, 0.005).
 (d) Square Z(U/D) ladder (v2 bare) at matched T/D.

Bethe m_g=3 comes from v1 (the only bare-gauge bethe m_g=3 source);
square from v2. Port of the old fig_single_site.py.
"""

from __future__ import annotations

import math

import common
import figstyle as fs
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

EXACT_T0 = 1e-6  # v1 encodes the exact-T=0 arm as T/D ~ 5e-9


def t_color(t, ts):
    lo, hi = min(ts), max(ts)
    x = 0.15 + 0.75 * (math.log(t) - math.log(lo)) / max(
        math.log(hi) - math.log(lo), 1e-12
    )
    return cm.viridis(x)


def z_of(row, _index):
    value = common.fnum(row["quasiparticle_weight_pole"])
    return float("nan") if value is None else value


def docc_of(row, _index):
    value = common.fnum(row["double_occupancy"])
    return float("nan") if value is None else value


def ladder(ax, ds, lattice, mg, gauge):
    ts = [
        t
        for t in common.branch_temperatures(ds, lattice, mg, gauge, "metal")
        if t > EXACT_T0
    ]
    for t in ts:
        us, zs = common.branch_series(ds, lattice, mg, gauge, t, "metal", z_of)
        ax.plot(us, zs, "-", lw=1.0, color=t_color(t, ts))
    if ts:
        us, zs = common.branch_series(
            ds, lattice, mg, gauge, ts[0], "insul", z_of
        )
        ax.plot(us, zs, "-", lw=1.6, color=fs.BRANCH_COLOR["insul"],
                label=r"$M_g{=}3$ insulator")
    return ts


def add_colorbar(fig, ax, ts):
    mappable = cm.ScalarMappable(
        cmap=cm.viridis, norm=mcolors.LogNorm(vmin=min(ts), vmax=max(ts))
    )
    bar = fig.colorbar(mappable, ax=ax, pad=0.015, aspect=28)
    bar.set_label(r"$T/D$ ($M_g{=}3$ metal)", fontsize=7)
    bar.ax.tick_params(labelsize=6)


def build() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.4, 5.8))
    (ax, bx), (cx, dx) = axes

    # ---------------- (a) Bethe Z ladder (v1 bare) ----------------
    ts_b = ladder(ax, "v1", "bethe", 3, "bare")
    mg1_ts = common.branch_temperatures("v2", "bethe", 1, "bare", "metal")
    if mg1_ts:
        us, zs = common.branch_series(
            "v2", "bethe", 1, "bare", mg1_ts[0], "metal", z_of
        )
        ax.plot(us, zs, "k--", lw=1.1,
                label=rf"$M_g{{=}}1$, $T/D={mg1_ts[0]:g}$")
    u_br = 32.0 / (3 * math.pi)
    ax.axvline(u_br, color="0.7", lw=0.8)
    ax.annotate(r"$U_c^{\rm BR}$", xy=(u_br - 0.04, 0.62), fontsize=7,
                color="0.4", ha="right")
    add_colorbar(fig, ax, ts_b)
    ax.set_xlabel(r"$U/D$")
    ax.set_ylabel(r"$Z=|\tilde R_0|^2$")
    ax.set_title("(a) Bethe", fontsize=9, loc="left")
    ax.legend(fontsize=6.5, frameon=False)
    ax.set_xlim(0.45, 3.45)
    ax.set_ylim(-0.02, 1.0)

    # ---------------- (b) Bethe docc, both branches ----------------
    t_cold = ts_b[0]
    for kind, label in (("metal", "metal"), ("insul", "insulator")):
        us, ds_ = common.branch_series(
            "v1", "bethe", 3, "bare", t_cold, kind, docc_of
        )
        bx.plot(us, ds_, "-", lw=1.3, color=fs.BRANCH_COLOR[kind], label=label)
    bethe_ustar = common.ustar_curve("v1", "bethe", 3, "bare")
    us_cold = next((u for t, u in bethe_ustar if abs(t - t_cold) < 1e-12), None)
    if us_cold:
        bx.axvline(us_cold, color="0.55", lw=0.8, ls=":")
        bx.annotate(r"$U^{*}$", xy=(us_cold + 0.02, 0.16), fontsize=8,
                    color="0.4")
    bx.set_xlabel(r"$U/D$")
    bx.set_ylabel(r"$D=\langle n_\uparrow n_\downarrow\rangle$")
    bx.set_title(f"(b) Bethe, $T/D={t_cold:g}$", fontsize=9, loc="left")
    bx.legend(fontsize=7, frameon=False)
    bx.set_xlim(1.6, 3.25)

    # ---------------- (c) first-order region, both lattices ----------------
    for ds, lattice, color, marker in (
        ("v1", "bethe", fs.BRANCH_COLOR["metal"], "s"),
        ("v2", "square", fs.SQUARE_COLOR, "^"),
    ):
        # first-order line only up to the lattice's endpoint corridor —
        # crossings above it are crossover artifacts, not the line
        t_panel = common.CORRIDORS[lattice][0] + 5e-4
        ust = [
            (t, u)
            for t, u in common.ustar_curve(ds, lattice, 3, "bare")
            if t <= t_panel
        ]
        t_max = max((t for t, _ in ust), default=None)
        uc2 = [
            (t, u)
            for t, u in common.uc2_curve(ds, lattice, 3, "bare")
            if t_max is not None and t <= t_max
        ]
        if ust:
            cx.plot([u for _, u in ust], [t for t, _ in ust], marker + "-",
                    ms=4, lw=1.2, color=color, label=f"$U^*$ {lattice}")
        if uc2:
            cx.plot([u for _, u in uc2], [t for t, _ in uc2], marker + "--",
                    ms=3, lw=0.9, color=color, alpha=0.55,
                    label=f"$U_{{c2}}$ {lattice}")
        if ust and uc2:
            shared = sorted(
                set(t for t, _ in ust) & set(t for t, _ in uc2)
            )
            d_ust = dict((t, u) for t, u in ust)
            d_uc2 = dict((t, u) for t, u in uc2)
            cx.fill_betweenx(
                shared,
                [d_ust[t] for t in shared],
                [d_uc2[t] for t in shared],
                color=color,
                alpha=0.10,
                lw=0,
            )
        # endpoint corridor — the UPDATED bands from the benchmark notes
        lo, hi = common.CORRIDORS[lattice]
        cx.axhspan(lo, hi, color=color, alpha=0.07, lw=0)
    markers = common.ruler_markers()
    if markers:
        cx.plot([u for _, u in markers], [t for t, _ in markers], "o", ms=5,
                mfc="none", color=fs.BRANCH_COLOR["insul"],
                label="ghost_Mg3 (fresh ruler)")
    cx.set_xlabel(r"$U/D$")
    cx.set_ylabel(r"$T/D$")
    cx.set_ylim(0.0, 0.016)
    cx.set_title("(c) first-order region", fontsize=9, loc="left")
    cx.legend(fontsize=6.5, frameon=False, loc="upper left")

    # ---------------- (d) square Z ladder (v2 bare) ----------------
    ts_s = ladder(dx, "v2", "square", 3, "bare")
    sq_mg1 = common.branch_temperatures("v2", "square", 1, "bare", "metal")
    if sq_mg1:
        us, zs = common.branch_series(
            "v2", "square", 1, "bare", sq_mg1[0], "metal", z_of
        )
        dx.plot(us, zs, "k--", lw=1.1,
                label=rf"$M_g{{=}}1$, $T/D={sq_mg1[0]:g}$")
    add_colorbar(fig, dx, ts_s)
    dx.set_xlabel(r"$U/D$")
    dx.set_ylabel(r"$Z=|\tilde R_0|^2$")
    dx.set_title("(d) square (matched $T/D$)", fontsize=9, loc="left")
    dx.legend(fontsize=6.5, frameon=False)
    dx.set_xlim(0.45, 3.45)
    dx.set_ylim(-0.02, 1.0)

    fig.tight_layout()
    fs.save(fig, "fig_single_site", common.OUT)


if __name__ == "__main__":
    build()
