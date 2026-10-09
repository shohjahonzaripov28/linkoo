/* =====================================================================
   LINKO MAP — 3D xarita: scroll-sayohat, erkin xarita, jonli samolyotlar,
   sun'iy yo'ldoshlar va ovozli hikoya.
   Tarkib:
     1. Sozlamalar va tillar
     2. Xarita uslublari (sun'iy yo'ldosh surati + 3D relyef)
     3. Xaritani yaratish
     4. Scroll-sayohat
     5. Ovoz (hikoya qilib berish)
     6. Jonli samolyotlar
     7. Sun'iy yo'ldoshlar va XKS (orbita hisob-kitobi)
     8. Erkin xarita: qidiruv, joylashuvim, tugmalar
     9. Yulduzli osmon va animatsiya sikli
   ===================================================================== */
(function () {
  "use strict";

  /* ================= 1. SOZLAMALAR VA TILLAR ================= */
  const CFG = window.LINKO_MAP || {};
  const TOUR = window.LINKO_TOUR || [];
  const KEY = CFG.maptilerKey || "";
  const LITE = matchMedia("(pointer: coarse)").matches ||
               (navigator.deviceMemory || 8) <= 4 ||
               (navigator.hardwareConcurrency || 8) <= 4;
  const REDUCED = document.documentElement.classList.contains("reduce-motion");

  const SETTINGS = {
    planesRefreshMs: 10000,     // samolyotlar har necha ms da yangilanadi
    satsRefreshMs: 1000,        // sun'iy yo'ldoshlar har sekund yangilanadi
    idleRotate: !LITE,          // bekatda kamera sekin aylanadi
    terrainExaggeration: 1.3,   // tog'larni biroz bo'rttirish
    pixelRatio: Math.min(window.devicePixelRatio || 1, LITE ? 1 : 1.5)
  };

  const I18N = {
    uz: {
      introTitle: "Dunyo bo'ylab 3D sayohat",
      introText: "Everest cho'qqisidan Xitoy va Buxorogacha, okeanlardan kosmosgacha. Pastga aylantiring, kamera o'zi uchib boradi.",
      start: "Sayohatni boshlash", explore: "Erkin xarita", tour: "Sayohat", hint: "↓ pastga aylantiring",
      listen: "Tinglash", askAi: "Linko AI'dan so'rash", livePlanes: "Jonli samolyotlar", liveSats: "Jonli sun'iy yo'ldoshlar",
      outroTitle: "Endi o'zingiz kashf eting", outroText: "Istalgan joyni qidiring, joylashuvingizni toping, samolyot va sun'iy yo'ldoshlarni kuzating.",
      search: "Joy qidirish: Buxoro, Pekin, Parij...", locate: "Men", planes: "Samolyotlar", sats: "Yo'ldoshlar",
      styleSat: "Sun'iy yo'ldosh", styleMap: "Xarita",
      noLoc: "Joylashuvni aniqlab bo'lmadi.", zoomIn: "Samolyotlarni ko'rish uchun xaritani yaqinlashtiring.",
      noPlanes: "Bu hududda hozir samolyot topilmadi.", planesErr: "Samolyot ma'lumoti hozir yuklanmadi.",
      satsErr: "Sun'iy yo'ldosh ma'lumoti yuklanmadi.", notFound: "Hech narsa topilmadi.",
      mapErr: "Xarita yuklanmadi. Internetni tekshiring.", voiceUz: "O'zbekcha ovoz topilmadi, turkcha ovoz bilan o'qiladi.",
      alt: "Balandlik", speed: "Tezlik", type: "Turi", askQ: "{name} haqida batafsil gapirib ber",
      planesCount: "{n} ta samolyot", satsCount: "{n} ta sun'iy yo'ldosh"
    },
    en: {
      introTitle: "A 3D journey around the world",
      introText: "From the summit of Everest to China and Bukhara, from the oceans to space. Scroll down and the camera flies by itself.",
      start: "Start the journey", explore: "Free map", tour: "Journey", hint: "↓ scroll down",
      listen: "Listen", askAi: "Ask Linko AI", livePlanes: "Live planes", liveSats: "Live satellites",
      outroTitle: "Now explore on your own", outroText: "Search any place, find your location, and follow planes and satellites.",
      search: "Search: Bukhara, Beijing, Paris...", locate: "Me", planes: "Planes", sats: "Satellites",
      styleSat: "Satellite", styleMap: "Map",
      noLoc: "Couldn't get your location.", zoomIn: "Zoom in to see planes.",
      noPlanes: "No planes found in this area right now.", planesErr: "Couldn't load plane data right now.",
      satsErr: "Couldn't load satellite data.", notFound: "Nothing found.",
      mapErr: "The map didn't load. Check your internet connection.", voiceUz: "No Uzbek voice found, using a Turkish voice.",
      alt: "Altitude", speed: "Speed", type: "Type", askQ: "Tell me more about {name}",
      planesCount: "{n} planes", satsCount: "{n} satellites"
    },
    ru: {
      introTitle: "3D-путешествие по миру",
      introText: "С вершины Эвереста до Китая и Бухары, от океанов до космоса. Прокручивайте вниз — камера летит сама.",
      start: "Начать путешествие", explore: "Свободная карта", tour: "Путешествие", hint: "↓ прокрутите вниз",
      listen: "Слушать", askAi: "Спросить Linko AI", livePlanes: "Самолёты онлайн", liveSats: "Спутники онлайн",
      outroTitle: "Теперь исследуйте сами", outroText: "Ищите любые места, найдите себя на карте, следите за самолётами и спутниками.",
      search: "Поиск: Бухара, Пекин, Париж...", locate: "Я", planes: "Самолёты", sats: "Спутники",
      styleSat: "Спутник", styleMap: "Карта",
      noLoc: "Не удалось определить местоположение.", zoomIn: "Приблизьте карту, чтобы увидеть самолёты.",
      noPlanes: "Сейчас в этом районе самолётов нет.", planesErr: "Не удалось загрузить данные о самолётах.",
      satsErr: "Не удалось загрузить данные о спутниках.", notFound: "Ничего не найдено.",
      mapErr: "Карта не загрузилась. Проверьте интернет.", voiceUz: "Узбекский голос не найден, используется турецкий.",
      alt: "Высота", speed: "Скорость", type: "Тип", askQ: "Расскажи подробнее о месте {name}",
      planesCount: "Самолётов: {n}", satsCount: "Спутников: {n}"
    },
    zh: {
      introTitle: "环游世界的3D之旅",
      introText: "从珠穆朗玛峰到中国和布哈拉，从海洋到太空。向下滚动，镜头会自动飞行。",
      start: "开始旅程", explore: "自由地图", tour: "旅程", hint: "↓ 向下滚动",
      listen: "收听", askAi: "问问 Linko AI", livePlanes: "实时航班", liveSats: "实时卫星",
      outroTitle: "现在自己去探索吧", outroText: "搜索任何地点，找到你的位置，追踪飞机和卫星。",
      search: "搜索：布哈拉、北京、巴黎...", locate: "我", planes: "飞机", sats: "卫星",
      styleSat: "卫星图", styleMap: "地图",
      noLoc: "无法获取你的位置。", zoomIn: "请放大地图以查看飞机。",
      noPlanes: "该区域目前没有飞机。", planesErr: "暂时无法加载航班数据。",
      satsErr: "无法加载卫星数据。", notFound: "未找到结果。",
      mapErr: "地图加载失败，请检查网络。", voiceUz: "未找到乌兹别克语语音，将使用土耳其语语音。",
      alt: "高度", speed: "速度", type: "机型", askQ: "请详细介绍{name}",
      planesCount: "{n} 架飞机", satsCount: "{n} 颗卫星"
    }
  };
  const LANG = I18N[CFG.lang] ? CFG.lang : "en";
  const L = I18N[LANG];
  const LOCALES = { uz: "uz-UZ", en: "en-US", ru: "ru-RU", zh: "zh-CN", tr: "tr-TR" };

  function lsGet(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } }
  function lsSet(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* bo'lmasa ham ishlaydi */ } }
  function esc(s) { const d = document.createElement("div"); d.textContent = s == null ? "" : String(s); return d.innerHTML; }
  function fmt(s, o) { return s.replace(/\{(\w+)\}/g, (m, k) => (o[k] != null ? o[k] : m)); }

  const $ = (id) => document.getElementById(id);
  const toastEl = $("mp-toast");
  let toastTimer = 0;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("show"), 3200);
  }
  const hudEl = $("mp-hud");
  function hud(text) { hudEl.textContent = text; }

  /* ================= 2. XARITA USLUBLARI ================= */
  const SKY = {
    "sky-color": "#061226",
    "sky-horizon-blend": 0.6,
    "horizon-color": "#2a6fb5",
    "horizon-fog-blend": 0.6,
    "fog-color": "#0a1a33",
    "fog-ground-blend": 0.35,
    "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 5, 1, 8, 0]
  };

  function satSource() {
    if (KEY) {
      return { type: "raster", tiles: ["https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key=" + KEY],
               tileSize: 512, maxzoom: 20, attribution: "© MapTiler © OpenStreetMap contributors" };
    }
    // Kalit bo'lmaganda vaqtincha Esri World Imagery (bepul, atributsiya bilan)
    return { type: "raster", tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"],
             tileSize: 256, maxzoom: 19, attribution: "Imagery © Esri, Maxar, Earthstar Geographics" };
  }
  function demSource() {
    if (KEY) return { type: "raster-dem", url: "https://api.maptiler.com/tiles/terrain-rgb-v2/tiles.json?key=" + KEY, tileSize: 256 };
    // Ochiq relyef ma'lumoti (AWS Terrain Tiles, Terrarium formati)
    return { type: "raster-dem", tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
             encoding: "terrarium", tileSize: 256, maxzoom: 15, attribution: "Terrain: Mapzen, AWS Terrain Tiles" };
  }
  function satelliteStyle() {
    return {
      version: 8,
      sources: { sat: satSource(), dem: demSource() },
      layers: [{ id: "sat", type: "raster", source: "sat", paint: { "raster-fade-duration": 250 } }],
      terrain: { source: "dem", exaggeration: SETTINGS.terrainExaggeration },
      sky: SKY
    };
  }
  function vectorStyleUrl() {
    return KEY ? "https://api.maptiler.com/maps/streets-v2-dark/style.json?key=" + KEY
               : "https://tiles.openfreemap.org/styles/liberty";
  }
  let styleKind = "sat";

  /* ================= 3. XARITANI YARATISH ================= */
  if (!window.maplibregl) {
    toast(L.mapErr);
    hud("OFFLINE");
    return;
  }

  const map = new maplibregl.Map({
    container: "map",
    style: satelliteStyle(),
    center: [65, 30],
    zoom: 1.4,
    pitch: 0,
    maxPitch: 85,
    pixelRatio: SETTINGS.pixelRatio,
    attributionControl: { compact: true },
    fadeDuration: 150
  });
  map.on("error", (e) => { if (e && e.error) console.warn("Map:", e.error.message || e.error); });

  function onStyleLoad() {
    try { map.setProjection({ type: "globe" }); } catch (e) { /* eski brauzer: oddiy xarita */ }
    try { if (!map.getSource("dem")) map.addSource("dem", demSource()); } catch (e) { /* bor */ }
    try { map.setTerrain({ source: "dem", exaggeration: SETTINGS.terrainExaggeration }); } catch (e) { /* relyefsiz */ }
    try { map.setSky(SKY); } catch (e) { /* osmonsiz */ }
    addOverlays();
  }
  map.on("style.load", onStyleLoad);

  // Samolyot belgisi (rasm fayli kerak emas, canvas'da chiziladi)
  function planeImage() {
    const s = 64, c = document.createElement("canvas");
    c.width = c.height = s;
    const g = c.getContext("2d");
    g.translate(s / 2, s / 2);
    g.fillStyle = "#e8f6ff";
    g.shadowColor = "rgba(80,200,255,0.9)";
    g.shadowBlur = 6;
    g.beginPath();
    g.moveTo(0, -26); g.lineTo(4, -16); g.lineTo(4, -4); g.lineTo(24, 6); g.lineTo(24, 11); g.lineTo(4, 5);
    g.lineTo(4, 16); g.lineTo(10, 21); g.lineTo(10, 25); g.lineTo(0, 22); g.lineTo(-10, 25); g.lineTo(-10, 21);
    g.lineTo(-4, 16); g.lineTo(-4, 5); g.lineTo(-24, 11); g.lineTo(-24, 6); g.lineTo(-4, -4); g.lineTo(-4, -16);
    g.closePath();
    g.fill();
    return g.getImageData(0, 0, s, s);
  }
  const EMPTY = { type: "FeatureCollection", features: [] };

  function addOverlays() {
    if (!map.hasImage("plane")) map.addImage("plane", planeImage(), { pixelRatio: 2 });
    if (!map.getSource("orbit")) map.addSource("orbit", { type: "geojson", data: Sats.orbitData || EMPTY });
    if (!map.getSource("sats")) map.addSource("sats", { type: "geojson", data: Sats.lastData || EMPTY });
    if (!map.getSource("planes")) map.addSource("planes", { type: "geojson", data: Planes.lastData || EMPTY });
    if (!map.getLayer("orbit")) {
      map.addLayer({ id: "orbit", type: "line", source: "orbit",
        paint: { "line-color": "#ffd166", "line-width": 1.6, "line-opacity": 0.75, "line-dasharray": [2, 2] } });
    }
    if (!map.getLayer("sats")) {
      map.addLayer({ id: "sats", type: "circle", source: "sats",
        paint: {
          "circle-radius": ["match", ["get", "g"], "stations", 4.5, "starlink", 1.6, 2.6],
          "circle-color": ["match", ["get", "g"], "stations", "#ffd166", "starlink", "#e2e8f0", "gps", "#86efac", "#7dd3fc"],
          "circle-opacity": 0.9,
          "circle-blur": 0.3
        } });
    }
    if (!map.getLayer("planes")) {
      map.addLayer({ id: "planes", type: "symbol", source: "planes",
        layout: {
          "icon-image": "plane",
          "icon-size": ["interpolate", ["linear"], ["zoom"], 3, 0.35, 8, 0.55, 13, 0.9],
          "icon-rotate": ["get", "trk"],
          "icon-rotation-alignment": "map",
          "icon-allow-overlap": true,
          "icon-ignore-placement": true
        },
        paint: { "icon-opacity": ["case", ["get", "gnd"], 0.45, 1] } });
    }
  }

  // Samolyotni bosganda ma'lumot oynasi
  map.on("click", "planes", (e) => {
    const f = e.features && e.features[0];
    if (!f) return;
    const p = Planes.data.get(f.properties.h);
    if (!p) return;
    new maplibregl.Popup({ closeButton: true, offset: 12 })
      .setLngLat(f.geometry.coordinates)
      .setHTML(
        "<b>✈️ " + esc(p.call || p.hex.toUpperCase()) + "</b><br>" +
        (p.type ? L.type + ": " + esc(p.type) + "<br>" : "") +
        L.alt + ": " + (p.gnd ? "0" : Math.round(p.alt * 0.3048).toLocaleString()) + " m<br>" +
        L.speed + ": " + Math.round(p.gs * 1.852) + " km/h"
      )
      .addTo(map);
  });
  map.on("mouseenter", "planes", () => { map.getCanvas().style.cursor = "pointer"; });
  map.on("mouseleave", "planes", () => { map.getCanvas().style.cursor = ""; });

  let userInteracting = false;
  map.on("mousedown", () => { userInteracting = true; });
  map.on("touchstart", () => { userInteracting = true; });
  map.on("mouseup", () => { userInteracting = false; });
  map.on("touchend", () => { userInteracting = false; });

  /* ================= 4. SCROLL-SAYOHAT ================= */
  const tourEl = $("tour");
  const dotsEl = $("mp-dots");
  const progEl = $("mp-progress");
  let mode = "tour";
  let activeIdx = -2;          // -1 = kirish, TOUR.length = yakun
  const sections = [];

  function iconSvg(path) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' + path + "</svg>";
  }
  const IC_SPEAK = iconSvg('<path d="M11 5L6 9H2v6h4l5 4V5z"/><path d="M15.5 8.5a5 5 0 0 1 0 7"/>');
  const IC_SPARK = iconSvg('<path d="M12 3l1.8 4.7L18.5 9.5l-4.7 1.8L12 16l-1.8-4.7L5.5 9.5l4.7-1.8z"/><path d="M19 15l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8z"/>');

  function buildTour() {
    let html = "";
    html += '<section class="mp-step mp-intro" data-i="-1"><div class="mp-card">' +
      '<div class="mp-num">LINKO MAP · 3D</div>' +
      "<h2>" + esc(L.introTitle) + "</h2>" +
      "<p>" + esc(L.introText) + "</p>" +
      '<div class="mp-actions">' +
      '<button type="button" class="mp-btn primary" id="start-btn"><span class="lbl">' + esc(L.start) + "</span> →</button>" +
      '<button type="button" class="mp-btn" data-explore="1"><span class="lbl">' + esc(L.explore) + "</span></button>" +
      "</div>" +
      '<div class="mp-scrollhint">' + esc(L.hint) + "</div>" +
      "</div></section>";
    TOUR.forEach((c, i) => {
      const name = c.name[LANG] || c.name.en;
      const text = c.text[LANG] || c.text.en;
      const q = encodeURIComponent(fmt(L.askQ, { name: name }));
      html += '<section class="mp-step" data-i="' + i + '"><div class="mp-card">' +
        '<div class="mp-num">' + String(i + 1).padStart(2, "0") + " / " + TOUR.length + "</div>" +
        "<h2>" + c.icon + " " + esc(name) + "</h2>" +
        '<div class="mp-stat">' + esc(c.stat) + "</div>" +
        (c.planes ? '<div class="mp-live"><i></i>' + esc(L.livePlanes) + ' · <span class="pl-count"></span></div>' : "") +
        (c.space ? '<div class="mp-live"><i></i>' + esc(L.liveSats) + ' · <span class="sat-count"></span></div>' : "") +
        "<p>" + esc(text) + "</p>" +
        '<div class="mp-actions">' +
        '<button type="button" class="mp-btn" data-speak="' + i + '">' + IC_SPEAK + '<span class="lbl">' + esc(L.listen) + "</span></button>" +
        '<a class="mp-btn" href="/ai?q=' + q + '" style="text-decoration:none">' + IC_SPARK + '<span class="lbl">' + esc(L.askAi) + "</span></a>" +
        "</div></div></section>";
    });
    html += '<section class="mp-step mp-intro" data-i="' + TOUR.length + '"><div class="mp-card">' +
      '<div class="mp-num">LINKO MAP</div>' +
      "<h2>" + esc(L.outroTitle) + "</h2>" +
      "<p>" + esc(L.outroText) + "</p>" +
      '<div class="mp-actions"><button type="button" class="mp-btn primary" data-explore="1"><span class="lbl">' + esc(L.explore) + "</span> →</button></div>" +
      "</div></section>";
    tourEl.innerHTML = html;
    tourEl.querySelectorAll(".mp-step").forEach((s) => sections.push(s));

    let dots = "";
    TOUR.forEach((c, i) => { dots += '<button type="button" data-go="' + i + '" title="' + esc(c.name[LANG] || c.name.en) + '"></button>'; });
    dotsEl.innerHTML = dots;
  }
  buildTour();

  function goTo(i) {
    const s = sections[i + 1];
    if (s) s.scrollIntoView({ behavior: REDUCED ? "auto" : "smooth" });
  }

  tourEl.addEventListener("click", (e) => {
    const t = e.target.closest("button");
    if (!t) return;
    if (t.id === "start-btn") { Voice.unlock(); goTo(0); return; }
    if (t.dataset.explore) { setMode("explore"); return; }
    if (t.dataset.speak != null) { Voice.unlock(); speakChapter(+t.dataset.speak, true); }
  });
  dotsEl.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) goTo(+b.dataset.go);
  });
  document.addEventListener("keydown", (e) => {
    if (mode !== "tour" || e.target.tagName === "INPUT") return;
    if (e.key === "ArrowDown" || e.key === " ") { e.preventDefault(); goTo(Math.min(TOUR.length, activeIdx + 1)); }
    if (e.key === "ArrowUp") { e.preventDefault(); goTo(Math.max(-1, activeIdx - 1)); }
  });

  // Qaysi bekat ekranda ko'rinib turganini kuzatish
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting && en.intersectionRatio >= 0.55) activate(+en.target.dataset.i);
    });
  }, { root: tourEl, threshold: [0.55] });
  sections.forEach((s) => io.observe(s));

  function distKm(a, b) {
    const R = 6371, toR = Math.PI / 180;
    const dLat = (b[1] - a[1]) * toR, dLon = (b[0] - a[0]) * toR;
    const h = Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * toR) * Math.cos(b[1] * toR) * Math.sin(dLon / 2) ** 2;
    return 2 * R * Math.asin(Math.sqrt(h));
  }

  function activate(i) {
    if (i === activeIdx || mode !== "tour") return;
    activeIdx = i;
    sections.forEach((s) => s.classList.toggle("active", +s.dataset.i === i));
    dotsEl.querySelectorAll("button").forEach((b, k) => b.classList.toggle("on", k === i));
    progEl.style.width = (Math.max(0, Math.min(TOUR.length, i + 1)) / TOUR.length * 100) + "%";

    if (i < 0 || i >= TOUR.length) {
      hud(i < 0 ? "GLOBAL VIEW" : "MISSION COMPLETE");
      Planes.set(false);
      Sats.set(i >= TOUR.length);
      flyCam({ center: [65, 30], zoom: LITE ? 1.3 : 1.5, pitch: 0, bearing: 0 }, 4000);
      Voice.stop();
      return;
    }
    const c = TOUR[i];
    hud(String(i + 1).padStart(2, "0") + " / " + TOUR.length + " · " + (c.name.en || "").toUpperCase());
    const from = map.getCenter();
    const d = distKm([from.lng, from.lat], [c.lon, c.lat]);
    const dur = REDUCED ? 0 : Math.max(2600, Math.min(LITE ? 6000 : 8500, 2200 + d * 0.9));
    try { map.setTerrain({ source: "dem", exaggeration: c.zoom >= 14 ? 1.0 : SETTINGS.terrainExaggeration }); } catch (e) { /* relyefsiz */ }
    flyCam({ center: [c.lon, c.lat], zoom: c.zoom, pitch: c.pitch, bearing: c.bearing }, dur);
    Planes.set(!!c.planes, [c.lon, c.lat]);
    Sats.set(!!c.space);
    speakChapter(i, false);
  }

  function flyCam(cam, duration) {
    map.stop();
    map.flyTo({ center: cam.center, zoom: cam.zoom, pitch: cam.pitch, bearing: cam.bearing,
                duration: duration, curve: 1.5, essential: true });
  }

  function setMode(m) {
    mode = m;
    document.body.classList.toggle("explore", m === "explore");
    $("mode-lbl").textContent = m === "explore" ? L.tour : L.explore;
    if (m === "explore") {
      Voice.stop();
      hud("EXPLORE MODE");
      Planes.set(planesBtnOn, null);
      Sats.set(satsBtnOn);
    } else {
      const i = activeIdx;
      activeIdx = -2;
      activate(i < -1 ? -1 : i);
    }
  }
  $("mode-btn").addEventListener("click", () => setMode(mode === "tour" ? "explore" : "tour"));

  /* ================= 5. OVOZ ================= */
  const Voice = {
    on: lsGet("linko_map_voice", "1") === "1",
    synth: window.speechSynthesis || null,
    unlocked: false, warnedUz: false, gen: 0,
    unlock() { this.unlocked = true; },
    pick(code) {
      const vs = this.synth ? this.synth.getVoices() : [];
      const c = vs.filter((v) => v.lang && v.lang.toLowerCase().replace("_", "-").indexOf(code) === 0);
      if (!c.length) return null;
      return c.find((v) => /natural|neural|online|google|premium|enhanced/i.test(v.name)) || c[0];
    },
    speak(text) {
      if (!this.synth || !this.on || !this.unlocked || !text) return;
      let lang = LANG, voice = this.pick(lang);
      if (!voice && lang === "uz") {
        voice = this.pick("tr");
        if (!this.warnedUz) { toast(L.voiceUz); this.warnedUz = true; }
        if (voice) lang = "tr";
      }
      this.stop();
      const my = ++this.gen;
      const parts = text.replace(/([.!?。！？])\s*/g, "$1\u0001").split("\u0001").filter((p) => p.trim());
      parts.forEach((p) => {
        const u = new SpeechSynthesisUtterance(p);
        u.lang = voice ? voice.lang : LOCALES[lang];
        if (voice) u.voice = voice;
        u.rate = 1.0;
        u.onend = () => { if (my !== this.gen) this.synth.cancel(); };
        this.synth.speak(u);
      });
    },
    stop() { this.gen++; if (this.synth) this.synth.cancel(); }
  };
  if (Voice.synth) {
    Voice.synth.getVoices();
    if ("onvoiceschanged" in Voice.synth) Voice.synth.onvoiceschanged = () => Voice.synth.getVoices();
  }
  window.addEventListener("pagehide", () => Voice.stop());
  ["pointerdown", "keydown", "touchstart"].forEach((ev) =>
    window.addEventListener(ev, () => Voice.unlock(), { passive: true, once: true }));

  function speakChapter(i, force) {
    const c = TOUR[i];
    if (!c) return;
    if (!force && !Voice.on) return;
    const was = Voice.on;
    if (force) Voice.on = true;
    Voice.speak((c.name[LANG] || c.name.en) + ". " + (c.text[LANG] || c.text.en));
    Voice.on = was;
  }
  const voiceBtn = $("voice-btn");
  function applyVoiceBtn() { voiceBtn.classList.toggle("on", Voice.on); voiceBtn.style.opacity = Voice.on ? 1 : 0.55; }
  voiceBtn.addEventListener("click", () => {
    Voice.on = !Voice.on;
    lsSet("linko_map_voice", Voice.on ? "1" : "0");
    Voice.unlock();
    applyVoiceBtn();
    if (!Voice.on) Voice.stop();
    else if (mode === "tour" && activeIdx >= 0 && activeIdx < TOUR.length) speakChapter(activeIdx, false);
  });
  applyVoiceBtn();

  /* ================= 6. JONLI SAMOLYOTLAR ================= */
  const Planes = {
    on: false, data: new Map(), timer: 0, center: null, lastData: null, busy: false,
    set(on, center) {
      this.on = on;
      clearInterval(this.timer);
      if (!on) {
        this.data.clear();
        this.push();
        return;
      }
      this.center = center || null;
      this.fetch();
      this.timer = setInterval(() => this.fetch(), SETTINGS.planesRefreshMs);
    },
    async fetch() {
      if (!this.on || this.busy || document.hidden) return;
      const c = this.center ? { lng: this.center[0], lat: this.center[1] } : map.getCenter();
      const z = map.getZoom();
      if (!this.center && z < 4) { toast(L.zoomIn); return; }
      const dist = z >= 10 ? 40 : z >= 8 ? 80 : z >= 6 ? 150 : 250;
      this.busy = true;
      try {
        const r = await fetch("/api/map/planes?lat=" + c.lat.toFixed(2) + "&lon=" + c.lng.toFixed(2) + "&dist=" + dist);
        const j = await r.json();
        if (!r.ok || !j.ac) throw new Error(j.error || "planes");
        const now = performance.now(), seen = new Set();
        j.ac.forEach((a) => {
          seen.add(a.h);
          this.data.set(a.h, { hex: a.h, call: a.c, type: a.ty, lat: a.la, lon: a.lo, alt: a.al || 0, gs: a.gs || 0, trk: a.tr || 0, gnd: !!a.g, t: now });
        });
        this.data.forEach((v, k) => { if (!seen.has(k)) this.data.delete(k); });
        document.querySelectorAll(".pl-count").forEach((el) => { el.textContent = fmt(L.planesCount, { n: this.data.size }); });
        if (!this.data.size && mode === "explore") toast(L.noPlanes);
      } catch (e) {
        if (this.on) toast(L.planesErr);
      }
      this.busy = false;
    },
    // Samolyotni tezligi va yo'nalishi bo'yicha silliq siljitish (yangilanishlar orasida)
    tick() {
      if (!this.on || !this.data.size) return;
      const now = performance.now(), feats = [];
      this.data.forEach((p) => {
        let lat = p.lat, lon = p.lon;
        if (!p.gnd && p.gs > 0) {
          const km = p.gs * 1.852 * ((now - p.t) / 3600000);
          const r = p.trk * Math.PI / 180;
          lat += (km * Math.cos(r)) / 111.32;
          lon += (km * Math.sin(r)) / (111.32 * Math.max(0.2, Math.cos(p.lat * Math.PI / 180)));
        }
        feats.push({ type: "Feature", geometry: { type: "Point", coordinates: [lon, lat] }, properties: { h: p.hex, trk: p.trk, gnd: p.gnd } });
      });
      this.lastData = { type: "FeatureCollection", features: feats };
      const src = map.getSource("planes");
      if (src) src.setData(this.lastData);
    },
    push() {
      this.lastData = EMPTY;
      const src = map.getSource("planes");
      if (src) src.setData(EMPTY);
    }
  };

  /* ================= 7. SUN'IY YO'LDOSHLAR ================= */
  // Soddalashtirilgan orbita: Kepler harakati + Yerning yassiligi (J2) ta'siri.
  // CelesTrak ma'lumoti har 6 soatda yangilanadi, shuning uchun aniqlik ko'rsatish uchun yetarli.
  const MU = 398600.4418, RE = 6378.137, J2 = 1.08262668e-3, D2R = Math.PI / 180;
  const Sats = {
    on: false, list: [], loaded: false, loading: false, timer: 0, lastData: null, orbitData: null, markers: {},
    set(on) {
      this.on = on;
      clearInterval(this.timer);
      if (!on) {
        this.lastData = EMPTY; this.orbitData = EMPTY;
        const s = map.getSource("sats"); if (s) s.setData(EMPTY);
        const o = map.getSource("orbit"); if (o) o.setData(EMPTY);
        Object.values(this.markers).forEach((m) => m.remove());
        this.markers = {};
        return;
      }
      this.load().then(() => {
        if (!this.on) return;
        this.update();
        this.timer = setInterval(() => this.update(), SETTINGS.satsRefreshMs);
      });
    },
    async load() {
      if (this.loaded || this.loading) return;
      this.loading = true;
      try {
        const r = await fetch("/api/map/sats");
        const j = await r.json();
        if (!r.ok || !j.sats) throw new Error("sats");
        this.list = j.sats.map(prep).filter(Boolean);
        this.loaded = true;
        document.querySelectorAll(".sat-count").forEach((el) => { el.textContent = fmt(L.satsCount, { n: this.list.length }); });
      } catch (e) {
        toast(L.satsErr);
      }
      this.loading = false;
    },
    update() {
      if (!this.on || !this.list.length) return;
      const now = Date.now(), gm = gmst(now), feats = [];
      for (const s of this.list) {
        const p = propagate(s, now, gm);
        if (p) feats.push({ type: "Feature", geometry: { type: "Point", coordinates: [p[0], p[1]] }, properties: { g: s.g } });
        if (s.label && p) this.marker(s, p);
      }
      this.lastData = { type: "FeatureCollection", features: feats };
      const src = map.getSource("sats");
      if (src) src.setData(this.lastData);
      // XKS orbitasi (keyingi 92 daqiqa) — har 30 soniyada qayta chiziladi
      const iss = this.list.find((s) => s.iss);
      if (iss && (!this.orbitAt || now - this.orbitAt > 30000)) {
        this.orbitAt = now;
        this.orbitData = orbitLine(iss, now);
        const o = map.getSource("orbit");
        if (o) o.setData(this.orbitData);
      }
    },
    marker(s, p) {
      let m = this.markers[s.label];
      if (!m) {
        const el = document.createElement("div");
        el.className = "sat-label";
        el.innerHTML = "<b>🛰️</b> " + esc(s.label);
        m = new maplibregl.Marker({ element: el, anchor: "left" }).setLngLat([p[0], p[1]]).addTo(map);
        this.markers[s.label] = m;
      } else {
        m.setLngLat([p[0], p[1]]);
      }
    }
  };

  function prep(o) {
    const mm = +o.mm, e = +o.e;
    if (!mm || !(e >= 0 && e < 1)) return null;
    const n0 = mm * 2 * Math.PI / 86400;               // rad/s
    const a = Math.cbrt(MU / (n0 * n0));
    const inc = o.i * D2R, p = a * (1 - e * e);
    const k = 1.5 * J2 * (RE / p) * (RE / p) * n0;
    const sinI = Math.sin(inc);
    const name = o.n || "";
    let label = null, iss = false;
    if (/ISS \(ZARYA\)/.test(name)) { label = "ISS"; iss = true; }
    else if (/CSS \(TIANHE\)/.test(name)) { label = "Tiangong 天宫"; }
    return {
      g: o.g, a, e, inc,
      raan0: o.ra * D2R, argp0: o.ap * D2R, m0: o.ma * D2R,
      ep: Date.parse(o.ep.endsWith("Z") ? o.ep : o.ep + "Z"),
      raanDot: -k * Math.cos(inc),
      argpDot: k * (2 - 2.5 * sinI * sinI),
      mDot: n0 + k * Math.sqrt(1 - e * e) * (1 - 1.5 * sinI * sinI),
      label, iss
    };
  }
  function gmst(ms) {
    const jd = ms / 86400000 + 2440587.5;
    let g = (280.46061837 + 360.98564736629 * (jd - 2451545.0)) % 360;
    if (g < 0) g += 360;
    return g * D2R;
  }
  // Natija: [uzunlik, kenglik, balandlik_km]
  function propagate(s, ms, gm) {
    const dt = (ms - s.ep) / 1000;
    if (!isFinite(dt)) return null;
    const M = s.m0 + s.mDot * dt, O = s.raan0 + s.raanDot * dt, w = s.argp0 + s.argpDot * dt, e = s.e;
    let E = M;
    for (let k = 0; k < 6; k++) E -= (E - e * Math.sin(E) - M) / (1 - e * Math.cos(E));
    const nu = 2 * Math.atan2(Math.sqrt(1 + e) * Math.sin(E / 2), Math.sqrt(1 - e) * Math.cos(E / 2));
    const r = s.a * (1 - e * Math.cos(E)), u = w + nu;
    const cO = Math.cos(O), sO = Math.sin(O), cu = Math.cos(u), su = Math.sin(u), ci = Math.cos(s.inc), si = Math.sin(s.inc);
    const x = r * (cO * cu - sO * su * ci), y = r * (sO * cu + cO * su * ci), z = r * (su * si);
    let lon = (Math.atan2(y, x) - gm) / D2R;
    lon = ((lon + 540) % 360) - 180;
    const lat = Math.atan2(z, Math.sqrt(x * x + y * y)) / D2R;
    return [lon, lat, r - RE];
  }
  function orbitLine(s, ms) {
    const lines = [];
    let cur = [], prev = null;
    for (let m = 0; m <= 92; m += 1) {
      const t = ms + m * 60000, p = propagate(s, t, gmst(t));
      if (!p) continue;
      if (prev && Math.abs(p[0] - prev[0]) > 180) { if (cur.length > 1) lines.push(cur); cur = []; }
      cur.push([p[0], p[1]]);
      prev = p;
    }
    if (cur.length > 1) lines.push(cur);
    return { type: "FeatureCollection", features: [{ type: "Feature", geometry: { type: "MultiLineString", coordinates: lines }, properties: {} }] };
  }

  /* ================= 8. ERKIN XARITA ================= */
  const searchIn = $("search-input"), resultsEl = $("search-results");
  searchIn.placeholder = L.search;
  document.querySelectorAll("[data-t]").forEach((el) => { el.textContent = L[el.dataset.t] || ""; });
  $("style-lbl").textContent = L.styleMap;

  let searchTimer = 0, searchSeq = 0;
  async function doSearch(q) {
    q = q.trim();
    if (q.length < 2) { resultsEl.style.display = "none"; return; }
    const my = ++searchSeq;
    try {
      const r = await fetch("/api/map/search?q=" + encodeURIComponent(q) + "&lang=" + LANG);
      const j = await r.json();
      if (my !== searchSeq) return;
      const res = j.results || [];
      if (!res.length) { resultsEl.innerHTML = '<button type="button" disabled>' + esc(L.notFound) + "</button>"; }
      else {
        resultsEl.innerHTML = res.map((x, k) =>
          '<button type="button" data-k="' + k + '">' + esc(x.name) + "<small>" + esc(x.display) + "</small></button>").join("");
        resultsEl.querySelectorAll("button[data-k]").forEach((b) => {
          b.addEventListener("click", () => {
            const x = res[+b.dataset.k];
            resultsEl.style.display = "none";
            searchIn.blur();
            if (x.bbox) {
              map.fitBounds([[x.bbox[2], x.bbox[0]], [x.bbox[3], x.bbox[1]]], { padding: 80, pitch: 55, maxZoom: 16, duration: 3500 });
            } else {
              map.flyTo({ center: [x.lon, x.lat], zoom: 13, pitch: 55, duration: 3500, essential: true });
            }
          });
        });
      }
      resultsEl.style.display = "block";
    } catch (e) {
      resultsEl.style.display = "none";
    }
  }
  searchIn.addEventListener("input", () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => doSearch(searchIn.value), 450); });
  searchIn.addEventListener("keydown", (e) => { if (e.key === "Enter") { clearTimeout(searchTimer); doSearch(searchIn.value); } });
  document.addEventListener("click", (e) => { if (!e.target.closest(".mp-search")) resultsEl.style.display = "none"; });

  let meMarker = null;
  $("locate-btn").addEventListener("click", () => {
    if (!navigator.geolocation) { toast(L.noLoc); return; }
    navigator.geolocation.getCurrentPosition((pos) => {
      const ll = [pos.coords.longitude, pos.coords.latitude];
      if (!meMarker) {
        const el = document.createElement("div");
        el.className = "me-dot";
        meMarker = new maplibregl.Marker({ element: el }).setLngLat(ll).addTo(map);
      } else meMarker.setLngLat(ll);
      map.flyTo({ center: ll, zoom: 15, pitch: 55, duration: 4000, essential: true });
    }, () => toast(L.noLoc), { enableHighAccuracy: true, timeout: 10000 });
  });

  let planesBtnOn = false, satsBtnOn = false;
  const planesBtn = $("planes-btn"), satsBtn = $("sats-btn");
  planesBtn.addEventListener("click", () => {
    planesBtnOn = !planesBtnOn;
    planesBtn.classList.toggle("on", planesBtnOn);
    Planes.set(planesBtnOn, null);
  });
  satsBtn.addEventListener("click", () => {
    satsBtnOn = !satsBtnOn;
    satsBtn.classList.toggle("on", satsBtnOn);
    Sats.set(satsBtnOn);
    if (satsBtnOn && map.getZoom() > 4) map.flyTo({ zoom: 1.8, pitch: 0, duration: 3000 });
  });
  // Erkin rejimda xarita siljisa, samolyotlar yangi hudud uchun yuklanadi
  let moveTimer = 0;
  map.on("moveend", () => {
    if (mode !== "explore" || !Planes.on) return;
    clearTimeout(moveTimer);
    moveTimer = setTimeout(() => Planes.fetch(), 800);
  });

  $("style-btn").addEventListener("click", () => {
    styleKind = styleKind === "sat" ? "map" : "sat";
    $("style-lbl").textContent = styleKind === "sat" ? L.styleMap : L.styleSat;
    map.setStyle(styleKind === "sat" ? satelliteStyle() : vectorStyleUrl(), { diff: false });
  });
  $("tilt-btn").addEventListener("click", () => {
    map.easeTo({ pitch: map.getPitch() > 20 ? 0 : 60, duration: 1200 });
  });

  /* ================= 9. YULDUZLI OSMON VA SIKL ================= */
  const stars = $("stars"), sctx = stars.getContext("2d");
  function drawStars() {
    const d = Math.min(window.devicePixelRatio || 1, 1.5);
    stars.width = stars.clientWidth * d;
    stars.height = stars.clientHeight * d;
    const W = stars.width, H = stars.height;
    const g = sctx.createRadialGradient(W * 0.5, H * 0.45, 0, W * 0.5, H * 0.5, Math.max(W, H) * 0.75);
    g.addColorStop(0, "#08142c"); g.addColorStop(1, "#01030a");
    sctx.fillStyle = g;
    sctx.fillRect(0, 0, W, H);
    const n = Math.round(W * H / 2600);
    for (let k = 0; k < n; k++) {
      const r = Math.random() < 0.94 ? Math.random() * 0.9 * d : (1 + Math.random()) * d;
      sctx.globalAlpha = 0.25 + Math.random() * 0.75;
      sctx.fillStyle = Math.random() < 0.15 ? "#c7d2fe" : Math.random() < 0.1 ? "#fde68a" : "#ffffff";
      sctx.beginPath();
      sctx.arc(Math.random() * W, Math.random() * H, r, 0, Math.PI * 2);
      sctx.fill();
    }
    sctx.globalAlpha = 1;
  }
  drawStars();
  window.addEventListener("resize", drawStars);

  let last = performance.now(), planeAcc = 0;
  function loop(now) {
    const dt = Math.min(0.1, (now - last) / 1000);
    last = now;
    planeAcc += dt;
    if (planeAcc > 0.12) { planeAcc = 0; Planes.tick(); }
    // Bekatda turganda kamera sekin aylanadi; kirish va kosmosda Yer shari aylanadi
    if (mode === "tour" && !REDUCED && !userInteracting && !map.isMoving() && !document.hidden) {
      const globeView = activeIdx < 0 || activeIdx >= TOUR.length || (TOUR[activeIdx] && TOUR[activeIdx].space);
      if (globeView) {
        const c = map.getCenter();
        map.jumpTo({ center: [c.lng + dt * 3, c.lat] });
      } else if (SETTINGS.idleRotate) {
        map.jumpTo({ bearing: map.getBearing() + dt * 2.2 });
      }
    }
    requestAnimationFrame(loop);
  }

  map.on("load", () => {
    hud("GLOBAL VIEW");
    if (CFG.startMode === "explore") setMode("explore");
    else activate(-1);
    requestAnimationFrame(loop);
  });
  $("mode-lbl").textContent = L.explore;
})();
