from __future__ import annotations

from gdmft.atlas.derive import (
    COEX_BOTH_INSUL_LOWER,
    COEX_BOTH_METAL_LOWER,
    COEX_EXOTIC_ONLY,
    COEX_METAL_ONLY,
    BranchPoint,
    assemble_branch,
    coexistence_code,
    derive_dataset,
    family_kind,
    insulator_spinodal,
    metal_spinodal,
    omega_crossing,
)


def _points(values: list[tuple[float, float, float]]) -> list[BranchPoint]:
    return [
        BranchPoint(row=i, u=u, z=z, omega_d=omega, resnorm=1e-8)
        for i, (u, z, omega) in enumerate(values)
    ]


def test_family_kind_maps_known_and_exotic_families() -> None:
    assert family_kind("metal-up") == "metal"
    assert family_kind("metal-down") == "metal"
    assert family_kind("insul-down") == "insul"
    assert family_kind("dark") is None
    assert family_kind("symmetry-broken") is None


def test_omega_crossing_interpolates_exactly() -> None:
    # d_omega = U - 2.5 crosses zero at exactly 2.5.
    metal = assemble_branch(
        _points([(u, 0.5, u - 2.5) for u in (2.0, 2.2, 2.4, 2.6, 2.8)]), "m"
    )
    insul = assemble_branch(
        _points([(u, 0.01, 0.0) for u in (2.0, 2.2, 2.4, 2.6, 2.8)]), "i"
    )
    result = omega_crossing(metal, insul)
    assert result["status"] == "crossed"
    assert abs(result["ustar"] - 2.5) < 1e-12
    assert result["u_lo"] == 2.4
    assert result["u_hi"] == 2.6
    assert result["n_overlap"] == 5


def test_omega_crossing_statuses() -> None:
    metal = assemble_branch(_points([(u, 0.5, -1.0) for u in (1.0, 2.0)]), "m")
    insul = assemble_branch(_points([(u, 0.01, 0.0) for u in (1.0, 2.0)]), "i")
    assert omega_crossing(metal, insul)["status"] == "metal_lower_everywhere"

    metal_high = assemble_branch(
        _points([(u, 0.5, 1.0) for u in (1.0, 2.0)]), "m"
    )
    assert (
        omega_crossing(metal_high, insul)["status"] == "insul_lower_everywhere"
    )

    disjoint = assemble_branch(_points([(3.0, 0.5, -1.0)]), "m")
    assert omega_crossing(disjoint, insul)["status"] == "no_overlap"


def test_omega_crossing_never_interpolates_across_a_continuity_break() -> None:
    metal = assemble_branch(
        _points(
            [
                (2.0, 0.50, -0.10),
                (2.1, 0.48, -0.05),
                (2.2, 0.05, 0.05),
                (2.3, 0.04, 0.10),
            ]
        ),
        "broken-metal",
    )
    insul = assemble_branch(
        _points([(u, 0.01, 0.0) for u in (2.0, 2.1, 2.2, 2.3)]),
        "insul",
    )
    assert metal.breaks == [1]
    result = omega_crossing(metal, insul)
    assert result["status"] == "no_continuous_crossing"
    assert "ustar" not in result


def test_find_breaks_flags_z_collapse_and_support_gap() -> None:
    # Z collapse 0.16 -> 0.03 (the verified bethe mg3 R-native pattern).
    smooth = [(2.0 + 0.05 * i, 0.30 - 0.01 * i, -1.0) for i in range(10)]
    collapse = [(2.55, 0.03, -1.0), (2.6, 0.028, -1.0)]
    branch = assemble_branch(_points(smooth + collapse), "collapse")
    assert len(branch.breaks) == 1
    assert branch.points[branch.breaks[0]].u == 2.45

    # Support gap: 0.05 spacing with a 0.5 hole.
    left = [(1.0 + 0.05 * i, 0.5, -1.0) for i in range(6)]
    right = [(1.75 + 0.05 * i, 0.5, -1.0) for i in range(6)]
    gapped = assemble_branch(_points(left + right), "gap")
    assert len(gapped.breaks) == 1
    assert gapped.points[gapped.breaks[0]].u == 1.25


def test_assemble_branch_prefers_lower_residual_duplicates() -> None:
    duplicates = [
        BranchPoint(row=0, u=2.0, z=0.5, omega_d=-1.0, resnorm=1e-3),
        BranchPoint(row=1, u=2.0, z=0.4, omega_d=-1.1, resnorm=1e-9),
    ]
    branch = assemble_branch(duplicates, "dup")
    assert len(branch.points) == 1
    assert branch.points[0].row == 1
    assert branch.anomalies


