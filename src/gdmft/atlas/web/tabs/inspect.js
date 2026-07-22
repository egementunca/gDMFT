/* Point inspector: pick one (dataset, lattice, m_g, gauge, T, U) key and
   reconstruct the full frequency-resolved picture from the stored pole
   parameters — A(omega), Sigma', Delta (channel-resolved), G_loc, the gap
   construction, and the Matsubara axis — with a broadening slider. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  var E = Atlas.E;
  var C = Atlas.colors;

  var RE_COLOR = C.cat[0]; /* blue */
  var IM_COLOR = C.cat[5]; /* red */
  var AUX_COLOR = C.cat[1]; /* aqua */

  function populatedKey(ds, lattice, mg, gauge, targetT, targetU) {
    var candidates = [];
    for (var i = 0; i < ds.n; i++) {
      if (
        ds.lattice(i) !== lattice ||
        ds.num("m_g", i) !== Number(mg) ||
        ds.str("gauge", i) !== gauge
      ) {
        continue;
      }
      candidates.push(i);
    }
    if (!candidates.length) return null;
    var converged = candidates.filter(function (i) {
      return ds.converged(i);
    });
    if (converged.length) candidates = converged;

    var tFloor = 1e-8;
    var targetLogT = Math.log(Math.max(targetT, tFloor)) / Math.LN10;
    var best = candidates[0];
    var bestScore = Infinity;
    candidates.forEach(function (i) {
      var logT = Math.log(Math.max(ds.t(i), tFloor)) / Math.LN10;
      var score =
        Math.abs(logT - targetLogT) +
        2 * Math.abs(ds.u(i) - targetU);
      if (score < bestScore) {
        best = i;
        bestScore = score;
      }
    });
    return {
      it: ds.d.cols.it[best],
      iu: ds.d.cols.iu[best],
      row: best,
    };
  }

  function moveToPopulatedKey(state, targetT, targetU) {
    var ds = Atlas.store.ds(state.ds);
    var key = populatedKey(
      ds,
      state.lattice,
      state.mg,
      state.gauge,
      targetT,
      targetU
    );
    if (!key) return false;
    state.it = key.it;
    state.iu = key.iu;
    state.row = key.row;
    return true;
  }

  function defaults() {
    var route = Atlas.store.primaryRoute("bethe", 3);
    if (!route) throw new Error("No primary source route for bethe m_g=3");
    var dsId = route.dataset_id;
    var ds = Atlas.store.ds(dsId);
    var mgs = ds.mgValues();
    var lattice = route.lattice;
    var mg = mgs.indexOf(3) >= 0 ? 3 : mgs[0];
    var state = {
      ds: dsId,
      lattice: lattice,
      mg: mg,
      gauge: route.gauge,
      it: 0,
      iu: 0,
      row: null,
      family: null,
      delta: 0.04,
      gem: true,
      hSector: "lattice",
      supplementarySource: false,
    };
    moveToPopulatedKey(state, 0.001, 2.0);
    return state;
  }

  function rowsAtKey(ds, state) {
    var keyed = ds.keyRows()[state.lattice];
    var rows = keyed && keyed[state.it] && keyed[state.it][state.iu]
      ? keyed[state.it][state.iu]
      : [];
    return rows.filter(function (i) {
      return (
        ds.num("m_g", i) === Number(state.mg) &&
        ds.str("gauge", i) === state.gauge
      );
    });
  }

  function gateChip(parent, label, tri) {
    var chip = E("span", "gate-chip", null, parent);
    var dot = E("span", "gate-dot", null, chip);
    dot.style.background =
      tri === 1 ? "#0ca30c" : tri === 0 ? "#d03b3b" : "#c3c2b7";
    E("span", null, label + (tri === 2 ? " ?" : tri === 1 ? " ✓" : " ✗"), chip);
  }

  function provenanceCard(view, ds, state, row, p) {
    var panel = E("div", "panel", null, view);
    E("h2", null, "Selected attempt", panel);
    var line1 = E("div", null, null, panel);
    E("strong", null, ds.str("family", row), line1);
    E(
      "span",
      "muted",
      "  pid " +
        ds.str("pid", row) +
        " · " +
        (ds._hasCategory
          ? ds.str("category", row)
          : "converged=" + ds.tri("src_converged", row)) +
        (ds.str("basin", row) ? " · basin " + ds.str("basin", row) : "") +
        " · resnorm " +
        Atlas.fmt(ds.num("resnorm", row)),
      line1
    );
    var gates = E("div", "gate-row", null, panel);
    gateChip(gates, "solver", ds.tri("ok", row));
    gateChip(gates, "equations", ds.tri("eq_ok", row));
    gateChip(gates, "guards", ds.tri("guards_ok", row));
    gateChip(gates, "bounds", ds.tri("bounds_ok", row));
    gateChip(gates, "continuity", ds.tri("cont_ok", row));
    gateChip(gates, "admissible", ds.tri("admissible", row));
    gateChip(gates, "selected", ds.tri("selected", row));

    /* parent chain */
    var chain = [];
    var cursor = row;
    for (var depth = 0; depth < 4; depth++) {
      var parentCol = ds.d.cols.parent;
      if (!parentCol || parentCol[cursor] === null) break;
      cursor = parentCol[cursor];
      chain.push(ds.str("pid", cursor) + " (" + ds.str("gauge", cursor) + ")");
    }
    if (chain.length) {
      E("div", "muted", "parents: " + chain.join(" ← "), panel);
    }
    if (p && p.hFromR) {
      E(
        "div",
        "muted",
        "h-sector shown via the canonical-R bare-equivalent view " +
          "(no bare h-sector stored for this row).",
        panel
      );
    }
    if (p && p.hSectorsDiffer) {
      E(
        "div",
        "caveat",
        "This legacy root stores different lattice and gateway h-sectors. " +
          "The functions below use the explicitly selected " + p.hSector +
          " sector; the stored scalar Z may refer to the other sector.",
        panel
      );
    }
    if (Number(state.mg) === 1 && state.gauge === "bare") {
      E(
        "div",
        "caveat",
        "Caveat (registered mg1 bound-expansion evidence): bare m_g=1 " +
          "h-sector parameters are optimizer-cap dependent; the pole " +
          "positions here are not cap-certified even where Z and docc are.",
        panel
      );
    }
    /* pole parameter table */
    if (p) {
      var table = E("table", "data", null, panel);
      var head = E("tr", null, null, E("thead", null, null, table));
      ["sector", "pole positions (/D)", "amplitudes (/D)", "residues (/D²)"].forEach(function (t) {
        E("th", "txt", t, head);
      });
      var body = E("tbody", null, null, table);
      var gRow = E("tr", null, null, body);
      E("td", "txt", "hybridization (g)", gRow);
      E("td", "txt", p.g.map(function (m) { return Atlas.fmt(m[0]); }).join(", "), gRow);
      E("td", "txt", p.g.map(function (m) { return Atlas.fmt(m[1]); }).join(", "), gRow);
      E("td", "txt", p.g.map(function (m) { return Atlas.fmt(m[1] * m[1]); }).join(", "), gRow);
      var hRow = E("tr", null, null, body);
      E("td", "txt", "self-energy (h, " + p.hSector + ")", hRow);
      E("td", "txt", p.h.map(function (m) { return Atlas.fmt(m[0]); }).join(", "), hRow);
      E("td", "txt", p.h.map(function (m) { return Atlas.fmt(m[1]); }).join(", "), hRow);
      E("td", "txt", p.h.map(function (m) { return Atlas.fmt(m[1] * m[1]); }).join(", "), hRow);
      var lam = ds.num("lam_red_d", row);
      var rOuter = ds.num("r_red", row);
      var zR = ds.num("z_from_r", row);
      if (lam !== null && rOuter !== null && zR !== null) {
        var cRow = E("tr", null, null, body);
        E("td", "txt", "canonical modes (λ, R²)", cRow);
        E("td", "txt", [-lam, 0, lam].map(Atlas.fmt).join(", "), cRow);
        E(
          "td",
          "txt",
          [rOuter, Math.sqrt(Math.max(0, zR)), rOuter]
            .map(Atlas.fmt)
            .join(", "),
          cRow
        );
        E(
          "td",
          "txt",
          [rOuter * rOuter, zR, rOuter * rOuter].map(Atlas.fmt).join(", "),
          cRow
        );
      }
    }
    E(
      "div",
      "muted",
      "stored Z_pole=" + Atlas.fmt(ds.num("z_pole", row)) +
        " · canonical Z_R=" + Atlas.fmt(ds.num("z_from_r", row)) +
        (p
          ? " · Z from selected h poles=" +
            Atlas.fmt(Atlas.spectra.zFromSelfEnergyModes(p.h))
          : ""),
      panel
    );
  }

  function onePanel(parent, title, spec) {
    var card = E("div", "spectra-card", null, parent);
    E("h3", null, title, card);
    spec.width = 460;
    var figure = Atlas.plot.figure(spec);
    card.appendChild(figure.el);
    return figure;
  }

  Atlas.registerTab("inspect", "Inspect", function (view) {
    var state = Atlas.state.inspect || (Atlas.state.inspect = defaults());
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
    if (state.it >= grid.t.length) state.it = 0;
    if (state.iu >= grid.u.length) state.iu = Math.floor(grid.u.length / 2);

    var ui = Atlas.ui;
    function rerender() {
      Atlas.saveState("inspect");
      Atlas.tabs
        .filter(function (tab) {
          return tab.id === "inspect";
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
          var route = Atlas.store.primaryRoute(
            state.lattice,
            Number(state.mg)
          );
          if (route && Atlas.DATA.datasets[route.dataset_id]) {
            state.ds = route.dataset_id;
            state.gauge = route.gauge;
          }
        }
        if (
          key === "ds" ||
          key === "lattice" ||
          key === "mg" ||
          key === "gauge" ||
          key === "supplementarySource"
        ) {
          var next = Atlas.store.ds(state.ds);
          if (!next.grids[state.lattice]) {
            state.lattice = next.dictOf("lattice")[0];
          }
          if (next.mgValues().indexOf(Number(state.mg)) < 0) {
            state.mg = next.mgValues()[0];
          }
          if (next.dictOf("gauge").indexOf(state.gauge) < 0) {
            state.gauge = Atlas.store.pickGauge(
              state.ds,
              state.lattice,
              Number(state.mg),
              "bare"
            );
          }
          moveToPopulatedKey(state, 0.001, 2.0);
        }
        if (key !== "row" && key !== "delta") state.row = null;
        rerender();
      };
    }
    view.innerHTML = "";

    var uSlider = document.createElement("input");
    uSlider.type = "range";
    uSlider.min = 0;
    uSlider.max = grid.u.length - 1;
    uSlider.value = state.iu;
    var uWrap = E("div", "field slider-field");
    E("span", "field-label", "U/D", uWrap);
    var uInner = E("div", "slider-inner", null, uWrap);
    uInner.appendChild(uSlider);
    var uReadout = E(
      "span", "slider-readout", "U/D = " + Atlas.fmt(grid.u[state.iu]), uInner
    );
    uSlider.addEventListener("input", function () {
      state.iu = Number(uSlider.value);
      state.row = null;
      uReadout.textContent = "U/D = " + Atlas.fmt(grid.u[state.iu]);
      renderBody(); /* live while dragging */
    });
    uSlider.addEventListener("change", function () {
      Atlas.saveState("inspect");
    });

    var dSlider = document.createElement("input");
    dSlider.type = "range";
    dSlider.min = 0.01;
    dSlider.max = 0.12;
    dSlider.step = 0.005;
    dSlider.value = state.delta;
    var dWrap = E("div", "field slider-field");
    E("span", "field-label", "broadening δ", dWrap);
    var dInner = E("div", "slider-inner", null, dWrap);
    dInner.appendChild(dSlider);
    var dReadout = E(
      "span", "slider-readout", "δ = " + Atlas.fmt(state.delta), dInner
    );
    dSlider.addEventListener("input", function () {
      state.delta = Number(dSlider.value);
      dReadout.textContent = "δ = " + Atlas.fmt(state.delta);
      renderBody(); /* live while dragging */
    });
    dSlider.addEventListener("change", function () {
      Atlas.saveState("inspect");
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
        ui.field(
          "self-energy h sector",
          ui.select(
            [
              { value: "lattice", label: "lattice" },
              { value: "gateway", label: "gateway" },
            ],
            state.hSector,
            set("hSector")
          )
        ),
        ui.field(
          "T/D",
          ui.select(
            grid.t.map(function (value, index) {
              return { value: index, label: Atlas.fmt(value) };
            }),
            state.it,
            set("it", Number)
          )
        ),
        uWrap,
        dWrap,
        ui.check("gem Σ overlay", state.gem, set("gem")),
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
          ? "Declared primary route: "
          : "Automatic primary source: ") +
          Atlas.store.dsLabel(activeRoute.dataset_id) + " · " +
          activeRoute.gauge + " · " + activeRoute.quadrature +
          (state.ds === activeRoute.dataset_id &&
          state.gauge === activeRoute.gauge
            ? " (active)"
            : " (you are inspecting a supplementary route)"),
        view
      );
    }

    var bodyHost = E("div", null, null, view);
    function renderBody() {
    bodyHost.innerHTML = "";
    var rows = rowsAtKey(ds, state);
    // campaign tag from run_id ("d09-fill-20260721:cell" -> "d09-fill-20260721");
    // duplicate keys exist as rows of fact, so picks prefer the newest
    // campaign (same rule the derived chains apply) and duplicate labels
    // carry the tag
    function runTag(i) {
      var run = ds.has("run") ? ds.str("run", i) : null;
      return run ? run.split(":")[0] : "";
    }
    function newestFirst(list) {
      return list.slice().sort(function (a, b) {
        var ra = runTag(a);
        var rb = runTag(b);
        return ra < rb ? 1 : ra > rb ? -1 : a - b;
      });
    }
    if (state.row === null || rows.indexOf(state.row) < 0) {
      // sticky branch: an attempt picked by hand pins its family, and
      // slider moves re-select that family at the new point when present
      // (converged first, else the recorded failed attempt, labeled)
      var pick = null;
      if (state.family) {
        var fam = rows.filter(function (i) {
          return ds.str("family", i) === state.family;
        });
        var famConv = fam.filter(function (i) {
          return ds.converged(i);
        });
        pick = famConv.length
          ? newestFirst(famConv)[0]
          : fam.length
            ? newestFirst(fam)[0]
            : null;
      }
      if (pick === null) {
        var preferred = rows.filter(function (i) {
          return ds.converged(i);
        });
        pick = preferred.length
          ? newestFirst(preferred)[0]
          : newestFirst(rows)[0];
      }
      state.row = pick;
    }
    if (rows.length) {
      var famCount = {};
      rows.forEach(function (i) {
        var f = ds.str("family", i);
        famCount[f] = (famCount[f] || 0) + 1;
      });
      bodyHost.appendChild(
        ui.row([
          ui.field(
            "attempt (sticky)",
            ui.select(
              rows.map(function (i) {
                var fam = ds.str("family", i);
                var tag = famCount[fam] > 1 ? runTag(i) : "";
                return {
                  value: i,
                  label:
                    fam +
                    (tag ? " · " + tag : "") +
                    (ds.converged(i) ? "" : " (not converged)"),
                };
              }),
              state.row,
              function (value) {
                state.family = ds.str("family", Number(value));
                set("row", Number)(value);
              }
            )
          ),
        ])
      );
      if (
        state.family &&
        state.row !== null &&
        state.row !== undefined &&
        ds.str("family", state.row) !== state.family
      ) {
        E(
          "p",
          "muted ds-note",
          "followed branch '" + state.family +
            "' has no attempt at this point — showing " +
            ds.str("family", state.row),
          bodyHost
        );
      }
    }

    if (state.row === undefined || state.row === null) {
      E("p", "muted panel", "No attempts at this key.", bodyHost);
      return;
    }
    var p = Atlas.spectra.params(ds, state.row, state.hSector);
    provenanceCard(bodyHost, ds, state, state.row, p);
    if (!p) {
      E(
        "p",
        "muted panel",
        "No pole parameters stored for this row.",
        bodyHost
      );
      return;
    }
    E(
      "div",
      "caveat",
      "Function preview: reconstructed in this browser from a six-significant-" +
        "digit payload with user-selected broadening. Square G_loc uses a " +
        "compact 512-node display DOS. Use the lossless registered roots and " +
        "production quadrature for numerical claims.",
      bodyHost
    );

    var u = grid.u[state.iu];
    var t = grid.t[state.it];
    var omegaMax = Math.max(2.5, u / 2 + 1.5);
    var real = Atlas.spectra.realCurves(p, state.lattice, state.delta, omegaMax, 480);
    var mats = Atlas.spectra.matsubaraCurves(p, state.lattice, t, 32);

    function zip(xs, ys) {
      return xs.map(function (x, k) {
        return [x, ys[k]];
      });
    }

    /* gem structure overlay for the Sigma panel (B=3, up arm, this key) */
    var gemSeries = [];
    var gem = Atlas.DATA.references.gem;
    if (
      state.gem &&
      gem &&
      Number(state.mg) === 3 &&
      gem.anchored_to === state.ds
    ) {
      var latticeCode = gem.dicts.lattice.indexOf(state.lattice);
      var upCode = gem.dicts.direction.indexOf("up");
      for (var gi = 0; gi < gem.n; gi++) {
        if (
          gem.cols.lattice[gi] === latticeCode &&
          gem.cols.budget[gi] === 3 &&
          gem.cols.direction[gi] === upCode &&
          gem.cols.iu[gi] === state.iu &&
          gem.cols.it[gi] === state.it &&
          gem.cols.sig_p[gi]
        ) {
          var gs = Atlas.spectra.gemSigma(
            gem.cols.sig_p[gi],
            gem.cols.sig_w[gi],
            state.delta,
            real.omega
          );
          gemSeries.push({
            label: "gem B=3 Re Σ′ (pole part)",
            color: C.gem,
            dash: true,
            marker: "none",
            points: zip(real.omega, gs.re),
          });
          break;
        }
      }
    }

    var gridBox = E("div", "spectra-grid", null, bodyHost);
    var pinning =
      state.lattice === "bethe"
        ? [{ y: 2 / Math.PI, label: "A(0) = 2/πD", color: C.muted }]
        : [];
    onePanel(gridBox, "A(ω) — local spectral function", {
      xLabel: "ω/D",
      panels: [
        {
          yLabel: "A(ω)",
          hlines: pinning,
          series: [
            {
              label: "A(ω)",
              color: RE_COLOR,
              marker: "none",
              points: zip(real.omega, real.a),
            },
          ],
        },
      ],
    });
    onePanel(
      gridBox,
      "Σ′(ω) — " + p.hSector + " self-energy (Hartree removed)",
      {
      xLabel: "ω/D",
      panels: [
        {
          yLabel: "Σ′",
          series: [
            {
              label: "Re Σ′",
              color: RE_COLOR,
              marker: "none",
              points: zip(real.omega, real.sigRe),
            },
            {
              label: "Im Σ′",
              color: IM_COLOR,
              marker: "none",
              points: zip(real.omega, real.sigIm),
            },
          ].concat(gemSeries),
        },
      ],
      }
    );
    onePanel(gridBox, "Δ(ω) — hybridization by channel", {
      xLabel: "ω/D",
      panels: [
        {
          yLabel: "Δ",
          series: [
            {
              label: "Re Δ (all channels)",
              color: RE_COLOR,
              marker: "none",
              points: zip(real.omega, real.delRe),
            },
            {
              label: "Re Δ (central V0 only)",
              color: AUX_COLOR,
              dash: true,
              marker: "none",
              points: zip(real.omega, real.del0Re),
            },
            {
              label: "Im Δ",
              color: IM_COLOR,
              marker: "none",
              points: zip(real.omega, real.delIm),
            },
          ],
        },
      ],
    });
    onePanel(gridBox, "G_loc(ω)", {
      xLabel: "ω/D",
      panels: [
        {
          yLabel: "G_loc",
          series: [
            {
              label: "Re G",
              color: RE_COLOR,
              marker: "none",
              points: zip(real.omega, real.gRe),
            },
            {
              label: "Im G",
              color: IM_COLOR,
              marker: "none",
              points: zip(real.omega, real.gIm),
            },
          ],
        },
      ],
    });
    onePanel(gridBox, "Gap construction: ω − ReΣ′(ω) vs the band ±D", {
      xLabel: "ω/D",
      panels: [
        {
          yLabel: "ω − ReΣ′",
          hlines: [
            { y: 1, label: "+D" },
            { y: -1, label: "−D" },
          ],
          series: [
            {
              label: "ω − ReΣ′(ω)",
              color: RE_COLOR,
              marker: "none",
              points: zip(real.omega, real.gap),
            },
          ],
        },
      ],
    });
    onePanel(gridBox, "Matsubara axis at T/D = " + Atlas.fmt(t), {
      xLabel: "ωₙ/D",
      panels: [
        {
          yLabel: "Im",
          series: [
            {
              label: "Im Σ′(iωₙ)",
              color: RE_COLOR,
              marker: "dot",
              points: zip(mats.wn, mats.sigIm),
            },
            {
              label: "Im Δ(iωₙ)",
              color: AUX_COLOR,
              marker: "dot",
              points: zip(mats.wn, mats.delIm),
            },
            {
              label: "Im G(iωₙ)",
              color: IM_COLOR,
              marker: "dot",
              points: zip(mats.wn, mats.gIm),
            },
          ],
        },
      ],
    });
    }
    renderBody();
  });
})();
