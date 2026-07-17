"""Validation and checksum verification for gDMFT dataset manifests."""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .points import validate_point_table


class ManifestError(ValueError):
    """Raised when a manifest or one of its local artifacts is invalid."""


def _schema() -> dict[str, Any]:
    resource = files("gdmft.schemas").joinpath("dataset-manifest-v1.schema.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def load_manifest(path: str | Path) -> dict[str, Any]:
    """Load and validate a JSON dataset manifest."""
    manifest_path = Path(path)
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read manifest {manifest_path}: {exc}") from exc
    validate_manifest(document)
    return document


def validate_manifest(document: dict[str, Any]) -> None:
    """Validate a decoded document against the packaged v1 schema."""
    validator = Draft202012Validator(_schema(), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(document), key=lambda error: list(error.path))
    if not errors:
        return
    messages = []
    for error in errors:
        location = ".".join(str(part) for part in error.absolute_path) or "<root>"
        messages.append(f"{location}: {error.message}")
    raise ManifestError("invalid dataset manifest:\n" + "\n".join(messages))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify_artifacts(document: dict[str, Any], root: str | Path) -> int:
    """Verify local artifacts and return the number of verified files."""
    root_path = Path(root).resolve()
    verified = 0
    for artifact in document["artifacts"]:
        if "path" not in artifact:
            continue
        artifact_path = (root_path / artifact["path"]).resolve()
        if artifact_path != root_path and root_path not in artifact_path.parents:
            raise ManifestError(f"artifact escapes dataset root: {artifact['path']}")
        if not artifact_path.is_file():
            raise ManifestError(f"artifact is missing: {artifact['path']}")
        size = artifact_path.stat().st_size
        if size != artifact["bytes"]:
            raise ManifestError(
                f"artifact size mismatch for {artifact['path']}: "
                f"expected {artifact['bytes']}, found {size}"
            )
        digest = _sha256(artifact_path)
        if digest != artifact["sha256"]:
            raise ManifestError(
                f"artifact checksum mismatch for {artifact['path']}: "
                f"expected {artifact['sha256']}, found {digest}"
            )
        if artifact.get("schema") == "gdmft.point.v1":
            try:
                validate_point_table(artifact_path, expected_rows=artifact.get("rows"))
            except ValueError as exc:
                raise ManifestError(str(exc)) from exc
        verified += 1
    return verified
