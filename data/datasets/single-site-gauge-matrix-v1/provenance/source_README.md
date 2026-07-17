# 08 — Single-Site Gauge Matrix (lossless canonical data layer)

The complete, provenance-preserving data layer for

```
{bethe, square} × {M_g = 1, M_g = 3} × {bare, canonical R}
```

built by `scripts/gauge_matrix/`. It is a **separate, non-destructive** export:
it reads the raw campaign artifacts, forward-converts every bare root to its
canonical (λ, R) gauge **deterministically** (an arrowhead eigendecomposition —
no optimizer, ED, gem, or DMFT-ED run), and records exactly what each
representation is evidence *of*. No raw attempt, checkpoint, or rejected root is
ever deleted or overwritten.

> **Provenance status (verified 2026-07-17).** This deliverable, its builders,
> and its acceptance tests are preserved by the scoped single-site repository
> checkpoint. The `code_commit` field inside the archived records and
> `_build_stats.json` remains `1a3af4a`: that is the execution/build base, not
> the later commit which first contains the frozen artifacts. D09 preserves the
> relevant solver-state patch and exact source hashes. Unrelated worktree changes
> are not part of this checkpoint.

## Files

| file | what it is |
|---|---|
| `source_manifest.csv` | every live source file: SHA-256, record count, role, evidence type (1550 files) |
| `roots.jsonl.gz` | deterministic, lossless gzip of all full representation records (20,228 records) |
| `roots_archive_manifest.json` | archive and decompressed SHA-256 values, sizes, and record count |
| `scalar_projection.csv` | flat per-record scalar view of the archived roots |
| `grid_registry.json` | canonical Bethe/Square benchmark grids + gem key sets + quadrature identities |
| `coverage_matrix.csv` | per benchmark `(U/D,T/D)` key, coverage split by evidence type |
| `coverage_report.md` | coverage / missing-key / missing-ladder / gem-subset summary |
| `square_quadrature_pilot.csv` | Nk=16 vs Nk=64 quadrature-uncertainty pilot + U=0 anchor |
| `ed_llk_config.json` | LLK finite-pole DMFT-ED config, deviations, and ground-state semantics |
| `ed_accepted.csv` / `ed_raw_attempts.csv` | converged-only ED view / lossless raw ED attempts |

Tests: `tests/test_gauge_matrix.py` (20 acceptance criteria) and
`tests/test_dmft_ed.py` (ED impurity-solver unit checks). Both pass standalone
(`.venv-numba/bin/python3 tests/test_*.py`) and under `pytest`.

## Evidence types — never conflated

Each representation carries exactly one:

- **`bare_native`** — a solution fit in the bare (η, W) gauge (the original root).
- **`R_converted_from_bare`** — the deterministic arrowhead forward map of a bare
  root to canonical (λ, R). A *mathematically complete* gauge representation
  (both h-sectors, all Mh+1=3 modes, normalization + closure at machine
  precision); **not** evidence of independent R-solver convergence. Exactly one
  per bare root.
- **`R_reoptimized_from_bare`** — a root re-optimized in R coordinates
  (`least_squares`) from the converted seed (square full-grid certification).
- **`R_native_continuation`** — an independent R-gauge warm-start continuation
  (Bethe Mg=3 at T/D ∈ {0.005, 0.025, 0.1}).

An organized folder, a scalar `dZ` check, a converted seed, and an independent
continuation are **not** equivalent evidence and are stored separately.

## Source inventory (recounted from the filesystem)

| cell | bare_native | source |
|---|---|---|
| Bethe Mg=3 | 5,506 (17 T) | `mg3_bethe/symmetric_bethe_T*.csv` |
| Square Mg=3 | 2,180 (10 T) | `20260710_rerun_mg3/symmetric_square_T*.csv` |
| Bethe Mg=1 | 583 | old-Bethe (299) + July-15 ext (284) attempt JSONs |
| Square Mg=1 | 299 | old-square attempt JSONs |
| **bare total** | **8,568** | 882 Mg=1 attempts = 299 + 284 + 299 |

R-gauge sources: Bethe Mg=3 R-native continuation **912** (3 T); Square Mg=3
R-reoptimization **2,180** (10 T). Record conservation is exact and enforced by
`test_gauge_matrix.py::test_01`.

The Mg=1 collector rebuilds (814 = 267 old-Bethe + 280 July-15 + 267 old-square)
and the old organized trees are recorded as **generated views**, never as
canonical sources (`test_20`). The Bethe Mg=1 organized view hardcodes the old
collector and omits the 284-record July-15 extension — the export merges all
three campaigns by provenance, so no attempt is lost.

Every `M_h=2` bare h-sector maps to **M_h+1 = 3** canonical modes; this is still
M_h=2 (not relabelled M_h=3, no M_h=4 introduced). Both the lattice and the
gateway h-sectors are exported even where the symmetric solver sets them equal.

## Gauge conversion quality

- Normalization `|ΣR²−1|` and ebar-closure `|Σλ R²−ebar|`: **≤ 1e-9 on every
  root** (machine precision).
- Interior (non-floor) inverse round-trip `(λ,R)→(η,W)`: **max 1.1e-10** across
  4,493 converted metal-arm roots.
- **Floor-limited roots: 4,075 / 8,568** (all have Z ≤ 1.3e-8 — deep insulator /
  dark-ghost boundaries where the inverse chart is singular). The forward
  representation is retained exactly; a failed inverse round-trip **always**
  sets `floor_limited=True`, so a floor-limited root can never masquerade as an
  ordinary interior R-native solution (`test_06`).

## Unit conventions

