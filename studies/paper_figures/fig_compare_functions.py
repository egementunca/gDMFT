#!/usr/bin/env python3
"""Reconstructed functions from the pole sum — ghost-DMFT vs gGA.

Nothing G/Σ/A is stored; everything is rebuilt from the finite pole set
(the verified atlas math, reused from fig_spectra):
  Σ'(z) = Σ_k W_k²/(z − η_k)          (Hartree U/2 removed)
  Δ(z)  = V0²/z + V1²/(z − ε_g) + V1²/(z + ε_g)
  A(ω)  = −Im G_loc(ω+iδ)/π,  G_loc = Hilbert[ρ](ω − Σ')
Bethe uses the closed-form G; square uses the DOS Hilbert transform.

Columns = representative couplings (metal / coexistence / insulator).
Top row: Im Σ'(iωₙ), Im Δ(iωₙ) on Matsubara, ghost solid vs gGA dashed
(gGA Σ' rebuilt from its stored self-energy poles). Bottom row: A(ω).
"""

from __future__ import annotations

import math

import compare
import fig_spectra as spx
import figstyle as fs
import matplotlib.pyplot as plt
import numpy as np

import common

U_COLUMNS = (2.0, 2.7, 3.2)
T_COLD = 0.001
DELTA = 0.02
CM = {"metal": fs.BRANCH_COLOR["metal"], "insul": fs.BRANCH_COLOR["insul"]}


def _row_at(lattice, kind, u):
    r = compare.route(lattice, 3)
    entry = common.branch(r["ds"], lattice, 3, r["gauge"], T_COLD, kind)
    if entry is None:
        return None
    rows = common.point_rows(r["ds"])
    for index in entry["rows"]:
        if math.isclose(float(rows[index]["u_over_d"]), u, rel_tol=1e-6):
            return index
    return None


def _gloc(lattice, zeta):
    return spx.g_bethe(zeta) if lattice == "bethe" else compare.g_square(zeta)


def _gem_sigma_prime(lattice, u, z):
    """gGA Im Σ' from its stored self-energy poles (Bethe m_g=3, cold)."""
    best = None
    for row in compare.gem_rows():
        if (row["lattice"] == lattice and row["budget"] == 3
                and math.isclose(row["t"], T_COLD, rel_tol=1e-6, abs_tol=1e-9)
                and row["dir"] == "up"
                and math.isclose(row["u"], u, rel_tol=1e-6)
                and row["sig_pos"] and row["sig_wgt"]):
            best = row
            break
    if best is None:
        return None
    out = np.zeros_like(z)
    for pos, wgt in zip(best["sig_pos"], best["sig_wgt"]):
        out = out + wgt / (z - pos)
    return out


def _figure(lattice):
    ds = compare.route(lattice, 3)["ds"]
    fig, axes = plt.subplots(2, len(U_COLUMNS), figsize=(7.6, 4.8),
                             sharex="row")
    wn = (2 * np.arange(0, 28) + 1) * math.pi * T_COLD
    omega = np.linspace(-3.2, 3.2, 900)
    for column, u in enumerate(U_COLUMNS):
        top, bottom = axes[0, column], axes[1, column]
        present = []
        for kind in ("metal", "insul"):
            index = _row_at(lattice, kind, u)
            if index is None:
                continue
            params = common.pole_params(ds, index)
            name = "metal" if kind == "metal" else "insulator"
            present.append(name)
            color = CM[kind]
            z_mats = 1j * wn
            top.plot(wn, spx.sigma_prime(params, z_mats).imag, "o-", ms=2.2,
                     lw=1.0, color=color, label=rf"Im$\,\Sigma'$ {name} (ours)")
            top.plot(wn, spx.delta_fn(params, z_mats).imag, "^:", ms=2.0,
                     lw=0.8, color=color, alpha=0.6,
                     label=rf"Im$\,\Delta$ {name} (ours)")
            zeta = (omega + 1j * DELTA) - spx.sigma_prime(params, omega + 1j * DELTA)
            bottom.plot(omega, -_gloc(lattice, zeta).imag / math.pi, "-", lw=1.1,
                        color=color, label=name)
        # gGA Σ' overlay (metal, from its own poles)
        gem_sig = _gem_sigma_prime(lattice, u, 1j * wn)
        if gem_sig is not None:
            top.plot(wn, gem_sig.imag, "s--", ms=2.2, lw=0.9,
                     color=fs.FRAMEWORK_COLOR["gga_gem"],
                     label=r"Im$\,\Sigma'$ gGA")
        title = f"$U/D={u:g}$" + (f" ({' + '.join(present)})" if present else "")
        top.set_title(title, fontsize=8.5)
        top.grid(alpha=0.25, lw=0.4)
        bottom.grid(alpha=0.25, lw=0.4)
        if column == 0:
            top.set_ylabel(r"Im$\,\Sigma'$, Im$\,\Delta$ $(i\omega_n)$")
            bottom.set_ylabel(r"$A(\omega)$")
        top.set_xlabel(r"$\omega_n/D$")
        bottom.set_xlabel(r"$\omega/D$")
    axes[0, 0].legend(fontsize=5.4, loc="best")
    axes[1, 0].legend(fontsize=6.2, loc="best")
    fig.suptitle(
        rf"{lattice.capitalize()} $M_g=3$: reconstructed $\Sigma'/\Delta$ "
        rf"and $A(\omega)$, ghost-DMFT vs gGA ($T/D={T_COLD:g}$)",
        fontsize=9.3,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.93))
    compare.gauge_caption(fig, lattice, 3)
    fs.save(fig, f"compare_functions_{lattice}_mg3", compare.outdir(lattice))


def build() -> None:
    for lattice in ("bethe", "square"):
        _figure(lattice)


if __name__ == "__main__":
    build()
