# Data policy

The repository tracks manifests, checksums, small canonical tables, and
publication-ready subsets. Raw run directories and caches are ignored.

## Dataset lifecycle

Processing and publication are separate axes.

`data_stage` records whether a dataset is `raw`, `validated`, or has
`selection_applied`. Applying selection never deletes rejected or metastable
rows.

`release_status` records whether the dataset is a `draft`, `published`, or
`superseded` release. Published data require rights, citation, environment,
and immutable archive metadata.

Large arrays should be archived as HDF5 or NPZ and referenced by manifest.
Published archives should use an immutable DOI provider such as Zenodo. Git
should contain the small tables needed to regenerate published figures plus
the manifest that locates the full archive.

Every scalar point table must follow `docs/data-contract.md`. Do not pack
pole arrays, Matsubara functions, or spectra into JSON strings in a CSV.

## Available draft datasets

- `single-site-gauge-matrix-v1`: frozen D08 predecessor with 20,228 native
  point rows and the lossless root archive.
- `single-site-scan-matrix-v2`: authoritative D09 matrix with 15,240 native
  point rows, the lossless raw campaign, validation evidence, and a portable
  producer-code audit archive.

Both manifests validate locally:

```bash
gdmft-data validate \
  data/datasets/single-site-gauge-matrix-v1/manifest.json
gdmft-data validate \
  data/datasets/single-site-scan-matrix-v2/manifest.json
```

They remain `draft`: numerical validation is recorded, while physical
admissibility, branch continuity, thermodynamic selection, release rights,
and immutable publication metadata are not yet complete.
