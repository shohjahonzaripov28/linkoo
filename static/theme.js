/* Linko: Kun / Tun mavzusi. Tanlov shu qurilmada (brauzerda) saqlanadi.
   Rejimlar: "dark" (standart), "light", "auto" (telefon sozlamasiga ergashadi). */
(function () {
  var KEY = "linko_theme";
  function stored() { try { return localStorage.getItem(KEY) || "dark"; } catch (e) { return "dark"; } }
  function resolve(mode) {
    if (mode === "auto") return window.matchMedia && matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
    return mode === "light" ? "light" : "dark";
  }
  function apply(mode) {
    var eff = resolve(mode);
    document.documentElement.setAttribute("data-theme", eff);
    var m = document.querySelector('meta[name="theme-color"]');
    if (m) m.setAttribute("content", eff === "light" ? "#f4f6ff" : "#0f1226");
    document.querySelectorAll("[data-theme-set]").forEach(function (b) {
      b.classList.toggle("active", b.getAttribute("data-theme-set") === mode);
    });
    document.querySelectorAll("[data-theme-toggle]").forEach(function (b) {
      b.setAttribute("data-mode", eff);
    });
  }
  function set(mode) {
    try { localStorage.setItem(KEY, mode); } catch (e) { /* xotira yopiq - sahifa yangilanguncha amal qiladi */ }
    apply(mode);
  }
  window.linkoTheme = { set: set, get: stored };
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-theme-set]");
    if (b) { set(b.getAttribute("data-theme-set")); return; }
    var t = e.target.closest("[data-theme-toggle]");
    if (t) { set(resolve(stored()) === "light" ? "dark" : "light"); }
  });
  if (window.matchMedia) {
    var mq = matchMedia("(prefers-color-scheme: light)");
    var onChange = function () { if (stored() === "auto") apply("auto"); };
    if (mq.addEventListener) mq.addEventListener("change", onChange);
  }
  apply(stored());
})();
