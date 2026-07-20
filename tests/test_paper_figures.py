from __future__ import annotations

import sys
from pathlib import Path

from gdmft.data import load_manifest, verify_artifacts

ROOT = Path(__file__).parents[1]
FIGDIR = ROOT / "studies/paper_figures"


def _import_common():
    if str(FIGDIR) not in sys.path:
        sys.path.insert(0, str(FIGDIR))
    import common

    return common


def test_benchmark_reference_dataset_is_registered_and_valid() -> None:
    registry = (ROOT / "data/registry.toml").read_text(encoding="utf-8")
    assert 'id = "references.benchmarks-v1"' in registry
    root = ROOT / "data/datasets/references-benchmarks-v1"
    manifest = load_manifest(root / "manifest.json")
    assert verify_artifacts(manifest, root) == len(manifest["artifacts"])
    checks = manifest["extensions"]["cross_check"]
    assert checks["gem_rows_matched"] > 3000
    assert checks["ghost_rows_matched"] > 2000


def test_endpoint_corridors_match_the_benchmark_notes() -> None:
    common = _import_common()
    # GGA_DMFT_BENCHMARK_20260715.md §5.3 and the square note
    assert common.CORRIDORS["bethe"] == (0.01, 0.015)
    assert common.CORRIDORS["square"] == (0.004, 0.005)


def test_derived_ustar_feeding_the_figures_is_the_published_value() -> None:
    common = _import_common()
    curve = dict(common.ustar_curve("v1", "bethe", 3, "bare"))
    assert abs(curve[0.01] - 2.492) < 5e-3


def test_benchmark_trio_smoke(tmp_path: Path) -> None:
    common = _import_common()
    import fig_benchmark_compare

    original = common.OUT
    common.OUT = tmp_path
    try:
        fig_benchmark_compare.build()
    finally:
        common.OUT = original
    for name in ("fig_gga_dmft_compare", "fig_bathsize_convergence"):
        assert (tmp_path / f"{name}.pdf").stat().st_size > 10_000
