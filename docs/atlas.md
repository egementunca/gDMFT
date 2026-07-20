# Interactive single-site explorer

`gdmft-atlas` builds one self-contained HTML file. It has no server and no
network dependency. Open the generated file directly in a browser.

## Build

```bash
.venv/bin/gdmft-atlas build --verify --stats
```

The stable output is `runs/atlas/gdmft_atlas.html`. `--verify` checks every
registered artifact checksum before the payload is built. Every browser
module is required; a missing tab fails the build.

For a byte-reproducible release build, set a fixed standard build timestamp:

```bash
SOURCE_DATE_EPOCH=0 .venv/bin/gdmft-atlas build --verify
```

## Which source is used

D08 and D09 are immutable evidence datasets with deliberate overlap. The
explorer never chooses the first matching dataset. The versioned policy in
`gdmft.atlas.catalog` declares these primary routes:

| Cell | Default source | Reason |
|---|---|---|
| Bethe, $M_g=1$, bare | D09 | Complete registered comparison grid |
| Bethe, $M_g=3$, bare | D08 | D09 has no corresponding bare population |
| Square, $M_g=1$, bare | D09 | Continuum elliptic DOS |
| Square, $M_g=3$, bare | D09 | Continuum elliptic DOS; supersedes D08 $N_k=16$ |

Exact bare-to-$R$ conversions are the same solution in another coordinate
system and do not add physics points. Independent $R$ continuations and
$R$ reoptimizations remain visible as gauge-route evidence. Numerically
accepted primary-route rows are still not selected thermodynamic phases.

The Atlas, Series, Branches, Tables, and Inspect tabs select this route
automatically from the chosen lattice and $M_g$. They do not ask the user to
choose D08 or D09 in normal use. Enable **show supplementary sources** only
to inspect a historical, converted, or independent gauge route explicitly.
The Gauge and QA tabs remain cross-dataset evidence views by design.

## What the tabs mean

| Tab | Content |
|---|---|
| Overview | Dataset provenance, primary-route counts, loaded references, provisional crossing diagnostics, and claim ledger |
| Atlas | $(U/D,T/D)$ evidence-status map by default; scalar and provisional branch-overlap maps on request |
| Series | User-defined $U$ or $T$ scans, pole-parameter scans, direct ED bath-parameter overlays, gem/ED scalar overlays, semianalytic curves, and export |
| Benchmarks | Primary-route ghost-DMFT against gem at matched finite $T$, with separately labeled ground-state ED markers |
| References | Exact comparison coverage, ED bath poles versus the ghost $g$-sector, and gem self-energy/canonical modes versus the ghost $h$-sector |
| Branches | Candidate metal/insulator attempt branches, continuity breaks, and provisional $\Omega$ crossings |
| Gauge | Exact conversion and independent reoptimization evidence, filtered by lattice, $M_g$, branch, and $T$ |
| QA | Nullable gates, residuals, unresolved conditions, and derivation report |
| Tables | Filtered attempt rows with observables, parameters, gates, quadrature, and provenance |
| Inspect | One root's pole tables and browser previews of $\Sigma$, $\Delta$, $G_{\rm loc}$, and $A_{\rm loc}$ |

The Atlas tab opens on evidence status, not a phase map. Candidate $U^*$,
spinodal, coexistence, and branch-split views use numerically converged
attempt labels. Physical guards, bound decisions, continuity, admissibility,
and final selection are not complete, so these views cannot be quoted as
phase boundaries.

## ED and CTQMC temperature

The LLK comparison contains two different calculations:

- DMFT-ED is a ground-state calculation with physical $T/D=0$.
  `bath_fit_beta=200` specifies the Matsubara grid used to fit a finite bath.
  It is not physical $T/D=0.005$.
- CTQMC at $\beta=200$ is the separate physical $T/D=0.005$ calculation.
  The registered reference is one digitized anchor at $U/D=2.4$, not a scan.

The current D09 ED table has 54 accepted Bethe rows. $N_b=1$ has both
continuation arms at 14 $U/D$ values; $N_b=3$ has both arms at 13 values
through $U/D=3.0$, while both $U/D=3.2$ attempts failed. Only ED rows with
an explicitly converged low-frequency estimator are plotted as $Z$
references. The D08 ED table is retained as separately labeled legacy
evidence and is never merged into D09 ED.

## Which parameters are comparable

The ED bath and the ghost $g$-sector have the same rational function form:

$$
\Delta(z)=\sum_\ell\frac{V_\ell^2}{z-\epsilon_\ell}.
$$

The References tab compares individual pole positions $\epsilon_\ell$ and
residues $V_\ell^2$. The Series tab's **g bath: ghost vs ED** preset compares
the corresponding reduced scans:

$$
|V_0|,\qquad |V_1|,\qquad |\epsilon_1|,\qquad
\sum_\ell V_\ell^2.
$$

The comparison pairs $M_g=1$ with $N_b=1$ and $M_g=3$ with $N_b=3$.
$V_1$ and $\epsilon_1$ are undefined for $N_b=1$, not zero. ED coupling
signs are gauge choices because only $V_\ell^2$ enters $\Delta(z)$. The two
ED continuation arms remain separate, and all ED markers are labeled as
physical $T/D=0$ references against the lowest stored ghost temperature
$T/D=0.001$. The References tab offers only exact shared $U/D$ values for
its one-point pole comparison. The Series overlay keeps ED-only values at
their true horizontal positions instead of silently nearest-matching them.

The registered D09 ED table stores `eps` and `V` at six significant digits.
A publication table of ED pole values would require a selected rerun that
saves full precision.

For gem $B=3$, the stored self-energy pole positions and residues are
comparable in role to the ghost $h$-sector pair. gem also stores canonical
mode energies and weights. A complete gem self-energy reconstruction must
include its stored linear term. Raw $R$ amplitudes are not compared directly
between different frameworks.

ED's interacting self-energy generally has many Lehmann poles. It is not a
two-pole $(\eta,W)$ object, and those poles were not saved in D09. NRG and
CTQMC do not have a unique finite-pole parameter vector.

## Quasiparticle-weight names

The normalized point contract keeps these meanings separate:

$$
Z_{\rm pole}
=
\left[
1-\left.\frac{\partial\Sigma}{\partial\omega}\right|_{\omega=0}
\right]^{-1},
\qquad
Z_R=R_{\rm qp}^2.
$$

`quasiparticle_weight_pole` stores the first quantity and
`quasiparticle_weight_from_r` stores the second. D09's historical source field
`Z_mats` was $Z_R$, so it is no longer shown as an independent Matsubara
estimate. The genuine legacy D08 $M_g=1$ Matsubara estimate remains separate.

## Function preview limits

The Inspect tab is for understanding one root. It reconstructs functions from
a six-significant-digit display payload with user-selected broadening. The
square preview uses a compact 512-node DOS. The lossless root archive and the
production quadrature, not browser-exported preview values, are the source for
numerical claims.

Legacy D08 roots can contain different lattice and gateway $h$-sectors. The
inspector exposes an explicit sector selector, reports the corresponding
$Z$ from the chosen poles, and never silently substitutes one sector for the
other.
