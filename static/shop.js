/* Linko do'kon: savat, mahsulot sahifasi, do'kon paneli, buyurtmalar, mahsulot formasi */
(function () {
  "use strict";
  function netMsg() { return (window.LINKO_UI && window.LINKO_UI.net) || "Network error"; }

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $all(sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); }
  function toast(msg, kind) { if (window.linkoToast) window.linkoToast(msg, kind); }
  function ask(msg) { return window.linkoConfirm ? window.linkoConfirm(msg) : Promise.resolve(true); }
  function post(url, body) {
    return fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok, d: d }; }); });
  }
  function fmt(n) { return String(n).replace(/\B(?=(\d{3})+(?!\d))/g, " "); }
  function bumpCart(n) {
    $all(".cart-link").forEach(function (link) {
      var badge = link.querySelector(".cart-badge");
      if (!badge && n > 0) { badge = document.createElement("span"); badge.className = "cart-badge"; link.appendChild(badge); }
      if (badge) { if (n > 0) badge.textContent = n; else badge.remove(); }
    });
    $all(".shop-tabs .tab-badge").forEach(function (b) { b.textContent = n; });
  }

  /* ---------- Kartochkadagi "+" tugmasi ---------- */
  document.addEventListener("click", function (e) {
    var btn = e.target.closest(".add-round");
    if (!btn) return;
    e.preventDefault();
    var id = btn.dataset.productId;
    if (btn.dataset.options === "1") { location.href = "/product/" + id; return; }
    post("/api/cart/add/" + id, {}).then(function (res) {
      if (!res.ok) {
        if (res.d.need_options) { location.href = "/product/" + id; return; }
        toast(res.d.message || netMsg(), "bad"); return;
      }
      btn.classList.add("done"); setTimeout(function () { btn.classList.remove("done"); }, 1000);
      bumpCart(res.d.cart_count);
      toast("✓", "ok");
    }).catch(function () { toast(netMsg(), "bad"); });
  });

  /* ---------- Filtr paneli ---------- */
  var ft = $("#filter-toggle"), fp = $("#filter-panel");
  if (ft && fp) ft.addEventListener("click", function () { fp.hidden = !fp.hidden; });

  $all(".load-more:not(.secondary)").forEach(function (a) {
    a.addEventListener("click", function () { a.innerHTML = '<span class="spinner"></span> ' + (a.dataset.loading || ""); });
  });

  /* ---------- Mahsulot sahifasi ---------- */
  var addBtn = $("#add-cart");
  if (addBtn) {
    var sel = { color: "", size: "" }, qty = 1;
    var hasColor = !!$("#color-group"), hasSize = !!$("#size-group");
    $all(".opt-group").forEach(function (g) {
      g.addEventListener("click", function (e) {
        var chip = e.target.closest(".opt-chip"); if (!chip) return;
        $all(".opt-chip", g).forEach(function (c) { c.classList.remove("active"); });
        chip.classList.add("active");
        if (g.id === "color-group") { sel.color = chip.dataset.v; var cp = $("#color-picked"); if (cp) cp.textContent = chip.dataset.label || ""; }
        else if (g.id === "size-group") { sel.size = chip.dataset.v; var sp = $("#size-picked"); if (sp) sp.textContent = chip.dataset.label || ""; }
      });
    });
    var q = $("#qty-val"), mi = $("#qty-minus"), pl = $("#qty-plus");
    var max = pl ? (+pl.dataset.max || 99) : 99;
    if (mi) mi.addEventListener("click", function () { qty = Math.max(1, qty - 1); q.textContent = qty; });
    if (pl) pl.addEventListener("click", function () { qty = Math.min(Math.min(99, max), qty + 1); q.textContent = qty; });
    var msg = $("#prod-msg");
    addBtn.addEventListener("click", function () {
      msg.hidden = true;
      post("/api/cart/add/" + addBtn.dataset.product, { color: sel.color, size: sel.size, qty: qty }).then(function (res) {
        if (!res.ok) { msg.textContent = res.d.message || netMsg(); msg.hidden = false; return; }
        bumpCart(res.d.cart_count);
        addBtn.classList.add("done"); addBtn.innerHTML = "✓";
        setTimeout(function () { location.href = "/cart"; }, 500);
      }).catch(function () { msg.textContent = netMsg(); msg.hidden = false; });
    });
    void hasColor; void hasSize;
  }
  var track = $("#media-track"), thumbs = $("#gallery-thumbs");
  if (track && thumbs) {
    thumbs.addEventListener("click", function (e) {
      var b = e.target.closest(".gt"); if (!b) return;
      track.scrollTo({ left: (+b.dataset.i) * track.clientWidth, behavior: "smooth" });
    });
    track.addEventListener("scroll", function () {
      var i = Math.round(track.scrollLeft / track.clientWidth);
      $all(".gt", thumbs).forEach(function (g, k) { g.classList.toggle("on", k === i); });
    });
  }
  var del = $("#del-product");
  if (del) del.addEventListener("click", function () {
    ask(del.dataset.confirmText).then(function (ok) {
      if (!ok) return;
      post("/api/products/delete/" + del.dataset.product).then(function (res) {
        if (!res.ok) { toast(netMsg(), "bad"); return; }
        location.href = "/store/manage";
      }).catch(function () { toast(netMsg(), "bad"); });
    });
  });

  /* ---------- Savat ---------- */
  var wrap = $("#cart-wrap");
  if (wrap) {
    var cmsg = $("#cart-msg");
    var recalc = function () {
      var grand = 0;
      $all(".cart-group", wrap).forEach(function (g) {
        var sub = 0;
        $all(".cart-line", g).forEach(function (l) { sub += (+l.dataset.price) * (+$(".qty-val", l).textContent); });
        $(".sub-val", g).textContent = fmt(sub); grand += sub;
        if (!$(".cart-line", g)) g.remove();
      });
      $("#grand-total").textContent = fmt(grand);
      if (!$(".cart-group", wrap)) location.reload();
    };
    wrap.addEventListener("click", function (e) {
      var line = e.target.closest(".cart-line"); if (!line) return;
      var id = line.dataset.line;
      if (e.target.closest(".line-remove")) {
        post("/api/cart/remove/" + id).then(function (res) {
          if (!res.ok) throw 0;
          line.remove(); bumpCart(res.d.cart_count); recalc();
        }).catch(function () { toast(netMsg(), "bad"); });
      } else if (e.target.closest(".qty-btn")) {
        post("/api/cart/qty/" + id, { delta: +e.target.closest(".qty-btn").dataset.d }).then(function (res) {
          if (!res.ok) throw 0;
          $(".qty-val", line).textContent = res.d.qty; bumpCart(res.d.cart_count); recalc();
          if (res.d.message) { cmsg.textContent = res.d.message; cmsg.hidden = false; } else { cmsg.hidden = true; }
        }).catch(function () { toast(netMsg(), "bad"); });
      }
    });
    var cf = $("#checkout-form");
    if (cf) cf.addEventListener("submit", function () {
      var b = $("#order-btn"); b.disabled = true; b.innerHTML = '<span class="spinner"></span>';
    });
  }

  /* ---------- Do'kon paneli: yashirish / o'chirish ---------- */
  document.addEventListener("click", function (e) {
    var tg = e.target.closest("[data-toggle-product]");
    if (tg) {
      post("/api/store/product/" + tg.dataset.toggleProduct + "/toggle").then(function (res) {
        if (res.ok) location.reload(); else toast(netMsg(), "bad");
      }).catch(function () { toast(netMsg(), "bad"); });
      return;
    }
    var dp = e.target.closest("[data-delete-product]");
    if (dp) {
      ask(dp.dataset.confirmText).then(function (ok) {
        if (!ok) return;
        post("/api/products/delete/" + dp.dataset.deleteProduct).then(function (res) {
          if (!res.ok) { toast(netMsg(), "bad"); return; }
          var row = dp.closest(".manage-row"); if (row) row.remove(); else location.reload();
        }).catch(function () { toast(netMsg(), "bad"); });
      });
    }
  });

  /* ---------- Buyurtma holatini o'zgartirish ---------- */
  document.addEventListener("click", function (e) {
    var b = e.target.closest("[data-set-status]");
    if (!b) return;
    var card = b.closest(".order-card");
    function go() {
      post("/api/orders/" + card.dataset.order + "/status", { status: b.dataset.setStatus }).then(function (res) {
        if (!res.ok) { toast(res.d.message || netMsg(), "bad"); return; }
        location.reload();
      }).catch(function () { toast(netMsg(), "bad"); });
    }
    if (b.dataset.confirmText) ask(b.dataset.confirmText).then(function (ok) { if (ok) go(); }); else go();
  });

  /* ---------- Do'kon formasi ---------- */
  var sform = $("#store-form");
  if (sform) {
    var nameIn = $("#sf-name"), handleIn = $("#sf-handle"), touched = !!handleIn.value;
    handleIn.addEventListener("input", function () { touched = true; handleIn.value = handleIn.value.toLowerCase().replace(/[^a-z0-9_.]/g, ""); });
    nameIn.addEventListener("input", function () {
      if (!touched) handleIn.value = nameIn.value.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_.]/g, "").slice(0, 30);
    });
    var desc = $("#sf-desc"), dc = $("#desc-count");
    desc.addEventListener("input", function () { dc.textContent = desc.value.length + "/300"; });
    function preview(input, box, asBg) {
      input.addEventListener("change", function () {
        var f = input.files && input.files[0]; if (!f) return;
        var url = URL.createObjectURL(f);
        if (asBg) box.style.backgroundImage = "url('" + url + "')";
        else { box.innerHTML = ""; box.appendChild(input); var im = document.createElement("img"); im.src = url; box.appendChild(im); }
      });
    }
    preview($("input[name=banner]", sform), $("#banner-box"), true);
    preview($("input[name=logo]", sform), $("#logo-box"), false);
    sform.addEventListener("submit", function () {
      var b = $("button[type=submit]", sform); b.disabled = true; b.innerHTML = '<span class="spinner"></span>';
    });
    var sd = $("#store-delete");
    if (sd) sd.addEventListener("click", function () {
      ask(sd.dataset.confirmText).then(function (ok) {
        if (!ok) return;
        post("/api/store/delete").then(function (res) {
          if (res.ok) location.href = res.d.redirect || "/shop"; else toast(netMsg(), "bad");
        }).catch(function () { toast(netMsg(), "bad"); });
      });
    });
  }

  /* ---------- Mahsulot formasi ---------- */
  var pf = $("#pf");
  if (pf) {
    var cat = JSON.parse($("#catalog-data").textContent), init = JSON.parse($("#pf-init").textContent);
    var catSel = $("#pf-cat"), subSel = $("#pf-sub"), subWrap = $("#pf-sub-wrap");
    var sizesBox = $("#pf-sizes"), sizesWrap = $("#pf-sizes-wrap"), sizeTitle = $("#pf-size-title"), allBtn = $("#pf-size-all");
    var chosen = {}; (init.sizes || []).forEach(function (s) { chosen[s] = true; });

    function fillCategories() {
      catSel.innerHTML = "";
      cat.categories.forEach(function (c) {
        var o = document.createElement("option"); o.value = c.id; o.textContent = c.name; catSel.appendChild(o);
      });
      catSel.value = init.category || "other";
      if (!catSel.value) catSel.value = "other";
    }
    function currentSystem() {
      var c = cat.categories.filter(function (x) { return x.id === catSel.value; })[0];
      if (!c) return "none";
      var s = c.subs.filter(function (x) { return x.id === subSel.value; })[0];
      return s ? s.size_system : c.size_system;
    }
    function fillSubs(keep) {
      var c = cat.categories.filter(function (x) { return x.id === catSel.value; })[0];
      subSel.innerHTML = "";
      if (!c || !c.subs.length) { subWrap.hidden = true; return; }
      subWrap.hidden = false;
      var o0 = document.createElement("option"); o0.value = ""; o0.textContent = "—"; subSel.appendChild(o0);
      c.subs.forEach(function (s) { var o = document.createElement("option"); o.value = s.id; o.textContent = s.name; subSel.appendChild(o); });
      subSel.value = keep || "";
    }
    function fillSizes() {
      var key = currentSystem(), sys = cat.size_systems[key];
      sizesBox.innerHTML = "";
      sizeTitle.textContent = sys.name;
      allBtn.hidden = !sys.values.length;
      sys.values.forEach(function (v) {
        var l = document.createElement("label"); l.className = "size-opt";
        var i = document.createElement("input"); i.type = "checkbox"; i.name = "sizes"; i.value = v.v; i.checked = !!chosen[v.v];
        i.addEventListener("change", function () { chosen[v.v] = i.checked; });
        var s = document.createElement("span"); s.textContent = v.label;
        l.appendChild(i); l.appendChild(s); sizesBox.appendChild(l);
      });
    }
    fillCategories(); fillSubs(init.subcategory); fillSizes();
    catSel.addEventListener("change", function () { chosen = {}; fillSubs(""); fillSizes(); });
    subSel.addEventListener("change", function () { chosen = {}; fillSizes(); });
    allBtn.addEventListener("click", function () {
      var boxes = $all("input", sizesBox), all = boxes.every(function (b) { return b.checked; });
      boxes.forEach(function (b) { b.checked = !all; chosen[b.value] = !all; });
      allBtn.textContent = all ? init.all : init.none;
    });

    // Narx maydonlari: 250 000 ko'rinishida
    $all(".money-input", pf).forEach(function (inp) {
      function f() { var d = inp.value.replace(/\D/g, ""); inp.value = d ? fmt(d) : ""; }
      inp.addEventListener("input", f); f();
    });

    // Rasmlar: yangi fayllar yig'iladi, eskilarini o'chirish mumkin
    var files = [], media = $("#pf-media"), fileIn = $("#pf-files"), addTile = $("#pm-add"), MAXP = 8;
    function existingCount() { return $all(".pm-item[data-existing]:not(.removed)", media).length; }
    function renderNew() {
      $all(".pm-item.new", media).forEach(function (n) { n.remove(); });
      files.forEach(function (f, idx) {
        var d = document.createElement("div"); d.className = "pm-item new";
        var im = document.createElement("img"); im.src = URL.createObjectURL(f);
        var x = document.createElement("button"); x.type = "button"; x.className = "pm-x"; x.textContent = "✕";
        x.addEventListener("click", function () { files.splice(idx, 1); renderNew(); syncInput(); });
        d.appendChild(im); d.appendChild(x); media.insertBefore(d, addTile);
      });
      markMain(); addTile.hidden = existingCount() + files.length >= MAXP;
    }
    function markMain() {
      $all(".pm-item", media).forEach(function (n) { n.classList.remove("main"); });
      var first = $(".pm-item:not(.removed)", media); if (first) first.classList.add("main");
    }
    function syncInput() {
      try { var dt = new DataTransfer(); files.forEach(function (f) { dt.items.add(f); }); fileIn.files = dt.files; } catch (e) { /* eski brauzer */ }
    }
    fileIn.addEventListener("change", function () {
      Array.prototype.slice.call(fileIn.files).forEach(function (f) { if (existingCount() + files.length < MAXP) files.push(f); });
      syncInput(); renderNew();
    });
    media.addEventListener("click", function (e) {
      var x = e.target.closest(".pm-x"); var item = x && x.closest(".pm-item[data-existing]"); if (!item) return;
      item.classList.add("removed"); item.hidden = true;
      var h = document.createElement("input"); h.type = "hidden"; h.name = "remove_media"; h.value = item.dataset.existing; pf.appendChild(h);
      markMain(); addTile.hidden = existingCount() + files.length >= MAXP;
    });
    markMain();
    pf.addEventListener("submit", function () {
      var b = $("#pf-submit"); b.disabled = true; b.innerHTML = '<span class="spinner"></span>';
    });
  }
})();
