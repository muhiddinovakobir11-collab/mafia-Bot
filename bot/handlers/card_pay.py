import random
import time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from config import ADMIN_IDS
from database.db import db
from services.sofpay import sofpay_client
from bot.keyboards import (
    get_card_packages_keyboard,
    get_card_invoice_keyboard,
    get_admin_card_confirm_keyboard
)

router = Router()

@router.message(F.text.contains("Karta orqali xarid"))
@router.message(Command("card"))
@router.message(Command("karta"))
@router.message(Command("donate"))
async def show_card_pay_menu(message: Message):
    packages = await db.get_card_packages(only_active=True)
    card_info = await db.get_card_details()

    text = (
        "💳 <b>KARTA ORQALI XARID (UZCARD / HUMO)</b>\n\n"
        "O'zbekiston bank kartalari (Click, Payme, Uzum va b.) orqali 0% komissiya bilan "
        "Almaz, Pul va VIP status xarid qiling!\n\n"
        "<i>Kerakli paketni tanlang:</i>"
    )
    kb = get_card_packages_keyboard(packages, pkg_type="almaz")
    await message.answer(text, reply_mode="HTML", parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "buy_card_menu")
async def show_card_pay_cb(call: CallbackQuery):
    packages = await db.get_card_packages(only_active=True)
    text = (
        "💳 <b>KARTA ORQALI XARID (UZCARD / HUMO)</b>\n\n"
        "O'zbekiston bank kartalari orqali 0% komissiya bilan "
        "Almaz, Pul va VIP status xarid qiling!\n\n"
        "<i>Kerakli paketni tanlang:</i>"
    )
    kb = get_card_packages_keyboard(packages, pkg_type="almaz")
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("card_view_"))
async def switch_card_view(call: CallbackQuery):
    pkg_type = call.data.replace("card_view_", "")
    packages = await db.get_card_packages(only_active=True)
    kb = get_card_packages_keyboard(packages, pkg_type=pkg_type)

    type_titles = {
        "almaz": "💎 <b>Almaz paketlari:</b>",
        "pul": "💰 <b>Pul paketlari:</b>",
        "vip": "👑 <b>VIP Status paketlari:</b>"
    }
    title = type_titles.get(pkg_type, "Xarid paketlari:")
    await call.message.edit_text(f"💳 <b>KARTA ORQALI XARID</b>\n\n{title}", parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("buy_card_pkg_"))
async def process_card_package_select(call: CallbackQuery):
    pkg_id = int(call.data.replace("buy_card_pkg_", ""))
    pkg = await db.get_card_package(pkg_id)
    if not pkg or not pkg["is_active"]:
        await call.answer("❌ Bu paket faol emas!", show_alert=True)
        return

    user_id = call.from_user.id
    card_info = await db.get_card_details()

    total_item_amount = pkg["amount"] + pkg["bonus"]
    item_name = f"{total_item_amount:,} {pkg['package_type'].upper()}"
    if pkg["package_type"] == "almaz":
        item_name = f"💎 {total_item_amount} Almaz"
    elif pkg["package_type"] == "pul":
        item_name = f"💰 {total_item_amount:,} Pul"
    elif pkg["package_type"] == "vip":
        item_name = f"👑 VIP Status ({total_item_amount} kun)"

    # SofPay orqali avtomatik to'lov hisobini yaratish
    sof_tx = await sofpay_client.create_transaction(
        amount=pkg["price_uzs"],
        description=f"MafiaBot - {user_id} - {item_name}"
    )

    if sof_tx:
        tx_id = sof_tx["tx_id"]
        final_amount = sof_tx.get("amount", pkg["price_uzs"])
        card_number = sof_tx.get("card_number") or card_info["card_number"]
        card_holder = sof_tx.get("shop", "Aiobuna")
    else:
        # Fallback local
        tx_id = f"TX{random.randint(100000, 999999)}"
        unique_offset = random.randint(5, 45)
        final_amount = pkg["price_uzs"] + unique_offset
        card_number = card_info["card_number"]
        card_holder = f"{card_info['card_holder']} ({card_info['card_bank']})"

    await db.create_card_transaction(
        user_id=user_id,
        package_id=pkg["id"],
        tx_id=tx_id,
        item_type=pkg["package_type"],
        item_amount=total_item_amount,
        price_uzs=pkg["price_uzs"],
        unique_amount=final_amount,
        card_number=card_number,
        card_holder=card_holder
    )

    invoice_text = (
        f"🧾 <b>SOFPAY TO'LOV HISOB-FAKTURASI (#{tx_id})</b>\n\n"
        f"📦 <b>Mahsulot:</b> {item_name}\n"
        f"💵 <b>To'lov summasi:</b> <code>{final_amount:,}</code> so'm\n"
        f"<i>(⚠️ Aynan shu <code>{final_amount:,}</code> so'm summani o'tkazing — to'lov avtomatik aniqlanadi!)</i>\n\n"
        f"💳 <b>To'lov kartasi:</b>\n"
        f"<code>{card_number}</code> <i>(Bosing va nusxa oling)</i>\n"
        f"👤 <b>Qabul qiluvchi:</b> {card_holder}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡️ <b>100% AVTOMATIK TASDIQLASH:</b>\n"
        f"1. Istalgan bank ilovasi (Click, Payme, Uzum va b.) orqali to'lovni o'tkazing.\n"
        f"2. To'lov amalga oshirilgach, quyidagi <b>'🔄 To'lovni tekshirish'</b> tugmasini bosing — hisobingizga darhol qo'shiladi!"
    )

    kb = get_card_invoice_keyboard(tx_id)
    await call.message.edit_text(invoice_text, parse_mode="HTML", reply_markup=kb)
    await call.answer()

