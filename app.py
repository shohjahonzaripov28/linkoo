# Linko - Login/Register tizimi
# Bu Linko ilovasining 1-bosqichi: foydalanuvchi ro'yxatdan o'tishi va tizimga kirishi

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, Response, g
import hashlib
import os
import re
from datetime import datetime
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
PAGE_SIZE = 10
app.secret_key = os.environ.get("SECRET_KEY", "linko-maxfiy-kalit-2026")

DB_PATH = os.path.join(os.path.dirname(__file__), "linko.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------- Tillar (i18n) - barcha matnlar translations.py faylida ----------
from translations import LANG_NAMES, TRANSLATIONS

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


OPEN_ENDPOINTS = {
    "static", "media", "login", "register", "forgot_password",
    "set_language", "privacy_page",
}


@app.before_request
def validate_session_user():
    """Sessiyadagi foydalanuvchi bazada bor-yo'qligini tekshiradi va profil ma'lumotlarini yangilab turadi.
    (Baza almashgandan keyin eski sessiya qolib ketib, sahifalar xato bermasligi uchun.)"""
    if request.endpoint in OPEN_ENDPOINTS or "user_id" not in session:
        return
    conn = get_db()
    row = conn.execute(
        "SELECT id, username, avatar_letter, nickname, avatar_file FROM users WHERE username = ?",
        (session.get("username", ""),),
    ).fetchone()
    conn.close()
    if not row:
        session.clear()
        return
    session["user_id"] = row["id"]
    session["avatar_letter"] = row["avatar_letter"]
    session["nickname"] = row["nickname"]
    session["avatar_file"] = row["avatar_file"]


@app.context_processor
def inject_translations():
    lang = current_lang()
    return dict(t=TRANSLATIONS[lang], lang=lang, langs=LANG_NAMES)


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

    for idx_sql in INDEX_STATEMENTS:
        conn.execute(idx_sql)

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
        security_answer = request.form.get("security_answer", "").strip()
        terms_accepted = request.form.get("terms_accepted")

        if not username or not password or not security_answer:
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
                hash_password(security_answer.lower()),
                datetime.now().strftime("%d.%m.%Y %H:%M"),
            ),
        )
        conn.commit()
        conn.close()

        flash("Muvaffaqiyatli ro'yxatdan o'tdingiz! Endi kirishingiz mumkin.")
        return redirect(url_for("login"))

    return render_template("register.html")


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
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["avatar_letter"] = user["avatar_letter"]
            session["nickname"] = user["nickname"]
            session["avatar_file"] = user["avatar_file"]
            return redirect(url_for("dashboard"))
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
                flash("Bu hisobda xavfsizlik savoli o'rnatilmagan. Yordam uchun bog'laning.")
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

    recent_rows = conn.execute(
        """SELECT partner, MAX(mid) as last_id FROM (
             SELECT id as mid, CASE WHEN sender = ? THEN receiver ELSE sender END as partner
             FROM private_messages WHERE sender = ? OR receiver = ?
           ) AS chat_pairs GROUP BY partner ORDER BY last_id DESC LIMIT 4""",
        (me, me, me),
    ).fetchall()

    recent_chats = []
    for r in recent_rows:
        user_row = conn.execute(
            "SELECT username, avatar_letter, avatar_file, nickname FROM users WHERE username = ?",
            (r["partner"],),
        ).fetchone()
        if user_row:
            recent_chats.append(user_row)
    conn.close()

    return render_template(
        "dashboard.html",
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
    """Bazaga saqlangan rasmlarni ko'rsatadi (static/uploads o'rniga)"""
    conn = get_db()
    row = conn.execute(
        "SELECT mimetype, data FROM uploaded_images WHERE filename = ?", (filename,)
    ).fetchone()
    conn.close()

    if not row:
        return "", 404

    data = row["data"]
    if isinstance(data, memoryview):
        data = bytes(data)
    response = Response(data, mimetype=row["mimetype"])
    response.headers["Cache-Control"] = "public, max-age=31536000"
    return response


@app.route("/feed", methods=["GET", "POST"])
def feed():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        image_file = request.files.get("image")
        image_filename = None

        conn = get_db()

        if image_file and image_file.filename and allowed_file(image_file.filename):
            image_filename = save_image_to_db(conn, image_file)

        if content or image_filename:
            conn.execute(
                "INSERT INTO posts (username, avatar_letter, content, image_file, created_at) VALUES (?, ?, ?, ?, ?)",
                (
                    session["username"],
                    session["avatar_letter"],
                    content,
                    image_filename,
                    datetime.now().strftime("%d.%m %H:%M"),
                ),
            )
            conn.commit()
        conn.close()

        return redirect(url_for("feed"))

    page = max(request.args.get("page", 1, type=int) or 1, 1)
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM posts ORDER BY id DESC LIMIT ? OFFSET ?",
        (PAGE_SIZE + 1, (page - 1) * PAGE_SIZE),
    ).fetchall()
    has_more = len(rows) > PAGE_SIZE
    posts = rows[:PAGE_SIZE]

    counts, mine = {}, set()
    if posts:
        ids = [p["id"] for p in posts]
        marks = ",".join("?" for _ in ids)
        for r in conn.execute(
            f"SELECT post_id, COUNT(*) AS c FROM likes WHERE post_id IN ({marks}) GROUP BY post_id",
            tuple(ids),
        ).fetchall():
            counts[r["post_id"]] = r["c"]
        for r in conn.execute(
            f"SELECT post_id FROM likes WHERE username = ? AND post_id IN ({marks})",
            (session["username"], *ids),
        ).fetchall():
            mine.add(r["post_id"])

    result = [
        {
            "id": p["id"],
            "username": p["username"],
            "avatar_letter": p["avatar_letter"],
            "content": p["content"],
            "image_file": p["image_file"],
            "created_at": p["created_at"],
            "like_count": counts.get(p["id"], 0),
            "liked_by_me": p["id"] in mine,
        }
        for p in posts
    ]
    conn.close()

    return render_template(
        "feed.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        posts=result,
        page=page,
        has_more=has_more,
        active="feed",
    )


