# What these four figures show (plain words)

Words used below:
- U* = the interaction value where metal and insulator have equal free
  energy. Below U* the metal wins, above it the insulator wins.
- Uc2 = the largest U where a metal solution still exists at all.
- corridor = the temperature band where the first-order transition ends.
  Above it there is no jump anymore, just a smooth change (crossover).

## fig_story_phase — the transition line

What was done: at each temperature we ran the metal solution up in U and
the insulator solution down in U, kept both, and found where their free
energies cross. That crossing is U* (solid line). The dashed line is where
the metal solution stops existing (Uc2). The shaded band is the corridor.
Both lattices are on the plot.

What it says: the transition is first order at low temperature: two
solutions coexist between the lines, and the winner switches at U*. The
square lattice has its transition at slightly smaller U and its corridor
at lower temperature than Bethe.

Trust: our U*(T) numbers agree with the independent reference
implementation, rerun fresh, to better than 0.1% at every temperature.

Source papers: Georges, Kotliar, Krauth, Rozenberg, Rev. Mod. Phys. 68,
13 (1996), Sec. VII (the standard picture of Uc1, Uc2, U*). Bulla, Costi,
Vollhardt, PRB 64, 045103 (2001) for the same construction with NRG.

## fig_story_pomeranchuk — why the line leans left

What was done: the entropy difference between insulator and metal,
measured two independent ways from our own free energies: (left) the
temperature derivative of the free-energy difference at fixed U; (right)
the same quantity obtained instead from the slope of the U* line
(Clausius–Clapeyron relation), compared with the direct measurement.

What it says: the insulator has MORE entropy than the metal — about
0.63 per site at our coldest points, heading toward ln 2 = 0.693, which
is the entropy of a free spin. So heating helps the insulator, which is
why the U* line tilts to smaller U as T grows. The two curves on the
right agreeing (within a few percent) means our free energies are
internally consistent — the line is real thermodynamics, not solver noise.

Source papers: Georges et al. RMP 1996, Sec. VII.D (entropy of the
insulator, shape of the line); Georges lecture notes cond-mat/0403123,
Sec. 4.4. The helium analogy (heating can freeze) is the Pomeranchuk
effect.

## fig_story_mottpole — what the Mott gap is made of

What was done: in the insulator our self-energy has a pole exactly at
zero energy. That pole IS the Mott gap: it pushes all spectral weight
away from the Fermi level. For an isolated atom its weight would be
exactly U^2/4. We plot how much weight is MISSING compared to U^2/4,
along the whole insulating branch, for both lattices, and the same
quantity for gem (the variational ghost method).

What it says: the missing weight is almost exactly the mean square of
the band energies (0.25 in our units) — the same number on both lattices.
In plain terms: hopping eats a fixed bite out of the atomic pole. The
simplest approximation (Hubbard-I) predicts no bite at all. gem loses
about twice the bite, and its loss shrinks with U while ours does not —
the two methods dress the same pole differently. This is a statement
about the Mott insulator you can only make when the self-energy is
written as poles.

Source papers: Lanata, Lee, Yao, Dobrosavljevic, "Emergent Bloch
Excitations in Mott Matter" (2017) — their Eq. (12) is the insulating
pole self-energy; the U^2/4 atomic value is standard (GKKR RMP 1996,
atomic limit).

## fig_story_closures — where the two methods really differ

What was done: both our method and gem write the metal self-energy as
one pair of poles. Left panel: the total weight those poles carry,
divided by the exact value U^2/4. Right panel: the position of the pole.
Metal branch, coldest temperature.

What it says: we keep the weight at about 90% of exact, flat in U (85%
on square); gem starts near 50% and climbs. gem also always puts its
pole closer to zero energy. Same pole structure, different fitting rule —
we impose matching of averages, gem minimizes an energy. Every visible
disagreement between the methods (for example in Z) traces back to
these two panels.

Source papers: Lee, Lanata, Kotliar, PRB 107, L121104 (2023) — the
framework comparison at matched bath size; Lanata et al. 2017 for the
ghost construction.

