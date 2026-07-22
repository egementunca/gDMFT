#!/usr/bin/env python3
"""Census: the gap report that defines the single-source completion campaign.

Declares the canonical comparison grid (user-approved 2026-07-21):
  * U/D: uniform 0.05 over [0.5, 4.0] plus 0.01-step windows through each
    lattice's coexistence region (window derived from the registered
    m_g=3 first-order data of that lattice);
  * T/D: the full 17-row ladder on BOTH lattices (square extended).

Then reports, for every cell of
  lattice x m_g x solve-route {bare, canonical-r-reoptimized,
  canonical-r-native} x arm {metal, insulator} x T,
how much of the canonical grid is covered by converged registered rows
(v1/D08 and v2/D09 merged — the completion target is one dataset), plus:
  * satellite-liveness per chain (m_g=3): the v2-native trap generalized;
  * far-pole cap audit in U/D and raw units (universal-cap check);
  * m_g=1 exact-T=0 anchor coverage;
  * gem (B=1,3) and DMFT-ED (N_b=1,3,5) coverage on the same grid.

Read-only. Output: a printed report plus
  runs/census/census_report.md  and  runs/census/missing_points.csv.
Nothing is solved from here; the reviewed gap list drives the fill runs.
"""

from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path

import common
import compare

OUT_DIR = common.OUT.parent / "census"

# ---------------------------------------------------------------- grid ----
T_LADDER = (
    0.001, 0.002, 0.003, 0.004, 0.005, 0.0065, 0.008, 0.01,
    0.015, 0.02, 0.025, 0.03, 0.05, 0.07, 0.1, 0.15, 0.2,
)
U_COARSE = tuple(round(i / 100.0, 3) for i in range(50, 401, 5))

# Solve routes that carry independent numerical content.  The exact
# conversion (canonical-r-converted) is a chart of its parent and is not a
# census axis.
ROUTES = ("bare", "canonical-r-reoptimized", "canonical-r-native")

# Structural expectations — absences that are physics results, not gaps.
#   * m_g=1 insulator arm: documented negative result (no gated insulator).
#   * m_g=3 exact T=0: no exact-T=0 machinery for the 5-parameter route.
STRUCTURAL = {
    "mg1-insulator": "m_g=1 insulator arm fails everywhere (the documented "
                     "negative result); absence is expected",
    "mg3-T0": "m_g=3 has no exact-T=0 solver route; T=0 anchors are "
              "m_g=1 only",
}

# Far-pole boxes as used by the historical solves (U/D units) and the raw
# half-bandwidth of each lattice in solver energy units (t = 0.5 both).
EPS1_BOX = {"bethe": 12.0, "square": 6.0}
D_RAW = {"bethe": 1.0, "square": 2.0}

SAT_LIVE = 0.05  # V1 above this = live satellite channel


def r3(x: float) -> float:
    return round(x, 3)


# First-order rows exist only below the endpoint corridor; warm rows carry
# grid-edge artifacts (Uc2 = 4.0) and must not shape the window.
CORRIDOR_T_MAX = {"bethe": 0.010, "square": 0.004}


def fine_window(lattice: str) -> tuple[float, float]:
    """Coexistence window from the registered m_g=3 first-order data
    (first-order T rows only)."""
    src = {"bethe": ("v1", "bare"), "square": ("v2", "bare")}[lattice]
    ds, gauge = src
    cap = CORRIDOR_T_MAX[lattice] + 1e-12
    ustars = [u for t, u in common.ustar_curve(ds, lattice, 3, gauge)
              if t <= cap]
    uc2s = [u for t, u in common.uc2_curve(ds, lattice, 3, gauge)
            if t <= cap]
    lo = min(ustars) - 0.05
    hi = max(uc2s) + 0.05
    return (r3(int(lo * 20) / 20.0), r3((int(hi * 20) + 1) / 20.0))


def canonical_grid(lattice: str) -> tuple[tuple[float, ...], tuple[float, float]]:
    lo, hi = fine_window(lattice)
    fine = [r3(lo + 0.01 * i) for i in range(int(round((hi - lo) / 0.01)) + 1)]
    return tuple(sorted(set(U_COARSE) | set(fine))), (lo, hi)


