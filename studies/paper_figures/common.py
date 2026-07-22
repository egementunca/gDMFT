"""Shared data access for the paper figures — registered datasets only.

Reuses the gdmft library: `iter_point_rows` for the tables,
`atlas.derive.derive_dataset` for branches / U* / spinodal diagnostics
(validated: U* = 2.492 at T/D = 0.01 on v1 bethe m_g=3 bare), and
`atlas.poles.extract_pole_table` for the bath/pole parameters from the
lossless raw archives.
"""

from __future__ import annotations

import csv
import json
from functools import cache
from pathlib import Path

from gdmft.atlas.derive import derive_dataset
from gdmft.atlas.poles import extract_pole_table
from gdmft.data import iter_point_rows

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data/datasets"
OUT = REPO / "runs/figures"
BENCH = DATA / "references-benchmarks-v1/tables"

DS_DIR = {
    "v1": DATA / "single-site-gauge-matrix-v1",
    "v2": DATA / "single-site-scan-matrix-v2",
}

# Endpoint corridors (last crossing rung, first rung without a crossing):
# bethe per GGA_DMFT_BENCHMARK_20260715.md §5.3 (U*(0.01)=2.492 moves the
# corridor up from (0.008, 0.01)); square per the square benchmark note.
CORRIDORS = {"bethe": (0.01, 0.015), "square": (0.004, 0.005)}


def fnum(value: str | None) -> float | None:
    if value in (None, "", "null"):
        return None
    number = float(value)
    return number


@cache
def compare_rows() -> tuple[dict, ...]:
    """The registered cross-method benchmark merge, typed."""
    rows = []
    with (BENCH / "compare_all.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            rows.append(
                {
                    "method": row["method"],
                    "budget": int(row["budget"]),
                    "t": float(row["T"]),
                    "u": float(row["U_over_D"]),
                    "branch": row["branch"],
                    "z": fnum(row["Z"]),
                    "docc": fnum(row["docc"]),
                    "ekin": fnum(row["ekin"]),
                    "etot": fnum(row["etot"]),
                    "sumr2": fnum(row["sumR2"]),
                }
            )
    return tuple(rows)


@cache
def point_rows(ds: str) -> tuple[dict, ...]:
    return tuple(iter_point_rows(DS_DIR[ds] / "points.csv"))


def converged(row: dict, ds: str) -> bool:
    if ds == "v2":
        return row["source_category"] == "converged_branch"
    return row["source_converged"] == "true"


@cache
def derived(ds: str) -> dict:
    """Branch assembly + U* + spinodals via the validated atlas pipeline."""
    rows = point_rows(ds)
    thin = []
    grids: dict[str, tuple] = {}
    per_lattice: dict[str, tuple[set, set]] = {}
    for i, row in enumerate(rows):
        lattice = row["lattice"]
        u = float(row["u_over_d"])
        t = float(row["t_over_d"])
        us, ts = per_lattice.setdefault(lattice, (set(), set()))
        us.add(u)
        ts.add(t)
        thin.append(
            {
                "i": i,
                "lattice": lattice,
                "m_g": int(row["m_g"]),
                "gauge": row["gauge"],
                "family": row["solution_family"],
                "u": u,
                "t": t,
                "z": fnum(row["quasiparticle_weight_pole"]),
                "omega_d": fnum(row["grand_potential_over_d"]),
                "resnorm": fnum(row["residual_norm"]),
                "converged": converged(row, ds),
            }
        )
    for lattice, (us, ts) in per_lattice.items():
        grids[lattice] = (sorted(us), sorted(ts))
    # Campaign-duplicate resolution (v2 revision 0.2.0): where the fill
    # campaign re-solved an existing grid key, derived chains keep the
    # NEWEST campaign's row — otherwise chains fork wherever the campaigns
    # found different families (old satellite-dead native vs protected
    # fill). Provenance rule, not selection; all rows stay in point_rows.
    if ds == "v2":
        best: dict[tuple, int] = {}
        for j, entry in enumerate(thin):
            key = (entry["lattice"], entry["m_g"], entry["gauge"],
                   entry["family"], entry["u"], entry["t"])
            k = best.get(key)
            rank = rows[entry["i"]]["run_id"].startswith("d09-fill-")
            prev = (k is not None
                    and rows[thin[k]["i"]]["run_id"].startswith("d09-fill-"))
            if k is None or (rank and not prev):
                best[key] = j
        thin = [thin[j] for j in sorted(best.values())]
    return derive_dataset(ds, thin, grids)


