from __future__ import annotations

import csv
import gzip
import hashlib
import json
import tarfile
from collections import Counter
from pathlib import Path

from gdmft.data import load_manifest, validate_point_table, verify_artifacts

ROOT = Path(__file__).parents[1]
D08 = ROOT / "data/datasets/single-site-gauge-matrix-v1"
D09 = ROOT / "data/datasets/single-site-scan-matrix-v2"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_single_site_manifests_and_artifacts_are_valid() -> None:
    for root in (D08, D09):
        manifest = load_manifest(root / "manifest.json")
        assert verify_artifacts(manifest, root) == len(manifest["artifacts"])


def test_native_point_tables_have_expected_dimensions() -> None:
    d08 = validate_point_table(D08 / "points.csv", expected_rows=20228)
    d09 = validate_point_table(D09 / "points.csv", expected_rows=61294)
    assert len(d08.run_ids) > 1
    assert len(d09.run_ids) == 14  # 7 original + 7 fill-campaign cells


def test_d09_attempt_and_gate_counts_are_preserved() -> None:
    rows = _rows(D09 / "points.csv")
    # 0.2.0 = original campaign + 20260721 fill (bare/conv/reopt each
    # 3,368 + 11,668; native 5,136 + 11,050).
    assert Counter(row["gauge"] for row in rows) == {
        "bare": 15036,
        "canonical-r-converted": 15036,
        "canonical-r-reoptimized": 15036,
        "canonical-r-native": 16186,
    }
    assert Counter(row["source_category"] for row in rows) == {
        "converged_branch": 40253,
        "branch_not_found": 19693,
        "failed_branch": 1348,
    }
    assert Counter(row["solver_succeeded"] for row in rows) == {
        "true": 61250,
        "false": 44,
    }
    assert Counter(row["physical_guards_clear"] for row in rows) == {
        "null": 41601,
        "false": 19693,
    }
    for field in (
        "bounds_clear",
        "continuity_passed",
        "physically_admissible",
        "selected",
    ):
        assert {row[field] for row in rows} == {"null"}


def test_d09_grid_and_square_quadrature_are_canonical() -> None:
    rows = _rows(D09 / "points.csv")
    bethe = [row for row in rows if row["lattice"] == "bethe"]
    bethe_keys = {
        (row["u_over_d"], row["t_over_d"])
        for row in bethe
    }
    square = [row for row in rows if row["lattice"] == "square"]
    square_keys = {(row["u_over_d"], row["t_over_d"]) for row in square}
    assert len(bethe_keys) == 1887
    assert len(square_keys) == 1791
    assert {row["lattice_quadrature"] for row in square} == {
        "continuum_elliptic_dos"
    }
    assert {row["dos_node_count"] for row in square} == {"2001"}
    assert {row["quadrature_node_count"] for row in bethe} == {"256"}
    manifest = json.loads((D09 / "manifest.json").read_text())
    corrections = manifest["extensions"]["metadata_corrections"]
    assert corrections[0]["id"] == "d09-bethe-effective-node-count-v1"
    assert corrections[0]["source_value"] == 65536


def test_quasiparticle_weight_estimators_are_not_mislabeled() -> None:
    d09 = _rows(D09 / "points.csv")
    assert all(row["quasiparticle_weight_from_r"] for row in d09)
    assert all(not row["quasiparticle_weight_matsubara"] for row in d09)
    assert max(
        abs(
            float(row["quasiparticle_weight_pole"])
            - float(row["quasiparticle_weight_from_r"])
        )
        for row in d09
    ) < 2e-14

    d08 = _rows(D08 / "points.csv")
    mg3 = [row for row in d08 if row["m_g"] == "3"]
    mg1 = [row for row in d08 if row["m_g"] == "1"]
    assert all(not row["quasiparticle_weight_matsubara"] for row in mg3)
    assert any(row["quasiparticle_weight_from_r"] for row in mg3)
    assert any(row["quasiparticle_weight_matsubara"] for row in mg1)


def test_lossless_archive_checksums_and_record_counts() -> None:
    roots = D08 / "raw/roots.jsonl.gz"
    campaign = D09 / "raw/raw_campaign.tar.gz"
    assert _sha256(roots) == (
        "c565118e41c0c8e8e7582871c97b31e7b79b267c934eac91d16f7eb86f83ae6f"
    )
    assert _sha256(campaign) == (
        "bee997175ebe211853638c4e657e77c784e09aad95232b2f3a91c44842807f0e"
    )

    digest = hashlib.sha256()
    root_rows = 0
    with gzip.open(roots, "rb") as stream:
        for line in stream:
            digest.update(line)
            root_rows += 1
    assert root_rows == 20228
    assert digest.hexdigest() == (
        "21f9244f8ebefaf0525f9b2077445f5d41a65ae82099e97a697eda4fc8620325"
    )

    attempt_rows = 0
    with tarfile.open(campaign, "r:gz") as archive:
        for member in archive.getmembers():
            parts = Path(member.name).parts
            if (
                member.isfile()
                and len(parts) == 3
                and parts[0] == "raw_campaign"
                and parts[1]
                in {
                    "bethe_mg1_bare",
                    "bethe_mg1_Rnative",
                    "bethe_mg3_Rnative",
                    "square_mg1_bare",
                    "square_mg1_Rnative",
                    "square_mg3_bare",
                    "square_mg3_Rnative",
                }
                and parts[2].endswith(".jsonl")
            ):
                extracted = archive.extractfile(member)
                assert extracted is not None
                attempt_rows += sum(1 for line in extracted if line.strip())
    assert attempt_rows == 15240


def test_source_archive_is_complete_and_portable() -> None:
    inventory = _rows(D09 / "provenance/source-code-inventory.csv")
    assert len(inventory) == 74
    assert Counter(row["transformation"] for row in inventory) == {
        "byte-for-byte": 67,
        "machine paths made repository-relative": 7,
    }

    stage3 = _rows(D09 / "provenance/stage3_source_manifest.csv")
    expected = {
        row["path"]: row["sha256"]
        for row in stage3
        if row["role"] in {"solver_code", "builder", "test"}
    }
    imported = {row["path"]: row["source_sha256"] for row in inventory}
    assert len(expected) == 34
    assert all(imported[path] == digest for path, digest in expected.items())

    source_archive = (
        D09 / "provenance/source-code-portable-1d987593.tar.gz"
    )
    with tarfile.open(source_archive, "r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            extracted = archive.extractfile(member)
            assert extracted is not None
            assert b"/Users/" not in extracted.read()


def test_manifests_keep_execution_and_selection_status_honest() -> None:
    for root in (D08, D09):
        document = json.loads((root / "manifest.json").read_text())
        assert document["release_status"] == "draft"
        assert document["data_stage"] == "validated"
        assert document["provenance"]["dirty"] is True
        assert document["provenance"]["revision"] == (
            "1a3af4af02029a84cf998109cb60dc96217863c8"
        )
        assert document["extensions"]["selection_status"] == "not applied"
