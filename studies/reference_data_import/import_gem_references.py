#!/usr/bin/env python3
"""Import the gem (TRIQS ghost-GA / g-RISB) benchmark scans as a reference dataset.

Unlike the single-site import, the gem scan outputs are gitignored run
artifacts in the source worktree, so this importer reads the filesystem and
records per-file SHA-256 provenance instead of git blobs. The generating
script (scripts/gem_scan.py) is tracked in the source repository; its blob at
the source revision is archived byte-for-byte (paths sanitized) under
provenance/.

The scans were produced in reduced units on both lattices (the square DOS was
rescaled to half bandwidth 1 before running gem), with the LLK energy
convention Etot = Ekin + U * docc at mu = 0, eloc = -U/2. This importer
cross-checks double occupancy and total energy against the registered
single-site.scan-matrix-v2 dataset on the coldest row before writing anything,
so a unit or convention mismatch aborts the import.
"""

from __future__ import annotations

import argparse
import csv
import datetime
import gzip
import hashlib
import io
import json
import re
import shutil
import statistics
import subprocess
import sys
import tarfile
from pathlib import Path
from typing import Any

DATASET_ID = "references.gem-gga-v1"
DATASET_DIR = "references-gem-gga-v1"
GEM_PIN_REVISION = "e76cb4c288608b28de4f7e6da31dfaefaefff73f"
LLK_SOURCE = {
    "id": "doi:10.1103/PhysRevB.107.L121104",
    "revision": (
        "pdf-sha256:"
        "32f39c77020c5f5e7389828c268219ffaf3dfbd34a14de51ea966c4b1b5d65f9"
    ),
}
SCAN_MATRIX_ID = "single-site.scan-matrix-v2"

SOURCE_DIRS = {
    "bethe": "results/runs/20260715_paper_scans/gem_gga",
    "square": "results/runs/20260715_paper_scans/gem_gga_square",
}
GEM_SCAN_SCRIPT = "scripts/gem_scan.py"

STRUCTURE_FIELDS = [
    "gem_lam",
    "gem_r2",
    "gem_sig_poles",
    "gem_sig_w2",
    "gem_sig_lin",
]
# Later passes append the framework-invariant structure columns; earlier
# pass files carry only the scalar columns. Both are valid inputs.
SOURCE_FIELDS = [
    "B",
    "T",
    "U_over_D",
    "direction",
    "Z",
    "Z_mats",
    "docc",
    "ekin",
    "etot",
    "sumR2",
    "iters",
    "diff",
    "converged",
    *STRUCTURE_FIELDS,
    "wall",
]
SOURCE_FIELDS_LEGACY = [
    field for field in SOURCE_FIELDS if field not in STRUCTURE_FIELDS
]

REFERENCE_COLUMNS = [
    "schema_version",
    "method",
    "lattice",
    "bath_budget",
    "u_over_d",
    "t_over_d",
    "direction",
    "quasiparticle_weight_slope",
    "quasiparticle_weight_matsubara",
    "double_occupancy",
    "kinetic_energy_over_d",
    "total_energy_over_d",
    "sum_r_squared",
    "self_energy_linear_term",
    "iterations",
    "convergence_diff",
    "converged",
    "crashed",
    "mode_energies",
    "mode_weights",
    "self_energy_pole_positions",
    "self_energy_pole_weights",
    "wall_seconds",
    "source_file",
]

EXPECTED_ROWS = {
    ("bethe", 1): 1768,
    ("bethe", 3): 1768,
    ("square", 1): 800,
    ("square", 3): 800,
}

