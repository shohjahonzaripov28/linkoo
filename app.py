# Linko - Login/Register tizimi
# Bu Linko ilovasining 1-bosqichi: foydalanuvchi ro'yxatdan o'tishi va tizimga kirishi

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, g
import hashlib
import secrets
import json
import urllib.request
import urllib.parse
import time
import os
import re
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import qrcode
except ImportError:
    qrcode = None

import io
import base64

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from config import ANTHROPIC_API_KEY as CONFIG_API_KEY
except ImportError:
    CONFIG_API_KEY = ""

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", CONFIG_API_KEY)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# ---------- Baza: Render'da PostgreSQL (DATABASE_URL), lokalda SQLite ----------
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

USE_POSTGRES = bool(DATABASE_URL)

if USE_POSTGRES:
    import psycopg2
    import psycopg2.extras
else:
    import sqlite3


class PGCursorWrapper:
    """psycopg2 kursorini sqlite3 kursoriga o'xshatib ko'rsatadi (.lastrowid bilan)"""

    def __init__(self, cur, is_insert):
        self._cur = cur
        self._lastrowid = None
        if is_insert:
            try:
                row = cur.fetchone()
                self._lastrowid = row["id"] if row else None
            except Exception:
                self._lastrowid = None

    def fetchone(self):
        return self._cur.fetchone()

    def fetchall(self):
        return self._cur.fetchall()

    @property
    def lastrowid(self):
        return self._lastrowid


class PGConnWrapper:
    """psycopg2 ulanishini sqlite3.Connection'ga o'xshatib ko'rsatadi,
    shunda qolgan butun kod (conn.execute(...), row["ustun"]) o'zgarmasdan ishlayveradi."""

    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, sql, params=()):
        sql_pg = sql.replace("?", "%s")

        # SQLite'ning "INSERT OR IGNORE" sintaksisini PostgreSQL'ga moslashtirish
        if "INSERT OR IGNORE INTO" in sql_pg.upper():
            sql_pg = re.sub(r"(?i)INSERT OR IGNORE INTO", "INSERT INTO", sql_pg)
            sql_pg = sql_pg.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"

        is_insert = sql_pg.strip().upper().startswith("INSERT")
        if is_insert and "RETURNING" not in sql_pg.upper():
            sql_pg = sql_pg.rstrip().rstrip(";") + " RETURNING id"

        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(sql_pg, params)
        return PGCursorWrapper(cur, is_insert)

    def commit(self):
        self._conn.commit()

    def close(self):
        try:
            self._conn.close()
        except Exception:
            pass

    def rollback(self):
        try:
            self._conn.rollback()
        except Exception:
            pass

app = Flask(__name__)
# Render kabi proksi ortasida to'g'ri https:// manzil olish uchun (QR havolasi uchun muhim)
from werkzeug.middleware.proxy_fix import ProxyFix
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
PAGE_SIZE = 10
MAX_MEDIA_PER_POST = 10
MAX_VIDEO_BYTES = 25 * 1024 * 1024
VIDEO_MIMES = {"mp4": "video/mp4", "m4v": "video/mp4", "mov": "video/quicktime", "webm": "video/webm"}
GOOGLE_CLIENT_ID = "".join(os.environ.get("GOOGLE_CLIENT_ID", "").split())  # ichidagi bo'shliq/yangi qatorlarni ham olib tashlaydi
NICK_RE = re.compile(r"^[A-Za-z0-9_.]{3,24}$")
app.secret_key = os.environ.get("SECRET_KEY", "linko-maxfiy-kalit-2026")

DB_PATH = os.path.join(os.path.dirname(__file__), "linko.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 120 * 1024 * 1024  # bitta so'rov (post) uchun umumiy chegara
# Bir marta kirgan foydalanuvchi 1 yil davomida avtomatik kiradi (chiqish tugmasini bosmaguncha)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=365)
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SECURE"] = bool(os.environ.get("RENDER"))

# ---------- Tillar (i18n) - barcha matnlar translations.py faylida ----------
from translations import LANG_NAMES, TRANSLATIONS
import locations
import catalog

def current_lang():
    lang = session.get("lang", "uz")
    return lang if lang in TRANSLATIONS else "uz"


@app.teardown_appcontext
def close_leftover_connections(exc):
    """Xatolik yuz bergan so'rovda ham baza ulanishlari yopiladi."""
    for conn in g.pop("_open_conns", []):
        try:
            conn.close()
        except Exception:
            pass


def error_response(code, title_key, text_key):
    """Xatolik: /api/ uchun JSON, sahifalar uchun do'stona xatolik sahifasi."""
    if request.path.startswith("/api/"):
        return jsonify({"error": text_key, "message": tr(text_key)}), code
    try:
        # Vaqtinchalik: xatoning qisqa sababi hamma uchun ko'rinadi (aniqlash uchun). Tuzatilgach SHOW_ERRORS=0 qo'ying.
        show = os.environ.get("SHOW_ERRORS", "1") != "0" or (session.get("username") or "").lower() in ADMIN_USERNAMES
        detail = getattr(g, "err_detail", "")[:300] if show else ""
        return render_template("error.html", code=code, title=tr(title_key), text=tr(text_key),
                               logged_in="user_id" in session, active="", detail=detail), code
    except Exception:
        return f"Error {code}", code


@app.errorhandler(413)
def too_large(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "video_too_big", "message": tr("video_too_big")}), 413
    return error_response(413, "err_413_title", "err_413_text")


@app.errorhandler(404)
def not_found(e):
    return error_response(404, "err_404_title", "err_404_text")


@app.errorhandler(405)
def method_not_allowed(e):
    return error_response(405, "err_404_title", "err_404_text")


@app.errorhandler(500)
def server_error(e):
    return error_response(500, "err_500_title", "err_500_text")


@app.errorhandler(Exception)
def unhandled_exception(e):
    """Kutilmagan xatolik: sahifa qotib qolmaydi, do'stona xabar ko'rsatiladi."""
    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return error_response(e.code or 500, "err_500_title", "err_500_text")
    app.logger.exception("Kutilmagan xatolik: %s", e)
    g.err_detail = (type(e).__name__ + ": " + str(e))[:600]
    transient = isinstance(e, psycopg2.OperationalError) if USE_POSTGRES else isinstance(e, sqlite3.OperationalError)
    if transient:
        return error_response(503, "err_503_title", "err_503_text")
    return error_response(500, "err_500_title", "err_500_text")


OPEN_ENDPOINTS = {
    "static", "media", "login", "register", "forgot_password",
    "set_language", "privacy_page", "home", "version", "google_auth", "web_manifest", "favicon",
}


ADMIN_USERNAMES = {
    n.strip().lower() for n in os.environ.get("ADMIN_USERNAMES", "").split(",") if n.strip()
}


def tr(key):
    """Joriy til bo'yicha matn (flash xabarlari uchun)."""
    return TRANSLATIONS[current_lang()].get(key, key)


def is_safe_next(path):
    return bool(path) and path.startswith("/") and not path.startswith("//") and "\\" not in path



# Tarjima uchun tillar (o'z nomi bilan)
TRANSLATE_LANGS = {
    "uz": "O'zbekcha", "ru": "Русский", "en": "English", "zh": "中文", "tr": "Türkçe", "ar": "العربية",
    "ko": "한국어", "ja": "日本語", "es": "Español", "de": "Deutsch", "fr": "Français", "hi": "हिन्दी",
    "kk": "Қазақша", "ky": "Кыргызча", "tg": "Тоҷикӣ", "fa": "فارسی", "az": "Azərbaycanca", "uk": "Українська",
}


# ---------- Foydalanuvchi sozlamalari ----------
PREF_DEFAULTS = {
    "allow_requests": "everyone",   # kontakt so'rovlarini kim yubora oladi
    "who_can_message": "everyone",  # kim yoza oladi
    "notif_sound": True,
    "notif_browser": False,
    "notif_preview": True,
    "notif_calls": True,
    "font_size": "medium",
    "reduce_motion": False,
    "enter_to_send": True,
    "wallpaper": "default",
    "translate_lang": "auto",
    "shrink_images": True,
    "show_online": "everyone",      # online / oxirgi marta ko'rinishini kim ko'ra oladi
    "read_receipts": True,          # "o'qildi" belgisini ko'rsatish
}
PREF_CHOICES = {
    "allow_requests": ("everyone", "nobody"),
    "who_can_message": ("everyone", "contacts"),
    "font_size": ("small", "medium", "large"),
    "wallpaper": ("default", "blue", "green", "sunset"),
    "translate_lang": ("auto",) + tuple(TRANSLATE_LANGS),
    "show_online": ("everyone", "nobody"),
}


def get_prefs(conn, username):
    prefs = dict(PREF_DEFAULTS)
    try:
        row = conn.execute("SELECT data FROM user_settings WHERE username = ?", (username,)).fetchone()
        if row and row["data"]:
            saved = json.loads(row["data"])
            for k, v in saved.items():
                if k in prefs and type(v) == type(prefs[k]):
                    if k in PREF_CHOICES and v not in PREF_CHOICES[k]:
                        continue
                    prefs[k] = v
    except Exception:
        pass
    return prefs


def save_pref(conn, username, key, value):
    if key not in PREF_DEFAULTS or type(value) != type(PREF_DEFAULTS[key]):
        return False
    if key in PREF_CHOICES and value not in PREF_CHOICES[key]:
        return False
    prefs = get_prefs(conn, username)
    prefs[key] = value
    data = json.dumps(prefs)
    row = conn.execute("SELECT id FROM user_settings WHERE username = ?", (username,)).fetchone()
    if row:
        conn.execute("UPDATE user_settings SET data = ? WHERE username = ?", (data, username))
    else:
        conn.execute("INSERT INTO user_settings (username, data) VALUES (?, ?)", (username, data))
    return True


# ---------- Bloklar va maxfiylik ----------
def is_blocked_between(conn, a, b):
    return bool(conn.execute(
        "SELECT 1 FROM user_blocks WHERE (blocker = ? AND blocked = ?) OR (blocker = ? AND blocked = ?)",
        (a, b, b, a),
    ).fetchone())


def can_message(conn, sender, receiver):
    """(ruxsat, xato_kaliti). Blok va maxfiylik sozlamalarini tekshiradi."""
    if is_blocked_between(conn, sender, receiver):
        return False, "chat_blocked_msg"
    if get_prefs(conn, receiver)["who_can_message"] == "contacts":
        ok = conn.execute(
            "SELECT 1 FROM contacts WHERE username = ? AND contact_username = ?", (receiver, sender)
        ).fetchone()
        if not ok:
            return False, "chat_privacy_msg"
    return True, ""


# ---------- Qurilmalar (sessiyalar) ----------
def parse_user_agent(ua):
    ua = ua or ""
    if "Edg/" in ua: browser = "Edge"
    elif "OPR/" in ua or "Opera" in ua: browser = "Opera"
    elif "YaBrowser" in ua: browser = "Yandex"
    elif "Firefox/" in ua: browser = "Firefox"
    elif "Chrome/" in ua or "CriOS" in ua: browser = "Chrome"
    elif "Safari/" in ua: browser = "Safari"
    else: browser = "Browser"
    if "iPhone" in ua: os_name = "iPhone"
    elif "iPad" in ua: os_name = "iPad"
    elif "Android" in ua: os_name = "Android"
    elif "Windows" in ua: os_name = "Windows"
    elif "Mac OS" in ua or "Macintosh" in ua: os_name = "macOS"
    elif "Linux" in ua: os_name = "Linux"
    else: os_name = "Device"
    return f"{browser} · {os_name}"


def start_session_record(conn, username):
    token = secrets.token_urlsafe(24)
    now = int(time.time())
    conn.execute(
        "INSERT INTO user_sessions (username, token, user_agent, ip, created_ts, last_seen_ts) VALUES (?, ?, ?, ?, ?, ?)",
        (username, token, (request.headers.get("User-Agent") or "")[:300], request.remote_addr or "", now, now),
    )
    session["sid"] = token
    return token


@app.before_request
def validate_session_user():
    """Har so'rovda: foydalanuvchi bazada bormi, bloklanmaganmi, adminmi, qurilma chiqarib yuborilmaganmi - tekshiradi.
    Kirmagan foydalanuvchi sahifaga kirmoqchi bo'lsa, login'dan keyin shu sahifaga qaytariladi."""
    g.is_admin = False
    if request.endpoint in OPEN_ENDPOINTS or request.endpoint is None:
        return

    if "user_id" not in session:
        if request.method == "GET" and not request.path.startswith("/api/"):
            return redirect(url_for("login", next=request.full_path.rstrip("?")))
        return

    conn = get_db()
    row = conn.execute(
        """SELECT u.id, u.username, u.avatar_letter, u.nickname, u.avatar_file, u.is_admin, u.last_seen_ts, b.id AS blocked_id
           FROM users u LEFT JOIN blocked_users b ON b.username = u.username
           WHERE u.username = ?""",
        (session.get("username", ""),),
    ).fetchone()
    if not row:
        session.clear()
        return
    if row["blocked_id"]:
        session.clear()
        if request.path.startswith("/api/"):
            return jsonify({"error": "blocked"}), 403
        flash(tr("blocked_msg"))
        return redirect(url_for("login"))

    # Qurilma (sessiya) tekshiruvi: boshqa qurilmadan chiqarib yuborilgan bo'lsa, kirish bekor qilinadi
    now = int(time.time())
    sid = session.get("sid")
    if sid:
        srow = conn.execute("SELECT id, last_seen_ts FROM user_sessions WHERE token = ?", (sid,)).fetchone()
        if not srow:
            session.clear()
            if request.path.startswith("/api/"):
                return jsonify({"error": "auth"}), 401
            return redirect(url_for("login"))
        if now - int(srow["last_seen_ts"] or 0) > 300:
            conn.execute("UPDATE user_sessions SET last_seen_ts = ? WHERE id = ?", (now, srow["id"]))
            conn.commit()
    else:
        start_session_record(conn, row["username"])  # eski sessiyalar uchun yozuv yaratamiz
        conn.commit()

    if now - int(row["last_seen_ts"] or 0) >= 20:  # online holati
        conn.execute("UPDATE users SET last_seen_ts = ? WHERE id = ?", (now, row["id"]))
        conn.commit()

    session.permanent = True  # 1 yil avtomatik kirish
    session["user_id"] = row["id"]
    session["avatar_letter"] = row["avatar_letter"]
    session["nickname"] = row["nickname"]
    session["avatar_file"] = row["avatar_file"]
    g.is_admin = bool(row["is_admin"]) or row["username"].lower() in ADMIN_USERNAMES


def admin_required():
    """Admin bo'lmasa False qaytaradi."""
    return "user_id" in session and getattr(g, "is_admin", False)


def get_conversations(conn, me, limit=50):
    """Shaxsiy suhbatlar ro'yxati: oxirgi xabar, vaqt va o'qilmagan xabarlar soni bilan (yangisi tepada)."""
    pairs = conn.execute(
        """SELECT partner, MAX(mid) AS last_id FROM (
             SELECT id AS mid, CASE WHEN sender = ? THEN receiver ELSE sender END AS partner
             FROM private_messages WHERE sender = ? OR receiver = ?
           ) AS chat_pairs GROUP BY partner ORDER BY last_id DESC LIMIT ?""",
        (me, me, me, limit),
    ).fetchall()
    if not pairs:
        return []

    unread = {
        r["sender"]: r["c"]
        for r in conn.execute(
            "SELECT sender, COUNT(*) AS c FROM private_messages WHERE receiver = ? AND is_read = 0 GROUP BY sender",
            (me,),
        ).fetchall()
    }
    ids = [p["last_id"] for p in pairs]
    marks = ",".join("?" for _ in ids)
    last_msgs = {
        r["id"]: r
        for r in conn.execute(
            f"SELECT id, sender, content, image_file, media_kind, created_at, created_ts FROM private_messages WHERE id IN ({marks})",
            tuple(ids),
        ).fetchall()
    }
    names = [p["partner"] for p in pairs]
    nmarks = ",".join("?" for _ in names)
    users = {
        r["username"]: r
        for r in conn.execute(
            f"SELECT username, avatar_letter, avatar_file, nickname, last_seen_ts FROM users WHERE username IN ({nmarks})",
            tuple(names),
        ).fetchall()
    }
    peer_prefs = bulk_prefs(conn, names)

    result = []
    for p in pairs:
        u = users.get(p["partner"])
        if not u:
            continue
        m = last_msgs.get(p["last_id"])
        text = (m["content"] or "")[:40] if m else ""
        mk = (m["media_kind"] if m else None) or ("image" if (m and m["image_file"]) else "text")
        if mk == "audio":
            text = "🎤 " + tr("msg_voice")
        elif mk == "video":
            text = "🎥 " + tr("msg_video_note")
        elif mk == "call":
            text = "📞 " + tr("call_title")
        elif mk == "order":
            text = "🛒 " + tr("order_title")
        pres = presence_info(conn, me, u["username"], peer_prefs.get(u["username"]), u["last_seen_ts"])
        result.append({
            "kind": "dm",
            "ts": int(m["created_ts"] or 0) if m else 0,
            "online": bool(pres and pres["online"]),
            "username": u["username"],
            "avatar_letter": u["avatar_letter"],
            "avatar_file": u["avatar_file"],
            "nickname": u["nickname"],
            "unread": unread.get(u["username"], 0),
            "preview": text,
            "has_image": bool(m and m["image_file"] and not m["content"] and mk == "image"),
            "mine": bool(m and m["sender"] == me),
            "time": m["created_at"] if m else "",
        })
    return result


def muted_keys(conn, me):
    try:
        return {r["chat_key"] for r in conn.execute("SELECT chat_key FROM chat_mutes WHERE username = ?", (me,)).fetchall()}
    except Exception:
        return set()


def group_unread_map(conn, me):
    """{group_id: o'qilmagan xabarlar soni} (o'zimniki hisobga olinmaydi)."""
    rows = conn.execute(
        """SELECT gm.group_id AS gid, COUNT(*) AS c FROM group_messages gm
           JOIN group_members m ON m.group_id = gm.group_id AND m.username = ?
           WHERE gm.id > COALESCE(m.last_read_id, 0) AND gm.username != ?
           GROUP BY gm.group_id""",
        (me, me),
    ).fetchall()
    return {r["gid"]: r["c"] for r in rows}


def count_unread(conn, me):
    """Menyudagi qizil raqam: shaxsiy + guruh/kanal xabarlari (ovozsiz qilingan chatlar hisobga olinmaydi)."""
    muted = muted_keys(conn, me)
    total = 0
    for r in conn.execute(
        "SELECT sender, COUNT(*) AS c FROM private_messages WHERE receiver = ? AND is_read = 0 GROUP BY sender", (me,)
    ).fetchall():
        if "dm:" + r["sender"] not in muted:
            total += r["c"]
    for gid, c in group_unread_map(conn, me).items():
        if "g:%s" % gid not in muted:
            total += c
    return total


def bulk_prefs(conn, names):
    names = list(set(names))
    out = {n: dict(PREF_DEFAULTS) for n in names}
    if not names:
        return out
    marks = ",".join("?" for _ in names)
    for r in conn.execute(f"SELECT username, data FROM user_settings WHERE username IN ({marks})", tuple(names)).fetchall():
        try:
            saved = json.loads(r["data"] or "{}")
        except Exception:
            continue
        for k, v in saved.items():
            if k in PREF_DEFAULTS and type(v) == type(PREF_DEFAULTS[k]):
                if k in PREF_CHOICES and v not in PREF_CHOICES[k]:
                    continue
                out[r["username"]][k] = v
    return out


ONLINE_WINDOW = 45  # soniya


def presence_text(ts):
    ts = int(ts or 0)
    if not ts:
        return {"online": False, "text": tr("last_seen_long_ago")}
    if int(time.time()) - ts < ONLINE_WINDOW:
        return {"online": True, "text": tr("status_online")}
    return {"online": False, "text": tr("last_seen_at").replace("{t}", time_ago(ts))}


def presence_info(conn, viewer, username, prefs=None, last_seen_ts=None):
    """Online / oxirgi marta (maxfiylik sozlamasini hisobga olib). Yashirin bo'lsa None."""
    if viewer == username:
        return {"online": True, "text": tr("status_online")}
    if prefs is None:
        prefs = get_prefs(conn, username)
    if prefs["show_online"] == "nobody":
        return None
    if last_seen_ts is None:
        row = conn.execute("SELECT last_seen_ts FROM users WHERE username = ?", (username,)).fetchone()
        last_seen_ts = row["last_seen_ts"] if row else 0
    return presence_text(last_seen_ts)


# ---------- Yangi layk va izohlar (feed faolligi) ----------
def feed_new_counts(conn, me):
    u = conn.execute("SELECT seen_like_id, seen_comment_id FROM users WHERE username = ?", (me,)).fetchone()
    if not u:
        return {"likes": 0, "comments": 0, "total": 0}
    likes = conn.execute(
        """SELECT COUNT(*) AS c FROM likes l JOIN posts p ON p.id = l.post_id
           WHERE p.username = ? AND l.username != ? AND l.id > ?""",
        (me, me, u["seen_like_id"] or 0),
    ).fetchone()["c"]
    comments = conn.execute(
        """SELECT COUNT(*) AS c FROM post_comments c JOIN posts p ON p.id = c.post_id
           WHERE p.username = ? AND c.username != ? AND c.id > ?""",
        (me, me, u["seen_comment_id"] or 0),
    ).fetchone()["c"]
    return {"likes": likes, "comments": comments, "total": likes + comments}


@app.route("/api/unread")
def api_unread():
    if "user_id" not in session:
        return jsonify({"total": 0}), 401
    me = session["username"]
    conn = get_db()
    total = count_unread(conn, me)
    call = None
    latest = None
    try:
        expire_calls(conn)
        call = incoming_call_for(conn, me)
        if total:
            muted = muted_keys(conn, me)
            row = None
            for cand in conn.execute(
                "SELECT id, sender, content, media_kind FROM private_messages WHERE receiver = ? AND is_read = 0 ORDER BY id DESC LIMIT 8",
                (me,),
            ).fetchall():
                if "dm:" + cand["sender"] not in muted:
                    row = cand
                    break
            if row:
                prefs = get_prefs(conn, me)
                mk = row["media_kind"]
                text = row["content"] or ""
                if mk == "audio":
                    text = "🎤 " + tr("msg_voice")
                elif mk == "video":
                    text = "🎥 " + tr("msg_video_note")
                elif mk == "call":
                    text = "📞 " + tr("call_title")
                elif mk == "order":
                    text = "🛒 " + tr("order_title")
                elif mk == "image" or (mk is None and not text):
                    text = "📷 " + tr("photo_msg")
                latest = {"id": row["id"], "from": row["sender"], "text": text[:80] if prefs["notif_preview"] else ""}
    except Exception:
        call = None
    feed = 0
    try:
        feed = feed_new_counts(conn, me)["total"]
    except Exception:
        feed = 0
    conn.close()
    return jsonify({"total": total, "call": call, "latest": latest, "feed": feed})



@app.url_defaults
def static_cache_bust(endpoint, values):
    """Telefon brauzeri eski style.css / shop.js ni ushlab qolmasin: fayl o'zgarganda havola ham o'zgaradi"""
    if endpoint == "static" and "v" not in values and values.get("filename"):
        try:
            values["v"] = int(os.path.getmtime(os.path.join(app.static_folder, values["filename"])))
        except OSError:
            pass

@app.context_processor
def inject_translations():
    lang = current_lang()
    unread_total = 0
    feed_new_total = 0
    prefs = dict(PREF_DEFAULTS)
    if "user_id" in session and request.endpoint not in OPEN_ENDPOINTS:
        try:
            conn = get_db()
            unread_total = count_unread(conn, session["username"])
            feed_new_total = feed_new_counts(conn, session["username"])["total"]
            prefs = get_prefs(conn, session["username"])
            conn.close()
        except Exception:
            unread_total = 0
    return dict(t=TRANSLATIONS[lang], lang=lang, langs=LANG_NAMES, unread_total=unread_total, prefs=prefs,
                feed_new_total=feed_new_total, translate_langs=TRANSLATE_LANGS,
                is_admin=getattr(g, "is_admin", False),
                google_client_id=GOOGLE_CLIENT_ID)


@app.route("/set-language/<lang_code>")
def set_language(lang_code):
    if lang_code in TRANSLATIONS:
        session["lang"] = lang_code
    return redirect(request.referrer or url_for("login"))


# Tez-tez qidiriladigan ustunlarga indeks - so'rovlarni tezlashtiradi
INDEX_STATEMENTS = [
    "CREATE INDEX IF NOT EXISTS idx_users_nickname ON users (nickname)",
    "CREATE INDEX IF NOT EXISTS idx_posts_username ON posts (username)",
    "CREATE INDEX IF NOT EXISTS idx_products_seller ON products (seller_username)",
    "CREATE INDEX IF NOT EXISTS idx_likes_post ON likes (post_id)",
    "CREATE INDEX IF NOT EXISTS idx_cart_username ON cart_items (username)",
    "CREATE INDEX IF NOT EXISTS idx_pm_sender ON private_messages (sender)",
    "CREATE INDEX IF NOT EXISTS idx_pm_receiver ON private_messages (receiver)",
    "CREATE INDEX IF NOT EXISTS idx_groupmembers_group ON group_members (group_id)",
    "CREATE INDEX IF NOT EXISTS idx_groupmembers_user ON group_members (username)",
    "CREATE INDEX IF NOT EXISTS idx_groupmsg_group ON group_messages (group_id)",
    "CREATE INDEX IF NOT EXISTS idx_contacts_username ON contacts (username)",
    "CREATE INDEX IF NOT EXISTS idx_contactreq_to ON contact_requests (to_username)",
    "CREATE INDEX IF NOT EXISTS idx_contactreq_from ON contact_requests (from_username)",
]


