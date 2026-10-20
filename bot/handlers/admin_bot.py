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
    waiting_for_car_user_id = State()
    waiting_for_car_qty = State()
    waiting_for_edit_user_id = State()
    waiting_for_edit_value = State()

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# --- MAIN ADMIN MENU ---

@router.message(F.text.contains("Admin Panel"))
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

# --- 6.1 CAR GRANTING WITH BUTTONS ---

ADMIN_CARS = [
    ("mashina_matiz", "🚗 Daewoo Matiz", "10%"),
    ("mashina_nexia", "🚙 Daewoo Nexia 2", "12%"),
    ("mashina_gentra", "🚙 Chevrolet Gentra", "15%"),
    ("mashina_monza", "🚗 Chevrolet Monza", "18%"),
    ("mashina_kaban", "🚘 Mercedes W140 Kaban", "20%"),
    ("mashina_malibu", "🚔 Chevrolet Malibu 2", "25%"),
    ("mashina_bmw", "🏎️ BMW M5 F90", "30%"),
    ("mashina_gelik", "🚙 Mercedes G63 Gelik", "35%"),
    ("mashina_porsche", "🏎️ Porsche 911 Turbo S", "40%"),
    ("mashina_rolls", "👑 Rolls-Royce Phantom", "50%"),
]

def get_cars_selection_keyboard(target_id: int) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for code, name, _ in ADMIN_CARS:
        row.append(InlineKeyboardButton(text=name, callback_data=f"adm_givecar_{target_id}_{code}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_give_car")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_car_qty_keyboard(target_id: int, car_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 ta 🚗", callback_data=f"adm_carqty_{target_id}_{car_code}_1"),
            InlineKeyboardButton(text="2 ta 🚗", callback_data=f"adm_carqty_{target_id}_{car_code}_2"),
            InlineKeyboardButton(text="3 ta 🚗", callback_data=f"adm_carqty_{target_id}_{car_code}_3"),
        ],
        [
            InlineKeyboardButton(text="5 ta 🚗", callback_data=f"adm_carqty_{target_id}_{car_code}_5"),
            InlineKeyboardButton(text="10 ta 🚗", callback_data=f"adm_carqty_{target_id}_{car_code}_10"),
            InlineKeyboardButton(text="✍️ Boshqa son", callback_data=f"adm_carqty_custom_{target_id}_{car_code}")
        ],
        [
            InlineKeyboardButton(text="🔙 Mashinalar ro'yxatiga", callback_data=f"adm_pickcar_{target_id}")
        ]
    ])

async def apply_give_car(event, bot, admin_id: int, target_id: int, car_code: str, qty: int):
    await db.add_inventory_item(target_id, car_code, qty)
    user = await db.get_user(target_id)
    car_name = next((name for c, name, _ in ADMIN_CARS if c == car_code), car_code)
    u_name = user["full_name"] if user else f"ID: {target_id}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Yana mashina berish", callback_data=f"adm_pickcar_{target_id}")],
        [InlineKeyboardButton(text="⚙️ Asosiy panel", callback_data="adm_back")]
    ])

    text = (
        f"✅ <b>MASHINA MUVAFFAQIYATLI BERILDI!</b> 🚗\n\n"
        f"👤 O'yinchi: <b>{u_name}</b> (<code>{target_id}</code>)\n"
        f"🚘 Mashina: <b>{car_name}</b>\n"
        f"🔢 Miqdor: <b>{qty} dona</b>\n\n"
        f"✨ O'yinchining garajiga muvaffaqiyatli qo'shildi!"
    )
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    elif hasattr(event, "edit_text"):
        try:
            await event.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await event.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")

    if target_id != admin_id:
        try:
            await bot.send_message(
                target_id,
                f"🎁 <b>TABRIKLAYMIZ! SOVG'A OLINDI!</b>\n\n"
                f"Bosh Administrator sizning hisobingizga <b>{qty} dona {car_name}</b> sovg'a qildi! 🚗💨\n\n"
                f"Garajingizni ko'rish uchun profilingizga kiring.",
                parse_mode="HTML"
            )
        except Exception:
            pass

