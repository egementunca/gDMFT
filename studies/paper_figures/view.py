#!/usr/bin/env python3
"""Open any paper / comparison figure in an interactive matplotlib window.

Unlike the batch build (which writes PNG/PDF/EPS to disk), this pops a live
window with the matplotlib toolbar — box-zoom, pan, and save — so you can
zoom into, e.g., the transition region where the temperature lines fan out.

Run from studies/paper_figures/ :
    ../../.venv/bin/python view.py                  # list available figures
    ../../.venv/bin/python view.py observables       # match a module by substring
    ../../.venv/bin/python view.py v0_death
    ../../.venv/bin/python view.py compare_params

It rebuilds the figure live (still also writes the files), then shows it. If
only the headless Agg backend is available it says so and how to fix it
(usually `pip install PyQt6`).
"""

from __future__ import annotations

import importlib
import os
import sys

# Must be set BEFORE the figure modules import figstyle, so figstyle leaves
# the backend interactive instead of forcing Agg.
os.environ["GDMFT_FIG_SHOW"] = "1"

# Optional gauge override, e.g.  view.py params --gauge canonical-r-native
for _i, _a in enumerate(sys.argv):
    if _a == "--gauge" and _i + 1 < len(sys.argv):
        os.environ["GDMFT_FIG_GAUGE"] = sys.argv[_i + 1]
    elif _a.startswith("--gauge="):
        os.environ["GDMFT_FIG_GAUGE"] = _a.split("=", 1)[1]

MODULES = [
    # comparison suite
    "fig_compare_observables",
    "fig_compare_residual",
    "fig_compare_convergence",
    "fig_compare_vs_T",
    "fig_compare_params",
    "fig_compare_functions",
    "fig_v0_death",
    # existing paper figures
    "fig_single_site",
    "fig_anatomy",
    "fig_lambda_frame",
    "fig_spectra",
    "fig_benchmark_compare",
]


def _pick_backend() -> str:
    import matplotlib

    for backend in ("MacOSX", "QtAgg", "TkAgg", "GTK4Agg"):
        try:
            matplotlib.use(backend, force=True)
            return backend
        except Exception:
            continue
    return matplotlib.get_backend()


def _list():
    print("available figures (pass any substring):\n")
    for module in MODULES:
        print("   ", module)


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if not args:
        _list()
        return
    query = args[0]
    matches = [m for m in MODULES if query in m]
    if not matches:
        print(f"no figure matches {query!r}.\n")
        _list()
        return
    if len(matches) > 1:
        print(f"{query!r} matches several — be more specific:\n")
        for module in matches:
            print("   ", module)
        return

    backend = _pick_backend()
    module = importlib.import_module(matches[0])
    print(f"building {matches[0]} on backend '{backend}' ...")
    module.build()

    import matplotlib.pyplot as plt

    if plt.get_backend().lower() == "agg":
        print(
            "\nNo interactive GUI backend is available (only Agg), so no "
            "window opened.\nThe files were still written. To get zoom, "
            "install a GUI backend, e.g.:\n    ../../.venv/bin/pip install PyQt6"
        )
        return
    print("\nClose the window(s) to exit.")
    plt.show()


if __name__ == "__main__":
    main()
