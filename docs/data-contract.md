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

## Parameters and dense functions

Variable-length pole arrays, residues, bath weights, Matsubara functions,
real-frequency functions, and spectra belong in a companion HDF5/NPZ file.
The scalar table stores a stable artifact path and group/key. Every array must
record axis values, units, broadening, grid construction, and residue cutoff.

## Derived and external data

Derived tables record all parent dataset IDs. External adapters preserve both
raw values and normalized values, including the exact formula used for energy
or unit conversion. A comparison never overwrites the source convention.

## Reproducibility floor

A dataset is not publishable without:

- immutable code revision and dirty flag;
- complete command/configuration and random seeds;
- environment lock hash;
- units and half-bandwidth convention;
- per-artifact SHA-256 and byte count;
- selection implementation and review status when selection was applied;
- citation and immutable archive location.
