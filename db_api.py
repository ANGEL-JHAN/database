from flask import Flask, request, jsonify, redirect, url_for
import sqlite3
from datetime import datetime
import uuid
import os
import json

# 🌐 CORS
from flask_cors import CORS

# 🔐 Seguridad para contraseñas
from werkzeug.security import generate_password_hash, check_password_hash

# 🔥 OAUTH
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook

# =========================
# 🚀 CREAR APP
# =========================
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Necesario para sesiones OAuth
CORS(app)  # Habilita CORS para todas las rutas

# =========================
# 🔑 KEYS.JSON
# =========================
KEYS_FILE = "keys.json"

# Cargar keys existentes
if os.path.exists(KEYS_FILE):
    with open(KEYS_FILE, "r") as f:
        api_keys = json.load(f)
else:
    api_keys = []

@app.route("/generate-key", methods=["POST"])
def generate_key():
    data = request.json
    usuario = data.get("usuario", "anonimo")

    new_key = str(uuid.uuid4())
    api_keys.append({"usuario": usuario, "apiKey": new_key})

    # Guardar en keys.json
    with open(KEYS_FILE, "w") as f:
        json.dump(api_keys, f, indent=2)

    return jsonify({
        "usuario": usuario,
        "apiKey": new_key,
        "mensaje": "Tu API Key fue generada correctamente"
    })

# =========================
# 🔥 LOGIN OAUTH
# =========================
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
# 🔐 RUTAS LOGIN OAUTH
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
# 🟢 API ORIGINAL
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
# 🔥 SISTEMA HOSTING + DB INIT
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        password TEXT,
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

# =========================
# 🔹 REGISTER (email + contraseña)
# =========================
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Faltan campos"}), 400

    hashed_pw = generate_password_hash(password)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_pw))
        conn.commit()
        return jsonify({"message": "Usuario registrado exitosamente"}), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "Usuario ya existe"}), 400
    finally:
        conn.close()

# =========================
# 🔹 LOGIN (email + contraseña)
# =========================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": "Faltan campos"}), 400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, password, plan FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if user and check_password_hash(user[2], password):
        return jsonify({
            "message": "Login exitoso",
            "user": {
                "id": user[0],
                "email": user[1],
                "plan": user[3]
            }
        })
    else:
        return jsonify({"error": "Email o contraseña incorrectos"}), 401

# =========================
# 🔹 USERS / SERVERS
# =========================
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
# 🚀 RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)