# Roadmap

## 0.1: reproducible data foundation

- Versioned dataset manifests and artifact checksums.
- Canonical scalar point-table contract.
- Function/checkpoint container contract.
- Dataset registry and validation CLI.
- CI validation of schemas, checksums, and examples.

## 0.2: numerical core

- Typed model, lattice, discretization, and solver configuration.
- Pole parameters and bare/canonical-R gauge transformations.
- Dense and sparse exact diagonalization backends.
- Thermodynamic and residual-block APIs.
- Immutable solver result and diagnostics objects.

## 0.3: single-site workflows

- `M_g=1` and `M_g=3` calculations.
- Bethe and square lattices.
- Metal-up and insulator-down continuation.
- Matched-root gauge parity tests.
- Thermodynamic selection and phase-diagram extraction.

## 0.4: nested-cluster workflows

- Shared particle-hole-symmetric site and bond model.
- Local and nearest-neighbor self-energy channels.
- Inclusion-exclusion observables.
- Momentum-resolved functions and spectral gaps.
- Branch, bounds, and reliability atlases.

## 0.5: comparisons and publication tools

- Pinned adapters for `gem` and regular DMFT solvers.
- Registered NRG, ghost-GA, and literature benchmark tables.
- Convention-aware comparison utilities.
- Static figures and a self-contained interactive atlas.
- DOI-backed full datasets with small canonical tables in Git.

## 1.0: first stable release

- Stable documented Python API.
- Reproducible CPU reference workflows.
- Clean-environment wheel and source builds.
- End-to-end regeneration of registered figures.
- License, citation metadata, and archived datasets.
