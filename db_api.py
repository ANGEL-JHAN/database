from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime
import uuid
import os
import json
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# 🚀 APP
# =========================
app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)

# =========================
# 🔑 KEYS.JSON + ADMIN
# =========================
KEYS_FILE = "keys.json"
ADMIN_KEY = "123456"

if os.path.exists(KEYS_FILE):
    with open(KEYS_FILE, "r") as f:
        api_keys = json.load(f)
else:
    api_keys = []

# Añadir key admin si no existe
if not any(k.get("apiKey") == ADMIN_KEY for k in api_keys):
    api_keys.append({
        "usuario": "admin",
        "apiKey": ADMIN_KEY,
        "plan": "admin",
        "uso": 0,
        "limite": 999999,
        "resumen": ""  # Guardaremos aquí el contexto resumido
    })
    with open(KEYS_FILE, "w") as f:
        json.dump(api_keys, f, indent=2)

def guardar_keys():
    with open(KEYS_FILE, "w") as f:
        json.dump(api_keys, f, indent=2)

def validar_key(key):
    if not key:
        return None, "Falta API KEY"
    for k in api_keys:
        if k["apiKey"] == key:
            if k.get("uso",0) >= k.get("limite",999999):
                return None, "Límite alcanzado"
            return k, None
    return None, "API KEY inválida"

# =========================
# 🔹 GENERAR / ELIMINAR KEYS
# =========================
@app.route("/generate-key", methods=["POST"])
def generate_key():
    data = request.json
    usuario = data.get("usuario", "anonimo")
    plan = data.get("plan", "free")
    planes = {"free":50,"pro":500,"enterprise":999999}
    if plan not in planes:
        return jsonify({"error":"Plan inválido"}),400
    new_key = str(uuid.uuid4())
    nueva_key = {"usuario":usuario,"apiKey":new_key,"plan":plan,"uso":0,"limite":planes[plan],"resumen":""}
    api_keys.append(nueva_key)
    guardar_keys()
    return jsonify({"usuario":usuario,"apiKey":new_key,"plan":plan,"limite":nueva_key["limite"]})

@app.route("/delete-key/<key>", methods=["DELETE"])
def delete_key(key):
    global api_keys
    antes = len(api_keys)
    api_keys = [k for k in api_keys if k["apiKey"] != key and k["apiKey"] != ADMIN_KEY]
    guardar_keys()
    if len(api_keys)==antes:
        return jsonify({"error":"Key no encontrada"}),404
    return jsonify({"success":True})

# =========================
# 🔹 DB INIT
# =========================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE,
            user TEXT UNIQUE,
            name TEXT,
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
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mensajes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            mensaje TEXT,
            respuesta TEXT,
            fecha TEXT
        )
    """)
    conn.commit()
    conn.close()
init_db()

# =========================
# 🔹 REGISTER
# =========================
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    email = data.get("email")
    user = data.get("user")
    name = data.get("name")
    password = data.get("password")
    
    if not email or not password or not user or not name:
        return jsonify({"error":"Faltan datos"}),400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    try:
        hashed = generate_password_hash(password)
        cursor.execute("INSERT INTO users (email,password,user,name) VALUES (?,?,?,?)",
                       (email,hashed,user,name))
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"error":"Usuario o email ya existe"}),400
    conn.close()
    return jsonify({"user":{"name":name,"user":user,"email":email}}),200

# =========================
# 🔹 LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error":"Faltan datos"}),400

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT email,user,name,password FROM users WHERE email=?",(email,))
    row = cursor.fetchone()
    conn.close()
    
    if row and check_password_hash(row[3], password):
        return jsonify({"user":{"name":row[2],"user":row[1],"email":row[0]}}),200
    return jsonify({"error":"Email o contraseña incorrectos"}),401

# =========================
# 🔹 IA MEMORIA OPTIMIZADA
# =========================
def generar_respuesta(usuario, mensaje, key_data):
    resumen = key_data.get("resumen","")
    respuesta = f"{resumen} → Respuesta a '{mensaje}'"
    nuevo_resumen = (resumen + f" [{usuario}:{mensaje}→{respuesta}]")[-5000:]
    key_data["resumen"] = nuevo_resumen
    return respuesta

# =========================
# 🔹 API IA
# =========================
@app.route("/api/ia", methods=["POST"])
def api_ia():
    key = request.headers.get("x-api-key")
    data = request.json
    mensaje = data.get("mensaje")
    usuario = data.get("usuario","anonimo")
    key_data, error = validar_key(key)
    if error:
        return jsonify({"error":error}),401
    if not mensaje:
        return jsonify({"error":"Falta mensaje"}),400

    respuesta = generar_respuesta(usuario, mensaje, key_data)

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO mensajes (usuario,mensaje,respuesta,fecha)
        VALUES (?,?,?,?)
    """,(usuario,mensaje,respuesta,str(datetime.now())))
    conn.commit()
    conn.close()

    key_data["uso"] = key_data.get("uso",0)+1
    guardar_keys()

    return jsonify({
        "respuesta":respuesta,
        "uso":key_data["uso"],
        "limite":key_data["limite"],
        "restante":key_data["limite"]-key_data["uso"]
    })

# =========================
# 🔹 Consultar todas las conversaciones
# =========================
@app.route("/mensajes", methods=["GET"])
def obtener_mensajes():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM mensajes ORDER BY fecha ASC")
    mensajes = cursor.fetchall()
    conn.close()
    resultados = [{"id":m[0],"usuario":m[1],"mensaje":m[2],"respuesta":m[3],"fecha":m[4]} for m in mensajes]
    return jsonify(resultados)

# =========================
# 🔹 Ruta raíz + test
# =========================
@app.route("/", methods=["GET"])
def home():
    return "API de ANGEL OFC funcionando. Usa /api/ia con POST."

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"status":"ok","message":"Servidor activo"})

# =========================
# 🚀 RUN
# =========================
if __name__=="__main__":
    port=int(os.environ.get("PORT",10000))
    app.run(host="0.0.0.0",port=port)