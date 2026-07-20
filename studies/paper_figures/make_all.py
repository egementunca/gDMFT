#!/usr/bin/env python3
"""Build every paper figure into runs/figures/ (pdf + png each)."""

from __future__ import annotations

import time

import fig_anatomy
import fig_benchmark_compare
import fig_lambda_frame
import fig_single_site
import fig_spectra


def main() -> None:
    start = time.time()
    fig_benchmark_compare.build()
    fig_single_site.build()
    fig_anatomy.build()
    fig_lambda_frame.build()
    fig_spectra.build()
    print(f"all figures built in {time.time() - start:.0f}s")


if __name__ == "__main__":
    main()
