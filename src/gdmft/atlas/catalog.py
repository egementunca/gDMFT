"""Deterministic source routing for the single-site atlas.

The registered single-site datasets overlap deliberately.  Registration
order must therefore never decide which population represents a physical
cell.  This module records that decision explicitly and keeps three separate
questions separate:

* Is this row on the primary route for its lattice and ``m_g``?
* Did the source dataset accept the numerical attempt?
* Does the row use the quadrature required by the route?

Only rows satisfying all three enter the default physics view.  Canonical-R
native and reoptimized rows from D09 remain available as gauge evidence.
Exact bare-to-R conversions are coordinate representations of their parents
and are excluded from physics counts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any

CATALOG_POLICY_VERSION = "gdmft.atlas.primary-route.v1"

D08_DATASET_ID = "single-site.gauge-matrix-v1"
D09_DATASET_ID = "single-site.scan-matrix-v2"

PRIMARY_PHYSICS = "primary-physics"
GAUGE_EVIDENCE = "gauge-evidence"
EXCLUDED_REPRESENTATION = "excluded-representation"
SUPPLEMENTARY = "supplementary"

_D09_STATUS_POLICY = "d09-source-category-v1"
_D08_STATUS_POLICY = "d08-legacy-source-converged-v1"


@dataclass(frozen=True)
class PrimaryRoute:
    """One explicit primary source for a lattice and impurity budget."""

    route_id: str
    lattice: str
    m_g: int
    dataset_id: str
    gauge: str
    purpose: str
    reason: str
    quadrature: str
    quadrature_status: str
    status_policy_id: str

    def as_metadata(self) -> dict[str, Any]:
        """Return a JSON-serializable route description."""
        return asdict(self)


PRIMARY_ROUTES = (
    PrimaryRoute(
        route_id="bethe-mg1-bare-d09",
        lattice="bethe",
        m_g=1,
        dataset_id=D09_DATASET_ID,
        gauge="bare",
        purpose=PRIMARY_PHYSICS,
        reason=(
            "D09 supplies the complete registered Bethe m_g=1 bare scan "
            "on the comparison grid."
        ),
        quadrature="bethe_semicircle",
        quadrature_status="canonical-route",
        status_policy_id=_D09_STATUS_POLICY,
    ),
    PrimaryRoute(
        route_id="bethe-mg3-bare-d08",
        lattice="bethe",
        m_g=3,
        dataset_id=D08_DATASET_ID,
        gauge="bare",
        purpose=PRIMARY_PHYSICS,
        reason=(
            "D08 contains the Bethe m_g=3 bare population; D09 contains "
            "only the independent canonical-R continuation for this cell."
        ),
        quadrature="bethe_semicircle_closed_form",
        quadrature_status="canonical-route",
        status_policy_id=_D08_STATUS_POLICY,
    ),
    PrimaryRoute(
        route_id="square-mg1-bare-d09",
        lattice="square",
        m_g=1,
        dataset_id=D09_DATASET_ID,
        gauge="bare",
        purpose=PRIMARY_PHYSICS,
        reason=(
            "D09 continuum elliptic-DOS rows supersede the historical "
            "D08 N_k=16 square scan."
        ),
        quadrature="continuum_elliptic_dos",
        quadrature_status="canonical-route",
        status_policy_id=_D09_STATUS_POLICY,
    ),
    PrimaryRoute(
        route_id="square-mg3-bare-d09",
        lattice="square",
        m_g=3,
        dataset_id=D09_DATASET_ID,
        gauge="bare",
        purpose=PRIMARY_PHYSICS,
        reason=(
            "D09 continuum elliptic-DOS rows supersede the historical "
            "D08 N_k=16 square scan."
        ),
        quadrature="continuum_elliptic_dos",
        quadrature_status="canonical-route",
        status_policy_id=_D09_STATUS_POLICY,
    ),
)

_PRIMARY_BY_CELL = {(route.lattice, route.m_g): route for route in PRIMARY_ROUTES}


@dataclass(frozen=True)
class CatalogDecision:
    """Catalog metadata attached to one source row."""

    policy_version: str
    route_id: str | None
    purpose: str
    reason: str
    is_primary_route: bool
    include_default_physics: bool
    status_policy_id: str | None
    status_field: str | None
    source_status: str | None
    status_accepted: bool | None
    quadrature: str | None
    expected_quadrature: str | None
    quadrature_status: str

    def as_metadata(self) -> dict[str, Any]:
        """Return a JSON-serializable row annotation."""
        return asdict(self)


def primary_route(lattice: str, m_g: int | str) -> PrimaryRoute:
    """Return the explicit primary source for ``(lattice, m_g)``.

    Unsupported cells fail loudly so a newly registered population cannot
    become primary merely because it appears first in a registry or payload.
    """
    cell = (_normalise_lattice(lattice), _normalise_m_g(m_g))
    try:
        return _PRIMARY_BY_CELL[cell]
    except KeyError as error:
        raise KeyError(f"no primary single-site route for {cell!r}") from error


def catalog_policy_metadata() -> dict[str, Any]:
    """Return the route policy in a form suitable for a payload or UI."""
    return {
        "schema_version": CATALOG_POLICY_VERSION,
        "default_physics_rule": (
            "primary route AND source status accepted AND quadrature matches"
        ),
        "converted_representation_rule": (
            "canonical-r-converted rows are exact coordinate representations "
            "and never enter default physics counts"
        ),
        "routes": [route.as_metadata() for route in PRIMARY_ROUTES],
    }


def classify_point(
    dataset_id: str, row: Mapping[str, Any]
) -> CatalogDecision:
    """Classify one ``gdmft.point.v1`` row under the catalog policy."""
    lattice = _normalise_lattice(row.get("lattice"))
    m_g = _normalise_m_g(row.get("m_g"))
    gauge = _normalise_text(row.get("gauge"))
    quadrature = _normalise_text(row.get("lattice_quadrature"))
    source_status, status_accepted, status_field, status_policy_id = (
        _source_status(dataset_id, row)
    )

    expected = _expected_quadrature(dataset_id, lattice)
    quadrature_status = _quadrature_status(quadrature, expected)

    if gauge == "canonical-r-converted":
        return CatalogDecision(
            policy_version=CATALOG_POLICY_VERSION,
            route_id=None,
            purpose=EXCLUDED_REPRESENTATION,
            reason=(
                "Exact bare-to-R conversion represents the parent physical "
                "solution in another coordinate system."
            ),
            is_primary_route=False,
            include_default_physics=False,
            status_policy_id=status_policy_id,
            status_field=status_field,
            source_status=source_status,
            status_accepted=status_accepted,
            quadrature=quadrature,
            expected_quadrature=expected,
            quadrature_status=quadrature_status,
        )

    if dataset_id == D09_DATASET_ID and gauge in {
        "canonical-r-native",
        "canonical-r-reoptimized",
    }:
        purpose = GAUGE_EVIDENCE
        if gauge == "canonical-r-native":
            reason = (
                "Independent canonical-R continuation tests solver-route "
                "agreement and remains separate from the bare primary route."
            )
        else:
            reason = (
                "Canonical-R reoptimization tests basin and gauge-route "
                "sensitivity and is not an additional default physics point."
            )
        return CatalogDecision(
            policy_version=CATALOG_POLICY_VERSION,
            route_id=f"d09-{gauge}",
            purpose=purpose,
            reason=reason,
            is_primary_route=False,
            include_default_physics=False,
            status_policy_id=status_policy_id,
            status_field=status_field,
            source_status=source_status,
            status_accepted=status_accepted,
            quadrature=quadrature,
            expected_quadrature=expected,
            quadrature_status=quadrature_status,
        )

    route = _PRIMARY_BY_CELL.get((lattice, m_g))
    is_primary = (
        route is not None
        and dataset_id == route.dataset_id
        and gauge == route.gauge
    )
    if is_primary:
        quadrature_status = _quadrature_status(quadrature, route.quadrature)
        include = status_accepted is True and quadrature_status == "matches"
        return CatalogDecision(
            policy_version=CATALOG_POLICY_VERSION,
            route_id=route.route_id,
            purpose=route.purpose,
            reason=route.reason,
            is_primary_route=True,
            include_default_physics=include,
            status_policy_id=route.status_policy_id,
            status_field=status_field,
            source_status=source_status,
            status_accepted=status_accepted,
            quadrature=quadrature,
            expected_quadrature=route.quadrature,
            quadrature_status=quadrature_status,
        )

    if route is None:
        reason = "No primary single-site route is registered for this cell."
    else:
        reason = (
            f"Not the primary source for this cell; use {route.dataset_id} "
            f"with gauge={route.gauge}."
        )
    return CatalogDecision(
        policy_version=CATALOG_POLICY_VERSION,
        route_id=None,
        purpose=SUPPLEMENTARY,
        reason=reason,
        is_primary_route=False,
        include_default_physics=False,
        status_policy_id=status_policy_id,
        status_field=status_field,
        source_status=source_status,
        status_accepted=status_accepted,
        quadrature=quadrature,
        expected_quadrature=expected,
        quadrature_status=quadrature_status,
    )


def catalog_metadata(dataset_id: str, row: Mapping[str, Any]) -> dict[str, Any]:
    """Return the payload-ready catalog annotation for one row."""
    return classify_point(dataset_id, row).as_metadata()


def is_default_physics(dataset_id: str, row: Mapping[str, Any]) -> bool:
    """Whether a row belongs in the catalog's default physics view."""
    return classify_point(dataset_id, row).include_default_physics


