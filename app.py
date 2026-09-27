# Linko - Login/Register tizimi
# Bu Linko ilovasining 1-bosqichi: foydalanuvchi ro'yxatdan o'tishi va tizimga kirishi

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import sqlite3
import hashlib
import os
from datetime import datetime
from werkzeug.utils import secure_filename

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from config import ANTHROPIC_API_KEY
except ImportError:
    ANTHROPIC_API_KEY = ""

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

app = Flask(__name__)
app.secret_key = "linko-maxfiy-kalit-2026"  # Ishlab chiqarishda buni murakkabroq qiling

DB_PATH = os.path.join(os.path.dirname(__file__), "linko.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db():
    """Bazaga ulanish yaratadi"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Baza va jadvalni birinchi marta yaratadi"""
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
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            receiver TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


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

        if not username or not password:
            flash("Iltimos, hamma maydonlarni to'ldiring")
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
            "INSERT INTO users (username, password_hash, avatar_letter) VALUES (?, ?, ?)",
            (username, hash_password(password), username[0].upper()),
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
            return redirect(url_for("dashboard"))
        else:
            flash("Login yoki parol xato")

    return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "dashboard.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        display_name=session.get("nickname") or session["username"],
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


@app.route("/feed", methods=["GET", "POST"])
def feed():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        content = request.form.get("content", "").strip()
        image_file = request.files.get("image")
        image_filename = None

        if image_file and image_file.filename and allowed_file(image_file.filename):
            safe_name = secure_filename(image_file.filename)
            unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))
            image_filename = unique_name

        if content or image_filename:
            conn = get_db()
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

    conn = get_db()
    posts = conn.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()

    result = []
    for p in posts:
        like_count = conn.execute(
            "SELECT COUNT(*) as c FROM likes WHERE post_id = ?", (p["id"],)
        ).fetchone()["c"]
        liked_by_me = conn.execute(
            "SELECT 1 FROM likes WHERE post_id = ? AND username = ?",
            (p["id"], session["username"]),
        ).fetchone()
        result.append(
            {
                "id": p["id"],
                "username": p["username"],
                "avatar_letter": p["avatar_letter"],
                "content": p["content"],
                "image_file": p["image_file"],
                "created_at": p["created_at"],
                "like_count": like_count,
                "liked_by_me": bool(liked_by_me),
            }
        )
    conn.close()

    return render_template(
        "feed.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        posts=result,
        active="feed",
    )


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

        if image_file and image_file.filename and allowed_file(image_file.filename):
            safe_name = secure_filename(image_file.filename)
            unique_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_name))
            image_filename = unique_name

        if title and price > 0:
            conn = get_db()
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
    products = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
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

    conn = get_db()
    users = conn.execute(
        "SELECT username, avatar_letter FROM users WHERE username != ? ORDER BY username",
        (session["username"],),
    ).fetchall()
    conn.close()

    return render_template(
        "people.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        users=users,
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
        active="people",
    )


@app.route("/api/dm/<other_username>")
def api_dm_messages(other_username):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    me = session["username"]
    conn = get_db()
    rows = conn.execute(
        """SELECT sender, receiver, content, created_at FROM private_messages
           WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)
           ORDER BY id DESC LIMIT 100""",
        (me, other_username, other_username, me),
    ).fetchall()
    conn.close()

    messages = [
        {"sender": r["sender"], "content": r["content"], "created_at": r["created_at"]}
        for r in reversed(rows)
    ]
    return jsonify({"messages": messages, "me": me})


@app.route("/api/dm/send/<other_username>", methods=["POST"])
def api_dm_send(other_username):
    if "user_id" not in session:
        return jsonify({"error": "kirish kerak"}), 401

    data = request.get_json(silent=True) or {}
    content = (data.get("content") or "").strip()

    if not content:
        return jsonify({"error": "bo'sh xabar"}), 400

    conn = get_db()
    conn.execute(
        "INSERT INTO private_messages (sender, receiver, content, created_at) VALUES (?, ?, ?, ?)",
        (session["username"], other_username, content[:1000], datetime.now().strftime("%H:%M")),
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
        "SELECT nickname FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    return render_template(
        "profile.html",
        username=username,
        avatar_letter=session["avatar_letter"],
        posts=posts,
        products=products,
        nickname=user_row["nickname"],
    )


@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        nickname = request.form.get("nickname", "").strip()

        if nickname:
            conn = get_db()
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
                    nickname=nickname,
                )

            conn.execute(
                "UPDATE users SET nickname = ? WHERE username = ?",
                (nickname, session["username"]),
            )
            conn.commit()
            conn.close()
            session["nickname"] = nickname
            flash("Nickname saqlandi!")

        return redirect(url_for("profile"))

    conn = get_db()
    user_row = conn.execute(
        "SELECT nickname FROM users WHERE username = ?", (session["username"],)
    ).fetchone()
    conn.close()

    return render_template(
        "profile_edit.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        nickname=user_row["nickname"] or "",
    )


@app.route("/settings")
def settings_page():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template(
        "settings.html",
        username=session["username"],
        avatar_letter=session["avatar_letter"],
        active="settings",
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
    print("Linko ishga tushmoqda... http://127.0.0.1:5000 manzilida oching")
    app.run(debug=True)
