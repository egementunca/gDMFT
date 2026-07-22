/* Atlas: (U/D, T/D) heatmaps — phase/coexistence map, ΔΩ polarity map,
   scalar observables — with the U*(T) line overlaid and cell drill-down. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;
  var C = Atlas.colors;
  // Registered endpoint corridors (same constants as the figure suite):
  // the first-order construction ends inside (T_low, T_high); the U*(T)
  // diagnostic is meaningful only at T <= T_low. Above it the crossing
  // wanders through crossover territory and must not be drawn.
  var CORRIDOR_TMAX = { bethe: 0.010, square: 0.004 };

  var SCALAR_VIEWS = [
    { key: "z_pole", label: "Z (pole)" },
    { key: "z_mats", label: "Z (Matsubara)" },
    { key: "docc", label: "double occupancy" },
    { key: "omega_d", label: "Ω/D" },
    { key: "etot_d", label: "E_tot/D" },
    { key: "lam_red_d", label: "λ_red/D" },
    { key: "r_red", label: "R_red" },
    { key: "resnorm", label: "log10 residual", log: true },
  ];

  var COEX_LABELS = {
    1: "metal only",
    2: "insulator only",
    3: "coexistence (metal Ω lower)",
    4: "coexistence (insul Ω lower)",
    5: "coexistence (Ω unknown)",
    6: "exotic only",
  };
  var COEX_COLORS = {
    1: C.metal,
    2: C.insul,
    3: C.both,
    4: C.both,
    5: C.both,
    6: C.exotic,
  };
  var COEX_LEGEND = {
    1: "metal only",
    2: "insulator only",
    3: "coexistence",
    6: "exotic only",
  };
  var COEX_LEGEND_COLORS = {
    1: C.metal,
    2: C.insul,
    3: C.both,
    6: C.exotic,
  };
  var STATUS_LABELS = {
    1: "attempts; none converged",
    2: "converged; validation incomplete",
    3: "converged; explicit gate failure",
    4: "admissible; not selected",
    5: "selected",
  };
  var STATUS_COLORS = {
    1: "#d3d1ca",
    2: "#eda100",
    3: "#e34948",
    4: "#1baf7a",
    5: "#2a78d6",
  };

  function defaults() {
    var lattices = Atlas.store.primaryLattices();
    var lattice = lattices.indexOf("bethe") >= 0 ? "bethe" : lattices[0];
    /* Open on a populated, directly recorded cell and show evidence
       coverage before any branch interpretation. */
    var mgs = Atlas.store.primaryMgValues(lattice);
    var mg = mgs.indexOf(1) >= 0 ? 1 : mgs[0];
    var state = {
      ds: null,
      lattice: lattice,
      mg: mg,
      gauge: "bare",
      view: "status",
      family: "metal",
      ustar: false,
      supplementarySource: false,
    };
    Atlas.store.applyPrimaryRoute(state);
    return state;
  }

  function groupRowsAtKey(ds, state, it, iu) {
    var keyed = ds.keyRows()[state.lattice];
    var rows = keyed && keyed[it] && keyed[it][iu] ? keyed[it][iu] : [];
    return rows.filter(function (i) {
      return (
        ds.num("m_g", i) === Number(state.mg) &&
        ds.str("gauge", i) === state.gauge
      );
    });
  }

  function familyKind(family) {
    if (family === "metal-up" || family === "metal-down") return "metal";
    if (family === "insul-down") return "insul";
    return null;
  }

  function bestRow(ds, rows) {
    var best = null;
    var bestRes = Infinity;
    rows.forEach(function (i) {
      var res = ds.num("resnorm", i);
      var value = res === null ? Infinity : res;
      if (best === null || value < bestRes) {
        best = i;
        bestRes = value;
      }
    });
    return best;
  }

  function statusValue(ds, state, it, iu) {
    var rows = groupRowsAtKey(ds, state, it, iu);
    if (!rows.length) return null;
    var converged = rows.filter(function (i) {
      return ds.converged(i);
    });
    if (!converged.length) return 1;
    if (
      converged.some(function (i) {
        return ds.tri("selected", i) === 1;
      })
    ) {
      return 5;
    }
    if (
      converged.some(function (i) {
        return ds.tri("admissible", i) === 1;
      })
    ) {
      return 4;
    }
    var validationKeys = [
      "ok",
      "eq_ok",
      "density_ok",
      "guards_ok",
      "bounds_ok",
      "cont_ok",
      "admissible",
    ];
    var explicitFailure = converged.some(function (i) {
      return validationKeys.some(function (key) {
        return ds.tri(key, i) === 0;
      });
    });
    return explicitFailure ? 3 : 2;
  }

  function cellValue(ds, state, it, iu) {
    var rows = groupRowsAtKey(ds, state, it, iu);
    if (state.view === "status") return statusValue(ds, state, it, iu);
    if (state.view === "phase") return null;
    var converged = rows.filter(function (i) {
      return ds.converged(i);
    });
    if (state.view === "domega") {
      var metal = null;
      var insul = null;
      converged.forEach(function (i) {
        var kind = familyKind(ds.str("family", i));
        var omega = ds.num("omega_d", i);
        if (kind === null || omega === null) return;
        if (kind === "metal" && (metal === null || omega < metal)) {
          metal = omega;
        }
        if (kind === "insul" && (insul === null || omega < insul)) {
          insul = omega;
        }
      });
      return metal !== null && insul !== null ? metal - insul : null;
    }
    var view = null;
    SCALAR_VIEWS.forEach(function (candidate) {
      if (candidate.key === state.view) view = candidate;
    });
    if (!view) return null;
    var matching = converged.filter(function (i) {
      return familyKind(ds.str("family", i)) === state.family;
    });
    var row = bestRow(ds, matching);
    if (row === null) return null;
    var value = ds.num(view.key, row);
    if (value === null) return null;
    return view.log ? (value > 0 ? Math.log10(value) : null) : value;
  }

  function gateChip(parent, label, tri) {
    var chip = E("span", "gate-chip", null, parent);
    var dot = E("span", "gate-dot", null, chip);
    dot.style.background =
      tri === 1 ? "#0ca30c" : tri === 0 ? "#d03b3b" : "#c3c2b7";
    E("span", null, label + (tri === 2 ? " ?" : tri === 1 ? " ✓" : " ✗"), chip);
  }

  function showCellDetail(state, it, iu) {
    var ds = Atlas.store.ds(state.ds);
    var grid = ds.grids[state.lattice];
    var rows = groupRowsAtKey(ds, state, it, iu);
    Atlas.showPin(function (pin) {
      E(
        "h3",
        null,
        state.lattice +
          " · m_g=" +
          state.mg +
          " · " +
          state.gauge +
          " · U/D=" +
          Atlas.fmt(grid.u[iu]) +
          " · T/D=" +
          Atlas.fmt(grid.t[it]),
        pin
      );
      if (!rows.length) {
        E(
          "p",
          "muted",
          "No " + state.gauge + " attempts at this key — this gauge is a " +
            "sparse subset in this dataset.",
          pin
        );
        var keyed = ds.keyRows()[state.lattice];
        var here = keyed && keyed[it] && keyed[it][iu] ? keyed[it][iu] : [];
        var byGauge = {};
        here.forEach(function (i) {
          if (ds.num("m_g", i) !== Number(state.mg)) return;
          var gauge = ds.str("gauge", i);
          byGauge[gauge] = (byGauge[gauge] || 0) + 1;
        });
        var others = Object.keys(byGauge);
        if (others.length) {
          E(
            "p",
            null,
            "Gauges with attempts at this key (m_g=" + state.mg + "): " +
              others
                .map(function (gauge) {
                  return gauge + " (" + byGauge[gauge] + ")";
                })
                .join(" · "),
            pin
          );
        } else {
          E(
            "p",
            null,
            "No attempts at this key for m_g=" + state.mg +
              " in any gauge of this dataset.",
            pin
          );
        }
        return;
      }
      rows.forEach(function (i) {
        var card = E("div", "pin-row", null, pin);
        var title = E("div", null, null, card);
        E("strong", null, ds.str("family", i), title);
        E(
          "span",
          "muted",
          "  " +
            (ds._hasCategory
              ? ds.str("category", i)
              : "converged=" + ds.tri("src_converged", i)) +
            (ds.str("basin", i) ? " · basin " + ds.str("basin", i) : ""),
          title
        );
        E(
          "div",
          "muted",
          "pid " + ds.str("pid", i),
          card
        );
        E(
          "div",
          null,
          "Z=" +
            Atlas.fmt(ds.num("z_pole", i)) +
            " · docc=" +
            Atlas.fmt(ds.num("docc", i)) +
            " · Ω/D=" +
            Atlas.fmt(ds.num("omega_d", i)) +
            " · res=" +
            Atlas.fmt(ds.num("resnorm", i)),
          card
        );
        var gates = E("div", "gate-row", null, card);
        gateChip(gates, "solver", ds.tri("ok", i));
        gateChip(gates, "equations", ds.tri("eq_ok", i));
        gateChip(gates, "guards", ds.tri("guards_ok", i));
        gateChip(gates, "admissible", ds.tri("admissible", i));
        gateChip(gates, "selected", ds.tri("selected", i));
      });
      E(
        "p",
        "muted",
        "Gate legend: ✓ true · ✗ false · ? unknown (unknown ≠ false).",
        pin
      );
    });
  }

  Atlas.registerTab("atlas", "Atlas", function (view) {
    /* every control change re-renders this tab in place — clear first,
       or the fresh render appends below the stale one */
    view.innerHTML = "";
    var state = Atlas.state.atlas || (Atlas.state.atlas = defaults());
    if (!state.supplementarySource) Atlas.store.applyPrimaryRoute(state);
    var ds = Atlas.store.ds(state.ds);
    if (!ds.grids[state.lattice]) state.lattice = ds.dictOf("lattice")[0];
    if (ds.mgValues().indexOf(Number(state.mg)) < 0) {
      state.mg = ds.mgValues()[0];
    }
    if (ds.dictOf("gauge").indexOf(state.gauge) < 0) {
      state.gauge = ds.dictOf("gauge")[0];
    }

    var ui = Atlas.ui;
    function set(key) {
      return function (value) {
        state[key] = value;
        if (
          !state.supplementarySource &&
          (key === "lattice" || key === "mg" || key === "supplementarySource")
        ) {
          Atlas.store.applyPrimaryRoute(state);
        }
        Atlas.saveState("atlas");
        Atlas.tabs
          .filter(function (tab) {
            return tab.id === "atlas";
          })[0]
          .render(view);
      };
    }

    var viewOptions = [
      { value: "status", label: "attempt / validation status" },
      { value: "phase", label: "candidate branch overlap (provisional)" },
      {
        value: "domega",
        label: "candidate ΔΩ/D = Ω_metal − Ω_insul (provisional)",
      },
    ].concat(
      SCALAR_VIEWS.filter(function (candidate) {
        return ds.has(candidate.key);
      }).map(function (candidate) {
        return { value: candidate.key, label: candidate.label };
      })
    );
    var provisional =
      state.view === "phase" || state.view === "domega";
    var isScalar =
      state.view !== "status" &&
      state.view !== "phase" &&
      state.view !== "domega";
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
          set("mg")
        )
      ),
      ui.field("map", ui.select(viewOptions, state.view, set("view"))),
    ];
    controls.push(
      ui.check(
        "show supplementary sources",
        !!state.supplementarySource,
        set("supplementarySource")
      )
    );
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
    if (isScalar) {
      controls.push(
        ui.field(
          "branch",
          ui.select(
            [
              { value: "metal", label: "metal" },
              { value: "insul", label: "insulator" },
            ],
            state.family,
            set("family")
          )
        )
      );
    }
    if (provisional) {
      controls.push(
        ui.check("diagnostic U*(T) overlay", state.ustar, set("ustar"))
      );
    }
    view.appendChild(ui.row(controls));

    var meta = Atlas.store.dsMeta(state.ds);
    if (meta) {
      var route = Atlas.store.primaryRoute(state.lattice, Number(state.mg));
      E(
        "p",
        "muted ds-note",
        (state.supplementarySource
          ? "Supplementary source: "
          : "Automatic primary source: ") +
          Atlas.store.dsLabel(state.ds) +
          " · " +
          (route && !state.supplementarySource
            ? route.quadrature + " · "
            : "") +
          ds.n +
          " attempts · " +
          (meta.description || ""),
        view
      );
    }
    if (provisional) {
      E(
        "div",
        "caveat provisional-panel",
        "Provisional branch-overlap diagnostic only. These maps use " +
          "converged attempt labels, while physical guards, continuity, " +
          "admissibility, and selected branches can still be unknown. Do " +
          "not read Uc, U*, or a publication phase boundary from this view.",
        view
      );
    }

    /* the selected (lattice, m_g, gauge) may simply not exist in this
       dataset — say so and list what does, instead of an empty grid */
    var groupCount = 0;
    for (var ri = 0; ri < ds.n; ri++) {
      if (
        ds.lattice(ri) === state.lattice &&
        ds.num("m_g", ri) === Number(state.mg) &&
        ds.str("gauge", ri) === state.gauge
      ) {
        groupCount++;
      }
    }
    if (!groupCount) {
      var emptyPanel = E("div", "panel", null, view);
      E(
        "h2",
        null,
        "No attempts for " + state.lattice + " · m_g=" + state.mg + " · " +
          state.gauge + " in this dataset",
        emptyPanel
      );
      E(
        "p",
        "muted",
        "Combinations this dataset does contain:",
        emptyPanel
      );
      var comboTable = E("table", "data", null, emptyPanel);
      var comboHead = E("tr", null, null, E("thead", null, null, comboTable));
      E("th", "txt", "lattice · m_g · gauge", comboHead);
      E("th", null, "attempts", comboHead);
      var comboBody = E("tbody", null, null, comboTable);
      Atlas.store.groupCombos(state.ds).forEach(function (combo) {
        var tr = E("tr", null, null, comboBody);
        E("td", "txt", combo.label, tr);
        E("td", null, String(combo.rows), tr);
      });
      return;
    }

    var panel = E("div", "panel", null, view);
    var grid = ds.grids[state.lattice];
    var overlay = null;
    if (provisional && state.ustar) {
      var corridorMax = CORRIDOR_TMAX[state.lattice];
      overlay = Atlas.store
        .ustarFor(state.ds, state.lattice, Number(state.mg), state.gauge)
        .filter(function (entry) {
          return (
            entry.ustar !== undefined &&
            (corridorMax === undefined || entry.t <= corridorMax + 1e-12)
          );
        })
        .sort(function (a, b) {
          return a.t - b.t;
        })
        .map(function (entry) {
          return [entry.ustar, entry.t];
        });
    }

    var figure;
    if (state.view === "status") {
      figure = Atlas.plot.heatmap({
        uValues: grid.u,
        tValues: grid.t,
        mode: "cat",
        catColors: STATUS_COLORS,
        catLabels: STATUS_LABELS,
        label: "attempt / validation status",
        value: function (it, iu) {
          return statusValue(ds, state, it, iu);
        },
        tipExtra: function (it, iu, node) {
          E(
            "div",
            "muted",
            groupRowsAtKey(ds, state, it, iu).length +
              " recorded attempt(s) · click for gate details",
            node
          );
        },
        onClick: function (it, iu) {
          showCellDetail(state, it, iu);
        },
      });
    } else if (state.view === "phase") {
      var coex = Atlas.store.coexFor(
        state.ds,
        state.lattice,
        Number(state.mg),
        state.gauge
      );
      var codeAt = {};
      if (coex) {
        coex.cells.forEach(function (cell) {
          codeAt[cell[0] + "," + cell[1]] = cell[2];
        });
      }
      figure = Atlas.plot.heatmap({
        uValues: grid.u,
        tValues: grid.t,
        mode: "cat",
        catColors: COEX_COLORS,
        catLabels: COEX_LEGEND,
        label: "candidate branch overlap",
        value: function (it, iu) {
          var code = codeAt[it + "," + iu];
          return code === undefined ? null : code;
        },
        tipExtra: function (it, iu, node) {
          var code = codeAt[it + "," + iu];
          if (code !== undefined && COEX_LABELS[code]) {
            E("div", "muted", COEX_LABELS[code], node);
          }
          E("div", "muted", "click for attempt details", node);
        },
        overlay: overlay,
        overlayLabel: "candidate U*(T) crossing (below corridor)",
        onClick: function (it, iu) {
          showCellDetail(state, it, iu);
        },
      });
      /* legend colors keyed by legend codes */
      figure.el.querySelectorAll(".viz-key-rect").forEach(function (key, idx) {
        var code = Object.keys(COEX_LEGEND)[idx];
        key.style.background = COEX_LEGEND_COLORS[code];
      });
    } else {
      var nonNullCells = 0;
      for (var ti = 0; ti < grid.t.length; ti++) {
        for (var uj = 0; uj < grid.u.length; uj++) {
          if (cellValue(ds, state, ti, uj) !== null) nonNullCells++;
        }
      }
      if (!nonNullCells) {
        var blank = E("div", "panel", null, view);
        E("h2", null, "Nothing to map for this selection", blank);
        E(
          "p",
          "muted",
          state.view === "domega"
            ? "ΔΩ needs at least one (U, T) cell where BOTH a metal and " +
              "an insulator attempt converged in this gauge — this group " +
              "has none. (m_g=1 groups never do: their insulator attempts " +
              "are dark states.)"
            : "No converged " +
              (state.family === "insul" ? "insulator" : "metal") +
              " rows carry this observable in this group. Try the other " +
              "branch, another gauge, or the phase map to see what exists.",
          blank
        );
        return;
      }
      var label =
        state.view === "domega"
          ? "ΔΩ/D (blue: metal lower)"
          : viewOptions
              .filter(function (option) {
                return option.value === state.view;
              })
              .map(function (option) {
                return option.label;
              })[0] +
            (isScalar ? " · " + state.family + " branch" : "");
      figure = Atlas.plot.heatmap({
        uValues: grid.u,
        tValues: grid.t,
        mode: state.view === "domega" ? "div" : "seq",
        label: label,
        value: function (it, iu) {
          return cellValue(ds, state, it, iu);
        },
        tipExtra: function (it, iu, node) {
          E("div", "muted", "click for attempt details", node);
        },
        overlay: overlay,
        overlayLabel: "candidate U*(T) crossing (below corridor)",
        onClick: function (it, iu) {
          showCellDetail(state, it, iu);
        },
      });
    }
    panel.appendChild(figure.el);
    var actions = E("div", "chart-actions", null, panel);
    actions.appendChild(
      ui.btn("download SVG", function () {
        Atlas.plot.dlSVG(figure.svgs[0], "atlas_map");
      })
    );
    actions.appendChild(
      ui.btn("download PNG", function () {
        Atlas.plot.dlPNG(figure.svgs[0], "atlas_map");
      })
    );
  });
})();
