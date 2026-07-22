# Results draft — skeleton with numbers pre-placed

Expand top to bottom. Every number here is verified (source: paper-story.md,
same section names). Where it says YOUR VOICE, write 2–3 sentences in your
own words — that's the only work. No data checking. No GUI. No reading.

---

## Opening (paste as-is, done)

All three methods approach the same object — the DMFT fixed point — through
a finite-dimensional representation, and differ in what they make finite and
in how the finite parameters are fixed. DMFT-ED truncates the hybridization
function to N_b bath poles fitted on the Matsubara axis; the impurity is
then solved exactly, and its self-energy carries emergent, uncontrolled pole
content. Ghost-GA enlarges the Hilbert space by B ghost orbitals and
determines a static quasiparticle Hamiltonian variationally; the single knob
simultaneously sets the bath, the quasiparticle space, and the self-energy
resolution (B−1 poles), and the construction coincides with DMFT under the
isometric condition R†R = 1. Ghost-DMFT makes both dynamical objects finite
and independent — M_h poles for Σ, M_g for Δ — and fixes them by
stationarity of the exact DMFT functional restricted to this manifold: the
matching conditions are equalities of equal-time density matrices, every
converged root is an exact stationary point at finite budgets, and the
representation becomes complete as M_h, M_g → ∞. The question of this paper
is then quantitative: what does each budget buy, and what does each closure
cost?

## 1. Budgets (expand: 1 short paragraph + the counting table)

STUB: All single-site calculations use M_h = 2; the bath budget M_g = 1, 3
is the axis. Two correspondence axes with gGA: bath-side M_g ↔ B (docc/
energies agree to 4e-4 at matched budget), spectral-side M_h+1 ↔ B.
[YOUR VOICE: one sentence on why independent budgets matter — the M_h=4
renormalizer at M_g=1, the M_g=2 control.]

## 2. Two closures, one manifold (expand: 2 paragraphs + 2 tables)

STUB: Both frameworks' Σ at matched budget is one mirrored pole pair; the
closures spend it differently. Ours holds the pole weight at a flat
89.1–89.7% (Bethe) / 83.7–87.2% (square) of the exact first moment U²/4
along the entire metal branch; gem spends 49→72%, placing poles closer in,
with the remainder in a linear-in-ω term equal to 1 − 1/ΣR² at every U —
the isometry deficit made spectroscopically visible. Our canonical frame is
unitary: ΣR̃² = 1 identically, R₀² = Z to 9e-16, interlacing with zero
violations on 1932 roots; G integrates to 1 by construction.
Scoreboard at U/D = 2.4 (exact E = −0.0621(1)): gGA −0.0618, ours −0.0610,
ED(5) −0.0605, ED(3) −0.0577. docc: all within 1e-3 of NRG. Z: all above
the anchors; no exact Z(U) reference exists.
[YOUR VOICE: the "representational debt" sentence — every finite method
owes somewhere: gem at m0(G), ours at m2(G), ED in Δ.]

## 3. What the budgets buy (expand: 2 paragraphs + phase-diagram figure)

STUB M_g=1: single PH bath level pins at ε_F, decouples — no insulating
bath configuration exists; Brinkman–Rice metal only, exact-T=0 collapse
bracketed (3.39, 3.40) vs 32/3π = 3.3953.
STUB M_g=3: satellites at Hubbard energies hold the gap; two gated
branches, Ω crossing. Table: U*(T) 2.757→2.492 and U_c2 2.816→2.500 over
T = 0.001→0.010; corridors Bethe (0.010, 0.015), square (0.004, 0.005);
two-code agreement ≤ 0.1–0.5%; square U* ~4% lower.
[YOUR VOICE: one sentence — the insulator is V0 → 0 with satellites alive;
total channel death is junk the protocol rejects.]

## 3b. Thermodynamics of the line (expand: 1 paragraph)

STUB: d(ΔΩ)/dU = ΔD to 0.1% across the coexistence window;
Clausius–Clapeyron closes to ~4%; ΔS = 0.63 at the coldest row → ln 2 —
the insulator carries the local-moment entropy; the line leans left
(electronic Pomeranchuk).
[YOUR VOICE: one sentence of physics — heating favors the moment carrier.]

## 4. The ladder (expand around fig_lambda_frame)

STUB: Z = (η/Λ)² exactly; metal dies by its Σ-pole descending onto its own
quasiparticle (η 0.96→0.24, Λ ~flat), jumping at the fold with η finite;
insulator has η = 0 exactly (Σ ≈ 2W²/ω — the Mott gap in Σ language) with
weight U²/4 − ⟨ε²⟩ (measured deficit 0.21–0.24 vs band variance 0.25, both
lattices) → the dressed Mott pole, a beyond-Hubbard-I statement only a
finite-pole Σ exposes. λ₋ ≈ V₀η/(√2W) is the KLR soft mode (sharpen_KLR
tracks 2λ₋).
[YOUR VOICE: the moving-house sentence — the electron doesn't vanish at
the transition; it relocates from the Fermi surface to ±U/2 with the
ledger balanced.]

## 5. Bond / NCS (expand: 2 paragraphs, from Mott+ + our reruns)

STUB: One G, shared h-set, Σ = Σ₁ = Σ₂ (split-vs-shared verified 5–6
digits); R₀ = Z on the whole half-filled Fermi surface. The bond insulator
is an embedded valence bond: hybridization alive, e₁ → 0, bond channel
B_g 0.33 → ≤0.02 — a second, anatomically different way to build a Mott
insulator out of poles. T=0.03: U_c2(e₁²) = 4.96–5.06, metal end 5.40,
U* = 5.09 (unclipped Ω; the document's 5.15 corrected). U_c1 open pending
the freed-bounds descent.
[YOUR VOICE: one sentence contrasting the two insulators.]

## Do-not-write list (keep beside you)

No raw satellite positions (invariants only). No V0 claims. No
"closer-than-gGA in Z". No U_c1 numbers. No warm-T Z comparisons. Nothing
from the fill campaign.
