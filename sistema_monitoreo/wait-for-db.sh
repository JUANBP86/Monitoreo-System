#!/usr/bin/env bash
set -e

: "Esperar a que la base de datos MySQL esté lista" 

HOST=${DB_HOST:-db}
USER=${DB_USER:-root}
PASS=${DB_PASSWORD:-}

echo "Esperando a la base de datos en $HOST..."

until mysql -h "$HOST" -u "$USER" -p"$PASS" --ssl=0 -e "SELECT 1" >/dev/null 2>&1; do
  echo "  - aún no disponible; reintentando en 2s..."
  sleep 2
done

echo "Base de datos disponible. Ejecutando migraciones e inicialización..."
python run_init.py || true
python check_admin.py || true
echo "Iniciando la aplicación..."
exec python app.py