@app.route("/api/posts/delete/<int:post_id>", methods=["POST"])
def api_post_delete(post_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    post = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()

    if not post or post["username"] != session["username"]:
        conn.close()
        return jsonify({"error": "ruxsat yo'q"}), 403

    if post["image_file"]:
        delete_image_from_db(conn, post["image_file"])

    conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.execute("DELETE FROM likes WHERE post_id = ?", (post_id,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


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


@app.route("/shop", methods=["GET", "POST"])
def shop():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        price_raw = request.form.get("price", "").strip()
        image_file = request.files.get("image")
        image_filename = None

        try:
            price = int(price_raw)
        except ValueError:
            price = 0

        conn = get_db()

        if image_file and image_file.filename and allowed_file(image_file.filename):
            image_filename = save_image_to_db(conn, image_file)

        if title and price > 0:
            conn.execute(
                """INSERT INTO products
                   (seller_username, seller_avatar, title, description, price, image_file, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    session["username"],
                    session["avatar_letter"],
                    title,
                    description,
                    price,
                    image_filename,
                    datetime.now().strftime("%d.%m %H:%M"),
                ),
            )
            conn.commit()
        conn.close()

        return redirect(url_for("shop"))

    conn = get_db()
    page = max(request.args.get("page", 1, type=int) or 1, 1)
    rows = conn.execute(
        "SELECT * FROM products ORDER BY id DESC LIMIT ? OFFSET ?",
        (PAGE_SIZE + 1, (page - 1) * PAGE_SIZE),
    ).fetchall()
    has_more = len(rows) > PAGE_SIZE
    products = rows[:PAGE_SIZE]
    cart_count = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) as c FROM cart_items WHERE username = ?",
        (session["username"],),
    ).fetchone()["c"]
    conn.close()

    return render_template(
        "shop.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        products=products,
        page=page,
        has_more=has_more,
        cart_count=cart_count,
        active="shop",
    )


@app.route("/api/cart/add/<int:product_id>", methods=["POST"])
def api_cart_add(product_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    existing = conn.execute(
        "SELECT id, quantity FROM cart_items WHERE username = ? AND product_id = ?",
        (session["username"], product_id),
    ).fetchone()

    if existing:
        conn.execute(
            "UPDATE cart_items SET quantity = quantity + 1 WHERE id = ?", (existing["id"],)
        )
    else:
        conn.execute(
            "INSERT INTO cart_items (username, product_id, quantity) VALUES (?, ?, 1)",
            (session["username"], product_id),
        )
    conn.commit()

    cart_count = conn.execute(
        "SELECT COALESCE(SUM(quantity), 0) as c FROM cart_items WHERE username = ?",
        (session["username"],),
    ).fetchone()["c"]
    conn.close()

    return jsonify({"ok": True, "cart_count": cart_count})


@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    items = conn.execute(
        """SELECT cart_items.id as cart_id, cart_items.quantity, products.*
           FROM cart_items JOIN products ON cart_items.product_id = products.id
           WHERE cart_items.username = ?""",
        (session["username"],),
    ).fetchall()
    conn.close()

    total = sum(item["price"] * item["quantity"] for item in items)

    return render_template(
        "cart.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        items=items,
        total=total,
        active="shop",
    )


@app.route("/api/cart/remove/<int:cart_id>", methods=["POST"])
def api_cart_remove(cart_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    conn.execute(
        "DELETE FROM cart_items WHERE id = ? AND username = ?",
        (cart_id, session["username"]),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/checkout", methods=["POST"])
def checkout():
    """Hozircha soxta/test to'lov - haqiqiy pul o'tkazilmaydi"""
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute("DELETE FROM cart_items WHERE username = ?", (session["username"],))
    conn.commit()
    conn.close()

    flash("Buyurtmangiz qabul qilindi! (test rejimida, haqiqiy to'lov hali ulanmagan)")
    return redirect(url_for("shop"))


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
    if query:
        rows = conn.execute(
            """SELECT username, avatar_letter, avatar_file, nickname FROM users
               WHERE username != ? AND (LOWER(username) LIKE LOWER(?) OR LOWER(COALESCE(nickname, '')) LIKE LOWER(?))
               ORDER BY username LIMIT 20""",
            (me, f"%{query}%", f"%{query}%"),
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

    add_url = request.host_url.rstrip("/") + url_for("add_contact_page", target_username=session["username"])
    qr_b64 = generate_qr_base64(add_url)

    return render_template(
        "qr.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        qr_b64=qr_b64,
        add_url=add_url,
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
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    conn = get_db()
    target = conn.execute("SELECT * FROM users WHERE username = ?", (target_username,)).fetchone()

    if not target:
        conn.close()
        flash("Bunday foydalanuvchi topilmadi")
        return redirect(url_for("people"))

    is_me = target_username == me
    is_contact = conn.execute(
        "SELECT 1 FROM contacts WHERE username = ? AND contact_username = ?", (me, target_username)
    ).fetchone()
    is_pending = conn.execute(
        "SELECT 1 FROM contact_requests WHERE from_username = ? AND to_username = ?", (me, target_username)
    ).fetchone()
    conn.close()

    return render_template(
        "add_contact.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        target=target,
        is_me=is_me,
        is_contact=bool(is_contact),
        is_pending=bool(is_pending),
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
    conn.close()

    if not other:
        return redirect(url_for("people"))

    return render_template(
        "dm.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        other_username=other["username"],
        other_avatar=other["avatar_letter"],
        other_avatar_file=other["avatar_file"],
        active="shaxsiy",
    )


@app.route("/api/dm/<other_username>")
def api_dm_messages(other_username):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    me = session["username"]
    conn = get_db()
    rows = conn.execute(
        """SELECT id, sender, receiver, content, image_file, created_at FROM private_messages
           WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
           ORDER BY id DESC LIMIT 100""",
        (me, other_username, other_username, me),
    ).fetchall()
    conn.close()

    messages = [
        {
            "id": r["id"],
            "sender": r["sender"],
            "content": r["content"],
            "image_file": r["image_file"],
            "created_at": r["created_at"],
        }
        for r in reversed(rows)
    ]
    return jsonify({"messages": messages, "me": me})


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

    content = (request.form.get("content") or "").strip()
    image_file = request.files.get("image")
    image_filename = None

    conn = get_db()

    if image_file and image_file.filename and allowed_file(image_file.filename):
        image_filename = save_image_to_db(conn, image_file)

    if not content and not image_filename:
        conn.close()
        return jsonify({"error": "bo'sh xabar"}), 400

    conn.execute(
        "INSERT INTO private_messages (sender, receiver, content, image_file, created_at) VALUES (?, ?, ?, ?, ?)",
        (session["username"], other_username, content[:1000], image_filename, datetime.now().strftime("%H:%M")),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/shaxsiy")
def shaxsiy():
    if "user_id" not in session:
        return redirect(url_for("login"))

    me = session["username"]
    conn = get_db()
    rows = conn.execute(
        """SELECT DISTINCT CASE WHEN sender = ? THEN receiver ELSE sender END AS partner
           FROM private_messages WHERE sender = ? OR receiver = ?""",
        (me, me, me),
    ).fetchall()

    conversations = []
    for r in rows:
        user_row = conn.execute(
            "SELECT username, avatar_letter, avatar_file, nickname FROM users WHERE username = ?",
            (r["partner"],),
        ).fetchone()
        if user_row:
            conversations.append(user_row)
    conn.close()

    return render_template(
        "shaxsiy.html",
        username=me,
        avatar_letter=session["avatar_letter"],
        conversations=conversations,
        active="shaxsiy",
    )


@app.route("/groups")
def groups_list():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    my_groups = conn.execute(
        """SELECT groups.* FROM groups
           JOIN group_members ON groups.id = group_members.group_id
           WHERE group_members.username = ? ORDER BY groups.id DESC""",
        (session["username"],),
    ).fetchall()
    conn.close()

    return render_template(
        "groups.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        my_groups=my_groups,
        active="groups",
    )


@app.route("/groups/new", methods=["GET", "POST"])
def group_new():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        selected = request.form.getlist("members")

        if name:
            cur = conn.execute(
                "INSERT INTO groups (name, avatar_letter, created_by, created_at) VALUES (?, ?, ?, ?)",
                (name, name[0].upper(), session["username"], datetime.now().strftime("%d.%m %H:%M")),
            )
            group_id = cur.lastrowid

            conn.execute(
                "INSERT OR IGNORE INTO group_members (group_id, username) VALUES (?, ?)",
                (group_id, session["username"]),
            )
            for member in selected:
                conn.execute(
                    "INSERT OR IGNORE INTO group_members (group_id, username) VALUES (?, ?)",
                    (group_id, member),
                )
            conn.commit()
            conn.close()
            return redirect(url_for("group_chat", group_id=group_id))

    users = conn.execute(
        "SELECT username, avatar_letter FROM users WHERE username != ? ORDER BY username",
        (session["username"],),
    ).fetchall()
    conn.close()

    return render_template(
        "group_new.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        users=users,
        active="groups",
    )


@app.route("/groups/<int:group_id>")
def group_chat(group_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    group = conn.execute("SELECT * FROM groups WHERE id = ?", (group_id,)).fetchone()
    is_member = conn.execute(
        "SELECT 1 FROM group_members WHERE group_id = ? AND username = ?",
        (group_id, session["username"]),
    ).fetchone()
    conn.close()

    if not group or not is_member:
        return redirect(url_for("groups_list"))

    return render_template(
        "group_chat.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        group=group,
        active="groups",
    )


@app.route("/api/groups/<int:group_id>/messages")
def api_group_messages(group_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    is_member = conn.execute(
        "SELECT 1 FROM group_members WHERE group_id = ? AND username = ?",
        (group_id, session["username"]),
    ).fetchone()
    if not is_member:
        conn.close()
        return jsonify({"error": "a'zo emassiz"}), 403

    rows = conn.execute(
        "SELECT id, username, content, image_file, created_at FROM group_messages WHERE group_id = ? ORDER BY id DESC LIMIT 100",
        (group_id,),
    ).fetchall()
    conn.close()

    messages = [
        {
            "id": r["id"],
            "username": r["username"],
            "content": r["content"],
            "image_file": r["image_file"],
            "created_at": r["created_at"],
        }
        for r in reversed(rows)
    ]
    return jsonify({"messages": messages, "me": session["username"]})


@app.route("/api/groups/message/delete/<int:message_id>", methods=["POST"])
def api_group_message_delete(message_id):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    conn = get_db()
    msg = conn.execute("SELECT * FROM group_messages WHERE id = ?", (message_id,)).fetchone()

    if not msg or msg["username"] != session["username"]:
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

    conn = get_db()
    is_member = conn.execute(
        "SELECT 1 FROM group_members WHERE group_id = ? AND username = ?",
        (group_id, session["username"]),
    ).fetchone()
    if not is_member:
        conn.close()
        return jsonify({"error": "a'zo emassiz"}), 403

    content = (request.form.get("content") or "").strip()
    image_file = request.files.get("image")
    image_filename = None

    if image_file and image_file.filename and allowed_file(image_file.filename):
        image_filename = save_image_to_db(conn, image_file)

    if not content and not image_filename:
        conn.close()
        return jsonify({"error": "bo'sh xabar"}), 400

    conn.execute(
        "INSERT INTO group_messages (group_id, username, content, image_file, created_at) VALUES (?, ?, ?, ?, ?)",
        (group_id, session["username"], content[:1000], image_filename, datetime.now().strftime("%H:%M")),
    )
    conn.commit()
    conn.close()

    return jsonify({"ok": True})


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    username = session["username"]
    conn = get_db()

    posts = conn.execute(
        "SELECT * FROM posts WHERE username = ? ORDER BY id DESC", (username,)
    ).fetchall()
    products = conn.execute(
        "SELECT * FROM products WHERE seller_username = ? ORDER BY id DESC", (username,)
    ).fetchall()
    user_row = conn.execute(
        "SELECT nickname, avatar_file FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    return render_template(
        "profile.html",
        username=username,
        avatar_letter=session["avatar_letter"],
        avatar_file=session.get("avatar_file"),
        posts=posts,
        products=products,
        nickname=user_row["nickname"] if user_row else None,
        active="profile",
    )


@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()
        avatar_image = request.files.get("avatar_image")

        conn = get_db()

        if avatar_image and avatar_image.filename and allowed_file(avatar_image.filename):
            unique_name = save_image_to_db(conn, avatar_image, prefix=f"avatar_{session['username']}_", avatar=True)
            conn.execute(
                "UPDATE users SET avatar_file = ? WHERE username = ?",
                (unique_name, session["username"]),
            )
            session["avatar_file"] = unique_name

        if nickname:
            existing = conn.execute(
                "SELECT username FROM users WHERE nickname = ? AND username != ?",
                (nickname, session["username"]),
            ).fetchone()

            if existing:
                conn.close()
                flash("Bu nickname band, boshqasini tanlang")
                return render_template(
                    "profile_edit.html",
                    username=session["username"],
                    avatar_letter=session["avatar_letter"],
                    avatar_file=session.get("avatar_file"),
                    nickname=nickname,
                )

            conn.execute(
                "UPDATE users SET nickname = ? WHERE username = ?",
                (nickname, session["username"]),
            )
            session["nickname"] = nickname

        conn.commit()
        conn.close()
        flash("Profil yangilandi!")
        return redirect(url_for("profile"))

    conn = get_db()
    user_row = conn.execute(
        "SELECT nickname, avatar_file FROM users WHERE username = ?", (session["username"],)
    ).fetchone()
    conn.close()

    return render_template(
        "profile_edit.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        nickname=user_row["nickname"] or "",
        avatar_file=user_row["avatar_file"],
    )


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
        "SELECT nickname FROM users WHERE username = ?", (session["username"],)
    ).fetchone()
    conn.close()

    return render_template(
        "settings.html",
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


@app.route("/settings/<section>")
def settings_stub(section):
    if "user_id" not in session:
        return redirect(url_for("login"))
    if section not in SETTINGS_STUBS:
        return redirect(url_for("settings_page"))

    title = SETTINGS_STUBS[section].get(current_lang(), SETTINGS_STUBS[section]["uz"])
    return render_template(
        "settings_stub.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        title=title,
        active="profile",
    )


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


@app.route("/logout")
def logout():
    session.clear()
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
