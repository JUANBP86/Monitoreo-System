import psutil
import requests
import socket
import time
import json
import platform
import subprocess
import os

# URL del servidor configurable por variable de entorno
SERVER = os.environ.get("MONITOR_SERVER_URL", "http://127.0.0.1:5000/metricas")
# Intervalo de envío configurable (segundos)
INTERVAL = int(os.environ.get("AGENT_INTERVAL", "60"))

def obtener_datos():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    disco = psutil.disk_usage('/').percent

    # Nueva métrica: Uso de red
    net_io = psutil.net_io_counters()
    net_usage = {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv
    }

    # Nueva métrica: Temperatura (si está disponible)
    temperatura = None
    try:
        if platform.system() == 'Linux':
            # Para Linux
            result = subprocess.run(['sensors'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                # Buscar temperatura en la salida
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'Core' in line and '°C' in line:
                        temp_str = line.split('°C')[0].split('+')[-1]
                        try:
                            temperatura = float(temp_str)
                            break
                        except ValueError:
                            continue
        elif platform.system() == 'Windows':
            # Para Windows, intentar WMI
            import wmi
            w = wmi.WMI()
            temp_info = w.query("SELECT * FROM Win32_TemperatureProbe")
            if temp_info:
                temperatura = temp_info[0].CurrentReading / 10.0  # Convertir de décimas de grado
    except Exception as e:
        print(f"No se pudo obtener temperatura: {e}")

    # Nueva métrica: Procesos activos
    procesos_activos = len(psutil.pids())

    # Nueva métrica: Uptime
    uptime = time.time() - psutil.boot_time()

    # Obtener la IP real del contenedor (la IP estática asignada por Docker)
    try:
        # Intentar obtener la IP de la interfaz de red principal
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = socket.gethostbyname(socket.gethostname())

    datos = {
        "ip": ip,
        "cpu": cpu,
        "ram": ram,
        "disco": disco,
        "net_usage": net_usage,
        "temperatura": temperatura,
        "procesos_activos": procesos_activos,
        "uptime": uptime
    }

    return datos


while True:

    datos = obtener_datos()

    try:

        response = requests.post(SERVER, json=datos, timeout=5)
        
        if response.status_code == 200:
            print(f"✓ Datos enviados exitosamente: {datos}")
        else:
            print(f"✗ Error HTTP {response.status_code}: {response.text}")

    except requests.exceptions.ConnectionError as e:

        print(f"✗ Error de conexión: {e}")
        print(f"  Intentando conectar a: {SERVER}")

    except requests.exceptions.Timeout:

        print(f"✗ Timeout: el servidor tardó demasiado en responder")

    except requests.exceptions.RequestException as e:

        print(f"✗ Error en la solicitud: {e}")

    except Exception as e:

        print(f"✗ Error inesperado: {e}")

    time.sleep(INTERVAL)