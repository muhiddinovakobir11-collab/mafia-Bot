import os
from pathlib import Path

# Baza va fayllar yo'li
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mafia.db"

# .env faylini yuklash (maxfiy kalitlar uchun)
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    try:
        with open(_env_path, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
    except Exception:
        pass

# Asosiy bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN", "8821320616:AAHTX9PHj4Ky8L5TJElc8oVU3oPmVHQowF8")
BOT_USERNAME = os.getenv("BOT_USERNAME", "mafioznikiuzbot")
ADMIN_IDS = [8055412146]

# Web Admin Panel sozlamalari
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("PORT", os.getenv("WEB_PORT", 8000)))
WEB_ADMIN_SECRET = os.getenv("WEB_ADMIN_SECRET", "mafia_admin_secret_8055412146")

# O'yin sozlamalari
MIN_PLAYERS = 3       # Test va tezkor boshlash uchun (odatda 4-5)
LOBBY_TIMEOUT = 60    # O'yin yig'ilish taymeri (soniya, 1 daqiqa)
NIGHT_TIMEOUT = 40    # Tun vaqti (soniya)
DAY_TALK_TIMEOUT = 50 # Kunduzgi muhokama vaqti (soniya)
VOTE_TIMEOUT = 40     # Ovoz berish vaqti (soniya)

# SofPay To'lov Tizimi sozlamalari
SOFPAY_SHOP_KEY = os.getenv("SOFPAY_SHOP_KEY", "sk_5b96eeebf9e5d73f32a50a423e06f22b")
SOFPAY_API_URL = os.getenv("SOFPAY_API_URL", "https://sofpay.uz/api/v1")

# Homiy / Rasmiy kanal sozlamalari (x2 bonus uchun)
SPONSOR_CHANNEL = os.getenv("SPONSOR_CHANNEL", "")

# GitHub Cloud Baza Sinxronizatsiyasi
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "muhiddinovakobir11-collab/mafia-Bot")
GITHUB_DB_BACKUP_PATH = os.getenv("GITHUB_DB_BACKUP_PATH", "database/cloud_db_backup.db")
