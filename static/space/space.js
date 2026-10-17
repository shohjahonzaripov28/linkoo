/* =====================================================================
   LINKO SPACE — Quyosh tizimi (Three.js)
   - Sayyoralar bugungi haqiqiy o'rnida boshlanadi (o'rtacha uzunlama, J2000)
   - Masshtab ixcham: hammasi bir ekranga sig'adi, kartada haqiqiy raqamlar
   - Bosilgan jismga kamera uchib boradi, uni aylantirib ko'rish mumkin
   - Yer -> xaritaga qaytish, Oy va Mars -> sirt xaritasi (map.js orqali)
   Teksturalar: Solar System Scope, CC BY 4.0 (CREDITS.txt)
   ===================================================================== */
import * as THREE from "three";
import { OrbitControls } from "./OrbitControls.js";

const BASE = "/static/space/";
const DAY_MS = 86400000;
const J2000 = Date.UTC(2000, 0, 1, 12);
const SIM_DAYS_PER_SEC = 6; // animatsiya tezligi: 1 soniya = 6 kun

/* ---------------- Jismlar (ixcham masshtab) ----------------
   r: radius, d: Quyoshdan masofa, P: aylanish davri (kun), L0/n: J2000 uzunlama va kunlik o'zgarish (grad)
   tilt: o'q og'ishi (grad), spin: o'z o'qi atrofida aylanish davri (soat, manfiy = teskari) */
const BODIES = [
  { id: "sun", r: 5, d: 0, tilt: 7.25, spin: 609, color: 0xffcc66 },
  { id: "mercury", r: 0.45, d: 10, P: 87.97, L0: 252.25, n: 4.09233, tilt: 0.03, spin: 1407.6, color: 0x9a948c },
  { id: "venus", r: 0.9, d: 14, P: 224.7, L0: 181.98, n: 1.60213, tilt: 177.4, spin: -5832.5, color: 0xd9b56a },
  { id: "earth", r: 1, d: 19, P: 365.256, L0: 100.46, n: 0.98561, tilt: 23.44, spin: 23.93, color: 0x3a6fb0 },
  { id: "mars", r: 0.6, d: 24, P: 686.98, L0: 355.45, n: 0.52403, tilt: 25.19, spin: 24.62, color: 0xb5562e },
  { id: "jupiter", r: 2.6, d: 34, P: 4332.6, L0: 34.40, n: 0.08309, tilt: 3.13, spin: 9.93, color: 0xc9a27a },
  { id: "saturn", r: 2.2, d: 46, P: 10759, L0: 49.94, n: 0.03346, tilt: 26.73, spin: 10.66, color: 0xd8c08a, ring: [2.75, 5.0] },
  { id: "uranus", r: 1.5, d: 57, P: 30689, L0: 313.23, n: 0.01173, tilt: 97.77, spin: -17.24, color: 0x9fd8e0 },
  { id: "neptune", r: 1.45, d: 66, P: 60190, L0: 304.88, n: 0.00598, tilt: 28.32, spin: 16.11, color: 0x3f62d8 },
];
const MOON = { id: "moon", r: 0.27, d: 2.2, P: 27.32, tilt: 6.7, spin: 655.7, color: 0xa9a9a9, parent: "earth" };