def get_db():
    """Bazaga ulanish yaratadi - DATABASE_URL bo'lsa PostgreSQL, bo'lmasa lokal SQLite"""
    if USE_POSTGRES:
        conn = PGConnWrapper(psycopg2.connect(DATABASE_URL))
    else:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
    # So'rov tugaganda yopilmay qolgan ulanishlarni teardown'da yopamiz (server qotib qolmasligi uchun)
    try:
        g.setdefault("_open_conns", []).append(conn)
    except RuntimeError:
        pass  # Flask konteksti tashqarisida (init_db) - o'zimiz yopamiz
    return conn


def ensure_feed_tables(conn):
    """Feed uchun jadvallar: ko'p media, izohlar, ko'rishlar, ulashishlar (ikkala baza turi uchun)."""
    pk = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    conn.execute(f"""CREATE TABLE IF NOT EXISTS post_media (
        id {pk}, post_id INTEGER NOT NULL, filename TEXT NOT NULL, kind TEXT NOT NULL, position INTEGER NOT NULL DEFAULT 0)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS post_comments (
        id {pk}, post_id INTEGER NOT NULL, username TEXT NOT NULL, content TEXT NOT NULL,
        created_at TEXT NOT NULL, created_ts BIGINT)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS post_views (
        id {pk}, post_id INTEGER NOT NULL, username TEXT NOT NULL, UNIQUE(post_id, username))""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS post_shares (
        id {pk}, post_id INTEGER NOT NULL, username TEXT NOT NULL, created_ts BIGINT)""")
    if USE_POSTGRES:
        conn.execute("ALTER TABLE posts ADD COLUMN IF NOT EXISTS created_ts BIGINT")
    else:
        cols = [row["name"] for row in conn.execute("PRAGMA table_info(posts)").fetchall()]
        if "created_ts" not in cols:
            conn.execute("ALTER TABLE posts ADD COLUMN created_ts BIGINT")
    for stmt in (
        "CREATE INDEX IF NOT EXISTS idx_post_media_post ON post_media (post_id)",
        "CREATE INDEX IF NOT EXISTS idx_post_comments_post ON post_comments (post_id)",
        "CREATE INDEX IF NOT EXISTS idx_post_views_post ON post_views (post_id)",
        "CREATE INDEX IF NOT EXISTS idx_post_shares_post ON post_shares (post_id)",
    ):
        conn.execute(stmt)


def ensure_google_columns(conn):
    """Google bilan kirish uchun users jadvaliga email va google_sub ustunlari."""
    if USE_POSTGRES:
        conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email TEXT")
        conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub TEXT")
    else:
        cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
        if "email" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
        if "google_sub" not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_sub ON users(google_sub)")


def add_column_if_missing(conn, table, column, coltype):
    if USE_POSTGRES:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {coltype}")
    else:
        cols = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]
        if column not in cols:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")


def ensure_extra_tables(conn):
    """Chat (ovoz/video/reply/stiker), qo'ng'iroq, sozlamalar, bloklar, qurilmalar uchun jadvallar va ustunlar."""
    pk = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    conn.execute(f"""CREATE TABLE IF NOT EXISTS user_settings (
        id {pk}, username TEXT UNIQUE NOT NULL, data TEXT NOT NULL)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS user_blocks (
        id {pk}, blocker TEXT NOT NULL, blocked TEXT NOT NULL, UNIQUE(blocker, blocked))""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS user_sessions (
        id {pk}, username TEXT NOT NULL, token TEXT UNIQUE NOT NULL, user_agent TEXT, ip TEXT,
        created_ts BIGINT NOT NULL, last_seen_ts BIGINT NOT NULL)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS calls (
        id {pk}, caller TEXT NOT NULL, callee TEXT NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL,
        created_ts BIGINT NOT NULL, answered_ts BIGINT, ended_ts BIGINT, last_ping BIGINT)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS call_signals (
        id {pk}, call_id INTEGER NOT NULL, to_user TEXT NOT NULL, sig_type TEXT NOT NULL,
        payload TEXT NOT NULL, created_ts BIGINT NOT NULL)""")
    for table in ("private_messages", "group_messages"):
        add_column_if_missing(conn, table, "media_kind", "TEXT")
        add_column_if_missing(conn, table, "reply_to", "INTEGER")
        add_column_if_missing(conn, table, "duration", "INTEGER")
    add_column_if_missing(conn, "users", "password_set", "INTEGER DEFAULT 1")
    for stmt in (
        "CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions (username)",
        "CREATE INDEX IF NOT EXISTS idx_calls_callee ON calls (callee, status)",
        "CREATE INDEX IF NOT EXISTS idx_call_signals_call ON call_signals (call_id, to_user, id)",
        "CREATE INDEX IF NOT EXISTS idx_user_blocks_blocker ON user_blocks (blocker)",
    ):
        conn.execute(stmt)