@router.callback_query(F.data.startswith("check_card_tx_"))
async def check_card_tx_status(call: CallbackQuery):
    tx_id = call.data.replace("check_card_tx_", "")
    tx = await db.get_card_transaction(tx_id)

    if not tx:
        await call.answer("❌ Bunday to'lov topilmadi!", show_alert=True)
        return

    if tx["status"] == "completed":
        await call.answer("✅ To'lovingiz allaqachon tasdiqlangan va balansga o'tgan!", show_alert=True)
        await call.message.edit_text(
            f"🎉 <b>TO'LOV MUVAFFAQIYATLI YAKUNLANGAN!</b>\n\n"
            f"Hisob-faktura: <code>#{tx_id}</code>\n"
            f"Balansingizga xarid qilingan mahsulot to'liq qo'shilgan. Rahmat!",
            parse_mode="HTML"
        )
        return

    if tx["status"] == "cancelled":
        await call.answer("❌ Bu to'lov bekor qilingan!", show_alert=True)
        return

    # 1. SofPay API orqali jonli tekshirish (Real-time polling)
    sof_tx = await sofpay_client.get_transaction(tx_id)
    if sof_tx and sof_tx.get("status") == "completed":
        comp = await db.complete_card_transaction(tx_id)
        if comp:
            await call.answer("✅ To'lovingiz SofPay orqali tasdiqlandi!", show_alert=True)
            await call.message.edit_text(
                f"🎉 <b>TO'LOV MUVAFFAQIYATLI YAKUNLANDI!</b>\n\n"
                f"🆔 Hisob-faktura: <code>#{tx_id}</code>\n"
                f"📦 Xaridingiz: <b>+{comp['item_amount']:,} {comp['item_type'].upper()}</b> balansga qo'shildi!\n\n"
                f"Rahmat, o'yinda omad tilaymiz! 🎲",
                parse_mode="HTML"
            )
            for aid in ADMIN_IDS:
                try:
                    await call.bot.send_message(
                        chat_id=aid,
                        text=(
                            f"💰 <b>SOFPAY TO'LOVI TASDIQLANDI!</b>\n\n"
                            f"🆔 TX: <code>#{tx_id}</code>\n"
                            f"👤 O'yinchi ID: <code>{tx['user_id']}</code>\n"
                            f"💵 Summa: <b>{tx['unique_amount']:,} so'm</b>\n"
                            f"📦 Berildi: {tx['item_amount']:,} {tx['item_type'].upper()}"
                        ),
                        parse_mode="HTML"
                    )
                except Exception:
                    pass
            return

    if tx.get("proof_file_id"):
        await call.answer("⏳ Chekingiz administrator tomonidan tekshirilmoqda...", show_alert=True)
    else:
        await call.answer(
            "⏳ To'lov hali kelib tushmadi!\nIltimos, kartaga pul o'tkazgach, 30 soniyadan keyin qayta tekshiring.",
            show_alert=True
        )

@router.callback_query(F.data.startswith("cancel_card_tx_"))
async def cancel_card_tx_callback(call: CallbackQuery):
    tx_id = call.data.replace("cancel_card_tx_", "")
    await sofpay_client.cancel_transaction(tx_id)
    await db.cancel_card_transaction(tx_id)
    await call.answer("❌ To'lov bekor qilindi.", show_alert=True)
    await call.message.edit_text(f"❌ <b>#{tx_id} raqamli to'lov bekor qilindi.</b>", parse_mode="HTML")