/* ---------------- Matnlar (4 til) ---------------- */
const T = {
  uz: {
    names: { sun: "Quyosh", mercury: "Merkuriy", venus: "Venera", earth: "Yer", moon: "Oy", mars: "Mars", jupiter: "Yupiter", saturn: "Saturn", uranus: "Uran", neptune: "Neptun" },
    kind: { sun: "Yulduz", planet: "Sayyora", moon: "Yerning yo'ldoshi" },
    diameter: "Diametri", dist: "Quyoshdan masofa", distMoon: "Yerdan masofa", day: "Bir sutka", year: "Bir yil", moons: "Yo'ldoshlari", temp: "Harorat", age: "Yoshi", spin: "O'z o'qi atrofida",
    km: "km", mkm: "mln km", h: "soat", min: "daq", days: "kun", years: "yil", byears: "mlrd yil", avg: "o'rtacha",
    toEarth: "Xaritaga kirish", surface: "Sirt xaritasi", overview: "Quyosh tizimi", backHome: "Yerga qaytish",
    tip: "Sayyorani bosing", load: "Koinot yuklanmoqda…", fail: "3D koinotni ochib bo'lmadi. Internet yoki brauzerni tekshiring.",
    pause: "To'xtatish", play: "Davom ettirish", credit: "Teksturalar: Solar System Scope (CC BY 4.0), NASA ma'lumotlari",
    desc: {
      sun: "Quyosh tizimining markazi: butun massaning 99,8% shu yerda. Uning nuri Yerga taxminan 8 daqiqa 20 soniyada yetib keladi.",
      mercury: "Quyoshga eng yaqin va eng kichik sayyora. Atmosferasi deyarli yo'q: kunduzi 430°C gacha qiziydi, kechasi −180°C gacha soviydi.",
      venus: "Eng issiq sayyora: qalin karbonat angidrid atmosferasi issiqlikni ushlab qoladi. Teskari aylanadi, u yerda Quyosh g'arbdan chiqadi.",
      earth: "Bizning uyimiz va hayot ma'lum bo'lgan yagona sayyora. Yuzasining 71% suv bilan qoplangan.",
      moon: "Yerning yagona tabiiy yo'ldoshi. Yerga doim bir tomoni bilan qaraydi. 1969-yilda inson birinchi marta shu yerga qadam qo'ygan.",
      mars: "Qizil sayyora: rangini temir oksidi beradi. Quyosh tizimidagi eng baland tog', Olimp (~22 km), shu yerda.",
      jupiter: "Eng katta sayyora: ichiga 1300 dan ortiq Yer sig'adi. Katta Qizil Dog' Yerdan ham kattaroq bo'ron.",
      saturn: "Muz va tosh bo'laklaridan iborat ajoyib halqalari bilan mashhur. O'rtacha zichligi suvnikidan ham kam.",
      uranus: "Yonboshlab aylanadigan muz giganti: o'qi 98° ga og'gan. Ko'kimtir rangini atmosferadagi metan beradi.",
      neptune: "Quyoshdan eng uzoq sayyora. Shamollari soatiga 2000 km dan oshadi, bu tizimdagi eng kuchli shamollar.",
    },
  },
  ru: {
    names: { sun: "Солнце", mercury: "Меркурий", venus: "Венера", earth: "Земля", moon: "Луна", mars: "Марс", jupiter: "Юпитер", saturn: "Сатурн", uranus: "Уран", neptune: "Нептун" },
    kind: { sun: "Звезда", planet: "Планета", moon: "Спутник Земли" },
    diameter: "Диаметр", dist: "Расстояние от Солнца", distMoon: "Расстояние от Земли", day: "Сутки", year: "Год", moons: "Спутники", temp: "Температура", age: "Возраст", spin: "Оборот вокруг оси",
    km: "км", mkm: "млн км", h: "ч", min: "мин", days: "дн.", years: "лет", byears: "млрд лет", avg: "в среднем",
    toEarth: "Открыть карту", surface: "Карта поверхности", overview: "Солнечная система", backHome: "Вернуться на Землю",
    tip: "Нажмите на планету", load: "Загружаем космос…", fail: "Не удалось открыть 3D-космос. Проверьте интернет или браузер.",
    pause: "Пауза", play: "Продолжить", credit: "Текстуры: Solar System Scope (CC BY 4.0), данные NASA",
    desc: {
      sun: "Центр Солнечной системы: в нём 99,8% всей массы. Его свет доходит до Земли примерно за 8 минут 20 секунд.",
      mercury: "Самая близкая к Солнцу и самая маленькая планета. Атмосферы почти нет: днём до 430°C, ночью до −180°C.",
      venus: "Самая горячая планета: плотная атмосфера из углекислого газа удерживает тепло. Вращается в обратную сторону, Солнце там встаёт на западе.",
      earth: "Наш дом и единственная известная планета с жизнью. 71% поверхности покрыто водой.",
      moon: "Единственный естественный спутник Земли. Всегда повёрнута к нам одной стороной. В 1969 году человек впервые ступил на её поверхность.",
      mars: "Красная планета: цвет ей даёт оксид железа. Здесь самая высокая гора Солнечной системы — Олимп (~22 км).",
      jupiter: "Самая большая планета: внутри поместилось бы более 1300 Земель. Большое Красное Пятно — шторм больше Земли.",
      saturn: "Знаменит кольцами из льда и камней. Его средняя плотность меньше, чем у воды.",
      uranus: "Ледяной гигант, вращающийся «лёжа на боку»: ось наклонена на 98°. Голубоватый цвет ему придаёт метан.",
      neptune: "Самая далёкая от Солнца планета. Ветры здесь превышают 2000 км/ч — самые сильные в системе.",
    },
  },
  en: {
    names: { sun: "Sun", mercury: "Mercury", venus: "Venus", earth: "Earth", moon: "Moon", mars: "Mars", jupiter: "Jupiter", saturn: "Saturn", uranus: "Uranus", neptune: "Neptune" },
    kind: { sun: "Star", planet: "Planet", moon: "Earth's moon" },
    diameter: "Diameter", dist: "Distance from the Sun", distMoon: "Distance from Earth", day: "One day", year: "One year", moons: "Moons", temp: "Temperature", age: "Age", spin: "Rotation",
    km: "km", mkm: "million km", h: "h", min: "min", days: "days", years: "years", byears: "billion years", avg: "average",
    toEarth: "Open the map", surface: "Surface map", overview: "Solar System", backHome: "Back to Earth",
    tip: "Tap a planet", load: "Loading space…", fail: "Couldn't open 3D space. Check your internet or browser.",
    pause: "Pause", play: "Play", credit: "Textures: Solar System Scope (CC BY 4.0), NASA data",
    desc: {
      sun: "The center of the Solar System, holding 99.8% of its mass. Its light reaches Earth in about 8 minutes 20 seconds.",
      mercury: "The smallest planet and the closest to the Sun. With almost no atmosphere, days reach 430°C and nights drop to −180°C.",
      venus: "The hottest planet: its thick carbon dioxide atmosphere traps heat. It spins backwards, so the Sun rises in the west.",
      earth: "Our home and the only planet known to host life. Water covers 71% of its surface.",
      moon: "Earth's only natural satellite. It always shows us the same side. Humans first walked on it in 1969.",
      mars: "The red planet, colored by iron oxide. It has the tallest mountain in the Solar System, Olympus Mons (~22 km).",
      jupiter: "The largest planet: more than 1,300 Earths would fit inside. The Great Red Spot is a storm bigger than Earth.",
      saturn: "Famous for its rings of ice and rock. Its average density is lower than water's.",
      uranus: "An ice giant that spins on its side, with its axis tilted 98°. Methane gives it its blue-green color.",
      neptune: "The farthest planet from the Sun. Its winds top 2,000 km/h, the strongest in the Solar System.",
    },
  },
  zh: {
    names: { sun: "太阳", mercury: "水星", venus: "金星", earth: "地球", moon: "月球", mars: "火星", jupiter: "木星", saturn: "土星", uranus: "天王星", neptune: "海王星" },
    kind: { sun: "恒星", planet: "行星", moon: "地球的卫星" },
    diameter: "直径", dist: "与太阳的距离", distMoon: "与地球的距离", day: "一天", year: "一年", moons: "卫星", temp: "温度", age: "年龄", spin: "自转周期",
    km: "公里", mkm: "百万公里", h: "小时", min: "分", days: "天", years: "年", byears: "亿年", avg: "平均",
    toEarth: "进入地图", surface: "表面地图", overview: "太阳系", backHome: "返回地球",
    tip: "点击行星", load: "正在加载太空…", fail: "无法打开 3D 太空，请检查网络或浏览器。",
    pause: "暂停", play: "继续", credit: "纹理：Solar System Scope（CC BY 4.0），NASA 数据",
    desc: {
      sun: "太阳系的中心，占整个太阳系质量的 99.8%。阳光大约 8 分 20 秒到达地球。",
      mercury: "距离太阳最近、也是最小的行星。几乎没有大气，白天可达 430°C，夜晚降到 −180°C。",
      venus: "最热的行星：浓厚的二氧化碳大气留住了热量。它反向自转，太阳从西边升起。",
      earth: "我们的家园，也是目前已知唯一有生命的行星。表面 71% 被水覆盖。",
      moon: "地球唯一的天然卫星，总是以同一面朝向地球。1969 年人类首次登上月球。",
      mars: "红色星球，颜色来自氧化铁。太阳系最高的山——奥林帕斯山（约 22 公里）就在这里。",
      jupiter: "最大的行星，内部能装下 1300 多个地球。大红斑是一场比地球还大的风暴。",
      saturn: "以冰和岩石组成的光环闻名。它的平均密度比水还小。",
      uranus: "“躺着”自转的冰巨星，自转轴倾斜 98°。甲烷让它呈蓝绿色。",
      neptune: "离太阳最远的行星。风速超过每小时 2000 公里，是太阳系最强的风。",
    },
  },
};

