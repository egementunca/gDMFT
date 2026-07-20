/* Overview: provenance from manifests, headline U*(T) diagnostics,
   claim ledger, derive-report summary. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;

  function firstDefined(values) {
    for (var i = 0; i < values.length; i++) {
      if (values[i] !== undefined && values[i] !== null && values[i] !== "") {
        return values[i];
      }
    }
    return null;
  }

  function catalogEntries() {
    var references = Atlas.DATA.references || {};
    var meta = Atlas.DATA.meta || {};
    var catalog =
      references.catalog ||
      references.reference_catalog ||
      Atlas.DATA.reference_catalog ||
      meta.reference_catalog;
    if (!catalog) return [];
    if (Array.isArray(catalog)) return catalog;
    var list =
      catalog.entries ||
      catalog.datasets ||
      catalog.references ||
      catalog.tables;
    if (Array.isArray(list)) return list;
    return Object.keys(catalog)
      .filter(function (key) {
        return catalog[key] && typeof catalog[key] === "object";
      })
      .map(function (key) {
        var entry = Object.assign({}, catalog[key]);
        if (!entry.id && !entry.dataset_id) entry.id = key;
        return entry;
      });
  }

  function catalogEntryFor(datasetId) {
    var entries = catalogEntries();
    for (var i = 0; i < entries.length; i++) {
      var id = firstDefined([
        entries[i].dataset_id,
        entries[i].reference_id,
        entries[i].id,
      ]);
      if (id === datasetId) return entries[i];
    }
    return null;
  }

  function countFrom(entry) {
    if (!entry) return null;
    var direct = firstDefined([
      entry.row_count,
      entry.rows,
      entry.n_rows,
      entry.n,
    ]);
    if (typeof direct === "number") return direct;
    var tables = entry.tables || entry.artifacts;
    if (!Array.isArray(tables)) return null;
    var total = 0;
    var found = false;
    tables.forEach(function (table) {
      var rows = firstDefined([
        table.row_count,
        table.rows,
        table.n_rows,
        table.n,
      ]);
      if (typeof rows === "number") {
        total += rows;
        found = true;
      }
    });
    return found ? total : null;
  }

  function datasetCount(ds, catalogEntry) {
    if (Atlas.DATA.datasets[ds.id]) return Atlas.DATA.datasets[ds.id].n;
    var own = countFrom(ds);
    if (own !== null) return own;
    var catalogCount = countFrom(catalogEntry);
    if (catalogCount !== null) return catalogCount;
    var gem = (Atlas.DATA.references || {}).gem;
    if (gem && ds.id.indexOf("gem") >= 0) return gem.n;
    if (ds.id.indexOf("benchmarks") >= 0) {
      var refs = Atlas.DATA.references || {};
      var total = 0;
      var found = false;
      ["nrg", "professor_gga", "ctqmc"].forEach(function (key) {
        if (refs[key] && typeof refs[key].n === "number") {
          total += refs[key].n;
          found = true;
        }
      });
      if (found) return total;
    }
    return null;
  }

  function availability(ds, catalogEntry) {
    if (Atlas.DATA.datasets[ds.id]) return "point rows loaded";
    if ((Atlas.DATA.references || {}).gem && ds.id.indexOf("gem") >= 0) {
      return "reference curves loaded";
    }
    if (
      ds.id.indexOf("benchmarks") >= 0 &&
      (Atlas.DATA.references || {}).nrg
    ) {
      return "dedicated source tables loaded";
    }
    if (catalogEntry) {
      return catalogEntry.loaded === false
        ? "catalog only"
        : "catalog metadata loaded";
    }
    return "registered metadata only";
  }

  function datasetPanel(view) {
    var panel = E("div", "panel", null, view);
    E("h2", null, "Registered datasets", panel);
    E(
      "p",
      "muted",
      "Counts are shown only when that dataset or its registered catalog " +
        "supplies them. A dash means the atlas did not load the rows; it " +
        "does not mean zero.",
      panel
    );
    var scroll = E("div", "table-scroll", null, panel);
    var table = E("table", "data", null, scroll);
    var head = E("tr", null, null, E("thead", null, null, table));
    ["dataset", "version", "kind", "stage", "rows", "availability", "source revision", "selection"].forEach(
      function (title) {
        E("th", "txt", title, head);
      }
    );
    var body = E("tbody", null, null, table);
    Atlas.DATA.meta.datasets.forEach(function (ds) {
      var catalogEntry = catalogEntryFor(ds.id);
      var row = E("tr", null, null, body);
      var idCell = E("td", "txt", null, row);
      E("strong", null, ds.id, idCell);
      E("div", "muted", ds.title, idCell);
      E("td", "txt", ds.version, row);
      E("td", "txt", ds.kind, row);
      E("td", "txt", ds.data_stage + " / " + ds.release_status, row);
      var n = datasetCount(ds, catalogEntry);
      E("td", null, n === null ? "—" : String(n), row);
      E("td", "txt", availability(ds, catalogEntry), row);
      E(
        "td",
        "txt",
        ds.revision
          ? ds.revision.slice(0, 8) + (ds.dirty ? " (dirty)" : "")
          : "—",
        row
      );
      E("td", "txt", ds.selection_status || "—", row);
    });
    var sources = [];
    Atlas.DATA.meta.datasets.forEach(function (ds) {
      (ds.external_sources || []).forEach(function (source) {
        var text = source.id + " @ " + source.revision.slice(0, 16);
        if (sources.indexOf(text) < 0) sources.push(text);
      });
    });
    if (sources.length) {
      E(
        "p",
        "muted",
        "External sources: " + sources.join(" · "),
        panel
      );
    }
  }

  function catalogPanel(view) {
    var entries = catalogEntries();
    if (!entries.length) return;
    var panel = E("div", "panel", null, view);
    E("h2", null, "Reference catalog", panel);
    E(
      "p",
      "muted",
      "This is an inventory of registered comparison material. Catalog " +
        "presence does not mean a curve is currently plotted.",
      panel
    );
    var scroll = E("div", "table-scroll", null, panel);
    var table = E("table", "data", null, scroll);
    var head = E("tr", null, null, E("thead", null, null, table));
    ["reference", "methods", "tables / artifacts", "rows", "status"].forEach(
      function (title) {
        E("th", "txt", title, head);
      }
    );
    var body = E("tbody", null, null, table);
    entries.forEach(function (entry) {
      var id = firstDefined([
        entry.dataset_id,
        entry.reference_id,
        entry.id,
        entry.title,
      ]);
      var methods = entry.methods || entry.method || [];
      if (!Array.isArray(methods)) methods = [methods];
      var artifacts = entry.tables || entry.artifacts || [];
      var artifactCount = Array.isArray(artifacts)
        ? artifacts.length
        : firstDefined([entry.artifact_count, entry.table_count]);
      var count = countFrom(entry);
      var tr = E("tr", null, null, body);
      E("td", "txt", id || "—", tr);
      E("td", "txt", methods.length ? methods.join(", ") : "—", tr);
      E(
        "td",
        null,
        artifactCount === null || artifactCount === undefined
          ? "—"
          : String(artifactCount),
        tr
      );
      E("td", null, count === null ? "—" : String(count), tr);
      E(
        "td",
        "txt",
        firstDefined([
          entry.availability,
          entry.status,
          entry.release_status,
          entry.loaded === false ? "catalog only" : null,
        ]) || "cataloged",
        tr
      );
    });
  }

  function populationCatalogPanel(view) {
    var catalog = Atlas.DATA.catalog;
    if (!catalog || !catalog.datasets) return;
    var panel = E("div", "panel", null, view);
    E("h2", null, "Primary-population catalog", panel);
    E(
      "div",
      "caveat",
      "The catalog chooses one source route per (lattice, M_g), but " +
        "thermodynamic branch selection is still " +
        (catalog.selection_status || "unknown") +
        ". Its default rows are numerically accepted source rows, not a " +
        "publication-ready physical selection.",
      panel
    );
    E(
      "p",
      "muted",
      String(catalog.default_physics_count || 0) +
        " rows satisfy the declared primary route, source-status, and " +
        "quadrature rules.",
      panel
    );
    var scroll = E("div", "table-scroll", null, panel);
    var table = E("table", "data", null, scroll);
    var head = E("tr", null, null, E("thead", null, null, table));
    [
      "dataset",
      "primary-physics attempts",
      "gauge evidence",
      "exact converted views",
      "supplementary",
      "default accepted rows",
      "quadrature status",
    ].forEach(function (title) {
      E("th", "txt", title, head);
    });
    var body = E("tbody", null, null, table);
    Object.keys(catalog.datasets)
      .sort()
      .forEach(function (datasetId) {
        var entry = catalog.datasets[datasetId];
        var roles = entry.role_counts || {};
        var quadrature = entry.quadrature_counts || {};
        var row = E("tr", null, null, body);
        E("td", "txt", datasetId, row);
        E("td", null, String(roles["primary-physics"] || 0), row);
        E("td", null, String(roles["gauge-evidence"] || 0), row);
        E("td", null, String(roles["excluded-representation"] || 0), row);
        E("td", null, String(roles.supplementary || 0), row);
        E("td", null, String(entry.default_row_count || 0), row);
        E(
          "td",
          "txt",
          Object.keys(quadrature)
            .sort()
            .map(function (key) {
              return key + ": " + quadrature[key];
            })
            .join(" · ") || "—",
          row
        );
      });
    var routes =
      catalog.policy && Array.isArray(catalog.policy.routes)
        ? catalog.policy.routes
        : [];
    if (routes.length) {
      var details = E("details", null, null, panel);
      E("summary", null, "show declared primary routes", details);
      var routeList = E("ul", "report-list", null, details);
      routes.forEach(function (route) {
        E(
          "li",
          null,
          route.lattice +
            " · M_g=" +
            route.m_g +
            " → " +
            route.dataset_id +
            " · " +
            route.gauge +
            " · " +
            route.quadrature,
          routeList
        );
      });
    }
  }

  function referenceAvailabilityPanel(view) {
    var refs = Atlas.DATA.references || {};
    var entries = [];
    if (refs.gem) {
      entries.push({
        name: "gem / gGA",
        rows: refs.gem.n,
        scope: "finite-T matched curves",
        status: "loaded",
      });
    }
    var ed = refs.ed || {};
    ["v2", "v1_legacy"].forEach(function (key) {
      if (!ed[key]) return;
      entries.push({
        name: key === "v2" ? "DMFT-ED D09" : "DMFT-ED D08 legacy",
        rows: firstDefined([ed[key].n, ed[key].rows && ed[key].rows.length]),
        scope:
          firstDefined([
            ed[key].status,
            ed[key].availability &&
              ed[key].availability.temperature_semantics &&
              ed[key].availability.temperature_semantics.join(", "),
          ]) || "T=0 anchors",
        status: key === "v2" ? "current evidence" : "legacy; kept separate",
      });
    });
    [
      ["nrg", "NRG thermal"],
      ["professor_gga", "professor gGA"],
      ["ctqmc", "LLK CTQMC anchor"],
    ].forEach(function (item) {
      var reference = refs[item[0]];
      if (!reference) return;
      entries.push({
        name: item[1],
        rows: reference.n,
        scope:
          reference.availability &&
          reference.availability.source_of_truth
            ? reference.availability.source_of_truth
            : "registered source table",
        status: "loaded",
      });
    });
    if (!entries.length) return;
    var panel = E("div", "panel", null, view);
    E("h2", null, "Loaded comparison tables", panel);
    E(
      "p",
      "muted",
      "These counts describe the individual tables in the atlas payload. " +
        "They are not added to the single-site attempt counts above.",
      panel
    );
    var scroll = E("div", "table-scroll", null, panel);
    var table = E("table", "data", null, scroll);
    var head = E("tr", null, null, E("thead", null, null, table));
    ["method / source", "rows", "scope / source table", "status"].forEach(
      function (title) {
        E("th", "txt", title, head);
      }
    );
    var body = E("tbody", null, null, table);
    entries.forEach(function (entry) {
      var row = E("tr", null, null, body);
      E("td", "txt", entry.name, row);
      E("td", null, entry.rows === null ? "—" : String(entry.rows), row);
      E("td", "txt", entry.scope, row);
      E("td", "txt", entry.status, row);
    });
  }

  function groupsWithCrossings() {
    var seen = {};
    var groups = [];
    Atlas.DATA.derived.ustar.forEach(function (entry) {
      var key = [entry.ds, entry.lattice, entry.m_g, entry.gauge].join("|");
      if (!seen[key]) {
        seen[key] = { key: key, entry: entry, crossed: 0 };
        groups.push(seen[key]);
      }
      if (entry.status === "crossed" || entry.status === "multiple_crossings") {
        seen[key].crossed++;
      }
    });
    return groups.filter(function (group) {
      return group.crossed > 0;
    });
  }

  function ustarPanel(view) {
    var panel = E("div", "panel", null, view);
    E("h2", null, "Candidate U*(T) crossing diagnostics", panel);
    E(
      "div",
      "caveat",
      "Provisional diagnostic, not a phase boundary. It uses converged " +
        "attempt labels on shared support; physical guards, continuity, " +
        "admissibility, and branch selection are not complete.",
      panel
    );
    E(
      "p",
      "muted",
      "The candidate is interpolated where Ω_metal/D − Ω_insul/D changes " +
        "sign. Use it to inspect branch overlap, not to quote Uc or U*.",
      panel
    );
    var groups = groupsWithCrossings();
    if (!groups.length) {
      E("p", "muted", "No crossings found.", panel);
      return;
    }
    var state = Atlas.state.overview || (Atlas.state.overview = {});
    if (!state.group || !groups.some(function (g) { return g.key === state.group; })) {
      /* prefer the headline group: v1 bethe m_g=3 bare */
      var preferred = groups.filter(function (group) {
        return (
          group.entry.lattice === "bethe" &&
          group.entry.m_g === 3 &&
          group.entry.gauge === "bare"
        );
      });
      state.group = (preferred[0] || groups[0]).key;
    }
    var holder = E("div", null, null, panel);
    function renderTable() {
      holder.innerHTML = "";
      var parts = state.group.split("|");
      var entries = Atlas.DATA.derived.ustar
        .filter(function (entry) {
          return (
            entry.ds === parts[0] &&
            entry.lattice === parts[1] &&
            String(entry.m_g) === parts[2] &&
            entry.gauge === parts[3]
          );
        })
        .sort(function (a, b) {
          return a.t - b.t;
        });
      var table = E("table", "data", null, holder);
      var head = E("tr", null, null, E("thead", null, null, table));
      ["T/D", "U*/D", "status", "overlap points"].forEach(function (title) {
        E("th", null, title, head);
      });
      var body = E("tbody", null, null, table);
      entries.forEach(function (entry) {
        var row = E("tr", null, null, body);
        E("td", null, Atlas.fmt(entry.t), row);
        E(
          "td",
          null,
          entry.ustar !== undefined ? Atlas.fmt(entry.ustar) : "—",
          row
        );
        E("td", "txt", entry.status, row);
        E("td", null, String(entry.n_overlap), row);
      });
    }
    var selector = Atlas.ui.select(
      groups.map(function (group) {
        var e = group.entry;
        return {
          value: group.key,
          label:
            e.ds +
            " · " +
            e.lattice +
            " · m_g=" +
            e.m_g +
            " · " +
            e.gauge +
            " (" +
            group.crossed +
            " T rows)",
        };
      }),
      state.group,
      function (value) {
        state.group = value;
        Atlas.saveState("overview");
        renderTable();
      }
    );
    panel.insertBefore(
      Atlas.ui.row([Atlas.ui.field("branch pair", selector)]),
      holder
    );
    renderTable();
  }

  function claimPanel(view) {
    var ledger = Atlas.DATA.evidence.claim_ledger;
    if (!ledger) return;
    var panel = E("div", "panel", null, view);
    E("h2", null, "Claim ledger (registered evidence)", panel);
    var table = E("table", "data", null, panel);
    var head = E("tr", null, null, E("thead", null, null, table));
    ledger.fields.forEach(function (field) {
      E("th", "txt", field, head);
    });
    var body = E("tbody", null, null, table);
    ledger.rows.forEach(function (rowValues) {
      var row = E("tr", null, null, body);
      rowValues.forEach(function (value) {
        E("td", "txt", value === null ? "—" : String(value), row);
      });
    });
    E(
      "p",
      "muted",
      "Source: " + ledger.source.path + " · sha256 " +
        ledger.source.sha256.slice(0, 12) + "…",
      panel
    );
  }

  function reportPanel(view) {
    var report = Atlas.DATA.derived.report;
    var panel = E("div", "panel", null, view);
    E("h2", null, "Derivation notes (" + report.length + ")", panel);
    var details = E("details", null, null, panel);
    E("summary", null, "show all notes", details);
    var list = E("ul", "report-list", null, details);
    report.forEach(function (line) {
      E("li", null, line, list);
    });
  }

  Atlas.registerTab("overview", "Overview", function (view) {
    datasetPanel(view);
    populationCatalogPanel(view);
    referenceAvailabilityPanel(view);
    catalogPanel(view);
    ustarPanel(view);
    claimPanel(view);
    reportPanel(view);
  });
})();
