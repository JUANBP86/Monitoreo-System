from flask import Flask, render_template, request, redirect, jsonify, url_for, Response
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from database import conectar
from config import (
    DB_HOST, DB_USER, DB_PASSWORD, DB_NAME,
    TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID,
    MAIL_SERVER, MAIL_PORT, MAIL_USE_TLS, MAIL_USE_SSL,
    MAIL_USERNAME, MAIL_PASSWORD, MAIL_DEFAULT_SENDER
)
from services.alerta_services import (
    crear_alerta,
    enviar_telegram,
    obtener_alertas_usuario,
    contar_alertas_abiertas,
    resolver_alerta,
    verificar_alertas_offline
)
from services.reporte_services import (
    exportar_reportes_csv,
    obtener_resumen_reportes,
    obtener_metricas_recientes,
    obtener_alertas as obtener_alertas_reporte
)
from collections import defaultdict
from datetime import datetime, timedelta
import traceback
from functools import wraps
import json
import time

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.rol != 'admin':
            return render_template('error.html', mensaje="Acceso denegado. Se requiere rol de administrador."), 403
        return f(*args, **kwargs)
    return decorated_function

def enviar_email(destinatario, asunto, cuerpo):
    """Envía un email si la configuración está disponible."""
    if not app.config['MAIL_USERNAME'] or not app.config['MAIL_PASSWORD']:
        print("[EMAIL] Configuración incompleta: no se envía el email")
        return False, "Configuración incompleta"

    try:
        msg = Message(asunto, recipients=[destinatario])
        msg.body = cuerpo
        msg.html = f"<pre>{cuerpo}</pre>"
        mail.send(msg)
        return True, None
    except Exception as e:
        print(f"[EMAIL] Error enviando email: {e}")
        return False, str(e)


