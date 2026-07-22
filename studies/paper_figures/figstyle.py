"""Shared styling for the paper figures (ported from the old figure set).

Color = framework (Okabe-Ito, colorblind-safe, fixed assignment);
line style = bath budget (1 dashed, 3 solid, 5 dash-dot);
insulator branches at alpha 0.45; branch colors metal blue / insulator red.
"""

from __future__ import annotations

import os
from pathlib import Path

import matplotlib

# Default to the headless Agg backend for batch figure building. When
# GDMFT_FIG_SHOW is set (by view.py), leave the backend alone so an
# interactive GUI window with zoom/pan can be used instead.
INTERACTIVE = bool(os.environ.get("GDMFT_FIG_SHOW"))
if not INTERACTIVE:
    matplotlib.use("Agg")
import matplotlib.colors as mcolors  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

FRAMEWORK_COLOR = {
    "ghost_dmft": "#0072B2",
    "gga_gem": "#E69F00",
    "dmft_ed": "#D55E00",
    "nrg": "#000000",
    "gga_prof": "#7F7F7F",
    "ctqmc_llk": "#000000",
}
FRAMEWORK_NAME = {
    "ghost_dmft": "ghost-DMFT (ours)",
    "gga_gem": "gGA (TRIQS/gem)",
    "dmft_ed": "DMFT-ED (LLK protocol)",
    "nrg": "NRG",
    "gga_prof": "gGA grid (ref.)",
    "ctqmc_llk": "CTQMC (LLK)",
}
BUDGET_STYLE = {1: (0, (4, 2)), 3: "solid", 5: (0, (5, 1.5, 1, 1.5))}
BRANCH_COLOR = {"metal": "#1f77b4", "insul": "#d62728", "insulator": "#d62728"}
SQUARE_COLOR = "#2ca02c"
INSULATOR_ALPHA = 0.45

plt.rcParams.update(
    {
        "font.size": 9,
        "axes.linewidth": 0.6,
        "lines.linewidth": 1.4,
        "figure.dpi": 150,
        "legend.frameon": False,
        # embed real (Type-42/TrueType) fonts in EPS/PS and PDF so the
        # publication vector files carry selectable text, not outlines
        "ps.fonttype": 42,
        "pdf.fonttype": 42,
    }
)


def shade(color: str, t: float, ts) -> tuple:
    """A light-tint (cold) → dark (warm) shade of a framework color.

    Encodes temperature *within* a fixed method color so several
    temperatures read as distinct lines while color still reads as the
    method. Spans a wide brightness range: coldest ≈ 72% toward white,
    warmest ≈ 32% toward black, linear in log T.
    """
    import math

    lo, hi = min(ts), max(ts)
    f = ((math.log(t) - math.log(lo)) / (math.log(hi) - math.log(lo))
         if hi > lo else 1.0)
    base = mcolors.to_rgb(color)
    light = tuple(c + (1.0 - c) * 0.72 for c in base)   # cold: toward white
    dark = tuple(c * (1.0 - 0.32) for c in base)         # warm: toward black
    return tuple(lo_ + (hi_ - lo_) * f for lo_, hi_ in zip(light, dark))


def save(fig, name: str, outdir: Path) -> None:
    # GDMFT_FIG_NOSAVE: fast preview (GUI/interactive) — keep the figure open
    # but write no files, so clicking through figures doesn't re-render EPS.
    if not os.environ.get("GDMFT_FIG_NOSAVE"):
        outdir.mkdir(parents=True, exist_ok=True)
        for ext in ("pdf", "png", "eps"):
            fig.savefig(outdir / f"{name}.{ext}", dpi=250, bbox_inches="tight")
    if INTERACTIVE:
        print(f"[show] {name}")
    else:
        plt.close(fig)
        print(f"wrote {outdir}/{name}.{{pdf,png,eps}}")