@router.callback_query(F.data == "adm_give_car")
async def adm_give_car_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👤 O'zimga ({call.from_user.id})", callback_data=f"adm_pickcar_{call.from_user.id}")],
        [InlineKeyboardButton(text="✍️ Boshqa foydalanuvchi ID sini kiritish", callback_data="adm_car_custom_user")],
        [InlineKeyboardButton(text="🔙 Asosiy panel", callback_data="adm_back")]
    ])
    await call.message.edit_text(
        "🚗 <b>FOYDALANUVCHIGA MASHINA BERISH</b>\n\n"
        "Kimning garajiga mashina qo'shmoqchisiz?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "adm_car_custom_user")
async def adm_car_ask_user_id(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminFSM.waiting_for_car_user_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_give_car")]
    ])
    await call.message.edit_text(
        "✍️ <b>Mashina beriladigan foydalanuvchining Telegram ID sini yuboring:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("adm_pickcar_"))
async def adm_pick_car_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.replace("adm_pickcar_", ""))
    user = await db.get_user(target_id)
    if not user:
        await call.answer("Foydalanuvchi topilmadi!", show_alert=True)
        return
    u_name = user["full_name"]
    await call.message.edit_text(
        f"🚗 <b>{u_name}</b> (<code>{target_id}</code>) uchun mashina tanlang:\n\n"
        f"Quyidagi mashinalardan birini bosing:",
        reply_markup=get_cars_selection_keyboard(target_id),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("adm_givecar_"))
async def adm_select_car_qty_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    rest = call.data.replace("adm_givecar_", "")
    target_id_str, car_code = rest.split("_", 1)
    target_id = int(target_id_str)

    car_name = next((name for c, name, _ in ADMIN_CARS if c == car_code), car_code)
    u = await db.get_user(target_id)
    u_name = u["full_name"] if u else f"ID: {target_id}"

    await call.message.edit_text(
        f"🚘 Tanlandi: <b>{car_name}</b>\n"
        f"👤 Qabul qiluvchi: <b>{u_name}</b> (<code>{target_id}</code>)\n\n"
        f"Nechta dona bermoqchisiz? Tanlang yoki sonini yozing:",
        reply_markup=get_car_qty_keyboard(target_id, car_code),
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("adm_carqty_"))
async def adm_grant_car_cb(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    data_str = call.data.replace("adm_carqty_", "")
    if data_str.startswith("custom_"):
        rest = data_str.replace("custom_", "")
        target_id_str, car_code = rest.split("_", 1)
        target_id = int(target_id_str)
        await state.set_state(AdminFSM.waiting_for_car_qty)
        await state.update_data(car_target_id=target_id, car_code=car_code)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data=f"adm_givecar_{target_id}_{car_code}")]
        ])
        await call.message.edit_text(
            "✍️ <b>Nechta mashina bermoqchisiz? Son ko'rinishida yozing:</b>\n<i>(Masalan: 1 yoki 5)</i>",
            reply_markup=kb,
            parse_mode="HTML"
        )
        await call.answer()
        return

    target_and_car, _, qty_str = data_str.rpartition("_")
    target_id_str, car_code = target_and_car.split("_", 1)
    target_id = int(target_id_str)
    qty = int(qty_str)

    await apply_give_car(call, call.bot, call.from_user.id, target_id, car_code, qty)
    await call.answer("✅ Mashina berildi!", show_alert=True)

# --- 6.2 PROFILE EDITING WITH BUTTONS ---

async def display_user_profile_edit_menu(event, target_id: int):
    import time
    user = await db.get_user(target_id)
    if not user:
        if isinstance(event, CallbackQuery):
            await event.answer("Foydalanuvchi topilmadi!", show_alert=True)
        return

    custom_title = user.get("custom_title") or "Oddiy fuqaro"
    rep = user.get("rep") or 0
    vip_until = user.get("vip_until") or 0
    vip_str = "Yo'q"
    if vip_until > time.time():
        rem_days = max(1, int((vip_until - time.time()) / 86400))
        vip_str = f"👑 {rem_days} kun qoldi"

    text = (
        f"✏️ <b>FOYDALANUVCHI PROFILINI TAHRIRLASH:</b>\n\n"
        f"👤 <b>Ism:</b> <b>{user['full_name']}</b> (@{user['username'] or 'yoq'})\n"
        f"🆔 <b>ID:</b> <code>{user['id']}</code>\n"
        f"🏷️ <b>Unvon / Maqom:</b> <b>{custom_title}</b>\n"
        f"⭐ <b>Daraja:</b> <b>{user['level']}-daraja</b>\n"
        f"⚡ <b>Tajriba (XP):</b> <b>{user['xp']:,} XP</b>\n"
        f"🌟 <b>Obro' (Rep):</b> <b>{rep} ball</b>\n"
        f"👑 <b>VIP Holati:</b> <b>{vip_str}</b>\n\n"
        f"<i>O'zgartirmoqchi bo'lgan parametr tugmasini bosing:</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏷️ Unvon / Maqom", callback_data=f"admedit_f_{target_id}_title"),
            InlineKeyboardButton(text="⭐ Daraja (Level)", callback_data=f"admedit_f_{target_id}_level")
        ],
        [
            InlineKeyboardButton(text="⚡ Tajriba (XP)", callback_data=f"admedit_f_{target_id}_xp"),
            InlineKeyboardButton(text="🌟 Obro' (Rep)", callback_data=f"admedit_f_{target_id}_rep")
        ],
        [
            InlineKeyboardButton(text="👑 VIP Kunlar berish", callback_data=f"admedit_f_{target_id}_vip"),
            InlineKeyboardButton(text="👤 Ismni o'zgartirish", callback_data=f"admedit_f_{target_id}_name")
        ],
        [
            InlineKeyboardButton(text="🔙 Admin panel", callback_data="adm_back")
        ]
    ])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        await event.answer()
    else:
        await event.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "adm_edit_profile")
