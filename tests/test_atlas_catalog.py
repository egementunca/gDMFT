from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

import pytest

from gdmft.atlas.catalog import (
    D08_DATASET_ID,
    D09_DATASET_ID,
    EXCLUDED_REPRESENTATION,
    GAUGE_EVIDENCE,
    PRIMARY_PHYSICS,
    SUPPLEMENTARY,
    catalog_metadata,
    catalog_policy_metadata,
    classify_point,
    default_physics_rows,
    primary_route,
)

ROOT = Path(__file__).parents[1]
D08 = ROOT / "data/datasets/single-site-gauge-matrix-v1/points.csv"
D09 = ROOT / "data/datasets/single-site-scan-matrix-v2/points.csv"


def _row(
    *,
    lattice: str,
    m_g: int,
    gauge: str,
    quadrature: str,
    category: str | None = "converged_branch",
    source_converged: str | None = "true",
    point_id: str = "point",
    u: str = "1.0",
    t: str = "0.01",
) -> dict[str, object]:
    return {
        "point_id": point_id,
        "lattice": lattice,
        "m_g": str(m_g),
        "gauge": gauge,
        "lattice_quadrature": quadrature,
        "source_category": category,
        "source_converged": source_converged,
        "solution_family": "metal-up",
        "continuation_direction": "up",
        "u_over_d": u,
        "t_over_d": t,
    }


@pytest.mark.parametrize(
    ("lattice", "m_g", "dataset_id", "quadrature"),
    [
        ("bethe", 1, D09_DATASET_ID, "bethe_semicircle"),
        ("bethe", 3, D09_DATASET_ID, "bethe_semicircle"),
        ("square", 1, D09_DATASET_ID, "continuum_elliptic_dos"),
        ("square", 3, D09_DATASET_ID, "continuum_elliptic_dos"),
    ],
)
def test_primary_route_matrix_is_explicit(
    lattice: str, m_g: int, dataset_id: str, quadrature: str
) -> None:
    route = primary_route(lattice, m_g)
    assert route.dataset_id == dataset_id
    assert route.gauge == "bare"
    assert route.quadrature == quadrature
    assert route.purpose == PRIMARY_PHYSICS

    row = _row(
        lattice=lattice,
        m_g=m_g,
        gauge="bare",
        quadrature=quadrature,
    )
    if dataset_id == D08_DATASET_ID:
        row["source_category"] = None
    decision = classify_point(dataset_id, row)
    assert decision.is_primary_route is True
    assert decision.status_accepted is True
    assert decision.quadrature_status == "matches"
    assert decision.include_default_physics is True


def test_unknown_cell_fails_loudly() -> None:
    with pytest.raises(KeyError, match="no primary"):
        primary_route("triangular", 3)


@pytest.mark.parametrize(
    "gauge", ["canonical-r-native", "canonical-r-reoptimized"]
)
def test_d09_independent_r_routes_are_gauge_evidence(gauge: str) -> None:
    row = _row(
        lattice="square",
        m_g=3,
        gauge=gauge,
        quadrature="continuum_elliptic_dos",
    )
    decision = classify_point(D09_DATASET_ID, row)
    assert decision.purpose == GAUGE_EVIDENCE
    assert decision.status_accepted is True
    assert decision.include_default_physics is False
    assert decision.reason


@pytest.mark.parametrize("dataset_id", [D08_DATASET_ID, D09_DATASET_ID])
def test_exact_conversions_never_enter_physics_counts(dataset_id: str) -> None:
    row = _row(
        lattice="bethe",
        m_g=1,
        gauge="canonical-r-converted",
        quadrature=(
            "bethe_semicircle"
            if dataset_id == D09_DATASET_ID
            else "bethe_semicircle_closed_form"
        ),
    )
    decision = classify_point(dataset_id, row)
    assert decision.purpose == EXCLUDED_REPRESENTATION
    assert decision.include_default_physics is False
    assert "coordinate" in decision.reason


