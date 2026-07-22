# Paper story — clean consolidated version

2026-07-21, audited and reconciled 2026-07-22 after the single-source merge
and the U_c1 forensics (every stale claim from the fast-moving sessions was
hunted and fixed in this pass; see §6 for the correction trail). One claim
per line,
each with its evidence source. Sources: [draft] = Static DMFT Draft April 28;
[Mott+] = the 39-page NCS consolidation document (dmft root, guide:
`docs/notes/MOTT_PLUS_GUIDE_20260720.md`); [RB] = PAPER_REBUILD_RUNBOOK;
[PCN] = POLE_COUNTING_NOTE_20260713; [BN] = GGA_DMFT_BENCHMARK_20260715 (§ as
noted); [SA] = SEMIANALYTICS_COMPARISON_20260711; [CL] = NCS_CLAIM_LEDGER;
[v1]/[v2]/[gem]/[bench] = registered gDMFT datasets — [v2] means
single-site.scan-matrix-v2 REVISION 0.2.0, the single source (61,294 rows,
both campaigns merged); [S] = measured fresh 2026-07-21/22 (this repo,
commands reproducible).

---

## 0. The thesis and the opening frame

**The opening paragraph (drop-in, user-approved 2026-07-21):**

> All three methods approach the same object — the DMFT fixed point —
> through a finite-dimensional representation, and differ in what they
> make finite and in how the finite parameters are fixed. DMFT-ED
> truncates the hybridization function to N_b bath poles fitted on the
> Matsubara axis; the impurity is then solved exactly, and its
> self-energy carries emergent, uncontrolled pole content. Ghost-GA
> enlarges the Hilbert space by B ghost orbitals and determines a static
> quasiparticle Hamiltonian variationally; the single knob simultaneously
> sets the bath, the quasiparticle space, and the self-energy resolution
> (B−1 poles), and the construction coincides with DMFT under the
> isometric condition R†R = 1. Ghost-DMFT makes both dynamical objects
> finite and independent — M_h poles for Σ, M_g for Δ — and fixes them by
> stationarity of the exact DMFT functional restricted to this manifold:
> the matching conditions are equalities of equal-time density matrices,
> every converged root is an exact stationary point at finite budgets,
> and the representation becomes complete as M_h, M_g → ∞. The question
> of this paper is then quantitative: what does each budget buy, and what
> does each closure cost?

The last sentence is the paper's structure: §1 knobs, §2 closures,
§3 budgets, §4 numbers, §5 the bond.

## 0a. The thesis, one line

Ghost-DMFT is DMFT written in a finite pole basis with two independent
budgets — M_h poles for Σ, M_g poles for the bath Δ — closed by matching
(expectation-value equalities), not by energy minimization. The paper shows
what each budget buys (single site: quasiparticle → Mott transition; bond:
singlet physics), benchmarked at matched budgets against the variational
ghost method (gGA/gem) and finite-bath DMFT-ED, with exact structural
identities (unitarity, interlacing, sum rules) that the variational scheme
provably lacks.

## 0b. The source-of-truth card (routing; supersedes every ad-hoc choice)

**One dataset: `single-site.scan-matrix-v2` revision 0.2.0** — the original
campaign plus the 20260721 canonical-grid fill merged under one id (61,294
rows; run_id prefix `d09-fill-20260721` marks the fill; contract-validated;
catalog primary routes point at it for EVERY cell, D08/v1 is historical
evidence only). Every solve route is present as labeled rows of fact —
bare, exact R-conversion, R-reoptimized refit, R-native — and NOTHING is
selected in the data; selection is analysis-time, on recorded columns.

| Cell | Primary route (catalog) | Canonical grid | Physical-gauge status |
|---|---|---|---|
| Bethe M_g=3 | D09 0.2.0 · bare | 111 U × 17 T (0.01 windows [2.40, 2.90]) | refit rows registered per bare root; native LIVE cold (protected seeding), dead only at the reproducible T = 0.07/0.1 window |
| Bethe M_g=1 | D09 · bare | 111 U × 17 T | all four gauge routes full |
| Square M_g=3 | D09 · bare | 103 U target (fill 3/17 T, SCC in progress) | old rows + fill merging per pass |
| Square M_g=1 | D09 · bare | 103 U × 17 T (ladder extended) | all four routes |
| Bethe M_g=2 | control cell (one T-row) | rides next promotion pass | insulator-death control, §2.4(d) |
| References | benchmarks-v1 + gem-v1 | gem fill running locally | gem: up arm, sumR2 ≤ 1.1, cold rows only for Z |

R-gauge facts (settled): the R-frame re-solve (`reoptimized`) reproduces
the bare roots to every stored digit where both exist — bare solves are
R-certified; `converted` is the same root's exact chart; the fill campaign
emits refit rows for every new bare root, so the physical-gauge view exists
for the whole flagship cell. The satellite POSITION is not determined by
matching in either frame (verified: refit rails at the same box) — figures
KEEP capped poles as × (§6b) and quote only V0, V1²/ε1, Δ(iω) [PCN].

Branch rules: metal = up assembly, insulator = down; cutoff doctrine
§2.4(f): metal quotable to U_c2 (first basin flip / break — prefix
cut), insulator raw params to U_x = 1.11(2) with positions never
quoted alone; U*/U_c2 drawn only
below the corridors (bethe (0.010, 0.015), square (0.004, 0.005)); NO
scheme U_c1 is ever quoted (§2.4(d) forensics: the branch end is a
pole-flight boundary, not a spinodal); derived chains resolve
campaign-duplicate keys to the newest campaign (provenance rule, counted
in the build report; all rows remain in the table); forbidden inputs:
the OLD 20260717 native bethe-mg3 metal below T=0.2, gem warm rows for
Z, sumR2 > 1.1, claim-ledger diagnostic rows.

Enforcement status: catalog primary routes → D09 for all cells (DONE,
tests re-pinned); campaign dedup in derived chains (DONE); pole-cap
keep-and-mark in figures (DONE); GUI per-cell warning banners + corridor
cap on the diagnostic U*(T) overlay (PENDING — the two remaining GUI
items). The earlier `paper-selection-v1` side-table idea is DROPPED per
user directive (no extra datasets): the single dataset + catalog rules
carry the whole truth.

## 0c. What each scheme PRESERVES — the organizing axis (proposed
2026-07-22; makes §0's frame operational)

Every method here is a rule for what survives the projection of the
exact local problem. Classify by the PRESERVED column and every
measured difference in this file becomes a corollary:

| scheme | finite object | preserved exactly | fixed by |
|---|---|---|---|
| exact DMFT | nothing | the whole function G_imp(iω) = G_loc(iω) | self-consistency |
| DMFT-ED | Δ → N_b poles | nothing — Δ approximated in a Matsubara fit metric (low-ω weighted); impurity then exact | χ² fit |
| gGA / gRISB | ghost QP space, B | energy stationarity (ground state variationally optimal) | energy minimization |
| ghost-DMFT | M_h + M_g poles | stationarity of the exact functional on the manifold + equal-time density-matrix equalities + unitarity of the canonical frame | matching (saddle) |
| SFT / VCA (Potthoff) | reference system | stationarity of the exact Ω[Σ] on the reference manifold, evaluated through the FULL function (all ω, no fit metric) | Ω-stationarity |

Corollaries as measured: gGA preserves no structural bookkeeping →
the two-deficit split (isometry ≤3% = linear term; moments 28–51%
unbooked; §2.2b), poles pulled in, Z by compensation. DMFT-ED's fit
metric → emergent Σ-pole content and opposite-side failure directions
at matched budget (§4). Ours preserves bookkeeping → the exact laws
(∫A = 1, interlacing, 2W² = U²/4 − ⟨ε_k²⟩, flat 89–90% Σ-weight,
V₀ = 0.455·√Z·D) and both-branch thermodynamic identities (conjugacy,
Clausius–Clapeyron) — at the price that nothing is optimal (saddle,
junk families, selection discipline). Even the pole-flight
compactification fits the frame: the combinations entering the
PRESERVED equalities are exactly the ones that stay finite (c* ≈ 0.40)
while unpreserved raw parameters flee (§2.4(d) test 4). SFT is the
family relative — restricted-manifold stationarity of an exact
functional, using low AND high frequencies with no fit metric — with
Σ-space rather than density matrices as the restriction language
[anchor: Potthoff, EPJB 32, 429 (2003); PRL 91, 206402 (2003) — §3c].

## 1. The knob dictionary — never misstate this again [PCN]

| framework | knob | Δ poles | Σ poles | matching |
|---|---|---|---|---|
| exact DMFT | — | continuum | continuum | G_imp = G_loc |
| DMFT-ED | N_b | N_b | emergent, many | Δ(iωₙ) fit (β=200 fictitious) |
| gGA / g-RISB | B | B | **B − 1** | static density matrices, variational |
| ghost-DMFT | M_h, M_g | **M_g** | **M_h** (→ M_h+1 canonical modes) | gateway equal-time + moment rows |

- All single-site campaigns are **M_h = 2** (Σ always a ±η pole pair, weight
  W² each) with **M_g = 1 or 3** (the bath budget that varies).
