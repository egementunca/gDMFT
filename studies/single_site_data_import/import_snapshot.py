#!/usr/bin/env python3
"""Import the frozen single-site D08/D09 results into gDMFT datasets.

The importer reads blobs from an exact Git revision. It never reads the dirty
source worktree, expanded caches, or gitignored run directories.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import shutil
import subprocess
import tarfile
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Any

SOURCE_REVISION = "1d987593969520b8cd6e191ca284682738778a6d"
EXECUTION_REVISION = "1a3af4af02029a84cf998109cb60dc96217863c8"
CREATED_AT = "2026-07-17T21:32:07Z"

D08_SOURCE = "results/deliverables/08_single_site_gauge_matrix"
D09_SOURCE = "results/deliverables/09_single_site_publication_validation"

D08_ID = "single-site.gauge-matrix-v1"
D09_ID = "single-site.scan-matrix-v2"

D08_FILES = {
    "roots.jsonl.gz": "raw/roots.jsonl.gz",
    "roots_archive_manifest.json": "raw/roots_archive_manifest.json",
    "scalar_projection.csv": "source_views/scalar_projection.csv",
    "grid_registry.json": "metadata/grid_registry.json",
    "coverage_matrix.csv": "evidence/coverage_matrix.csv",
    "coverage_report.md": "evidence/coverage_report.md",
    "_build_stats.json": "evidence/build_stats.json",
    "source_manifest.csv": "provenance/source_manifest.csv",
    "ed_accepted.csv": "legacy/ed/accepted.csv",
    "ed_raw_attempts.csv": "legacy/ed/raw_attempts.csv",
    "ed_llk_config.json": "legacy/ed/config.json",
    "square_quadrature_pilot.csv": "legacy/square/quadrature_pilot.csv",
    "README.md": "provenance/source_README.md",
}

D09_FILES = {
    "raw_campaign.tar.gz": "raw/raw_campaign.tar.gz",
    "stage3_scalar_projection.csv": "source_views/stage3_scalar_projection.csv",
    "coverage_after_v2.csv": "evidence/coverage_after_v2.csv",
    "bare_R_pairing.csv": "evidence/bare_R_pairing.csv",
    "unresolved_conditions_v2.csv": "evidence/unresolved_conditions_v2.csv",
    "stage3_audit_v2.csv": "evidence/stage3_audit_v2.csv",
    "mg1_bound_expansion.csv": "evidence/mg1_bound_expansion.csv",
    "claim_ledger.csv": "evidence/claim_ledger.csv",
    "square_node_certification.json": (
        "evidence/square/square_node_certification.json"
    ),
    "square_integration_registry.json": (
        "evidence/square/square_integration_registry.json"
    ),
    "square_pilot_v2_raw.csv": "evidence/square/square_pilot_v2_raw.csv",
    "square_stationary_convergence_v2.csv": (
        "evidence/square/square_stationary_convergence_v2.csv"
    ),
    "square_claim_gate_v2.csv": "evidence/square/square_claim_gate_v2.csv",
    "square_branch_matches.csv": "evidence/square/square_branch_matches.csv",
    "square_resolution_decision.md": (
        "evidence/square/square_resolution_decision.md"
    ),
    "ed_llk_protocol.json": "evidence/ed/ed_llk_protocol.json",
    "ed_validation.csv": "evidence/ed/ed_validation.csv",
    "ed_validation_checks.csv": "evidence/ed/ed_validation_checks.csv",
    "ed_raw_attempts.csv": "evidence/ed/ed_raw_attempts.csv",
    "ed_accepted.csv": "evidence/ed/ed_accepted.csv",
    "stage3_source_manifest.csv": "provenance/stage3_source_manifest.csv",
    "dirty_patch.diff": "provenance/execution_patch.diff",
    "README.md": "provenance/source_README.md",
}

D09_CELLS = {
    "bethe_mg1_bare",
    "bethe_mg1_Rnative",
    "bethe_mg3_Rnative",
    "square_mg1_bare",
    "square_mg1_Rnative",
    "square_mg3_bare",
    "square_mg3_Rnative",
}

GAUGE_BY_EVIDENCE = {
    "bare_native": "bare",
    "R_converted_from_bare": "canonical-r-converted",
    "R_reoptimized_from_bare": "canonical-r-reoptimized",
    "R_native_continuation": "canonical-r-native",
}

POINT_COLUMNS = [
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repository", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--revision", default=SOURCE_REVISION)
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def git_bytes(repository: Path, revision: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository), "show", f"{revision}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def sanitize_public_paths(data: bytes) -> bytes:
    text = data.decode("utf-8")
    text = re.sub(r"/Users/[^/]+/dmft/", "", text)
    return text.encode("utf-8")


def copy_source_files(
    repository: Path,
    revision: str,
    source_root: str,
    mapping: dict[str, str],
    destination: Path,
    transforms: dict[str, Callable[[bytes], bytes]] | None = None,
) -> list[dict[str, Any]]:
    transforms = transforms or {}
    records: list[dict[str, Any]] = []
    for source_name, target_name in mapping.items():
        source_path = f"{source_root}/{source_name}"
        original = git_bytes(repository, revision, source_path)
        transform = transforms.get(source_name)
        imported = transform(original) if transform else original
        target_path = destination / target_name
        write_bytes(target_path, imported)
        records.append(
            {
                "source_path": source_path,
                "imported_path": target_name,
                "source_sha256": sha256_bytes(original),
                "imported_sha256": sha256_bytes(imported),
                "source_bytes": len(original),
                "imported_bytes": len(imported),
                "transformation": (
                    "machine path replaced by repository-relative reference"
                    if transform
                    else "byte-for-byte"
                ),
            }
        )
    return records


def nullable_bool(value: Any) -> str:
    if value is None:
        return "null"
    normalized = str(value).strip().lower()
    if normalized in {"", "none", "null", "nan"}:
        return "null"
    if normalized in {"1", "true", "yes"}:
        return "true"
    if normalized in {"0", "false", "no"}:
        return "false"
    raise ValueError(f"invalid boolean value {value!r}")


def value_or_empty(value: Any) -> Any:
    return "" if value is None else value


def write_points(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=POINT_COLUMNS,
            extrasaction="ignore",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {column: value_or_empty(row.get(column)) for column in POINT_COLUMNS}
            )
            count += 1
    return count


def d08_point_rows(source: Path) -> Iterable[dict[str, Any]]:
    with source.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            evidence = row["evidence_type"]
            # D08 Mg=3 `Z_mats` was populated from the canonical Fermi-mode
            # residue, so it is not an independent Matsubara estimator.  The
            # older Mg=1 campaigns did evaluate a distinct Matsubara estimate.
            # Keep those meanings in separate contract columns.
            if row["M_g"] == "3":
                z_from_r = row["Z_pole_from_R"] or row["Z_mats"]
                z_matsubara = ""
            else:
                z_from_r = row["Z_pole_from_R"]
                z_matsubara = row["Z_mats"]
            yield {
                "schema_version": "gdmft.point.v1",
                "run_id": f"d08:{row['campaign']}",
                "point_id": row["source_record_id"],
                "lattice": row["lattice"],
                "m_h": row["M_h"],
                "m_g": row["M_g"],
                "solution_family": row["branch"],
                "gauge": GAUGE_BY_EVIDENCE[evidence],
                "solver": row["solver_route"],
                "u_over_d": row["U_over_D"],
                "t_over_d": row["T_over_D"],
                # D08 did not retain a distinct optimizer-success field.
                "solver_succeeded": nullable_bool(row["converged"]),
                "equations_accepted": nullable_bool(row["equation_accepted"]),
                "density_consistent": "null",
                "physical_guards_clear": "null",
                "bounds_clear": "null",
                "continuity_passed": nullable_bool(row["branch_continuous"]),
                "physically_admissible": nullable_bool(row["physical"]),
                "selected": nullable_bool(row["selected"]),
                "selection_reason": "",
                "source_parent_point_id": row["parent_id"],
                "source_campaign": row["campaign"],
                "source_evidence_type": evidence,
                "source_converged": nullable_bool(row["converged"]),
                "source_floor_limited": nullable_bool(row["floor_limited"]),
                "continuation_direction": row["continuation_direction"],
                "basin": (
                    row["branch"]
                    if row["branch"] in {"coupled", "dark", "symmetry-broken"}
                    else ""
                ),
                "lattice_quadrature": row["lattice_quadrature"],
                "u_raw": row["U_raw"],
                "t_raw": row["T_raw"],
                "quasiparticle_weight_pole": row["Z_pole"],
                "quasiparticle_weight_from_r": z_from_r,
                "quasiparticle_weight_matsubara": z_matsubara,
                "double_occupancy": row["D_occ"],
                "density": row["n"],
                "grand_potential": row["Omega"],
                "grand_potential_over_d": row["Omega_over_D"],
                "potential_energy": row["E_pot"],
                "potential_energy_over_d": row["E_pot_over_D"],
                "residual_norm": row["total_residual"],
                "canonical_lambda_reduced": row["lam_reduced"],
                "canonical_r_reduced": row["Rf_reduced"],
                "canonical_mode_count": row["n_modes"],
                "norm_error": row["norm_error"],
                "closure_error": row["closure_error"],
                "roundtrip_error": row["roundtrip_error"],
                "source_code_revision": EXECUTION_REVISION,
                "source_dirty_state": "dirty",
            }


def current_d09_records(archive: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    with tarfile.open(archive, "r:gz") as source:
        for member in source.getmembers():
            parts = Path(member.name).parts
            if (
                not member.isfile()
                or len(parts) != 3
                or parts[0] != "raw_campaign"
                or parts[1] not in D09_CELLS
                or not parts[2].endswith(".jsonl")
            ):
                continue
            extracted = source.extractfile(member)
            if extracted is None:
                raise ValueError(f"cannot read archive member {member.name}")
            for line in extracted:
                if not line.strip():
                    continue
                record = json.loads(line)
                attempt_id = record["attempt_id"]
                if attempt_id in records:
                    raise ValueError(f"duplicate attempt_id {attempt_id}")
                records[attempt_id] = record
    return records


def d09_point_rows(
    scalar_source: Path, raw_records: dict[str, dict[str, Any]]
) -> Iterable[dict[str, Any]]:
    with scalar_source.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            raw = raw_records.pop(row["attempt_id"])
            evidence = row["evidence_type"]
            optimizer = raw.get("optimizer") or {}
            if evidence == "R_converted_from_bare":
                solver_succeeded = "true"
                active_bound = "null"
            else:
                solver_succeeded = nullable_bool(optimizer.get("success"))
                active_mask = optimizer.get("active_mask")
                active_bound = (
                    "null"
                    if active_mask is None
                    else nullable_bool(any(active_mask))
                )

            category = row["category"]
            equations_accepted = (
                "true"
                if category in {"converged_branch", "branch_not_found"}
                else "false"
            )
            guards_clear = "false" if category == "branch_not_found" else "null"
            yield {
                "schema_version": "gdmft.point.v1",
                "run_id": f"d09:{row['cell']}",
                "point_id": row["attempt_id"],
                "lattice": row["lattice"],
                "m_h": raw["M_h"],
                "m_g": row["M_g"],
                "solution_family": row["branch"],
                "gauge": GAUGE_BY_EVIDENCE[evidence],
                "solver": row["solver_route"],
                "u_over_d": row["U_over_D"],
                "t_over_d": row["T_over_D"],
                "solver_succeeded": solver_succeeded,
                "equations_accepted": equations_accepted,
                "density_consistent": "null",
                "physical_guards_clear": guards_clear,
                "bounds_clear": "null",
                "continuity_passed": "null",
                "physically_admissible": "null",
                "selected": "null",
                "selection_reason": "",
                "source_parent_point_id": row["parent_attempt_id"],
                "source_cell": row["cell"],
                "source_evidence_type": evidence,
                "source_category": category,
                "source_converged": nullable_bool(row["converged"]),
                "source_floor_limited": nullable_bool(row["floor_limited"]),
                "source_optimizer_active_bound": active_bound,
                "basin": row["basin"],
                "lattice_quadrature": row["lattice_quadrature"],
                # The projection copied the 256**2 two-dimensional default
                # into Bethe metadata. The Bethe semicircle route actually
                # evaluates 256 one-dimensional nodes.
                "quadrature_node_count": (
                    "256" if row["lattice"] == "bethe" else row["node_count"]
                ),
                "dos_node_count": row["n_eps_dos"],
                "raw_half_bandwidth": raw["D"],
                "u_raw": row["U_raw"],
                "t_raw": row["T_raw"],
                "quasiparticle_weight_pole": row["Z_pole"],
                # The D09 producer called this scalar `Z_mats`, but it is the
                # exact canonical quasiparticle-mode residue R_qp^2.
                "quasiparticle_weight_from_r": row["Z_mats"],
                "quasiparticle_weight_matsubara": "",
                "double_occupancy": row["D_occ"],
                "density": row["n"],
                "grand_potential": row["Omega"],
                "grand_potential_over_d": row["Omega_over_D"],
                "kinetic_energy": row["E_kin"],
                "kinetic_energy_over_d": row["E_kin_over_D"],
                "potential_energy": row["E_pot"],
                "potential_energy_over_d": (
                    (raw.get("observables") or {}).get("E_pot_over_D")
                ),
                "total_energy": row["E_tot"],
                "total_energy_over_d": row["E_tot_over_D"],
                "residual_norm": row["resnorm"],
                "canonical_lambda_reduced": row["lam_reduced"],
                "canonical_r_reduced": row["Rf_reduced"],
                "canonical_mode_count": row["n_modes"],
                "norm_error": row["norm_error"],
                "closure_error": row["closure_error"],
                "roundtrip_error": row["roundtrip_error"],
                "source_code_revision": row["code_commit"],
                "source_dirty_state": row["dirty"],
            }
    if raw_records:
        raise ValueError(f"{len(raw_records)} raw attempts were not projected")


def git_tree_entries(
    repository: Path, revision: str, pathspecs: list[str]
) -> list[tuple[str, str]]:
    result = subprocess.run(
        [
            "git",
            "-C",
            str(repository),
            "ls-tree",
            "-r",
            revision,
            "--",
            *pathspecs,
        ],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    entries: list[tuple[str, str]] = []
    for line in result.stdout.splitlines():
        metadata, path = line.split("\t", 1)
        mode, object_type, _object_id = metadata.split()
        if object_type == "blob":
            entries.append((mode, path))
    return sorted(set(entries), key=lambda item: item[1])


def build_source_archive(
    repository: Path, revision: str, destination: Path
) -> list[dict[str, Any]]:
    pathspecs = [
        "BHFM2",
        "scripts/gauge_matrix",
        "scripts/dmft_ed_llk.py",
        "scripts/dmft_ed_bench.py",
        "scripts/landscape_map.py",
        "scripts/symmetric_continuation.py",
        "scripts/symmetric_continuation_R.py",
        "scripts/paper_scan_mg3.py",
        "tests/test_stage3_v2.py",
        "tests/test_gauge_matrix.py",
        "tests/test_dmft_ed.py",
        "pyproject.toml",
    ]
    entries = git_tree_entries(repository, revision, pathspecs)
    inventory: list[dict[str, Any]] = []
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as raw_stream:
        with gzip.GzipFile(fileobj=raw_stream, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for mode, path in entries:
                    source_data = git_bytes(repository, revision, path)
                    data = sanitize_public_paths(source_data)
                    info = tarfile.TarInfo(
                        f"paper-consolidation-{revision[:8]}/{path}"
                    )
                    info.size = len(data)
                    info.mode = 0o755 if mode == "100755" else 0o644
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    archive.addfile(info, io.BytesIO(data))
                    inventory.append(
                        {
                            "path": path,
                            "source_sha256": sha256_bytes(source_data),
                            "archive_sha256": sha256_bytes(data),
                            "source_bytes": len(source_data),
                            "archive_bytes": len(data),
                            "transformation": (
                                "machine paths made repository-relative"
                                if source_data != data
                                else "byte-for-byte"
                            ),
                            "git_mode": mode,
                        }
                    )
    return inventory


def write_inventory(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=[
                "path",
                "source_sha256",
                "archive_sha256",
                "source_bytes",
                "archive_bytes",
                "transformation",
                "git_mode",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def artifact_role(path: Path) -> str:
    parts = path.parts
    if path.name == "points.csv":
        return "canonical-scalar-point-table"
    if parts[0] == "raw":
        return "lossless-raw-archive"
    if parts[0] == "source_views":
        return "source-scalar-projection"
    if parts[0] == "evidence":
        return "validation-evidence"
    if parts[0] == "legacy":
        return "legacy-supporting-evidence"
    if parts[0] == "provenance":
        return "provenance"
    return "documentation"


def media_type(path: Path) -> tuple[str, str | None]:
    name = path.name
    if name.endswith(".tar.gz"):
        return "application/x-tar", "gzip"
    if name.endswith(".jsonl.gz"):
        return "application/x-ndjson", "gzip"
    if path.suffix == ".csv":
        return "text/csv", None
    if path.suffix == ".json":
        return "application/json", None
    if path.suffix == ".md":
        return "text/markdown", None
    if path.suffix == ".diff":
        return "text/x-diff", None
    return "application/octet-stream", None


def artifact_entries(dataset: Path, point_rows: int) -> list[dict[str, Any]]:
    artifacts: list[dict[str, Any]] = []
    for path in sorted(dataset.rglob("*")):
        if (
            not path.is_file()
            or path.name == "manifest.json"
            or path.name == ".gitattributes"
        ):
            continue
        relative = path.relative_to(dataset)
        kind, compression = media_type(relative)
        artifact: dict[str, Any] = {
            "artifact_id": str(relative).replace("/", "."),
            "path": relative.as_posix(),
            "role": artifact_role(relative),
            "media_type": kind,
            "sha256": sha256_path(path),
            "bytes": path.stat().st_size,
        }
        if compression:
            artifact["compression"] = compression
        if relative.as_posix() == "points.csv":
            artifact["schema"] = "gdmft.point.v1"
            artifact["rows"] = point_rows
        artifacts.append(artifact)
    return artifacts


def common_manifest(
    dataset_id: str,
    title: str,
    description: str,
    command: list[str],
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "gdmft.dataset.v1",
        "dataset_id": dataset_id,
        "title": title,
        "version": "0.1.0",
        "dataset_kind": "aggregate",
        "data_stage": "validated",
        "release_status": "draft",
        "created_at": CREATED_AT,
        "description": description,
        "provenance": {
            "repository": "paper-consolidation",
            "revision": EXECUTION_REVISION,
            "dirty": True,
            "command": command,
            "python": "3 (exact execution patch version not recorded)",
        },
        "conventions": {
            "energy_unit": "D in the canonical point view",
            "half_bandwidth": 1.0,
            "interaction_axis": "u_over_d",
            "temperature_axis": "t_over_d",
            "double_occupancy": "per physical site",
            "grand_potential": "raw and divided by D are separate columns",
            "solution_difference": "second solution minus first solution",
            "particle_hole": "half filling, density = 1",
        },
        "gate_contract": {
            "point_schema": "gdmft.point.v1",
            "evidence_fields": [
                "solver_succeeded",
                "equations_accepted",
                "density_consistent",
                "physical_guards_clear",
                "bounds_clear",
                "continuity_passed",
            ],
            "decision_fields": ["physically_admissible", "selected"],
            "unknown_encoding": "null",
        },
        "artifacts": artifacts,
    }


def write_json(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def d08_readme() -> str:
    return """# Single-site gauge matrix v1

