# Sistema de Monitoreo con Autenticación - Guía de Instalación v2.0

## 🚀 Pasos para ejecutar el sistema

### 1️⃣ Actualizar la Base de Datos

Ejecuta el script SQL para crear la tabla de usuarios:

```bash
mysql -h localhost -u root monitoreo_sistemas < database_setup.sql
```

O en MySQL Workbench/Consola:
```sql
SOURCE database_setup.sql;
```

Esto creará las tablas:
- `usuarios` - Tabla de usuarios con autenticación
- `dispositivos` - Dispositivos monitoreados (ahora con foreign key a usuarios)
- `metricas` - Métricas de CPU, RAM, DISCO
- `alertas` - Sistema de alertas
- `logs_auditoria` - Registro de acciones

### 2️⃣ Instalar dependencias

```bash
pip install -r requirements.txt
```

Las dependencias son:
- flask
- flask-login
- mysql-connector-python
- psutil
- requests
- werkzeug

### 3️⃣ Ejecutar el servidor Flask

```bash
python app.py
```

El servidor estará disponible en: **http://127.0.0.1:5000**

### 4️⃣ Crear tu cuenta

1. Abre el navegador en `http://127.0.0.1:5000`
2. Click en "Registrarse"
3. Completa los datos:
   - Nombre: Tu nombre
   - Usuario: Mínimo 3 caracteres
   - Correo: tu@email.com
   - Contraseña: Mínimo 6 caracteres
4. Haz click en "Crear Cuenta"

### 5️⃣ Ingresar a tu cuenta

1. Click en "Ingresar"
2. Usa el usuario y contraseña que acabas de crear
3. ¡Listo! Ya estás dentro del dashboard

### 6️⃣ Registrar dispositivos

1. En el dashboard, haz click en "+ Nuevo Dispositivo"
2. Completa los datos:
   - Nombre: Nombre descriptivo (ej: "Servidor Principal")
   - IP: La IP del dispositivo (ej: 127.0.0.1, 192.168.1.100)
   - Tipo: Selecciona de la lista
   - Ubicación: Ubicación física

### 7️⃣ Configurar agent.py en los dispositivos

En cada dispositivo que quieras monitorear, ejecuta `agent.py`:

```bash
python agent.py
```

Este script:
- Recolecta métricas cada 60 segundos
- Las envía a http://127.0.0.1:5000/metricas
- Mostrará logs de envío exitoso o errores

## 📊 Flujo de datos

```
Agent (dispositivo) → Recolecta datos
        ↓
    POST /metricas
        ↓
    Flask (servidor) → Valida IP
        ↓
    BD → Busca dispositivo registrado
        ↓
    Inserta métricas en tabla
        ↓
Dashboard → Consulta y muestra datos
```

## 🔐 Características de Seguridad

✅ **Contraseñas hasheadas** con werkzeug
✅ **Sesiones de usuario** con Flask-Login
✅ **Rutas protegidas** - Solo usuarios autenticados pueden ver sus dispositivos
✅ **Aislamiento de datos** - Cada usuario solo ve sus propios dispositivos
✅ **Registro de auditoría** - Se registran logins y cambios

## 🔑 Cambios Principales v2.0

| Aspecto | v1.0 | v2.0 |
|--------|------|------|
| Autenticación | ❌ No | ✅ Sí |
| Usuarios | ❌ No | ✅ Sí |
| Dispositivos compartidos | ✅ Sí | ❌ No (privados por usuario) |
| Tabla usuarios | ❌ No | ✅ Sí |
| Hash de contraseña | ❌ No | ✅ Werkzeug PBKDF2 |
| Sesiones | ❌ No | ✅ Sí |
| Logs de acceso | ❌ No | ✅ Sí |

## 🆘 Solución de Problemas

### Error: `'current_user' is undefined`
✅ **Solucionado** - Se agregó context processor

### Error: Tabla usuarios no existe
```bash
mysql -u root monitoreo_sistemas < database_setup.sql
```

### Error: Usuario o contraseña incorrectos
- Verifica que creaste la cuenta correctamente
- Revisa en MySQL: `SELECT * FROM usuarios;`

### Agent no envía datos
1. Verifica que Flask está corriendo: `python app.py`
2. Verifica que la IP en agent.py es correcta
3. Registra un dispositivo con esa misma IP
4. Revisa los logs en la terminal de Flask

### Dispositivo no aparece en el dashboard
1. ¿Están en el mismo usuario? (vs otra cuenta)
2. ¿Está registrado en BD? -> Va a `/registrar` y crea uno
3. ¿El agent.py está corriendo? -> Ejecuta `python agent.py`

## 📝 Archivos principales

```
sistema_monitoreo/
├── app.py                          # Servidor Flask con autenticación
├── agent.py                        # Cliente que envía métricas
├── database.py                     # Conexión a MySQL
├── config.py                       # Configuración de BD
├── requirements.txt                # Dependencias Python
├── database_setup.sql              # Script SQL para crear tablas
├── templates/
│   ├── base.html                   # Template base con navbar
│   ├── login.html                  # Formulario de login
│   ├── registro.html               # Formulario de registro
│   ├── dashboard.html              # Dashboard del usuario
│   ├── dispositivos.html           # Lista de dispositivos
│   ├── registrar.html              # Registro de nuevo dispositivo
│   └── error.html                  # Página de error
└── test_debug.py                   # Script de diagnóstico
```

## 🎯 Próximos pasos recomendados

1. ✅ Crear cuenta de usuario
2. ✅ Registrar un dispositivo
3. ✅ Ejecutar agent.py en una máquina
4. ⏳ Ver datos llegar al dashboard
5. ⏳ Implementar alertas dinámicas
6. ⏳ Crear reportes

---

**¿Necesitas ayuda?** Revisa los logs en la terminal de Flask para errores específicos.