def log_action(usuario_id, accion, detalles=None):
    """Guarda un registro de auditoría en la base de datos."""
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS logs_auditoria (
                id INT AUTO_INCREMENT PRIMARY KEY,
                usuario_id INT,
                accion VARCHAR(100),
                detalles TEXT,
                fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id) ON DELETE SET NULL,
                INDEX idx_usuario_id (usuario_id),
                INDEX idx_fecha (fecha)
            )
        """)
        cursor.execute(
            "INSERT INTO logs_auditoria(usuario_id, accion, detalles) VALUES(%s, %s, %s)",
            (usuario_id, accion, detalles)
        )
        conexion.commit()
        conexion.close()
    except Exception as e:
        print(f"[AUDITORÍA] No se pudo guardar el registro: {e}")

metricas = defaultdict(list)
app = Flask(__name__)
app.secret_key = "tu-clave-secreta-super-segura-2024"  # CAMBIAR EN PRODUCCIÓN

# Configurar Flask-Mail
app.config['MAIL_SERVER'] = MAIL_SERVER
app.config['MAIL_PORT'] = MAIL_PORT
app.config['MAIL_USE_TLS'] = MAIL_USE_TLS
app.config['MAIL_USE_SSL'] = MAIL_USE_SSL
app.config['MAIL_USERNAME'] = MAIL_USERNAME
app.config['MAIL_PASSWORD'] = MAIL_PASSWORD
app.config['MAIL_DEFAULT_SENDER'] = MAIL_DEFAULT_SENDER

mail = Mail(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Context processor para disponibilizar current_user en todos los templates
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# Clase Usuario para Flask-Login
class Usuario(UserMixin):
    def __init__(self, id, username, correo, nombre, rol):
        self.id = id
        self.username = username
        self.correo = correo
        self.nombre = nombre
        self.rol = rol

@login_manager.user_loader
def load_user(user_id):
    """Carga el usuario desde la BD"""
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id, username, correo, nombre, rol FROM usuarios WHERE id = %s", (user_id,))
        resultado = cursor.fetchone()
        conexion.close()
        
        if resultado:
            return Usuario(resultado['id'], resultado['username'], resultado['correo'], resultado['nombre'], resultado['rol'])
    except Exception as e:
        print(f"[ERROR] Error al cargar usuario: {e}")
    
    return None

# ==================== RUTAS DE AUTENTICACIÓN ====================

@app.route('/admin/crear-usuario', methods=['GET', 'POST'])
@login_required
@admin_required
def crear_usuario():
    """Crear nuevo usuario (solo admin)"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            correo = request.form.get('correo', '').strip()
            nombre = request.form.get('nombre', '').strip()
            contraseña = request.form.get('contraseña', '')
            contraseña_confirm = request.form.get('contraseña_confirm', '')
            rol = request.form.get('rol', 'user')

            # Validaciones
            if not all([username, correo, nombre, contraseña]):
                return redirect(url_for('admin') + '?error=Todos los campos son requeridos')

            if len(username) < 3:
                return redirect(url_for('admin') + '?error=El usuario debe tener al menos 3 caracteres')

            if len(contraseña) < 6:
                return redirect(url_for('admin') + '?error=La contraseña debe tener al menos 6 caracteres')

            if contraseña != contraseña_confirm:
                return redirect(url_for('admin') + '?error=Las contraseñas no coinciden')

            if rol not in ['admin', 'user']:
                return redirect(url_for('admin') + '?error=Rol inválido')

            # Verificar si el usuario ya existe
            conexion = conectar()
            cursor = conexion.cursor()
            cursor.execute("SELECT id FROM usuarios WHERE username = %s OR correo = %s", (username, correo))
            
            if cursor.fetchone():
                conexion.close()
                return redirect(url_for('admin') + '?error=El usuario o correo ya están registrados')

            # Crear nuevo usuario
            contraseña_hash = generate_password_hash(contraseña)
            sql = """
            INSERT INTO usuarios(username, correo, nombre, contraseña, rol)
            VALUES(%s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (username, correo, nombre, contraseña_hash, rol))
            conexion.commit()
            nuevo_usuario_id = cursor.lastrowid
            conexion.close()

            log_action(current_user.id, 'Crear usuario', f'ID={nuevo_usuario_id}, username={username}, rol={rol}')
            print(f"[ADMIN] {current_user.username} creó usuario: {username} con rol {rol}")
            return redirect(url_for('admin') + '?success=Usuario creado exitosamente')
        
        except Exception as e:
            print(f"[ERROR] Error creando usuario: {e}\n{traceback.format_exc()}")
            return redirect(url_for('admin') + '?error=Error al crear el usuario')

    # Para GET, redirigir al admin con un indicador para mostrar el formulario
    return redirect(url_for('admin') + '?show_create_form=1')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login de usuarios"""
    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            contraseña = request.form.get('contraseña', '')

            if not all([username, contraseña]):
                return render_template('login.html', error='Usuario y contraseña requeridos'), 400

            # Buscar usuario en BD
            conexion = conectar()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("""
                SELECT id, username, correo, nombre, rol, contraseña, activo 
                FROM usuarios WHERE username = %s
            """, (username,))
            
            usuario = cursor.fetchone()
            conexion.close()

            # Validar credenciales
            if not usuario:
                print(f"[LOGIN] Intento fallido: usuario {username} no existe")
                return render_template('login.html', error='Usuario o contraseña incorrectos'), 401

            if not usuario['activo']:
                print(f"[LOGIN] Intento fallido: usuario {username} desactivado")
                return render_template('login.html', error='Usuario desactivado'), 401

            if not check_password_hash(usuario['contraseña'], contraseña):
                print(f"[LOGIN] Intento fallido: contraseña incorrecta para {username}")
                return render_template('login.html', error='Usuario o contraseña incorrectos'), 401

            # Crear objeto usuario y login
            user = Usuario(usuario['id'], usuario['username'], usuario['correo'], usuario['nombre'], usuario['rol'])
            login_user(user)

            log_action(usuario['id'], 'Login', f'Usuario {username} inició sesión')

            # Actualizar último acceso
            conexion = conectar()
            cursor = conexion.cursor()
            cursor.execute("UPDATE usuarios SET ultimo_acceso = NOW() WHERE id = %s", (usuario['id'],))
            conexion.commit()
            conexion.close()

            print(f"[LOGIN] ✓ Login exitoso: {username}")
            return redirect(url_for('dashboard'))

        except Exception as e:
            print(f"[ERROR] Error en login: {e}\n{traceback.format_exc()}")
            return render_template('login.html', error='Error al procesar login'), 500

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout del usuario"""
    username = current_user.username
    user_id = current_user.id
    logout_user()
    log_action(user_id, 'Logout', f'Usuario {username} cerró sesión')
    print(f"[LOGOUT] ✓ {username} ha cerrado sesión")
    return redirect(url_for('login'))


# ==================== RUTAS DEL DASHBOARD ====================

@app.route('/')
def index():
    """Redirige al dashboard si está logueado, sino al login"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal del usuario"""
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)

        # Obtener dispositivos del usuario logueado
        cursor.execute("""
        SELECT d.id, d.nombre, d.ip, d.tipo, d.ubicacion, d.estado,
        
        (SELECT cpu FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as cpu,

        (SELECT ram FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as ram,

        (SELECT disco FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as disco,

        (SELECT temperatura FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as temperatura,

        (SELECT procesos_activos FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as procesos_activos,

        (SELECT estado FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as metrica_estado,

        (SELECT fecha FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as ultima_actualizacion

        FROM dispositivos d
        WHERE d.usuario_id = %s
        ORDER BY d.fecha_registro DESC
        """, (current_user.id,))

        dispositivos = cursor.fetchall()
        
        # Determinar si cada dispositivo está online
        ahora = datetime.now()
        for dispositivo in dispositivos:
            if dispositivo['ultima_actualizacion']:
                # Si la última actualización fue hace menos de 5 minutos, está online
                tiempo_transcurrido = ahora - dispositivo['ultima_actualizacion']
                dispositivo['online'] = tiempo_transcurrido < timedelta(minutes=5)
            else:
                # Si no tiene métricas, está offline
                dispositivo['online'] = False
        
        verificar_alertas_offline(conexion, current_user.id)
        alertas_abiertas = contar_alertas_abiertas(conexion, current_user.id)

        ultima_actualizacion = None
        for dispositivo in dispositivos:
            if dispositivo['ultima_actualizacion']:
                if ultima_actualizacion is None or dispositivo['ultima_actualizacion'] > ultima_actualizacion:
                    ultima_actualizacion = dispositivo['ultima_actualizacion']

        if ultima_actualizacion:
            ultima_actualizacion = ultima_actualizacion.strftime('%d/%m/%Y %H:%M:%S')
        else:
            ultima_actualizacion = 'Sin actualizaciones'

        conexion.close()

        return render_template('dashboard.html', dispositivos=dispositivos, alertas_abiertas=alertas_abiertas, ultima_actualizacion=ultima_actualizacion)
    
    except Exception as e:
        print(f"[ERROR] Error en dashboard: {e}\n{traceback.format_exc()}")
        return render_template('error.html', mensaje="Error al cargar el dashboard"), 500


