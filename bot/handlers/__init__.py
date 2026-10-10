from bot.handlers.start import router as start_router
from bot.handlers.group_game import router as game_router
from bot.handlers.night_actions import router as night_router
from bot.handlers.shop import router as shop_router
from bot.handlers.stars_pay import router as stars_router
from bot.handlers.admin_bot import router as admin_router
from bot.handlers.clans import router as clans_router
from bot.handlers.duels import router as duels_router
from bot.handlers.quests_achievements import router as quests_router
from bot.handlers.card_pay import router as card_router
from bot.handlers.extra_features import router as extra_features_router

__all__ = [
    "start_router",
    "game_router",
    "night_router",
    "shop_router",
    "stars_router",
    "admin_router",
    "clans_router",
    "duels_router",
    "quests_router",
    "card_router",
    "extra_features_router"
]



