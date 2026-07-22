#!/usr/bin/env python3
"""Converged bath / pole parameters vs U/D (ours), with a gGA Σ-pole overlay.

2x3 panels: V0, V1 (g-sector hybridization couplings), ε1 (satellite
position), W, η (Σ-pole weight & position), Λ=√(η²+2W²). Ghost-DMFT metal
branch as a temperature ladder. Poles pinned at the solver's position box
(satellite ε1 at the lattice box edge, high-T η at 8) are FILTERED — their
position is undetermined (bound-limited audit); the g-sector satellite panels
are marker-only where survivors are sparse. gGA's Σ-pole position η (the
framework-invariant one) is overlaid as cold markers.

Source (dataset + gauge) is resolved from the catalog primary-route policy
and stamped on the figure; override with GDMFT_FIG_GAUGE. Parameters ARE
gauge-dependent, so the stamp matters here.
"""

from __future__ import annotations

import math

import compare
import figstyle as fs
import matplotlib.pyplot as plt

import common

PARAMS = [
    ("v0", r"$V_0$"), ("v1inv", r"$V_1^2/\epsilon_1$ (slope invariant)"),
    ("eps1", r"$\epsilon_1$"),
    ("w", r"$W$"), ("eta", r"$\eta$"), ("lam", r"$\Lambda=\sqrt{\eta^2+2W^2}$"),
]


Z_TAIL = 5e-3  # below this the quasiparticle is gone: the branch assembly's
               # post-collapse continuation (railed W, dead satellite) is not
               # the metal and must not plot as if it were.


def _ghost_series(lattice, m_g, t, key):
    """Per-quantity trust: g-sector satellite (V1, ε1) dropped where the
    position is box-pinned; V0/W/η/Λ dropped only where η itself is pinned;
    post-collapse tail rows (Z < Z_TAIL) dropped from every panel."""
    r = compare.route(lattice, m_g)
    entry = common.branch(r["ds"], lattice, m_g, r["gauge"], t, "metal")
    if entry is None:
        return [], [], [], [], 0, 0
    rows = common.point_rows(r["ds"])
    satellite = key == "eps1"  # only the raw position is box-censored;
    # the slope invariant V1^2/eps1 is determined even where eps1 rails.
    # First-order rows: the metal ends at its spinodal. Anything the branch
    # assembly appends AFTER a continuity break beyond U* is a different
    # family (the documented collector-artifact islands, e.g. square
    # U/D = 2.8-3.2 with W railed at its box) — truncate there.
    ustar = next((u for tt, u in
                  common.ustar_curve(r["ds"], lattice, m_g, r["gauge"])
                  if abs(tt - t) < 1e-12), None)
    us, ys, dropped, tail = [], [], 0, 0
    cap_us, cap_ys = [], []
    first_break = min(entry["breaks"]) if entry.get("breaks") else None
    for position, index in enumerate(entry["rows"]):
        u_here = float(rows[index]["u_over_d"])
        # cutoff doctrine: the metal branch ends at the first basin flip
        # or the first recorded continuity break, whichever comes first
        # (prefix cut — the classifier flip-flops in the pseudo-family
        # region past the spinodal, so filtering is wrong)
        if rows[index].get("basin") not in (None, "", "metal"):
            tail += len(entry["rows"]) - position
            break
        if first_break is not None and position >= first_break:
            tail += len(entry["rows"]) - position
            break
        if (ustar is not None and position > 0
                and (position - 1) in entry["breaks"]
                and u_here > ustar):
            tail += len(entry["rows"]) - position
            break
        z = common.fnum(rows[index]["quasiparticle_weight_pole"])
        if z is not None and z < Z_TAIL:
            tail += 1
            continue
        params = common.pole_params(r["ds"], index)
        at_cap = compare.eps1_pinned(params, lattice) if satellite \
            else compare.eta_pinned(params)
        if key == "lam":
            eta, w = params["eta"], params["w"]
            val = None if (eta is None or w is None) else math.sqrt(
                eta * eta + 2 * w * w)
        elif key == "v1inv":
            v1, e1 = params["v1"], params["eps1"]
            val = None if (v1 is None or not e1) else v1 * v1 / e1
        else:
            val = params[key]
        if val is not None:
            if at_cap:
                # KEPT, not hidden: a pole resting at its position cap is
                # the solver's declared pure-slope representation — the
                # coordinate is not fitted there, the slope invariant is.
                cap_us.append(float(rows[index]["u_over_d"]))
                cap_ys.append(val)
                dropped += 1
            else:
                us.append(float(rows[index]["u_over_d"]))
                ys.append(val)
        if position in entry["breaks"]:  # do not bridge continuity breaks
            us.append(float("nan"))
            ys.append(float("nan"))
    return us, ys, cap_us, cap_ys, dropped, tail


