#!/usr/bin/env bash
set -e

echo "Esperando a la base de datos en ${DB_HOST:-db}..."

# Usar Python para verificar la conexión (más confiable que el cliente mysql)
until python -c "
import mysql.connector, os, sys
try:
    conn = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'db'),
        user=os.environ.get('DB_USER', 'monitoreo'),
        password=os.environ.get('DB_PASSWORD', 'monitoreo_pass'),
        database=os.environ.get('DB_NAME', 'monitoreo_sistemas'),
        connection_timeout=5
    )
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
" 2>/dev/null; do
  echo "  - aún no disponible; reintentando en 3s..."
  sleep 3
done

echo "Base de datos disponible. Ejecutando migraciones e inicialización..."
python run_init.py || true
python check_admin.py || true
echo "Iniciando la aplicación..."
exec python app.py
