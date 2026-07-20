"""Assemble the atlas payload from registered datasets.

The payload (`gdmft.atlas.payload.v1`) is a single JSON document embedded in
the built HTML: manifest-derived metadata, column-compressed point tables,
reference tables (gem, DMFT-ED, NRG, professor gGA, CTQMC), build-time
derived diagnostics, and small evidence extracts. Every byte traces back to
a registered artifact.
"""

from __future__ import annotations

import base64
import gzip
import json
import math
from pathlib import Path
from typing import Any

from gdmft.data import (
    find_artifact,
    iter_point_rows,
    load_manifest,
    verify_artifacts,
)

from .catalog import catalog_policy_metadata, classify_point
from .columns import (
    ATLAS_COLUMNS,
    ENERGY_PAIRS,
    assert_header_locked,
)
from .derive import derive_dataset
from .dos import square_dos_table
from .poles import extract_pole_table
from .registry import RegistryEntry, load_registry

PAYLOAD_SCHEMA = "gdmft.atlas.payload.v1"
POINT_SCHEMA = "gdmft.point.v1"
REFERENCE_SCHEMA = "gdmft.reference.v1"

DISCLAIMER = (
    "Default sources follow the versioned primary-route catalog. Numerical "
    "acceptance is not physical or thermodynamic selection. U*, spinodal, "
    "coexistence, and branch-split views are provisional attempt diagnostics "
    "and must not be quoted as phase boundaries."
)

GATE_COLUMNS = (
    "solver_succeeded",
    "equations_accepted",
    "density_consistent",
    "physical_guards_clear",
    "bounds_clear",
    "continuity_passed",
    "physically_admissible",
    "selected",
)

EVIDENCE_TABLES = (
    # (artifact path, payload key, numeric fields)
    ("evidence/claim_ledger.csv", "claim_ledger", set()),
    (
        "evidence/unresolved_conditions_v2.csv",
        "unresolved",
        {"U_over_D", "T_over_D", "Z_pole", "resnorm"},
    ),
    (
        "evidence/mg1_bound_expansion.csv",
        "mg1_bound",
        {
            "U_over_D",
            "T_over_D",
            "Z_pole_bare_default",
            "Z_pole_bare_expanded",
            "rel_dZ_bare",
            "Z_R_default",
            "Z_R_expanded",
            "rel_dZ_R",
            "D_default",
            "D_expanded",
            "rel_dD",
            "rel_dOmega",
        },
    ),
    ("evidence/coverage_after_v2.csv", "coverage_after", set()),
    ("evidence/stage3_audit_v2.csv", "stage3_audit", set()),
)

PAIRING_FIELDS = (
    "cell",
    "bare_attempt_id",
    "U_over_D",
    "T_over_D",
    "branch",
    "Z_bare",
    "Z_converted",
    "Z_reopt",
    "basin_bare",
    "basin_reopt",
    "bound_limited",
    "dOmega_over_D",
    "dZ",
    "dZ_convert",
    "different_basin",
    "floor_limited",
    "resnorm_reopt",
)
PAIRING_NUMERIC = {
    "U_over_D",
    "T_over_D",
    "Z_bare",
    "Z_converted",
    "Z_reopt",
    "dOmega_over_D",
    "dZ",
    "dZ_convert",
    "resnorm_reopt",
}

ED_V2_FIELDS = (
    "Nb",
    "U_over_D",
    "route",
    "Z",
    "Z_single_point",
    "Z_converged",
    "Z_by_npts",
    "docc",
    "ekin",
    "etot",
    "n_imp",
    "chi2_normalized",
    "scipy_cost_half",
    "chi2_common_norm",
    "fit_rel_rms",
    "dDelta",
    "iters",
    "fixed_point_converged",
    "fit_optimizer_converged",
    "bath_approximation_quality",
    "Z_estimator_converged",
    "accuracy_qualified",
    "accepted",
    "temperature_semantics",
    "T_over_D",
    "bath_fit_beta",
    "eps",
    "V",
    "wall",
    "direction",
    "code_commit",
    "dirty",
)
ED_V2_NUMERIC = {
    "Nb",
    "U_over_D",
    "Z",
    "Z_single_point",
    "docc",
    "ekin",
    "etot",
    "n_imp",
    "chi2_normalized",
    "scipy_cost_half",
    "chi2_common_norm",
    "fit_rel_rms",
    "dDelta",
    "iters",
    "T_over_D",
    "bath_fit_beta",
    "wall",
}
ED_V2_FLAGS = {
    "Z_converged",
    "fixed_point_converged",
    "fit_optimizer_converged",
    "Z_estimator_converged",
    "accuracy_qualified",
    "accepted",
}
ED_V2_LISTS = {"eps", "V"}

NRG_FIELDS = (
    "u_over_d",
    "t_over_d",
    "double_occupancy",
    "kinetic_energy_over_d",
    "potential_energy_over_d",
    "total_energy_over_d",
)
NRG_NUMERIC = set(NRG_FIELDS)
PROF_GGA_FIELDS = (
    "budget",
    "t_over_d",
    "u_over_d",
    "double_occupancy",
    "total_energy_raw",
)
PROF_GGA_NUMERIC = set(PROF_GGA_FIELDS)
CTQMC_FIELDS = (
    "method",
    "budget",
    "t_over_d",
    "u_over_d",
    "branch",
    "z",
    "double_occupancy",
    "kinetic_energy_over_d",
    "total_energy_over_d",
)
CTQMC_NUMERIC = {
    "budget",
    "t_over_d",
    "u_over_d",
    "z",
    "double_occupancy",
    "kinetic_energy_over_d",
    "total_energy_over_d",
}
ED_V1_FIELDS = (
    "lattice",
    "N_b",
    "U_over_D",
    "direction",
    "temperature_semantics",
    "T_over_D",
    "bath_fit_beta",
    "llk_role",
    "Z",
    "docc",
    "ekin",
    "etot",
    "n_imp",
    "fit_cost_half_chi2",
    "dDelta",
    "iters",
    "converged",
    "bath_optimizer",
)
ED_V1_NUMERIC = {
    "N_b",
    "U_over_D",
    "T_over_D",
    "bath_fit_beta",
    "Z",
    "docc",
    "ekin",
    "etot",
    "n_imp",
    "fit_cost_half_chi2",
    "dDelta",
    "iters",
    "converged",
}


