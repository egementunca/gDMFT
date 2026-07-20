/* Benchmarks: ghost-DMFT vs gem (gGA) vs finite-bath DMFT-ED at matched
   bath budget, on the LLK axes — plus the pole-structure comparison. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;
  var C = Atlas.colors;

  var QUANTITIES = [
    { key: "docc", label: "double occupancy" },
    { key: "etot_d", label: "E_tot/D" },
    { key: "z_pole", label: "Z" },
  ];

  /* Route each cell to the registered bare population intended for
     comparison. In particular, square m_g=3 must use the continuum v2
     grid, while the complete historical bethe m_g=3 bare scan is in v1. */
  function oursSource(lattice, mg) {
    var candidates = [];
    var catalog = Atlas.DATA.catalog;
    var routes =
      catalog && catalog.policy && Array.isArray(catalog.policy.routes)
        ? catalog.policy.routes
        : [];
    routes.forEach(function (route) {
      if (
        route.lattice === lattice &&
        Number(route.m_g) === Number(mg) &&
        Atlas.DATA.datasets[route.dataset_id]
      ) {
        candidates.push({
          ds: route.dataset_id,
          gauge: route.gauge,
          route: route.route_id,
        });
      }
    });
    var ids = Atlas.store.pointIds().slice();
    ids.sort(function (a, b) {
      function rank(id) {
        var v1 = id.indexOf("gauge-matrix") >= 0;
        if (lattice === "bethe" && mg === 3) return v1 ? 0 : 1;
        return v1 ? 1 : 0;
      }
      return rank(a) - rank(b);
    });
    ids.forEach(function (id) {
      candidates.push({ ds: id, gauge: "bare" });
    });
    ids.forEach(function (id) {
      Atlas.store
        .ds(id)
        .dictOf("gauge")
        .forEach(function (gauge) {
          if (gauge !== "bare") candidates.push({ ds: id, gauge: gauge });
        });
    });
    for (var k = 0; k < candidates.length; k++) {
      var ds = Atlas.store.ds(candidates[k].ds);
      if (!ds.grids[lattice]) continue;
      if (ds.mgValues().indexOf(mg) < 0) continue;
      if (ds.dictOf("gauge").indexOf(candidates[k].gauge) < 0) continue;
      for (var i = 0; i < ds.n; i++) {
        if (
          ds.lattice(i) === lattice &&
          ds.num("m_g", i) === mg &&
          ds.str("gauge", i) === candidates[k].gauge &&
          ds.converged(i) &&
          ["metal-up", "metal-down"].indexOf(ds.str("family", i)) >= 0
        ) {
          return candidates[k];
        }
      }
    }
    return null;
  }

  function shortDs(id) {
    if (id.indexOf("gauge-matrix") >= 0) return "D08 gauge matrix";
    if (id.indexOf("scan-matrix") >= 0) return "D09 scan matrix";
    return id;
  }

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
    return { lattice: "bethe", budget: 3, t: 0.001, diff: false };
  }

  Atlas.registerTab("bench", "Benchmarks", function (view) {
    var state = Atlas.state.bench || (Atlas.state.bench = defaults());
    var ui = Atlas.ui;
    var gem = Atlas.DATA.references.gem;
    view.innerHTML = "";
    if (!gem) {
      E("p", "muted panel", "No gem reference dataset registered.", view);
      return;
    }
    var anchor = Atlas.store.ds(gem.anchored_to);
    if (!anchor.grids[state.lattice]) state.lattice = "bethe";
    var grid = anchor.grids[state.lattice];
    var it = nearestIndex(grid.t, state.t);
    state.t = grid.t[it];

    function rerender() {
      Atlas.saveState("bench");
      Atlas.tabs
        .filter(function (tab) {
          return tab.id === "bench";
        })[0]
        .render(view);
    }
    function set(key, cast) {
      return function (value) {
        state[key] = cast ? cast(value) : value;
        rerender();
      };
    }

    view.appendChild(
      ui.row([
        ui.field(
          "lattice",
          ui.select(
            Object.keys(anchor.grids).map(function (value) {
              return { value: value, label: value };
            }),
            state.lattice,
            set("lattice")
          )
        ),
        ui.field(
          "matched integer budgets",
          ui.select(
            [
              { value: 1, label: "ours M_g 1 · gem B 1 · ED N_b 1" },
              { value: 3, label: "ours M_g 3 · gem B 3 · ED N_b 3" },
            ],
            state.budget,
            set("budget", Number)
          )
        ),
        ui.field(
          "T/D",
          ui.select(
            grid.t.map(function (value) {
              return { value: value, label: Atlas.fmt(value) };
            }),
            state.t,
            set("t", Number)
          )
        ),
        ui.check("difference vs gem (up arm)", state.diff, set("diff")),
      ])
    );
    E(
      "p",
      "muted ds-note",
      "M_g, gem B, and ED N_b are distinct method-specific parameters. " +
        "This control only matches their integer comparison budgets; it " +
        "does not identify their equations or variational spaces.",
      view
    );

    var source = oursSource(state.lattice, Number(state.budget));
    if (!source) {
      E("p", "muted panel", "No converged metal rows for this cell.", view);
      return;
    }
    var ds = Atlas.store.ds(source.ds);
    var oursLabel =
      "ours · " + shortDs(source.ds) + " · " + source.gauge;
    var sourceRows = ds.rowsWhere({
      lattice: state.lattice,
      m_g: Number(state.budget),
      gauge: source.gauge,
    });
    var quadratures = {};
    sourceRows.forEach(function (row) {
      var quadrature = ds.str("quadrature", row);
      if (quadrature) quadratures[quadrature] = true;
    });
    E(
      "p",
      "muted ds-note",
      "Our source: " +
        source.ds +
        " · " +
        source.gauge +
        (source.route ? " · route " + source.route : "") +
        (Object.keys(quadratures).length
          ? " · " + Object.keys(quadratures).sort().join(", ")
          : ""),
      view
    );

    /* our metal branch at this T, per quantity */
    var dsGrid = ds.grids[state.lattice];
    var dsIt = nearestIndex(dsGrid.t, state.t);
    var branch = Atlas.store.branch(
      source.ds,
      state.lattice,
      Number(state.budget),
      source.gauge,
      dsGrid.t[dsIt],
      "metal"
    );
    if (Math.abs(dsGrid.t[dsIt] - state.t) > 1e-12) {
      E(
        "p",
        "muted",
        "note: our nearest T/D is " + Atlas.fmt(dsGrid.t[dsIt]),
        view
      );
    }

    function oursPoints(qtyKey) {
      if (!branch) return [];
      var points = [];
      branch.rows.forEach(function (row, position) {
        points.push([ds.u(row), ds.num(qtyKey, row)]);
        if (branch.breaks.indexOf(position) >= 0) points.push(null);
      });
      return points;
    }
    function gemPoints(qtyKey, direction) {
      return (
        Atlas.store.gemCurve({
          lattice: state.lattice,
          budget: Number(state.budget),
          direction: direction,
          qty: Atlas.store.gemQty(qtyKey),
          xAxis: "u",
          it: it,
        }) || []
      ).map(function (point) {
        return [point[0], point[1]];
      });
    }

    if (state.t >= 0.05) {
      E(
        "div",
        "caveat panel",
        "Warm-temperature caveat (registered gem evidence): bethe " +
          "T/D ≥ 0.05 gem rows are qualitative only (thermal spin-penalty, " +
          "sum-rule drift, Z inflation). Compare docc/energies, not Z.",
        view
      );
    }
    E(
      "div",
      "caveat",
      "DMFT-ED markers are ground-state T/D=0 references and are shown as " +
        "a separate temperature limit, not as an exact join to the selected " +
        "finite T. beta_fit=200 is the bath-fit grid, not physical T/D=0.005.",
      view
    );

    var panel = E("div", "panel", null, view);
    var edQualityMessages = {};
    var panels = QUANTITIES.map(function (qty) {
      var series = [];
      if (state.diff) {
        var gemMap = {};
        gemPoints(qty.key, "up").forEach(function (point) {
          gemMap[point[0]] = point[1];
        });
        var diffPoints = [];
        oursPoints(qty.key).forEach(function (point) {
          if (!point) {
            diffPoints.push(null);
            return;
          }
          if (gemMap[point[0]] !== undefined && point[1] !== null) {
            diffPoints.push([point[0], point[1] - gemMap[point[0]]]);
          }
        });
        series.push({
          label: "ours − gem up",
          tipLabel: "ours − gem up",
          legendKey: "ours-minus-gem",
          color: C.ours,
          marker: "circle",
          connect: false,
          points: diffPoints,
        });
        return {
          yLabel: "Δ " + qty.label,
          height: 190,
          hlines: [{ y: 0 }],
          series: series,
        };
      }
      series.push({
        label: oursLabel,
        tipLabel: "ours",
        legendKey: "ours",
        color: C.ours,
        marker: "circle",
        markerOrder: 3,
        markerSize: 3.6,
        connect: false,
        points: oursPoints(qty.key),
      });
      series.push({
        label: "gem B=" + state.budget + " up",
        tipLabel: "gem up",
        legendKey: "gem-up",
        color: C.gem,
        marker: "diamond",
        markerOrder: 2,
        markerSize: 4.4,
        connect: false,
        points: gemPoints(qty.key, "up"),
      });
      series.push({
        label: "gem B=" + state.budget + " down",
        tipLabel: "gem down",
        legendKey: "gem-down",
        color: C.gem,
        marker: "odiamond",
        markerOrder: 0,
        markerSize: 5.4,
        connect: false,
        points: gemPoints(qty.key, "down"),
      });
      [Number(state.budget)].forEach(function (nb) {
        var edAll = Atlas.store.edPoints(state.lattice, qty.key);
        if (
          edAll.qualitySummary &&
          edAll.qualitySummary.required &&
          edAll.qualitySummary.omitted
        ) {
          edQualityMessages[qty.key] =
            "DMFT-ED Z: " +
            edAll.qualitySummary.included +
            " rows have an explicitly converged low-frequency Z estimator; " +
            edAll.qualitySummary.omitted +
            " accepted rows are omitted" +
            (edAll.qualitySummary.omittedUnknown
              ? " because this payload does not carry their Z-quality flag"
              : " because their Z estimator is not certified") +
            ".";
        }
        var selectedEd = edAll.filter(function (point) {
            return point.nb === nb;
          });
        var pts = selectedEd
          .map(function (point) {
            return [point.u, point.value];
          })
          .sort(function (a, b) {
            return a[0] - b[0];
          });
        if (pts.length) {
          var accuracyKnown = selectedEd.some(function (point) {
            return point.accuracyQualified !== null;
          });
          var accuracyQualified =
            accuracyKnown &&
            selectedEd.every(function (point) {
              return point.accuracyQualified === true;
            });
          series.push({
            label:
              "DMFT-ED N_b=" +
              nb +
              " · T=0 · " +
              (accuracyQualified
                ? "accuracy-qualified"
                : accuracyKnown
                  ? "fixed-point accepted"
                  : "quality tier not recorded"),
            tipLabel: "DMFT-ED N_b=" + nb + " · T=0",
            legendKey: "ed-" + nb,
            color: C.ed,
            marker: nb === 1 ? "osquare" : "square",
            markerOrder: 1,
            markerSize: 4.8,
            connect: false,
            points: pts,
          });
        }
      });
      return { yLabel: qty.label, height: 200, series: series };
    });

    var figure = Atlas.plot.figure({
      width: 940,
      xLabel: "U/D",
      panels: panels,
    });
    panel.appendChild(figure.el);
    Object.keys(edQualityMessages).forEach(function (key) {
      E("div", "caveat", edQualityMessages[key], panel);
    });
    var actions = E("div", "chart-actions", null, panel);
    actions.appendChild(
      ui.btn("download SVG", function () {
        figure.svgs.forEach(function (svg, index) {
          Atlas.plot.dlSVG(svg, "bench_panel" + (index + 1));
        });
      })
    );
    actions.appendChild(
      ui.btn("download PNG", function () {
        figure.svgs.forEach(function (svg, index) {
          Atlas.plot.dlPNG(svg, "bench_panel" + (index + 1));
        });
      })
    );

    /* ---- pole-structure comparison (B=3 only, where gem recorded it) ---- */
    if (Number(state.budget) === 3 && branch && ds.d.poles) {
      var structPanel = E("div", "panel", null, view);
      E(
        "h2",
        null,
        "Σ pole structure: ours vs gem (framework-invariant objects)",
        structPanel
      );
      E(
        "p",
        "muted",
        "Our mirrored pole pair (±η, W²) against gem's self-energy poles " +
          "from its converged (R, Λ). gem recorded structure only on part " +
          "of the B=3 rows; raw R magnitudes are never compared.",
        structPanel
      );
      var table = E("table", "data", null, structPanel);
      var head = E("tr", null, null, E("thead", null, null, table));
      [
        "U/D",
        "η ours",
        "|pole| gem",
        "W² ours",
        "w² gem",
        "Z ours",
        "Z gem",
      ].forEach(function (title) {
        E("th", null, title, head);
      });
      var body = E("tbody", null, null, table);
      var latticeCode = gem.dicts.lattice.indexOf(state.lattice);
      var upCode = gem.dicts.direction.indexOf("up");
      var shown = 0;
      branch.rows.forEach(function (row) {
        if (shown >= 24) return;
        var iu = ds.d.cols.iu[row];
        var uValue = ds.u(row);
        /* gem iu indexes the anchor grid — match by value */
        var gemIu = grid.u.indexOf(uValue);
        if (gemIu < 0) return;
        for (var gi = 0; gi < gem.n; gi++) {
          if (
            gem.cols.lattice[gi] === latticeCode &&
            gem.cols.budget[gi] === 3 &&
            gem.cols.direction[gi] === upCode &&
            gem.cols.iu[gi] === gemIu &&
            gem.cols.it[gi] === it &&
            gem.cols.sig_p[gi]
          ) {
            var p = Atlas.spectra.params(ds, row);
            if (!p || !p.h.length) return;
            var eta = Math.abs(p.h[0][0]);
            var w2 = p.h[0][1] * p.h[0][1];
            var gemPole = Math.abs(gem.cols.sig_p[gi][0]);
            var gemW2 = gem.cols.sig_w[gi][0];
            var tr = E("tr", null, null, body);
            E("td", null, Atlas.fmt(uValue), tr);
            E("td", null, Atlas.fmt(eta), tr);
            E("td", null, Atlas.fmt(gemPole), tr);
            E("td", null, Atlas.fmt(w2), tr);
            E("td", null, Atlas.fmt(gemW2), tr);
            E("td", null, Atlas.fmt(ds.num("z_pole", row)), tr);
            E("td", null, Atlas.fmt(gem.cols.z_slope[gi]), tr);
            shown++;
            return;
          }
        }
      });
      if (!shown) {
        E(
          "p",
          "muted",
          "No gem structure rows at this (lattice, T).",
          structPanel
        );
      }
    }

    /* ---- caveats from the registered reference manifest ---- */
    if (gem.caveats && gem.caveats.length) {
      var caveatPanel = E("div", "panel", null, view);
      E("h2", null, "Comparison caveats (from the gem manifest)", caveatPanel);
      var list = E("ul", "report-list", null, caveatPanel);
      gem.caveats.forEach(function (caveat) {
        E("li", null, caveat, list);
      });
    }
  });
})();