# ------------------------------------------------------------- coverage ----
def arm_of(family: str) -> str:
    fam = (family or "").lower()
    if "metal" in fam:
        return "metal"
    if "insul" in fam or fam == "ins":
        return "insulator"
    return "other"


def covered_points() -> dict:
    """(lattice, m_g, route, arm, T) -> set of covered canonical U (merged
    over datasets), counting only converged rows."""
    cov: dict = collections.defaultdict(set)
    raw_families: dict = collections.defaultdict(set)
    for ds in ("v1", "v2"):
        for row in common.point_rows(ds):
            gauge = row["gauge"]
            if gauge not in ROUTES:
                continue
            if ds == "v1" and row["lattice"] == "square":
                continue  # N_k=16 legacy evidence, never coverage
            if not common.converged(row, ds):
                continue
            lattice = row["lattice"]
            m_g = int(row["m_g"])
            arm = arm_of(row["solution_family"])
            raw_families[(ds, lattice, m_g, gauge)].add(row["solution_family"])
            t = float(row["t_over_d"])
            tk = next((tt for tt in T_LADDER if abs(tt - t) < 1e-9), None)
            if tk is None:
                continue
            cov[(lattice, m_g, gauge, arm, tk)].add(r3(float(row["u_over_d"])))
    return {"cov": cov, "families": raw_families}


def satellite_liveness() -> list[tuple]:
    """Per (ds, lattice, gauge, family, T): max V1 for m_g=3 chains."""
    out = []
    for ds in ("v1", "v2"):
        rows = common.point_rows(ds)
        acc: dict = collections.defaultdict(float)
        n: dict = collections.defaultdict(int)
        for i, row in enumerate(rows):
            if int(row["m_g"]) != 3 or row["gauge"] not in ROUTES:
                continue
            if ds == "v1" and row["lattice"] == "square":
                continue  # legacy
            if not common.converged(row, ds):
                continue
            p = common.pole_params(ds, i)
            if p["v1"] is None:
                continue
            key = (ds, row["lattice"], row["gauge"],
                   arm_of(row["solution_family"]), float(row["t_over_d"]))
            acc[key] = max(acc[key], p["v1"])
            n[key] += 1
        for key in sorted(acc):
            out.append((*key, acc[key], n[key]))
    return out


def cap_audit() -> list[dict]:
    out = []
    for ds in ("v1", "v2"):
        rows = common.point_rows(ds)
        stats: dict = collections.defaultdict(lambda: [0.0, 0.0, 0, 0])
        for i, row in enumerate(rows):
            if row["gauge"] not in ROUTES or not common.converged(row, ds):
                continue
            p = common.pole_params(ds, i)
            lattice = row["lattice"]
            s = stats[(ds, lattice, int(row["m_g"]), row["gauge"])]
            if p.get("eps1") is not None:
                s[0] = max(s[0], p["eps1"])
                s[3] += 1
                if p["eps1"] >= 0.95 * EPS1_BOX[lattice]:
                    s[2] += 1
            if p.get("eta") is not None:
                s[1] = max(s[1], p["eta"])
        for (ds_, lat, mg, gauge), (e1max, etamax, npin, ntot) in sorted(stats.items()):
            out.append({
                "ds": ds_, "lattice": lat, "m_g": mg, "gauge": gauge,
                "eps1_max": e1max, "eps1_max_raw": e1max * D_RAW[lat],
                "eps1_box": EPS1_BOX[lat],
                "eps1_box_raw": EPS1_BOX[lat] * D_RAW[lat],
                "pinned": npin, "rows": ntot, "eta_max": etamax,
                "eta_max_raw": etamax * D_RAW[lat],
            })
    return out


def mg1_t0_coverage() -> dict:
    out = {}
    for ds in ("v1", "v2"):
        for row in common.point_rows(ds):
            if int(row["m_g"]) != 1 or row["gauge"] != "bare":
                continue
            t = float(row["t_over_d"])
            if t > 1e-6:
                continue
            if not common.converged(row, ds):
                continue
            key = (row["lattice"], arm_of(row["solution_family"]))
            out.setdefault(key, set()).add(r3(float(row["u_over_d"])))
    return out


