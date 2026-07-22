#!/usr/bin/env python3
"""Agreement with DMFT-ED, with ED's own bath-convergence as the yardstick.

Top row: docc, Z, E_tot/D vs U at the coldest rows — ghost-DMFT and gGA at
budget M_g, against DMFT-ED N_b=5 (best converged, solid) and N_b=3 (faint,
to expose ED's own bath dependence). Bottom row: residual vs the N_b=5
anchor for ghost, gGA, and — as the reference scale — DMFT-ED N_b=3 itself.

Reading (data, not asserted): docc residuals sit at ~10^-3 and inside ED's
own N_b=3→5 spread, i.e. the methods agree ("same"). Z is strongly bath
limited — ED's Z nearly doubles from N_b=3 to N_b=5 — so the Z residuals are
large for every finite-bath method ("not quite the same"); the honest
statement about approaching exact DMFT is the bath-size convergence figure,
not a single ED reference.
"""

from __future__ import annotations

import compare
import figstyle as fs
import matplotlib.pyplot as plt
import numpy as np

import common  # noqa: F401

OBS = [("docc", compare.OBS_LABEL["docc"]),
       ("z", compare.OBS_LABEL["z"]),
       ("etot", compare.OBS_LABEL["etot"])]
T_COLD = 0.001
XMAX = 2.7  # focus on the metallic window; past this everything is insulating


def _ed(budget, obs):
    return compare.bethe_series("dmft_ed", budget, None, obs, "up")


def _interp_on(u_ref, xs, ys):
    xs = np.asarray(xs, float)
    ys = np.asarray(ys, float)
    u = np.asarray(u_ref, float)
    out = np.interp(u, xs, ys, left=np.nan, right=np.nan)
    out[(u < xs.min()) | (u > xs.max())] = np.nan
    return out


def _figure(m_g):
    anchor_u, anchor_y = _ed(5, "docc")
    if not anchor_u:
        print(f"  (no DMFT-ED N_b=5; skipped residual m_g={m_g})")
        return
    fig, axs = plt.subplots(2, 3, figsize=(7.6, 4.8), sharex=True)
    for col, (obs, label) in enumerate(OBS):
        top, bot = axs[0, col], axs[1, col]
        gu, gy = compare.ghost_metal_series("bethe", m_g, T_COLD, obs)
        qu, qy = compare.gem_metal_series("bethe", m_g, T_COLD, obs)
        e5u, e5y = _ed(5, obs)
        e3u, e3y = _ed(3, obs)
        # matched-budget ED: at budget 1 the fair like-for-like column is
        # N_b = m_g, and it fails in the OPPOSITE direction (too insulating,
        # LLK Fig. 2) - protocol-delicate per their Sec. II.B (1/w_n
        # weighting at N_b=1), so it is context, not the reference.
        emu, emy = (_ed(m_g, obs) if m_g not in (3, 5) else ([], []))
        top.plot(gu, gy, "-o", ms=2.6, lw=1.1,
                 color=fs.FRAMEWORK_COLOR["ghost_dmft"],
                 label=rf"{fs.FRAMEWORK_NAME['ghost_dmft']} $M_g{{=}}{m_g}$")
        top.plot(qu, qy, "-s", ms=2.4, lw=1.0,
                 color=fs.FRAMEWORK_COLOR["gga_gem"],
                 label=rf"{fs.FRAMEWORK_NAME['gga_gem']} $B{{=}}{m_g}$")
        top.plot(e5u, e5y, "D", ms=3.0, mfc="none", mew=1.0,
                 color=fs.FRAMEWORK_COLOR["dmft_ed"],
                 label=r"DMFT-ED $N_b{=}5$")
        top.plot(e3u, e3y, "x", ms=3.0, mew=0.8, alpha=0.6,
                 color=fs.FRAMEWORK_COLOR["dmft_ed"],
                 label=r"DMFT-ED $N_b{=}3$")
        if emu:
            top.plot(emu, emy, "^", ms=3.0, mfc="none", mew=0.8,
                     color="0.35",
                     label=rf"DMFT-ED $N_b{{=}}{m_g}$ (matched budget)")
        top.set_ylabel(label)
        top.grid(alpha=0.25, lw=0.4)

        bot.axhline(0, color="0.6", lw=0.7)
        bot.plot(gu, np.asarray(gy, float) - _interp_on(gu, e5u, e5y), "-o",
                 ms=2.4, lw=1.0, color=fs.FRAMEWORK_COLOR["ghost_dmft"])
        bot.plot(qu, np.asarray(qy, float) - _interp_on(qu, e5u, e5y), "-s",
                 ms=2.2, lw=0.9, color=fs.FRAMEWORK_COLOR["gga_gem"])
        bot.plot(e3u, np.asarray(e3y, float) - _interp_on(e3u, e5u, e5y), "x-",
                 ms=3.0, lw=0.8, alpha=0.7, color=fs.FRAMEWORK_COLOR["dmft_ed"])
        delta = {"docc": r"$\Delta\langle n_\uparrow n_\downarrow\rangle$",
                 "z": r"$\Delta Z$",
                 "etot": r"$\Delta E_{\rm tot}/D$"}[obs]
        bot.set_ylabel(delta + r"  (method $-$ ED$_{N_b=5}$)")
        if emu:
            bot.plot(emu, np.asarray(emy, float) - _interp_on(emu, e5u, e5y),
                     "^-", ms=2.8, lw=0.8, mfc="none", color="0.35")
        bot.set_xlabel(r"$U/D$")
        bot.set_xlim(0.4, XMAX)
        bot.grid(alpha=0.25, lw=0.4)
    axs[0, 0].legend(fontsize=5.8, loc="best")
    ref_note = (r"reference = ED $N_b{=}5$ (proxy for converged DMFT); "
                r"$\times$ = ED's own $N_b{=}3\!\to\!5$ spread = the yardstick")
    if m_g == 1:
        ref_note += r"; $\triangle$ = matched-budget ED (opposite-side failure)"
    fig.suptitle(
        rf"Bethe $M_g={m_g}$ vs DMFT-ED  ({ref_note})", fontsize=8.6,
    )
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    compare.benchmark_note(fig)
    fs.save(fig, f"compare_residual_bethe_mg{m_g}", compare.outdir("bethe"))


def build() -> None:
    for m_g in (1, 3):
        _figure(m_g)


if __name__ == "__main__":
    build()
