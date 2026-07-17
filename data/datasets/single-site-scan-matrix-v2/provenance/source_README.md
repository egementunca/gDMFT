# 09 — Single-Site Publication Validation And Scan-Matrix Completion

> ## v2 lossless data-preservation correction (2026-07-17)
>
> The v1 scan matrix ran correctly but its per-attempt rows were not lossless
> (reduced to sumV2/sumW2, single evidence route, mixed square node counts) and
> the canonical data lived only under gitignored `results/runs/`. This was
> corrected **without new physics**:
>
> - **v1 preserved** verbatim: producer `scripts/gauge_matrix/scan_matrix_v1.py`,
>   data `results/runs/20260717_scan_matrix/` (91 T-files) — untouched.
> - **Lossless v2** (`scan_matrix.py` → `results/runs/20260717_scan_matrix_v2/`):
>   every attempt is a JSON record with the complete native `x_sol`, full g /
>   bare-h / canonical-h arrays (no sumV2/sumW2 reduction), the full optimizer
>   result (status/message/nfev/njev/cost/optimality/active_mask + per-bound
>   distances), the complete residual vector + block norms, continuation parent +
>   seed provenance, all observables raw+reduced, and quadrature/node/commit ids.
> - **Three evidence records per bare root**: `bare_native` + exact
>   `R_converted_from_bare` + `R_reoptimized_from_bare` (seeded from the
>   conversion); `R_native_continuation` kept separate. **15,240 attempts**,
>   **3,368 bare/R pairs**.
> - **Common square discretization**: both square budgets use `n_eps=2001`,
>   **certified** by an interacting-node convergence test (≤1.04e-5 vs n_eps=8001;
>   `square_node_certification.json`).
> - **Tracked canonical data**: deterministic `raw_campaign.tar.gz` (6.6 MB —
>   every per-T
>   JSONL + registries + superseded runs). The extracted `raw_campaign/` and the
>   44 MB `stage3_attempts.jsonl` are gitignored (regenerable via
>   `build_stage3_v2.py`, which extracts the archive). A **clean checkout rebuilds
>   and verifies D08+D09 without `results/runs/`** (`verify_clean_checkout.py`);
>   D08 is streamed from its tracked `roots.jsonl.gz`.
> - **Coverage terminology** (`coverage_after_v2.csv`): attempted_keys /
>   keys_with_at_least_one_converged_branch / converged_branch_attempts /
>   failed_branch_attempts / branch_not_found / solver_failed. **Every registered
>   key on all 7 grids has ≥1 converged branch.** A dark/non-converged Z=0 attempt
>   is `branch_not_found` (Mg=1 BR insulator) or `failed_branch`, never a physical
>   result. `unresolved_conditions_v2.csv` lists every failed condition (351,
>   mostly mg3 near-spinodal R attempts) — recorded, never synthesized.
> - **Pairing diagnostics** (`bare_R_pairing.csv`): per bare root dZ/dD/dOmega vs
>   converted + reoptimized; exact-conversion dZ ≤ 3.9e-15; `different_basin` /
>   `bound_limited` / `floor_limited` flagged. **Mg=1 bound-expansion check**
>   (`mg1_bound_expansion.csv`): the Mg=1 bare h-params are cap-limited (Z drifts
>   ~1–2% under h-bound expansion along the flat i-ω renormalizer direction) →
>   flagged `bound_limited`, **not** labelled converged; the cap-independent value
>   is the independent R fit.
> - **Acceptance tests**: `tests/test_stage3_v2.py` (9/9) + the clean-checkout
>   verifier — all pass. `physical` / `branch_continuous` / `selected` remain unset.
>
> The v1 tables below (`coverage_before/after.csv`, `scan_command_manifest.csv`,
> etc.) are retained as the v1 record; the **authoritative lossless data is v2**.


Publication-grade numerical resolution + reference comparisons, then execution
of the registered single-site scan matrix. Built on deliverable 08, treating its
report as a claim verified against the live worktree.

> **Provenance (reproducibility-grade).** The scoped single-site checkpoint
> tracks these artifacts, builders, tests, and canonical archives. The
> `code_commit` stamped in run rows is `1a3af4a`, the execution base. The
> relevant tracked solver difference is preserved in `dirty_patch.diff`; it is
> deliberately scoped to `BHFM2/core/solve_min.py` and does not embed unrelated
> paper, NCS, or analysis changes. Builders and tests that were untracked when
> the runs executed are pinned individually by hash. The final containing
> commit is verified directly with
> `verify_clean_checkout.py --commit SHA`.

