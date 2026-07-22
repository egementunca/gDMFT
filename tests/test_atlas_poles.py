from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from gdmft.atlas.poles import (
    PoleError,
    _record_poles,
    _reduce_record,
    extract_pole_table,
)


def test_reduce_symmetric_record_normalizes_by_raw_d() -> None:
    # square-style raw record (D = 2): everything halves
    result = _reduce_record(
        g_eps=[0.0, 4.0, -4.0],
        g_v=[0.6, 1.2, 1.2],
        h_eta=[1.5, -1.5],
        h_w=[0.8, 0.8],
        raw_d=2.0,
    )
    assert result == {
        "red": {"v0": 0.3, "v1": 0.6, "eps1": 2.0, "w": 0.4, "eta": 0.75}
    }


def test_reduce_asymmetric_record_falls_back_to_full_arrays() -> None:
    # the v1 dark family: a single non-centered g mode
    result = _reduce_record(
        g_eps=[-5.0], g_v=[0.1], h_eta=[27.0, -20.0], h_w=[18.0, 18.0], raw_d=1.0
    )
    assert "full" in result
    assert result["full"]["ge"] == [-5.0]
    assert result["full"]["he"] == [27.0, -20.0]


def test_reduce_mg1_record_has_no_satellites() -> None:
    result = _reduce_record(
        g_eps=[0.0], g_v=[0.34], h_eta=[13.9, -13.9], h_w=[7.44, 7.44], raw_d=1.0
    )
    assert result["red"]["v0"] == 0.34
    assert result["red"]["v1"] is None
    assert result["red"]["eps1"] is None
    assert result["red"]["eta"] == 13.9


def test_record_poles_uses_canonical_view_when_bare_h_missing() -> None:
    record = {
        "g_sector": {"eps_g": [0.0, 2.0, -2.0], "V_g": [0.5, 1.0, 1.0]},
        "bare_h_sectors": None,
        "canonical_h_sectors": {"eta_R": [1.0, -1.0], "W_R": [0.7, 0.7]},
    }
    result = _record_poles(record, 1.0)
    assert result["h_from_R"] is True
    assert result["red"]["eta"] == 1.0
    assert result["gateway_red"]["eta"] == 1.0

    with pytest.raises(PoleError):
        _record_poles({"g_sector": {}}, 1.0)


def test_record_poles_preserves_distinct_lattice_and_gateway_h_sectors() -> None:
    record = {
        "g_sector": {"eps_g": [0.0], "V_g": [0.5]},
        "bare_h_sectors": {
            "eta_lattice": [1.0, -1.0],
            "W_lattice": [0.7, 0.7],
            "eta_gateway": [2.0, -2.0],
            "W_gateway": [0.8, 0.8],
        },
    }
    result = _record_poles(record, 1.0)
    assert result["red"]["eta"] == 1.0
    assert result["gateway_red"]["eta"] == 2.0
    assert result["gateway_differs"] is True


def test_extract_pole_table_joins_by_id_and_orders_rows(tmp_path: Path) -> None:
    records = [
        {
            "identity": {"source_record_id": "bbb"},
            "model": {"D": 1.0},
            "g_sector": {"eps_g": [0.0], "V_g": [0.2]},
            "bare_h_sectors": {"eta_lattice": [1.0, -1.0], "W_lattice": [0.5, 0.5]},
            "canonical_h_sectors": None,
        },
        {
            "identity": {"source_record_id": "aaa"},
            "model": {"D": 2.0},
            "g_sector": {"eps_g": [0.0], "V_g": [0.4]},
            "bare_h_sectors": {"eta_lattice": [2.0, -2.0], "W_lattice": [1.0, 1.0]},
            "canonical_h_sectors": None,
        },
    ]
    archive = tmp_path / "roots.jsonl.gz"
    with gzip.open(archive, "wt", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record) + "\n")

    table = extract_pole_table(archive, ["aaa", "bbb"], kind="jsonl")
    # row order follows the point-id list, with per-record D normalization
    assert table["red"]["v0"] == [0.2, 0.2]
    assert table["red"]["eta"] == [1.0, 1.0]
    assert table["counts"] == {
        "rows": 2,
        "reduced": 2,
        "full": 0,
        "h_from_R": 0,
        "gateway_differs": 0,
    }
    assert table["gateway_red"]["eta"] == [1.0, 1.0]

    with pytest.raises(PoleError, match="no raw record"):
        extract_pole_table(archive, ["aaa", "missing"], kind="jsonl")


def test_real_archives_match_declared_counts() -> None:
    root = Path(__file__).parents[1]
    v2 = root / "data/datasets/single-site-scan-matrix-v2"
    manifest = json.loads((v2 / "manifest.json").read_text())
    cells = set(manifest["grid"]["cells"])
    import csv

    with (v2 / "points.csv").open(encoding="utf-8", newline="") as stream:
        point_rows = list(csv.DictReader(stream))
    # Revision 0.2.0: two campaigns whose grids overlap share attempt ids,
    # so records are namespaced by campaign and each archive read separately.
    from gdmft.atlas.poles import assemble_pole_table, collect_pole_records

    merged = {
        f"d09|{pid}": entry
        for pid, entry in collect_pole_records(
            v2 / "raw/raw_campaign.tar.gz", kind="tar", cells=cells
        ).items()
    }
    merged.update({
        f"fill|{pid}": entry
        for pid, entry in collect_pole_records(
            v2 / "raw/fill_attempts_20260721.jsonl.gz", kind="v2-jsonl"
        ).items()
    })
    keys = [
        ("fill|" if row["run_id"].startswith("d09-fill-") else "d09|")
        + row["point_id"]
        for row in point_rows
    ]
    table = assemble_pole_table(keys, merged)
    assert table["counts"]["rows"] == 61294
    # every v2 record is PH-symmetric: no full-array fallbacks
    assert table["counts"]["full"] == 0
    assert table["counts"]["h_from_R"] == 0
    assert table["counts"]["gateway_differs"] == 0
