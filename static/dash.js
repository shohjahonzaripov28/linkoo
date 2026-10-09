/* Bosh sahifadagi kichik animatsiyalar: Linko AI humanoidi va Linko Map globusi.
   Ekranda ko'rinmasa to'xtaydi, "harakatni kamaytirish" yoqilgan bo'lsa bitta kadr chiziladi. */
(function () {
  "use strict";
  const REDUCED = document.documentElement.classList.contains("reduce-motion") ||
                  (window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches);
  const TAU = Math.PI * 2;

  function sprite(rgb, size) {
    const c = document.createElement("canvas");
    c.width = c.height = size;
    const g = c.getContext("2d"), r = size / 2;
    const grd = g.createRadialGradient(r, r, 0, r, r, r);
    grd.addColorStop(0, "rgba(255,255,255,1)");
    grd.addColorStop(0.2, `rgba(${rgb},1)`);
    grd.addColorStop(0.5, `rgba(${rgb},0.3)`);
    grd.addColorStop(1, `rgba(${rgb},0)`);
    g.fillStyle = grd;
    g.fillRect(0, 0, size, size);
    return c;
  }
  const BLUE = sprite("70,200,255", 32), ORANGE = sprite("255,150,55", 32), GOLD = sprite("255,210,110", 32);
  const VIOLET = sprite("167,139,250", 32), PINK = sprite("236,72,153", 32), CYAN = sprite("125,211,252", 32);

  /* ---- Humanoid (Linko AI) ---- */
  function halfWidth(y) {
    let w = 0;
    const hd = (y + 0.36) / 0.26;
    if (hd > -1 && hd < 1) { let h = 0.175 * Math.sqrt(1 - hd * hd); if (hd > 0) h *= 1 - 0.3 * hd * hd; w = h; }
    if (y > -0.2 && y < 0.1) w = Math.max(w, 0.078);
    if (y > -0.02) { const t = Math.min(1, (y + 0.02) / 0.24); w = Math.max(w, 0.08 + 0.4 * (1 - Math.pow(1 - t, 2.4))); }
    return w;
  }
  const BUST = [];
  (function () {
    const lines = 34;
    for (let k = 0; k < lines; k++) {
      const y = -0.62 + 1.1 * k / (lines - 1), hw = halfWidth(y);
      if (hw < 0.01) continue;
      const n = Math.max(6, Math.round(hw * 70));
      for (let j = 0; j < n; j++) {
        const x = (-1 + 2 * (j + 0.5) / n) * hw, u = x / hw, z = Math.sqrt(Math.max(0, 1 - u * u));
        const core = y < -0.12 && Math.exp(-(x * x) / 0.006 - ((y + 0.32) * (y + 0.32)) / 0.016) > 0.45;
        const fade = y > 0.3 ? Math.max(0.1, 1 - (y - 0.3) / 0.2) : 1;
        BUST.push([x, y + 0.03 * z, z, core ? 1 : 0, (0.25 + 0.75 * Math.pow(1 - z, 2)) * fade, y]);
      }
    }
    for (let j = 0; j < 60; j++) {   // oltin chiziqlar
      const v = j / 60, line = j % 3 - 1;
      BUST.push([line * 0.05 * (1 + 4 * Math.sin(v * Math.PI)) * (1 - v * v), -0.15 + v * 0.55, 0.5, 2, 0.9, 0]);
    }
  })();

  function drawAI(g, w, h, t) {
    g.clearRect(0, 0, w, h);
    g.globalCompositeOperation = "lighter";
    const S = h * 0.78 / 1.2, cx = w * 0.55, cy = h * 0.58;
    const breath = 1 + 0.012 * Math.sin(t * 1.6), yaw = 0.25 * Math.sin(t * 0.5);
    const scan = -0.62 + ((t * 0.35) % 1) * 1.2, ds = Math.max(2.5, S * 0.03);
    // Boshdagi to'q sariq nur
    g.globalAlpha = 0.5 + 0.1 * Math.sin(t * 2);
    g.drawImage(ORANGE, cx + Math.sin(yaw) * 0.08 * S - S * 0.32, cy - 0.33 * S - S * 0.32, S * 0.64, S * 0.64);
    for (const p of BUST) {
      let x = p[0];
      if (p[5] < -0.05) x = x * Math.cos(yaw) + p[2] * 0.15 * Math.sin(yaw);
      const X = cx + x * S * breath, Y = cy + p[1] * S * breath;
      const d = (p[1] - scan) * 20;
      let a = p[4] + 0.6 * Math.exp(-d * d);
      if (p[3] === 2) a = 0.35 + 0.65 * Math.max(0, Math.sin((p[1] * 3 - t) * 3));
      g.globalAlpha = Math.min(1, a);
      g.drawImage(p[3] === 1 ? ORANGE : p[3] === 2 ? GOLD : BLUE, X - ds / 2, Y - ds / 2, ds, ds);
    }
    g.globalAlpha = 1;
    const pul = 1 + 0.2 * Math.sin(t * 4);
    g.drawImage(CYAN, cx - S * 0.08 * pul, cy + 0.42 * S - S * 0.08 * pul, S * 0.16 * pul, S * 0.16 * pul);
    g.globalCompositeOperation = "source-over";
  }

  /* ---- Globus (Linko Map) ---- */
  const GLOBE = [];
  (function () {
    const n = 900, gold = Math.PI * (3 - Math.sqrt(5));
    for (let i = 0; i < n; i++) {
      const y = 1 - 2 * (i + 0.5) / n, r = Math.sqrt(1 - y * y), th = gold * i;
      const x = Math.cos(th) * r, z = Math.sin(th) * r;
      const land = Math.sin(x * 6.5 + 1) * Math.cos(y * 4.2) + Math.sin(z * 5.3 + y * 2.5) > 0.45;
      GLOBE.push([x, y, z, land]);
    }
  })();
  const ROUTES = [[0.6, 0.45, 1.9, 0.6], [1.2, 0.5, 2.6, 0.2], [-0.4, 0.3, 0.9, 0.65], [2.0, 0.1, 3.2, 0.5], [0.2, -0.2, 1.4, 0.4]];
  function sph(lon, lat) { return [Math.cos(lat) * Math.cos(lon), Math.sin(lat), Math.cos(lat) * Math.sin(lon)]; }

  function drawGlobe(g, w, h, t) {
    g.clearRect(0, 0, w, h);
    g.globalCompositeOperation = "lighter";
    const R = Math.min(w * 0.42, h * 0.4), cx = w * 0.56, cy = h * 0.5, rot = t * 0.25;
    const cr = Math.cos(rot), sr = Math.sin(rot), ds = Math.max(2, R * 0.045);
    g.globalAlpha = 0.35;
    g.drawImage(VIOLET, cx - R * 1.5, cy - R * 1.5, R * 3, R * 3);
    for (const p of GLOBE) {
      const X = p[0] * cr + p[2] * sr, Z = -p[0] * sr + p[2] * cr;
      if (Z < -0.1) continue;
      g.globalAlpha = (0.2 + 0.7 * Math.max(0, Z)) * (p[3] ? 1 : 0.35);
      const s = p[3] ? ds : ds * 0.7;
      g.drawImage(p[3] ? CYAN : BLUE, cx + X * R - s / 2, cy - p[1] * R - s / 2, s, s);
    }
    // Uchayotgan "samolyotlar" yoylari
    for (let k = 0; k < ROUTES.length; k++) {
      const a = ROUTES[k], prog = (t * 0.25 + k * 0.21) % 1;
      for (let i = 0; i <= 24; i++) {
        const f = i / 24;
        if (f > prog) break;
        const v = sph(a[0] + (a[2] - a[0]) * f, a[1] + (a[3] - a[1]) * f), lift = 1 + 0.22 * Math.sin(f * Math.PI);
        const X = v[0] * cr + v[2] * sr, Z = -v[0] * sr + v[2] * cr;
        if (Z < 0) continue;
        const head = f > prog - 0.05;
        g.globalAlpha = head ? 1 : 0.35 + 0.4 * f;
        const s = head ? ds * 2.2 : ds * 0.9;
        g.drawImage(head ? PINK : VIOLET, cx + X * R * lift - s / 2, cy - v[1] * R * lift - s / 2, s, s);
      }
    }
    g.globalAlpha = 1;
    g.globalCompositeOperation = "source-over";
  }

  /* ---- Ishga tushirish ---- */
  const items = [];
  document.querySelectorAll(".hero-canvas").forEach((c) => {
    const item = { c, g: c.getContext("2d"), kind: c.dataset.kind, visible: true, w: 0, h: 0 };
    items.push(item);
  });
  if (!items.length) return;
  function size() {
    const d = Math.min(window.devicePixelRatio || 1, 2);
    items.forEach((it) => {
      it.w = it.c.width = Math.round(it.c.clientWidth * d);
      it.h = it.c.height = Math.round(it.c.clientHeight * d);
    });
  }
  size();
  window.addEventListener("resize", size);
  if ("IntersectionObserver" in window) {
    const io = new IntersectionObserver((es) => es.forEach((e) => {
      const it = items.find((x) => x.c === e.target);
      if (it) it.visible = e.isIntersecting;
    }));
    items.forEach((it) => io.observe(it.c));
  }
  const t0 = performance.now();
  function frame(now) {
    const t = (now - t0) / 1000 + 3;
    items.forEach((it) => {
      if (!it.visible || !it.w) return;
      (it.kind === "ai" ? drawAI : drawGlobe)(it.g, it.w, it.h, t);
    });
    if (!REDUCED) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
})();