def default_physics_rows(
    datasets: Mapping[str, Iterable[Mapping[str, Any]]],
) -> list[tuple[str, Mapping[str, Any]]]:
    """Select and deterministically order default-physics rows.

    The return value retains the source dataset ID.  Ordering depends only on
    physical coordinates and stable source identity, never mapping insertion
    order.
    """
    selected = [
        (dataset_id, row)
        for dataset_id, rows in datasets.items()
        for row in rows
        if is_default_physics(dataset_id, row)
    ]
    selected.sort(key=lambda item: _catalog_sort_key(*item))
    return selected


def _source_status(
    dataset_id: str, row: Mapping[str, Any]
) -> tuple[str | None, bool | None, str | None, str | None]:
    if dataset_id == D09_DATASET_ID:
        field = "source_category"
        value = _normalise_text(row.get(field))
        accepted = None if value is None else value == "converged_branch"
        return value, accepted, field, _D09_STATUS_POLICY
    if dataset_id == D08_DATASET_ID:
        field = "source_converged"
        value = _normalise_text(row.get(field))
        if value is None:
            accepted = None
        elif value == "true":
            accepted = True
        elif value == "false":
            accepted = False
        else:
            accepted = None
        return value, accepted, field, _D08_STATUS_POLICY
    return None, None, None, None


