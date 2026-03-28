import sqlite3

# 🗄️ Crear / conectar base de datos
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# 📊 Crear tabla
cursor.execute("""
CREATE TABLE IF NOT EXISTS mensajes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mensaje TEXT,
    respuesta TEXT,
    fecha TEXT
)
""")

conn.commit()
conn.close()

print("✅ Base de datos creada")