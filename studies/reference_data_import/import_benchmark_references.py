#!/usr/bin/env python3
"""Import the cross-method benchmark reference tables as a registered dataset.

Sources (old worktree + refs, all gitignored run outputs or external data):
- the audited tidy benchmark merge the Jul-16 paper figures read
  (compare_all / compare_vs_T / convergence_U2.4, audit: ALL CHECKS PASS)
- the NRG thermal reference curves (T_arr.dat + per-U D/Ekin/Epot .dat)
- the professor's gGA grids (.npy, parsed with a pure-python reader;
  E_tot stored RAW in the eps_loc = -U/2 convention — add U/2 for LLK axes)
- the CTQMC anchor (LLK Table I / Fig. 3, beta = 200)
- the fresh-ruler marker tables fig_single_site draws

The importer is self-verifying: the merge's ghost/gem rows are cross-checked
against the already-registered point datasets, and the prof grids re-derived
from the .npy files must reproduce the merge's gga_prof rows exactly (which
also validates the .npy parser and the +U/2 convention).
"""

from __future__ import annotations

import argparse
import ast
import csv
import datetime
import hashlib
import json
import shutil
import struct
import subprocess
import sys
from pathlib import Path
from typing import Any

DATASET_ID = "references.benchmarks-v1"
DATASET_DIR = "references-benchmarks-v1"

LLK_SOURCE = {
    "id": "doi:10.1103/PhysRevB.107.L121104",
    "revision": (
        "pdf-sha256:"
        "32f39c77020c5f5e7389828c268219ffaf3dfbd34a14de51ea966c4b1b5d65f9"
    ),
}

BENCH_DIR = "results/runs/20260715_paper_scans/benchmarks"
COPY_FILES = {
    f"{BENCH_DIR}/compare_all.csv": "tables/compare_all.csv",
    f"{BENCH_DIR}/compare_vs_T.csv": "tables/compare_vs_T.csv",
    f"{BENCH_DIR}/convergence_U2.4.csv": "tables/convergence_U2.4.csv",
    f"{BENCH_DIR}/ACCEPTANCE.md": "provenance/ACCEPTANCE.md",
    "results/runs/20260710_rerun_mg3/prof_ghost_mg3_markers.csv": (
        "tables/prof_ghost_mg3_markers.csv"
    ),
    "results/runs/20260710_rerun_mg3/prof_ghost_mg3_markers_T5orig.csv": (
        "tables/prof_ghost_mg3_markers_T5orig.csv"
    ),
}
NRG_US = (1.0, 2.0, 3.2)

# LLK Table I / Fig. 3 anchor (beta = 200), the literal the old assembler
# carried in scripts/collect_benchmarks.py.
CTQMC_ROW = {
    "method": "ctqmc_llk",
    "budget": 0,
    "t_over_d": 0.005,
    "u_over_d": 2.4,
    "branch": "exact",
    "z": 0.12,
    "double_occupancy": 0.0545,
    "kinetic_energy_over_d": "",
    "total_energy_over_d": -0.0621,
}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_npy(path: Path) -> tuple[tuple[int, ...], list[float]]:
    """Minimal pure-python .npy (v1/v2) reader for little-endian float64."""
    data = path.read_bytes()
    if data[:6] != b"\x93NUMPY":
        raise ValueError(f"{path}: not an npy file")
    major = data[6]
    if major == 1:
        header_len = struct.unpack("<H", data[8:10])[0]
        offset = 10 + header_len
        header = data[10:offset]
    else:
        header_len = struct.unpack("<I", data[8:12])[0]
        offset = 12 + header_len
        header = data[12:offset]
    meta = ast.literal_eval(header.decode("latin1").strip())
    if meta["descr"] not in ("<f8", "|f8"):
        raise ValueError(f"{path}: unsupported dtype {meta['descr']}")
    if meta["fortran_order"]:
        raise ValueError(f"{path}: fortran order not supported")
    shape = tuple(meta["shape"])
    count = 1
    for dim in shape:
        count *= dim
    values = list(struct.unpack(f"<{count}d", data[offset : offset + 8 * count]))
    return shape, values


