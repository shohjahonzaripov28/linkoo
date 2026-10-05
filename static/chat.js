/* Linko chat: shaxsiy va guruh chatlari uchun umumiy skript.
   Matn, rasm, ovozli xabar, dumaloq video xabar, stikerlar, reply (javob), tarjima (xabarni bosish). */
(function () {
  "use strict";
  var card = document.querySelector(".chat-card");
  var cfgEl = document.getElementById("chat-cfg");
  if (!card || !cfgEl) return;

  var cfg = JSON.parse(cfgEl.textContent);
  var T = cfg.t;
  var kind = card.dataset.kind;           // "dm" | "group"
  var target = card.dataset.target;       // foydalanuvchi nomi yoki guruh id
  var me = card.dataset.me;

  var API_LIST = kind === "dm" ? "/api/dm/" + encodeURIComponent(target) : "/api/groups/" + target + "/messages";
  var API_SEND = kind === "dm" ? "/api/dm/send/" + encodeURIComponent(target) : "/api/groups/" + target + "/send";
  function apiDelete(id) { return kind === "dm" ? "/api/dm/delete/" + id : "/api/groups/message/delete/" + id; }

  var $ = function (id) { return document.getElementById(id); };
  var box = $("messages"), form = $("send-form"), input = $("message-input");
  var imageInput = $("image-input"), previewRow = $("preview-row"), previewImg = $("preview-img");
  var btnSend = $("btn-send"), btnMic = $("btn-mic"), btnVnote = $("btn-vnote");
  var nodes = new Map();      // id -> element
  var store = new Map();      // id -> message data
  var translations = new Map();
  var replyTo = null;
  var firstLoad = true;
  var sending = false;

  /* ---------- yordamchilar ---------- */
  function esc(s) { var d = document.createElement("div"); d.textContent = s == null ? "" : s; return d.innerHTML; }
  function fmtTime(sec) { sec = Math.max(0, Math.round(sec || 0)); return Math.floor(sec / 60) + ":" + String(sec % 60).padStart(2, "0"); }
  function profileHref(name) { return name === me ? "/profile" : "/u/" + encodeURIComponent(name); }
  var toastTimer;
  function toast(text) {
    var el = $("chat-toast"); el.textContent = text; el.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { el.hidden = true; }, 2200);
  }
  function nearBottom() { return box.scrollHeight - box.scrollTop - box.clientHeight < 140; }
  function scrollBottom() { box.scrollTop = box.scrollHeight; }
  function icon(name) {
    var p = {
      play: '<path d="M8 5.5v13l11-6.5-11-6.5Z" fill="currentColor" stroke="none"/>',
      pause: '<path d="M7 5h3.5v14H7zM13.5 5H17v14h-3.5z" fill="currentColor" stroke="none"/>',
      reply: '<path d="M9 7 4 12l5 5"/><path d="M4 12h9a7 7 0 0 1 7 7"/>',
      phone: '<path d="M5 4h3.2l1.6 4-2 1.3a11 11 0 0 0 5.9 5.9l1.3-2 4 1.6V18a2 2 0 0 1-2.2 2A15.5 15.5 0 0 1 3 6.2 2 2 0 0 1 5 4Z"/>',
      video: '<rect x="3" y="6" width="13" height="12" rx="2.5"/><path d="m16 10.5 5-2.5v8l-5-2.5"/>'
    }[name];
    return '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">' + p + "</svg>";
  }
  function previewOf(m) {
    if (m.kind === "audio") return "🎤 " + T.voice;
    if (m.kind === "video") return "🎥 " + T.vnote;
    if (m.kind === "image") return "📷 " + (m.content || T.photo);
    if (m.kind === "sticker") return m.content;
    return m.content || "";
  }

  /* ---------- xabar qatorini yaratish ---------- */
  function buildMedia(m) {
    var src = "/media/" + encodeURIComponent(m.image_file);
    if (m.kind === "image") {
      return '<a class="msg-image-link" href="' + src + '" target="_blank" rel="noopener"><img class="msg-image" src="' + src + '" alt="" loading="lazy"></a>';
    }
    if (m.kind === "audio") {
      var bars = "", seed = m.id * 9301 + 49297;
      for (var i = 0; i < 28; i++) { seed = (seed * 9301 + 49297) % 233280; bars += '<i style="height:' + (22 + Math.round(seed / 233280 * 78)) + '%"></i>'; }
      return '<div class="voice" data-src="' + src + '" data-dur="' + (m.duration || 0) + '">' +
        '<button type="button" class="voice-play" aria-label="play">' + icon("play") + "</button>" +
        '<div class="voice-wave">' + bars + "</div>" +
        '<span class="voice-dur">' + fmtTime(m.duration) + "</span>" +
        '<button type="button" class="voice-speed">1x</button></div>';
    }
    if (m.kind === "video") {
      return '<div class="vnote" data-src="' + src + '"><video src="' + src + '#t=0.1" playsinline preload="metadata"></video>' +
        '<span class="vnote-play">' + icon("play") + '</span><span class="vnote-dur">' + fmtTime(m.duration) + "</span></div>";
    }
    return "";
  }

  function callLabel(m) {
    var parts = (m.content || "audio:ended").split(":");
    var ck = parts[0] === "video" ? "video" : "audio";
    var status = parts[1] || "ended";
    var name = ck === "video" ? T.callVideo : T.callAudio;
    if (status === "missed") return { text: T.callMissed, cls: "missed", ck: ck };
    if (status === "declined") return { text: T.callDeclined, cls: "missed", ck: ck };
    return { text: name + (m.duration ? " · " + fmtTime(m.duration) : ""), cls: "", ck: ck };
  }

  function buildRow(m) {
    var isMe = m.author === me;
    var row = document.createElement("div");
    row.dataset.id = m.id;

    if (m.kind === "call") {
      var cl = callLabel(m);
      row.className = "msg-call-row";
      row.innerHTML = '<button type="button" class="msg-call ' + cl.cls + '" data-call="' + cl.ck + '">' +
        icon(cl.ck === "video" ? "video" : "phone") + "<span>" + esc(cl.text) + '</span><time>' + esc(m.created_at) + "</time></button>";
      return row;
    }

    row.className = "msg-row " + (isMe ? "msg-right" : "msg-left");
    var reply = "";
    if (m.reply) {
      reply = '<div class="msg-reply" data-reply-id="' + m.reply.id + '"><b>' + esc(m.reply.author) + "</b><span>" +
        esc(previewOf({ kind: m.reply.kind, content: m.reply.text })) + "</span></div>";
    }
    var author = "";
    if (kind === "group" && !isMe) {
      author = '<a class="msg-author" href="' + profileHref(m.author) + '">' + esc(m.author) + "</a>";
    }
    var quick = '<button type="button" class="msg-quick-reply" aria-label="' + esc(T.reply) + '">' + icon("reply") + "</button>";

    if (m.kind === "sticker") {
      row.innerHTML = quick + '<div class="msg-sticker-wrap">' + author + reply +
        '<div class="msg-sticker">' + esc(m.content) + '</div><div class="msg-time sticker-time">' + esc(m.created_at) + "</div></div>";
    } else {
      row.innerHTML = quick + '<div class="msg-bubble ' + (isMe ? "msg-mine" : "msg-other") + (m.kind === "video" ? " has-vnote" : "") + '">' +
        author + reply + buildMedia(m) +
        (m.content ? '<div class="msg-text">' + esc(m.content) + "</div>" : "") +
        '<div class="msg-translation" hidden></div>' +
        '<div class="msg-time">' + esc(m.created_at) + "</div></div>";
    }
    return row;
  }

  function sync(list) {
    var ids = new Set(list.map(function (m) { return m.id; }));
    nodes.forEach(function (el, id) { if (!ids.has(id)) { el.remove(); nodes.delete(id); store.delete(id); } });
    var stick = firstLoad || nearBottom();
    var added = false, lastMine = false;
    list.forEach(function (m) {
      store.set(m.id, m);
      if (!nodes.has(m.id)) {
        var el = buildRow(m);
        box.appendChild(el);
        nodes.set(m.id, el);
        added = true;
        lastMine = m.author === me;
      }
    });
    if (added && (stick || lastMine)) scrollBottom();
    firstLoad = false;
  }

  function load() {
    return fetch(API_LIST).then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
      if (d && d.messages) sync(d.messages);
    }).catch(function () {});
  }

  /* ---------- yuborish ---------- */
  function clearReply() {
    replyTo = null; $("reply-bar").hidden = true;
  }
  function setReply(m) {
    replyTo = { id: m.id };
    $("reply-bar-author").textContent = m.author + " ";
    $("reply-bar-text").textContent = previewOf(m);
    $("reply-bar").hidden = false;
    input.focus();
  }
  $("reply-bar-close").addEventListener("click", clearReply);

  function post(fd) {
    if (replyTo) fd.append("reply_to", replyTo.id);
    return fetch(API_SEND, { method: "POST", body: fd }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (data) {
        if (!res.ok) { toast(data.message || T.upload); return false; }
        clearReply();
        return load().then(function () { scrollBottom(); return true; });
      });
    }).catch(function () { toast(T.net); return false; });
  }

  function shrinkImage(file) {
    if (!cfg.shrinkImages || file.type === "image/gif" || file.size < 400 * 1024) return Promise.resolve(file);
    return new Promise(function (resolve) {
      var url = URL.createObjectURL(file), img = new Image();
      img.onload = function () {
        var max = 1600, s = Math.min(1, max / Math.max(img.width, img.height));
        var c = document.createElement("canvas"); c.width = Math.round(img.width * s); c.height = Math.round(img.height * s);
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        c.toBlob(function (b) { URL.revokeObjectURL(url); resolve(b ? new File([b], "photo.jpg", { type: "image/jpeg" }) : file); }, "image/jpeg", 0.82);
      };
      img.onerror = function () { URL.revokeObjectURL(url); resolve(file); };
      img.src = url;
    });
  }

  function updateButtons() {
    var hasText = input.value.trim().length > 0 || imageInput.files.length > 0;
    btnSend.hidden = !hasText;
    btnMic.hidden = hasText;
    btnVnote.hidden = hasText;
  }
  function autosize() { input.style.height = "auto"; input.style.height = Math.min(input.scrollHeight, 120) + "px"; }
  input.addEventListener("input", function () { autosize(); updateButtons(); });
  input.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey && cfg.enterToSend && !e.isComposing) { e.preventDefault(); form.requestSubmit(); }
  });

  imageInput.addEventListener("change", function () {
    if (imageInput.files.length > 0) { previewImg.src = URL.createObjectURL(imageInput.files[0]); previewRow.style.display = "flex"; }
    updateButtons();
  });
  $("preview-remove").addEventListener("click", function () { imageInput.value = ""; previewRow.style.display = "none"; updateButtons(); });

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    if (sending) return;
    var content = input.value.trim();
    var file = imageInput.files[0];
    if (!content && !file) return;
    sending = true;
    var done = function (fd) {
      fd.append("content", content);
      input.value = ""; imageInput.value = ""; previewRow.style.display = "none"; autosize(); updateButtons();
      post(fd).then(function () { sending = false; });
    };
    var fd = new FormData();
    if (file) { shrinkImage(file).then(function (f) { fd.append("image", f, f.name || "photo.jpg"); done(fd); }); }
    else done(fd);
  });

  /* ---------- stikerlar va emoji ---------- */
  var PACKS = [
    { icon: "😀", items: "😀 😃 😄 😁 😆 😅 😂 🤣 😊 😇 🙂 😉 😍 🥰 😘 😋 😛 😜 🤪 🤗 🤭 🤔 😎 🥳 😏 😴 😭 😡 🥺 🤯 😱 🙄".split(" ") },
    { icon: "❤️", items: "❤️ 🧡 💛 💚 💙 💜 🖤 🤍 💔 💕 💖 🔥 ✨ 👍 👎 👏 🙌 🙏 💪 🤝 ✌️ 🤞 👌 🤟 👋 🫶".split(" ") },
    { icon: "🐶", items: "🐶 🐱 🐭 🐹 🐰 🦊 🐻 🐼 🐨 🐯 🦁 🐮 🐷 🐸 🐵 🐔 🐧 🦄 🐝 🦋 🐢 🐙 🐬 🦈".split(" ") },
    { icon: "🍕", items: "🍎 🍕 🍔 🍟 🌭 🍿 🍩 🍪 🎂 🍫 ☕ 🍺 🎉 🎁 🎈 ⚽ 🏀 🎮 🎵 🚀 🌈 ☀️ 🌙 ⭐".split(" ") }
  ];
  var stTab = "stickers", stPack = 0;
  function renderStickers() {
    var packs = $("sticker-packs"), grid = $("sticker-grid");
    packs.innerHTML = ""; grid.innerHTML = "";
    var items;
    if (stTab === "stickers") {
      PACKS.forEach(function (p, i) {
        var b = document.createElement("button"); b.type = "button"; b.textContent = p.icon;
        b.className = "pack-btn" + (i === stPack ? " active" : ""); b.dataset.pack = i; packs.appendChild(b);
      });
      items = PACKS[stPack].items;
      grid.className = "sticker-grid big";
    } else {
      items = [].concat.apply([], PACKS.map(function (p) { return p.items; }));
      grid.className = "sticker-grid small";
    }
    items.forEach(function (em) {
      var b = document.createElement("button"); b.type = "button"; b.className = "st-item"; b.textContent = em; b.dataset.emoji = em; grid.appendChild(b);
    });
  }
  $("btn-sticker").addEventListener("click", function () {
    var panel = $("sticker-panel"); panel.hidden = !panel.hidden;
    if (!panel.hidden) renderStickers();
  });
  $("sticker-panel").addEventListener("click", function (e) {
    var tab = e.target.closest(".st-tab");
    if (tab) {
      stTab = tab.dataset.tab;
      document.querySelectorAll(".st-tab").forEach(function (b) { b.classList.toggle("active", b === tab); });
      renderStickers(); return;
    }
    var pk = e.target.closest(".pack-btn");
    if (pk) { stPack = +pk.dataset.pack; renderStickers(); return; }
    var it = e.target.closest(".st-item");
    if (!it) return;
    if (stTab === "stickers") {
      var fd = new FormData(); fd.append("sticker", it.dataset.emoji);
      $("sticker-panel").hidden = true;
      post(fd);
    } else {
      var s = input.selectionStart == null ? input.value.length : input.selectionStart;
      input.value = input.value.slice(0, s) + it.dataset.emoji + input.value.slice(input.selectionEnd || s);
      input.focus(); input.selectionStart = input.selectionEnd = s + it.dataset.emoji.length;
      autosize(); updateButtons();
    }
  });

  /* ---------- ovozli xabar ---------- */
  var rec = null;
  function pickMime(list) {
    if (!window.MediaRecorder) return "";
    for (var i = 0; i < list.length; i++) { if (MediaRecorder.isTypeSupported(list[i])) return list[i]; }
    return "";
  }
  function stopStream(stream) { if (stream) stream.getTracks().forEach(function (t) { t.stop(); }); }

  btnMic.addEventListener("click", function () {
    if (rec || !navigator.mediaDevices || !window.MediaRecorder) { if (!window.MediaRecorder) toast(T.micDenied); return; }
    navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
      var mime = pickMime(["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg;codecs=opus"]);
      var mr = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
      var chunks = [], started = Date.now(), cancelled = false;
      rec = { mr: mr, stream: stream, cancel: function () { cancelled = true; } };
      mr.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
      mr.onstop = function () {
        stopStream(stream); clearInterval(rec && rec.timer);
        var dur = Math.round((Date.now() - started) / 1000);
        rec = null; $("rec-bar").hidden = true; form.hidden = false;
        if (cancelled || !chunks.length || dur < 1) return;
        var type = (mr.mimeType || mime || "audio/webm").split(";")[0];
        var ext = type.indexOf("mp4") >= 0 ? "m4a" : type.indexOf("ogg") >= 0 ? "ogg" : "webm";
        var fd = new FormData();
        fd.append("audio", new File(chunks, "voice." + ext, { type: type }));
        fd.append("duration", dur);
        post(fd);
      };
      mr.start(250);
      $("rec-bar").hidden = false; form.hidden = true; $("sticker-panel").hidden = true;
      var timeEl = $("rec-time"); timeEl.textContent = "0:00";
      rec.timer = setInterval(function () {
        var s = (Date.now() - started) / 1000; timeEl.textContent = fmtTime(s);
        if (s >= 300 && rec) rec.mr.stop();
      }, 250);
    }).catch(function () { toast(T.micDenied); });
  });
  $("rec-cancel").addEventListener("click", function () { if (rec) { rec.cancel(); rec.mr.stop(); } });
  $("rec-send").addEventListener("click", function () { if (rec) rec.mr.stop(); });

  /* ---------- dumaloq video xabar ---------- */
  var vn = { stream: null, mr: null, facing: "user", timer: null, cancelled: false };
  var vnOverlay = $("vnote-overlay"), vnPreview = $("vnote-preview"), vnRecordBtn = $("vnote-record");
  function openVnote() {
    if (!navigator.mediaDevices || !window.MediaRecorder) { toast(T.camDenied); return; }
    vnOverlay.hidden = false;
    startVnoteStream();
  }
  function startVnoteStream() {
    stopStream(vn.stream);
    navigator.mediaDevices.getUserMedia({ video: { facingMode: vn.facing, width: { ideal: 480 }, height: { ideal: 480 } }, audio: true }).then(function (stream) {
      vn.stream = stream; vnPreview.srcObject = stream;
    }).catch(function () { vnOverlay.hidden = true; toast(T.camDenied); });
  }
  function closeVnote() {
    clearInterval(vn.timer);
    if (vn.mr && vn.mr.state !== "inactive") { vn.cancelled = true; vn.mr.stop(); }
    stopStream(vn.stream); vn.stream = null; vnPreview.srcObject = null;
    vnOverlay.hidden = true; vnRecordBtn.classList.remove("recording"); $("vnote-time").textContent = "0:00";
    vn.mr = null;
  }
  btnVnote.addEventListener("click", openVnote);
  $("vnote-cancel").addEventListener("click", closeVnote);
  $("vnote-flip").addEventListener("click", function () {
    if (vn.mr && vn.mr.state === "recording") return;
    vn.facing = vn.facing === "user" ? "environment" : "user"; startVnoteStream();
  });
  vnRecordBtn.addEventListener("click", function () {
    if (vn.mr && vn.mr.state === "recording") { vn.mr.stop(); return; }
    if (!vn.stream) return;
    var mime = pickMime(["video/webm;codecs=vp8,opus", "video/webm", "video/mp4"]);
    var mr = mime ? new MediaRecorder(vn.stream, { mimeType: mime, videoBitsPerSecond: 800000 }) : new MediaRecorder(vn.stream);
    var chunks = [], started = Date.now();
    vn.mr = mr; vn.cancelled = false;
    mr.ondataavailable = function (e) { if (e.data && e.data.size) chunks.push(e.data); };
    mr.onstop = function () {
      clearInterval(vn.timer);
      var dur = Math.round((Date.now() - started) / 1000);
      var cancelled = vn.cancelled;
      var type = (mr.mimeType || mime || "video/webm").split(";")[0];
      stopStream(vn.stream); vn.stream = null; vnPreview.srcObject = null;
      vnOverlay.hidden = true; vnRecordBtn.classList.remove("recording"); vn.mr = null;
      if (cancelled || !chunks.length || dur < 1) return;
      var fd = new FormData();
      fd.append("video", new File(chunks, "note." + (type.indexOf("mp4") >= 0 ? "mp4" : "webm"), { type: type }));
      fd.append("duration", dur);
      post(fd);
    };
    mr.start(250);
    vnRecordBtn.classList.add("recording");
    vn.timer = setInterval(function () {
      var s = (Date.now() - started) / 1000; $("vnote-time").textContent = fmtTime(s);
      if (s >= 60 && vn.mr) vn.mr.stop();
    }, 250);
  });

  /* ---------- ovozli xabarni ijro etish ---------- */
  var currentVoice = null;
  function stopVoice(v) {
    if (!v) return;
    var a = v._audio; if (a) a.pause();
    v.classList.remove("playing"); v.querySelector(".voice-play").innerHTML = icon("play");
  }
  function paintProgress(v, ratio) {
    var bars = v.querySelectorAll(".voice-wave i"), n = Math.round(bars.length * ratio);
    bars.forEach(function (b, i) { b.classList.toggle("on", i < n); });
  }
  function toggleVoice(v) {
    if (currentVoice && currentVoice !== v) stopVoice(currentVoice);
    if (!v._audio) {
      var a = new Audio(v.dataset.src); a.preload = "auto"; v._audio = a;
      a.addEventListener("timeupdate", function () {
        var d = (isFinite(a.duration) && a.duration > 0) ? a.duration : (+v.dataset.dur || 1);
        paintProgress(v, a.currentTime / d);
        v.querySelector(".voice-dur").textContent = fmtTime(a.currentTime);
      });
      a.addEventListener("ended", function () {
        stopVoice(v); paintProgress(v, 0); v.querySelector(".voice-dur").textContent = fmtTime(+v.dataset.dur);
      });
    }
    if (v.classList.contains("playing")) { stopVoice(v); return; }
    v._audio.play().then(function () {
      v.classList.add("playing"); v.querySelector(".voice-play").innerHTML = icon("pause"); currentVoice = v;
    }).catch(function () { toast(T.net); });
  }

  /* ---------- tarjima ---------- */
  function toggleTranslate(id) {
    var el = nodes.get(id), m = store.get(id);
    if (!el || !m || !m.content || m.kind !== "text") return;
    var tbox = el.querySelector(".msg-translation");
    if (!tbox) return;
    if (!tbox.hidden) { tbox.hidden = true; return; }
    if (translations.has(id)) { tbox.textContent = translations.get(id); tbox.hidden = false; return; }
    tbox.textContent = T.translating; tbox.hidden = false; tbox.classList.add("loading");
    fetch("/api/translate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text: m.content }) })
      .then(function (r) { return r.json().catch(function () { return {}; }).then(function (d) { return { ok: r.ok, d: d }; }); })
      .then(function (res) {
        tbox.classList.remove("loading");
        if (!res.ok || !res.d.ok) { tbox.hidden = true; toast(res.d.message || T.translateFailed); return; }
        if (res.d.same) { tbox.hidden = true; toast(T.translateSame); return; }
        translations.set(id, res.d.text); tbox.textContent = res.d.text;
      }).catch(function () { tbox.classList.remove("loading"); tbox.hidden = true; toast(T.translateFailed); });
  }

  /* ---------- amallar menyusi (uzoq bosish / o'ng tugma) ---------- */
  var sheet = $("action-sheet"), sheetId = null;
  function openSheet(id) {
    var m = store.get(id); if (!m) return;
    sheetId = id;
    $("action-preview").textContent = (m.author === me ? "" : m.author + ": ") + previewOf(m);
    sheet.querySelector('[data-act="translate"]').hidden = !(m.kind === "text" && m.content);
    sheet.querySelector('[data-act="copy"]').hidden = !(m.kind === "text" && m.content) && m.kind !== "sticker";
    sheet.querySelector('[data-act="delete"]').hidden = m.author !== me || m.kind === "call";
    sheet.querySelector('[data-act="delete"] span').textContent = T.del;
    sheet.hidden = false;
  }
  function closeSheet() { sheet.hidden = true; sheetId = null; }
  sheet.addEventListener("click", function (e) {
    if (e.target === sheet) { closeSheet(); return; }
    var b = e.target.closest(".action-item"); if (!b) return;
    var id = sheetId, m = store.get(id); closeSheet(); if (!m) return;
    if (b.dataset.act === "reply") setReply(m);
    else if (b.dataset.act === "translate") toggleTranslate(id);
    else if (b.dataset.act === "copy") {
      (navigator.clipboard ? navigator.clipboard.writeText(m.content) : Promise.reject()).then(function () { toast(T.copied); }).catch(function () {
        var ta = document.createElement("textarea"); ta.value = m.content; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); toast(T.copied); } catch (err) { /* ignore */ } ta.remove();
      });
    } else if (b.dataset.act === "delete") {
      fetch(apiDelete(id), { method: "POST" }).then(load).catch(function () { toast(T.net); });
    }
  });

  /* ---------- bosish, uzoq bosish, surish ---------- */
  var press = { timer: null, x: 0, y: 0, long: false, row: null, swiping: false, dx: 0 };
  function rowOf(t) { var r = t.closest(".msg-row"); return r && r.dataset.id ? r : null; }
  box.addEventListener("touchstart", function (e) {
    var row = rowOf(e.target); if (!row || e.touches.length !== 1) return;
    press.row = row; press.x = e.touches[0].clientX; press.y = e.touches[0].clientY; press.long = false; press.swiping = false; press.dx = 0;
    clearTimeout(press.timer);
    press.timer = setTimeout(function () { press.long = true; if (navigator.vibrate) navigator.vibrate(15); openSheet(+row.dataset.id); }, 480);
  }, { passive: true });
  box.addEventListener("touchmove", function (e) {
    if (!press.row) return;
    var dx = e.touches[0].clientX - press.x, dy = e.touches[0].clientY - press.y;
    if (Math.abs(dx) > 10 || Math.abs(dy) > 10) clearTimeout(press.timer);
    if (!press.swiping && dx > 12 && Math.abs(dy) < 20 && dx > Math.abs(dy)) press.swiping = true;
    if (press.swiping) {
      press.dx = Math.min(dx, 80);
      press.row.style.transition = "none"; press.row.style.transform = "translateX(" + press.dx + "px)";
    }
  }, { passive: true });
  function endTouch() {
    clearTimeout(press.timer);
    if (press.row && press.swiping) {
      var row = press.row;
      row.style.transition = "transform .18s"; row.style.transform = "";
      if (press.dx >= 55) { var m = store.get(+row.dataset.id); if (m) setReply(m); }
      press.suppressClick = true; setTimeout(function () { press.suppressClick = false; }, 300);
    }
    press.row = null; press.swiping = false;
  }
  box.addEventListener("touchend", endTouch);
  box.addEventListener("touchcancel", endTouch);
  box.addEventListener("contextmenu", function (e) {
    var row = rowOf(e.target); if (!row) return;
    e.preventDefault(); openSheet(+row.dataset.id);
  });

  box.addEventListener("click", function (e) {
    if (press.long) { press.long = false; return; }
    if (press.suppressClick) return;

    var call = e.target.closest(".msg-call");
    if (call) { startCall(call.dataset.call); return; }

    var quick = e.target.closest(".msg-quick-reply");
    if (quick) { var qm = store.get(+quick.closest(".msg-row").dataset.id); if (qm) setReply(qm); return; }

    var rq = e.target.closest(".msg-reply");
    if (rq) {
      var tgt = nodes.get(+rq.dataset.replyId);
      if (tgt) { tgt.scrollIntoView({ behavior: "smooth", block: "center" }); tgt.classList.add("flash"); setTimeout(function () { tgt.classList.remove("flash"); }, 1200); }
      return;
    }

    var voicePlay = e.target.closest(".voice-play");
    if (voicePlay) { toggleVoice(voicePlay.closest(".voice")); return; }
    var wave = e.target.closest(".voice-wave");
    if (wave) {
      var v = wave.closest(".voice");
      if (v._audio && isFinite(v._audio.duration)) {
        var rect = wave.getBoundingClientRect(); v._audio.currentTime = ((e.clientX - rect.left) / rect.width) * v._audio.duration;
      } else toggleVoice(v);
      return;
    }
    var sp = e.target.closest(".voice-speed");
    if (sp) {
      var next = sp.textContent === "1x" ? 1.5 : sp.textContent === "1.5x" ? 2 : 1;
      sp.textContent = (next === 1 ? "1" : next) + "x";
      var vv = sp.closest(".voice"); if (vv._audio) vv._audio.playbackRate = next; vv.dataset.rate = next;
      return;
    }
    var vnote = e.target.closest(".vnote");
    if (vnote) {
      var vid = vnote.querySelector("video");
      document.querySelectorAll(".vnote.playing video").forEach(function (o) { if (o !== vid) { o.pause(); o.closest(".vnote").classList.remove("playing"); } });
      if (vid.paused) { vid.play(); vnote.classList.add("playing"); } else { vid.pause(); vnote.classList.remove("playing"); }
      vid.onended = function () { vnote.classList.remove("playing"); };
      return;
    }
    if (e.target.closest("a, button, img, video, audio")) return;

    // Oddiy matnli xabarni bir marta bosish: tarjima
    var bubble = e.target.closest(".msg-bubble");
    if (bubble) { var row = bubble.closest(".msg-row"); toggleTranslate(+row.dataset.id); }
  });

  /* ---------- qo'ng'iroq boshlash (shaxsiy chat) ---------- */
  function startCall(ckind) {
    if (kind !== "dm") return;
    fetch("/api/call/start", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ to: target, kind: ckind }) })
      .then(function (r) { return r.json().catch(function () { return {}; }); })
      .then(function (d) { if (d.ok) location.href = "/call/" + d.id; else toast(d.message || T.net); })
      .catch(function () { toast(T.net); });
  }
  window.LinkoStartCall = startCall;

  /* ---------- ishga tushirish ---------- */
  updateButtons();
  load();
  setInterval(function () { if (!document.hidden) load(); }, 2000);
  document.addEventListener("visibilitychange", function () { if (!document.hidden) load(); });
})();
