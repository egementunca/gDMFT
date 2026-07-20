"""Shared styling for the paper figures (ported from the old figure set).

Color = framework (Okabe-Ito, colorblind-safe, fixed assignment);
line style = bath budget (1 dashed, 3 solid, 5 dash-dot);
insulator branches at alpha 0.45; branch colors metal blue / insulator red.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
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
    }
)


def save(fig, name: str, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    for ext in ("pdf", "png"):
        fig.savefig(outdir / f"{name}.{ext}", dpi=250, bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {outdir}/{name}.pdf")
