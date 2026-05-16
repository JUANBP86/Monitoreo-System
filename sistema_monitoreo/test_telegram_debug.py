#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de diagnóstico detallado para Telegram"""

import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

print("=" * 60)
print("DIAGNÓSTICO TELEGRAM - ANÁLISIS DETALLADO")
print("=" * 60)

print("\n1️⃣  DATOS CONFIGURADOS:")
print(f"   Token: {TELEGRAM_BOT_TOKEN}")
print(f"   Chat ID: {TELEGRAM_CHAT_ID}")

# Verificar que el token sea válido consultando info del bot
print("\n2️⃣  VERIFICANDO VALIDEZ DEL TOKEN...")
url_me = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
try:
    response = requests.get(url_me, timeout=10)
    print(f"   Status Code: {response.status_code}")
    print(f"   Respuesta: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Intentar enviar mensaje con detalles del error
print("\n3️⃣  ENVIANDO MENSAJE DE PRUEBA...")
url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": TELEGRAM_CHAT_ID,
    "text": "🤖 Prueba del bot",
    "parse_mode": "HTML"
}

print(f"   URL: {url}")
print(f"   Payload: {payload}")

try:
    response = requests.post(url, json=payload, timeout=10)
    print(f"   Status Code: {response.status_code}")
    print(f"   Respuesta JSON: {response.json()}")
except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n" + "=" * 60)
print("💡 POSIBLES SOLUCIONES:")
print("   • Verifica que el Token sea correcto (sin espacios)")
print("   • Verifica que el Chat ID sea tu ID personal")
print("   • Asegúrate de haber iniciado el bot en Telegram (@BotFather)")
print("   • El bot debe tener permisos para enviar mensajes")
print("=" * 60)
