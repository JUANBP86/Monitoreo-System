#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script para obtener automáticamente el Chat ID"""

import requests
from config import TELEGRAM_BOT_TOKEN

print("=" * 60)
print("OBTENIENDO CHAT ID AUTOMÁTICAMENTE")
print("=" * 60)

print("\n⏳ Leyendo mensajes recibidos por el bot...")
print("(Asegúrate de haber escrito /start en el bot)")

url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

try:
    response = requests.get(url, timeout=10)
    data = response.json()
    
    if data['ok']:
        updates = data.get('result', [])
        
        if updates:
            print(f"\n✅ Se encontraron {len(updates)} actualizaciones\n")
            
            for update in updates:
                if 'message' in update:
                    chat_id = update['message']['chat']['id']
                    first_name = update['message']['chat'].get('first_name', 'Usuario')
                    text = update['message'].get('text', '')
                    
                    print(f"📱 Chat ID: {chat_id}")
                    print(f"   Nombre: {first_name}")
                    print(f"   Mensaje: {text}")
                    print()
            
            # Usar el primer chat encontrado
            chat_id = updates[0]['message']['chat']['id']
            print("=" * 60)
            print(f"🎯 CHAT ID DETECTADO: {chat_id}")
            print("=" * 60)
            print("\n📋 Actualiza tu config.py con:")
            print(f'TELEGRAM_CHAT_ID = "{chat_id}"')
            
        else:
            print("❌ No se encontraron mensajes.")
            print("   Asegúrate de:")
            print("   1. Abrir el bot 'Almjun32_bot' en Telegram")
            print("   2. Enviar /start")
            print("   3. Ejecutar este script nuevamente")
    else:
        print("❌ Error en la API de Telegram")
        print(response.json())
        
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
