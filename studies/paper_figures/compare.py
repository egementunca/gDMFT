"""Shared helpers for the cross-method comparison figures.

The three frameworks compared are ghost-DMFT ("ours"), gGA ("gem" g-RISB),
and DMFT-ED (LLK). The paper thesis (April 28 draft): ghost-DMFT is an exact
parametrization of DMFT for a finite pole count, so it should sit closer to
exact DMFT-ED than gGA does, and → exact as M_g grows.

Data sources:
  - Bethe cross-method: references-benchmarks-v1/compare_all.csv (the only
    table where ghost + gGA + DMFT-ED coexist), via common.compare_rows().
    DMFT-ED is T=0 only; ghost & gGA share the T grid 0.001-0.2.
  - Square: ghost-vs-gGA only (no DMFT-ED). Ghost from our v2 scan
    (common), gGA from the raw gem scan (references-gem-gga-v1/points.csv),
    merged on the fly here.

Encoding convention (all comparison figures): color = method; temperature =
a lighter (cold) → fuller (warm) shade of that method color (figstyle.shade)
with markers+lines; DMFT-ED drawn as T=0 marker anchors.
"""

from __future__ import annotations

import ast
import csv
import math
import os
from functools import cache

import common
import figstyle as fs  # noqa: F401  (imported first so the backend is set)
import numpy as np
from gdmft.atlas import catalog
from gdmft.atlas.dos import square_dos_table
from matplotlib.lines import Line2D

COMPARE_OUT = common.OUT / "comparison"
GEM_DIR = common.DATA / "references-gem-gga-v1"

# --------------------------------------------------------------------------
# gauge / source routing (see docs/atlas.md, src/gdmft/atlas/catalog.py)
# --------------------------------------------------------------------------
# The registered datasets overlap on purpose and carry several gauges per
# cell: `bare` (PRIMARY_PHYSICS), `canonical-r-converted` (an EXACT bare→R
# copy — identical observables, excluded), and `canonical-r-native` /
# `canonical-r-reoptimized` (INDEPENDENT R solves — genuinely *different*
# fixed points, kept as gauge evidence). Every raw-point figure routes its
# (dataset, gauge) through the catalog policy so the choice is auditable, not
# hardcoded. Override the preferred gauge for a whole run with the env var
# GDMFT_FIG_GAUGE (or by setting compare.GAUGE before build()); default None
# means the policy's primary-physics gauge (bare).
#
# NB: the Bethe *scalar* figures read the benchmark merge (compare_all.csv),
# which carries only the bare-route ghost-DMFT rows, so the override changes
# the parameter/function/V0 figures (which read raw points) but not those.
_DS_KEY = {catalog.D08_DATASET_ID: "v1", catalog.D09_DATASET_ID: "v2"}
GAUGE = os.environ.get("GDMFT_FIG_GAUGE") or None


def route(lattice: str, m_g) -> dict:
    """Resolve (dataset key, gauge) for a cell via the catalog policy,
    honouring the GAUGE override."""
    entry = catalog.primary_route(lattice, int(m_g))
    return {
        "ds": _DS_KEY[entry.dataset_id],
        "gauge": GAUGE or entry.gauge,
        "default_gauge": entry.gauge,
        "dataset_id": entry.dataset_id,
        "reason": entry.reason,
    }


def route_flag(lattice: str, m_g) -> str:
    """One-line provenance stamp for a figure caption."""
    r = route(lattice, m_g)
    tag = ("primary-physics" if r["gauge"] == r["default_gauge"]
           else f"OVERRIDE of default '{r['default_gauge']}'")
    return (f"source: {lattice} $M_g$={m_g}, '{r['gauge']}' gauge — {tag} "
            f"({catalog.CATALOG_POLICY_VERSION}); canonical-R native/"
            f"reoptimized are separate solutions, not shown")

# Representative temperatures (cold → warm). Selection snaps to the nearest
# available T per (lattice, m_g); gem Bethe rows at/above 0.05 are qualitative.
T_TARGETS = (0.001, 0.005, 0.01, 0.02, 0.05)
GEM_QUALITATIVE_T = 0.05

# gem junk cut: the captured spectral weight sum-rule detector (same 1.1 gate
# fig_benchmark_compare uses).
SUMR2_MAX = 1.1

