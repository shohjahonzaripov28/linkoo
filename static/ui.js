/* Linko: umumiy interfeys yordamchilari.
   - linkoConfirm(matn): brauzerning confirm() oynasi o'rniga (telefonlarda confirm() ko'pincha bloklanadi yoki ishlamaydi)
   - linkoToast(matn): qisqa xabar
   - [data-confirm] atributi: bosishdan oldin tasdiq so'raydi */
(function () {
  var UI = window.LINKO_UI || {};

  window.linkoConfirm = function (message, opts) {
    opts = opts || {};
    return new Promise(function (resolve) {
      var ov = document.createElement("div");
      ov.className = "lk-overlay";
      ov.innerHTML = '<div class="lk-dialog" role="alertdialog" aria-modal="true"><p class="lk-msg"></p>' +
        '<div class="lk-actions"><button type="button" class="lk-btn lk-cancel"></button>' +
        '<button type="button" class="lk-btn lk-ok"></button></div></div>';
      ov.querySelector(".lk-msg").textContent = message || "";
      var okBtn = ov.querySelector(".lk-ok"), noBtn = ov.querySelector(".lk-cancel");
      okBtn.textContent = opts.ok || UI.ok || "OK";
      noBtn.textContent = opts.cancel || UI.cancel || "Cancel";
      if (opts.danger !== false) okBtn.classList.add("danger");
      function done(v) {
        document.removeEventListener("keydown", onKey, true);
        if (ov.parentNode) ov.parentNode.removeChild(ov);
        resolve(v);
      }
      function onKey(e) {
        if (e.key === "Escape") { e.preventDefault(); done(false); }
        else if (e.key === "Enter") { e.preventDefault(); done(true); }
      }
      okBtn.addEventListener("click", function () { done(true); });
      noBtn.addEventListener("click", function () { done(false); });
      ov.addEventListener("click", function (e) { if (e.target === ov) done(false); });
      document.addEventListener("keydown", onKey, true);
      document.body.appendChild(ov);
      try { okBtn.focus(); } catch (e) { /* ignore */ }
    });
  };

  var toastTimer = null, toastEl = null;
  window.linkoToast = function (message, kind) {
    if (!toastEl) {
      toastEl = document.createElement("div");
      toastEl.className = "lk-toast";
      toastEl.setAttribute("role", "status");
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = message;
    toastEl.className = "lk-toast show" + (kind ? " " + kind : "");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { toastEl.className = "lk-toast"; }, 2800);
  };

  document.addEventListener("click", function (e) {
    var t = e.target.closest ? e.target.closest("[data-confirm]") : null;
    if (!t || t.dataset.confirmed === "1") return;
    e.preventDefault();
    e.stopPropagation();
    window.linkoConfirm(t.getAttribute("data-confirm")).then(function (ok) {
      if (!ok) return;
      if (t.tagName === "A") { location.href = t.href; return; }
      if (t.form) {
        t.dataset.confirmed = "1";
        if (t.form.requestSubmit) t.form.requestSubmit(t); else t.form.submit();
      }
    });
  }, true);
})();