/* Haqiqiy ma'lumotlar (kartada ko'rsatiladi) */
const FACTS = {
  sun: { diameter: 1392700, spin: { d: 25.4 }, temp: "5 500°C", age: 4.6 },
  mercury: { diameter: 4879, dist: 57.9, day: { d: 176 }, year: { d: 88 }, moons: "0", temp: "−173…427°C" },
  venus: { diameter: 12104, dist: 108.2, day: { d: 117 }, year: { d: 225 }, moons: "0", temp: "464°C" },
  earth: { diameter: 12742, dist: 149.6, day: { h: 24 }, year: { d: 365.25 }, moons: "1", temp: "15°C" },
  moon: { diameter: 3474, distMoon: 384400, day: { d: 29.5 }, temp: "−173…127°C" },
  mars: { diameter: 6779, dist: 227.9, day: { h: 24, m: 39 }, year: { d: 687 }, moons: "2", temp: "−65°C" },
  jupiter: { diameter: 139820, dist: 778.5, day: { h: 9, m: 56 }, year: { y: 11.86 }, moons: "95+", temp: "−110°C" },
  saturn: { diameter: 116460, dist: 1432, day: { h: 10, m: 33 }, year: { y: 29.46 }, moons: "274", temp: "−140°C" },
  uranus: { diameter: 50724, dist: 2867, day: { h: 17, m: 14 }, year: { y: 84 }, moons: "28", temp: "−195°C" },
  neptune: { diameter: 49244, dist: 4515, day: { h: 16, m: 6 }, year: { y: 164.8 }, moons: "16", temp: "−200°C" },
};

