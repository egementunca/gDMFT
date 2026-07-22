#!/usr/bin/env python3
"""Where the central bath coupling V0 dies vs where Z dies (ghost-DMFT).

V0 (the central hybridization coupling, position-fixed at ε=0, so it is not
bound-limited) and Z both collapse toward zero at the Mott edge. If they
cross zero at *different* U/D — or diverge with temperature — that is
physically suggestive (flagged by the user; we plot, not interpret).

(a) V0(U) (solid) and Z(U) (dashed) along the metal branch at a few T, with
    death markers where each falls below the threshold.
(b) The death loci U(V0→0) and U(Z→0) vs T, with the metal spinodal U_c2(T)
    for reference.
Bethe m_g=3 (v1).
"""

from __future__ import annotations

import compare
import figstyle as fs
import matplotlib.pyplot as plt

import common

LATTICE, MG = "bethe", 3
THR = 0.05  # "death" threshold in units of D
V0_COLOR = "#6a51a3"   # central coupling
Z_COLOR = fs.FRAMEWORK_COLOR["ghost_dmft"]


def _series(t):
    r = compare.route(LATTICE, MG)
    DS, GAUGE = r["ds"], r["gauge"]
    entry = common.branch(DS, LATTICE, MG, GAUGE, t, "metal")
    if entry is None:
        return [], [], []
    rows = common.point_rows(DS)
    us, v0s, zs = [], [], []
    for index in entry["rows"]:
        us.append(float(rows[index]["u_over_d"]))
        v0s.append(common.pole_params(DS, index)["v0"])
        zs.append(common.fnum(rows[index]["quasiparticle_weight_pole"]))
    return us, v0s, zs


def _death_u(us, ys, thr=THR):
    """First U (in increasing U) where y drops below thr."""
    for u, y in zip(us, ys):
        if y is not None and y < thr:
            return u
    return None


def _shade(base, t, ts):
    return fs.shade(base, t, ts)


def build() -> None:
    r = compare.route(LATTICE, MG)
    DS, GAUGE = r["ds"], r["gauge"]
    all_ts = [t for t in common.branch_temperatures(DS, LATTICE, MG, GAUGE, "metal")
              if t > 1e-6]
    if not all_ts:
        print("  (no bethe m_g=3 metal branch; skipped V0 death)")
        return
    show_ts = compare.select_temperatures(all_ts, (0.001, 0.01, 0.03))

    fig, (ax, bx) = plt.subplots(1, 2, figsize=(7.4, 3.2))

    # ---- (a) V0(U) and Z(U) with death markers ----
    for t in show_ts:
        us, v0s, zs = _series(t)
        ax.plot(us, v0s, "-", lw=1.2, color=_shade(V0_COLOR, t, show_ts))
        ax.plot(us, zs, "--", lw=1.0, color=_shade(Z_COLOR, t, show_ts))
        for ys, col in ((v0s, V0_COLOR), (zs, Z_COLOR)):
            ud = _death_u(us, ys)
            if ud is not None:
                ax.axvline(ud, color=_shade(col, t, show_ts), lw=0.6, ls=":")
    ax.axhline(THR, color="0.7", lw=0.7, ls=":")
    ax.plot([], [], "-", color=V0_COLOR, label=r"$V_0$ (central coupling)")
    ax.plot([], [], "--", color=Z_COLOR, label=r"$Z$")
    ax.set_xlabel(r"$U/D$")
    ax.set_ylabel(r"$V_0/D$,  $Z$")
    ax.set_xlim(1.5, 3.4)
    ax.set_ylim(-0.02, 1.0)
    ax.grid(alpha=0.25, lw=0.4)
    ax.legend(fontsize=7, loc="upper right")
    ax.set_title(rf"(a) $V_0$ and $Z$ vs $U$ (shade: $T/D$="
                 rf"{', '.join(f'{t:g}' for t in show_ts)})", fontsize=8.5,
                 loc="left")

    # ---- (b) death loci U(V0->0), U(Z->0), and U_c2 vs T ----
    tv0, uv0, tz, uz = [], [], [], []
    for t in all_ts:
        us, v0s, zs = _series(t)
        du0, duz = _death_u(us, v0s), _death_u(us, zs)
        if du0 is not None:
            tv0.append(t); uv0.append(du0)
        if duz is not None:
            tz.append(t); uz.append(duz)
    bx.plot(uv0, tv0, "-o", ms=3.5, color=V0_COLOR,
            label=r"$U(V_0<%.2g)$" % THR)
    bx.plot(uz, tz, "--s", ms=3.2, color=Z_COLOR, label=r"$U(Z<%.2g)$" % THR)
    uc2 = common.uc2_curve(DS, LATTICE, MG, GAUGE)
    if uc2:
        bx.plot([u for _, u in uc2], [t for t, _ in uc2], "-", lw=0.9,
                color="0.55", label=r"$U_{c2}$ (metal edge)")
    bx.set_xlabel(r"$U/D$")
    bx.set_ylabel(r"$T/D$")
    bx.set_yscale("log")
    bx.grid(alpha=0.25, lw=0.4)
    bx.legend(fontsize=6.6, loc="best")
    bx.set_title(r"(b) death loci vs temperature", fontsize=8.5, loc="left")

    fig.suptitle(
        r"ghost-DMFT (Bethe $M_g{=}3$): the bath coupling $V_0$ going to zero",
        fontsize=9.3,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.93))
    compare.gauge_caption(fig, LATTICE, MG)
    fs.save(fig, "v0_death_bethe_mg3", compare.outdir("bethe"))


if __name__ == "__main__":
    build()
