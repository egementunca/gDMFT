# Reference data import

Imports external benchmark results as registered reference datasets.

`import_gem_references.py` builds `data/datasets/references-gem-gga-v1/` from
the gem (TRIQS ghost-GA / g-RISB) scan CSVs in the paper-consolidation
worktree. The scan outputs are gitignored run artifacts there, so the importer
reads the filesystem and records per-file SHA-256 provenance (plus the
byte-for-byte raw archive and the tracked generating script at the source
revision) instead of git blobs.

Before writing anything it cross-checks double occupancy and total energy
against the registered single-site datasets on the coldest temperature row;
a unit or convention mismatch aborts the import. Note the bethe m_g=3
comparison uses the v1 gauge-matrix bare rows: the v2 bethe m_g=3 cell holds
only independent canonical-R continuations whose metal chain falls into the
effective-m_g=1 family (the documented negative control).

Rerun with:

```
.venv/bin/python studies/reference_data_import/import_gem_references.py --replace
```

then re-register in `data/registry.toml` if the id changes (the script prints
the registry block).
