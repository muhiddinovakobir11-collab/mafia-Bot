import os
import asyncio
import logging
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import uvicorn
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, WEB_HOST, WEB_PORT
from database.db import db
from database.db_sync import db_sync
from bot.handlers import (
    start_router,
    game_router,
    night_router,
    shop_router,
    stars_router,
    admin_router,
    clans_router,
    duels_router,
    quests_router,
    card_router,
    extra_features_router
)
from web.app import app as web_app

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MafiaBot")
import socket

def get_free_port(preferred: int, host: str = "0.0.0.0") -> int:
    if os.getenv("PORT"):
        return preferred
    for p in [preferred, 8000, 8088, 8888, 5000]:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, p))
                return p
        except Exception:
            continue
    return preferred

async def run_web_server():
    active_port = get_free_port(WEB_PORT, WEB_HOST)
    config = uvicorn.Config(
        app=web_app,
        host=WEB_HOST,
        port=active_port,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    logger.info(f"🌐 Web Admin Panel ishga tushdi: http://localhost:{active_port}")
    await server.serve()

async def run_bot():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Register handlers
    dp.include_router(start_router)
    dp.include_router(game_router)
    dp.include_router(night_router)
    dp.include_router(shop_router)
    dp.include_router(stars_router)
    dp.include_router(admin_router)
    dp.include_router(clans_router)
    dp.include_router(duels_router)
    dp.include_router(quests_router)
    dp.include_router(card_router)
    dp.include_router(extra_features_router)

    # Initialize database with cloud persistence
    logger.info("📦 Ma'lumotlar bazasi Cloud zaxiradan tekshirilmoqda...")
    await db_sync.restore_from_cloud()

    logger.info("📦 Ma'lumotlar bazasi initsializatsiya qilinmoqda...")
    await db.init()
    logger.info("✅ Ma'lumotlar bazasi tayyor!")

    # Initial cloud sync
    await db_sync.backup_to_cloud()

    # Start background auto backup loop (every 5 minutes)
    asyncio.create_task(db_sync.run_auto_backup_loop(interval_seconds=300))

    # Delete existing webhook if any and start polling with auto-retry
    while True:
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("🤖 Mafia Telegram boti ishga tushmoqda...")
            await dp.start_polling(bot)
            break
        except Exception as e:
            logger.warning(f"⚠️ Telegram ulanish xatosi ({e}). 3 soniyadan so'ng qayta ulanadi...")
            await asyncio.sleep(3)

async def main():
    logger.info("🚀 Mafia Bot va Web Admin Server ishga tushirilmoqda...")
    await asyncio.gather(
        run_bot(),
        run_web_server()
    )

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        try:
            asyncio.run(db_sync.backup_to_cloud())
        except Exception:
            pass
        logger.info("🛑 Bot va Server to'xtatildi.")
