# Cross-method benchmark references v1

The reference tables behind the paper's benchmark figures, registered so the
figures read only registered data.

`tables/compare_all.csv` (10,936 rows) is the audited tidy merge
(`method, budget, T, U_over_D, branch, Z, docc, ekin, etot, sumR2`) built by
the source repository's `collect_benchmarks.py` on 2026-07-16 (acceptance
report archived under `provenance/ACCEPTANCE.md`). Methods: `ghost_dmft`
(ours, budgets 1/3 — the only registered source of our bethe m_g=3
E_kin/E_tot, evaluated via the lattice-observable route), `gga_gem` (gem
g-RISB B=1/3), `dmft_ed` (LLK protocol, N_b=1/3/5), `gga_prof` (reference implementation's
grids, E_tot already shifted +U/2 to LLK axes), `nrg` (thermal reference at
U/D = 1, 2, 3.2), `ctqmc_llk` (the beta=200 anchor at U/D=2.4).
`compare_vs_T.csv` and `convergence_U2.4.csv` are its two audited slices.

Source-of-truth inputs are registered alongside: `tables/nrg_thermal.csv`
(normalized from the NRG .dat curves), `tables/prof_gga_grids.csv`
(parsed from the .npy grids; `total_energy_raw` is in the eps_loc = -U/2
convention — ADD U/2 for LLK axes), `tables/ctqmc_anchors.csv`, and the
fresh-ruler marker tables used by the phase-diagram figure.

Import-time verification: gem and ghost rows of the merge reproduce the
already-registered gem reference and v1 bare bethe m_g=3 scan at machine
precision, and the gga_prof rows reproduce the .npy grids under the +U/2
convention (which also validates the pure-python .npy parser).
