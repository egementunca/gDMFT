from __future__ import annotations

import csv
import json
import statistics
from collections import Counter
from pathlib import Path

from gdmft.data import load_manifest, verify_artifacts

ROOT = Path(__file__).parents[1]
REF = ROOT / "data/datasets/references-gem-gga-v1"
D08 = ROOT / "data/datasets/single-site-gauge-matrix-v1"
D09 = ROOT / "data/datasets/single-site-scan-matrix-v2"

EXPECTED_CELL_ROWS = {
    ("bethe", "1"): 1768,
    ("bethe", "3"): 1768,
    ("square", "1"): 800,
    ("square", "3"): 800,
}


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_reference_manifest_registry_and_artifacts_are_valid() -> None:
    manifest = load_manifest(REF / "manifest.json")
    assert verify_artifacts(manifest, REF) == len(manifest["artifacts"])
    assert manifest["dataset_kind"] == "external_reference"
    assert {source["id"] for source in manifest["external_sources"]} >= {"gem"}

    registry = (ROOT / "data/registry.toml").read_text(encoding="utf-8")
    assert 'id = "references.gem-gga-v1"' in registry
    assert "data/datasets/references-gem-gga-v1/manifest.json" in registry


def test_reference_row_counts_and_unique_key() -> None:
    rows = _rows(REF / "points.csv")
    assert len(rows) == 5136
    assert Counter(
        (row["lattice"], row["bath_budget"]) for row in rows
    ) == Counter(EXPECTED_CELL_ROWS)
    keys = {
        (
            row["lattice"],
            row["bath_budget"],
            row["t_over_d"],
            row["u_over_d"],
            row["direction"],
        )
        for row in rows
    }
    assert len(keys) == 5136
    assert {row["schema_version"] for row in rows} == {"gdmft.reference.v1"}
    assert {row["method"] for row in rows} == {"gem-gga"}


def test_reference_covers_every_scan_matrix_key_both_directions() -> None:
    scan_keys: dict[str, set[tuple[float, float]]] = {"bethe": set(), "square": set()}
    with (D09 / "points.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            scan_keys[row["lattice"]].add(
                (float(row["u_over_d"]), float(row["t_over_d"]))
            )
    # Revision 0.2.0 canonical grids (fill campaign merged).
    assert len(scan_keys["bethe"]) == 1887
    assert len(scan_keys["square"]) == 1791

    gem_keys: dict[tuple[str, str, str], set[tuple[float, float]]] = {}
    for row in _rows(REF / "points.csv"):
        gem_keys.setdefault(
            (row["lattice"], row["bath_budget"], row["direction"]), set()
        ).add((float(row["u_over_d"]), float(row["t_over_d"])))
    # 0.2.0: the scan grid grew (fill campaign); gem's own grids are the
    # pre-fill anchor set and must be a strict SUBSET until the gem fill
    # lands. Every gem key must exist in the scan grid; the deficit is the
    # reported fill-in-progress coverage, not drift.
    for lattice in ("bethe", "square"):
        for budget in ("1", "3"):
            for direction in ("up", "down"):
                keys = gem_keys[(lattice, budget, direction)]
                assert keys <= scan_keys[lattice]
                assert len(keys) >= (884 if lattice == "bethe" else 360)


def test_reference_crash_stall_and_structure_semantics() -> None:
    rows = _rows(REF / "points.csv")
    crashed = [row for row in rows if row["crashed"] == "true"]
    assert len(crashed) == 29
    for row in crashed:
        assert row["converged"] == "false"
        assert row["iterations"] == "-1"
        assert row["quasiparticle_weight_slope"] == ""
        assert row["double_occupancy"] == ""
        assert row["total_energy_over_d"] == ""

    structure_counts = Counter(
        (row["lattice"], row["bath_budget"])
        for row in rows
        if row["self_energy_pole_positions"]
    )
    assert structure_counts == {("bethe", "3"): 1029, ("square", "3"): 797}
    for row in rows:
        if row["bath_budget"] == "1":
            assert row["self_energy_pole_positions"] == ""
            assert row["self_energy_pole_weights"] == ""
        elif row["self_energy_pole_positions"]:
            assert len(row["self_energy_pole_positions"].split(";")) == 2
            assert len(row["self_energy_pole_weights"].split(";")) == 2


