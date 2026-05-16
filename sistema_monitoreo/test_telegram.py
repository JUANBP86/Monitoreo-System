#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script de prueba para verificar la configuración del bot de Telegram"""

from services.alerta_services import enviar_telegram
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

print("=" * 50)
print("PRUEBA DE CONFIGURACIÓN TELEGRAM")
print("=" * 50)

# Verificar configuración
print(f"\n✓ Bot Token: {TELEGRAM_BOT_TOKEN[:10]}...{TELEGRAM_BOT_TOKEN[-5:]}")
print(f"✓ Chat ID: {TELEGRAM_CHAT_ID}")

# Enviar mensaje de prueba
print("\n📨 Enviando mensaje de prueba...")
mensaje_prueba = """
🤖 <b>PRUEBA DEL BOT</b>

El bot de Telegram está funcionando correctamente ✅

<i>Mensaje enviado desde: sistema_monitoreo</i>
"""

resultado = enviar_telegram(mensaje_prueba)

if resultado:
    print("✅ ¡Mensaje enviado exitosamente!")
    print("\n💡 Consejo: Revisa tu chat de Telegram para confirmar.")
else:
    print("❌ Error al enviar el mensaje. Verifica:")
    print("   1. El Token es válido")
    print("   2. El Chat ID es correcto")
    print("   3. Tienes conexión a internet")

print("\n" + "=" * 50)