const SURFACE = { moon: true, mars: true };

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = text;
  return e;
}

function ringTexture() {
  // Saturn halqasi: ichkaridan tashqariga (C, B, Kassini bo'shlig'i, A, Enke bo'shlig'i)
  const c = document.createElement("canvas");
  c.width = 512; c.height = 2;
  const g = c.getContext("2d");
  const img = g.createImageData(512, 1);
  for (let x = 0; x < 512; x++) {
    const t = x / 511;
    let a;
    if (t < 0.12) a = 0.12 + t * 0.6;               // C halqa (xira)
    else if (t < 0.52) a = 0.75 + 0.2 * Math.sin(t * 60) * 0.3; // B halqa (yorqin)
    else if (t < 0.58) a = 0.06;                     // Kassini bo'shlig'i
    else if (t < 0.9) a = 0.55 + 0.1 * Math.sin(t * 90); // A halqa
    else if (t < 0.92) a = 0.12;                     // Enke bo'shlig'i
    else a = 0.45 * (1 - (t - 0.92) / 0.08);
    const shade = 0.78 + 0.22 * Math.sin(t * 23);
    img.data[x * 4] = 222 * shade; img.data[x * 4 + 1] = 200 * shade; img.data[x * 4 + 2] = 160 * shade;
    img.data[x * 4 + 3] = Math.max(0, Math.min(1, a)) * 255;
  }
  g.putImageData(img, 0, 0);
  g.putImageData(img, 0, 1);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

function glowTexture() {
  const c = document.createElement("canvas");
  c.width = c.height = 256;
  const g = c.getContext("2d");
  const gr = g.createRadialGradient(128, 128, 0, 128, 128, 128);
  gr.addColorStop(0, "rgba(255,230,170,0.9)");
  gr.addColorStop(0.25, "rgba(255,190,90,0.45)");
  gr.addColorStop(0.6, "rgba(255,140,40,0.12)");
  gr.addColorStop(1, "rgba(255,120,30,0)");
  g.fillStyle = gr; g.fillRect(0, 0, 256, 256);
  const tex = new THREE.CanvasTexture(c);
  tex.colorSpace = THREE.SRGBColorSpace;
  return tex;
}

export function createSpace(opts) {
  const root = opts.container;
  const lang = T[opts.lang] ? opts.lang : "en";
  const L = T[lang];
  const lite = !!opts.lite;
  const nf = new Intl.NumberFormat({ uz: "ru-RU", ru: "ru-RU", en: "en-US", zh: "zh-CN" }[lang] || "en-US", { maximumFractionDigits: 2 });

  /* ---------- DOM ---------- */
  root.innerHTML = "";
  const canvas = el("canvas", "sp-cv");
  const labels = el("div", "sp-labels");
  const card = el("div", "sp-card"); card.hidden = true;
  const bar = el("div", "sp-bar");
  const homeBtn = el("button", "sp-btn", L.backHome); homeBtn.type = "button";
  const overBtn = el("button", "sp-btn", L.overview); overBtn.type = "button"; overBtn.hidden = true;
  const pauseBtn = el("button", "sp-btn sp-icon"); pauseBtn.type = "button";
  const tip = el("div", "sp-tip", L.tip);
  const credit = el("div", "sp-credit", L.credit);
  const loading = el("div", "sp-loading", L.load);
  bar.append(overBtn, homeBtn, pauseBtn);
  root.append(canvas, labels, bar, card, tip, credit, loading);

  /* ---------- Three.js ---------- */
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({ canvas, antialias: !lite, powerPreference: "high-performance" });
  } catch (e) {
    loading.textContent = L.fail;
    throw e;
  }
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, lite ? 1.25 : 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, 1, 0.02, 3000);
  const controls = new OrbitControls(camera, canvas);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.enablePan = false;
  controls.minDistance = 8;
  controls.maxDistance = 260;
  controls.rotateSpeed = 0.6;

  scene.add(new THREE.AmbientLight(0xffffff, 0.14));
  const sunLight = new THREE.PointLight(0xffffff, 2.6, 0, 0);
  scene.add(sunLight);

  const loader = new THREE.TextureLoader();
  let left = 0;
  const doneOne = () => { if (--left <= 0) loading.hidden = true; };
  function tex(name) {
    left++;
    const t = loader.load(BASE + name + ".webp", doneOne, undefined, doneOne);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = Math.min(4, renderer.capabilities.getMaxAnisotropy());
    return t;
  }

  // Yulduzli osmon
  const sky = new THREE.Mesh(
    new THREE.SphereGeometry(1400, 48, 32),
    new THREE.MeshBasicMaterial({ map: tex("stars"), side: THREE.BackSide, color: 0x8a8f9c })
  );
  scene.add(sky);

  const seg = lite ? 40 : 64;
  const objs = {};   // id -> { cfg, pivot, mesh, label, angle }
  const pickables = [];

  function makeBody(cfg) {
    const pivot = new THREE.Object3D();      // joylashuv (orbita bo'ylab)
    const tiltG = new THREE.Object3D();      // o'q og'ishi
    tiltG.rotation.z = THREE.MathUtils.degToRad(cfg.tilt || 0);
    pivot.add(tiltG);
    const geo = new THREE.SphereGeometry(cfg.r, cfg.r > 1 ? seg : Math.max(24, seg / 2), cfg.r > 1 ? seg / 2 : 20);
    const mat = cfg.id === "sun"
      ? new THREE.MeshBasicMaterial({ map: tex("sun"), color: 0xffffff })
      : new THREE.MeshStandardMaterial({ map: tex(cfg.id), color: 0xffffff, roughness: 1, metalness: 0 });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.userData.id = cfg.id;
    tiltG.add(mesh);
    pickables.push(mesh);

    if (cfg.ring) {
      const [ri, ro] = cfg.ring;
      const rg = new THREE.RingGeometry(ri, ro, 160, 1);
      const pos = rg.attributes.position, uv = rg.attributes.uv, v = new THREE.Vector3();
      for (let i = 0; i < pos.count; i++) { v.fromBufferAttribute(pos, i); uv.setXY(i, (v.length() - ri) / (ro - ri), 0.5); }
      const ring = new THREE.Mesh(rg, new THREE.MeshBasicMaterial({ map: ringTexture(), transparent: true, side: THREE.DoubleSide, depthWrite: false }));
      ring.rotation.x = -Math.PI / 2;
      tiltG.add(ring);
    }

    const label = el("button", "sp-label", L.names[cfg.id]);
    label.type = "button";
    label.addEventListener("click", (e) => { e.stopPropagation(); focus(cfg.id); });
    labels.appendChild(label);

    const o = { cfg, pivot, mesh, label, angle: 0 };
    objs[cfg.id] = o;
    return o;
  }

  // Quyosh
  const sunO = makeBody(BODIES[0]);
  scene.add(sunO.pivot);
  const glow = new THREE.Sprite(new THREE.SpriteMaterial({ map: glowTexture(), blending: THREE.AdditiveBlending, depthWrite: false, transparent: true }));
  glow.scale.set(30, 30, 1);
  sunO.pivot.add(glow);

  // Sayyoralar va orbitalar
  const orbitMat = new THREE.LineBasicMaterial({ color: 0x9fb4d8, transparent: true, opacity: 0.16 });
  const daysNow = (Date.now() - J2000) / DAY_MS;
  BODIES.slice(1).forEach((cfg) => {
    const o = makeBody(cfg);
    o.angle = THREE.MathUtils.degToRad((cfg.L0 + cfg.n * daysNow) % 360);
    scene.add(o.pivot);
    const pts = [];
    for (let i = 0; i <= 256; i++) { const a = (i / 256) * Math.PI * 2; pts.push(new THREE.Vector3(Math.cos(a) * cfg.d, 0, -Math.sin(a) * cfg.d)); }
    scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), orbitMat));
  });
  // Oy (Yer atrofida)
  const moonO = makeBody(MOON);
  moonO.angle = Math.PI * 2 * (((daysNow - 5.6) / MOON.P) % 1);
  scene.add(moonO.pivot);

  /* ---------- Holat ---------- */
  let simDays = 0, paused = false, running = false, raf = 0, lastT = 0;
  let focusId = null, flight = null;
  const tmpV = new THREE.Vector3(), prevFocusPos = new THREE.Vector3();

  function overviewPose() {
    const w = root.clientWidth || 1, h = root.clientHeight || 1;
    const far = w < 700 ? 1.3 : 0.82;
    const portrait = h > w ? 1.25 : 1;
    return { pos: new THREE.Vector3(0, 58 * far * portrait, 100 * far * portrait), target: new THREE.Vector3(0, 0, 0) };
  }

  function place() {
    BODIES.slice(1).forEach((cfg) => {
      const o = objs[cfg.id];
      const a = o.angle + (simDays / cfg.P) * Math.PI * 2;
      o.pivot.position.set(Math.cos(a) * cfg.d, 0, -Math.sin(a) * cfg.d);
    });
    const e = objs.earth.pivot.position;
    const ma = moonO.angle + (simDays / MOON.P) * Math.PI * 2;
    moonO.pivot.position.set(e.x + Math.cos(ma) * MOON.d, Math.sin(ma) * 0.25, e.z - Math.sin(ma) * MOON.d);
  }

  function spinAll(dt) {
    [...BODIES, MOON].forEach((cfg) => {
      const o = objs[cfg.id];
      const speed = 0.35 * Math.pow(24 / Math.abs(cfg.spin), 0.35) * Math.sign(cfg.spin);
      o.mesh.rotation.y += speed * dt;
    });
  }

  /* ---------- Kamera parvozi ---------- */
  const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
  function flyTo(pos, target, ms, done) {
    flight = { p0: camera.position.clone(), t0: controls.target.clone(), p1: pos, t1: target, start: performance.now(), ms, done };
    controls.enabled = false;
  }

  function focusPose(id) {
    const o = objs[id], r = o.cfg.r;
    const p = o.pivot.getWorldPosition(new THREE.Vector3());
    // Kamera Quyosh tomonda (yoritilgan tomonni ko'rish uchun), biroz yuqoridan
    const toSun = id === "sun" ? new THREE.Vector3(0.3, 0.35, 1).normalize() : p.clone().multiplyScalar(-1).normalize();
    const side = new THREE.Vector3().crossVectors(toSun, new THREE.Vector3(0, 1, 0)).normalize();
    const dir = toSun.clone().multiplyScalar(0.82).add(side.multiplyScalar(0.45)).add(new THREE.Vector3(0, 0.3, 0)).normalize();
    const aspect = (root.clientWidth || 1) / (root.clientHeight || 1);
    const pf = aspect < 1 ? Math.min(1.9, Math.max(1, 0.75 / aspect)) : 1; // tik ekranda uzoqroqdan
    const dist = (id === "saturn" ? r * 5.2 : id === "sun" ? r * 4.2 : r * 3.6) * pf;
    return { pos: p.clone().add(dir.multiplyScalar(dist)), target: p, r };
  }

  function focus(id) {
    if (!objs[id]) return;
    focusId = id;
    const fp = focusPose(id);
    controls.minDistance = fp.r * 1.4;
    controls.maxDistance = Math.max(fp.r * 14, 18);
    prevFocusPos.copy(fp.target);
    flyTo(fp.pos, fp.target, 1700, null);
    showCard(id);
    overBtn.hidden = false;
    tip.hidden = true;
    labels.classList.add("focused");
    Object.values(objs).forEach((o) => o.label.classList.toggle("on", o.cfg.id === id));
  }

  function overview(ms) {
    focusId = null;
    card.hidden = true;
    applyOffset();
    overBtn.hidden = true;
    tip.hidden = false;
    labels.classList.remove("focused");
    Object.values(objs).forEach((o) => o.label.classList.remove("on"));
    controls.minDistance = 8; controls.maxDistance = 260;
    const ov = overviewPose();
    flyTo(ov.pos, ov.target, ms || 1800, null);
  }

  /* ---------- Ma'lumot kartasi ---------- */
  function dur(v) {
    if (!v) return "";
    if (v.y != null) return nf.format(v.y) + " " + L.years;
    if (v.d != null) return nf.format(v.d) + " " + L.days;
    return v.h + " " + L.h + (v.m ? " " + v.m + " " + L.min : "");
  }
  function showCard(id) {
    const f = FACTS[id] || {};
    card.innerHTML = "";
    const kind = id === "sun" ? L.kind.sun : id === "moon" ? L.kind.moon : L.kind.planet;
    card.append(el("div", "sp-kind", kind), el("h2", "sp-name", L.names[id]), el("p", "sp-desc", L.desc[id]));
    const grid = el("div", "sp-grid");
    const row = (k, v) => { if (v == null || v === "") return; const c = el("div", "sp-cell"); c.append(el("small", null, k), el("b", null, v)); grid.appendChild(c); };
    row(L.diameter, nf.format(f.diameter) + " " + L.km);
    if (f.dist != null) row(L.dist, nf.format(f.dist) + " " + L.mkm);
    if (f.distMoon != null) row(L.distMoon, nf.format(f.distMoon) + " " + L.km);
    if (f.day) row(L.day, dur(f.day));
    if (f.spin) row(L.spin, dur(f.spin));
    if (f.year) row(L.year, dur(f.year));
    if (f.moons != null) row(L.moons, f.moons);
    if (f.age != null) row(L.age, nf.format(f.age) + " " + L.byears);
    row(L.temp, f.temp);
    card.appendChild(grid);
    const acts = el("div", "sp-acts");
    if (id === "earth") {
      const b = el("button", "sp-go", L.toEarth); b.type = "button";
      b.addEventListener("click", () => opts.onEarth && opts.onEarth());
      acts.appendChild(b);
    }
    if (SURFACE[id]) {
      const b = el("button", "sp-go", L.surface); b.type = "button";
      b.addEventListener("click", () => opts.onSurface && opts.onSurface(id));
      acts.appendChild(b);
    }
    if (acts.childNodes.length) card.appendChild(acts);
    card.hidden = false;
    card.scrollTop = 0;
    applyOffset();
  }

  /* ---------- Bosish (raycast) ---------- */
  const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
  let down = null;
  canvas.addEventListener("pointerdown", (e) => { down = { x: e.clientX, y: e.clientY, t: performance.now() }; });
  canvas.addEventListener("pointerup", (e) => {
    if (!down) return;
    const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y);
    const quick = performance.now() - down.t < 450;
    down = null;
    if (moved > 6 || !quick) return;
    const rect = canvas.getBoundingClientRect();
    ndc.set(((e.clientX - rect.left) / rect.width) * 2 - 1, -((e.clientY - rect.top) / rect.height) * 2 + 1);
    ray.setFromCamera(ndc, camera);
    const hit = ray.intersectObjects(pickables, false)[0];
    if (hit) focus(hit.object.userData.id);
  });

  homeBtn.addEventListener("click", () => {
    focus("earth");
    setTimeout(() => opts.onEarth && opts.onEarth(), 1500);
  });
  overBtn.addEventListener("click", () => overview());
  function setPauseUi() {
    pauseBtn.textContent = paused ? "▶" : "❚❚";
    pauseBtn.setAttribute("aria-label", paused ? L.play : L.pause);
    pauseBtn.title = paused ? L.play : L.pause;
  }
  pauseBtn.addEventListener("click", () => { paused = !paused; setPauseUi(); });
  setPauseUi();
  window.addEventListener("keydown", (e) => {
    if (!running) return;
    if (e.key === "Escape" && focusId) overview();
  });

  /* ---------- O'lcham ---------- */
  // Telefonda karta pastni egallaydi: sahnani biroz yuqoriga suramiz, sayyora karta ortida qolmasin
  function applyOffset() {
    const w = root.clientWidth || window.innerWidth, h = root.clientHeight || window.innerHeight;
    if (!card.hidden && w < 700) camera.setViewOffset(w, h, 0, Math.round(h * 0.2), w, h);
    else camera.clearViewOffset();
    camera.updateProjectionMatrix();
  }
  function resize() {
    const w = root.clientWidth || window.innerWidth, h = root.clientHeight || window.innerHeight;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    applyOffset();
  }
  new ResizeObserver(resize).observe(root);

  /* ---------- Yozuvlar (sayyora nomlari) ---------- */
  const LABEL_ORDER = ["sun", "jupiter", "saturn", "earth", "mars", "venus", "uranus", "neptune", "mercury", "moon"];
  function updateLabels() {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    const placed = [];
    const order = focusId ? [focusId].concat(LABEL_ORDER.filter((k) => k !== focusId)) : LABEL_ORDER;
    order.map((k) => objs[k]).forEach((o) => {
      o.pivot.getWorldPosition(tmpV);
      const r = o.cfg.r;
      tmpV.y += r * 1.15;
      const camDist = camera.position.distanceTo(tmpV);
      tmpV.project(camera);
      const visible = tmpV.z < 1 && Math.abs(tmpV.x) < 1.1 && Math.abs(tmpV.y) < 1.1;
      // Oy nomi faqat yaqindan ko'rinadi
      const hideSmall = o.cfg.id === "moon" && camDist > 45 && focusId !== "moon";
      if (!visible || hideSmall) { o.label.style.display = "none"; return; }
      const x = (tmpV.x * 0.5 + 0.5) * w, y = (-tmpV.y * 0.5 + 0.5) * h;
      // Nomlar bir-birining ustiga chiqmasin: muhimrog'i qoladi
      const lw = o.label.textContent.length * 8 + 14, lh = 20;
      const box = { l: x - lw / 2, r: x + lw / 2, t: y - lh, b: y };
      if (placed.some((p) => box.l < p.r && box.r > p.l && box.t < p.b && box.b > p.t)) { o.label.style.display = "none"; return; }
      placed.push(box);
      o.label.style.display = "";
      o.label.style.transform = "translate(" + x.toFixed(1) + "px," + y.toFixed(1) + "px) translate(-50%,-100%)";
    });
  }

  /* ---------- Asosiy sikl ---------- */
  function frame(t) {
    if (!running) return;
    raf = requestAnimationFrame(frame);
    const dt = Math.min(0.05, (t - (lastT || t)) / 1000);
    lastT = t;
    if (!paused) { simDays += dt * SIM_DAYS_PER_SEC; spinAll(dt); }
    place();

    if (flight) {
      const k = Math.min(1, (t - flight.start) / flight.ms), e = ease(k);
      // Kuzatilayotgan jism parvoz paytida ham siljiydi
      if (focusId) { const fp = objs[focusId].pivot.getWorldPosition(new THREE.Vector3()); flight.p1.add(fp.clone().sub(flight.t1)); flight.t1.copy(fp); }
      camera.position.lerpVectors(flight.p0, flight.p1, e);
      controls.target.lerpVectors(flight.t0, flight.t1, e);
      if (k >= 1) { const d = flight.done; flight = null; controls.enabled = true; if (focusId) objs[focusId].pivot.getWorldPosition(prevFocusPos); if (d) d(); }
    } else if (focusId) {
      // Fokusdagi jism bilan birga harakatlanish
      const p = objs[focusId].pivot.getWorldPosition(tmpV);
      const delta = p.clone().sub(prevFocusPos);
      camera.position.add(delta);
      controls.target.add(delta);
      prevFocusPos.copy(p);
    }
    controls.update();
    renderer.render(scene, camera);
    updateLabels();
  }

  /* ---------- Tashqi API ---------- */
  function start() {
    if (running) return;
    running = true; lastT = 0;
    resize();
    raf = requestAnimationFrame(frame);
  }
  function stop() { running = false; cancelAnimationFrame(raf); }

  const api = {
    /* fromEarth: Yer yonidan boshlab uzoqlashadi; focusOn: to'g'ridan-to'g'ri shu jismga */
    show(o) {
      o = o || {};
      start();
      place();
      if (o.focusOn) {
        const fp = focusPose(o.focusOn);
        camera.position.copy(fp.pos); controls.target.copy(fp.target);
        focus(o.focusOn);
      } else if (o.fromEarth) {
        focusId = null;
        const ep = objs.earth.pivot.getWorldPosition(new THREE.Vector3());
        const away = ep.clone().normalize();
        camera.position.copy(ep).add(away.multiplyScalar(-3.4)).add(new THREE.Vector3(0, 0.8, 0));
        controls.target.copy(ep);
        card.hidden = true; overBtn.hidden = true; tip.hidden = false;
        labels.classList.remove("focused");
        setTimeout(() => overview(2800), 150);
      } else {
        const ov = overviewPose();
        camera.position.copy(ov.pos); controls.target.copy(ov.target);
      }
    },
    hide() { stop(); },
    focus,
    overview,
    get running() { return running; },
  };

  // Teksturalar sekin yuklansa ham "yuklanmoqda" yozuvi 6 soniyadan keyin yo'qoladi
  setTimeout(() => { loading.hidden = true; }, 6000);

  return api;
}
