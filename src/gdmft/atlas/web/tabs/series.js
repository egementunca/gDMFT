/* Series builder: stack branch curves from any dataset/lattice/m_g/gauge,
   vs U at fixed T or vs T at fixed U. One panel per quantity scale-group
   (never a second y-axis). gem and DMFT-ED reference overlays. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;
  var C = Atlas.colors;

  function shortDs(id) {
    if (id.indexOf("gauge-matrix") >= 0) return "D08";
    if (id.indexOf("scan-matrix") >= 0) return "D09";
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
    var route = Atlas.store.primaryRoute("bethe", 3);
    if (!route) throw new Error("No primary source route for bethe m_g=3");
    var state = {
      x: "u",
      fixed: { u: 2.0, t: 0.01 },
      list: [
        {
          ds: route.dataset_id,
          lattice: "bethe",
          mg: 3,
          gauge: "bare",
          family: "metal",
          qty: "z_pole",
          slot: 0,
        },
        {
          ds: route.dataset_id,
          lattice: "bethe",
          mg: 3,
          gauge: "bare",
          family: "insul",
          qty: "z_pole",
          slot: 1,
        },
      ],
      gem: false,
      ed: false,
      junk: false,
      table: false,
      supplementarySources: false,
    };
    state.list.forEach(Atlas.store.applyPrimaryRoute);
    return state;
  }

  function familyOptions(ds) {
    var options = [
      { value: "metal", label: "metal (spliced)" },
      { value: "insul", label: "insulator" },
    ];
    ds.dictOf("family").forEach(function (family) {
      if (
        ["metal-up", "metal-down", "insul-down"].indexOf(family) < 0
      ) {
        options.push({ value: family, label: family + " (exotic)" });
      }
    });
    return options;
  }

  /* Which panel a series lands on: an explicit user choice ("1".."4")
     or the quantity's scale-group. Same panel = same y-axis. */
  function panelKeyOf(def) {
    if (def.panel && def.panel !== "auto") return "panel " + def.panel;
    return (Atlas.store.qty(def.qty) || { group: def.qty }).group;
  }

  function seriesLabel(def, showSource) {
    var qty = Atlas.store.qty(def.qty);
    return (
      (showSource ? shortDs(def.ds) + " " : "") +
      def.lattice +
      " m" +
      def.mg +
      " " +
      def.gauge +
      " " +
      def.family +
      " · " +
      (qty ? qty.label : def.qty)
    );
  }

  function seriesPoints(def, state) {
    var ds = Atlas.store.ds(def.ds);
    var grid = ds.grids[def.lattice];
    if (!grid) return [];
    var points = [];
    if (state.x === "u") {
      var it = nearestIndex(grid.t, state.fixed.t);
      var t = grid.t[it];
      if (def.family === "metal" || def.family === "insul") {
        var branch = Atlas.store.branch(
          def.ds,
          def.lattice,
          Number(def.mg),
          def.gauge,
          t,
          def.family
        );
        if (!branch) return [];
        branch.rows.forEach(function (row, position) {
          points.push([ds.u(row), ds.num(def.qty, row), row]);
          if (branch.breaks.indexOf(position) >= 0) points.push(null);
        });
        return points;
      }
      for (var i = 0; i < ds.n; i++) {
        if (
          ds.str("family", i) === def.family &&
          ds.lattice(i) === def.lattice &&
          ds.num("m_g", i) === Number(def.mg) &&
          ds.str("gauge", i) === def.gauge &&
          ds.d.cols.it[i] === it &&
          ds.converged(i)
        ) {
          points.push([ds.u(i), ds.num(def.qty, i), i]);
        }
      }
    } else {
      var iu = nearestIndex(grid.u, state.fixed.u);
      var metalSet = { "metal-up": 1, "metal-down": 1 };
      for (var j = 0; j < ds.n; j++) {
        var family = ds.str("family", j);
        var match =
          def.family === "metal"
            ? metalSet[family] === 1
            : def.family === "insul"
              ? family === "insul-down"
              : family === def.family;
        if (
          match &&
          ds.lattice(j) === def.lattice &&
          ds.num("m_g", j) === Number(def.mg) &&
          ds.str("gauge", j) === def.gauge &&
          ds.d.cols.iu[j] === iu &&
          ds.converged(j)
        ) {
          points.push([ds.t(j), ds.num(def.qty, j), j]);
        }
      }
    }
    points.sort(function (a, b) {
      return (a ? a[0] : Infinity) - (b ? b[0] : Infinity);
    });
    return points;
  }

  function gemOverlaySeries(state, notices) {
    var gem = Atlas.DATA.references.gem;
    if (!gem || !state.gem) return [];
    var anchorGrids = Atlas.DATA.datasets[gem.anchored_to].grids;
    var seen = {};
    var overlays = [];
    state.list.forEach(function (def) {
      var gemQty = Atlas.store.gemQty(def.qty);
      var structLabel = Atlas.store.gemStructLabel(def.qty);
      var budget = Number(def.mg);
      if (budget !== 1 && budget !== 3) return;
      if (!gemQty && !structLabel) {
        var qtyLabel = (Atlas.store.qty(def.qty) || { label: def.qty }).label;
        notices.push(
          "gem overlay: no analog for " + qtyLabel + " — bath parameters " +
            "are framework-specific; comparable quantities: Z, docc, " +
            "E_kin/D, E_tot/D, η, W, Λ, ΣW²"
        );
        return;
      }
      if (!anchorGrids[def.lattice]) return;
      var grid = anchorGrids[def.lattice];
      var options = {
        lattice: def.lattice,
        budget: budget,
        qty: gemQty,
        xAxis: state.x,
      };
      if (state.x === "u") {
        var it = grid.t.indexOf(
          grid.t[nearestIndex(grid.t, state.fixed.t)]
        );
        if (Math.abs(grid.t[it] - state.fixed.t) > 1e-9 * (1 + state.fixed.t)) {
          /* the fixed T is not on the gem grid — nearest is still useful,
             the arm label carries the exact value via the tooltip */
        }
        options.it = it;
      } else {
        options.iu = nearestIndex(grid.u, state.fixed.u);
      }
      var dedupe = [def.lattice, budget, gemQty || def.qty, state.x].join("|");
      if (seen[dedupe]) return;
      seen[dedupe] = true;
      if (structLabel && !gemQty) options.struct = true;
      if (options.struct) options.qty = def.qty;
      var structEmpty = true;
      ["up", "down"].forEach(function (direction) {
        var pts = Atlas.store.gemCurve(
          Object.assign({ direction: direction }, options)
        );
        if (pts && pts.length) {
          structEmpty = false;
          overlays.push({
            label: options.struct
              ? "gem B=" + budget + " " + structLabel + " " + direction
              : "gem B=" + budget + " " + direction + " (" + def.lattice + ")",
            tipLabel: options.struct
              ? "gem B=" + budget + " " + structLabel + " " + direction
              : "gem B=" + budget + " " + direction,
            legendKey:
              "gem-" + budget + "-" + direction + "-" +
              (options.struct ? structLabel : def.qty),
            color: C.gem,
            marker: direction === "down" ? "odiamond" : "diamond",
            markerOrder: direction === "down" ? 0 : 2,
            markerSize: direction === "down" ? 5.2 : 4.3,
            connect: false,
            points: pts,
            group: panelKeyOf(def),
            log: !!(Atlas.store.qty(def.qty) || {}).log,
          });
        }
        if (state.junk) {
          var junk = Atlas.store.gemCurve(
            Object.assign(
              { direction: direction, junkOnly: true },
              options
            )
          );
          if (junk && junk.length) {
            overlays.push({
              label: "gem junk ΣR²>1.1 (" + direction + ")",
              color: C.gem,
              marker: "x",
              connect: false,
              points: junk.map(function (point) {
                return [point[0], point[1]];
              }),
              group: panelKeyOf(def),
              log: !!(Atlas.store.qty(def.qty) || {}).log,
              markerOnly: true,
            });
          }
        }
      });
      if (options.struct && structEmpty) {
        notices.push(
          "gem overlay: gem recorded no Σ-pole structure for " +
            def.lattice + " B=" + budget + " at this slice (B=1 never has " +
            "structure; bethe B=3 coverage is partial)"
        );
      }
    });
    return overlays;
  }

  function edOverlaySeries(state, notices) {
    if (!state.ed || state.x !== "u") return [];
    var seen = {};
    var overlays = [];
    state.list.forEach(function (def) {
      var bathQuantity =
        ["p_v0", "p_v1", "p_eps1", "p_sumv2"].indexOf(def.qty) >= 0;
      var points = bathQuantity
        ? Atlas.store.edBathPoints(def.lattice, def.qty)
        : Atlas.store.edPoints(def.lattice, def.qty);
      if (
        points.qualitySummary &&
        points.qualitySummary.required &&
        points.qualitySummary.omitted
      ) {
        notices.push(
          "DMFT-ED Z overlay omits " +
            points.qualitySummary.omitted +
            " accepted row(s) without an explicitly certified " +
            "low-frequency Z estimator"
        );
      }
      var budget = Number(def.mg);
      var matching = points.filter(function (point) {
        return Number(point.nb) === budget;
      });
      if (!matching.length) {
        if (
          bathQuantity &&
          budget === 1 &&
          ["p_v1", "p_eps1"].indexOf(def.qty) >= 0
        ) {
          notices.push(
            "DMFT-ED N_b=1 has one central bath pole, so " +
              (Atlas.store.qty(def.qty) || { label: def.qty }).label +
              " is undefined rather than zero"
          );
        } else if (bathQuantity && def.lattice !== "bethe") {
          notices.push(
            "DMFT-ED bath arrays are stored only for Bethe; the legacy " +
              "square ED table has no eps/V arrays"
          );
        }
        return;
      }
      notices.push(
        "DMFT-ED markers are ground-state T/D=0 references, not an exact " +
          "join to the selected finite T. beta_fit=200 is a bath-fit grid, " +
          "not physical T/D=0.005"
      );
      if (bathQuantity) {
        notices.push(
          "DMFT-ED bath markers use the stored finite-bath pole sum: " +
            "|V0|, |V1|, |eps1|, or sum V_l^2. Coupling signs are gauge; " +
            "up/down continuation arms are separate. Bath-quality tiers " +
            "remain in the source rows; fixed-point acceptance is not an " +
            "accuracy qualification."
        );
      }
      ["up", "down"].forEach(function (direction) {
        var dedupe =
          [def.lattice, def.qty, budget, direction].join("|");
        if (seen[dedupe]) return;
        seen[dedupe] = true;
        var arm = matching.filter(function (point) {
          return point.direction === null || point.direction === direction;
        });
        var pts = arm
          .filter(function (point) {
            return point.value !== null;
          })
          .map(function (point) {
            return [point.u, point.value];
          })
          .sort(function (a, b) {
            return a[0] - b[0];
        });
        if (!pts.length) return;
        var qtyLabel =
          (Atlas.store.qty(def.qty) || { label: def.qty }).label;
        overlays.push({
          label:
            "DMFT-ED N_b=" + budget + " " + direction +
            " (T=0, " + def.lattice + ")",
          tipLabel:
            "ED N_b=" + budget + " " + direction + " · " + qtyLabel,
          legendKey:
            "ed-" + budget + "-" + direction,
          color: C.ed,
          marker:
            budget === 1
              ? direction === "down" ? "otriangle" : "triangle"
              : direction === "down" ? "osquare" : "square",
          markerOrder: direction === "down" ? 0 : 1,
          markerSize: direction === "down" ? 5.2 : 4.3,
          connect: false,
          points: pts,
          group: panelKeyOf(def),
          log: !!(Atlas.store.qty(def.qty) || {}).log,
        });
      });
    });
    return overlays;
  }

  function semiOverlaySeries(state, plotted) {
    if (!state.semi) return [];
    var seen = {};
    var overlays = [];
    plotted.forEach(function (entry) {
      var domain = entry.points
        .filter(function (point) {
          return point && point[1] !== null;
        })
        .map(function (point) {
          return point[0];
        });
      Atlas.semi
        .curves(entry.def.qty, entry.def.lattice, state.x, state.fixed, domain)
        .forEach(function (curve) {
          if (seen[curve.label]) return;
          seen[curve.label] = true;
          overlays.push({
            label: curve.label,
            color: C.exotic,
            dash: true,
            marker: "none",
            points: curve.points,
            group: panelKeyOf(entry.def),
            log: !!(Atlas.store.qty(entry.def.qty) || {}).log,
          });
        });
    });
    return overlays;
  }

  /* Why did a series produce nothing visible? */
  function emptyReason(def, state) {
    var ds = Atlas.store.ds(def.ds);
    var exists = false;
    for (var i = 0; i < ds.n; i++) {
      if (
        ds.lattice(i) === def.lattice &&
        ds.num("m_g", i) === Number(def.mg) &&
        ds.str("gauge", i) === def.gauge
      ) {
        exists = true;
        break;
      }
    }
    if (!exists) {
      return (
        "no " + def.lattice + " m_g=" + def.mg + " " + def.gauge +
        " rows exist in " + shortDs(def.ds) +
        " (the Atlas tab lists every combination this dataset contains)"
      );
    }
    var qty = Atlas.store.qty(def.qty);
    if (
      qty &&
      qty.pole &&
      ["metal", "insul"].indexOf(def.family) < 0 &&
      ["p_sumv2", "p_sumw2"].indexOf(def.qty) < 0
    ) {
      return (
        qty.label + " is undefined for the asymmetric exotic families — " +
        "their modes don't reduce to a symmetric pair; use ΣV²/ΣW² here, " +
        "or the Inspect tab for the full mode arrays"
      );
    }
    return (
      "no converged " + def.family + " attempts carry " +
      (qty ? qty.label : def.qty) + " at this fixed " +
      (state.x === "u" ? "T" : "U")
    );
  }

  var PRESETS = [
    {
      label: "Z: m_g=1 vs 3",
      apply: function (state, base) {
        var mg1 = Atlas.store.primaryRoute("bethe", 1);
        if (!mg1) throw new Error("No primary source route for bethe m_g=1");
        state.list = [
          { ds: mg1.dataset_id, lattice: "bethe", mg: 1, gauge: mg1.gauge, family: "metal", qty: "z_pole", slot: 0 },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "z_pole", slot: 1 },
        ];
        state.x = "u";
      },
    },
    {
      label: "Ω crossing (U*)",
      apply: function (state, base) {
        state.list = [
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "omega_d", slot: 0 },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "insul", qty: "omega_d", slot: 1 },
        ];
        state.x = "u";
      },
    },
    {
      label: "docc: ours vs gem vs ED",
      apply: function (state, base) {
        state.list = [
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "docc", slot: 0 },
        ];
        state.x = "u";
        state.gem = true;
        state.ed = true;
      },
    },
    {
      label: "g bath: ghost vs ED",
      apply: function (state, base) {
        var mg1 = Atlas.store.primaryRoute("bethe", 1);
        if (!mg1) throw new Error("No primary source route for bethe m_g=1");
        state.list = [
          { ds: mg1.dataset_id, lattice: "bethe", mg: 1, gauge: mg1.gauge, family: "metal", qty: "p_v0", slot: 0 },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_v0", slot: 1 },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_v1", slot: 2 },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_eps1", slot: 3 },
          { ds: mg1.dataset_id, lattice: "bethe", mg: 1, gauge: mg1.gauge, family: "metal", qty: "p_sumv2", slot: 4 },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_sumv2", slot: 5 },
        ];
        state.x = "u";
        state.fixed.t = 0.001;
        state.ed = true;
      },
    },
    {
      label: "Z estimators",
      apply: function (state, base) {
        state.list = [
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "z_pole", slot: 0 },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "z_mats", slot: 1 },
        ];
        state.x = "u";
      },
    },
    {
      label: "D(T) thermal",
      apply: function (state, base) {
        state.list = [
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "docc", slot: 0 },
        ];
        state.x = "t";
        state.gem = true;
      },
    },
    {
      label: "lattice vs gateway h-sector",
      apply: function (state, base) {
        state.list = [
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_lam", slot: 0, panel: "1" },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_eta", slot: 1, panel: "1" },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_w", slot: 2 },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_lam_gateway", slot: 3, panel: "1" },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_eta_gateway", slot: 4, panel: "1" },
          { ds: base, lattice: "bethe", mg: 3, gauge: "bare", family: "metal", qty: "p_w_gateway", slot: 5 },
        ];
        state.x = "u";
        state.semi = true;
      },
    },
  ];

  Atlas.registerTab("series", "Series", function (view) {
    var state = Atlas.state.series || (Atlas.state.series = defaults());
    var ui = Atlas.ui;
    if (!state.supplementarySources) {
      state.list.forEach(Atlas.store.applyPrimaryRoute);
    }

    function rerender() {
      Atlas.saveState("series");
      Atlas.tabs
        .filter(function (tab) {
          return tab.id === "series";
        })[0]
        .render(view);
    }
    function set(key) {
      return function (value) {
        state[key] = value;
        rerender();
      };
    }

    view.innerHTML = "";

    /* keep every definition consistent with its dataset — switching the
       dataset must never leave a family/gauge/quantity the new dataset
       doesn't have while the control displays something else */
    state.list.forEach(function (def) {
      var ds = Atlas.store.ds(def.ds);
      if (!ds.grids[def.lattice]) def.lattice = ds.dictOf("lattice")[0];
      if (ds.mgValues().indexOf(Number(def.mg)) < 0) {
        def.mg = ds.mgValues()[0];
      }
      if (ds.dictOf("gauge").indexOf(def.gauge) < 0) {
        def.gauge = Atlas.store.pickGauge(
          def.ds, def.lattice, Number(def.mg), "bare"
        );
      }
      if (
        ["metal", "insul"].indexOf(def.family) < 0 &&
        ds.dictOf("family").indexOf(def.family) < 0
      ) {
        def.family = "metal";
      }
      var qtyOk = Atlas.store.qtyFor(ds).some(function (qty) {
        return qty.key === def.qty;
      });
      if (!qtyOk) def.qty = "z_pole";
    });

    /* ---- series definition rows ---- */
    var seriesPanel = E("div", "panel", null, view);
    E("h2", null, "Series", seriesPanel);
    state.list.forEach(function (def, index) {
      var ds = Atlas.store.ds(def.ds);
      function setDef(key, cast) {
        return function (value) {
          def[key] = cast ? cast(value) : value;
          if (
            !state.supplementarySources &&
            (key === "lattice" || key === "mg")
          ) {
            Atlas.store.applyPrimaryRoute(def);
          }
          if (key === "ds") {
            var next = Atlas.store.ds(def.ds);
            if (!next.grids[def.lattice]) {
              def.lattice = next.dictOf("lattice")[0];
            }
            if (next.mgValues().indexOf(Number(def.mg)) < 0) {
              def.mg = next.mgValues()[0];
            }
            if (next.dictOf("gauge").indexOf(def.gauge) < 0) {
              def.gauge = next.dictOf("gauge")[0];
            }
          }
          rerender();
        };
      }
      var key = E("span", "viz-key", null, null);
      key.style.background = C.cat[def.slot % C.cat.length];
      var latticeValues = state.supplementarySources
        ? ds.dictOf("lattice")
        : Atlas.store.primaryLattices();
      var mgValues = state.supplementarySources
        ? ds.mgValues()
        : Atlas.store.primaryMgValues(def.lattice);
      var rowControls = [key];
      if (state.supplementarySources) {
        rowControls.push(
          ui.field(
            "evidence dataset",
            ui.select(
              Atlas.store.pointIds().map(function (id) {
                return { value: id, label: Atlas.store.dsLabel(id) };
              }),
              def.ds,
              setDef("ds")
            )
          )
        );
      }
      rowControls.push(
        ui.field(
          "lattice",
          ui.select(
            latticeValues.map(function (value) {
              return { value: value, label: value };
            }),
            def.lattice,
            setDef("lattice")
          )
        ),
        ui.field(
          "m_g",
          ui.select(
            mgValues.map(function (value) {
              return { value: value, label: String(value) };
            }),
            def.mg,
            setDef("mg", Number)
          )
        )
      );
      if (state.supplementarySources) {
        rowControls.push(
          ui.field(
            "gauge route",
            ui.select(
              ds.dictOf("gauge").map(function (value) {
                var populated = false;
                for (var ri = 0; ri < ds.n; ri++) {
                  if (
                    ds.str("gauge", ri) === value &&
                    ds.lattice(ri) === def.lattice &&
                    ds.num("m_g", ri) === Number(def.mg)
                  ) {
                    populated = true;
                    break;
                  }
                }
                return {
                  value: value,
                  label: value + (populated ? "" : " — no rows here"),
                };
              }),
              def.gauge,
              setDef("gauge")
            )
          )
        );
      }
      rowControls.push(
        ui.field(
          "branch",
          ui.select(familyOptions(ds), def.family, setDef("family"))
        ),
        ui.field(
          "quantity",
          ui.select(
            Atlas.store.qtyFor(ds).map(function (qty) {
              return { value: qty.key, label: qty.label };
            }),
            def.qty,
            setDef("qty")
          )
        ),
        ui.field(
          "panel",
          ui.select(
            [{ value: "auto", label: "auto" }].concat(
              ["1", "2", "3", "4"].map(function (n) {
                return { value: n, label: "panel " + n };
              })
            ),
            def.panel || "auto",
            setDef("panel")
          )
        ),
        ui.btn("remove", function () {
          state.list.splice(index, 1);
          rerender();
        })
      );
      var row = ui.row(
        rowControls,
        "filter-row series-row"
      );
      seriesPanel.appendChild(row);
    });
    var addRow = E("div", "filter-row", null, seriesPanel);
    addRow.appendChild(
      ui.check(
        "show supplementary sources",
        !!state.supplementarySources,
        function (value) {
          state.supplementarySources = value;
          rerender();
        }
      )
    );
    addRow.appendChild(
      ui.btn("+ add series", function () {
        var used = state.list.map(function (def) {
          return def.slot;
        });
        var slot = 0;
        while (used.indexOf(slot) >= 0) slot++;
        var template = state.list[state.list.length - 1] || defaults().list[0];
        state.list.push(
          Object.assign({}, template, { slot: slot })
        );
        rerender();
      })
    );
    PRESETS.forEach(function (preset) {
      addRow.appendChild(
        ui.btn(preset.label, function () {
          var route = Atlas.store.primaryRoute("bethe", 3);
          if (!route) throw new Error("No primary source route for bethe m_g=3");
          preset.apply(state, route.dataset_id);
          if (!state.supplementarySources) {
            state.list.forEach(Atlas.store.applyPrimaryRoute);
          }
          rerender();
        }, "btn-ghost")
      );
    });

    /* ---- axis + overlay controls ---- */
    var firstDef = state.list[0];
    var axisGrid = firstDef
      ? Atlas.store.ds(firstDef.ds).grids[firstDef.lattice]
      : null;
    var controls = [
      ui.field(
        "x axis",
        ui.select(
          [
            { value: "u", label: "U/D at fixed T" },
            { value: "t", label: "T/D at fixed U" },
          ],
          state.x,
          set("x")
        )
      ),
    ];
    if (axisGrid) {
      var fixedValues = state.x === "u" ? axisGrid.t : axisGrid.u;
      var fixedKey = state.x === "u" ? "t" : "u";
      var currentIndex = nearestIndex(fixedValues, state.fixed[fixedKey]);
      var slider = document.createElement("input");
      slider.type = "range";
      slider.min = 0;
      slider.max = fixedValues.length - 1;
      slider.value = currentIndex;
      var readout = E(
        "span",
        "slider-readout",
        (state.x === "u" ? "T/D = " : "U/D = ") +
          Atlas.fmt(fixedValues[currentIndex])
      );
      slider.addEventListener("input", function () {
        state.fixed[fixedKey] = fixedValues[Number(slider.value)];
        readout.textContent =
          (state.x === "u" ? "T/D = " : "U/D = ") +
          Atlas.fmt(state.fixed[fixedKey]);
        renderChart(); /* live: redraw the chart only, controls survive */
      });
      slider.addEventListener("change", function () {
        Atlas.saveState("series");
      });
      var sliderWrap = E("div", "field slider-field");
      E(
        "span",
        "field-label",
        state.x === "u" ? "step T/D" : "step U/D",
        sliderWrap
      );
      var inner = E("div", "slider-inner", null, sliderWrap);
      inner.appendChild(slider);
      inner.appendChild(readout);
      controls.push(sliderWrap);
    }
    controls.push(
      ui.check("gem overlay", state.gem, set("gem")),
      ui.check("ΣR²>1.1 junk (×)", state.junk, set("junk")),
      ui.check("DMFT-ED anchors", state.ed, set("ed")),
      ui.check("semianalytic refs", state.semi, set("semi")),
      ui.check("table view", state.table, set("table"))
    );
    view.appendChild(ui.row(controls));

    /* chart + table live in their own host so slider drags can redraw
       them without touching the controls above */
    var chartHost = E("div", null, null, view);
    function renderChart() {
    chartHost.innerHTML = "";

    /* ---- assemble figure: one panel per quantity group ---- */
    var plotted = state.list.map(function (def) {
      var qty = Atlas.store.qty(def.qty);
      return {
        def: def,
        label: seriesLabel(def, !!state.supplementarySources),
        color: C.cat[def.slot % C.cat.length],
        points: seriesPoints(def, state),
        group: panelKeyOf(def),
        log: !!(qty && qty.log),
        marker:
          state.x === "t"
            ? def.family === "insul"
              ? "open"
              : "circle"
            : undefined,
        connect: state.x !== "t",
      };
    });
    var overlayNotices = [];
    var overlays = gemOverlaySeries(state, overlayNotices)
      .concat(edOverlaySeries(state, overlayNotices))
      .concat(semiOverlaySeries(state, plotted));
    var groups = [];
    var byGroup = {};
    plotted.concat(overlays).forEach(function (series) {
      if (!byGroup[series.group]) {
        byGroup[series.group] = [];
        groups.push(series.group);
      }
      byGroup[series.group].push(series);
    });

    var chartPanel = E("div", "panel", null, chartHost);
    if (!groups.length) {
      E("p", "muted", "Add a series to plot.", chartPanel);
      return;
    }
    if (state.x === "t") {
      E(
        "div",
        "caveat",
        "Temperature-series markers are independent fixed-temperature " +
          "roots. They are not connected because no continuation or " +
          "branch-continuity certificate across T has been applied.",
        chartPanel
      );
    }
    plotted.forEach(function (entry) {
      var hasData = entry.points.some(function (point) {
        return point && point[1] !== null;
      });
      if (hasData) return;
      var notice = E("div", "series-notice", null, chartPanel);
      var key = E("span", "viz-key", null, notice);
      key.style.background = entry.color;
      E("span", null, entry.label + " — " + emptyReason(entry.def, state), notice);
    });
    overlayNotices
      .filter(function (text, index) {
        return overlayNotices.indexOf(text) === index;
      })
      .forEach(function (text) {
        var notice = E("div", "series-notice", null, chartPanel);
        var key = E("span", "viz-key", null, notice);
        key.style.background =
          text.indexOf("DMFT-ED") === 0 ? C.ed : C.gem;
        E("span", null, text, notice);
      });

    /* U* markers for the plotted branch pairs at this fixed T */
    var vlines = [];
    if (state.x === "u") {
      var seenGroups = {};
      state.list.forEach(function (def) {
        var groupKey = [def.ds, def.lattice, def.mg, def.gauge].join("|");
        if (seenGroups[groupKey]) return;
        seenGroups[groupKey] = true;
        var grid = Atlas.store.ds(def.ds).grids[def.lattice];
        if (!grid) return;
        var t = grid.t[nearestIndex(grid.t, state.fixed.t)];
        Atlas.store
          .ustarFor(def.ds, def.lattice, Number(def.mg), def.gauge)
          .forEach(function (entry) {
            if (Math.abs(entry.t - t) < 1e-12 && entry.ustar !== undefined) {
              vlines.push({
                x: entry.ustar,
                label:
                  "candidate U* " +
                  (state.supplementarySources
                    ? shortDs(def.ds) + " "
                    : "") +
                  "m" + def.mg,
              });
            }
          });
      });
    }

    var logGroups = {};
    groups.forEach(function (group) {
      logGroups[group] = byGroup[group].every(function (series) {
        return series.log;
      });
    });
    function panelLabel(group) {
      if (group.indexOf("panel ") !== 0) return group;
      var labels = [];
      byGroup[group].forEach(function (series) {
        if (!series.def) return;
        var qty = Atlas.store.qty(series.def.qty);
        var label = qty ? qty.label : series.def.qty;
        if (labels.indexOf(label) < 0) labels.push(label);
      });
      if (!labels.length) return group;
      return (
        labels.slice(0, 2).join(" · ") + (labels.length > 2 ? " · …" : "")
      );
    }
    var figure = Atlas.plot.figure({
      width: 940,
      xLabel: state.x === "u" ? "U/D" : "T/D",
      xLog: state.x === "t",
      panels: groups.map(function (group) {
        return {
          yLabel: panelLabel(group),
          yLog: !!logGroups[group],
          height: groups.length > 2 ? 190 : 250,
          vlines: vlines,
          series: byGroup[group].map(function (series) {
            return {
              label: series.label,
              color: series.color,
              dash: series.dash,
              marker: series.markerOnly
                ? "x"
                : series.marker !== undefined
                  ? series.marker
                  : undefined,
              connect: series.markerOnly ? false : series.connect,
              markerOrder: series.markerOrder,
              markerSize: series.markerSize,
              tipLabel: series.tipLabel,
              legendKey: series.legendKey,
              points: series.points.map(function (point) {
                return point === null ? null : [point[0], point[1]];
              }),
            };
          }),
        };
      }),
    });
    chartPanel.appendChild(figure.el);
    var actions = E("div", "chart-actions", null, chartPanel);
    actions.appendChild(
      ui.btn("download SVG", function () {
        figure.svgs.forEach(function (svg, index) {
          Atlas.plot.dlSVG(svg, "series_panel" + (index + 1));
        });
      })
    );
    actions.appendChild(
      ui.btn("download PNG", function () {
        figure.svgs.forEach(function (svg, index) {
          Atlas.plot.dlPNG(svg, "series_panel" + (index + 1));
        });
      })
    );

    /* ---- table view twin ---- */
    if (state.table) {
      var tablePanel = E("div", "panel", null, chartHost);
      E("h2", null, "Plotted values", tablePanel);
      var xs = {};
      var all = plotted.concat(overlays);
      all.forEach(function (series) {
        series.points.forEach(function (point) {
          if (point && point[1] !== null) xs[point[0]] = true;
        });
      });
      var xValues = Object.keys(xs)
        .map(Number)
        .sort(function (a, b) {
          return a - b;
        });
      var table = E("table", "data", null, tablePanel);
      var head = E("tr", null, null, E("thead", null, null, table));
      E("th", null, state.x === "u" ? "U/D" : "T/D", head);
      all.forEach(function (series) {
        E("th", "txt", series.tipLabel || series.label, head);
      });
      var body = E("tbody", null, null, table);
      xValues.forEach(function (x) {
        var row = E("tr", null, null, body);
        E("td", null, Atlas.fmt(x), row);
        all.forEach(function (series) {
          var value = null;
          series.points.forEach(function (point) {
            if (point && Math.abs(point[0] - x) < 1e-12) value = point[1];
          });
          E("td", null, value === null ? "—" : Atlas.fmt(value), row);
        });
      });
    }
    }
    renderChart();
  });
})();
