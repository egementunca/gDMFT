#!/usr/bin/env python3
"""A tiny clickable figure browser — no tkinter (the uv Python's Tk is broken).

The control panel is itself a matplotlib window (Button + RadioButtons
widgets), so it is backend-agnostic: it runs on whatever interactive backend
is available. Qt (PyQt6) is preferred and reliable with uv-managed Pythons.

Pick a gauge on the left, click a figure button — it builds live with that
gauge and opens in its own window with the zoom/pan toolbar. No files are
written in preview mode (use make_comparison.py to save).

Run from studies/paper_figures/ :
    ../../.venv/bin/python gui.py

If it reports no GUI backend:  cd ../.. && uv pip install PyQt6
"""

from __future__ import annotations

import importlib
import os
import sys

os.environ["GDMFT_FIG_SHOW"] = "1"      # keep figures open after build()
os.environ["GDMFT_FIG_NOSAVE"] = "1"    # preview only: write nothing

import matplotlib  # noqa: E402


def _pick_backend():
    for binding in ("PyQt6", "PySide6", "PyQt5", "PySide2"):
        try:
            __import__(binding)
            matplotlib.use("QtAgg", force=True)
            return "QtAgg"
        except Exception:
            continue
    for backend in ("TkAgg", "MacOSX"):
        try:
            matplotlib.use(backend, force=True)
            # force the real import so a broken Tk fails here, not later
            import matplotlib.pyplot as _plt  # noqa: F401
            _plt.figure()
            _plt.close("all")
            return backend
        except Exception:
            continue
    return None


BACKEND = _pick_backend()
if BACKEND is None:
    sys.exit(
        "No interactive GUI backend is available.\n"
        "Install Qt into the venv:\n"
        "    cd ../.. && uv pip install PyQt6\n"
        "then re-run:  ../../.venv/bin/python gui.py"
    )

import compare  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.widgets import Button, RadioButtons  # noqa: E402

FIGURES = {
    "Observables (docc / Z / E)": "fig_compare_observables",
    "Agreement w/ DMFT-ED": "fig_compare_residual",
    "Convergence in bath size": "fig_compare_convergence",
    "Observables vs temperature": "fig_compare_vs_T",
    "Converged pole parameters": "fig_compare_params",
    "Functions  Σ / Δ / A(ω)": "fig_compare_functions",
    "V0 death": "fig_v0_death",
    "paper: single-site story": "fig_single_site",
    "paper: bath anatomy": "fig_anatomy",
    "paper: gateway eigenstructure": "fig_lambda_frame",
    "paper: spectra": "fig_spectra",
    "paper: benchmark compare": "fig_benchmark_compare",
}
GAUGES = {
    "bare (default)": None,
    "canonical-r-native": "canonical-r-native",
    "canonical-r-reoptimized": "canonical-r-reoptimized",
    "canonical-r-converted": "canonical-r-converted",
}


def main():
    control = plt.figure("gDMFT figures", figsize=(4.7, 8.8))
    control_num = control.number
    control.text(0.5, 0.975, "gDMFT figure browser", ha="center",
                 fontsize=13, fontweight="bold")
    control.text(0.5, 0.952, "pick a gauge, then click a figure",
                 ha="center", fontsize=8, color="0.4")

    rax = control.add_axes([0.10, 0.79, 0.80, 0.135])
    rax.set_title("gauge", fontsize=9, loc="left")
    radio = RadioButtons(rax, list(GAUGES), activecolor="#0072B2")

    widgets = [radio]  # keep references alive

    def make_cb(module_name):
        def _cb(_event):
            compare.GAUGE = GAUGES[radio.value_selected]
            for num in list(plt.get_fignums()):
                if num != control_num:
                    plt.close(num)
            try:
                module = importlib.import_module(module_name)
                module.build()
            except Exception as exc:  # noqa: BLE001
                print(f"[gui] {module_name} failed: {exc}")
                return
            for num in plt.get_fignums():
                if num != control_num:
                    plt.figure(num).show()
        return _cb

    labels = list(FIGURES)
    top, height, gap = 0.735, 0.046, 0.0075
    for i, label in enumerate(labels):
        bottom = top - i * (height + gap) - height
        bax = control.add_axes([0.08, bottom, 0.84, height])
        button = Button(bax, label, color="#eef2f6", hovercolor="#d6e4f0")
        button.label.set_fontsize(8.5)
        button.on_clicked(make_cb(FIGURES[label]))
        widgets.append(button)

    control.text(0.5, 0.030,
                 "gauge changes: params · functions · V0 · square observables",
                 ha="center", fontsize=7.5, color="#0072B2")
    control.text(0.5, 0.014,
                 "(Bethe scalar figures use the bare-route benchmark → gauge N/A)",
                 ha="center", fontsize=6.8, color="0.5")
    control.text(0.5, 0.002, f"backend: {BACKEND}", ha="center",
                 fontsize=6.5, color="0.6")
    control._gui_widgets = widgets  # prevent GC
    plt.show()


if __name__ == "__main__":
    main()
