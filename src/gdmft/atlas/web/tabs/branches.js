/* Branches: Z(U) and Ω(U) for the metal/insulator pair at fixed T, with
   continuity breaks, the U* crossing, and the spinodal-proxy readout. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;
  var C = Atlas.colors;

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
      supplementarySource: false,
    };
    Atlas.store.applyPrimaryRoute(state);
    return state;
  }

  /* Derived h-sector scales: ±Λ (solid) and ±η (dashed) for both
     branches on one energy axis, with the atomic ±U/2 cone. Interlacing
     −Λ < −η < 0 < +η < +Λ holds point by point; the insulator's η → 0
     (the ω=0 Mott pole) while its Λ rides toward the atomic ±U/2. */
  function ladderPanel(ds, metal, insul, vlines) {
    var series = [];
    function add(branch, color, name) {
      if (!branch) return;
      [
        ["p_lam", false, "±Λ"],
        ["p_eta", true, "±η"],
      ].forEach(function (spec) {
        [1, -1].forEach(function (sign) {
          var points = [];
          branch.rows.forEach(function (row, position) {
            var value = ds.num(spec[0], row);
            points.push([
              ds.u(row),
              value === null ? null : sign * value,
            ]);
            if (branch.breaks.indexOf(position) >= 0) points.push(null);
          });
          series.push({
            label: name + " " + spec[2],
            color: color,
            /* filled dots for lam, open dots for eta - coincident
               branches stay mutually visible */
            marker: spec[1] ? "opoint" : "point",
            points: points,
            skipLegend: sign < 0,
          });
        });
      });
    }
    add(metal, C.metal, "metal");
    add(insul, C.insul, "insulator");
    var uValues = [];
    [metal, insul].forEach(function (branch) {
      if (branch) {
        branch.rows.forEach(function (row) {
          uValues.push(ds.u(row));
        });
      }
    });
    if (uValues.length) {
      var lo = Math.min.apply(null, uValues);
      var hi = Math.max.apply(null, uValues);
      [1, -1].forEach(function (sign) {
        series.push({
          label: "atomic ±U/2",
          color: C.exotic,
          dash: true,
          marker: "none",
          points: [
            [lo, (sign * lo) / 2],
            [hi, (sign * hi) / 2],
          ],
          skipLegend: sign < 0,
        });
      });
    }
    return {
      yLabel: "derived h-sector scales /D",
      height: 280,
      vlines: vlines,
      hlines: [{ y: 0 }],
      series: series,
    };
  }

  /* Associated pole weights behind the h-sector scales: V0 (central
     g-sector hybridization coupling) is the metal's lifeline — it
     collapses toward 0 as the quasiparticle peak dies near Uc2, so this
     panel is where you watch V0 die under the same U/D as the ±Λ/±η
     ladder above. V1 is the satellite coupling; W is the Σ-pole weight
     that feeds Λ. Branch color matches the ladder; one marker per
     coupling. All amplitudes are non-negative (≥ 0), so a single
     positive axis with the 0 line suffices. */
  function weightsPanel(ds, metal, insul, vlines) {
    var series = [];
    var specs = [
      ["p_v0", "point", "V0"],
      ["p_v1", "opoint", "V1"],
      ["p_w", "square", "W"],
    ];
    function add(branch, color, name) {
      if (!branch) return;
      specs.forEach(function (spec) {
        var points = [];
        branch.rows.forEach(function (row, position) {
          points.push([ds.u(row), ds.num(spec[0], row)]);
          if (branch.breaks.indexOf(position) >= 0) points.push(null);
        });
        series.push({
          label: name + " " + spec[2],
          color: color,
          marker: spec[1],
          points: points,
        });
      });
    }
    add(metal, C.metal, "metal");
    add(insul, C.insul, "insulator");
    return {
      yLabel: "pole weights (V0, V1, W) /D",
      height: 230,
      vlines: vlines,
      hlines: [{ y: 0 }],
      series: series,
    };
  }

  function branchSeries(ds, branch, qtyKey, color, label, marks) {
    var points = [];
    branch.rows.forEach(function (row, position) {
      points.push([ds.u(row), ds.num(qtyKey, row)]);
      if (branch.breaks.indexOf(position) >= 0) points.push(null);
    });
    return {
      label: label,
      color: color,
      marker: "point",
      points: points,
    };
  }

  Atlas.registerTab("branches", "Branches", function (view) {
    var state = Atlas.state.branches || (Atlas.state.branches = defaults());
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
    var it = nearestIndex(grid.t, state.t);
    var t = grid.t[it];

    var ui = Atlas.ui;
    function rerender() {
      Atlas.saveState("branches");
      Atlas.tabs
        .filter(function (tab) {
          return tab.id === "branches";
        })[0]
        .render(view);
    }
    function set(key, cast) {
      return function (value) {
        state[key] = cast ? cast(value) : value;
        if (
          !state.supplementarySource &&
          (key === "lattice" || key === "mg" || key === "supplementarySource")
        ) {
          Atlas.store.applyPrimaryRoute(state);
        }
        rerender();
      };
    }
    view.innerHTML = "";

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
    /* live readout while dragging; full redraw on release (a redraw
       mid-drag would destroy the slider under the pointer) */
    slider.addEventListener("input", function () {
      state.t = grid.t[Number(slider.value)];
      readout.textContent = "T/D = " + Atlas.fmt(state.t);
      renderChart(); /* live while dragging */
    });
    slider.addEventListener("change", function () {
      Atlas.saveState("branches");
    });

    var latticeValues = state.supplementarySource
      ? ds.dictOf("lattice")
      : Atlas.store.primaryLattices();
    var mgValues = state.supplementarySource
      ? ds.mgValues()
      : Atlas.store.primaryMgValues(state.lattice);
    var controls = [
        ui.field(
          "lattice",
          ui.select(
            latticeValues.map(function (value) {
              return { value: value, label: value };
            }),
            state.lattice,
            set("lattice")
          )
        ),
        ui.field(
          "m_g",
          ui.select(
            mgValues.map(function (value) {
              return { value: value, label: String(value) };
            }),
            state.mg,
            set("mg", Number)
          )
        ),
        sliderWrap,
        ui.check(
          "show supplementary sources",
          !!state.supplementarySource,
          set("supplementarySource")
        ),
    ];
    if (state.supplementarySource) {
      controls.splice(
        2,
        0,
        ui.field(
          "evidence dataset",
          ui.select(
            Atlas.store.pointIds().map(function (id) {
              return { value: id, label: Atlas.store.dsLabel(id) };
            }),
            state.ds,
            set("ds")
          )
        ),
        ui.field(
          "gauge route",
          ui.select(
            ds.dictOf("gauge").map(function (value) {
              return { value: value, label: value };
            }),
            state.gauge,
            set("gauge")
          )
        )
      );
    }
    view.appendChild(ui.row(controls));
    var activeRoute = Atlas.store.primaryRoute(
      state.lattice,
      Number(state.mg)
    );
    if (activeRoute) {
      E(
        "p",
        "muted ds-note",
        (state.supplementarySource
          ? "Supplementary source: "
          : "Automatic primary source: ") +
          Atlas.store.dsLabel(state.ds) + " · " + state.gauge + " · " +
          (state.supplementarySource
            ? "not the automatic route unless it matches the catalog"
            : activeRoute.quadrature),
        view
      );
    }

    var chartHost = E("div", null, null, view);
    function renderChart() {
    chartHost.innerHTML = "";
    var it = nearestIndex(grid.t, state.t);
    var t = grid.t[it];

    var metal = Atlas.store.branch(
      state.ds,
      state.lattice,
      Number(state.mg),
      state.gauge,
      t,
      "metal"
    );
    var insul = Atlas.store.branch(
      state.ds,
      state.lattice,
      Number(state.mg),
      state.gauge,
      t,
      "insul"
    );
    var ustarEntry = null;
    Atlas.store
      .ustarFor(state.ds, state.lattice, Number(state.mg), state.gauge)
      .forEach(function (entry) {
        if (Math.abs(entry.t - t) < 1e-12) ustarEntry = entry;
      });
    var spinodal = null;
    Atlas.DATA.derived.spinodals.forEach(function (entry) {
      if (
        entry.ds === state.ds &&
        entry.lattice === state.lattice &&
        entry.m_g === Number(state.mg) &&
        entry.gauge === state.gauge &&
        Math.abs(entry.t - t) < 1e-12
      ) {
        spinodal = entry;
      }
    });

    var diag = E("div", "panel", null, chartHost);
    E("h2", null, "Diagnostics at T/D = " + Atlas.fmt(t), diag);
    var parts = [];
    if (ustarEntry) {
      parts.push(
        "U*: " +
          (ustarEntry.ustar !== undefined
            ? Atlas.fmt(ustarEntry.ustar)
            : "—") +
          " (" +
          ustarEntry.status +
          ", " +
          ustarEntry.n_overlap +
          " overlap points)"
      );
    } else {
      parts.push("U*: no metal/insulator pair at this T");
    }
    if (spinodal) {
      if (spinodal.uc2 !== undefined) {
        parts.push(
          "metal edge Uc2 ≈ " +
            Atlas.fmt(spinodal.uc2) +
            " (" +
            spinodal.uc2_kind +
            ")"
        );
      }
      if (spinodal.uc1 !== undefined) {
        parts.push(
          "insulator support edge Uc1 ≈ " +
            Atlas.fmt(spinodal.uc1) +
            " (" +
            spinodal.uc1_kind +
            ")"
        );
      }
    }
    E("p", null, parts.join(" · "), diag);
    E(
      "p",
      "muted",
      "Support edges are where the recorded branch ends — diagnostics on " +
        "selection-free data, not certified spinodals.",
      diag
    );

    if (!metal && !insul) {
      E("p", "muted panel", "No converged branches at this slice.", chartHost);
      return;
    }
    var vlines = [];
    if (ustarEntry && ustarEntry.ustar !== undefined) {
      vlines.push({ x: ustarEntry.ustar, label: "U*" });
    }
    function panelFor(qtyKey, yLabel) {
      var series = [];
      if (metal) {
        series.push(
          branchSeries(ds, metal, qtyKey, C.metal, "metal · " + yLabel)
        );
      }
      if (insul) {
        series.push(
          branchSeries(ds, insul, qtyKey, C.insul, "insulator · " + yLabel)
        );
      }
      return {
        yLabel: yLabel,
        height: 230,
        vlines: vlines,
        series: series,
      };
    }
    var panel = E("div", "panel", null, chartHost);
    var panels = [
      panelFor("z_pole", "Z"),
      panelFor("omega_d", "Ω/D"),
      ladderPanel(ds, metal, insul, vlines),
    ];
    /* Only when the source carries an embedded pole table — otherwise the
       couplings are all null and the panel would draw empty. */
    if (ds.has("p_v0")) {
      panels.push(weightsPanel(ds, metal, insul, vlines));
    }
    var figure = Atlas.plot.figure({
      width: 940,
      xLabel: "U/D",
      panels: panels,
    });
    panel.appendChild(figure.el);
    var actions = E("div", "chart-actions", null, panel);
    actions.appendChild(
      ui.btn("download SVG", function () {
        figure.svgs.forEach(function (svg, index) {
          Atlas.plot.dlSVG(svg, "branches_panel" + (index + 1));
        });
      })
    );
    actions.appendChild(
      ui.btn("download PNG", function () {
        figure.svgs.forEach(function (svg, index) {
          Atlas.plot.dlPNG(svg, "branches_panel" + (index + 1));
        });
      })
    );
    }
    renderChart();
  });
})();
