/* =====================================================================
   LINKO MAP
   1. Tumanli kinematik sayohat: 12 sahna, canvas'da kadrlar ketma-ketligi
      (video emas: scroll qaysi kadr ko'rinishini tanlaydi, telefonda qotmaydi)
   2. Oxirida tuman ichidan erkin xaritaga o'tadi
   3. Erkin xarita: qidiruv, joylashuvim, sun'iy yo'ldosh, 3D
   Kun / tun mavzusi: html[data-theme] ga ergashadi (theme.js)
   ===================================================================== */
(function () {
  "use strict";

  const CFG = window.LINKO_MAP || {};
  const STORY = window.LINKO_STORY || [];
  const FR = window.LINKO_FRAMES || { ver: 1, seq: {} };
  const COARSE = matchMedia("(pointer: coarse)").matches;
  const LITE = COARSE || (navigator.deviceMemory || 8) <= 4 || (navigator.hardwareConcurrency || 8) <= 4;
  const CONN = navigator.connection || {};
  const SLOW = !!CONN.saveData || /(^|-)2g|3g/.test(CONN.effectiveType || "");
  const REDUCED = document.documentElement.classList.contains("reduce-motion") ||
                  matchMedia("(prefers-reduced-motion: reduce)").matches;

  const I18N = {
    en: { scroll: "SCROLL", toMap: "MAP", toStory: "JOURNEY", open: "OPEN THE MAP",
          search: "Search: Beijing, Paris, Dubai...", locate: "Me", styleSat: "Satellite", styleMap: "Map",
          noLoc: "Couldn't get your location.", notFound: "Nothing found.", mapErr: "The map didn't load. Check your internet." },
    uz: { scroll: "PASTGA", toMap: "XARITA", toStory: "SAYOHAT", open: "XARITANI OCHISH",
          search: "Joy qidirish: Pekin, Parij, Dubay...", locate: "Men", styleSat: "Sun'iy yo'ldosh", styleMap: "Xarita",
          noLoc: "Joylashuvni aniqlab bo'lmadi.", notFound: "Hech narsa topilmadi.", mapErr: "Xarita yuklanmadi. Internetni tekshiring." },
    ru: { scroll: "ЛИСТАЙТЕ", toMap: "КАРТА", toStory: "ПУТЕШЕСТВИЕ", open: "ОТКРЫТЬ КАРТУ",
          search: "Поиск: Пекин, Париж, Дубай...", locate: "Я", styleSat: "Спутник", styleMap: "Карта",
          noLoc: "Не удалось определить местоположение.", notFound: "Ничего не найдено.", mapErr: "Карта не загрузилась. Проверьте интернет." },
    zh: { scroll: "向下滑动", toMap: "地图", toStory: "旅程", open: "打开地图",
          search: "搜索：北京、巴黎、迪拜...", locate: "我", styleSat: "卫星图", styleMap: "地图",
          noLoc: "无法获取你的位置。", notFound: "未找到结果。", mapErr: "地图加载失败，请检查网络。" }
  };
  const LANG = I18N[CFG.lang] ? CFG.lang : "en";
  const L = I18N[LANG];

  const $ = (id) => document.getElementById(id);
  function esc(s) { const d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  let toastT = 0;
  function toast(m) { const t = $("toast"); t.textContent = m; t.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("show"), 3200); }
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const lerp = (a, b, t) => a + (b - a) * t;
  const smooth = (e0, e1, x) => { const t = clamp((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); };

  /* ================= MAVZU (kun / tun) ================= */
  function readTheme() {
    const light = document.documentElement.getAttribute("data-theme") === "light";
    return light ? { light: true, mist: [236, 238, 240] } : { light: false, mist: [11, 17, 32] };
  }
  let TH = readTheme();
  const rgba = (c, a) => "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")";

  /* ================= CANVAS ================= */
  const cv = $("cv");
  const ctx = cv.getContext("2d", { alpha: false });
  const storyEl = $("story"), track = $("track");
  let W = 1, H = 1, VH = 1, total = 1, dirty = true, fogTex = null;
  // Telefon (tik ekran) uchun 450x800 kadrlar, kompyuter uchun 1280x720
  let SET = innerWidth / innerHeight < 0.85 ? "m" : "d";

  /* ================= SAHNALAR ================= */
  const scenes = STORY.map((s) => ({ s, start: 0, end: 0 }));
  function measure() {
    W = Math.max(1, cv.clientWidth); H = Math.max(1, cv.clientHeight);
    cv.width = W; cv.height = H;                      // 1x piksel: kadrlar shu o'lchamda, telefon yengil ishlaydi
    VH = storyEl.clientHeight || innerHeight;
    let y = 0;
    scenes.forEach((sc) => { sc.start = y; y += sc.s.len * VH; sc.end = y; });
    total = y;
    track.style.height = (total + VH) + "px";
    fogTex = null; grads = null; dirty = true;
  }

  /* ================= KADRLARNI YUKLASH ================= */
  // Har sahna = bitta fayl (bitta so'rov). Fayl oqim bo'lib kelayotganda kadrlar birma-bir ajratiladi:
  // avval har 8-kadr keladi, shuning uchun to'liq yuklanmasdan ham scroll ishlaydi.
  const store = {};
  function frames(seq) { const k = SET + ":" + seq; return store[k] || (store[k] = new Array(FR.seq[seq] || 0).fill(null)); }
  const requested = new Set();
  let queue = [], running = 0;
  const MAXQ = SLOW ? 1 : 2;
  function plan(ci) {
    const order = [ci, ci + 1, ci - 1, ci + 2, ci + 3];
    for (let k = 0; k < scenes.length; k++) if (order.indexOf(k) < 0) order.push(k);
    queue = [];
    order.forEach((k) => { if (scenes[k] && queue.indexOf(scenes[k].s.seq) < 0) queue.push(scenes[k].s.seq); });
    pump();
  }
  function pump() {
    while (running < MAXQ && queue.length) {
      const seq = queue.shift();
      const key = SET + ":" + seq;
      if (requested.has(key)) continue;
      requested.add(key);
      running++;
      loadPack(SET, seq).catch(() => { requested.delete(key); }).then(() => { running--; pump(); });
    }
  }
  async function loadPack(set, seq) {
    const ent = (FR.pack && FR.pack[set] && FR.pack[set][seq]) || [];
    const HEAD = 16;                                   // fayl boshidagi "LINKOPACK1" sarlavhasi
    const size = HEAD + ent.reduce((a, e) => a + e[1], 0);
    const buf = new Uint8Array(size);
    let got = 0, k = 0, off = HEAD;
    const emit = () => {
      while (k < ent.length && off + ent[k][1] <= got) {
        const [idx, len] = ent[k];
        const img = new Image();
        img.decoding = "async";
        img.onload = () => { if (set === SET) { frames(seq)[idx] = img; dirty = true; } };
        img.src = URL.createObjectURL(new Blob([buf.subarray(off, off + len)], { type: "image/webp" }));
        off += len; k++;
      }
    };
    const r = await fetch(CFG.frameBase + "/" + seq + "_" + set + ".bin?v=" + FR.ver);
    if (!r.ok) throw new Error("pack " + r.status);
    if (r.body && r.body.getReader) {
      const rd = r.body.getReader();
      for (;;) {
        const { done, value } = await rd.read();
        if (done) break;
        buf.set(value.subarray(0, Math.max(0, Math.min(value.length, size - got))), got);
        got += value.length;
        emit();
      }
    } else {
      buf.set(new Uint8Array(await r.arrayBuffer()).subarray(0, size)); got = size; emit();
    }
    if (k < ent.length) throw new Error("pack short");
  }
  function getImg(seq, i) {
    const a = frames(seq);
    if (a[i]) return a[i];
    for (let d = 1; d < a.length; d++) { if (a[i - d]) return a[i - d]; if (a[i + d]) return a[i + d]; }
    return null;
  }

  /* ================= TUMAN TEKSTURASI ================= */
  function makeFog() {
    const c = document.createElement("canvas");
    c.width = 1024; c.height = 384;
    const g = c.getContext("2d");
    let seed = 7;
    const rnd = () => { seed = (seed * 16807) % 2147483647; return seed / 2147483647; };
    const m = TH.mist;
    for (let n = 0; n < 130; n++) {
      const x = rnd() * 1024, y = 90 + rnd() * 210, r = 50 + rnd() * 150, a = 0.05 + rnd() * 0.13;
      [-1024, 0, 1024].forEach((dx) => {
        const gr = g.createRadialGradient(x + dx, y, 0, x + dx, y, r);
        gr.addColorStop(0, rgba(m, a)); gr.addColorStop(1, rgba(m, 0));
        g.fillStyle = gr; g.fillRect(x + dx - r, y - r, r * 2, r * 2);
      });
    }
    g.globalCompositeOperation = "destination-in";
    const lg = g.createLinearGradient(0, 0, 0, 384);
    lg.addColorStop(0, "rgba(0,0,0,0)"); lg.addColorStop(0.35, "rgba(0,0,0,1)");
    lg.addColorStop(0.7, "rgba(0,0,0,1)"); lg.addColorStop(1, "rgba(0,0,0,0)");
    g.fillStyle = lg; g.fillRect(0, 0, 1024, 384);
    return c;
  }
  function fogLayer(top, h, off, alpha) {
    if (alpha <= 0.01) return;
    const w = 1024 * (h / 384);
    let x = -((off % w) + w) % w;
    ctx.globalAlpha = Math.min(1, alpha);
    for (; x < W; x += w) ctx.drawImage(fogTex, x, top, w, h);
  }

  /* ================= CHIZISH ================= */
  let grads = null;
  function makeGrads() {
    const m = TH.mist, o = {};
    o.band = ctx.createLinearGradient(0, H * 0.3, 0, H * 0.7);
    o.band.addColorStop(0, rgba(m, 0)); o.band.addColorStop(0.5, rgba(m, 0.42)); o.band.addColorStop(1, rgba(m, 0));
    o.bottom = ctx.createLinearGradient(0, H, 0, H * 0.52);
    o.bottom.addColorStop(0, rgba(m, 0.9)); o.bottom.addColorStop(1, rgba(m, 0));
    o.top = ctx.createLinearGradient(0, 0, 0, H * 0.17);
    o.top.addColorStop(0, rgba(m, 0.6)); o.top.addColorStop(1, rgba(m, 0));
    return o;
  }
  function drawScene(sc, p, alpha, zoom) {
    const n = FR.seq[sc.s.seq] || 1;
    const f = lerp(sc.s.range[0], sc.s.range[1], p);
    const img = getImg(sc.s.seq, Math.round(f * (n - 1)));
    if (!img || !img.naturalWidth) return;
    const s = Math.max(W / img.naturalWidth, H / img.naturalHeight) * zoom;
    const dw = img.naturalWidth * s, dh = img.naturalHeight * s;
    ctx.globalAlpha = alpha;
    ctx.drawImage(img, (W - dw) / 2, (H - dh) / 2, dw, dh);
  }

  function sceneAt(y) {
    for (let k = 0; k < scenes.length; k++) if (y < scenes[k].end) return k;
    return scenes.length - 1;
  }

  let ys = 0, curIdx = -1, bigA = 0;
  function render(t) {
    const y = ys;
    const i = sceneAt(y), sc = scenes[i];
    const p = clamp((y - sc.start) / (sc.end - sc.start), 0, 1);
    const nx = scenes[i + 1];

    ctx.globalCompositeOperation = "source-over";
    ctx.globalAlpha = 1;
    ctx.fillStyle = rgba(TH.mist, 1);
    ctx.fillRect(0, 0, W, H);

    // Kamera asta oldinga siljiydi
    drawScene(sc, p, 1, 1.03 + 0.07 * p);
    let ink = lerp(sc.s.ink[0], sc.s.ink[1], p);
    let mist = sc.s.mist;
    if (nx && p > 0.8) {
      const xf = smooth(0.8, 1, p);
      drawScene(nx, 0, xf, 1.03);
      ink = lerp(ink, nx.s.ink[0], xf);
      mist = lerp(mist, nx.s.mist, xf);
    }

    // "Tush rasmi": rangni olib, qog'oz rangiga yaqinlashtirish
    if (ink > 0.01) {
      ctx.globalCompositeOperation = "saturation";
      ctx.globalAlpha = ink; ctx.fillStyle = "#808080"; ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = TH.light ? "screen" : "multiply";
      ctx.globalAlpha = ink * (TH.light ? 0.42 : 0.38); ctx.fillStyle = TH.light ? "#a7adb4" : "#26324d"; ctx.fillRect(0, 0, W, H);
    }
    ctx.globalCompositeOperation = "source-over";

    // Tuman: sahnalar chegarasida quyuqlashadi, o'rtasida tarqaladi
    let bump;
    if (i === 0) bump = 0.75 * (1 - smooth(0, 0.45, p));
    else bump = 1 - smooth(0, 0.16, p);
    if (nx) bump = Math.max(bump, smooth(0.76, 1, p));
    if (sc.s.final) bump = Math.max(bump, smooth(0.35, 0.95, p) * 1.2);
    const veil = clamp(mist + 0.72 * bump, 0, 1);
    ctx.globalAlpha = veil;
    ctx.fillStyle = rgba(TH.mist, 1);
    ctx.fillRect(0, 0, W, H);

    if (!fogTex) fogTex = makeFog();
    const drift = REDUCED ? 0 : t * 0.012;
    fogLayer(H * 0.38, H * 0.8, drift + y * 0.08, 0.45 + veil * 1.3);
    if (!LITE) fogLayer(-H * 0.12, H * 0.62, -drift * 0.6 - y * 0.05, 0.22 + veil);

    if (!grads) grads = makeGrads();
    // Katta yozuv ortida yengil tuman tasmasi (o'qilishi uchun)
    if (bigA > 0.02) { ctx.globalAlpha = bigA; ctx.fillStyle = grads.band; ctx.fillRect(0, H * 0.3, W, H * 0.4); }
    // Pastki va yuqori qirralar (matn uchun)
    ctx.globalAlpha = 1;
    ctx.fillStyle = grads.bottom; ctx.fillRect(0, H * 0.52, W, H * 0.48);
    ctx.fillStyle = grads.top; ctx.fillRect(0, 0, W, H * 0.17);

    ui(i, p, y);
  }

  /* ================= MATNLAR ================= */
  const bigEl = $("big"), capEl = $("cap"), hintEl = $("hint"), progEl = $("progress"), ringFg = $("ring-fg"), goBtn = $("cap-go");
  const last = {};
  function setStyle(el, key, prop, val) { if (last[key] !== val) { last[key] = val; el.style[prop] = val; } }
  // Katta yozuv ekranga sig'sin (eng keng harf oralig'ida ham)
  function fitBig() {
    bigEl.style.fontSize = "";
    const base = parseFloat(getComputedStyle(bigEl).fontSize) || 100;
    const n = Math.max(1, (bigEl.textContent || "").length);
    const est = n * base * (0.62 + 0.44);                 // harf kengligi + maksimal oraliq
    const room = bigEl.clientWidth * 0.9;
    if (est > room) bigEl.style.fontSize = Math.max(28, base * room / est).toFixed(1) + "px";
  }
  function ui(i, p, y) {
    if (i !== curIdx) {
      curIdx = i;
      const s = scenes[i].s;
      bigEl.textContent = s.big || "";
      fitBig();
      $("cap-n").textContent = String(i + 1).padStart(2, "0");
      $("cap-tag").textContent = s.tag || "";
      $("cap-name").textContent = s.name[LANG] || s.name.en;
      $("cap-stat").textContent = s.stat || "";
      $("cap-text").textContent = s.text[LANG] || s.text.en;
      goBtn.classList.toggle("show", !!s.final);
      plan(i);
    }
    const s = scenes[i].s;
    let a, c;
    if (i === 0) { a = 1 - smooth(0.6, 0.82, p); c = 1 - smooth(0.55, 0.78, p); }
    else if (s.final) { a = smooth(0.08, 0.3, p); c = smooth(0.12, 0.32, p); }
    else { a = smooth(0.1, 0.28, p) * (1 - smooth(0.68, 0.84, p)); c = smooth(0.14, 0.3, p) * (1 - smooth(0.72, 0.86, p)); }
    bigA = a;
    setStyle(bigEl, "bo", "opacity", a.toFixed(3));
    setStyle(bigEl, "bt", "transform", "translateX(" + ((0.5 - p) * 7).toFixed(2) + "vw)");
    setStyle(bigEl, "bl", "letterSpacing", (0.28 + 0.16 * p).toFixed(3) + "em");
    setStyle(capEl, "co", "opacity", c.toFixed(3));
    setStyle(capEl, "ct", "transform", "translateY(" + ((1 - c) * 16).toFixed(1) + "px)");
    setStyle(capEl, "cp", "pointerEvents", c > 0.5 ? "auto" : "none");
    setStyle(hintEl, "ho", "opacity", y < VH * 0.15 ? "1" : "0");
    const pr = clamp(y / Math.max(1, total), 0, 1);
    setStyle(progEl, "pw", "width", (pr * 100).toFixed(2) + "%");
    setStyle(ringFg, "rd", "strokeDashoffset", (138.2 * (1 - pr)).toFixed(1));
    if (s.final && p > 0.97 && !autoMapDone) { autoMapDone = true; setMode("map"); }
    if (!s.final) autoMapDone = false;
  }

  /* ================= ASOSIY SIKL ================= */
  let mode = "story", autoMapDone = false, lastFog = 0;
  function loop(t) {
    requestAnimationFrame(loop);
    if (mode !== "story") return;
    const target = storyEl.scrollTop;
    const prev = ys;
    ys += (target - ys) * (REDUCED ? 1 : COARSE ? 0.34 : 0.13);
    if (Math.abs(target - ys) < 0.5) ys = target;
    const fogDue = !REDUCED && t - lastFog > (LITE ? 66 : 33);
    if (ys === prev && !dirty && !fogDue) return;
    if (fogDue) lastFog = t;
    dirty = false;
    render(t);
  }

  measure();
  plan(0);
  window.addEventListener("resize", () => {
    const r = storyEl.scrollTop / Math.max(1, total);
    const ns = innerWidth / innerHeight < 0.85 ? "m" : "d";
    if (ns !== SET) { SET = ns; plan(Math.max(0, curIdx)); }
    measure();
    storyEl.scrollTop = r * total; ys = storyEl.scrollTop;
    fitBig();
  });
  requestAnimationFrame(loop);

  $("hint-t").textContent = L.scroll;
  goBtn.textContent = L.open;
  goBtn.addEventListener("click", () => setMode("map"));

  /* ================= REJIM: SAYOHAT / XARITA ================= */
  const fade = $("fade");
  $("mode-lbl").textContent = L.toMap;
  function setMode(m) {
    if (m === mode) return;
    fade.classList.add("on");
    setTimeout(() => {
      mode = m;
      document.body.classList.toggle("explore", m === "map");
      $("mode-lbl").textContent = m === "map" ? L.toStory : L.toMap;
      $("mode-btn").classList.toggle("on", m === "map");
      if (m === "map") initMap();
      else { storyEl.scrollTop = 0; ys = 0; curIdx = -1; autoMapDone = false; dirty = true; }
      setTimeout(() => fade.classList.remove("on"), 120);
    }, 700);
  }
  $("mode-btn").addEventListener("click", () => setMode(mode === "map" ? "story" : "map"));

  /* ================= ERKIN XARITA (kerak bo'lganda yuklanadi) ================= */
  const KEY = CFG.maptilerKey || "";
  let map = null, mapLoading = false, styleKind = "map", terrainOn = false, meMarker = null, darkFailed = false;

  function loadLib() {
    return new Promise((ok, no) => {
      if (window.maplibregl) return ok();
      const css = document.createElement("link");
      css.rel = "stylesheet"; css.href = "https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.css";
      document.head.append(css);
      const s = document.createElement("script");
      s.src = "https://unpkg.com/maplibre-gl@5.6.0/dist/maplibre-gl.js";
      s.onload = ok; s.onerror = no;
      document.head.append(s);
    });
  }
  function vectorStyle() {
    const dark = !TH.light && !darkFailed;
    if (KEY) return "https://api.maptiler.com/maps/" + (dark ? "streets-v2-dark" : "streets-v2") + "/style.json?key=" + KEY;
    return "https://tiles.openfreemap.org/styles/" + (dark ? "dark" : "liberty");
  }
  function satStyle() {
    const src = KEY
      ? { type: "raster", tiles: ["https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key=" + KEY], tileSize: 512, maxzoom: 20, attribution: "© MapTiler © OpenStreetMap contributors" }
      : { type: "raster", tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"], tileSize: 256, maxzoom: 19, attribution: "Imagery © Esri, Maxar, Earthstar Geographics" };
    return { version: 8, sources: { sat: src }, layers: [{ id: "sat", type: "raster", source: "sat" }] };
  }
  function demSource() {
    return KEY ? { type: "raster-dem", url: "https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key=" + KEY, tileSize: 256 }
               : { type: "raster-dem", tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"], encoding: "terrarium", tileSize: 256, maxzoom: 15, attribution: "Terrain: Mapzen, AWS" };
  }
  function applyExtras() {
    try { map.setProjection({ type: "globe" }); } catch (e) { /* oddiy xarita */ }
    if (terrainOn) {
      try { if (!map.getSource("dem")) map.addSource("dem", demSource()); map.setTerrain({ source: "dem", exaggeration: 1.3 }); } catch (e) { /* relyefsiz */ }
    }
  }

  async function initMap() {
    if (map || mapLoading) { if (map) map.resize(); return; }
    mapLoading = true;
    try { await loadLib(); } catch (e) { toast(L.mapErr); mapLoading = false; return; }
    map = new maplibregl.Map({
      container: "map",
      style: vectorStyle(),
      center: [100, 30],
      zoom: innerWidth < 700 ? 1.2 : 1.8,
      pixelRatio: Math.min(devicePixelRatio || 1, LITE ? 1 : 1.5),
      maxPitch: 75,
      attributionControl: { compact: true },
      fadeDuration: 0
    });
    map.on("style.load", applyExtras);
    map.on("error", (e) => {
      // Tungi uslub topilmasa, oddiy uslubga qaytadi
      if (!TH.light && !darkFailed && styleKind === "map" && !map.isStyleLoaded()) { darkFailed = true; map.setStyle(vectorStyle(), { diff: false }); }
      if (e && e.error) console.warn("Map:", e.error.message || e.error);
    });
    mapLoading = false;
  }

  $("style-lbl").textContent = L.styleSat;
  $("style-btn").addEventListener("click", () => {
    if (!map) return;
    styleKind = styleKind === "map" ? "sat" : "map";
    $("style-lbl").textContent = styleKind === "map" ? L.styleSat : L.styleMap;
    $("style-btn").classList.toggle("on", styleKind === "sat");
    map.setStyle(styleKind === "map" ? vectorStyle() : satStyle(), { diff: false });
  });
  $("tilt-btn").addEventListener("click", () => {
    if (!map) return;
    terrainOn = !terrainOn;
    $("tilt-btn").classList.toggle("on", terrainOn);
    if (terrainOn) { applyExtras(); map.easeTo({ pitch: 60, duration: 1200 }); }
    else { try { map.setTerrain(null); } catch (e) { /* */ } map.easeTo({ pitch: 0, duration: 1000 }); }
  });

  // Mavzu o'zgarsa: tuman rangi va xarita uslubi ham o'zgaradi
  new MutationObserver(() => {
    const n = readTheme();
    if (n.light === TH.light) return;
    TH = n; fogTex = null; grads = null; dirty = true;
    if (map && styleKind === "map") map.setStyle(vectorStyle(), { diff: false });
  }).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });

  // Qidiruv (OpenStreetMap, server orqali)
  const searchIn = $("search-input"), resultsEl = $("search-results");
  searchIn.placeholder = L.search;
  document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = L[el.dataset.t] || ""; });
  let sT = 0, sSeq = 0;
  async function doSearch(q) {
    q = q.trim();
    if (q.length < 2) { resultsEl.style.display = "none"; return; }
    const my = ++sSeq;
    try {
      const r = await fetch("/api/map/search?q=" + encodeURIComponent(q) + "&lang=" + LANG);
      const j = await r.json();
      if (my !== sSeq) return;
      const res = j.results || [];
      resultsEl.innerHTML = res.length
        ? res.map((x, k) => '<button type="button" data-k="' + k + '">' + esc(x.name) + "<small>" + esc(x.display) + "</small></button>").join("")
        : '<button type="button" disabled>' + esc(L.notFound) + "</button>";
      resultsEl.querySelectorAll("button[data-k]").forEach((b) => b.addEventListener("click", () => {
        const x = res[+b.dataset.k];
        resultsEl.style.display = "none"; searchIn.blur();
        if (!map) return;
        if (x.bbox) map.fitBounds([[x.bbox[2], x.bbox[0]], [x.bbox[3], x.bbox[1]]], { padding: 60, maxZoom: 16, duration: 2500 });
        else map.flyTo({ center: [x.lon, x.lat], zoom: 13, duration: 2500 });
      }));
      resultsEl.style.display = "block";
    } catch (e) { resultsEl.style.display = "none"; }
  }
  searchIn.addEventListener("input", () => { clearTimeout(sT); sT = setTimeout(() => doSearch(searchIn.value), 450); });
  searchIn.addEventListener("keydown", (e) => { if (e.key === "Enter") { clearTimeout(sT); doSearch(searchIn.value); } });
  document.addEventListener("click", (e) => { if (!e.target.closest(".lm-search")) resultsEl.style.display = "none"; });

  $("locate-btn").addEventListener("click", () => {
    if (!navigator.geolocation || !map) { toast(L.noLoc); return; }
    navigator.geolocation.getCurrentPosition((pos) => {
      const ll = [pos.coords.longitude, pos.coords.latitude];
      if (!meMarker) { const el = document.createElement("div"); el.className = "me-dot"; meMarker = new maplibregl.Marker({ element: el }).setLngLat(ll).addTo(map); }
      else meMarker.setLngLat(ll);
      map.flyTo({ center: ll, zoom: 15, duration: 3000 });
    }, () => toast(L.noLoc), { enableHighAccuracy: true, timeout: 10000 });
  });

  if (CFG.startMode === "explore") setMode("map");
})();