def read_dat(path: Path) -> list[float]:
    return [
        float(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]


def load_compare_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def build_nrg_table(refs: Path) -> list[dict]:
    temperatures = read_dat(refs / "T_arr.dat")
    rows = []
    for u in NRG_US:
        docc = read_dat(refs / f"D_arr_U{u:.3f}.dat")
        ekin = read_dat(refs / f"Ekin_arr_U{u:.3f}.dat")
        epot = read_dat(refs / f"Epot_arr_U{u:.3f}.dat")
        if not (len(temperatures) == len(docc) == len(ekin) == len(epot)):
            raise ValueError(f"NRG file length mismatch at U={u}")
        for t, d, ek, ep in zip(temperatures, docc, ekin, epot, strict=True):
            rows.append(
                {
                    "u_over_d": u,
                    "t_over_d": t,
                    "double_occupancy": d,
                    "kinetic_energy_over_d": ek,
                    "potential_energy_over_d": ep,
                    "total_energy_over_d": ek + ep,
                }
            )
    return rows


def build_prof_table(ref2: Path) -> list[dict]:
    _, t_values = read_npy(ref2 / "T_array.npy")
    _, u_values = read_npy(ref2 / "U_array.npy")
    rows = []
    for budget in (1, 3):
        docc_shape, docc = read_npy(ref2 / f"docc_B{budget}.npy")
        etot_shape, etot = read_npy(ref2 / f"Etot_B{budget}.npy")
        expected = (len(t_values), len(u_values))
        if docc_shape != expected or etot_shape != expected:
            raise ValueError(
                f"prof grid shape mismatch B={budget}: {docc_shape} vs {expected}"
            )
        for i, t in enumerate(t_values):
            for j, u in enumerate(u_values):
                rows.append(
                    {
                        "budget": budget,
                        "t_over_d": t,
                        "u_over_d": u,
                        "double_occupancy": docc[i * len(u_values) + j],
                        # RAW eps_loc = -U/2 convention; +U/2 gives LLK axes
                        "total_energy_raw": etot[i * len(u_values) + j],
                    }
                )
    return rows


def median(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[len(ordered) // 2] if ordered else float("nan")


def cross_check(dataset: Path, repo_root: Path, report: dict[str, Any]) -> None:
    compare = load_compare_rows(dataset / "tables/compare_all.csv")

    # 1. gem rows must be identical to the registered gem reference.
    gem_reg: dict[tuple, float] = {}
    with (
        repo_root / "data/datasets/references-gem-gga-v1/points.csv"
    ).open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["lattice"] != "bethe" or row["double_occupancy"] == "":
                continue
            gem_reg[
                (
                    row["bath_budget"],
                    row["t_over_d"],
                    row["u_over_d"],
                    row["direction"],
                )
            ] = float(row["double_occupancy"])
    deltas = []
    for row in compare:
        if row["method"] != "gga_gem" or row["docc"] == "":
            continue
        key = (row["budget"], row["T"], row["U_over_D"], row["branch"])
        if key in gem_reg:
            deltas.append(abs(float(row["docc"]) - gem_reg[key]))
    if len(deltas) < 3000 or median(deltas) > 1e-12:
        raise ValueError(
            f"gem cross-check failed: {len(deltas)} matches, "
            f"median {median(deltas):.2e}"
        )
    report["gem_rows_matched"] = len(deltas)

    # 2. ghost rows against the registered v1 bare bethe m_g=3 scan
    #    (same source campaign; docc must agree at machine precision).
    ours: dict[tuple, float] = {}
    with (
        repo_root / "data/datasets/single-site-gauge-matrix-v1/points.csv"
    ).open(newline="") as stream:
        for row in csv.DictReader(stream):
            if (
                row["lattice"] == "bethe"
                and row["m_g"] == "3"
                and row["gauge"] == "bare"
                and row["source_converged"] == "true"
                and row["double_occupancy"]
            ):
                family = row["solution_family"]
                kind = (
                    "metal"
                    if family in ("metal-up", "metal-down")
                    else "insulator"
                    if family == "insul-down"
                    else None
                )
                if kind:
                    ours[(row["t_over_d"], row["u_over_d"], kind)] = float(
                        row["double_occupancy"]
                    )
    ghost_deltas = []
    for row in compare:
        if row["method"] != "ghost_dmft" or row["budget"] != "3":
            continue
        if row["docc"] == "":
            continue
        key = (row["T"], row["U_over_D"], row["branch"])
        if key in ours:
            ghost_deltas.append(abs(float(row["docc"]) - ours[key]))
    if len(ghost_deltas) < 2000 or median(ghost_deltas) > 1e-9:
        raise ValueError(
            f"ghost cross-check failed: {len(ghost_deltas)} matches, "
            f"median {median(ghost_deltas):.2e}"
        )
    report["ghost_rows_matched"] = len(ghost_deltas)

    # 3. prof grids re-derived from .npy + U/2 must reproduce the merge.
    prof = load_compare_rows(dataset / "tables/prof_gga_grids.csv")
    prof_map = {
        (
            row["budget"],
            f"{float(row['t_over_d']):.10g}",
            f"{float(row['u_over_d']):.10g}",
        ): (float(row["double_occupancy"]), float(row["total_energy_raw"]))
        for row in prof
    }
    prof_checked = 0
    for row in compare:
        if row["method"] != "gga_prof":
            continue
        key = (
            row["budget"],
            f"{float(row['T']):.10g}",
            f"{float(row['U_over_D']):.10g}",
        )
        if key not in prof_map:
            raise ValueError(f"prof grid key missing: {key}")
        docc, etot_raw = prof_map[key]
        if row["docc"] and abs(float(row["docc"]) - docc) > 1e-12:
            raise ValueError(f"prof docc mismatch at {key}")
        if row["etot"]:
            expected = etot_raw + float(row["U_over_D"]) / 2.0
            if abs(float(row["etot"]) - expected) > 1e-9:
                raise ValueError(f"prof etot (+U/2) mismatch at {key}")
        prof_checked += 1
    if prof_checked < 2000:
        raise ValueError(f"prof cross-check thin: {prof_checked}")
    report["prof_rows_matched"] = prof_checked

    # 4. NRG table internal consistency vs the merge.
    nrg = load_compare_rows(dataset / "tables/nrg_thermal.csv")
    nrg_map = {
        (f"{float(r['u_over_d']):.10g}", f"{float(r['t_over_d']):.10g}"): float(
            r["total_energy_over_d"]
        )
        for r in nrg
    }
    nrg_checked = 0
    for row in compare:
        if row["method"] != "nrg" or row["etot"] == "":
            continue
        key = (f"{float(row['U_over_D']):.10g}", f"{float(row['T']):.10g}")
        if key not in nrg_map or abs(nrg_map[key] - float(row["etot"])) > 1e-9:
            raise ValueError(f"NRG mismatch at {key}")
        nrg_checked += 1
    report["nrg_rows_matched"] = nrg_checked


def readme() -> str:
    return """# Cross-method benchmark references v1

The reference tables behind the paper's benchmark figures, registered so the
figures read only registered data.

`tables/compare_all.csv` (10,936 rows) is the audited tidy merge
(`method, budget, T, U_over_D, branch, Z, docc, ekin, etot, sumR2`) built by
the source repository's `collect_benchmarks.py` on 2026-07-16 (acceptance
report archived under `provenance/ACCEPTANCE.md`). Methods: `ghost_dmft`
(ours, budgets 1/3 — the only registered source of our bethe m_g=3
E_kin/E_tot, evaluated via the lattice-observable route), `gga_gem` (gem
g-RISB B=1/3), `dmft_ed` (LLK protocol, N_b=1/3/5), `gga_prof` (professor's
grids, E_tot already shifted +U/2 to LLK axes), `nrg` (thermal reference at
U/D = 1, 2, 3.2), `ctqmc_llk` (the beta=200 anchor at U/D=2.4).
`compare_vs_T.csv` and `convergence_U2.4.csv` are its two audited slices.

Source-of-truth inputs are registered alongside: `tables/nrg_thermal.csv`
(normalized from the NRG .dat curves), `tables/prof_gga_grids.csv`
(parsed from the .npy grids; `total_energy_raw` is in the eps_loc = -U/2
convention — ADD U/2 for LLK axes), `tables/ctqmc_anchors.csv`, and the
fresh-ruler marker tables used by the phase-diagram figure.

Import-time verification: gem and ghost rows of the merge reproduce the
already-registered gem reference and v1 bare bethe m_g=3 scan at machine
precision, and the prof rows reproduce the .npy grids under the +U/2
convention (which also validates the pure-python .npy parser).
"""


def write_json(path: Path, document: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def artifact_entries(dataset: Path) -> list[dict[str, Any]]:
    artifacts = []
    for path in sorted(dataset.rglob("*")):
        if not path.is_file() or path.name in ("manifest.json", ".gitattributes"):
            continue
        relative = path.relative_to(dataset)
        suffix = relative.suffix
        media = {
            ".csv": "text/csv",
            ".md": "text/markdown",
            ".json": "application/json",
        }.get(suffix, "application/octet-stream")
        artifacts.append(
            {
                "artifact_id": str(relative).replace("/", "."),
                "path": relative.as_posix(),
                "role": (
                    "provenance"
                    if relative.parts[0] == "provenance"
                    else "reference-scalar-table"
                    if suffix == ".csv"
                    else "documentation"
                ),
                "media_type": media,
                "sha256": sha256_path(path),
                "bytes": path.stat().st_size,
            }
        )
    return artifacts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source-repository",
        type=Path,
        default=Path("/Users/egementunca/dmft/worktrees/paper-consolidation"),
    )
    parser.add_argument(
        "--refs-root", type=Path, default=Path("/Users/egementunca/dmft/refs")
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data/datasets",
    )
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[2]
    source = args.source_repository.resolve()
    refs = (args.refs_root / "ref_data").resolve()
    ref2 = refs / "ref_data2"

    dataset = args.output_root.resolve() / DATASET_DIR
    if dataset.exists():
        if not args.replace:
            raise FileExistsError(f"{dataset} exists; pass --replace")
        shutil.rmtree(dataset)
    dataset.mkdir(parents=True)
    (dataset / ".gitattributes").write_text("**/*.csv binary\n", encoding="ascii")

    source_files = []

    def record(path: Path, label: str) -> None:
        source_files.append(
            {
                "path": label,
                "sha256": sha256_path(path),
                "bytes": path.stat().st_size,
            }
        )

    # byte-for-byte copies
    for rel_source, rel_target in COPY_FILES.items():
        src = source / rel_source
        dst = dataset / rel_target
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
        record(src, rel_source)

    # normalized reference tables
    nrg_rows = build_nrg_table(refs)
    write_csv(
        dataset / "tables/nrg_thermal.csv",
        [
            "u_over_d",
            "t_over_d",
            "double_occupancy",
            "kinetic_energy_over_d",
            "potential_energy_over_d",
            "total_energy_over_d",
        ],
        nrg_rows,
    )
    for name in ["T_arr.dat"] + [
        f"{kind}_arr_U{u:.3f}.dat"
        for u in NRG_US
        for kind in ("D", "Ekin", "Epot")
    ]:
        record(refs / name, f"refs/ref_data/{name}")

    prof_rows = build_prof_table(ref2)
    write_csv(
        dataset / "tables/prof_gga_grids.csv",
        ["budget", "t_over_d", "u_over_d", "double_occupancy", "total_energy_raw"],
        prof_rows,
    )
    for name in (
        "T_array.npy",
        "U_array.npy",
        "docc_B1.npy",
        "docc_B3.npy",
        "Etot_B1.npy",
        "Etot_B3.npy",
    ):
        record(ref2 / name, f"refs/ref_data/ref_data2/{name}")

    write_csv(
        dataset / "tables/ctqmc_anchors.csv",
        list(CTQMC_ROW.keys()),
        [CTQMC_ROW],
    )

    with (dataset / "provenance/source_files.csv").open(
        "w", encoding="utf-8", newline=""
    ) as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["path", "sha256", "bytes"], lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(source_files)

    report: dict[str, Any] = {}
    cross_check(dataset, repo_root, report)

    source_revision = subprocess.run(
        ["git", "-C", str(source), "rev-parse", "HEAD"],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
    ).stdout.strip()
    dirty = bool(
        subprocess.run(
            ["git", "-C", str(source), "status", "--porcelain"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
        ).stdout.strip()
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
            "source_dirty": dirty,
            "counts": {
                "compare_all_rows": len(
                    load_compare_rows(dataset / "tables/compare_all.csv")
                ),
                "nrg_rows": len(nrg_rows),
                "prof_rows": len(prof_rows),
            },
            "cross_check": report,
            "note": (
                "benchmark tables are gitignored run outputs in the source "
                "worktree; provenance is the per-file sha256 inventory"
            ),
        },
    )
    (dataset / "README.md").write_text(readme(), encoding="utf-8")

    manifest = {
        "schema_version": "gdmft.dataset.v1",
        "dataset_id": DATASET_ID,
        "title": "Cross-method benchmark references v1",
        "version": "0.1.0",
        "dataset_kind": "external_reference",
        "data_stage": "validated",
        "release_status": "draft",
        "created_at": created_at,
        "description": (
            "Audited cross-method benchmark merge (ghost-DMFT, gem g-RISB, "
            "DMFT-ED, professor gGA grids, NRG, CTQMC anchor) plus its "
            "source-of-truth reference tables, on LLK axes."
        ),
        "provenance": {
            "repository": "paper-consolidation",
            "revision": source_revision,
            "dirty": dirty,
            "command": [
                "python3",
                "studies/reference_data_import/import_benchmark_references.py",
            ],
            "python": sys.version.split()[0],
        },
        "conventions": {
            "energy_unit": "D",
            "half_bandwidth": 1.0,
            "interaction_axis": "u_over_d",
            "temperature_axis": "t_over_d",
            "double_occupancy": "per physical site",
            "grand_potential": "not recorded",
            "particle_hole": (
                "half filling; LLK total-energy convention "
                "E_tot = E_kin + U * docc (prof grids stored raw, add U/2)"
            ),
        },
        "external_sources": [LLK_SOURCE],
        "extensions": {
            "methods": [
                "ghost_dmft",
                "gga_gem",
                "dmft_ed",
                "gga_prof",
                "nrg",
                "ctqmc_llk",
            ],
            "cross_check": report,
        },
        "artifacts": artifact_entries(dataset),
    }
    write_json(dataset / "manifest.json", manifest)
    print(
        json.dumps(
            {"dataset": str(dataset), "cross_check": report}, indent=2, sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