# ==================== RUTAS DE DISPOSITIVOS ====================

@app.route('/dispositivos')
@login_required
def dispositivos():
    """Lista de dispositivos del usuario"""
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
        SELECT d.id, d.nombre, d.ip, d.tipo, d.ubicacion, d.estado, d.fecha_registro,
        (SELECT fecha FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as ultima_actualizacion
        FROM dispositivos d
        WHERE d.usuario_id = %s
        ORDER BY d.fecha_registro DESC
        """, (current_user.id,))

        lista_dispositivos = cursor.fetchall()
        
        # Determinar si cada dispositivo está online
        ahora = datetime.now()
        for dispositivo in lista_dispositivos:
            if dispositivo['ultima_actualizacion']:
                tiempo_transcurrido = ahora - dispositivo['ultima_actualizacion']
                dispositivo['online'] = tiempo_transcurrido < timedelta(minutes=5)
            else:
                dispositivo['online'] = False
        
        conexion.close()

        return render_template('dispositivos.html', dispositivos=lista_dispositivos)
    
    except Exception as e:
        print(f"[ERROR] Error listando dispositivos: {e}")
        return render_template('error.html', mensaje="Error al cargar dispositivos"), 500


@app.route('/registrar', methods=['GET', 'POST'])
@login_required
def registrar():
    """Registrar nuevo dispositivo"""
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre', '').strip()
            ip = request.form.get('ip', '').strip()
            tipo = request.form.get('tipo', '').strip()
            ubicacion = request.form.get('ubicacion', '').strip()

            if not all([nombre, ip, tipo, ubicacion]):
                return render_template('registrar.html', error='Todos los campos son requeridos'), 400

            # Verificar que la IP sea única para este usuario
            conexion = conectar()
            cursor = conexion.cursor()

            cursor.execute("""
                SELECT id FROM dispositivos 
                WHERE usuario_id = %s AND ip = %s
            """, (current_user.id, ip))
            
            if cursor.fetchone():
                conexion.close()
                return render_template('registrar.html', error='Ya tienes un dispositivo con esa IP'), 400

            # Insertar dispositivo
            sql = """
            INSERT INTO dispositivos(usuario_id, nombre, ip, tipo, ubicacion, estado)
            VALUES(%s, %s, %s, %s, %s, 'activo')
            """

            cursor.execute(sql, (current_user.id, nombre, ip, tipo, ubicacion))
            conexion.commit()
            dispositivo_id = cursor.lastrowid
            conexion.close()

            log_action(current_user.id, 'Registrar dispositivo', f'ID={dispositivo_id}, nombre={nombre}, ip={ip}, tipo={tipo}, ubicacion={ubicacion}')
            print(f"[DISPOSITIVO] ✓ {current_user.username} registró: {nombre} ({ip})")
            return redirect(url_for('dispositivos'))
        
        except Exception as e:
            print(f"[ERROR] Error registrando dispositivo: {e}")
            return render_template('registrar.html', error='Error al registrar dispositivo'), 500

    return render_template('registrar.html')


@app.route('/editar-dispositivo/<int:device_id>', methods=['GET', 'POST'])
@login_required
def editar_dispositivo(device_id):
    """Editar un dispositivo existente"""
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, nombre, ip, tipo, ubicacion
            FROM dispositivos
            WHERE id = %s AND usuario_id = %s
        """, (device_id, current_user.id))

        dispositivo = cursor.fetchone()
        if not dispositivo:
            conexion.close()
            return render_template('error.html', mensaje='Dispositivo no encontrado o sin permiso'), 404

        if request.method == 'POST':
            nombre = request.form.get('nombre', '').strip()
            ip = request.form.get('ip', '').strip()
            tipo = request.form.get('tipo', '').strip()
            ubicacion = request.form.get('ubicacion', '').strip()

            if not all([nombre, ip, tipo, ubicacion]):
                conexion.close()
                dispositivo = {
                    'id': device_id,
                    'nombre': nombre,
                    'ip': ip,
                    'tipo': tipo,
                    'ubicacion': ubicacion
                }
                return render_template('registrar.html', error='Todos los campos son requeridos', device=dispositivo,
                                       action_url=url_for('editar_dispositivo', device_id=device_id),
                                       page_title='Editar Dispositivo', submit_text='Guardar Cambios') , 400

            cursor.execute("""
                SELECT id FROM dispositivos
                WHERE usuario_id = %s AND ip = %s AND id != %s
            """, (current_user.id, ip, device_id))
            if cursor.fetchone():
                conexion.close()
                dispositivo = {
                    'id': device_id,
                    'nombre': nombre,
                    'ip': ip,
                    'tipo': tipo,
                    'ubicacion': ubicacion
                }
                return render_template('registrar.html', error='Ya tienes un dispositivo con esa IP', device=dispositivo,
                                       action_url=url_for('editar_dispositivo', device_id=device_id),
                                       page_title='Editar Dispositivo', submit_text='Guardar Cambios') , 400

            cursor.execute("""
                UPDATE dispositivos
                SET nombre = %s, ip = %s, tipo = %s, ubicacion = %s
                WHERE id = %s AND usuario_id = %s
            """, (nombre, ip, tipo, ubicacion, device_id, current_user.id))
            conexion.commit()
            conexion.close()

            log_action(current_user.id, 'Editar dispositivo', f'ID={device_id}, nombre={nombre}, ip={ip}, tipo={tipo}, ubicacion={ubicacion}')
            print(f"[DISPOSITIVO] ✓ {current_user.username} editó dispositivo ID: {device_id}")
            return redirect(url_for('dispositivos'))

        conexion.close()
        return render_template('registrar.html', device=dispositivo,
                               action_url=url_for('editar_dispositivo', device_id=device_id),
                               page_title='Editar Dispositivo', submit_text='Guardar Cambios')

    except Exception as e:
        print(f"[ERROR] Error editando dispositivo: {e}")
        return render_template('error.html', mensaje='Error al editar dispositivo'), 500