# Box edges where fit-pole positions pile up under the solver's position
# constraint (from the bound-limited-data audit): satellite eps1 and the
# high-T metal Sigma-pole eta. Poles within tol of an edge have an
# undetermined position and are filtered from the parameter/V0 figures.
# A fit pole is treated as bound-limited (position untrustworthy) once it
# reaches within ~5% of the box edge, not only exactly on it — in bethe
# m_g=3 the satellite parks in a band just below 12, carrying real weight.
EPS1_BOX = {"bethe": 12.0, "square": 6.0}
ETA_BOX = 8.0
BOX_MARGIN = 0.95  # fraction of the box edge above which a pole is "pinned"
ETA_PIN = 7.5

OBS_LABEL = {
    "docc": r"$\langle n_\uparrow n_\downarrow\rangle$",
    "z": r"$Z$",
    "ekin": r"$E_{\rm kin}/D$",
    "etot": r"$E_{\rm tot}/D$",
    "epot": r"$E_{\rm pot}/D$",
}

# marker per method so overlaid temperatures stay separable in mono/EPS
METHOD_MARKER = {"ghost_dmft": "o", "gga_gem": "s", "dmft_ed": "D"}


def outdir(lattice: str):
    # A non-default gauge lands in its own subfolder so an override run never
    # overwrites the primary (bare) figures.
    base = COMPARE_OUT / lattice
    return base / f"gauge-{GAUGE}" if GAUGE else base


# --------------------------------------------------------------------------
# shared legends (placed INSIDE the canvas so they show in the interactive
# viewer too, not only in tight-bbox saved files)
# --------------------------------------------------------------------------
def method_key(fig, methods, y: float = 0.075, extra=None):
    handles = [
        Line2D([], [], color=fs.FRAMEWORK_COLOR[m],
               marker=METHOD_MARKER.get(m, "o"),
               mfc=("none" if m == "dmft_ed" else fs.FRAMEWORK_COLOR[m]),
               label=fs.FRAMEWORK_NAME[m])
        for m in methods
    ]
    if extra:
        handles += list(extra)
    leg = fig.legend(handles=handles, loc="lower center", ncol=len(handles),
                     fontsize=8, bbox_to_anchor=(0.5, y))
    fig.add_artist(leg)
    return leg


def temperature_key(fig, temps, y: float = 0.015, base: str = "#111111",
                    title="temperature shade (lighter = colder)"):
    handles = [
        Line2D([], [], color=fs.shade(base, t, temps), lw=3,
               label=rf"$T/D={t:g}$")
        for t in temps
    ]
    return fig.legend(handles=handles, loc="lower center",
                      ncol=max(1, len(handles)), fontsize=7.0,
                      bbox_to_anchor=(0.5, y), title=title, title_fontsize=7.0)


def gauge_caption(fig, lattice, m_g, y: float = 0.004):
    """Stamp the resolved gauge/source route at the very bottom of a figure.

    These figures read raw points, so the gauge IS applied here."""
    fig.text(0.5, y, route_flag(lattice, m_g), ha="center", fontsize=6.0,
             color=("#c0392b" if GAUGE else "0.45"))


def benchmark_note(fig, y: float = 0.004):
    """Stamp for the Bethe scalar figures, which read the bare-route
    benchmark merge and therefore IGNORE the gauge override."""
    if GAUGE:
        fig.text(0.5, y, f"gauge override '{GAUGE}' is IGNORED here — Bethe "
                 "scalars come from the bare-route benchmark table "
                 "(compare_all.csv)", ha="center", fontsize=6.2,
                 color="#c0392b")
    else:
        fig.text(0.5, y, "source: ghost/gGA/ED scalars from "
                 "references-benchmarks-v1 (bare-route ghost-DMFT)",
                 ha="center", fontsize=6.0, color="0.45")


# --------------------------------------------------------------------------
# temperature selection
# --------------------------------------------------------------------------
def select_temperatures(available, targets=T_TARGETS):
    """Snap the target temperatures onto the available grid (dedup, sorted)."""
    picked: list[float] = []
    for target in targets:
        if not available:
            break
        near = min(available, key=lambda t: abs(t - target))
        if near not in picked and abs(near - target) <= 0.4 * target + 1e-9:
            picked.append(near)
    return sorted(picked)