def column_exists(conn, table, column):
    if USE_POSTGRES:
        return bool(conn.execute(
            "SELECT 1 FROM information_schema.columns WHERE table_name = ? AND column_name = ?", (table, column)
        ).fetchone())
    return column in [row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def ensure_v9_tables(conn):
    """v9: guruh/kanal rollari, o'qildi/online, feed faolligi, bio, biznes akkaunt, do'kon, buyurtmalar."""
    pk = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    first_seen = not column_exists(conn, "users", "seen_like_id")
    first_read = not column_exists(conn, "group_members", "last_read_id")
    for col, typ in (("bio", "TEXT"), ("last_seen_ts", "BIGINT"), ("account_type", "TEXT DEFAULT 'personal'"),
                     ("business_name", "TEXT"), ("phone", "TEXT"), ("country", "TEXT"), ("region", "TEXT"),
                     ("district", "TEXT"), ("seen_like_id", "INTEGER DEFAULT 0"), ("seen_comment_id", "INTEGER DEFAULT 0")):
        add_column_if_missing(conn, "users", col, typ)
    for col, typ in (("kind", "TEXT DEFAULT 'group'"), ("description", "TEXT"), ("avatar_file", "TEXT"),
                     ("is_public", "INTEGER DEFAULT 0"), ("invite_code", "TEXT"), ("post_mode", "TEXT DEFAULT 'all'")):
        add_column_if_missing(conn, "groups", col, typ)
    add_column_if_missing(conn, "group_members", "role", "TEXT DEFAULT 'member'")
    add_column_if_missing(conn, "group_members", "last_read_id", "INTEGER DEFAULT 0")
    for table in ("private_messages", "group_messages"):
        add_column_if_missing(conn, table, "created_ts", "BIGINT")
    add_column_if_missing(conn, "products", "channel_id", "INTEGER")
    add_column_if_missing(conn, "products", "colors", "TEXT")
    add_column_if_missing(conn, "products", "sizes", "TEXT")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS product_media (
        id {pk}, product_id INTEGER NOT NULL, filename TEXT NOT NULL, position INTEGER NOT NULL DEFAULT 0)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS cart_lines (
        id {pk}, username TEXT NOT NULL, product_id INTEGER NOT NULL, qty INTEGER NOT NULL DEFAULT 1,
        color TEXT NOT NULL DEFAULT '', size TEXT NOT NULL DEFAULT '', UNIQUE(username, product_id, color, size))""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS orders (
        id {pk}, buyer TEXT NOT NULL, seller TEXT NOT NULL, total INTEGER NOT NULL DEFAULT 0,
        country TEXT, region TEXT, district TEXT, address TEXT, phone TEXT, status TEXT NOT NULL DEFAULT 'new',
        created_ts BIGINT NOT NULL)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS order_items (
        id {pk}, order_id INTEGER NOT NULL, product_id INTEGER, title TEXT NOT NULL, price INTEGER NOT NULL,
        qty INTEGER NOT NULL, color TEXT, size TEXT)""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS chat_mutes (
        id {pk}, username TEXT NOT NULL, chat_key TEXT NOT NULL, UNIQUE(username, chat_key))""")
    # Guruh yaratuvchisi - ega
    conn.execute(
        """UPDATE group_members SET role = 'owner'
           WHERE (role IS NULL OR role = 'member')
             AND username = (SELECT created_by FROM groups WHERE groups.id = group_members.group_id)"""
    )
    conn.execute("UPDATE group_members SET role = 'member' WHERE role IS NULL")
    if first_seen:  # eski layk/izohlar "yangi" hisoblanmasin
        conn.execute("UPDATE users SET seen_like_id = (SELECT COALESCE(MAX(id), 0) FROM likes), "
                     "seen_comment_id = (SELECT COALESCE(MAX(id), 0) FROM post_comments)")
    if first_read:  # eski guruh xabarlari o'qilmagan bo'lib ko'rinmasin
        conn.execute("UPDATE group_members SET last_read_id = "
                     "COALESCE((SELECT MAX(id) FROM group_messages WHERE group_id = group_members.group_id), 0)")
    for stmt in (
        "CREATE INDEX IF NOT EXISTS idx_product_media_product ON product_media (product_id)",
        "CREATE INDEX IF NOT EXISTS idx_cart_lines_user ON cart_lines (username)",
        "CREATE INDEX IF NOT EXISTS idx_orders_seller ON orders (seller)",
        "CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members (username)",
        "CREATE INDEX IF NOT EXISTS idx_group_messages_group ON group_messages (group_id, id)",
        "CREATE INDEX IF NOT EXISTS idx_products_channel ON products (channel_id)",
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_groups_invite ON groups (invite_code)",
    ):
        conn.execute(stmt)


def slugify_handle(text):
    base = re.sub(r"[^a-z0-9_.]", "", (text or "").lower().replace(" ", "_").replace("-", "_"))
    return base.strip("_.")[:30]


def unique_handle(conn, base, exclude_username=None):
    base = slugify_handle(base)
    if len(base) < 3:
        base = (base + "shop")[:30] if base else "shop"
    handle, n = base, 1
    while True:
        row = conn.execute("SELECT username FROM stores WHERE handle = ?", (handle,)).fetchone()
        if not row or (exclude_username and row["username"] == exclude_username):
            return handle
        n += 1
        suffix = str(n)
        handle = base[: 30 - len(suffix)] + suffix


def ensure_v10_tables(conn):
    """v10: do'kon profillari, kategoriyalar katalogi, ombor, chegirma, buyurtma holatlari."""
    pk = "SERIAL PRIMARY KEY" if USE_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
    conn.execute(f"""CREATE TABLE IF NOT EXISTS stores (
        id {pk}, username TEXT UNIQUE NOT NULL, name TEXT NOT NULL, handle TEXT UNIQUE NOT NULL,
        logo_file TEXT, banner_file TEXT, description TEXT, category TEXT, phone TEXT,
        country TEXT, region TEXT, district TEXT, address TEXT, hours TEXT, telegram TEXT, instagram TEXT,
        created_ts BIGINT NOT NULL)""")
    for table, col, typ in (
        ("products", "category", "TEXT"), ("products", "subcategory", "TEXT"), ("products", "old_price", "INTEGER"),
        ("products", "stock", "INTEGER"), ("products", "brand", "TEXT"), ("products", "status", "TEXT DEFAULT 'active'"),
        ("products", "views", "INTEGER DEFAULT 0"), ("products", "sold", "INTEGER DEFAULT 0"), ("products", "created_ts", "BIGINT"),
        ("orders", "updated_ts", "BIGINT"), ("orders", "note", "TEXT"), ("order_items", "image_file", "TEXT"),
    ):
        add_column_if_missing(conn, table, col, typ)
    conn.execute("UPDATE products SET status = 'active' WHERE status IS NULL")
    conn.execute("UPDATE products SET views = 0 WHERE views IS NULL")
    conn.execute("UPDATE products SET sold = 0 WHERE sold IS NULL")
    conn.execute("UPDATE products SET category = 'other' WHERE category IS NULL OR category = ''")
    for stmt in (
        "CREATE INDEX IF NOT EXISTS idx_products_seller ON products (seller_username)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products (category, subcategory)",
        "CREATE INDEX IF NOT EXISTS idx_stores_user ON stores (username)",
        "CREATE INDEX IF NOT EXISTS idx_orders_buyer ON orders (buyer)",
    ):
        conn.execute(stmt)
    # v9 dagi biznes akkauntlar uchun do'kon profili yaratiladi
    for u in conn.execute(
        """SELECT username, business_name, phone, country, region, district FROM users
           WHERE account_type = 'business' AND username NOT IN (SELECT username FROM stores)"""
    ).fetchall():
        name = (u["business_name"] or u["username"])[:40]
        conn.execute(
            "INSERT INTO stores (username, name, handle, phone, country, region, district, created_ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (u["username"], name, unique_handle(conn, name or u["username"]), u["phone"], u["country"], u["region"], u["district"], int(time.time())),
        )


def init_db():
    """Baza va jadvallarni birinchi ishga tushganda avtomatik yaratadi"""
    if USE_POSTGRES:
        init_db_postgres()
    else:
        init_db_sqlite()


def init_db_postgres():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_letter TEXT NOT NULL,
            nickname TEXT,
            avatar_file TEXT,
            security_answer_hash TEXT,
            terms_accepted_at TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS private_messages (
            id SERIAL PRIMARY KEY,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            content TEXT NOT NULL,
            image_file TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            avatar_letter TEXT NOT NULL,
            content TEXT,
            image_file TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id SERIAL PRIMARY KEY,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            UNIQUE(post_id, username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            seller_username TEXT NOT NULL,
            seller_avatar TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            image_file TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            UNIQUE(username, product_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            avatar_letter TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id SERIAL PRIMARY KEY,
            group_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            UNIQUE(group_id, username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS group_messages (
            id SERIAL PRIMARY KEY,
            group_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            image_file TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contact_requests (
            id SERIAL PRIMARY KEY,
            from_username TEXT NOT NULL,
            to_username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(from_username, to_username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            contact_username TEXT NOT NULL,
            UNIQUE(username, contact_username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_images (
            id SERIAL PRIMARY KEY,
            filename TEXT UNIQUE NOT NULL,
            mimetype TEXT NOT NULL,
            data BYTEA NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blocked_users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            blocked_at TEXT NOT NULL
        )
    """)
    # Eski bazalarda bo'lmagan ustunlarni qo'shamiz (PostgreSQL'da xavfsiz, allaqachon bo'lsa o'tkazib yuboradi)
    conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin INTEGER DEFAULT 0")
    # Eski xabarlar "o'qilgan" hisoblanadi (DEFAULT 1), yangilari 0 bilan yoziladi
    conn.execute("ALTER TABLE private_messages ADD COLUMN IF NOT EXISTS is_read INTEGER DEFAULT 1")

    for idx_sql in INDEX_STATEMENTS:
        conn.execute(idx_sql)
    ensure_feed_tables(conn)
    ensure_google_columns(conn)
    ensure_extra_tables(conn)
    ensure_v9_tables(conn)
    ensure_v10_tables(conn)

    conn.commit()
    conn.close()


def init_db_sqlite():
    """Baza va jadvalni birinchi marta yaratadi (lokal sinov uchun)"""
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            avatar_letter TEXT NOT NULL
        )
    """)

    # Eski bazalarda "nickname" ustuni bo'lmasligi mumkin - shu yerda qo'shamiz
    existing_cols = [row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()]
    if "nickname" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN nickname TEXT")
    if "avatar_file" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN avatar_file TEXT")
    if "security_answer_hash" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN security_answer_hash TEXT")
    if "terms_accepted_at" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN terms_accepted_at TEXT")
    if "is_admin" not in existing_cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER DEFAULT 0")

    # private_messages va group_messages jadvallari mavjud bo'lsa, image_file ustunini qo'shamiz
    conn.execute("""
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    pm_cols = [row["name"] for row in conn.execute("PRAGMA table_info(private_messages)").fetchall()]
    if "image_file" not in pm_cols:
        conn.execute("ALTER TABLE private_messages ADD COLUMN image_file TEXT")
    if "is_read" not in pm_cols:
        conn.execute("ALTER TABLE private_messages ADD COLUMN is_read INTEGER DEFAULT 1")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            avatar_letter TEXT NOT NULL,
            content TEXT,
            image_file TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            UNIQUE(post_id, username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            seller_username TEXT NOT NULL,
            seller_avatar TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            price INTEGER NOT NULL,
            image_file TEXT,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            UNIQUE(username, product_id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            avatar_letter TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            UNIQUE(group_id, username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    gm_cols = [row["name"] for row in conn.execute("PRAGMA table_info(group_messages)").fetchall()]
    if "image_file" not in gm_cols:
        conn.execute("ALTER TABLE group_messages ADD COLUMN image_file TEXT")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS contact_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_username TEXT NOT NULL,
            to_username TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(from_username, to_username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            contact_username TEXT NOT NULL,
            UNIQUE(username, contact_username)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            mimetype TEXT NOT NULL,
            data BLOB NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS blocked_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            blocked_at TEXT NOT NULL
        )
    """)

    for idx_sql in INDEX_STATEMENTS:
        conn.execute(idx_sql)
    ensure_feed_tables(conn)
    ensure_google_columns(conn)
    ensure_extra_tables(conn)
    ensure_v9_tables(conn)
    ensure_v10_tables(conn)

    conn.commit()
    conn.close()


def save_image_to_db(conn, file_storage, prefix="", avatar=False):
    """Rasm faylini kichraytirib/siqib bazaga saqlaydi va generatsiya qilingan nomini qaytaradi"""
    safe_name = secure_filename(file_storage.filename)
    unique_name = f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{safe_name}"
    mimetype = file_storage.mimetype or "image/jpeg"

    max_dim = 480 if avatar else 1280
    data = None

    if Image is not None:
        try:
            img = Image.open(file_storage.stream)
            img = img.convert("RGB")
            img.thumbnail((max_dim, max_dim), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=82, optimize=True)
            data = buf.getvalue()
            mimetype = "image/jpeg"
        except Exception:
            data = None

    if data is None:
        # Pillow mavjud bo'lmasa yoki rasmni o'qiy olmasa (masalan animatsion GIF),
        # original faylni o'zgarishsiz saqlaymiz
        file_storage.stream.seek(0)
        data = file_storage.read()

    db_data = psycopg2.Binary(data) if USE_POSTGRES else data
    conn.execute(
        "INSERT INTO uploaded_images (filename, mimetype, data, created_at) VALUES (?, ?, ?, ?)",
        (unique_name, mimetype, db_data, datetime.now().strftime("%d.%m.%Y %H:%M")),
    )
    return unique_name


def delete_image_from_db(conn, filename):
    """Bazadagi rasmni o'chiradi (agar mavjud bo'lsa)"""
    if not filename:
        return
    conn.execute("DELETE FROM uploaded_images WHERE filename = ?", (filename,))


def hash_password(password):
    """Parolni oddiy hash qilish (xavfsizlik uchun)"""
    return hashlib.sha256(password.encode()).hexdigest()


APP_VERSION = "linko-2026-10-06-v8"


@app.route("/version")
def version():
    """Render'da qaysi kod versiyasi ishlayotganini ko'rish uchun."""
    return jsonify({"version": APP_VERSION, "database": "postgresql" if USE_POSTGRES else "sqlite"})


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        terms_accepted = request.form.get("terms_accepted")

        if not username or not password:
            flash("Iltimos, hamma maydonlarni to'ldiring")
            return render_template("register.html")

        if not terms_accepted:
            flash("Davom etish uchun ommaviy oferta va maxfiylik siyosatiga rozilik bildiring")
            return render_template("register.html")

        if password != confirm:
            flash("Parollar mos kelmadi")
            return render_template("register.html")

        if len(password) < 4:
            flash("Parol kamida 4 ta belgidan iborat bo'lishi kerak")
            return render_template("register.html")

        conn = get_db()
        existing = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()

        if existing:
            flash("Bu foydalanuvchi nomi allaqachon band")
            conn.close()
            return render_template("register.html")

        conn.execute(
            "INSERT INTO users (username, password_hash, avatar_letter, security_answer_hash, terms_accepted_at) VALUES (?, ?, ?, ?, ?)",
            (
                username,
                hash_password(password),
                username[0].upper(),
                None,
                datetime.now().strftime("%d.%m.%Y %H:%M"),
            ),
        )
        conn.commit()
        conn.close()

        flash("Muvaffaqiyatli ro'yxatdan o'tdingiz! Endi kirishingiz mumkin.")
        return redirect(url_for("login"))

    return render_template("register.html")


def login_user(user):
    """Foydalanuvchini sessiyaga kiritadi (1 yil eslab qoladi) va qurilmani ro'yxatga oladi."""
    lang = session.get("lang")
    session.clear()
    if lang:
        session["lang"] = lang
    session.permanent = True
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["avatar_letter"] = user["avatar_letter"]
    session["nickname"] = user["nickname"]
    session["avatar_file"] = user["avatar_file"]
    conn = get_db()
    try:
        start_session_record(conn, user["username"])
        conn.commit()
    finally:
        conn.close()


def verify_google_token(credential):
    """Google ID tokenini Google serveri orqali tekshiradi. Muvaffaqiyatda {sub, email, name} qaytaradi, aks holda None."""
    if not credential or not GOOGLE_CLIENT_ID:
        return None
    try:
        url = "https://oauth2.googleapis.com/tokeninfo?" + urllib.parse.urlencode({"id_token": credential})
        with urllib.request.urlopen(url, timeout=8) as resp:
            info = json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    if info.get("aud") != GOOGLE_CLIENT_ID:
        return None
    if str(info.get("email_verified")).lower() != "true":
        return None
    try:
        if int(info.get("exp", 0)) < time.time():
            return None
    except (TypeError, ValueError):
        return None
    if not info.get("sub") or not info.get("email"):
        return None
    return {"sub": info["sub"], "email": info["email"].lower(), "name": info.get("name") or ""}


def make_username_from_email(conn, email):
    base = re.sub(r"[^a-z0-9_]", "", email.split("@")[0].lower()) or "user"
    base = base[:18]
    if len(base) < 3:
        base = (base + "user")[:6]
    candidate = base
    n = 1
    while conn.execute("SELECT 1 FROM users WHERE LOWER(username) = ? OR LOWER(COALESCE(nickname, '')) = ?",
                       (candidate, candidate)).fetchone():
        n += 1
        candidate = f"{base}{n}" if n < 100 else f"{base}{secrets.randbelow(100000)}"
    return candidate


@app.route("/auth/google", methods=["POST"])
def google_auth():
    """Google bilan kirish / ro'yxatdan o'tish (yoki mavjud hisobga Google'ni ulash)."""
    data = request.get_json(silent=True) or {}
    info = verify_google_token(data.get("credential", ""))
    if not info:
        return jsonify({"ok": False, "error": tr("google_failed")}), 400

    conn = get_db()
    try:
        # 1) Allaqachon tizimga kirgan foydalanuvchi: Google'ni hisobiga ulaymiz
        if "user_id" in session:
            me = conn.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],)).fetchone()
            if me:
                other = conn.execute("SELECT username FROM users WHERE google_sub = ?", (info["sub"],)).fetchone()
                if other and other["username"] != me["username"]:
                    return jsonify({"ok": False, "error": tr("google_already_linked")}), 409
                conn.execute("UPDATE users SET google_sub = ?, email = ? WHERE id = ?",
                             (info["sub"], info["email"], me["id"]))
                conn.commit()
                return jsonify({"ok": True, "redirect": url_for("settings_page")})

        # 2) Mavjud Google hisobi
        user = conn.execute("SELECT * FROM users WHERE google_sub = ?", (info["sub"],)).fetchone()
        if not user:
            # 3) Yangi hisob
            username = make_username_from_email(conn, info["email"])
            conn.execute(
                "INSERT INTO users (username, password_hash, avatar_letter, security_answer_hash, terms_accepted_at, email, google_sub, password_set) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, 0)",
                (username, hash_password(secrets.token_hex(24)), username[0].upper(), None,
                 datetime.now().strftime("%d.%m.%Y %H:%M"), info["email"], info["sub"]),
            )
            conn.commit()
            user = conn.execute("SELECT * FROM users WHERE google_sub = ?", (info["sub"],)).fetchone()

        blocked = conn.execute("SELECT 1 FROM blocked_users WHERE username = ?", (user["username"],)).fetchone()
        if blocked:
            return jsonify({"ok": False, "error": tr("blocked_msg")}), 403
        login_user(user)
        nxt = request.args.get("next", "") or data.get("next", "")
        return jsonify({"ok": True, "redirect": nxt if is_safe_next(nxt) else url_for("dashboard")})
    finally:
        conn.close()


def delete_user_everything(conn, username):
    """Foydalanuvchining barcha ma'lumotlarini butunlay o'chiradi."""
    for post in conn.execute("SELECT * FROM posts WHERE username = ?", (username,)).fetchall():
        delete_post_everything(conn, post)
    # u egasi bo'lgan guruh/kanallar: boshqa a'zo bo'lsa egalik o'tadi, bo'lmasa o'chadi
    for gm in conn.execute("SELECT group_id FROM group_members WHERE username = ? AND role = 'owner'", (username,)).fetchall():
        gid = gm["group_id"]
        heir = conn.execute(
            """SELECT username FROM group_members WHERE group_id = ? AND username != ?
               ORDER BY CASE role WHEN 'admin' THEN 0 ELSE 1 END, id LIMIT 1""",
            (gid, username),
        ).fetchone()
        if heir:
            conn.execute("UPDATE group_members SET role = 'owner' WHERE group_id = ? AND username = ?", (gid, heir["username"]))
            conn.execute("UPDATE groups SET created_by = ? WHERE id = ?", (heir["username"], gid))
        else:
            delete_group_everything(conn, gid)
    conn.execute("DELETE FROM chat_mutes WHERE username = ?", (username,))
    conn.execute("DELETE FROM cart_lines WHERE username = ?", (username,))
    conn.execute("DELETE FROM order_items WHERE order_id IN (SELECT id FROM orders WHERE buyer = ? OR seller = ?)", (username, username))
    conn.execute("DELETE FROM orders WHERE buyer = ? OR seller = ?", (username, username))
    for table in ("post_comments", "post_views", "post_shares", "likes", "cart_items", "group_members"):
        conn.execute(f"DELETE FROM {table} WHERE username = ?", (username,))
    # postlardagi boshqa izohlar o'chmaydi, faqat foydalanuvchining o'zinikilari
    for row in conn.execute(
        "SELECT image_file FROM private_messages WHERE (sender = ? OR receiver = ?) AND image_file IS NOT NULL",
        (username, username),
    ).fetchall():
        delete_image_from_db(conn, row["image_file"])
    conn.execute("DELETE FROM private_messages WHERE sender = ? OR receiver = ?", (username, username))
    for row in conn.execute(
        "SELECT image_file FROM group_messages WHERE username = ? AND image_file IS NOT NULL", (username,)
    ).fetchall():
        delete_image_from_db(conn, row["image_file"])
    conn.execute("DELETE FROM group_messages WHERE username = ?", (username,))
    conn.execute("DELETE FROM messages WHERE username = ?", (username,))
    delete_store_everything(conn, username)
    conn.execute("DELETE FROM contact_requests WHERE from_username = ? OR to_username = ?", (username, username))
    conn.execute("DELETE FROM contacts WHERE username = ? OR contact_username = ?", (username, username))
    conn.execute("DELETE FROM blocked_users WHERE username = ?", (username,))
    conn.execute("DELETE FROM user_sessions WHERE username = ?", (username,))
    conn.execute("DELETE FROM user_settings WHERE username = ?", (username,))
    conn.execute("DELETE FROM user_blocks WHERE blocker = ? OR blocked = ?", (username, username))
    for c in conn.execute("SELECT id FROM calls WHERE caller = ? OR callee = ?", (username, username)).fetchall():
        conn.execute("DELETE FROM call_signals WHERE call_id = ?", (c["id"],))
    conn.execute("DELETE FROM calls WHERE caller = ? OR callee = ?", (username, username))
    row = conn.execute("SELECT avatar_file FROM users WHERE username = ?", (username,)).fetchone()
    if row and row["avatar_file"]:
        delete_image_from_db(conn, row["avatar_file"])
    conn.execute("DELETE FROM users WHERE username = ?", (username,))


@app.route("/api/account/delete", methods=["POST"])
def api_account_delete():
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "auth"}), 401
    data = request.get_json(silent=True) or {}
    me = session["username"]
    if (data.get("confirm") or "").strip().lower() != me.lower():
        return jsonify({"ok": False, "error": tr("delete_account_mismatch")}), 400
    conn = get_db()
    try:
        delete_user_everything(conn, me)
        conn.commit()
    except Exception:
        conn.rollback()
        return jsonify({"ok": False, "error": tr("err_network")}), 500
    finally:
        conn.close()
    session.clear()
    return jsonify({"ok": True, "redirect": url_for("login")})


@app.after_request
def mobile_no_zoom(resp):
    """Telefonda sahifa qo'l bilan yaqinlashib/siljib ketmasligi uchun viewport'ni qat'iylashtiradi."""
    try:
        if resp.mimetype == "text/html" and not resp.direct_passthrough:
            body = resp.get_data(as_text=True)
            body = body.replace(
                'width=device-width, initial-scale=1">',
                'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">',
            )
            if "</body>" in body:
                body = body.replace("</body>", NO_ZOOM_JS + "</body>", 1)
            if "rel=\"icon\"" not in body and "</head>" in body:
                body = body.replace("</head>", BRAND_HEAD + "</head>", 1)
            resp.set_data(body)
    except Exception:
        pass
    return resp


BRAND_HEAD = (
    '<link rel="icon" type="image/svg+xml" href="/static/logo.svg">'
    '<link rel="icon" type="image/png" sizes="64x64" href="/static/favicon-64.png">'
    '<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">'
    '<link rel="manifest" href="/manifest.webmanifest">'
    '<meta name="theme-color" content="#0f1226">'
)


@app.route("/manifest.webmanifest")
def web_manifest():
    data = {
        "name": "Linko", "short_name": "Linko", "start_url": "/", "display": "standalone",
        "background_color": "#0f1226", "theme_color": "#0f1226",
        "icons": [
            {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png"},
            {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png"},
            {"src": "/static/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    return Response(json.dumps(data), mimetype="application/manifest+json")


@app.route("/favicon.ico")
def favicon():
    return redirect("/static/favicon-64.png", code=302)


NO_ZOOM_JS = """<script>
document.addEventListener('gesturestart',function(e){e.preventDefault();});
document.addEventListener('gesturechange',function(e){e.preventDefault();});
document.addEventListener('touchmove',function(e){if(e.touches&&e.touches.length>1){e.preventDefault();}},{passive:false});
</script>"""


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and user["password_hash"] == hash_password(password):
            conn = get_db()
            is_blocked = conn.execute(
                "SELECT 1 FROM blocked_users WHERE username = ?", (user["username"],)
            ).fetchone()
            conn.close()
            if is_blocked:
                flash(tr("blocked_msg"))
                return render_template("login.html")
            login_user(user)
            nxt = request.args.get("next", "")
            return redirect(nxt if is_safe_next(nxt) else url_for("dashboard"))
        else:
            flash("Login yoki parol xato")

    return render_template("login.html")


@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        step = request.form.get("step", "username")
        username = request.form.get("username", "").strip()

        conn = get_db()
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if not user:
            conn.close()
            flash("Bunday foydalanuvchi topilmadi")
            return render_template("forgot.html", step="username")

        if step == "username":
            if not user["security_answer_hash"]:
                conn.close()
                flash(tr("forgot_no_question"))
                return render_template("forgot.html", step="username")
            conn.close()
            return render_template("forgot.html", step="answer", username=username)

        if step == "answer":
            answer = request.form.get("security_answer", "").strip().lower()
            new_password = request.form.get("new_password", "")

            if user["security_answer_hash"] != hash_password(answer):
                conn.close()
                flash("Javob noto'g'ri")
                return render_template("forgot.html", step="answer", username=username)

            if len(new_password) < 4:
                conn.close()
                flash("Yangi parol kamida 4 ta belgidan iborat bo'lishi kerak")
                return render_template("forgot.html", step="answer", username=username)

            conn.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (hash_password(new_password), username),
            )
            conn.commit()
            conn.close()
            flash("Parol muvaffaqiyatli o'zgartirildi! Endi kirishingiz mumkin.")
            return redirect(url_for("login"))

    return render_template("forgot.html", step="username")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    conn = get_db()
    pending_count = conn.execute(
        "SELECT COUNT(*) as c FROM contact_requests WHERE to_username = ?",
        (me,),
    ).fetchone()["c"]

    recent_chats = get_conversations(conn, me, limit=4)
    feed_new = feed_new_counts(conn, me)
    conn.close()

    return render_template(
        "dashboard.html",
        feed_new=feed_new,
        username=me,
        avatar_letter=session["avatar_letter"],
        avatar_file=session.get("avatar_file"),
        display_name=session.get("nickname") or me,
        pending_count=pending_count,
        recent_chats=recent_chats,
        active="home",
    )


@app.route("/chat")
def chat():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "chat.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        active="chat",
    )


@app.route("/api/messages")
def api_messages():
    """Oxirgi 50 ta xabarni JSON shaklida qaytaradi (chat sahifasi shuni so'rab turadi)"""
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    rows = conn.execute(
        "SELECT username, content, created_at FROM messages ORDER BY id DESC LIMIT 50"
    ).fetchall()
    conn.close()

    messages = [
        {"username": r["username"], "content": r["content"], "created_at": r["created_at"]}
        for r in reversed(rows)
    ]
    return jsonify({"messages": messages, "me": session["username"]})


@app.route("/api/send", methods=["POST"])
def api_send():
    """Yangi xabarni bazaga saqlaydi"""
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()

    if not content:
        return jsonify({"error": "bo'sh xabar"}), 400

    if len(content) > 1000:
        content = content[:1000]

    conn = get_db()
    conn.execute(
        "INSERT INTO messages (username, content, created_at) VALUES (?, ?, ?)",
        (session["username"], content, datetime.now().strftime("%H:%M")),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/media/<filename>")
def media(filename):
    """Bazaga saqlangan rasm va videolarni ko'rsatadi (video uchun Range - bo'lak-bo'lak yuklash - qo'llab-quvvatlanadi)."""
    conn = get_db()
    meta = conn.execute(
        "SELECT mimetype, LENGTH(data) AS size FROM uploaded_images WHERE filename = ?", (filename,)
    ).fetchone()

    if not meta:
        conn.close()
        return "", 404

    mimetype, size = meta["mimetype"], int(meta["size"] or 0)

    if mimetype.startswith(("video/", "audio/")):
        start, end = 0, size - 1
        status = 200
        range_header = request.headers.get("Range", "")
        m = re.match(r"bytes=(\d*)-(\d*)", range_header)
        if m and (m.group(1) or m.group(2)):
            if m.group(1):
                start = int(m.group(1))
                end = int(m.group(2)) if m.group(2) else size - 1
            else:  # oxirgi N bayt
                start = max(0, size - int(m.group(2)))
            if start >= size:
                conn.close()
                return Response(status=416, headers={"Content-Range": f"bytes */{size}"})
            end = min(end, size - 1, start + 3 * 1024 * 1024 - 1)  # bir marta ko'pi bilan 3 MB
            status = 206
        length = end - start + 1
        if USE_POSTGRES:
            row = conn.execute(
                "SELECT SUBSTRING(data FROM ? FOR ?) AS chunk FROM uploaded_images WHERE filename = ?",
                (start + 1, length, filename),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT SUBSTR(data, ?, ?) AS chunk FROM uploaded_images WHERE filename = ?",
                (start + 1, length, filename),
            ).fetchone()
        conn.close()
        chunk = row["chunk"] if row else b""
        if isinstance(chunk, memoryview):
            chunk = bytes(chunk)
        response = Response(chunk, status=status, mimetype=mimetype)
        response.headers["Accept-Ranges"] = "bytes"
        response.headers["Content-Length"] = str(len(chunk))
        if status == 206:
            response.headers["Content-Range"] = f"bytes {start}-{start + len(chunk) - 1}/{size}"
        response.headers["Cache-Control"] = "public, max-age=31536000"
        return response

    row = conn.execute("SELECT data FROM uploaded_images WHERE filename = ?", (filename,)).fetchone()
    conn.close()
    data = row["data"]
    if isinstance(data, memoryview):
        data = bytes(data)
    response = Response(data, mimetype=mimetype)
    response.headers["Cache-Control"] = "public, max-age=31536000"
    return response


def save_video_to_db(conn, file_storage):
    """Videoni bazaga saqlaydi (hajm chegarasi bilan). Hajm katta bo'lsa ValueError('video_too_big')."""
    ext = file_storage.filename.rsplit(".", 1)[-1].lower() if "." in file_storage.filename else ""
    if ext not in VIDEO_MIMES:
        raise ValueError("bad_type")
    data = file_storage.read()
    if len(data) > MAX_VIDEO_BYTES:
        raise ValueError("video_too_big")
    unique_name = f"v{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{secure_filename(file_storage.filename) or 'video.' + ext}"
    db_data = psycopg2.Binary(data) if USE_POSTGRES else data
    conn.execute(
        "INSERT INTO uploaded_images (filename, mimetype, data, created_at) VALUES (?, ?, ?, ?)",
        (unique_name, VIDEO_MIMES[ext], db_data, datetime.now().strftime("%d.%m.%Y %H:%M")),
    )
    return unique_name


def time_ago(ts, fallback=""):
    """'2 soat oldin' ko'rinishidagi vaqt (joriy til bo'yicha)."""
    if not ts:
        return fallback
    diff = max(0, int(time.time()) - int(ts))
    t = TRANSLATIONS[current_lang()]
    if diff < 60:
        return t["ago_now"]
    if diff < 3600:
        return t["ago_min"].replace("{n}", str(diff // 60))
    if diff < 86400:
        return t["ago_hour"].replace("{n}", str(diff // 3600))
    if diff < 86400 * 7:
        return t["ago_day"].replace("{n}", str(diff // 86400))
    return fallback


def build_post_cards(conn, rows, me):
    """Postlar ro'yxatiga media, layk, izoh, ko'rish va ulashish sonlarini qo'shadi (bir nechta guruhlangan so'rovda)."""
    rows = list(rows)
    if not rows:
        return []
    ids = [r["id"] for r in rows]
    marks = ",".join("?" for _ in ids)
    ids_t = tuple(ids)

    media_map = {}
    for r in conn.execute(
        f"SELECT post_id, filename, kind FROM post_media WHERE post_id IN ({marks}) ORDER BY position, id", ids_t
    ).fetchall():
        media_map.setdefault(r["post_id"], []).append({"filename": r["filename"], "kind": r["kind"]})

    def grouped(sql):
        return {r["post_id"]: r["c"] for r in conn.execute(sql, ids_t).fetchall()}

    likes = grouped(f"SELECT post_id, COUNT(*) AS c FROM likes WHERE post_id IN ({marks}) GROUP BY post_id")
    comments = grouped(f"SELECT post_id, COUNT(*) AS c FROM post_comments WHERE post_id IN ({marks}) GROUP BY post_id")
    views = grouped(f"SELECT post_id, COUNT(*) AS c FROM post_views WHERE post_id IN ({marks}) GROUP BY post_id")
    shares = grouped(f"SELECT post_id, COUNT(DISTINCT username) AS c FROM post_shares WHERE post_id IN ({marks}) GROUP BY post_id")
    mine = {
        r["post_id"]
        for r in conn.execute(
            f"SELECT post_id FROM likes WHERE username = ? AND post_id IN ({marks})", (me, *ids)
        ).fetchall()
    }
    names = list({r["username"] for r in rows})
    nmarks = ",".join("?" for _ in names)
    users = {
        r["username"]: r
        for r in conn.execute(
            f"SELECT username, avatar_letter, avatar_file, nickname FROM users WHERE username IN ({nmarks})", tuple(names)
        ).fetchall()
    }

    cards = []
    for p in rows:
        u = users.get(p["username"])
        media = media_map.get(p["id"], [])
        if not media and p["image_file"]:
            media = [{"filename": p["image_file"], "kind": "image"}]
        cards.append({
            "id": p["id"],
            "username": p["username"],
            "display": (u["nickname"] if u and u["nickname"] else p["username"]),
            "avatar_letter": (u["avatar_letter"] if u else p["avatar_letter"]),
            "avatar_file": (u["avatar_file"] if u else None),
            "content": p["content"],
            "media": media,
            "image_file": p["image_file"],
            "created_at": p["created_at"],
            "ago": time_ago(p["created_ts"], p["created_at"]),
            "like_count": likes.get(p["id"], 0),
            "liked_by_me": p["id"] in mine,
            "comment_count": comments.get(p["id"], 0),
            "view_count": views.get(p["id"], 0),
            "share_count": shares.get(p["id"], 0),
            "is_owner": p["username"] == me,
        })
    return cards


def delete_post_everything(conn, post):
    """Postni va unga bog'liq barcha narsani (media, layk, izoh, ko'rish, ulashish) o'chiradi."""
    pid = post["id"]
    for m in conn.execute("SELECT filename FROM post_media WHERE post_id = ?", (pid,)).fetchall():
        delete_image_from_db(conn, m["filename"])
    if post["image_file"]:
        delete_image_from_db(conn, post["image_file"])
    for table in ("post_media", "post_comments", "post_views", "post_shares", "likes"):
        conn.execute(f"DELETE FROM {table} WHERE post_id = ?", (pid,))
    conn.execute("DELETE FROM posts WHERE id = ?", (pid,))


@app.route("/feed", methods=["GET", "POST"])
def feed():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]

    if request.method == "POST":  # eski oddiy forma (zaxira): faqat matn
        content = request.form.get("content", "").strip()
        if content:
            conn = get_db()
            conn.execute(
                "INSERT INTO posts (username, avatar_letter, content, image_file, created_at, created_ts) VALUES (?, ?, ?, ?, ?, ?)",
                (me, session["avatar_letter"], content, None, datetime.now().strftime("%d.%m %H:%M"), int(time.time())),
            )
            conn.commit()
            conn.close()
        return redirect(url_for("feed"))

    page = max(request.args.get("page", 1, type=int) or 1, 1)
    f = "friends" if request.args.get("f") == "friends" else "all"
    conn = get_db()
    if f == "friends":
        rows = conn.execute(
            """SELECT * FROM posts
               WHERE username = ? OR username IN (SELECT contact_username FROM contacts WHERE username = ?)
               ORDER BY id DESC LIMIT ? OFFSET ?""",
            (me, me, PAGE_SIZE + 1, (page - 1) * PAGE_SIZE),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM posts ORDER BY id DESC LIMIT ? OFFSET ?",
            (PAGE_SIZE + 1, (page - 1) * PAGE_SIZE),
        ).fetchall()
    has_more = len(rows) > PAGE_SIZE
    cards = build_post_cards(conn, rows[:PAGE_SIZE], me)
    conn.close()

    return render_template(
        "feed.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        posts=cards,
        page=page,
        has_more=has_more,
        f=f,
        single=False,
        active="feed",
    )


@app.route("/post/<int:post_id>")
def post_page(post_id):
    """Bitta post sahifasi (ulashilgan havola shu yerga olib keladi)."""
    me = session["username"]
    conn = get_db()
    row = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not row:
        conn.close()
        flash(tr("profile_not_found"))
        return redirect(url_for("feed"))
    cards = build_post_cards(conn, [row], me)
    conn.close()
    return render_template(
        "feed.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        posts=cards,
        page=1,
        has_more=False,
        f="all",
        single=True,
        active="feed",
    )


@app.route("/api/posts/create", methods=["POST"])
def api_post_create():
    """Yangi post: matn + 10 tagacha rasm/video (bir nechta fayl)."""
    if "user_id" not in session:
        return jsonify({"error": "login"}), 401

    content = (request.form.get("content") or "").strip()[:2000]
    files = [f for f in request.files.getlist("media") if f and f.filename]
    if not content and not files:
        return jsonify({"error": "empty"}), 400
    if len(files) > MAX_MEDIA_PER_POST:
        return jsonify({"error": "too_many"}), 400

    conn = get_db()
    saved = []  # (filename, kind)
    try:
        for fs in files:
            ext = fs.filename.rsplit(".", 1)[-1].lower() if "." in fs.filename else ""
            if ext in VIDEO_MIMES:
                saved.append((save_video_to_db(conn, fs), "video"))
            elif allowed_file(fs.filename):
                saved.append((save_image_to_db(conn, fs), "image"))
        if not content and not saved:
            conn.rollback()
            return jsonify({"error": "bad_type"}), 400

        first_image = next((name for name, kind in saved if kind == "image"), None)
        cur = conn.execute(
            "INSERT INTO posts (username, avatar_letter, content, image_file, created_at, created_ts) VALUES (?, ?, ?, ?, ?, ?)",
            (session["username"], session["avatar_letter"], content, first_image,
             datetime.now().strftime("%d.%m %H:%M"), int(time.time())),
        )
        post_id = cur.lastrowid
        for pos, (name, kind) in enumerate(saved):
            conn.execute(
                "INSERT INTO post_media (post_id, filename, kind, position) VALUES (?, ?, ?, ?)",
                (post_id, name, kind, pos),
            )
        conn.commit()
    except ValueError as e:
        conn.rollback()
        return jsonify({"error": str(e)}), (413 if str(e) == "video_too_big" else 400)
    finally:
        conn.close()
    return jsonify({"ok": True, "id": post_id})


@app.route("/api/posts/<int:post_id>/view", methods=["POST"])
def api_post_view(post_id):
    """Postni ko'rilgan deb belgilaydi (har bir odam uchun 1 marta, egasi hisobga olinmaydi)."""
    if "user_id" not in session:
        return jsonify({"error": "login"}), 401
    conn = get_db()
    post = conn.execute("SELECT username FROM posts WHERE id = ?", (post_id,)).fetchone()
    if post and post["username"] != session["username"]:
        conn.execute(
            "INSERT OR IGNORE INTO post_views (post_id, username) VALUES (?, ?)", (post_id, session["username"])
        )
        conn.commit()
    count = conn.execute("SELECT COUNT(*) AS c FROM post_views WHERE post_id = ?", (post_id,)).fetchone()["c"]
    conn.close()
    return jsonify({"views": count})


@app.route("/api/posts/<int:post_id>/share", methods=["POST"])
def api_post_share(post_id):
    if "user_id" not in session:
        return jsonify({"error": "login"}), 401
    conn = get_db()
    if conn.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,)).fetchone():
        conn.execute(
            "INSERT INTO post_shares (post_id, username, created_ts) VALUES (?, ?, ?)",
            (post_id, session["username"], int(time.time())),
        )
        conn.commit()
    count = conn.execute(
        "SELECT COUNT(DISTINCT username) AS c FROM post_shares WHERE post_id = ?", (post_id,)
    ).fetchone()["c"]
    conn.close()
    return jsonify({"shares": count})


def comment_to_dict(r, post_owner, me):
    return {
        "id": r["id"],
        "username": r["username"],
        "display": r["nickname"] or r["username"],
        "avatar_letter": r["avatar_letter"],
        "avatar_file": r["avatar_file"],
        "content": r["content"],
        "ago": time_ago(r["created_ts"], r["created_at"]),
        "can_delete": r["username"] == me or post_owner == me or bool(getattr(g, "is_admin", False)),
    }


COMMENT_SELECT = """SELECT c.id, c.username, c.content, c.created_at, c.created_ts,
                           u.nickname, u.avatar_letter, u.avatar_file
                    FROM post_comments c LEFT JOIN users u ON u.username = c.username"""


@app.route("/api/posts/<int:post_id>/comments", methods=["GET", "POST"])
def api_post_comments(post_id):
    if "user_id" not in session:
        return jsonify({"error": "login"}), 401
    me = session["username"]
    conn = get_db()
    post = conn.execute("SELECT username FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post:
        conn.close()
        return jsonify({"error": "not_found"}), 404

    if request.method == "POST":
        data = request.get_json(silent=True) or {}
        content = (data.get("content") or "").strip()[:500]
        if not content:
            conn.close()
            return jsonify({"error": "empty"}), 400
        cur = conn.execute(
            "INSERT INTO post_comments (post_id, username, content, created_at, created_ts) VALUES (?, ?, ?, ?, ?)",
            (post_id, me, content, datetime.now().strftime("%d.%m %H:%M"), int(time.time())),
        )
        conn.commit()
        row = conn.execute(COMMENT_SELECT + " WHERE c.id = ?", (cur.lastrowid,)).fetchone()
        count = conn.execute("SELECT COUNT(*) AS c FROM post_comments WHERE post_id = ?", (post_id,)).fetchone()["c"]
        conn.close()
        return jsonify({"comment": comment_to_dict(row, post["username"], me), "count": count})

    rows = conn.execute(
        COMMENT_SELECT + " WHERE c.post_id = ? ORDER BY c.id DESC LIMIT 50", (post_id,)
    ).fetchall()
    count = conn.execute("SELECT COUNT(*) AS c FROM post_comments WHERE post_id = ?", (post_id,)).fetchone()["c"]
    conn.close()
    return jsonify({
        "comments": [comment_to_dict(r, post["username"], me) for r in reversed(rows)],
        "count": count,
    })


@app.route("/api/comments/delete/<int:comment_id>", methods=["POST"])
def api_comment_delete(comment_id):
    if "user_id" not in session:
        return jsonify({"error": "login"}), 401
    me = session["username"]
    conn = get_db()
    c = conn.execute(
        """SELECT c.id, c.post_id, c.username, p.username AS post_owner
           FROM post_comments c LEFT JOIN posts p ON p.id = c.post_id WHERE c.id = ?""",
        (comment_id,),
    ).fetchone()
    if not c or not (c["username"] == me or c["post_owner"] == me or g.is_admin):
        conn.close()
        return jsonify({"error": "forbidden"}), 403
    conn.execute("DELETE FROM post_comments WHERE id = ?", (comment_id,))
    conn.commit()
    count = conn.execute("SELECT COUNT(*) AS c FROM post_comments WHERE post_id = ?", (c["post_id"],)).fetchone()["c"]
    conn.close()
    return jsonify({"ok": True, "count": count})


@app.route("/api/posts/<int:post_id>/stats")
def api_post_stats(post_id):
    """Post statistikasi: faqat post egasi va admin uchun."""
    if "user_id" not in session:
        return jsonify({"error": "login"}), 401
    conn = get_db()
    post = conn.execute("SELECT username FROM posts WHERE id = ?", (post_id,)).fetchone()
    if not post or (post["username"] != session["username"] and not g.is_admin):
        conn.close()
        return jsonify({"error": "forbidden"}), 403

    def count(sql):
        return conn.execute(sql, (post_id,)).fetchone()["c"]

    viewers = conn.execute(
        """SELECT v.username, u.nickname FROM post_views v LEFT JOIN users u ON u.username = v.username
           WHERE v.post_id = ? ORDER BY v.id DESC LIMIT 20""",
        (post_id,),
    ).fetchall()
    result = {
        "views": count("SELECT COUNT(*) AS c FROM post_views WHERE post_id = ?"),
        "likes": count("SELECT COUNT(*) AS c FROM likes WHERE post_id = ?"),
        "comments": count("SELECT COUNT(*) AS c FROM post_comments WHERE post_id = ?"),
        "shares": count("SELECT COUNT(DISTINCT username) AS c FROM post_shares WHERE post_id = ?"),
        "viewers": [{"username": v["username"], "display": v["nickname"] or v["username"]} for v in viewers],
    }
    conn.close()
    return jsonify(result)


@app.route("/api/posts/delete/<int:post_id>", methods=["POST"])
def api_post_delete(post_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

    if not post or (post["username"] != session["username"] and not g.is_admin):
        conn.close()
        return jsonify({"error": "ruxsat yo'q"}), 403

    delete_post_everything(conn, post)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ---------------- ADMIN ----------------

@app.route("/admin")
def admin_page():
    if not admin_required():
        flash(tr("admin_only"))
        return redirect(url_for("dashboard"))

    q = request.args.get("q", "").strip().lstrip("@")
    conn = get_db()
    if q:
        like = f"%{q}%"
        users = conn.execute(
            """SELECT u.username, u.nickname, u.avatar_letter, u.avatar_file, u.is_admin, b.id AS blocked_id
               FROM users u LEFT JOIN blocked_users b ON b.username = u.username
               WHERE LOWER(u.username) LIKE LOWER(?) OR LOWER(COALESCE(u.nickname, '')) LIKE LOWER(?)
               ORDER BY u.id DESC LIMIT 50""",
            (like, like),
        ).fetchall()
    else:
        users = conn.execute(
            """SELECT u.username, u.nickname, u.avatar_letter, u.avatar_file, u.is_admin, b.id AS blocked_id
               FROM users u LEFT JOIN blocked_users b ON b.username = u.username
               ORDER BY u.id DESC LIMIT 50"""
        ).fetchall()
    posts = conn.execute("SELECT id, username, content, image_file, created_at FROM posts ORDER BY id DESC LIMIT 30").fetchall()
    products = conn.execute("SELECT id, seller_username, title, price, image_file FROM products ORDER BY id DESC LIMIT 30").fetchall()
    conn.close()

    admin_set = ADMIN_USERNAMES
    users = [
        {**dict(u), "is_admin_user": bool(u["is_admin"]) or u["username"].lower() in admin_set}
        for u in users
    ]
    return render_template(
        "admin.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        users=users,
        posts=posts,
        products=products,
        q=q,
        active="profile",
    )


@app.route("/api/admin/block/<target_username>", methods=["POST"])
def api_admin_block(target_username):
    if not admin_required():
        return jsonify({"error": "ruxsat yo'q"}), 403
    if target_username == session["username"]:
        return jsonify({"error": "o'zingizni bloklab bo'lmaydi"}), 400

    conn = get_db()
    user = conn.execute("SELECT username, is_admin FROM users WHERE username = ?", (target_username,)).fetchone()
    if not user:
        conn.close()
        return jsonify({"error": "topilmadi"}), 404
    if bool(user["is_admin"]) or user["username"].lower() in ADMIN_USERNAMES:
        conn.close()
        return jsonify({"error": "adminni bloklab bo'lmaydi"}), 400

    conn.execute(
        "INSERT OR IGNORE INTO blocked_users (username, blocked_at) VALUES (?, ?)",
        (target_username, datetime.now().strftime("%d.%m.%Y %H:%M")),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "blocked": True})


@app.route("/api/admin/unblock/<target_username>", methods=["POST"])
def api_admin_unblock(target_username):
    if not admin_required():
        return jsonify({"error": "ruxsat yo'q"}), 403
    conn = get_db()
    conn.execute("DELETE FROM blocked_users WHERE username = ?", (target_username,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "blocked": False})


@app.route("/api/posts/edit/<int:post_id>", methods=["POST"])
def api_post_edit(post_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    data = request.get_json(silent=True) or {}
    new_content = (data.get("content") or "").strip()

    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

    if not post or post["username"] != session["username"]:
        conn.close()
        return jsonify({"error": "ruxsat yo'q"}), 403

    conn.execute("UPDATE posts SET content = ? WHERE id = ?", (new_content, post_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "content": new_content})


@app.route("/api/like/<int:post_id>", methods=["POST"])
def api_like(post_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    existing = conn.execute(
        "SELECT id FROM likes WHERE post_id = ? AND username = ?",
        (post_id, session["username"]),
    ).fetchone()

    if existing:
        conn.execute("DELETE FROM likes WHERE id = ?", (existing["id"],))
        liked = False
    else:
        conn.execute(
            "INSERT INTO likes (post_id, username) VALUES (?, ?)",
            (post_id, session["username"]),
        )
        liked = True

    conn.commit()
    like_count = conn.execute(
        "SELECT COUNT(*) as c FROM likes WHERE post_id = ?", (post_id,)
    ).fetchone()["c"]
    conn.close()

    return jsonify({"liked": liked, "like_count": like_count})


# ---------- Biznes akkaunt, do'kon, savat va buyurtmalar ----------
def normalize_phone(raw):
    p = re.sub(r"[\s\-()]", "", (raw or "").strip())
    return p if re.match(r"^\+?\d{7,15}$", p) else ""


def parse_options(text):
    seen, out = set(), []
    for part in re.split(r"[,;\n]", text or ""):
        v = part.strip()[:24]
        if v and v.lower() not in seen:
            seen.add(v.lower())
            out.append(v)
    return out[:30]


def user_location_text(u, lang=None):
    lang = lang or current_lang()
    parts = []
    for v in (u["district"], u["region"]):
        if v:
            parts.append(v)
    if u["country"]:
        parts.append(locations.country_name(u["country"], lang))
    return ", ".join(parts)


# ---------- Do'kon (marketplace): kategoriyalar, do'kon profillari, mahsulotlar, savat, buyurtmalar ----------
SHOP_PAGE_SIZE = 12
ORDER_STATUSES = ("new", "confirmed", "shipped", "delivered", "cancelled")
SORTS = {
    "new": "p.id DESC",
    "cheap": "p.price ASC, p.id DESC",
    "expensive": "p.price DESC, p.id DESC",
    "popular": "p.sold DESC, p.views DESC, p.id DESC",
}
HANDLE_RE = re.compile(r"^[a-z0-9_.]{3,30}$")


def is_business(conn, username):
    return bool(conn.execute("SELECT 1 FROM stores WHERE username = ?", (username,)).fetchone())


def get_store(conn, username):
    return conn.execute("SELECT * FROM stores WHERE username = ?", (username,)).fetchone()


def clean_social(v):
    return re.sub(r"[^A-Za-z0-9_.]", "", (v or "").strip().lstrip("@"))[:32]


def place_text(country, region, district, lang=None):
    lang = lang or current_lang()
    parts = [x for x in (district, region) if x]
    if country:
        parts.append(locations.country_name(country, lang))
    return ", ".join(parts)


def color_label(token):
    return catalog.color_name(token, current_lang())


def size_label_fn(token):
    return catalog.size_label(token, current_lang())


app.jinja_env.globals.update(
    cat_name=lambda cid: catalog.category_name(cid, current_lang()),
    cat_icon=lambda cid: catalog.category_icon(cid),
    sub_name=lambda cid, sid: catalog.sub_name(cid, sid, current_lang()),
    color_opts=lambda raw: catalog.display_options(raw, "color", current_lang()),
    size_opts=lambda raw: catalog.display_options(raw, "size", current_lang()),
    color_label=color_label,
    size_label=size_label_fn,
)
app.jinja_env.filters["money"] = lambda n: "{:,}".format(int(n or 0)).replace(",", " ")


@app.route("/api/geo/countries")
def api_geo_countries():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    return jsonify({"countries": locations.country_list(current_lang())})


@app.route("/api/geo/regions")
def api_geo_regions():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    return jsonify({"regions": locations.region_list(request.args.get("country", ""))})


@app.route("/api/geo/districts")
def api_geo_districts():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    return jsonify({"districts": locations.district_list(request.args.get("country", ""), request.args.get("region", ""))})


def product_card_rows(conn, where_sql, params, limit, offset, order_sql="p.id DESC"):
    return conn.execute(
        f"""SELECT p.*, COALESCE(s.name, u.business_name, u.nickname, p.seller_username) AS seller_business,
                   s.handle AS store_handle, s.logo_file AS store_logo, u.nickname AS seller_nick,
                   gr.name AS channel_name
            FROM products p
            LEFT JOIN users u ON u.username = p.seller_username
            LEFT JOIN stores s ON s.username = p.seller_username
            LEFT JOIN groups gr ON gr.id = p.channel_id
            {where_sql} ORDER BY {order_sql} LIMIT ? OFFSET ?""",
        (*params, limit, offset),
    ).fetchall()


def shop_where(args, base=("p.status = 'active'",)):
    """Qidiruv, kategoriya, narx, saralash filtrlaridan SQL sharti va filtr lug'ati."""
    where, params = list(base), []
    q = (args.get("q") or "").strip()[:60]
    if q:
        where.append("(LOWER(p.title) LIKE LOWER(?) OR LOWER(COALESCE(p.brand, '')) LIKE LOWER(?) OR LOWER(COALESCE(p.description, '')) LIKE LOWER(?))")
        params += [f"%{q}%"] * 3
    cat = (args.get("cat") or "").strip()
    sub = (args.get("sub") or "").strip()
    if cat and catalog.valid_category(cat):
        if cat == "other":
            where.append("(p.category = 'other' OR p.category IS NULL OR p.category = '')")
        else:
            where.append("p.category = ?")
            params.append(cat)
        if sub and catalog.valid_category(cat, sub):
            where.append("p.subcategory = ?")
            params.append(sub)
        else:
            sub = ""
    else:
        cat, sub = "", ""
    pmin = args.get("min", type=int) if hasattr(args, "get") else None
    pmax = args.get("max", type=int) if hasattr(args, "get") else None
    if pmin and pmin > 0:
        where.append("p.price >= ?")
        params.append(pmin)
    if pmax and pmax > 0:
        where.append("p.price <= ?")
        params.append(pmax)
    instock = args.get("instock") == "1"
    if instock:
        where.append("(p.stock IS NULL OR p.stock > 0)")
    sort = args.get("sort") if args.get("sort") in SORTS else "new"
    return where, params, {"q": q, "cat": cat, "sub": sub, "min": pmin or "", "max": pmax or "",
                           "instock": "1" if instock else "", "sort": sort}


def active_filter_args(f, **extra):
    """URL uchun bo'sh bo'lmagan filtrlar."""
    out = {k: v for k, v in f.items() if v and not (k == "sort" and v == "new")}
    out.update({k: v for k, v in extra.items() if v})
    return out


def cart_count_for(conn, me):
    return conn.execute("SELECT COALESCE(SUM(qty), 0) AS c FROM cart_lines WHERE username = ?", (me,)).fetchone()["c"]


def category_counts(conn, extra_where="", params=()):
    rows = conn.execute(
        f"SELECT COALESCE(NULLIF(category, ''), 'other') AS c, COALESCE(subcategory, '') AS s, COUNT(*) AS n "
        f"FROM products p WHERE p.status = 'active' {extra_where} GROUP BY 1, 2", params).fetchall()
    cats, subs = {}, {}
    for r in rows:
        cats[r["c"]] = cats.get(r["c"], 0) + r["n"]
        subs[(r["c"], r["s"])] = r["n"]
    return cats, subs


@app.route("/shop")
def shop():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    channel_id = request.args.get("channel", type=int)
    channel = group_row(conn, channel_id) if channel_id else None
    where, params, f = shop_where(request.args)
    if channel:
        where.append("p.channel_id = ?")
        params.append(channel["id"])
    where_sql = "WHERE " + " AND ".join(where)
    rows = product_card_rows(conn, where_sql, params, SHOP_PAGE_SIZE + 1, (page - 1) * SHOP_PAGE_SIZE, SORTS[f["sort"]])
    has_more = len(rows) > SHOP_PAGE_SIZE
    products = rows[:SHOP_PAGE_SIZE]
    filtered = bool(f["q"] or f["cat"] or f["min"] or f["max"] or f["instock"] or f["sort"] != "new" or channel)

    cat_counts, _ = category_counts(conn)
    cats = []
    for c in catalog.category_list(current_lang()):
        c["count"] = cat_counts.get(c["id"], 0)
        cats.append(c)
    stores_strip, deals = [], []
    if page == 1 and not filtered:
        stores_strip = conn.execute(
            """SELECT s.*, (SELECT COUNT(*) FROM products p WHERE p.seller_username = s.username AND p.status = 'active') AS n
               FROM stores s ORDER BY n DESC, s.id DESC LIMIT 14""").fetchall()
        stores_strip = [s for s in stores_strip if s["n"]]
        deals = product_card_rows(conn, "WHERE p.status = 'active' AND p.old_price IS NOT NULL AND p.old_price > p.price", (), 8, 0)
    my_store = get_store(conn, me)
    can_add = True
    if channel:
        can_add = member_role(conn, channel["id"], me) in ("owner", "admin")
    cart_count = cart_count_for(conn, me)
    conn.close()
    return render_template(
        "shop.html", username=me, avatar_letter=session["avatar_letter"],
        products=products, page=page, has_more=has_more, cart_count=cart_count,
        f=f, filtered=filtered, channel=channel, can_add=can_add, my_store=my_store,
        cats=cats, stores_strip=stores_strip, deals=deals,
        url_args=active_filter_args(f, channel=channel["id"] if channel else None),
        shop_tab="home", active="shop",
    )


@app.route("/shop/catalog")
def shop_catalog():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    cat_counts, sub_counts = category_counts(conn)
    cats = []
    for c in catalog.category_list(current_lang()):
        c["count"] = cat_counts.get(c["id"], 0)
        for s in c["subs"]:
            s["count"] = sub_counts.get((c["id"], s["id"]), 0)
        cats.append(c)
    cart_count = cart_count_for(conn, me)
    conn.close()
    return render_template("shop_catalog.html", username=me, avatar_letter=session["avatar_letter"],
                           cats=cats, cart_count=cart_count, shop_tab="catalog", active="shop")


@app.route("/stores")
def stores():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    q = (request.args.get("q") or "").strip()[:40]
    cat = (request.args.get("cat") or "").strip()
    where, params = [], []
    if q:
        where.append("(LOWER(s.name) LIKE LOWER(?) OR LOWER(s.handle) LIKE LOWER(?))")
        params += [f"%{q}%", f"%{q}%"]
    if cat and catalog.valid_category(cat):
        where.append("s.category = ?")
        params.append(cat)
    else:
        cat = ""
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    rows = conn.execute(
        f"""SELECT s.*, (SELECT COUNT(*) FROM products p WHERE p.seller_username = s.username AND p.status = 'active') AS n
            FROM stores s {where_sql} ORDER BY n DESC, s.id DESC LIMIT ? OFFSET ?""",
        (*params, SHOP_PAGE_SIZE + 1, (page - 1) * SHOP_PAGE_SIZE)).fetchall()
    has_more = len(rows) > SHOP_PAGE_SIZE
    my_store = get_store(conn, me)
    cart_count = cart_count_for(conn, me)
    conn.close()
    cards = [dict(r, place=place_text(r["country"], r["region"], r["district"])) for r in rows[:SHOP_PAGE_SIZE]]
    return render_template(
        "stores.html", username=me, avatar_letter=session["avatar_letter"], stores=cards, q=q, cat=cat,
        page=page, has_more=has_more, my_store=my_store, cart_count=cart_count,
        cats=catalog.category_list(current_lang()), shop_tab="stores", active="shop",
    )


@app.route("/store/<handle>")
def store_page(handle):
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    store = conn.execute("SELECT * FROM stores WHERE handle = ?", (handle.lower(),)).fetchone()
    if not store:
        conn.close()
        flash(tr("store_not_found"))
        return redirect(url_for("stores"))
    owner = store["username"] == me
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    base = ("p.seller_username = ?",) if owner else ("p.seller_username = ?", "p.status = 'active'")
    where, params, f = shop_where(request.args, base=base)
    params = [store["username"]] + params
    where_sql = "WHERE " + " AND ".join(where)
    rows = product_card_rows(conn, where_sql, params, SHOP_PAGE_SIZE + 1, (page - 1) * SHOP_PAGE_SIZE, SORTS[f["sort"]])
    has_more = len(rows) > SHOP_PAGE_SIZE
    cat_counts, _ = category_counts(conn, "AND p.seller_username = ?", (store["username"],))
    chips = [{"id": cid, "n": n} for cid, n in sorted(cat_counts.items(), key=lambda kv: -kv[1])]
    stats = conn.execute(
        "SELECT COUNT(*) AS n, COALESCE(SUM(sold), 0) AS sold FROM products WHERE seller_username = ? AND status = 'active'",
        (store["username"],)).fetchone()
    seller = conn.execute("SELECT username, nickname, last_seen_ts FROM users WHERE username = ?", (store["username"],)).fetchone()
    cart_count = cart_count_for(conn, me)
    conn.close()
    return render_template(
        "store.html", username=me, avatar_letter=session["avatar_letter"], store=store, owner=owner,
        place=place_text(store["country"], store["region"], store["district"]),
        products=rows[:SHOP_PAGE_SIZE], has_more=has_more, page=page, f=f, chips=chips,
        stats=stats, seller=seller, cart_count=cart_count,
        since=datetime.fromtimestamp(store["created_ts"]).strftime("%m.%Y"),
        url_args=active_filter_args(f), shop_tab="stores", active="shop",
    )


# ----- Do'kon ochish va sozlash -----
def read_store_form(conn, me, existing=None):
    f = request.form
    data = {
        "name": f.get("name", "").strip()[:40],
        "handle": slugify_handle(f.get("handle", "")),
        "description": f.get("description", "").strip()[:300],
        "category": f.get("category", "").strip(),
        "phone": f.get("phone", "").strip(),
        "country": f.get("country", "").strip(),
        "region": f.get("region", "").strip(),
        "district": f.get("district", "").strip(),
        "address": f.get("address", "").strip()[:120],
        "hours": f.get("hours", "").strip()[:60],
        "telegram": clean_social(f.get("telegram")),
        "instagram": clean_social(f.get("instagram")),
    }
    error = None
    if len(data["name"]) < 2:
        error = tr("business_name_required")
    elif not data["handle"]:
        data["handle"] = slugify_handle(data["name"])
    if not error and not HANDLE_RE.match(data["handle"] or ""):
        error = tr("store_handle_invalid")
    if not error:
        row = conn.execute("SELECT username FROM stores WHERE handle = ?", (data["handle"],)).fetchone()
        if row and row["username"] != me:
            error = tr("store_handle_taken")
    if not error and data["category"] and not catalog.valid_category(data["category"]):
        data["category"] = ""
    if not error and not normalize_phone(data["phone"]):
        error = tr("phone_invalid")
    if not error and not locations.is_valid(data["country"], data["region"], data["district"]):
        error = tr("order_location_required")
    return data, error


def store_form_page(store_data, editing, error=None):
    me = session["username"]
    return render_template(
        "store_form.html", username=me, avatar_letter=session["avatar_letter"], data=store_data, editing=editing,
        countries=locations.country_list(current_lang()), cats=catalog.category_list(current_lang()),
        error=error, shop_tab="store", active="shop",
    )


@app.route("/store/open", methods=["GET", "POST"])
def store_open():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    if get_store(conn, me):
        conn.close()
        return redirect(url_for("store_manage"))
    u = conn.execute("SELECT phone, country, region, district FROM users WHERE username = ?", (me,)).fetchone()
    if request.method == "POST":
        data, error = read_store_form(conn, me)
        if error:
            conn.close()
            return store_form_page(data, False, error)
        logo = request.files.get("logo")
        banner = request.files.get("banner")
        logo_name = save_image_to_db(conn, logo, prefix="store_logo_", avatar=True) if logo and logo.filename and allowed_file(logo.filename) else None
        banner_name = save_image_to_db(conn, banner, prefix="store_banner_") if banner and banner.filename and allowed_file(banner.filename) else None
        conn.execute(
            """INSERT INTO stores (username, name, handle, logo_file, banner_file, description, category, phone, country, region,
                                   district, address, hours, telegram, instagram, created_ts)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (me, data["name"], data["handle"], logo_name, banner_name, data["description"], data["category"],
             normalize_phone(data["phone"]), data["country"], data["region"], data["district"], data["address"],
             data["hours"], data["telegram"], data["instagram"], int(time.time())),
        )
        conn.execute("UPDATE users SET account_type = 'business', business_name = ? WHERE username = ?", (data["name"], me))
        conn.execute("UPDATE users SET phone = ? WHERE username = ? AND (phone IS NULL OR phone = '')", (normalize_phone(data["phone"]), me))
        conn.commit()
        conn.close()
        flash(tr("store_created"))
        return redirect(url_for("store_manage"))
    data = {"name": "", "handle": "", "description": "", "category": "", "phone": (u["phone"] if u else "") or "",
            "country": (u["country"] if u else "") or "", "region": (u["region"] if u else "") or "",
            "district": (u["district"] if u else "") or "", "address": "", "hours": "", "telegram": "", "instagram": ""}
    conn.close()
    return store_form_page(data, False)


@app.route("/store/settings", methods=["GET", "POST"])
def store_settings():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    store = get_store(conn, me)
    if not store:
        conn.close()
        return redirect(url_for("store_open"))
    if request.method == "POST":
        data, error = read_store_form(conn, me, store)
        if error:
            data.update({"logo_file": store["logo_file"], "banner_file": store["banner_file"], "id": store["id"]})
            conn.close()
            return store_form_page(data, True, error)
        logo_name, banner_name = store["logo_file"], store["banner_file"]
        logo, banner = request.files.get("logo"), request.files.get("banner")
        if request.form.get("remove_logo") and logo_name:
            delete_image_from_db(conn, logo_name)
            logo_name = None
        if request.form.get("remove_banner") and banner_name:
            delete_image_from_db(conn, banner_name)
            banner_name = None
        if logo and logo.filename and allowed_file(logo.filename):
            if logo_name:
                delete_image_from_db(conn, logo_name)
            logo_name = save_image_to_db(conn, logo, prefix="store_logo_", avatar=True)
        if banner and banner.filename and allowed_file(banner.filename):
            if banner_name:
                delete_image_from_db(conn, banner_name)
            banner_name = save_image_to_db(conn, banner, prefix="store_banner_")
        conn.execute(
            """UPDATE stores SET name = ?, handle = ?, logo_file = ?, banner_file = ?, description = ?, category = ?, phone = ?,
                                 country = ?, region = ?, district = ?, address = ?, hours = ?, telegram = ?, instagram = ?
               WHERE username = ?""",
            (data["name"], data["handle"], logo_name, banner_name, data["description"], data["category"],
             normalize_phone(data["phone"]), data["country"], data["region"], data["district"], data["address"],
             data["hours"], data["telegram"], data["instagram"], me),
        )
        conn.execute("UPDATE users SET business_name = ? WHERE username = ?", (data["name"], me))
        conn.commit()
        conn.close()
        flash(tr("store_saved"))
        return redirect(url_for("store_manage"))
    data = dict(store)
    conn.close()
    return store_form_page(data, True)


def delete_store_everything(conn, username):
    for prod in conn.execute("SELECT * FROM products WHERE seller_username = ?", (username,)).fetchall():
        delete_product_everything(conn, prod)
    st = get_store(conn, username)
    if st:
        for n in (st["logo_file"], st["banner_file"]):
            if n:
                delete_image_from_db(conn, n)
        conn.execute("DELETE FROM stores WHERE username = ?", (username,))
    conn.execute("UPDATE users SET account_type = 'personal', business_name = NULL WHERE username = ?", (username,))


@app.route("/api/store/delete", methods=["POST"])
def api_store_delete():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    conn = get_db()
    if not get_store(conn, session["username"]):
        conn.close()
        return jsonify({"ok": False}), 404
    delete_store_everything(conn, session["username"])
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "redirect": url_for("shop")})


@app.route("/api/business/enable", methods=["POST"])
def api_business_enable():
    """Eski mijozlar uchun: tezkor do'kon ochish (nom + telefon)."""
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    data = request.get_json(silent=True) or {}
    name = (data.get("business_name") or "").strip()[:40]
    phone = normalize_phone(data.get("phone"))
    if not name:
        return jsonify({"ok": False, "message": tr("business_name_required")}), 400
    if not phone:
        return jsonify({"ok": False, "message": tr("phone_invalid")}), 400
    me = session["username"]
    conn = get_db()
    if not get_store(conn, me):
        conn.execute("INSERT INTO stores (username, name, handle, phone, created_ts) VALUES (?, ?, ?, ?, ?)",
                     (me, name, unique_handle(conn, name), phone, int(time.time())))
        conn.execute("UPDATE users SET account_type = 'business', business_name = ?, phone = COALESCE(NULLIF(phone, ''), ?) WHERE username = ?",
                     (name, phone, me))
        conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ----- Do'kon paneli -----
def require_store(conn, me):
    st = get_store(conn, me)
    if not st:
        conn.close()
        return None
    return st


@app.route("/store/manage")
def store_manage():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    store = require_store(conn, me)
    if not store:
        return redirect(url_for("store_open"))
    st = request.args.get("st", "all")
    where = "WHERE p.seller_username = ?"
    if st == "active":
        where += " AND p.status = 'active'"
    elif st == "hidden":
        where += " AND p.status = 'hidden'"
    elif st == "out":
        where += " AND p.stock IS NOT NULL AND p.stock <= 0"
    else:
        st = "all"
    products = product_card_rows(conn, where, (me,), 80, 0)
    stats = conn.execute(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END), 0) AS active,
                  COALESCE(SUM(CASE WHEN status = 'hidden' THEN 1 ELSE 0 END), 0) AS hidden,
                  COALESCE(SUM(CASE WHEN stock IS NOT NULL AND stock <= 0 THEN 1 ELSE 0 END), 0) AS out
           FROM products WHERE seller_username = ?""", (me,)).fetchone()
    ostats = conn.execute(
        """SELECT COUNT(*) AS total,
                  COALESCE(SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END), 0) AS new,
                  COALESCE(SUM(CASE WHEN status = 'delivered' THEN total ELSE 0 END), 0) AS revenue
           FROM orders WHERE seller = ?""", (me,)).fetchone()
    conn.close()
    return render_template("store_manage.html", username=me, avatar_letter=session["avatar_letter"], store=store,
                           products=products, stats=stats, ostats=ostats, st=st, shop_tab="store", store_tab="products", active="shop")


@app.route("/api/store/product/<int:product_id>/toggle", methods=["POST"])
def api_store_product_toggle(product_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    conn = get_db()
    p = conn.execute("SELECT id, status FROM products WHERE id = ? AND seller_username = ?", (product_id, session["username"])).fetchone()
    if not p:
        conn.close()
        return jsonify({"ok": False}), 404
    new = "hidden" if p["status"] == "active" else "active"
    conn.execute("UPDATE products SET status = ? WHERE id = ?", (new, product_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "status": new})


def manageable_channels(conn, me):
    return conn.execute(
        """SELECT g.id, g.name FROM groups g JOIN group_members m ON m.group_id = g.id
           WHERE m.username = ? AND m.role IN ('owner', 'admin') AND g.kind = 'channel' ORDER BY g.name""", (me,)).fetchall()


def to_int_or_none(raw, minimum=0, maximum=2_000_000_000):
    raw = re.sub(r"\D", "", raw or "")
    if not raw:
        return None
    n = int(raw)
    return n if minimum <= n <= maximum else None


@app.route("/store/product/new", methods=["GET", "POST"])
@app.route("/store/product/<int:product_id>/edit", methods=["GET", "POST"])
def store_product_form(product_id=None):
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    store = require_store(conn, me)
    if not store:
        return redirect(url_for("store_open"))
    product, media = None, []
    if product_id:
        product = conn.execute("SELECT * FROM products WHERE id = ? AND seller_username = ?", (product_id, me)).fetchone()
        if not product:
            conn.close()
            return redirect(url_for("store_manage"))
        media = [r["filename"] for r in conn.execute(
            "SELECT filename FROM product_media WHERE product_id = ? ORDER BY position, id", (product_id,)).fetchall()]
        if not media and product["image_file"]:
            media = [product["image_file"]]
    channels = manageable_channels(conn, me)
    preset_channel = request.args.get("channel", type=int)

    if request.method == "POST":
        f = request.form
        title = f.get("title", "").strip()[:80]
        description = f.get("description", "").strip()[:1500]
        brand = f.get("brand", "").strip()[:40]
        price = to_int_or_none(f.get("price"), 1)
        old_price = to_int_or_none(f.get("old_price"), 1)
        if price and old_price and old_price <= price:
            old_price = None
        stock = to_int_or_none(f.get("stock"), 0, 1_000_000)
        category = f.get("category", "").strip()
        sub = f.get("subcategory", "").strip()
        if not catalog.valid_category(category):
            category, sub = "other", ""
        elif sub and not catalog.valid_category(category, sub):
            sub = ""
        system = catalog.size_system_for(category, sub)
        colors = ", ".join(catalog.clean_colors(f.getlist("colors")))
        sizes = ", ".join(catalog.clean_sizes(system, f.getlist("sizes"), f.get("custom_sizes", "")))
        channel_id = f.get("channel_id", type=int)
        if channel_id and member_role(conn, channel_id, me) not in ("owner", "admin"):
            channel_id = None
        status = "hidden" if f.get("hidden") else "active"

        if len(title) < 2 or not price:
            conn.close()
            flash(tr("product_invalid"))
            return redirect(request.url)
        keep = list(media)
        for name in f.getlist("remove_media"):
            if name in keep:
                keep.remove(name)
                delete_image_from_db(conn, name)
        new_files = [x for x in request.files.getlist("images") if x and x.filename and allowed_file(x.filename)]
        for x in new_files[: max(0, 8 - len(keep))]:
            try:
                keep.append(save_image_to_db(conn, x))
            except Exception:
                pass
        main = keep[0] if keep else None
        if product:
            conn.execute(
                """UPDATE products SET title = ?, description = ?, brand = ?, price = ?, old_price = ?, stock = ?, category = ?,
                          subcategory = ?, colors = ?, sizes = ?, channel_id = ?, status = ?, image_file = ? WHERE id = ?""",
                (title, description, brand, price, old_price, stock, category, sub, colors, sizes, channel_id, status, main, product["id"]))
            pid = product["id"]
            conn.execute("DELETE FROM product_media WHERE product_id = ?", (pid,))
        else:
            cur = conn.execute(
                """INSERT INTO products (seller_username, seller_avatar, title, description, brand, price, old_price, stock, category,
                          subcategory, colors, sizes, channel_id, status, image_file, created_at, created_ts)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (me, session["avatar_letter"], title, description, brand, price, old_price, stock, category, sub, colors, sizes,
                 channel_id, status, main, datetime.now().strftime("%d.%m %H:%M"), int(time.time())))
            pid = cur.lastrowid
        for i, name in enumerate(keep):
            conn.execute("INSERT INTO product_media (product_id, filename, position) VALUES (?, ?, ?)", (pid, name, i))
        conn.commit()
        conn.close()
        flash(tr("product_saved"))
        return redirect(url_for("product_page", product_id=pid))

    if product:
        p = dict(product)
        p["colors_list"] = [c.strip() for c in (product["colors"] or "").split(",") if c.strip()]
        sel_sizes = [c.strip() for c in (product["sizes"] or "").split(",") if c.strip()]
        system = catalog.size_system_for(product["category"] or "", product["subcategory"] or "")
        known = set(catalog.SIZE_SYSTEMS.get(system, []))
        p["sizes_list"] = [s for s in sel_sizes if s in known]
        p["custom_sizes"] = ", ".join(s for s in sel_sizes if s not in known)
    else:
        p = {"title": "", "description": "", "brand": "", "price": "", "old_price": "", "stock": "", "category": "",
             "subcategory": "", "colors_list": [], "sizes_list": [], "custom_sizes": "", "channel_id": preset_channel,
             "status": "active"}
    cart_count = cart_count_for(conn, me)
    conn.close()
    return render_template(
        "store_product_form.html", username=me, avatar_letter=session["avatar_letter"], store=store, p=p,
        editing=bool(product), media=media, channels=channels, cart_count=cart_count,
        catalog_json=catalog.catalog_payload(current_lang()), shop_tab="store", store_tab="products", active="shop",
    )


# ----- Mahsulot sahifasi -----
@app.route("/product/<int:product_id>")
def product_page(product_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    rows = product_card_rows(conn, "WHERE p.id = ?", (product_id,), 1, 0)
    if not rows:
        conn.close()
        return redirect(url_for("shop"))
    p = dict(rows[0])
    role = member_role(conn, p["channel_id"], me) if p["channel_id"] else None
    mine = p["seller_username"] == me
    if p["status"] != "active" and not (mine or g.is_admin or role in ("owner", "admin")):
        conn.close()
        flash(tr("product_unavailable"))
        return redirect(url_for("shop"))
    if not mine:
        conn.execute("UPDATE products SET views = COALESCE(views, 0) + 1 WHERE id = ?", (product_id,))
        conn.commit()
    media = [r["filename"] for r in conn.execute(
        "SELECT filename FROM product_media WHERE product_id = ? ORDER BY position, id", (product_id,)).fetchall()]
    if not media and p["image_file"]:
        media = [p["image_file"]]
    store = get_store(conn, p["seller_username"])
    seller = conn.execute("SELECT username, nickname, avatar_letter, avatar_file, last_seen_ts FROM users WHERE username = ?",
                          (p["seller_username"],)).fetchone()
    store_more = product_card_rows(conn, "WHERE p.seller_username = ? AND p.id != ? AND p.status = 'active'",
                                   (p["seller_username"], product_id), 6, 0)
    related = []
    if p["category"]:
        related = product_card_rows(conn, "WHERE p.category = ? AND p.id != ? AND p.seller_username != ? AND p.status = 'active'",
                                    (p["category"], product_id, p["seller_username"]), 6, 0)
    cart_count = cart_count_for(conn, me)
    conn.close()
    stock = p["stock"]
    return render_template(
        "product.html", username=me, avatar_letter=session["avatar_letter"], p=p, media=media,
        colors=catalog.display_options(p["colors"], "color", current_lang()),
        sizes=catalog.display_options(p["sizes"], "size", current_lang()),
        size_system_label=catalog.size_system_name(catalog.size_system_for(p["category"] or "", p["subcategory"] or ""), current_lang()),
        store=store, seller=seller, store_more=store_more, related=related,
        place=place_text(store["country"], store["region"], store["district"]) if store else "",
        is_mine=mine, can_delete=mine or g.is_admin or role in ("owner", "admin"),
        out_of_stock=(stock is not None and stock <= 0), stock=stock,
        discount=(round((p["old_price"] - p["price"]) * 100 / p["old_price"]) if p["old_price"] and p["old_price"] > p["price"] else 0),
        cart_count=cart_count, shop_tab="home", active="shop",
    )


@app.route("/api/products/delete/<int:product_id>", methods=["POST"])
def api_product_delete(product_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not product:
        conn.close()
        return jsonify({"error": "ruxsat yo'q"}), 403
    role = member_role(conn, product["channel_id"], session["username"]) if product["channel_id"] else None
    if product["seller_username"] != session["username"] and not g.is_admin and role not in ("owner", "admin"):
        conn.close()
        return jsonify({"error": "ruxsat yo'q"}), 403
    delete_product_everything(conn, product)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


def delete_product_everything(conn, product):
    names = {r["filename"] for r in conn.execute("SELECT filename FROM product_media WHERE product_id = ?", (product["id"],)).fetchall()}
    if product["image_file"]:
        names.add(product["image_file"])
    for n in names:
        delete_image_from_db(conn, n)
    conn.execute("DELETE FROM product_media WHERE product_id = ?", (product["id"],))
    conn.execute("DELETE FROM cart_lines WHERE product_id = ?", (product["id"],))
    conn.execute("DELETE FROM cart_items WHERE product_id = ?", (product["id"],))
    conn.execute("DELETE FROM products WHERE id = ?", (product["id"],))


def cart_total_count(conn, me):
    return cart_count_for(conn, me)


def cart_qty_of_product(conn, me, product_id):
    return conn.execute("SELECT COALESCE(SUM(qty), 0) AS c FROM cart_lines WHERE username = ? AND product_id = ?",
                        (me, product_id)).fetchone()["c"]


def stock_error(stock):
    return tr("cart_stock_limit").replace("{n}", str(max(int(stock), 0)))


@app.route("/api/cart/add/<int:product_id>", methods=["POST"])
def api_cart_add(product_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401
    me = session["username"]
    data = request.get_json(silent=True) or {}
    conn = get_db()
    p = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if not p or p["status"] != "active":
        conn.close()
        return jsonify({"ok": False, "message": tr("product_unavailable")}), 404
    if p["seller_username"] == me:
        conn.close()
        return jsonify({"ok": False, "message": tr("cart_own_product")}), 400
    colors, sizes = parse_options(p["colors"]), parse_options(p["sizes"])
    color = (data.get("color") or "").strip()
    size = (data.get("size") or "").strip()
    if (colors and color not in colors) or (sizes and size not in sizes):
        conn.close()
        return jsonify({"ok": False, "need_options": True, "message": tr("cart_choose_options")}), 400
    if not colors:
        color = ""
    if not sizes:
        size = ""
    try:
        qty = max(1, min(99, int(data.get("qty") or 1)))
    except (TypeError, ValueError):
        qty = 1
    if p["stock"] is not None and cart_qty_of_product(conn, me, product_id) + qty > p["stock"]:
        conn.close()
        return jsonify({"ok": False, "message": stock_error(p["stock"]) if p["stock"] > 0 else tr("product_out_of_stock")}), 400
    existing = conn.execute(
        "SELECT id, qty FROM cart_lines WHERE username = ? AND product_id = ? AND color = ? AND size = ?",
        (me, product_id, color, size),
    ).fetchone()
    if existing:
        conn.execute("UPDATE cart_lines SET qty = ? WHERE id = ?", (min(99, existing["qty"] + qty), existing["id"]))
    else:
        conn.execute("INSERT INTO cart_lines (username, product_id, qty, color, size) VALUES (?, ?, ?, ?, ?)",
                     (me, product_id, qty, color, size))
    conn.commit()
    count = cart_count_for(conn, me)
    conn.close()
    return jsonify({"ok": True, "cart_count": count})


@app.route("/api/cart/qty/<int:line_id>", methods=["POST"])
def api_cart_qty(line_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401
    me = session["username"]
    data = request.get_json(silent=True) or {}
    conn = get_db()
    line = conn.execute("SELECT id, qty, product_id FROM cart_lines WHERE id = ? AND username = ?", (line_id, me)).fetchone()
    if not line:
        conn.close()
        return jsonify({"ok": False}), 404
    try:
        delta = int(data.get("delta") or 0)
    except (TypeError, ValueError):
        delta = 0
    qty = max(1, min(99, line["qty"] + delta))
    message = ""
    if delta > 0:
        p = conn.execute("SELECT stock FROM products WHERE id = ?", (line["product_id"],)).fetchone()
        if p and p["stock"] is not None and cart_qty_of_product(conn, me, line["product_id"]) + (qty - line["qty"]) > p["stock"]:
            qty = line["qty"]
            message = stock_error(p["stock"]) if p["stock"] > 0 else tr("product_out_of_stock")
    conn.execute("UPDATE cart_lines SET qty = ? WHERE id = ?", (qty, line_id))
    conn.commit()
    count = cart_count_for(conn, me)
    conn.close()
    return jsonify({"ok": True, "qty": qty, "cart_count": count, "message": message})


@app.route("/api/cart/remove/<int:cart_id>", methods=["POST"])
def api_cart_remove(cart_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401
    conn = get_db()
    conn.execute("DELETE FROM cart_lines WHERE id = ? AND username = ?", (cart_id, session["username"]))
    conn.commit()
    count = cart_count_for(conn, session["username"])
    conn.close()
    return jsonify({"ok": True, "cart_count": count})


def cart_groups(conn, me):
    """Savatdagi mahsulotlar do'konlar bo'yicha guruhlanadi."""
    lines = conn.execute(
        """SELECT cl.id AS line_id, cl.qty, cl.color, cl.size, p.id AS product_id, p.title, p.price, p.image_file, p.stock, p.status,
                  p.seller_username, COALESCE(s.name, u.business_name, u.nickname, p.seller_username) AS store_name,
                  s.handle AS store_handle, s.logo_file AS store_logo
           FROM cart_lines cl JOIN products p ON p.id = cl.product_id
           LEFT JOIN users u ON u.username = p.seller_username
           LEFT JOIN stores s ON s.username = p.seller_username
           WHERE cl.username = ? ORDER BY p.seller_username, cl.id""",
        (me,),
    ).fetchall()
    groups_ = {}
    for l in lines:
        gr = groups_.setdefault(l["seller_username"], {
            "seller": l["seller_username"], "name": l["store_name"], "handle": l["store_handle"], "logo": l["store_logo"],
            "lines": [], "total": 0,
        })
        gr["lines"].append(l)
        gr["total"] += l["price"] * l["qty"]
    return list(groups_.values())


@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    groups_ = cart_groups(conn, me)
    u = conn.execute("SELECT country, region, district, phone FROM users WHERE username = ?", (me,)).fetchone()
    cart_count = cart_count_for(conn, me)
    conn.close()
    total = sum(gr["total"] for gr in groups_)
    return render_template(
        "cart.html", username=me, avatar_letter=session["avatar_letter"], groups=groups_, total=total,
        addr=dict(u) if u else {}, countries=locations.country_list(current_lang()),
        cart_count=cart_count, shop_tab="cart", active="shop",
    )


def fmt_money(n):
    return "{:,}".format(int(n)).replace(",", " ")


def send_order_dm(conn, sender, receiver, text):
    conn.execute(
        "INSERT INTO private_messages (sender, receiver, content, image_file, media_kind, duration, created_at, created_ts, is_read) "
        "VALUES (?, ?, ?, NULL, 'order', NULL, ?, ?, 0)",
        (sender, receiver, text[:1800], datetime.now().strftime("%H:%M"), int(time.time())),
    )


@app.route("/checkout", methods=["POST"])
def checkout():
    """Buyurtma: har bir do'konga uning mahsulotlari bo'yicha alohida buyurtma va chatga xabar yuboriladi.
    To'lov hozircha online emas - do'kon bilan chatda kelishiladi."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    country = request.form.get("country", "").strip()
    region = request.form.get("region", "").strip()
    district = request.form.get("district", "").strip()
    address = request.form.get("address", "").strip()[:200]
    note = request.form.get("note", "").strip()[:300]
    phone = normalize_phone(request.form.get("phone"))

    conn = get_db()
    groups_ = cart_groups(conn, me)
    error = None
    if not groups_:
        error = tr("cart_empty_error")
    elif not country or not locations.is_valid(country, region, district):
        error = tr("order_location_required")
    elif locations.region_list(country) and not region:
        error = tr("order_location_required")
    elif region and locations.district_list(country, region) and not district:
        error = tr("order_location_required")
    elif not phone:
        error = tr("phone_invalid")
    if not error:  # mavjudlik va ombor qoldig'i
        totals = {}
        for gr in groups_:
            for l in gr["lines"]:
                totals[l["product_id"]] = totals.get(l["product_id"], 0) + l["qty"]
                if l["status"] != "active":
                    error = tr("cart_item_unavailable").replace("{name}", l["title"])
                    break
            if error:
                break
        if not error:
            for gr in groups_:
                for l in gr["lines"]:
                    if l["stock"] is not None and totals[l["product_id"]] > l["stock"]:
                        error = tr("cart_item_unavailable").replace("{name}", l["title"])
                        break
                if error:
                    break
    if error:
        conn.close()
        flash(error)
        return redirect(url_for("cart"))

    lang = current_lang()
    sent = 0
    for gr in groups_:
        seller = gr["seller"]
        if is_blocked_between(conn, me, seller):
            continue
        cur = conn.execute(
            "INSERT INTO orders (buyer, seller, total, country, region, district, address, phone, note, status, created_ts, updated_ts) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'new', ?, ?)",
            (me, seller, gr["total"], country, region, district, address, phone, note, int(time.time()), int(time.time())),
        )
        oid = cur.lastrowid
        lines_txt = []
        for l in gr["lines"]:
            conn.execute(
                "INSERT INTO order_items (order_id, product_id, title, price, qty, color, size, image_file) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (oid, l["product_id"], l["title"], l["price"], l["qty"], l["color"], l["size"], l["image_file"]),
            )
            conn.execute(
                "UPDATE products SET sold = COALESCE(sold, 0) + ?, stock = CASE WHEN stock IS NULL THEN NULL ELSE stock - ? END WHERE id = ?",
                (l["qty"], l["qty"], l["product_id"]),
            )
            opts = " · ".join(x for x in (catalog.color_name(l["color"], lang) if l["color"] else "",
                                          catalog.size_label(l["size"], lang) if l["size"] else "") if x)
            lines_txt.append(f"• {l['title']}" + (f" ({opts})" if opts else "") +
                             f" × {l['qty']} — {fmt_money(l['price'] * l['qty'])} {tr('currency_sum')}")
            conn.execute("DELETE FROM cart_lines WHERE id = ?", (l["line_id"],))
        place = place_text(country, region, district, lang)
        text = "\n".join([
            f"🛒 {tr('order_title')} #{oid}",
            *lines_txt,
            f"{tr('order_total')}: {fmt_money(gr['total'])} {tr('currency_sum')}",
            f"📍 {place}",
            *([f"🏠 {address}"] if address else []),
            f"📞 {phone}",
            *([f"💬 {note}"] if note else []),
        ])
        send_order_dm(conn, me, seller, text)
        sent += 1
    conn.execute("UPDATE users SET country = COALESCE(NULLIF(country, ''), ?), region = COALESCE(NULLIF(region, ''), ?), "
                 "district = COALESCE(NULLIF(district, ''), ?), phone = COALESCE(NULLIF(phone, ''), ?) WHERE username = ?",
                 (country, region, district, phone, me))
    conn.commit()
    conn.close()

    if not sent:
        flash(tr("chat_blocked_msg"))
        return redirect(url_for("cart"))
    flash(tr("order_sent"))
    return redirect(url_for("orders"))


# ----- Buyurtmalar -----
def orders_with_items(conn, where_sql, params, limit=60):
    rows = conn.execute(
        f"""SELECT o.*, COALESCE(s.name, us.business_name, us.nickname, o.seller) AS store_name, s.handle AS store_handle,
                   s.logo_file AS store_logo, COALESCE(ub.nickname, o.buyer) AS buyer_name, ub.avatar_letter AS buyer_letter,
                   ub.avatar_file AS buyer_avatar
            FROM orders o LEFT JOIN stores s ON s.username = o.seller
            LEFT JOIN users us ON us.username = o.seller LEFT JOIN users ub ON ub.username = o.buyer
            {where_sql} ORDER BY o.id DESC LIMIT ?""", (*params, limit)).fetchall()
    ids = [r["id"] for r in rows]
    items = {}
    if ids:
        marks = ",".join("?" for _ in ids)
        for it in conn.execute(f"SELECT * FROM order_items WHERE order_id IN ({marks}) ORDER BY id", tuple(ids)).fetchall():
            items.setdefault(it["order_id"], []).append(it)
    out = []
    for r in rows:
        d = dict(r)
        d["items"] = items.get(r["id"], [])
        d["place"] = place_text(r["country"], r["region"], r["district"])
        d["ago"] = time_ago(r["created_ts"], "")
        out.append(d)
    return out


@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    rows = orders_with_items(conn, "WHERE o.buyer = ?", (me,))
    my_store = get_store(conn, me)
    cart_count = cart_count_for(conn, me)
    conn.close()
    return render_template("orders.html", username=me, avatar_letter=session["avatar_letter"], orders=rows,
                           my_store=my_store, cart_count=cart_count, shop_tab="orders", active="shop")


@app.route("/store/orders")
def store_orders():
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    store = require_store(conn, me)
    if not store:
        return redirect(url_for("store_open"))
    st = request.args.get("st", "all")
    if st in ORDER_STATUSES:
        rows = orders_with_items(conn, "WHERE o.seller = ? AND o.status = ?", (me, st))
    else:
        st = "all"
        rows = orders_with_items(conn, "WHERE o.seller = ?", (me,))
    counts = {r["status"]: r["n"] for r in conn.execute(
        "SELECT status, COUNT(*) AS n FROM orders WHERE seller = ? GROUP BY status", (me,)).fetchall()}
    conn.close()
    return render_template("store_orders.html", username=me, avatar_letter=session["avatar_letter"], store=store,
                           orders=rows, st=st, counts=counts, total_count=sum(counts.values()),
                           shop_tab="store", store_tab="orders", active="shop")


SELLER_FLOW = {"new": ("confirmed", "cancelled"), "confirmed": ("shipped", "cancelled"), "shipped": ("delivered",)}


@app.route("/api/orders/<int:order_id>/status", methods=["POST"])
def api_order_status(order_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    new = ((request.get_json(silent=True) or {}).get("status") or "").strip()
    if new not in ORDER_STATUSES:
        return jsonify({"ok": False}), 400
    conn = get_db()
    o = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    if not o or me not in (o["buyer"], o["seller"]):
        conn.close()
        return jsonify({"ok": False}), 404
    if me == o["seller"]:
        allowed = SELLER_FLOW.get(o["status"], ())
    else:
        allowed = ("cancelled",) if o["status"] == "new" else ()
    if new not in allowed:
        conn.close()
        return jsonify({"ok": False, "message": tr("order_status_forbidden")}), 400
    conn.execute("UPDATE orders SET status = ?, updated_ts = ? WHERE id = ?", (new, int(time.time()), order_id))
    if new == "cancelled":
        for it in conn.execute("SELECT product_id, qty FROM order_items WHERE order_id = ?", (order_id,)).fetchall():
            if it["product_id"]:
                conn.execute(
                    "UPDATE products SET stock = CASE WHEN stock IS NULL THEN NULL ELSE stock + ? END, "
                    "sold = CASE WHEN COALESCE(sold, 0) >= ? THEN sold - ? ELSE 0 END WHERE id = ?",
                    (it["qty"], it["qty"], it["qty"], it["product_id"]))
    other = o["buyer"] if me == o["seller"] else o["seller"]
    send_order_dm(conn, me, other, f"📦 {tr('order_title')} #{order_id}: {tr('order_status_' + new)}")
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "status": new, "label": tr("order_status_" + new)})



@app.route("/people")
def people():
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    query = request.args.get("q", "").strip()
    conn = get_db()

    my_contacts = conn.execute(
        """SELECT users.username, users.avatar_letter, users.avatar_file, users.nickname
           FROM contacts JOIN users ON contacts.contact_username = users.username
           WHERE contacts.username = ? ORDER BY users.username""",
        (me,),
    ).fetchall()

    incoming_requests = conn.execute(
        """SELECT contact_requests.id, users.username, users.avatar_letter, users.avatar_file
           FROM contact_requests JOIN users ON contact_requests.from_username = users.username
           WHERE contact_requests.to_username = ? ORDER BY contact_requests.id DESC""",
        (me,),
    ).fetchall()

    search_results = []
    query = query.lstrip("@").strip()
    if query:
        like = f"%{query}%"
        rows = conn.execute(
            """SELECT u.username, u.avatar_letter, u.avatar_file, u.nickname FROM users u
               WHERE (LOWER(u.username) LIKE LOWER(?) OR LOWER(COALESCE(u.nickname, '')) LIKE LOWER(?))
                 AND u.username NOT IN (SELECT username FROM blocked_users)
               ORDER BY (CASE WHEN LOWER(u.username) = LOWER(?) OR LOWER(COALESCE(u.nickname, '')) = LOWER(?) THEN 0 ELSE 1 END),
                        u.username
               LIMIT 30""",
            (like, like, query, query),
        ).fetchall()
        contact_names = {c["username"] for c in my_contacts}
        pending_out = {
            r["to_username"]
            for r in conn.execute(
                "SELECT to_username FROM contact_requests WHERE from_username = ?", (me,)
            ).fetchall()
        }
        for r in rows:
            search_results.append({
                "username": r["username"],
                "avatar_letter": r["avatar_letter"],
                "avatar_file": r["avatar_file"],
                "nickname": r["nickname"],
                "is_me": r["username"] == me,
                "is_contact": r["username"] in contact_names,
                "is_pending": r["username"] in pending_out,
            })

    conn.close()

    return render_template(
        "people.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        my_contacts=my_contacts,
        incoming_requests=incoming_requests,
        search_results=search_results,
        query=query,
        active="people",
    )


@app.route("/api/contacts/request/<to_username>", methods=["POST"])
def api_contact_request(to_username):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    me = session["username"]
    if to_username == me:
        return jsonify({"error": "bu siz"}), 400

    conn = get_db()

    already = conn.execute(
        "SELECT 1 FROM contacts WHERE username = ? AND contact_username = ?", (me, to_username)
    ).fetchone()
    if already:
        conn.close()
        return jsonify({"status": "already_contact"})

    # Agar qarshi tomon allaqachon so'rov yuborgan bo'lsa - avtomatik ikkalasini ham qo'shamiz
    reverse = conn.execute(
        "SELECT id FROM contact_requests WHERE from_username = ? AND to_username = ?",
        (to_username, me),
    ).fetchone()

    if reverse:
        conn.execute("DELETE FROM contact_requests WHERE id = ?", (reverse["id"],))
        conn.execute(
            "INSERT OR IGNORE INTO contacts (username, contact_username) VALUES (?, ?)", (me, to_username)
        )
        conn.execute(
            "INSERT OR IGNORE INTO contacts (username, contact_username) VALUES (?, ?)", (to_username, me)
        )
        conn.commit()
        conn.close()
        return jsonify({"status": "accepted"})

    if is_blocked_between(conn, me, to_username):
        conn.close()
        return jsonify({"error": "blocked", "message": tr("chat_blocked_msg")}), 403
    if get_prefs(conn, to_username)["allow_requests"] == "nobody":
        conn.close()
        return jsonify({"error": "not_allowed", "message": tr("request_not_allowed")}), 403

    conn.execute(
        "INSERT OR IGNORE INTO contact_requests (from_username, to_username, created_at) VALUES (?, ?, ?)",
        (me, to_username, datetime.now().strftime("%d.%m %H:%M")),
    )
    conn.commit()
    conn.close()
    return jsonify({"status": "requested"})


@app.route("/api/contacts/accept/<int:request_id>", methods=["POST"])
def api_contact_accept(request_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    me = session["username"]
    conn = get_db()
    req = conn.execute(
        "SELECT * FROM contact_requests WHERE id = ? AND to_username = ?", (request_id, me)
    ).fetchone()

    if not req:
        conn.close()
        return jsonify({"error": "topilmadi"}), 404

    conn.execute(
        "INSERT OR IGNORE INTO contacts (username, contact_username) VALUES (?, ?)",
        (me, req["from_username"]),
    )
    conn.execute(
        "INSERT OR IGNORE INTO contacts (username, contact_username) VALUES (?, ?)",
        (req["from_username"], me),
    )
    conn.execute("DELETE FROM contact_requests WHERE id = ?", (request_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/contacts/decline/<int:request_id>", methods=["POST"])
def api_contact_decline(request_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    conn.execute(
        "DELETE FROM contact_requests WHERE id = ? AND to_username = ?",
        (request_id, session["username"]),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})



# ---------------- QR kod (tashqi kutubxonasiz, sof Python) ----------------
_QR_ECC_PER_BLOCK = {  # [daraja][versiya 1..10]
    "L": (-1, 7, 10, 15, 20, 26, 18, 20, 24, 30, 18),
    "M": (-1, 10, 16, 26, 18, 24, 16, 18, 22, 22, 26),
}
_QR_NUM_BLOCKS = {
    "L": (-1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 4),
    "M": (-1, 1, 1, 1, 2, 2, 4, 4, 4, 5, 5),
}
_QR_FORMAT_BITS = {"L": 1, "M": 0}


def _qr_raw_modules(ver):
    result = (16 * ver + 128) * ver + 64
    if ver >= 2:
        numalign = ver // 7 + 2
        result -= (25 * numalign - 10) * numalign - 55
        if ver >= 7:
            result -= 36
    return result


def _qr_align_positions(ver):
    if ver == 1:
        return []
    numalign = ver // 7 + 2
    size = ver * 4 + 17
    step = (ver * 4 + numalign * 2 + 1) // (numalign * 2 - 2) * 2
    result = [size - 7 - i * step for i in range(numalign - 1)] + [6]
    return list(reversed(result))


def _gf_mul(x, y):
    z = 0
    for i in range(7, -1, -1):
        z = (z << 1) ^ ((z >> 7) * 0x11D)
        z ^= ((y >> i) & 1) * x
    return z


def _rs_divisor(degree):
    result = [0] * (degree - 1) + [1]
    root = 1
    for _ in range(degree):
        for j in range(degree):
            result[j] = _gf_mul(result[j], root)
            if j + 1 < degree:
                result[j] ^= result[j + 1]
        root = _gf_mul(root, 0x02)
    return result


def _rs_remainder(data, divisor):
    result = [0] * len(divisor)
    for b in data:
        factor = b ^ result.pop(0)
        result.append(0)
        for i, coef in enumerate(divisor):
            result[i] ^= _gf_mul(coef, factor)
    return result


def qr_matrix(text, ecc="M"):
    """Matnni QR kod matritsasiga aylantiradi (True = qora modul). Byte rejimi, 1..8 versiya."""
    data = text.encode("utf-8")
    for ecc_level in (ecc, "L"):
        for ver in range(1, 9):
            capacity = _qr_raw_modules(ver) // 8 - _QR_ECC_PER_BLOCK[ecc_level][ver] * _QR_NUM_BLOCKS[ecc_level][ver]
            cc_bits = 8 if ver < 10 else 16
            if 4 + cc_bits + len(data) * 8 <= capacity * 8:
                break
        else:
            continue
        break
    else:
        raise ValueError("matn juda uzun")

    # --- ma'lumot bitlari
    bits = []
    def put(val, n):
        bits.extend((val >> i) & 1 for i in range(n - 1, -1, -1))
    put(0b0100, 4)
    put(len(data), cc_bits)
    for b in data:
        put(b, 8)
    cap_bits = capacity * 8
    put(0, min(4, cap_bits - len(bits)))
    put(0, -len(bits) % 8)
    pad = 0xEC
    while len(bits) < cap_bits:
        put(pad, 8)
        pad ^= 0xEC ^ 0x11
    codewords = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]

    # --- Reed-Solomon va bloklarni aralashtirish
    numblocks = _QR_NUM_BLOCKS[ecc_level][ver]
    blockecc = _QR_ECC_PER_BLOCK[ecc_level][ver]
    rawcw = _qr_raw_modules(ver) // 8
    numshort = numblocks - rawcw % numblocks
    shortlen = rawcw // numblocks
    divisor = _rs_divisor(blockecc)
    blocks, k = [], 0
    for i in range(numblocks):
        datlen = shortlen - blockecc + (0 if i < numshort else 1)
        dat = codewords[k:k + datlen]
        k += datlen
        ecc_bytes = _rs_remainder(dat, divisor)
        if i < numshort:
            dat = dat + [0]
        blocks.append(dat + ecc_bytes)
    final = []
    for i in range(len(blocks[0])):
        for j, blk in enumerate(blocks):
            if i != shortlen - blockecc or j >= numshort:
                final.append(blk[i])

    # --- matritsa va funksional modullar
    size = ver * 4 + 17
    modules = [[False] * size for _ in range(size)]
    isfunc = [[False] * size for _ in range(size)]

    def setf(x, y, dark):
        modules[y][x] = dark
        isfunc[y][x] = True

    for i in range(size):
        setf(6, i, i % 2 == 0)
        setf(i, 6, i % 2 == 0)
    for cx, cy in ((3, 3), (size - 4, 3), (3, size - 4)):
        for dy in range(-4, 5):
            for dx in range(-4, 5):
                xx, yy = cx + dx, cy + dy
                if 0 <= xx < size and 0 <= yy < size:
                    setf(xx, yy, max(abs(dx), abs(dy)) not in (2, 4))
    pos = _qr_align_positions(ver)
    for i, ax in enumerate(pos):
        for j, ay in enumerate(pos):
            if (i == 0 and j == 0) or (i == 0 and j == len(pos) - 1) or (i == len(pos) - 1 and j == 0):
                continue
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    setf(ax + dx, ay + dy, max(abs(dx), abs(dy)) != 1)

    def draw_format(mask):
        fdata = (_QR_FORMAT_BITS[ecc_level] << 3) | mask
        rem = fdata
        for _ in range(10):
            rem = (rem << 1) ^ ((rem >> 9) * 0x537)
        fbits = ((fdata << 10) | rem) ^ 0x5412
        bit = lambda i: ((fbits >> i) & 1) != 0
        for i in range(0, 6):
            setf(8, i, bit(i))
        setf(8, 7, bit(6))
        setf(8, 8, bit(7))
        setf(7, 8, bit(8))
        for i in range(9, 15):
            setf(14 - i, 8, bit(i))
        for i in range(0, 8):
            setf(size - 1 - i, 8, bit(i))
        for i in range(8, 15):
            setf(8, size - 15 + i, bit(i))
        setf(8, size - 8, True)

    def draw_version():
        if ver < 7:
            return
        rem = ver
        for _ in range(12):
            rem = (rem << 1) ^ ((rem >> 11) * 0x1F25)
        vbits = (ver << 12) | rem
        for i in range(18):
            b = ((vbits >> i) & 1) != 0
            a, c = size - 11 + i % 3, i // 3
            setf(a, c, b)
            setf(c, a, b)

    draw_format(0)
    draw_version()

    # --- ma'lumotni zigzag tartibida joylash
    i = 0
    x = size - 1
    while x >= 1:
        if x == 6:
            x = 5
        for vert in range(size):
            for j in range(2):
                xx = x - j
                upward = ((x + 1) & 2) == 0
                yy = (size - 1 - vert) if upward else vert
                if not isfunc[yy][xx] and i < len(final) * 8:
                    modules[yy][xx] = ((final[i >> 3] >> (7 - (i & 7))) & 1) != 0
                    i += 1
        x -= 2

    masks = [
        lambda x, y: (x + y) % 2 == 0,
        lambda x, y: y % 2 == 0,
        lambda x, y: x % 3 == 0,
        lambda x, y: (x + y) % 3 == 0,
        lambda x, y: (x // 3 + y // 2) % 2 == 0,
        lambda x, y: x * y % 2 + x * y % 3 == 0,
        lambda x, y: (x * y % 2 + x * y % 3) % 2 == 0,
        lambda x, y: ((x + y) % 2 + x * y % 3) % 2 == 0,
    ]

    def apply_mask(m):
        for yy in range(size):
            for xx in range(size):
                if not isfunc[yy][xx] and masks[m](xx, yy):
                    modules[yy][xx] = not modules[yy][xx]

    def penalty():
        score = 0
        for grid in (modules, [list(r) for r in zip(*modules)]):
            for row in grid:
                run, prev = 1, row[0]
                for v in row[1:]:
                    if v == prev:
                        run += 1
                    else:
                        if run >= 5:
                            score += 3 + run - 5
                        run, prev = 1, v
                if run >= 5:
                    score += 3 + run - 5
        for yy in range(size - 1):
            for xx in range(size - 1):
                if modules[yy][xx] == modules[yy][xx + 1] == modules[yy + 1][xx] == modules[yy + 1][xx + 1]:
                    score += 3
        dark = sum(sum(r) for r in modules)
        total = size * size
        k2 = (abs(dark * 20 - total * 10) + total - 1) // total - 1
        return score + k2 * 10

    best, best_mask = None, 0
    for m in range(8):
        apply_mask(m)
        draw_format(m)
        pen = penalty()
        if best is None or pen < best:
            best, best_mask = pen, m
        apply_mask(m)  # qaytarib olamiz
    apply_mask(best_mask)
    draw_format(best_mask)
    return modules


def qr_svg(text, border=4):
    """QR kodni SVG (vektor) ko'rinishida qaytaradi - har qanday ekranda aniq ko'rinadi."""
    m = qr_matrix(text)
    n = len(m) + border * 2
    parts = []
    for y, row in enumerate(m):
        x = 0
        while x < len(row):
            if row[x]:
                start = x
                while x < len(row) and row[x]:
                    x += 1
                parts.append(f"M{start + border},{y + border}h{x - start}v1h-{x - start}z")
            else:
                x += 1
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" shape-rendering="crispEdges" '
        f'width="100%" height="100%"><rect width="{n}" height="{n}" fill="#fff"/>'
        f'<path d="{"".join(parts)}" fill="#000"/></svg>'
    )


def generate_qr_base64(data):
    if not qrcode:
        return None
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@app.route("/qr")
def qr_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    add_url = request.host_url.rstrip("/") + url_for("user_profile", target_username=session["username"])
    try:
        qr_svg_markup = qr_svg(add_url)
    except Exception:
        qr_svg_markup = None

    return render_template(
        "qr.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        qr_svg=qr_svg_markup,
        add_url=add_url,
        nickname=session.get("nickname"),
        active="people",
    )


@app.route("/scan")
def scan_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "scan.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        active="home",
    )


@app.route("/add/<target_username>")
def add_contact_page(target_username):
    """Eski QR kodlar uchun: ochiq profilga yo'naltiradi."""
    return redirect(url_for("user_profile", target_username=target_username))


@app.route("/u/<target_username>")
def user_profile(target_username):
    """Boshqa odamning ochiq profili (QR skanerlash yoki qidiruvdan keyin shu ochiladi)."""
    me = session["username"]
    if target_username == me:
        return redirect(url_for("profile"))

    conn = get_db()
    target = conn.execute("SELECT * FROM users WHERE username = ?", (target_username,)).fetchone()
    blocked = conn.execute(
        "SELECT 1 FROM blocked_users WHERE username = ?", (target_username,)
    ).fetchone() if target else None

    if not target or (blocked and not g.is_admin):
        conn.close()
        flash(tr("profile_not_found"))
        return redirect(url_for("people"))

    is_contact = conn.execute(
        "SELECT 1 FROM contacts WHERE username = ? AND contact_username = ?", (me, target_username)
    ).fetchone()
    is_pending = conn.execute(
        "SELECT 1 FROM contact_requests WHERE from_username = ? AND to_username = ?", (me, target_username)
    ).fetchone()
    posts = build_post_cards(
        conn,
        conn.execute("SELECT * FROM posts WHERE username = ? ORDER BY id DESC LIMIT 20", (target_username,)).fetchall(),
        me,
    )
    products = conn.execute(
        "SELECT * FROM products WHERE seller_username = ? AND status = 'active' ORDER BY id DESC LIMIT 20", (target_username,)
    ).fetchall()
    target_store = get_store(conn, target_username)
    presence = presence_info(conn, me, target_username, None, target["last_seen_ts"])
    contacts_count = conn.execute("SELECT COUNT(*) AS c FROM contacts WHERE username = ?", (target_username,)).fetchone()["c"]
    conn.close()

    return render_template(
        "add_contact.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        target=target,
        is_contact=bool(is_contact),
        is_pending=bool(is_pending),
        is_blocked=bool(blocked),
        target_is_admin=bool(target["is_admin"]) or target["username"].lower() in ADMIN_USERNAMES,
        posts=posts,
        products=products,
        presence=presence,
        contacts_count=contacts_count,
        location_text=user_location_text(target),
        is_business=bool(target_store),
        store=target_store,
        active="people",
    )


@app.route("/dm/<other_username>")
def dm(other_username):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    other = conn.execute(
        "SELECT * FROM users WHERE username = ?", (other_username,)
    ).fetchone()
    i_blocked = False
    peer = None
    muted = False
    if other:
        i_blocked = bool(conn.execute(
            "SELECT 1 FROM user_blocks WHERE blocker = ? AND blocked = ?", (session["username"], other["username"])
        ).fetchone())
        peer = presence_info(conn, session["username"], other["username"], None, other["last_seen_ts"])
        muted = ("dm:" + other["username"]) in muted_keys(conn, session["username"])
    conn.close()

    if not other:
        return redirect(url_for("people"))

    return render_template(
        "dm.html",
        i_blocked=i_blocked,
        peer=peer,
        chat_muted=muted,
        can_post=True,
        other_display=other["nickname"] or other["username"],
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        other_username=other["username"],
        other_avatar=other["avatar_letter"],
        other_avatar_file=other["avatar_file"],
        active="shaxsiy",
    )


AUDIO_EXT = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a", "audio/x-m4a": "m4a", "audio/m4a": "m4a",
             "audio/mpeg": "mp3", "audio/wav": "wav", "audio/x-wav": "wav", "audio/aac": "aac",
             "video/webm": "webm", "video/mp4": "mp4", "video/quicktime": "mov"}
MAX_AUDIO_BYTES = 10 * 1024 * 1024
MAX_VNOTE_BYTES = 25 * 1024 * 1024


def save_chat_blob(conn, file_storage, kind):
    """Ovozli xabar (audio) yoki dumaloq video xabarni bazaga saqlaydi. Xato: ValueError('bad_type'|'empty'|'too_big')."""
    mime = (file_storage.mimetype or "").split(";")[0].strip().lower()
    if kind == "audio":
        allowed = {m for m in AUDIO_EXT if m.startswith("audio/")} | {"video/webm", "video/mp4"}
        limit, prefix = MAX_AUDIO_BYTES, "a"
    else:
        allowed = {"video/webm", "video/mp4", "video/quicktime"}
        limit, prefix = MAX_VNOTE_BYTES, "n"
    if mime not in allowed:
        raise ValueError("bad_type")
    data = file_storage.read()
    if not data:
        raise ValueError("empty")
    if len(data) > limit:
        raise ValueError("too_big")
    name = f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S%f')}_{secrets.token_hex(3)}.{AUDIO_EXT[mime]}"
    db_data = psycopg2.Binary(data) if USE_POSTGRES else data
    conn.execute(
        "INSERT INTO uploaded_images (filename, mimetype, data, created_at) VALUES (?, ?, ?, ?)",
        (name, mime, db_data, datetime.now().strftime("%d.%m.%Y %H:%M")),
    )
    return name


def serialize_chat_rows(conn, rows, table, author_col, read_visible=False):
    """Xabarlar ro'yxatini JSON'ga tayyorlaydi (reply bilan birga)."""
    reply_ids = {r["reply_to"] for r in rows if r["reply_to"]}
    replies = {}
    if reply_ids:
        marks = ",".join("?" for _ in reply_ids)
        for rr in conn.execute(
            f"SELECT id, {author_col} AS author, content, image_file, media_kind FROM {table} WHERE id IN ({marks})",
            tuple(reply_ids),
        ).fetchall():
            k = rr["media_kind"] or ("image" if rr["image_file"] else "text")
            replies[rr["id"]] = {"id": rr["id"], "author": rr["author"], "text": (rr["content"] or "")[:80], "kind": k}
    out = []
    for r in rows:
        kind = r["media_kind"] or ("image" if r["image_file"] else "text")
        out.append({
            "id": r["id"],
            "author": r[author_col],
            "content": r["content"],
            "image_file": r["image_file"],
            "kind": kind,
            "duration": r["duration"] or 0,
            "reply": replies.get(r["reply_to"]) if r["reply_to"] else None,
            "created_at": r["created_at"],
            "read": bool(read_visible and table == "private_messages" and r["is_read"]),
        })
    return out


def read_chat_payload(conn, table, scope_sql, scope_params):
    """Yuborilayotgan xabarni (matn / rasm / ovoz / video / stiker + reply) tekshiradi.
    Qaytaradi: (content, image_file, media_kind, duration, reply_to) yoki (None, xato_javob)."""
    content = (request.form.get("content") or "").strip()[:1000]
    sticker = (request.form.get("sticker") or "").strip()
    try:
        duration = max(0, min(600, int(request.form.get("duration") or 0)))
    except ValueError:
        duration = 0
    reply_to = None
    try:
        rid = int(request.form.get("reply_to") or 0)
    except ValueError:
        rid = 0
    if rid:
        ok = conn.execute(f"SELECT 1 FROM {table} WHERE id = ? AND ({scope_sql})", (rid, *scope_params)).fetchone()
        if ok:
            reply_to = rid

    image_file = request.files.get("image")
    audio_file = request.files.get("audio")
    vnote_file = request.files.get("video")
    filename, kind = None, None
    try:
        if audio_file and audio_file.filename is not None and audio_file.mimetype:
            filename, kind = save_chat_blob(conn, audio_file, "audio"), "audio"
        elif vnote_file and vnote_file.mimetype:
            filename, kind = save_chat_blob(conn, vnote_file, "video"), "video"
        elif image_file and image_file.filename and allowed_file(image_file.filename):
            filename, kind = save_image_to_db(conn, image_file), "image"
    except ValueError as e:
        err = str(e)
        msg = tr("video_too_big") if err == "too_big" else tr("upload_failed")
        return None, (jsonify({"error": err, "message": msg}), 413 if err == "too_big" else 400)

    if not filename and sticker:
        if len(sticker) <= 16 and not re.search(r"[A-Za-z0-9]", sticker):
            content, kind = sticker, "sticker"
    if not content and not filename:
        return None, (jsonify({"error": "bo'sh xabar"}), 400)
    if kind in ("audio", "video"):
        content = ""
    return (content, filename, kind, duration if kind in ("audio", "video") else None, reply_to), None


@app.route("/api/dm/<other_username>")
def api_dm_messages(other_username):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    me = session["username"]
    conn = get_db()
    rows = conn.execute(
        """SELECT id, sender, receiver, content, image_file, media_kind, duration, reply_to, created_at, created_ts, is_read FROM private_messages
           WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
           ORDER BY id DESC LIMIT 100""",
        (me, other_username, other_username, me),
    ).fetchall()
    # Suhbat ochiq: undagi xabarlar o'qilgan hisoblanadi
    conn.execute(
        "UPDATE private_messages SET is_read = 1 WHERE sender = ? AND receiver = ? AND is_read = 0",
        (other_username, me),
    )
    conn.commit()
    rows = list(reversed(rows))
    peer_prefs = get_prefs(conn, other_username)
    messages = serialize_chat_rows(conn, rows, "private_messages", "sender", read_visible=bool(peer_prefs["read_receipts"]))
    peer = presence_info(conn, me, other_username, peer_prefs)
    conn.close()
    return jsonify({"messages": messages, "me": me, "peer": peer})


@app.route("/api/dm/delete/<int:message_id>", methods=["POST"])
def api_dm_delete(message_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    msg = conn.execute("SELECT * FROM private_messages WHERE id = ?", (message_id,)).fetchone()

    if not msg or msg["sender"] != session["username"]:
        conn.close()
        return jsonify({"error": "ruxsat yo'q"}), 403

    if msg["image_file"]:
        delete_image_from_db(conn, msg["image_file"])

    conn.execute("DELETE FROM private_messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/dm/send/<other_username>", methods=["POST"])
def api_dm_send(other_username):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    me = session["username"]
    conn = get_db()
    other = conn.execute("SELECT username FROM users WHERE username = ?", (other_username,)).fetchone()
    if not other or other["username"] == me:
        conn.close()
        return jsonify({"error": "user"}), 404
    ok, why = can_message(conn, me, other["username"])
    if not ok:
        conn.close()
        return jsonify({"error": why, "message": tr(why)}), 403

    payload, err = read_chat_payload(
        conn, "private_messages",
        "(sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)", (me, other_username, other_username, me),
    )
    if err:
        conn.close()
        return err
    content, filename, kind, duration, reply_to = payload

    conn.execute(
        "INSERT INTO private_messages (sender, receiver, content, image_file, media_kind, duration, reply_to, created_at, created_ts, is_read) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
        (me, other_username, content, filename, kind, duration, reply_to, datetime.now().strftime("%H:%M"), int(time.time())),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


# ---------- Guruhlar va kanallar ----------
GROUP_ROLES = ("owner", "admin", "member")


def group_row(conn, gid):
    r = conn.execute("SELECT * FROM groups WHERE id = ?", (gid,)).fetchone()
    return dict(r) if r else None


def member_role(conn, gid, username):
    r = conn.execute("SELECT role FROM group_members WHERE group_id = ? AND username = ?", (gid, username)).fetchone()
    if not r:
        return None
    return r["role"] if r["role"] in GROUP_ROLES else "member"


def group_member_count(conn, gid):
    return conn.execute("SELECT COUNT(*) AS c FROM group_members WHERE group_id = ?", (gid,)).fetchone()["c"]


def group_max_msg_id(conn, gid):
    return conn.execute("SELECT COALESCE(MAX(id), 0) AS m FROM group_messages WHERE group_id = ?", (gid,)).fetchone()["m"]


def group_can_post(group, role):
    if role in ("owner", "admin"):
        return True
    if not role:
        return False
    return group.get("kind") != "channel" and (group.get("post_mode") or "all") == "all"


def ensure_invite_code(conn, group):
    if group.get("invite_code"):
        return group["invite_code"]
    for _ in range(5):
        code = secrets.token_urlsafe(7).replace("-", "a").replace("_", "b")
        try:
            conn.execute("UPDATE groups SET invite_code = ? WHERE id = ?", (code, group["id"]))
            conn.commit()
            group["invite_code"] = code
            return code
        except Exception:
            conn.rollback()
    return ""


def join_group(conn, gid, username, role="member"):
    conn.execute(
        "INSERT OR IGNORE INTO group_members (group_id, username, role, last_read_id) VALUES (?, ?, ?, ?)",
        (gid, username, role, group_max_msg_id(conn, gid)),
    )


def delete_group_everything(conn, gid):
    for row in conn.execute("SELECT image_file FROM group_messages WHERE group_id = ? AND image_file IS NOT NULL", (gid,)).fetchall():
        delete_image_from_db(conn, row["image_file"])
    g_ = conn.execute("SELECT avatar_file FROM groups WHERE id = ?", (gid,)).fetchone()
    if g_ and g_["avatar_file"]:
        delete_image_from_db(conn, g_["avatar_file"])
    conn.execute("DELETE FROM group_messages WHERE group_id = ?", (gid,))
    conn.execute("DELETE FROM group_members WHERE group_id = ?", (gid,))
    conn.execute("DELETE FROM chat_mutes WHERE chat_key = ?", ("g:%s" % gid,))
    conn.execute("UPDATE products SET channel_id = NULL WHERE channel_id = ?", (gid,))
    conn.execute("DELETE FROM groups WHERE id = ?", (gid,))


def group_preview(m):
    if not m:
        return ""
    mk = m["media_kind"] or ("image" if m["image_file"] else "text")
    if mk == "audio":
        return "🎤 " + tr("msg_voice")
    if mk == "video":
        return "🎥 " + tr("msg_video_note")
    if mk == "image":
        return "📷 " + (m["content"] or tr("photo_msg"))
    if mk == "order":
        return "🛒 " + tr("order_title")
    return (m["content"] or "")[:40]


def get_all_chats(conn, me):
    """Hamma chatlar bitta ro'yxatda: shaxsiy + guruhlar + kanallar (oxirgi faollik bo'yicha)."""
    muted = muted_keys(conn, me)
    items = get_conversations(conn, me, limit=100)
    for it in items:
        it["muted"] = ("dm:" + it["username"]) in muted
    rows = conn.execute(
        """SELECT g.id, g.name, g.avatar_letter, g.avatar_file, g.kind, m.role
           FROM groups g JOIN group_members m ON m.group_id = g.id WHERE m.username = ?""",
        (me,),
    ).fetchall()
    if rows:
        gids = [r["id"] for r in rows]
        marks = ",".join("?" for _ in gids)
        last = {}
        for m in conn.execute(
            f"""SELECT gm.* FROM group_messages gm JOIN (
                   SELECT group_id, MAX(id) AS mid FROM group_messages WHERE group_id IN ({marks}) GROUP BY group_id
                ) x ON gm.id = x.mid""",
            tuple(gids),
        ).fetchall():
            last[m["group_id"]] = m
        counts = {r["group_id"]: r["c"] for r in conn.execute(
            f"SELECT group_id, COUNT(*) AS c FROM group_members WHERE group_id IN ({marks}) GROUP BY group_id", tuple(gids)
        ).fetchall()}
        unread = group_unread_map(conn, me)
        for r in rows:
            m = last.get(r["id"])
            prev = group_preview(m)
            if m and r["kind"] != "channel" and m["username"] != me and prev:
                prev = m["username"] + ": " + prev
            items.append({
                "kind": r["kind"] or "group",
                "id": r["id"],
                "name": r["name"],
                "avatar_letter": r["avatar_letter"],
                "avatar_file": r["avatar_file"],
                "unread": unread.get(r["id"], 0),
                "preview": prev,
                "mine": bool(m and m["username"] == me and r["kind"] != "channel"),
                "time": m["created_at"] if m else "",
                "ts": int(m["created_ts"] or 0) if m else 0,
                "members": counts.get(r["id"], 1),
                "muted": ("g:%s" % r["id"]) in muted,
                "has_image": False,
            })
    items.sort(key=lambda x: x["ts"], reverse=True)
    return items


@app.route("/shaxsiy")
def shaxsiy():
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    conn = get_db()
    chats = get_all_chats(conn, me)
    conn.close()
    flt = request.args.get("f", "all")
    if flt not in ("all", "dm", "group", "channel"):
        flt = "all"

    return render_template(
        "shaxsiy.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        conversations=chats,
        flt=flt,
        active="shaxsiy",
    )


@app.route("/groups")
def groups_list():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return redirect(url_for("shaxsiy", f="group"))


@app.route("/groups/new", methods=["GET", "POST"])
def group_new():
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    kind = request.values.get("kind", "group")
    if kind not in ("group", "channel"):
        kind = "group"
    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()[:60]
        description = request.form.get("description", "").strip()[:300]
        selected = request.form.getlist("members")
        is_public = 1 if (request.form.get("is_public") == "1" or kind == "channel" and request.form.get("is_public") != "0") else 0
        if name:
            cur = conn.execute(
                "INSERT INTO groups (name, avatar_letter, created_by, created_at, kind, description, is_public, post_mode) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (name, name[0].upper(), me, datetime.now().strftime("%d.%m %H:%M"), kind, description, is_public,
                 "admins" if kind == "channel" else "all"),
            )
            group_id = cur.lastrowid
            join_group(conn, group_id, me, "owner")
            for member in selected:
                u = conn.execute("SELECT username FROM users WHERE username = ?", (member,)).fetchone()
                if u and u["username"] != me and not is_blocked_between(conn, me, u["username"]):
                    join_group(conn, group_id, u["username"])
            conn.commit()
            ensure_invite_code(conn, group_row(conn, group_id))
            conn.close()
            return redirect(url_for("group_chat", group_id=group_id))
        flash(tr("group_name_required"))

    users = conn.execute(
        """SELECT u.username, u.nickname, u.avatar_letter, u.avatar_file FROM contacts c
           JOIN users u ON u.username = c.contact_username WHERE c.username = ? ORDER BY u.username""",
        (me,),
    ).fetchall()
    conn.close()

    return render_template(
        "group_new.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        users=users,
        kind=kind,
        active="shaxsiy",
    )


@app.route("/groups/<int:group_id>")
def group_chat(group_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    conn = get_db()
    group = group_row(conn, group_id)
    role = member_role(conn, group_id, me) if group else None
    if not group or (not role and not group.get("is_public") and not g.is_admin):
        conn.close()
        return redirect(url_for("shaxsiy"))
    count = group_member_count(conn, group_id)
    muted = ("g:%s" % group_id) in muted_keys(conn, me)
    conn.close()

    return render_template(
        "group_chat.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        group=group,
        role=role,
        is_member=bool(role),
        can_post=group_can_post(group, role),
        member_count=count,
        chat_muted=muted,
        active="shaxsiy",
    )


@app.route("/api/groups/<int:group_id>/messages")
def api_group_messages(group_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    me = session["username"]
    conn = get_db()
    group = group_row(conn, group_id)
    role = member_role(conn, group_id, me) if group else None
    if not group or (not role and not group.get("is_public")):
        conn.close()
        return jsonify({"error": "a'zo emassiz"}), 403

    rows = conn.execute(
        "SELECT id, username, content, image_file, media_kind, duration, reply_to, created_at, created_ts FROM group_messages WHERE group_id = ? ORDER BY id DESC LIMIT 100",
        (group_id,),
    ).fetchall()
    rows = list(reversed(rows))
    messages = serialize_chat_rows(conn, rows, "group_messages", "username")
    reads = conn.execute("SELECT username, COALESCE(last_read_id, 0) AS lr FROM group_members WHERE group_id = ?", (group_id,)).fetchall()
    staff = role in ("owner", "admin")
    for m in messages:
        m["seen"] = sum(1 for r in reads if r["username"] != m["author"] and r["lr"] >= m["id"])
        m["can_delete"] = (m["author"] == me) or staff
    if role and rows:
        top = rows[-1]["id"]
        conn.execute("UPDATE group_members SET last_read_id = ? WHERE group_id = ? AND username = ? AND COALESCE(last_read_id, 0) < ?",
                     (top, group_id, me, top))
        conn.commit()
    count = len(reads)
    conn.close()
    return jsonify({"messages": messages, "me": me, "kind": group.get("kind") or "group", "members": count,
                    "can_post": group_can_post(group, role)})


@app.route("/api/groups/message/delete/<int:message_id>", methods=["POST"])
def api_group_message_delete(message_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    msg = conn.execute("SELECT * FROM group_messages WHERE id = ?", (message_id,)).fetchone()
    if not msg:
        conn.close()
        return jsonify({"error": "ruxsat yo'q"}), 403
    role = member_role(conn, msg["group_id"], session["username"])
    if msg["username"] != session["username"] and role not in ("owner", "admin") and not g.is_admin:
        conn.close()
        return jsonify({"error": "ruxsat yo'q"}), 403

    if msg["image_file"]:
        delete_image_from_db(conn, msg["image_file"])

    conn.execute("DELETE FROM group_messages WHERE id = ?", (message_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/groups/<int:group_id>/send", methods=["POST"])
def api_group_send(group_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    me = session["username"]
    conn = get_db()
    group = group_row(conn, group_id)
    role = member_role(conn, group_id, me) if group else None
    if not group or not role:
        conn.close()
        return jsonify({"error": "a'zo emassiz"}), 403
    if not group_can_post(group, role):
        conn.close()
        return jsonify({"error": "readonly", "message": tr("channel_readonly")}), 403

    payload, err = read_chat_payload(conn, "group_messages", "group_id = ?", (group_id,))
    if err:
        conn.close()
        return err
    content, filename, kind, duration, reply_to = payload

    cur = conn.execute(
        "INSERT INTO group_messages (group_id, username, content, image_file, media_kind, duration, reply_to, created_at, created_ts) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (group_id, me, content, filename, kind, duration, reply_to, datetime.now().strftime("%H:%M"), int(time.time())),
    )
    conn.execute("UPDATE group_members SET last_read_id = ? WHERE group_id = ? AND username = ?", (cur.lastrowid, group_id, me))
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


def group_settings_context(conn, group, me, role):
    members = conn.execute(
        """SELECT m.username, m.role, u.nickname, u.avatar_letter, u.avatar_file, u.last_seen_ts FROM group_members m
           JOIN users u ON u.username = m.username WHERE m.group_id = ?
           ORDER BY CASE m.role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END, u.username""",
        (group["id"],),
    ).fetchall()
    member_names = {m["username"] for m in members}
    candidates = [c for c in conn.execute(
        """SELECT u.username, u.nickname, u.avatar_letter, u.avatar_file FROM contacts c
           JOIN users u ON u.username = c.contact_username WHERE c.username = ? ORDER BY u.username""",
        (me,),
    ).fetchall() if c["username"] not in member_names]
    return members, candidates


@app.route("/groups/<int:group_id>/settings")
def group_settings(group_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    group = group_row(conn, group_id)
    role = member_role(conn, group_id, me) if group else None
    if not group or (not role and not g.is_admin):
        conn.close()
        return redirect(url_for("shaxsiy"))
    members, candidates = group_settings_context(conn, group, me, role)
    code = ensure_invite_code(conn, group) if role in ("owner", "admin") else (group.get("invite_code") or "")
    muted = ("g:%s" % group_id) in muted_keys(conn, me)
    product_count = conn.execute("SELECT COUNT(*) AS c FROM products WHERE channel_id = ?", (group_id,)).fetchone()["c"]
    conn.close()
    return render_template(
        "group_settings.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        group=group,
        role=role,
        members=members,
        candidates=candidates,
        invite_link=url_for("join_by_code", code=code, _external=True) if code else "",
        chat_muted=muted,
        product_count=product_count,
        active="shaxsiy",
    )


def _group_manager(conn, group_id, me):
    """(group, role) yoki (None, None). Faqat ega yoki admin uchun."""
    group = group_row(conn, group_id)
    role = member_role(conn, group_id, me) if group else None
    if not group or (role not in ("owner", "admin") and not g.is_admin):
        return None, None
    return group, role


@app.route("/api/groups/<int:group_id>/update", methods=["POST"])
def api_group_update(group_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    conn = get_db()
    group, role = _group_manager(conn, group_id, me)
    if not group:
        conn.close()
        return jsonify({"ok": False, "message": tr("group_no_permission")}), 403
    name = (request.form.get("name") or group["name"]).strip()[:60] or group["name"]
    description = (request.form.get("description") or "").strip()[:300]
    conn.execute("UPDATE groups SET name = ?, avatar_letter = ?, description = ? WHERE id = ?",
                 (name, name[0].upper(), description, group_id))
    if role == "owner" or g.is_admin:
        if "is_public" in request.form:
            conn.execute("UPDATE groups SET is_public = ? WHERE id = ?", (1 if request.form.get("is_public") == "1" else 0, group_id))
        if group.get("kind") != "channel" and request.form.get("post_mode") in ("all", "admins"):
            conn.execute("UPDATE groups SET post_mode = ? WHERE id = ?", (request.form.get("post_mode"), group_id))
    avatar = request.files.get("avatar")
    if avatar and avatar.filename and allowed_file(avatar.filename):
        new_name = save_image_to_db(conn, avatar, prefix="gavatar_", avatar=True)
        if group.get("avatar_file"):
            delete_image_from_db(conn, group["avatar_file"])
        conn.execute("UPDATE groups SET avatar_file = ? WHERE id = ?", (new_name, group_id))
    if request.form.get("remove_avatar") == "1" and group.get("avatar_file") and not (avatar and avatar.filename):
        delete_image_from_db(conn, group["avatar_file"])
        conn.execute("UPDATE groups SET avatar_file = NULL WHERE id = ?", (group_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/groups/<int:group_id>/members/add", methods=["POST"])
def api_group_add_members(group_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    data = request.get_json(silent=True) or {}
    conn = get_db()
    group, role = _group_manager(conn, group_id, me)
    if not group:
        conn.close()
        return jsonify({"ok": False, "message": tr("group_no_permission")}), 403
    added = 0
    for name in (data.get("usernames") or [])[:100]:
        u = conn.execute("SELECT username FROM users WHERE username = ?", (name,)).fetchone()
        if u and not member_role(conn, group_id, u["username"]) and not is_blocked_between(conn, me, u["username"]):
            join_group(conn, group_id, u["username"])
            added += 1
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "added": added})


@app.route("/api/groups/<int:group_id>/role", methods=["POST"])
def api_group_role(group_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    data = request.get_json(silent=True) or {}
    target = data.get("username")
    new_role = data.get("role")
    conn = get_db()
    group = group_row(conn, group_id)
    if not group or (member_role(conn, group_id, me) != "owner" and not g.is_admin):
        conn.close()
        return jsonify({"ok": False, "message": tr("group_owner_only")}), 403
    trole = member_role(conn, group_id, target)
    if not trole or trole == "owner" or new_role not in ("admin", "member"):
        conn.close()
        return jsonify({"ok": False}), 400
    conn.execute("UPDATE group_members SET role = ? WHERE group_id = ? AND username = ?", (new_role, group_id, target))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "role": new_role})


@app.route("/api/groups/<int:group_id>/kick", methods=["POST"])
def api_group_kick(group_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    data = request.get_json(silent=True) or {}
    target = data.get("username")
    conn = get_db()
    group, role = _group_manager(conn, group_id, me)
    if not group:
        conn.close()
        return jsonify({"ok": False, "message": tr("group_no_permission")}), 403
    trole = member_role(conn, group_id, target)
    if not trole or trole == "owner" or target == me or (trole == "admin" and role != "owner" and not g.is_admin):
        conn.close()
        return jsonify({"ok": False, "message": tr("group_no_permission")}), 403
    conn.execute("DELETE FROM group_members WHERE group_id = ? AND username = ?", (group_id, target))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/groups/<int:group_id>/join", methods=["POST"])
def api_group_join(group_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    conn = get_db()
    group = group_row(conn, group_id)
    if not group or not group.get("is_public"):
        conn.close()
        return jsonify({"ok": False}), 403
    join_group(conn, group_id, me)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/join/<code>")
def join_by_code(code):
    if "user_id" not in session:
        return redirect(url_for("login", next="/join/" + code))
    conn = get_db()
    row = conn.execute("SELECT id FROM groups WHERE invite_code = ?", (code,)).fetchone()
    if not row:
        conn.close()
        flash(tr("group_link_invalid"))
        return redirect(url_for("shaxsiy"))
    join_group(conn, row["id"], session["username"])
    conn.commit()
    conn.close()
    return redirect(url_for("group_chat", group_id=row["id"]))


@app.route("/api/groups/<int:group_id>/leave", methods=["POST"])
def api_group_leave(group_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    conn = get_db()
    group = group_row(conn, group_id)
    role = member_role(conn, group_id, me) if group else None
    if not group or not role:
        conn.close()
        return jsonify({"ok": False}), 400
    if role == "owner":
        if group_member_count(conn, group_id) > 1:
            conn.close()
            return jsonify({"ok": False, "message": tr("group_owner_cannot_leave")}), 400
        delete_group_everything(conn, group_id)
    else:
        conn.execute("DELETE FROM group_members WHERE group_id = ? AND username = ?", (group_id, me))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/groups/<int:group_id>/delete", methods=["POST"])
def api_group_delete(group_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    conn = get_db()
    group = group_row(conn, group_id)
    if not group or (member_role(conn, group_id, me) != "owner" and not g.is_admin):
        conn.close()
        return jsonify({"ok": False, "message": tr("group_owner_only")}), 403
    delete_group_everything(conn, group_id)
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/groups/<int:group_id>/transfer", methods=["POST"])
def api_group_transfer(group_id):
    """Egalikni boshqa a'zoga o'tkazish."""
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    target = (request.get_json(silent=True) or {}).get("username")
    conn = get_db()
    group = group_row(conn, group_id)
    if not group or member_role(conn, group_id, me) != "owner" or not member_role(conn, group_id, target) or target == me:
        conn.close()
        return jsonify({"ok": False, "message": tr("group_owner_only")}), 403
    conn.execute("UPDATE group_members SET role = 'owner' WHERE group_id = ? AND username = ?", (group_id, target))
    conn.execute("UPDATE group_members SET role = 'admin' WHERE group_id = ? AND username = ?", (group_id, me))
    conn.execute("UPDATE groups SET created_by = ? WHERE id = ?", (target, group_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/discover")
def discover():
    """Ommaviy guruh va kanallarni qidirish."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    q = request.args.get("q", "").strip()
    conn = get_db()
    sql = ("SELECT g.id, g.name, g.avatar_letter, g.avatar_file, g.kind, g.description, "
           "(SELECT COUNT(*) FROM group_members m WHERE m.group_id = g.id) AS members, "
           "(SELECT 1 FROM group_members m2 WHERE m2.group_id = g.id AND m2.username = ?) AS joined "
           "FROM groups g WHERE g.is_public = 1 ")
    params = [me]
    if q:
        sql += "AND LOWER(g.name) LIKE LOWER(?) "
        params.append(f"%{q}%")
    sql += "ORDER BY members DESC, g.id DESC LIMIT 40"
    rows = conn.execute(sql, tuple(params)).fetchall()
    conn.close()
    return render_template("discover.html", username=me, avatar_letter=session["avatar_letter"], results=rows, q=q, active="shaxsiy")


@app.route("/api/mute", methods=["POST"])
def api_mute():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    data = request.get_json(silent=True) or {}
    key = str(data.get("key") or "")
    if not re.match(r"^(dm:[A-Za-z0-9_.\-]{1,40}|g:\d{1,12})$", key):
        return jsonify({"ok": False}), 400
    conn = get_db()
    if data.get("muted"):
        conn.execute("INSERT OR IGNORE INTO chat_mutes (username, chat_key) VALUES (?, ?)", (session["username"], key))
    else:
        conn.execute("DELETE FROM chat_mutes WHERE username = ? AND chat_key = ?", (session["username"], key))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


# ---------- Audio / video qo'ng'iroq (WebRTC; signal almashinuvi server orqali) ----------
CALL_RING_SECONDS = 45
CALL_LOST_SECONDS = 25


def finish_call(conn, call, status):
    """Qo'ng'iroqni tugatadi va chatga yozuv qo'shadi (faqat bir marta)."""
    fresh = conn.execute("SELECT status FROM calls WHERE id = ?", (call["id"],)).fetchone()
    if not fresh or fresh["status"] not in ("ringing", "accepted"):
        return False
    now = int(time.time())
    duration = 0
    if call["answered_ts"] and status == "ended":
        duration = max(0, now - int(call["answered_ts"]))
    conn.execute("UPDATE calls SET status = ?, ended_ts = ? WHERE id = ?", (status, now, call["id"]))
    unseen = 0 if status == "ended" else 1
    conn.execute(
        "INSERT INTO private_messages (sender, receiver, content, image_file, media_kind, duration, created_at, created_ts, is_read) "
        "VALUES (?, ?, ?, NULL, 'call', ?, ?, ?, ?)",
        (call["caller"], call["callee"], f"{call['kind']}:{status}", duration, datetime.now().strftime("%H:%M"), int(time.time()), 1 - unseen),
    )
    conn.execute("DELETE FROM call_signals WHERE call_id = ?", (call["id"],))
    return True


def expire_calls(conn):
    now = int(time.time())
    for c in conn.execute("SELECT * FROM calls WHERE status = 'ringing' AND created_ts < ?", (now - CALL_RING_SECONDS,)).fetchall():
        finish_call(conn, c, "missed")
    for c in conn.execute(
        "SELECT * FROM calls WHERE status = 'accepted' AND COALESCE(last_ping, answered_ts, created_ts) < ?", (now - CALL_LOST_SECONDS,)
    ).fetchall():
        finish_call(conn, c, "ended")
    conn.commit()


def get_call_for_user(conn, call_id, me):
    c = conn.execute("SELECT * FROM calls WHERE id = ?", (call_id,)).fetchone()
    if not c or me not in (c["caller"], c["callee"]):
        return None
    return c


def incoming_call_for(conn, me):
    now = int(time.time())
    c = conn.execute(
        "SELECT * FROM calls WHERE callee = ? AND status = 'ringing' AND created_ts >= ? ORDER BY id DESC LIMIT 1",
        (me, now - CALL_RING_SECONDS),
    ).fetchone()
    if not c:
        return None
    u = conn.execute("SELECT username, nickname, avatar_letter, avatar_file FROM users WHERE username = ?", (c["caller"],)).fetchone()
    if not u:
        return None
    return {"id": c["id"], "from": u["username"], "display": u["nickname"] or u["username"],
            "letter": u["avatar_letter"], "avatar_file": u["avatar_file"], "kind": c["kind"]}


@app.route("/api/call/start", methods=["POST"])
def api_call_start():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    data = request.get_json(silent=True) or {}
    to = (data.get("to") or "").strip()
    kind = "video" if data.get("kind") == "video" else "audio"
    me = session["username"]
    conn = get_db()
    expire_calls(conn)
    target = conn.execute("SELECT username FROM users WHERE username = ?", (to,)).fetchone()
    if not target or to == me:
        conn.close()
        return jsonify({"error": "user"}), 404
    ok, why = can_message(conn, me, to)
    if not ok:
        conn.close()
        return jsonify({"error": why, "message": tr(why)}), 403
    busy = conn.execute(
        "SELECT 1 FROM calls WHERE status IN ('ringing', 'accepted') AND (caller IN (?, ?) OR callee IN (?, ?))",
        (me, to, me, to),
    ).fetchone()
    if busy:
        conn.close()
        return jsonify({"error": "busy", "message": tr("call_busy")}), 409
    now = int(time.time())
    conn.execute(
        "INSERT INTO calls (caller, callee, kind, status, created_ts, last_ping) VALUES (?, ?, ?, 'ringing', ?, ?)",
        (me, to, kind, now, now),
    )
    conn.commit()
    row = conn.execute("SELECT id FROM calls WHERE caller = ? AND callee = ? ORDER BY id DESC LIMIT 1", (me, to)).fetchone()
    conn.close()
    return jsonify({"ok": True, "id": row["id"]})


@app.route("/api/call/<int:call_id>/accept", methods=["POST"])
def api_call_accept(call_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    conn = get_db()
    expire_calls(conn)
    c = get_call_for_user(conn, call_id, session["username"])
    if not c or c["callee"] != session["username"] or c["status"] != "ringing":
        conn.close()
        return jsonify({"error": "gone"}), 409
    now = int(time.time())
    conn.execute("UPDATE calls SET status = 'accepted', answered_ts = ?, last_ping = ? WHERE id = ?", (now, now, call_id))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/call/<int:call_id>/decline", methods=["POST"])
def api_call_decline(call_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    conn = get_db()
    c = get_call_for_user(conn, call_id, session["username"])
    if c and c["status"] == "ringing":
        # chaqiruvchi bekor qilsa "missed", qabul qiluvchi rad etsa "declined"
        finish_call(conn, c, "missed" if c["caller"] == session["username"] else "declined")
        conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/call/<int:call_id>/end", methods=["POST"])
def api_call_end(call_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    conn = get_db()
    c = get_call_for_user(conn, call_id, session["username"])
    if c:
        if c["status"] == "ringing":
            finish_call(conn, c, "missed" if c["caller"] == session["username"] else "declined")
        elif c["status"] == "accepted":
            finish_call(conn, c, "ended")
        conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/call/<int:call_id>/signal", methods=["POST"])
def api_call_signal(call_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    data = request.get_json(silent=True) or {}
    sig_type = data.get("type")
    payload = json.dumps(data.get("data"))
    if sig_type not in ("offer", "answer", "ice") or len(payload) > 20000:
        return jsonify({"error": "bad"}), 400
    me = session["username"]
    conn = get_db()
    c = get_call_for_user(conn, call_id, me)
    if not c or c["status"] != "accepted":
        conn.close()
        return jsonify({"error": "gone"}), 409
    other = c["callee"] if c["caller"] == me else c["caller"]
    conn.execute(
        "INSERT INTO call_signals (call_id, to_user, sig_type, payload, created_ts) VALUES (?, ?, ?, ?, ?)",
        (call_id, other, sig_type, payload, int(time.time())),
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/call/<int:call_id>/poll")
def api_call_poll(call_id):
    """Qo'ng'iroq holati va menga kelgan signallar (ham heartbeat vazifasini bajaradi)."""
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    try:
        after = int(request.args.get("after", 0))
    except ValueError:
        after = 0
    conn = get_db()
    expire_calls(conn)
    c = get_call_for_user(conn, call_id, me)
    if not c:
        conn.close()
        return jsonify({"error": "gone"}), 404
    if c["status"] == "accepted":
        conn.execute("UPDATE calls SET last_ping = ? WHERE id = ?", (int(time.time()), call_id))
        conn.commit()
    sigs = conn.execute(
        "SELECT id, sig_type, payload FROM call_signals WHERE call_id = ? AND to_user = ? AND id > ? ORDER BY id LIMIT 100",
        (call_id, me, after),
    ).fetchall()
    conn.close()
    return jsonify({
        "status": c["status"],
        "signals": [{"id": r["id"], "type": r["sig_type"], "data": json.loads(r["payload"])} for r in sigs],
    })


@app.route("/api/call/ice")
def api_call_ice():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    servers = [{"urls": ["stun:stun.l.google.com:19302", "stun:stun1.l.google.com:19302"]}]
    turn_url = os.environ.get("TURN_URL", "").strip()
    if turn_url:
        servers.append({
            "urls": [u.strip() for u in turn_url.split(",") if u.strip()],
            "username": os.environ.get("TURN_USERNAME", ""),
            "credential": os.environ.get("TURN_CREDENTIAL", ""),
        })
    return jsonify({"iceServers": servers})


@app.route("/call/<int:call_id>")
def call_page(call_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    expire_calls(conn)
    c = get_call_for_user(conn, call_id, me)
    if not c or c["status"] not in ("ringing", "accepted"):
        conn.close()
        if not c:
            return redirect(url_for("shaxsiy"))
        return redirect(url_for("dm", other_username=c["callee"] if c["caller"] == me else c["caller"]))
    peer_name = c["callee"] if c["caller"] == me else c["caller"]
    peer = conn.execute("SELECT username, nickname, avatar_letter, avatar_file FROM users WHERE username = ?", (peer_name,)).fetchone()
    conn.close()
    return render_template(
        "call.html",
        call=c, role="caller" if c["caller"] == me else "callee",
        peer=peer, peer_display=peer["nickname"] or peer["username"],
        username=me, active="shaxsiy",
    )


# ---------- Xabarni tarjima qilish ----------
_TRANSLATE_CACHE = {}
GTX_LANG = {"zh": "zh-CN"}


def _translate_gtx(text, target):
    url = "https://translate.googleapis.com/translate_a/single?" + urllib.parse.urlencode(
        {"client": "gtx", "sl": "auto", "tl": GTX_LANG.get(target, target), "dt": "t", "q": text}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    translated = "".join(part[0] for part in data[0] if part and part[0])
    detected = (data[2] if len(data) > 2 and isinstance(data[2], str) else "")
    if not translated:
        raise ValueError("empty")
    return translated, detected.split("-")[0]


def _translate_mymemory(text, target):
    url = "https://api.mymemory.translated.net/get?" + urllib.parse.urlencode(
        {"q": text[:480], "langpair": "Autodetect|" + GTX_LANG.get(target, target)}
    )
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    out = ((data.get("responseData") or {}).get("translatedText") or "").strip()
    if not out or "MYMEMORY WARNING" in out.upper():
        raise ValueError("empty")
    return out, ""


def _translate_claude(text, target):
    if not (anthropic and ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "bu_yerga_kalitni_yozing"):
        raise ValueError("no key")
    name = TRANSLATE_LANGS.get(target, target)
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    resp = client.messages.create(
        model="claude-sonnet-5", max_tokens=600,
        messages=[{"role": "user", "content": f"Translate to {name} ({target}). Reply with only the translation:\n\n{text}"}],
    )
    out = "".join(b.text for b in resp.content if b.type == "text").strip()
    if not out:
        raise ValueError("empty")
    return out, ""


def translate_text(text, target):
    """Matnni target tiliga tarjima qiladi. Qaytaradi: (tarjima, aniqlangan_til). Xatoda None.
    Ketma-ket urinadi: Google (bepul) -> MyMemory (bepul) -> Anthropic (kalit bo'lsa)."""
    key = (text, target)
    if key in _TRANSLATE_CACHE:
        return _TRANSLATE_CACHE[key]
    result = None
    for provider in (_translate_gtx, _translate_mymemory, _translate_claude):
        try:
            result = provider(text, target)
            break
        except Exception as e:
            app.logger.warning("translate %s failed: %s", provider.__name__, e)
    if result is not None:
        if len(_TRANSLATE_CACHE) > 2000:
            _TRANSLATE_CACHE.clear()
        _TRANSLATE_CACHE[key] = result
    return result


@app.route("/api/translate", methods=["POST"])
def api_translate():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()[:1000]
    if not text:
        return jsonify({"ok": False}), 400
    target = (data.get("target") or "").strip()
    if target not in TRANSLATE_LANGS:
        conn = get_db()
        prefs = get_prefs(conn, session["username"])
        conn.close()
        target = prefs["translate_lang"] if prefs["translate_lang"] != "auto" else current_lang()
    res = translate_text(text, target)
    if not res:
        return jsonify({"ok": False, "message": tr("translate_failed")}), 502
    translated, detected = res
    same = bool(detected) and detected == GTX_LANG.get(target, target).split("-")[0]
    return jsonify({"ok": True, "text": translated, "same": same, "target": target})


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    conn = get_db()

    posts = build_post_cards(
        conn, conn.execute("SELECT * FROM posts WHERE username = ? ORDER BY id DESC LIMIT 50", (username,)).fetchall(), username
    )
    products = conn.execute(
        "SELECT * FROM products WHERE seller_username = ? ORDER BY id DESC", (username,)
    ).fetchall()
    user_row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    contacts_count = conn.execute("SELECT COUNT(*) AS c FROM contacts WHERE username = ?", (username,)).fetchone()["c"]
    feed_new = feed_new_counts(conn, username)
    my_store = get_store(conn, username)
    conn.close()

    return render_template(
        "profile.html",
        store=my_store,
        username=username,
        avatar_letter=session["avatar_letter"],
        avatar_file=session.get("avatar_file"),
        posts=posts,
        products=products,
        nickname=user_row["nickname"] if user_row else None,
        bio=(user_row["bio"] or "") if user_row else "",
        location_text=user_location_text(user_row) if user_row else "",
        is_business=bool(my_store),
        business_name=(my_store["name"] if my_store else ""),
        contacts_count=contacts_count,
        feed_new=feed_new,
        active="profile",
    )


@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    conn = get_db()
    u = conn.execute("SELECT * FROM users WHERE username = ?", (me,)).fetchone()

    my_store = get_store(conn, me)

    def render_form(nickname, form=None):
        data = form or {
            "bio": u["bio"] or "", "phone": u["phone"] or "", "country": u["country"] or "",
            "region": u["region"] or "", "district": u["district"] or "",
        }
        return render_template(
            "profile_edit.html",
            username=me,
            avatar_letter=session["avatar_letter"],
            avatar_file=session.get("avatar_file"),
            nickname=nickname,
            data=data,
            store=my_store,
            countries=locations.country_list(current_lang()),
        )

    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip().lstrip("@").strip()
        bio = request.form.get("bio", "").strip()[:160]
        phone_raw = request.form.get("phone", "").strip()
        phone = normalize_phone(phone_raw)
        country = request.form.get("country", "").strip()
        region = request.form.get("region", "").strip()
        district = request.form.get("district", "").strip()
        form = {"bio": bio, "phone": phone_raw, "country": country, "region": region, "district": district}
        error = None
        if nickname:
            if not NICK_RE.match(nickname):
                error = tr("nick_invalid")
            elif conn.execute(
                """SELECT username FROM users
                   WHERE username != ? AND (LOWER(nickname) = LOWER(?) OR LOWER(username) = LOWER(?))""",
                (me, nickname, nickname),
            ).fetchone():
                error = tr("nick_taken")
        if not error and phone_raw and not phone:
            error = tr("phone_invalid")
        if not error and not locations.is_valid(country, region, district):
            error = tr("order_location_required")
        if error:
            conn.close()
            flash(error)
            return render_form(nickname, form)

        avatar_image = request.files.get("avatar_image")
        if avatar_image and avatar_image.filename and allowed_file(avatar_image.filename):
            unique_name = save_image_to_db(conn, avatar_image, prefix=f"avatar_{me}_", avatar=True)
            conn.execute("UPDATE users SET avatar_file = ? WHERE username = ?", (unique_name, me))
            session["avatar_file"] = unique_name
        if nickname:
            conn.execute("UPDATE users SET nickname = ? WHERE username = ?", (nickname, me))
            session["nickname"] = nickname
        conn.execute(
            "UPDATE users SET bio = ?, phone = ?, country = ?, region = ?, district = ? WHERE username = ?",
            (bio, phone, country, region, district, me),
        )
        conn.commit()
        conn.close()
        flash(tr("profile_updated"))
        return redirect(url_for("profile"))

    nick = u["nickname"] or ""
    conn.close()
    return render_form(nick)


@app.route("/profile/avatar/remove", methods=["POST"])
def profile_avatar_remove():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    old = conn.execute(
        "SELECT avatar_file FROM users WHERE username = ?", (session["username"],)
    ).fetchone()

    if old and old["avatar_file"]:
        delete_image_from_db(conn, old["avatar_file"])

    conn.execute("UPDATE users SET avatar_file = NULL WHERE username = ?", (session["username"],))
    conn.commit()
    conn.close()
    session["avatar_file"] = None
    flash("Profil rasmi olib tashlandi")
    return redirect(url_for("profile_edit"))


@app.route("/settings/storage")
def storage_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    conn = get_db()

    files = []
    avatar_row = conn.execute("SELECT avatar_file FROM users WHERE username = ?", (me,)).fetchone()
    if avatar_row and avatar_row["avatar_file"]:
        files.append(("Profil rasmi", avatar_row["avatar_file"]))

    for row in conn.execute("SELECT image_file FROM posts WHERE username = ? AND image_file IS NOT NULL", (me,)).fetchall():
        files.append(("Feed post", row["image_file"]))

    for row in conn.execute("SELECT image_file FROM products WHERE seller_username = ? AND image_file IS NOT NULL", (me,)).fetchall():
        files.append(("Do'kon mahsuloti", row["image_file"]))

    for row in conn.execute("SELECT image_file FROM private_messages WHERE sender = ? AND image_file IS NOT NULL", (me,)).fetchall():
        files.append(("Shaxsiy xabar", row["image_file"]))

    for row in conn.execute("SELECT image_file FROM group_messages WHERE username = ? AND image_file IS NOT NULL", (me,)).fetchall():
        files.append(("Guruh xabari", row["image_file"]))

    total_bytes = 0
    file_count = 0
    for label, filename in files:
        size_row = conn.execute(
            "SELECT LENGTH(data) as sz FROM uploaded_images WHERE filename = ?", (filename,)
        ).fetchone()
        if size_row and size_row["sz"]:
            total_bytes += size_row["sz"]
            file_count += 1

    conn.close()

    if total_bytes >= 1024 * 1024:
        size_display = f"{total_bytes / (1024 * 1024):.1f} MB"
    else:
        size_display = f"{total_bytes / 1024:.1f} KB"

    return render_template(
        "storage.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        total_size=size_display,
        file_count=file_count,
        active="profile",
    )


@app.route("/privacy")
def privacy_page():
    logged_in = "user_id" in session
    return render_template(
        "privacy.html",
        username=session.get("username"),
        avatar_letter=session.get("avatar_letter"),
        logged_in=logged_in,
        active="profile",
    )


@app.route("/settings")
def settings_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    user_row = conn.execute(
        "SELECT nickname, email, google_sub FROM users WHERE username = ?", (session["username"],)
    ).fetchone()
    conn.close()

    return render_template(
        "settings.html",
        google_email=(user_row["email"] if user_row and user_row["google_sub"] else None),
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        avatar_file=session.get("avatar_file"),
        nickname=user_row["nickname"] if user_row else None,
        active="profile",
    )


SETTINGS_STUBS = {
    "privacy-settings": {
        "uz": "Maxfiylik", "ru": "Конфиденциальность", "zh": "隐私", "en": "Privacy",
    },
    "security": {
        "uz": "Xavfsizlik", "ru": "Безопасность", "zh": "安全", "en": "Security",
    },
    "notifications": {
        "uz": "Bildirishnomalar", "ru": "Уведомления", "zh": "通知", "en": "Notifications",
    },
    "interface": {
        "uz": "Interfeys", "ru": "Интерфейс", "zh": "界面", "en": "Interface",
    },
    "chat-settings": {
        "uz": "Chat sozlamalari", "ru": "Настройки чата", "zh": "聊天设置", "en": "Chat settings",
    },
    "devices": {
        "uz": "Qurilmalar", "ru": "Устройства", "zh": "设备", "en": "Devices",
    },
}

# Har bir bo'limdagi sozlamalar (kalit nomlari PREF_DEFAULTS'dan)
SETTINGS_SCHEMA = {
    "privacy-settings": ["allow_requests", "who_can_message", "show_online", "read_receipts"],
    "notifications": ["notif_sound", "notif_browser", "notif_preview", "notif_calls"],
    "interface": ["font_size", "reduce_motion"],
    "chat-settings": ["enter_to_send", "wallpaper", "translate_lang", "shrink_images"],
}


def build_setting_items(prefs, keys):
    items = []
    for key in keys:
        default = PREF_DEFAULTS[key]
        if isinstance(default, bool):
            items.append({"key": key, "type": "toggle", "value": bool(prefs[key]), "options": []})
        else:
            if key == "translate_lang":
                options = [("auto", tr("opt_auto"))] + [(code, name) for code, name in TRANSLATE_LANGS.items()]
            else:
                options = [(v, tr("opt_" + v)) for v in PREF_CHOICES[key]]
            items.append({"key": key, "type": "select", "value": prefs[key], "options": options})
    return items


@app.route("/settings/<section>")
def settings_stub(section):
    if "user_id" not in session:
        return redirect(url_for("login"))
    if section not in SETTINGS_STUBS:
        return redirect(url_for("settings_page"))

    me = session["username"]
    title = SETTINGS_STUBS[section].get(current_lang(), SETTINGS_STUBS[section]["uz"])
    conn = get_db()
    prefs = get_prefs(conn, me)
    extra = {}
    if section == "privacy-settings":
        extra["blocked"] = conn.execute(
            """SELECT u.username, u.nickname, u.avatar_letter, u.avatar_file FROM user_blocks b
               JOIN users u ON u.username = b.blocked WHERE b.blocker = ? ORDER BY u.username""",
            (me,),
        ).fetchall()
    elif section == "security":
        u = conn.execute("SELECT email, google_sub, password_set FROM users WHERE username = ?", (me,)).fetchone()
        extra["google_email"] = u["email"] if u and u["google_sub"] else None
        extra["password_set"] = bool(u["password_set"]) if u and u["password_set"] is not None else True
    elif section == "devices":
        rows = conn.execute(
            "SELECT id, token, user_agent, ip, created_ts, last_seen_ts FROM user_sessions WHERE username = ? ORDER BY last_seen_ts DESC LIMIT 30",
            (me,),
        ).fetchall()
        extra["sessions"] = [{
            "id": r["id"],
            "name": parse_user_agent(r["user_agent"]),
            "ip": r["ip"],
            "ago": time_ago(r["last_seen_ts"], tr("ago_long")),
            "current": r["token"] == session.get("sid"),
        } for r in rows]
    conn.close()

    return render_template(
        "settings_stub.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        title=title,
        section=section,
        items=build_setting_items(prefs, SETTINGS_SCHEMA.get(section, [])),
        active="profile",
        **extra,
    )


@app.route("/api/settings", methods=["POST"])
def api_settings_save():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    data = request.get_json(silent=True) or {}
    conn = get_db()
    ok = save_pref(conn, session["username"], data.get("key"), data.get("value"))
    conn.commit()
    conn.close()
    return jsonify({"ok": ok}), (200 if ok else 400)


@app.route("/api/settings/password", methods=["POST"])
def api_change_password():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    data = request.get_json(silent=True) or {}
    current = data.get("current") or ""
    new = data.get("new") or ""
    me = session["username"]
    conn = get_db()
    u = conn.execute("SELECT password_hash, password_set FROM users WHERE username = ?", (me,)).fetchone()
    password_set = bool(u["password_set"]) if u["password_set"] is not None else True
    if password_set and u["password_hash"] != hash_password(current):
        conn.close()
        return jsonify({"ok": False, "message": tr("password_wrong")}), 400
    if len(new) < 4:
        conn.close()
        return jsonify({"ok": False, "message": tr("password_short")}), 400
    conn.execute("UPDATE users SET password_hash = ?, password_set = 1 WHERE username = ?", (hash_password(new), me))
    conn.commit()
    conn.close()
    return jsonify({"ok": True, "message": tr("password_changed")})


@app.route("/api/blocks/<target>", methods=["POST"])
def api_block_user(target):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    me = session["username"]
    if target == me:
        return jsonify({"ok": False}), 400
    conn = get_db()
    exists = conn.execute("SELECT 1 FROM users WHERE username = ?", (target,)).fetchone()
    if not exists:
        conn.close()
        return jsonify({"ok": False}), 404
    conn.execute("INSERT OR IGNORE INTO user_blocks (blocker, blocked) VALUES (?, ?)", (me, target))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/blocks/<target>/remove", methods=["POST"])
def api_unblock_user(target):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    conn = get_db()
    conn.execute("DELETE FROM user_blocks WHERE blocker = ? AND blocked = ?", (session["username"], target))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/sessions/revoke/<int:sid_id>", methods=["POST"])
def api_session_revoke(sid_id):
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    conn = get_db()
    row = conn.execute("SELECT token FROM user_sessions WHERE id = ? AND username = ?", (sid_id, session["username"])).fetchone()
    if row:
        conn.execute("DELETE FROM user_sessions WHERE id = ?", (sid_id,))
        conn.commit()
    conn.close()
    return jsonify({"ok": True, "self": bool(row and row["token"] == session.get("sid"))})


@app.route("/api/sessions/revoke_others", methods=["POST"])
def api_session_revoke_others():
    if "user_id" not in session:
        return jsonify({"error": "auth"}), 401
    conn = get_db()
    conn.execute("DELETE FROM user_sessions WHERE username = ? AND token != ?", (session["username"], session.get("sid", "")))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/settings/language")
def settings_language():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "settings_language.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        active="profile",
    )


@app.route("/settings/about")
def settings_about():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "settings_about.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        active="profile",
    )


@app.route("/ai")
def ai_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "ai.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        active="ai",
    )


@app.route("/api/ai/send", methods=["POST"])
def api_ai_send():
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    if not anthropic:
        return jsonify({
            "error": "Kutubxona o'rnatilmagan. Terminalda: pip install anthropic"
        }), 500

    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "bu_yerga_kalitni_yozing":
        return jsonify({
            "error": "API kalit sozlanmagan. config.py fayliga o'z Anthropic API kalitingizni yozing."
        }), 500

    data = request.get_json(silent=True) or {}
    history = data.get("history", [])
    message = (data.get("message") or "").strip()

    if not message:
        return jsonify({"error": "bo'sh xabar"}), 400

    messages = history + [{"role": "user", "content": message}]

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=1024,
            messages=messages,
        )
        reply_text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return jsonify({"reply": reply_text})
    except Exception as e:
        return jsonify({"error": f"AI bilan bog'lanishda xato: {str(e)}"}), 500


@app.route("/feed/activity")
def feed_activity():
    """Postlarimdagi layk va izohlar: kim layk bosgan, kim izoh yozgan."""
    if "user_id" not in session:
        return redirect(url_for("login"))
    me = session["username"]
    conn = get_db()
    u = conn.execute("SELECT seen_like_id, seen_comment_id FROM users WHERE username = ?", (me,)).fetchone()
    seen_l, seen_c = (u["seen_like_id"] or 0, u["seen_comment_id"] or 0) if u else (0, 0)

    posts = conn.execute("SELECT id, content, image_file, created_at, created_ts FROM posts WHERE username = ? ORDER BY id DESC LIMIT 60", (me,)).fetchall()
    ids = [p["id"] for p in posts]
    likes_by_post, comments_by_post, thumbs = {}, {}, {}
    if ids:
        marks = ",".join("?" for _ in ids)
        for r in conn.execute(
            f"""SELECT l.id, l.post_id, l.username, u.nickname, u.avatar_letter, u.avatar_file FROM likes l
                LEFT JOIN users u ON u.username = l.username
                WHERE l.post_id IN ({marks}) AND l.username != ? ORDER BY l.id DESC""",
            (*ids, me),
        ).fetchall():
            likes_by_post.setdefault(r["post_id"], []).append({
                "username": r["username"], "display": r["nickname"] or r["username"], "letter": r["avatar_letter"] or r["username"][:1].upper(),
                "avatar_file": r["avatar_file"], "new": r["id"] > seen_l, "id": r["id"]})
        for r in conn.execute(
            f"""SELECT c.id, c.post_id, c.username, c.content, c.created_at, u.nickname, u.avatar_letter, u.avatar_file FROM post_comments c
                LEFT JOIN users u ON u.username = c.username
                WHERE c.post_id IN ({marks}) AND c.username != ? ORDER BY c.id DESC""",
            (*ids, me),
        ).fetchall():
            comments_by_post.setdefault(r["post_id"], []).append({
                "username": r["username"], "display": r["nickname"] or r["username"], "letter": r["avatar_letter"] or r["username"][:1].upper(),
                "avatar_file": r["avatar_file"], "text": r["content"], "when": r["created_at"], "new": r["id"] > seen_c, "id": r["id"]})
        for r in conn.execute(
            f"SELECT post_id, filename, kind FROM post_media WHERE post_id IN ({marks}) ORDER BY position, id", tuple(ids)
        ).fetchall():
            if r["post_id"] not in thumbs and r["kind"] == "image":
                thumbs[r["post_id"]] = r["filename"]
    cards = []
    for p in posts:
        lk, cm = likes_by_post.get(p["id"], []), comments_by_post.get(p["id"], [])
        if not lk and not cm:
            continue
        cards.append({
            "id": p["id"], "text": (p["content"] or "")[:90], "thumb": thumbs.get(p["id"]) or p["image_file"],
            "ago": time_ago(p["created_ts"], p["created_at"]),
            "likes": lk, "comments": cm,
            "new_likes": sum(1 for x in lk if x["new"]), "new_comments": sum(1 for x in cm if x["new"]),
            "sort": (sum(1 for x in lk if x["new"]) + sum(1 for x in cm if x["new"]), p["id"]),
        })
    cards.sort(key=lambda c: c["sort"], reverse=True)
    totals = feed_new_counts(conn, me)
    # ko'rildi deb belgilaymiz
    conn.execute("UPDATE users SET seen_like_id = (SELECT COALESCE(MAX(id), 0) FROM likes), "
                 "seen_comment_id = (SELECT COALESCE(MAX(id), 0) FROM post_comments) WHERE username = ?", (me,))
    conn.commit()
    conn.close()
    return render_template(
        "feed_activity.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        cards=cards,
        new_likes=totals["likes"],
        new_comments=totals["comments"],
        tab=("comments" if request.args.get("tab") == "comments" else "likes"),
        active="feed",
    )


@app.route("/logout")
def logout():
    sid = session.get("sid")
    if sid:
        try:
            conn = get_db()
            conn.execute("DELETE FROM user_sessions WHERE token = ?", (sid,))
            conn.commit()
            conn.close()
        except Exception:
            pass
    lang = session.get("lang")
    session.clear()
    if lang:
        session["lang"] = lang
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    port = int(os.environ.get("PORT", 5000))
    debug_mode = os.environ.get("FLASK_DEBUG", "1") == "1"
    print(f"Linko ishga tushmoqda... http://127.0.0.1:{port} manzilida oching")
    app.run(host="0.0.0.0", port=port, debug=debug_mode)
else:
    # Hosting (gunicorn) orqali ishga tushganda ham baza tayyor bo'lishi uchun
    init_db()
