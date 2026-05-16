"""
Script de espera para la base de datos y arranque de la aplicación.
Reemplaza wait-for-db.sh para evitar problemas de line endings en Windows/Docker.
"""
import subprocess
import sys
import time
import os

def wait_for_db():
    """Espera hasta que MySQL esté disponible."""
    import mysql.connector

    host = os.environ.get('DB_HOST', 'db')
    user = os.environ.get('DB_USER', 'monitoreo')
    password = os.environ.get('DB_PASSWORD', 'monitoreo_pass')
    database = os.environ.get('DB_NAME', 'monitoreo_sistemas')

    print(f"Esperando a la base de datos en {host}...")

    while True:
        try:
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=password,
                database=database,
                connection_timeout=5
            )
            conn.close()
            print("Base de datos disponible.")
            return
        except Exception:
            print("  - aún no disponible; reintentando en 3s...")
            time.sleep(3)


def run_command(cmd, description):
    """Ejecuta un comando y muestra el resultado."""
    print(f"{description}...")
    try:
        result = subprocess.run(
            [sys.executable] + cmd,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.stdout:
            print(result.stdout)
        if result.returncode != 0 and result.stderr:
            print(f"  Advertencia: {result.stderr}")
    except Exception as e:
        print(f"  Error en {description}: {e}")


if __name__ == '__main__':
    wait_for_db()

    run_command(['run_init.py'], 'Ejecutando migraciones')
    run_command(['check_admin.py'], 'Verificando admin')

    print("Iniciando la aplicación...")
    os.execvp(sys.executable, [sys.executable, 'app.py'])
