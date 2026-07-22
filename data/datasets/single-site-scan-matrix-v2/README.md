# Single-site scan matrix v2

This is the authoritative D09 single-site scan dataset. It contains 15,240
unique attempts over seven registered cells:

- 3,368 bare-native roots;
- 3,368 exact canonical-R conversions;
- 3,368 canonical-R reoptimizations seeded from those conversions;
- 5,136 independent canonical-R continuation attempts.

The Bethe grid has 884 `(U/D, T/D)` keys over 17 temperatures. The square grid
has 400 keys over 10 temperatures. Every registered key has at least one
converged branch. All authoritative square rows use the continuum elliptic DOS
with `n_eps=2001`.

`m_h=2` names the bare h-sector budget. Its canonical-R representation stores
`n_modes=3` because the forward gauge map adds the central mode; it does not
mean that an independent `m_h=3` physical model was solved.

The source classification contains 9,753 `converged_branch`, 5,136
`branch_not_found`, and 351 `failed_branch` attempts. A `branch_not_found` row
is a dark decoupled solution, not the requested physical branch. The gDMFT
view therefore records its residual acceptance separately and sets
`physical_guards_clear=false`.

No thermodynamic branch selection has been applied. `bounds_clear`,
`continuity_passed`, `physically_admissible`, and `selected` remain null.
Active optimizer bounds are retained only as source evidence because the Mg=1
bound-expansion test shows that absence of an active-mask bit is not enough to
certify bound independence.

The source projection named the canonical quasiparticle-mode residue `Z_mats`.
In this normalized view it is correctly stored as
`quasiparticle_weight_from_r = R_qp^2`; the independent Matsubara-estimator
column is null. The source projection and raw archive remain unchanged.

The normalized Bethe rows report the effective one-dimensional semicircle
node count, 256. The source projection recorded 65,536 by copying the
two-dimensional `256**2` default even though that was not the Bethe
integration route. Both original source records remain unchanged, and the
manifest records this correction as `d09-bethe-effective-node-count-v1`.

`raw/raw_campaign.tar.gz` is the lossless source. It stores complete native
vectors, full bare and canonical pole arrays, optimizer results, bound
distances, residual vectors and blocks, ancestry, observables, quadrature, and
source revision for every attempt. The compact portable source-code archive
under `provenance/` is an audit freeze, not an importable gDMFT core. Its file
inventory records original and archived hashes; seven machine-specific paths
were made repository-relative without changing numerical code.

The archived square node-certification JSON is evidence from the source
campaign; its interacting-node producer rows were not committed, so it is not
independently rederived by this repository.

## Superseding revision 0.2.0 (fill campaign 20260721)

Appends the canonical-grid fill campaign as rows with run_id prefix
`d09-fill-20260721` (source: dmft worktree deliverable 09/fill_20260721 at
commit `db6595009654`): the unified 17-row T-ladder on BOTH lattices,
uniform 0.05 U-grid plus 0.01 coexistence windows, and the previously
missing `bethe_mg3_bare` cell — every bare root accompanied by its exact
canonical-R conversion and its R-reoptimized refit; R-native chains grown
from bare roots (seed provenance recorded). All evidence routes are rows
of fact; nothing is selected. Raw lossless records:
`raw/fill_attempts_20260721.jsonl.gz`. square_mg3 rows are partial until
the SCC pass completes; the import is idempotent and re-run per pass.