- Two correspondence axes with gGA [PCN]: bath-side M_g ↔ B (docc/energy
  benchmarks; M_g=1 vs B=1 to 4e-4, M_g=3 vs B=3 to ~4–6e-4) and
  spectral-side M_h+1 ↔ B (our M_h=2 ↔ their B=3: both have 2-pole Σ + 3
  coherent features). "M_g=1 agrees with B=1" is bath-dominance of
  ground-state observables, NOT framework coincidence — we always carry a
  Hubbard-band-capable Σ; what M_g=1 cannot hold is an *insulating bath
  configuration* (its single PH level pins at ε_F, inside the gap, and
  decouples).
- Independence is the selling point: gGA's one knob buys QP space, bath, and
  Σ resolution together; we can spend where physics needs it (M_h=4
  renormalizer at fixed M_g=1 in NCS; the M_g=2 paired-bath control).

## 2. Two closures on one manifold — the method-comparison section

### 2.1 Structure (documented + re-verified)

- gGA is variational: E_tot → exact monotonically from above (LLK Table I;
  gem −0.06184 vs LLK B=3 −0.06155 vs CTQMC −0.0621(1); the 3e-4 is the
  thermal ensemble [BN §3]).
- gGA's R is unnormalized: ΣR² ≤ 1 is the ISOMETRY — how much of the
  electron the quasiparticle space represents (0.970 at U=2.4 cold).
  Its Σ carries a linear term **sig_lin = 1 − 1/ΣR² exactly** — the
  R²-sum shortfall and the linear term are the same fact seen two ways
  [BN §4b; re-verified per-U to 4 digits [S]]. An exact Σ decays at ∞;
  the linear term is the unitarity deficit made visible. DISTINCT and
  an order of magnitude larger: the first-moment shortfall of its pole
  weights vs U²/4 (§2.2 table; decomposed in 2.2b — the two deficits
  even trend oppositely in U). Also a junk detector: gem
  rows with ΣR² > 1.1 are junk; their warm metal drifts to 1.06+ [BN §2].
- Ours closes the books: canonical transformation is unitary on the (1+M_h)
  d–h block, ΣR̃² = 1 identically, Z = R̃₀² (9e-16 on 1932 points [RB R3]);
  G from the lattice resolvent ⇒ ∫A = 1 by construction; interlacing
  −Λ<−η<0<+η<+Λ with zero violations = causality, checked not assumed.
  Mode weights are exactly (Z, (1−Z)/2, (1−Z)/2) at (0, ±Λ) [BN §4b].
- Price of matching: nothing is variational (Ω is a saddle — evaluate at
  roots, never minimize [Mott+ §3]); junk families solve the equations
  tighter than physics (residuals 1e-8 vs 1e-5) so selection must be
  gate → classify → Ω, never residual- or FE-first [RB].

### 2.2 The Σ-pole accounting (the mechanism table)

Both frameworks' Σ at matched spectral budget is one mirrored pole pair.
Measured on the cold metal branch (Bethe, T=0.001; ours [v1], gem via its
converged (R,Λ) [BN §4b], per-U re-extraction [S]):

| U/D | ours η | gem η | ours 2W²/(U²/4) | gem w/(U²/4) | ours Z | gem Z |
|---|---|---|---|---|---|---|
| 0.5 | 0.964 | 0.672 | 0.890 | 0.490 | 0.943 | 0.934 |
| 1.5 | 0.838 | 0.628 | 0.892 | 0.568 | 0.583 | 0.546 |
| 2.0 | 0.709 | 0.559 | 0.894 | 0.630 | 0.360 | 0.329 |
| 2.4 | 0.550 | 0.449 | 0.896 | 0.682 | 0.190 | 0.169 |
| 2.75 | 0.305 | 0.242 | 0.898 | 0.723 | 0.052 | 0.041 |

- Exact yardstick: first Σ-moment = U²n(1−n) = U²/4 (operator identity;
  ED satisfies it exactly at any N_b; a continuum-DMFT exact fact).
- New this session [S]: our metal holds the Σ-pole weight at a **flat
  89.0–89.8% of U²/4 along the entire branch**; the insulator carries the
  ω=0 pole (η=0 exactly) with weight ratio 0.904 (U=3) → 0.944 (U=4) → 1
  in the deep-Mott limit (where ΣW²=U²/4 and Λ→U/2 are exact [RB R3]).
- gem spends less weight (49→72% of U²/4), closer in, plus the linear term;
  the position/weight differences partly compensate in Z (median |Δη|=0.20,
  |ΔW²|=0.10, but |ΔZ|=0.028) [BN §4b]. That compensation is the concrete
  content of LLK's "Z is the framework-sensitive observable".
- ΔZ(U) shape [S]: absolute gap peaks at U/D≈1.5 (0.037) and vanishes at
  both ends; relative gap grows monotonically (1% → 21%); T-independent to
  <3% for T ≤ 0.01. Warm rows (T ≥ 0.05) are NOT a Z comparison axis —
  gem's warm Z drifts ≥ 1 and the static slope stops meaning Z [BN §2].

### 2.2b Why R differs — one choice, every observed difference (plain words)

What R IS in each scheme decides everything in the table above.