# Photo / Receipt upload handler
@router.message(F.photo)
async def handle_payment_screenshot(message: Message, bot: Bot):
    user_id = message.from_user.id
    # Find most recent pending transaction for user
    transactions = await db.get_card_transactions(limit=5, status="pending")
    user_txs = [t for t in transactions if t["user_id"] == user_id]

    if not user_txs:
        # Not a payment screenshot or no pending tx
        return

    active_tx = user_txs[0]
    tx_id = active_tx["tx_id"]
    file_id = message.photo[-1].file_id

    # Save proof
    await db.set_card_tx_proof(tx_id, file_id)

    await message.reply(
        f"✅ <b>To'lov cheki qabul qilindi! (#{tx_id})</b>\n\n"
        f"Chekingiz administratorga yuborildi. Bir necha daqiqada tekshirilib, balansingiz to'ldiriladi.",
        parse_mode="HTML"
    )

    # Notify admins
    admin_kb = get_admin_card_confirm_keyboard(tx_id)
    caption = (
        f"🔔 <b>YANGI TO'LOV CHEKI KELDI!</b>\n\n"
        f"🆔 <b>To'lov ID:</b> <code>#{tx_id}</code>\n"
        f"👤 <b>Foydalanuvchi:</b> {message.from_user.full_name} (@{message.from_user.username or 'yoq'})\n"
        f"🆔 <b>Telegram ID:</b> <code>{user_id}</code>\n"
        f"📦 <b>Mahsulot:</b> {active_tx['item_amount']} {active_tx['item_type'].upper()}\n"
        f"💵 <b>Kutilgan summa:</b> <b>{active_tx['unique_amount']:,} so'm</b>\n"
        f"💳 <b>Karta:</b> {active_tx['card_number']}\n\n"
        f"<i>Quyidagi tugmalar orqali bir zumda tasdiqlashingiz mumkin:</i>"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_photo(
                chat_id=admin_id,
                photo=file_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=admin_kb
            )
        except Exception:
            pass

# Admin Approve / Reject Callbacks
@router.callback_query(F.data.startswith("adm_appr_tx_"))
async def admin_approve_tx(call: CallbackQuery, bot: Bot):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    tx_id = call.data.replace("adm_appr_tx_", "")
    res = await db.complete_card_transaction(tx_id)

    if not res:
        await call.answer("⚠️ Bu to'lov allaqachon tasdiqlangan yoki bekor qilingan!", show_alert=True)
        return

    await call.answer("✅ To'lov tasdiqlandi va balans to'ldirildi!", show_alert=True)
    await call.message.edit_caption(
        caption=(call.message.caption or "") + "\n\n✅ <b>TASDIQLANDI! Foydalanuvchi balansiga berildi.</b>",
        parse_mode="HTML"
    )

    # Notify user
    item_str = f"{res['item_amount']} {res['item_type']}"
    if res['item_type'] == 'almaz':
        item_str = f"💎 <b>+{res['item_amount']} Almaz</b>"
    elif res['item_type'] == 'pul':
        item_str = f"💰 <b>+{res['item_amount']:,} Pul</b>"
    elif res['item_type'] == 'vip':
        item_str = f"👑 <b>+{res['item_amount']} kunlik VIP Status</b>"

    try:
        await bot.send_message(
            chat_id=res["user_id"],
            text=(
                f"🎉 <b>TO'LOVINGIZ TASDIQLANDI!</b>\n\n"
                f"To'lov ID: <code>#{tx_id}</code>\n"
                f"Hisobingizga {item_str} muvaffaqiyatli qo'shildi!\n\n"
                f"<i>O'yinlardan zavqlaning!</i>"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("adm_rejc_tx_"))
async def admin_reject_tx(call: CallbackQuery, bot: Bot):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("❌ Siz admin emassiz!", show_alert=True)
        return

    tx_id = call.data.replace("adm_rejc_tx_", "")
    tx = await db.get_card_transaction(tx_id)
    await db.cancel_card_transaction(tx_id)

    await call.answer("❌ To'lov rad etildi.", show_alert=True)
    await call.message.edit_caption(
        caption=(call.message.caption or "") + "\n\n❌ <b>RAD ETILDI. Bekor qilindi.</b>",
        parse_mode="HTML"
    )

    if tx:
        try:
            await bot.send_message(
                chat_id=tx["user_id"],
                text=(
                    f"❌ <b>#{tx_id} to'lovingiz tasdiqlanmadi.</b>\n\n"
                    f"Chek mos kelmadi yoki to'lov amalga oshirilmagan. "
                    f"Savollar bo'lsa adminga murojaat qiling."
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass
