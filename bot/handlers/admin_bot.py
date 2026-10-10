import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS, WEB_PORT, WEB_ADMIN_SECRET
from database.db import db
from bot.keyboards import get_admin_main_keyboard
from game.engine import game_manager

router = Router()

class AdminFSM(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_custom_amount = State()
    waiting_for_ban_id = State()
    waiting_for_unban_id = State()
    waiting_for_broadcast_text = State()
    waiting_for_star_price = State()
    waiting_for_item_price = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# --- MAIN ADMIN MENU ---

@router.message(F.text == "⚙️ Admin Panel")
@router.message(Command("admin"))
async def open_admin_panel(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    text = (
        "⚙️ <b>BOSH ADMIN BOSHQARUV PANELI</b> ⚙️\n\n"
        f"Xush kelibsiz, Bosh Administrator (ID: <code>{message.from_user.id}</code>)!\n\n"
        "Quyidagi tugmalar orqali barcha amallarni knopkalar orqali bajaring:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_main_keyboard())

@router.callback_query(F.data == "adm_back")
async def adm_back_cb(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    await call.message.edit_text(
        "⚙️ <b>BOSH ADMIN BOSHQARUV PANELI</b>\nQuyidagi bo'limlardan birini tanlang:",
        reply_markup=get_admin_main_keyboard(),
        parse_mode="HTML"
    )
    await call.answer()

# --- 1. STATS ---

@router.callback_query(F.data == "adm_stats")
async def show_adm_stats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    stats = await db.get_stats()
    active_games = len(game_manager.rooms)

    text = (
        "📊 <b>BOTNING UMUMIY STATISTIKASI:</b>\n\n"
        f"👥 <b>Foydalanuvchilar:</b> {stats['total_users']:,} nafar\n"
        f"🎮 <b>Hozirgi faol o'yinlar:</b> {active_games} ta\n"
        f"🕹️ <b>Jami o'ynalgan o'yinlar:</b> {stats['total_games']:,} ta\n"
        f"💰 <b>Tizimdagi jami Pul:</b> {stats['total_pul']:,} tanga\n"
        f"💎 <b>Tizimdagi jami Almaz:</b> {stats['total_almaz']:,} ta\n\n"
        f"🌐 <b>Web Admin Panel:</b> <code>http://localhost:{WEB_PORT}</code>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")]
    ])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

# --- 2. USERS & FIND ---

@router.callback_query(F.data == "adm_users")
async def adm_users_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 O'z ma'lumotlarimni ko'rish", callback_data="user_info_self")],
        [InlineKeyboardButton(text="🔍 ID bo'yicha qidirish", callback_data="user_info_search")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")]
    ])
    await call.message.edit_text(
        "👤 <b>FOYDALANUVCHILARNI BOSHQARISH</b>\n\n"
        "O'zingizning yoki boshqa foydalanuvchining ma'lumotlarini ko'rish uchun tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "user_info_self")
async def adm_user_info_self(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    u = await db.get_user(call.from_user.id)
    text = (
        f"👤 <b>FOYDALANUVCHI MA'LUMOTI:</b>\n\n"
        f"🆔 ID: <code>{u['id']}</code>\n"
        f"👤 Ism: <b>{u['full_name']}</b> (@{u['username'] or 'yoq'})\n"
        f"🎖 Daraja: {u['level']}-daraja ({u['xp']} XP)\n"
        f"💰 Pul: <b>{u['pul']:,}</b> | 💎 Almaz: <b>{u['almaz']}</b>\n"
        f"🚫 Bloklangan: {'Ha' if u['is_banned'] else 'Yo\'q'}\n"
        f"🎮 O'yinlar: {u['games_played']} ta ({u['games_won']} g'alaba)"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Balans qo'shish", callback_data="bact_add_pul")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_users")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "user_info_search")
async def adm_user_search_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminFSM.waiting_for_user_id)
    await state.update_data(next_step="show_info")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_users")]
    ])
    await call.message.edit_text(
        "🔍 <b>Qidirilayotgan foydalanuvchining Telegram ID sini yuboring:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

# --- 3. BALANCE MANAGEMENT WITH BUTTONS (No manual /addpul commands required!) ---

@router.callback_query(F.data == "adm_balance")
async def adm_balance_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Pul berish 💰", callback_data="bact_add_pul"),
            InlineKeyboardButton(text="➖ Pul ayirish 💰", callback_data="bact_sub_pul")
        ],
        [
            InlineKeyboardButton(text="➕ Almaz berish 💎", callback_data="bact_add_almaz"),
            InlineKeyboardButton(text="➖ Almaz ayirish 💎", callback_data="bact_sub_almaz")
        ],
        [
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")
        ]
    ])
    await call.message.edit_text(
        "💰 <b>BALANS BOSHQARUVI (KNOPKALI TIZIM)</b>\n\n"
        "Quyidagi tugmalardan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("bact_"))
async def adm_select_balance_target(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    action = call.data.replace("bact_", "")
    await state.update_data(balance_action=action)

    action_names = {
        "add_pul": "💰 Pul qo'shish",
        "sub_pul": "💰 Pul ayirish",
        "add_almaz": "💎 Almaz qo'shish",
        "sub_almaz": "💎 Almaz ayirish",
    }
    act_title = action_names.get(action, "Balans o'zgartirish")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👤 O'zimga ({call.from_user.id})", callback_data=f"btarget_{call.from_user.id}")],
        [InlineKeyboardButton(text="✍️ Boshqa foydalanuvchi ID sini kiritish", callback_data="btarget_custom")],
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_balance")]
    ])

    await call.message.edit_text(
        f"🎯 <b>Amal: {act_title}</b>\n\n"
        f"Kimning hisobiga amal oshirilsin?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "btarget_custom")
async def adm_ask_custom_user_id(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminFSM.waiting_for_user_id)
    await state.update_data(next_step="balance_amount")
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_balance")]
    ])
    await call.message.edit_text(
        "✍️ <b>Foydalanuvchining Telegram ID sini yozib yuboring:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("btarget_"))
async def adm_show_amount_buttons(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    target_id = int(call.data.replace("btarget_", ""))
    await state.update_data(target_user_id=target_id)
    data = await state.get_data()
    action = data.get("balance_action", "add_pul")

    await display_amount_presets(call.message, action, target_id)
    await call.answer()

async def display_amount_presets(message: Message, action: str, target_id: int):
    u = await db.get_user(target_id)
    u_name = u["full_name"] if u else f"ID: {target_id}"

    if action == "add_pul":
        title = f"💰 <b>{u_name}</b> hisobiga <b>Pul qo'shish</b>:"
        buttons = [
            [InlineKeyboardButton(text="+1,000 💰", callback_data="bval_1000"), InlineKeyboardButton(text="+5,000 💰", callback_data="bval_5000")],
            [InlineKeyboardButton(text="+10,000 💰", callback_data="bval_10000"), InlineKeyboardButton(text="+25,000 💰", callback_data="bval_25000")],
            [InlineKeyboardButton(text="+50,000 💰", callback_data="bval_50000"), InlineKeyboardButton(text="+100,000 💰", callback_data="bval_100000")],
            [InlineKeyboardButton(text="+500,000 💰", callback_data="bval_500000"), InlineKeyboardButton(text="+1,000,000 💰", callback_data="bval_1000000")],
            [InlineKeyboardButton(text="✍️ Boshqa miqdor kiritish", callback_data="bval_custom")],
            [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_balance")]
        ]
    elif action == "sub_pul":
        title = f"💰 <b>{u_name}</b> hisobidan <b>Pul ayirish</b>:"
        buttons = [
            [InlineKeyboardButton(text="-1,000 💰", callback_data="bval_-1000"), InlineKeyboardButton(text="-5,000 💰", callback_data="bval_-5000")],
            [InlineKeyboardButton(text="-10,000 💰", callback_data="bval_-10000"), InlineKeyboardButton(text="-25,000 💰", callback_data="bval_-25000")],
            [InlineKeyboardButton(text="-50,000 💰", callback_data="bval_-50000"), InlineKeyboardButton(text="-100,000 💰", callback_data="bval_-100000")],
            [InlineKeyboardButton(text="✍️ Boshqa miqdor kiritish", callback_data="bval_custom")],
            [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_balance")]
        ]
    elif action == "add_almaz":
        title = f"💎 <b>{u_name}</b> hisobiga <b>Almaz qo'shish</b>:"
        buttons = [
            [InlineKeyboardButton(text="+5 💎", callback_data="bval_5"), InlineKeyboardButton(text="+10 💎", callback_data="bval_10")],
            [InlineKeyboardButton(text="+25 💎", callback_data="bval_25"), InlineKeyboardButton(text="+50 💎", callback_data="bval_50")],
            [InlineKeyboardButton(text="+100 💎", callback_data="bval_100"), InlineKeyboardButton(text="+250 💎", callback_data="bval_250")],
            [InlineKeyboardButton(text="+500 💎", callback_data="bval_500"), InlineKeyboardButton(text="+1,000 💎", callback_data="bval_1000")],
            [InlineKeyboardButton(text="✍️ Boshqa miqdor kiritish", callback_data="bval_custom")],
            [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_balance")]
        ]
    else: # sub_almaz
        title = f"💎 <b>{u_name}</b> hisobidan <b>Almaz ayirish</b>:"
        buttons = [
            [InlineKeyboardButton(text="-5 💎", callback_data="bval_-5"), InlineKeyboardButton(text="-10 💎", callback_data="bval_-10")],
            [InlineKeyboardButton(text="-25 💎", callback_data="bval_-25"), InlineKeyboardButton(text="-50 💎", callback_data="bval_-50")],
            [InlineKeyboardButton(text="-100 💎", callback_data="bval_-100"), InlineKeyboardButton(text="-500 💎", callback_data="bval_-500")],
            [InlineKeyboardButton(text="✍️ Boshqa miqdor kiritish", callback_data="bval_custom")],
            [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_balance")]
        ]

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.edit_text(title + "\n\nKerakli miqdor tugmasini bosing:", reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("bval_"))
async def adm_apply_balance_preset(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    val_str = call.data.replace("bval_", "")
    if val_str == "custom":
        await state.set_state(AdminFSM.waiting_for_custom_amount)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_balance")]
        ])
        await call.message.edit_text(
            "✍️ <b>Kerakli miqdorni son ko'rinishida yozib yuboring:</b>\n<i>(Masalan: 75000 yoki 150)</i>",
            reply_markup=kb,
            parse_mode="HTML"
        )
        await call.answer()
        return

    amount = int(val_str)
    data = await state.get_data()
    action = data.get("balance_action", "add_pul")
    target_id = data.get("target_user_id", call.from_user.id)

    # Apply
    if "pul" in action:
        await db.update_balance(target_id, pul_diff=amount)
        cur_icon = "💰 Pul"
    else:
        await db.update_balance(target_id, almaz_diff=amount)
        cur_icon = "💎 Almaz"

    user = await db.get_user(target_id)
    new_bal = user["pul"] if "pul" in action else user["almaz"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yana balans o'zgartirish", callback_data="adm_balance")],
        [InlineKeyboardButton(text="⚙️ Asosiy panel", callback_data="adm_back")]
    ])

    await call.message.edit_text(
        f"✅ <b>Balans muvaffaqiyatli yangilandi!</b>\n\n"
        f"👤 Foydalanuvchi: <b>{user['full_name']}</b> (<code>{target_id}</code>)\n"
        f"💵 Amal: <b>{amount:+,} {cur_icon}</b>\n"
        f"📊 Yangi balans: <b>{new_bal:,} {cur_icon}</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer("✅ Balans saqlandi!", show_alert=True)

    # Notify target user if not admin themselves
    if target_id != call.from_user.id:
        try:
            await call.bot.send_message(
                target_id,
                f"💳 <b>Hisobingiz ma'muriyat tomonidan yangilandi:</b> {amount:+,} {cur_icon}!"
            )
        except Exception:
            pass

    await state.clear()

# --- 4. BAN / UNBAN WITH BUTTONS ---

@router.callback_query(F.data == "adm_ban")
async def adm_ban_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚫 Foydalanuvchini bloklash (Ban)", callback_data="ban_action_ban")],
        [InlineKeyboardButton(text="✅ Blokdan chiqarish (Unban)", callback_data="ban_action_unban")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")]
    ])
    await call.message.edit_text(
        "🚫 <b>BLOKLASH VA BLOKDAN CHIQARISH</b>\n\nAmalni tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("ban_action_"))
async def adm_ban_ask_id(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    action_type = call.data.replace("ban_action_", "")
    await state.update_data(ban_type=action_type)
    await state.set_state(AdminFSM.waiting_for_ban_id)

    title = "🚫 <b>Bloklash (Ban) uchun</b>" if action_type == "ban" else "✅ <b>Blokdan chiqarish (Unban) uchun</b>"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_ban")]
    ])
    await call.message.edit_text(
        f"{title} foydalanuvchining Telegram ID sini yuboring:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

# --- 5. STARS PRICES WITH BUTTONS ---

@router.callback_query(F.data == "adm_stars_edit")
async def adm_stars_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    packages = await db.get_star_packages(only_active=False)
    buttons = []
    for p in packages:
        status_icon = "🟢" if p["is_active"] else "🔴"
        txt = f"{status_icon} {p['title']} — ⭐️ {p['stars_price']}"
        buttons.append([InlineKeyboardButton(text=txt, callback_data=f"pkg_edit_{p['id']}")])

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(
        "⭐️ <b>STARS PAKETLARI VA NARXLARI (KNOPKALI BOSHQARUV)</b>\n\n"
        "Narxini yoki holatini o'zgartirish uchun kerakli paketni tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("pkg_edit_"))
async def adm_pkg_details(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    pkg_id = int(call.data.replace("pkg_edit_", ""))
    pkg = await db.get_package_by_id(pkg_id)
    if not pkg:
        await call.answer("Paket topilmadi!", show_alert=True)
        return

    status_str = "🟢 Faol" if pkg["is_active"] else "🔴 O'chirilgan"
    text = (
        f"⭐️ <b>PAKET #{pkg['id']}: {pkg['title']}</b>\n\n"
        f"⭐️ Hozirgi narxi: <b>{pkg['stars_price']} Stars</b>\n"
        f"💎/💰 Miqdor: <b>{pkg['amount']:,}</b> (+{pkg['bonus']:,} bonus)\n"
        f"Holat: <b>{status_str}</b>\n\n"
        f"Narxni sozlash uchun pastdagi tugmalarni bosing:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐️ -5", callback_data=f"pkg_adj_{pkg_id}_-5"),
            InlineKeyboardButton(text="⭐️ +5", callback_data=f"pkg_adj_{pkg_id}_5"),
            InlineKeyboardButton(text="⭐️ +25", callback_data=f"pkg_adj_{pkg_id}_25")
        ],
        [
            InlineKeyboardButton(text="🔄 Holatni o'zgartirish (On/Off)", callback_data=f"pkg_toggle_{pkg_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Paketlar ro'yxatiga", callback_data="adm_stars_edit")
        ]
    ])

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("pkg_adj_"))
async def adm_pkg_adjust_price(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    parts = call.data.split("_")
    pkg_id = int(parts[2])
    delta = int(parts[3])

    pkg = await db.get_package_by_id(pkg_id)
    if pkg:
        new_stars = max(1, pkg["stars_price"] + delta)
        await db.update_star_package(pkg_id, new_stars, pkg["amount"], pkg["bonus"], pkg["title"], pkg["is_active"])
        await call.answer(f"⭐️ Yangi narx: {new_stars} Stars!")
        await adm_pkg_details(call)

@router.callback_query(F.data.startswith("pkg_toggle_"))
async def adm_pkg_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    pkg_id = int(call.data.replace("pkg_toggle_", ""))
    pkg = await db.get_package_by_id(pkg_id)
    if pkg:
        new_active = 0 if pkg["is_active"] else 1
        await db.update_star_package(pkg_id, pkg["stars_price"], pkg["amount"], pkg["bonus"], pkg["title"], new_active)
        await call.answer("Holat yangilandi!")
        await adm_pkg_details(call)

# --- 6. SHOP ITEMS WITH BUTTONS ---

@router.callback_query(F.data == "adm_shop_edit")
async def adm_shop_items_menu(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    items = await db.get_items(only_active=False)
    buttons = []
    row = []
    for it in items:
        status_icon = "🟢" if it["is_active"] else "🔴"
        row.append(InlineKeyboardButton(text=f"{status_icon} {it['icon']} {it['name'][:12]}", callback_data=f"sitem_{it['code']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.edit_text(
        "🛍️ <b>DO'KON BUYUMLARI NARXINI SOZLASH (KNOPKALI)</b>\n\n"
        "Narxini ko'rish yoki tahrirlash uchun buyumni tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("sitem_"))
async def adm_shop_item_details(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    code = call.data.replace("sitem_", "")
    item = await db.get_item_by_code(code)
    if not item:
        await call.answer("Buyum topilmadi!", show_alert=True)
        return

    text = (
        f"{item['icon']} <b>{item['name']}</b> (<code>{item['code']}</code>)\n\n"
        f"💰 Pul narxi: <b>{item['price_pul']:,} Pul</b>\n"
        f"💎 Almaz narxi: <b>{item['price_almaz']} Almaz</b>\n"
        f"📖 Ta'rif: <i>{item['description']}</i>\n"
        f"Holat: <b>{'🟢 Sotuvda mavjud' if item['is_active'] else '🔴 O\'chirilgan'}</b>\n\n"
        f"Narxni o'zgartirish uchun tanlang:"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Pul narxini +/-", callback_data=f"siadj_pul_{code}"),
            InlineKeyboardButton(text="💎 Almaz narxini +/-", callback_data=f"siadj_almaz_{code}")
        ],
        [
            InlineKeyboardButton(text="🔄 Holatni o'zgartirish (On/Off)", callback_data=f"sitoggle_{code}")
        ],
        [
            InlineKeyboardButton(text="🔙 Do'kon ro'yxatiga", callback_data="adm_shop_edit")
        ]
    ])

    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data.startswith("sitoggle_"))
async def adm_shop_item_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    code = call.data.replace("sitoggle_", "")
    item = await db.get_item_by_code(code)
    if item:
        new_active = 0 if item["is_active"] else 1
        await db.update_item(code, item["name"], item["price_pul"], item["price_almaz"], item["description"], new_active)
        await call.answer("Holat yangilandi!")
        await adm_shop_item_details(call)

@router.callback_query(F.data.startswith("siadj_pul_"))
async def adm_adjust_item_pul(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    code = call.data.replace("siadj_pul_", "")
    item = await db.get_item_by_code(code)
    if not item:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="-500 💰", callback_data=f"sichg_pul_{code}_-500"),
            InlineKeyboardButton(text="+500 💰", callback_data=f"sichg_pul_{code}_500"),
            InlineKeyboardButton(text="+1,000 💰", callback_data=f"sichg_pul_{code}_1000")
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"sitem_{code}")]
    ])
    await call.message.edit_text(
        f"{item['icon']} <b>{item['name']}</b>\n"
        f"Hozirgi Pul narxi: <b>{item['price_pul']:,} Pul</b>\n\n"
        f"O'zgartirish tugmasini bosing:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("siadj_almaz_"))
async def adm_adjust_item_almaz(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    code = call.data.replace("siadj_almaz_", "")
    item = await db.get_item_by_code(code)
    if not item:
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="-1 💎", callback_data=f"sichg_almaz_{code}_-1"),
            InlineKeyboardButton(text="+1 💎", callback_data=f"sichg_almaz_{code}_1"),
            InlineKeyboardButton(text="+5 💎", callback_data=f"sichg_almaz_{code}_5")
        ],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data=f"sitem_{code}")]
    ])
    await call.message.edit_text(
        f"{item['icon']} <b>{item['name']}</b>\n"
        f"Hozirgi Almaz narxi: <b>{item['price_almaz']} Almaz</b>\n\n"
        f"O'zgartirish tugmasini bosing:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("sichg_"))
async def adm_save_item_delta(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    cur_type = parts[1] # pul or almaz
    code = parts[2]
    delta = int(parts[3])

    item = await db.get_item_by_code(code)
    if item:
        if cur_type == "pul":
            new_price = max(0, item["price_pul"] + delta)
            await db.update_item(code, item["name"], new_price, item["price_almaz"], item["description"], item["is_active"])
            await call.answer(f"💰 Yangi narx: {new_price:,} Pul!")
        else:
            new_price = max(0, item["price_almaz"] + delta)
            await db.update_item(code, item["name"], item["price_pul"], new_price, item["description"], item["is_active"])
            await call.answer(f"💎 Yangi narx: {new_price} Almaz!")
        await adm_shop_item_details(call)

# --- 7. BROADCAST WITH CONFIRMATION BUTTON ---

@router.callback_query(F.data == "adm_broadcast")
async def adm_broadcast_prompt(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return

    await state.set_state(AdminFSM.waiting_for_broadcast_text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_back")]
    ])
    await call.message.edit_text(
        "📢 <b>BARCHA FOYDALANUVCHILARGA XABAR TARQATISH</b>\n\n"
        "Yubormoqchi bo'lgan e'lon matningizni ushbu chatga yozib yuboring:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

# --- FSM TEXT HANDLERS ---

@router.message(AdminFSM.waiting_for_user_id)
async def fsm_received_user_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamlardan iborat Telegram ID yuboring!")
        return

    target_id = int(text)
    user = await db.get_user(target_id)
    if not user:
        await message.answer(f"❌ ID <code>{target_id}</code> bo'yicha foydalanuvchi topilmadi!", parse_mode="HTML")
        await state.clear()
        return

    data = await state.get_data()
    next_step = data.get("next_step")

    if next_step == "show_info":
        info_text = (
            f"👤 <b>FOYDALANUVCHI MA'LUMOTI:</b>\n\n"
            f"🆔 ID: <code>{user['id']}</code>\n"
            f"👤 Ism: <b>{user['full_name']}</b> (@{user['username'] or 'yoq'})\n"
            f"🎖 Daraja: {user['level']}-daraja ({user['xp']} XP)\n"
            f"💰 Pul: <b>{user['pul']:,}</b> | 💎 Almaz: <b>{user['almaz']}</b>\n"
            f"🚫 Bloklangan: {'Ha' if user['is_banned'] else 'Yo\'q'}\n"
            f"🎮 O'yinlar: {user['games_played']} ta ({user['games_won']} g'alaba)"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Balans qo'shish", callback_data="bact_add_pul")],
            [InlineKeyboardButton(text="🔙 Asosiy panel", callback_data="adm_back")]
        ])
        await message.answer(info_text, reply_markup=kb, parse_mode="HTML")
        await state.clear()
    else: # balance_amount
        await state.update_data(target_user_id=target_id)
        action = data.get("balance_action", "add_pul")
        await display_amount_presets(message, action, target_id)

@router.message(AdminFSM.waiting_for_custom_amount)
async def fsm_received_custom_amount(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    try:
        amount = int(text)
    except ValueError:
        await message.answer("⚠️ Iltimos, to'g'ri son kiriting!")
        return

    data = await state.get_data()
    action = data.get("balance_action", "add_pul")
    target_id = data.get("target_user_id", message.from_user.id)

    if "sub" in action and amount > 0:
        amount = -amount

    if "pul" in action:
        await db.update_balance(target_id, pul_diff=amount)
        cur_icon = "💰 Pul"
    else:
        await db.update_balance(target_id, almaz_diff=amount)
        cur_icon = "💎 Almaz"

    user = await db.get_user(target_id)
    new_bal = user["pul"] if "pul" in action else user["almaz"]

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yana balans o'zgartirish", callback_data="adm_balance")],
        [InlineKeyboardButton(text="⚙️ Asosiy panel", callback_data="adm_back")]
    ])

    await message.answer(
        f"✅ <b>Balans muvaffaqiyatli saqlandi!</b>\n\n"
        f"👤 Foydalanuvchi: <b>{user['full_name']}</b> (<code>{target_id}</code>)\n"
        f"💵 Kiritildi: <b>{amount:+,} {cur_icon}</b>\n"
        f"📊 Yangi balans: <b>{new_bal:,} {cur_icon}</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.clear()

@router.message(AdminFSM.waiting_for_ban_id)
async def fsm_received_ban_id(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text = message.text.strip()
    if not text.isdigit():
        await message.answer("⚠️ Iltimos, faqat raqamli ID kiriting!")
        return

    target_id = int(text)
    data = await state.get_data()
    ban_type = data.get("ban_type", "ban")

    is_banned = (ban_type == "ban")
    await db.set_ban(target_id, is_banned=is_banned)

    status_str = "🚫 Bloklandi (Ban)" if is_banned else "✅ Blokdan chiqarildi (Unban)"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ban menyusiga", callback_data="adm_ban")],
        [InlineKeyboardButton(text="⚙️ Asosiy panel", callback_data="adm_back")]
    ])
    await message.answer(
        f"✅ ID <code>{target_id}</code> foydalanuvchisi holati o'zgartirildi: <b>{status_str}</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await state.clear()

@router.message(AdminFSM.waiting_for_broadcast_text)
async def fsm_received_broadcast(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    text_to_send = message.text
    users = await db.search_users(limit=5000)
    sent_count = 0
    fail_count = 0

    status_msg = await message.answer("⏳ Xabar tarqatilmoqda...")

    for u in users:
        try:
            await message.bot.send_message(u["id"], f"📢 <b>RASMIY E'LON:</b>\n\n{text_to_send}", parse_mode="HTML")
            sent_count += 1
        except Exception:
            fail_count += 1

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚙️ Asosiy panel", callback_data="adm_back")]
    ])

    await status_msg.edit_text(
        f"✅ <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"Yuborildi: {sent_count} ta\n"
        f"Yetib bormadi (bloklagan): {fail_count} ta",
        reply_markup=kb
    )
    await state.clear()

# --- WEB PANEL LINK ---

@router.callback_query(F.data == "adm_weblink")
async def show_weblink(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    text = (
        "🌐 <b>WEB ADMIN SAYTI BO'YICHA MA'LUMOT:</b>\n\n"
        f"Sayt manzili: <code>http://localhost:{WEB_PORT}</code>\n"
        f"🔑 <b>Admin Maxfiy Kalit:</b> <code>{WEB_ADMIN_SECRET}</code>\n\n"
        f"🔗 <b>Bir klikda kirish havolasi:</b>\n"
        f"<code>http://localhost:{WEB_PORT}/?secret={WEB_ADMIN_SECRET}</code>\n\n"
        "Sayt orqali foydalanuvchilarni qulay jadvalda ko'rish, qidirish, "
        "narxlarni o'zgartirish va do'konga yangi buyumlar qo'shish mumkin!"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")]
    ])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()
