# Single-site data snapshot: 2026-07-17

The first real gDMFT data import is split into a frozen predecessor and an
authoritative scan matrix. Both are draft datasets: the numerical validation
is preserved, but no physical or thermodynamic branch selection has been
applied.

| Dataset | Role | Native rows | Lossless archive |
|---|---|---:|---:|
| `single-site.gauge-matrix-v1` | D08 historical gauge matrix | 20,228 | 4.8 MB |
| `single-site.scan-matrix-v2` | D09 authoritative scan matrix | 15,240 | 6.9 MB |

## Authoritative coverage

D09 covers seven registered cells:

| Lattice | Budget and route | Grid keys | Temperatures |
|---|---|---:|---:|
| Bethe | `M_g=1` bare | 884 | 17 |
| Bethe | `M_g=1` canonical-R native | 884 | 17 |
| Bethe | `M_g=3` canonical-R native | 884 | 17 |
| Square | `M_g=1` bare | 400 | 10 |
| Square | `M_g=1` canonical-R native | 400 | 10 |
| Square | `M_g=3` bare | 400 | 10 |
| Square | `M_g=3` canonical-R native | 400 | 10 |

Every registered key has at least one converged branch. Every bare root also
has an exact canonical-R conversion and a canonical-R reoptimization. The
attempt inventory is:

- 3,368 bare-native;
- 3,368 exact canonical-R converted;
- 3,368 canonical-R reoptimized;
- 5,136 independent canonical-R continuation.

The square rows use the continuum elliptic DOS at `n_eps=2001`. The older D08
square rows use `N_k=16` and remain historical evidence only.

`m_h=2` is the bare h-sector budget throughout this import. The canonical-R
view contains three modes because the gauge transformation adds the central
mode (`n_modes=m_h+1`); it is not a separate three-pole physical-budget scan.

## Observables and evidence

The canonical point views expose `Z` from the pole and Matsubara definitions,
double occupancy, density, grand potential, kinetic, potential, and total
energies, residual norms, reduced canonical parameters, lattice quadrature,
and provenance. The lossless archives additionally retain:

- complete native solution vectors;
- full ghost bath energies and hybridizations;
- full bare-h and canonical-R pole arrays and residues;
- optimizer status, active bounds, and bound distances;
- complete residual vectors and seven block norms;
- continuation parent and seed provenance.

D09 classifications are 9,753 `converged_branch`, 5,136
`branch_not_found`, and 351 `failed_branch`. The `branch_not_found` rows are
dark decoupled solutions, so they do not establish the requested physical
branch.

## Validation holdings

The dataset includes matched bare/canonical-R diagnostics, Mg=1 bound
expansion, square quadrature comparisons, and the LLK DMFT-ED validation
tables. Exact bare-to-R conversion agrees to machine precision. The Mg=1
bound expansion shows roughly 1-2% `Z` drift along a flat direction, so bounds
are not certified globally.

The LLK evidence includes `N_b={1,3,5}` validation data, but it is supporting
evidence rather than a required external benchmark grid. The copyrighted PDF
is not redistributed; its SHA-256 and DOI are recorded.

## Deliberately unresolved

`bounds_clear`, branch continuity, physical admissibility, and thermodynamic
selection remain unknown in the authoritative point table. These are the next
analysis layer, not missing solver data. The archived square node
certification is retained as source evidence, but its interacting-node raw
producer rows were not committed and cannot currently be rederived here.

The nested-cluster results are not part of this import. They should become a
separate dataset after their gauge, scan, observable, and branch contracts are
fixed.
