from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# 🟢 Ruta de prueba
@app.route("/")
def home():
    return "API Python funcionando 🚀"

# 💾 Guardar datos
@app.route("/guardar", methods=["POST"])
def guardar():
    data = request.json
    mensaje = data.get("mensaje")
    respuesta = data.get("respuesta")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # 🧠 crear tabla si no existe (IMPORTANTE)
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

# 🚀 IMPORTANTE PARA RENDER
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)