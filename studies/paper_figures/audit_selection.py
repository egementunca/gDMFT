#!/usr/bin/env python3
"""Provenance / selection audit for the comparison figures.

Answers "are we mixing incompatible datasets / branches / gauges?" by (1)
printing the resolved selection matrix from the catalog policy, and (2)
cross-checking that the pre-merged benchmark table (compare_all.csv, used by
the Bethe scalar figures) is byte-identical to the raw datasets (used by the
parameter/function/V0 figures) for the same cell, branch, and gauge.

Run from studies/paper_figures/ :
    ../../.venv/bin/python audit_selection.py
"""

from __future__ import annotations

import math

import common
import compare
from gdmft.atlas import catalog


def _raw_branch(kind, t=0.001, ds="v1", lat="bethe", mg=3, gauge="bare"):
    entry = common.branch(ds, lat, mg, gauge, t, kind)
    if entry is None:
        return {}
    rows = common.point_rows(ds)
    return {
        round(float(rows[i]["u_over_d"]), 3): (
            common.fnum(rows[i]["double_occupancy"]),
            common.fnum(rows[i]["quasiparticle_weight_pole"]),
        )
        for i in entry["rows"]
    }


def _bench(method, budget, branch, t=0.001):
    out = {}
    for r in common.compare_rows():
        if r["method"] == method and r["budget"] == budget and r["branch"] == branch:
            if method == "dmft_ed" or math.isclose(r["t"], t, rel_tol=1e-6):
                out[round(r["u"], 3)] = (r["docc"], r["z"])
    return out


def _maxdiff(a, b):
    us = sorted(set(a) & set(b))
    md = mz = 0.0
    for u in us:
        (ad, az), (bd, bz) = a[u], b[u]
        if None not in (ad, bd):
            md = max(md, abs(ad - bd))
        if None not in (az, bz):
            mz = max(mz, abs(az - bz))
    return len(us), md, mz


def main():
    print("=" * 70)
    print("CATALOG PRIMARY ROUTES (gdmft.atlas.primary-route policy)")
    print("=" * 70)
    for lat in ("bethe", "square"):
        for mg in (1, 3):
            r = catalog.primary_route(lat, mg)
            print(f"  {lat:6} m_g={mg}: {r.dataset_id:28} gauge={r.gauge}")

    print("\n" + "=" * 70)
    print("PREFERRED GAUGE THIS RUN:",
          compare.GAUGE or "bare (policy default)")
    print("=" * 70)

    print("\n" + "=" * 70)
    print("CONSISTENCY: benchmark table (compare_all.csv) vs raw datasets")
    print("  (max |Δ| should be 0 — same underlying scan, pre-merged)")
    print("=" * 70)
    checks = [
        ("ghost metal  vs v1-bare metal ",
         _bench("ghost_dmft", 3, "metal"), _raw_branch("metal")),
        ("ghost insul  vs v1-bare insul ",
         _bench("ghost_dmft", 3, "insulator"), _raw_branch("insul")),
    ]
    gem_raw = {}
    for row in compare.gem_rows():
        if (row["lattice"] == "bethe" and row["budget"] == 3
                and row["dir"] == "up"
                and math.isclose(row["t"], 0.001, rel_tol=1e-6)):
            gem_raw[round(row["u"], 3)] = (row["docc"], row["z"])
    checks.append(("gem up       vs raw gem scan  ",
                   _bench("gga_gem", 3, "up"), gem_raw))
    ok = True
    for label, a, b in checks:
        n, md, mz = _maxdiff(a, b)
        flag = "OK" if md == 0 and mz == 0 else "*** MISMATCH ***"
        ok = ok and md == 0 and mz == 0
        print(f"  {label}: {n:3} pts  max|Δdocc|={md:.1e}  max|ΔZ|={mz:.1e}  {flag}")

    print("\n" + "=" * 70)
    print("BRANCH FAMILIES per cell (raw datasets, bare gauge)")
    print("=" * 70)
    for ds, lat, mg in (("v1", "bethe", 3), ("v2", "square", 3),
                        ("v2", "bethe", 1), ("v2", "square", 1)):
        fams = {}
        for row in common.point_rows(ds):
            if (row["lattice"] == lat and row["m_g"] == str(mg)
                    and row["gauge"] == "bare"):
                fams[row["solution_family"]] = fams.get(
                    row["solution_family"], 0) + 1
        print(f"  {ds} {lat:6} m_g={mg}: {fams}")

    print("\n" + "=" * 70)
    print("VERDICT:", "selection is coherent (all cross-checks = 0)" if ok
          else "*** INCONSISTENCY FOUND — investigate above ***")
    print("=" * 70)


if __name__ == "__main__":
    main()
