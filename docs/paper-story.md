# Paper story — clean consolidated version

2026-07-21, audited and reconciled 2026-07-22 after the single-source merge
and the U_c1 forensics (every stale claim from the fast-moving sessions was
hunted and fixed in this pass; see §6 for the correction trail). One claim
per line,
each with its evidence source. Sources: [draft] = Static DMFT Draft April 28;
[Mott+] = the professor's 39-page NCS document (dmft root, guide:
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

Branch rules: metal = up assembly, insulator = down; U*/U_c2 drawn only
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
- gGA's R is unnormalized: ΣR² = captured weight ≤ 1 (0.970 at U=2.4 cold).
  Its Σ carries a linear term **sig_lin = 1 − 1/ΣR² exactly** — "the sum
  rule and the linear term are the same fact seen two ways" [BN §4b;
  re-verified per-U to 4 digits [S]]. An exact Σ decays at ∞; the linear
  term is the unitarity deficit made visible. Also a junk detector: gem
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

### 2.3 The honest scoreboard (fixed budget; do not overclaim)

At U/D = 2.4 cold: E_tot — gGA −0.06184, ours −0.06098, ED5 −0.06052,
ED3 −0.05772 vs exact −0.0621(1): gGA best (its home turf), ours second,
ahead of ED at equal and larger bath [S, bench]. Z — everyone above the
anchors (CTQMC β=200: 0.12, itself finite-T-biased per LLK; ED rising to
0.137 at N_b=5): gem 0.169, ours 0.190; gGA closer; no clean exact-Z anchor
exists (NRG rows carry docc/E only) — **one NRG/CTQMC Z(U) curve from the
professor upgrades the whole section**. docc — all methods within 1e-3 of
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
semianalytic target for the professor: derive this constant from the
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

(U² − D²)/4 → 0 at U = D, and the scheme's insulating branch reaches
**U ≈ 1.10–1.15 (Bethe) / ≈ 1.0 (square)** — the dressed Mott-pole
weight's own floor. The ENDING was then audited (forensics below): it is
a pole-flight boundary of the finite-pole parametrization, NOT a
thermodynamic spinodal — the weight law sets WHERE the branch ends, the
runaway is HOW. gem's Mott-pole deficit is roughly TWICE ours (0.52 at
U=3, opposite U-trend), and its cold down-sweep loses the insulator at
U = 2.90 — but that number is gem's iteration-basin artifact, not gGA's
U_c1: Lanatà's published variational endpoint is ≈ 2.0 [their PRB;
pin]. The honest cross-method statement is the three-ends taxonomy
below, which REPLACES an earlier "closures bracket the spinodal" claim.

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
1. **Fold test — negative.** s_min of the residual Jacobian along the
   descent RISES (4.4e-6 → 1.6e-4 over U = 1.6 → 0.95), never → 0: no
   spinodal at 1.125; ‖F‖ drifts smoothly through the 1e-4 gate.
2. **Lifted-box continuation — pole flight, not continuation.** With
   V₁/ε_g boxes raised to 24: V₁ explodes (6.3 → 24), ε_g rails at any
   cap, ‖F‖ climbs off the gate with s_min still ordinary — no nearby
   root exists; the branch ends as a RUNAWAY of the restricted finite-
   pole parametrization, with onset exactly where the dressed-weight law
   (U²−D²)/4 crosses zero at U ≈ D. So: demonstrated end ≈ 1.10–1.15,
   characterized as pole-flight onset at the weight-law floor — not a
   thermodynamic spinodal.
3. **Hessian stability test — structurally uninformative.** ∂²F has two
   negative modes on BOTH branches (metal control: −4.3 at U=2.7): the
   matching functional is a saddle by construction [Mott+ §3], so
   metastable-vs-saddle needs the fixed-point-map Jacobian (Strand) or
   the KLR mode — open follow-up, not achievable in raw parameter space.

**Three different "ends", never to be conflated** (this replaces the
earlier bracketing claim, whose gem-side number was a sweep artifact):
- ≈ 1.10–1.15: matching's stationary root ceases to exist as a finite-
  pole object (pole flight; today's result);
- ≈ 2.0: gGA's VARIATIONAL existence endpoint (Lanatà's published U_c1;
  our local gem down-sweep's 2.90 was its iteration-basin artifact — a
  third kind of end, algorithmic);
