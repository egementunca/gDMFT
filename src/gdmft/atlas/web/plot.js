/* SVG plotting engine: linked line panels (one y-scale per panel — never a
   dual axis), ordinal heatmaps, crosshair + single tooltip, drag-x-zoom,
   SVG/PNG export. Palette per the validated reference instance. */
(function () {
  "use strict";
  var Atlas = window.Atlas;

  var C = {
    surface: "#fcfcfb",
    page: "#f9f9f7",
    ink: "#0b0b0b",
    ink2: "#52514e",
    muted: "#898781",
    grid: "#e1e0d9",
    axis: "#c3c2b7",
    cat: [
      "#2a78d6",
      "#1baf7a",
      "#eda100",
      "#008300",
      "#4a3aa7",
      "#e34948",
      "#e87ba4",
      "#eb6834",
    ],
    /* Entity-stable assignments (color follows the entity, never rank). */
    metal: "#2a78d6",
    insul: "#e34948",
    both: "#4a3aa7",
    exotic: "#898781",
    ours: "#2a78d6",
    gem: "#4a3aa7",
    ed: "#1baf7a",
    seq: [
      "#cde2fb",
      "#b7d3f6",
      "#9ec5f4",
      "#86b6ef",
      "#6da7ec",
      "#5598e7",
      "#3987e5",
      "#2a78d6",
      "#256abf",
      "#1c5cab",
      "#184f95",
      "#104281",
      "#0d366b",
    ],
    divMid: "#f0efec",
    divNeg: "#2a78d6",
    divPos: "#e34948",
  };
  Atlas.colors = C;

  var SVGNS = "http://www.w3.org/2000/svg";
  function S(tag, attrs, parent) {
    var node = document.createElementNS(SVGNS, tag);
    for (var key in attrs) node.setAttribute(key, attrs[key]);
    if (parent) parent.appendChild(node);
    return node;
  }
  function E(tag, className, text, parent) {
    var node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = text;
    if (parent) parent.appendChild(node);
    return node;
  }
  Atlas.E = E;

  function fmt(value) {
    if (value === null || value === undefined) return "—";
    if (value === 0) return "0";
    var abs = Math.abs(value);
    if (abs >= 1e5 || abs < 1e-4) return value.toExponential(3);
    return String(parseFloat(value.toPrecision(6)));
  }
  Atlas.fmt = fmt;

  function hexToRgb(hex) {
    return [
      parseInt(hex.slice(1, 3), 16),
      parseInt(hex.slice(3, 5), 16),
      parseInt(hex.slice(5, 7), 16),
    ];
  }
  function mix(a, b, t) {
    var ca = hexToRgb(a);
    var cb = hexToRgb(b);
    var out = "#";
    for (var i = 0; i < 3; i++) {
      out += Math.round(ca[i] + (cb[i] - ca[i]) * t)
        .toString(16)
        .padStart(2, "0");
    }
    return out;
  }
  function seqColor(t) {
    var scaled = Math.max(0, Math.min(1, t)) * (C.seq.length - 1);
    var i = Math.min(C.seq.length - 2, Math.floor(scaled));
    return mix(C.seq[i], C.seq[i + 1], scaled - i);
  }
  function divColor(t) {
    /* t in [-1, 1]: negative → blue (metal), positive → red (insulator). */
    return t < 0 ? mix(C.divMid, C.divNeg, -t) : mix(C.divMid, C.divPos, t);
  }
  Atlas.seqColor = seqColor;
  Atlas.divColor = divColor;

  /* --- axis helpers ------------------------------------------------- */
  function niceTicks(lo, hi, target) {
    if (!(hi > lo)) return [lo];
    var span = hi - lo;
    var step = Math.pow(10, Math.floor(Math.log10(span / target)));
    var err = (span / target) / step;
    if (err >= 7.5) step *= 10;
    else if (err >= 3.5) step *= 5;
    else if (err >= 1.5) step *= 2;
    var ticks = [];
    for (
      var v = Math.ceil(lo / step) * step;
      v <= hi + step * 1e-9;
      v += step
    ) {
      var tick = Math.abs(v) < Math.abs(step) * 1e-10 ? 0 : v;
      ticks.push(parseFloat(tick.toPrecision(12)));
    }
    return ticks;
  }
  function logTicks(lo, hi) {
    var ticks = [];
    for (
      var e = Math.ceil(Math.log10(lo) - 1e-9);
      e <= Math.floor(Math.log10(hi) + 1e-9);
      e++
    ) {
      ticks.push(Math.pow(10, e));
    }
    if (ticks.length < 2) return niceTicks(lo, hi, 4);
    return ticks;
  }

  function makeScale(domain, range, log) {
    var d0 = domain[0];
    var d1 = domain[1];
    if (log) {
      var l0 = Math.log10(d0);
      var l1 = Math.log10(d1);
      var scale = function (v) {
        return (
          range[0] +
          ((Math.log10(v) - l0) / (l1 - l0 || 1)) * (range[1] - range[0])
        );
      };
      scale.invert = function (p) {
        return Math.pow(
          10,
          l0 + ((p - range[0]) / (range[1] - range[0])) * (l1 - l0)
        );
      };
      scale.ticks = function () {
        return logTicks(d0, d1);
      };
      return scale;
    }
    var scaleLin = function (v) {
      return (
        range[0] + ((v - d0) / (d1 - d0 || 1)) * (range[1] - range[0])
      );
    };
    scaleLin.invert = function (p) {
      return d0 + ((p - range[0]) / (range[1] - range[0])) * (d1 - d0);
    };
    scaleLin.ticks = function (n) {
      return niceTicks(d0, d1, n || 5);
    };
    return scaleLin;
  }

  /* --- tooltip (one, shared) ---------------------------------------- */
  var tip = null;
  function tooltip() {
    if (!tip) {
      tip = E("div", "viz-tip", null, document.body);
      tip.hidden = true;
    }
    return tip;
  }
  function showTip(clientX, clientY, build) {
    var node = tooltip();
    node.innerHTML = "";
    build(node);
    node.hidden = false;
    var pad = 14;
    var rect = node.getBoundingClientRect();
    var x = clientX + pad;
    if (x + rect.width > window.innerWidth - 8) {
      x = clientX - rect.width - pad;
    }
    x = Math.max(8, Math.min(x, window.innerWidth - rect.width - 8));
    var y = Math.min(clientY + pad, window.innerHeight - rect.height - 8);
    node.style.left = x + "px";
    node.style.top = Math.max(8, y) + "px";
  }
  function hideTip() {
    if (tip) tip.hidden = true;
  }
  Atlas.hideTip = hideTip;

  function markerSymbol(marker) {
    var symbols = {
      dot: "●",
      circle: "●",
      point: "●",
      only: "●",
      open: "○",
      opoint: "○",
      square: "■",
      osquare: "□",
      diamond: "◆",
      odiamond: "◇",
      triangle: "▲",
      otriangle: "△",
      x: "×",
    };
    return symbols[marker] || null;
  }

  function htmlSeriesKey(parent, color, dash, marker) {
    var symbol = markerSymbol(marker);
    if (symbol) {
      var glyph = E("span", "viz-marker-key", symbol, parent);
      glyph.style.color = color;
      return glyph;
    }
    var key = E("span", "viz-key", null, parent);
    key.style.background = color;
    key.style.color = color;
    if (dash) key.classList.add("viz-key-dash");
    return key;
  }

  function tipRow(node, color, label, value, dash, marker) {
    var row = E("div", "viz-tip-row", null, node);
    var keyWrap = E("span", "viz-tip-key", null, row);
    if (color) htmlSeriesKey(keyWrap, color, dash, marker);
    E("span", "viz-tip-value", value, row);
    E("span", "viz-tip-label", label, row);
  }

  function drawSeriesMarker(parent, marker, cx, cy, series) {
    var color = series.color;
    var small = marker === "point" || marker === "opoint";
    var radius = series.markerSize || (small ? 2.8 : series.big ? 5 : 4);
    var open =
      marker === "open" ||
      marker === "opoint" ||
      marker === "osquare" ||
      marker === "odiamond" ||
      marker === "otriangle";
    var fill = open ? C.surface : color;
    var stroke = open ? color : C.surface;
    var strokeWidth = open ? 1.7 : 1.5;

    if (marker === "x") {
      var cross = S(
        "g",
        { stroke: color, "stroke-width": 1.8, "stroke-linecap": "round" },
        parent
      );
      S(
        "line",
        {
          x1: cx - radius,
          y1: cy - radius,
          x2: cx + radius,
          y2: cy + radius,
        },
        cross
      );
      S(
        "line",
        {
          x1: cx - radius,
          y1: cy + radius,
          x2: cx + radius,
          y2: cy - radius,
        },
        cross
      );
      return;
    }
    if (marker === "square" || marker === "osquare") {
      S(
        "rect",
        {
          x: cx - radius,
          y: cy - radius,
          width: 2 * radius,
          height: 2 * radius,
          rx: 0.8,
          fill: fill,
          stroke: stroke,
          "stroke-width": strokeWidth,
        },
        parent
      );
      return;
    }
    if (marker === "diamond" || marker === "odiamond") {
      S(
        "polygon",
        {
          points:
            cx + "," + (cy - radius - 0.5) + " " +
            (cx + radius + 0.5) + "," + cy + " " +
            cx + "," + (cy + radius + 0.5) + " " +
            (cx - radius - 0.5) + "," + cy,
          fill: fill,
          stroke: stroke,
          "stroke-width": strokeWidth,
        },
        parent
      );
      return;
    }
    if (marker === "triangle" || marker === "otriangle") {
      S(
        "polygon",
        {
          points:
            cx + "," + (cy - radius - 0.8) + " " +
            (cx + radius + 0.8) + "," + (cy + radius) + " " +
            (cx - radius - 0.8) + "," + (cy + radius),
          fill: fill,
          stroke: stroke,
          "stroke-width": strokeWidth,
        },
        parent
      );
      return;
    }
    S(
      "circle",
      {
        cx: cx,
        cy: cy,
        r: radius,
        fill: fill,
        stroke: stroke,
        "stroke-width": strokeWidth,
      },
      parent
    );
  }

  /* --- figure: stacked panels, shared x ------------------------------ */
  /* spec = { width?, xLabel, xLog?, xDomain?, panels: [{ yLabel, yLog?, height?,
       series: [{ label, color, points [[x,y]|y null], dash?, marker?
                  ('dot'|'open'|'x'|'none'), big? }],
       vlines: [{x,label}], hlines: [{y,label}] }],
     onPointClick?(series, point) } */
  function figure(spec) {
    var container = E("div", "viz-figure");
    var width = spec.width || 900;
    var margin = { left: 64, right: 16 };
    var fullDomain = xDomainOf(spec);
    var domain = fullDomain.slice();
    var zoomHistory = [];
    var svgs = [];

    function xDomainOf(figSpec) {
      if (
        Array.isArray(figSpec.xDomain) &&
        figSpec.xDomain.length === 2 &&
        Number.isFinite(Number(figSpec.xDomain[0])) &&
        Number.isFinite(Number(figSpec.xDomain[1])) &&
        Number(figSpec.xDomain[1]) > Number(figSpec.xDomain[0])
      ) {
        return [Number(figSpec.xDomain[0]), Number(figSpec.xDomain[1])];
      }
      var lo = Infinity;
      var hi = -Infinity;
      figSpec.panels.forEach(function (panel) {
        panel.series.forEach(function (series) {
          series.points.forEach(function (point) {
            if (!point) return;
            if (point[0] < lo) lo = point[0];
            if (point[0] > hi) hi = point[0];
          });
        });
      });
      if (!(hi > lo)) {
        lo = 0;
        hi = 1;
      }
      /* Auto-computed range only: pad so markers at the extreme x values
         are not half-clipped by the plot border. An explicit xDomain
         stays exact (References passes its own padded window). */
      if (figSpec.xLog) {
        if (lo <= 0) lo = 1e-16;
        return [lo / 1.05, hi * 1.05];
      }
      var pad = (hi - lo) * 0.025;
      return [lo - pad, hi + pad];
    }

    function render() {
      container.innerHTML = "";
      svgs.length = 0;
      var zoomTools = E("div", "viz-zoom-tools", null, container);
      zoomTools.hidden =
        zoomHistory.length === 0 &&
        domain[0] === fullDomain[0] &&
        domain[1] === fullDomain[1];
      var zoomOut = E("button", "btn viz-zoom-btn", "− Zoom out", zoomTools);
      zoomOut.type = "button";
      zoomOut.title = "Return to the previous horizontal zoom";
      zoomOut.setAttribute("aria-label", "Zoom out one level");
      zoomOut.disabled = zoomHistory.length === 0;
      zoomOut.addEventListener("click", function () {
        if (!zoomHistory.length) return;
        domain = zoomHistory.pop();
        render();
      });
      var resetZoom = E(
        "button",
        "btn viz-zoom-btn",
        "↺ Reset zoom",
        zoomTools
      );
      resetZoom.type = "button";
      resetZoom.title = "Restore the complete horizontal range";
      resetZoom.setAttribute("aria-label", "Reset horizontal zoom");
      resetZoom.disabled =
        zoomHistory.length === 0 &&
        domain[0] === fullDomain[0] &&
        domain[1] === fullDomain[1];
      resetZoom.addEventListener("click", function () {
        domain = fullDomain.slice();
        zoomHistory = [];
        render();
      });
      var xTickH = 34;
      spec.panels.forEach(function (panel, panelIndex) {
        var last = panelIndex === spec.panels.length - 1;
        var height = (panel.height || 240) + (last ? xTickH : 6);
        var svg = S("svg", {
          viewBox: "0 0 " + width + " " + height,
          width: "100%",
          "font-family":
            'system-ui, -apple-system, "Segoe UI", sans-serif',
        });
        svg.style.display = "block";
        container.appendChild(svg);
        svgs.push(svg);
        drawPanel(svg, panel, last, height, xTickH);
      });
      if (spec.xLabel) {
        E("div", "viz-x-label", spec.xLabel, container);
      }
      var legendSeries = [];
      var legendSeen = {};
      spec.panels.forEach(function (panel) {
        panel.series.forEach(function (series) {
          var key = series.legendKey || series.label;
          if (!series.skipLegend && !legendSeen[key]) {
            legendSeen[key] = true;
            legendSeries.push(series);
          }
        });
      });
      if (legendSeries.length >= 2) {
        container.appendChild(legend(legendSeries));
      }
    }

    function yDomainOf(panel) {
      var lo = Infinity;
      var hi = -Infinity;
      panel.series.forEach(function (series) {
        series.points.forEach(function (point) {
          if (!point || point[1] === null) return;
          if (point[0] < domain[0] - 1e-12 || point[0] > domain[1] + 1e-12) {
            return;
          }
          if (point[1] < lo) lo = point[1];
          if (point[1] > hi) hi = point[1];
        });
      });
      (panel.hlines || []).forEach(function (line) {
        if (line.y < lo) lo = line.y;
        if (line.y > hi) hi = line.y;
      });
      if (!(hi >= lo)) {
        lo = 0;
        hi = 1;
      }
      if (panel.yLog) {
        if (lo <= 0) lo = 1e-16;
        return [lo / 1.5, hi * 1.5];
      }
      var pad = (hi - lo || Math.abs(hi) || 1) * 0.06;
      return [lo - pad, hi + pad];
    }

    function drawPanel(svg, panel, withXAxis, height, xTickH) {
      var top = 10;
      var plotH = height - top - (withXAxis ? xTickH : 6);
      var plotX = [margin.left, width - margin.right];
      var xScale = makeScale(domain, plotX, spec.xLog);
      var yScale = makeScale(yDomainOf(panel), [top + plotH, top], panel.yLog);

      S(
        "rect",
        {
          x: plotX[0],
          y: top,
          width: plotX[1] - plotX[0],
          height: plotH,
          fill: C.surface,
        },
        svg
      );

      /* gridlines: hairline, solid, recessive */
      yScale.ticks(4).forEach(function (tickValue) {
        var y = yScale(tickValue);
        if (y < top - 0.5 || y > top + plotH + 0.5) return;
        S(
          "line",
          {
            x1: plotX[0],
            x2: plotX[1],
            y1: y,
            y2: y,
            stroke: C.grid,
            "stroke-width": 1,
          },
          svg
        );
        var label = S(
          "text",
          {
            x: plotX[0] - 8,
            y: y + 3.5,
            "text-anchor": "end",
            "font-size": 11,
            fill: C.muted,
          },
          svg
        );
        label.textContent = panel.yLog
          ? "1e" + Math.round(Math.log10(tickValue))
          : fmt(tickValue);
      });
      if (withXAxis) {
        xScale.ticks(8).forEach(function (tickValue) {
          var x = xScale(tickValue);
          if (x < plotX[0] - 0.5 || x > plotX[1] + 0.5) return;
          S(
            "line",
            {
              x1: x,
              x2: x,
              y1: top + plotH,
              y2: top + plotH + 4,
              stroke: C.axis,
              "stroke-width": 1,
            },
            svg
          );
          var label = S(
            "text",
            {
              x: x,
              y: top + plotH + 17,
              "text-anchor": "middle",
              "font-size": 11,
              fill: C.muted,
            },
            svg
          );
          label.textContent = spec.xLog
            ? fmt(tickValue)
            : fmt(tickValue);
        });
      }
      S(
        "line",
        {
          x1: plotX[0],
          x2: plotX[1],
          y1: top + plotH,
          y2: top + plotH,
          stroke: C.axis,
          "stroke-width": 1,
        },
        svg
      );

      /* reference vlines (dashed = threshold semantics, not grid) */
      (panel.vlines || []).forEach(function (line) {
        if (line.x < domain[0] || line.x > domain[1]) return;
        var x = xScale(line.x);
        S(
          "line",
          {
            x1: x,
            x2: x,
            y1: top,
            y2: top + plotH,
            stroke: line.color || C.ink2,
            "stroke-width": 1,
            "stroke-dasharray": "4 3",
          },
          svg
        );
        if (line.label) {
          var text = S(
            "text",
            {
              x: x + 4,
              y: top + 12,
              "font-size": 10.5,
              fill: C.ink2,
            },
            svg
          );
          text.textContent = line.label;
        }
      });
      (panel.hlines || []).forEach(function (line) {
        var y = yScale(line.y);
        S(
          "line",
          {
            x1: plotX[0],
            x2: plotX[1],
            y1: y,
            y2: y,
            stroke: line.color || C.ink2,
            "stroke-width": 1,
            "stroke-dasharray": "4 3",
          },
          svg
        );
      });

      /* series */
      var clipId = "clip" + Math.random().toString(36).slice(2, 8);
      var clip = S("clipPath", { id: clipId }, svg);
      S(
        "rect",
        { x: plotX[0], y: top - 6, width: plotX[1] - plotX[0], height: plotH + 12 },
        clip
      );
      var plotGroup = S("g", { "clip-path": "url(#" + clipId + ")" }, svg);

      function visiblePoints(series) {
        return series.points.filter(function (point) {
          return (
            point &&
            point[1] !== null &&
            point[0] >= domain[0] - 1e-12 &&
            point[0] <= domain[1] + 1e-12 &&
            (!panel.yLog || point[1] > 0)
          );
        });
      }

      /* Draw all connecting paths first, then every marker. A later series
         can no longer paint a line over an earlier method's data points. */
      panel.series.forEach(function (series) {
        var legacyMarkerOnly =
          series.marker === "only" ||
          series.marker === "point" ||
          series.marker === "opoint";
        if (
          series.connect !== false &&
          (series.connect === true || !legacyMarkerOnly)
        ) {
          var path = "";
          var pen = false;
          series.points.forEach(function (point) {
            if (!point || point[1] === null || (panel.yLog && point[1] <= 0)) {
              pen = false;
              return;
            }
            var command = pen ? "L" : "M";
            path +=
              command + xScale(point[0]) + " " + yScale(point[1]) + " ";
            pen = true;
          });
          S(
            "path",
            {
              d: path,
              fill: "none",
              stroke: series.color,
              "stroke-width": series.marker && series.marker !== "none" ? 1.4 : 2,
              opacity:
                series.marker && series.marker !== "none" ? 0.58 : 1,
              "stroke-linejoin": "round",
              "stroke-linecap": "round",
              "stroke-dasharray": series.dash ? "5 4" : "none",
            },
            plotGroup
          );
        }
      });
      panel.series
        .slice()
        .sort(function (a, b) {
          return (a.markerOrder || 0) - (b.markerOrder || 0);
        })
        .forEach(function (series) {
        var visible = visiblePoints(series);
        var marker = series.marker || (visible.length <= 40 ? "dot" : "none");
        if (marker !== "none") {
          visible.forEach(function (point) {
            var cx = xScale(point[0]);
            var cy = yScale(point[1]);
            drawSeriesMarker(plotGroup, marker, cx, cy, series);
          });
        }
        });

      /* crosshair + hover layer */
      var hover = S(
        "rect",
        {
          x: plotX[0],
          y: top,
          width: plotX[1] - plotX[0],
          height: plotH,
          fill: "transparent",
          cursor: "crosshair",
        },
        svg
      );
      var crossLine = S(
        "line",
        {
          y1: top,
          y2: top + plotH,
          stroke: C.axis,
          "stroke-width": 1,
          visibility: "hidden",
          "pointer-events": "none",
        },
        svg
      );
      var zoomRect = S(
        "rect",
        {
          y: top,
          height: plotH,
          fill: C.cat[0],
          opacity: 0.12,
          visibility: "hidden",
          "pointer-events": "none",
        },
        svg
      );

      var allX = allXPositions(panel);
      function clientToX(event) {
        var rect = svg.getBoundingClientRect();
        var px =
          ((event.clientX - rect.left) / rect.width) * width;
        return xScale.invert(px);
      }
      var dragStart = null;
      hover.addEventListener("pointerdown", function (event) {
        dragStart = clientToX(event);
        hover.setPointerCapture(event.pointerId);
      });
      hover.addEventListener("pointermove", function (event) {
        var xValue = clientToX(event);
        if (dragStart !== null) {
          var a = xScale(Math.min(dragStart, xValue));
          var b = xScale(Math.max(dragStart, xValue));
          zoomRect.setAttribute("x", a);
          zoomRect.setAttribute("width", Math.max(0, b - a));
          zoomRect.setAttribute("visibility", "visible");
        }
        var snapped = nearest(allX, xValue);
        if (snapped === null) return;
        broadcastCross(snapped);
        showTip(event.clientX, event.clientY, function (node) {
          E(
            "div",
            "viz-tip-head",
            panel.yLabel + " · " + spec.xLabel + " = " + fmt(snapped),
            node
          );
          var rows = [];
          panel.series.forEach(function (series) {
            var value = valueAt(series, snapped);
            if (value === undefined) return;
            rows.push({ series: series, value: value });
          });
          rows.slice(0, 8).forEach(function (entry) {
            tipRow(
              node,
              entry.series.color,
              entry.series.tipLabel || entry.series.label,
              fmt(entry.value),
              entry.series.dash,
              entry.series.marker
            );
          });
          if (rows.length > 8) {
            E(
              "div",
              "viz-tip-more",
              "+" + (rows.length - 8) + " more in this panel",
              node
            );
          }
        });
      });
      hover.addEventListener("pointerup", function (event) {
        if (dragStart === null) return;
        var xEnd = clientToX(event);
        zoomRect.setAttribute("visibility", "hidden");
        var lo = Math.min(dragStart, xEnd);
        var hi = Math.max(dragStart, xEnd);
        dragStart = null;
        if (
          Math.abs(xScale(hi) - xScale(lo)) > 8 &&
          hi > lo
        ) {
          zoomHistory.push(domain.slice());
          domain = [lo, hi];
          render();
        }
      });
      hover.addEventListener("pointercancel", function () {
        dragStart = null;
        zoomRect.setAttribute("visibility", "hidden");
        broadcastCross(null);
        hideTip();
      });
      hover.addEventListener("pointerleave", function () {
        dragStart = null;
        zoomRect.setAttribute("visibility", "hidden");
        broadcastCross(null);
        hideTip();
      });
      hover.addEventListener("dblclick", function () {
        domain = fullDomain.slice();
        zoomHistory = [];
        render();
      });

      svg._cross = function (xValue) {
        if (xValue === null) {
          crossLine.setAttribute("visibility", "hidden");
          return;
        }
        var x = xScale(xValue);
        crossLine.setAttribute("x1", x);
        crossLine.setAttribute("x2", x);
        crossLine.setAttribute("visibility", "visible");
      };

      /* y label */
      if (panel.yLabel) {
        var yLabel = S(
          "text",
          {
            x: 14,
            y: top + plotH / 2,
            transform:
              "rotate(-90 14 " + (top + plotH / 2) + ")",
            "text-anchor": "middle",
            "font-size": 11.5,
            fill: C.ink2,
          },
          svg
        );
        yLabel.textContent = panel.yLabel;
      }
    }

    function allXPositions(panel) {
      var seen = {};
      panel.series.forEach(function (series) {
        series.points.forEach(function (point) {
          if (point && point[1] !== null) seen[point[0]] = true;
        });
      });
      return Object.keys(seen)
        .map(Number)
        .sort(function (a, b) {
          return a - b;
        });
    }
    function nearest(sorted, value) {
      if (!sorted.length) return null;
      var lo = 0;
      var hi = sorted.length - 1;
      while (hi - lo > 1) {
        var mid = (lo + hi) >> 1;
        if (sorted[mid] < value) lo = mid;
        else hi = mid;
      }
      return Math.abs(sorted[lo] - value) < Math.abs(sorted[hi] - value)
        ? sorted[lo]
        : sorted[hi];
    }
    function valueAt(series, xValue) {
      for (var i = 0; i < series.points.length; i++) {
        var point = series.points[i];
        if (point && Math.abs(point[0] - xValue) < 1e-12) return point[1];
      }
      return undefined;
    }
    function broadcastCross(xValue) {
      svgs.forEach(function (svg) {
        if (svg._cross) svg._cross(xValue);
      });
    }

    render();
    return { el: container, svgs: svgs };
  }

  function legend(seriesList) {
    var box = E("div", "viz-legend");
    seriesList.forEach(function (series) {
      var chip = E("span", "viz-legend-chip", null, box);
      htmlSeriesKey(chip, series.color, series.dash, series.marker);
      E("span", null, series.label, chip);
    });
    return box;
  }
  Atlas.legendBox = legend;

  /* --- heatmap -------------------------------------------------------- */
  /* spec = { uValues, tValues, value(it,iu) -> number|null (or code),
       mode: 'seq'|'div'|'cat', catColors {code:hex}, catLabels {code:label},
       label, tipExtra?(it,iu,node), onClick?(it,iu), overlay: [[u,t]...],
       overlayLabel, width? } */
  function heatmap(spec) {
    var container = E("div", "viz-figure");
    var width = spec.width || 900;
    var margin = { left: 64, right: 18, top: 8, bottom: 40 };
    var nU = spec.uValues.length;
    var nT = spec.tValues.length;
    var cellW = (width - margin.left - margin.right) / nU;
    var cellH = Math.max(11, Math.min(24, 380 / nT));
    var plotH = cellH * nT;
    var height = margin.top + plotH + margin.bottom;
    var svg = S("svg", {
      viewBox: "0 0 " + width + " " + height,
      width: "100%",
      "font-family": 'system-ui, -apple-system, "Segoe UI", sans-serif',
    });
    container.appendChild(svg);

    var values = [];
    var lo = Infinity;
    var hi = -Infinity;
    for (var it = 0; it < nT; it++) {
      for (var iu = 0; iu < nU; iu++) {
        var value = spec.value(it, iu);
        values.push(value);
        if (spec.mode !== "cat" && value !== null) {
          if (value < lo) lo = value;
          if (value > hi) hi = value;
        }
      }
    }
    if (spec.mode === "div") {
      /* robust symmetric domain: 95th percentile of |v|, so a few large
         far-from-crossing cells don't wash out the structure near ΔΩ=0;
         cells beyond the domain clamp to the pole colors */
      var magnitudes = values
        .filter(function (value) {
          return value !== null;
        })
        .map(Math.abs)
        .sort(function (a, b) {
          return a - b;
        });
      var mag =
        magnitudes[Math.floor(magnitudes.length * 0.95)] ||
        magnitudes[magnitudes.length - 1] ||
        1;
      lo = -mag;
      hi = mag;
    }
    if (!(hi > lo)) {
      hi = lo + 1;
    }

    function cellColor(value) {
      if (value === null) return C.page;
      if (spec.mode === "cat") return spec.catColors[value] || C.page;
      if (spec.mode === "div") {
        return divColor(Math.max(-1, Math.min(1, value / hi)));
      }
      return seqColor((value - lo) / (hi - lo));
    }

    function yOf(it) {
      /* low T at the bottom */
      return margin.top + (nT - 1 - it) * cellH;
    }

    /* the surface gap between cells only exists when cells can afford it —
       on ragged sub-3px grids the gap would swallow the fill */
    var gap = cellW >= 3 ? 0.5 : 0;
    for (it = 0; it < nT; it++) {
      for (iu = 0; iu < nU; iu++) {
        var v = values[it * nU + iu];
        var rect = S(
          "rect",
          {
            x: margin.left + iu * cellW + gap,
            y: yOf(it) + 0.5,
            width: Math.max(0.5, cellW - 2 * gap),
            height: cellH - 1,
            fill: cellColor(v),
          },
          svg
        );
        (function (it2, iu2, v2, rect2) {
          rect2.addEventListener("pointermove", function (event) {
            rect2.setAttribute("stroke", C.ink);
            rect2.setAttribute("stroke-width", 1);
            showTip(event.clientX, event.clientY, function (node) {
              E(
                "div",
                "viz-tip-head",
                "U/D = " +
                  fmt(spec.uValues[iu2]) +
                  " · T/D = " +
                  fmt(spec.tValues[it2]),
                node
              );
              var label =
                spec.mode === "cat"
                  ? spec.catLabels[v2] || "—"
                  : fmt(v2);
              tipRow(node, cellColor(v2), spec.label, label, false);
              if (spec.tipExtra) spec.tipExtra(it2, iu2, node);
            });
          });
          rect2.addEventListener("pointerleave", function () {
            rect2.removeAttribute("stroke");
            hideTip();
          });
          if (spec.onClick) {
            rect2.style.cursor = "pointer";
            rect2.addEventListener("click", function () {
              spec.onClick(it2, iu2);
            });
          }
        })(it, iu, v, rect);
      }
    }

    /* axis tick labels: the U axis is CATEGORICAL (one equal-width column
       per grid value), and the union grid is non-uniform (0.05 coarse +
       0.01 windows), so every-Nth-column ticks land on ragged values.
       Instead tick the columns nearest to round U values. */
    var uTickIdx = [];
    if (nU) {
      var uLoVal = spec.uValues[0];
      var uHiVal = spec.uValues[nU - 1];
      var stepU = (uHiVal - uLoVal) / 8;
      var mag = Math.pow(10, Math.floor(Math.log(stepU) / Math.LN10));
      var norm = stepU / mag;
      var niceStep = (norm < 1.5 ? 1 : norm < 3.5 ? 2 : norm < 7.5 ? 5 : 10)
        * mag;
      var used = {};
      for (var uv = Math.ceil(uLoVal / niceStep) * niceStep;
           uv <= uHiVal + 1e-9; uv += niceStep) {
        var bestI = 0;
        for (var k = 1; k < nU; k++) {
          if (Math.abs(spec.uValues[k] - uv)
              < Math.abs(spec.uValues[bestI] - uv)) bestI = k;
        }
        if (!used[bestI]) { used[bestI] = true; uTickIdx.push(bestI); }
      }
    }
    for (var ti = 0; ti < uTickIdx.length; ti++) {
      iu = uTickIdx[ti];
      var uText = S(
        "text",
        {
          x: margin.left + (iu + 0.5) * cellW,
          y: margin.top + plotH + 15,
          "text-anchor": "middle",
          "font-size": 10.5,
          fill: C.muted,
        },
        svg
      );
      uText.textContent = fmt(spec.uValues[iu]);
    }
    var tEvery = Math.max(1, Math.ceil(nT / 12));
    for (it = 0; it < nT; it += tEvery) {
      var tText = S(
        "text",
        {
          x: margin.left - 7,
          y: yOf(it) + cellH / 2 + 3.5,
          "text-anchor": "end",
          "font-size": 10.5,
          fill: C.muted,
        },
        svg
      );
      tText.textContent = fmt(spec.tValues[it]);
    }
    var xAxisLabel = S(
      "text",
      {
        x: margin.left + (width - margin.left - margin.right) / 2,
        y: margin.top + plotH + 32,
        "text-anchor": "middle",
        "font-size": 11.5,
        fill: C.ink2,
      },
      svg
    );
    xAxisLabel.textContent = "U/D";
    var yAxisLabel = S(
      "text",
      {
        x: 14,
        y: margin.top + plotH / 2,
        transform: "rotate(-90 14 " + (margin.top + plotH / 2) + ")",
        "text-anchor": "middle",
        "font-size": 11.5,
        fill: C.ink2,
      },
      svg
    );
    yAxisLabel.textContent = "T/D";

    /* overlay polyline (e.g. the U*(T) line) in data coordinates */
    if (spec.overlay && spec.overlay.length > 1) {
      var uIndex = {};
      spec.uValues.forEach(function (u, i) {
        uIndex[u] = i;
      });
      var path = "";
      var pen = false;
      spec.overlay.forEach(function (point) {
        var uPos = interpIndex(spec.uValues, point[0]);
        var tPos = spec.tValues.indexOf(point[1]);
        if (uPos === null || tPos < 0) {
          pen = false;
          return;
        }
        var x = margin.left + (uPos + 0.5) * cellW;
        var y = yOf(tPos) + cellH / 2;
        path += (pen ? "L" : "M") + x + " " + y + " ";
        pen = true;
      });
      S(
        "path",
        {
          d: path,
          fill: "none",
          stroke: C.ink,
          "stroke-width": 2,
          "stroke-linejoin": "round",
          "stroke-dasharray": "6 4",
          "pointer-events": "none",
        },
        svg
      );
    }

    /* scale legend */
    var legendBox = E("div", "viz-scalebar", null, container);
    if (spec.mode === "cat") {
      Object.keys(spec.catLabels).forEach(function (code) {
        var chip = E("span", "viz-legend-chip", null, legendBox);
        var key = E("span", "viz-key viz-key-rect", null, chip);
        key.style.background = spec.catColors[code];
        E("span", null, spec.catLabels[code], chip);
      });
    } else {
      var bar = E("span", "viz-gradient", null, legendBox);
      var stops = [];
      for (var s = 0; s <= 10; s++) {
        var t = s / 10;
        stops.push(
          (spec.mode === "div" ? divColor(t * 2 - 1) : seqColor(t)) +
            " " +
            t * 100 +
            "%"
        );
      }
      bar.style.background = "linear-gradient(90deg," + stops.join(",") + ")";
      E("span", "muted", fmt(lo), legendBox);
      E("span", "viz-scalebar-label", spec.label, legendBox);
      E("span", "muted", fmt(hi), legendBox);
    }
    if (spec.overlay && spec.overlay.length > 1 && spec.overlayLabel) {
      var overlayChip = E("span", "viz-legend-chip", null, legendBox);
      var overlayKey = E("span", "viz-key viz-key-dash", null, overlayChip);
      overlayKey.style.background = C.ink;
      E("span", null, spec.overlayLabel, overlayChip);
    }

    return { el: container, svgs: [svg] };
  }

  /* --- pole map ------------------------------------------------------- */
  /* Analytic-structure scatter: pole POSITION on y (energy /D), U/D on x,
     each pole's WEIGHT encoded by marker color (log ramp by default). A
     pole whose weight falls below `threshold` is drawn as a muted × so a
     coupling's death (V0 → 0 near the Mott edge) is visible at a glance.
     Marker SHAPE encodes the pole family, leaving color free for weight —
     the caller picks which branch(es) to show; nothing forces metal and
     insulator together. Per-marker hover reports the exact weight.
     spec = { width?, height?, xLabel?, yLabel?, t, threshold, logColor?,
       markers: [{ u, pos, weight, shape, family, branch }],
       uDomain?, yDomain?, vlines?: [{x,label}],
       shapeLegend?: [{shape,label}], scaleLabel? } */
  function poleMap(spec) {
    var container = E("div", "viz-figure");
    var width = spec.width || 900;
    var margin = { left: 66, right: 16, top: 12, bottom: 40 };
    var plotH = spec.height || 430;
    var height = margin.top + plotH + margin.bottom;
    var svg = S("svg", {
      viewBox: "0 0 " + width + " " + height,
      width: "100%",
      "font-family": 'system-ui, -apple-system, "Segoe UI", sans-serif',
    });
    svg.style.display = "block";
    container.appendChild(svg);

    var markers = spec.markers.filter(function (m) {
      return (
        m &&
        m.weight !== null && m.weight !== undefined &&
        m.pos !== null && m.pos !== undefined &&
        m.u !== null && m.u !== undefined
      );
    });
    var plotX = [margin.left, width - margin.right];
    var plotY = [margin.top + plotH, margin.top];

    var us = markers.map(function (m) { return m.u; });
    var uLo, uHi;
    if (spec.uDomain) {
      uLo = spec.uDomain[0]; uHi = spec.uDomain[1];
    } else if (us.length) {
      uLo = Math.min.apply(null, us); uHi = Math.max.apply(null, us);
      var padU = (uHi - uLo) * 0.03 || 0.1; uLo -= padU; uHi += padU;
    } else { uLo = 0; uHi = 1; }

    var poss = markers.map(function (m) { return m.pos; });
    var yLo, yHi;
    if (spec.yDomain) {
      yLo = spec.yDomain[0]; yHi = spec.yDomain[1];
    } else if (poss.length) {
      yLo = Math.min.apply(null, poss); yHi = Math.max.apply(null, poss);
      var padY = (yHi - yLo) * 0.08 || 0.1; yLo -= padY; yHi += padY;
    } else { yLo = -1; yHi = 1; }

    var xScale = makeScale([uLo, uHi], plotX, false);
    var yScale = makeScale([yLo, yHi], plotY, false);

    var positiveWeights = markers
      .map(function (m) { return m.weight; })
      .filter(function (w) { return w > 0; });
    var wLo = positiveWeights.length
      ? Math.min.apply(null, positiveWeights) : 1e-6;
    var wHi = positiveWeights.length
      ? Math.max.apply(null, positiveWeights) : 1;
    if (!(wHi > wLo)) wHi = wLo * 10 || 1;
    var logColor = spec.logColor !== false;
    function weightColor(w) {
      var t = logColor
        ? (Math.log10(w) - Math.log10(wLo)) /
          (Math.log10(wHi) - Math.log10(wLo) || 1)
        : (w - wLo) / (wHi - wLo || 1);
      return seqColor(Math.max(0, Math.min(1, t)));
    }

    S("rect", {
      x: plotX[0], y: margin.top, width: plotX[1] - plotX[0],
      height: plotH, fill: C.surface,
    }, svg);

    /* y gridlines (position); the pos=0 line is emphasized */
    yScale.ticks(6).forEach(function (tv) {
      var y = yScale(tv);
      if (y < margin.top - 0.5 || y > margin.top + plotH + 0.5) return;
      var zero = Math.abs(tv) < 1e-9;
      S("line", {
        x1: plotX[0], x2: plotX[1], y1: y, y2: y,
        stroke: zero ? C.axis : C.grid, "stroke-width": zero ? 1.4 : 1,
      }, svg);
      var lab = S("text", {
        x: plotX[0] - 8, y: y + 3.5, "text-anchor": "end",
        "font-size": 11, fill: C.muted,
      }, svg);
      lab.textContent = fmt(tv);
    });
    /* x ticks (U/D) */
    xScale.ticks(8).forEach(function (tv) {
      var x = xScale(tv);
      if (x < plotX[0] - 0.5 || x > plotX[1] + 0.5) return;
      S("line", {
        x1: x, x2: x, y1: margin.top, y2: margin.top + plotH,
        stroke: C.grid, "stroke-width": 1,
      }, svg);
      var lab = S("text", {
        x: x, y: margin.top + plotH + 16, "text-anchor": "middle",
        "font-size": 11, fill: C.muted,
      }, svg);
      lab.textContent = fmt(tv);
    });
    /* reference vlines (e.g. U*) */
    (spec.vlines || []).forEach(function (v) {
      var x = xScale(v.x);
      if (x < plotX[0] || x > plotX[1]) return;
      S("line", {
        x1: x, x2: x, y1: margin.top, y2: margin.top + plotH,
        stroke: C.ink2, "stroke-width": 1.2, "stroke-dasharray": "5 4",
      }, svg);
      if (v.label) {
        var lab = S("text", {
          x: x + 4, y: margin.top + 12, "font-size": 10.5, fill: C.ink2,
        }, svg);
        lab.textContent = v.label;
      }
    });
    /* axis labels */
    var xl = S("text", {
      x: plotX[0] + (plotX[1] - plotX[0]) / 2, y: height - 6,
      "text-anchor": "middle", "font-size": 11.5, fill: C.ink2,
    }, svg);
    xl.textContent = spec.xLabel || "U/D";
    var yl = S("text", {
      x: 15, y: margin.top + plotH / 2,
      transform: "rotate(-90 15 " + (margin.top + plotH / 2) + ")",
      "text-anchor": "middle", "font-size": 11.5, fill: C.ink2,
    }, svg);
    yl.textContent = spec.yLabel || "pole position /D";

    /* markers: alive = weight-colored shape, dead = muted × */
    var below = 0;
    markers.forEach(function (m) {
      var cx = xScale(m.u), cy = yScale(m.pos);
      if (cx < plotX[0] - 3 || cx > plotX[1] + 3) return;
      if (cy < margin.top - 3 || cy > margin.top + plotH + 3) return;
      var dead = m.weight < spec.threshold;
      var group = S("g", {}, svg);
      var shownColor;
      if (dead) {
        below++;
        shownColor = C.muted;
        var r = 3.5;
        var cross = S("g", {
          stroke: C.muted, "stroke-width": 1.6, "stroke-linecap": "round",
        }, group);
        S("line", { x1: cx - r, y1: cy - r, x2: cx + r, y2: cy + r }, cross);
        S("line", { x1: cx - r, y1: cy + r, x2: cx + r, y2: cy - r }, cross);
      } else {
        shownColor = weightColor(m.weight);
        drawSeriesMarker(group, m.shape || "dot", cx, cy,
          { color: shownColor, markerSize: 4.2 });
      }
      var hit = S("circle", {
        cx: cx, cy: cy, r: 8, fill: "transparent",
      }, group);
      hit.style.cursor = "crosshair";
      hit.addEventListener("pointerenter", function (event) {
        showTip(event.clientX, event.clientY, function (node) {
          E("div", "viz-tip-head",
            (m.branch ? m.branch + " · " : "") + "U/D = " + fmt(m.u) +
            " · T/D = " + fmt(spec.t), node);
          tipRow(node, shownColor, m.family + " weight",
            fmt(m.weight) + (dead ? "  (below threshold)" : ""), false);
          tipRow(node, null, "position /D",
            (m.pos > 0 ? "+" : "") + fmt(m.pos), false);
        });
      });
      hit.addEventListener("pointerleave", hideTip);
    });

    /* colorbar for weight */
    var legendBox = E("div", "viz-scalebar", null, container);
    var bar = E("span", "viz-gradient", null, legendBox);
    var stops = [];
    for (var s = 0; s <= 10; s++) {
      stops.push(seqColor(s / 10) + " " + s * 10 + "%");
    }
    bar.style.background = "linear-gradient(90deg," + stops.join(",") + ")";
    E("span", "muted", fmt(wLo), legendBox);
    E("span", "viz-scalebar-label",
      spec.scaleLabel || ("pole weight" + (logColor ? " (log)" : "")),
      legendBox);
    E("span", "muted", fmt(wHi), legendBox);

    /* shape + threshold legend */
    var shapeBox = E("div", "viz-scalebar", null, container);
    (spec.shapeLegend || []).forEach(function (sl) {
      var chip = E("span", "viz-legend-chip", null, shapeBox);
      var glyph = E("span", "viz-marker-key", markerSymbol(sl.shape), chip);
      glyph.style.color = C.ink2;
      E("span", null, sl.label, chip);
    });
    var deadChip = E("span", "viz-legend-chip", null, shapeBox);
    var deadGlyph = E("span", "viz-marker-key", "×", deadChip);
    deadGlyph.style.color = C.muted;
    E("span", null,
      "weight < " + fmt(spec.threshold) + " (" + below + " poles)", deadChip);

    return { el: container, svgs: [svg], below: below };
  }

  function interpIndex(sorted, value) {
    if (value < sorted[0] || value > sorted[sorted.length - 1]) return null;
    for (var i = 0; i < sorted.length - 1; i++) {
      if (value >= sorted[i] && value <= sorted[i + 1]) {
        var span = sorted[i + 1] - sorted[i];
        return i + (span ? (value - sorted[i]) / span : 0);
      }
    }
    return sorted.length - 1;
  }

  /* --- export --------------------------------------------------------- */
  function svgMarkup(svg) {
    var clone = svg.cloneNode(true);
    clone.setAttribute("xmlns", SVGNS);
    var viewBox = svg.getAttribute("viewBox").split(" ");
    clone.setAttribute("width", viewBox[2]);
    clone.setAttribute("height", viewBox[3]);
    var background = document.createElementNS(SVGNS, "rect");
    background.setAttribute("x", 0);
    background.setAttribute("y", 0);
    background.setAttribute("width", viewBox[2]);
    background.setAttribute("height", viewBox[3]);
    background.setAttribute("fill", C.surface);
    clone.insertBefore(background, clone.firstChild);
    return new XMLSerializer().serializeToString(clone);
  }
  function dlSVG(svg, name) {
    Atlas.store.download(name + ".svg", "image/svg+xml", svgMarkup(svg));
  }
  function dlPNG(svg, name) {
    var viewBox = svg.getAttribute("viewBox").split(" ");
    var image = new Image();
    image.onload = function () {
      var canvas = document.createElement("canvas");
      canvas.width = viewBox[2] * 2;
      canvas.height = viewBox[3] * 2;
      var context = canvas.getContext("2d");
      context.fillStyle = C.surface;
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      canvas.toBlob(function (blob) {
        var a = document.createElement("a");
        a.href = URL.createObjectURL(blob);
        a.download = name + ".png";
        a.click();
        setTimeout(function () {
          URL.revokeObjectURL(a.href);
        }, 500);
      });
    };
    image.src =
      "data:image/svg+xml;charset=utf-8," +
      encodeURIComponent(svgMarkup(svg));
  }

  Atlas.plot = {
    figure: figure,
    heatmap: heatmap,
    poleMap: poleMap,
    dlSVG: dlSVG,
    dlPNG: dlPNG,
  };
})();