@app.route('/eliminar-dispositivo/<int:device_id>', methods=['POST'])
@login_required
def eliminar_dispositivo(device_id):
    """Eliminar un dispositivo"""
    try:
        conexion = conectar()
        cursor = conexion.cursor()

        # Verificar que el dispositivo pertenezca al usuario
        cursor.execute("""
            SELECT id FROM dispositivos 
            WHERE id = %s AND usuario_id = %s
        """, (device_id, current_user.id))

        if not cursor.fetchone():
            conexion.close()
            return jsonify({"error": "No tienes permiso"}), 403

        # Eliminar dispositivo
        cursor.execute("DELETE FROM dispositivos WHERE id = %s", (device_id,))
        conexion.commit()
        conexion.close()

        log_action(current_user.id, 'Eliminar dispositivo', f'ID={device_id}')
        print(f"[DISPOSITIVO] ✓ {current_user.username} eliminó dispositivo ID: {device_id}")
        return jsonify({"status": "ok"})
    
    except Exception as e:
        print(f"[ERROR] Error eliminando dispositivo: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== RUTAS PARA RECIBIR MÉTRICAS ====================

@app.route('/metricas', methods=['POST'])
def recibir_metricas():
    """Recibe métricas del agent.py"""
    try:
        data = request.json
        ip = data.get("ip")
        cpu = data.get("cpu")
        ram = data.get("ram")
        disco = data.get("disco")
        net_usage = data.get("net_usage", {})
        temperatura = data.get("temperatura")
        procesos_activos = data.get("procesos_activos")
        uptime = data.get("uptime")

        print(f"\n{'='*60}")
        print(f"[RECIBIDO] Datos de {ip}: CPU={cpu:.1f}%, RAM={ram:.1f}%, DISCO={disco:.1f}%")
        if temperatura:
            print(f"  Temperatura: {temperatura:.1f}°C")
        print(f"  Procesos activos: {procesos_activos}")
        print(f"  Uptime: {uptime:.0f} segundos")

        # Guardar en memoria también
        metricas[ip].append({
            "cpu": cpu,
            "ram": ram,
            "disco": disco,
            "net_usage": net_usage,
            "temperatura": temperatura,
            "procesos_activos": procesos_activos,
            "uptime": uptime
        })

        # limitar a últimos 30 datos en memoria
        if len(metricas[ip]) > 30:
            metricas[ip].pop(0)

        # Guardar en la base de datos
        try:
            conexion = conectar()
            cursor = conexion.cursor()

            # Obtener el ID del dispositivo por IP
            print(f"[BD] Buscando dispositivo con IP: {ip}")
            cursor.execute("SELECT id, usuario_id FROM dispositivos WHERE ip = %s", (ip,))
            resultado = cursor.fetchone()

            if resultado:
                dispositivo_id, usuario_id = resultado
                print(f"[BD] ✓ Dispositivo encontrado (ID: {dispositivo_id})")
                
                # Determinar estado (basado en umbrales)
                estado = "OK"
                if cpu > 80 or ram > 80 or disco > 90:
                    estado = "ALERTA"
                if cpu > 95 or ram > 95 or disco > 95:
                    estado = "CRITICO"

                print(f"[BD] Estado calculado: {estado}")

                # Insertar métrica en la BD
                sql = """
                INSERT INTO metricas(dispositivo_id, cpu, ram, disco, net_bytes_sent, net_bytes_recv, 
                                   temperatura, procesos_activos, uptime, estado, fecha)
                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                """
                cursor.execute(sql, (dispositivo_id, cpu, ram, disco, 
                                   net_usage.get('bytes_sent', 0), net_usage.get('bytes_recv', 0),
                                   temperatura, procesos_activos, uptime, estado))
                conexion.commit()

                if estado in ["ALERTA", "CRITICO"]:
                    mensaje_alerta = f"{estado}: {ip} - CPU {cpu:.1f}%, RAM {ram:.1f}%, DISCO {disco:.1f}%"
                    if temperatura:
                        mensaje_alerta += f", Temp {temperatura:.1f}°C"
                    crear_alerta(conexion, dispositivo_id, usuario_id, estado, mensaje_alerta)
                    enviar_telegram(mensaje_alerta)
                    print(f"[TELEGRAM] Mensaje enviado: {mensaje_alerta}")
                    
                    # Enviar email al usuario
                    cursor.execute("SELECT correo, nombre FROM usuarios WHERE id = %s", (usuario_id,))
                    usuario = cursor.fetchone()
                    if usuario:
                        asunto = f"Alerta {estado} - Sistema de Monitoreo"
                        cuerpo = f"""Hola {usuario['nombre']},

Se ha detectado una alerta {estado} en tu dispositivo:

Dispositivo: {ip}
Mensaje: {mensaje_alerta}
Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Por favor revisa el sistema de monitoreo para más detalles.

Saludos,
Sistema de Monitoreo
"""
                        enviar_email(usuario['correo'], asunto, cuerpo)
                        print(f"[EMAIL] Alerta enviada a {usuario['correo']}")
                
                print(f"[BD] ✓ Métrica insertada correctamente en la BD")
            else:
                print(f"[BD] ✗ ERROR: No se encontró dispositivo con IP {ip}")
                print(f"[BD] Un usuario debe registrar este dispositivo en /registrar")
            
            conexion.close()
        except Exception as e:
            print(f"[BD] ✗ Error guardando en BD: {e}")

        print(f"{'='*60}\n")
        return {"status": "ok"}
    
    except Exception as e:
        print(f"[ERROR] Error recibiendo métricas: {e}")
        return {"status": "error", "mensaje": str(e)}, 400


@app.route('/datos/<ip>')
@login_required
def obtener_datos(ip):
    """Obtiene datos en tiempo real de un dispositivo"""
    try:
        # Verificar que el dispositivo pertenezca al usuario
        conexion = conectar()
        cursor = conexion.cursor()
        
        cursor.execute("""
            SELECT id FROM dispositivos 
            WHERE ip = %s AND usuario_id = %s
        """, (ip, current_user.id))
        
        if not cursor.fetchone():
            conexion.close()
            return jsonify({"error": "No tienes permiso"}), 403
        
        conexion.close()
        return jsonify(metricas[ip])
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/estado')
@login_required
def estado():
    """Obtiene el estado de todos los dispositivos del usuario"""
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)

        cursor.execute("""
        SELECT d.id, d.nombre, d.ip,

        (SELECT cpu FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as cpu,

        (SELECT ram FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as ram,

        (SELECT disco FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as disco,

        (SELECT temperatura FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as temperatura,

        (SELECT procesos_activos FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as procesos_activos,

        (SELECT estado FROM metricas 
         WHERE dispositivo_id = d.id 
         ORDER BY fecha DESC LIMIT 1) as estado

        FROM dispositivos d
        WHERE d.usuario_id = %s
        """, (current_user.id,))

        data = cursor.fetchall()
        alertas_abiertas = contar_alertas_abiertas(conexion, current_user.id)
        conexion.close()

        return jsonify({"dispositivos": data, "alertas_abiertas": alertas_abiertas})
    
    except Exception as e:
        print(f"[ERROR] Error en estado: {e}")
        return jsonify({"error": "Error al obtener estado"}), 500


