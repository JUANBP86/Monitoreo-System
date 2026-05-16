import requests
from datetime import datetime, timedelta
from database import conectar
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID


def enviar_telegram(mensaje):
    """Envía un mensaje a Telegram si la configuración está disponible."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Configuración incompleta: no se envía el mensaje")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensaje,
        "parse_mode": "HTML"
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"[TELEGRAM] Error enviando mensaje: {e}")
        return False


def crear_alerta(conexion, dispositivo_id, usuario_id, tipo, mensaje):
    """Inserta una alerta nueva si no existe una alerta abierta del mismo tipo."""
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT id FROM alertas WHERE dispositivo_id = %s AND tipo = %s AND resuelta = FALSE",
        (dispositivo_id, tipo)
    )

    if cursor.fetchone():
        return False

    cursor.execute(
        "INSERT INTO alertas(dispositivo_id, usuario_id, tipo, mensaje, fecha_alerta) VALUES(%s, %s, %s, %s, NOW())",
        (dispositivo_id, usuario_id, tipo, mensaje)
    )
    conexion.commit()
    return True


def obtener_alertas_usuario(conexion, usuario_id):
    """Obtiene todas las alertas del usuario, ordenadas por fecha."""
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT a.id, a.dispositivo_id, d.nombre AS dispositivo, d.ip, a.tipo, a.mensaje, a.fecha_alerta, a.resuelta, a.fecha_resolucion "
        "FROM alertas a "
        "JOIN dispositivos d ON d.id = a.dispositivo_id "
        "WHERE a.usuario_id = %s "
        "ORDER BY a.fecha_alerta DESC",
        (usuario_id,)
    )
    return cursor.fetchall()


def contar_alertas_abiertas(conexion, usuario_id):
    """Cuenta alertas abiertas para un usuario."""
    cursor = conexion.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM alertas WHERE usuario_id = %s AND resuelta = FALSE",
        (usuario_id,)
    )
    resultado = cursor.fetchone()
    return resultado[0] if resultado else 0


def resolver_alerta(conexion, alerta_id, usuario_id):
    """Marca una alerta como resuelta si pertenece al usuario."""
    cursor = conexion.cursor()
    cursor.execute(
        "UPDATE alertas SET resuelta = TRUE, fecha_resolucion = NOW() "
        "WHERE id = %s AND usuario_id = %s AND resuelta = FALSE",
        (alerta_id, usuario_id)
    )
    conexion.commit()
    return cursor.rowcount > 0


def verificar_alertas_offline(conexion, usuario_id, umbral_minutos=5):
    """Genera alertas offline cuando un dispositivo no envía métricas dentro del umbral."""
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(
        "SELECT d.id, d.nombre, d.ip, "
        "(SELECT fecha FROM metricas WHERE dispositivo_id = d.id ORDER BY fecha DESC LIMIT 1) AS ultima_actualizacion "
        "FROM dispositivos d "
        "WHERE d.usuario_id = %s",
        (usuario_id,)
    )

    dispositivos = cursor.fetchall()
    ahora = datetime.now()
    umbral = ahora - timedelta(minutes=umbral_minutos)
    created = 0

    for dispositivo in dispositivos:
        ultima = dispositivo['ultima_actualizacion']
        if ultima is None or ultima < umbral:
            mensaje = (
                f"OFFLINE: {dispositivo['nombre']} ({dispositivo['ip']}) "
                f"no ha enviado métricas desde {ultima.strftime('%Y-%m-%d %H:%M:%S') if ultima else 'inicio'}"
            )
            if crear_alerta(conexion, dispositivo['id'], usuario_id, 'OFFLINE', mensaje):
                enviar_telegram(mensaje)
                created += 1
    return created
