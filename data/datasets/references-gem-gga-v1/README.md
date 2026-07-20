# gem ghost-GA (g-RISB) benchmark scans v1

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