def bethe_temperatures(m_g: int):
    ts = set()
    for row in common.compare_rows():
        if (
            row["method"] == "ghost_dmft"
            and row["budget"] == m_g
            and row["branch"] == "metal"
        ):
            ts.add(row["t"])
    return sorted(ts)


def square_temperatures(m_g: int):
    """Temperatures present in BOTH our square scan and the gem square scan."""
    r = route("square", m_g)
    gem = {
        round(row["t"], 6)
        for row in gem_rows()
        if row["lattice"] == "square" and row["budget"] == m_g
    }
    ours = {
        round(t, 6)
        for t in common.branch_temperatures(
            r["ds"], "square", m_g, r["gauge"], "metal")
    }
    return sorted(gem & ours)


# --------------------------------------------------------------------------
# raw gem scan (references-gem-gga-v1)
# --------------------------------------------------------------------------
def _parse_arr(text):
    """gem stores pole arrays SEMICOLON-separated ('-0.6718;0.6717'); the
    original literal_eval parser silently returned None on that format and
    the gGA overlays were empty. Accept both formats."""
    if text in (None, "", "null"):
        return None
    if ";" in text:
        try:
            return [float(x) for x in text.split(";") if x.strip()]
        except ValueError:
            return None
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return None
    if isinstance(value, (list, tuple)):
        return [float(x) for x in value]
    return [float(value)]


def _gem_sigma_pole(pos_text, w_text):
    """Outer Sigma-pole (|eta|, residue) for the gem overlay, or (None, None)."""
    pos = _parse_arr(pos_text)
    wgt = _parse_arr(w_text)
    if not pos or not wgt or len(pos) != len(wgt):
        return None, None
    idx = max(range(len(pos)), key=lambda k: abs(pos[k]))
    return abs(pos[idx]), wgt[idx]


