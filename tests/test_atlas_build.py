from __future__ import annotations

import base64
import gzip
import json
import re
from pathlib import Path

import pytest

from gdmft.atlas.build import _build_time, assemble_html, build_atlas

ROOT = Path(__file__).parents[1]
SIZE_BUDGET_BYTES = 3_500_000


@pytest.fixture(scope="module")
def built(tmp_path_factory: pytest.TempPathFactory):
    output = tmp_path_factory.mktemp("atlas") / "atlas.html"
    path, stats = build_atlas(
        registry=ROOT / "data/registry.toml", output=output
    )
    html = path.read_text(encoding="utf-8")
    match = re.search(
        r'data-encoding="gzip-base64">\n(.*?)\n</script>', html, re.S
    )
    assert match is not None
    payload = json.loads(
        gzip.decompress(base64.b64decode(match.group(1).replace("\n", "")))
    )
    return path, stats, html, payload


def test_build_produces_html_under_budget(built) -> None:
    path, stats, html, _ = built
    assert path.is_file()
    assert stats["html_bytes"] < SIZE_BUDGET_BYTES
    assert "<title>gDMFT Atlas</title>" in html
    assert "Atlas.init" in html
    # A literal NaN token would break JSON.parse in the browser.
    assert re.search(r"\bNaN\b", html) is None


def test_payload_carries_all_registered_data(built) -> None:
    _, _, _, payload = built
    datasets = payload["datasets"]
    assert datasets["single-site.gauge-matrix-v1"]["n"] == 20228
    assert datasets["single-site.scan-matrix-v2"]["n"] == 15240

    gem = payload["references"]["gem"]
    assert gem["n"] == 5136
    assert gem["anchored_to"] == "single-site.scan-matrix-v2"
    assert gem["coverage"]["bethe_b3_up"] == 52 * 17
    assert gem["coverage"]["square_b1_down"] == 40 * 10

    ed = payload["references"]["ed"]
    assert len(ed["v2"]["rows"]) == 54
    assert len(ed["v1_legacy"]["rows"]) > 0

    references = payload["references"]
    assert references["nrg"]["n"] == 72
    assert references["professor_gga"]["n"] == 2562
    assert references["ctqmc"]["n"] == 1

    assert len(payload["evidence"]["claim_ledger"]["rows"]) == 5
    assert len(payload["evidence"]["bare_r_pairing"]["rows"]) == 3368


def test_payload_carries_explicit_primary_route_catalog(built) -> None:
    _, _, _, payload = built
    catalog = payload["catalog"]
    routes = {
        (route["lattice"], route["m_g"]): route
        for route in catalog["policy"]["routes"]
    }
    assert routes[("bethe", 1)]["dataset_id"] == "single-site.scan-matrix-v2"
    assert routes[("bethe", 3)]["dataset_id"] == "single-site.gauge-matrix-v1"
    assert routes[("square", 1)]["dataset_id"] == "single-site.scan-matrix-v2"
    assert routes[("square", 3)]["dataset_id"] == "single-site.scan-matrix-v2"
    assert catalog["default_physics_count"] == 6648
    assert catalog["selection_status"] == "not applied"
    assert payload["derived"]["basis"]["kind"] == "attempt-level diagnostic"

    d08 = catalog["datasets"]["single-site.gauge-matrix-v1"]
    d09 = catalog["datasets"]["single-site.scan-matrix-v2"]
    assert d08["role_counts"]["primary-physics"] == 5506
    assert d08["default_row_count"] == 4633
    assert d09["role_counts"]["primary-physics"] == 3368
    assert d09["role_counts"]["gauge-evidence"] == 8504
    assert d09["default_row_count"] == 2015


