import mysql.connector
import os

SQL_PATH = '/app/database_setup.sql'
DB_CONFIG = dict(host='db', user='root', password='root_password', database='monitoreo_sistemas')

if not os.path.exists(SQL_PATH):
    print('No se encontró', SQL_PATH)
    raise SystemExit(1)

with open(SQL_PATH, 'r', encoding='utf-8') as f:
    sql = f.read()

try:
    conn = mysql.connector.connect(host=DB_CONFIG['host'], user=DB_CONFIG['user'], password=DB_CONFIG['password'])
    cursor = conn.cursor()
    # Create database if not exists
    cursor.execute("CREATE DATABASE IF NOT EXISTS monitoreo_sistemas CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    conn.close()

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    # Split statements by semicolon and execute
    statements = [s.strip() for s in sql.split(';') if s.strip()]
    for stmt in statements:
        try:
            cursor.execute(stmt)
            # fetch to clear results if any
            try:
                if cursor.with_rows:
                    _ = cursor.fetchall()
            except Exception:
                pass
        except Exception as inner_e:
            print('Statement error:', inner_e)
    conn.commit()
    print('Schema applied')
except Exception as e:
    print('ERROR', e)
