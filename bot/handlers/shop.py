import time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database.db import db
from bot.keyboards import get_shop_menu_keyboard

router = Router()

@router.message(F.text.contains("Do'kon & Narsalar"))
@router.callback_query(F.data == "open_shop")
async def show_shop_menu(event: Message | CallbackQuery):
    text = (
        "🛍️ <b>MAFIYA SEHRLI DO'KONI</b>\n\n"
        "Bu yerda o'yinda sizga ustunlik beruvchi kuchli artefaktlar, himoya vositalari va VIP statusni "
        "💰 <b>Pul</b> yoki 💎 <b>Almaz</b> evaziga sotib olishingiz mumkin!\n\n"
        "<i>Qaysi bo'limga o'tmoqchisiz?</i>"
    )
    if isinstance(event, Message):
        await event.answer(text, parse_mode="HTML", reply_markup=get_shop_menu_keyboard())
    else:
        await event.message.answer(text, parse_mode="HTML", reply_markup=get_shop_menu_keyboard())
        await event.answer()

@router.callback_query(F.data == "shop_view_pul")
async def view_shop_pul(call: CallbackQuery):
    items = await db.get_items(only_active=True)
    pul_items = [it for it in items if it["price_pul"] > 0]

    buttons = []
    for it in pul_items:
        txt = f"{it['icon']} {it['name']} — 💰 {it['price_pul']:,}"
        buttons.append([InlineKeyboardButton(text=txt, callback_data=f"buy_item_pul_{it['code']}")])

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="open_shop")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.answer(
        "💰 <b>PULGA SOTIB OLINADIGAN BUYUMLAR:</b>\n\n"
        "O'zingizga kerakli narsani tanlang va xarid qiling:",
        reply_markup=kb
    )
    await call.answer()

@router.callback_query(F.data == "shop_view_almaz")
async def view_shop_almaz(call: CallbackQuery):
    items = await db.get_items(only_active=True)
    almaz_items = [it for it in items if it["price_almaz"] > 0]

    buttons = []
    for it in almaz_items:
        txt = f"{it['icon']} {it['name']} — 💎 {it['price_almaz']}"
        buttons.append([InlineKeyboardButton(text=txt, callback_data=f"buy_item_almaz_{it['code']}")])

    buttons.append([InlineKeyboardButton(text="🔙 Orqaga", callback_data="open_shop")])
    kb = InlineKeyboardMarkup(inline_keyboard=buttons)

    await call.message.answer(
        "💎 <b>ALMAZGA SOTIB OLINADIGAN BUYUMLAR VA VIP:</b>\n\n"
        "O'zingizga kerakli narsani tanlang va xarid qiling:",
        reply_markup=kb
    )
    await call.answer()

@router.callback_query(F.data.startswith("buy_item_pul_"))
async def handle_buy_item_pul(call: CallbackQuery):
    item_code = call.data.replace("buy_item_pul_", "")
    user = await db.get_user(call.from_user.id)
    item = await db.get_item_by_code(item_code)

    if not item or not item["is_active"]:
        await call.answer("❌ Bu buyum mavjud emas!", show_alert=True)
        return

    price = item["price_pul"]
    if user["pul"] < price:
        await call.answer(f"❌ Mablag' yetarli emas! Sizda {user['pul']:,} pul bor, kerak: {price:,} pul.", show_alert=True)
        return

    # Deduct pul and add to inventory
    await db.update_balance(user["id"], pul_diff=-price)
    await db.add_inventory_item(user["id"], item_code, 1)

    await call.answer(f"✅ {item['name']} muvaffaqiyatli sotib olindi!", show_alert=True)
    await call.message.answer(
        f"🎉 <b>Xarid muvaffaqiyatli amalga oshirildi!</b>\n\n"
        f"Siz <b>{item['icon']} {item['name']}</b> sotib oldingiz.\n"
        f"💰 Sarflandi: <b>{price:,} Pul</b>\n"
        f"🎒 Bu narsa o'yin paytida avtomatik foyda beradi!"
    )

