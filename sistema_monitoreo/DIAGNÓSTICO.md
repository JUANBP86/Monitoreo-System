# GUÍA DE DIAGNÓSTICO: Datos no llegan a la Base de Datos

## Paso 1: Crear la estructura de la BD

Ejecuta el script SQL para asegurar que las tablas existan:

```bash
mysql -h localhost -u root monitoreo_sistemas < database_setup.sql
```

O en MySQL Workbench/Terminal de MySQL:
```sql
SOURCE database_setup.sql;
```

## Paso 2: Ejecutar el script de diagnóstico

Con el servidor Flask corriendo, abre otra terminal y ejecuta:

```bash
python test_debug.py
```

Este script mostrará:
- ✓ Si la tabla 'metricas' existe
- ✓ Dispositivos registrados en la BD
- ✓ Últimas métricas guardadas
- ✓ Intenta enviar datos de prueba

## Paso 3: Registrar un dispositivo

Si no hay dispositivos registrados, ve a:
```
http://127.0.0.1:5000/registrar
```

**IMPORTANTE**: 
- Nombre: cualquiera
- IP: debe ser igual a la que envía agent.py (revisa en la terminal de agent.py)
- En desarrollo local, usa: `127.0.0.1` o la IP de tu máquina

## Paso 4: Revisar logs en la terminal de Flask

Cuando ejecutes agent.py o test_debug.py, verás en la terminal de Flask:

```
============================================================
[RECIBIDO] Datos de 127.0.0.1: CPU=45.5%, RAM=62.3%, DISCO=55.8%
[BD] Buscando dispositivo con IP: 127.0.0.1
[BD] ✓ Dispositivo encontrado (ID: 1)
[BD] Estado calculado: OK
[BD] ✓ Métrica insertada correctamente en la BD
============================================================
```

## Cambios realizados:

### 1. **agent.py**
- ❌ Cambiado: `http://192.168.0.9:5000` (IP específica de red)
- ✅ Ahora: `http://127.0.0.1:5000` (localhost para desarrollo)
- ✅ Mejor manejo de errores con mensajes detallados

### 2. **app.py**
- ✅ Logging detallado en /metricas para ver cada paso
- ✅ Mensajes claros si el dispositivo no existe
- ✅ Muestra si se inserta correctamente en BD

### 3. **database_setup.sql** (NUEVO)
- ✅ Script para crear tablas si no existen
- ✅ Estructura correcta con relaciones y índices

### 4. **test_debug.py** (NUEVO)
- ✅ Script para diagnosticar dónde falla el flujo
- ✅ Muestra dispositivos, métricas y permite pruebas

## Flujo esperado de datos:

```
agent.py (recolecta datos)
    ↓
POST /metricas (Flask recibe)
    ↓
Busca dispositivo por IP en BD
    ↓
Inserta en tabla metricas
    ↓
dashboard.html (consulta y muestra)
```

## Verificación rápida:

```bash
# 1. Ver dispositivos registrados
mysql -u root monitoreo_sistemas -e "SELECT * FROM dispositivos;"

# 2. Ver métricas guardadas
mysql -u root monitoreo_sistemas -e "SELECT * FROM metricas LIMIT 5;"

# 3. Ver alertas
mysql -u root monitoreo_sistemas -e "SELECT * FROM alertas LIMIT 5;"
```

¿Ya ejecutaste los pasos? ¿Qué errores ves en los logs?
