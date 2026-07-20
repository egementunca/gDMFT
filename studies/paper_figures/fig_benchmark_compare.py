#!/usr/bin/env python3
"""The benchmark pair (LLK PRB 107 Fig. 2/3 analogues), from registered data.

fig_gga_dmft_compare  — (a) docc (b) E_tot/D (c) E_kin/D (d) Z vs U/D,
                        half-filled Bethe, coldest rows, matched budgets
fig_bathsize_convergence — observables vs bath size at U/D = 2.4

Only the three frameworks the user compares: ghost-DMFT (ours), gem g-RISB,
and DMFT-ED. External reference data (NRG, professor grids, CTQMC) is NOT
drawn — user decision 2026-07-18. Reads the registered
references-benchmarks-v1 merge (its ghost/gem/ED rows). Encoding:
color = framework, line style = bath budget, insulator branches faint,
gem junk filtered by the sum-rule detector (sum R^2 <= 1.1).
"""

from __future__ import annotations

import math

import common
import figstyle as fs
import matplotlib.pyplot as plt

T0 = 0.001


def rows(**filters):
    out = []
    for row in common.compare_rows():
        keep = True
        for key, want in filters.items():
            value = row[key]
            if isinstance(want, float):
                keep = value is not None and math.isclose(value, want)
            else:
                keep = value == want
            if not keep:
                break
        if keep:
            out.append(row)
    return out


def first_per_u(selection):
    seen = {}
    for row in selection:
        seen.setdefault(row["u"], row)
    return [seen[u] for u in sorted(seen)]


def drop_gem_junk(selection):
    return [
        row
        for row in selection
        if row["sumr2"] is None or row["sumr2"] <= 1.1
    ]


def xy(selection, column):
    pts = [(row["u"], row[column]) for row in selection if row[column] is not None]
    return [p[0] for p in pts], [p[1] for p in pts]


def fig_compare():
    fig, axs = plt.subplots(2, 2, figsize=(7.0, 5.6), sharex=True)
    observables = [
        ("docc", r"$\langle n_\uparrow n_\downarrow\rangle$"),
        ("etot", r"$E_{\rm tot}/D$"),
        ("ekin", r"$E_{\rm kin}/D$"),
        ("z", r"$Z$"),
    ]
    for ax, (col, label) in zip(axs.ravel(), observables, strict=True):
        for b in (1, 3):
            met = first_per_u(
                rows(method="ghost_dmft", budget=b, t=T0, branch="metal")
            )
            ax.plot(
                *xy(met, col),
                color=fs.FRAMEWORK_COLOR["ghost_dmft"],
                ls=fs.BUDGET_STYLE[b],
                label=f"{fs.FRAMEWORK_NAME['ghost_dmft']} $M_g$={b}",
            )
            if b == 3:
                ins = first_per_u(
                    rows(method="ghost_dmft", budget=b, t=T0, branch="insulator")
                )
                ax.plot(
                    *xy(ins, col),
                    color=fs.FRAMEWORK_COLOR["ghost_dmft"],
                    ls=fs.BUDGET_STYLE[b],
                    alpha=fs.INSULATOR_ALPHA,
                )
        for b in (1, 3):
            up = drop_gem_junk(rows(method="gga_gem", budget=b, t=T0, branch="up"))
            up = [row for row in up if row["z"] is not None]
            ax.plot(
                *xy(sorted(up, key=lambda r: r["u"]), col),
                color=fs.FRAMEWORK_COLOR["gga_gem"],
                ls=fs.BUDGET_STYLE[b],
                label=f"{fs.FRAMEWORK_NAME['gga_gem']} $B$={b}",
            )
            down = drop_gem_junk(
                rows(method="gga_gem", budget=b, t=T0, branch="down")
            )
            if down:
                ax.plot(
                    *xy(sorted(down, key=lambda r: r["u"]), col),
                    color=fs.FRAMEWORK_COLOR["gga_gem"],
                    ls=fs.BUDGET_STYLE[b],
                    alpha=fs.INSULATOR_ALPHA,
                )
        for b in (1, 3, 5):
            up = sorted(
                rows(method="dmft_ed", budget=b, branch="up"),
                key=lambda r: r["u"],
            )
            ax.plot(
                *xy(up, col),
                color=fs.FRAMEWORK_COLOR["dmft_ed"],
                ls=fs.BUDGET_STYLE[b],
                label=f"{fs.FRAMEWORK_NAME['dmft_ed']} $N_b$={b}",
            )
        ax.set_ylabel(label)
        ax.set_xlim(0.4, 4.05)
        ax.grid(alpha=0.25, lw=0.4)
    for ax in axs[1]:
        ax.set_xlabel(r"$U/D$")
    handles, labels = axs[0, 0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="lower center",
        ncol=3,
        fontsize=7.2,
        bbox_to_anchor=(0.5, -0.005),
    )
    fig.suptitle(
        "Half-filled Bethe lattice, coldest rows "
        r"($T/D=10^{-3}$; DMFT-ED at $T=0$): "
        "matched bath budgets across frameworks",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0.075, 1, 0.97))
    fs.save(fig, "fig_gga_dmft_compare", common.OUT)


def fig_convergence():
    fig, axs = plt.subplots(1, 3, figsize=(7.0, 2.6))
    observables = [
        ("docc", r"$\langle n_\uparrow n_\downarrow\rangle$"),
        ("etot", r"$E_{\rm tot}/D$"),
        ("z", r"$Z$"),
    ]
    U = 2.4
    for ax, (col, label) in zip(axs, observables, strict=True):
        for method, budgets, t_sel in (
            ("ghost_dmft", (1, 3), T0),
            ("gga_gem", (1, 3), T0),
            ("dmft_ed", (1, 3, 5), None),
        ):
            xs, ys = [], []
            for b in budgets:
                sel = [
                    row
                    for row in rows(method=method, budget=b, u=U)
                    if (t_sel is None or math.isclose(row["t"], t_sel))
                    and row["branch"] in ("metal", "up")
                    and row[col] is not None
                ]
                if sel:
                    xs.append(b)
                    ys.append(sel[0][col])
            ax.plot(
                xs,
                ys,
                marker="o",
                ms=5,
                color=fs.FRAMEWORK_COLOR[method],
                label=fs.FRAMEWORK_NAME[method],
            )
        ax.set_xticks([1, 3, 5])
        ax.set_xlabel(r"bath size ($M_g$ / $B$ / $N_b$)")
        ax.set_ylabel(label)
        ax.grid(alpha=0.25, lw=0.4)
    axs[1].legend(fontsize=6.8, loc="best")
    fig.suptitle(
        r"Convergence with bath size at $U/D=2.4$ (metallic), coldest rows",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fs.save(fig, "fig_bathsize_convergence", common.OUT)


def build() -> None:
    fig_compare()
    fig_convergence()


if __name__ == "__main__":
    build()