## Stage 0 — verified (see D08 README, corrected)

All six D08 builds + both test suites + the legacy audit reproduce; every count
independently confirmed (8568 bare + 8568 exact R; 912 R-native; 2180 R-reopt;
manifest 1467 raw = 922 canonical + 545 checkpoint, 83 non-raw; gem 884/400 ⊆
grid). D08's provenance wording distinguishes the execution base from the
containing repository checkpoint; the old
`square_quadrature_pilot.csv` was flagged (its "Nk=64" rows are a pre-existing
stationary solve whose log does not record the mesh value — superseded by
Stage 1).

## Stage 1 — square resolution (continuum route)

Selectable route added to the solver lattice API (`solve_min._lattice_quadrature`
via `ModelParamsMin.lattice_quadrature`), backward-compatible (default
`uniform_kmesh` reproduces stored roots exactly). **Node-convergence** of
`continuum_elliptic_dos` at U=0: `|E_kin/D + 4/π²|` = 1.1e-6 / 2.8e-7 / 7.3e-8 /
2.2e-8 at n_eps = 1001 / 2001 / 4001 / 8001 → **n_eps=4001 converged** (the scan
value; recorded per row). Pilots: `square_pilot_raw.csv` (v1, Mg=3, preserved) +
`square_pilot_v2_raw.csv` (adds Mg=1, bare AND R-native routes, integration-node
count per row, U=0 de-duplicated, both branches, both T).

**Decision (`square_resolution_decision.md`):** **continuum adopted as the
canonical square route.** Nk=64 accepted for energies/`D_occ`/`n` (≤0.07% vs
continuum) but **not** sub-percent `Z` (0.14%); Nk=16 historical only. The full
scan matrix uses the continuum route for square (`n_eps=4001`).

## Stage 2 — LLK DMFT-ED (`ed_*`, PDF-validated)

