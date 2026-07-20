from __future__ import annotations

import base64
import csv
import gzip
import json
from pathlib import Path

import pytest

from gdmft.atlas.columns import (
    ATLAS_COLUMNS,
    EXPECTED_CSV_COLUMNS,
    assert_header_locked,
    handled_csv_columns,
)
from gdmft.atlas.payload import (
    encode_payload,
    pack_table,
    round6,
    round_floats,
)

ROOT = Path(__file__).parents[1]
POINT_TABLES = (
    ROOT / "data/datasets/single-site-gauge-matrix-v1/points.csv",
    ROOT / "data/datasets/single-site-scan-matrix-v2/points.csv",
)


def test_round6_and_round_floats() -> None:
    assert round6(0.6350811849) == 0.635081
    assert round6(4.6e-05) == 4.6e-05
    assert round6(0.0) == 0.0
    rounded = round_floats(
        {"a": [1.23456789, float("nan")], "b": float("inf"), "ok": True}
    )
    assert rounded == {"a": [1.23457, None], "b": None, "ok": True}


def test_encode_payload_roundtrip_and_no_nan() -> None:
    payload = {"x": [1.5, None, 0.000123456789], "s": "text", "n": 5136}
    blob, stats = encode_payload(round_floats(payload), compress=True)
    unpacked = json.loads(
        gzip.decompress(base64.b64decode(blob.replace("\n", "")))
    )
    assert unpacked == {"x": [1.5, None, 0.000123457], "s": "text", "n": 5136}
    assert set(stats) >= {"raw_json_bytes", "gzip_bytes", "embedded_bytes"}

    with pytest.raises(ValueError):
        encode_payload({"bad": float("nan")}, compress=True)


def test_pack_table_orders_fields_and_parses_numbers() -> None:
    rows = [
        {"a": "1.25", "b": "x", "c": None},
        {"a": None, "b": "y", "c": "z"},
    ]
    packed = pack_table(rows, ("a", "b", "c"), {"a"})
    assert packed == {
        "fields": ["a", "b", "c"],
        "rows": [[1.25, "x", None], [None, "y", "z"]],
    }


def test_schema_lock_against_contract_and_real_headers() -> None:
    # Every locked column is accounted for exactly once.
    assert handled_csv_columns() == set(EXPECTED_CSV_COLUMNS)
    assert len({spec.key for spec in ATLAS_COLUMNS}) == len(ATLAS_COLUMNS)

    # The packaged machine contract's required columns are a subset.
    contract = json.loads(
        (ROOT / "src/gdmft/schemas/point-table-v1.json").read_text()
    )
    assert set(contract["required_columns"]) <= set(EXPECTED_CSV_COLUMNS)

    # The real registered tables carry exactly the locked header.
    for table in POINT_TABLES:
        with table.open(encoding="utf-8", newline="") as stream:
            header = next(csv.reader(stream))
        assert_header_locked(tuple(header))


def test_header_lock_rejects_drift() -> None:
    with pytest.raises(ValueError, match="drifted"):
        assert_header_locked(EXPECTED_CSV_COLUMNS[:-1])
    shuffled = (
        EXPECTED_CSV_COLUMNS[1],
        EXPECTED_CSV_COLUMNS[0],
        *EXPECTED_CSV_COLUMNS[2:],
    )
    with pytest.raises(ValueError, match="drifted"):
        assert_header_locked(shuffled)