def test_spinodal_kinds_distinguish_death_from_grid_edge() -> None:
    metal = assemble_branch(
        _points([(u, 0.5, -1.0) for u in (1.0, 1.1, 1.2)]), "m"
    )
    died = metal_spinodal(metal, attempted_u={1.0, 1.1, 1.2, 1.3})
    assert died == {"uc2": 1.2, "uc2_kind": "interior_break"}
    edge = metal_spinodal(metal, attempted_u={1.0, 1.1, 1.2})
    assert edge == {"uc2": 1.2, "uc2_kind": "support_edge"}

    insul = assemble_branch(
        _points([(u, 0.01, 0.0) for u in (2.0, 2.1, 2.2)]), "i"
    )
    interior = insulator_spinodal(insul, attempted_u={1.9, 2.0, 2.1, 2.2})
    assert interior == {"uc1": 2.0, "uc1_kind": "interior_break"}


def test_coexistence_codes() -> None:
    assert coexistence_code(True, True, False, -1.0, 0.0) == (
        COEX_BOTH_METAL_LOWER
    )
    assert coexistence_code(True, True, False, 0.0, -1.0) == (
        COEX_BOTH_INSUL_LOWER
    )
    assert coexistence_code(True, False, False, None, None) == COEX_METAL_ONLY
    assert coexistence_code(False, False, True, None, None) == COEX_EXOTIC_ONLY


def _thin(
    i: int,
    family: str,
    u: float,
    *,
    converged: bool = True,
    z: float = 0.5,
    omega: float | None = None,
    t: float = 0.01,
) -> dict:
    return {
        "i": i,
        "lattice": "bethe",
        "m_g": 3,
        "gauge": "bare",
        "family": family,
        "u": u,
        "t": t,
        "z": z,
        "omega_d": omega,
        "resnorm": 1e-8,
        "converged": converged,
    }


def test_derive_dataset_splices_metal_down_and_up_segments() -> None:
    # metal-down covers low U, metal-up covers high U: one spliced branch.
    rows = [
        _thin(0, "metal-down", 1.0, omega=-2.0),
        _thin(1, "metal-down", 1.1, omega=-1.9),
        _thin(2, "metal-up", 1.2, omega=-1.8),
        _thin(3, "metal-up", 1.3, omega=-1.7),
        _thin(4, "insul-down", 1.1, omega=-1.7, z=0.01),
        _thin(5, "insul-down", 1.2, omega=-1.6, z=0.01),
        _thin(6, "insul-down", 1.3, omega=-1.5, z=0.01),
        _thin(7, "dark", 1.0, z=1e-5),
    ]
    grids = {"bethe": ([1.0, 1.1, 1.2, 1.3], [0.01])}
    derived = derive_dataset("test", rows, grids)

    metal = [b for b in derived["branches"] if b["kind"] == "metal"]
    assert len(metal) == 1
    assert metal[0]["rows"] == [0, 1, 2, 3]
    assert metal[0]["breaks"] == []

    # metal is lower at every shared key here.
    assert derived["ustar"][0]["status"] == "metal_lower_everywhere"
    # The dark row shows up as an exotic-family report, not a branch.
    assert any("dark" in line for line in derived["report"])


def test_derive_dataset_mg1_no_insulator_path() -> None:
    # Insulator attempts exist but never converged (the mg1 dark story):
    # no insul branch, no crossing entry, metal spinodal is interior.
    rows = [
        _thin(0, "metal-up", 1.0, omega=-2.0),
        _thin(1, "metal-up", 1.1, omega=-1.9),
        _thin(2, "insul-down", 1.0, converged=False),
        _thin(3, "insul-down", 1.1, converged=False),
        _thin(4, "insul-down", 1.2, converged=False),
        _thin(5, "metal-up", 1.2, converged=False),
    ]
    grids = {"bethe": ([1.0, 1.1, 1.2], [0.01])}
    derived = derive_dataset("test", rows, grids)
    kinds = {b["kind"] for b in derived["branches"]}
    assert kinds == {"metal"}
    assert derived["ustar"] == []
    assert derived["spinodals"][0]["uc2"] == 1.1
    assert derived["spinodals"][0]["uc2_kind"] == "interior_break"
    assert "uc1" not in derived["spinodals"][0]
