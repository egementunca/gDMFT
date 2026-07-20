/* Application shell: tab registry, hash router with per-tab state
   (shareable permalinks), small form-control helpers. */
(function () {
  "use strict";
  var Atlas = window.Atlas;
  Atlas.tabs = [];
  Atlas.state = {};

  Atlas.registerTab = function (id, title, render) {
    Atlas.tabs.push({ id: id, title: title, render: render });
  };

  /* ---- hash <-> state ---- */
  function parseHash() {
    var hash = location.hash.replace(/^#/, "");
    var slash = hash.indexOf("/");
    var tabId = slash < 0 ? hash : hash.slice(0, slash);
    if (slash >= 0) {
      try {
        Atlas.state[tabId] = JSON.parse(
          decodeURIComponent(hash.slice(slash + 1))
        );
      } catch (error) {
        /* stale or hand-edited hash: fall back to defaults */
      }
    }
    return tabId;
  }
  var suppressHash = false;
  Atlas.saveState = function (tabId) {
    suppressHash = true;
    location.replace(
      "#" +
        tabId +
        "/" +
        encodeURIComponent(JSON.stringify(Atlas.state[tabId] || {}))
    );
    setTimeout(function () {
      suppressHash = false;
    }, 0);
  };

  function currentTab() {
    var tabId = parseHash();
    for (var i = 0; i < Atlas.tabs.length; i++) {
      if (Atlas.tabs[i].id === tabId) return Atlas.tabs[i];
    }
    return Atlas.tabs[0] || null;
  }

  /* ---- form-control helpers (labels in ink, values via textContent) ---- */
  var ui = {};
  ui.field = function (labelText, control) {
    var wrap = Atlas.E("label", "field");
    Atlas.E("span", "field-label", labelText, wrap);
    wrap.appendChild(control);
    return wrap;
  };
  ui.select = function (options, value, onChange) {
    var select = document.createElement("select");
    options.forEach(function (option) {
      var opt = document.createElement("option");
      opt.value = String(option.value);
      opt.textContent = option.label;
      select.appendChild(opt);
    });
    select.value = String(value);
    if (select.selectedIndex < 0 && options.length) {
      select.value = String(options[0].value);
    }
    select.addEventListener("change", function () {
      onChange(select.value);
    });
    return select;
  };
  ui.check = function (labelText, checked, onChange) {
    var wrap = Atlas.E("label", "check");
    var input = document.createElement("input");
    input.type = "checkbox";
    input.checked = !!checked;
    input.addEventListener("change", function () {
      onChange(input.checked);
    });
    wrap.appendChild(input);
    Atlas.E("span", null, labelText, wrap);
    return wrap;
  };
  ui.btn = function (labelText, onClick, className) {
    var button = Atlas.E("button", "btn" + (className ? " " + className : ""));
    button.type = "button";
    button.textContent = labelText;
    button.addEventListener("click", onClick);
    return button;
  };
  ui.row = function (children, className) {
    var row = Atlas.E("div", className || "filter-row");
    children.forEach(function (child) {
      if (child) row.appendChild(child);
    });
    return row;
  };
  Atlas.ui = ui;

  /* ---- pin box (detail popover) ---- */
  Atlas.showPin = function (build) {
    var pin = document.getElementById("pin");
    pin.innerHTML = "";
    var close = ui.btn("✕", function () {
      pin.hidden = true;
    }, "pin-close");
    pin.appendChild(close);
    build(pin);
    pin.hidden = false;
  };

  /* ---- render loop ---- */
  function renderNav(active) {
    var nav = document.getElementById("tabs");
    nav.innerHTML = "";
    Atlas.tabs.forEach(function (tab) {
      var button = document.createElement("button");
      button.textContent = tab.title;
      if (active && tab.id === active.id) button.className = "active";
      button.addEventListener("click", function () {
        location.hash = "#" + tab.id;
      });
      nav.appendChild(button);
    });
  }

  function renderView(tab) {
    var view = document.getElementById("view");
    view.innerHTML = "";
    Atlas.hideTip && Atlas.hideTip();
    document.getElementById("pin").hidden = true;
    if (tab) tab.render(view);
  }

  function renderAll() {
    var tab = currentTab();
    renderNav(tab);
    renderView(tab);
  }

  Atlas.init = function () {
    var data = Atlas.DATA;
    document.getElementById("mast-sub").textContent =
      data.meta.datasets
        .map(function (ds) {
          return ds.id + " v" + ds.version;
        })
        .join(" · ") +
      " · built " +
      data.meta.built_at;
    var disclaimer = document.getElementById("disclaimer");
    disclaimer.textContent = data.meta.disclaimer;
    disclaimer.hidden = false;
    renderAll();
    window.addEventListener("hashchange", function () {
      if (!suppressHash) renderAll();
    });
  };
})();