def gem_coverage() -> dict:
    cov: dict = collections.defaultdict(set)
    for g in compare.gem_rows():
        tk = next((tt for tt in T_LADDER if abs(tt - g["t"]) < 1e-9), None)
        if tk is None:
            continue
        cov[(g["lattice"], g["budget"], g["dir"], tk)].add(r3(g["u"]))
    return cov


def ed_coverage() -> dict:
    cov: dict = collections.defaultdict(set)
    for row in common.compare_rows():
        if row["method"] != "dmft_ed":
            continue
        cov[(row["budget"], row["branch"])].add(r3(row["u"]))
    return cov


# --------------------------------------------------------------- report ----
def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    missing_rows: list[dict] = []

    def emit(text: str = "") -> None:
        print(text)
        lines.append(text)

    grids = {}
    emit("# Census — canonical grid and gap report")
    emit()
    emit("## Canonical grid")
    for lattice in ("bethe", "square"):
        grid, window = canonical_grid(lattice)
        grids[lattice] = grid
        emit(f"- {lattice}: {len(grid)} U points "
             f"(coarse 0.05 on [0.5, 4.0] + 0.01 window [{window[0]}, "
             f"{window[1]}]), T-ladder {len(T_LADDER)} rows "
             f"{T_LADDER[0]}..{T_LADDER[-1]}")
    emit()

    data = covered_points()
    cov = data["cov"]

    emit("## Ghost cells: missing canonical points per (cell, route, arm)")
    emit()
    emit("route legend: bare = solve-native; reopt = physical-gauge refit "
         "seeded from bare; native = independent physical-gauge "
         "continuation. Merged over v1+v2; converged rows only.")
    emit()
    total_missing = collections.Counter()
    for lattice in ("bethe", "square"):
        grid = set(grids[lattice])
        for m_g in (1, 3):
            for gauge in ROUTES:
                for arm in ("metal", "insulator"):
                    if m_g == 1 and arm == "insulator":
                        continue  # structural, reported separately
                    per_t = []
                    n_missing = 0
                    for t in T_LADDER:
                        have = cov.get((lattice, m_g, gauge, arm, t), set())
                        miss = sorted(grid - have)
                        n_missing += len(miss)
                        per_t.append((t, len(have & grid), len(miss)))
                        for u in miss:
                            missing_rows.append({
                                "lattice": lattice, "m_g": m_g,
                                "route": gauge, "arm": arm, "T": t, "U": u,
                            })
                    label = {"bare": "bare",
                             "canonical-r-reoptimized": "reopt",
                             "canonical-r-native": "native"}[gauge]
                    key = f"{lattice} mg{m_g} {label:6s} {arm:9s}"
                    tot = len(grid) * len(T_LADDER)
                    total_missing[(lattice, m_g, gauge)] += n_missing
                    frac = 100.0 * (tot - n_missing) / tot
                    gap_t = [f"{t:g}" for t, _, m in per_t if m > 0]
                    emit(f"  {key}: {tot - n_missing}/{tot} covered "
                         f"({frac:4.1f}%) — gapped T rows: "
                         f"{', '.join(gap_t) if gap_t else 'none'}")
        emit()

    emit("## Satellite liveness (m_g=3 chains; dead = max V1 < "
         f"{SAT_LIVE})")
    dead = []
    for ds, lattice, gauge, arm, t, v1max, nrows in satellite_liveness():
        if arm == "metal" and v1max < SAT_LIVE:
            dead.append((ds, lattice, gauge, t, v1max, nrows))
    if dead:
        for ds, lattice, gauge, t, v1max, nrows in dead:
            emit(f"  DEAD metal chain: {ds} {lattice} {gauge} T={t:g} "
                 f"(max V1={v1max:.4f}, {nrows} rows)")
    else:
        emit("  all metal chains live")
    emit()

    emit("## Far-pole cap audit (universal-cap check)")
    for s in cap_audit():
        if s["m_g"] != 3:
            continue
        emit(f"  {s['ds']} {s['lattice']} mg3 {s['gauge']}: "
             f"eps1 max {s['eps1_max']:.3f}/box {s['eps1_box']:g} (U/D) = "
             f"raw {s['eps1_max_raw']:.3f}/box {s['eps1_box_raw']:g}; "
             f"pinned {s['pinned']}/{s['rows']}; "
             f"eta max {s['eta_max']:.3f} (raw {s['eta_max_raw']:.3f})")
    emit()

    emit("## m_g=1 exact-T=0 anchors (bare)")
    emit("  NOTE: v1's m_g=1 cells hold the exotic-family evidence study "
         "(families 'dark'/'coupled'), not physical arms; its T~1e-8 rows "
         "are that study's cold foot. The exact-T=0 BR arm was solved in "
         "the dmft repo (results/runs/20260710_rerun_mg1) but never "
         "registered — an IMPORT gap, then a solve gap for the canonical "
         "grid's extra points.")
    t0 = mg1_t0_coverage()
    for lattice in ("bethe", "square"):
        grid = set(grids[lattice])
        have = t0.get((lattice, "metal"), set())
        emit(f"  {lattice} metal T=0: {len(have & grid)}/{len(grid)} "
             f"canonical U covered")
        for u in sorted(grid - have):
            missing_rows.append({"lattice": lattice, "m_g": 1,
                                 "route": "bare", "arm": "metal",
                                 "T": 0.0, "U": u})
    emit()

    emit("## gem coverage (canonical grid)")
    gcov = gem_coverage()
    for lattice in ("bethe", "square"):
        grid = set(grids[lattice])
        for budget in (1, 3):
            for direction in ("up", "down"):
                n_missing = 0
                gap_t = []
                for t in T_LADDER:
                    have = gcov.get((lattice, budget, direction, t), set())
                    miss = grid - have
                    n_missing += len(miss)
                    if miss:
                        gap_t.append(f"{t:g}")
                    for u in sorted(miss):
                        missing_rows.append({
                            "lattice": lattice, "m_g": f"gem-B{budget}",
                            "route": "gem", "arm": direction, "T": t,
                            "U": u,
                        })
                tot = len(grid) * len(T_LADDER)
                emit(f"  gem {lattice} B={budget} {direction:4s}: "
                     f"{tot - n_missing}/{tot} covered — gapped T rows: "
                     f"{len(gap_t)}/{len(T_LADDER)}")
    emit()

    emit("## DMFT-ED coverage (T=0 anchors, coarse grid target)")
    ecov = ed_coverage()
    for budget in (1, 3, 5):
        for branch in ("up", "down"):
            have = ecov.get((budget, branch), set())
            miss = sorted(set(U_COARSE) - have)
            emit(f"  ED N_b={budget} {branch:4s}: "
                 f"{len(set(U_COARSE)) - len(miss)}/{len(U_COARSE)} coarse "
                 f"U covered")
            for u in miss:
                missing_rows.append({"lattice": "bethe",
                                     "m_g": f"ed-Nb{budget}",
                                     "route": "dmft-ed", "arm": branch,
                                     "T": 0.0, "U": u})
    emit()

    emit("## Structural absences (not gaps)")
    for key, text in STRUCTURAL.items():
        emit(f"  - {key}: {text}")
    emit()

    counter = collections.Counter(
        (r["lattice"], str(r["m_g"]), r["route"]) for r in missing_rows
    )
    emit("## Fill-list summary (missing solve points)")
    for (lattice, m_g, route), n in sorted(counter.items()):
        emit(f"  {lattice:6s} {m_g:8s} {route:12s}: {n:6d} points")
    emit(f"  TOTAL: {len(missing_rows)} points")

    (OUT_DIR / "census_report.md").write_text("\n".join(lines) + "\n")
    with (OUT_DIR / "missing_points.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=["lattice", "m_g", "route", "arm", "T", "U"]
        )
        writer.writeheader()
        writer.writerows(missing_rows)
    print(f"\nwrote {OUT_DIR / 'census_report.md'} and missing_points.csv "
          f"({len(missing_rows)} rows)")


if __name__ == "__main__":
    sys.exit(main())
