import sqlite3
from datetime import datetime

def guardar(mensaje, respuesta):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO mensajes (mensaje, respuesta, fecha)
    VALUES (?, ?, ?)
    """, (mensaje, respuesta, str(datetime.now())))

    conn.commit()
    conn.close()

    print("💾 Guardado")

# 🧪 prueba
guardar("hola", "soy tu IA")