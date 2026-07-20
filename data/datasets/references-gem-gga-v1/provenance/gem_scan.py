#!/usr/bin/env python3
"""TRIQS/gem ghost-GA (g-RISB) scan on grids matched to the 20260715 rebuild.

Extends scripts/gem_compare.py (07-12 matched points) into the systematic
comparison dataset for the paper: B = 1 and B = 3 bath orbitals (== our
M_g = 1 / M_g = 3 budgets), U/D 0.5 -> 4.0 warm-chained in BOTH directions
(branch resolution inside the coexistence window), T rows matched to ours.

Protocol notes (deliberate, documented):
  - gem clone: refs/gem (branch `unstable`, the TRIQS default; the
    Temperature / thermal_refactored branches share the identical
    solve_impurity / SimpleED thermal path — audited 2026-07-15).
  - FULL Fock space at T > 0 (use_Ntot=False, use_Sz=False), following
    gem's own test_temperature: a restricted sector under-counts the
    partition function (solve_Hemb warns exactly this). The 07-12 pilot
    used the restricted 36-dim sector — fine at T/D <= 0.01, wrong warmer.
  - LLK energy convention: Etot = Ekin + U * docc (mu = 0, eloc = -U/2 PH
    setup; validate against LLK Table I: B=3, U/D=2.4 -> Etot = -0.06155).
  - Z is gem's Sigma-slope estimator (compute_Z); ours is pole-Z. Same at
    PH for a pole self-energy within one framework, but framework-sensitive
    across methods (LLK's own conclusion) — compare docc/energies tightly,
    Z qualitatively.
  - sumR2 = sum_a |R_a|^2 (spin-up column): gem's R is unnormalized
    (sumR2 = Z <= 1), our canonical R-gauge is normalized (sum R^2 = 1 with
    R_qp closing the books). Recorded per point for the convention doc.

Output: results/runs/20260715_paper_scans/gem_gga/gem_B<B>_T<T>.csv

Usage:
  .venv-numba/bin/python3 scripts/gem_scan.py --B 3 --rows 0.005,0.01
  .venv-numba/bin/python3 scripts/gem_scan.py --B 1 --rows all
  [--validate]   (one point: B=3, U=2.4, coldest row, print vs Table I)
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import os
import sys
import time

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEM = "refs/gem/python"
if GEM not in sys.path:
    sys.path.insert(0, GEM)

from gem.fragment import Fragment  # noqa: E402
from gem.lattice import Lattice  # noqa: E402
from gem.solvers.simple_ed import SimpleED  # noqa: E402

OUT = os.path.join(_ROOT, "results/runs/20260715_paper_scans/gem_gga")
NIMP = 2                      # one orbital x two spins
ITMAX, MIX, TOL, SPIN_PEN, MU = 400, 0.2, 1e-6, 1.0, 0.0

# semicircular discretization (2001 points, as the 07-12 pilot)
e_list = np.linspace(-1, 1, 2001)
wks = np.sqrt(1 - e_list ** 2)
wks /= wks.sum()
eks = np.array([np.kron(np.array([[e]], dtype=np.complex128), np.eye(2))
                for e in e_list])
LATTICE = Lattice(eks, wk_list=wks)

# U/D grid: 0.1 outside the transition region, 0.05 inside [2.0, 3.6]
U_GRID = np.unique(np.round(np.concatenate([
    np.arange(0.5, 4.0 + 1e-9, 0.1),
    np.arange(2.0, 3.6 + 1e-9, 0.05),
]), 3))

T_ROWS = [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2]


def solve(U, T, B, Lambda0, R0):
    nbath = NIMP * B
    ntot = NIMP + nbath
    eloc = np.zeros((NIMP, NIMP))
    eloc[0, 0] = eloc[1, 1] = -U / 2
    Ut = np.zeros((NIMP,) * 4)
    Ut[0, 0, 1, 1] = U
    Ut[1, 1, 0, 0] = U
    # full Fock space: exact thermal ensemble (see header)
    ed = SimpleED(ntot, use_Ntot=False, use_Sz=False, dtype=np.complex128)
    fr = Fragment(NIMP, nbath, eloc, Ut, ed, Lambda=Lambda0, R=R0, verbose=0)
    it = diff = None
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        for it in range(ITMAX):
            LATTICE.solve_qp([fr], T=T)
            fr.update_hybridization(T=T)
            fr.impose_spin_SU2_symmetry()
            fr.solve_impurity(MU, T=T, num_eig=10, spin_pen=SPIN_PEN)
            Lo, Ro = fr.Lambda.copy(), fr.R.copy()
            fr.update_self_energy(T=T)
            fr.impose_spin_SU2_symmetry()
            Ln, Rn = fr.Lambda, fr.R
            ln = np.linalg.eigh(Ln[::2, ::2])
            lo = np.linalg.eigh(Lo[::2, ::2])
            diff = max(np.abs(np.abs(lo[1] @ Ro[::2, ::2])
                              - np.abs(ln[1] @ Rn[::2, ::2])).max(),
                       np.abs(ln[0] - lo[0]).max())
            fr.Lambda = (1 - MIX) * Ln + MIX * Lo
            fr.R = (1 - MIX) * Rn + MIX * Ro
            fr.impose_spin_SU2_symmetry()
            if diff < TOL and it > 2:
                break
        Z = fr.compute_Z()[0, 0].real
        # Matsubara-slope Z at the row's own beta: robust at finite T where
        # the real-axis h=1e-8 slope estimator breaks on thermal Lambda
        # eigenvalues near z = 0 (observed: Z ~ 1 flat at T/D >= 0.05).
        w0 = np.pi * T
        sig0 = fr.compute_self_energy(1j * w0, mu=MU)[0, 0]
        Z_mats = float(1.0 / (1.0 - sig0.imag / w0))
        docc = fr.E2loc.real / U
        ekin = LATTICE.compute_ekin([fr], T).real
    etot = ekin + fr.E2loc.real
    sumR2 = float(np.sum(np.abs(fr.R[::2, ::2]) ** 2))
    st = structure_of(fr.Lambda, fr.R, U)
    return dict(Z=Z, Z_mats=Z_mats, docc=docc, ekin=ekin, etot=etot,
                sumR2=sumR2, iters=it, diff=float(diff),
                converged=int(diff < TOL),
                Lambda=fr.Lambda.copy(), R=fr.R.copy(),
                D=fr.D.copy(), Lambda_c=fr.Lambda_c.copy(), **st)


def structure_of(Lam, R, U):
    """Framework-invariant converged structure from gem's (Lambda, R),
    spin-up block: the mode spectrum (lam, |Rt|^2 = the R vector), the
    self-energy pole pair (zeros of M(z)=sum|Rt|^2/(z-lam), weights -1/M'),
    and the linear term sig_lin = 1 - 1/sumR2. Cheap; same objects as
    scripts/gem_structure_compare.py. Returned as ';'-joined strings."""
    lam, Uv = np.linalg.eigh(Lam[::2, ::2])
    Rt = (Uv.conj().T @ R[::2, ::2]).ravel()
    r2 = np.abs(Rt) ** 2
    s = float(r2.sum())
    B = lam.size
    if B >= 2:
        poly = np.zeros(B)
        for a in range(B):
            poly = poly + r2[a] * np.poly([lam[b] for b in range(B) if b != a])
        roots = np.sort(np.roots(poly).real)
        Mp = lambda z: -float(np.sum(r2 / (z - lam) ** 2))  # noqa: E731
        w2 = np.array([-1.0 / Mp(z0) for z0 in roots])
    else:
        roots, w2 = np.zeros(0), np.zeros(0)
    j = lambda a: ";".join(f"{x:.6g}" for x in a)  # noqa: E731
    return dict(gem_lam=j(lam), gem_r2=j(r2),
                gem_sig_poles=j(roots), gem_sig_w2=j(w2),
                gem_sig_lin=(1.0 - 1.0 / s) if s else float("nan"))


def run_row(B, T):
    t0 = time.time()
    rows = []
    for direction, grid in (("up", U_GRID), ("down", U_GRID[::-1])):
        L0 = R0 = None
        for U in grid:
            t1 = time.time()
            try:
                r = solve(float(U), T, B, L0, R0)
            except Exception as e:
                # gem's internal thermal fits can die (SVD non-convergence
                # observed at T/D=0.005 inside update_self_energy_thermal_
                # penalty). Record the casualty, drop the warm state, go on.
                print(f"  [gem B={B} T={T:g} {direction:4s} U/D={U:4.2f}] "
                      f"CRASH {type(e).__name__}: {e}", flush=True)
                L0 = R0 = None
                rows.append(dict(B=B, T=T, U_over_D=float(U),
                                 direction=direction, Z=np.nan,
                                 Z_mats=np.nan, docc=np.nan, ekin=np.nan,
                                 etot=np.nan, sumR2=np.nan, iters=-1,
                                 diff=np.nan, converged=0,
                                 gem_lam="", gem_r2="", gem_sig_poles="",
                                 gem_sig_w2="", gem_sig_lin=np.nan,
                                 wall=round(time.time() - t1, 2)))
                continue
            if r["converged"]:
                L0, R0 = r["Lambda"], r["R"]
            # drop the matrix-valued keys before the row goes to CSV
            for k in ("Lambda", "R", "D", "Lambda_c"):
                r.pop(k, None)
            rows.append(dict(B=B, T=T, U_over_D=float(U),
                             direction=direction,
                             **{k: v for k, v in r.items()},
                             wall=round(time.time() - t1, 2)))
            print(f"  [gem B={B} T={T:g} {direction:4s} U/D={U:4.2f}] "
                  f"Z={r['Z']:.4f} D={r['docc']:.5f} Etot={r['etot']:.5f} "
                  f"({'ok' if r['converged'] else 'STALL'} it={r['iters']})",
                  flush=True)
    os.makedirs(OUT, exist_ok=True)
    fn = os.path.join(OUT, f"gem_B{B}_T{T:g}.csv")
    fields = ["B", "T", "U_over_D", "direction", "Z", "Z_mats", "docc",
              "ekin", "etot", "sumR2", "iters", "diff", "converged",
              "gem_lam", "gem_r2", "gem_sig_poles", "gem_sig_w2",
              "gem_sig_lin", "wall"]
    with open(fn, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"gem B={B} T/D={T:g}: wrote {os.path.basename(fn)} "
          f"({len(rows)} rows, {time.time() - t0:.0f}s)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--B", type=int, default=3)
    ap.add_argument("--rows", default=None)
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args()

    if a.validate:
        r = solve(2.4, 0.001, 3, None, None)
        print(f"VALIDATE B=3 U/D=2.4 T/D=0.001: Etot={r['etot']:.5f} "
              f"(LLK Table I g-RISB Nb=3: -0.06155; CTQMC -0.0621(1))\n"
              f"  Z={r['Z']:.5f} docc={r['docc']:.5f} ekin={r['ekin']:.5f} "
              f"sumR2={r['sumR2']:.5f} iters={r['iters']}")
        return

    rows = T_ROWS if a.rows in (None, "all") else \
        [float(x) for x in a.rows.split(",")]
    for T in rows:
        run_row(a.B, T)


if __name__ == "__main__":
    main()