# Import-time convention guard: ours vs gem on the coldest row (T/D = 0.001),
# converged up-arm metal points with sumR2 <= 1.1. The 2026-07-15/16 benchmark
# notes report median |d docc| ~ 4e-4 (bethe Mg=3), 7.8e-4 (square Mg=3),
# 2.5e-3 (square Mg=1); thresholds below are loose multiples that still catch
# any unit or convention break (factor-2 energy scale, +U/2 shift, ...).
#
# The bethe m_g=3 comparison must use the v1 gauge-matrix BARE rows: the
# scan-matrix v2 bethe_mg3 cell holds only independent canonical-R
# continuations, whose metal chain falls into the effective-m_g=1 family
# (the documented negative control), so it is the wrong population to compare
# against gem B=3. v1 records no total energy, hence docc-only there.
CROSS_CHECKS = [
    # (lattice, budget, points source, our gauge, check etot, docc tol, etot tol)
    ("bethe", 3, "v1", "bare", False, 5e-3, None),
    ("bethe", 1, "v2", "bare", True, 1e-2, 1e-2),
    ("square", 3, "v2", "bare", True, 5e-3, 5e-3),
    ("square", 1, "v2", "bare", True, 1e-2, 1e-2),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-repository",
        type=Path,
        default=Path("/Users/egementunca/dmft/worktrees/paper-consolidation"),
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data/datasets",
    )
    parser.add_argument(
        "--scan-matrix-points",
        type=Path,
        default=(
            Path(__file__).resolve().parents[2]
            / "data/datasets/single-site-scan-matrix-v2/points.csv"
        ),
    )
    parser.add_argument(
        "--gauge-matrix-points",
        type=Path,
        default=(
            Path(__file__).resolve().parents[2]
            / "data/datasets/single-site-gauge-matrix-v1/points.csv"
        ),
    )
    parser.add_argument("--replace", action="store_true")
    return parser.parse_args()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def git_output(repository: Path, *argv: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *argv],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    )
    return result.stdout


def sanitize_public_paths(data: bytes) -> bytes:
    text = data.decode("utf-8")
    text = re.sub(r"/Users/[^/]+/dmft/", "", text)
    return text.encode("utf-8")


def assert_gem_pin(repo_root: Path) -> None:
    sources = (repo_root / "external/sources.toml").read_text(encoding="utf-8")
    match = re.search(r'^revision = "([0-9a-f]{40})"', sources, re.MULTILINE)
    if match is None or match.group(1) != GEM_PIN_REVISION:
        raise ValueError(
            "external/sources.toml gem revision does not match "
            f"{GEM_PIN_REVISION}; update the importer or the pin"
        )


def number_or_empty(value: str) -> str:
    """Pass numeric strings through verbatim; encode nan/missing as empty."""
    text = (value or "").strip()
    if not text or text.lower() == "nan":
        return ""
    float(text)  # raises on garbage
    return text


def filename_temperature(name: str) -> str:
    match = re.fullmatch(r"gem_B([13])_T([0-9.]+)\.csv", name)
    if match is None:
        raise ValueError(f"unexpected gem scan file name: {name}")
    return match.group(2)


def collect_rows(
    source_repository: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str, str, str]] = set()
    for lattice, relative_dir in SOURCE_DIRS.items():
        directory = source_repository / relative_dir
        files = sorted(directory.glob("gem_B*_T*.csv"))
        if not files:
            raise FileNotFoundError(f"no gem scan CSVs under {directory}")
        for path in files:
            file_temperature = filename_temperature(path.name)
            data = path.read_bytes()
            source_files.append(
                {
                    "path": f"{relative_dir}/{path.name}",
                    "sha256": sha256_bytes(data),
                    "bytes": len(data),
                }
            )
            reader = csv.DictReader(io.StringIO(data.decode("utf-8")))
            if reader.fieldnames not in (SOURCE_FIELDS, SOURCE_FIELDS_LEGACY):
                raise ValueError(
                    f"{path.name}: unexpected columns {reader.fieldnames}"
                )
            for raw_row in reader:
                source_row = {field: "" for field in STRUCTURE_FIELDS}
                source_row.update(raw_row)
                if float(source_row["T"]) != float(file_temperature):
                    raise ValueError(
                        f"{path.name}: row temperature {source_row['T']} does "
                        f"not match file name"
                    )
                budget = int(source_row["B"])
                crashed = source_row["iters"].strip() == "-1"
                converged = source_row["converged"].strip() == "1"
                if crashed and converged:
                    raise ValueError(f"{path.name}: crashed row marked converged")
                key = (
                    lattice,
                    budget,
                    source_row["T"],
                    source_row["U_over_D"],
                    source_row["direction"],
                )
                if key in seen:
                    raise ValueError(f"duplicate gem point {key!r}")
                seen.add(key)
                rows.append(
                    {
                        "schema_version": "gdmft.reference.v1",
                        "method": "gem-gga",
                        "lattice": lattice,
                        "bath_budget": budget,
                        "u_over_d": source_row["U_over_D"],
                        "t_over_d": source_row["T"],
                        "direction": source_row["direction"],
                        "quasiparticle_weight_slope": number_or_empty(
                            source_row["Z"]
                        ),
                        "quasiparticle_weight_matsubara": number_or_empty(
                            source_row["Z_mats"]
                        ),
                        "double_occupancy": number_or_empty(source_row["docc"]),
                        "kinetic_energy_over_d": number_or_empty(
                            source_row["ekin"]
                        ),
                        "total_energy_over_d": number_or_empty(
                            source_row["etot"]
                        ),
                        "sum_r_squared": number_or_empty(source_row["sumR2"]),
                        "self_energy_linear_term": number_or_empty(
                            source_row["gem_sig_lin"]
                        ),
                        "iterations": source_row["iters"],
                        "convergence_diff": number_or_empty(source_row["diff"]),
                        "converged": "true" if converged else "false",
                        "crashed": "true" if crashed else "false",
                        "mode_energies": source_row["gem_lam"],
                        "mode_weights": source_row["gem_r2"],
                        "self_energy_pole_positions": source_row["gem_sig_poles"],
                        "self_energy_pole_weights": source_row["gem_sig_w2"],
                        "wall_seconds": number_or_empty(source_row["wall"]),
                        "source_file": f"{relative_dir}/{path.name}",
                    }
                )
    rows.sort(
        key=lambda row: (
            row["lattice"],
            row["bath_budget"],
            float(row["t_over_d"]),
            float(row["u_over_d"]),
            row["direction"],
        )
    )
    return rows, source_files