def test_d09_ed_payload_keeps_complete_protocol_semantics(built) -> None:
    _, _, _, payload = built
    ed = payload["references"]["ed"]
    assert ed["current_key"] == "v2"
    assert ed["legacy_keys"] == ["v1_legacy"]

    current = ed["v2"]
    assert current["n"] == 54
    assert {
        "eps",
        "V",
        "bath_fit_beta",
        "chi2_normalized",
        "fit_rel_rms",
        "fixed_point_converged",
        "fit_optimizer_converged",
        "bath_approximation_quality",
        "Z_estimator_converged",
        "accuracy_qualified",
    } <= set(current["fields"])
    index = {field: i for i, field in enumerate(current["fields"])}
    first = current["rows"][0]
    assert first[index["eps"]] == [0.0]
    assert first[index["V"]] == [pytest.approx(0.0942115)]
    assert first[index["Z_by_npts"]] == [
        [2, 1.0],
        [3, 1.0],
        [4, 1.0],
        [6, 1.0],
    ]
    assert first[index["fixed_point_converged"]] == 1
    assert first[index["accepted"]] == 1
    assert first[index["bath_fit_beta"]] == 200
    assert current["availability"]["physical_t_over_d"] == [0.0]
    assert current["availability"]["bath_fit_beta"] == [200.0]
    assert current["availability"]["z_estimator_converged_rows"] == 24
    assert current["availability"]["accuracy_qualified_rows"] == 12
    assert current["availability"]["finite_temperature_join"] is False
    assert "NOT a physical T/D=0.005" in current["protocol"][
        "ground_state_semantics"
    ]["warning"]

    legacy = ed["v1_legacy"]
    assert legacy["n"] == 523
    assert legacy["status"] == "legacy D08 supporting evidence"
    assert "do not merge" in legacy["warning"]
    assert legacy["availability"]["lattices"] == ["bethe", "square"]


def test_d09_ed_bath_arrays_have_the_registered_reduced_layout(built) -> None:
    _, _, _, payload = built
    current = payload["references"]["ed"]["v2"]
    index = {field: i for i, field in enumerate(current["fields"])}
    rows = current["rows"]

    nb1 = [row for row in rows if int(row[index["Nb"]]) == 1]
    nb3 = [row for row in rows if int(row[index["Nb"]]) == 3]
    assert len(nb1) == 28
    assert len(nb3) == 26
    assert {row[index["direction"]] for row in nb1 + nb3} == {"up", "down"}

    assert all(row[index["eps"]] == [0.0] for row in nb1)
    assert all(len(row[index["V"]]) == 1 for row in nb1)
    assert any(row[index["V"]][0] < 0 for row in nb1)

    for row in nb3:
        eps = row[index["eps"]]
        couplings = row[index["V"]]
        assert eps[0] == 0.0
        assert eps[1] == pytest.approx(-eps[2])
        assert couplings[1] == pytest.approx(couplings[2])
    assert {row[index["U_over_D"]] for row in nb3} == {
        0.0,
        0.1,
        0.2,
        0.3,
        0.4,
        0.5,
        1.0,
        1.5,
        2.0,
        2.4,
        2.5,
        2.8,
        3.0,
    }


def test_dedicated_benchmark_tables_and_availability(built) -> None:
    _, _, _, payload = built
    references = payload["references"]

    nrg = references["nrg"]
    assert nrg["n"] == 72
    assert nrg["source"]["path"] == "tables/nrg_thermal.csv"
    assert "compare_all" not in nrg["source"]["path"]
    assert len(nrg["upstream_files"]) == 10
    assert nrg["availability"]["u_over_d"] == [1.0, 2.0, 3.2]
    assert len(nrg["availability"]["t_over_d"]) == 24
    assert nrg["availability"]["finite_rows"] == {
        "double_occupancy": 64,
        "kinetic_energy_over_d": 65,
        "potential_energy_over_d": 65,
        "total_energy_over_d": 65,
    }

    professor = references["professor_gga"]
    assert professor["n"] == 2562
    assert professor["source"]["path"] == "tables/prof_gga_grids.csv"
    assert professor["availability"]["bath_budgets"] == [1, 3]
    assert len(professor["availability"]["u_over_d"]) == 21
    assert len(professor["availability"]["t_over_d"]) == 61
    assert len(professor["upstream_files"]) == 6
    assert "total_energy_raw + U_over_D/2" in professor["availability"][
        "energy_convention"
    ]

    ctqmc = references["ctqmc"]
    assert ctqmc["n"] == 1
    assert ctqmc["source"]["path"] == "tables/ctqmc_anchors.csv"
    assert ctqmc["availability"]["t_over_d"] == [0.005]
    assert ctqmc["availability"]["finite_rows"][
        "kinetic_energy_over_d"
    ] == 0

    availability = references["availability"]
    assert availability["dmft_ed_d09"]["rows"] == 54
    assert availability["dmft_ed_d08_legacy"]["rows"] == 523
    assert availability["nrg"]["rows"] == 72
    assert availability["professor_gga"]["rows"] == 2562
    assert availability["ctqmc"]["rows"] == 1
    for key in ("nrg", "professor_gga", "ctqmc"):
        assert references[key]["source"]["provenance"]["revision"] == (
            "1d987593969520b8cd6e191ca284682738778a6d"
        )
    catalog = {
        entry["dataset_id"]: entry for entry in references["catalog"]
    }
    assert catalog["references.gem-gga-v1"]["n"] == 5136
    assert catalog["references.benchmarks-v1"]["n"] == 2635
    assert "compare_all" in catalog["references.benchmarks-v1"]["availability"]
    meta_counts = {
        entry["id"]: entry["row_count"] for entry in payload["meta"]["datasets"]
    }
    assert meta_counts["references.gem-gga-v1"] == 5136
    assert meta_counts["references.benchmarks-v1"] == 2635


