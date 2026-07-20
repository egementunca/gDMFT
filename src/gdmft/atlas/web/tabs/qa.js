/* QA: gate ledger (unknown ≠ false), column coverage, grid coverage,
   residual distributions, unresolved-conditions browser, derivation notes. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;
  var C = Atlas.colors;

  var GATE_LABELS = {
    solver_succeeded: "solver succeeded",
    equations_accepted: "equations accepted",
    density_consistent: "density consistent",
    physical_guards_clear: "physical guards clear",
    bounds_clear: "bounds clear",
    continuity_passed: "continuity passed",
    physically_admissible: "physically admissible",
    selected: "selected",
  };

  function gatePanel(view) {
    var panel = E("div", "panel", null, view);
    E("h2", null, "Gate ledger", panel);
    E(
      "p",
      "muted",
      "Contract rule: unknown ≠ false. A null gate has not been evaluated; " +
        "it is rendered as its own state, never merged with a failure.",
      panel
    );
    Atlas.store.pointIds().forEach(function (dsId) {
      var gates = Atlas.DATA.datasets[dsId].gates;
      E("h3", null, dsId, panel);
      var table = E("table", "data", null, panel);
      var head = E("tr", null, null, E("thead", null, null, table));
      ["gate", "true", "false", "unknown"].forEach(function (title) {
        E("th", "txt", title, head);
      });
      var body = E("tbody", null, null, table);
      Object.keys(GATE_LABELS).forEach(function (gate) {
        var counts = gates[gate];
        var row = E("tr", null, null, body);
        E("td", "txt", GATE_LABELS[gate], row);
        E("td", null, String(counts["true"]), row);
        E("td", null, String(counts["false"]), row);
        E("td", null, String(counts["null"]), row);
      });
    });
  }

  function coveragePanel(view) {
    var panel = E("div", "panel", null, view);
    E("h2", null, "Column coverage (non-null rows)", panel);
    var ids = Atlas.store.pointIds();
    var names = {};
    ids.forEach(function (dsId) {
      Object.keys(Atlas.DATA.datasets[dsId].nonnull).forEach(function (name) {
        names[name] = true;
      });
    });
    var scroll = E("div", "table-scroll", null, panel);
    var table = E("table", "data", null, scroll);
    var head = E("tr", null, null, E("thead", null, null, table));
    E("th", "txt", "column", head);
    ids.forEach(function (dsId) {
      E("th", "txt", dsId.indexOf("gauge-matrix") >= 0 ? "v1" : "v2", head);
    });
    var body = E("tbody", null, null, table);
    Object.keys(names)
      .sort()
      .forEach(function (name) {
        var row = E("tr", null, null, body);
        E("td", "txt", name, row);
        ids.forEach(function (dsId) {
          var dataset = Atlas.DATA.datasets[dsId];
          var count = dataset.nonnull[name];
          var cell = E(
            "td",
            null,
            count === undefined ? "—" : count + " / " + dataset.n,
            row
          );
          if (count === 0) cell.className = "muted";
        });
      });
    ids.forEach(function (dsId) {
      var dropped = Atlas.DATA.datasets[dsId].cols_dropped;
      if (dropped.length) {
        E(
          "p",
          "muted",
          (dsId.indexOf("gauge-matrix") >= 0 ? "v1" : "v2") +
            " columns not recorded (dropped from the payload): " +
            dropped.join(", "),
          panel
        );
      }
    });
  }

  function residualPanel(view) {
    var panel = E("div", "panel", null, view);
    E("h2", null, "Residual-norm distribution (log10, converged rows)", panel);
    var seriesList = [];
    Atlas.store.pointIds().forEach(function (dsId, index) {
      var ds = Atlas.store.ds(dsId);
      var logs = [];
      for (var i = 0; i < ds.n; i++) {
        if (!ds.converged(i)) continue;
        var value = ds.num("resnorm", i);
        if (value !== null && value > 0) logs.push(Math.log10(value));
      }
      if (!logs.length) return;
      var lo = Math.min.apply(null, logs);
      var hi = Math.max.apply(null, logs);
      var bins = 36;
      var width = (hi - lo) / bins || 1;
      var counts = [];
      for (var b = 0; b < bins; b++) counts.push(0);
      logs.forEach(function (value) {
        var bin = Math.min(bins - 1, Math.floor((value - lo) / width));
        counts[bin]++;
      });
      seriesList.push({
        label: (dsId.indexOf("gauge-matrix") >= 0 ? "v1" : "v2") +
          " (" + logs.length + " rows)",
        color: C.cat[index % C.cat.length],
        marker: "none",
        points: counts.map(function (count, b) {
          return [lo + (b + 0.5) * width, count];
        }),
      });
    });
    var figure = Atlas.plot.figure({
      width: 940,
      xLabel: "log10 residual norm",
      panels: [{ yLabel: "rows / bin", height: 220, series: seriesList }],
    });
    panel.appendChild(figure.el);
  }

  function unresolvedPanel(view) {
    var unresolved = Atlas.DATA.evidence.unresolved;
    if (!unresolved) return;
    var panel = E("div", "panel", null, view);
    E(
      "h2",
      null,
      "Unresolved conditions (registered evidence, " +
        unresolved.rows.length +
        " rows)",
      panel
    );
    var index = {};
    unresolved.fields.forEach(function (name, i) {
      index[name] = i;
    });
    var reasons = {};
    unresolved.rows.forEach(function (row) {
      var reason = String(row[index.reason] || "—");
      reasons[reason] = (reasons[reason] || 0) + 1;
    });
    var reasonTable = E("table", "data", null, panel);
    var head = E("tr", null, null, E("thead", null, null, reasonTable));
    E("th", "txt", "reason", head);
    E("th", null, "rows", head);
    var body = E("tbody", null, null, reasonTable);
    Object.keys(reasons)
      .sort(function (a, b) {
        return reasons[b] - reasons[a];
      })
      .forEach(function (reason) {
        var row = E("tr", null, null, body);
        E("td", "txt", reason, row);
        E("td", null, String(reasons[reason]), row);
      });
    var details = E("details", null, null, panel);
    E("summary", null, "all rows", details);
    var scroll = E("div", "table-scroll", null, details);
    var table = E("table", "data", null, scroll);
    var head2 = E("tr", null, null, E("thead", null, null, table));
    unresolved.fields.forEach(function (name) {
      E("th", "txt", name, head2);
    });
    var body2 = E("tbody", null, null, table);
    unresolved.rows.forEach(function (rowValues) {
      var row = E("tr", null, null, body2);
      rowValues.forEach(function (value) {
        E(
          "td",
          typeof value === "number" ? null : "txt",
          value === null ? "—" : typeof value === "number" ? Atlas.fmt(value) : String(value),
          row
        );
      });
    });
  }

  function evidenceTables(view) {
    [
      ["coverage_after", "Grid coverage after v2 (registered evidence)"],
      ["mg1_bound", "m_g=1 bound-expansion test (registered evidence)"],
      ["stage3_audit", "Stage-3 archive audit (registered evidence)"],
    ].forEach(function (item) {
      var tableData = Atlas.DATA.evidence[item[0]];
      if (!tableData) return;
      var panel = E("div", "panel", null, view);
      E("h2", null, item[1], panel);
      var scroll = E("div", "table-scroll", null, panel);
      var table = E("table", "data", null, scroll);
      var head = E("tr", null, null, E("thead", null, null, table));
      tableData.fields.forEach(function (name) {
        E("th", "txt", name, head);
      });
      var body = E("tbody", null, null, table);
      tableData.rows.forEach(function (rowValues) {
        var row = E("tr", null, null, body);
        rowValues.forEach(function (value) {
          E(
            "td",
            typeof value === "number" ? null : "txt",
            value === null
              ? "—"
              : typeof value === "number"
                ? Atlas.fmt(value)
                : String(value),
            row
          );
        });
      });
      E(
        "p",
        "muted",
        "Source: " +
          tableData.source.path +
          " · sha256 " +
          tableData.source.sha256.slice(0, 12) +
          "…",
        panel
      );
    });
  }

  function reportPanel(view) {
    var report = Atlas.DATA.derived.report;
    var panel = E("div", "panel", null, view);
    E("h2", null, "Derivation anomaly report (" + report.length + ")", panel);
    var list = E("ul", "report-list", null, panel);
    report.forEach(function (line) {
      E("li", null, line, list);
    });
  }

  Atlas.registerTab("qa", "QA", function (view) {
    gatePanel(view);
    coveragePanel(view);
    residualPanel(view);
    unresolvedPanel(view);
    evidenceTables(view);
    reportPanel(view);
  });
})();
