#!/usr/bin/env python3
"""Build every cross-method comparison figure into runs/figures/comparison/.

ghost-DMFT (ours) vs gGA (gem) vs DMFT-ED, split by lattice and M_g, with
temperature as separate lines. Output as PNG + PDF + EPS. Run from this
directory:  ../../.venv/bin/python make_comparison.py
"""

from __future__ import annotations

import os
import sys
import time

# Honour --gauge / GDMFT_FIG_GAUGE BEFORE importing the figure modules (which
# import compare, which reads the gauge at import time). Default: the catalog
# primary-physics route (bare).
for _i, _a in enumerate(sys.argv):
    if _a == "--gauge" and _i + 1 < len(sys.argv):
        os.environ["GDMFT_FIG_GAUGE"] = sys.argv[_i + 1]
    elif _a.startswith("--gauge="):
        os.environ["GDMFT_FIG_GAUGE"] = _a.split("=", 1)[1]

import fig_compare_convergence
import fig_compare_functions
import fig_compare_observables
import fig_compare_params
import fig_compare_residual
import fig_compare_vs_T
import fig_v0_death


def main() -> None:
    start = time.time()
    print(f"preferred gauge: {os.environ.get('GDMFT_FIG_GAUGE') or 'bare (policy default)'}")
    for module in (
        fig_compare_observables,
        fig_compare_residual,
        fig_compare_convergence,
        fig_compare_vs_T,
        fig_compare_params,
        fig_compare_functions,
        fig_v0_death,
    ):
        print(f"== {module.__name__} ==")
        module.build()
    print(f"all comparison figures built in {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
