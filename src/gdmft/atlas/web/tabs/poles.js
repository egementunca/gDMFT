/* Poles: the analytic-structure map. Pole positions on the energy axis
   (0 = central g-sector coupling V0, ±ε1 = g-sector satellites V1, ±η =
   Σ-poles W) versus U/D at a fixed T, each pole COLORED by its weight and
   flagged with an × once its weight drops below a settable threshold — so a
   coupling's death (V0 → 0 at the Mott edge) is visible directly. Branch is
   a free choice: metal, insulator, or both stacked. Never forced together. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;

  /* Pole family → marker shape (color stays free for weight). V0 sits at a
     structurally fixed position (0), so its location is always meaningful;
     the satellite ε1 and Σ-pole η are FIT, so their position is only
     defined while the pole carries weight. */
  var FAMILIES = [
    { key: "v0", posKey: null, wKey: "p_v0",
      shape: "dot", family: "V0 (central)", fixed: true },
    { key: "v1", posKey: "p_eps1", wKey: "p_v1",
      shape: "diamond", family: "V1 (satellite)" },
    { key: "w", posKey: "p_eta", wKey: "p_w",
      shape: "square", family: "W (Σ-pole)" },
  ];


  function nearestIndex(values, target) {
    var best = 0;
    for (var i = 1; i < values.length; i++) {
      if (Math.abs(values[i] - target) < Math.abs(values[best] - target)) {
        best = i;
      }
    }
    return best;
  }

  function defaults() {
    var state = {
      ds: null,
      lattice: "bethe",
      mg: 3,
      gauge: "bare",
      t: 0.01,
      branch: "metal",
      threshold: 1e-3,
      logColor: true,
      hideNull: true,
      show: { v0: true, v1: true, w: true },
    };
    Atlas.store.applyPrimaryRoute(state);
    return state;
  }

  /* One marker per pole per U row: central at 0, satellites/Σ-poles at ±pos.
     Weights are the stored coupling amplitudes (units of D). */
  function markersFor(ds, branch, branchLabel, show, hideNull, threshold) {
    var markers = [];
    var hidden = 0;
    if (!branch) return { markers: markers, hidden: hidden };
    branch.rows.forEach(function (row) {
      var u = ds.u(row);
      FAMILIES.forEach(function (f) {
        if (show && show[f.key] === false) return;
        var w = ds.num(f.wKey, row);
        if (w === null) return;
        if (f.posKey === null) {
          markers.push({
            u: u, pos: 0, weight: w, shape: f.shape,
            family: f.family, branch: branchLabel,
          });
          return;
        }
        /* fit pole: below the weight threshold its residue is too small to
           pin a position, so the location is noise — drop it rather than
           scatter a fake point. V0 (fixed at 0) is never dropped: it shows
           its death in place as an ×. */
        if (hideNull && w < threshold) {
          hidden += 2;
          return;
        }
        var pos = ds.num(f.posKey, row);
        if (pos === null) return;
        [1, -1].forEach(function (sign) {
          markers.push({
            u: u, pos: sign * pos, weight: w, shape: f.shape,
            family: f.family, branch: branchLabel,
          });
        });
      });
    });
    return { markers: markers, hidden: hidden };
  }

  /* Cell-global axis domains: min/max over EVERY T slice of the cell (all
     pole families, no weight threshold), so sliding T never rescales the
     axes — pole motion is visible as motion, not as an axis jump. Cached
     per (dataset, lattice, mg, gauge, branch-mode). */
  var domainCache = {};

  function cellDomains(ds, state, grid, kinds) {
    var key = [state.ds, state.lattice, state.mg, state.gauge,
               kinds.join("+")].join("|");
    if (domainCache[key]) return domainCache[key];
    var uLo = Infinity, uHi = -Infinity;
    var yLo = Infinity, yHi = -Infinity;
    grid.t.forEach(function (tv) {
      kinds.forEach(function (kind) {
        var branch = Atlas.store.branch(
          state.ds, state.lattice, Number(state.mg), state.gauge, tv, kind);
        markersFor(ds, branch, kind, null, false, 0).markers
          .forEach(function (m) {
            if (m.u < uLo) uLo = m.u;
            if (m.u > uHi) uHi = m.u;
            if (m.pos < yLo) yLo = m.pos;
            if (m.pos > yHi) yHi = m.pos;
          });
      });
    });
    var out = null;
    if (isFinite(uLo) && isFinite(yLo)) {
      var padU = (uHi - uLo) * 0.03 || 0.1;
      var padY = (yHi - yLo) * 0.08 || 0.1;
      out = { u: [uLo - padU, uHi + padU], y: [yLo - padY, yHi + padY] };
    }
    domainCache[key] = out;
    return out;
  }

  function numberField(labelText, value, onChange) {
    var input = document.createElement("input");
    input.type = "number";
    input.step = "any";
    input.min = "0";
    input.value = String(value);
    input.style.width = "7.5em";
    input.addEventListener("change", function () {
      var parsed = parseFloat(input.value);
      if (isFinite(parsed) && parsed >= 0) onChange(parsed);
    });
    return Atlas.ui.field(labelText, input);
  }

  Atlas.registerTab("poles", "Poles", function (view) {
    var state = Atlas.state.poles || (Atlas.state.poles = defaults());
    if (!state.show) state.show = { v0: true, v1: true, w: true };
    if (state.hideNull === undefined) state.hideNull = true;
    if (!state.supplementarySource) Atlas.store.applyPrimaryRoute(state);
    var ds = Atlas.store.ds(state.ds);
    if (!ds.grids[state.lattice]) state.lattice = ds.dictOf("lattice")[0];
    if (ds.mgValues().indexOf(Number(state.mg)) < 0) {
      state.mg = ds.mgValues()[0];
    }
    if (ds.dictOf("gauge").indexOf(state.gauge) < 0) {
      state.gauge = ds.dictOf("gauge")[0];
    }
    var grid = ds.grids[state.lattice];

    var ui = Atlas.ui;
    function rerender() {
      Atlas.saveState("poles");
      Atlas.tabs
        .filter(function (tab) { return tab.id === "poles"; })[0]
        .render(view);
    }
    function set(key, cast) {
      return function (value) {
        state[key] = cast ? cast(value) : value;
        if (key === "lattice" || key === "mg") {
          Atlas.store.applyPrimaryRoute(state);
        }
        rerender();
      };
    }
    view.innerHTML = "";

    if (!ds.has("p_v0")) {
      E("p", "muted panel",
        "This source carries no embedded pole table, so pole positions and " +
        "weights are unavailable here.", view);
      return;
    }

    var it = nearestIndex(grid.t, state.t);
    var t = grid.t[it];
    /* Restored state can point at a T that has no rows for this cell
       (e.g. the m_g=1 exotic T ~ 1e-8 slice): clamp to the nearest
       populated slice instead of opening on an empty chart. */
    function sliceHasRows(tv) {
      return ["metal", "insul"].some(function (kind) {
        var branch = Atlas.store.branch(
          state.ds, state.lattice, Number(state.mg), state.gauge, tv, kind);
        return branch && branch.rows.length > 0;
      });
    }
    if (!sliceHasRows(t)) {
      var candidates = grid.t
        .map(function (tv, i) { return { tv: tv, i: i }; })
        .filter(function (c) { return sliceHasRows(c.tv); })
        .sort(function (a, b) {
          return Math.abs(a.tv - t) - Math.abs(b.tv - t);
        });
      if (candidates.length) {
        it = candidates[0].i;
        t = grid.t[it];
        state.t = t;
      }
    }
    var slider = document.createElement("input");
    slider.type = "range";
    slider.min = 0;
    slider.max = grid.t.length - 1;
    slider.value = it;
    var sliderWrap = E("div", "field slider-field");
    E("span", "field-label", "step T/D", sliderWrap);
    var inner = E("div", "slider-inner", null, sliderWrap);
    inner.appendChild(slider);
    var readout = E("span", "slider-readout", "T/D = " + Atlas.fmt(t), inner);
    slider.addEventListener("input", function () {
      state.t = grid.t[Number(slider.value)];
      readout.textContent = "T/D = " + Atlas.fmt(state.t);
      renderChart();
    });
    slider.addEventListener("change", function () {
      Atlas.saveState("poles");
    });

    var latticeValues = Atlas.store.primaryLattices();
    var mgValues = Atlas.store.primaryMgValues(state.lattice);
    view.appendChild(
      ui.row([
        ui.field("lattice", ui.select(
          latticeValues.map(function (v) { return { value: v, label: v }; }),
          state.lattice, set("lattice"))),
        ui.field("m_g", ui.select(
          mgValues.map(function (v) {
            return { value: v, label: String(v) };
          }), state.mg, set("mg", Number))),
        ui.field("branch", ui.select([
          { value: "metal", label: "metal" },
          { value: "insul", label: "insulator" },
          { value: "both", label: "both (stacked)" },
        ], state.branch, set("branch"))),
        sliderWrap,
        numberField("weight threshold", state.threshold, function (v) {
          state.threshold = v;
          rerender();
        }),
        ui.check("log color scale", !!state.logColor, set("logColor")),
        ui.check("hide sub-threshold satellites", !!state.hideNull,
          set("hideNull")),
      ])
    );

    /* Family toggles: hide the far-out ±ε1 satellites to let the axis
       auto-zoom onto the near-0 V0/W band where V0 actually dies. */
    function showToggle(key, labelText) {
      return ui.check(labelText, state.show[key] !== false, function (on) {
        state.show[key] = on;
        rerender();
      });
    }
    view.appendChild(
      ui.row([
        E("span", "field-label", "show poles:"),
        showToggle("v0", "● V0 central"),
        showToggle("v1", "◆ V1 satellite"),
        showToggle("w", "■ W Σ-pole"),
      ])
    );

    var activeRoute = Atlas.store.primaryRoute(state.lattice, Number(state.mg));
    if (activeRoute) {
      E("p", "muted ds-note",
        "Automatic primary source: " + Atlas.store.dsLabel(state.ds) + " · " +
        state.gauge + " · " + activeRoute.quadrature, view);
    }
    E("p", "muted",
      "Position = pole energy /D (0 central, ±ε1 g-sector satellites, ±η " +
      "Σ-poles); color = pole weight; × marks weight below the threshold. " +
      "Hover any pole for its exact weight.", view);

    var shapeLegend = [
      { shape: "dot", label: "V0 (central coupling)" },
      { shape: "diamond", label: "V1 (satellite coupling)" },
      { shape: "square", label: "W (Σ-pole weight)" },
    ];

    var chartHost = E("div", null, null, view);
    function renderChart() {
      chartHost.innerHTML = "";
      var it2 = nearestIndex(grid.t, state.t);
      var t2 = grid.t[it2];
      var kinds = state.branch === "both"
        ? ["metal", "insul"]
        : [state.branch];
      var dom = cellDomains(ds, state, grid, kinds);
      var vlines = [];
      Atlas.store
        .ustarFor(state.ds, state.lattice, Number(state.mg), state.gauge)
        .forEach(function (entry) {
          if (Math.abs(entry.t - t2) < 1e-12 && entry.ustar !== undefined) {
            vlines.push({ x: entry.ustar, label: "U*" });
          }
        });

      var anyDrawn = false;
      var figures = [];
      kinds.forEach(function (kind) {
        var label = kind === "insul" ? "insulator" : "metal";
        var branch = Atlas.store.branch(
          state.ds, state.lattice, Number(state.mg), state.gauge, t2, kind);
        var built = markersFor(ds, branch, label, state.show,
          state.hideNull, Number(state.threshold));
        var markers = built.markers;
        var panel = E("div", "panel", null, chartHost);
        E("h2", null,
          label + " · pole map at T/D = " + Atlas.fmt(t2), panel);
        if (!markers.length) {
          E("p", "muted", "No pole-bearing " + label +
            " points at this slice.", panel);
          return;
        }
        anyDrawn = true;
        if (built.hidden) {
          E("p", "muted",
            built.hidden + " satellite/Σ poles hidden (weight below the " +
            "threshold, position undetermined). Uncheck “hide sub-threshold " +
            "satellites” to show them.", panel);
        }
        var fig = Atlas.plot.poleMap({
          width: 940,
          height: state.branch === "both" ? 320 : 440,
          t: t2,
          uDomain: dom ? dom.u : undefined,
          yDomain: dom ? dom.y : undefined,
          xLabel: "U/D",
          yLabel: "pole position /D",
          threshold: Number(state.threshold),
          logColor: !!state.logColor,
          markers: markers,
          vlines: vlines,
          shapeLegend: shapeLegend,
        });
        panel.appendChild(fig.el);
        figures.push(fig);
        var actions = E("div", "chart-actions", null, panel);
        actions.appendChild(ui.btn("download SVG", function () {
          fig.svgs.forEach(function (svg, i) {
            Atlas.plot.dlSVG(svg, "poles_" + label + (i + 1));
          });
        }));
        actions.appendChild(ui.btn("download PNG", function () {
          fig.svgs.forEach(function (svg, i) {
            Atlas.plot.dlPNG(svg, "poles_" + label + (i + 1));
          });
        }));
      });
      if (!anyDrawn && kinds.length) {
        E("p", "muted panel",
          "No converged pole data for this selection.", chartHost);
      }
    }
    renderChart();
  });
})();
