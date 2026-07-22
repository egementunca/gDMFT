"""Build-time derived quantities for the atlas.

Everything here is a diagnostic computed from converged solver attempts —
NOT a thermodynamic branch selection (the datasets carry
`selection_status = "not applied"`). Renderers must keep that visible.

The physics-critical rules encoded here, verified against the datasets:
- `metal-up` and `metal-down` are U-axis segments of one metal branch
  (coarse low-U scanned down, fine high-U scanned up); they are spliced,
  never overlaid.
- `insul-down` overlaps the metal branch on the coexistence window.
- Exotic families (dark, coupled, symmetry-broken, ...) never participate
  in branch pairing.
- Continuity breaks (for example the bethe m_g=3 R-native T/D=0.02 collapse
  of Z from 0.16 to 0.03 across U/D 3.5 -> 3.55) are flagged and split the
  branch; they are never bridged or deleted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import median
from typing import Any

METAL_FAMILIES = frozenset({"metal-up", "metal-down"})
INSULATOR_FAMILIES = frozenset({"insul-down"})

# Continuity thresholds (documented in docs/atlas.md): a break is flagged
# between consecutive points of a branch when the jump in Z exceeds
# max(ABS_Z_JUMP, REL_Z_FACTOR * median jump) or the U gap exceeds
# REL_U_FACTOR * median spacing.
ABS_Z_JUMP = 0.1
REL_Z_FACTOR = 6.0
REL_U_FACTOR = 3.0

# Coexistence cell codes (mirrored in web/tabs/atlas.js).
COEX_NONE = 0
COEX_METAL_ONLY = 1
COEX_INSUL_ONLY = 2
COEX_BOTH_METAL_LOWER = 3
COEX_BOTH_INSUL_LOWER = 4
COEX_BOTH_OMEGA_UNKNOWN = 5
COEX_EXOTIC_ONLY = 6


def family_kind(family: str) -> str | None:
    """Map a solution family to its branch kind, or None for exotics."""
    if family in METAL_FAMILIES:
        return "metal"
    if family in INSULATOR_FAMILIES:
        return "insul"
    return None


@dataclass(frozen=True)
class BranchPoint:
    """One converged attempt participating in branch assembly."""

    row: int
    u: float
    z: float | None
    omega_d: float | None
    resnorm: float | None


@dataclass
class Branch:
    """An assembled branch: U-sorted points plus continuity break positions."""

    points: list[BranchPoint]
    breaks: list[int] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)

    def segments(self) -> list[tuple[int, int]]:
        """Maximal continuous index ranges [start, end] between breaks."""
        if not self.points:
            return []
        bounds = [-1, *self.breaks, len(self.points) - 1]
        return [
            (bounds[i] + 1, bounds[i + 1])
            for i in range(len(bounds) - 1)
            if bounds[i] + 1 <= bounds[i + 1]
        ]


def assemble_branch(points: list[BranchPoint], label: str) -> Branch:
    """Sort by U, resolve duplicate-U attempts, flag continuity breaks."""
    by_u: dict[float, BranchPoint] = {}
    anomalies: list[str] = []
    for point in sorted(
        points,
        key=lambda p: (
            p.u,
            p.resnorm if p.resnorm is not None else float("inf"),
        ),
    ):
        if point.u in by_u:
            anomalies.append(
                f"{label}: duplicate converged attempt at U/D={point.u:g}; "
                f"kept the lower-residual row"
            )
            continue
        by_u[point.u] = point
    ordered = [by_u[u] for u in sorted(by_u)]
    branch = Branch(points=ordered, anomalies=anomalies)
    branch.breaks = find_breaks(ordered, anomalies, label)
    return branch


def find_breaks(
    points: list[BranchPoint], anomalies: list[str], label: str
) -> list[int]:
    """Indices i such that continuity breaks between points[i] and [i+1]."""
    if len(points) < 2:
        return []
    z_jumps = [
        abs(b.z - a.z)
        for a, b in zip(points, points[1:], strict=False)
        if a.z is not None and b.z is not None
    ]
    u_gaps = [b.u - a.u for a, b in zip(points, points[1:], strict=False)]
    z_threshold = ABS_Z_JUMP
    if len(z_jumps) >= 4:
        z_threshold = max(ABS_Z_JUMP, REL_Z_FACTOR * median(z_jumps))
    u_threshold = REL_U_FACTOR * median(u_gaps) if len(u_gaps) >= 4 else None

    breaks: list[int] = []
    for i, (a, b) in enumerate(zip(points, points[1:], strict=False)):
        reason = None
        if a.z is not None and b.z is not None:
            jump = abs(b.z - a.z)
            if jump > z_threshold:
                reason = f"|dZ|={jump:.3g} > {z_threshold:.3g}"
        if reason is None and u_threshold is not None:
            gap = b.u - a.u
            if gap > u_threshold + 1e-12:
                reason = f"dU={gap:g} > {u_threshold:g} (support gap)"
        if reason is not None:
            breaks.append(i)
            anomalies.append(
                f"{label}: continuity break between U/D={a.u:g} and "
                f"{b.u:g} ({reason})"
            )
    return breaks


def omega_crossing(metal: Branch, insul: Branch) -> dict[str, Any]:
    """Locate U*(T) on support continuous in both candidate branches."""
    metal_omega = {
        p.u: p.omega_d for p in metal.points if p.omega_d is not None
    }
    insul_omega = {
        p.u: p.omega_d for p in insul.points if p.omega_d is not None
    }
    shared = sorted(set(metal_omega) & set(insul_omega))
    result: dict[str, Any] = {"n_overlap": len(shared)}
    if len(shared) < 2:
        result["status"] = "no_overlap" if not shared else "insufficient_overlap"
        return result

    def segment_map(branch: Branch) -> dict[float, int]:
        mapping: dict[float, int] = {}
        for segment_id, (start, end) in enumerate(branch.segments()):
            for point in branch.points[start : end + 1]:
                mapping[point.u] = segment_id
        return mapping

    metal_segment = segment_map(metal)
    insul_segment = segment_map(insul)
    delta = [metal_omega[u] - insul_omega[u] for u in shared]
    crossings: list[tuple[float, float, float, float]] = []
    continuous_intervals = 0
    for k in range(len(shared) - 1):
        d0, d1 = delta[k], delta[k + 1]
        if d0 == 0.0:
            crossings.append((shared[k], shared[k], d0, d0))
            continue
        continuous = (
            metal_segment.get(shared[k]) == metal_segment.get(shared[k + 1])
            and insul_segment.get(shared[k]) == insul_segment.get(shared[k + 1])
        )
        if not continuous:
            continue
        continuous_intervals += 1
        if (d0 < 0.0 < d1) or (d0 > 0.0 > d1):
            ustar = shared[k] + d0 * (shared[k + 1] - shared[k]) / (d0 - d1)
            crossings.append((ustar, shared[k], d0, d1))
    if delta[-1] == 0.0:
        crossings.append((shared[-1], shared[-1], delta[-1], delta[-1]))
    result["n_continuous_intervals"] = continuous_intervals

    upward = [c for c in crossings if c[2] <= 0.0 <= c[3]]
    if not upward:
        if all(d < 0.0 for d in delta):
            result["status"] = "metal_lower_everywhere"
        elif all(d > 0.0 for d in delta):
            result["status"] = "insul_lower_everywhere"
        elif metal.breaks or insul.breaks:
            result["status"] = "no_continuous_crossing"
        else:
            result["status"] = "no_upward_crossing"
        return result

    ustar, u_lo, d_lo, d_hi = upward[0]
    result["status"] = (
        "crossed" if len(upward) == 1 else "multiple_crossings"
    )
    result["ustar"] = ustar
    result["u_lo"] = u_lo
    result["u_hi"] = min(u for u in shared if u > u_lo) if u_lo < shared[-1] else u_lo
    result["d_omega_lo"] = d_lo
    result["d_omega_hi"] = d_hi
    # Coverage gate: a crossing interpolated across a hole in the grid
    # (bracket wider than one canonical coarse step) or from a thin
    # both-branch row is not a U* diagnostic — report the status but no
    # number, so overlays have nothing to draw until the data lands.
    if (result["u_hi"] - result["u_lo"]) > 0.06 or len(shared) < 10:
        result["status"] = "crossing_unresolved_sparse"
        del result["ustar"]
    return result


def metal_spinodal(
    branch: Branch, attempted_u: set[float]
) -> dict[str, Any] | None:
    """Uc2 proxy: where the low-U-connected metal segment ends."""
    segments = branch.segments()
    if not segments:
        return None
    start, end = segments[0]
    uc2 = branch.points[end].u
    beyond = any(u > uc2 + 1e-12 for u in attempted_u)
    return {"uc2": uc2, "uc2_kind": "interior_break" if beyond else "support_edge"}


def insulator_spinodal(
    branch: Branch, attempted_u: set[float]
) -> dict[str, Any] | None:
    """Uc1 proxy: where the high-U-connected insulator segment starts."""
    segments = branch.segments()
    if not segments:
        return None
    start, end = segments[-1]
    uc1 = branch.points[start].u
    below = any(u < uc1 - 1e-12 for u in attempted_u)
    return {"uc1": uc1, "uc1_kind": "interior_break" if below else "support_edge"}


def coexistence_code(
    has_metal: bool,
    has_insul: bool,
    has_exotic: bool,
    metal_omega: float | None,
    insul_omega: float | None,
) -> int:
    """Categorical phase-map code for one grid cell."""
    if has_metal and has_insul:
        if metal_omega is None or insul_omega is None:
            return COEX_BOTH_OMEGA_UNKNOWN
        if metal_omega <= insul_omega:
            return COEX_BOTH_METAL_LOWER
        return COEX_BOTH_INSUL_LOWER
    if has_metal:
        return COEX_METAL_ONLY
    if has_insul:
        return COEX_INSUL_ONLY
    if has_exotic:
        return COEX_EXOTIC_ONLY
    return COEX_NONE


def derive_dataset(
    dataset_id: str,
    rows: list[dict[str, Any]],
    grids: dict[str, tuple[list[float], list[float]]],
) -> dict[str, Any]:
    """Derive branches, U*(T), spinodal proxies, and coexistence maps.

    `rows` are thin per-attempt dicts: ``i`` (dataset row index), ``lattice``,
    ``m_g``, ``gauge``, ``family``, ``u``, ``t``, ``z``, ``omega_d``,
    ``resnorm``, ``converged``. `grids` maps lattice -> (sorted U values,
    sorted T values) covering every row of that lattice.
    """
    report: list[str] = []
    groups: dict[tuple[str, int, str], list[dict[str, Any]]] = {}
    unknown_families: set[str] = set()
    for row in rows:
        groups.setdefault(
            (row["lattice"], row["m_g"], row["gauge"]), []
        ).append(row)
        if row["converged"] and family_kind(row["family"]) is None:
            unknown_families.add(row["family"])
    for family in sorted(unknown_families):
        report.append(
            f"{dataset_id}: family {family!r} treated as exotic "
            "(excluded from branch pairing)"
        )

    branches_out: list[dict[str, Any]] = []
    ustar_out: list[dict[str, Any]] = []
    spinodals_out: list[dict[str, Any]] = []
    coex_out: list[dict[str, Any]] = []

    for (lattice, m_g, gauge), group_rows in sorted(groups.items()):
        u_index = {u: i for i, u in enumerate(grids[lattice][0])}
        t_index = {t: i for i, t in enumerate(grids[lattice][1])}
        by_t: dict[float, list[dict[str, Any]]] = {}
        for row in group_rows:
            by_t.setdefault(row["t"], []).append(row)

        coex_cells: list[list[int]] = []
        for t in sorted(by_t):
            t_rows = by_t[t]
            label = f"{dataset_id} {lattice} m_g={m_g} {gauge} T/D={t:g}"
            kind_points: dict[str, list[BranchPoint]] = {
                "metal": [],
                "insul": [],
            }
            attempted: dict[str, set[float]] = {"metal": set(), "insul": set()}
            for row in t_rows:
                kind = family_kind(row["family"])
                if kind is None:
                    continue
                attempted[kind].add(row["u"])
                if row["converged"]:
                    kind_points[kind].append(
                        BranchPoint(
                            row=row["i"],
                            u=row["u"],
                            z=row["z"],
                            omega_d=row["omega_d"],
                            resnorm=row["resnorm"],
                        )
                    )

            assembled: dict[str, Branch] = {}
            for kind in ("metal", "insul"):
                if not kind_points[kind]:
                    continue
                branch = assemble_branch(kind_points[kind], f"{label} {kind}")
                assembled[kind] = branch
                report.extend(branch.anomalies)
                branches_out.append(
                    {
                        "ds": dataset_id,
                        "lattice": lattice,
                        "m_g": m_g,
                        "gauge": gauge,
                        "t": t,
                        "kind": kind,
                        "rows": [p.row for p in branch.points],
                        "breaks": branch.breaks,
                    }
                )

            entry = {
                "ds": dataset_id,
                "lattice": lattice,
                "m_g": m_g,
                "gauge": gauge,
                "t": t,
            }
            if "metal" in assembled and "insul" in assembled:
                ustar_out.append(
                    {**entry, **omega_crossing(assembled["metal"], assembled["insul"])}
                )
            spinodal_entry = dict(entry)
            if "metal" in assembled:
                metal_result = metal_spinodal(
                    assembled["metal"], attempted["metal"]
                )
                if metal_result:
                    spinodal_entry.update(metal_result)
            if "insul" in assembled:
                insul_result = insulator_spinodal(
                    assembled["insul"], attempted["insul"]
                )
                if insul_result:
                    spinodal_entry.update(insul_result)
            if len(spinodal_entry) > len(entry):
                spinodals_out.append(spinodal_entry)

            # Coexistence codes per U cell of this temperature row.
            by_u: dict[float, dict[str, Any]] = {}
            for row in t_rows:
                cell = by_u.setdefault(
                    row["u"],
                    {
                        "metal": False,
                        "insul": False,
                        "exotic": False,
                        "metal_omega": None,
                        "insul_omega": None,
                    },
                )
                if not row["converged"]:
                    continue
                kind = family_kind(row["family"])
                if kind is None:
                    cell["exotic"] = True
                    continue
                cell[kind] = True
                omega_key = f"{kind}_omega"
                omega = row["omega_d"]
                if omega is not None and (
                    cell[omega_key] is None or omega < cell[omega_key]
                ):
                    cell[omega_key] = omega
            for u, cell in by_u.items():
                code = coexistence_code(
                    cell["metal"],
                    cell["insul"],
                    cell["exotic"],
                    cell["metal_omega"],
                    cell["insul_omega"],
                )
                if code != COEX_NONE:
                    coex_cells.append([t_index[t], u_index[u], code])

        coex_out.append(
            {
                "ds": dataset_id,
                "lattice": lattice,
                "m_g": m_g,
                "gauge": gauge,
                "cells": sorted(coex_cells),
            }
        )

    return {
        "branches": branches_out,
        "ustar": ustar_out,
        "spinodals": spinodals_out,
        "coex": coex_out,
        "report": report,
    }
