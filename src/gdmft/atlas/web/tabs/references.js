/* Reference coverage and parameter anatomy. This tab keeps physical
   temperature semantics and method-specific budget meanings explicit. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;
  var C = Atlas.colors;

  function objects(table) {
    if (!table) return [];
    return table.rows.map(function (values) {
      var row = {};
      table.fields.forEach(function (field, index) {
        row[field] = values[index];
      });
      return row;
    });
  }

  function unique(rows, field) {
    var seen = {};
    rows.forEach(function (row) {
      if (row[field] !== null && row[field] !== undefined) {
        seen[String(row[field])] = row[field];
      }
    });
    return Object.keys(seen)
      .map(function (key) { return seen[key]; })
      .sort(function (a, b) { return Number(a) - Number(b); });
  }

  function nearest(values, target) {
    var best = values[0];
    values.forEach(function (value) {
      if (Math.abs(value - target) < Math.abs(best - target)) best = value;
    });
    return best;
  }

  function routeFor(lattice, mg) {
    var catalog = Atlas.DATA.catalog;
    var routes =
      catalog && catalog.policy && Array.isArray(catalog.policy.routes)
        ? catalog.policy.routes
        : [];
    for (var i = 0; i < routes.length; i++) {
      if (
        routes[i].lattice === lattice &&
        Number(routes[i].m_g) === Number(mg)
      ) {
        return routes[i];
      }
    }
    return null;
  }

  function primaryPoint(lattice, mg, u, t) {
    var route = routeFor(lattice, mg);
    if (!route || !Atlas.DATA.datasets[route.dataset_id]) return null;
    var ds = Atlas.store.ds(route.dataset_id);
    var grid = ds.grids[lattice];
    if (!grid) return null;
    var chosenT = nearest(grid.t, t);
    var branch = Atlas.store.branch(
      route.dataset_id,
      lattice,
      Number(mg),
      route.gauge,
      chosenT,
      "metal"
    );
    if (!branch || !branch.rows.length) return null;
    var matching = branch.rows.filter(function (candidate) {
      return Math.abs(ds.u(candidate) - u) <= 1e-10 * (1 + Math.abs(u));
    });
    if (!matching.length) return null;
    var row = matching[0];
    return {
      route: route,
      ds: ds,
      row: row,
      u: ds.u(row),
      t: ds.t(row),
      params: Atlas.spectra.params(ds, row, "lattice"),
    };
  }

  function addTable(parent, headers, rows) {
    var scroll = E("div", "table-scroll", null, parent);
    var table = E("table", "data", null, scroll);
    var head = E("tr", null, null, E("thead", null, null, table));
    headers.forEach(function (header) {
      E("th", "txt", header, head);
    });
    var body = E("tbody", null, null, table);
    rows.forEach(function (values) {
      var tr = E("tr", null, null, body);
      values.forEach(function (value, index) {
        E("td", index === 0 ? "txt" : null, value, tr);
      });
    });
    return table;
  }

  function coveragePanel(view) {
    var refs = Atlas.DATA.references || {};
    var ed = refs.ed || {};
    var currentEd = objects(ed.v2);
    var legacyEd = objects(ed.v1_legacy);
    var nrg = objects(refs.nrg);
    var professor = objects(refs.professor_gga);
    var ctqmc = objects(refs.ctqmc);
    var panel = E("div", "panel", null, view);
    E("h2", null, "What can actually be compared", panel);
    E(
      "p",
      "muted",
      "A shared integer budget is only a comparison convention. M_g, gem B, " +
        "and ED N_b are different method-specific objects.",
      panel
    );
    addTable(
      panel,
      [
        "method",
        "lattice",
        "physical temperature",
        "stored coverage",
        "stored scalars",
        "stored pole / mode data",
        "allowed join",
      ],
      [
        [
          "ghost-DMFT primary routes",
          "Bethe + square",
          "registered scan T/D",
          String((Atlas.DATA.catalog || {}).default_physics_count || 0) +
            " accepted primary-route attempts",
          "Z, d, n, Ω; D09 energies",
          "g and h poles; canonical λ and R in roots",
          "route by lattice and M_g; branch selection still pending",
        ],
        [
          "gem / gGA",
          "Bethe + square",
          "same D09 finite-T grid",
          String(refs.gem ? refs.gem.n : 0) + " attempts",
          "Z, d, E_kin, E_tot",
          "canonical modes and B=3 Σ poles where retained",
          "point-for-point finite-T comparison after quality filter",
        ],
        [
          "DMFT-ED D09",
          "Bethe",
          "ground state (T/D=0)",
          String(currentEd.length) +
            " accepted; N_b=1: 14 U values, N_b=3: 13",
          "Z, d, E_kin, E_tot",
          "bath ε_l and V_l; no stored many-body Σ poles",
          "separate T=0 panel; beta_fit=200 is not physical temperature",
        ],
        [
          "DMFT-ED D08 legacy",
          "Bethe + square",
          "ground state (T/D=0)",
          String(legacyEd.length) + " accepted prototype rows",
          "Z, d, E_kin, E_tot",
          "no bath arrays in this compact legacy table",
          "supporting evidence only; do not merge with D09 ED",
        ],
        [
          "NRG",
          "Bethe",
          String(unique(nrg, "t_over_d").length) + " thermal T values",
          String(nrg.length) + " rows at U/D = 1, 2, 3.2",
          "d and energies, with missing source values kept null",
          "none",
          "exact shared (U,T) keys only; energy convention needs review",
        ],
        [
          "reference gGA",
          "Bethe",
          String(unique(professor, "t_over_d").length) + " T values",
          String(professor.length) + " rows; B=1,3",
          "d and raw total energy",
          "none in the registered scalar table",
          "apply the recorded +U/2 energy transformation explicitly",
        ],
        [
          "LLK CTQMC",
          "Bethe",
          ctqmc.length ? "T/D=" + Atlas.fmt(ctqmc[0].t_over_d) : "—",
          ctqmc.length ? "one U/D=" + Atlas.fmt(ctqmc[0].u_over_d) + " anchor" : "0",
          "digitized Z, d, E_tot; E_kin absent",
          "none",
          "one exact anchor only; never a scan",
        ],
      ]
    );
  }

  function stemPoints(modes) {
    var points = [];
    modes
      .slice()
      .sort(function (a, b) { return a[0] - b[0]; })
      .forEach(function (mode) {
        points.push([mode[0], 0]);
        points.push([mode[0], mode[1]]);
        points.push(null);
      });
    return points;
  }

  function modePoints(modes) {
    return modes
      .slice()
      .sort(function (a, b) { return a[0] - b[0]; })
      .map(function (mode) { return [mode[0], mode[1]]; });
  }

  function modesNearestZero(modes) {
    if (!modes.length) return [];
    var minAbs = Math.min.apply(
      null,
      modes.map(function (mode) { return Math.abs(mode[0]); })
    );
    var tolerance = Math.max(1, minAbs) * 1e-10;
    return modes.filter(function (mode) {
      return Math.abs(Math.abs(mode[0]) - minAbs) <= tolerance;
    });
  }

  function symmetricPaddedDomain(modes, padding) {
    var maxAbs = modes.reduce(function (largest, mode) {
      return Math.max(largest, Math.abs(mode[0]));
    }, 0);
    var halfWidth = Math.max(0.25, maxAbs * (1 + padding));
    return [-halfWidth, halfWidth];
  }

  function edPoleFigure(state, ours, edModes, oursModes, xDomain) {
    return Atlas.plot.figure({
      width: 900,
      xLabel: "hybridization pole position ε/D",
      xDomain: xDomain,
      panels: [
        {
          yLabel: "residue V²/D²",
          height: 210,
          series: [
            {
              label: "DMFT-ED N_b=" + state.nb + " · T=0",
              tipLabel: "DMFT-ED",
              color: C.ed,
              marker: "square",
              markerOrder: 1,
              markerSize: 4.8,
              connect: false,
              points: modePoints(edModes),
            },
            {
              label:
                "ghost M_g=" + state.nb +
                (ours ? " · T/D=" + Atlas.fmt(ours.t) : ""),
              tipLabel: "ghost g sector",
              color: C.ours,
              marker: "circle",
              markerOrder: 2,
              markerSize: 3.7,
              connect: false,
              points: modePoints(oursModes),
            },
          ],
        },
      ],
    });
  }

  function edPanel(view, state, rerender) {
    var table = ((Atlas.DATA.references || {}).ed || {}).v2;
    var rows = objects(table).filter(function (row) {
      return Number(row.accepted) === 1;
    });
    if (!rows.length) return;
    var budgets = unique(rows, "Nb").map(Number);
    if (budgets.indexOf(Number(state.nb)) < 0) state.nb = budgets[0];
    var budgetRows = rows.filter(function (row) {
      return Number(row.Nb) === Number(state.nb);
    });
    var allUValues = unique(budgetRows, "U_over_D").map(Number);
    var uValues = allUValues.filter(function (value) {
      return primaryPoint("bethe", Number(state.nb), value, 0.001) !== null;
    });
    if (!uValues.length) return;
    state.edU = nearest(uValues, Number(state.edU));
    var chosen = budgetRows.filter(function (row) {
      return (
        Number(row.U_over_D) === Number(state.edU) &&
        row.direction === state.edDirection
      );
    })[0];
    if (!chosen) {
      chosen = budgetRows.filter(function (row) {
        return Number(row.U_over_D) === Number(state.edU);
      })[0];
    }

    var panel = E("div", "panel", null, view);
    E("h2", null, "DMFT-ED bath poles compared with the ghost g-sector", panel);
    E(
      "div",
      "caveat",
      "The direct analogy is Δ(z)=Σ_l V_l²/(z−ε_l). The ED calculation is " +
        "ground-state DMFT-ED. Its beta_fit=200 grid fits the bath and is " +
        "not a physical T/D=0.005 calculation. Stored ε and V are rounded " +
        "to six significant digits.",
      panel
    );
    var ui = Atlas.ui;
    panel.appendChild(
      ui.row([
        ui.field(
          "ED N_b",
          ui.select(
            budgets.map(function (value) {
              return { value: value, label: String(value) };
            }),
            state.nb,
            function (value) {
              state.nb = Number(value);
              rerender();
            }
          )
        ),
        ui.field(
          "ED U/D",
          ui.select(
            uValues.map(function (value) {
              return { value: value, label: Atlas.fmt(value) };
            }),
            state.edU,
            function (value) {
              state.edU = Number(value);
              rerender();
            }
          )
        ),
        ui.field(
          "continuation",
          ui.select(
            [
              { value: "up", label: "up" },
              { value: "down", label: "down" },
            ],
            state.edDirection,
            function (value) {
              state.edDirection = value;
              rerender();
            }
          )
        ),
      ])
    );
    if (allUValues.length > uValues.length) {
      E(
        "p",
        "muted",
        "The selector contains exact shared U/D values only. " +
          (allUValues.length - uValues.length) +
          " accepted ED-only value(s) outside the stored ghost metal branch " +
          "remain visible at their true U/D in the Series tab.",
        panel
      );
    }
    if (!chosen) return;

    var edModes = chosen.eps.map(function (position, index) {
      return [position, chosen.V[index] * chosen.V[index]];
    });
    var ours = primaryPoint("bethe", Number(state.nb), state.edU, 0.001);
    var oursModes =
      ours && ours.params
        ? ours.params.g.map(function (mode) {
            return [mode[0], mode[1] * mode[1]];
          })
        : [];
    var centralEdModes = modesNearestZero(edModes);
    var centralOursModes = modesNearestZero(oursModes);
    var centralModes = centralEdModes.concat(centralOursModes);
    E("h3", null, "Central-mode window", panel);
    E(
      "p",
      "muted",
      "Magnified comparison of the bath mode nearest ε=0 from each method. " +
        "All satellite modes are excluded from this view only; they remain " +
        "in the full-span plot and table below.",
      panel
    );
    panel.appendChild(
      edPoleFigure(
        state,
        ours,
        centralEdModes,
        centralOursModes,
        symmetricPaddedDomain(centralModes, 0.15)
      ).el
    );
    E("h3", null, "Full bath span", panel);
    E(
      "p",
      "muted",
      "Every stored ED bath mode and ghost g-sector mode is shown. The " +
        "horizontal range has 8% side padding so the outermost markers are " +
        "fully visible.",
      panel
    );
    panel.appendChild(
      edPoleFigure(
        state,
        ours,
        edModes,
        oursModes,
        symmetricPaddedDomain(edModes.concat(oursModes), 0.08)
      ).el
    );
    var tableRows = [];
    edModes.forEach(function (mode, index) {
      tableRows.push([
        "DMFT-ED bath mode " + index,
        Atlas.fmt(mode[0]),
        Atlas.fmt(chosen.V[index]),
        Atlas.fmt(mode[1]),
        "T/D=0; beta_fit=" + Atlas.fmt(chosen.bath_fit_beta),
      ]);
    });
    if (ours && ours.params) {
      ours.params.g.forEach(function (mode, index) {
        tableRows.push([
          "ghost g mode " + index,
          Atlas.fmt(mode[0]),
          Atlas.fmt(mode[1]),
          Atlas.fmt(mode[1] * mode[1]),
          ours.route.dataset_id + " · T/D=" + Atlas.fmt(ours.t) +
            " · U/D=" + Atlas.fmt(ours.u),
        ]);
      });
    }
    addTable(
      panel,
      ["mode", "position /D", "amplitude /D", "residue /D²", "provenance"],
      tableRows
    );
    E(
      "p",
      "muted",
      "ED fixed point accepted=" + chosen.fixed_point_converged +
        " · bath quality=" + chosen.bath_approximation_quality +
        " · Z estimator converged=" + chosen.Z_estimator_converged +
        " · accuracy qualified=" + chosen.accuracy_qualified,
      panel
    );
  }

  function gemPanel(view, state, rerender) {
    var gem = (Atlas.DATA.references || {}).gem;
    if (!gem) return;
    var anchor = Atlas.store.ds(gem.anchored_to);
    var latticeCode = gem.dicts.lattice.indexOf(state.gemLattice);
    if (latticeCode < 0) {
      state.gemLattice = gem.dicts.lattice[0];
      latticeCode = 0;
    }
    var directionCode = gem.dicts.direction.indexOf(state.gemDirection);
    var candidates = [];
    for (var i = 0; i < gem.n; i++) {
      if (
        gem.cols.lattice[i] === latticeCode &&
        gem.cols.budget[i] === 3 &&
        gem.cols.direction[i] === directionCode &&
        gem.cols.converged[i] &&
        gem.cols.sig_p[i]
      ) {
        candidates.push(i);
      }
    }
    if (!candidates.length) return;
    var grid = anchor.grids[state.gemLattice];
    var tValues = unique(
      candidates.map(function (index) {
        return { t: grid.t[gem.cols.it[index]] };
      }),
      "t"
    ).map(Number);
    state.gemT = nearest(tValues, Number(state.gemT));
    var atT = candidates.filter(function (index) {
      return grid.t[gem.cols.it[index]] === state.gemT;
    });
    var uValues = unique(
      atT.map(function (index) {
        return { u: grid.u[gem.cols.iu[index]] };
      }),
      "u"
    ).map(Number);
    state.gemU = nearest(uValues, Number(state.gemU));
    var index = atT.filter(function (candidate) {
      return grid.u[gem.cols.iu[candidate]] === state.gemU;
    })[0];
    var ours = primaryPoint(
      state.gemLattice,
      3,
      state.gemU,
      state.gemT
    );
    var gemModes = gem.cols.sig_p[index].map(function (position, modeIndex) {
      return [position, gem.cols.sig_w[index][modeIndex]];
    });
    var oursModes =
      ours && ours.params
        ? ours.params.h.map(function (mode) {
            return [mode[0], mode[1] * mode[1]];
          })
        : [];

    var panel = E("div", "panel", null, view);
    E("h2", null, "gem B=3 structure compared with the ghost h-sector", panel);
    E(
      "p",
      "muted",
      "The self-energy pole positions and residues are comparable in role. " +
        "A full gem Σ reconstruction must also include its stored linear " +
        "term; raw R magnitudes are not compared between frameworks.",
      panel
    );
    var ui = Atlas.ui;
    panel.appendChild(
      ui.row([
        ui.field(
          "lattice",
          ui.select(
            gem.dicts.lattice.map(function (value) {
              return { value: value, label: value };
            }),
            state.gemLattice,
            function (value) {
              state.gemLattice = value;
              rerender();
            }
          )
        ),
        ui.field(
          "T/D",
          ui.select(
            tValues.map(function (value) {
              return { value: value, label: Atlas.fmt(value) };
            }),
            state.gemT,
            function (value) {
              state.gemT = Number(value);
              rerender();
            }
          )
        ),
        ui.field(
          "U/D",
          ui.select(
            uValues.map(function (value) {
              return { value: value, label: Atlas.fmt(value) };
            }),
            state.gemU,
            function (value) {
              state.gemU = Number(value);
              rerender();
            }
          )
        ),
        ui.field(
          "gem scan direction",
          ui.select(
            gem.dicts.direction.map(function (value) {
              return { value: value, label: value };
            }),
            state.gemDirection,
            function (value) {
              state.gemDirection = value;
              rerender();
            }
          )
        ),
      ])
    );
    var figure = Atlas.plot.figure({
      width: 900,
      xLabel: "self-energy pole position /D",
      panels: [
        {
          yLabel: "pole residue /D²",
          height: 250,
          series: [
            {
              label: "gem B=3 pole part",
              tipLabel: "gem",
              color: C.gem,
              marker: "diamond",
              markerOrder: 1,
              markerSize: 4.8,
              connect: false,
              points: stemPoints(gemModes),
            },
            {
              label: "ghost M_g=3 h-sector",
              tipLabel: "ghost h sector",
              color: C.ours,
              marker: "circle",
              markerOrder: 2,
              markerSize: 3.7,
              connect: false,
              points: stemPoints(oursModes),
            },
          ],
        },
      ],
    });
    panel.appendChild(figure.el);
    var rows = [];
    gemModes.forEach(function (mode, modeIndex) {
      rows.push([
        "gem Σ pole " + modeIndex,
        Atlas.fmt(mode[0]),
        Atlas.fmt(mode[1]),
        "linear term=" + Atlas.fmt(gem.cols.sig_lin[index]),
      ]);
    });
    if (ours && ours.params) {
      ours.params.h.forEach(function (mode, modeIndex) {
        rows.push([
          "ghost h pole " + modeIndex,
          Atlas.fmt(mode[0]),
          Atlas.fmt(mode[1] * mode[1]),
          ours.route.dataset_id + " · " + ours.route.gauge,
        ]);
      });
    }
    addTable(panel, ["mode", "position /D", "residue /D²", "note"], rows);

    var canonicalRows = [];
    (gem.cols.lam[index] || []).forEach(function (position, modeIndex) {
      canonicalRows.push([
        "gem canonical mode " + modeIndex,
        Atlas.fmt(position),
        Atlas.fmt((gem.cols.r2[index] || [])[modeIndex]),
      ]);
    });
    if (ours) {
      var lambda = ours.ds.num("lam_red_d", ours.row);
      var rOuter = ours.ds.num("r_red", ours.row);
      var zR = ours.ds.num("z_from_r", ours.row);
      if (lambda !== null && rOuter !== null && zR !== null) {
        [-lambda, 0, lambda].forEach(function (position, modeIndex) {
          canonicalRows.push([
            "ghost canonical mode " + modeIndex,
            Atlas.fmt(position),
            Atlas.fmt(modeIndex === 1 ? zR : rOuter * rOuter),
          ]);
        });
      }
    }
    if (canonicalRows.length) {
      E("h3", null, "Canonical mode positions and weights", panel);
      addTable(panel, ["mode", "λ/D", "weight R²"], canonicalRows);
    }
  }

  function defaults() {
    return {
      nb: 3,
      edU: 2.4,
      edDirection: "up",
      gemLattice: "bethe",
      gemT: 0.001,
      gemU: 2.0,
      gemDirection: "up",
    };
  }

  Atlas.registerTab("references", "References", function (view) {
    var state =
      Atlas.state.references || (Atlas.state.references = defaults());
    function rerender() {
      Atlas.saveState("references");
      Atlas.tabs
        .filter(function (tab) { return tab.id === "references"; })[0]
        .render(view);
    }
    view.innerHTML = "";
    coveragePanel(view);
    edPanel(view, state, rerender);
    gemPanel(view, state, rerender);
  });
})();
