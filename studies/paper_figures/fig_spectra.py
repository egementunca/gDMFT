#!/usr/bin/env python3
"""F2 + F3 — Σ(iωₙ)/Δ(iωₙ) on both branches and the lattice A(ω) (new).

Named in the paper plan (R2: "Σ(iω)/Δ(iω) both branches; lattice G/A(ω)")
but never scripted. Reconstruction from the archived pole parameters
(v1 bethe m_g=3 bare, coldest T), the same verified math as the atlas:

  Σ'(z) = Σ_k W_k²/(z − η_k)   (Hartree U/2 removed)
  Δ(z)  = V0²/z + V1²/(z − ε_g) + V1²/(z + ε_g)
  G_loc = Hilbert[ρ](z − Σ'(z)), Bethe closed form
  A(ω)  = −Im G_loc(ω + iδ)/π

Columns: three representative couplings — metallic, coexistence window
(both branches), insulating. Top row: Im Σ'(iωₙ) and Im Δ(iωₙ);
bottom row: A(ω) with the A(0) = 2/πD pinning line.
"""

from __future__ import annotations

import math

import common
import figstyle as fs
import matplotlib.pyplot as plt
import numpy as np

T_COLD = 0.001
DELTA = 0.02
U_COLUMNS = (2.0, 2.7, 3.2)  # metal / coexistence / insulator
CM = {"metal": fs.BRANCH_COLOR["metal"], "insul": fs.BRANCH_COLOR["insul"]}


def row_at(kind, u):
    entry = common.branch("v1", "bethe", 3, "bare", T_COLD, kind)
    if entry is None:
        return None
    rows = common.point_rows("v1")
    for index in entry["rows"]:
        if math.isclose(float(rows[index]["u_over_d"]), u):
            return index
    return None


def sigma_prime(params, z):
    eta, w = params["eta"], params["w"]
    if eta is None or w is None:
        return np.zeros_like(z)
    return w**2 / (z - eta) + w**2 / (z + eta)


def delta_fn(params, z):
    out = np.zeros_like(z)
    if params["v0"] is not None:
        out = out + params["v0"] ** 2 / z
    if params["v1"] is not None and params["eps1"] is not None:
        out = out + params["v1"] ** 2 / (z - params["eps1"])
        out = out + params["v1"] ** 2 / (z + params["eps1"])
    return out


def g_bethe(zeta):
    """G(ζ) = 2(ζ − s√(ζ²−1)) with the branch giving Im G ≤ 0."""
    root = np.sqrt(zeta * zeta - 1.0 + 0j)
    g1 = 2.0 * (zeta - root)
    g2 = 2.0 * (zeta + root)
    return np.where(g1.imag <= 0, g1, g2)


def build() -> None:
    fig, axes = plt.subplots(2, len(U_COLUMNS), figsize=(7.4, 4.6),
                             sharex="row")
    wn = (2 * np.arange(0, 28) + 1) * math.pi * T_COLD
    omega = np.linspace(-3.2, 3.2, 900)

    for column, u in enumerate(U_COLUMNS):
        top, bottom = axes[0, column], axes[1, column]
        present = []
        for kind in ("metal", "insul"):
            index = row_at(kind, u)
            if index is None:
                continue
            params = common.pole_params("v1", index)
            present.append("metal" if kind == "metal" else "insulator")
            color = CM[kind]
            name = "metal" if kind == "metal" else "insulator"

            z_mats = 1j * wn
            sig = sigma_prime(params, z_mats)
            dlt = delta_fn(params, z_mats)
            top.plot(wn, sig.imag, "o-", ms=2.4, lw=1.0, color=color,
                     label=rf"Im$\,\Sigma'$ {name}")
            top.plot(wn, dlt.imag, "s--", ms=2.2, lw=0.9, color=color,
                     alpha=0.55, label=rf"Im$\,\Delta$ {name}")

            z_real = omega + 1j * DELTA
            zeta = z_real - sigma_prime(params, z_real)
            g = g_bethe(zeta)
            bottom.plot(omega, -g.imag / math.pi, "-", lw=1.1, color=color,
                        label=name)
        top.set_title(f"$U/D={u:g}$ ({' + '.join(present)})", fontsize=8.5)
        top.grid(alpha=0.25, lw=0.4)
        bottom.grid(alpha=0.25, lw=0.4)
        bottom.axhline(2 / math.pi, color="0.6", lw=0.7, ls=":")
        if column == 0:
            top.set_ylabel(r"Im$\,\Sigma'(i\omega_n)$, Im$\,\Delta(i\omega_n)$")
            bottom.set_ylabel(r"$A(\omega)$")
            bottom.annotate(r"$A(0)=2/\pi D$", xy=(-3.0, 2 / math.pi + 0.02),
                            fontsize=6.5, color="0.4")
        top.set_xlabel(r"$\omega_n/D$")
        bottom.set_xlabel(r"$\omega/D$")
    axes[0, 0].legend(fontsize=5.8, frameon=False)
    axes[1, 0].legend(fontsize=6.5, frameon=False)
    fig.suptitle(
        r"Matsubara $\Sigma'/\Delta$ and lattice $A(\omega)$ across the "
        rf"transition (Bethe $M_g{{=}}3$, $T/D={T_COLD:g}$, $\delta={DELTA:g}$)",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fs.save(fig, "fig_spectra", common.OUT)


if __name__ == "__main__":
    build()