def check_counts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[tuple[str, int], int] = {}
    crashes = 0
    nonconverged = 0
    soft = 0
    gross = 0
    structure = {key: 0 for key in EXPECTED_ROWS}
    for row in rows:
        key = (row["lattice"], row["bath_budget"])
        counts[key] = counts.get(key, 0) + 1
        if row["crashed"] == "true":
            crashes += 1
        elif row["converged"] == "false":
            nonconverged += 1
        if row["self_energy_pole_positions"]:
            structure[key] += 1
        if row["sum_r_squared"]:
            total_weight = float(row["sum_r_squared"])
            if total_weight > 1.1:
                gross += 1
            elif total_weight > 1.0001:
                soft += 1
    if counts != EXPECTED_ROWS:
        raise ValueError(f"unexpected row counts: {counts}")
    return {
        "row_counts": {
            f"{lattice}_b{budget}": count
            for (lattice, budget), count in sorted(counts.items())
        },
        "total_rows": len(rows),
        "crashed_rows": crashes,
        "stalled_rows": nonconverged,
        "sum_rule_soft_rows": soft,
        "sum_rule_gross_rows": gross,
        "structure_rows": {
            f"{lattice}_b{budget}": count
            for (lattice, budget), count in sorted(structure.items())
        },
    }


def load_cold_metal_rows(
    points: Path, converged_filter: str
) -> dict[tuple[str, int, str], dict[float, tuple[float, float | None]]]:
    """Cold-row (T/D = 0.001) converged metal points from a registered table."""
    table: dict[tuple[str, int, str], dict[float, tuple[float, float | None]]]
    table = {}
    with points.open("r", encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            if converged_filter == "v2":
                converged = row["source_category"] == "converged_branch"
            else:
                converged = row["source_converged"] == "true"
            if (
                float(row["t_over_d"] or "nan") != 0.001
                or not converged
                or row["solution_family"] not in {"metal-up", "metal-down"}
                or not row["double_occupancy"]
            ):
                continue
            key = (row["lattice"], int(row["m_g"]), row["gauge"])
            etot = row["total_energy_over_d"]
            table.setdefault(key, {})[float(row["u_over_d"])] = (
                float(row["double_occupancy"]),
                float(etot) if etot else None,
            )
    return table


def cross_check_conventions(
    rows: list[dict[str, Any]],
    scan_matrix_points: Path,
    gauge_matrix_points: Path,
) -> dict[str, Any]:
    """Abort unless gem agrees with the registered datasets on cold rows."""
    ours_by_source = {
        "v2": load_cold_metal_rows(scan_matrix_points, "v2"),
        "v1": load_cold_metal_rows(gauge_matrix_points, "v1"),
    }

    gem: dict[tuple[str, int], dict[float, tuple[float, float]]] = {}
    for row in rows:
        if (
            float(row["t_over_d"]) != 0.001
            or row["direction"] != "up"
            or row["converged"] != "true"
            or not row["sum_r_squared"]
            or float(row["sum_r_squared"]) > 1.1
        ):
            continue
        gem.setdefault((row["lattice"], row["bath_budget"]), {})[
            float(row["u_over_d"])
        ] = (
            float(row["double_occupancy"]),
            float(row["total_energy_over_d"]),
        )

    report = {}
    for lattice, budget, source, gauge, check_etot, docc_tol, etot_tol in (
        CROSS_CHECKS
    ):
        mine = ours_by_source[source].get((lattice, budget, gauge), {})
        theirs = gem.get((lattice, budget), {})
        shared = sorted(set(mine) & set(theirs))
        if len(shared) < 10:
            raise ValueError(
                f"convention check {lattice} b={budget} ({source}/{gauge}): "
                f"only {len(shared)} shared cold metal points"
            )
        docc_median = statistics.median(
            abs(mine[u][0] - theirs[u][0]) for u in shared
        )
        if docc_median > docc_tol:
            raise ValueError(
                f"convention check FAILED for {lattice} b={budget} "
                f"({source}/{gauge}): median |d docc| = {docc_median:.2e} "
                f"(tol {docc_tol:.0e})"
            )
        entry: dict[str, Any] = {
            "shared_cold_metal_points": len(shared),
            "our_source": source,
            "our_gauge": gauge,
            "median_abs_d_docc": round(docc_median, 8),
        }
        if check_etot:
            etot_median = statistics.median(
                abs(mine[u][1] - theirs[u][1]) for u in shared
            )
            if etot_median > etot_tol:
                raise ValueError(
                    f"convention check FAILED for {lattice} b={budget} "
                    f"({source}/{gauge}): median |d etot| = "
                    f"{etot_median:.2e} (tol {etot_tol:.0e})"
                )
            entry["median_abs_d_etot_over_d"] = round(etot_median, 8)
        report[f"{lattice}_b{budget}"] = entry
    return report


def write_points(path: Path, rows: list[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=REFERENCE_COLUMNS, lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def build_raw_archive(
    source_repository: Path,
    source_files: list[dict[str, Any]],
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as raw_stream:
        with gzip.GzipFile(fileobj=raw_stream, mode="wb", mtime=0) as compressed:
            with tarfile.open(fileobj=compressed, mode="w") as archive:
                for record in source_files:
                    data = (source_repository / record["path"]).read_bytes()
                    info = tarfile.TarInfo(f"gem_scan_outputs/{record['path']}")
                    info.size = len(data)
                    info.mode = 0o644
                    info.mtime = 0
                    info.uid = 0
                    info.gid = 0
                    info.uname = ""
                    info.gname = ""
                    archive.addfile(info, io.BytesIO(data))


def media_type(path: Path) -> tuple[str, str | None]:
    if path.name.endswith(".tar.gz"):
        return "application/x-tar", "gzip"
    if path.suffix == ".csv":
        return "text/csv", None
    if path.suffix == ".json":
        return "application/json", None
    if path.suffix == ".md":
        return "text/markdown", None
    if path.suffix == ".py":
        return "text/x-python", None
    return "application/octet-stream", None


def artifact_role(path: Path) -> str:
    if path.name == "points.csv":
        return "reference-scalar-table"
    if path.parts[0] == "raw":
        return "lossless-raw-archive"
    if path.parts[0] == "provenance":
        return "provenance"
    return "documentation"


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
            artifact["schema"] = "gdmft.reference.v1"
            artifact["rows"] = point_rows
        artifacts.append(artifact)
    return artifacts


def readme() -> str:
    return """# gem ghost-GA (g-RISB) benchmark scans v1

Reference dataset: the TRIQS/gem ghost Gutzwiller (g-RISB) scans run for the
2026-07-15/16 benchmark layer, matched point-for-point to the
`single-site.scan-matrix-v2` grids. gem bath budget `B` corresponds to our
`m_g` (B=1 <-> m_g=1, B=3 <-> m_g=3). Coverage: bethe B=1 and B=3 on all 17
temperature rows x 52 U/D values, square B=1 and B=3 on all 10 rows x 40
values, both up and down sweep directions everywhere; 5,136 rows total.

## Units and conventions

All values are in reduced units with half bandwidth D = 1 on BOTH lattices:
the square DOS was rescaled to half bandwidth 1 before running gem, so
`u_over_d`, `t_over_d`, and every energy are directly comparable to the
canonical scan-matrix columns. Energy convention is LLK (PRB 107, L121104):
`total_energy = kinetic_energy + U * double_occupancy` at mu = 0,
eloc = -U/2. The importer verifies cold-row (T/D = 0.001) agreement of
double occupancy and total energy against the registered scan matrix before
writing anything; the achieved medians are recorded in
`provenance/import_report.json`.

## Columns

`quasiparticle_weight_slope` is gem's real-axis Sigma-slope estimator
(`compute_Z`); `quasiparticle_weight_matsubara` is the Matsubara-slope
estimator at the row's own temperature. `sum_r_squared` is gem's captured
spectral weight sum_a |R_a|^2 (gem's R is unnormalized; physical <= 1).
`self_energy_linear_term` = 1 - 1/sum_r_squared, gem's large-z linear
self-energy coefficient (identically 0 in our canonical frame).

The structure columns are framework-invariant objects computed from gem's
converged (Lambda, R) in the Lambda eigenbasis (see `provenance/gem_scan.py`,
`structure_of`): `mode_energies` / `mode_weights` are the mode spectrum
(semicolon-joined), `self_energy_pole_positions` / `self_energy_pole_weights`
the self-energy pole pair (zeros of M(z) with weights -1/M'). B=1 has no
interior self-energy pole (structureless RISB / Brinkman-Rice), so those two
columns are empty for every B=1 row; parts of the bethe B=3 pass predate the
structure columns, so their coverage there is partial.

`crashed=true` rows are recorded gem-internal failures (SVD non-convergence
in the thermal fit); their observables are empty and `iterations` is -1.
`converged=false` with `crashed=false` means the mixing iteration stalled at
the tolerance.

## Caveats (from the benchmark notes, verified against LLK)

- **Warm temperature (bethe T/D >= 0.05) is qualitative only**: gem's spin
  penalty corrupts the T > 0 Boltzmann weights, its thermal update lets
  sum_r_squared drift above 1, and its Z inflates toward 1.
- **Z is the framework-sensitive observable**: compare double occupancy and
  energies tightly; compare Z only on cold rows (LLK's conclusion).
- **sum_r_squared > 1.1 rows are junk** (spurious fixed points) — gem's
  framework-native junk detector. Soft violations (1 < s <= ~1.06) occur on
  physical warm branches; treat with care.
- **Never compare raw R magnitudes across frameworks** (gem unnormalized,
  our canonical gauge normalized); compare Z and pole content instead.

## Provenance

The scan CSVs are gitignored run outputs of the source worktree, so this
dataset records filesystem SHA-256 checksums per source file
(`provenance/source_files.csv`) plus the byte-for-byte raw archive
(`raw/gem_scan_outputs.tar.gz`). The generating script is archived at the
source revision with machine paths made repository-relative
(`provenance/gem_scan.py`). The gem code itself is pinned in
`external/sources.toml` (revision in this manifest's `external_sources`).
"""


def write_json(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def build_dataset(args: argparse.Namespace) -> None:
    repo_root = Path(__file__).resolve().parents[2]
    assert_gem_pin(repo_root)
    source_repository = args.source_repository.resolve()

    dataset = args.output_root.resolve() / DATASET_DIR
    if dataset.exists():
        if not args.replace:
            raise FileExistsError(f"{dataset} exists; pass --replace to rebuild")
        shutil.rmtree(dataset)
    dataset.mkdir(parents=True)
    (dataset / ".gitattributes").write_text("**/*.csv binary\n", encoding="ascii")

    rows, source_files = collect_rows(source_repository)
    counts = check_counts(rows)
    convention_report = cross_check_conventions(
        rows, args.scan_matrix_points, args.gauge_matrix_points
    )

    row_count = write_points(dataset / "points.csv", rows)
    build_raw_archive(
        source_repository, source_files, dataset / "raw/gem_scan_outputs.tar.gz"
    )

    script_blob = subprocess.run(
        [
            "git",
            "-C",
            str(source_repository),
            "show",
            f"HEAD:{GEM_SCAN_SCRIPT}",
        ],
        check=True,
        stdout=subprocess.PIPE,
    ).stdout
    (dataset / "provenance").mkdir(exist_ok=True)
    (dataset / "provenance/gem_scan.py").write_bytes(
        sanitize_public_paths(script_blob)
    )

    with (dataset / "provenance/source_files.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["path", "sha256", "bytes"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(source_files)

    source_revision = git_output(
        source_repository, "rev-parse", "HEAD"
    ).strip()
    source_dirty = bool(
        git_output(source_repository, "status", "--porcelain").strip()
    )
    created_at = (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    write_json(
        dataset / "provenance/import_report.json",
        {
            "source_repository": "paper-consolidation",
            "source_revision": source_revision,
            "source_dirty": source_dirty,
            "source_note": (
                "scan CSVs are gitignored run outputs; provenance is the "
                "per-file sha256 inventory, not git blobs"
            ),
            "counts": counts,
            "convention_cross_check": convention_report,
            "generating_script": {
                "path": GEM_SCAN_SCRIPT,
                "source_sha256": sha256_bytes(script_blob),
                "archived_sha256": sha256_bytes(
                    sanitize_public_paths(script_blob)
                ),
                "transformation": (
                    "machine path replaced by repository-relative reference"
                ),
            },
        },
    )

    (dataset / "README.md").write_text(readme(), encoding="utf-8")

    manifest = {
        "schema_version": "gdmft.dataset.v1",
        "dataset_id": DATASET_ID,
        "title": "gem ghost-GA (g-RISB) benchmark scans v1",
        "version": "0.1.0",
        "dataset_kind": "external_reference",
        "data_stage": "validated",
        "release_status": "draft",
        "created_at": created_at,
        "description": (
            "TRIQS/gem ghost-GA scans matched point-for-point to the "
            "single-site scan matrix grids (bethe 17 T x 52 U, square "
            "10 T x 40 U, B = 1 and 3, both sweep directions), in reduced "
            "units with the LLK energy convention."
        ),
        "provenance": {
            "repository": "paper-consolidation",
            "revision": source_revision,
            "dirty": source_dirty,
            "command": [
                "python3",
                "studies/reference_data_import/import_gem_references.py",
            ],
            "python": sys.version.split()[0],
        },
        "conventions": {
            "energy_unit": (
                "D (reduced units; the square DOS was rescaled to half "
                "bandwidth 1 before running gem)"
            ),
            "half_bandwidth": 1.0,
            "interaction_axis": "u_over_d",
            "temperature_axis": "t_over_d",
            "double_occupancy": "per physical site",
            "grand_potential": "not recorded by the gem scans",
            "particle_hole": (
                "half filling; mu = 0, eloc = -U/2, "
                "total_energy = kinetic_energy + U * double_occupancy (LLK)"
            ),
        },
        "grid": {
            "bethe": {"temperatures": 17, "u_values": 52},
            "square": {"temperatures": 10, "u_values": 40},
            "bath_budgets": [1, 3],
            "directions": ["up", "down"],
            "matched_to": SCAN_MATRIX_ID,
        },
        "external_sources": [
            {"id": "gem", "revision": GEM_PIN_REVISION},
            LLK_SOURCE,
        ],
        "extensions": {
            "budget_map": "gem bath_budget B corresponds to scan-matrix m_g",
            "counts": counts,
            "convention_cross_check": convention_report,
            "caveats": [
                "bethe T/D >= 0.05 rows are qualitative only "
                "(spin-penalty thermal weights, sum-rule drift, Z inflation)",
                "compare double occupancy and energies tightly; compare Z "
                "only on cold rows (framework-sensitive observable)",
                "sum_r_squared > 1.1 marks junk fixed points",
                "never compare raw R magnitudes across frameworks",
            ],
        },
        "artifacts": artifact_entries(dataset, row_count),
    }
    write_json(dataset / "manifest.json", manifest)

    print(
        json.dumps(
            {
                "dataset": str(dataset),
                "rows": row_count,
                "counts": counts,
                "convention_cross_check": convention_report,
                "registry_block": (
                    f'\n[[dataset]]\nid = "{DATASET_ID}"\n'
                    f'version = "0.1.0"\n'
                    f'manifest = "data/datasets/{DATASET_DIR}/manifest.json"\n'
                    f'data_stage = "validated"\nrelease_status = "draft"\n'
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


def main() -> None:
    build_dataset(parse_args())


if __name__ == "__main__":
    main()
