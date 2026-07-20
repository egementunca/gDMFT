/* Closed-form semianalytic reference curves (dashed overlays).
   Brinkman-Rice: Z(U) = 1 - (U/U_BR)^2 at T -> 0, with the analytic
   U_BR/D = 32/(3π) on the Bethe lattice and the released square-scan
   endpoint 3.222 on square. Atomic limit at half filling (mu = U/2):
   docc(U, T) = 1 / (2 + 2 exp(U/2T)). */
(function () {
  "use strict";
  var Atlas = window.Atlas;

  var U_BR = { bethe: 32 / (3 * Math.PI), square: 3.222 };

  function brZ(lattice, uValues) {
    var ubr = U_BR[lattice];
    if (!ubr) return null;
    return uValues
      .filter(function (u) {
        return u <= ubr;
      })
      .map(function (u) {
        return [u, 1 - (u / ubr) * (u / ubr)];
      });
  }

  function atomicDocc(u, t) {
    return 1 / (2 + 2 * Math.exp(u / (2 * t)));
  }

  /* Reference curves for one plotted quantity in the series builder.
     xAxis: 'u' (fixed t) or 't' (fixed u); domain: sorted x values. */
  function curves(qtyKey, lattice, xAxis, fixed, domain) {
    var out = [];
    if (!domain.length) return out;
    if (qtyKey === "z_pole" || qtyKey === "z_mats") {
      if (xAxis === "u") {
        var points = brZ(lattice, domain);
        if (points && points.length > 1) {
          out.push({
            label:
              "Brinkman–Rice Z (T→0, U_BR/D=" +
              Atlas.fmt(U_BR[lattice]) +
              ")",
            points: points,
          });
        }
      }
    }
    if (qtyKey === "p_lam" && xAxis === "u") {
      /* gateway ladder: Λ approaches U/2 with growing correlation */
      out.push({
        label: "U/2 (gateway ladder)",
        points: domain.map(function (u) {
          return [u, u / 2];
        }),
      });
    }
    if (qtyKey === "docc") {
      if (xAxis === "u") {
        out.push({
          label: "atomic limit docc (T/D=" + Atlas.fmt(fixed.t) + ")",
          points: domain.map(function (u) {
            return [u, atomicDocc(u, fixed.t)];
          }),
        });
      } else {
        out.push({
          label: "atomic limit docc (U/D=" + Atlas.fmt(fixed.u) + ")",
          points: domain.map(function (t) {
            return [t, atomicDocc(fixed.u, t)];
          }),
        });
      }
    }
    return out;
  }

  Atlas.semi = { curves: curves, U_BR: U_BR };
})();
