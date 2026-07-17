# Architecture

gDMFT separates numerical physics, solver orchestration, data persistence, and
scientific selection. Dependencies point downward; low-level modules never
import workflows, plotting code, or command-line runners.

```text
configuration, parameters, and schemas
                 |
                 v
       ED, lattices, and gauges
                 |
                 v
       models and residual blocks
                 |
                 v
       solvers and continuation
                 |
                 v
    observables and validation gates
                 |
                 v
       studies and comparisons
                 |
                 v
        datasets and rendering
```

## Package map

```text
src/gdmft/
  config.py
  parameters.py
  lattices/
  ed/
  gauges/
  models/
  solvers/
  observables/
  data/
  comparisons/
  cli/
```

Only `data/` and the packaged schemas are implemented in the initial
development release. Other modules are added when their public contracts and
parity tests are ready.

## Stable solver boundary

Numerical solvers will return an immutable `SolveResult` containing:

- model and discretization configuration;
- parameters in a named gauge;
- scalar observables with explicit definitions;
- residual blocks and Jacobian diagnostics;
- independent validation gates;
- seed and continuation ancestry;
- references to dense function artifacts;
- source and environment provenance.

CPU and accelerator implementations use explicit backend interfaces. Runtime
behavior must not depend on import order or global monkeypatching.

## Workflow policy

Branch construction and selection live above the numerical core. A workflow
may define continuation order, multistart policy, bounds, rejection gates, and
thermodynamic selection without changing the model equations.

This keeps three questions separate:

1. Was the equation solved?
2. Is the root numerically and physically admissible?
3. Should the root represent the reported state?
