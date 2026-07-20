# Single-site gauge matrix v1

This is the frozen D08 predecessor dataset. It retains 20,228 full records:
8,568 bare roots, 8,568 deterministic canonical-R conversions, 2,180
canonical-R reoptimizations, and 912 independent canonical-R continuations.

`points.csv` is a gDMFT-native scalar view. `raw/roots.jsonl.gz` is the
lossless source of pole arrays, residues, parameters, observables, and
provenance. The source projection and validation evidence are retained
byte-for-byte. The original gitignored run tree is not bundled, so D08 is a
verified frozen result set rather than a campaign that can be re-solved from
this dataset alone.

The square-lattice rows in D08 use the historical `N_k=16` mesh and are
preliminary for sub-percent claims. Use the child D09 scan-matrix dataset for
the canonical continuum-DOS square results.

`m_h=2` names the bare h-sector budget. Its canonical-R representation has
`n_modes=3` because the forward gauge map adds the central mode; this is a
coordinate transformation, not a different physical pole-budget solve.

No branch selection has been applied. The legacy `converged` flag is exposed
as `solver_succeeded` because D08 did not retain a separate optimizer-success
field; `equations_accepted`, physical admissibility, continuity, and selection
remain unknown unless explicitly present in the source row.

The normalized scalar view separates quasiparticle-weight estimators. For
`m_g=3`, the legacy source field `Z_mats` was the canonical Fermi-mode residue
and is imported as `quasiparticle_weight_from_r`; its Matsubara field is null.
For the older `m_g=1` campaigns, the distinct stored Matsubara estimate remains
in `quasiparticle_weight_matsubara`. The source projection is unchanged.
