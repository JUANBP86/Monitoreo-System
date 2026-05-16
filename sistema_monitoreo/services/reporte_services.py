from io import StringIO
import csv


def _build_date_filter(prefix, fecha_inicio, fecha_fin):
    condiciones = []
    params = []

    if fecha_inicio:
        condiciones.append(f"{prefix} >= %s")
        params.append(fecha_inicio)
    if fecha_fin:
        condiciones.append(f"{prefix} < %s")
        params.append(fecha_fin)

    clause = " AND " + " AND ".join(condiciones) if condiciones else ""
    return clause, params


def obtener_resumen_reportes(conexion, usuario_id, fecha_inicio=None, fecha_fin=None):
    cursor = conexion.cursor()

    cursor.execute("SELECT COUNT(*) FROM dispositivos WHERE usuario_id = %s", (usuario_id,))
    total_dispositivos = cursor.fetchone()[0] or 0

    filtro_metricas, params_metricas = _build_date_filter('m.fecha', fecha_inicio, fecha_fin)
    cursor.execute(
        f"SELECT COUNT(*) FROM metricas m "
        f"JOIN dispositivos d ON d.id = m.dispositivo_id "
        f"WHERE d.usuario_id = %s{filtro_metricas}",
        tuple([usuario_id] + params_metricas)
    )
    total_metricas = cursor.fetchone()[0] or 0

    cursor.execute(
        f"SELECT COUNT(*) FROM metricas m "
        f"JOIN dispositivos d ON d.id = m.dispositivo_id "
        f"WHERE d.usuario_id = %s AND m.estado = 'CRITICO'{filtro_metricas}",
        tuple([usuario_id] + params_metricas)
    )
    total_criticos = cursor.fetchone()[0] or 0

    filtros_alertas, params_alertas = _build_date_filter('a.fecha_alerta', fecha_inicio, fecha_fin)
    cursor.execute(
        f"SELECT COUNT(*) FROM alertas a WHERE a.usuario_id = %s{filtros_alertas}",
        tuple([usuario_id] + params_alertas)
    )
    total_alertas = cursor.fetchone()[0] or 0

    cursor.execute(
        "SELECT COUNT(*) FROM alertas WHERE usuario_id = %s AND resuelta = FALSE",
        (usuario_id,)
    )
    abiertas = cursor.fetchone()[0] or 0

    return {
        'total_dispositivos': total_dispositivos,
        'total_metricas': total_metricas,
        'total_criticos': total_criticos,
        'total_alertas': total_alertas,
        'alertas_abiertas': abiertas
    }


def obtener_metricas_recientes(conexion, usuario_id, fecha_inicio=None, fecha_fin=None, limite=50):
    filtro, params = _build_date_filter('m.fecha', fecha_inicio, fecha_fin)
    sql = (
        "SELECT d.nombre AS dispositivo, d.ip, m.cpu, m.ram, m.disco, m.estado, m.fecha "
        "FROM metricas m "
        "JOIN dispositivos d ON d.id = m.dispositivo_id "
        "WHERE d.usuario_id = %s" + filtro + " "
        "ORDER BY m.fecha DESC LIMIT %s"
    )
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(sql, tuple([usuario_id] + params + [limite]))
    return cursor.fetchall()


def obtener_alertas(conexion, usuario_id, fecha_inicio=None, fecha_fin=None, limite=50):
    filtro, params = _build_date_filter('a.fecha_alerta', fecha_inicio, fecha_fin)
    sql = (
        "SELECT a.id, d.nombre AS dispositivo, d.ip, a.tipo, a.mensaje, a.fecha_alerta, a.resuelta, a.fecha_resolucion "
        "FROM alertas a "
        "JOIN dispositivos d ON d.id = a.dispositivo_id "
        "WHERE a.usuario_id = %s" + filtro + " "
        "ORDER BY a.fecha_alerta DESC LIMIT %s"
    )
    cursor = conexion.cursor(dictionary=True)
    cursor.execute(sql, tuple([usuario_id] + params + [limite]))
    return cursor.fetchall()


def exportar_reportes_csv(metricas, alertas):
    salida = StringIO()
    writer = csv.writer(salida)

    writer.writerow(['Tipo', 'Dispositivo', 'IP', 'Estado/Tema', 'CPU', 'RAM', 'DISCO', 'Fecha', 'Resuelta'])

    for m in metricas:
        writer.writerow([
            'Métrica',
            m.get('dispositivo'),
            m.get('ip'),
            m.get('estado'),
            m.get('cpu'),
            m.get('ram'),
            m.get('disco'),
            m.get('fecha'),
            ''
        ])

    writer.writerow([])
    writer.writerow(['Tipo', 'Dispositivo', 'IP', 'Alerta', 'Fecha', 'Resuelta'])

    for a in alertas:
        writer.writerow([
            'Alerta',
            a.get('dispositivo'),
            a.get('ip'),
            a.get('mensaje'),
            a.get('fecha_alerta'),
            'Sí' if a.get('resuelta') else 'No'
        ])

    return salida.getvalue()
