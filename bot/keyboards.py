from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Dict, Any

def get_main_keyboard(is_admin: bool = False) -> ReplyKeyboardMarkup:
    kb = [
        [KeyboardButton(text="🔵 👤 Profil & Balans"), KeyboardButton(text="🟣 🛍️ Do'kon & Narsalar")],
        [KeyboardButton(text="🟢 💳 Karta orqali xarid"), KeyboardButton(text="🟡 ⭐️ Stars to'ldirish")],
        [KeyboardButton(text="🏰 Mafia Klani"), KeyboardButton(text="🎰 Kazino & O'yinlar")],
        [KeyboardButton(text="🎯 Kunlik Missiyalar"), KeyboardButton(text="🎁 Kunlik bonus")],
        [KeyboardButton(text="🏆 Reyting & Top"), KeyboardButton(text="🤝 Do'stlarni taklif qilish")],
        [KeyboardButton(text="📖 O'yin qoidalari & Rollar"), KeyboardButton(text="➕ Botni guruhga qo'shish")]
    ]
    if is_admin:
        kb.append([KeyboardButton(text="🔴 ⚙️ Admin Panel")])

    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

def get_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟣 🎒 Inventarim", callback_data="my_inventory"),
            InlineKeyboardButton(text="🟣 🛍️ Do'konga o'tish", callback_data="open_shop")
        ],
        [
            InlineKeyboardButton(text="🟢 💳 Karta orqali xarid (So'm)", callback_data="buy_card_menu"),
            InlineKeyboardButton(text="🟡 ⭐️ Stars xarid", callback_data="buy_stars_menu")
        ]
    ])

def get_shop_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟡 💰 Pulga sotib olish", callback_data="shop_view_pul"),
            InlineKeyboardButton(text="🔵 💎 Almazga sotib olish", callback_data="shop_view_almaz")
        ],
        [
            InlineKeyboardButton(text="🟢 🔄 Almazni Pulga almashtirish", callback_data="shop_exchange"),
            InlineKeyboardButton(text="🟣 🎒 Mening inventarim", callback_data="my_inventory")
        ]
    ])

def get_star_packages_keyboard(packages: List[Dict[str, Any]], pkg_type: str = "almaz") -> InlineKeyboardMarkup:
    buttons = []
    for pkg in packages:
        badge = "🔵 💎" if pkg_type == "almaz" else "🟡 💰"
        text = f"{badge} {pkg['title']} — ⭐️ {pkg['stars_price']}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"buy_pkg_{pkg['id']}")])

    toggle_btn = (
        InlineKeyboardButton(text="🟡 💰 Pul paketlariga o'tish", callback_data="stars_type_pul")
        if pkg_type == "almaz" else
        InlineKeyboardButton(text="🔵 💎 Almaz paketlariga o'tish", callback_data="stars_type_almaz")
    )
    buttons.append([toggle_btn])
    buttons.append([InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_card_packages_keyboard(packages: List[Dict[str, Any]], pkg_type: str = "almaz") -> InlineKeyboardMarkup:
    buttons = []
    filtered = [p for p in packages if p["package_type"] == pkg_type]
    for pkg in filtered:
        badge = "🔵 💎" if pkg_type == "almaz" else ("🟡 💰" if pkg_type == "pul" else "🟣 👑")
        text = f"{badge} {pkg['title']} — {pkg['price_uzs']:,} so'm"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"buy_card_pkg_{pkg['id']}")])

    type_switch = []
    if pkg_type != "almaz":
        type_switch.append(InlineKeyboardButton(text="🔵 💎 Almazlar", callback_data="card_view_almaz"))
    if pkg_type != "pul":
        type_switch.append(InlineKeyboardButton(text="🟡 💰 Pullar", callback_data="card_view_pul"))
    if pkg_type != "vip":
        type_switch.append(InlineKeyboardButton(text="🟣 👑 VIP", callback_data="card_view_vip"))
    if type_switch:
        buttons.append(type_switch)

    buttons.append([InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_card_invoice_keyboard(tx_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔵 🔄 To'lovni tekshirish", callback_data=f"check_card_tx_{tx_id}")
        ],
        [
            InlineKeyboardButton(text="🔴 ❌ Bekor qilish", callback_data=f"cancel_card_tx_{tx_id}")
        ]
    ])

def get_admin_card_confirm_keyboard(tx_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 ✅ Tasdiqlash (Berilsin)", callback_data=f"adm_appr_tx_{tx_id}"),
            InlineKeyboardButton(text="🔴 ❌ Rad etish", callback_data=f"adm_rejc_tx_{tx_id}")
        ]
    ])

def get_lobby_keyboard(chat_id: int, bot_username: str = None) -> InlineKeyboardMarkup:
    from config import BOT_USERNAME
    b_name = bot_username or BOT_USERNAME
    join_url = f"https://t.me/{b_name}?start=join_{chat_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🤵 Qo'shilish", callback_data=f"join_{chat_id}"),
            InlineKeyboardButton(text="🚪 Chiqish", callback_data=f"leave_{chat_id}")
        ],
        [
            InlineKeyboardButton(text="🚀 O'yinni boshlash", callback_data=f"forcestart_{chat_id}"),
            InlineKeyboardButton(text="🤖 +Bot qo'shish", callback_data=f"addbot_{chat_id}")
        ],
        [
            InlineKeyboardButton(text="🔗 Shaxsiyda ochish", url=join_url)
        ]
    ])

def get_group_redirect_keyboard(group_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔵 Перейти в группу", url=group_url)
        ]
    ])

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔵 📊 Statistika", callback_data="adm_stats"),
            InlineKeyboardButton(text="🟣 👤 Foydalanuvchilarni boshqarish", callback_data="adm_users")
        ],
        [
            InlineKeyboardButton(text="🟢 💰 Balans berish / olish", callback_data="adm_balance"),
            InlineKeyboardButton(text="🔴 🚫 Ban / Unban", callback_data="adm_ban")
        ],
        [
            InlineKeyboardButton(text="🟡 ⭐️ Stars narxlarini o'zgartirish", callback_data="adm_stars_edit"),
            InlineKeyboardButton(text="🟣 🛍️ Do'kon narxlarini o'zgartirish", callback_data="adm_shop_edit")
        ],
        [
            InlineKeyboardButton(text="🔵 📢 Xabar tarqatish (Broadcast)", callback_data="adm_broadcast"),
            InlineKeyboardButton(text="🟢 🌐 Web Panel havolasi", callback_data="adm_weblink")
        ],
        [
            InlineKeyboardButton(text="💾 Baza Zaxirasi & Cloud Sync", callback_data="adm_dbsync")
        ]
    ])

def get_casino_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎰 Slot Mashinasi", callback_data="play_slot_fast"),
            InlineKeyboardButton(text="🎯 Darts Otish", callback_data="play_darts_fast")
        ],
        [
            InlineKeyboardButton(text="🎲 Omadli Kubik", callback_data="play_dice_fast"),
            InlineKeyboardButton(text="⚔️ Duel Qoidalari", callback_data="duel_help_info")
        ],
        [
            InlineKeyboardButton(text="💍 Nikoh & Oila", callback_data="marriage_info"),
            InlineKeyboardButton(text="🎟️ Promo-kod faollashtirish", callback_data="promo_code_enter")
        ]
    ])

