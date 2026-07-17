from __future__ import annotations

import json
from pathlib import Path

import pytest

from gdmft.data import (
    ManifestError,
    load_manifest,
    validate_manifest,
    validate_point_table,
    verify_artifacts,
)

EXAMPLE = Path(__file__).parents[1] / "data" / "example" / "manifest.json"


def test_example_manifest_and_artifact_are_valid() -> None:
    document = load_manifest(EXAMPLE)
    verify_artifacts(document, EXAMPLE.parent)
    assert document["schema_version"] == "gdmft.dataset.v1"


def test_selected_dataset_requires_selection_policy() -> None:
    document = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    document["data_stage"] = "selection_applied"
    with pytest.raises(ManifestError, match="selection"):
        validate_manifest(document)


def test_artifact_cannot_escape_dataset_root() -> None:
    document = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    document["artifacts"][0]["path"] = "../points.csv"
    with pytest.raises(ManifestError):
        validate_manifest(document)


def test_point_table_rejects_invalid_gate(tmp_path: Path) -> None:
    table = tmp_path / "points.csv"
    text = (EXAMPLE.parent / "points.csv").read_text(encoding="utf-8")
    table.write_text(
        text.replace(
            ",true,true,true,true,true,null",
            ",true,maybe,true,true,true,null",
        )
    )
    with pytest.raises(ValueError, match="must be true, false, or null"):
        validate_point_table(table)


def test_point_table_checks_declared_row_count() -> None:
    with pytest.raises(ValueError, match="row-count mismatch"):
        validate_point_table(EXAMPLE.parent / "points.csv", expected_rows=2)


def test_selected_point_requires_reason_and_physical_decision(tmp_path: Path) -> None:
    table = tmp_path / "points.csv"
    text = (EXAMPLE.parent / "points.csv").read_text(encoding="utf-8")
    table.write_text(text.replace(",null,null,null,,", ",null,null,true,,"))
    with pytest.raises(ValueError, match="physically_admissible=true"):
        validate_point_table(table)


def test_published_dataset_requires_rights_and_archive() -> None:
    document = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    document["data_stage"] = "selection_applied"
    document["release_status"] = "published"
    document["selection"] = {
        "policy": "example",
        "implementation": "example",
        "reviewed": True,
    }
    with pytest.raises(ManifestError, match="publication|rights"):
        validate_manifest(document)
