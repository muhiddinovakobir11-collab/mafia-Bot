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

async def run_web_server():
    config = uvicorn.Config(
        app=web_app,
        host=WEB_HOST,
        port=WEB_PORT,
        log_level="warning",
        access_log=False
    )
    server = uvicorn.Server(config)
    logger.info(f"🌐 Web Admin Panel ishga tushdi: http://localhost:{WEB_PORT}")
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

    # Initialize database
    logger.info("📦 Ma'lumotlar bazasi initsializatsiya qilinmoqda...")
    await db.init()
    logger.info("✅ Ma'lumotlar bazasi tayyor!")

    # Delete existing webhook if any and start polling
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("🤖 Mafia Telegram boti ishga tushmoqda...")
    await dp.start_polling(bot)

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
        logger.info("🛑 Bot va Server to'xtatildi.")
