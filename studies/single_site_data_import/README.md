# Single-site data import

This study promotes the frozen single-site D08/D09 results from the
paper-consolidation repository into the gDMFT data contract. It performs no
solver run, fitting, branch selection, or observable recomputation.

The importer reads only Git blobs from preservation commit
`1d987593969520b8cd6e191ca284682738778a6d`. It does not read the source
worktree, `results/runs/`, or expanded caches.

```bash
python3 studies/single_site_data_import/import_snapshot.py \
  --source-repository /path/to/paper-consolidation \
  --output-root data/datasets
```

It creates:

- `single-site-gauge-matrix-v1`: the frozen D08 predecessor and full root
  archive;
- `single-site-scan-matrix-v2`: the authoritative D09 scan matrix, full raw
  campaign, validation evidence, and portable source-code audit archive.

Both datasets contain a gDMFT `points.csv`. Source scalar projections are
retained unchanged so every adaptation can be audited. The importer leaves
bounds, continuity, physical admissibility, and selection unknown unless the
source explicitly established them.

The D09 source-code archive is not installed under `src/gdmft`. It preserves
the producer closure for audit while the numerical core is ported behind the
interfaces described in `docs/architecture.md`. Machine-specific paths are
made repository-relative; the inventory records original and archived hashes.
