# Square-Lattice Resolution Decision (Stage 1)

**Decision:** adopt **`continuum_elliptic_dos`** as the canonical square-lattice
route for all local single-site thermodynamic observables. **`N_k=16`** is
retained only as historical finite-grid data. **`N_k=64`** is accepted for a
*declared subset* of claims (energies, D_occ, n, Ω) but **not** for sub-percent
`Z`.

## What was done

A new selectable, provenance-recorded lattice-integration route was added to the
solver's lattice API (`BHFM2.core.solve_min._lattice_quadrature`, selected by
`ModelParamsMin.lattice_quadrature`), **backward-compatibly**: the default
`uniform_kmesh` reproduces the pre-edit stationary solutions exactly (verified —
a stored `N_k=16` root's residual re-evaluates to its stored `resnorm`
2.207e-05). The continuum route is a graded 1-D integral of the exact square DOS
`ρ(ε)=K(m)/(2π²t)`, `m=1-(ε/4t)²`; its U=0 anchor matches `E_kin/D = -4/π²` to
**8e-9** (`square_integration_registry.json`).

A **true stationary-solution pilot** (not a fixed-root reevaluation) re-solved
the symmetric M_g=3 equations at all four routes from matched physical parents,
`U/D ∈ {0,1,2,2.5,3.0}`, `T/D ∈ {0.001,0.01}`, metal + insulator branches
(`results/runs/20260717_square_resolution/`, 80 rows, 68 converged; the 12
non-converged are physical — the insulator branch does not exist at `U/D=1`, and
the metal at `U/D=3.0` sits at the spinodal). U=0 uses the analytic
non-interacting values per route.

## Convergence (metal, cold `T/D=0.001`; continuum = reference)

Max relative error of the **best mesh `N_k=64`** vs the continuum reference,
predeclared gate = **0.1%**:

| observable | max \|rel N_k=64\| | gate |
|---|---|---|
| `Z_pole`, `Z_fermi` | **0.141%** (at `U/D=2`) | **FAIL** |
| `D_occ` | 0.069% | PASS |
| `Omega/D` | 0.012% | PASS |
| `E_kin/D` | 0.061% | PASS |
| `E_pot/D`, `E_tot/D` | 0.057–0.069% | PASS |
| `n` | 0.000% | PASS |

`N_k=16` fails every observable (`Z` 2.8–5.0%, `E_kin/D` 0.6–1.5%, `D_occ`
0.7–2.1%). Full signed absolute / relative / scale-aware differences per point
are in `square_stationary_convergence.csv`; per-observable gate verdicts in
`square_claim_gate.csv`; branch identity across routes in
`square_branch_matches.csv`.

`Z` converges slowest because it is the residue at the van Hove Fermi level —
exactly where the uniform mesh is worst. The continuum route removes this bias
by construction.

## Branch / spinodal caveat

Near the spinodal (`U/D=3.0`) the metal branch does not cleanly converge
(`resnorm ≈ 5.6e-3`) and is quadrature-**insensitive** because branch
instability, not quadrature, dominates. At warm `T/D=0.01`, `U/D≥2.5` the metal
`Z` has already collapsed (`Z≈0.008`) and is likewise quadrature-insensitive.
**No sub-percent `Z` claim is admissible at or past the spinodal** without adding
the nearest bracketing `U/D` points from the dense grid; there, report
scale-aware differences (`abs / max(|x|,0.05)`), not raw relative ratios.

## Predeclared claim gate (applied)

For an observable entering a sub-percent square comparison: (1) quadrature
uncertainty ≤ 0.1%; (2) ≤ 20% of the plotted method difference; (3) unambiguous
branch match; (4) residuals below threshold. Criterion (2) is per-claim and must
be checked against the specific gem/ED method difference at each plotted point;
adopting the continuum route removes quadrature as a confound so (1) is met for
every local observable.

## Decision (chosen options)

- **`continuum elliptic DOS` adopted as the canonical square route** for
  `Z`, `D_occ`, `n`, `Omega/D`, `E_kin/D`, `E_pot/D`, `E_tot/D`.
- **`N_k=16` retained only as historical finite-grid data** (in the D08 export,
  already tagged `quadrature_resolution_status = preliminary_...`).
- **`N_k=64` accepted for a declared subset of claims — TIGHTENED by the v2
  full-grid gate.** The v1 summary (cold metal only) had energies/`D_occ` at
  ≤0.07%; the v2 gate across **both temperatures, both branches, both `M_g`, and
  both solver routes** (`square_claim_gate_v2.csv`, 444 rows, Nk64 passes 338)
  shows the worst-case Nk64 error is **`Z` 0.18%, `D_occ` 0.19%, `E_kin/D`
  0.16%, `E_pot/D`/`E_tot/D` 0.19%** — all **FAIL** 0.1%. Only **`Omega/D`
  (0.016%) and `n` (0%) PASS** at Nk=64. So `N_k=64` is accepted **only for
  `Omega/D` and `n`**; **`Z`, `D_occ`, and every energy require the continuum
  route** for a sub-percent square claim.
- **Sub-percent `Z`, `D_occ`, and energy square claims must use the continuum
  route.** (Consequently the Stage-3 square scans use the continuum route.)
- A fine `A(k,ω)` display calculation may still use a dense uniform k-mesh; that
  is a visualization, not a thermodynamic accuracy claim.

## v2 correction note

This decision was re-derived from the **v2 pilot** (`square_pilot_v2_raw.csv`),
which corrects the v1 pilot (preserved as prototype evidence): it adds `M_g=1`,
distinguishes `bare_native` vs `R_native` solver routes, records the actual
integration node count per row, de-duplicates the U=0 rows, and applies the gate
across both temperatures and both branches (v1 gated only cold metal). The
continuum node count (`n_eps=4001`) is node-convergence-validated: `|E_kin/D +
4/π²|` = 1.1e-6/2.8e-7/7.3e-8/2.2e-8 at `n_eps` = 1001/2001/4001/8001
(`square_integration.py`).

## What this does NOT establish

This pilot resolves the *quadrature* uncertainty. It does not by itself validate
the ghost-DMFT vs gem/ED cross-method agreement (that is a separate claim, gated
per point by criterion (2)). It also does not re-solve the dense square grid —
per the task, the dense grid is only rerun if a specific claim needs a
continuum-route point not already covered here.