class PayloadError(ValueError):
    """Raised when registered data cannot be assembled into a payload."""


def round6(value: float) -> float:
    """Round to 6 significant digits (the payload float precision)."""
    if value == 0 or not math.isfinite(value):
        return value
    return float(f"{value:.6g}")


def round_floats(node: Any) -> Any:
    """Recursively round every float; non-finite values become null.

    JSON has no NaN/Infinity — a stray one would make the embedded payload
    unparseable in the browser, so they are nulled here and the dumps are
    run with allow_nan=False as the hard enforcement.
    """
    if isinstance(node, bool):
        return node
    if isinstance(node, float):
        return round6(node) if math.isfinite(node) else None
    if isinstance(node, list):
        return [round_floats(item) for item in node]
    if isinstance(node, dict):
        return {key: round_floats(value) for key, value in node.items()}
    return node


def parse_number(
    value: str | None, context: str, nonfinite: dict[str, int]
) -> float | None:
    if value is None:
        return None
    number = float(value)
    if not math.isfinite(number):
        nonfinite[context] = nonfinite.get(context, 0) + 1
        return None
    return number


def pack_table(
    rows: list[dict[str, str | None]],
    fields: tuple[str, ...],
    numeric: set[str],
) -> dict[str, Any]:
    """Column-order a list of row dicts into {fields, rows}."""
    packed: list[list[Any]] = []
    for row in rows:
        record: list[Any] = []
        for field in fields:
            value = row.get(field)
            if value is None:
                record.append(None)
            elif field in numeric:
                record.append(float(value))
            else:
                record.append(value)
        packed.append(record)
    return {"fields": list(fields), "rows": packed}


def _require_table_fields(
    rows: list[dict[str, str | None]],
    fields: tuple[str, ...],
    context: str,
) -> None:
    if not rows:
        raise PayloadError(f"{context}: registered table is empty")
    missing = set(fields) - set(rows[0])
    if missing:
        raise PayloadError(
            f"{context}: registered table is missing fields {sorted(missing)}"
        )


def _binary_code(value: str | None, context: str) -> int | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"1", "true"}:
        return 1
    if normalized in {"0", "false"}:
        return 0
    raise PayloadError(f"{context}: expected a binary flag, found {value!r}")


def _number_list(value: str | None, context: str) -> list[float] | None:
    if value is None:
        return None
    try:
        return [float(part) for part in value.split(";")]
    except ValueError as exc:
        raise PayloadError(
            f"{context}: invalid semicolon-separated numeric list {value!r}"
        ) from exc


def _z_by_npts(value: str | None, context: str) -> list[list[float]] | None:
    """Decode ``n:Z;n:Z`` as ordered ``[[n, Z], ...]`` pairs."""
    if value is None:
        return None
    pairs: list[list[float]] = []
    try:
        for part in value.split(";"):
            n_points, z_value = part.split(":", 1)
            pairs.append([int(n_points), float(z_value)])
    except ValueError as exc:
        raise PayloadError(
            f"{context}: invalid Z-by-point-count trace {value!r}"
        ) from exc
    return pairs


def pack_ed_v2(rows: list[dict[str, str | None]]) -> dict[str, Any]:
    """Pack the complete D09 accepted ED view without flattening arrays."""
    _require_table_fields(rows, ED_V2_FIELDS, "D09 ed_accepted.csv")
    packed: list[list[Any]] = []
    for row_number, row in enumerate(rows, start=2):
        record: list[Any] = []
        for field in ED_V2_FIELDS:
            value = row[field]
            context = f"D09 ed_accepted.csv line {row_number} field {field}"
            if field in ED_V2_NUMERIC:
                record.append(None if value is None else float(value))
            elif field in ED_V2_FLAGS:
                record.append(_binary_code(value, context))
            elif field in ED_V2_LISTS:
                record.append(_number_list(value, context))
            elif field == "Z_by_npts":
                record.append(_z_by_npts(value, context))
            else:
                record.append(value)
        packed.append(record)
    return {"fields": list(ED_V2_FIELDS), "rows": packed}


def read_table(path: Path) -> list[dict[str, str | None]]:
    return list(iter_point_rows(path))


def _manifest_source(
    dataset_id: str,
    manifest: dict[str, Any],
    artifact: dict[str, Any],
) -> dict[str, Any]:
    """Carry enough manifest provenance to audit one embedded table."""
    return {
        "dataset": dataset_id,
        "dataset_version": manifest["version"],
        "data_stage": manifest["data_stage"],
        "release_status": manifest["release_status"],
        "path": artifact["path"],
        "sha256": artifact["sha256"],
        "role": artifact["role"],
        "provenance": manifest["provenance"],
        "external_sources": manifest.get("external_sources", []),
    }


def _unique_numbers(
    rows: list[dict[str, str | None]], field: str
) -> list[float]:
    values: set[float] = set()
    for row in rows:
        value = row.get(field)
        if value is None:
            continue
        number = float(value)
        if math.isfinite(number):
            values.add(number)
    return sorted(values)


def _unique_text(
    rows: list[dict[str, str | None]], field: str
) -> list[str]:
    return sorted(
        {value for row in rows if (value := row.get(field)) is not None}
    )


