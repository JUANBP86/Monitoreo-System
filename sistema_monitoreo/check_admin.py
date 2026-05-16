import mysql.connector
from werkzeug.security import generate_password_hash

DB = dict(host='db', user='monitoreo', password='monitoreo_pass', database='monitoreo_sistemas')

try:
    c = mysql.connector.connect(**DB)
    cur = c.cursor()
    cur.execute("SELECT id FROM usuarios WHERE username='jbohorquez'")
    rows = cur.fetchall()
    if rows:
        print('Admin already exists:', rows)
    else:
        pwd_hash = generate_password_hash('admin123')
        cur.execute("INSERT INTO usuarios (username, correo, contraseña, nombre, rol, activo) VALUES (%s,%s,%s,%s,%s,%s)",
                    ('jbohorquez', 'jbohorquez@example.com', pwd_hash, 'Juan Bohorquez', 'admin', 1))
        c.commit()
        print('Admin created')
except Exception as e:
    print('ERROR', e)