- In gGA, R is computed from the embedding wavefunction — the normalized
  overlap between the ghost quasiparticle orbitals and the physical
  electron. Nothing in that construction enforces completeness of the
  kept space, and nothing enforces moment bookkeeping on its Σ. That
  single omission has TWO distinct symptoms of very different size
  (this file's own conflation, corrected 2026-07-22 — §6): the
  ISOMETRY deficit 1 − ΣR² — the fraction of the electron the
  quasiparticle space fails to represent — is SMALL (0.3% at U=0.5 →
  3% at 2.75, cold metal) and equals the linear Σ term exactly
  (sig_lin = 1 − 1/ΣR²); the FIRST-MOMENT deficit — pole weight
  missing vs the exact U²/4 — is an order of magnitude LARGER (51% at
  U=0.5 → 28% at 2.75) and is not that number. Measured, they trend
  OPPOSITELY along the metal: at small U the scheme is nearly
  perfectly isometric (ΣR² = 0.9967 at U=0.5 — nearly DMFT by the LLK
  criterion) while its Σ carries barely half the exact moment — the
  occupied low-frequency physics needs almost no high-energy weight
  and nothing else asks for it; deeper in U, Mott physics forces
  atomic weight into the poles (moment deficit falls) while
  compressing the electron into the ghost space gets harder (isometry
  deficit grows). 1 − ΣR² remains the scheme's distance from DMFT in
  its own variables [draft; LLK]; the moment deficit is the running
  price of no bookkeeping.
- In ghost-DMFT, R̃ comes from a canonical (unitary) rotation of the
  gateway — a change of basis, not a compression. A basis change cannot
  lose electron: ΣR̃² = 1 identically, and Z = R̃₀² is then a mode
  weight, not a fit. The matching equalities must therefore place FULL
  spectral weight; our pair carries a flat ~90% of the exact U²/4, the
  missing ~10% being the multi particle-hole tail no single pair can
  represent at ANY normalization — a representation error, not a
  bookkeeping loss.
- WHY the variational closure sheds weight: the energy it minimizes is
  dominated by the occupied low-frequency region. Pulling pole weight
  closer to ω = 0 buys correlation energy; high-frequency sum rules
  cost the energy nothing, so they are simply not enforced. Hence the
  measured signature: gem's poles sit closer in (smaller η, every U)
  with less weight (49% → 72% of U²/4, RISING with U as Mott physics
  forces more of the atomic weight to be represented) — while ours
  stays flat at ~90% because an identity, not a physics regime, pins it.
- The INSULATOR contrast is a weights story, NOT an isometry story
  (measured 2026-07-22): gem's insulating ΣR² is 0.976–0.992 — in the
  gapped state completeness is cheap (no low-energy competition), so
  the isometry deficit explains only 0.03–0.05 of its Mott-pole
  deficit. The rest is under-weighted Hubbard-band poles: gem removes
  0.47 (U=3) → 0.40 (U=4) beyond the atomic U²/4, where our matching
  removes exactly the band variance ⟨ε_k²⟩ = 0.25, U-independent and
  bath-budget-independent (§2.4). Same cause as the metal — weight
  only where energy wants it — shrinking toward the atomic limit as
  the Hubbard bands come to dominate the energy as well. That is the
  entire content of "gem's Mott-pole deficit is ~2× ours with the
  opposite U-trend": ours is pinned constant by bookkeeping, theirs is
  an energy choice decaying with U.
- Same division in the mode frame (the GUI's gem overlays): our
  canonical modes sit at (0, ±Λ) with weights exactly (Z, (1−Z)/2,
  (1−Z)/2); gem's quasiparticle modes carry total weight ΣR² < 1 at
  energy-optimized positions. Mode POSITIONS compare freely; mode
  WEIGHTS only with the isometry deficit in mind.
- WHY Z still nearly agrees (the compensation): the Z of a mirrored
  pair is set by weight/position² (1/Z − 1 = 2W²/η²). A closer, lighter
  pole and a farther, heavier pole can produce nearly the same
  low-frequency slope — measured: |Δη| = 0.20 and |ΔW²| = 0.10 median,
  yet |ΔZ| = 0.028. That is the concrete content of LLK's "Z is the
  framework-sensitive observable": in the variational scheme Z is a
  ratio of two misplaced quantities protected by no sum rule; in ours
  it is pinned to the canonical mode structure.
- The division of wins follows from the same choice, with no extra
  input: energy — variational by construction (their home turf, §2.3);
  structure — unitarity, interlacing, moment accounting, and the
  both-branch thermodynamic identities (§3b) — matching by
  construction. One sentence for the draft: the variational closure
  optimizes the number it reports; the matching closure preserves the
  structure it represents; every observed difference in §2.2 follows
  from that division.

### 2.3 The honest scoreboard (fixed budget; do not overclaim)

At U/D = 2.4 cold: E_tot — gGA −0.06184, ours −0.06098, ED5 −0.06052,
ED3 −0.05772 vs exact −0.0621(1): gGA best (its home turf), ours second,
ahead of ED at equal and larger bath [S, bench]. Z — everyone above the
anchors (CTQMC β=200: 0.12, itself finite-T-biased per LLK; ED rising to
0.137 at N_b=5): gem 0.169, ours 0.190; gGA closer; no clean exact-Z anchor
exists (NRG rows carry docc/E only) — **one NRG/CTQMC Z(U) reference curve
upgrades the whole section**. docc — all methods within 1e-3 of
NRG at T=0.001 (ours +6e-4 at U=1, gGA +1e-4; tie at U=2) [S]: docc does
not discriminate. What is claimably ours at fixed budget: the exact
identities (sum rule, unitarity, interlacing, no linear-Σ pathology), the
independent budgets, both-branch thermodynamics, and — per LLK's own
axis — energy accuracy ahead of ED per orbital.

## 2.4 Where it does NOT fit — and what that tells us
(overnight session 2026-07-21→22, all [S] from registered data; this is the
"beyond the visible curves" layer — anomalies, mechanisms, and the
semianalytic questions they define)

### (a) The metal's Σ-weight constant is lattice-dependent but U-flat

2W²/(U²/4) along the cold metal branch: **0.891–0.897 (Bethe), 0.837–0.872
(square)** — flat across the whole branch in both lattices, weakly
T-dependent (Bethe 0.881–0.892 at T=0.01). So the ~10% moment deficit is
not universal noise and not U-physics: it is a **structural constant of
the M_h=2 matching closure that knows about the lattice DOS**. Open
semianalytic target: derive this constant from the
M_h=2 matching conditions (his gateway machinery is exactly suited); a
closed form for 0.89/0.85 would turn our largest unexplained number into
a theorem.

### (b) The bath budget controls what the Σ-sector can SEE

At M_g=1 the same M_h=2 h-sector abandons structure entirely: 2W²/(U²/4)
= 100–1000 (far-pole/renormalizer configuration, pure slope — the GA
limit). At M_g=3 it suddenly holds 85–90% of the exact moment at finite
η. Same Σ budget, different bath: **the equal-time matching data only
determines Σ structure when the bath can hold Hubbard-energy content**
(the satellites feed the ⟨d†h⟩/⟨h†h⟩ correlators that pin η). This is a
cross-sector mechanism no curve shows: M_g resolution feeds M_h
determinacy. It also explains from first principles why the satellite-dead
chains land exactly on the m_g=1 renormalizer metal.

### (c) The Mott pole's dressed residue: atomic weight minus band variance

Along the ENTIRE insulating branch (η = 0 exactly everywhere), the
absolute deficit is nearly constant and equals the band variance scale:

| U/D | 1.125 | 1.5 | 2.5 | 3.0 | 4.0 |
|---|---|---|---|---|---|
| U²/4 − 2W² (Bethe) | 0.244 | 0.208 | 0.210 | 0.216 | 0.225 |

vs ⟨ε²⟩ = D²/4 = **0.25** for the Bethe semicircle — and the square
lattice, whose elliptic DOS has the SAME variance 1/4 in D units, gives
**0.227–0.243**. So, measured and lattice-robust:

    2W²_ins ≈ U²/4 − ⟨ε_k²⟩  (+ c/U recovery, c ≈ 0.1)

Hubbard-I would give deficit 0. The matching closure dresses the ω=0
Mott pole by subtracting (approximately) the kinetic variance — a
quantitative beyond-Hubbard-I statement about the Mott insulator that
only a finite-pole Σ makes visible. Second semianalytic ask: derive the
⟨ε²⟩ subtraction from the deep-Mott expansion of the matching equations.

### (d) The insulator's over-survival, its ending, and the three kinds of
branch end (fully audited 2026-07-22)

(U² − D²)/4 → 0 at U = D, and the scheme's insulating branch ends at
**U_flight = 1.11(2) (Bethe, forensics-grade: last interior root
U = 1.125, none at 1.100)**. Square: the registered scan's
`equations_accepted` flag extends to ≈ 1.0, but that is a LOOSE
per-campaign gate — the rows below ≈ 1.25 sit with V₁ on its cap and
‖F‖ off the root plateau (the Series left-tail the GUI currently draws;
the coupling-railed onset ≈ 1.2–1.3 is the honest square end pending a
forensics-grade run). Same lesson at home as in the taxonomy:
ACCEPTANCE BOUNDARY ≠ BRANCH END, and our own registered flags contain
both. The ENDING was audited (forensics below): it is a pole-flight
boundary of the finite-pole parametrization, NOT a thermodynamic
spinodal — the weight law sets WHERE the branch ends, the runaway is
HOW. gem's Mott-pole deficit is roughly TWICE ours (0.52 at
U=3, opposite U-trend; decomposed in §2.2b — an under-weighting
choice at near-perfect isometry, not a representation loss), and its cold down-sweep loses the insulator at
U = 2.90 — but that number is gem's iteration-basin artifact, not gGA's
U_c1: Lanatà's published variational endpoint is ≈ 2.0 [their PRB;
pin]. The honest cross-method statement is the three-ends taxonomy
below, which REPLACES an earlier "closures bracket the spinodal" claim.

**The eigenvalue form of the over-survival (user observation,
2026-07-22 night; ATTRIBUTION CORRECTED same night — everything in
this block is GHOST-DMFT-internal, nothing here is an exact-DMFT
result):** within our scheme, the inner gateway eigenvalue obeys the
user's first-order Landau expansion OF THE MATCHING CONDITIONS,
λ₋ ≈ V₀η/(√2 W), essentially exactly along the metal (λ-frame figure,
panel c: our exact numerics and the expansion coincide) — the Landau
reconstruction is the correct linearization of ghost-DMFT near its own
soft mode. Substituting our measured laws V₀ = 0.455·√Z·D and
η = Λ√Z gives λ₋ ≈ 0.32·(Λ/W)·Z·D ∝ Z — the scheme's inner eigenvalue
is its coherence scale in disguise [prefactor check pending;
sharpen_KLR]. On our insulating branch V₀ → 0 and η = 0, so λ₋ = 0 AT
MACHINE PRECISION: the scheme's own soft mode is structurally dead on
the insulator — the amplitude that would carry a destabilization is a
variable the equal-time closure sets to exact zero. The contrast with
exact DMFT must be stated carefully (an earlier version of this block
claimed "exact DMFT keeps V₀ finite" — WRONG as stated: the exact T=0
insulator also has Δ(0) = 0 inside its clean gap): exact DMFT's U_c1
instability is carried by the ω-STRUCTURE near the gap edges closing
in (BCV; the KLR soft mode of the exact Landau functional) — it does
not require weight at ω = 0 beforehand. So the honest one-liner is
not "small vs zero" but: **the exact instability lives in variables
the static closure does not match; our λ₋ = 0 identically because the
closure admits the strictly decoupled insulator.** The M_g = 2/3/5
and M_h = 4 controls are that sentence measured four ways.

Mechanism of the over-survival (plain words, for the paper): exact
DMFT's insulator dies when the gap closes and the screening resonance
re-forms inside it — low-energy bath weight is always available to seed
the metal's return. Our insulating configuration has NO live low-energy
channel (V₀ = 0 IS the insulator; the satellites sit at Hubbard
energies), so nothing can seed that destruction, and the insulating
fixed point stays stationary until the dressed Mott pole itself runs
out of weight at U ≈ D. So: our scheme's insulator-down arm survives to
less than HALF the known U_c1, the death mechanism (not the accuracy) is
what is missing at M_g=3, and the paper quotes NO scheme U_c1.
**The U_c1 forensics (2026-07-22, three tests, all local):** the claim
"our insulator survives to U ≈ 1.1" was itself audited after an external
critique (correctly) noted that 1.125 is an acceptance boundary, not a
demonstrated branch end. Results:
1. **Fold test — negative** (re-measured 2026-07-22 in the five-quantity
   signature run, which supersedes the first coarse scan; conclusion
   unchanged). s_min of the residual Jacobian stays within
   [4.4e-6, 2.9e-5] from U = 1.6 through the entire failed descent to
   0.70, mildly RISING toward small U, never → 0: no fold, no partner
   root, no spinodal. ‖F‖ leaves the root plateau (2–6e-5 =
   re-evaluation noise on stored campaign roots) at U = 1.100 and ramps
   SMOOTHLY ×20 to 1.5e-3 by U = 0.70 — a supply failure, not a
   collision.
