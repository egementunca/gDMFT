/* Payload decode + application bootstrap. Runs first. */
(function () {
  "use strict";
  window.Atlas = window.Atlas || {};

  function fail(message) {
    var view = document.getElementById("view");
    view.innerHTML =
      '<div class="error-panel"><h2>Cannot load atlas payload</h2><p>' +
      message +
      "</p><p>Rebuild with <code>gdmft-atlas build --no-compress</code> " +
      "for a browser without DecompressionStream support.</p></div>";
  }

  async function decodePayload() {
    var element = document.getElementById("atlas-payload");
    var encoding = element.getAttribute("data-encoding");
    var packed = element.textContent.replace(/\s+/g, "");
    var bytes = Uint8Array.from(atob(packed), function (c) {
      return c.charCodeAt(0);
    });
    if (encoding === "gzip-base64") {
      if (typeof DecompressionStream === "undefined") {
        throw new Error(
          "this browser lacks DecompressionStream('gzip') " +
            "(needs Chrome/Edge 80+, Safari 16.4+, Firefox 113+)"
        );
      }
      var stream = new Blob([bytes])
        .stream()
        .pipeThrough(new DecompressionStream("gzip"));
      return JSON.parse(await new Response(stream).text());
    }
    if (encoding === "base64-json") {
      return JSON.parse(new TextDecoder().decode(bytes));
    }
    throw new Error("unknown payload encoding " + encoding);
  }

  window.addEventListener("DOMContentLoaded", function () {
    decodePayload()
      .then(function (data) {
        Atlas.DATA = data;
        if (typeof Atlas.init === "function") {
          Atlas.init();
        } else {
          fail("application modules missing (Atlas.init undefined)");
        }
      })
      .catch(function (error) {
        fail(String(error && error.message ? error.message : error));
      });
  });
})();
