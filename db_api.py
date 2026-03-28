from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

@app.route("/guardar", methods=["POST"])
def guardar():
    data = request.json
    mensaje = data.get("mensaje")
    respuesta = data.get("respuesta")

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO mensajes (mensaje, respuesta, fecha)
    VALUES (?, ?, ?)
    """, (mensaje, respuesta, str(datetime.now())))

    conn.commit()
    conn.close()

    return jsonify({"status": "guardado"})

app.run(port=5000)