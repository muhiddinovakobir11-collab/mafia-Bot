import os
from pathlib import Path

# Asosiy bot sozlamalari
BOT_TOKEN = os.getenv("BOT_TOKEN", "8821320616:AAHTX9PHj4Ky8L5TJElc8oVU3oPmVHQowF8")
ADMIN_IDS = [8055412146]

# Baza va fayllar yo'li
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "mafia.db"

# Web Admin Panel sozlamalari
WEB_HOST = os.getenv("WEB_HOST", "0.0.0.0")
WEB_PORT = int(os.getenv("WEB_PORT", 8080))
WEB_ADMIN_SECRET = os.getenv("WEB_ADMIN_SECRET", "mafia_admin_secret_8055412146")

# O'yin sozlamalari
MIN_PLAYERS = 3       # Test va tezkor boshlash uchun (odatda 4-5)
LOBBY_TIMEOUT = 45    # O'yin yig'ilish taymeri (soniya)
NIGHT_TIMEOUT = 35    # Tun vaqti (soniya)
DAY_TALK_TIMEOUT = 40 # Kunduzgi muhokama vaqti (soniya)
VOTE_TIMEOUT = 35     # Ovoz berish vaqti (soniya)

# SofPay To'lov Tizimi sozlamalari
SOFPAY_SHOP_KEY = os.getenv("SOFPAY_SHOP_KEY", "sk_5b96eeebf9e5d73f32a50a423e06f22b")
SOFPAY_API_URL = os.getenv("SOFPAY_API_URL", "https://sofpay.uz/api/v1")

# Homiy / Rasmiy kanal sozlamalari (x2 bonus uchun)
SPONSOR_CHANNEL = os.getenv("SPONSOR_CHANNEL", "")