2. **Lifted-box continuation — pole flight with DIVERGING DEMAND.**
   Boxes raised to 24: the last interior root is U = 1.125
   (V₁ = 6.27 — above the registered cap 5 that was already squeezing
   the U = 1.15 row — ε_g = 11.27, genuinely interior); at U = 1.100
   the optimizer's best point jumps to V₁ = 12.8, ε_g = 20.8 with ‖F‖
   off-plateau; below, ε_g rails at 24, then V₁ rails at 24 by
   U = 0.80. The sharpener (external critique's test, run verbatim):
   **V₁²/ε_g — the second-order virtual-excitation scale, the
   combination a far satellite still exerts on low energies and the
   number that stays meaningful when positions rail — also diverges**
   (0.20 at U = 3 → 0.83 at 1.6 → 3.49 at 1.125 → 7.9 at 1.10 → 24,
   railed). The critique expected this invariant to stay controlled
   (which would have meant a redundant flat-direction escape at fixed
   physics); measured, it does NOT — the equations demand unboundedly
   more bath influence than any finite configuration supplies. Formal
   name: a NONCOMPACT ENDPOINT of the finite-pole representation.
   Onset where (U²−D²)/4 crosses zero at U = D. Figure:
   fig_story_poleflight (story set); source CSV with provenance in
   studies/paper_figures/data/. PARTLY SUPERSEDED by test 4: the ‖F‖
   ramp is box-limited (falls ∝ 1/ε as the box grows) — the runaway is
   a minimizing SEQUENCE, not a dead end.
3. **Hessian stability test — structurally uninformative.** ∂²F has two
   negative modes on BOTH branches (metal control: −4.3 at U=2.7): the
   matching functional is a saddle by construction [Mott+ §3], so
   Hessian signature counting CANNOT distinguish stable from unstable
   DMFT branches — negative directions are present even for the
   physical metal. The correct stability object is the linearized
   self-consistency map δx_{n+1} = J_FP δx_n: a branch is iteratively
   stable while the leading eigenvalue of J_FP is < 1, and a SPINODAL
   is where that eigenvalue reaches 1 (Strand's boundary; the KLR soft
   mode in our variables [sharpen_KLR]). Computing J_FP is the open
   follow-up — raw parameter space cannot decide it.
4. **Box-scaling test (same day, evening) — the runaway is a boundary
   SOLUTION.** Repeating the descent with satellite boxes 24 / 80 / 240
   (external protocol: compactified variables x = 1/ε, c = V₁²/ε²):
   (i) at every U below the crossover, ‖F‖ FALLS with the box, ∝ 1/ε
   (U=1.00: 5.6e-4 → 1.7e-4 → 1.1e-4) — the finite-box ramp of test 2
   was approximation error, and the infimum is 0 at the boundary;
   (ii) the mixing ratio is box-INDEPENDENT at matched U and saturates:
   V₁/ε → 0.61–0.68, i.e. c* ≈ 0.40–0.46 finite (so the critique's
   dimensionless c = V₁²/ε² stays controlled while V₁²/ε diverges ∝ ε
   at fixed c — both statements were right, about different
   combinations); (iii) for U ≥ 1.125 genuine finite roots persist at
   plateau residual with the POSITION soft (valley ε ≈ 14–20 at box
   240 vs 11–12 at the registered caps — mild cap-squeeze all along,
   invariants unaffected, consistent with [PCN] position-sloppiness);
   (iv) 2W² tracks (U²−D²)/4 with a small positive finite-T offset
   down through the crossover, then DEPARTS the law below U ≈ 1.05 and
   SATURATES at ≈ 0.05 to at least U = 0.85 — the prediction
   "compactified branch terminates at the weight-law zero U = D" was
   tested and REFUTED at the probed ε ≤ 200. Limit object: a PH pair at
   ε → ∞ with V/ε → √c* contributes Δ_pair(iω) → −2c·iω — a pure
   ω-LINEAR bath term, i.e. a RENORMALIZER (the NCS M_h=4 pole-at-
   infinity concept, emerging spontaneously in the single-site
   insulator's g-sector). Below the crossover the insulator wants part
   of its bath budget spent as a renormalizer, which finite-position
   M_g=3 cannot express. Consequences: U_flight is REINTERPRETED as the
   finite-root → boundary crossover, still 1.11(2) at plateau
   tolerance but not a branch DEATH; no raw parameter (V₁, ε₁, or any
   cutoff on them) can locate a physical U_c1 — thresholds on them
   measure the box, not physics; the right next implementation is the
   compactified solve itself (two finite poles + an explicit ω-linear
   coefficient as a free parameter), which would make the boundary
   branch regular and answer whether W → 0 in the true ε → ∞ limit
   (§7 ask).
5. **M_g=5 control (2026-07-22, night; PH-symmetric, central + two
   pairs, 7 params, T=0.001 Bethe descent U=4.0 → 0.90): the crossover
   is BUDGET-INDEPENDENT.** Plateau-quality roots (‖F‖ ≈ 2e-5) down to
   U = 1.125; flight onset between 1.125 and 1.100 — U_x^(5) = U_x^(3)
   = 1.11(2) within grid resolution. With M_g=2's consistent endpoint,
   the crossover does NOT creep with bath expressivity: it is pinned
   by the h-sector, and the external U_c1^(M_g) superscript is
   unnecessary at these budgets — the crossover belongs to the CLOSURE
   (static matching) and lattice, not the budget. Sharper structure,
   both budgets: 2W² sits ABOVE the dressed law by a finite-T offset
   (+0.045 at U=1.6 → +0.03 at 1.2 → +0.017 at 1.125 → +0.005 at
   1.10) and the flight starts EXACTLY where the offset is exhausted —
   U_x is where the measured pole weight meets the law line. Below,
   2W² freezes at ≈ 0.05 at BOTH budgets (the same scale as the
   offset) while the law goes negative. Also: V₀ = 0 the whole way
   (proper insulator), the second pair parks at Hubbard positions
   (never takes a screening role — M_g=2's lesson again), and there is
   NO new instability anywhere near U ≈ 2.0–2.4: smooth plateau roots
   straight through the exact insulator's death region — the
   closure-deep blindness confirmed at a third budget. Prediction this
   creates: U_x(T) should track the offset's T-dependence (testable;
   not run). Data: scratch descent log; codec = 10-line PH-symmetric
   extension of the M_g=2 control's, reproducible from the frozen
   producers.
6. **M_h=4 control (same night; two Σ pairs at M_g=3, 7 params): the
   extra Σ freedom is INERT under the present matching set — and the
   crossover does not move.** The residual builder returns the SAME 14
   matching rows as M_h=2 (no equalities exist for the new h-ghosts),
   and the run shows exactly what the preservation frame predicts for
   undetermined freedom: the second pair sits FROZEN at its seed
   (W₂ = 0.3000, η₂ = 2.0000, unmoved over 73 points, U = 4.0 → 0.85)
   — an exact flat direction. The active pair keeps η₁ = 0 (the Mott
   pole) and rides law + the same finite-T offset once the spectator's
   frozen 2W₂² = 0.18 is subtracted (active weight at the crossover
   0.087 vs law 0.066; frozen sub-floor active weight ≈ 0.058 — the
   same ≈ 0.05). Flight onset again between 1.125 and 1.100: **U_x
   unmoved at a THIRD budget axis.** Fits ~10× tighter on the plateau
   (‖F‖ ~ 1e-6): more parameters fit the same rows better, determine
   nothing new. Honest scope: this tests M_h=4 under the M_h=2 row
   set; the REAL M_h=4 question needs the enlarged equal-time set
   (draft Eqs. 16/19 generalized to the new h-ghosts — the NCS
   renormalizer machinery has the two-site version; single-site port
   is the ask). Until then the statement is: enlarging Σ without
   enlarging the PRESERVED data does nothing — representation is not
   the bottleneck, the matched data is.

**Three different "ends", three symbols, never to be conflated** (this
replaces the earlier bracketing claim, whose gem-side number was a
sweep artifact):
- **U_flight ≈ 1.1 D**: matching's stationary root ceases to exist as a
  finite-pole object (pole flight / noncompact endpoint; Bethe
  forensics-grade 1.11(2); square registered railing onset ≈ 1.2–1.3,
  forensics-grade run pending);
- **U_c1^gGA ≈ 2.0 D**: gGA's VARIATIONAL existence endpoint (Lanatà's
  published number; pin pending; our local gem down-sweep's 2.90 was
  its iteration-basin artifact — a third kind of end, algorithmic);
- **U_c1^DMFT ≈ 2.4 D**: exact DMFT's metastability endpoint (BCV pin
  pending).
The paper quotes NO scheme U_c1; "converged = true" is never "metastable
phase exists" — the symbols exist precisely so that no numerical branch
termination gets mistaken for a physical critical point.

