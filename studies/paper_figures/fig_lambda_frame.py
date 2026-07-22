#!/usr/bin/env python3
"""F6 — the gateway eigenstructure (draft Eqs. 26–29), from registered data.

 (a) the d–h eigenvalue ladder −Λ < −η < 0 < +η < +Λ vs U/D (Bethe coldest
     T, both branches; Λ = sqrt(η² + 2W²) from the archived pole
     parameters).
 (b) Λ(U) on both branches vs the deep-Mott U/2 asymptote; inset:
     U/2 − Λ on the insulating branch (log).
 (c) the inner gateway eigenvalue λ₋ of the full 6×6 PH gateway matrix
     (exact eigensolve from V0, V1, ε_g, W, η) vs the leading expansion
     V0·η/(√2 W), metal branch approaching U*; the insulating branch has
     V0 → 0 so λ₋ is a numerical zero (stated, not plotted). The Vieta
     determinant identity λ₁λ₂λ₃ = V0·ε_g·η is checked in-script.
 (d) identity residuals on every converged v1 bethe m_g=3 point:
     canonical-map norm/closure/roundtrip errors, and |Z_from_R − Z_pole|
     (the |R̃₀|² = Z zero-mode identity) where recorded.

Adaptation note: the old panel (d) plotted the unregistered r3 eigen-frame
residuals; the registered equivalents shown here are the same class of
machine-precision identity checks carried by the point table itself.
"""

from __future__ import annotations

import math

import common
import figstyle as fs
import matplotlib.pyplot as plt
import numpy as np

CM = {"metal": fs.BRANCH_COLOR["metal"], "insul": fs.BRANCH_COLOR["insul"]}
T_COLD = 0.001


def lam_of(params):
    if params["eta"] is None or params["w"] is None:
        return None
    return math.sqrt(params["eta"] ** 2 + 2 * params["w"] ** 2)


def branch_lam_eta(kind):
    def lam(row, index):
        value = lam_of(common.pole_params("v1", index))
        return float("nan") if value is None else value

    def eta(row, index):
        value = common.pole_params("v1", index)["eta"]
        return float("nan") if value is None else value

    u1, lams = common.branch_series("v1", "bethe", 3, "bare", T_COLD, kind, lam)
    u2, etas = common.branch_series("v1", "bethe", 3, "bare", T_COLD, kind, eta)
    return u1, lams, u2, etas


def gateway_lam_minus(v0, v1, eps_g, w, eta):
    """Inner positive eigenvalue of the full PH gateway matrix + Vieta
    product of the three positive eigenvalues."""
    H = np.zeros((6, 6))
    H[1, 1], H[2, 2] = -eta, eta
    H[0, 1] = H[1, 0] = w
    H[0, 2] = H[2, 0] = w
    H[0, 3] = H[3, 0] = v0
    H[4, 4], H[5, 5] = eps_g, -eps_g
    H[0, 4] = H[4, 0] = v1
    H[0, 5] = H[5, 0] = v1
    lam = np.linalg.eigvalsh(H)
    pos = np.sort(lam[lam > 0])
    return pos[0], float(np.prod(pos))


