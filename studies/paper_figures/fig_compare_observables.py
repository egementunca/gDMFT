#!/usr/bin/env python3
"""Cross-method observables vs U/D, temperature ladder — one figure per
(lattice, M_g).

2x2 panels: double occupancy, Z, E_tot/D, E_kin/D. Each panel overlays
ghost-DMFT (ours) and gGA (gem) at several temperatures (color = method,
lighter shade = colder, markers+lines), with DMFT-ED drawn as T=0 marker
anchors on Bethe. docc reads "the same" across methods; Z is the
discriminating "not quite the same" panel (the prof's R(Z)).

Bethe = ghost + gGA + DMFT-ED (compare_all.csv). Square = ghost (v2) vs
gGA (gem scan) only; no DMFT-ED there.
"""

from __future__ import annotations

import common
import compare
import figstyle as fs
import matplotlib.pyplot as plt

OBS = ["docc", "z", "etot", "ekin"]


def _panel(ax, lattice, m_g, obs, temps):
    for t in temps:
        us, ys = compare.ghost_metal_series(lattice, m_g, t, obs)
        ax.plot(
            us, ys, "-", marker=compare.METHOD_MARKER["ghost_dmft"], ms=2.6,
            lw=1.1, color=fs.shade(fs.FRAMEWORK_COLOR["ghost_dmft"], t, temps),
        )
        gus, gys = compare.gem_metal_series(lattice, m_g, t, obs)
        ax.plot(
            gus, gys, "-", marker=compare.METHOD_MARKER["gga_gem"], ms=2.4,
            lw=1.0, color=fs.shade(fs.FRAMEWORK_COLOR["gga_gem"], t, temps),
        )
    if lattice == "bethe":
        eus, eys = compare.ed_series(m_g, obs)
        ax.plot(
            eus, eys, compare.METHOD_MARKER["dmft_ed"], ms=3.4,
            color=fs.FRAMEWORK_COLOR["dmft_ed"], mfc="none", mew=1.0,
        )
    ax.set_ylabel(compare.OBS_LABEL[obs])
    ax.grid(alpha=0.25, lw=0.4)


def _figure(lattice, m_g):
    if lattice == "bethe":
        temps = compare.select_temperatures(compare.bethe_temperatures(m_g))
    else:
        temps = compare.select_temperatures(compare.square_temperatures(m_g))
    if not temps:
        print(f"  (no temperatures for {lattice} m_g={m_g}; skipped)")
        return

    fig, axs = plt.subplots(2, 2, figsize=(7.2, 5.6), sharex=True)
    for ax, obs in zip(axs.ravel(), OBS, strict=True):
        _panel(ax, lattice, m_g, obs, temps)
    for ax in axs[1]:
        ax.set_xlabel(r"$U/D$")

    # Shared, in-canvas keys (show in the interactive viewer too, not only in
    # tight-bbox saves): method = color/marker; temperature = light→dark shade.
    methods = (["ghost_dmft", "gga_gem"]
               + (["dmft_ed"] if lattice == "bethe" else []))
    compare.method_key(fig, methods, y=0.075)
    compare.temperature_key(
        fig, temps, y=0.012,
        title="temperature shade of each method (lighter = colder)")
    if lattice == "bethe":
        compare.benchmark_note(fig)
    else:
        compare.gauge_caption(fig, lattice, m_g)

    ed_note = "; DMFT-ED at $T=0$" if lattice == "bethe" else " (no DMFT-ED)"
    fig.suptitle(
        rf"{lattice.capitalize()} lattice, $M_g={m_g}$: observables vs $U/D$"
        rf" across temperature{ed_note}",
        fontsize=9.5,
    )
    fig.tight_layout(rect=(0, 0.17, 1, 0.955))
    fs.save(fig, f"compare_observables_{lattice}_mg{m_g}", compare.outdir(lattice))


def build() -> None:
    for lattice in ("bethe", "square"):
        for m_g in (1, 3):
            _figure(lattice, m_g)


if __name__ == "__main__":
    build()