**Why flight, in plain words (the paragraph for the draft):** the insulator's
identity is the Σ-pole at ω = 0, and its measured weight budget is
2W² = U²/4 − ⟨ε_k²⟩ — the atomic weight minus what band motion eats.
As U → D from above, that budget runs out: the wall the insulator is
built of runs out of bricks. The down-sweep's equal-time data still
describe an insulator (n = 1/2, low double occupancy, U-scale
high-energy weight), so the matching equations keep demanding one — and
the only lever left is the bath satellite, pushed simultaneously to
larger coupling and larger distance; even V₁²/ε_g, the grip a far
satellite keeps on the low-energy sector, must grow without bound.
Every step outward improves the residual slightly; no finite point
satisfies it; the root exits through the boundary of parameter space.
Nothing became unstable (s_min regular) and nothing collided (no fold).
[Refined by forensics test 4: the exit is a CONVERGING limit, not a
failure — the boundary object is the insulator with a renormalizer
(ω-linear) bath component at fixed mixing c* ≈ 0.40, and the residual
of the finite-box approximants falls as 1/ε.] That is why this endpoint
must never be called U_c1. The trend is visible long before the end:
along the cold insulator, V₁ rises monotonically as U falls from 4, the
demanded satellite position rises with it (detached from the cap at a
soft raw ≈ 10 on both lattices deep in the insulator — near the seed
scale, weakly determined, quote V₁²/ε_g not ε_g — back on the cap by
U ≈ 2.5–2.9), and V₁²/ε_g runs 0.20 (U=3) → 0.83 (1.6) → ∞ (U_flight):
the bath must grip harder as the Mott pole weakens, and the demanded
grip diverges when the weight law hits its floor. The bare mixing
ratio V₁/ε_g tells the same story as a regime statement: 0.11 (U=4)
→ 0.27 (1.6) → 0.56 (last root) → toward V₁ = ε_g along the escape —
the satellite leaves the perturbative far-weak-level regime BEFORE the
branch ends (fig_story_poleflight, third panel; ratio crosses ~0.3
near U ≈ 1.5).

Draft summary sentence (tightened per an external critique, adopted): "We
explicitly tested whether the low-U termination of the insulating
finite-pole branch is a fold and found that it is not: the residual
Jacobian remains regular while the auxiliary pole parameters — and the
low-energy coupling scale V₁²/ε_g they leave behind — run to infinity.
The endpoint is therefore a noncompact pole-flight boundary of the
restricted spectral representation, occurring at the dressed Mott-pole
weight floor U ≈ D, rather than a thermodynamic spinodal. Consequently
the left edge of the physical coexistence wedge is not predicted by
static matching at the bath budgets examined."

**The M_g=2 knob (same day, 20 s): prediction REFUTED, and the
refutation is the better result.** M_g=2 = one PH bath pair with free position and no central
level — the bath *can* supply low-energy weight. Outcome: the insulator
survives to U ≈ 1.25 (same as M_g=3), the pair stays parked at
ε_g ≈ 10–12 the whole descent (never takes the screening role), and the
Mott-pole deficits are IDENTICAL to M_g=3 (0.21/0.22/0.224 at
U = 2.5/3/4). Two conclusions: (1) the dressed Mott-pole residue law
U²/4 − ⟨ε²⟩ is bath-budget-independent — a property of the Σ-sector and
lattice alone; (2) the over-survival is closure-deep, not budget-shallow:
**static equal-time matching has no counterpart of the dynamical
gap-closing instability that kills the exact insulator at U_c1, at the
budgets examined (M_g = 2 and 3).** Not claimed for all budgets — in
the large-pole limit the parametrization must recover exact DMFT,
stability structure included; what the control establishes is that the
blindness is not curable by one more bath knob. The open question this creates is pointed at the
consistency-matched closure (the Kadanoff–Baym rank-restoring
conditions, Mott+ §9): it is the natural candidate for what would reintroduce the insulator's death — the
designed control says plainly that nothing less dynamical will.
(Caveats: one cold T-row; below U ≈ 1.25 the failed descent rows are
bound-railed, honestly recorded as non-converged.)
Endpoint audit (same day): the M_g=2 branch end passes through the SAME
forensics as M_g=3 — s_min rises, never → 0, and at matched U the
(‖F‖, s_min) values agree with the M_g=3 scan to three digits. The
insulator's pole-flight ending is budget-independent down to the
numerics: it belongs to the h-sector Mott pole, the bath is a passenger.
Data: bethe_mg2_bare (222 records) is wired into the promotion list and
enters D09 on the next pass.

### (e) V₀ along the metal: the law, the ending, and the plateau that
confused everyone (measured 2026-07-22; resolves the parked V0 ask)

Cold Bethe m_g=3 bare metal-up (registered v2, basin=metal rows only):
- **V₀ never goes to 0 because the metal branch dies first.** The
  first-order spinodal ends the branch at U_c2 = 2.816 with Z still
  finite (last basin=metal row U=2.81: Z = 0.025, V₀ = 0.072). V₀ → 0
  would need Z → 0 continuously — the T = 0 second-order scenario that
  never happens at finite T.
- **The measured law is V₀ = c·√Z with c = 0.455 D** — constant to
  0.6% over the endgame (U = 2.76–2.81 while Z halves), drifting only
  from 0.335 at U = 0.5 (weak-coupling crossover). Physically: V₀² is
  the bath's low-energy spectral weight, and the quasiparticle part of
  Δ = (D²/4)·G carries weight Z·D²/4 — measured V₀²/(Z D²/4) ≈ 0.83.
  The central level IS the screening resonance's weight, and it scales
  with Z, not with any exchange scale.
- **A/U is refuted**: V₀·U is non-monotone (0.16 → 0.48 peak near
  U ≈ 2 → 0.18) — no meaningful A exists. The t²/U-type intuition
  lives elsewhere: in the INSULATOR'S V₁²/ε₁ (virtual-excitation
  scale, §2.4(d)), not in the metal's V₀.
- **The "V₀ converges to a value ≈ 0.06" observation is the
  post-spinodal tail**: for U ≥ 2.82 the up-chain's rows carry
  basin=other (the registered classifier itself says the chain left
  the metal basin) — a weak-resonance junk root with V₀ ≈ 0.059–0.064,
  Z ≈ 0.018 flat. Not metal physics; Series/Inspect show it honestly
  once the basin column is read.
- Companion constants now measured on BOTH sectors of the metal: the
  Σ-pole pair holds 89–90% of its exact weight U²/4; the central bath
  level holds ≈ 83% of the naive quasiparticle weight Z D²/4. Same
  ~10–17% multi-particle-hole tail, two sectors — one derivation ask.
- **The post-spinodal region supports NO V₀ fit at all (probed
  2026-07-22, U=3.5):** the basin=other tail family is a bound-railed
  pseudo-root — W sits AT its box (W = 10, i.e. 2W² = 200 vs exact
  U²/4 = 3.06), the satellite is dead (V₁ = 0), ‖F‖ is ~30× the root
  plateau, and a stiffness probe finds V₀ SOFT with the refit
  PREFERRING V₀ = 0 (‖F‖ 1.6e-4 at V₀=0 vs 4.5e-4 at the stored
  0.0638) — the recorded 0.06 is chain-seed memory, and its raw value
  is lattice-INDEPENDENT (bethe 0.0614, square raw 0.0616), which no
  physical coupling is. Third instance today of acceptance ≠
  existence, now on the metal side. Consequences: (i) any A/U (or
  other) fit in that region is moot — there is nothing physical to
  fit; the two real V₀ facts are the metal law V₀ = 0.455·√Z·D up to
  the spinodal and V₀ ≡ 0 in the insulator; (ii) NEW enforcement ask:
  branch assemblies currently splice basin=other rows onto the metal
  branch past U_c2 — assemblies should cut (or families split) at the
  basin flip, and W-at-cap should be an admissibility flag like the
  satellite caps (§7).

### (f) The cutoff doctrine — where each direction's numbers end, and
the physical reason (2026-07-22; answers "how do I choose the cutoff")

