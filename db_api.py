from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import uuid
import os

app = Flask(__name__)

# 🟢 Ruta de prueba
@app.route("/")
def home():
    return "API Python funcionando 🚀"

# 💾 Guardar datos (NO TOCADO)
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
# 🔥 NUEVO: SISTEMA HOSTING
# =========================

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 👤 Usuarios
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE,
        plan TEXT DEFAULT 'free'
    )
    """)

    # 🖥️ Servidores
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


# 👤 Crear usuario
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


# 👤 Ver usuarios
@app.route("/users", methods=["GET"])
def obtener_users():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    conn.close()

    return jsonify(users)


# 🖥️ Crear servidor
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


# 📋 Ver servidores
@app.route("/servers", methods=["GET"])
def obtener_servers():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM servers")
    servers = cursor.fetchall()

    conn.close()

    return jsonify(servers)


# 📋 Servidores por usuario
@app.route("/servers/<int:user_id>", methods=["GET"])
def servers_usuario(user_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM servers WHERE user_id = ?", (user_id,))
    servers = cursor.fetchall()

    conn.close()

    return jsonify(servers)


# 🚀 IMPORTANTE PARA RENDER
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)