@cache
def pole_table(ds: str) -> dict:
    """Per-row pole parameters from the registered lossless raw archives.

    v2 (0.2.0) carries TWO campaigns whose grids overlap, and overlapping
    keys share attempt ids across campaigns — so records are namespaced by
    the row's campaign (run_id prefix) and each campaign is read from its
    own archive: the 20260717 tar and the 20260721 fill JSONL."""
    rows = point_rows(ds)
    root = DS_DIR[ds]
    if ds == "v1":
        return extract_pole_table(
            root / "raw/roots.jsonl.gz",
            [row["point_id"] for row in rows], kind="jsonl"
        )
    from gdmft.atlas.poles import assemble_pole_table, collect_pole_records

    manifest = json.loads((root / "manifest.json").read_text())
    cells = set(manifest["grid"]["cells"])
    old = collect_pole_records(
        root / "raw/raw_campaign.tar.gz", kind="tar", cells=cells)
    merged = {f"d09|{pid}": entry for pid, entry in old.items()}
    fill_path = root / "raw/fill_attempts_20260721.jsonl.gz"
    if fill_path.exists():
        fill = collect_pole_records(fill_path, kind="v2-jsonl")
        merged.update(
            {f"fill|{pid}": entry for pid, entry in fill.items()})
    keys = [
        ("fill|" if row["run_id"].startswith("d09-fill-") else "d09|")
        + row["point_id"]
        for row in rows
    ]
    return assemble_pole_table(keys, merged)


def pole_params(ds: str, index: int) -> dict:
    red = pole_table(ds)["red"]
    def pick(key):
        value = red[key][index]
        if value is None:
            return None
        return abs(value) if key in ("eps1", "eta") else value
    return {key: pick(key) for key in ("v0", "v1", "eps1", "w", "eta")}


def branch(ds: str, lattice: str, mg: int, gauge: str, t: float, kind: str):
    """Row-index list + break positions for one assembled branch."""
    for entry in derived(ds)["branches"]:
        if (
            entry["lattice"] == lattice
            and entry["m_g"] == mg
            and entry["gauge"] == gauge
            and entry["kind"] == kind
            and abs(entry["t"] - t) < 1e-12
        ):
            return entry
    return None


def branch_series(ds, lattice, mg, gauge, t, kind, value):
    """(u, value(row)) along a branch with NaN gaps at continuity breaks."""
    entry = branch(ds, lattice, mg, gauge, t, kind)
    if entry is None:
        return [], []
    rows = point_rows(ds)
    us, ys = [], []
    for position, index in enumerate(entry["rows"]):
        us.append(float(rows[index]["u_over_d"]))
        ys.append(value(rows[index], index))
        if position in entry["breaks"]:
            us.append(float("nan"))
            ys.append(float("nan"))
    return us, ys


def ustar_curve(ds: str, lattice: str, mg: int, gauge: str):
    """[(t, ustar)] where a grand-potential crossing exists."""
    out = []
    for entry in derived(ds)["ustar"]:
        if (
            entry["lattice"] == lattice
            and entry["m_g"] == mg
            and entry["gauge"] == gauge
            and entry.get("ustar") is not None
        ):
            out.append((entry["t"], entry["ustar"]))
    return sorted(out)


def uc2_curve(ds: str, lattice: str, mg: int, gauge: str):
    out = []
    for entry in derived(ds)["spinodals"]:
        if (
            entry["lattice"] == lattice
            and entry["m_g"] == mg
            and entry["gauge"] == gauge
            and entry.get("uc2") is not None
        ):
            out.append((entry["t"], entry["uc2"]))
    return sorted(out)


def branch_temperatures(ds: str, lattice: str, mg: int, gauge: str, kind: str):
    out = set()
    for entry in derived(ds)["branches"]:
        if (
            entry["lattice"] == lattice
            and entry["m_g"] == mg
            and entry["gauge"] == gauge
            and entry["kind"] == kind
            and entry["rows"]
        ):
            out.add(entry["t"])
    return sorted(out)


def ruler_markers():
    """(t, ustar) fresh-ruler markers from the registered tables."""
    out = set()
    for name in (
        "prof_ghost_mg3_markers.csv",
        "prof_ghost_mg3_markers_T5orig.csv",
    ):
        path = BENCH / name
        if not path.exists():
            continue
        with path.open(newline="") as stream:
            for row in csv.DictReader(stream):
                try:
                    out.add((float(row["T"]), float(row["Ustar"])))
                except (KeyError, ValueError):
                    pass
    return sorted(out)
