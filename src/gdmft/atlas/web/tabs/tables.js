/* Tables: filtered row browser over any point dataset, column chooser,
   sort, CSV export of the current selection. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;

  var RENDER_CAP = 400;

  var COLUMN_GROUPS = [
    {
      label: "identity",
      keys: [
        "pid",
        "run",
        "family",
        "gauge",
        "solver",
        "cell",
        "campaign",
        "evidence_type",
      ],
    },
    {
      label: "axes",
      keys: ["_lattice", "m_h", "_mg", "_u", "_t", "n_modes"],
    },
    {
      label: "observables",
      keys: [
        "z_pole",
        "z_from_r",
        "z_mats",
        "docc",
        "density",
        "omega_d",
        "ekin_d",
        "epot_d",
        "etot_d",
        "lam_red_d",
        "r_red",
        "resnorm",
        "norm_err",
        "closure_err",
        "roundtrip_err",
      ],
    },
    {
      label: "pole parameters",
      keys: [
        "p_v0",
        "p_v1",
        "p_eps1",
        "p_w",
        "p_w_gateway",
        "p_eta",
        "p_eta_gateway",
        "p_lam",
        "p_lam_gateway",
        "p_sumv2",
        "p_sumw2",
        "p_sumw2_gateway",
      ],
    },
    {
      label: "gates",
      keys: [
        "ok",
        "eq_ok",
        "density_ok",
        "guards_ok",
        "bounds_ok",
        "cont_ok",
        "admissible",
        "selected",
        "category",
        "src_converged",
        "floor_limited",
        "active_bound",
        "basin",
        "direction",
      ],
    },
    {
      label: "provenance",
      keys: [
        "sel_reason",
        "quadrature",
        "quad_nodes",
        "dos_nodes",
        "code_rev",
        "dirty",
      ],
    },
  ];
  var LABELS = {
    _lattice: "lattice",
    _mg: "m_g",
    _u: "U/D",
    _t: "T/D",
    pid: "point id",
    run: "run",
    family: "family",
    gauge: "gauge",
    solver: "solver",
    cell: "cell",
    campaign: "campaign",
    m_h: "m_h",
    n_modes: "canonical modes",
    ok: "solver ok",
    eq_ok: "equations",
    density_ok: "density ok",
    guards_ok: "guards",
    bounds_ok: "bounds",
    cont_ok: "continuity",
    admissible: "admissible",
    selected: "selected",
    category: "category",
    src_converged: "converged",
    floor_limited: "floor limited",
    active_bound: "active bound",
    basin: "basin",
    evidence_type: "evidence",
    direction: "direction",
    sel_reason: "selection reason",
    quadrature: "quadrature",
    quad_nodes: "quadrature nodes",
    dos_nodes: "DOS nodes",
    code_rev: "code revision",
    dirty: "dirty state",
  };
  var DEFAULT_COLUMNS = [
    "pid",
    "_lattice",
    "_mg",
    "family",
    "gauge",
    "evidence_type",
    "_u",
    "_t",
    "z_pole",
    "docc",
    "omega_d",
    "resnorm",
    "category",
    "src_converged",
    "quadrature",
    "quad_nodes",
    "code_rev",
  ];

  function columnLabel(key) {
    if (LABELS[key]) return LABELS[key];
    var qty = Atlas.store.qty(key);
    return qty ? qty.label : key;
  }

  function cellValue(ds, key, i) {
    if (key === "_lattice") return ds.lattice(i);
    if (key === "_mg") return ds.num("m_g", i);
    if (key === "_u") return ds.u(i);
    if (key === "_t") return ds.t(i);
    var qty = Atlas.store.qty(key);
    if (qty) return ds.num(key, i);
    if (
      [
        "ok",
        "eq_ok",
        "density_ok",
        "guards_ok",
        "bounds_ok",
        "cont_ok",
        "admissible",
        "selected",
        "src_converged",
        "floor_limited",
        "active_bound",
      ].indexOf(key) >= 0
    ) {
      var tri = ds.tri(key, i);
      return tri === 1 ? "true" : tri === 0 ? "false" : "unknown";
    }
    if (
      ["m_h", "n_modes", "quad_nodes", "dos_nodes"].indexOf(key) >= 0
    ) {
      return ds.num(key, i);
    }
    return ds.str(key, i);
  }

  function availableColumns(ds) {
    var keys = [];
    COLUMN_GROUPS.forEach(function (group) {
      group.keys.forEach(function (key) {
        if (key.charAt(0) === "_" || ds.has(key)) keys.push(key);
      });
    });
    return keys;
  }

  function applyPrimaryTableRoute(state) {
    var lattices = Atlas.store.primaryLattices();
    var lattice = state.filters.lattice;
    if (lattices.indexOf(lattice) < 0) {
      lattice = lattices.indexOf("bethe") >= 0 ? "bethe" : lattices[0];
      state.filters.lattice = lattice;
    }
    var mgs = Atlas.store.primaryMgValues(lattice);
    var mg = Number(state.filters.m_g);
    if (mgs.indexOf(mg) < 0) {
      mg = mgs.indexOf(3) >= 0 ? 3 : mgs[0];
      state.filters.m_g = String(mg);
    }
    var route = Atlas.store.primaryRoute(lattice, mg);
    if (!route) return null;
    state.ds = route.dataset_id;
    state.filters.gauge = route.gauge;
    return route;
  }

  function defaults() {
    var state = {
      ds: null,
      filters: { lattice: "bethe", m_g: "3", gauge: "bare" },
      convergedOnly: false,
      columns: DEFAULT_COLUMNS.slice(),
      sort: "_u",
      dir: 1,
      supplementarySource: false,
    };
    applyPrimaryTableRoute(state);
    return state;
  }

  Atlas.registerTab("tables", "Tables", function (view) {
    var state = Atlas.state.tables || (Atlas.state.tables = defaults());
    if (!state.supplementarySource) applyPrimaryTableRoute(state);
    var ds = Atlas.store.ds(state.ds);
    var ui = Atlas.ui;

    function rerender() {
      Atlas.saveState("tables");
      Atlas.tabs
        .filter(function (tab) {
          return tab.id === "tables";
        })[0]
        .render(view);
    }
    view.innerHTML = "";

    /* ---- filter row ---- */
    function filterSelect(key, dict) {
      var options = [{ value: "", label: "all" }].concat(
        dict.map(function (value) {
          return { value: value, label: value };
        })
      );
      return ui.field(
        key,
        ui.select(options, state.filters[key] || "", function (value) {
          state.filters[key] = value;
          rerender();
        })
      );
    }
    var controls = [];
    if (state.supplementarySource) {
      controls.push(
        ui.field(
          "evidence dataset",
          ui.select(
            Atlas.store.pointIds().map(function (id) {
              return { value: id, label: Atlas.store.dsLabel(id) };
            }),
            state.ds,
            function (value) {
              state.ds = value;
              state.filters = {};
              rerender();
            }
          )
        ),
        filterSelect("lattice", ds.dictOf("lattice")),
        ui.field(
          "m_g",
          ui.select(
            [{ value: "", label: "all" }].concat(
              ds.mgValues().map(function (value) {
                return { value: value, label: String(value) };
              })
            ),
            state.filters.m_g || "",
            function (value) {
              state.filters.m_g = value;
              rerender();
            }
          )
        ),
        filterSelect("gauge", ds.dictOf("gauge"))
      );
    } else {
      controls.push(
        ui.field(
          "lattice",
          ui.select(
            Atlas.store.primaryLattices().map(function (value) {
              return { value: value, label: value };
            }),
            state.filters.lattice,
            function (value) {
              state.filters.lattice = value;
              applyPrimaryTableRoute(state);
              rerender();
            }
          )
        ),
        ui.field(
          "m_g",
          ui.select(
            Atlas.store
              .primaryMgValues(state.filters.lattice)
              .map(function (value) {
                return { value: value, label: String(value) };
              }),
            state.filters.m_g,
            function (value) {
              state.filters.m_g = value;
              applyPrimaryTableRoute(state);
              rerender();
            }
          )
        )
      );
    }
    controls.push(
      filterSelect("family", ds.dictOf("family")),
      ui.check(
        "show supplementary sources",
        !!state.supplementarySource,
        function (value) {
          state.supplementarySource = value;
          if (!value) applyPrimaryTableRoute(state);
          rerender();
        }
      )
    );
    ["solver", "campaign", "evidence_type", "quadrature"].forEach(
      function (key) {
        if (ds.has(key)) controls.push(filterSelect(key, ds.dictOf(key)));
      }
    );
    if (ds.has("category")) {
      controls.push(filterSelect("category", ds.dictOf("category")));
    }
    if (ds.has("basin")) {
      controls.push(filterSelect("basin", ds.dictOf("basin")));
    }
    controls.push(
      ui.check("converged only", state.convergedOnly, function (value) {
        state.convergedOnly = value;
        rerender();
      })
    );
    view.appendChild(ui.row(controls));
    E(
      "p",
      "muted ds-note",
      (state.supplementarySource
        ? "Supplementary evidence source: "
        : "Automatic primary source: ") +
        Atlas.store.dsLabel(state.ds) +
        (state.supplementarySource
          ? " · raw source rows"
          : " · " + state.filters.gauge + " route"),
      view
    );

    /* ---- column chooser ---- */
    var chooser = E("details", "panel column-chooser", null, view);
    E("summary", null, "columns (" + state.columns.length + " shown)", chooser);
    COLUMN_GROUPS.forEach(function (group) {
      var groupBox = E("div", "column-group", null, chooser);
      E("span", "field-label", group.label, groupBox);
      group.keys.forEach(function (key) {
        if (key.charAt(0) !== "_" && !ds.has(key)) return;
        groupBox.appendChild(
          ui.check(columnLabel(key), state.columns.indexOf(key) >= 0, function (
            checked
          ) {
            if (checked && state.columns.indexOf(key) < 0) {
              state.columns.push(key);
            }
            if (!checked) {
              state.columns = state.columns.filter(function (existing) {
                return existing !== key;
              });
            }
            rerender();
          })
        );
      });
    });

    /* ---- row selection ---- */
    var rows = [];
    for (var i = 0; i < ds.n; i++) {
      var keep = true;
      for (var key in state.filters) {
        var want = state.filters[key];
        if (!want) continue;
        var got = key === "m_g" ? ds.num("m_g", i) : ds.str(key, i);
        if (String(got) !== String(want)) {
          keep = false;
          break;
        }
      }
      if (keep && state.convergedOnly && !ds.converged(i)) keep = false;
      if (keep) rows.push(i);
    }
    var columns = state.columns.filter(function (key) {
      return key.charAt(0) === "_" || ds.has(key);
    });
    var sortKey = columns.indexOf(state.sort) >= 0 ? state.sort : "_u";
    rows.sort(function (a, b) {
      var va = cellValue(ds, sortKey, a);
      var vb = cellValue(ds, sortKey, b);
      if (va === null) return 1;
      if (vb === null) return -1;
      if (va < vb) return -state.dir;
      if (va > vb) return state.dir;
      return 0;
    });

    var panel = E("div", "panel", null, view);
    var meta = E("div", "table-meta", null, panel);
    E(
      "span",
      null,
      rows.length +
        " rows match" +
        (rows.length > RENDER_CAP
          ? " · showing first " + RENDER_CAP + " (export gets all)"
          : ""),
      meta
    );
    meta.appendChild(
      ui.btn("export CSV", function () {
        var lines = rows.map(function (rowIndex) {
          return columns.map(function (column) {
            return cellValue(ds, column, rowIndex);
          });
        });
        Atlas.store.download(
          "atlas_rows.csv",
          "text/csv",
          Atlas.store.toCSV(columns.map(columnLabel), lines)
        );
      })
    );
    E(
      "p",
      "muted",
      "CSV export uses the atlas display payload precision. Point IDs, " +
        "campaign, evidence type, quadrature, and code revision identify " +
        "the registered source for lossless follow-up.",
      panel
    );

    var scroll = E("div", "table-scroll", null, panel);
    var table = E("table", "data", null, scroll);
    var head = E("tr", null, null, E("thead", null, null, table));
    columns.forEach(function (column) {
      var th = E("th", "txt sortable", columnLabel(column), head);
      if (column === sortKey) {
        th.textContent += state.dir > 0 ? " ↑" : " ↓";
      }
      th.addEventListener("click", function () {
        if (state.sort === column) state.dir = -state.dir;
        else {
          state.sort = column;
          state.dir = 1;
        }
        rerender();
      });
    });
    var body = E("tbody", null, null, table);
    rows.slice(0, RENDER_CAP).forEach(function (rowIndex) {
      var tr = E("tr", null, null, body);
      columns.forEach(function (column) {
        var value = cellValue(ds, column, rowIndex);
        var numeric = typeof value === "number";
        E(
          "td",
          numeric ? null : "txt",
          value === null ? "—" : numeric ? Atlas.fmt(value) : String(value),
          tr
        );
      });
    });
  });
})();
