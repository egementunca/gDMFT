"""Column specification mapping the point contract into the atlas payload.

`EXPECTED_CSV_COLUMNS` locks the exact 58-column `gdmft.point.v1` header this
atlas build understands. `ATLAS_COLUMNS` maps the generically-encoded columns;
`SPECIAL_COLUMNS` names the columns the payload builder transforms instead of
copying (grid indices, parent resolution, per-lattice constants, raw-unit
normalization). A dataset whose header differs fails the build loudly.
"""

from __future__ import annotations

from dataclasses import dataclass

EXPECTED_CSV_COLUMNS = (
    "schema_version",
    "run_id",
    "point_id",
    "lattice",
    "m_h",
    "m_g",
    "solution_family",
    "gauge",
    "solver",
    "u_over_d",
    "t_over_d",
    "solver_succeeded",
    "equations_accepted",
    "density_consistent",
    "physical_guards_clear",
    "bounds_clear",
    "continuity_passed",
    "physically_admissible",
    "selected",
    "selection_reason",
    "source_parent_point_id",
    "source_cell",
    "source_campaign",
    "source_evidence_type",
    "source_category",
    "source_converged",
    "source_floor_limited",
    "source_optimizer_active_bound",
    "continuation_direction",
    "basin",
    "lattice_quadrature",
    "quadrature_node_count",
    "dos_node_count",
    "raw_half_bandwidth",
    "u_raw",
    "t_raw",
    "quasiparticle_weight_pole",
    "quasiparticle_weight_from_r",
    "quasiparticle_weight_matsubara",
    "double_occupancy",
    "density",
    "grand_potential",
    "grand_potential_over_d",
    "kinetic_energy",
    "kinetic_energy_over_d",
    "potential_energy",
    "potential_energy_over_d",
    "total_energy",
    "total_energy_over_d",
    "residual_norm",
    "canonical_lambda_reduced",
    "canonical_r_reduced",
    "canonical_mode_count",
    "norm_error",
    "closure_error",
    "roundtrip_error",
    "source_code_revision",
    "source_dirty_state",
)


@dataclass(frozen=True)
class ColumnSpec:
    """One generically-encoded payload column."""

    csv_name: str
    key: str
    kind: str  # "categorical" | "tristate" | "number" | "text"


ATLAS_COLUMNS = (
    ColumnSpec("run_id", "run", "categorical"),
    ColumnSpec("point_id", "pid", "text"),
    ColumnSpec("lattice", "lattice", "categorical"),
    ColumnSpec("m_h", "m_h", "number"),
    ColumnSpec("m_g", "m_g", "number"),
    ColumnSpec("solution_family", "family", "categorical"),
    ColumnSpec("gauge", "gauge", "categorical"),
    ColumnSpec("solver", "solver", "categorical"),
    ColumnSpec("solver_succeeded", "ok", "tristate"),
    ColumnSpec("equations_accepted", "eq_ok", "tristate"),
    ColumnSpec("density_consistent", "density_ok", "tristate"),
    ColumnSpec("physical_guards_clear", "guards_ok", "tristate"),
    ColumnSpec("bounds_clear", "bounds_ok", "tristate"),
    ColumnSpec("continuity_passed", "cont_ok", "tristate"),
    ColumnSpec("physically_admissible", "admissible", "tristate"),
    ColumnSpec("selected", "selected", "tristate"),
    ColumnSpec("selection_reason", "sel_reason", "categorical"),
    ColumnSpec("source_cell", "cell", "categorical"),
    ColumnSpec("source_campaign", "campaign", "categorical"),
    ColumnSpec("source_evidence_type", "evidence_type", "categorical"),
    ColumnSpec("source_category", "category", "categorical"),
    ColumnSpec("source_converged", "src_converged", "tristate"),
    ColumnSpec("source_floor_limited", "floor_limited", "tristate"),
    ColumnSpec("source_optimizer_active_bound", "active_bound", "tristate"),
    ColumnSpec("continuation_direction", "direction", "categorical"),
    ColumnSpec("basin", "basin", "categorical"),
    ColumnSpec("lattice_quadrature", "quadrature", "categorical"),
    ColumnSpec("quadrature_node_count", "quad_nodes", "number"),
    ColumnSpec("dos_node_count", "dos_nodes", "number"),
    ColumnSpec("quasiparticle_weight_pole", "z_pole", "number"),
    ColumnSpec("quasiparticle_weight_from_r", "z_from_r", "number"),
    ColumnSpec("quasiparticle_weight_matsubara", "z_mats", "number"),
    ColumnSpec("double_occupancy", "docc", "number"),
    ColumnSpec("density", "density", "number"),
    ColumnSpec("residual_norm", "resnorm", "number"),
    ColumnSpec("canonical_r_reduced", "r_red", "number"),
    ColumnSpec("canonical_mode_count", "n_modes", "number"),
    ColumnSpec("norm_error", "norm_err", "number"),
    ColumnSpec("closure_error", "closure_err", "number"),
    ColumnSpec("roundtrip_error", "roundtrip_err", "number"),
    ColumnSpec("source_code_revision", "code_rev", "categorical"),
    ColumnSpec("source_dirty_state", "dirty", "categorical"),
)

# Columns the payload builder transforms instead of copying verbatim:
# - schema_version: asserted, then dropped
# - u_over_d / t_over_d: become per-lattice grid indices iu / it
# - u_raw / t_raw / raw_half_bandwidth: collapse to a per-lattice raw_d
#   constant (u_raw = u_over_d * raw_d)
# - source_parent_point_id: resolved to a row-index `parent` column
# - grand_potential / kinetic_energy / potential_energy / total_energy:
#   dropped in favour of their *_over_d twins (backfilled from raw / raw_d
#   when only the raw value is recorded)
# - grand_potential_over_d etc.: encoded as numbers omega_d / ekin_d /
#   epot_d / etot_d
# - canonical_lambda_reduced: recorded raw in the source tables; stored
#   normalized as lam_red_d = value / raw_d(lattice)
SPECIAL_COLUMNS = (
    "schema_version",
    "u_over_d",
    "t_over_d",
    "u_raw",
    "t_raw",
    "raw_half_bandwidth",
    "source_parent_point_id",
    "grand_potential",
    "grand_potential_over_d",
    "kinetic_energy",
    "kinetic_energy_over_d",
    "potential_energy",
    "potential_energy_over_d",
    "total_energy",
    "total_energy_over_d",
    "canonical_lambda_reduced",
)

ENERGY_PAIRS = (
    ("grand_potential", "grand_potential_over_d", "omega_d"),
    ("kinetic_energy", "kinetic_energy_over_d", "ekin_d"),
    ("potential_energy", "potential_energy_over_d", "epot_d"),
    ("total_energy", "total_energy_over_d", "etot_d"),
)


def assert_header_locked(columns: tuple[str, ...] | list[str]) -> None:
    """Fail loudly when a table header drifts from the locked contract."""
    if tuple(columns) != EXPECTED_CSV_COLUMNS:
        expected = set(EXPECTED_CSV_COLUMNS)
        found = set(columns)
        raise ValueError(
            "point table header drifted from the atlas contract; "
            f"missing={sorted(expected - found)} "
            f"unexpected={sorted(found - expected)} "
            f"(or column order changed)"
        )


def handled_csv_columns() -> set[str]:
    """Every CSV column the atlas build accounts for."""
    return {spec.csv_name for spec in ATLAS_COLUMNS} | set(SPECIAL_COLUMNS)