def _gem_cold_up_metal(
    rows: list[dict[str, str]], lattice: str, budget: str
) -> dict[float, dict[str, str]]:
    table: dict[float, dict[str, str]] = {}
    for row in rows:
        if (
            row["lattice"] == lattice
            and row["bath_budget"] == budget
            and row["direction"] == "up"
            and float(row["t_over_d"]) == 0.001
            and row["converged"] == "true"
            and row["sum_r_squared"]
            and float(row["sum_r_squared"]) <= 1.1
        ):
            table[float(row["u_over_d"])] = row
    return table


def test_reference_agrees_with_registered_datasets_on_cold_rows() -> None:
    gem_rows = _rows(REF / "points.csv")

    # bethe B=3 must match the v1 gauge-matrix BARE rows (the scan-matrix v2
    # bethe m_g=3 cell is R-native continuation, a different population).
    ours: dict[float, float] = {}
    with (D08 / "points.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if (
                row["lattice"] == "bethe"
                and row["m_g"] == "3"
                and row["gauge"] == "bare"
                and row["solution_family"] in {"metal-up", "metal-down"}
                and row["source_converged"] == "true"
                and row["double_occupancy"]
                and float(row["t_over_d"] or "nan") == 0.001
            ):
                ours[float(row["u_over_d"])] = float(row["double_occupancy"])
    gem = _gem_cold_up_metal(gem_rows, "bethe", "3")
    shared = sorted(set(ours) & set(gem))
    assert len(shared) >= 20
    docc_median = statistics.median(
        abs(ours[u] - float(gem[u]["double_occupancy"])) for u in shared
    )
    assert docc_median < 5e-3

    # square B=3 must match the v2 scan-matrix bare rows, docc and E_tot.
    ours_sq: dict[float, tuple[float, float]] = {}
    with (D09 / "points.csv").open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if (
                row["lattice"] == "square"
                and row["m_g"] == "3"
                and row["gauge"] == "bare"
                and row["solution_family"] in {"metal-up", "metal-down"}
                and row["source_category"] == "converged_branch"
                and row["t_over_d"] == "0.001"
            ):
                ours_sq[float(row["u_over_d"])] = (
                    float(row["double_occupancy"]),
                    float(row["total_energy_over_d"]),
                )
    gem_sq = _gem_cold_up_metal(gem_rows, "square", "3")
    shared_sq = sorted(set(ours_sq) & set(gem_sq))
    assert len(shared_sq) >= 20
    assert (
        statistics.median(
            abs(ours_sq[u][0] - float(gem_sq[u]["double_occupancy"]))
            for u in shared_sq
        )
        < 5e-3
    )
    assert (
        statistics.median(
            abs(ours_sq[u][1] - float(gem_sq[u]["total_energy_over_d"]))
            for u in shared_sq
        )
        < 5e-3
    )


def test_reference_import_report_is_honest() -> None:
    report = json.loads(
        (REF / "provenance/import_report.json").read_text(encoding="utf-8")
    )
    assert report["counts"]["total_rows"] == 5136
    assert report["counts"]["crashed_rows"] == 29
    assert set(report["convention_cross_check"]) == {
        "bethe_b1",
        "bethe_b3",
        "square_b1",
        "square_b3",
    }
    assert report["convention_cross_check"]["bethe_b3"]["our_source"] == "v1"

    source_files = _rows(REF / "provenance/source_files.csv")
    assert len(source_files) == 54
    archived_script = (REF / "provenance/gem_scan.py").read_text(
        encoding="utf-8"
    )
    assert "/Users/" not in archived_script
