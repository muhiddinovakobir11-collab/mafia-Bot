from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    PreCheckoutQuery,
    LabeledPrice,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command
from database.db import db
from bot.keyboards import get_star_packages_keyboard

router = Router()

@router.message(F.text.contains("Stars to'ldirish"))
@router.message(F.text.contains("Stars orqali"))
@router.message(Command("stars", "donat", "donate"))
@router.callback_query(F.data == "buy_stars_menu")
@router.callback_query(F.data == "stars_type_almaz")
async def show_stars_almaz_menu(event: Message | CallbackQuery):
    is_cb = isinstance(event, CallbackQuery)
    user_id = event.from_user.id
    chat_type = event.message.chat.type if is_cb else event.chat.type
    bot = event.bot

    packages = await db.get_star_packages(pkg_type="almaz", only_active=True)
    text = (
        "⭐️ <b>TELEGRAM STARS ORQALI ALMAZ VA PUL XARID QILISH</b> ⭐️\n\n"
        "Almazlar — botdagi premium valyuta bo'lib, ular orqali eng kuchli artefaktlar, "
        "VIP status va noyob unvonlarni sotib olishingiz mumkin!\n\n"
        "<i>Quyidagi paketlardan birini tanlang:</i>"
    )
    kb = get_star_packages_keyboard(packages, pkg_type="almaz")

    if chat_type in ["group", "supergroup"]:
        if not is_cb:
            bot_info = await bot.get_me()
            bot_url = f"https://t.me/{bot_info.username}?start=stars"
            group_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🤖 Botga o'tish ➔", url=bot_url)]
            ])
            await event.reply(
                "⭐️ <b>Stars va to'lovlar menyusi shaxsiy lichkangizga yuborildi!</b>\n"
                "<i>Paketlarni ko'rish uchun pastdagi tugmani bosing:</i>",
                parse_mode="HTML",
                reply_markup=group_kb
            )
        try:
            await bot.send_message(user_id, text, parse_mode="HTML", reply_markup=kb)
            if is_cb:
                await event.answer("⭐️ Stars paketlari shaxsiy lichkangizga yuborildi!", show_alert=False)
        except Exception:
            if is_cb:
                bot_info = await bot.get_me()
                await event.answer(f"⚠️ Avval @{bot_info.username} ga kirib Start bosing!", show_alert=True)
        return

    # In DM:
    if is_cb:
        try:
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await event.message.answer(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "stars_type_pul")
async def show_stars_pul_menu(call: CallbackQuery):
    packages = await db.get_star_packages(pkg_type="pul", only_active=True)
    text = (
        "💰 <b>TELEGRAM STARS ORQALI PUL (TANGA) XARID QILISH</b> 💰\n\n"
        "Pul paketlarini xarid qiling va darhol o'yindagi eng zo'r himoya vositalariga ega bo'ling!\n\n"
        "<i>O'zingizga ma'qul paketni tanlang:</i>"
    )
    kb = get_star_packages_keyboard(packages, pkg_type="pul")

    if call.message.chat.type in ["group", "supergroup"]:
        try:
            await call.bot.send_message(call.from_user.id, text, parse_mode="HTML", reply_markup=kb)
            await call.answer("⭐️ Stars pul paketlari shaxsiy lichkangizga yuborildi!", show_alert=False)
        except Exception:
            bot_info = await call.bot.get_me()
            await call.answer(f"⚠️ Avval @{bot_info.username} ga kirib Start bosing!", show_alert=True)
        return

    try:
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    except Exception:
        await call.message.answer(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("buy_pkg_"))
async def create_stars_invoice(call: CallbackQuery):
    pkg_id = int(call.data.replace("buy_pkg_", ""))
    pkg = await db.get_package_by_id(pkg_id)

    if not pkg or not pkg["is_active"]:
        await call.answer("❌ Bu paket hozirda mavjud emas!", show_alert=True)
        return

    stars_amount = pkg["stars_price"]
    currency = "XTR" # Telegram Stars currency code

    payload = f"stars_pkg_{pkg['id']}_{call.from_user.id}"

    # Telegram Stars invoice
    prices = [LabeledPrice(label=pkg["title"], amount=stars_amount)]

    try:
        await call.bot.send_invoice(
            chat_id=call.from_user.id,
            title=f"⭐️ {pkg['title']} xaridi",
            description=f"Telegram Stars orqali {pkg['title']} hisobingizga qo'shiladi.",
            payload=payload,
            currency=currency,
            prices=prices,
            provider_token="" # Must be empty for Telegram Stars!
        )
        if call.message.chat.type in ["group", "supergroup"]:
            await call.answer("⭐️ To'lov hisob-fakturasi shaxsiy lichkangizga yuborildi!", show_alert=False)
        else:
            await call.answer("⭐️ To'lov cheki yuborildi!")
    except Exception as e:
        print(f"[Stars Invoice Error]: {e}")
        await call.answer("❌ To'lov chekini yaratishda xatolik yuz berdi!", show_alert=True)

@router.pre_checkout_query()
async def process_pre_checkout(pre_checkout_query: PreCheckoutQuery):
    # Always approve valid pre-checkout for Telegram Stars
    await pre_checkout_query.answer(ok=True)

@router.message(F.successful_payment)
async def process_successful_payment(message: Message):
    sp = message.successful_payment
    payload = sp.invoice_payload

    if payload.startswith("stars_pkg_"):
        parts = payload.split("_")
        pkg_id = int(parts[2])
        pkg = await db.get_package_by_id(pkg_id)

        if pkg:
            user_id = message.from_user.id
            if pkg["package_type"] == "almaz":
                total_almaz = pkg["amount"] + pkg["bonus"]
                await db.update_balance(user_id, almaz_diff=total_almaz)
                await message.answer(
                    f"🎉 <b>TO'LOV MUVAFFAQIYATLI QABUL QILINDI!</b> ⭐️\n\n"
                    f"Hisobingizga <b>+{total_almaz} 💎 Almaz</b> qo'shildi!\n"
                    f"Haridingiz uchun rahmat, maroqli o'yin tilaymiz!"
                )
            elif pkg["package_type"] == "pul":
                total_pul = pkg["amount"] + pkg["bonus"]
                await db.update_balance(user_id, pul_diff=total_pul)
                await message.answer(
                    f"🎉 <b>TO'LOV MUVAFFAQIYATLI QABUL QILINDI!</b> ⭐️\n\n"
                    f"Hisobingizga <b>+{total_pul:,} 💰 Pul</b> qo'shildi!\n"
                    f"Haridingiz uchun rahmat, maroqli o'yin tilaymiz!"
                )