@cache
def gem_rows():
    out = []
    with (GEM_DIR / "points.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            if row["converged"] != "true" or row["crashed"] == "true":
                continue
            eta, w_res = _gem_sigma_pole(
                row["self_energy_pole_positions"],
                row["self_energy_pole_weights"],
            )
            out.append(
                {
                    "lattice": row["lattice"],
                    "budget": int(row["bath_budget"]),
                    "u": float(row["u_over_d"]),
                    "t": float(row["t_over_d"]),
                    "dir": row["direction"],
                    "docc": common.fnum(row["double_occupancy"]),
                    "z": common.fnum(row["quasiparticle_weight_slope"]),
                    "ekin": common.fnum(row["kinetic_energy_over_d"]),
                    "etot": common.fnum(row["total_energy_over_d"]),
                    "sumr2": common.fnum(row["sum_r_squared"]),
                    "sig_eta": eta,
                    "sig_w_res": w_res,
                    "sig_pos": _parse_arr(row["self_energy_pole_positions"]),
                    "sig_wgt": _parse_arr(row["self_energy_pole_weights"]),
                }
            )
    return tuple(out)


# --------------------------------------------------------------------------
# observable series per (lattice, m_g, temperature)
# --------------------------------------------------------------------------
def _epot(u, docc):
    return None if docc is None else u * docc


def _sorted_first(pairs):
    seen: dict[float, float] = {}
    for u, y in pairs:
        if y is not None:
            seen.setdefault(u, y)
    us = sorted(seen)
    return us, [seen[u] for u in us]


def bethe_series(method: str, m_g: int, t, obs: str, branch: str):
    """(us, ys) from compare_all.csv. For dmft_ed, t is ignored (T=0)."""
    pairs = []
    for row in common.compare_rows():
        if row["method"] != method or row["budget"] != m_g:
            continue
        if row["branch"] != branch:
            continue
        if method != "dmft_ed" and not math.isclose(row["t"], t, rel_tol=1e-6):
            continue
        if (
            method == "gga_gem"
            and row["sumr2"] is not None
            and row["sumr2"] > SUMR2_MAX
        ):
            continue
        y = _epot(row["u"], row["docc"]) if obs == "epot" else row[obs]
        pairs.append((row["u"], y))
    return _sorted_first(pairs)


_GHOST_COL = {
    "docc": "double_occupancy",
    "z": "quasiparticle_weight_pole",
    "ekin": "kinetic_energy_over_d",
    "etot": "total_energy_over_d",
}


def square_ghost_series(m_g: int, t, obs: str, kind: str):
    r = route("square", m_g)

    def value(row, _index):
        if obs == "epot":
            return _epot(
                float(row["u_over_d"]), common.fnum(row["double_occupancy"])
            )
        return common.fnum(row[_GHOST_COL[obs]])

    return common.branch_series(
        r["ds"], "square", m_g, r["gauge"], t, kind, value)


def square_gem_series(m_g: int, t, obs: str, direction: str):
    pairs = []
    for row in gem_rows():
        if row["lattice"] != "square" or row["budget"] != m_g:
            continue
        if not math.isclose(row["t"], t, rel_tol=1e-6, abs_tol=1e-9):
            continue
        if row["dir"] != direction:
            continue
        if row["sumr2"] is not None and row["sumr2"] > SUMR2_MAX:
            continue
        y = _epot(row["u"], row["docc"]) if obs == "epot" else row[obs]
        pairs.append((row["u"], y))
    return _sorted_first(pairs)


# --------------------------------------------------------------------------
# clean metal-branch accessors (used by every comparison figure)
# --------------------------------------------------------------------------
def metal_cutoff(us, zs, rise: float = 0.05):
    """First U where a metal Z-sweep re-enters a spurious high-Z solution.

    A physical metallic Z decreases monotonically toward the Mott
    transition; gGA's "up" sweep re-finds a high-Z branch past it. Returns
    that U (exclusive clip point) or None if the sweep stays physical.
    """
    run = float("inf")
    for u, z in zip(us, zs):
        if z is None:
            continue
        if z <= run:
            run = z
        elif z > run + rise:
            return u
    return None


def ghost_metal_series(lattice: str, m_g: int, t, obs: str):
    if lattice == "bethe":
        return bethe_series("ghost_dmft", m_g, t, obs, "metal")
    return square_ghost_series(m_g, t, obs, "metal")


def gem_metal_series(lattice: str, m_g: int, t, obs: str):
    """gGA "up" (metal) series, spurious high-U metastable tail clipped."""
    if lattice == "bethe":
        uz, zz = bethe_series("gga_gem", m_g, t, "z", "up")

        def getter(o):
            return bethe_series("gga_gem", m_g, t, o, "up")
    else:
        uz, zz = square_gem_series(m_g, t, "z", "up")

        def getter(o):
            return square_gem_series(m_g, t, o, "up")
    cutoff = metal_cutoff(uz, zz)
    us, ys = getter(obs)
    if cutoff is not None:
        keep = [(u, y) for u, y in zip(us, ys) if u < cutoff]
        us = [u for u, _ in keep]
        ys = [y for _, y in keep]
    return us, ys


def ed_series(m_g: int, obs: str):
    """DMFT-ED (Bethe only) at T=0, up sweep."""
    return bethe_series("dmft_ed", m_g, None, obs, "up")


# --------------------------------------------------------------------------
# bound-limited pole filter (from the audit)
# --------------------------------------------------------------------------
def eps1_pinned(params: dict, lattice: str) -> bool:
    """Satellite g-sector position at the parameterization box edge."""
    eps1 = params.get("eps1")
    box = EPS1_BOX.get(lattice)
    return eps1 is not None and box is not None and eps1 >= BOX_MARGIN * box


def eta_pinned(params: dict) -> bool:
    """Σ-pole position pinned at the (high-T) box edge."""
    eta = params.get("eta")
    return eta is not None and eta >= ETA_PIN


def bound_pinned(params: dict, lattice: str) -> bool:
    return eps1_pinned(params, lattice) or eta_pinned(params)


# --------------------------------------------------------------------------
# square-lattice local Green's function (ported from the atlas JS gSquare)
# --------------------------------------------------------------------------
@cache
def _square_dos():
    energies, weights = square_dos_table(512)
    return np.array(energies), np.array(weights)


def g_square(zeta):
    """G_loc(zeta) = sum_k w_k/(zeta - eps_k) over the square DOS (D=1 units)."""
    energies, weights = _square_dos()
    z = np.asarray(zeta)
    return np.sum(weights / (z[..., None] - energies), axis=-1)
