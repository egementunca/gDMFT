# Data contract

## Scalar point table

Each row represents one solver point, not one plotted point. Required identity
columns are:

```text
schema_version, run_id, point_id, lattice, m_h, m_g, solution_family, gauge,
solver, u_over_d, t_over_d
```

The following gates are independent nullable booleans:

```text
solver_succeeded, equations_accepted, density_consistent,
physical_guards_clear, bounds_clear, continuity_passed,
physically_admissible, selected
```

Unknown is not equivalent to false, and convergence never implies selection.
Selection requires a named policy and a reason field.

The `gdmft-data validate` command checks the required CSV columns, value types,
nullable gates, unique `(run_id, point_id)` keys, declared row count, file
size, and checksum.

Core scalar observables use unambiguous names such as
`double_occupancy_impurity_1`, `double_occupancy_impurity_2_per_site`,
`double_occupancy_ncs`, `quasiparticle_weight_pole`,
`quasiparticle_weight_matsubara`, `grand_potential_total`, `kinetic_energy`,
`potential_energy`, `total_energy`, and `entropy`. Mathematical symbols belong
in display metadata rather than machine column names.

The three quasiparticle-weight columns are not interchangeable:

- `quasiparticle_weight_pole` is derived from the self-energy pole
  derivative;
- `quasiparticle_weight_from_r` is the canonical quasiparticle-mode residue
  $R_{\mathrm{qp}}^2$;
- `quasiparticle_weight_matsubara` is populated only when an independent
  Matsubara-frequency estimator was actually evaluated.

A producer's historical field name does not override these meanings. The D09
source field called `Z_mats` is normalized into
`quasiparticle_weight_from_r`, while the original source projection remains
unchanged.

## Parameters and dense functions

Variable-length pole arrays, residues, bath weights, Matsubara functions,
real-frequency functions, and spectra belong in a companion HDF5/NPZ file.
The scalar table stores a stable artifact path and group/key. Every array must
record axis values, units, broadening, grid construction, and residue cutoff.

## Derived and external data

Derived tables record all parent dataset IDs. External adapters preserve both
raw values and normalized values, including the exact formula used for energy
or unit conversion. A comparison never overwrites the source convention.

Overlapping result campaigns do not choose a source by registration order.
`gdmft.atlas.catalog` declares the primary source for each
`(lattice, m_g)` cell and classifies exact gauge conversions, independent
gauge-route solves, and historical grids separately. A primary route plus
source acceptance is still not thermodynamic branch selection.

External temperature semantics are part of the comparison key. D09 DMFT-ED
is a ground-state calculation. Its `bath_fit_beta=200` defines the numerical
bath-fit grid and is not a physical temperature. CTQMC at $\beta=200$ is the
separate physical $T/D=0.005$ anchor.

## Reproducibility floor

A dataset is not publishable without:

- immutable code revision and dirty flag;
- complete command/configuration and random seeds;
- environment lock hash;
- units and half-bandwidth convention;
- per-artifact SHA-256 and byte count;
- selection implementation and review status when selection was applied;
- citation and immutable archive location.