def _expected_quadrature(dataset_id: str, lattice: str) -> str | None:
    if dataset_id == D09_DATASET_ID:
        return {
            "bethe": "bethe_semicircle",
            "square": "continuum_elliptic_dos",
        }.get(lattice)
    if dataset_id == D08_DATASET_ID:
        return {
            "bethe": "bethe_semicircle_closed_form",
            "square": "uniform_kmesh",
        }.get(lattice)
    return None


def _quadrature_status(value: str | None, expected: str | None) -> str:
    if value is None or expected is None:
        return "unknown"
    return "matches" if value == expected else "mismatch"


def _catalog_sort_key(
    dataset_id: str, row: Mapping[str, Any]
) -> tuple[Any, ...]:
    return (
        _normalise_lattice(row.get("lattice")),
        _normalise_m_g(row.get("m_g")),
        _normalise_float(row.get("t_over_d")),
        _normalise_float(row.get("u_over_d")),
        _normalise_text(row.get("solution_family")) or "",
        _normalise_text(row.get("continuation_direction")) or "",
        _normalise_text(row.get("point_id")) or "",
        dataset_id,
    )


def _normalise_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text == "null":
        return None
    return text


def _normalise_lattice(value: Any) -> str:
    text = _normalise_text(value)
    return "" if text is None else text.lower()


def _normalise_m_g(value: Any) -> int:
    if value is None or value == "":
        return -1
    try:
        return int(value)
    except (TypeError, ValueError):
        return -1


def _normalise_float(value: Any) -> float:
    if value is None or value == "":
        return float("inf")
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("inf")
