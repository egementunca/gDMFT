/* Columnar payload accessors: decode dicts/constants, grid lookups,
   quantity registry, derived-branch and reference-curve helpers. */
(function () {
  "use strict";
  var Atlas = window.Atlas;

  /* Quantity registry: label + scale group (one panel per group — never a
     second y-axis). `log` marks strictly-positive diagnostics that default
     to a log10 axis. */
  var QTY = [
    { key: "z_pole", label: "Z (pole)", group: "Z" },
    { key: "z_mats", label: "Z (Matsubara)", group: "Z" },
    { key: "z_from_r", label: "Z (from R)", group: "Z" },
    { key: "docc", label: "double occupancy", group: "docc" },
    { key: "density", label: "density n", group: "density" },
    { key: "omega_d", label: "Ω/D", group: "energy" },
    { key: "ekin_d", label: "E_kin/D", group: "energy" },
    { key: "epot_d", label: "E_pot/D", group: "energy" },
    { key: "etot_d", label: "E_tot/D", group: "energy" },
    { key: "lam_red_d", label: "λ_red/D", group: "lambda" },
    { key: "r_red", label: "R_red", group: "R" },
    { key: "resnorm", label: "residual norm", group: "residual", log: true },
    { key: "norm_err", label: "norm error", group: "gauge-err", log: true },
    { key: "closure_err", label: "closure error", group: "gauge-err", log: true },
    {
      key: "roundtrip_err",
      label: "roundtrip error",
      group: "gauge-err",
      log: true,
    },
    /* Pole/bath parameters, reconstructed per row from the embedded pole
       tables (units of D). Reduced symmetric parameters only — asymmetric
       exotic records plot null. gem overlays exist ONLY for the
       framework-invariant ones (η, W, Λ, ΣW² via gem's Σ-pole structure).
       The g-sector parameters have a direct DMFT-ED bath analog because
       both methods store Delta(z) as a finite pole sum. */
    { key: "p_v0", label: "V0 (central coupling)", group: "bath coupling", pole: true },
    { key: "p_v1", label: "V1 (satellite coupling)", group: "bath coupling", pole: true },
    { key: "p_w", label: "W (Σ-pole weight)", group: "bath coupling", pole: true },
    {
      key: "p_w_gateway",
      label: "W (gateway h-sector)",
      group: "bath coupling",
      pole: true,
    },
    { key: "p_eps1", label: "ε1 (satellite position)", group: "pole position", pole: true },
    { key: "p_eta", label: "η (Σ-pole position)", group: "pole position", pole: true },
    {
      key: "p_eta_gateway",
      label: "η (gateway h-sector)",
      group: "pole position",
      pole: true,
    },
    { key: "p_lam", label: "Λ = √(η² + 2W²)", group: "lambda", pole: true },
    {
      key: "p_lam_gateway",
      label: "Λ (gateway h-sector)",
      group: "lambda",
      pole: true,
    },
    { key: "p_sumv2", label: "ΣV²", group: "sum rules", pole: true },
    { key: "p_sumw2", label: "ΣW²", group: "sum rules", pole: true },
    {
      key: "p_sumw2_gateway",
      label: "ΣW² (gateway h-sector)",
      group: "sum rules",
      pole: true,
    },
  ];

  function Dataset(id) {
    this.id = id;
    this.d = Atlas.DATA.datasets[id];
    this.n = this.d.n;
    this.grids = this.d.grids;
    this.rawD = this.d.raw_d;
    this._keyRows = null;
    this._hasCategory =
      this.d.cols.category !== undefined ||
      this.d.constants.category !== undefined;
  }

  Dataset.prototype.has = function (key) {
    if (key.slice(0, 2) === "p_") return !!this.d.poles;
    return (
      this.d.cols[key] !== undefined || this.d.constants[key] !== undefined
    );
  };

  /* Pole-derived scalars from the embedded per-row pole tables. */
  Dataset.prototype.poleNum = function (key, i) {
    var poles = this.d.poles;
    if (!poles) return null;
    var gatewayKey = {
      p_w_gateway: "p_w",
      p_eta_gateway: "p_eta",
      p_lam_gateway: "p_lam",
      p_sumw2_gateway: "p_sumw2",
    }[key];
    if (gatewayKey) {
      var gatewayFull = (poles.gateway_full || {})[String(i)];
      if (gatewayFull) {
        if (gatewayKey !== "p_sumw2" || !gatewayFull.hw) return null;
        var gatewaySum = 0;
        for (var gf = 0; gf < gatewayFull.hw.length; gf++) {
          gatewaySum += gatewayFull.hw[gf] * gatewayFull.hw[gf];
        }
        return gatewaySum;
      }
      var gateway = poles.gateway_red;
      if (!gateway) return null;
      var gw = gateway.w[i];
      var geta = gateway.eta[i];
      if (gatewayKey === "p_w") return gw;
      if (gatewayKey === "p_eta") {
        return geta === null ? null : Math.abs(geta);
      }
      if (gatewayKey === "p_lam") {
        return geta === null || gw === null
          ? null
          : Math.sqrt(geta * geta + 2 * gw * gw);
      }
      return gw === null ? null : 2 * gw * gw;
    }
    var full = poles.full[String(i)];
    if (full) {
      /* asymmetric record: only the sums are well defined */
      var sum = 0;
      var k;
      if (key === "p_sumv2") {
        for (k = 0; k < full.gv.length; k++) sum += full.gv[k] * full.gv[k];
        return sum;
      }
      if (key === "p_sumw2" && full.hw) {
        for (k = 0; k < full.hw.length; k++) sum += full.hw[k] * full.hw[k];
        return sum;
      }
      return null;
    }
    var red = poles.red;
    var v0 = red.v0[i];
    var v1 = red.v1[i];
    var eps1 = red.eps1[i];
    var w = red.w[i];
    var eta = red.eta[i];
    switch (key) {
      case "p_v0":
        return v0;
      case "p_v1":
        return v1;
      case "p_eps1":
        return eps1 === null ? null : Math.abs(eps1);
      case "p_eta":
        return eta === null ? null : Math.abs(eta);
      case "p_w":
        return w;
      case "p_lam":
        return eta === null || w === null
          ? null
          : Math.sqrt(eta * eta + 2 * w * w);
      case "p_sumv2":
        if (v0 === null && v1 === null) return null;
        return (v0 === null ? 0 : v0 * v0) + (v1 === null ? 0 : 2 * v1 * v1);
      case "p_sumw2":
        return w === null ? null : 2 * w * w;
      default:
        return null;
    }
  };

  /* Raw payload value: constants win, then the column array. */
  Dataset.prototype.raw = function (key, i) {
    if (this.d.constants[key] !== undefined) return this.d.constants[key];
    var col = this.d.cols[key];
    return col === undefined ? null : col[i];
  };

  /* Categorical value decoded to its string (or null). */
  Dataset.prototype.str = function (key, i) {
    var value = this.raw(key, i);
    if (value === null || value === undefined) return null;
    var dict = this.d.dicts[key];
    return dict ? dict[value] : String(value);
  };

  Dataset.prototype.num = function (key, i) {
    if (key.slice(0, 2) === "p_") return this.poleNum(key, i);
    var value = this.raw(key, i);
    return typeof value === "number" ? value : null;
  };

  /* Tri-state gate: 0=false, 1=true, 2=unknown (unknown !== false). */
  Dataset.prototype.tri = function (key, i) {
    var value = this.raw(key, i);
    return value === null || value === undefined ? 2 : value;
  };

  Dataset.prototype.lattice = function (i) {
    return this.str("lattice", i);
  };
  Dataset.prototype.u = function (i) {
    return this.grids[this.lattice(i)].u[this.d.cols.iu[i]];
  };
  Dataset.prototype.t = function (i) {
    return this.grids[this.lattice(i)].t[this.d.cols.it[i]];
  };

  Dataset.prototype.converged = function (i) {
    if (this._hasCategory) {
      return this.str("category", i) === "converged_branch";
    }
    return this.tri("src_converged", i) === 1;
  };

  Dataset.prototype.dictOf = function (key) {
    if (this.d.dicts[key]) return this.d.dicts[key];
    if (this.d.constants[key] !== undefined) {
      return [String(this.d.constants[key])];
    }
    return [];
  };

  /* Distinct m_g values (numeric column, usually {1,3}). */
  Dataset.prototype.mgValues = function () {
    if (this.d.constants.m_g !== undefined) return [this.d.constants.m_g];
    var seen = {};
    var col = this.d.cols.m_g;
    for (var i = 0; i < col.length; i++) seen[col[i]] = true;
    return Object.keys(seen)
      .map(Number)
      .sort(function (a, b) {
        return a - b;
      });
  };

  /* lattice -> it -> iu -> [row indices] */
  Dataset.prototype.keyRows = function () {
    if (this._keyRows) return this._keyRows;
    var map = {};
    for (var i = 0; i < this.n; i++) {
      var lattice = this.lattice(i);
      var it = this.d.cols.it[i];
      var iu = this.d.cols.iu[i];
      var byT = (map[lattice] = map[lattice] || {});
      var byU = (byT[it] = byT[it] || {});
      (byU[iu] = byU[iu] || []).push(i);
    }
    this._keyRows = map;
    return map;
  };

  /* Rows matching a plain filter object (string keys compared decoded). */
  Dataset.prototype.rowsWhere = function (filter) {
    var out = [];
    for (var i = 0; i < this.n; i++) {
      var keep = true;
      for (var key in filter) {
        var want = filter[key];
        if (want === null || want === undefined || want === "") continue;
        var got = key === "m_g" ? this.num("m_g", i) : this.str(key, i);
        if (String(got) !== String(want)) {
          keep = false;
          break;
        }
      }
      if (keep) out.push(i);
    }
    return out;
  };

  var store = {
    QTY: QTY,

    pointIds: function () {
      return Object.keys(Atlas.DATA.datasets);
    },

    primaryRoutes: function () {
      var catalog = Atlas.DATA.catalog;
      return catalog && catalog.policy && Array.isArray(catalog.policy.routes)
        ? catalog.policy.routes
        : [];
    },

    primaryRoute: function (lattice, mg) {
      var routes = store.primaryRoutes();
      for (var i = 0; i < routes.length; i++) {
        if (
          routes[i].lattice === lattice &&
          Number(routes[i].m_g) === Number(mg)
        ) {
          return routes[i];
        }
      }
      return null;
    },

    primaryLattices: function () {
      var values = [];
      store.primaryRoutes().forEach(function (route) {
        if (values.indexOf(route.lattice) < 0) values.push(route.lattice);
      });
      return values;
    },

    primaryMgValues: function (lattice) {
      var values = [];
      store.primaryRoutes().forEach(function (route) {
        if (
          route.lattice === lattice &&
          values.indexOf(Number(route.m_g)) < 0
        ) {
          values.push(Number(route.m_g));
        }
      });
      return values.sort(function (a, b) {
        return a - b;
      });
    },

    /* Normal physics views route from (lattice, m_g). Dataset and gauge
       become explicit only in supplementary-source mode. */
    applyPrimaryRoute: function (target) {
      var route = store.primaryRoute(target.lattice, Number(target.mg));
      if (!route) {
        throw new Error(
          "No primary source route for " + target.lattice + " m_g=" + target.mg
        );
      }
      if (!Atlas.DATA.datasets[route.dataset_id]) {
        throw new Error(
          "Primary source dataset is not loaded: " + route.dataset_id
        );
      }
      target.ds = route.dataset_id;
      target.gauge = route.gauge;
      return route;
    },

    /* The primary dataset: the one the gem reference is anchored to. */
    primaryId: function () {
      var gem = Atlas.DATA.references.gem;
      if (gem && Atlas.DATA.datasets[gem.anchored_to]) {
        return gem.anchored_to;
      }
      return store.pointIds()[0];
    },

    ds: (function () {
      var cache = {};
      return function (id) {
        if (!cache[id]) cache[id] = new Dataset(id);
        return cache[id];
      };
    })(),

    /* Human-facing dataset label: short handle + manifest title. */
    dsLabel: function (dsId) {
      var short =
        dsId.indexOf("gauge-matrix") >= 0
          ? "D08"
          : dsId.indexOf("scan-matrix") >= 0
            ? "D09"
            : dsId;
      var title = "";
      Atlas.DATA.meta.datasets.forEach(function (entry) {
        if (entry.id === dsId) title = entry.title;
      });
      return short + " — " + (title || dsId);
    },

    dsMeta: function (dsId) {
      var found = null;
      Atlas.DATA.meta.datasets.forEach(function (entry) {
        if (entry.id === dsId) found = entry;
      });
      return found;
    },

    /* Distinct (lattice, m_g, gauge) combinations with row counts —
       so empty selections can say what DOES exist. Cached per dataset. */
    groupCombos: function (dsId) {
      var ds = store.ds(dsId);
      if (ds._combos) return ds._combos;
      var counts = {};
      for (var i = 0; i < ds.n; i++) {
        var key =
          ds.lattice(i) + " · m_g=" + ds.num("m_g", i) + " · " +
          ds.str("gauge", i);
        counts[key] = (counts[key] || 0) + 1;
      }
      ds._combos = Object.keys(counts)
        .sort()
        .map(function (key) {
          return { label: key, rows: counts[key] };
        });
      return ds._combos;
    },

    /* First gauge (preferring `preferred`) that actually has rows for
       (lattice, m_g) — defaults must land on data, not on an empty cell. */
    pickGauge: function (dsId, lattice, mg, preferred) {
      var ds = store.ds(dsId);
      var gauges = ds.dictOf("gauge").slice();
      if (preferred && gauges.indexOf(preferred) > 0) {
        gauges.splice(gauges.indexOf(preferred), 1);
        gauges.unshift(preferred);
      }
      for (var g = 0; g < gauges.length; g++) {
        for (var i = 0; i < ds.n; i++) {
          if (
            ds.lattice(i) === lattice &&
            ds.num("m_g", i) === mg &&
            ds.str("gauge", i) === gauges[g]
          ) {
            return gauges[g];
          }
        }
      }
      return gauges[0];
    },

    qtyFor: function (ds) {
      return QTY.filter(function (q) {
        return ds.has(q.key);
      });
    },

    qty: function (key) {
      for (var i = 0; i < QTY.length; i++) {
        if (QTY[i].key === key) return QTY[i];
      }
      return null;
    },

    /* Derived branches for (ds,lattice,m_g,gauge,t,kind). */
    branch: function (dsId, lattice, mg, gauge, t, kind) {
      var branches = Atlas.DATA.derived.branches;
      for (var i = 0; i < branches.length; i++) {
        var b = branches[i];
        if (
          b.ds === dsId &&
          b.lattice === lattice &&
          b.m_g === mg &&
          b.gauge === gauge &&
          b.kind === kind &&
          Math.abs(b.t - t) < 1e-12
        ) {
          return b;
        }
      }
      return null;
    },

    ustarFor: function (dsId, lattice, mg, gauge) {
      return Atlas.DATA.derived.ustar.filter(function (e) {
        return (
          e.ds === dsId &&
          e.lattice === lattice &&
          e.m_g === mg &&
          e.gauge === gauge
        );
      });
    },

    coexFor: function (dsId, lattice, mg, gauge) {
      var maps = Atlas.DATA.derived.coex;
      for (var i = 0; i < maps.length; i++) {
        var m = maps[i];
        if (
          m.ds === dsId &&
          m.lattice === lattice &&
          m.m_g === mg &&
          m.gauge === gauge
        ) {
          return m;
        }
      }
      return null;
    },

    /* gem reference curve: values vs U at fixed it (or vs T at fixed iu).
       Junk filter: converged rows with sum R^2 <= 1.1 (the framework-native
       junk detector from the benchmark notes) unless includeJunk. */
    gemCurve: function (options) {
      var gem = Atlas.DATA.references.gem;
      if (!gem) return null;
      var latticeCode = gem.dicts.lattice.indexOf(options.lattice);
      var directionCode = gem.dicts.direction.indexOf(options.direction);
      var grids =
        Atlas.DATA.datasets[gem.anchored_to].grids[options.lattice];
      var cols = gem.cols;
      var pts = [];
      for (var i = 0; i < gem.n; i++) {
        if (
          cols.lattice[i] !== latticeCode ||
          cols.budget[i] !== options.budget ||
          cols.direction[i] !== directionCode
        ) {
          continue;
        }
        if (options.xAxis === "u" && cols.it[i] !== options.it) continue;
        if (options.xAxis === "t" && cols.iu[i] !== options.iu) continue;
        if (!cols.converged[i]) continue;
        var sumr2 = cols.sumr2[i];
        var junk = sumr2 !== null && sumr2 > 1.1;
        if (options.junkOnly) {
          if (!junk) continue;
        } else if (junk && !options.includeJunk) {
          continue;
        }
        var value = options.struct
          ? store.gemStructVal(cols, i, options.qty)
          : cols[options.qty][i];
        if (value === null) continue;
        var x =
          options.xAxis === "u" ? grids.u[cols.iu[i]] : grids.t[cols.it[i]];
        pts.push([x, value, i]);
      }
      pts.sort(function (a, b) {
        return a[0] - b[0];
      });
      return pts;
    },

    /* Framework-invariant structure values computed from gem's recorded
       pole arrays (the benchmark notes' comparison objects): our eta maps
       to gem's |Sigma-pole position|, W^2 to the pole weight, Lambda to
       the outer mode |lambda|. Bath parameters (V0, V1, eps1) have NO gem
       analog by construction — bath functions differ between frameworks.
       They do have a DMFT-ED bath analog; see edBathPoints below. */
    gemStructVal: function (cols, i, qtyKey) {
      function maxAbs(list) {
        if (!list || !list.length) return null;
        var out = 0;
        for (var k = 0; k < list.length; k++) {
          if (Math.abs(list[k]) > out) out = Math.abs(list[k]);
        }
        return out;
      }
      if (qtyKey === "p_eta") return maxAbs(cols.sig_p[i]);
      if (qtyKey === "p_eta_gateway") return maxAbs(cols.sig_p[i]);
      if (qtyKey === "p_lam") return maxAbs(cols.lam[i]);
      if (qtyKey === "p_lam_gateway") return maxAbs(cols.lam[i]);
      if (qtyKey === "p_w") {
        var weight = maxAbs(cols.sig_w[i]);
        return weight === null ? null : Math.sqrt(weight);
      }
      if (qtyKey === "p_w_gateway") {
        var gatewayWeight = maxAbs(cols.sig_w[i]);
        return gatewayWeight === null ? null : Math.sqrt(gatewayWeight);
      }
      if (qtyKey === "p_sumw2") {
        var weights = cols.sig_w[i];
        if (!weights || !weights.length) return null;
        var sum = 0;
        for (var j = 0; j < weights.length; j++) sum += weights[j];
        return sum;
      }
      if (qtyKey === "p_sumw2_gateway") {
        var gatewayWeights = cols.sig_w[i];
        if (!gatewayWeights || !gatewayWeights.length) return null;
        var gatewayTotal = 0;
        for (var g = 0; g < gatewayWeights.length; g++) {
          gatewayTotal += gatewayWeights[g];
        }
        return gatewayTotal;
      }
      return null;
    },

    gemStructLabel: function (qtyKey) {
      return {
        p_eta: "Σ-pole |position|",
        p_eta_gateway: "Σ-pole |position|",
        p_lam: "outer mode |λ|",
        p_lam_gateway: "outer mode |λ|",
        p_w: "Σ-pole √weight",
        p_w_gateway: "Σ-pole √weight",
        p_sumw2: "Σ-pole weight sum",
        p_sumw2_gateway: "Σ-pole weight sum",
      }[qtyKey] || null;
    },

    /* Map our quantity keys onto gem reference columns (null: no analog). */
    gemQty: function (qtyKey) {
      return (
        {
          z_pole: "z_slope",
          z_mats: "z_mats",
          docc: "docc",
          ekin_d: "ekin_d",
          etot_d: "etot_d",
        }[qtyKey] || null
      );
    },

    /* DMFT-ED reference points (T=0 anchors) for a lattice. Z is only
       exposed when the source table explicitly certifies its estimator;
       accepted fixed points alone are not a Z-quality statement. */
    edPoints: function (lattice, qtyKey) {
      var mapping = {
        z_pole: "Z",
        z_mats: "Z",
        docc: "docc",
        ekin_d: "ekin",
        etot_d: "etot",
      };
      var field = mapping[qtyKey];
      if (!field) return [];
      var out = [];
      var qualitySummary = {
        required: field === "Z",
        included: 0,
        omitted: 0,
        omittedUnknown: 0,
      };
      var ed = (Atlas.DATA.references || {}).ed || {};
      function harvest(table, latticeField, nbField, acceptedField) {
        if (!table) return;
        var idx = {};
        table.fields.forEach(function (name, j) {
          idx[name] = j;
        });
        var zQualityField =
          idx.Z_estimator_converged !== undefined
            ? "Z_estimator_converged"
            : idx.Z_converged !== undefined
              ? "Z_converged"
              : null;
        table.rows.forEach(function (row) {
          if (latticeField === null) {
            if (lattice !== "bethe") return; // v2 evidence ED is Bethe-only
          } else if (row[idx[latticeField]] !== lattice) {
            return;
          }
          if (
            acceptedField !== null &&
            String(row[idx[acceptedField]]) !== "1"
          ) {
            return;
          }
          var value = row[idx[field]];
          if (value === null) return;
          if (field === "Z") {
            if (zQualityField === null) {
              qualitySummary.omitted++;
              qualitySummary.omittedUnknown++;
              return;
            }
            if (String(row[idx[zQualityField]]) !== "1") {
              qualitySummary.omitted++;
              return;
            }
          }
          out.push({
            nb: row[idx[nbField]],
            u: row[idx.U_over_D],
            value: value,
            direction:
              idx.direction === undefined ? null : row[idx.direction],
            zEstimatorConverged:
              zQualityField === null
                ? null
                : String(row[idx[zQualityField]]) === "1",
            accuracyQualified:
              idx.accuracy_qualified === undefined
                ? null
                : String(row[idx.accuracy_qualified]) === "1",
          });
          qualitySummary.included++;
        });
      }
      harvest(ed.v2, null, "Nb", "accepted");
      if (lattice !== "bethe") harvest(ed.v1_legacy, "lattice", "N_b", null);
      out.qualitySummary = qualitySummary;
      return out;
    },

    /* DMFT-ED bath parameters in the same reduced convention as the ghost
       g-sector:

         Delta(z) = sum_l V_l^2 / (z - eps_l)

       Nb=1 stores [0] and [V0]. Nb=3 stores [0,+eps1,-eps1] and
       [V0,V1,V1]. Coupling signs are gauge choices, so only magnitudes are
       compared. Both continuation arms are retained: accepted Nb=1 arms
       are not numerically identical on every U point. */
    edBathPoints: function (lattice, qtyKey) {
      var supported = {
        p_v0: true,
        p_v1: true,
        p_eps1: true,
        p_sumv2: true,
      };
      var out = [];
      out.reductionSummary = {
        undefinedSatellite: 0,
        malformed: 0,
      };
      if (lattice !== "bethe" || !supported[qtyKey]) return out;
      var table = ((Atlas.DATA.references || {}).ed || {}).v2;
      if (!table) return out;
      var idx = {};
      table.fields.forEach(function (name, j) {
        idx[name] = j;
      });
      table.rows.forEach(function (row) {
        if (String(row[idx.accepted]) !== "1") return;
        var eps = row[idx.eps];
        var couplings = row[idx.V];
        if (
          !Array.isArray(eps) ||
          !Array.isArray(couplings) ||
          eps.length !== couplings.length ||
          !eps.length
        ) {
          out.reductionSummary.malformed++;
          return;
        }
        var nb = Number(row[idx.Nb]);
        var value = null;
        if (qtyKey === "p_v0") {
          value = Math.abs(couplings[0]);
        } else if (qtyKey === "p_sumv2") {
          value = couplings.reduce(function (sum, coupling) {
            return sum + coupling * coupling;
          }, 0);
        } else if (nb === 3 && eps.length === 3) {
          if (qtyKey === "p_v1") value = Math.abs(couplings[1]);
          if (qtyKey === "p_eps1") value = Math.abs(eps[1]);
        } else {
          out.reductionSummary.undefinedSatellite++;
          return;
        }
        if (value === null || !Number.isFinite(value)) {
          out.reductionSummary.malformed++;
          return;
        }
        out.push({
          nb: nb,
          u: Number(row[idx.U_over_D]),
          direction: row[idx.direction],
          value: value,
          bathQuality: row[idx.bath_approximation_quality],
          fitRelRms: row[idx.fit_rel_rms],
          accuracyQualified:
            String(row[idx.accuracy_qualified]) === "1",
        });
      });
      return out;
    },

    toCSV: function (fields, rows) {
      function cell(value) {
        if (value === null || value === undefined) return "";
        var text = String(value);
        return /[",\n]/.test(text)
          ? '"' + text.replace(/"/g, '""') + '"'
          : text;
      }
      var lines = [fields.map(cell).join(",")];
      rows.forEach(function (row) {
        lines.push(row.map(cell).join(","));
      });
      return lines.join("\n");
    },

    download: function (name, mime, content) {
      var blob = new Blob([content], { type: mime });
      var a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = name;
      a.click();
      setTimeout(function () {
        URL.revokeObjectURL(a.href);
      }, 500);
    },
  };

  Atlas.store = store;
})();
