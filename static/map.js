/* =====================================================================
   LINKO MAP
   1. Kinematik sayohat: haqiqiy videolar, scroll bilan boshqariladi
      (samolyot uchishi va Xitoy devori bo'ylab dron — scroll bilan oldinga/orqaga)
   2. Oxiriga yetganda avtomatik ravishda erkin xaritaga o'tadi
   3. Erkin xarita: yorug', yengil; qidiruv, joylashuvim, sun'iy yo'ldosh, 3D
   ===================================================================== */
(function () {
  "use strict";

  /* ================= SOZLAMALAR VA TILLAR ================= */
  const CFG = window.LINKO_MAP || {};
  const STORY = window.LINKO_STORY || [];
  const LITE = matchMedia("(pointer: coarse)").matches ||
               (navigator.deviceMemory || 8) <= 4 ||
               (navigator.hardwareConcurrency || 8) <= 4;
  const CONN = navigator.connection || {};
  const SLOW = !!CONN.saveData || /(^|-)2g|3g/.test(CONN.effectiveType || "");
  const REDUCED = document.documentElement.classList.contains("reduce-motion");
  // Video sifati: katta ekranli kuchli kompyuterda 1280, qolganlarida 960
  const Q = (!LITE && !SLOW && window.innerWidth * (window.devicePixelRatio || 1) > 1300) ? 1280 : 960;

  const I18N = {
    uz: { start: "Sayohatni boshlash", hint: "↓ pastga aylantiring", toMap: "Xarita", toStory: "Sayohat",
          outroTitle: "Endi o'zingiz kashf eting", outroText: "Xaritada istalgan joyni toping.",
          search: "Joy qidirish: Pekin, Parij, Dubay...", locate: "Men", styleSat: "Sun'iy yo'ldosh", styleMap: "Xarita",
          noLoc: "Joylashuvni aniqlab bo'lmadi.", notFound: "Hech narsa topilmadi.", mapErr: "Xarita yuklanmadi. Internetni tekshiring.",
          voiceUz: "O'zbekcha ovoz topilmadi, turkcha ovoz bilan o'qiladi." },
    en: { start: "Start the journey", hint: "↓ scroll down", toMap: "Map", toStory: "Journey",
          outroTitle: "Now explore on your own", outroText: "Find any place on the map.",
          search: "Search: Beijing, Paris, Dubai...", locate: "Me", styleSat: "Satellite", styleMap: "Map",
          noLoc: "Couldn't get your location.", notFound: "Nothing found.", mapErr: "The map didn't load. Check your internet.",
          voiceUz: "No Uzbek voice found, using a Turkish voice." },
    ru: { start: "Начать путешествие", hint: "↓ прокрутите вниз", toMap: "Карта", toStory: "Путешествие",
          outroTitle: "Теперь исследуйте сами", outroText: "Найдите любое место на карте.",
          search: "Поиск: Пекин, Париж, Дубай...", locate: "Я", styleSat: "Спутник", styleMap: "Карта",
          noLoc: "Не удалось определить местоположение.", notFound: "Ничего не найдено.", mapErr: "Карта не загрузилась. Проверьте интернет.",
          voiceUz: "Узбекский голос не найден, используется турецкий." },
    zh: { start: "开始旅程", hint: "↓ 向下滚动", toMap: "地图", toStory: "旅程",
          outroTitle: "现在自己去探索吧", outroText: "在地图上查找任何地点。",
          search: "搜索：北京、巴黎、迪拜...", locate: "我", styleSat: "卫星图", styleMap: "地图",
          noLoc: "无法获取你的位置。", notFound: "未找到结果。", mapErr: "地图加载失败，请检查网络。",
          voiceUz: "未找到乌兹别克语语音，将使用土耳其语语音。" }
  };
  const LANG = I18N[CFG.lang] ? CFG.lang : "en";
  const L = I18N[LANG];
  const LOCALES = { uz: "uz-UZ", en: "en-US", ru: "ru-RU", zh: "zh-CN", tr: "tr-TR" };

  const $ = (id) => document.getElementById(id);
  function lsGet(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* ixtiyoriy */ } }
  function esc(s) { const d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  let toastT = 0;
  function toast(m) { const t = $("toast"); t.textContent = m; t.classList.add("show"); clearTimeout(toastT); toastT = setTimeout(() => t.classList.remove("show"), 3200); }
  const clamp = (v, a, b) => (v < a ? a : v > b ? b : v);
  const smooth = (e0, e1, x) => { const t = clamp((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); };

  /* ================= MEDIA MANZILLARI ================= */
  // MEDIA_BASE (Cloudflare) berilsa, videolar o'sha yerdan; bo'lmasa to'g'ridan-to'g'ri Pexels'dan
  function videoUrl(s) {
    if (CFG.mediaBase) return CFG.mediaBase.replace(/\/$/, "") + "/" + s.id + "_" + Q + ".mp4";
    return "https://videos.pexels.com/video-files/" + s.pexels[Q];
  }
  function posterUrl(s) {
    if (CFG.mediaBase) return CFG.mediaBase.replace(/\/$/, "") + "/" + s.id + ".jpg";
    return s.poster + "?auto=compress&cs=tinysrgb&w=" + (Q === 1280 ? 1280 : 960);
  }

  /* ================= SAHNALAR ================= */
  const stage = $("stage"), storyEl = $("story"), track = $("track");
  const OUTRO = 0.9;                                  // oxirgi bo'sh qism (ekran balandligi)
  const scenes = STORY.map((s, i) => {
    const el = document.createElement("div");
    el.className = "scene";
    const img = document.createElement("img");
    img.alt = "";
    img.decoding = "async";
    if (i < 2) img.src = posterUrl(s);
    const v = document.createElement("video");
    v.muted = true; v.playsInline = true; v.preload = "none";
    v.setAttribute("muted", ""); v.setAttribute("playsinline", "");
    v.addEventListener("loadeddata", () => v.classList.add("ready"));
    el.append(img, v);
    stage.append(el);
    return { s, el, img, v, loaded: false, cur: s.from, start: 0, end: 0 };
  });

  let VH = window.innerHeight, total = 0;
  function measure() {
    VH = storyEl.clientHeight || window.innerHeight;
    let y = 0;
    scenes.forEach((sc) => { sc.start = y; y += sc.s.len * VH; sc.end = y; });
    total = y + OUTRO * VH;
    track.style.height = (total + VH) + "px";
  }
  measure();
  window.addEventListener("resize", () => { const r = storyEl.scrollTop / Math.max(1, total); measure(); storyEl.scrollTop = r * total; });

  function load(sc, auto) {
    if (!sc.img.src) sc.img.src = posterUrl(sc.s);
    if (sc.loaded) return;
    sc.loaded = true;
    sc.v.preload = auto ? "auto" : "metadata";
    sc.v.src = videoUrl(sc.s);
    sc.v.addEventListener("loadedmetadata", () => { try { sc.v.currentTime = sc.s.from; } catch (e) { /* keyin */ } }, { once: true });
  }
  function unload(sc) {
    if (!sc.loaded) return;
    sc.loaded = false;
    sc.v.pause();
    sc.v.classList.remove("ready");
    sc.v.removeAttribute("src");
    sc.v.load();
  }

  /* ================= MATN VA ASBOBLAR ================= */
  const capEl = $("caption"), capTag = $("cap-tag"), capTitle = $("cap-title"), capStat = $("cap-stat"), capText = $("cap-text"), capExtra = $("cap-extra");
  const hud = $("hud"), hudSpd = $("hud-spd"), hudAlt = $("hud-alt"), hudSpdU = $("hud-spd-u"), hudAltU = $("hud-alt-u");
  let capIdx = -2;
  function setCaption(i) {
    if (i === capIdx) return;
    capIdx = i;
    if (i >= scenes.length) {
      capTag.textContent = "LINKO MAP";
      capTitle.textContent = L.outroTitle;
      capStat.textContent = "";
      capText.textContent = L.outroText;
      capExtra.innerHTML = "";
      return;
    }
    const s = scenes[i].s;
    capTag.textContent = s.tag || "";
    capTitle.textContent = s.title[LANG] || s.title.en;
    capStat.textContent = s.stat || "";
    capText.textContent = s.text[LANG] || s.text.en;
    capExtra.innerHTML = i === 0
      ? '<button type="button" class="cap-start" id="start-btn">' + esc(L.start) + ' ↓</button><div class="cap-hint">' + esc(L.hint) + "</div>"
      : "";
    if (i === 0) $("start-btn").addEventListener("click", () => { Voice.unlock(); storyEl.scrollTo({ top: VH * 0.9, behavior: "smooth" }); });
  }
  function fmtNum(n) { return Math.round(n).toLocaleString("en-US").replace(/,/g, " "); }
  function setHud(kind, p) {
    if (!kind) { hud.classList.remove("show"); return; }
    hud.classList.add("show");
    let spd = 0, alt = 0, su = "kt", au = "ft";
    if (kind === "takeoff") { spd = 165 * smooth(0, 0.45, p) + 15 * smooth(0.45, 1, p); alt = 1500 * Math.pow(smooth(0.42, 1, p), 1.6); }
    else if (kind === "climb") { spd = 180 + 70 * p; alt = 1500 + 8500 * p; }
    else if (kind === "cruise") { spd = 250 + 230 * smooth(0, 0.6, p); alt = 10000 + 25000 * smooth(0, 0.6, p); }
    else if (kind === "space") { spd = 27600; alt = 400; su = "km/h"; au = "km"; }
    hudSpd.textContent = fmtNum(spd); hudAlt.textContent = fmtNum(alt);
    hudSpdU.textContent = su; hudAltU.textContent = au;
  }

  /* ================= NUQTALAR VA PROGRESS ================= */
  const dotsEl = $("dots");
  dotsEl.innerHTML = scenes.map((sc, i) => '<button type="button" data-i="' + i + '" title="' + esc(sc.s.title[LANG] || sc.s.title.en) + '"></button>').join("");
  dotsEl.addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) storyEl.scrollTo({ top: scenes[+b.dataset.i].start + 2, behavior: "smooth" }); });
  const dotBtns = [...dotsEl.querySelectorAll("button")];

  /* ================= OVOZ ================= */
  const Voice = {
    on: lsGet("linko_map_voice", "1") === "1", synth: window.speechSynthesis || null, unlocked: false, warned: false, timer: 0,
    unlock() { this.unlocked = true; },
    pick(code) {
      const vs = this.synth ? this.synth.getVoices() : [];
      const c = vs.filter((v) => v.lang && v.lang.toLowerCase().replace("_", "-").indexOf(code) === 0);
      return c.find((v) => /natural|neural|online|google|premium|enhanced/i.test(v.name)) || c[0] || null;
    },
    // Sahnaga kirgandan 0,9 soniya keyin o'qiydi (tez scroll qilinsa, o'qimaydi)
    schedule(text) {
      clearTimeout(this.timer);
      this.stop();
      if (!this.on || !this.unlocked || !this.synth || !text) return;
      this.timer = setTimeout(() => this.speak(text), 900);
    },
    speak(text) {
      let lang = LANG, voice = this.pick(lang);
      if (!voice && lang === "uz") { voice = this.pick("tr"); if (voice) lang = "tr"; if (!this.warned) { toast(L.voiceUz); this.warned = true; } }
      text.replace(/([.!?。！？])\s*/g, "$1\u0001").split("\u0001").filter((x) => x.trim()).forEach((part) => {
        const u = new SpeechSynthesisUtterance(part);
        u.lang = voice ? voice.lang : LOCALES[lang];
        if (voice) u.voice = voice;
        this.synth.speak(u);
      });
    },
    stop() { if (this.synth) this.synth.cancel(); }
  };
  if (Voice.synth) { Voice.synth.getVoices(); if ("onvoiceschanged" in Voice.synth) Voice.synth.onvoiceschanged = () => Voice.synth.getVoices(); }
  ["pointerdown", "keydown", "touchstart", "wheel"].forEach((ev) => window.addEventListener(ev, () => Voice.unlock(), { passive: true, once: true }));
  window.addEventListener("pagehide", () => Voice.stop());
  const voiceBtn = $("voice-btn");
  function paintVoice() { voiceBtn.classList.toggle("on", Voice.on); voiceBtn.style.opacity = Voice.on ? 1 : 0.6; }
  voiceBtn.addEventListener("click", () => {
    Voice.on = !Voice.on; Voice.unlock(); lsSet("linko_map_voice", Voice.on ? "1" : "0"); paintVoice();
    if (!Voice.on) Voice.stop(); else if (activeIdx >= 0 && activeIdx < scenes.length) { const s = scenes[activeIdx].s; Voice.schedule((s.title[LANG] || s.title.en) + ". " + (s.text[LANG] || s.text.en)); }
  });
  paintVoice();

  /* ================= ASOSIY SIKL ================= */
  let activeIdx = -1, mode = "story", autoMapDone = false;
  const progEl = $("progress");

  function frame() {
    if (mode === "story") tick();
    requestAnimationFrame(frame);
  }

  function tick() {
    const y = storyEl.scrollTop;
    progEl.style.width = (clamp(y / total, 0, 1) * 100) + "%";

    // Qaysi sahna faol
    let i = scenes.findIndex((sc) => y >= sc.start && y < sc.end);
    if (i < 0) i = y >= (scenes.length ? scenes[scenes.length - 1].end : 0) ? scenes.length : 0;

    if (i !== activeIdx) {
      activeIdx = i;
      dotBtns.forEach((b, k) => b.classList.toggle("on", k === i));
      // Yaqin sahnalarni yuklash, uzoqdagilarni bo'shatish (xotira tejaladi)
      scenes.forEach((sc, k) => {
        if (k === i || k === i + 1) load(sc, true);
        else if (k === i + 2 || k === i - 1) load(sc, false);
        else if (Math.abs(k - i) > 2) unload(sc);
      });
      if (i < scenes.length) {
        const s = scenes[i].s;
        Voice.schedule((s.title[LANG] || s.title.en) + ". " + (s.text[LANG] || s.text.en));
      } else Voice.stop();
    }

    // Har bir sahnaning ko'rinishi va videosi
    for (let k = 0; k < scenes.length; k++) {
      const sc = scenes[k];
      const p = clamp((y - sc.start) / (sc.end - sc.start), 0, 1);
      let op = 0;
      if (k === i) op = 1;
      else if (k === i + 1) op = smooth(0.82, 1, (y - scenes[i].start) / (scenes[i].end - scenes[i].start)); // keyingisi asta paydo bo'ladi
      if (i >= scenes.length && k === scenes.length - 1) op = 1;
      sc.el.style.opacity = op;
      sc.el.style.zIndex = k === i + 1 ? 2 : 1;

      const v = sc.v;
      if (op <= 0 || !sc.loaded) { if (!v.paused) v.pause(); continue; }
      if (sc.s.mode === "scrub") {
        // Scroll -> video vaqti (silliq)
        const pp = k === i + 1 ? 0 : p;
        const target = sc.s.from + (sc.s.to - sc.s.from) * pp;
        sc.cur += (target - sc.cur) * (REDUCED ? 1 : 0.18);
        if (!v.paused) v.pause();
        if (v.readyState >= 1 && !v.seeking && Math.abs(v.currentTime - sc.cur) > 0.04) {
          try { v.currentTime = sc.cur; } catch (e) { /* hali yuklanmagan */ }
        }
      } else {
        if (v.readyState >= 2 && v.paused) { const pr = v.play(); if (pr && pr.catch) pr.catch(() => {}); }
        if (v.currentTime > sc.s.to || v.ended) { try { v.currentTime = sc.s.from; } catch (e) { /* */ } }
      }
    }

    // Matn: sahna boshida paydo bo'ladi, oxirida yo'qoladi
    setCaption(i);
    if (i < scenes.length) {
      const sc = scenes[i], p = (y - sc.start) / (sc.end - sc.start);
      const a = i === 0 ? 1 - smooth(0.55, 0.8, p) : smooth(0.02, 0.16, p) * (1 - smooth(0.74, 0.88, p));
      capEl.style.opacity = a;
      capEl.style.transform = "translateY(" + ((1 - a) * 24) + "px)";
      setHud(sc.s.hud, clamp(p, 0, 1));
    } else {
      const p = (y - scenes[scenes.length - 1].end) / (OUTRO * VH);
      capEl.style.opacity = smooth(0, 0.3, p);
      capEl.style.transform = "none";
      setHud(null);
      // Oxiriga yetdi -> erkin xaritaga o'tish
      if (p > 0.85 && !autoMapDone) { autoMapDone = true; setMode("map"); }
    }
    if (y < total - VH) autoMapDone = false;
  }
  requestAnimationFrame(frame);

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
      if (m === "map") {
        Voice.stop();
        scenes.forEach((sc) => sc.v.pause());
        initMap();
      } else {
        storyEl.scrollTop = 0;
        activeIdx = -1;
      }
      setTimeout(() => fade.classList.remove("on"), 80);
    }, 550);
  }
  $("mode-btn").addEventListener("click", () => setMode(mode === "map" ? "story" : "map"));

  /* ================= ERKIN XARITA (kerak bo'lganda yuklanadi) ================= */
  const KEY = CFG.maptilerKey || "";
  let map = null, mapLoading = false, styleKind = "map", terrainOn = false, meMarker = null;

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
    return KEY ? "https://api.maptiler.com/maps/streets-v2/style.json?key=" + KEY : "https://tiles.openfreemap.org/styles/liberty";
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
      zoom: window.innerWidth < 700 ? 1.2 : 1.8,
      pixelRatio: Math.min(window.devicePixelRatio || 1, LITE ? 1 : 1.5),
      maxPitch: 75,
      attributionControl: { compact: true },
      fadeDuration: 0
    });
    map.on("style.load", applyExtras);
    map.on("error", (e) => { if (e && e.error) console.warn("Map:", e.error.message || e.error); });
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

  if (CFG.startMode === "explore") { mode = "story"; setMode("map"); }
})();
