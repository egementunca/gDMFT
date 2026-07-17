# gDMFT

`gDMFT` is an open scientific framework for ghost dynamical mean-field theory.
It is designed to make ghost-extended DMFT calculations reproducible,
inspectable, and reusable across models, lattices, solvers, and future studies.

The project treats a numerical result as more than a converged parameter
vector. A result includes its model definition, gauge, continuation history,
observables, residuals, validation gates, provenance, and selection status.

## Project goals

- single-site and cluster ghost-DMFT models;
- Bethe and square-lattice workflows;
- bare and canonical-R parameterizations;
- explicit metallic, insulating, and metastable branch tracking;
- scalar observables, Green's functions, self-energies, and spectra;
- reproducible comparisons with DMFT, NRG, ghost-GA, and related methods;
- versioned datasets that regenerate figures and interactive atlases.

## Current status

The reproducibility layer is implemented first: versioned dataset manifests,
typed scalar point tables, artifact checksums, provenance, and independent
numerical gate fields. The solver modules will be added behind stable
interfaces as they pass parity and end-to-end tests. APIs may change before
version `1.0`.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'

gdmft-data validate data/example/manifest.json
pytest
```

The example dataset is intentionally small and is not a physics result.

## Result lifecycle

```text
study definition
      -> raw solver points
      -> numerical validation
      -> branch continuity
      -> physical and thermodynamic selection
      -> registered dataset
      -> comparison, figures, and atlas
```

These states remain separate. In particular, convergence does not imply that
a root is physical, branch-continuous, or selected.

## Repository map

```text
src/gdmft/     library, command-line tools, and packaged schemas
data/          dataset registry, examples, and small published tables
studies/       study specification convention and runnable studies
external/      pinned external software and reference sources
docs/          concepts, architecture, workflow, and data policy
tests/         unit, parity, schema, and end-to-end tests
```

## Documentation

- [Concepts](docs/concepts.md)
- [Workflow](docs/workflow.md)
- [Architecture](docs/architecture.md)
- [Data contract](docs/data-contract.md)
- [Data and external-source policy](docs/data-policy.md)
- [Roadmap](docs/roadmap.md)

## Reproducibility principles

1. Units and energy conventions are explicit.
2. Every artifact is tied to an immutable code revision and checksum.
3. Numerical, physical, continuity, bounds, and selection gates are separate.
4. Gauge-dependent coordinates are distinguished from physical observables.
5. External implementations are pinned comparisons, not correctness labels.
6. Large datasets are archived immutably; figures consume registered versions.

License and citation metadata will be finalized before the first public
release.