def build() -> None:
    fig, axes = plt.subplots(2, 2, figsize=(7.1, 5.4))
    (ax, bx), (cx, dx) = axes

    # ---------------- (a) the ladder ----------------
    for kind in ("metal", "insul"):
        u1, lams, u2, etas = branch_lam_eta(kind)
        color = CM[kind]
        name = "metal" if kind == "metal" else "insulator"
        ax.plot(u1, lams, "-", lw=1.3, color=color,
                label=f"$\\pm\\Lambda$ {name}")
        ax.plot(u1, [-v for v in lams], "-", lw=1.3, color=color)
        ax.plot(u2, etas, "--", lw=0.9, color=color,
                label=f"$\\pm\\eta$ {name}")
        ax.plot(u2, [-v for v in etas], "--", lw=0.9, color=color)
    ax.axhline(0.0, color="0.35", lw=0.8)
    ax.annotate(r"$\lambda_0\equiv 0$ (zero mode, $|\tilde R_0|^2=Z$)",
                xy=(0.52, 0.075), fontsize=6.5, color="0.35")
    ax.annotate(r"insulator: $\eta\to 0$ ($\omega{=}0$ pole)",
                xy=(2.35, -0.17), fontsize=6, color=CM["insul"])
    ax.set_xlabel(r"$U/D$")
    ax.set_ylabel(r"$\lambda/D,\ \eta/D$")
    ax.set_title("(a) gateway $d$–$h$ ladder (Bethe, $T/D=10^{-3}$)",
                 fontsize=9, loc="left")
    ax.legend(fontsize=6, frameon=False, ncol=2, loc="lower left")

    # ---------------- (b) Lambda -> U/2 ----------------
    for kind in ("metal", "insul"):
        u1, lams, _, _ = branch_lam_eta(kind)
        bx.plot(u1, lams, "-", lw=1.3, color=CM[kind],
                label="metal" if kind == "metal" else "insulator")
    ug = np.linspace(0.4, 3.3, 10)
    bx.plot(ug, ug / 2, "k:", lw=1.0, label=r"$U/2$ (atomic)")
    bx.set_xlabel(r"$U/D$")
    bx.set_ylabel(r"$\Lambda/D$")
    bx.set_title(r"(b) $\Lambda=\sqrt{\eta^2+\Sigma W^2}$ vs the deep-Mott"
                 r" $U/2$", fontsize=9, loc="left")
    bx.legend(fontsize=6.5, frameon=False, loc="upper left")
    inset = bx.inset_axes([0.60, 0.12, 0.36, 0.38])
    u1, lams, _, _ = branch_lam_eta("insul")
    gap = [
        u / 2 - lam if not math.isnan(lam) else float("nan")
        for u, lam in zip(u1, lams, strict=True)
    ]
    inset.plot(u1, gap, "-", lw=1.0, color=CM["insul"])
    inset.set_yscale("log")
    inset.set_xlabel(r"$U/D$", fontsize=6)
    inset.set_ylabel(r"$U/2-\Lambda$", fontsize=6)
    inset.tick_params(labelsize=5.5)

    # ---------------- (c) lambda_- vs the expansion ----------------
    rows = common.point_rows("v1")
    entry = common.branch("v1", "bethe", 3, "bare", T_COLD, "metal")
    vieta_dev, n_vieta = 0.0, 0
    u_vals, lam_exact, lam_approx = [], [], []
    for index in entry["rows"] if entry else []:
        row = rows[index]
        u = float(row["u_over_d"])
        if u < 2.2:
            continue
        p = common.pole_params("v1", index)
        if any(p[k] is None for k in ("v0", "v1", "eps1", "w", "eta")):
            continue
        lam_minus, product = gateway_lam_minus(
            p["v0"], p["v1"], p["eps1"], p["w"], p["eta"]
        )
        approx = p["v0"] * p["eta"] / (math.sqrt(2.0) * p["w"])
        if approx > 1e-11:
            reference = p["v0"] * p["eps1"] * p["eta"]
            vieta_dev = max(vieta_dev, abs(product - reference) / reference)
            n_vieta += 1
            u_vals.append(u)
            lam_exact.append(lam_minus)
            lam_approx.append(approx)
    cx.plot(u_vals, lam_exact, "o", ms=3.5, mfc="none", color=CM["metal"],
            label="exact, metal")
    cx.plot(u_vals, lam_approx, "-", lw=1.0, color=CM["metal"],
            label=r"$V_0\eta/(\sqrt{2}\,W)$, metal")
    ustar = common.ustar_curve("v1", "bethe", 3, "bare")
    us = next((u for t, u in ustar if abs(t - T_COLD) < 1e-12), None)
    if us:
        cx.axvline(us, color="0.55", lw=0.8, ls=":")
        cx.annotate(r"$U^{*}$", xy=(us + 0.01, 0.2), fontsize=8, color="0.4")
    cx.annotate("insulator branch: $V_0\\to 0$,\n$\\lambda_-=0$ at machine "
                "precision\n(the $\\omega{=}0$ Mott pole)",
                xy=(0.97, 0.06), xycoords="axes fraction", ha="right",
                va="bottom", fontsize=6, color=CM["insul"])
    cx.set_yscale("log")
    cx.set_ylim(8e-4, 3e-1)
    cx.set_xlabel(r"$U/D$")
    cx.set_ylabel(r"$\lambda_-/D$")
    cx.set_title(r"(c) inner gateway eigenvalue: exact vs expansion",
                 fontsize=9, loc="left")
    cx.legend(fontsize=6, frameon=False, loc="lower left")
    print(f"Vieta product identity on {n_vieta} resolvable points: "
          f"max rel deviation {vieta_dev:.2e}")

    # ---------------- (d) identity residuals: worst case per U ----------
    # Not a point cloud (thousands of overlapping dots): for each identity
    # take the WORST residual over all converged points at each U. Four clean
    # envelopes that all sit near machine precision — the actual message.
    floor = 1e-18
    series = {
        "norm_error": ("#7f7f7f", "norm error"),
        "closure_error": ("#2ca02c", "closure error"),
        "roundtrip_error": ("#9467bd", "roundtrip error"),
    }
    worst: dict[str, dict[float, float]] = {key: {} for key in series}
    zr_worst: dict[float, float] = {}
    for row in rows:
        if (
            row["lattice"] != "bethe"
            or row["m_g"] != "3"
            or row["source_converged"] != "true"
        ):
            continue
        u = float(row["u_over_d"])
        for key in series:
            value = common.fnum(row[key])
            if value is not None:
                worst[key][u] = max(worst[key].get(u, 0.0), abs(value))
        z_pole = common.fnum(row["quasiparticle_weight_pole"])
        z_from_r = common.fnum(row["quasiparticle_weight_from_r"])
        if z_pole is not None and z_from_r is not None:
            zr_worst[u] = max(zr_worst.get(u, 0.0), abs(z_from_r - z_pole))

    def envelope(mapping):
        us = sorted(mapping)
        return us, [mapping[u] + floor for u in us]

    for key, (color, label) in series.items():
        us, ys = envelope(worst[key])
        dx.plot(us, ys, "-", lw=1.1, color=color, label=label)
    us, ys = envelope(zr_worst)
    dx.plot(us, ys, "-", lw=1.1, color="#e377c2",
            label=r"$|\,|\tilde R_0|^2 - Z\,|$")
    dx.axhline(1e-8, color="0.7", lw=0.7, ls=":")
    dx.annotate(r"$10^{-8}$", xy=(0.55, 1.4e-8), fontsize=6, color="0.5")
    dx.set_yscale("log")
    dx.set_xlabel(r"$U/D$")
    dx.set_ylabel("worst identity residual")
    dx.set_title("(d) canonical-map identities (worst case per $U$)",
                 fontsize=9, loc="left")
    dx.legend(fontsize=6, frameon=False, loc="upper right")

    fig.tight_layout()
    fs.save(fig, "fig_lambda_frame", common.OUT)


if __name__ == "__main__":
    build()