## fig_story_poleflight — how the insulator branch ends (and how it doesn't)

What was done: we followed the insulating solution down in U at the
coldest temperature, with the usual limits on the bath parameters
removed (raised from 5 and 12 to 24), and at every step recorded the
bath satellite's coupling and position, their combinations V1^2/eps_g
and V1/eps_g, the size of the matching-equation error, and the
smallest singular value of its Jacobian. The last quantity is the direct test for a
spinodal: if the branch died by meeting its unstable partner (a fold),
that number would go to zero.

What it says: it never goes to zero. The equations do not become
singular anywhere — instead, below U/D between 1.125 and 1.100, no
finite set of bath parameters solves them anymore. The coupling and the
position run to whatever limit we allow, the error grows smoothly, and
even the combination V1^2/eps_g — the part of a far satellite that
still acts on low energies, the number that stays meaningful when
positions saturate — grows without bound. In plain words: the insulator
is built on the self-energy pole at zero frequency, whose measured
weight is U^2/4 minus the band's mean square energy; that budget runs
out at U = D (dotted line). Below it the equations still ask for an
insulator but there is nothing left to build one from, and the bath
tries to fake it with infinite coupling at infinite energy. The mixing
ratio V1/eps_g (third panel) makes the approach visible: about 0.1
deep in the insulator — a weakly admixed high-energy level, the
textbook perturbative satellite — it climbs to 0.56 at the last
solution and heads toward V1 = eps_g along the escape. The satellite
stops being a far, weak level before the branch ends. The branch
end is the representation running out of material, not a phase becoming
unstable. For this reason we never call this endpoint Uc1: the exact
insulator dies much earlier (near U/D = 2.4) by a different mechanism —
the gap closes — which equal-time matching data cannot see.

Trust: filled symbols are stored, independently re-checked solutions;
open symbols are the descent past the last finite solution — there the
stationary point retreats to infinite satellite energy at fixed
V1/eps_g, and the plotted error is the finite-box approximation error
(it falls as the box grows; the run shown uses the box 24). The error level of the filled symbols (a few 1e-5) is
re-evaluation noise on stored roots, not a solver limitation. Source
data with full provenance: studies/paper_figures/data/.

Source papers: Georges, Kotliar, Krauth, Rozenberg, RMP 68, 13 (1996),
Sec. VII for Uc1/Uc2; Strand, PRB 83, 205136 (2011) for what a genuine
DMFT fold looks like; Kotliar, Lange, Rozenberg, PRL 84, 5180 (2000)
for the soft mode that would signal one.

## fig_story_budget_controls — what the budget scans say about Uc1

What was done: the insulating solution was followed down in U at the
coldest temperature with three different resource budgets — the
standard bath (m_g = 3, with its limits raised to 240 so nothing is
squeezed), a doubled bath (m_g = 5, one extra symmetric pair), and a
doubled self-energy (m_h = 4) — plus one run of the split-duty bath
(a physical pair near the Hubbard band together with an explicit
omega-linear channel).

What it says, panel by panel: (a) the Mott-pole weight follows the
same dressed law at every budget, with a small finite-temperature
offset that runs out exactly at the crossover marked U_x — and shows
no feature at all near U/D = 2.0 or 2.4, where the variational and
exact insulators die. (b) The satellite position leaves its finite
valley at the same U_x for both bath budgets: adding poles does not
move the endpoint. (c) The matching error stays at solver quality
straight through the exact death region — the closure carries no
death mechanism there, which is why no scheme Uc1 is quoted. (d) What
the insulator increasingly wants as U falls is the omega-linear
channel share, heading for the value the runaway converges to.

Trust: every curve is a fresh descent from stored campaign roots with
the commands in the data-file headers; the m_g = 3 and split-duty
tables are transcribed from the session runs verbatim.

Source papers: Georges-Kotliar-Krauth-Rozenberg RMP 68, 13 (1996) for
Uc1; Lanata et al. PRB 96, 195126 (2017) for the variational endpoint;
Liebsch-Ishida, JPCM 24, 053201 (2012) for bath-size convergence
discipline.