This is the frozen D08 predecessor dataset. It retains 20,228 full records:
8,568 bare roots, 8,568 deterministic canonical-R conversions, 2,180
canonical-R reoptimizations, and 912 independent canonical-R continuations.

`points.csv` is a gDMFT-native scalar view. `raw/roots.jsonl.gz` is the
lossless source of pole arrays, residues, parameters, observables, and
provenance. The source projection and validation evidence are retained
byte-for-byte. The original gitignored run tree is not bundled, so D08 is a
verified frozen result set rather than a campaign that can be re-solved from
this dataset alone.

The square-lattice rows in D08 use the historical `N_k=16` mesh and are
preliminary for sub-percent claims. Use the child D09 scan-matrix dataset for
the canonical continuum-DOS square results.

`m_h=2` names the bare h-sector budget. Its canonical-R representation has
`n_modes=3` because the forward gauge map adds the central mode; this is a
coordinate transformation, not a different physical pole-budget solve.

No branch selection has been applied. The legacy `converged` flag is exposed
as `solver_succeeded` because D08 did not retain a separate optimizer-success
field; `equations_accepted`, physical admissibility, continuity, and selection
remain unknown unless explicitly present in the source row.

The normalized scalar view separates quasiparticle-weight estimators. For
`m_g=3`, the legacy source field `Z_mats` was the canonical Fermi-mode residue
and is imported as `quasiparticle_weight_from_r`; its Matsubara field is null.
For the older `m_g=1` campaigns, the distinct stored Matsubara estimate remains
in `quasiparticle_weight_matsubara`. The source projection is unchanged.
"""


def d09_readme() -> str:
    return """# Single-site scan matrix v2

