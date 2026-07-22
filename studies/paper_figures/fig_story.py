#!/usr/bin/env python3
"""The four story plots — static, self-contained, routes hardcoded.

No selection surface: every panel reads its verified route directly
(bethe m_g=3 = v1 bare; square m_g=3 = v2 bare; gem = registered csv).
Outputs runs/figures/story/fig_story_*.png|pdf:

  phase        U*(T) + U_c2(T), endpoint corridors shaded, crossover above
  pomeranchuk  Delta_S from -d(dOmega)/dT vs T and U, ln2 reference,
               Clausius-Clapeyron closure inset
  mottpole     insulator Sigma-pole weight vs U: atomic U^2/4, dressed
               U^2/4 - <eps^2>, both lattices, gem contrast
  closures     metal Sigma-weight ratio (ours flat, lattice-split) vs
               gem (rising), and the pole-position eta comparison
"""

from __future__ import annotations

import csv
import math

import common
import figstyle as fs
import matplotlib.pyplot as plt

OUT = common.OUT / "story"
CORRIDOR = {"bethe": (0.010, 0.015), "square": (0.004, 0.005)}
ROUTE = {"bethe": ("v1", "bare"), "square": ("v2", "bare")}
COL = {"bethe": "#185FA5", "square": "#993C1D",
       "ours": "#185FA5", "gem": "#BA7517"}


def branch_vals(lattice, t, kind, col):
    ds, gauge = ROUTE[lattice]
    rows = common.point_rows(ds)
    e = common.branch(ds, lattice, 3, gauge, t, kind)
    out = {}
    if e is None:
        return out
    for idx in e["rows"]:
        r = rows[idx]
        v = common.fnum(r[col])
        if v is not None:
            out[round(float(r["u_over_d"]), 3)] = v
    return out


def branch_poles(lattice, t, kind):
    ds, gauge = ROUTE[lattice]
    rows = common.point_rows(ds)
    e = common.branch(ds, lattice, 3, gauge, t, kind)
    out = []
    if e is None:
        return out
    for idx in e["rows"]:
        r = rows[idx]
        p = common.pole_params(ds, idx)
        if p["w"] is not None:
            out.append((float(r["u_over_d"]), p))
    return sorted(out)


def gem_rows_raw(lattice, budget, direction, t):
    path = common.DATA / "references-gem-gga-v1" / "points.csv"
    out = []
    with path.open(newline="") as stream:
        for r in csv.DictReader(stream):
            if (r["lattice"] != lattice or int(r["bath_budget"]) != budget
                    or r["direction"] != direction
                    or abs(float(r["t_over_d"]) - t) > 1e-12
                    or r["converged"] != "true"):
                continue
            try:
                wgt = [float(x) for x in
                       r["self_energy_pole_weights"].split(";") if x]
                pos = [float(x) for x in
                       r["self_energy_pole_positions"].split(";") if x]
            except ValueError:
                wgt, pos = [], []
            out.append((float(r["u_over_d"]), wgt, pos,
                        common.fnum(r["quasiparticle_weight_slope"])))
    return sorted(out)


# ---------------------------------------------------------------- 1 ------
def fig_phase():
    fig, ax = plt.subplots(figsize=(4.6, 3.4))
    for lattice, marker in (("bethe", "o"), ("square", "s")):
        ds, gauge = ROUTE[lattice]
        cap = CORRIDOR[lattice][0] + 1e-12
        us = [(t, u) for t, u in common.ustar_curve(ds, lattice, 3, gauge)
              if t <= cap]
        u2 = [(t, u) for t, u in common.uc2_curve(ds, lattice, 3, gauge)
              if t <= cap]
        c = COL[lattice]
        ax.plot([u for _, u in us], [t for t, _ in us], "-", color=c,
                marker=marker, ms=3.5, lw=1.4,
                label=f"{lattice}  $U^*(T)$")
        ax.plot([u for _, u in u2], [t for t, _ in u2], "--", color=c,
                marker=marker, ms=3, lw=1.0, mfc="none",
                label=f"{lattice}  $U_{{c2}}(T)$ (spinodal)")
        ax.axhspan(*CORRIDOR[lattice], color=c, alpha=0.12, lw=0)
        ax.annotate("endpoint corridor", xy=(2.28, sum(CORRIDOR[lattice]) / 2),
                    fontsize=6.5, color=c, va="center")
    ax.annotate("crossover only above the corridor\n(no first-order line)",
                xy=(2.38, 0.0170), fontsize=7, color="0.35", ha="center")
    ax.set_xlabel(r"$U/D$")
    ax.set_ylabel(r"$T/D$")
    ax.set_ylim(0, 0.021)
    ax.set_xlim(2.25, 2.9)
    ax.legend(fontsize=6.5, frameon=False, loc="upper right")
    ax.set_title("First-order Mott line and metal spinodal, both lattices",
                 fontsize=9)
    fig.tight_layout()
    fs.save(fig, "fig_story_phase", OUT)