| | U/D | T/D | energy | quadratic | Ω / energy |
|---|---|---|---|---|---|
| Bethe (D=1) | uot/2 | T_code | x/D=x | q/D²=q | E/D=E |
| Square (D=2) | uot/4 | T_code/2 | x/D | q/D² | E/D |
| gem | stored = U/D, T/D | | already reduced | | |
| ED | stored = U/D | T=0 (ground state) | | | |

Reduced axes are stored as `U_over_D`/`T_over_D` everywhere (the old
Bethe-`T`/square-`T_over_D` split is normalized). Raw code values are retained
alongside. Square energy-like quantities carry both raw (D=2) and `_over_D` /
`_over_D2` reduced values.

## Coverage (see `coverage_report.md`)

- gem benchmark keys ⊆ dense Mg=3 grid: **884/884 (Bethe), 400/400 (Square), 0
  outside**.
- Mg=3 bare covers the full benchmark grid on both lattices.
- Missing independent **R-native** ladders: Bethe Mg=3 present at 3 of 17 T/D
  (**14 missing**); Square Mg=3 has R-reoptimization at all 10 T/D but **0
  R-native ladders (10 missing)**.
- Missing **Mg=1** benchmark keys, enumerated in `coverage_matrix.csv`:
  **Bethe 659/884, Square 330/400** absent.

## Square quadrature gate (`square_quadrature_pilot.csv`)

The ghost square roots use a uniform **Nk=16 (256-point) k-mesh**; gem and
DMFT-ED use the continuum elliptic DOS. The Nk=16→Nk=64 pilot at T/D=0.001
finds relative quadrature uncertainty **up to 98% for Z (near the spinodal),
2.1% for D_occ, 0.39% for Ω/D**, and the U=0 E_kin/D anchor is 0.63% off the
continuum −4/π². **Sub-percent square-energy accuracy claims are GATED** (all
> 0.1%). Dimensionless Z/D_occ/n and phase topology may still be reported with
the mesh stated. Completing the gate (Nk∈{16,32,64} or a matched-continuum
recompute) is a **solver run requiring approval** — the pilot is PRELIMINARY
(only Nk∈{16,64} at one T/D exist as solved roots).

## DMFT-ED (LLK) status (`ed_llk_config.json`)

Ground-state finite-pole DMFT-ED, half-filled Bethe D=1. **T=0 semantics**:
`temperature_semantics=ground_state, T_over_D=0, bath_fit_beta=200` — β=200 is a
fictitious bath-fit grid, never a physical T/D; ED cannot enter a finite-T join.
Accepted view (converged only) vs lossless raw attempts:

| lattice | Nb=1 | Nb=3 | Nb=5 |
|---|---|---|---|
| Bethe accepted / total | 91/114 | 92/114 | 88/114 |
| Square accepted / total | 80/90 | 88/90 | 84/90 |

Stalled rows (Bethe 23/22/26, Square 10/2/6) are excluded from the accepted view
and retained losslessly in `ed_raw_attempts.csv`. **Prototype caveats recorded:**
bath fit uses Levenberg-Marquardt, not the paper's conjugate gradient; the CSV
`fit_chi` is scipy `.cost` = **½ χ²**; the DMFT gate is on Σ only; real-frequency
A(ω) uses the impurity-cluster G, not a lattice reconstruction. `N_b={1,3}` are
the primary budgets, `N_b=5` optional, `N_b=7` out of scope. The square ED is
**this work's extension, not an LLK reproduction**.

## Rebuild

```
.venv-numba/bin/python3 scripts/gauge_matrix/build.py         # manifest + roots + scalar
.venv-numba/bin/python3 scripts/gauge_matrix/build.py --archive-only  # rearchive an expanded roots.jsonl
.venv-numba/bin/python3 scripts/gauge_matrix/build_grids.py   # grids + coverage
.venv-numba/bin/python3 scripts/gauge_matrix/build_ed.py      # ED config + accepted/raw
.venv-numba/bin/python3 scripts/gauge_matrix/build_pilot.py   # square quadrature pilot
.venv-numba/bin/python3 tests/test_gauge_matrix.py            # 20 acceptance checks
.venv-numba/bin/python3 tests/test_dmft_ed.py                 # ED unit checks
```

The expanded `roots.jsonl` is a gitignored build product. Tests deliberately
stream `roots.jsonl.gz` even when the expanded file exists, and verify the
archive plus its decompressed payload against `roots_archive_manifest.json`.

## Remaining solver runs (require explicit approval — NOT run here)

These supply *independent solver-route parity* / lift the square-energy gate.
The deterministic `R_converted_from_bare` partners already supply the complete
gauge representation for every bare root, so none of these are needed merely to
have both coordinate representations.

```
# Bethe Mg=3 R-native continuation, 14 missing T/D ladders (optimizer):
.venv-numba/bin/python3 scripts/symmetric_continuation_R.py --rows 0.001,0.002,0.003,0.004,0.0065,0.008,0.01,0.015,0.02,0.03,0.05,0.07,0.15,0.2

# Square Mg=3 R-native continuation, all 10 T/D ladders (optimizer) — no script yet (square sibling of symmetric_continuation_R.py)

# Bethe Mg=3 certification, persist re-optimized xR_sol for all 5,506 (optimizer; writes to gauge_certify_full/, never overwrites raw):
.venv-numba/bin/python3 scripts/gauge_certify_mg3.py --rows all

# Square k-mesh convergence, pilot points at Nk∈{16,32,64} (optimizer; changes the stationary solution — do not just recompute observables):
#   U/D={0,1,2,2.5,3.0}, T/D={0.001,0.01}, all branches

# Mg=1 bare + R-native scans on the 659 (Bethe) / 330 (Square) missing benchmark keys (optimizer) — only if a direct Mg=1→Mg=3 vs gem B=1→B=3 accuracy claim is intended
```
