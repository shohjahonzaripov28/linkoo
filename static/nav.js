/* =====================================================================
   LINKO NAV — GPS navigator (Map ichida)
   - Marshrut: OpenRouteService (server orqali, kalit serverda) — mashina, piyoda, velosiped
   - Svetaforlar: OpenStreetMap (highway/crossing = traffic_signals), marshrut bo'ylab
   - Harakat paytida: keyingi burilish, masofa, yetib borish vaqti, ovozli ko'rsatma,
     svetafor ogohlantirishi, yo'ldan chiqilsa qayta hisoblash, ekran o'chmasligi
   map.js xarita yaratilgach LinkoNav.attach(map, ctx) ni chaqiradi.
   ===================================================================== */
(function () {
  "use strict";

  const NT = {
    uz: {
      route: "Yo'nalish", from: "Qayerdan", to: "Qayerga", myLoc: "Mening joylashuvim", pick: "Xaritadan tanlash",
      car: "Mashina", foot: "Piyoda", bike: "Velosiped", find: "Yo'lni topish", start: "Boshlash", stop: "Tugatish", close: "Yopish",
      searchPh: "Manzil yoki joy nomi", signals: "svetafor", signalsLoading: "svetaforlar…", eta: "yetib borish",
      noLoc: "Joylashuvni aniqlab bo'lmadi. GPS va brauzer ruxsatini yoqing.", noKey: "Navigatsiya hali sozlanmagan: serverda ORS kaliti yo'q.",
      noRoute: "Bu joylar orasida yo'l topilmadi.", tooLong: "Masofa juda uzoq.", busy: "Server band, birozdan keyin urinib ko'ring.",
      err: "Marshrutni olib bo'lmadi. Internetni tekshiring.", same: "Boshlanish va manzil bir xil.", needTo: "Qayerga borishni tanlang.",
      arrive: "Manzilga yetib keldingiz", reroute: "Yo'l qayta hisoblanmoqda", pickHint: "Xaritada nuqtani bosing", recenter: "Markazga",
      sigAhead: "Oldinda svetafor", voice: "Ovoz", picked: "Xaritadagi nuqta", nothing: "Hech narsa topilmadi.",
      m: "m", km: "km", min: "daq", h: "soat", sayM: "metr", sayKm: "kilometr",
      man: ["Chapga buriling", "O'ngga buriling", "Keskin chapga buriling", "Keskin o'ngga buriling", "Biroz chapga buriling", "Biroz o'ngga buriling",
            "To'g'riga yuring", "Aylanma yo'lga kiring", "Aylanma yo'ldan chiqing", "Ortga qayriling", "Manzilga yetib kelasiz", "Yo'lga chiqing", "Chap tomonda qoling", "O'ng tomonda qoling"],
      exitN: (n) => n + "-chiqish", then: (d, p) => d + "dan keyin " + p.charAt(0).toLowerCase() + p.slice(1), now: (p) => "Hozir " + p.charAt(0).toLowerCase() + p.slice(1)
    },
    ru: {
      route: "Маршрут", from: "Откуда", to: "Куда", myLoc: "Моё местоположение", pick: "Выбрать на карте",
      car: "Авто", foot: "Пешком", bike: "Велосипед", find: "Найти маршрут", start: "Поехали", stop: "Завершить", close: "Закрыть",
      searchPh: "Адрес или место", signals: "светофоров", signalsLoading: "светофоры…", eta: "прибытие",
      noLoc: "Не удалось определить местоположение. Включите GPS и разрешение браузера.", noKey: "Навигация ещё не настроена: на сервере нет ключа ORS.",
      noRoute: "Маршрут между этими точками не найден.", tooLong: "Слишком большое расстояние.", busy: "Сервер занят, попробуйте чуть позже.",
      err: "Не удалось построить маршрут. Проверьте интернет.", same: "Начало и конец совпадают.", needTo: "Выберите, куда ехать.",
      arrive: "Вы прибыли", reroute: "Перестраиваем маршрут", pickHint: "Нажмите точку на карте", recenter: "Центрировать",
      sigAhead: "Впереди светофор", voice: "Голос", picked: "Точка на карте", nothing: "Ничего не найдено.",
      m: "м", km: "км", min: "мин", h: "ч", sayM: "метров", sayKm: "километров",
      man: ["Поверните налево", "Поверните направо", "Резко налево", "Резко направо", "Плавно налево", "Плавно направо",
            "Двигайтесь прямо", "Въезжайте на круг", "Съезжайте с круга", "Развернитесь", "Вы прибудете на место", "Начните движение", "Держитесь левее", "Держитесь правее"],
      exitN: (n) => n + "-й съезд", then: (d, p) => "Через " + d + " " + p.charAt(0).toLowerCase() + p.slice(1), now: (p) => "Сейчас " + p.charAt(0).toLowerCase() + p.slice(1)
    },
    en: {
      route: "Directions", from: "From", to: "To", myLoc: "My location", pick: "Pick on map",
      car: "Car", foot: "Walk", bike: "Bike", find: "Find route", start: "Start", stop: "End", close: "Close",
      searchPh: "Address or place", signals: "traffic lights", signalsLoading: "traffic lights…", eta: "arrival",
      noLoc: "Couldn't get your location. Turn on GPS and allow it in the browser.", noKey: "Navigation isn't set up yet: the server has no ORS key.",
      noRoute: "No route found between these points.", tooLong: "That distance is too long.", busy: "The server is busy. Try again in a moment.",
      err: "Couldn't get a route. Check your internet.", same: "Start and destination are the same.", needTo: "Choose where to go.",
      arrive: "You have arrived", reroute: "Rerouting", pickHint: "Tap a point on the map", recenter: "Recenter",
      sigAhead: "Traffic light ahead", voice: "Voice", picked: "Point on map", nothing: "Nothing found.",
      m: "m", km: "km", min: "min", h: "h", sayM: "meters", sayKm: "kilometers",
      man: ["Turn left", "Turn right", "Turn sharp left", "Turn sharp right", "Bear left", "Bear right",
            "Continue straight", "Enter the roundabout", "Exit the roundabout", "Make a U-turn", "You will arrive at your destination", "Head out", "Keep left", "Keep right"],
      exitN: (n) => "exit " + n, then: (d, p) => "In " + d + ", " + p.charAt(0).toLowerCase() + p.slice(1), now: (p) => p
    },
    zh: {
      route: "路线", from: "起点", to: "终点", myLoc: "我的位置", pick: "在地图上选择",
      car: "驾车", foot: "步行", bike: "骑行", find: "查找路线", start: "开始导航", stop: "结束", close: "关闭",
      searchPh: "地址或地点", signals: "个红绿灯", signalsLoading: "红绿灯…", eta: "到达",
      noLoc: "无法获取位置，请打开 GPS 并允许浏览器定位。", noKey: "导航尚未配置：服务器没有 ORS 密钥。",
      noRoute: "这两点之间找不到路线。", tooLong: "距离太远。", busy: "服务器繁忙，请稍后再试。",
      err: "无法获取路线，请检查网络。", same: "起点和终点相同。", needTo: "请选择目的地。",
      arrive: "您已到达目的地", reroute: "正在重新规划路线", pickHint: "点击地图上的位置", recenter: "回到中心",
      sigAhead: "前方红绿灯", voice: "语音", picked: "地图上的点", nothing: "未找到结果。",
      m: "米", km: "公里", min: "分钟", h: "小时", sayM: "米", sayKm: "公里",
      man: ["左转", "右转", "向左急转", "向右急转", "稍向左转", "稍向右转", "直行", "进入环岛", "驶出环岛", "掉头", "即将到达目的地", "出发", "靠左行驶", "靠右行驶"],
      exitN: (n) => "第" + n + "出口", then: (d, p) => d + "后" + p, now: (p) => "现在" + p
    }
  };
  const SPEECH_LANG = { uz: "uz-UZ", ru: "ru-RU", en: "en-US", zh: "zh-CN" };
  const MODE_CFG = {
    car: { far: 400, near: 70, off: 45, sig: 160, zoom: 17, pitch: 55 },
    bike: { far: 160, near: 35, off: 35, sig: 80, zoom: 17.3, pitch: 45 },
    foot: { far: 60, near: 15, off: 30, sig: 40, zoom: 17.8, pitch: 35 }
  };

  /* ---------------- Yordamchi geometriya ---------------- */
  const R = 6371000, rad = (d) => d * Math.PI / 180, deg = (r) => r * 180 / Math.PI;
  function dist(a, b) {
    const p1 = rad(a[1]), p2 = rad(b[1]), dp = p2 - p1, dl = rad(b[0] - a[0]);
    const h = Math.sin(dp / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
  }
  function bearing(a, b) {
    const p1 = rad(a[1]), p2 = rad(b[1]), dl = rad(b[0] - a[0]);
    return (deg(Math.atan2(Math.sin(dl) * Math.cos(p2), Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl))) + 360) % 360;
  }
  // Nuqtani kesmaga proyeksiya: {d: masofa (m), t: 0..1}
  function projSeg(p, a, b) {
    const k = Math.cos(rad(p[1])) * 111320, ky = 110540;
    const ax = a[0] * k, ay = a[1] * ky, bx = b[0] * k, by = b[1] * ky, px = p[0] * k, py = p[1] * ky;
    const dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy;
    const t = L2 ? Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / L2)) : 0;
    return { d: Math.hypot(px - (ax + t * dx), py - (ay + t * dy)), t };
  }

  function arrowSvg(type) {
    const ang = { 0: -90, 1: 90, 2: -135, 3: 135, 4: -40, 5: 40, 6: 0, 11: 0, 12: -25, 13: 25 }[type];
    let inner;
    if (type === 9) inner = '<path d="M16 40V20a8 8 0 0 1 16 0v14"/><path d="M26 28l6 7 6-7"/>';
    else if (type === 7 || type === 8) inner = '<circle cx="24" cy="22" r="8"/><path d="M24 40V30M24 14V6M18 12l6-6 6 6"/>';
    else if (type === 10) inner = '<path d="M14 42V8"/><path d="M14 8h20l-5 7 5 7H14"/>';
    else inner = '<g transform="rotate(' + (ang || 0) + ' 24 26)"><path d="M24 42V12"/><path d="M14 22l10-10 10 10"/></g>';
    return '<svg viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="4" stroke-linecap="round" stroke-linejoin="round">' + inner + "</svg>";
  }

  function trafficLightImage() {
    const c = document.createElement("canvas"); c.width = 28; c.height = 56;
    const g = c.getContext("2d");
    g.fillStyle = "#111827"; g.strokeStyle = "#ffffff"; g.lineWidth = 2.5;
    const r = 7, x = 3, y = 3, w = 22, h = 50;
    g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath();
    g.fill(); g.stroke();
    [["#ef4444", 14], ["#f59e0b", 28], ["#22c55e", 42]].forEach(([col, cy]) => { g.fillStyle = col; g.beginPath(); g.arc(14, cy, 5.2, 0, Math.PI * 2); g.fill(); });
    return g.getImageData(0, 0, 28, 56);
  }

  const CSS = `
  .nv-panel{position:absolute;z-index:6;left:14px;top:calc(112px + env(safe-area-inset-top));width:min(380px,calc(100% - 28px));box-sizing:border-box;
    background:var(--mist);color:var(--ink);border:1px solid var(--line);border-radius:20px;padding:14px;box-shadow:0 16px 44px rgba(0,0,0,.3);font-size:14px}
  .nv-panel[hidden],.nv-hud[hidden],.nv-foot[hidden],.nv-sum[hidden],.nv-chip[hidden],.nv-res[hidden],.nv-recenter[hidden],.nv-pickhint[hidden]{display:none}
  .nv-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;font-weight:600;letter-spacing:.04em}
  .nv-x{background:none;border:none;color:var(--ink);font-size:22px;line-height:1;cursor:pointer;padding:2px 6px}
  .nv-modes{display:grid;grid-template-columns:repeat(3,1fr);gap:4px;background:rgba(127,127,127,.12);border-radius:12px;padding:4px;margin-bottom:10px}
  .nv-modes button{border:none;background:none;color:var(--ink2);border-radius:9px;padding:8px 4px;font:inherit;font-size:13px;font-weight:600;cursor:pointer}
  .nv-modes button.on{background:#3b82f6;color:#fff}
  .nv-field{position:relative;margin-bottom:8px}
  .nv-field label{display:block;font-size:11px;color:var(--ink2);margin:0 0 4px 4px;letter-spacing:.06em}
  .nv-field input{width:100%;box-sizing:border-box;height:42px;border-radius:12px;border:1px solid var(--line);background:var(--glass);color:var(--ink);padding:0 40px 0 12px;font:inherit;font-size:15px;outline:none}
  .nv-field input:focus{border-color:#3b82f6}
  .nv-pin{position:absolute;right:6px;bottom:6px;width:30px;height:30px;border:none;border-radius:9px;background:none;color:var(--ink2);cursor:pointer}
  .nv-pin svg{width:18px;height:18px}
  .nv-res{position:absolute;left:0;right:0;top:100%;z-index:3;margin-top:4px;background:var(--mist);border:1px solid var(--line);border-radius:14px;overflow:hidden;max-height:240px;overflow-y:auto;box-shadow:0 12px 30px rgba(0,0,0,.25)}
  .nv-res button{display:block;width:100%;text-align:left;background:none;border:none;border-bottom:1px solid var(--line);padding:10px 12px;color:var(--ink);font:inherit;font-size:14px;cursor:pointer}
  .nv-res button:last-child{border-bottom:none}
  .nv-res small{display:block;font-size:11.5px;color:var(--ink2);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .nv-go{width:100%;height:46px;border:none;border-radius:14px;background:#3b82f6;color:#fff;font:inherit;font-size:15px;font-weight:700;cursor:pointer;margin-top:4px}
  .nv-go:disabled{opacity:.6;cursor:default}
  .nv-sum{margin-top:12px;padding-top:12px;border-top:1px solid var(--line)}
  .nv-credit{margin-top:8px;font-size:10px;color:var(--ink2);text-align:center}
  .nv-big{font-size:24px;font-weight:700}
  .nv-sub{color:var(--ink2);font-size:13px;margin:2px 0 10px}
  .nv-hud{position:absolute;z-index:6;left:12px;right:12px;top:calc(60px + env(safe-area-inset-top));display:flex;gap:12px;align-items:center;background:#1d4ed8;color:#fff;border-radius:20px;padding:12px 14px;box-shadow:0 14px 40px rgba(0,0,0,.35);max-width:560px}
  .nv-arrow{flex:0 0 auto;width:52px;height:52px}
  .nv-hud b{display:block;font-size:26px;font-weight:700;line-height:1.1}
  .nv-hud span{display:block;font-size:14.5px;opacity:.92;margin-top:2px}
  .nv-foot{position:absolute;z-index:6;left:12px;right:12px;bottom:calc(14px + env(safe-area-inset-bottom));display:flex;gap:10px;align-items:center;background:var(--mist);color:var(--ink);border:1px solid var(--line);border-radius:20px;padding:10px 12px;box-shadow:0 12px 34px rgba(0,0,0,.3);max-width:560px}
  .nv-foot .nv-eta{flex:1;min-width:0}
  .nv-foot .nv-eta b{font-size:19px;font-weight:700;color:#22c55e}
  .nv-foot .nv-eta small{display:block;font-size:12.5px;color:var(--ink2)}
  .nv-fbtn{height:42px;min-width:42px;padding:0 12px;border-radius:12px;border:1px solid var(--line);background:var(--glass);color:var(--ink);font:inherit;font-size:13px;font-weight:600;cursor:pointer}
  .nv-fbtn.stop{background:#ef4444;border-color:#ef4444;color:#fff}
  .nv-chip{position:absolute;z-index:6;left:14px;top:calc(150px + env(safe-area-inset-top));display:flex;align-items:center;gap:8px;background:#111827;color:#fff;border-radius:999px;padding:7px 12px 7px 8px;font-size:13.5px;font-weight:700;box-shadow:0 8px 24px rgba(0,0,0,.35)}
  .nv-chip i{display:inline-flex;flex-direction:column;gap:2px;background:#000;border-radius:6px;padding:3px}
  .nv-chip i::before,.nv-chip i::after,.nv-chip i em{content:"";display:block;width:7px;height:7px;border-radius:50%}
  .nv-chip i::before{background:#ef4444}.nv-chip i em{background:#f59e0b}.nv-chip i::after{background:#22c55e}
  .nv-recenter{position:absolute;z-index:6;right:14px;bottom:calc(90px + env(safe-area-inset-bottom))}
  .nv-pickhint{position:absolute;z-index:6;left:50%;top:calc(120px + env(safe-area-inset-top));transform:translateX(-50%);background:#111827;color:#fff;border-radius:999px;padding:9px 16px;font-size:13px;pointer-events:none}
  .nv-me{width:30px;height:30px}
  .nv-me svg{width:30px;height:30px;filter:drop-shadow(0 2px 4px rgba(0,0,0,.4))}
  .nv-pt{width:16px;height:16px;border-radius:50%;border:3px solid #fff;box-shadow:0 2px 6px rgba(0,0,0,.4)}
  body.navigating #mapbar,body.navigating .lm-top{display:none}
  body.navigating .nv-chip{top:calc(150px + env(safe-area-inset-top))}
  @media (min-width:700px){.nv-hud,.nv-foot{left:auto;right:auto;margin:0 auto;width:min(560px,calc(100% - 24px));left:50%;transform:translateX(-50%)}}
  `;

  function h(tag, attrs, html) {
    const e = document.createElement(tag);
    if (attrs) Object.keys(attrs).forEach((k) => { if (k === "class") e.className = attrs[k]; else e.setAttribute(k, attrs[k]); });
    if (html != null) e.innerHTML = html;
    return e;
  }

  const LinkoNav = {
    attach(map, ctx) {
      if (this._attached) return;
      this._attached = true;
      const LANG = NT[ctx.lang] ? ctx.lang : "en";
      const T = NT[LANG];
      const toast = ctx.toast || ((m) => alert(m));
      const esc = ctx.esc || ((s) => String(s));
      const wrap = document.getElementById("mapwrap");
      const nf0 = new Intl.NumberFormat({ uz: "ru-RU", ru: "ru-RU", en: "en-US", zh: "zh-CN" }[LANG], { maximumFractionDigits: 1 });

      const st = document.createElement("style"); st.textContent = CSS; document.head.appendChild(st);

      /* ---------- Tugma (xarita panelida) ---------- */
      const btn = h("button", { type: "button", class: "lm-btn", id: "nav-btn" },
        '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 11l18-8-8 18-2-8-8-2z"/></svg><span class="lbl">' + esc(T.route) + "</span>");
      const btnBox = document.querySelector(".lm-mapbtns");
      btnBox.insertBefore(btn, btnBox.firstChild);

      /* ---------- Panel ---------- */
      const pinSvg = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M12 21s-7-6.2-7-11a7 7 0 0 1 14 0c0 4.8-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg>';
      const panel = h("div", { class: "nv-panel", hidden: "" },
        '<div class="nv-head"><span>' + esc(T.route) + '</span><button type="button" class="nv-x" aria-label="' + esc(T.close) + '">×</button></div>' +
        '<div class="nv-modes"><button type="button" data-m="car" class="on">' + esc(T.car) + '</button><button type="button" data-m="foot">' + esc(T.foot) + '</button><button type="button" data-m="bike">' + esc(T.bike) + "</button></div>" +
        '<div class="nv-field" data-f="from"><label>' + esc(T.from) + '</label><input type="search" autocomplete="off" enterkeyhint="search" placeholder="' + esc(T.searchPh) + '"><button type="button" class="nv-pin" title="' + esc(T.pick) + '" aria-label="' + esc(T.pick) + '">' + pinSvg + '</button><div class="nv-res" hidden></div></div>' +
        '<div class="nv-field" data-f="to"><label>' + esc(T.to) + '</label><input type="search" autocomplete="off" enterkeyhint="search" placeholder="' + esc(T.searchPh) + '"><button type="button" class="nv-pin" title="' + esc(T.pick) + '" aria-label="' + esc(T.pick) + '">' + pinSvg + '</button><div class="nv-res" hidden></div></div>' +
        '<button type="button" class="nv-go" data-a="find">' + esc(T.find) + "</button>" +
        '<div class="nv-sum" hidden><div class="nv-big"></div><div class="nv-sub"></div><button type="button" class="nv-go" data-a="start">' + esc(T.start) + '</button><div class="nv-credit">© openrouteservice.org by HeiGIT · © OpenStreetMap</div></div>');
      wrap.appendChild(panel);
      const hud = h("div", { class: "nv-hud", hidden: "" }, '<div class="nv-arrow"></div><div><b></b><span></span></div>');
      const foot = h("div", { class: "nv-foot", hidden: "" },
        '<div class="nv-eta"><b></b><small></small></div><button type="button" class="nv-fbtn" data-a="voice"></button><button type="button" class="nv-fbtn stop" data-a="stop">' + esc(T.stop) + "</button>");
      const chip = h("div", { class: "nv-chip", hidden: "" }, "<i><em></em></i><span></span>");
      const recenter = h("button", { type: "button", class: "nv-fbtn nv-recenter", hidden: "" }, esc(T.recenter));
      const pickHint = h("div", { class: "nv-pickhint", hidden: "" }, esc(T.pickHint));
      wrap.append(hud, foot, chip, recenter, pickHint);

      /* ---------- Holat ---------- */
      let mode = "car";
      const pts = { from: { me: true, name: T.myLoc, ll: null }, to: null };
      let route = null;        // {coords, cum, steps, distance, duration}
      let signals = [];        // [{lat, lon, along}]
      let nav = null;          // navigatsiya holati
      let pickFor = null, watchId = null, wakeLock = null, follow = true;
      let markers = { from: null, to: null, me: null };
      const fromInput = panel.querySelector('[data-f="from"] input'), toInput = panel.querySelector('[data-f="to"] input');
      fromInput.value = T.myLoc;

      /* ---------- Ovoz ---------- */
      let voiceOn = true, voice = null, voiceLang = LANG;
      function pickVoice() {
        if (!("speechSynthesis" in window)) return;
        const vs = speechSynthesis.getVoices();
        const want = SPEECH_LANG[LANG].slice(0, 2);
        voice = vs.find((v) => v.lang && v.lang.toLowerCase().startsWith(want)) || null;
        voiceLang = LANG;
        if (!voice) {
          // O'zbek ovozi bo'lmasa: rus ovozi va ruscha ko'rsatma (aks holda ingliz)
          const fb = LANG === "uz" ? "ru" : "en";
          voice = vs.find((v) => v.lang && v.lang.toLowerCase().startsWith(fb)) || null;
          voiceLang = voice ? fb : LANG;
        }
        foot.querySelector('[data-a="voice"]').textContent = (voiceOn ? "🔊 " : "🔇 ") + voiceLang.toUpperCase();
      }
      if ("speechSynthesis" in window) { pickVoice(); speechSynthesis.onvoiceschanged = pickVoice; }
      function say(text) {
        if (!voiceOn || !voice || !("speechSynthesis" in window)) return;
        try {
          speechSynthesis.cancel();
          const u = new SpeechSynthesisUtterance(text);
          u.lang = voice.lang; u.rate = 1;
          try { u.voice = voice; } catch (e) { /* ovoz obyekti mos kelmasa, til bo'yicha tanlanadi */ }
          speechSynthesis.speak(u);
        } catch (e) { /* */ }
      }
      foot.querySelector('[data-a="voice"]').addEventListener("click", () => { voiceOn = !voiceOn; if (!voiceOn && "speechSynthesis" in window) speechSynthesis.cancel(); pickVoice(); });

      /* ---------- Formatlash ---------- */
      function fmtDist(m, L) {
        L = L || T;
        if (m >= 1000) return nf0.format(Math.round(m / 100) / 10) + " " + L.km;
        const r = m > 300 ? 50 : m > 100 ? 10 : 5;
        return Math.max(r, Math.round(m / r) * r) + " " + L.m;
      }
      function sayDist(m, L) {
        if (m >= 1000) return (Math.round(m / 100) / 10).toString().replace(".", L === NT.ru || L === NT.uz ? "," : ".") + " " + L.sayKm;
        const r = m > 300 ? 50 : 10;
        return Math.max(r, Math.round(m / r) * r) + " " + L.sayM;
      }
      function fmtDur(s) {
        const mins = Math.max(1, Math.round(s / 60));
        if (mins < 60) return mins + " " + T.min;
        return Math.floor(mins / 60) + " " + T.h + " " + (mins % 60) + " " + T.min;
      }
      function clock(sec) { const d = new Date(Date.now() + sec * 1000); return d.toLocaleTimeString({ uz: "ru-RU", ru: "ru-RU", en: "en-GB", zh: "zh-CN" }[LANG], { hour: "2-digit", minute: "2-digit" }); }
      function phrase(step, L) {
        L = L || T;
        let p = L.man[step.type] || L.man[6];
        if (step.type === 7 && step.exit) p += ", " + L.exitN(step.exit);
        return p;
      }

      /* ---------- Xarita qatlamlari ---------- */
      const EMPTY = { type: "FeatureCollection", features: [] };
      // Uslub hali yuklanayotgan bo'lsa (masalan, kamera harakatlanayotganda), xarita bo'shagach qayta chiziladi
      let retryQueued = false;
      function retryLater() {
        if (retryQueued) return;
        retryQueued = true;
        map.once("idle", () => { retryQueued = false; if (route) { drawRoute(nav ? nav.idx : null); drawSignals(); } });
      }
      function ensureLayers() {
        try {
          if (!map.hasImage("nv-tl")) map.addImage("nv-tl", trafficLightImage(), { pixelRatio: 2 });
          if (!map.getSource("nv-route")) map.addSource("nv-route", { type: "geojson", data: EMPTY });
          if (!map.getSource("nv-sig")) map.addSource("nv-sig", { type: "geojson", data: EMPTY });
          if (!map.getLayer("nv-route-case")) map.addLayer({ id: "nv-route-case", type: "line", source: "nv-route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#1e3a8a", "line-width": ["interpolate", ["linear"], ["zoom"], 5, 5, 16, 13] } });
          if (!map.getLayer("nv-route")) map.addLayer({ id: "nv-route", type: "line", source: "nv-route", layout: { "line-join": "round", "line-cap": "round" }, paint: { "line-color": "#3b82f6", "line-width": ["interpolate", ["linear"], ["zoom"], 5, 3, 16, 8] } });
          if (!map.getLayer("nv-sig")) map.addLayer({ id: "nv-sig", type: "symbol", source: "nv-sig", minzoom: 11, layout: { "icon-image": "nv-tl", "icon-size": ["interpolate", ["linear"], ["zoom"], 11, 0.45, 17, 0.95], "icon-allow-overlap": true, "icon-anchor": "bottom" } });
        } catch (e) { retryLater(); return false; }
        return true;
      }
      function drawRoute(fromIdx) {
        if (!ensureLayers() || !route) return;
        let coords = route.coords;
        if (fromIdx != null && nav) coords = [nav.snap].concat(route.coords.slice(fromIdx + 1));
        map.getSource("nv-route").setData({ type: "Feature", geometry: { type: "LineString", coordinates: coords.length > 1 ? coords : route.coords } });
      }
      function drawSignals() {
        if (!ensureLayers()) return;
        map.getSource("nv-sig").setData({ type: "FeatureCollection", features: signals.map((s) => ({ type: "Feature", geometry: { type: "Point", coordinates: [s.lon, s.lat] } })) });
      }
      function clearLayers() {
        try { if (map.getSource("nv-route")) map.getSource("nv-route").setData(EMPTY); if (map.getSource("nv-sig")) map.getSource("nv-sig").setData(EMPTY); } catch (e) { /* */ }
      }
      // Uslub almashsa (kun/tun, sun'iy yo'ldosh) qatlamlar qayta qo'shiladi
      map.on("style.load", () => { if (route) { drawRoute(nav ? nav.idx : null); drawSignals(); } });

      function setMarker(kind, ll, color) {
        if (markers[kind]) { markers[kind].remove(); markers[kind] = null; }
        if (!ll) return;
        const el = h("div", { class: "nv-pt" }); el.style.background = color;
        markers[kind] = new maplibregl.Marker({ element: el }).setLngLat(ll).addTo(map);
      }

      /* ---------- Joy qidirish ---------- */
      function bindField(kind, input) {
        const res = input.parentNode.querySelector(".nv-res");
        let tmr = 0, seq = 0;
        async function run(q) {
          q = q.trim();
          if (q.length < 2 || q === T.myLoc) { res.hidden = true; return; }
          const my = ++seq;
          try {
            const r = await fetch("/api/map/search?q=" + encodeURIComponent(q) + "&lang=" + LANG);
            const j = await r.json();
            if (my !== seq) return;
            const list = j.results || [];
            res.innerHTML = "";
            if (kind === "from") {
              const b = h("button", { type: "button" }, "📍 " + esc(T.myLoc));
              b.addEventListener("mousedown", (e) => { e.preventDefault(); pts.from = { me: true, name: T.myLoc, ll: null }; input.value = T.myLoc; res.hidden = true; setMarker("from", null); });
              res.appendChild(b);
            }
            if (!list.length) res.appendChild(h("button", { type: "button", disabled: "" }, esc(T.nothing)));
            list.forEach((x) => {
              const b = h("button", { type: "button" }, esc(x.name) + "<small>" + esc(x.display) + "</small>");
              b.addEventListener("mousedown", (e) => { e.preventDefault(); choose(kind, x.name, [x.lon, x.lat]); res.hidden = true; });
              res.appendChild(b);
            });
            res.hidden = false;
          } catch (e) { res.hidden = true; }
        }
        input.addEventListener("input", () => { clearTimeout(tmr); tmr = setTimeout(() => run(input.value), 450); });
        input.addEventListener("keydown", (e) => { if (e.key === "Enter") { clearTimeout(tmr); run(input.value); } });
        input.addEventListener("focus", () => { if (kind === "from" && input.value === T.myLoc) input.select(); });
        input.addEventListener("blur", () => setTimeout(() => { res.hidden = true; }, 150));
        input.parentNode.querySelector(".nv-pin").addEventListener("click", () => {
          pickFor = kind; pickHint.hidden = false; panel.hidden = true;
        });
      }
      function choose(kind, name, ll) {
        if (kind === "from") { pts.from = { me: false, name, ll }; fromInput.value = name; setMarker("from", ll, "#22c55e"); }
        else { pts.to = { name, ll }; toInput.value = name; setMarker("to", ll, "#ef4444"); }
        resetRoute();
      }
      bindField("from", fromInput);
      bindField("to", toInput);
      map.on("click", (e) => {
        if (!pickFor) return;
        const ll = [e.lngLat.lng, e.lngLat.lat];
        choose(pickFor, T.picked + " (" + ll[1].toFixed(4) + ", " + ll[0].toFixed(4) + ")", ll);
        pickFor = null; pickHint.hidden = true; panel.hidden = false;
      });

      /* ---------- Panel boshqaruvi ---------- */
      function openPanel() { panel.hidden = false; btn.classList.add("on"); }
      function closePanel() { panel.hidden = true; btn.classList.remove("on"); if (!nav) { resetRoute(); setMarker("from", null); setMarker("to", null); } }
      btn.addEventListener("click", () => (panel.hidden ? openPanel() : closePanel()));
      panel.querySelector(".nv-x").addEventListener("click", closePanel);
      panel.querySelectorAll(".nv-modes button").forEach((b) => b.addEventListener("click", () => {
        mode = b.dataset.m;
        panel.querySelectorAll(".nv-modes button").forEach((x) => x.classList.toggle("on", x === b));
        resetRoute();
      }));
      function resetRoute() {
        route = null; signals = [];
        panel.querySelector(".nv-sum").hidden = true;
        panel.querySelector('[data-a="find"]').hidden = false;
        clearLayers();
      }

      function myPosition() {
        return new Promise((ok, no) => {
          if (!navigator.geolocation) return no(new Error("nogeo"));
          navigator.geolocation.getCurrentPosition((p) => ok([p.coords.longitude, p.coords.latitude]), no, { enableHighAccuracy: true, timeout: 15000, maximumAge: 5000 });
        });
      }

      async function fetchRoute(from, to) {
        const r = await fetch("/api/nav/route", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ mode, coords: [from, to] }) });
        const j = await r.json().catch(() => ({}));
        if (!r.ok || !j.ok) {
          const msg = { nokey: T.noKey, noroute: T.noRoute, toolong: T.tooLong, busy: T.busy, rate: T.busy, same: T.same }[j.error] || T.err;
          throw new Error(msg);
        }
        const cum = [0];
        for (let i = 1; i < j.coords.length; i++) cum.push(cum[i - 1] + dist(j.coords[i - 1], j.coords[i]));
        return { coords: j.coords, cum, steps: j.steps, distance: j.distance || cum[cum.length - 1], duration: j.duration };
      }

      async function fetchSignals() {
        signals = [];
        const sub = panel.querySelector(".nv-sub");
        try {
          // Ko'p nuqtali yo'lni siqamiz: oldingi saqlangan nuqtadan kamida 10 m uzoqdagilar
          const line = [route.coords[0]];
          let lastCum = 0;
          for (let i = 1; i < route.coords.length; i++) {
            if (route.cum[i] - lastCum >= 10 || i === route.coords.length - 1) { line.push(route.coords[i]); lastCum = route.cum[i]; }
          }
          const r = await fetch("/api/nav/signals", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ coords: line.slice(0, 6000) }) });
          const j = await r.json();
          signals = j.signals || [];
        } catch (e) { signals = []; }
        drawSignals();
        updateSummary();
        if (nav) nav.sigIdx = 0;
        return signals;
      }

      function updateSummary() {
        if (!route) return;
        panel.querySelector(".nv-big").textContent = fmtDur(route.duration) + " · " + fmtDist(route.distance);
        const sig = route.sigLoading ? T.signalsLoading : (signals.length + " " + T.signals);
        panel.querySelector(".nv-sub").textContent = T.eta + " " + clock(route.duration) + " · 🚦 " + sig;
      }

      const findBtn = panel.querySelector('[data-a="find"]');
      findBtn.addEventListener("click", async () => {
        if (!pts.to) { toast(T.needTo); toInput.focus(); return; }
        findBtn.disabled = true;
        try {
          let from = pts.from.ll;
          if (pts.from.me) { try { from = await myPosition(); } catch (e) { throw new Error(T.noLoc); } setMarker("from", from, "#22c55e"); }
          route = await fetchRoute(from, pts.to.ll);
          route.sigLoading = true;
          drawRoute();
          const b = route.coords.reduce((bb, c) => [[Math.min(bb[0][0], c[0]), Math.min(bb[0][1], c[1])], [Math.max(bb[1][0], c[0]), Math.max(bb[1][1], c[1])]], [[180, 90], [-180, -90]]);
          map.fitBounds(b, { padding: { top: 140, bottom: 60, left: innerWidth > 700 ? 420 : 40, right: 40 }, maxZoom: 16, duration: 1200 });
          findBtn.hidden = true;
          panel.querySelector(".nv-sum").hidden = false;
          updateSummary();
          fetchSignals().then(() => { route.sigLoading = false; updateSummary(); });
        } catch (e) { toast(e.message || T.err); }
        findBtn.disabled = false;
      });

      /* ================= NAVIGATSIYA ================= */
      panel.querySelector('[data-a="start"]').addEventListener("click", startNav);
      foot.querySelector('[data-a="stop"]').addEventListener("click", () => stopNav(false));
      recenter.addEventListener("click", () => { follow = true; recenter.hidden = true; if (nav && nav.pos) moveCamera(nav.pos, nav.heading, true); });
      map.on("dragstart", () => { if (nav) { follow = false; recenter.hidden = false; } });

      async function keepAwake() {
        try { if ("wakeLock" in navigator) wakeLock = await navigator.wakeLock.request("screen"); } catch (e) { wakeLock = null; }
      }
      document.addEventListener("visibilitychange", () => { if (nav && document.visibilityState === "visible") keepAwake(); });

      function startNav() {
        if (!route) return;
        if (!navigator.geolocation) { toast(T.noLoc); return; }
        nav = { idx: 0, snap: route.coords[0], pos: null, heading: 0, stepIdx: 0, said: {}, off: 0, lastReroute: 0, sigIdx: 0, sigSaid: new Set(), arrived: false };
        follow = true;
        panel.hidden = true; btn.classList.remove("on");
        hud.hidden = false; foot.hidden = false;
        document.body.classList.add("navigating");
        pickVoice();
        keepAwake();
        const meEl = h("div", { class: "nv-me" }, '<svg viewBox="0 0 30 30"><circle cx="15" cy="15" r="13" fill="#fff"/><path d="M15 4l7 19-7-4-7 4z" fill="#2563eb"/></svg>');
        if (markers.me) markers.me.remove();
        markers.me = new maplibregl.Marker({ element: meEl, rotationAlignment: "map", pitchAlignment: "map" }).setLngLat(route.coords[0]).addTo(map);
        updateHud(route.coords[0], 0);
        say((NT[voiceLang] || T).man[11]);
        nav.lastFix = Date.now(); nav.warned = false;
        watchId = navigator.geolocation.watchPosition(onFix, (err) => {
          // Ruxsat berilmagan bo'lsa - darhol; vaqtinchalik xatolarda faqat 25 soniya signal bo'lmasa, bir marta
          if (!nav) return;
          if (err && err.code === 1) { toast(T.noLoc); stopNav(false); return; }
          if (!nav.warned && Date.now() - nav.lastFix > 25000) { nav.warned = true; toast(T.noLoc); }
        }, { enableHighAccuracy: true, maximumAge: 1000, timeout: 30000 });
      }

      function stopNav(arrived) {
        if (watchId != null) navigator.geolocation.clearWatch(watchId);
        watchId = null; nav = null;
        try { if (wakeLock) wakeLock.release(); } catch (e) { /* */ }
        wakeLock = null;
        if ("speechSynthesis" in window) speechSynthesis.cancel();
        hud.hidden = true; foot.hidden = true; chip.hidden = true; recenter.hidden = true;
        document.body.classList.remove("navigating");
        if (markers.me) { markers.me.remove(); markers.me = null; }
        map.easeTo({ pitch: 0, bearing: 0, duration: 800 });
        if (arrived) { resetRoute(); setMarker("from", null); setMarker("to", null); }
        else { drawRoute(); openPanel(); }
      }

      function moveCamera(pos, heading, force) {
        if (!follow && !force) return;
        const cfg = MODE_CFG[mode];
        map.easeTo({ center: pos, bearing: heading, pitch: cfg.pitch, zoom: cfg.zoom, duration: force ? 600 : 900, essential: true,
          padding: { top: innerHeight * 0.35, bottom: 60, left: 0, right: 0 } });
      }

      function locate(pos) {
        // Avvalgi joy atrofidan qidiramiz, topilmasa butun yo'l bo'ylab
        const c = route.coords;
        let best = { d: Infinity, i: 0, t: 0 };
        const scan = (a, b) => { for (let i = Math.max(0, a); i < Math.min(c.length - 1, b); i++) { const p = projSeg(pos, c[i], c[i + 1]); if (p.d < best.d) best = { d: p.d, i, t: p.t }; } };
        scan(nav.idx - 3, nav.idx + 80);
        if (best.d > 60) scan(0, c.length - 1);
        const along = route.cum[best.i] + best.t * (route.cum[best.i + 1] - route.cum[best.i]);
        const a = c[best.i], b = c[best.i + 1];
        const snap = [a[0] + (b[0] - a[0]) * best.t, a[1] + (b[1] - a[1]) * best.t];
        return { off: best.d, idx: best.i, along, snap, segBearing: bearing(a, b) };
      }

      async function reroute(pos) {
        if (Date.now() - nav.lastReroute < 12000) return;
        nav.lastReroute = Date.now();
        toast(T.reroute); say((NT[voiceLang] || T).reroute);
        try {
          route = await fetchRoute(pos, pts.to.ll);
          route.sigLoading = true;
          nav.idx = 0; nav.stepIdx = 0; nav.said = {}; nav.off = 0; nav.sigSaid = new Set();
          drawRoute(0);
          fetchSignals().then(() => { if (route) route.sigLoading = false; });
        } catch (e) { toast(e.message || T.err); }
      }

      function onFix(p) {
        if (!nav || !route) return;
        nav.lastFix = Date.now(); nav.warned = false;
        const pos = [p.coords.longitude, p.coords.latitude];
        const acc = p.coords.accuracy || 30, speed = p.coords.speed || 0;
        const loc = locate(pos);
        const cfg = MODE_CFG[mode];
        // Yo'ldan chiqish: 3 marta ketma-ket chegaradan uzoq (GPS aniqligi yaxshi bo'lsa)
        if (loc.off > cfg.off + Math.min(acc, 40)) { if (++nav.off >= 3) { nav.off = 0; reroute(pos); } }
        else nav.off = 0;
        nav.idx = loc.idx; nav.snap = loc.snap; nav.pos = loc.off < cfg.off ? loc.snap : pos;
        const gpsHeading = p.coords.heading;
        nav.heading = (speed > 1.5 && gpsHeading != null && !isNaN(gpsHeading)) ? gpsHeading : loc.segBearing;
        markers.me.setLngLat(nav.pos).setRotation(nav.heading);
        moveCamera(nav.pos, nav.heading);
        drawRoute(loc.idx);
        updateHud(nav.pos, loc.along);
      }

      function updateHud(pos, along) {
        if (!route) return;
        const steps = route.steps;
        // Joriy qadam - biz hozir yurayotgan bo'lak; keyingi burilish - keyingi qadamning boshi
        let si = nav.stepIdx;
        while (si < steps.length - 1 && route.cum[Math.min(steps[si].to, route.cum.length - 1)] <= along + 3) si++;
        if (si !== nav.stepIdx) nav.stepIdx = si;
        const next = steps[si + 1] || steps[si];
        const turnAt = next ? route.cum[Math.min(next.from, route.cum.length - 1)] : route.distance;
        const toTurn = Math.max(0, turnAt - along);
        const remain = Math.max(0, route.distance - along);
        const remDur = route.duration * (route.distance ? remain / route.distance : 0);

        hud.querySelector(".nv-arrow").innerHTML = arrowSvg(next ? next.type : 6);
        hud.querySelector("b").textContent = fmtDist(toTurn);
        hud.querySelector("span").textContent = phrase(next || { type: 6 }) + (next && next.name ? " · " + next.name : "");
        foot.querySelector(".nv-eta b").textContent = fmtDur(remDur);
        foot.querySelector(".nv-eta small").textContent = fmtDist(remain) + " · " + T.eta + " " + clock(remDur);

        // Ovozli ko'rsatmalar (uzoqdan va yaqindan bittadan)
        const cfg = MODE_CFG[mode], key = route.steps.indexOf(next);
        const VL = NT[voiceLang] || T;
        if (next && toTurn <= cfg.far && toTurn > cfg.near * 1.6 && !nav.said["f" + key]) {
          nav.said["f" + key] = 1; say(VL.then(sayDist(toTurn, VL), phrase(next, VL)));
        } else if (next && toTurn <= cfg.near && !nav.said["n" + key]) {
          nav.said["n" + key] = 1; nav.said["f" + key] = 1;
          if (next.type !== 10) say(VL.now(phrase(next, VL)));
        }

        // Svetafor ogohlantirishi
        while (nav.sigIdx < signals.length && signals[nav.sigIdx].along < along - 5) nav.sigIdx++;
        const sg = signals[nav.sigIdx];
        if (sg && sg.along - along <= cfg.sig) {
          chip.hidden = false;
          chip.querySelector("span").textContent = fmtDist(Math.max(0, sg.along - along));
          // bir chorrahadagi bir nechta svetafor - bitta ogohlantirish
          const cluster = Math.round(sg.along / 40);
          if (!nav.sigSaid.has(cluster) && mode !== "foot") { nav.sigSaid.add(cluster); if (toTurn > cfg.near * 2) say(VL.sigAhead); }
        } else chip.hidden = true;

        // Yetib kelish
        if (!nav.arrived && remain < 25) {
          nav.arrived = true;
          hud.querySelector(".nv-arrow").innerHTML = arrowSvg(10);
          hud.querySelector("b").textContent = T.arrive;
          hud.querySelector("span").textContent = pts.to ? pts.to.name : "";
          say(VL.arrive);
          setTimeout(() => stopNav(true), 5000);
        }
      }

      // Tashqaridan: "shu joyga yo'l" (masalan, qidiruv natijasidan)
      LinkoNav.routeTo = (name, lon, lat) => { openPanel(); choose("to", name, [lon, lat]); };
      LinkoNav.isNavigating = () => !!nav;
      LinkoNav._test = { map, locate: (p) => locate(p), state: () => ({ nav, route, signals }), onFix: (p) => onFix(p) };
    }
  };
  window.LinkoNav = LinkoNav;
})();