@router.callback_query(F.data.startswith("buy_item_almaz_"))
async def handle_buy_item_almaz(call: CallbackQuery):
    item_code = call.data.replace("buy_item_almaz_", "")
    user = await db.get_user(call.from_user.id)
    item = await db.get_item_by_code(item_code)

    if not item or not item["is_active"]:
        await call.answer("❌ Bu buyum mavjud emas!", show_alert=True)
        return

    price = item["price_almaz"]
    if user["almaz"] < price:
        await call.answer(f"❌ Almaz yetarli emas! Sizda {user['almaz']} ta almaz bor, kerak: {price} ta.", show_alert=True)
        return

    # Deduct almaz
    await db.update_balance(user["id"], almaz_diff=-price)

    # Special logic for VIP items
    if item_code == "vip_7":
        new_vip = max(int(time.time()), user.get("vip_until", 0)) + (7 * 86400)
        import aiosqlite
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute("UPDATE users SET vip_until = ? WHERE id = ?;", (new_vip, user["id"]))
            await conn.commit()
    elif item_code == "vip_30":
        new_vip = max(int(time.time()), user.get("vip_until", 0)) + (30 * 86400)
        import aiosqlite
        async with aiosqlite.connect(db.db_path) as conn:
            await conn.execute("UPDATE users SET vip_until = ? WHERE id = ?;", (new_vip, user["id"]))
            await conn.commit()
    else:
        await db.add_inventory_item(user["id"], item_code, 1)

    await call.answer(f"✅ {item['name']} muvaffaqiyatli xarid qilindi!", show_alert=True)
    await call.message.answer(
        f"🎉 <b>Xarid muvaffaqiyatli!</b>\n\n"
        f"Siz <b>{item['icon']} {item['name']}</b> xarid qildingiz.\n"
        f"💎 Sarflandi: <b>{price} Almaz</b>"
    )

@router.callback_query(F.data == "shop_exchange")
async def show_exchange_menu(call: CallbackQuery):
    rate_str = await db.get_setting("almaz_to_pul_rate", "500")
    rate = int(rate_str)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"💎 1 Almaz ➔ 💰 {rate:,} Pul", callback_data="exchange_1")],
        [InlineKeyboardButton(text=f"💎 5 Almaz ➔ 💰 {rate * 5:,} Pul", callback_data="exchange_5")],
        [InlineKeyboardButton(text=f"💎 10 Almaz ➔ 💰 {rate * 10:,} Pul", callback_data="exchange_10")],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="open_shop")]
    ])
    await call.message.answer(
        f"🔄 <b>ALMAZNI PULGA ALMASHTIRISH VALYUTA BIRJASI</b>\n\n"
        f"Joriy kurs: <b>1 💎 Almaz = {rate:,} 💰 Pul</b>\n\n"
        f"Qancha almashtirmoqchisiz?",
        reply_markup=kb
    )
    await call.answer()

@router.callback_query(F.data.startswith("exchange_"))
async def process_exchange(call: CallbackQuery):
    amt_str = call.data.replace("exchange_", "")
    if not amt_str.isdigit():
        return
    almaz_to_spend = int(amt_str)

    rate_str = await db.get_setting("almaz_to_pul_rate", "500")
    rate = int(rate_str)
    pul_to_receive = almaz_to_spend * rate

    user = await db.get_user(call.from_user.id)
    if user["almaz"] < almaz_to_spend:
        await call.answer("❌ Almazlaringiz soni yetarli emas!", show_alert=True)
        return

    await db.update_balance(user["id"], pul_diff=pul_to_receive, almaz_diff=-almaz_to_spend)
    await call.answer(f"✅ +{pul_to_receive:,} pulga almashtirildi!", show_alert=True)
    await call.message.answer(
        f"✅ <b>Almashuv bajarildi!</b>\n"
        f"💎 -{almaz_to_spend} Almaz\n"
        f"💰 +{pul_to_receive:,} Pul hisobingizga qo'shildi!"
    )