This is the authoritative D09 single-site scan dataset. It contains 15,240
unique attempts over seven registered cells:

- 3,368 bare-native roots;
- 3,368 exact canonical-R conversions;
- 3,368 canonical-R reoptimizations seeded from those conversions;
- 5,136 independent canonical-R continuation attempts.

The Bethe grid has 884 `(U/D, T/D)` keys over 17 temperatures. The square grid
has 400 keys over 10 temperatures. Every registered key has at least one
converged branch. All authoritative square rows use the continuum elliptic DOS
with `n_eps=2001`.

`m_h=2` names the bare h-sector budget. Its canonical-R representation stores
`n_modes=3` because the forward gauge map adds the central mode; it does not
mean that an independent `m_h=3` physical model was solved.

The source classification contains 9,753 `converged_branch`, 5,136
`branch_not_found`, and 351 `failed_branch` attempts. A `branch_not_found` row
is a dark decoupled solution, not the requested physical branch. The gDMFT
view therefore records its residual acceptance separately and sets
`physical_guards_clear=false`.

No thermodynamic branch selection has been applied. `bounds_clear`,
`continuity_passed`, `physically_admissible`, and `selected` remain null.
Active optimizer bounds are retained only as source evidence because the Mg=1
bound-expansion test shows that absence of an active-mask bit is not enough to
certify bound independence.