# ---------------------------------------------------------------- 2 ------
def fig_pomeranchuk():
    ts = [0.001, 0.002, 0.003, 0.004, 0.005, 0.0065, 0.008, 0.01]
    OM = {t: (branch_vals("bethe", t, "metal", "grand_potential_over_d"),
              branch_vals("bethe", t, "insul", "grand_potential_over_d"))
          for t in ts}
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.8, 3.1))
    for u, c in ((2.5, "#185FA5"), (2.6, "#5DCAA5"), (2.7, "#BA7517")):
        xs, ys = [], []
        for i in range(1, len(ts) - 1):
            ok = True
            vals = []
            for t in (ts[i - 1], ts[i + 1]):
                m, ins = OM[t]
                if u in m and u in ins:
                    vals.append(ins[u] - m[u])
                else:
                    ok = False
            if ok:
                xs.append(ts[i])
                ys.append(-(vals[1] - vals[0]) / (ts[i + 1] - ts[i - 1]))
        ax.plot(xs, ys, "o-", ms=3.5, lw=1.2, color=c, label=f"$U/D={u}$")
    ax.axhline(math.log(2), color="0.3", ls=":", lw=1)
    ax.annotate(r"$\ln 2$ (free local moment)", xy=(0.0021, 0.70),
                fontsize=7.5, color="0.3")
    ax.set_xlabel(r"$T/D$")
    ax.set_ylabel(r"$\Delta S = S_{\rm ins}-S_{\rm met}$")
    ax.set_ylim(0.3, 0.75)
    ax.legend(fontsize=7, frameon=False, loc="lower left")
    ax.set_title(r"Entropy jump: $-\partial(\Delta\Omega)/\partial T$",
                 fontsize=9)

    # Clausius-Clapeyron closure: slope-inferred Delta_S vs direct
    ustar = dict(common.ustar_curve("v1", "bethe", 3, "bare"))
    tt = sorted(t for t in ustar if t <= 0.0101)
    xs, ys = [], []
    for i, t in enumerate(tt):
        if i == 0 or i == len(tt) - 1:
            continue
        dudt = (ustar[tt[i + 1]] - ustar[tt[i - 1]]) / (tt[i + 1] - tt[i - 1])
        dm = branch_vals("bethe", t, "metal", "double_occupancy")
        di = branch_vals("bethe", t, "insul", "double_occupancy")
        shared = sorted(set(dm) & set(di), key=lambda u: abs(u - ustar[t]))
        if not shared:
            continue
        u0 = shared[0]
        xs.append(t)
        ys.append(-dudt * (dm[u0] - di[u0]))
    bx.plot(xs, ys, "D-", ms=3.5, lw=1.2, color="#534AB7",
            label=r"$-\,\frac{dU^*}{dT}\,\Delta D$  (Clausius–Clapeyron)")
    # direct value at U nearest U* for comparison
    xs2, ys2 = [], []
    for i in range(1, len(tt) - 1):
        t = tt[i]
        u0 = round(2.7 if t <= 0.003 else 2.6 if t <= 0.0065 else 2.5, 2)
        vals = []
        ok = True
        for tside in (tt[i - 1], tt[i + 1]):
            m, ins = OM[tside]
            if u0 in m and u0 in ins:
                vals.append(ins[u0] - m[u0])
            else:
                ok = False
        if ok:
            xs2.append(t)
            ys2.append(-(vals[1] - vals[0]) / (tt[i + 1] - tt[i - 1]))
    bx.plot(xs2, ys2, "o--", ms=3.5, lw=1.0, color="#0F6E56",
            label=r"direct $-\partial(\Delta\Omega)/\partial T$ near $U^*$")
    bx.axhline(math.log(2), color="0.3", ls=":", lw=1)
    bx.set_xlabel(r"$T/D$")
    bx.set_ylim(0.3, 0.75)
    bx.legend(fontsize=6.5, frameon=False, loc="lower left")
    bx.set_title("The relation closes on our own line", fontsize=9)
    fig.suptitle("The electronic Pomeranchuk effect, measured (Bethe, m$_g$=3)",
                 fontsize=9.5, y=1.0)
    fig.tight_layout()
    fs.save(fig, "fig_story_pomeranchuk", OUT)