Worked directly from `refs/PhysRevB.107.L121104-accepted.pdf` (sha
`32f39c77…`, hashed). `scripts/dmft_ed_llk.py` (decoupled — the Bethe lattice
self-consistency is **vendored**, not imported, so LLK results do not depend on
the dirty square additions in `dmft_ed_bench.py`; the stable-import provenance is
pinned in `DEPENDENCIES`). Adds: CG bath-fit (paper's optimizer, matches LM);
normalized χ² (with SciPy's ½-cost kept separate, never relabelled); a
budget-independent **common diagnostic norm**; **five separated flags**
(`fixed_point_converged`, `fit_optimizer_converged`, `bath_approximation_quality`,
`Z_estimator_converged`, `accuracy_qualified`); Z low-frequency extrapolation;
lattice-spectrum-from-Σ (≠ impurity-cluster).

**Direct paper comparison — `ed_validation_checks.csv`: 21/21.** Our DMFT-ED
matches **LLK Fig 3 (dashed) docc/Z/etot at U/D=2.4 for N_b={1,3,5}** within
figure-digitization tolerance; U=0 exact; CG≡LM; monotone N_b convergence;
N_b=5 → CTQMC; common-norm bath χ² decreasing. Grids (`results/runs/20260717_ed_llk/`):
accepted (fixed-point converged) 54/56; **N_b=3 accuracy_qualified = 12/28**
(weak-coupling + deep-insulator, NOT near Mott — matching LLK's "N_b=3 needs
N_b=5" near the transition); N_b=1 = 0 (crude 1-pole). Protocol +
paper-vs-implementation table + Table I g-RISB anchors in `ed_llk_protocol.json`.
`N_b=7` not run; `N_b=5` optional control. This module is DMFT-ED (the paper's
dashed curves); the ghost/g-RISB side is gem (D08).

## Stage 3 — registered scan matrix (EXECUTED, resumable)

`scripts/gauge_matrix/scan_matrix.py`: branch-aware continuation over the exact
benchmark grids (Bethe 52 U/D × 17 T/D = 884 keys; Square 40 × 10 = 400),
{M_g=1,3} × {bare_native, R_native}, square on the continuum route. Immutable
versioned output (`results/runs/20260717_scan_matrix/<cell>/T*.csv`), append-only
registry (`scan_run_registry.csv`), resumable (skips complete T-files), every
attempt retained, `selected` never set, exact canonical-R attached to every bare
root.

**Coverage (`coverage_before.csv` → `coverage_after.csv`) — 7/7 cells COMPLETE:**

| cell | before (keys) | after | quadrature |
|---|---|---|---|
| bethe M_g=1 bare | 225/884 | **884/884** ✅ | semicircle |
| bethe M_g=1 R-native | 0/884 | **884/884** ✅ | semicircle |
| bethe M_g=3 R-native | 156/884 | **884/884** ✅ (14 ladders filled) | semicircle |
| square M_g=1 bare | 70 (Nk=16) | **400/400** ✅ | continuum n_eps=4001 |
| square M_g=1 R-native | 0 | **400/400** ✅ | continuum n_eps=4001 |
| square M_g=3 bare | 400 (Nk=16) | **400/400** ✅ | continuum n_eps=2001 |
| square M_g=3 R-native | 0 (Nk=16 reopt ≠ continuum) | **400/400** ✅ | continuum n_eps=2001 |

**8,504 rows total; 8,062 converged; `selected=0` everywhere; `n_modes=3`
everywhere; exact canonical-R attached to every bare root.** The square M_g=3
cells used the node-convergence-validated `n_eps=2001` (2.8e-7 error, ~2× faster
than 4001 for the expensive cold-T 5-param continuum solve); the node count is
recorded per row and each cell is internally uniform (one 4001 T0.001 file that
ran before the switch is **preserved**, not deleted, under
`square_mg3_bare/_superseded_4001/`). The campaign survived a mid-run kill and
**resumed** from its per-T checkpoints (the runner skips complete T-files) — the
demonstrated resumability the prompt requires.

`unresolved_conditions.csv` lists all **442** non-converged conditions as
explicit gaps (never interpolated / synthesized) — dominated by the M_g=1
insulator branch, which collapses to Z=0 (the documented Brinkman-Rice-only
result, a physical outcome, not a solver failure), plus near-spinodal metal
points.

**Rebuild / re-verify:**
```
for c in bethe_mg1_bare bethe_mg1_Rnative bethe_mg3_Rnative \
         square_mg1_bare square_mg1_Rnative; do
  .venv-numba/bin/python3 scripts/gauge_matrix/scan_matrix.py --cell $c; done
for c in square_mg3_bare square_mg3_Rnative; do
  SCAN_N_EPS=2001 .venv-numba/bin/python3 scripts/gauge_matrix/scan_matrix.py --cell $c; done
.venv-numba/bin/python3 scripts/gauge_matrix/build_stage3_reports.py
.venv-numba/bin/python3 scripts/gauge_matrix/build_d09_manifest.py
```

## Reproducibility

Deterministic builders regenerate every derived table from the raw runs + code:
`build.py` / `build_grids.py` / `build_ed.py` (D08); `build_ed_protocol.py`,
`build_ed_views.py`, `build_stage3_reports.py`, `build_d09_manifest.py` (D09);
`square_integration.py` (node convergence). Before a commit, the verifier can
check the current scoped trees; after committing, run
`verify_clean_checkout.py --commit SHA` to export and test that exact Git tree.

## Files

`source_manifest.csv` (comprehensive hashes + scoped solver patch),
`dirty_patch.diff`, `raw_campaign.tar.gz`,
`square_integration_registry.json`, `square_stationary_convergence.csv`,
`square_branch_matches.csv`, `square_claim_gate.csv`, `square_pilot_v2_raw.csv`,
`square_resolution_decision.md`, `ed_llk_protocol.json`, `ed_validation.csv`,
`ed_validation_checks.csv`, `ed_accepted.csv`, `ed_raw_attempts.csv`,
`coverage_before.csv`, `coverage_after.csv`, `scan_command_manifest.csv`,
`scan_run_registry.csv` (in the run dir), `unresolved_conditions.csv`,
`stage3_audit.csv`, `README.md`.

## Completion status

The registered scan matrix is **complete — 7/7 cells** ({bethe,square} ×
{M_g=1,3} × {bare_native, R_native}), on the exact benchmark grids, with the
square cells on the Stage-1 continuum route. Every bare root carries its exact
canonical-R partner; independent R-native grids were run as distinct evidence
for all four {lattice × M_g} combinations (previously absent). Raw D08 artifacts
remain byte-identical (1467/1467); D08 + ED test suites pass (20/20 + 11/11); no
branch is auto-`selected`; every unresolved condition is recorded explicitly.

Remaining (not in this task's scope): the accepted-view / cross-method physics
comparisons that select the paper story are deliberately deferred (the matrix is
an atlas, not a selection). A finite-T or square ED extension, if pursued, is
separate work.