def test_payload_gate_tallies_match_dataset_invariants(built) -> None:
    _, _, _, payload = built
    gates = payload["datasets"]["single-site.scan-matrix-v2"]["gates"]
    assert gates["solver_succeeded"] == {
        "true": 15224,
        "false": 16,
        "null": 0,
    }
    assert gates["physical_guards_clear"] == {
        "true": 0,
        "false": 5136,
        "null": 10104,
    }
    for gate in (
        "bounds_clear",
        "continuity_passed",
        "physically_admissible",
        "selected",
    ):
        assert gates[gate] == {"true": 0, "false": 0, "null": 15240}


def test_payload_grids_and_encoding_are_consistent(built) -> None:
    _, _, _, payload = built
    scan = payload["datasets"]["single-site.scan-matrix-v2"]
    assert len(scan["grids"]["bethe"]["u"]) == 52
    assert len(scan["grids"]["bethe"]["t"]) == 17
    assert len(scan["grids"]["square"]["u"]) == 40
    assert len(scan["grids"]["square"]["t"]) == 10
    assert scan["raw_d"] == {"bethe": 1.0, "square": 2.0}
    assert len(scan["cols"]["iu"]) == scan["n"]
    assert len(scan["cols"]["pid"]) == scan["n"]
    # v2 constants: schema-fixed values folded out of the arrays.
    assert scan["constants"]["m_h"] == 2
    assert scan["constants"]["density"] == 1.0
    # v1 drops its all-null energies, v2 keeps them.
    v1 = payload["datasets"]["single-site.gauge-matrix-v1"]
    assert "kinetic_energy_over_d" in v1["cols_dropped"]
    assert "ekin_d" in scan["cols"]


def test_payload_embeds_poles_and_dos(built) -> None:
    _, _, _, payload = built
    scan = payload["datasets"]["single-site.scan-matrix-v2"]
    gauge = payload["datasets"]["single-site.gauge-matrix-v1"]
    # every row joined 1:1; v2 is fully PH-symmetric, v1 keeps exotics as
    # full arrays and 3,092 rows use the canonical-R h-sector view
    assert scan["poles"]["counts"]["rows"] == 15240
    assert scan["poles"]["counts"]["full"] == 0
    assert scan["poles"]["counts"]["h_from_R"] == 0
    assert gauge["poles"]["counts"]["rows"] == 20228
    assert gauge["poles"]["counts"]["full"] > 0
    assert gauge["poles"]["counts"]["h_from_R"] == 3092
    assert len(scan["poles"]["red"]["v0"]) == 15240

    dos = payload["dos"]["square"]
    assert len(dos["eps"]) == 512
    assert sum(dos["w"]) == pytest.approx(1.0, abs=1e-3)


def test_payload_reproduces_published_ustar(built) -> None:
    # U*(T/D = 0.01) = 2.492 for bethe m_g=3 bare (gauge-matrix v1) —
    # the benchmark-note headline number.
    _, _, _, payload = built
    entries = [
        entry
        for entry in payload["derived"]["ustar"]
        if entry["ds"] == "single-site.gauge-matrix-v1"
        and entry["lattice"] == "bethe"
        and entry["m_g"] == 3
        and entry["gauge"] == "bare"
        and abs(entry["t"] - 0.01) < 1e-12
    ]
    assert len(entries) == 1
    assert entries[0]["ustar"] == pytest.approx(2.492, abs=5e-3)


def test_uncompressed_encoding_attribute() -> None:
    html = assemble_html("QUJD", compressed=False)
    assert 'data-encoding="base64-json"' in html
    html = assemble_html("QUJD", compressed=True)
    assert 'data-encoding="gzip-base64"' in html


def test_source_date_epoch_makes_release_timestamp_reproducible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    assert _build_time() == "1970-01-01T00:00:00Z"
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "not-an-integer")
    with pytest.raises(ValueError, match="SOURCE_DATE_EPOCH"):
        _build_time()