def test_status_and_quadrature_are_independent_gates() -> None:
    branch_not_found = _row(
        lattice="square",
        m_g=1,
        gauge="bare",
        quadrature="continuum_elliptic_dos",
        category="branch_not_found",
    )
    status_rejected = classify_point(D09_DATASET_ID, branch_not_found)
    assert status_rejected.is_primary_route is True
    assert status_rejected.status_accepted is False
    assert status_rejected.quadrature_status == "matches"
    assert status_rejected.include_default_physics is False

    wrong_quadrature = dict(branch_not_found)
    wrong_quadrature["source_category"] = "converged_branch"
    wrong_quadrature["lattice_quadrature"] = "uniform_kmesh"
    quadrature_rejected = classify_point(D09_DATASET_ID, wrong_quadrature)
    assert quadrature_rejected.status_accepted is True
    assert quadrature_rejected.quadrature_status == "mismatch"
    assert quadrature_rejected.include_default_physics is False


def test_nonprimary_bare_population_is_supplementary() -> None:
    d08_square = _row(
        lattice="square",
        m_g=3,
        gauge="bare",
        quadrature="uniform_kmesh",
    )
    decision = classify_point(D08_DATASET_ID, d08_square)
    assert decision.purpose == SUPPLEMENTARY
    assert decision.is_primary_route is False
    assert decision.include_default_physics is False
    assert D09_DATASET_ID in decision.reason


def test_policy_and_row_metadata_are_json_serializable() -> None:
    policy = catalog_policy_metadata()
    assert len(policy["routes"]) == 4
    assert "registration" not in policy["default_physics_rule"]

    row = _row(
        lattice="bethe",
        m_g=1,
        gauge="bare",
        quadrature="bethe_semicircle",
    )
    metadata = catalog_metadata(D09_DATASET_ID, row)
    assert metadata["purpose"] == PRIMARY_PHYSICS
    json.dumps({"policy": policy, "row": metadata})


def test_default_physics_selection_is_independent_of_mapping_order() -> None:
    d09_primary = _row(
        lattice="square",
        m_g=3,
        gauge="bare",
        quadrature="continuum_elliptic_dos",
        point_id="d09-primary",
    )
    d08_historical = _row(
        lattice="square",
        m_g=3,
        gauge="bare",
        quadrature="uniform_kmesh",
        point_id="d08-historical",
    )
    first = default_physics_rows(
        {
            D08_DATASET_ID: [d08_historical],
            D09_DATASET_ID: [d09_primary],
        }
    )
    second = default_physics_rows(
        {
            D09_DATASET_ID: [d09_primary],
            D08_DATASET_ID: [d08_historical],
        }
    )
    assert [(dataset, row["point_id"]) for dataset, row in first] == [
        (D09_DATASET_ID, "d09-primary")
    ]
    assert [(dataset, row["point_id"]) for dataset, row in second] == [
        (D09_DATASET_ID, "d09-primary")
    ]


def test_real_tables_have_expected_catalog_roles() -> None:
    counts: Counter[str] = Counter()
    accepted_primary = 0
    for dataset_id, path in ((D08_DATASET_ID, D08), (D09_DATASET_ID, D09)):
        with path.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                decision = classify_point(dataset_id, row)
                counts[decision.purpose] += 1
                accepted_primary += int(decision.include_default_physics)

    # Revision 0.2.0 totals (fill campaign merged; bethe-mg3 routed to D09):
    # primary = 3,368 old bare + 11,668 fill bare roots (= the stage3
    # pairing-row count); excluded = the exact conversions of both
    # campaigns + D08's converted view.
    assert counts == {
        PRIMARY_PHYSICS: 15036,
        GAUGE_EVIDENCE: 31222,
        EXCLUDED_REPRESENTATION: 23604,
        SUPPLEMENTARY: 11660,
    }
    assert 0 < accepted_primary < counts[PRIMARY_PHYSICS]
