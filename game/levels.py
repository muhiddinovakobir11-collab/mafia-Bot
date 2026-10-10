from typing import Dict, Any

LEVEL_REWARDS = {
    2: {"pul": 1000, "almaz": 0, "item": None, "msg": "💰 1,000 Pul"},
    3: {"pul": 1500, "almaz": 10, "item": None, "msg": "💎 10 Almaz va 💰 1,500 Pul"},
    4: {"pul": 2500, "almaz": 15, "item": None, "msg": "💎 15 Almaz va 💰 2,500 Pul"},
    5: {"pul": 3500, "almaz": 30, "item": "qalqon", "msg": "💎 30 Almaz, 💰 3,500 Pul va 🛡️ Qalqon"},
}

def get_reward_for_level(lvl: int) -> Dict[str, Any]:
    if lvl in LEVEL_REWARDS:
        return LEVEL_REWARDS[lvl]
    p = lvl * 750
    a = lvl * 3
    return {
        "pul": p,
        "almaz": a,
        "item": None,
        "msg": f"💎 {a} Almaz va 💰 {p:,} Pul"
    }

def format_level_up_message(new_level: int, reward_msg: str) -> str:
    return (
        f"🎉 <b>TABRIKLAYMIZ! YANGI DARAJAGA ERISHDINGIZ!</b> 🎉\n\n"
        f"🎖 Siz <b>{new_level}-darajaga</b> ko'tarildingiz!\n\n"
        f"🎁 <b>Sizning sovg'angiz:</b>\n"
        f"✨ {reward_msg}\n\n"
        f"<i>O'yinlarda faol qatnashing va yangi sovg'alarga ega bo'ling!</i>"
    )