async def adm_edit_profile_menu(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.clear()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"👤 O'z profilim ({call.from_user.id})", callback_data=f"adm_eduser_{call.from_user.id}")],
        [InlineKeyboardButton(text="✍️ Boshqa foydalanuvchi ID sini kiritish", callback_data="adm_edit_custom_user")],
        [InlineKeyboardButton(text="🔙 Asosiy panel", callback_data="adm_back")]
    ])
    await call.message.edit_text(
        "✏️ <b>PROFILNI TAHRIRLASH (ADMIN)</b>\n\n"
        "Kimning profilini tahrirlamoqchisiz?",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "adm_edit_custom_user")
async def adm_edit_ask_user_id(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminFSM.waiting_for_edit_user_id)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="adm_edit_profile")]
    ])
    await call.message.edit_text(
        "✍️ <b>Tahrirlanadigan foydalanuvchining Telegram ID sini yuboring:</b>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data.startswith("adm_eduser_"))
async def adm_eduser_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    target_id = int(call.data.replace("adm_eduser_", ""))
    await display_user_profile_edit_menu(call, target_id)

@router.callback_query(F.data.startswith("admedit_f_"))
async def adm_edit_field_cb(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    parts = call.data.split("_")
    target_id = int(parts[2])
    field = parts[3]

    await state.set_state(AdminFSM.waiting_for_edit_value)
    await state.update_data(edit_target_id=target_id, edit_field=field)

    prompts = {
        "title": "🏷️ <b>Yangi unvon / maqomni yozib yuboring:</b>\n<i>(Masalan: 👑 Don Karleone, 🎩 Shahar Hokimi, 🕶️ Mafioz)</i>",
        "level": "⭐ <b>Yangi daraja (Level) raqamini kiriting:</b>\n<i>(Masalan: 5, 10, 50)</i>",
        "xp": "⚡ <b>Yangi XP miqdorini kiriting:</b>\n<i>(Masalan: 2500)</i>",
        "rep": "🌟 <b>Yangi Obro' (Rep) ballini kiriting:</b>\n<i>(Masalan: 25)</i>",
        "vip": "👑 <b>Necha kunlik VIP status berilsin?</b>\n<i>(Masalan: 7, 30 yoki 0 - VIPni bekor qilish)</i>",
        "name": "👤 <b>Foydalanuvchining yangi ismini kiriting:</b>"
    }

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data=f"adm_eduser_{target_id}")]
    ])
    await call.message.edit_text(prompts.get(field, "Qiymatni kiriting:"), reply_markup=kb, parse_mode="HTML")
    await call.answer()

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

@router.message(AdminFSM.waiting_for_car_user_id)
async def fsm_received_car_user_id(message: Message, state: FSMContext):
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
    await state.clear()
    await message.answer(
        f"🚗 <b>{user['full_name']}</b> (<code>{target_id}</code>) uchun mashina tanlang:\n\n"
        f"Quyidagi mashinalardan birini bosing:",
        reply_markup=get_cars_selection_keyboard(target_id),
        parse_mode="HTML"
    )