- ≈ 2.4: exact DMFT's metastability endpoint (BCV pin pending).
The paper quotes NO scheme U_c1; "converged = true" is never "metastable
phase exists" — today's numbers are that discipline made explicit.

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
gap-closing instability that kills the exact insulator at U_c1, at any
bath budget.** The Aspen question this creates is pointed at the
professor's own construction: his consistency-matched closure (the
Kadanoff–Baym rank-restoring conditions, Mott+ §9) is the natural
candidate for what would reintroduce the insulator's death — the
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

### (e) The gateway scale crossover sits just below the transition

Λ/(U/2) along the cold metal: 2.07 (U=1) → 1.00 at **U = 2.62** → the
gateway's outer scale switches from band-dominated to
interaction-dominated ~5% below U* = 2.757, with the insulator's Λ
approaching U/2 from below. Reported as a measured observation (the
transition happens where the gateway becomes atomic-like), not yet a law.

### Marathon asks distilled from this section
1. Derive the metal's Σ-weight constant (0.89 Bethe / 0.85 square) from
   the M_h=2 matching — the professor's gateway algebra.
2. Derive 2W²_ins = U²/4 − ⟨ε²⟩ + O(1/U) from the deep-Mott expansion.
3. Exact Z(U) anchor (unchanged ask).
4. Pin the literature numbers for the three-ends taxonomy in (d):
   exact U_c1 from BCV Fig. 9, and gGA's variational U_c1 (~2.0) from
   Lanatà PRB 96, 195126.
5. Stability follow-up (open): metastable-vs-saddle needs the
   fixed-point-map Jacobian (Strand) or the KLR mode — raw parameter
   space cannot decide it (§2.4(d) test 3).

## 3. Single site — what each bath budget buys

### 3.1 M_g = 1: the quasiparticle and nothing else [RB R1, SA]

BR metal, continuous collapse; exact-T=0 window brackets the collapse at
U_c/D ∈ (3.39, 3.40) vs analytic 32/3π = 3.3953 [BN §4]. The insulator is
structurally impossible (PH bath level pinned at ε_F decouples; every
descent fails the gate on both lattices — the documented negative result).
Both semianalytic documents agree once translated; cite the professor's
Secs. 12–18/24–25 only (his own Sec. 12 retracts the early purity sections)
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
registered-data derivation [S]. U*(T) is a two-code line (prof's code rerun
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
professor's endpoint detector sharpen_KLR tracks (2λ₋). Figure polish: gate the insulator cut at its gated end (still open);
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
  mode at the endpoint. **The professor's detector is literally named
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

## 5. Two-site / NCS — the professor's installment and ours

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

Out of scope by the professor's own instruction: doping (and everything
arc/pseudogap beyond the outlook paragraph).

## 6. Session corrections (so this file self-heals)

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

The real fix is a solver-protocol decision for the professor (added to
asks): either (a) the renormalizer move applied to the g-sector — FREEZE
ε₁ at the declared universal cap and fit the slope directly (his own
M_h=4 h-sector construction; floors scale as 1/ε₁², his proof), making
the representation explicit instead of implicit-by-cap; or (b) add the
Δ-moment matching row that would pin the satellite position physically
(the moment machinery exists — N_MOMENTS / gateway_plus_impfill_moments)
— at the cost of changing the condition counting. Until decided, the
figures' ×-at-cap treatment is the honest display.

## 7. Asks (professor) and next actions

1. Exact Z(U/D) anchor (NRG or CTQMC curve, Bethe, cold). Blocks §2.3's
   headline. One email.
2. Mott+ TeX/PDF final package + late-campaign programs [RB flag 8].
3. NCS U_c1: freed-bounds descent rerun (or his own).
4. Confirm gem = draft ref [13] [RB flag 4].
5. Lanatà U_c1 ≈ 2.0 pin + BCV exact U_c1 pin (the three-ends taxonomy).
6. Us, still open: wedge U*(T) line (NCS, the one substantial new run);
   V0 reconciliation with the user's own view; ladder-figure insulator cut
   at the gated end; GUI warning banners + corridor cap (last two
   enforcement items); square m_g=3 SCC resubmit on wall-clock + gem fill
   completion (B=3 running, B=1 + square queued); stability follow-up
   (fixed-point-map Jacobian / KLR mode).
   DONE since first written: `_parse_arr` + gem overlays; v2-native repair
   (fill campaign); single source 0.2.0 + routing; campaign dedup;
   pole-cap keep-and-mark; M_g=2 control; U_c1 forensics.