def _finite_counts(
    rows: list[dict[str, str | None]], fields: tuple[str, ...]
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for field in fields:
        count = 0
        for row in rows:
            value = row.get(field)
            if value is None:
                continue
            try:
                finite = math.isfinite(float(value))
            except ValueError:
                finite = False
            count += int(finite)
        counts[field] = count
    return counts


def _tristate_code(value: str | None, context: str) -> int:
    if value is None:
        return 2
    if value == "true":
        return 1
    if value == "false":
        return 0
    raise PayloadError(f"{context}: invalid gate value {value!r}")


def encode_point_dataset(
    entry: RegistryEntry,
    manifest: dict[str, Any],
    rows: list[dict[str, str | None]],
    report: list[str],
) -> dict[str, Any]:
    """Column-compress one gdmft.point.v1 table."""
    dataset_id = entry.id
    n = len(rows)
    nonfinite: dict[str, int] = {}

    # Per-lattice grids from the full attempt set.
    lattices = sorted({row["lattice"] for row in rows if row["lattice"]})
    grids: dict[str, dict[str, list[float]]] = {}
    for lattice in lattices:
        u_values = sorted(
            {
                float(row["u_over_d"])
                for row in rows
                if row["lattice"] == lattice
            }
        )
        t_values = sorted(
            {
                float(row["t_over_d"])
                for row in rows
                if row["lattice"] == lattice
            }
        )
        grids[lattice] = {"u": u_values, "t": t_values}
    u_index = {
        lattice: {u: i for i, u in enumerate(grids[lattice]["u"])}
        for lattice in lattices
    }
    t_index = {
        lattice: {t: i for i, t in enumerate(grids[lattice]["t"])}
        for lattice in lattices
    }

    # Raw half bandwidth per lattice: column when present, else manifest.
    raw_d: dict[str, float] = {}
    for row in rows:
        value = row["raw_half_bandwidth"]
        if value is None:
            continue
        lattice = row["lattice"]
        number = float(value)
        if lattice in raw_d and raw_d[lattice] != number:
            raise PayloadError(
                f"{dataset_id}: inconsistent raw_half_bandwidth for {lattice}"
            )
        raw_d[lattice] = number
    manifest_raw_d = (manifest.get("extensions") or {}).get(
        "raw_half_bandwidth", {}
    )
    for lattice in lattices:
        if lattice not in raw_d:
            if lattice not in manifest_raw_d:
                raise PayloadError(
                    f"{dataset_id}: no raw_half_bandwidth for {lattice} in "
                    "column or manifest extensions"
                )
            raw_d[lattice] = float(manifest_raw_d[lattice])
        elif lattice in manifest_raw_d and float(
            manifest_raw_d[lattice]
        ) != raw_d[lattice]:
            raise PayloadError(
                f"{dataset_id}: column and manifest raw_half_bandwidth "
                f"disagree for {lattice}"
            )

    cols: dict[str, Any] = {}
    constants: dict[str, Any] = {}
    cols_dropped: list[str] = []
    dicts: dict[str, list[str]] = {}

    cols["iu"] = [u_index[row["lattice"]][float(row["u_over_d"])] for row in rows]
    cols["it"] = [t_index[row["lattice"]][float(row["t_over_d"])] for row in rows]

    for spec in ATLAS_COLUMNS:
        values = [row[spec.csv_name] for row in rows]
        non_null = [value for value in values if value is not None]
        if not non_null:
            cols_dropped.append(spec.csv_name)
            continue
        if spec.kind == "categorical":
            unique = sorted(set(non_null))
            if len(unique) == 1 and len(non_null) == n:
                constants[spec.key] = unique[0]
                continue
            code = {value: i for i, value in enumerate(unique)}
            dicts[spec.key] = unique
            cols[spec.key] = [
                None if value is None else code[value] for value in values
            ]
        elif spec.kind == "tristate":
            encoded = [
                _tristate_code(value, f"{dataset_id}.{spec.csv_name}")
                for value in values
            ]
            if len(set(encoded)) == 1 and encoded[0] != 2:
                constants[spec.key] = encoded[0]
                continue
            cols[spec.key] = encoded
        elif spec.kind == "number":
            numbers = [
                parse_number(value, f"{dataset_id}.{spec.csv_name}", nonfinite)
                for value in values
            ]
            finite = [number for number in numbers if number is not None]
            if not finite:
                cols_dropped.append(spec.csv_name)
                continue
            rounded = [
                None if number is None else round6(number) for number in numbers
            ]
            unique = set(rounded)
            if len(unique) == 1 and None not in unique:
                constants[spec.key] = rounded[0]
                continue
            cols[spec.key] = rounded
        elif spec.kind == "text":
            cols[spec.key] = ["" if value is None else value for value in values]
        else:  # pragma: no cover - spec kinds are closed
            raise PayloadError(f"unknown column kind {spec.kind}")

    # Energies: prefer *_over_d, backfill from raw / raw_d.
    for raw_name, over_d_name, key in ENERGY_PAIRS:
        values: list[float | None] = []
        backfilled = 0
        for row in rows:
            over_d = parse_number(
                row[over_d_name], f"{dataset_id}.{over_d_name}", nonfinite
            )
            if over_d is None:
                raw = parse_number(
                    row[raw_name], f"{dataset_id}.{raw_name}", nonfinite
                )
                if raw is not None:
                    over_d = raw / raw_d[row["lattice"]]
                    backfilled += 1
            values.append(None if over_d is None else round6(over_d))
        if backfilled:
            report.append(
                f"{dataset_id}: {key} backfilled from raw values for "
                f"{backfilled} rows"
            )
        if any(value is not None for value in values):
            cols[key] = values
        else:
            cols_dropped.append(over_d_name)

    # canonical_lambda_reduced is recorded raw; normalize per lattice.
    lam_values: list[float | None] = []
    for row in rows:
        lam = parse_number(
            row["canonical_lambda_reduced"],
            f"{dataset_id}.canonical_lambda_reduced",
            nonfinite,
        )
        lam_values.append(
            None if lam is None else round6(lam / raw_d[row["lattice"]])
        )
    if any(value is not None for value in lam_values):
        cols["lam_red_d"] = lam_values
    else:
        cols_dropped.append("canonical_lambda_reduced")

    # Parent resolution.
    row_by_pid = {row["point_id"]: i for i, row in enumerate(rows)}
    parents: list[int | None] = []
    unresolved_parents = 0
    for row in rows:
        parent_id = row["source_parent_point_id"]
        if parent_id is None:
            parents.append(None)
        elif parent_id in row_by_pid:
            parents.append(row_by_pid[parent_id])
        else:
            parents.append(None)
            unresolved_parents += 1
    if any(parent is not None for parent in parents):
        cols["parent"] = parents
    if unresolved_parents:
        report.append(
            f"{dataset_id}: {unresolved_parents} parent point ids do not "
            "resolve to a row in the same table"
        )

    for context, count in sorted(nonfinite.items()):
        report.append(f"{context}: {count} non-finite values treated as null")

    gates = {
        gate: {
            "true": sum(1 for row in rows if row[gate] == "true"),
            "false": sum(1 for row in rows if row[gate] == "false"),
            "null": sum(1 for row in rows if row[gate] is None),
        }
        for gate in GATE_COLUMNS
    }
    nonnull = {
        name: sum(1 for row in rows if row[name] is not None)
        for name in rows[0]
    }

    return {
        "n": n,
        "title": manifest.get("title", dataset_id),
        "grids": grids,
        "raw_d": raw_d,
        "dicts": dicts,
        "constants": constants,
        "cols": cols,
        "cols_dropped": sorted(cols_dropped),
        "gates": gates,
        "nonnull": nonnull,
    }


def encode_catalog_dataset(
    dataset_id: str, rows: list[dict[str, str | None]]
) -> dict[str, Any]:
    """Compact route/status annotations for one immutable attempt table."""
    role_counts: dict[str, int] = {}
    quadrature_counts: dict[str, int] = {}
    route_counts: dict[str, dict[str, int]] = {}
    default_rows: list[int] = []
    for index, row in enumerate(rows):
        decision = classify_point(dataset_id, row)
        role_counts[decision.purpose] = role_counts.get(decision.purpose, 0) + 1
        quadrature_counts[decision.quadrature_status] = (
            quadrature_counts.get(decision.quadrature_status, 0) + 1
        )
        if decision.route_id is not None:
            route = route_counts.setdefault(
                decision.route_id,
                {"attempts": 0, "source_status_accepted": 0, "default_rows": 0},
            )
            route["attempts"] += 1
            if decision.status_accepted is True:
                route["source_status_accepted"] += 1
            if decision.include_default_physics:
                route["default_rows"] += 1
        if decision.include_default_physics:
            default_rows.append(index)
    return {
        "role_counts": dict(sorted(role_counts.items())),
        "quadrature_counts": dict(sorted(quadrature_counts.items())),
        "route_counts": dict(sorted(route_counts.items())),
        "default_rows": default_rows,
        "default_row_count": len(default_rows),
    }


def thin_rows_for_derive(
    dataset_id: str,
    rows: list[dict[str, str | None]],
    raw_d: dict[str, float],
    report: list[str],
) -> list[dict[str, Any]]:
    """Reduce point rows to what derive_dataset needs, with the right
    converged predicate for this dataset generation."""
    has_category = any(row["source_category"] is not None for row in rows)
    predicate = "source_category" if has_category else "source_converged"
    report.append(
        f"{dataset_id}: converged predicate = {predicate}"
    )
    thin: list[dict[str, Any]] = []
    for i, row in enumerate(rows):
        if has_category:
            converged = row["source_category"] == "converged_branch"
        else:
            converged = row["source_converged"] == "true"
        omega = row["grand_potential_over_d"]
        if omega is None and row["grand_potential"] is not None:
            omega = str(
                float(row["grand_potential"]) / raw_d[row["lattice"]]
            )
        thin.append(
            {
                "i": i,
                "lattice": row["lattice"],
                "m_g": int(row["m_g"]),
                "gauge": row["gauge"],
                "family": row["solution_family"],
                "u": float(row["u_over_d"]),
                "t": float(row["t_over_d"]),
                "z": (
                    None
                    if row["quasiparticle_weight_pole"] is None
                    else float(row["quasiparticle_weight_pole"])
                ),
                "omega_d": None if omega is None else float(omega),
                "resnorm": (
                    None
                    if row["residual_norm"] is None
                    else float(row["residual_norm"])
                ),
                "converged": converged,
            }
        )
    return thin


def encode_gem_reference(
    entry: RegistryEntry,
    manifest: dict[str, Any],
    rows: list[dict[str, str | None]],
    anchor_id: str,
    anchor_grids: dict[str, dict[str, list[float]]],
    report: list[str],
) -> dict[str, Any]:
    """Encode the gem reference table, index-anchored to the scan grids."""
    dataset_id = entry.id
    nonfinite: dict[str, int] = {}
    u_index = {
        lattice: {u: i for i, u in enumerate(anchor_grids[lattice]["u"])}
        for lattice in anchor_grids
    }
    t_index = {
        lattice: {t: i for i, t in enumerate(anchor_grids[lattice]["t"])}
        for lattice in anchor_grids
    }

    def parse_pole_list(value: str | None) -> list[float] | None:
        if value is None:
            return None
        return [round6(float(part)) for part in value.split(";")]

    n = len(rows)
    cols: dict[str, Any] = {
        "lattice": [],
        "budget": [],
        "iu": [],
        "it": [],
        "direction": [],
        "z_slope": [],
        "z_mats": [],
        "docc": [],
        "ekin_d": [],
        "etot_d": [],
        "sumr2": [],
        "sig_lin": [],
        "converged": [],
        "crashed": [],
        "lam": [],
        "r2": [],
        "sig_p": [],
        "sig_w": [],
    }
    lattice_values = sorted({row["lattice"] for row in rows})
    lattice_code = {value: i for i, value in enumerate(lattice_values)}
    direction_values = sorted({row["direction"] for row in rows})
    direction_code = {value: i for i, value in enumerate(direction_values)}

    keys_seen: dict[tuple[str, int, str], set[tuple[float, float]]] = {}
    for row in rows:
        lattice = row["lattice"]
        u = float(row["u_over_d"])
        t = float(row["t_over_d"])
        if lattice not in u_index or u not in u_index[lattice] or (
            t not in t_index[lattice]
        ):
            raise PayloadError(
                f"{dataset_id}: point (lattice={lattice}, U/D={u}, T/D={t}) "
                f"is outside the {anchor_id} grid it is declared matched to"
            )
        budget = int(row["bath_budget"])
        keys_seen.setdefault(
            (lattice, budget, row["direction"]), set()
        ).add((u, t))
        cols["lattice"].append(lattice_code[lattice])
        cols["budget"].append(budget)
        cols["iu"].append(u_index[lattice][u])
        cols["it"].append(t_index[lattice][t])
        cols["direction"].append(direction_code[row["direction"]])
        for key, name in (
            ("z_slope", "quasiparticle_weight_slope"),
            ("z_mats", "quasiparticle_weight_matsubara"),
            ("docc", "double_occupancy"),
            ("ekin_d", "kinetic_energy_over_d"),
            ("etot_d", "total_energy_over_d"),
            ("sumr2", "sum_r_squared"),
            ("sig_lin", "self_energy_linear_term"),
        ):
            number = parse_number(
                row[name], f"{dataset_id}.{name}", nonfinite
            )
            cols[key].append(None if number is None else round6(number))
        cols["converged"].append(1 if row["converged"] == "true" else 0)
        cols["crashed"].append(1 if row["crashed"] == "true" else 0)
        cols["lam"].append(parse_pole_list(row["mode_energies"]))
        cols["r2"].append(parse_pole_list(row["mode_weights"]))
        cols["sig_p"].append(parse_pole_list(row["self_energy_pole_positions"]))
        cols["sig_w"].append(parse_pole_list(row["self_energy_pole_weights"]))

    # The whole point of the reference: every anchor key is covered, both
    # budgets, both sweep directions. Grid drift must fail the build.
    coverage: dict[str, Any] = {}
    for lattice in anchor_grids:
        anchor_keys = {
            (u, t)
            for u in anchor_grids[lattice]["u"]
            for t in anchor_grids[lattice]["t"]
        }
        for budget in sorted({int(row["bath_budget"]) for row in rows}):
            for direction in direction_values:
                seen = keys_seen.get((lattice, budget, direction), set())
                missing = anchor_keys - seen
                if missing:
                    raise PayloadError(
                        f"{dataset_id}: {lattice} B={budget} {direction} is "
                        f"missing {len(missing)} of {len(anchor_keys)} "
                        f"{anchor_id} grid keys (first: "
                        f"{sorted(missing)[:3]})"
                    )
                coverage[f"{lattice}_b{budget}_{direction}"] = len(seen)

    for context, count in sorted(nonfinite.items()):
        report.append(f"{context}: {count} non-finite values treated as null")

    caveats = (manifest.get("extensions") or {}).get("caveats", [])
    return {
        "n": n,
        "title": manifest.get("title", dataset_id),
        "anchored_to": anchor_id,
        "dicts": {"lattice": lattice_values, "direction": direction_values},
        "cols": cols,
        "coverage": coverage,
        "caveats": caveats,
    }


def load_evidence_tables(
    manifest: dict[str, Any], root: Path
) -> dict[str, Any]:
    """Extract the registered evidence CSVs the QA/overview tabs render."""
    evidence: dict[str, Any] = {}
    for artifact_path, key, numeric in EVIDENCE_TABLES:
        artifact = find_artifact(manifest, path=artifact_path)
        rows = read_table(root / artifact["path"])
        fields = tuple(rows[0].keys()) if rows else ()
        evidence[key] = pack_table(rows, fields, numeric)
        evidence[key]["source"] = {
            "path": artifact["path"],
            "sha256": artifact["sha256"],
        }
    pairing = find_artifact(manifest, path="evidence/bare_R_pairing.csv")
    pairing_rows = read_table(root / pairing["path"])
    missing = set(PAIRING_FIELDS) - set(pairing_rows[0].keys())
    if missing:
        raise PayloadError(
            f"bare_R_pairing.csv is missing expected fields {sorted(missing)}"
        )
    evidence["bare_r_pairing"] = pack_table(
        pairing_rows, PAIRING_FIELDS, PAIRING_NUMERIC
    )
    evidence["bare_r_pairing"]["source"] = {
        "path": pairing["path"],
        "sha256": pairing["sha256"],
    }
    return evidence


def load_ed_references(
    manifests: dict[str, tuple[RegistryEntry, dict[str, Any], Path]],
) -> dict[str, Any]:
    """DMFT-ED evidence, with current D09 and legacy D08 kept separate."""
    ed: dict[str, Any] = {
        "current_key": "v2",
        "legacy_keys": ["v1_legacy"],
    }
    scan = manifests.get("single-site.scan-matrix-v2")
    if scan is not None:
        _, manifest, root = scan
        artifact = find_artifact(manifest, path="evidence/ed/ed_accepted.csv")
        rows = read_table(root / artifact["path"])
        protocol_artifact = find_artifact(
            manifest, path="evidence/ed/ed_llk_protocol.json"
        )
        protocol = json.loads(
            (root / protocol_artifact["path"]).read_text(encoding="utf-8")
        )
        ed["v2"] = pack_ed_v2(rows)
        ed["v2"].update(
            {
                "n": len(rows),
                "status": "current D09 validation evidence",
                "lattice": "bethe",
                "source": _manifest_source(
                    "single-site.scan-matrix-v2", manifest, artifact
                ),
                "protocol": protocol,
                "protocol_source": _manifest_source(
                    "single-site.scan-matrix-v2",
                    manifest,
                    protocol_artifact,
                ),
                "availability": {
                    "rows": len(rows),
                    "lattices": ["bethe"],
                    "bath_budgets": [
                        int(value) for value in _unique_numbers(rows, "Nb")
                    ],
                    "u_over_d": _unique_numbers(rows, "U_over_D"),
                    "directions": _unique_text(rows, "direction"),
                    "temperature_semantics": _unique_text(
                        rows, "temperature_semantics"
                    ),
                    "physical_t_over_d": _unique_numbers(rows, "T_over_D"),
                    "bath_fit_beta": _unique_numbers(rows, "bath_fit_beta"),
                    "accepted_rows": sum(
                        _binary_code(row["accepted"], "D09 accepted")
                        == 1
                        for row in rows
                    ),
                    "fixed_point_converged_rows": sum(
                        _binary_code(
                            row["fixed_point_converged"],
                            "D09 fixed_point_converged",
                        )
                        == 1
                        for row in rows
                    ),
                    "fit_optimizer_converged_rows": sum(
                        _binary_code(
                            row["fit_optimizer_converged"],
                            "D09 fit_optimizer_converged",
                        )
                        == 1
                        for row in rows
                    ),
                    "z_estimator_converged_rows": sum(
                        _binary_code(
                            row["Z_estimator_converged"],
                            "D09 Z_estimator_converged",
                        )
                        == 1
                        for row in rows
                    ),
                    "accuracy_qualified_rows": sum(
                        _binary_code(
                            row["accuracy_qualified"],
                            "D09 accuracy_qualified",
                        )
                        == 1
                        for row in rows
                    ),
                    "finite_temperature_join": False,
                },
                "field_semantics": {
                    "eps": "ordered bath-energy list",
                    "V": "ordered bath-hybridization list",
                    "Z_by_npts": "ordered [Matsubara-point count, Z] pairs",
                    "bath_fit_beta": (
                        "fictitious Matsubara bath-fit beta, not physical "
                        "inverse temperature"
                    ),
                    "accepted": "fixed_point_converged",
                    "accuracy_qualified": (
                        "fixed point, optimizer, bath tier, and Z estimator "
                        "all qualified"
                    ),
                },
            }
        )
    gauge = manifests.get("single-site.gauge-matrix-v1")
    if gauge is not None:
        _, manifest, root = gauge
        artifact = find_artifact(manifest, path="legacy/ed/accepted.csv")
        rows = read_table(root / artifact["path"])
        _require_table_fields(rows, ED_V1_FIELDS, "D08 legacy accepted.csv")
        ed["v1_legacy"] = pack_table(rows, ED_V1_FIELDS, ED_V1_NUMERIC)
        ed["v1_legacy"].update(
            {
                "n": len(rows),
                "status": "legacy D08 supporting evidence",
                "warning": (
                    "Historical prototype table; do not merge with the "
                    "current D09 LLK-protocol evidence."
                ),
                "source": _manifest_source(
                    "single-site.gauge-matrix-v1", manifest, artifact
                ),
                "availability": {
                    "rows": len(rows),
                    "lattices": _unique_text(rows, "lattice"),
                    "bath_budgets": [
                        int(value) for value in _unique_numbers(rows, "N_b")
                    ],
                    "u_over_d": _unique_numbers(rows, "U_over_D"),
                    "directions": _unique_text(rows, "direction"),
                    "temperature_semantics": _unique_text(
                        rows, "temperature_semantics"
                    ),
                    "physical_t_over_d": _unique_numbers(rows, "T_over_D"),
                    "bath_fit_beta": _unique_numbers(rows, "bath_fit_beta"),
                    "finite_temperature_join": False,
                },
            }
        )
    return ed


def _upstream_files(
    rows: list[dict[str, str | None]], prefix: str, *, exclude: str = ""
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for row in rows:
        path = row["path"] or ""
        if not path.startswith(prefix) or (exclude and exclude in path):
            continue
        selected.append(
            {
                "path": path,
                "sha256": row["sha256"],
                "bytes": int(row["bytes"] or 0),
            }
        )
    return selected


def load_benchmark_references(
    manifests: dict[str, tuple[RegistryEntry, dict[str, Any], Path]],
) -> dict[str, Any]:
    """Load dedicated benchmark source tables, never the historical merge."""
    registered = manifests.get("references.benchmarks-v1")
    if registered is None:
        return {}
    _, manifest, root = registered
    dataset_id = "references.benchmarks-v1"

    inventory_artifact = find_artifact(
        manifest, path="provenance/source_files.csv"
    )
    inventory_rows = read_table(root / inventory_artifact["path"])
    _require_table_fields(
        inventory_rows,
        ("path", "sha256", "bytes"),
        "benchmark source_files.csv",
    )

    nrg_artifact = find_artifact(manifest, path="tables/nrg_thermal.csv")
    nrg_rows = read_table(root / nrg_artifact["path"])
    _require_table_fields(nrg_rows, NRG_FIELDS, "nrg_thermal.csv")
    nrg = pack_table(nrg_rows, NRG_FIELDS, NRG_NUMERIC)
    nrg.update(
        {
            "n": len(nrg_rows),
            "title": "NRG thermal reference",
            "source": _manifest_source(dataset_id, manifest, nrg_artifact),
            "upstream_files": _upstream_files(
                inventory_rows,
                "refs/ref_data/",
                exclude="/ref_data2/",
            ),
            "availability": {
                "rows": len(nrg_rows),
                "lattices": ["bethe"],
                "u_over_d": _unique_numbers(nrg_rows, "u_over_d"),
                "t_over_d": _unique_numbers(nrg_rows, "t_over_d"),
                "finite_rows": _finite_counts(
                    nrg_rows,
                    (
                        "double_occupancy",
                        "kinetic_energy_over_d",
                        "potential_energy_over_d",
                        "total_energy_over_d",
                    ),
                ),
                "temperature_semantics": ["finite_temperature"],
                "source_of_truth": nrg_artifact["path"],
            },
        }
    )

    prof_artifact = find_artifact(
        manifest, path="tables/prof_gga_grids.csv"
    )
    prof_rows = read_table(root / prof_artifact["path"])
    _require_table_fields(prof_rows, PROF_GGA_FIELDS, "prof_gga_grids.csv")
    professor_gga = pack_table(
        prof_rows, PROF_GGA_FIELDS, PROF_GGA_NUMERIC
    )
    professor_gga.update(
        {
            "n": len(prof_rows),
            "title": "Professor gGA grids",
            "source": _manifest_source(dataset_id, manifest, prof_artifact),
            "upstream_files": _upstream_files(
                inventory_rows, "refs/ref_data/ref_data2/"
            ),
            "availability": {
                "rows": len(prof_rows),
                "lattices": ["bethe"],
                "bath_budgets": [
                    int(value)
                    for value in _unique_numbers(prof_rows, "budget")
                ],
                "u_over_d": _unique_numbers(prof_rows, "u_over_d"),
                "t_over_d": _unique_numbers(prof_rows, "t_over_d"),
                "finite_rows": _finite_counts(
                    prof_rows,
                    ("double_occupancy", "total_energy_raw"),
                ),
                "temperature_semantics": ["finite_temperature"],
                "source_of_truth": prof_artifact["path"],
                "energy_convention": (
                    "stored total_energy_raw uses eps_loc=-U/2; "
                    "LLK-axis E_tot/D = total_energy_raw + U_over_D/2"
                ),
            },
        }
    )

    ctqmc_artifact = find_artifact(
        manifest, path="tables/ctqmc_anchors.csv"
    )
    ctqmc_rows = read_table(root / ctqmc_artifact["path"])
    _require_table_fields(ctqmc_rows, CTQMC_FIELDS, "ctqmc_anchors.csv")
    ctqmc = pack_table(ctqmc_rows, CTQMC_FIELDS, CTQMC_NUMERIC)
    ctqmc.update(
        {
            "n": len(ctqmc_rows),
            "title": "LLK CTQMC anchor",
            "source": _manifest_source(dataset_id, manifest, ctqmc_artifact),
            "availability": {
                "rows": len(ctqmc_rows),
                "lattices": ["bethe"],
                "methods": _unique_text(ctqmc_rows, "method"),
                "u_over_d": _unique_numbers(ctqmc_rows, "u_over_d"),
                "t_over_d": _unique_numbers(ctqmc_rows, "t_over_d"),
                "finite_rows": _finite_counts(
                    ctqmc_rows,
                    (
                        "z",
                        "double_occupancy",
                        "kinetic_energy_over_d",
                        "total_energy_over_d",
                    ),
                ),
                "temperature_semantics": ["finite_temperature"],
                "source_of_truth": ctqmc_artifact["path"],
            },
        }
    )

    return {
        "nrg": nrg,
        "professor_gga": professor_gga,
        "ctqmc": ctqmc,
    }


def build_payload(
    registry_path: str | Path,
    *,
    verify: bool = False,
    built_at: str,
    gdmft_version: str,
) -> dict[str, Any]:
    """Assemble the full payload from every registered dataset."""
    report: list[str] = []
    entries = load_registry(registry_path)
    manifests: dict[str, tuple[RegistryEntry, dict[str, Any], Path]] = {}
    for entry in entries:
        manifest = load_manifest(entry.manifest)
        root = entry.manifest.parent
        if verify:
            verify_artifacts(manifest, root)
        manifests[entry.id] = (entry, manifest, root)

    payload: dict[str, Any] = {
        "meta": {
            "atlas_schema": PAYLOAD_SCHEMA,
            "built_at": built_at,
            "gdmft_version": gdmft_version,
            "disclaimer": DISCLAIMER,
            "verified_checksums": verify,
            "datasets": [],
        },
        "datasets": {},
        "catalog": {
            "policy": catalog_policy_metadata(),
            "datasets": {},
            "default_physics_count": 0,
            "selection_status": "not applied",
        },
        "references": {},
        "derived": {
            "basis": {
                "kind": "attempt-level diagnostic",
                "source_filter": "source numerical convergence only",
                "thermodynamic_selection": "not applied",
                "physical_admissibility": "not established",
            },
            "branches": [],
            "ustar": [],
            "spinodals": [],
            "coex": [],
            "report": report,
        },
        "evidence": {},
    }

    point_ids: list[str] = []
    gem_entries: list[str] = []
    for dataset_id, (entry, manifest, _root) in manifests.items():
        schemas = {
            artifact.get("schema")
            for artifact in manifest["artifacts"]
        }
        payload["meta"]["datasets"].append(
            {
                "id": dataset_id,
                "title": manifest.get("title", dataset_id),
                "version": entry.version,
                "kind": manifest["dataset_kind"],
                "data_stage": entry.data_stage,
                "release_status": entry.release_status,
                "created_at": manifest.get("created_at"),
                "revision": manifest["provenance"]["revision"],
                "dirty": manifest["provenance"]["dirty"],
                "repository": manifest["provenance"]["repository"],
                "selection_status": (manifest.get("extensions") or {}).get(
                    "selection_status"
                ),
                "metadata_corrections": (manifest.get("extensions") or {}).get(
                    "metadata_corrections", []
                ),
                "external_sources": manifest.get("external_sources", []),
                "description": manifest.get("description", ""),
            }
        )
        if POINT_SCHEMA in schemas:
            point_ids.append(dataset_id)
        elif REFERENCE_SCHEMA in schemas:
            gem_entries.append(dataset_id)

    if not point_ids:
        raise PayloadError("no registered gdmft.point.v1 datasets found")

    for dataset_id in point_ids:
        entry, manifest, root = manifests[dataset_id]
        artifact = find_artifact(manifest, schema=POINT_SCHEMA)
        rows = read_table(root / artifact["path"])
        assert_header_locked(tuple(rows[0].keys()))
        expected_rows = artifact.get("rows")
        if expected_rows is not None and len(rows) != expected_rows:
            raise PayloadError(
                f"{dataset_id}: points.csv has {len(rows)} rows, manifest "
                f"says {expected_rows}"
            )
        bad_schema = {
            row["schema_version"] for row in rows
        } - {POINT_SCHEMA}
        if bad_schema:
            raise PayloadError(
                f"{dataset_id}: unexpected schema_version values {bad_schema}"
            )
        encoded = encode_point_dataset(entry, manifest, rows, report)
        catalog_dataset = encode_catalog_dataset(dataset_id, rows)
        payload["catalog"]["datasets"][dataset_id] = catalog_dataset
        payload["catalog"]["default_physics_count"] += catalog_dataset[
            "default_row_count"
        ]

        archives = [
            artifact
            for artifact in manifest["artifacts"]
            if artifact.get("role") == "lossless-raw-archive"
            and (
                artifact.get("path", "").endswith(".jsonl.gz")
                or artifact.get("path", "").endswith(".tar.gz")
            )
        ]
        if len(archives) != 1:
            raise PayloadError(
                f"{dataset_id}: expected one lossless raw archive, found "
                f"{[a.get('path') for a in archives]}"
            )
        archive = archives[0]
        point_ids = [row["point_id"] for row in rows]
        archive_file = root / archive["path"]
        if archive["path"].endswith(".jsonl.gz"):
            pole_table = extract_pole_table(
                archive_file, point_ids, kind="jsonl"
            )
        else:
            cells = set((manifest.get("grid") or {}).get("cells") or [])
            pole_table = extract_pole_table(
                archive_file, point_ids, kind="tar", cells=cells
            )
        counts = pole_table["counts"]
        report.append(
            f"{dataset_id}: poles for {counts['rows']} rows "
            f"({counts['reduced']} reduced, {counts['full']} full arrays, "
            f"{counts['h_from_R']} h-sector from canonical R view)"
        )
        encoded["poles"] = pole_table
        payload["datasets"][dataset_id] = encoded

        thin = thin_rows_for_derive(dataset_id, rows, encoded["raw_d"], report)
        derive_grids = {
            lattice: (grid["u"], grid["t"])
            for lattice, grid in encoded["grids"].items()
        }
        derived = derive_dataset(dataset_id, thin, derive_grids)
        payload["derived"]["branches"].extend(derived["branches"])
        payload["derived"]["ustar"].extend(derived["ustar"])
        payload["derived"]["spinodals"].extend(derived["spinodals"])
        payload["derived"]["coex"].extend(derived["coex"])
        report.extend(derived["report"])

    for dataset_id in gem_entries:
        entry, manifest, root = manifests[dataset_id]
        artifact = find_artifact(manifest, schema=REFERENCE_SCHEMA)
        rows = read_table(root / artifact["path"])
        anchor_id = (manifest.get("grid") or {}).get("matched_to")
        if anchor_id not in payload["datasets"]:
            raise PayloadError(
                f"{dataset_id}: declared matched_to {anchor_id!r} is not a "
                "registered point dataset"
            )
        payload["references"]["gem"] = encode_gem_reference(
            entry,
            manifest,
            rows,
            anchor_id,
            payload["datasets"][anchor_id]["grids"],
            report,
        )

    payload["references"]["ed"] = load_ed_references(manifests)
    payload["references"].update(load_benchmark_references(manifests))

    ed = payload["references"]["ed"]
    availability: dict[str, Any] = {}
    if "v2" in ed:
        availability["dmft_ed_d09"] = ed["v2"]["availability"]
    if "v1_legacy" in ed:
        availability["dmft_ed_d08_legacy"] = ed["v1_legacy"][
            "availability"
        ]
    for reference_key in ("nrg", "professor_gga", "ctqmc"):
        reference = payload["references"].get(reference_key)
        if reference is not None:
            availability[reference_key] = reference["availability"]
    payload["references"]["availability"] = availability
    gem = payload["references"].get("gem")
    benchmark_tables = [
        {
            "id": key,
            "row_count": payload["references"][key]["n"],
            "path": payload["references"][key]["source"]["path"],
        }
        for key in ("nrg", "professor_gga", "ctqmc")
        if key in payload["references"]
    ]
    payload["references"]["catalog"] = [
        {
            "dataset_id": "references.gem-gga-v1",
            "methods": ["gem/gGA"],
            "n": 0 if gem is None else gem["n"],
            "tables": [] if gem is None else [{"id": "points", "row_count": gem["n"]}],
            "availability": "matched finite-temperature reference rows loaded",
        },
        {
            "dataset_id": "references.benchmarks-v1",
            "methods": ["NRG", "professor gGA", "CTQMC"],
            "n": sum(table["row_count"] for table in benchmark_tables),
            "tables": benchmark_tables,
            "availability": (
                "dedicated source tables loaded; lossy compare_all view excluded"
            ),
        },
    ]

    reference_counts = {
        entry["dataset_id"]: entry["n"]
        for entry in payload["references"]["catalog"]
    }
    for dataset_meta in payload["meta"]["datasets"]:
        if dataset_meta["id"] in payload["datasets"]:
            dataset_meta["row_count"] = payload["datasets"][
                dataset_meta["id"]
            ]["n"]
        elif dataset_meta["id"] in reference_counts:
            dataset_meta["row_count"] = reference_counts[dataset_meta["id"]]

    dos_energies, dos_weights = square_dos_table()
    payload["dos"] = {
        "square": {
            "eps": dos_energies,
            "w": dos_weights,
            "convention": "D = 1, weights sum to 1, even midpoint grid",
        }
    }

    scan = manifests.get("single-site.scan-matrix-v2")
    if scan is not None:
        _, manifest, root = scan
        payload["evidence"] = load_evidence_tables(manifest, root)

    return round_floats(payload)


def encode_payload(
    payload: dict[str, Any], *, compress: bool = True
) -> tuple[str, dict[str, int]]:
    """Serialize the payload for embedding; returns (blob, size stats)."""
    raw = json.dumps(
        payload, separators=(",", ":"), sort_keys=True, allow_nan=False
    )
    stats = {"raw_json_bytes": len(raw.encode("utf-8"))}
    for section, value in payload.items():
        section_raw = json.dumps(
            value, separators=(",", ":"), sort_keys=True, allow_nan=False
        )
        stats[f"section_{section}_bytes"] = len(section_raw.encode("utf-8"))
    if not compress:
        stats["embedded_bytes"] = stats["raw_json_bytes"]
        return raw, stats
    packed = gzip.compress(raw.encode("utf-8"), 9, mtime=0)
    stats["gzip_bytes"] = len(packed)
    encoded = base64.b64encode(packed).decode("ascii")
    wrapped = "\n".join(
        encoded[i : i + 120] for i in range(0, len(encoded), 120)
    )
    stats["embedded_bytes"] = len(wrapped)
    return wrapped, stats