The source projection named the canonical quasiparticle-mode residue `Z_mats`.
In this normalized view it is correctly stored as
`quasiparticle_weight_from_r = R_qp^2`; the independent Matsubara-estimator
column is null. The source projection and raw archive remain unchanged.

The normalized Bethe rows report the effective one-dimensional semicircle
node count, 256. The source projection recorded 65,536 by copying the
two-dimensional `256**2` default even though that was not the Bethe
integration route. Both original source records remain unchanged, and the
manifest records this correction as `d09-bethe-effective-node-count-v1`.

`raw/raw_campaign.tar.gz` is the lossless source. It stores complete native
vectors, full bare and canonical pole arrays, optimizer results, bound
distances, residual vectors and blocks, ancestry, observables, quadrature, and
source revision for every attempt. The compact portable source-code archive
under `provenance/` is an audit freeze, not an importable gDMFT core. Its file
inventory records original and archived hashes; seven machine-specific paths
were made repository-relative without changing numerical code.

The archived square node-certification JSON is evidence from the source
campaign; its interacting-node producer rows were not committed, so it is not
independently rederived by this repository.
"""


def build_datasets(
    repository: Path, output_root: Path, revision: str, replace: bool
) -> None:
    d08 = output_root / "single-site-gauge-matrix-v1"
    d09 = output_root / "single-site-scan-matrix-v2"
    for destination in (d08, d09):
        if destination.exists():
            if not replace:
                raise FileExistsError(
                    f"{destination} exists; pass --replace to rebuild"
                )
            shutil.rmtree(destination)
        destination.mkdir(parents=True)
        (destination / ".gitattributes").write_text(
            "**/*.csv binary\n**/*.diff binary\n",
            encoding="ascii",
        )

    d08_imports = copy_source_files(
        repository, revision, D08_SOURCE, D08_FILES, d08
    )
    d09_imports = copy_source_files(
        repository,
        revision,
        D09_SOURCE,
        D09_FILES,
        d09,
        transforms={
            "ed_llk_protocol.json": sanitize_public_paths,
            "stage3_source_manifest.csv": sanitize_public_paths,
        },
    )

    d08_rows = write_points(
        d08 / "points.csv",
        d08_point_rows(d08 / "source_views/scalar_projection.csv"),
    )
    raw_records = current_d09_records(d09 / "raw/raw_campaign.tar.gz")
    d09_rows = write_points(
        d09 / "points.csv",
        d09_point_rows(
            d09 / "source_views/stage3_scalar_projection.csv",
            raw_records,
        ),
    )
    if d08_rows != 20228:
        raise ValueError(f"expected 20,228 D08 rows, found {d08_rows}")
    if d09_rows != 15240:
        raise ValueError(f"expected 15,240 D09 rows, found {d09_rows}")

    source_archive = d09 / "provenance/source-code-portable-1d987593.tar.gz"
    source_inventory = build_source_archive(
        repository, revision, source_archive
    )
    write_inventory(
        d09 / "provenance/source-code-inventory.csv", source_inventory
    )

    (d08 / "README.md").write_text(d08_readme(), encoding="utf-8")
    (d09 / "README.md").write_text(d09_readme(), encoding="utf-8")
    write_json(
        d08 / "provenance/migration_report.json",
        {
            "source_revision": revision,
            "execution_revision": EXECUTION_REVISION,
            "imports": d08_imports,
            "derived": {
                "points.csv": {
                    "rows": d08_rows,
                    "source": "source_views/scalar_projection.csv",
                }
            },
            "excluded": [
                ".gitattributes (source repository metadata)",
                ".gitignore (source repository metadata)",
                "expanded roots.jsonl (regenerable from roots.jsonl.gz)",
            ],
        },
    )
    write_json(
        d09 / "provenance/migration_report.json",
        {
            "source_revision": revision,
            "execution_revision": EXECUTION_REVISION,
            "imports": d09_imports,
            "derived": {
                "points.csv": {
                    "rows": d09_rows,
                    "source": "source_views/stage3_scalar_projection.csv "
                    "+ raw/raw_campaign.tar.gz",
                    "normalizations": [
                        "source Z_mats mapped to canonical R_qp^2 field",
                        (
                            "Bethe source node_count=65536 corrected to "
                            "effective one-dimensional count 256"
                        ),
                    ],
                },
                "provenance/source-code-portable-1d987593.tar.gz": {
                    "files": len(source_inventory),
                    "source": revision,
                    "transformation": (
                        "machine paths made repository-relative; original "
                        "and archived hashes are in source-code-inventory.csv"
                    ),
                },
            },
            "excluded": [
                ".gitattributes and .gitignore (source repository metadata)",
                "expanded raw_campaign/ and stage3_attempts.jsonl "
                "(regenerable from raw_campaign.tar.gz)",
                "superseded top-level v1 reports and projections",
                "LLK reference PDF (copyrighted; checksum retained)",
                "machine-specific D09 source_manifest.csv",
            ],
        },
    )

    d08_artifacts = artifact_entries(d08, d08_rows)
    d08_manifest = common_manifest(
        D08_ID,
        "Single-site gauge matrix v1",
        "Frozen historical bare/canonical-R gauge matrix and full root archive.",
        ["python3", "scripts/gauge_matrix/build.py"],
        d08_artifacts,
    )
    d08_manifest["external_sources"] = [
        {
            "id": "doi:10.1103/PhysRevB.107.L121104",
            "revision": (
                "pdf-sha256:"
                "32f39c77020c5f5e7389828c268219ffaf3dfbd34a14de51ea966c4b1b5d65f9"
            ),
        }
    ]
    d08_manifest["grid"] = {
        "lattices": ["bethe", "square"],
        "m_g": [1, 3],
        "source": "metadata/grid_registry.json",
    }
    d08_manifest["extensions"] = {
        "preservation_revision": revision,
        "raw_half_bandwidth": {"bethe": 1.0, "square": 2.0},
        "record_counts": {
            "total": 20228,
            "bare_native": 8568,
            "canonical_r_converted": 8568,
            "canonical_r_reoptimized": 2180,
            "canonical_r_native": 912,
        },
        "gauge_mode_counting": {
            "bare_m_h": 2,
            "canonical_n_modes": 3,
            "rule": "canonical_n_modes = bare_m_h + 1",
        },
        "square_status": "historical N_k=16; not canonical for sub-percent claims",
        "selection_status": "not applied",
    }
    write_json(d08 / "manifest.json", d08_manifest)

    d09_artifacts = artifact_entries(d09, d09_rows)
    d09_manifest = common_manifest(
        D09_ID,
        "Single-site scan matrix v2",
        (
            "Authoritative lossless Bethe/square, Mg=1/3, "
            "bare/canonical-R single-site scan matrix."
        ),
        ["python3", "scripts/gauge_matrix/build_stage3_v2.py", "--strict"],
        d09_artifacts,
    )
    d09_manifest["parent_dataset_ids"] = [D08_ID]
    d09_manifest["external_sources"] = [
        {
            "id": "doi:10.1103/PhysRevB.107.L121104",
            "revision": (
                "pdf-sha256:"
                "32f39c77020c5f5e7389828c268219ffaf3dfbd34a14de51ea966c4b1b5d65f9"
            ),
        }
    ]
    d09_manifest["grid"] = {
        "bethe": {"keys": 884, "temperatures": 17},
        "square": {
            "keys": 400,
            "temperatures": 10,
            "quadrature": "continuum_elliptic_dos",
            "n_eps": 2001,
        },
        "m_g": [1, 3],
        "m_h": 2,
        "cells": sorted(D09_CELLS),
    }
    d09_manifest["extensions"] = {
        "preservation_revision": revision,
        "raw_half_bandwidth": {"bethe": 1.0, "square": 2.0},
        "attempt_counts": {
            "total": 15240,
            "bare_native": 3368,
            "canonical_r_converted": 3368,
            "canonical_r_reoptimized": 3368,
            "canonical_r_native": 5136,
        },
        "source_categories": {
            "converged_branch": 9753,
            "branch_not_found": 5136,
            "failed_branch": 351,
        },
        "gauge_mode_counting": {
            "bare_m_h": 2,
            "canonical_n_modes": 3,
            "rule": "canonical_n_modes = bare_m_h + 1",
        },
        "keys_with_at_least_one_converged_branch": {
            "registered": 4252,
            "complete": True,
        },
        "metadata_corrections": [
            {
                "id": "d09-bethe-effective-node-count-v1",
                "field": "quadrature_node_count",
                "source_value": 65536,
                "normalized_value": 256,
                "scope": "bethe rows",
                "reason": (
                    "producer recorded the 256**2 two-dimensional default; "
                    "the Bethe semicircle route used 256 one-dimensional nodes"
                ),
                "source_value_preserved_in": [
                    "source_views/stage3_scalar_projection.csv",
                    "raw/raw_campaign.tar.gz",
                ],
            }
        ],
        "selection_status": "not applied",
        "source_code_archive_is_importable_core": False,
        "source_code_archive_is_byte_exact": False,
        "source_code_archive_path_changes_only": True,
    }
    write_json(d09 / "manifest.json", d09_manifest)

    print(
        json.dumps(
            {
                "d08_rows": d08_rows,
                "d09_rows": d09_rows,
                "d08_artifacts": len(d08_artifacts),
                "d09_artifacts": len(d09_artifacts),
                "source_archive_files": len(source_inventory),
                "source_archive_sha256": sha256_path(source_archive),
            },
            indent=2,
            sort_keys=True,
        )
    )


def main() -> None:
    args = parse_args()
    build_datasets(
        args.source_repository.resolve(),
        args.output_root.resolve(),
        args.revision,
        args.replace,
    )


if __name__ == "__main__":
    main()
