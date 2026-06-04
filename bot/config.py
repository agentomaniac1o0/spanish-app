import os

BACKEND_URL = os.getenv("SPANISH_BACKEND_URL", "http://100.103.32.107:8100")
BACKEND_API_KEY = os.getenv("SPANISH_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-v4-flash")
