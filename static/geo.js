/* Linko: davlat -> viloyat -> tuman tanlash (katalogdan). Konteyner: <div data-geo data-country=".." data-region=".." data-district=".."> */
(function () {
  "use strict";
  var root = document.querySelector("[data-geo]");
  if (!root) return;
  var c = root.querySelector('[name="country"]'), r = root.querySelector('[name="region"]'), d = root.querySelector('[name="district"]');
  var rw = root.querySelector(".geo-region"), dw = root.querySelector(".geo-district");
  var ph = { region: root.dataset.phRegion || "", district: root.dataset.phDistrict || "" };
  var need = root.dataset.required === "1";
  var init = { region: root.dataset.region || "", district: root.dataset.district || "" };

  function fill(sel, items, value, placeholder) {
    sel.innerHTML = "";
    sel.appendChild(new Option(placeholder, ""));
    items.forEach(function (it) { var o = new Option(it, it); if (it === value) o.selected = true; sel.appendChild(o); });
  }
  function toggle(wrap, sel, show) {
    wrap.hidden = !show; sel.required = show && need;
    if (!show) sel.value = "";
  }
  function loadDistricts(value) {
    if (!r.value) { toggle(dw, d, false); return Promise.resolve(); }
    return fetch("/api/geo/districts?country=" + encodeURIComponent(c.value) + "&region=" + encodeURIComponent(r.value))
      .then(function (x) { return x.json(); })
      .then(function (data) {
        var list = data.districts || [];
        fill(d, list, value, ph.district); toggle(dw, d, list.length > 0);
      });
  }
  function loadRegions(value, distValue) {
    if (!c.value) { toggle(rw, r, false); toggle(dw, d, false); return Promise.resolve(); }
    return fetch("/api/geo/regions?country=" + encodeURIComponent(c.value))
      .then(function (x) { return x.json(); })
      .then(function (data) {
        var list = data.regions || [];
        fill(r, list, value, ph.region); toggle(rw, r, list.length > 0);
        return loadDistricts(distValue || "");
      });
  }
  c.addEventListener("change", function () { loadRegions("", ""); });
  r.addEventListener("change", function () { loadDistricts(""); });
  c.required = need;
  loadRegions(init.region, init.district);
})();
