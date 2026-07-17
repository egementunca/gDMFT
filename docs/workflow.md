# Workflow

## 1. Define a study

A study declares the model, lattice, channel budgets, gauge, numerical grids,
bounds, solver tolerances, seeds, continuation directions, requested
observables, and output schemas.

## 2. Generate raw points

Each attempt receives a stable identity and records its full configuration,
seed, continuation parent, parameters, residual blocks, optimizer status, and
source provenance. Rejected attempts are retained.

## 3. Validate numerically

Equation, density, physical-guard, and bound checks are evaluated separately.
Function-level checks include causality, moments, sum rules, and gauge parity
where applicable.

## 4. Construct branches

Continuation ancestry and first-failure boundaries define branch membership.
Cross-polished or rescued roots remain labeled and cannot silently replace a
native continuation point.

## 5. Select reported states

Physical admissibility is established before thermodynamic comparison. The
selection policy and its implementation version are stored in the dataset.

## 6. Compute observables

Scalar tables and dense function artifacts are generated from the selected
canonical roots. Derived tables cite their parent dataset IDs.

## 7. Register and archive

The manifest records conventions, code revision, environment, source assets,
artifact sizes, and SHA-256 values. Large lossless artifacts are uploaded to
an immutable archive.

## 8. Compare and render

External adapters preserve source conventions and emit normalized comparison
tables. Figures and atlases read only registered dataset versions.
