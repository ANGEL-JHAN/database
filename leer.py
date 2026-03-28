import sqlite3

def leer():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM mensajes")
    datos = cursor.fetchall()

    conn.close()

    return datos

# 🧪 mostrar datos
for fila in leer():
    print(fila)