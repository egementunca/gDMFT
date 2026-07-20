/* Gauge: bare vs canonical-R agreement — the registered pairing evidence
   (dZ on conversion and re-optimization) plus per-gauge identity-error
   medians from the point tables. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;
  var C = Atlas.colors;

  function defaults() {
    return { lattice: "bethe", mg: null, branch: "all", t: null };
  }

  function fieldIndex(table) {
    var index = {};
    table.fields.forEach(function (name, i) {
      index[name] = i;
    });
    return index;
  }

  function median(values) {
    if (!values.length) return null;
    var sorted = values.slice().sort(function (a, b) {
      return a - b;
    });
    return sorted[Math.floor(sorted.length / 2)];
  }

  function value(row, index, field) {
    return index[field] === undefined ? null : row[index[field]];
  }

  function latticeOf(row, index) {
    var cell = String(value(row, index, "cell") || "");
    return cell.indexOf("square") === 0 ? "square" : "bethe";
  }

  function mgOf(row, index) {
    var direct = value(row, index, "m_g");
    if (direct !== null) return Number(direct);
    var match = String(value(row, index, "cell") || "").match(/_mg(\d+)/);
    return match ? Number(match[1]) : null;
  }

  function isTrue(raw) {
    return raw === true || raw === 1 || raw === "1" ||
      String(raw).toLowerCase() === "true";
  }

  Atlas.registerTab("gauge", "Gauge", function (view) {
    var state = Atlas.state.gauge || (Atlas.state.gauge = defaults());
    var ui = Atlas.ui;
    view.innerHTML = "";
    var pairing = Atlas.DATA.evidence.bare_r_pairing;
    if (!pairing) {
      E("p", "muted panel", "No pairing evidence registered.", view);
      return;
    }
    var idx = fieldIndex(pairing);
    var lattices = {};
    pairing.rows.forEach(function (row) {
      lattices[latticeOf(row, idx)] = true;
    });
    if (!lattices[state.lattice]) state.lattice = Object.keys(lattices)[0];

    var mgSet = {};
    pairing.rows.forEach(function (row) {
      if (latticeOf(row, idx) === state.lattice) {
        mgSet[mgOf(row, idx)] = true;
      }
    });
    var mgValues = Object.keys(mgSet)
      .map(Number)
      .filter(function (mg) {
        return !isNaN(mg);
      })
      .sort(function (a, b) {
        return a - b;
      });
    if (state.mg === null || mgValues.indexOf(Number(state.mg)) < 0) {
      state.mg = mgValues[0];
    }

    var branchSet = {};
    pairing.rows.forEach(function (row) {
      if (
        latticeOf(row, idx) === state.lattice &&
        mgOf(row, idx) === Number(state.mg)
      ) {
        branchSet[String(value(row, idx, "branch"))] = true;
      }
    });
    var branchValues = Object.keys(branchSet).sort();
    if (
      state.branch !== "all" &&
      branchValues.indexOf(state.branch) < 0
    ) {
      state.branch = "all";
    }

    var tSet = {};
    pairing.rows.forEach(function (row) {
      if (
        latticeOf(row, idx) === state.lattice &&
        mgOf(row, idx) === Number(state.mg) &&
        (state.branch === "all" ||
          String(value(row, idx, "branch")) === state.branch)
      ) {
        tSet[value(row, idx, "T_over_D")] = true;
      }
    });
    var tValues = Object.keys(tSet)
      .map(Number)
      .sort(function (a, b) {
        return a - b;
      });
    if (state.t === null || tValues.indexOf(state.t) < 0) {
      state.t = tValues[0];
    }

    function rerender() {
      Atlas.saveState("gauge");
      Atlas.tabs
        .filter(function (tab) {
          return tab.id === "gauge";
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
            Object.keys(lattices).map(function (value) {
              return { value: value, label: value };
            }),
            state.lattice,
            set("lattice")
          )
        ),
        ui.field(
          "M_g",
          ui.select(
            mgValues.map(function (mg) {
              return { value: mg, label: String(mg) };
            }),
            state.mg,
            set("mg", Number)
          )
        ),
        ui.field(
          "branch attempt",
          ui.select(
            [{ value: "all", label: "all branches" }].concat(
              branchValues.map(function (branch) {
                return { value: branch, label: branch };
              })
            ),
            state.branch,
            set("branch")
          )
        ),
        ui.field(
          "T/D",
          ui.select(
            tValues.map(function (value) {
              return { value: value, label: Atlas.fmt(value) };
            }),
            state.t,
            set("t", Number)
          )
        ),
      ])
    );

    var slice = pairing.rows.filter(function (row) {
      return (
        latticeOf(row, idx) === state.lattice &&
        mgOf(row, idx) === Number(state.mg) &&
        (state.branch === "all" ||
          String(value(row, idx, "branch")) === state.branch) &&
        value(row, idx, "T_over_D") === state.t
      );
    });

    /* conversion is exact (machine precision); re-optimization can move —
       log10 |dZ| for both, per U */
    var convert = [];
    var reopt = [];
    var convertValues = [];
    var reoptValues = [];
    var zeroConvert = 0;
    var zeroReopt = 0;
    var basinFlips = [];
    slice.forEach(function (row) {
      var u = value(row, idx, "U_over_D");
      var dzConvert = value(row, idx, "dZ_convert");
      var dzReopt = value(row, idx, "dZ");
      if (dzConvert !== null) {
        dzConvert = Math.abs(dzConvert);
        convertValues.push(dzConvert);
        if (dzConvert === 0) zeroConvert++;
        else convert.push([u, dzConvert]);
      }
      if (dzReopt !== null) {
        dzReopt = Math.abs(dzReopt);
        reoptValues.push(dzReopt);
        if (dzReopt === 0) zeroReopt++;
        else reopt.push([u, dzReopt]);
      }
      if (isTrue(value(row, idx, "different_basin"))) {
        basinFlips.push(row);
      }
    });
    convert.sort(function (a, b) {
      return a[0] - b[0];
    });
    reopt.sort(function (a, b) {
      return a[0] - b[0];
    });

    var summary = E("div", "panel", null, view);
    E("h2", null, "Gauge evidence, not independent-branch proof", summary);
    E(
      "p",
      null,
      slice.length +
        " matched bare roots at this slice · median |dZ| conversion: " +
        Atlas.fmt(median(convertValues)) +
        " · median |dZ| re-optimization: " +
        Atlas.fmt(median(reoptValues)) +
        " · exact-zero conversion/re-optimization: " +
        zeroConvert +
        "/" +
        zeroReopt +
        " · different-basin re-optimizations: " +
        basinFlips.length,
      summary
    );
    E(
      "p",
      "muted",
        "Bare → canonical-R conversion is an exact coordinate map; " +
        "re-optimization in R coordinates should return the same point " +
        "unless the optimizer lands in a different basin. Exact zeros are " +
        "counted above but cannot appear on the logarithmic plot.",
      summary
    );

    if (convert.length || reopt.length) {
      var panel = E("div", "panel", null, view);
      var figure = Atlas.plot.figure({
        width: 940,
        xLabel: "U/D",
        panels: [
          {
            yLabel: "|dZ|",
            yLog: true,
            height: 260,
            series: [
              {
                label: "|dZ| bare → converted (exact map)",
                color: C.cat[1],
                marker: "only",
                points: convert,
              },
              {
                label: "|dZ| bare → re-optimized",
                color: C.cat[0],
                marker: "only",
                points: reopt,
              },
            ],
          },
        ],
      });
      panel.appendChild(figure.el);
    }

    if (basinFlips.length) {
      var flipPanel = E("div", "panel", null, view);
      E("h2", null, "Different-basin re-optimizations", flipPanel);
      var scroll = E("div", "table-scroll", null, flipPanel);
      var table = E("table", "data", null, scroll);
      var head = E("tr", null, null, E("thead", null, null, table));
      ["U/D", "branch", "Z bare", "Z reopt", "basin bare", "basin reopt", "bound limited"].forEach(
        function (title) {
          E("th", "txt", title, head);
        }
      );
      var body = E("tbody", null, null, table);
      basinFlips.slice(0, 60).forEach(function (row) {
        var tr = E("tr", null, null, body);
        E("td", null, Atlas.fmt(value(row, idx, "U_over_D")), tr);
        E("td", "txt", String(value(row, idx, "branch")), tr);
        E("td", null, Atlas.fmt(value(row, idx, "Z_bare")), tr);
        E("td", null, Atlas.fmt(value(row, idx, "Z_reopt")), tr);
        E("td", "txt", String(value(row, idx, "basin_bare")), tr);
        E("td", "txt", String(value(row, idx, "basin_reopt")), tr);
        E("td", "txt", String(value(row, idx, "bound_limited")), tr);
      });
    }

    /* per-dataset per-gauge identity-error medians from the point tables */
    var errorPanel = E("div", "panel", null, view);
    E("h2", null, "Canonical-map identity errors (point tables)", errorPanel);
    var scroll2 = E("div", "table-scroll", null, errorPanel);
    var table2 = E("table", "data", null, scroll2);
    var head2 = E("tr", null, null, E("thead", null, null, table2));
    ["dataset", "gauge", "rows", "median norm err", "median closure err", "median roundtrip err"].forEach(
      function (title) {
        E("th", "txt", title, head2);
      }
    );
    var body2 = E("tbody", null, null, table2);
    Atlas.store.pointIds().forEach(function (dsId) {
      var ds = Atlas.store.ds(dsId);
      ds.dictOf("gauge").forEach(function (gauge) {
        var errors = { norm_err: [], closure_err: [], roundtrip_err: [] };
        var count = 0;
        for (var i = 0; i < ds.n; i++) {
          if (ds.str("gauge", i) !== gauge) continue;
          if (ds.lattice(i) !== state.lattice) continue;
          if (ds.num("m_g", i) !== Number(state.mg)) continue;
          if (Math.abs(ds.t(i) - state.t) > 1e-12) continue;
          if (
            state.branch !== "all" &&
            ds.str("family", i) !== state.branch
          ) {
            continue;
          }
          count++;
          Object.keys(errors).forEach(function (key) {
            var value = ds.num(key, i);
            if (value !== null) errors[key].push(value);
          });
        }
        if (!count) return;
        var tr = E("tr", null, null, body2);
        E("td", "txt", dsId.indexOf("gauge-matrix") >= 0 ? "v1" : "v2", tr);
        E("td", "txt", gauge, tr);
        E("td", null, String(count), tr);
        ["norm_err", "closure_err", "roundtrip_err"].forEach(function (key) {
          E("td", null, Atlas.fmt(median(errors[key])), tr);
        });
      });
    });
  });
})();
