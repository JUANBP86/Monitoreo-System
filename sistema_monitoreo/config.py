import os

# Database (can be overridden via environment variables)
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_USER = os.environ.get('DB_USER', 'root')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_NAME = os.environ.get('DB_NAME', 'monitoreo_sistemas')

# Telegram alert configuration (use env vars in Docker)
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8645532198:AAFxDCrewAsWgOr-Z5zQApJaVHXsilUgwrQ')
_chat = os.environ.get('TELEGRAM_CHAT_ID')
TELEGRAM_CHAT_ID = int(_chat) if _chat else 1334190620

# Email configuration (use env vars in Docker)
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ('1', 'true', 'yes')
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() in ('1', 'true', 'yes')
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'infomonitoreo01@gmail.com')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'Kiara25.')
MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', MAIL_USERNAME)