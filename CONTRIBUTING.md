# Contributing

gDMFT is under active development. Contributions should keep numerical
behavior, data provenance, and scientific interpretation independently
reviewable.

## Requirements

1. Add tests for each numerical or data-contract change.
2. State units and conventions at every public boundary.
3. Keep convergence, physicality, continuity, bounds, and selection separate.
4. Pin external software and datasets to immutable versions.
5. Store generated runs outside Git until they are promoted through a
   validated dataset manifest.
6. Mark experimental functionality explicitly.

Run before submitting a change:

```bash
ruff check .
pytest
python -m build
```
