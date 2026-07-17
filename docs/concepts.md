# Concepts

## Ghost-DMFT state

A gDMFT state is a stationary solution of a finite ghost-extended
representation of the interacting lattice problem. The state includes the
pole parameters, the physical Green's functions and self-energies they
generate, thermodynamic observables, and numerical diagnostics.

`M_g` and `M_h` label the chosen channel budgets of the two auxiliary sectors.
They are model-resolution parameters, not physical observables. Comparisons
between budgets must use matched units, lattices, temperatures, and selection
rules.

## Gauges

Bare and canonical-R coordinates can describe the same physical state.
Coordinate values and inactive dark directions may differ even when physical
observables agree. Gauge parity is therefore tested at the level of canonical
roots, Green's functions, thermodynamics, and residuals.

## Branches

Nonlinear equations may contain multiple roots. A branch is a continuation
family with explicit parentage, direction, and failure boundaries. Labels such
as `metal-up` and `insulator-down` describe how a family was constructed; they
do not by themselves establish thermodynamic stability.

## Validation gates

Every point carries separate states for:

- equation acceptance;
- density consistency;
- physical guards;
- active bounds;
- physical admissibility;
- branch continuity;
- final selection.

An unknown gate remains unknown. It is not silently treated as passing.

## Observables

Canonical scalar observables include density, double occupancy, quasiparticle
residue, grand potential, kinetic and potential energy, total energy, and
entropy. Dense artifacts contain self-energies, hybridizations, Green's
functions, spectral functions, pole arrays, and residues.

Cluster observables use explicit local, bond-cluster, and inclusion-exclusion
names. They are not interpreted as sublattice order parameters unless the
model actually contains sublattice symmetry breaking.

## Units

Published comparisons use the lattice half-bandwidth `D` as the default energy
unit. Both raw and normalized axes may be stored, but figures and tables must
state whether they show `U`, `T`, `U/D`, or `T/D`.