@router.message(AdminFSM.waiting_for_car_qty)
async def fsm_received_car_qty(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    text = message.text.strip()
    if not text.isdigit() or int(text) <= 0:
        await message.answer("⚠️ Iltimos, musbat butun son kiriting (masalan: 1, 2, 5)!")
        return
    qty = int(text)
    data = await state.get_data()
    target_id = data.get("car_target_id", message.from_user.id)
    car_code = data.get("car_code", "mashina_matiz")
    await state.clear()
    await apply_give_car(message, message.bot, message.from_user.id, target_id, car_code, qty)

@router.message(AdminFSM.waiting_for_edit_user_id)
async def fsm_received_edit_user_id(message: Message, state: FSMContext):
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
    await state.clear()
    await display_user_profile_edit_menu(message, target_id)

@router.message(AdminFSM.waiting_for_edit_value)
async def fsm_received_edit_value(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    data = await state.get_data()
    target_id = data.get("edit_target_id")
    field = data.get("edit_field")
    val_text = message.text.strip()

    if not target_id or not field:
        await state.clear()
        return

    kwargs = {}
    if field in ["level", "xp", "rep", "vip"]:
        if not (val_text.isdigit() or (val_text.startswith("-") and val_text[1:].isdigit())):
            await message.answer("⚠️ Iltimos, faqat butun son kiriting!")
            return
        num = int(val_text)
        if field == "level":
            kwargs["level"] = max(1, num)
        elif field == "xp":
            kwargs["xp"] = max(0, num)
        elif field == "rep":
            kwargs["rep"] = num
        elif field == "vip":
            kwargs["vip_days"] = num
    elif field == "title":
        kwargs["custom_title"] = val_text
    elif field == "name":
        kwargs["full_name"] = val_text

    await db.edit_user_profile(target_id, **kwargs)
    await state.clear()

    await message.answer("✅ <b>Foydalanuvchi ma'lumotlari muvaffaqiyatli saqlandi!</b>", parse_mode="HTML")
    await display_user_profile_edit_menu(message, target_id)

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

# --- DATABASE SYNC & BACKUP ---

@router.callback_query(F.data == "adm_dbsync")
async def show_adm_dbsync(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    import time
    from pathlib import Path
    from database.db_sync import db_sync
    from config import GITHUB_REPO

    db_p = Path(db.db_path)
    file_size_kb = (db_p.stat().st_size / 1024) if db_p.exists() else 0
    stats = await db.get_stats()
    clans = await db.get_top_clans(100)

    last_sync_str = (
        time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(db_sync.last_backup_time))
        if db_sync.last_backup_time else "Hali bajarilmadi"
    )

    text = (
        "💾 <b>MA'LUMOTLAR BAZASI VA CLOUD SINXRONIZATSIYASI</b>\n\n"
        f"📁 <b>Fayl hajmi:</b> {file_size_kb:.1f} KB\n"
        f"👥 <b>Foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"🏰 <b>Klanlar:</b> {len(clans)} ta\n"
        f"🕹 <b>Jami o'yinlar:</b> {stats['total_games']} ta\n\n"
        f"☁️ <b>GitHub Cloud Baza:</b> <code>{GITHUB_REPO}</code>\n"
        f"🔄 <b>Oxirgi Cloud Sync:</b> {last_sync_str}\n"
        f"📊 <b>Cloud Holati:</b> {db_sync.last_backup_status}\n\n"
        "<i>Render qayta ishga tushganda yoki yangi kod yuklanganda barcha ma'lumotlar Cloud'dan avtomatik tiklanadi!</i>"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Bazani yuklab olish (.db)", callback_data="adm_download_db")],
        [InlineKeyboardButton(text="🔄 Cloud'ga hozir saqlash (Force Sync)", callback_data="adm_force_cloud_backup")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="adm_back")]
    ])
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data == "adm_force_cloud_backup")
async def adm_force_cloud_backup_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    from database.db_sync import db_sync
    await call.answer("⏳ Baza GitHub Cloud'ga saqlanmoqda...", show_alert=False)
    success = await db_sync.backup_to_cloud()
    if success:
        await call.answer("✅ Baza GitHub Cloud'ga muvaffaqiyatli saqlandi!", show_alert=True)
    else:
        await call.answer(f"❌ Xatolik: {db_sync.last_backup_status}", show_alert=True)
    await show_adm_dbsync(call)

@router.callback_query(F.data == "adm_download_db")
async def adm_download_db_cb(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    from aiogram.types import FSInputFile
    import time
    db_file = FSInputFile(str(db.db_path), filename=f"mafia_backup_{int(time.time())}.db")
    await call.message.answer_document(
        document=db_file,
        caption="💾 <b>Joriy Mafia ma'lumotlar bazasi nusxasi (.db)</b>",
        parse_mode="HTML"
    )
    await call.answer()

@router.message(Command("backup"))
async def cmd_backup(message: Message):
    if not is_admin(message.from_user.id):
        return

    from aiogram.types import FSInputFile
    from database.db_sync import db_sync
    import time

    status_msg = await message.answer("⏳ Baza zaxiralanmoqda va Cloud'ga yuborilmoqda...")
    await db_sync.backup_to_cloud()

    db_file = FSInputFile(str(db.db_path), filename=f"mafia_backup_{int(time.time())}.db")
    await message.answer_document(
        document=db_file,
        caption=(
            f"💾 <b>MAFIA BAZASI ZAXIRA NUSXASI</b>\n\n"
            f"📅 Vaqt: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"☁️ Cloud Sync: {db_sync.last_backup_status}"
        ),
        parse_mode="HTML"
    )
    await status_msg.delete()

