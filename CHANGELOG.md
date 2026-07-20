# Changelog

## Unreleased

- Added the initial gDMFT package and documentation structure.
- Added versioned dataset-manifest and scalar point-table contracts.
- Added checksum, provenance, gate, row-count, and CSV type validation.
- Added a pinned external-source registry and reproducible study convention.
- Imported the frozen 20,228-record single-site gauge matrix.
- Imported the authoritative 15,240-attempt single-site scan matrix with
  canonical gDMFT point views, lossless archives, validation evidence, and a
  portable producer-code audit snapshot.
- Imported the gem ghost-GA (g-RISB) benchmark scans as a registered
  reference dataset (5,136 rows covering both scan-matrix grids at B=1,3 in
  both sweep directions), with import-time convention cross-checks against
  the registered single-site datasets.
- Added `gdmft-atlas build`: a self-contained interactive atlas (single
  offline HTML) with phase-diagram heatmaps, a series builder, gem/DMFT-ED
  benchmark views, branch/gauge/QA diagnostics, per-point spectral
  reconstruction from the lossless raw archives, and full manifest
  provenance. See docs/atlas.md.
- Imported the cross-method benchmark references as a registered dataset
  (audited compare merge, NRG thermal curves, professor gGA grids parsed
  from .npy, CTQMC anchor, fresh-ruler markers) with import-time
  machine-precision cross-checks against the registered point datasets.
- Added the paper-figure pipeline (studies/paper_figures): the LLK-style
  benchmark figures (ghost-DMFT vs gem vs DMFT-ED only — no external
  reference data drawn), the single-site phase-diagram figure with the
  endpoint corridors updated to bethe (0.01, 0.015) / square
  (0.004, 0.005), the bath-anatomy and gateway-ladder figures, and the new
  Matsubara/spectral figure — all reading registered data only, output in
  runs/figures/.
