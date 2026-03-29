from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import uuid
import os

# 🔥 OAUTH (AQUÍ VA LO QUE PEDISTE)
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask import redirect, url_for

app = Flask(__name__)

# 🔐 Necesario para sesiones OAuth
app.secret_key = "supersecretkey"


# =========================
# 🔥 LOGIN OAUTH
# =========================

# ⚠️ REEMPLAZA CON TUS CLAVES REALES
google_bp = make_google_blueprint(
    client_id="GOOGLE_ID",
    client_secret="GOOGLE_SECRET",
    redirect_url="/login/google"
)
app.register_blueprint(google_bp, url_prefix="/login")

github_bp = make_github_blueprint(
    client_id="GITHUB_ID",
    client_secret="GITHUB_SECRET",
)
app.register_blueprint(github_bp, url_prefix="/login")

facebook_bp = make_facebook_blueprint(
    client_id="FACEBOOK_ID",
    client_secret="FACEBOOK_SECRET",
)
app.register_blueprint(facebook_bp, url_prefix="/login")


# =========================
# 🔐 RUTAS LOGIN
# =========================

@app.route("/login/google")
def login_google():
    if not google.authorized:
        return redirect(url_for("google.login"))

    resp = google.get("/oauth2/v2/userinfo")
    info = resp.json()

    email = info.get("email")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
        conn.commit()
    except:
        pass

    conn.close()

    return jsonify(info)


@app.route("/login/github")
def login_github():
    if not github.authorized:
        return redirect(url_for("github.login"))

    resp = github.get("/user")
    info = resp.json()

    email = info.get("email") or f"{info.get('login')}@github"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
        conn.commit()
    except:
        pass

    conn.close()

    return jsonify(info)


@app.route("/login/facebook")
def login_facebook():
    if not facebook.authorized:
        return redirect(url_for("facebook.login"))

    resp = facebook.get("/me?fields=id,name,email")
    info = resp.json()

    email = info.get("email") or f"{info.get('id')}@facebook"

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
        conn.commit()
    except:
        pass

    conn.close()

    return jsonify(info)


# =========================
# 🟢 TU API ORIGINAL (NO TOCADO)
# =========================

@app.route("/")
def home():
    return "API Python funcionando 🚀"

@app.route("/guardar", methods=["POST"])
def guardar():
    data = request.json
    mensaje = data.get("mensaje")
    respuesta = data.get("respuesta")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS mensajes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        mensaje TEXT,
        respuesta TEXT,
        fecha TEXT
    )
    """)

    cursor.execute("""
    INSERT INTO mensajes (mensaje, respuesta, fecha)
    VALUES (?, ?, ?)
    """, (mensaje, respuesta, str(datetime.now())))

    conn.commit()
    conn.close()

    return jsonify({"status": "guardado"})


# =========================
# 🔥 SISTEMA HOSTING
# =========================

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        plan TEXT DEFAULT 'free'
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS servers (
        id TEXT,
        user_id INTEGER,
        name TEXT,
        status TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

init_db()


@app.route("/users", methods=["POST"])
def crear_usuario():
    data = request.json
    email = data.get("email")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    try:
        cursor.execute("INSERT INTO users (email) VALUES (?)", (email,))
        conn.commit()
        return jsonify({"message": "Usuario creado"})
    except:
        return jsonify({"error": "Usuario ya existe"}), 400
    finally:
        conn.close()


@app.route("/users", methods=["GET"])
def obtener_users():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    conn.close()

    return jsonify(users)


@app.route("/servers", methods=["POST"])
def crear_server():
    data = request.json
    user_id = data.get("user_id")
    name = data.get("name")

    server_id = str(uuid.uuid4())

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO servers (id, user_id, name, status, created_at)
    VALUES (?, ?, ?, ?, ?)
    """, (server_id, user_id, name, "running", str(datetime.now())))

    conn.commit()
    conn.close()

    return jsonify({
        "message": "Servidor creado 🚀",
        "id": server_id,
        "name": name
    })


@app.route("/servers", methods=["GET"])
def obtener_servers():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM servers")
    servers = cursor.fetchall()

    conn.close()

    return jsonify(servers)


@app.route("/servers/<int:user_id>", methods=["GET"])
def servers_usuario(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM servers WHERE user_id = ?", (user_id,))
    servers = cursor.fetchall()

    conn.close()

    return jsonify(servers)


# =========================
# 🚀 RENDER
# =========================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)