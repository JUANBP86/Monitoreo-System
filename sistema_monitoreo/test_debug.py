"""
Script de prueba para verificar el flujo de datos del sistema de monitoreo
"""
import requests
import json
import time
from database import conectar

def test_enviar_metricas():
    """Prueba el envío de métricas al servidor"""
    print("\n" + "="*60)
    print("TEST 1: Enviando datos de prueba al servidor")
    print("="*60)
    
    datos_prueba = {
        "ip": "127.0.0.1",
        "cpu": 45.5,
        "ram": 62.3,
        "disco": 55.8
    }
    
    try:
        response = requests.post(
            "http://127.0.0.1:5000/metricas",
            json=datos_prueba,
            timeout=5
        )
        print(f"[HTTP] Status: {response.status_code}")
        print(f"[HTTP] Respuesta: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"[ERROR] {e}")
        return False

def test_dispositivos_registrados():
    """Verifica cuáles dispositivos están registrados"""
    print("\n" + "="*60)
    print("TEST 2: Comprobando dispositivos registrados")
    print("="*60)
    
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, ip FROM dispositivos")
        dispositivos = cursor.fetchall()
        conexion.close()
        
        if dispositivos:
            print(f"[BD] Se encontraron {len(dispositivos)} dispositivo(s):")
            for d in dispositivos:
                print(f"  - ID: {d['id']}, Nombre: {d['nombre']}, IP: {d['ip']}")
            return True
        else:
            print("[BD] ✗ No hay dispositivos registrados!")
            print("[BD] Debes registrar uno primero en http://127.0.0.1:5000/registrar")
            return False
    except Exception as e:
        print(f"[ERROR BD] {e}")
        return False

def test_metricas_guardadas():
    """Verifica si hay métricas guardadas en la BD"""
    print("\n" + "="*60)
    print("TEST 3: Comprobando métricas guardadas en BD")
    print("="*60)
    
    try:
        conexion = conectar()
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT m.id, d.nombre, m.cpu, m.ram, m.disco, m.estado, m.fecha
            FROM metricas m
            JOIN dispositivos d ON m.dispositivo_id = d.id
            ORDER BY m.fecha DESC
            LIMIT 5
        """)
        metricas = cursor.fetchall()
        conexion.close()
        
        if metricas:
            print(f"[BD] Se encontraron {len(metricas)} métrica(s) reciente(s):")
            for m in metricas:
                print(f"  - {m['nombre']}: CPU={m['cpu']}%, RAM={m['ram']}%, DISCO={m['disco']}% [{m['estado']}] @ {m['fecha']}")
            return True
        else:
            print("[BD] ✗ No hay métricas guardadas en la BD")
            return False
    except Exception as e:
        print(f"[ERROR BD] {e}")
        return False

def test_tabla_existe():
    """Verifica si la tabla metricas existe"""
    print("\n" + "="*60)
    print("TEST 0: Verificando estructura de BD")
    print("="*60)
    
    try:
        conexion = conectar()
        cursor = conexion.cursor()
        cursor.execute("SHOW TABLES LIKE 'metricas'")
        tabla = cursor.fetchone()
        conexion.close()
        
        if tabla:
            print("[BD] ✓ Tabla 'metricas' existe")
            return True
        else:
            print("[BD] ✗ Tabla 'metricas' NO existe")
            print("[BD] Ejecuta el script database_setup.sql para crearla")
            return False
    except Exception as e:
        print(f"[ERROR BD] {e}")
        return False

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# DIAGNÓSTICO DEL SISTEMA DE MONITOREO")
    print("#"*60)
    
    # Ejecutar pruebas en orden
    tabla_existe = test_tabla_existe()
    dispositivos_ok = test_dispositivos_registrados()
    metricas_ok = test_metricas_guardadas()
    
    print("\n" + "="*60)
    print("TEST 4: Intentando enviar datos de prueba")
    print("="*60)
    if dispositivos_ok:
        test_enviar_metricas()
        print("\n[INFO] Espera 2 segundos y verifica si aparece en TEST 3...")
        time.sleep(2)
        test_metricas_guardadas()
    else:
        print("Primero registra un dispositivo con IP 127.0.0.1")
    
    print("\n" + "#"*60)
    print("# FIN DEL DIAGNÓSTICO")
    print("#"*60 + "\n")
