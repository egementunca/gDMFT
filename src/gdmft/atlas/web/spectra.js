/* Real-frequency and Matsubara reconstruction from stored pole parameters.
   All inputs are in units of D (normalized at build time).

   Sigma'(z) = sum_k w_k^2 / (z - eta_k)        (Hartree U/2 removed)
   Delta(z)  = sum_j v_j^2 / (z - eps_j)
   G_loc(z)  = Hilbert[rho](z - Sigma'(z)):
     bethe:  G(zeta) = 2 (zeta - s*sqrt(zeta^2 - 1)), branch with Im G <= 0
     square: sum_k w_k / (zeta - eps_k) over the embedded DOS table
   A(omega)  = -Im G_loc(omega + i*delta) / pi */
(function () {
  "use strict";
  var Atlas = window.Atlas;

  /* complex helpers on [re, im] pairs */
  function cdiv(ar, ai, br, bi) {
    var d = br * br + bi * bi;
    return [(ar * br + ai * bi) / d, (ai * br - ar * bi) / d];
  }
  function csqrt(ar, ai) {
    var r = Math.hypot(ar, ai);
    var re = Math.sqrt((r + ar) / 2);
    var im = Math.sqrt((r - ar) / 2);
    if (ai < 0) im = -im;
    return [re, im];
  }

  function modeList(energies, amplitudes) {
    var modes = [];
    if (!energies || !amplitudes) return modes;
    for (var i = 0; i < energies.length; i++) {
      modes.push([energies[i], amplitudes[i]]);
    }
    return modes;
  }

  /* Pole parameters for one dataset row, as explicit mode lists. The
     lattice and gateway h-sectors are distinct named views. */
  function params(ds, i, hSector) {
    var poles = ds.d.poles;
    if (!poles) return null;
    hSector = hSector === "gateway" ? "gateway" : "lattice";
    var full = poles.full[String(i)];
    var gatewayFull = (poles.gateway_full || {})[String(i)];
    var h = [];
    if (hSector === "gateway") {
      if (gatewayFull) {
        h = modeList(gatewayFull.he, gatewayFull.hw);
      } else if (poles.gateway_red) {
        var gw = poles.gateway_red.w[i];
        var ge = poles.gateway_red.eta[i];
        if (gw !== null && ge !== null) {
          h = [[ge, gw], [-ge, gw]];
        }
      }
    }
    if (full) {
      if (hSector === "lattice") h = modeList(full.he, full.hw);
      return {
        g: modeList(full.ge, full.gv),
        h: h,
        full: true,
        hSector: hSector,
        hSectorsDiffer: (poles.gateway_differs || []).indexOf(i) >= 0,
        hFromR: poles.h_from_R.indexOf(i) >= 0,
      };
    }
    var red = poles.red;
    var gModes = [];
    if (red.v0[i] !== null) gModes.push([0, red.v0[i]]);
    if (red.v1[i] !== null && red.eps1[i] !== null) {
      gModes.push([red.eps1[i], red.v1[i]]);
      gModes.push([-red.eps1[i], red.v1[i]]);
    }
    if (hSector === "lattice" && red.w[i] !== null && red.eta[i] !== null) {
      h.push([red.eta[i], red.w[i]]);
      h.push([-red.eta[i], red.w[i]]);
    }
    if (!gModes.length && !h.length) return null;
    return {
      g: gModes,
      h: h,
      full: false,
      hSector: hSector,
      hSectorsDiffer: (poles.gateway_differs || []).indexOf(i) >= 0,
      hFromR: poles.h_from_R.indexOf(i) >= 0,
    };
  }

  function zFromSelfEnergyModes(modes) {
    var derivative = 0;
    for (var i = 0; i < modes.length; i++) {
      var eta = modes[i][0];
      if (eta === 0) return 0;
      derivative += (modes[i][1] * modes[i][1]) / (eta * eta);
    }
    return 1 / (1 + derivative);
  }

  function poleSum(modes, zr, zi) {
    var re = 0;
    var im = 0;
    for (var k = 0; k < modes.length; k++) {
      var weight = modes[k][1] * modes[k][1];
      var q = cdiv(weight, 0, zr - modes[k][0], zi);
      re += q[0];
      im += q[1];
    }
    return [re, im];
  }

  function gBethe(zr, zi) {
    /* G = 2 (zeta - s sqrt(zeta^2 - 1)); pick s so Im G <= 0 for zi > 0 */
    var s2 = csqrt(zr * zr - zi * zi - 1, 2 * zr * zi);
    var g1 = [2 * (zr - s2[0]), 2 * (zi - s2[1])];
    var g2 = [2 * (zr + s2[0]), 2 * (zi + s2[1])];
    return g1[1] <= 0 ? g1 : g2;
  }

  function gSquare(zr, zi) {
    var dos = Atlas.DATA.dos.square;
    var re = 0;
    var im = 0;
    for (var k = 0; k < dos.eps.length; k++) {
      var q = cdiv(dos.w[k], 0, zr - dos.eps[k], zi);
      re += q[0];
      im += q[1];
    }
    return [re, im];
  }

  function gLoc(lattice, zr, zi) {
    return lattice === "square" ? gSquare(zr, zi) : gBethe(zr, zi);
  }

  /* Real-frequency curves on a symmetric omega grid. */
  function realCurves(p, lattice, delta, omegaMax, nPoints) {
    var out = {
      omega: [],
      a: [],
      sigRe: [],
      sigIm: [],
      delRe: [],
      delIm: [],
      del0Re: [],
      gRe: [],
      gIm: [],
      gap: [],
    };
    var central = p.g.filter(function (mode) {
      return mode[0] === 0;
    });
    for (var k = 0; k <= nPoints; k++) {
      var omega = -omegaMax + (2 * omegaMax * k) / nPoints;
      var sig = poleSum(p.h, omega, delta);
      var del = poleSum(p.g, omega, delta);
      var del0 = poleSum(central, omega, delta);
      var zeta = [omega - sig[0], delta - sig[1]];
      var g = gLoc(lattice, zeta[0], zeta[1]);
      out.omega.push(omega);
      out.sigRe.push(sig[0]);
      out.sigIm.push(sig[1]);
      out.delRe.push(del[0]);
      out.delIm.push(del[1]);
      out.del0Re.push(del0[0]);
      out.gRe.push(g[0]);
      out.gIm.push(g[1]);
      out.a.push(-g[1] / Math.PI);
      out.gap.push(omega - sig[0]);
    }
    return out;
  }

  /* Matsubara curves at temperature t (units of D). */
  function matsubaraCurves(p, lattice, t, nMax) {
    var out = { wn: [], sigIm: [], delIm: [], gIm: [] };
    for (var n = 0; n < nMax; n++) {
      var wn = (2 * n + 1) * Math.PI * t;
      var sig = poleSum(p.h, 0, wn);
      var del = poleSum(p.g, 0, wn);
      var zeta = [-sig[0], wn - sig[1]];
      var g = gLoc(lattice, zeta[0], zeta[1]);
      out.wn.push(wn);
      out.sigIm.push(sig[1]);
      out.delIm.push(del[1]);
      out.gIm.push(g[1]);
    }
    return out;
  }

  /* gem self-energy pole curve (B=3 structure comparison overlay). */
  function gemSigma(sigP, sigW, delta, omegaGrid) {
    var re = [];
    var im = [];
    for (var k = 0; k < omegaGrid.length; k++) {
      var sumRe = 0;
      var sumIm = 0;
      for (var j = 0; j < sigP.length; j++) {
        var q = cdiv(sigW[j], 0, omegaGrid[k] - sigP[j], delta);
        sumRe += q[0];
        sumIm += q[1];
      }
      re.push(sumRe);
      im.push(sumIm);
    }
    return { re: re, im: im };
  }

  Atlas.spectra = {
    params: params,
    zFromSelfEnergyModes: zFromSelfEnergyModes,
    realCurves: realCurves,
    matsubaraCurves: matsubaraCurves,
    gemSigma: gemSigma,
  };
})();