# ---------------------------------------------------------------- 3 ------
def fig_mottpole():
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    for lattice, marker in (("bethe", "o"), ("square", "s")):
        ch = branch_poles(lattice, 0.001, "insul")
        us = [u for u, p in ch if u >= 1.3]
        w2 = [2 * p["w"] ** 2 for u, p in ch if u >= 1.3]
        ax.plot(us, [u * u / 4 - w for u, w in zip(us, w2)], marker + "-",
                color=COL[lattice], ms=2.5, lw=1.1,
                label=f"{lattice}: $U^2/4 - 2W^2$ (matching)")
    gem = gem_rows_raw("bethe", 3, "down", 0.001)
    gus = [u for u, w, p, z in gem if w and z is not None and z < 0.01]
    gdef = [u * u / 4 - sum(w) for u, w, p, z in gem
            if w and z is not None and z < 0.01]
    ax.plot(gus, gdef, "^", color=COL["gem"], ms=4,
            label="bethe: gem/gGA (variational)")
    ax.axhline(0.25, color="0.3", ls=":", lw=1)
    ax.annotate(r"band variance $\langle\epsilon_k^2\rangle = D^2/4$",
                xy=(1.45, 0.262), fontsize=7.5, color="0.3")
    ax.axhline(0.0, color="0.6", lw=0.7)
    ax.annotate("Hubbard-I (undressed pole)", xy=(1.45, 0.02), fontsize=7,
                color="0.5")
    ax.set_xlabel(r"$U/D$")
    ax.set_ylabel(r"Mott-pole weight deficit  $U^2/4 - \Sigma$-pole weight")
    ax.set_ylim(-0.05, 0.62)
    ax.legend(fontsize=6.5, frameon=False, loc="upper right")
    ax.set_title("The dressed Mott pole: atomic weight minus band variance",
                 fontsize=9)
    fig.tight_layout()
    fs.save(fig, "fig_story_mottpole", OUT)


# ---------------------------------------------------------------- 4 ------
def fig_closures():
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.8, 3.1))
    for lattice, marker in (("bethe", "o"), ("square", "s")):
        ch = branch_poles(lattice, 0.001, "metal")
        pts = [(u, 2 * p["w"] ** 2 / (u * u / 4)) for u, p in ch
               if 0.8 <= u <= 2.75]
        ax.plot([u for u, _ in pts], [r for _, r in pts], marker, ms=2.2,
                color=COL[lattice], label=f"ours, {lattice}")
    gem = gem_rows_raw("bethe", 3, "up", 0.001)
    pts = [(u, sum(w) / (u * u / 4)) for u, w, p, z in gem
           if w and 0.8 <= u <= 2.75]
    ax.plot([u for u, _ in pts], [r for _, r in pts], "^", ms=3,
            color=COL["gem"], label="gem, bethe")
    ax.axhline(1.0, color="0.3", ls=":", lw=1)
    ax.annotate("exact first moment $U^2/4$", xy=(0.9, 1.02), fontsize=7.5,
                color="0.3")
    ax.set_xlabel(r"$U/D$")
    ax.set_ylabel(r"$\Sigma$-pole weight / $(U^2/4)$")
    ax.set_ylim(0.4, 1.1)
    ax.legend(fontsize=6.5, frameon=False, loc="lower right")
    ax.set_title("How each closure spends the moment", fontsize=9)

    ch = branch_poles("bethe", 0.001, "metal")
    ax2pts = [(u, p["eta"]) for u, p in ch if 0.5 <= u <= 2.8]
    bx.plot([u for u, _ in ax2pts], [e for _, e in ax2pts], "o", ms=2.2,
            color=COL["ours"], label=r"ours: $\eta$")
    gpts = [(u, sum(abs(x) for x in p) / len(p)) for u, w, p, z in gem
            if p and 0.5 <= u <= 2.8]
    bx.plot([u for u, _ in gpts], [e for _, e in gpts], "^", ms=3,
            color=COL["gem"], label=r"gem: $\eta$")
    bx.set_xlabel(r"$U/D$")
    bx.set_ylabel(r"$\Sigma$-pole position $\eta/D$")
    bx.legend(fontsize=7, frameon=False, loc="lower left")
    bx.set_title("...and where it puts the pole", fontsize=9)
    fig.suptitle("Same manifold, two metrics (metal branch, T/D = 0.001)",
                 fontsize=9.5, y=1.0)
    fig.tight_layout()
    fs.save(fig, "fig_story_closures", OUT)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    fig_phase()
    fig_pomeranchuk()
    fig_mottpole()
    fig_closures()
    print(f"wrote 4 figures -> {OUT}")


if __name__ == "__main__":
    main()
