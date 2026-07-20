"""Validation and reading for canonical scalar point tables."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Iterator
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path
from typing import Any

NULL_VALUES = {"", "null"}


@dataclass(frozen=True)
class PointTableSummary:
    """Validated point-table dimensions and identities."""

    rows: int
    columns: tuple[str, ...]
    run_ids: tuple[str, ...]


def _contract() -> dict[str, Any]:
    resource = files("gdmft.schemas").joinpath("point-table-v1.json")
    return json.loads(resource.read_text(encoding="utf-8"))


def _require_text(value: str | None, field: str, line: int) -> None:
    if value is None or not value.strip():
        raise ValueError(f"point table line {line}: {field} must not be empty")


def _require_integer(value: str | None, field: str, line: int) -> None:
    try:
        parsed = int(value or "")
    except ValueError as exc:
        raise ValueError(
            f"point table line {line}: {field} must be an integer"
        ) from exc
    if parsed < 0:
        raise ValueError(f"point table line {line}: {field} must be nonnegative")


def _require_number(value: str | None, field: str, line: int) -> None:
    try:
        parsed = float(value or "")
    except ValueError as exc:
        raise ValueError(
            f"point table line {line}: {field} must be a number"
        ) from exc
    if not math.isfinite(parsed):
        raise ValueError(f"point table line {line}: {field} must be finite")


def _parse_nullable_boolean(
    value: str | None, field: str, line: int
) -> bool | None:
    normalized = (value or "").strip().lower()
    if normalized not in {"true", "false", "null", ""}:
        raise ValueError(
            f"point table line {line}: {field} must be true, false, or null"
        )
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def iter_point_rows(path: str | Path) -> Iterator[dict[str, str | None]]:
    """Stream a scalar table as dictionaries with contract null decoding.

    Values equal to one of the contract null encodings (empty string or
    ``"null"``) are returned as ``None``; every other value is returned as
    its verbatim CSV string. Works for any table that follows the point
    contract's null convention (point tables, reference tables).
    """
    table_path = Path(path)
    with table_path.open("r", encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError(f"table has no header: {table_path}")
        for row in reader:
            yield {
                key: (None if value in NULL_VALUES else value)
                for key, value in row.items()
            }


def find_artifact(
    document: dict[str, Any],
    *,
    role: str | None = None,
    schema: str | None = None,
    path: str | None = None,
) -> dict[str, Any]:
    """Return the single manifest artifact matching the given filters."""
    matches = [
        artifact
        for artifact in document["artifacts"]
        if (role is None or artifact.get("role") == role)
        and (schema is None or artifact.get("schema") == schema)
        and (path is None or artifact.get("path") == path)
    ]
    wanted = {"role": role, "schema": schema, "path": path}
    filters = {key: value for key, value in wanted.items() if value is not None}
    if not matches:
        raise ValueError(f"no artifact matches {filters}")
    if len(matches) > 1:
        raise ValueError(f"multiple artifacts match {filters}")
    return matches[0]


def validate_point_table(
    path: str | Path, *, expected_rows: int | None = None
) -> PointTableSummary:
    """Validate a CSV point table against the packaged v1 contract."""
    table_path = Path(path)
    contract = _contract()
    try:
        stream = table_path.open("r", encoding="utf-8", newline="")
    except OSError as exc:
        raise ValueError(f"cannot read point table {table_path}: {exc}") from exc

    with stream:
        reader = csv.DictReader(stream)
        columns = reader.fieldnames
        if columns is None:
            raise ValueError(f"point table has no header: {table_path}")
        if len(columns) != len(set(columns)):
            raise ValueError(f"point table has duplicate columns: {table_path}")
        missing = [name for name in contract["required_columns"] if name not in columns]
        if missing:
            raise ValueError(
                f"point table is missing required columns: {', '.join(missing)}"
            )

        identities: set[tuple[str, str]] = set()
        run_ids: set[str] = set()
        row_count = 0
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"point table line {line}: too many values")
            if row["schema_version"] != contract["schema_version"]:
                raise ValueError(
                    f"point table line {line}: unsupported schema_version "
                    f"{row['schema_version']!r}"
                )
            for field in contract["text_columns"]:
                _require_text(row[field], field, line)
            for field in contract["integer_columns"]:
                _require_integer(row[field], field, line)
            for field in contract["number_columns"]:
                _require_number(row[field], field, line)
            gate_fields = contract["evidence_fields"] + contract["decision_fields"]
            gates = {
                field: _parse_nullable_boolean(row[field], field, line)
                for field in gate_fields
            }
            if gates["selected"] is True:
                if gates["physically_admissible"] is not True:
                    raise ValueError(
                        f"point table line {line}: selected requires "
                        "physically_admissible=true"
                    )
                if not (row["selection_reason"] or "").strip():
                    raise ValueError(
                        f"point table line {line}: selected requires selection_reason"
                    )

            identity = (row["run_id"], row["point_id"])
            if identity in identities:
                raise ValueError(
                    f"point table line {line}: duplicate run_id/point_id {identity!r}"
                )
            identities.add(identity)
            run_ids.add(row["run_id"])
            row_count += 1

    if expected_rows is not None and row_count != expected_rows:
        raise ValueError(
            f"point table row-count mismatch: expected {expected_rows}, "
            f"found {row_count}"
        )
    return PointTableSummary(row_count, tuple(columns), tuple(sorted(run_ids)))