def _gem_eta(m_g, t, lattice):
    pairs = []
    for row in compare.gem_rows():
        if (row["lattice"] == lattice and row["budget"] == m_g
                and math.isclose(row["t"], t, rel_tol=1e-6, abs_tol=1e-9)
                and row["dir"] == "up" and row["sig_eta"] is not None):
            pairs.append((row["u"], row["sig_eta"]))
    pairs.sort()
    return [u for u, _ in pairs], [e for _, e in pairs]


def _figure(lattice, m_g):
    r = compare.route(lattice, m_g)
    temps = compare.select_temperatures(
        common.branch_temperatures(r["ds"], lattice, m_g, r["gauge"], "metal"))
    if not temps:
        print(f"  (no {lattice} m_g={m_g} '{r['gauge']}' metal branch; skipped)")
        return
    fig, axs = plt.subplots(2, 3, figsize=(7.6, 5.6), sharex=True)
    total_dropped = 0
    total_tail = 0
    gem_handle = None
    for ax, (key, label) in zip(axs.ravel(), PARAMS, strict=True):
        marker_only = key == "eps1"  # sparse: position is box-limited
        for t in temps:
            us, ys, cap_us, cap_ys, dropped, tail = _ghost_series(
                lattice, m_g, t, key)
            total_dropped += dropped
            total_tail += tail
            ax.plot(us, ys, "o" if marker_only else "-o", ms=2.4, lw=1.0,
                    color=fs.shade(fs.FRAMEWORK_COLOR["ghost_dmft"], t, temps))
            if cap_us:
                ax.plot(cap_us, cap_ys, "x", ms=2.6, mew=0.7,
                        color="0.55", zorder=1)
        if marker_only:
            ax.text(0.5, 0.9,
                    "× = pole resting at its position cap: the coordinate is\n"
                    "not fitted there (declared slope representation);\n"
                    "filled = position genuinely determined",
                    transform=ax.transAxes, ha="center", va="top",
                    fontsize=5.8, color="0.45")
        if key == "v1inv":
            ax.text(0.5, 0.9,
                    "position-independent combination —\n"
                    "determined even where $\epsilon_1$ rails",
                    transform=ax.transAxes, ha="center", va="top",
                    fontsize=5.8, color="0.45")
        if key == "eta":
            gu, ge = _gem_eta(m_g, temps[0], lattice)
            if gu:
                ax.plot(gu, ge, "s", ms=3, mfc="none", mew=1.0,
                        color=fs.FRAMEWORK_COLOR["gga_gem"])
                gem_handle = plt.Line2D(
                    [], [], marker="s", ls="none", mfc="none",
                    color=fs.FRAMEWORK_COLOR["gga_gem"], label=r"gGA $\eta$ (cold)")
        ax.set_ylabel(label)
        ax.grid(alpha=0.25, lw=0.4)
    for ax in axs[1]:
        ax.set_xlabel(r"$U/D$")

    ghost_handle = plt.Line2D(
        [], [], marker="o", color=fs.FRAMEWORK_COLOR["ghost_dmft"],
        label="ghost-DMFT (metal)")
    cap_handle = plt.Line2D(
        [], [], marker="x", ls="none", color="0.55",
        label="at position cap (slope repr.)")
    compare.method_key(fig, [], y=0.085,
                       extra=[ghost_handle, cap_handle]
                       + ([gem_handle] if gem_handle else []))
    compare.temperature_key(fig, temps, y=0.028,
                            title=f"ghost-DMFT shade (lighter = colder); "
                                  f"{total_dropped} points AT the cap (kept, ×); "
                                  f"{total_tail // len(PARAMS)} post-collapse rows (Z<{Z_TAIL:g}) excluded")
    compare.gauge_caption(fig, lattice, m_g)

    fig.suptitle(
        rf"{lattice.capitalize()} $M_g={m_g}$: converged pole parameters "
        r"(ghost-DMFT metal)", fontsize=9.3)
    fig.tight_layout(rect=(0, 0.15, 1, 0.95))
    fs.save(fig, f"compare_params_{lattice}_mg{m_g}", compare.outdir(lattice))


def build() -> None:
    for lattice in ("bethe", "square"):
        _figure(lattice, 3)


if __name__ == "__main__":
    build()
