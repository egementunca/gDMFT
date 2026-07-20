from __future__ import annotations

from pathlib import Path

from gdmft.atlas.build import REQUIRED_MODULES, WEB_MODULES

ROOT = Path(__file__).parents[1]
WEB = ROOT / "src/gdmft/atlas/web"


def _text(path: str) -> str:
    return (WEB / path).read_text(encoding="utf-8")


def test_public_build_requires_every_declared_browser_module() -> None:
    assert REQUIRED_MODULES == set(WEB_MODULES)
    assert "tabs/references.js" in WEB_MODULES
    assert all((WEB / path).is_file() for path in WEB_MODULES)


def test_default_solution_view_is_status_not_phase_claim() -> None:
    atlas = _text("tabs/atlas.js")
    assert 'view: "status"' in atlas
    assert "ustar: false" in atlas
    assert "candidate branch overlap (provisional)" in atlas
    assert "Provisional branch-overlap diagnostic only" in atlas


def test_reference_temperature_and_budget_semantics_are_explicit() -> None:
    benchmark = _text("tabs/bench.js")
    references = _text("tabs/references.js")
    series = _text("tabs/series.js")
    assert "M_g, gem B, and ED N_b are distinct" in benchmark
    assert "m_g = B = Nb" not in benchmark
    assert "beta_fit=200 is the bath-fit grid" in benchmark
    assert "beta_fit=200 is a bath-fit grid" in series
    assert "ground-state DMFT-ED" in references
    assert "not a physical T/D=0.005" in references
    assert "bath ε_l and V_l" in references


def test_ed_z_and_dual_h_sector_guardrails_are_present() -> None:
    store = _text("store.js")
    inspect = _text("tabs/inspect.js")
    spectra = _text("spectra.js")
    assert "Z_estimator_converged" in store
    assert "accepted fixed points alone are not a Z-quality statement" in store
    assert "self-energy h sector" in inspect
    assert "different lattice and gateway h-sectors" in inspect
    assert "six-significant-" in inspect
    assert "gateway_red" in spectra
    assert "hSectorsDiffer" in spectra
    assert "function populatedKey" in inspect
    assert "moveToPopulatedKey(state, 0.001, 2.0)" in inspect


def test_mobile_and_gauge_contracts_are_not_regressed() -> None:
    css = _text("style.css")
    gauge = _text("tabs/gauge.js")
    assert "@media (max-width: 720px)" in css
    assert ".spectra-grid { grid-template-columns: minmax(0, 1fr); }" in css
    assert 'marker: "only"' in gauge
    assert "zeroConvert" in gauge


def test_normal_views_route_sources_automatically() -> None:
    store = _text("store.js")
    assert "applyPrimaryRoute" in store
    assert "No primary source route for " in store
    assert '? "D08"' in store
    assert '? "D09"' in store

    for path in (
        "tabs/atlas.js",
        "tabs/branches.js",
        "tabs/inspect.js",
        "tabs/tables.js",
    ):
        source = _text(path)
        assert "supplementarySource" in source
        assert "show supplementary sources" in source
        assert "Automatic primary source:" in source

    series = _text("tabs/series.js")
    assert "supplementarySources" in series
    assert "show supplementary sources" in series
    assert "state.list.forEach(Atlas.store.applyPrimaryRoute)" in series
    assert '"evidence dataset"' in series


def test_plot_hover_markers_and_zoom_are_discoverable() -> None:
    plot = _text("plot.js")
    css = _text("style.css")
    bench = _text("tabs/bench.js")
    series = _text("tabs/series.js")

    assert "var allX = allXPositions(panel);" in plot
    assert 'panel.yLabel + " · " + spec.xLabel' in plot
    assert "rows.slice(0, 8)" in plot
    assert "entry.series.tipLabel || entry.series.label" in plot
    assert '"− Zoom out"' in plot
    assert '"↺ Reset zoom"' in plot
    assert "zoomHistory.push(domain.slice())" in plot
    assert "zoomTools.hidden" in plot
    assert "var pad = (hi - lo) * 0.025;" in plot
    assert "return [lo / 1.05, hi * 1.05];" in plot
    assert "svgs.length = 0" in plot
    assert "pointercancel" in plot
    assert "drawSeriesMarker" in plot
    assert "series.connect !== false" in plot
    assert ".viz-zoom-tools" in css
    assert ".viz-zoom-tools[hidden]" in css
    assert ".viz-marker-key" in css

    assert 'marker: "circle"' in bench
    assert 'marker: "diamond"' in bench
    assert 'marker: "odiamond"' in bench
    assert '"osquare" : "square"' in bench
    assert bench.count("connect: false") >= 5
    assert "state.x !== \"t\"" in series
    assert "They are not connected" in series


def test_ed_bath_poles_have_central_and_padded_full_views() -> None:
    plot = _text("plot.js")
    references = _text("tabs/references.js")

    assert "Array.isArray(figSpec.xDomain)" in plot
    assert "Central-mode window" in references
    assert "Full bath span" in references
    assert "All satellite modes are excluded from this view only" in references
    assert "horizontal range has 8% side padding" in references
    assert "var centralOursModes = modesNearestZero(oursModes)" in references
    assert "centralEdModes.concat(centralOursModes)" in references
    assert "symmetricPaddedDomain(centralModes, 0.15)" in references
    assert "symmetricPaddedDomain(edModes.concat(oursModes), 0.08)" in references
    assert "points: modePoints(edModes)" in references
    assert "The selector contains exact shared U/D values only" in references


def test_series_exposes_lossless_ed_bath_parameter_comparisons() -> None:
    store = _text("store.js")
    series = _text("tabs/series.js")

    assert "edBathPoints: function" in store
    assert "value = Math.abs(couplings[0])" in store
    assert "value = Math.abs(couplings[1])" in store
    assert "value = Math.abs(eps[1])" in store
    assert "return sum + coupling * coupling" in store
    assert "direction: row[idx.direction]" in store
    assert "bathQuality: row[idx.bath_approximation_quality]" in store

    assert '"g bath: ghost vs ED"' in series
    assert "Atlas.store.edBathPoints" in series
    assert "point.direction === null || point.direction === direction" in series
    assert 'direction === "down" ? "otriangle" : "triangle"' in series
    assert 'direction === "down" ? "osquare" : "square"' in series
    assert "is undefined rather than zero" in series
    assert '"square ED table has no eps/V arrays"' in series