**Principle: a quantity is quotable exactly where its branch exists as
a finite regular root. The cutoff is never a threshold on the quantity
itself** (no "V₀ < 0.05 = dead", no "ε > 10⁴ = gone") **— it is the
existence boundary of the stationary object, read from recorded
columns** (basin, cap flags, residual vs the campaign's root plateau).
The two sweep directions end by DIFFERENT physical events, so their
cutoffs have different standing:

- **METAL (up): ends at the spinodal U_c2(T) — a thermodynamic event.**
  The branch loses existence (in iteration language: the J_FP
  eigenvalue reaches 1, the KLR soft mode). Everything metallic (Z,
  V₀, η, W) is quotable up to and including U_c2, and V₀'s apparent
  survival is just the law V₀ = c√Z ending at finite Z. Operational
  cut: the FIRST basin flip or recorded continuity break, whichever
  comes first (prefix cut — the classifier flip-flops in the
  pseudo-family region, so filtering is wrong; fig_v0_death implements
  it). U_c2 itself is physics: it belongs on the phase diagram (below
  the corridor), and the pseudo-family beyond it is never drawn.
- **INSULATOR (down): two rules, because the ending is a handover, not
  a death.** (1) Variable rule, all U: the satellite POSITION is
  valley-soft everywhere (ε ≈ 14–20 at equal residual, box 240) —
  never quote ε₁ or V₁ alone; quote the invariants V₁²/ε₁, V₁/ε₁,
  Δ(iω). (2) Branch rule: finite roots end at the crossover
  U_x = 1.11(2) (Bethe cold; square pending). Below U_x the stationary
  point exists only at the compactification boundary (the ω-linear /
  renormalizer bath limit, (d) test 4): raw parameters there are
  BOX-RELATIVE and must never be plotted as data; the preserved
  combinations (c* ≈ 0.40 and the equal-time entries) remain finite
  and may appear only as boundary-limit diagnostics with an explicit
  O(1/ε_box) error label. U_x is METHOD, not physics — quote it as the
  finite-representation crossover U_x^(M_g=3), never as U_c1, and
  take no thermodynamics from below it.
- **The asymmetry is itself a paper claim:** in this scheme the metal
  ends PHYSICALLY (a true spinodal — a trustworthy U_c2(T), the sharp
  right edge of the hysteresis wedge) while the insulator ends
  REPRESENTATIONALLY (no fold; handover to a renormalizer bath). That
  is exactly why the computed wedge has a sharp right edge and an open
  left edge at finite bath budget, and why the left edge awaits the
  compactified solve (§7).
- Recorded-column status: basin, breaks, and residual are recorded;
  W-at-cap is NOT captured by source_optimizer_active_bound (measured:
  the U = 3.5 pseudo-row carries bound = false with W exactly at its
  cap) — until the flag ask lands, the operational metal cut is basin
  flip + first break.

### (g) The gateway scale crossover sits just below the transition

Λ/(U/2) along the cold metal: 2.07 (U=1) → 1.00 at **U = 2.62** → the
gateway's outer scale switches from band-dominated to
interaction-dominated ~5% below U* = 2.757, with the insulator's Λ
approaching U/2 from below. Reported as a measured observation (the
transition happens where the gateway becomes atomic-like), not yet a law.

### Derivation asks distilled from this section
1. Derive the metal's Σ-weight constant (0.89 Bethe / 0.85 square) from
   the M_h=2 matching — the draft's gateway algebra.
2. Derive 2W²_ins = U²/4 − ⟨ε²⟩ + O(1/U) from the deep-Mott expansion.
3. Exact Z(U) anchor (unchanged ask).
4. Pin the literature numbers for the three-ends taxonomy in (d):
   exact U_c1 from BCV Fig. 9, and gGA's variational U_c1 (~2.0) from
   Lanatà PRB 96, 195126.
5. Stability follow-up (open): metastable-vs-saddle needs the leading
   eigenvalue of the linearized self-consistency map J_FP (spinodal =
   eigenvalue → 1; Strand / KLR soft mode) — raw parameter space cannot
   decide it (§2.4(d) test 3).
6. GUI honesty (from the 2026-07-22 screenshot session): the Series tab
   draws the recorded NON-converged descent tails (bound-railed V₁,
   wandering ε_g below U_flight) indistinguishably from data — mark
   rows hollow/× when the coupling sits on its cap or ‖F‖ is off the
   root plateau. Related data-quality item: `physically_admissible` is
   NULL throughout v2 and `equations_accepted` is a loose per-campaign
   gate (admits Bethe cold rows to 0.95, below the demonstrated
   U_flight = 1.11(2)) — either populate the admissibility verdict or
   have consumers derive it; the selection audit should never read
   `equations_accepted` as "root exists".
7. Branch-assembly honesty (from the V₀-tail probe, §2.4(e)): cut
   assemblies (or split families) at the basin flip so basin=other
   pseudo-roots stop extending the metal past U_c2; make W-at-cap an
   admissibility flag alongside the satellite caps.
8. Square forensics-grade endpoint: repeat the five-quantity signature
   run (fig_story_poleflight) on the square lattice — expected to land
   at its common weight floor U = D like Bethe; until then the square
   end is quoted as "railing onset ≈ 1.2–1.3".
9. Landau reconstruction port (user request 2026-07-22 — "atlas lost
   my landau fittings"): NOTHING was lost — the corpus lives on the
   dmft side and was never ported: study/landau_recon/
   (landau_reconstruction.py, ghost_dmft_landau_v2.tex/pdf),
   study/{canonical_landau_reconstruction, landau_functional_bethe,
   STUDY_PACK_canonical_R_landau}.md, deliverable
   results/deliverables/06_square-landau/ (two-field finite-T), plus
   archive drafts (landau_two_variable_matching.tex). The frame: Ω as
   a Landau-type functional in the canonical R₀ [study pack §0].
   Target port: a paper_figures module refitting fresh per the
   reconstruction protocol — v2 carries canonical_r_reduced and
   grand_potential_over_d on both branches; if the protocol needs
   off-root constrained solves, they run dmft-side and the fit results
   import as a small reference table. Meanwhile the GUI already plots
   the canonical columns: Series → quantity groups "lambda" (λ_red/D)
   and "R" (R_red).
10. Housekeeping: fig_story.py/compare ROUTE still pins bethe m_g=3 to
   v1 (predates the route flip; values agree with v2 to 4+ decimals) —
   flip to v2 and re-verify the quoted constants on rebuild.
   fig_v0_death is already v2 + doctrine-cut.
11. M_h=4 matching rows (from control 6): generalize the equal-time
   matching set to added h-ghosts for the single site (the NCS
   renormalizer machinery carries the two-site version) — the true
   M_h=4 insulator test, and the precise sense in which "the matched
   data, not the representation, is the bottleneck" becomes testable.
12. Cheap fourth column + stability demonstrator (optional, from the
   TRIQS sweep): an IPT Bethe up/down hysteresis run on our T-ladder
   (deterministic, minutes) gives IPT's U_c1/U_c2/Z(U) as a clearly
   labeled reference scheme, and its DMFT loop is the clean place to
   demonstrate the J_FP iteration-multiplier → 1 spinodal detector
   before applying the same diagnostic to our matching loop (closes
   ask 5 with a protocol the field recognizes).

## 3. Single site — what each bath budget buys

### 3.1 M_g = 1: the quasiparticle and nothing else [RB R1, SA]

BR metal, continuous collapse; exact-T=0 window brackets the collapse at
U_c/D ∈ (3.39, 3.40) vs analytic 32/3π = 3.3953 [BN §4]. The insulator is
structurally impossible (PH bath level pinned at ε_F decouples; every
descent fails the gate on both lattices — the documented negative result).
Both semianalytic documents agree once translated; cite the Mott+ document's
Secs. 12–18/24–25 only (its Sec. 12 retracts the early purity sections)
[SA]. Anchored (Λ=U/2) vs free-λ frames are the two known frames of the
same theory; production numbers use the free frame [SA].

### 3.2 M_g = 3: the Mott transition [RB R2, v1]

Two gated branches; insulator = V₀→0 with ±V₁ alive (bath satellites at
Hubbard energies hold the gap; total channel death = junk, rejected).
First-order machinery from registered data [v1, S]:

| T/D | U* | U_c2 | U_c2−U* |
|---|---|---|---|
| 0.001 | 2.757 | 2.816 | 0.059 |
| 0.005 | 2.598 | 2.646 | 0.048 |
| 0.008 | 2.528 | 2.550 | 0.022 |
| 0.010 | 2.492 | 2.500 | 0.008 |
| 0.015 | — | — | closed |

Endpoint corridors (final flag state, fine-window 2026-07-15): **Bethe
T*/D ∈ (0.01, 0.015); square (0.004, 0.005)** [RB flag 2] — matches the
registered-data derivation [S]. U*(T) is a two-code line (the reference implementation rerun
fresh, ≤0.1–0.5%); U_c2(0.001)=2.80–2.82 now AGREES with his fresh rerun
(2.825; the old 2.9–3.0 was his loose acceptance) [RB flag 1]. Square U*
sits ~4% lower and the endpoint genuinely colder — a real lattice effect.
Caveat: the assembled insulator arm reaches U ≈ 1.12 flat in T — a
pole-flight boundary of the parametrization, not a spinodal (full
forensics in §2.4(d)); NO scheme U_c1 is quoted anywhere.

### 3.3 The centerpiece figure: the gateway ladder as the Mott transition

fig_lambda_frame(a), all elements identities: center rung = quasiparticle
(R̃₀²=Z); inner rungs ±η = the Σ-poles; outer ±Λ, Λ²=η²+2W²; weights
(Z, (1−Z)/2, (1−Z)/2); Z=(η/Λ)² [S; BN §4b]. Metal: η slides in
(0.96→0.24), Λ barely moves — the metal dies by its scattering pole
descending onto its own quasiparticle; at the spinodal η is still finite:
the ladder jumps = first order. Insulator: η=0 exactly (Σ ≈ 2W²/ω — what a
Mott gap IS in Σ language; exact insulator = (U²/4)/ω, ours at 90–94% of
that weight, → exact deep in). Λ→U/2 = atomic Hubbard levels. Transition =
the rungs trading places; coexistence = both ladder configurations solving
the equations; soft mode λ₋ ≈ V₀η/(√2W) near the jump (both semianalytic
docs [SA]; insulator λ₋=0 machine precision) — the same mode the
the consolidation code's endpoint detector sharpen_KLR tracks (2λ₋). Figure polish: gate the insulator cut at its gated end (still open);
the `_parse_arr` semicolon bug is FIXED and the gGA ±η overlay renders
(50 cold points) [S 07-22].

### 3.4 Open: V0 along the metal branch

My session reading (v1 bethe bare metal): cold V0 falls to ~0.06 ∝ 0.45√Z
at the spinodal; warm (T≥0.01, above endpoint) tails flatten ~U^−1.15
(t²/U-compatible). **User's own inspection disagrees** — reconcile against
the exact view they use before anything enters the paper. Related [PCN]:
bath-pole positions are representation-laden; the invariant object is
Δ(iω) — any V0 claim should also be stated through Δ.

## 3b. First-order thermodynamics: the checks that make U*(T) quotable
(added 2026-07-21, all from registered v1 bethe m_g=3 data, zero new solves)

1. **Thermodynamic conjugacy across branches.** d(ΔΩ)/dU = ΔD (the
   ∂Ω/∂U = ⟨n↑n↓⟩ identity applied to the branch difference) holds to
   **0.1%** at every 0.05-grid point of the coexistence window at T=0.001
   (ratio 1.000–1.001; 1.03 only at the last point before the spinodal).
   The internal-consistency proof of the Ω evaluation behind U*. (NCS
   analogue already verified at 1.5e-6 [CL]; now the single-site line
   has it too.)
2. **Clausius–Clapeyron closes on our own data.** dU*/dT = (S_met −
   S_ins)/(D_met − D_ins): the registered U*(T) slope is negative
   everywhere (−54 → −18 over T = 0.001 → 0.01), and the slope-inferred
   entropy jump agrees with the DIRECT measurement −∂(ΔΩ)/∂T at fixed U
   to ~4% (0.588 vs 0.565 at T=0.002, U=2.70).
3. **The electronic Pomeranchuk effect, measured.** ΔS_direct = 0.63 at
   the coldest usable row (T=0.002, U=2.5), decreasing with T and U —
   approaching the free-local-moment value **ln 2 = 0.693 from below** as
   T→0, shrinking as the metal's linear-in-T entropy grows. Heating
   favors the insulator because it carries the moment entropy; that is
   why the U*(T) line leans left.
   Caveats: finite differences on the T-ladder (coldest centered row is
   T=0.002); D at the grid point nearest U*; no direct entropy column —
   both ΔS routes are Ω-derived, which is why their 4% agreement is a
   check, not a tautology.

## 3c. Literature anchors (which citation underwrites which claim)

- Georges–Kotliar–Krauth–Rozenberg, RMP 68, 13 (1996) §II.A–B, VII.C–E —
  the coexistence canon (U_c1/U_c2 spinodals, U* by free energy). Our
  §3.2 table is this picture from a matching closure.
- Bulla–Costi–Vollhardt, PRB 64, 045103 (2001) — spectra through the
  transition, up/down hysteresis, and the explicit warning that a
  finite-T Z estimator is not a transition criterion → literature backing
  for our "warm-T Z is not a comparison axis" rule [BN §2].
- Joo–Oudovenko, PRB 64, 193102 (2001) — critical slowing + convergence
  strictness near coexistence → the calibrated-gate protocol's ancestry.
- Kotliar–Lange–Rozenberg, PRL 84, 5180 (2000) — Landau functional, soft
  mode at the endpoint. **The consolidation code's detector is literally named
  sharpen_KLR**; our λ₋ ≈ V₀η/(√2W) is this scalar mode in the gateway
  frame. Cite where ladder panel (c) meets the endpoint corridor.
- Strand et al., PRB 83, 205136 (2011) — Z-shaped isotherm, saddle-node
  folds, Maxwell construction, pseudo-arclength continuation. Underwrites
  the spinodal reading ("a failed forward scan = a fold"); optional
  outlook: tracing the unstable middle branch.
- Lanatà et al., PRB 96, 195126 (2017) — ghost-GA Mott: their Eqs.
  (9)/(12) are the metallic vs insulating finite-pole Σ; their ghost
  counting is the variational twin of our ladder anatomy (§3.3) and knob
  dictionary (§1).
- Lee–Lanatà–Kotliar, PRB 107, L121104 (2023) — already central (§2, §4).
- Liebsch–Ishida, JPCM 24, 053201 (2012) — when a discrete bath is
  adequate; cite with the ED comparisons.
- Caffarel–Krauth, PRL 72, 1545 (1994) — ED-DMFT origin.
- Park–Haule–Kotliar, PRL 101, 186403 (2008) — cluster coexistence stays
  first order with shifted U_c's → the bridge to Mott+'s singlet-assisted
  localization (U_c2 ~8% below single-site).
- Bellomia et al. (gRISB square up/down hysteresis) — verify against the
  gem companion (Giuli et al., arXiv:2603.20559) for the right
  gGA-hysteresis citation; ties to our gem up/down arms.
- Potthoff, EPJB 32, 429 (2003) + Potthoff–Aichhorn–Dahnken, PRL 91,
  206402 (2003) — self-energy-functional theory / VCA: stationarity of
  the exact Ω[Σ] on a reference-system manifold, no fit metric. Cite
  as the family relative of our restricted-manifold stationarity
  (§0c); the contrast (Σ-space vs density-matrix matching as the
  restriction language) is a framing sentence for the introduction.
- Pelz–Adler–Reitner–Toschi, arXiv:2303.01914 — inside the coexistence
  region the two branches differ SHARPLY at the two-particle level (the
  number of charge-channel vertex-divergence lines JUMPS across the
  MIT, insulator side higher; lines accumulate as T → 0). Two uses:
  (1) independent evidence that the coexisting branches are not smoothly
  connected objects — consonant with our no-fold finding being a
  statement about the representation, not the physics; (2) an honest
  scope line: vertex divergences are a dynamical two-particle
  phenomenon, invisible to any static equal-time closure by
  construction — the same blindness class as the gap-closing
  instability (§2.4(d)).

**Ecosystem practice note (TRIQS sweep, 2026-07-22):** the standard
tutorial stack (IPT on Bethe, cthyb Hubbard) scans U with a FRESH seed
per point and never draws the hysteresis — coexistence work in that
ecosystem lives in papers, with three tools: seeded up/down
continuation (our protocol), critical slowing down of the DMFT loop as
the practical spinodal detector (iteration multiplier → 1 = KLR soft
mode = the J_FP eigenvalue of §2.4(d); Joo–Oudovenko made a convergence
criterion of it, Strand a continuation method), and only rarely a free
energy (hard in QMC). Consequences for us: our both-branch Ω machinery
(U*, conjugacy, Clausius–Clapeyron) is a differentiator worth stating;
and the field's own U_c1/U_c2 practice is seeded-continuation
"solution disappears" boundaries — the same acceptance-vs-existence
caveat we formalized, which the three-symbol discipline handles.

**Reading core while the data cooks (5 sessions → 5 paper sections):**
Georges lectures §1.1 + 4.2–4.4 (intro language); GKKR §VII.C–E (§3.2);
Bulla §III–IV (warm rules + spectra); Strand (branch/spinodal methods
paragraphs); Lanatà 2017 (§1 + §3.3 ladder).

## 4. Benchmarks section (what may be said, with sources)

- LLK reproduction layer: our ED reimplementation reproduces their Fig. 3
  convergence pattern (docc/E converge by N_b=3–5; Z slowest) [BN §3].
  ED's pre-critical N_b=3 bump in docc/E_kin/Z cancels in E_tot
  (E_tot = E_kin + U·docc; component errors ±0.04 opposite-sign, total
  +0.003) — observed cancellation, not a variational theorem [S, user's
  agent]. The paper text never explains that bump; ours can, in one line.
- B=1: both ghost frameworks are the BR/Gutzwiller metal (no Σ pole in
  gem; docc agree 4e-4; the failure directions vs DMFT are opposite to
  ED N_b=1's too-insulating collapse [LLK Fig. 2; S]).
- NRG: docc agreement at 1e-3 where clean [bench]; the M_g=1 U=3.2 docc
  "agreement" 1e-5 is a curve crossing, not convergence [S].
- gem junk policy: sumR2 ≤ 1.1 cut, warm-row exclusions, up-arm only for
  the metal [BN §2; compare.py].
- gem's U=2.8/T=0.001 up-arm row (Z jumps to 0.132): arm crossing —
  exclude until checked [S].

## 5. Two-site / NCS — the consolidation document's installment and ours

His Mott+ document provides the derivation layer the user was asked for
[Mott+]: inclusion–exclusion functional (weights −3/+4 at z=4), gateway
twins per sector, **matching = per-ghost-family equal-time correlator
equalities** (occupation + hybridization; 17=17 at M_h=2, 21=21 at M_h=4)
— i.e. C1 "matching conditions as expectation-value equalities" exists;
our job is the audit/rederivation in the draft's language, not invention.
Established there + verified by us:

- **One G; shared h-set; Σ = Σ₁ = Σ₂** (split-vs-shared closures agree to
  5–6 digits; the shared frame is principle, removing 4·M_h moment rows)
  [Mott+ §2, RB flag 7; ncs_min.py implements it; HF stationarity 1e-8].
- **R₀ = Z on the whole half-filled Fermi surface** (magnetic zone
  boundary) ⇒ nodal–antinodal differentiation symmetry-forbidden at n=1
  [Mott+ Prop 3].
- The insulator is an **embedded valence bond**: local h-poles → ω=0 at
  finite weight (e₁→0, the same Mott pole as single-site), bond channel
  open (B_g²/|ε_b| ≈ 0.8–1.1), environment-exchange discriminator B_g 0.33
  (metal) vs ≤0.02 (ins); physical frame: lattice-self-consistent
  two-impurity Kondo competition (Kondo-screened vs RKKY singlet)
  [Mott+ §7.4]. Contrast with single site (V₀→0, ±V₁ alive): **two
  different pole anatomies of a Mott insulator — the section's payoff.**
- Wedge numbers, our exact re-evaluation where they differ: U*(0.03) =
  **5.09** (his 5.15; his Ω program's ±700 clip breaks the deep-pole
  cancellation), U_c2(e1²) = 4.96–5.06, metal end 5.40, ΔD = 0.021
  [RB 4d]. Rung 4a PASS (quote the surviving CSV numbers, not the verdict
  prose); rung 4b 6/8 rows (two hopped family in the final pass — mark
  excluded) [RB corrections 07-12]. **U_c1 OPEN** — his own freed-bounds
  check shows the pinned descent was a frustrated genuine V₂→0 root;
  needs the freed-bounds descent rerun [RB flag 7].
- High-T diagnostic layer (T raw 0.26–0.50): reverse-oriented Ω zero —
  never call it U*(T); scheme physics; claim only with [CL] wording.
- His closure theory (support rule, pair-ghost uniqueness, envelope bound
  ⇒ no Fermi arcs at pair level, d-wave cross ghost as the forced repair)
  is the outlook section; unaudited by us — cite as his, flag audit status.
- Remaining compute for the paper: **the U*(T) line across the wedge**
  (T = 0.01–0.045) with the unclipped Ω evaluator; optional M_g=2
  paired-bath control [RB 4e; Mott+ next-steps].

Out of scope for this paper: doping (and everything
arc/pseudogap beyond the outlook paragraph).

## 6. Session corrections (so this file self-heals)

- 2026-07-22 (night): the eigenvalue block first attributed the
  λ₋ = V₀η/(√2W) expansion and the finite-mode contrast to exact DMFT
  — user caught it: the expansion and the figure are ghost-DMFT-
  internal, and "exact DMFT keeps V₀ finite" is false at T = 0 (clean
  gap ⇒ Δ(0) = 0 there too; the exact instability is gap-edge
  ω-structure). Rewritten same night; the corrected contrast is
  "lives in unmatched variables", not "small vs zero".
- 2026-07-22 (evening): the pole-flight interpretation was UPGRADED by
  the box-scaling test (§2.4(d) test 4): "the demand leaves the
  representable region / no solution exists below U_flight" was too
  strong — no FINITE root exists, but the finite-box residual ramp was
  approximation error (∝ 1/ε), the minimizing sequence converges to a
  boundary object (renormalizer bath at mixing c* ≈ 0.40), and the
  predicted hard termination of the compactified branch at the
  weight-law zero U = D was tested and refuted (2W² saturates ≈ 0.05
  below it, probed to U = 0.85, ε ≤ 200). No-fold, no-scheme-U_c1, and
  the three-symbol discipline all stand; U_flight is now the
  finite-root → boundary crossover.
- 2026-07-22: §2.2b's first draft conflated the ISOMETRY deficit
  (1 − ΣR² = linear term, ≤3%) with the FIRST-MOMENT deficit of gem's
  Σ-pole weights (28–51%) — "three names for one number" was wrong.
  Two deficits, one cause (no bookkeeping), OPPOSITE U-trends
  (measured cold: metal ΣR² 0.9967 → 0.9713 while moment capture
  0.490 → 0.723; insulator ΣR² 0.976–0.992 with absolute deficit
  0.52 → 0.43). Corrected same day; the decomposition is now the
  content of 2.2b and the insulator bullet there.
- 2026-07-21: budget dictionary corrected — Σ poles are M_h (=2 always in
  the single-site set), NOT M_g; earlier "M_g=3 is the minimal Σ topology"
  wording was wrong. The Mott transition is bought by the *bath* satellites
  (insulating bath configuration), while the ω=0 Mott pole lives in the
  h-sector at both budgets.
- Much of the closure comparison was already documented in [BN §4b] and
  [PCN] (linear-term identity, structure table, sum-rule audit, unitarity);
  this session's genuinely new items: the U²/4-normalized flat 89–90%
  metal Σ-weight + insulator 0.90→0.94 approach [S]; ΔZ(U) shape and
  T-independence [S]; the registered-data U*/U_c2/corridor table [S]; the
  v2-canonical diagnosis below [S]; the `_parse_arr` bug [S].
- **D09/v2 bethe m_g=3 canonical-native cell**: metal arms (up AND down)
  carry live satellites at T=0.2 (V1≈1.1; Z/docc match v1 bare to 4–5
  decimals) and are satellite-dead for ALL T ≤ 0.15 (V1 ≤ 0.02; h-sector in
  renormalizer configuration W~2–9 at η~12–17; Z = m_g=1 values; BR death
  3.4) — the documented g-matching degeneracy: a chain never revives a dead
  channel [RB R2 finding (b)]. The insulator arm is live and gauge-pairs
  with v1 bare at 1e-5→2.6e-7. Consequences: the atlas ΔΩ "crossing" from
  that cell (~2.1 cold) was a cross-budget artifact. RESOLVED 2026-07-22:
  the fill campaign supplied bethe_mg3_bare (refit rows per root) and a
  protected R-native re-solve seeded from bare roots — the new native
  metal is LIVE at every cold row; only the reproducible T = 0.07/0.1
  window stays satellite-dead (both gauges, both campaigns — documented
  finding, growth-point protocol fix deferred). Routing now points at the
  merged D09 0.2.0; the old dead chains remain in the table as history
  and are superseded-per-key in derived chains.

## 6b. Poles at the position cap: kept, explained, and the real fix (2026-07-22)

Policy change (user directive): capped poles are never discarded. Figures
now KEEP them, plotted at the cap with × markers and the legend "at
position cap (slope representation)"; filled markers mean the position is
genuinely determined. Plain-words explanation that goes wherever the
figure goes: a far pole enters the equations only through V₁²/ε₁, so when
the equations do not need a position, the coordinate rests at its cap —
that is a representation, like a gauge choice, not a failed fit. The
physics is the slope invariant, plotted in its own panel. (The R gauge
does NOT cure this: it compactifies only the h-sector; the g-sector
satellite is bare in both routes — documented in
symmetric_continuation_R.)

The real fix is a solver-protocol decision (added to
asks): either (a) the renormalizer move applied to the g-sector — FREEZE
ε₁ at the declared universal cap and fit the slope directly (his own
M_h=4 h-sector construction; floors scale as 1/ε₁², his proof), making
the representation explicit instead of implicit-by-cap; or (b) add the
Δ-moment matching row that would pin the satellite position physically
(the moment machinery exists — N_MOMENTS / gateway_plus_impfill_moments)
— at the cost of changing the condition counting. Until decided, the
figures' ×-at-cap treatment is the honest display.

## 7. Open asks and next actions

1. Exact Z(U/D) anchor (NRG or CTQMC curve, Bethe, cold). Blocks §2.3's
   headline. One email.
2. Mott+ TeX/PDF final package + late-campaign programs [RB flag 8].
3. NCS U_c1: freed-bounds descent rerun (or his own).
4. Confirm gem = draft ref [13] [RB flag 4].
5. Lanatà U_c1 ≈ 2.0 pin + BCV exact U_c1 pin (the three-ends taxonomy).
6. Us, still open: wedge U*(T) line (NCS, the one substantial new run);
   ladder-figure insulator cut
   at the gated end; GUI warning banners + corridor cap (last two
   enforcement items); square m_g=3 SCC resubmit on wall-clock + gem fill
   completion (B=3 running, B=1 + square queued); stability follow-up
   (fixed-point-map Jacobian / KLR mode).
   NEW ask (2026-07-22 evening): the COMPACTIFIED SOLVE — two finite
   bath poles + an explicit ω-linear bath coefficient (renormalizer) as
   a free parameter, replacing the runaway pair below the crossover;
   makes the boundary branch regular, answers whether W → 0 in the true
   limit, and is the correct implementation of the external
   compactified-variables protocol. Related smaller ask: re-emit the
   registered insul-down satellite positions with a wider box or mark
   them valley-soft (ε ≈ 14–20 equal-residual at box 240) — positions
   were mildly cap-squeezed branch-wide; invariants unaffected.
   RESOLVED same day: the V0 reconciliation (now §2.4(e) — the law is
   V₀ = 0.455·√Z·D, the plateau was the basin=other tail).
   DONE since first written: `_parse_arr` + gem overlays; v2-native repair
   (fill campaign); single source 0.2.0 + routing; campaign dedup;
   pole-cap keep-and-mark; M_g=2 control; U_c1 forensics; pole-flight
   signature run + fig_story_poleflight + three-symbol nomenclature
   (U_flight / U_c1^gGA / U_c1^DMFT) + J_FP stability formulation
   (2026-07-22, external critique adopted where it survived testing —
   its "controlled invariant" expectation measured FALSE, which
   sharpened the diagnosis to a noncompact endpoint).