@app.route('/stream')
@login_required
def stream():
    """Server-Sent Events para actualizaciones en tiempo real"""
    def generate():
        while True:
            try:
                # Obtener datos actualizados
                conexion = conectar()
                cursor = conexion.cursor(dictionary=True)
                
                cursor.execute("""
                SELECT d.nombre, d.ip,
                (SELECT cpu FROM metricas WHERE dispositivo_id = d.id ORDER BY fecha DESC LIMIT 1) as cpu,
                (SELECT ram FROM metricas WHERE dispositivo_id = d.id ORDER BY fecha DESC LIMIT 1) as ram,
                (SELECT disco FROM metricas WHERE dispositivo_id = d.id ORDER BY fecha DESC LIMIT 1) as disco,
                (SELECT temperatura FROM metricas WHERE dispositivo_id = d.id ORDER BY fecha DESC LIMIT 1) as temperatura,
                (SELECT procesos_activos FROM metricas WHERE dispositivo_id = d.id ORDER BY fecha DESC LIMIT 1) as procesos_activos
                FROM dispositivos d WHERE d.usuario_id = %s
                """, (current_user.id,))
                
                dispositivos = cursor.fetchall()
                alertas_abiertas = contar_alertas_abiertas(conexion, current_user.id)
                conexion.close()
                
                data = {
                    'dispositivos': dispositivos,
                    'alertas_abiertas': alertas_abiertas,
                    'timestamp': datetime.now().isoformat()
                }
                
                yield f"data: {json.dumps(data)}\n\n"
                
            except Exception as e:
                print(f"[SSE] Error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
            time.sleep(10)  # Actualizar cada 10 segundos
    
    return Response(generate(), mimetype='text/event-stream')


@app.route('/alertas')
@login_required
def alertas():
    """Lista alertas del usuario"""
    try:
        conexion = conectar()
        verificar_alertas_offline(conexion, current_user.id)
        alertas = obtener_alertas_usuario(conexion, current_user.id)
        conexion.close()

        return render_template('alertas.html', alertas=alertas)
    except Exception as e:
        print(f"[ERROR] Error en alertas: {e}\n{traceback.format_exc()}")
        return render_template('error.html', mensaje="Error al cargar las alertas"), 500


@app.route('/alertas/resolver/<int:alerta_id>', methods=['POST'])
@login_required
def resolver_alerta_route(alerta_id):
    """Marca una alerta como resuelta"""
    try:
        conexion = conectar()
        éxito = resolver_alerta(conexion, alerta_id, current_user.id)
        conexion.close()

        if éxito:
            return redirect(url_for('alertas'))
        return render_template('error.html', mensaje="No se pudo resolver la alerta"), 403
    except Exception as e:
        print(f"[ERROR] Error resolviendo alerta: {e}\n{traceback.format_exc()}")
        return render_template('error.html', mensaje="Error al resolver la alerta"), 500


@app.route('/reportes')
@login_required
def reportes():
    """Muestra el módulo de reportes"""
    try:
        desde = request.args.get('desde')
        hasta = request.args.get('hasta')
        fecha_inicio = None
        fecha_fin = None

        if desde:
            fecha_inicio = datetime.strptime(desde, '%Y-%m-%d')
        if hasta:
            fecha_fin = datetime.strptime(hasta, '%Y-%m-%d') + timedelta(days=1)

        conexion = conectar()
        resumen = obtener_resumen_reportes(conexion, current_user.id, fecha_inicio, fecha_fin)
        metricas_recientes = obtener_metricas_recientes(conexion, current_user.id, fecha_inicio, fecha_fin)
        alertas_lista = obtener_alertas_reporte(conexion, current_user.id, fecha_inicio, fecha_fin)

        if request.args.get('export') == 'csv':
            csv_data = exportar_reportes_csv(metricas_recientes, alertas_lista)
            conexion.close()
            return Response(csv_data, mimetype='text/csv', headers={
                'Content-Disposition': 'attachment; filename=reportes.csv'
            })

        conexion.close()
        return render_template('reportes.html', resumen=resumen, metricas=metricas_recientes, alertas=alertas_lista, desde=desde, hasta=hasta)
    except Exception as e:
        print(f"[ERROR] Error en reportes: {e}\n{traceback.format_exc()}")
        return render_template('error.html', mensaje="Error al cargar el módulo de reportes"), 500


@app.route('/admin')
@login_required
@admin_required
def admin():
    """Panel de administración"""
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        
        # Obtener todos los usuarios
        cursor.execute("SELECT id, username, correo, nombre, rol, activo, fecha_registro, ultimo_acceso FROM usuarios ORDER BY fecha_registro DESC")
        usuarios = cursor.fetchall()
        
        # Estadísticas generales
        cursor.execute("SELECT COUNT(*) as total_usuarios FROM usuarios")
        total_usuarios = cursor.fetchone()['total_usuarios']
        
        cursor.execute("SELECT COUNT(*) as total_dispositivos FROM dispositivos")
        total_dispositivos = cursor.fetchone()['total_dispositivos']
        
        cursor.execute("SELECT COUNT(*) as total_alertas FROM alertas WHERE resuelta = FALSE")
        alertas_abiertas = cursor.fetchone()['total_alertas']
        
        conexion.close()
        
        show_create_form = request.args.get('show_create_form', '0') == '1'
        error = request.args.get('error')
        success = request.args.get('success')
        
        return render_template('admin.html', 
                             usuarios=usuarios, 
                             total_usuarios=total_usuarios,
                             total_dispositivos=total_dispositivos,
                             alertas_abiertas=alertas_abiertas,
                             show_create_form=show_create_form,
                             error=error,
                             success=success)
    except Exception as e:
        print(f"[ERROR] Error en admin: {e}\n{traceback.format_exc()}")
        return render_template('error.html', mensaje="Error al cargar el panel de administración"), 500


@app.route('/admin/historial')
@login_required
@admin_required
def historial():
    """Muestra el historial de cambios del sistema."""
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT l.id, l.usuario_id, u.username, l.accion, l.detalles, l.fecha
            FROM logs_auditoria l
            LEFT JOIN usuarios u ON l.usuario_id = u.id
            ORDER BY l.fecha DESC
            LIMIT 500
        """)
        logs = cursor.fetchall()
        conexion.close()
        return render_template('historial.html', logs=logs)
    except Exception as e:
        print(f"[ERROR] Error cargando historial: {e}\n{traceback.format_exc()}")
        return render_template('error.html', mensaje='Error al cargar el historial de auditoría'), 500


@app.route('/admin/cambiar-rol/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def cambiar_rol(user_id):
    """Cambiar rol de un usuario"""
    try:
        nuevo_rol = request.form.get('rol')
        if nuevo_rol not in ['admin', 'user']:
            return jsonify({"error": "Rol inválido"}), 400
        
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("UPDATE usuarios SET rol = %s WHERE id = %s", (nuevo_rol, user_id))
        conexion.commit()
        conexion.close()
        
        log_action(current_user.id, 'Cambiar rol de usuario', f'ID={user_id}, nuevo_rol={nuevo_rol}')
        print(f"[ADMIN] {current_user.username} cambió rol de usuario {user_id} a {nuevo_rol}")
        return jsonify({"status": "ok"})
    
    except Exception as e:
        print(f"[ERROR] Error cambiando rol: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/toggle-usuario/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def toggle_usuario(user_id):
    """Activar/desactivar usuario"""
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        
        # Obtener estado actual
        cursor.execute("SELECT activo FROM usuarios WHERE id = %s", (user_id,))
        resultado = cursor.fetchone()
        if not resultado:
            conexion.close()
            return jsonify({"error": "Usuario no encontrado"}), 404
        
        nuevo_estado = not resultado[0]
        cursor.execute("UPDATE usuarios SET activo = %s WHERE id = %s", (nuevo_estado, user_id))
        conexion.commit()
        conexion.close()
        
        accion = "activado" if nuevo_estado else "desactivado"
        log_action(current_user.id, f'{accion.capitalize()} usuario', f'ID={user_id}')
        print(f"[ADMIN] {current_user.username} {accion} usuario {user_id}")
        return jsonify({"status": "ok", "activo": nuevo_estado})
    
    except Exception as e:
        print(f"[ERROR] Error toggling usuario: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/test-alerta', methods=['POST'])
@login_required
@admin_required
def test_alerta():
    """Enviar una alerta de prueba por email"""
    try:
        # Enviar email de prueba
        destinatario = current_user.correo
        asunto = "Prueba de Alerta - Sistema de Monitoreo"
        cuerpo = f"""
        ¡Hola {current_user.nombre or current_user.username}!

        Esta es una alerta de prueba del Sistema de Monitoreo de Dispositivos.

        Si recibes este email, significa que la configuración de correo está funcionando correctamente.

        Fecha de envío: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

        Atentamente,
        Sistema de Monitoreo
        """

        success, error_msg = enviar_email(destinatario, asunto, cuerpo)
        if success:
            print(f"[TEST] Alerta de prueba enviada a {destinatario}")
            return jsonify({"status": "ok", "mensaje": f"Alerta de prueba enviada a {destinatario}"})
        else:
            return jsonify({"error": f"Error al enviar el email: {error_msg}"}), 500
    
    except Exception as e:
        print(f"[ERROR] Error en test alerta: {e}")
        return jsonify({"error": str(e)}), 500


# ==================== MANEJADOR DE ERRORES ====================

@app.errorhandler(404)
def pagina_no_encontrada(error):
    """Maneja errores 404"""
    return render_template('error.html', mensaje="Página no encontrada"), 404


@app.errorhandler(500)
def error_servidor(error):
    """Maneja errores 500"""
    return render_template('error.html', mensaje="Error interno del servidor"), 500


if __name__ == "__main__":
    print("\n" + "="*60)
    print("Sistema de Monitoreo de Dispositivos v2.0")
    print("Con autenticación de usuarios")
    print("="*60)
    print("Iniciando en http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
