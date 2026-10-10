import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from database.db import db

router = Router()

@router.message(Command("duel"))
async def start_duel_cmd(message: Message):
    if message.chat.type == "private":
        await message.answer("⚠️ 1v1 Duel faqat Telegram guruhlarida o'ynaladi! Botni guruhingizga qo'shing.")
        return

    args = message.text.split()
    bet_amount = 500
    bet_type = "pul"

    if len(args) > 1 and args[1].isdigit():
        bet_amount = max(100, int(args[1]))

    challenger = await db.get_user(message.from_user.id)
    if not challenger or challenger["pul"] < bet_amount:
        await message.answer(f"❌ Garov tikish uchun hisobingizda kamida <b>{bet_amount:,} Pul</b> bo'lishi kerak!")
        return

    # Check if replied to someone
    opponent_id = 0
    opponent_name = "Istalgan o'yinchi"
    if message.reply_to_message and not message.reply_to_message.from_user.is_bot:
        if message.reply_to_message.from_user.id == message.from_user.id:
            await message.answer("⚠️ O'zingizga o'zingiz duel e'lon qila olmaysiz!")
            return
        opponent_id = message.reply_to_message.from_user.id
        opponent_name = message.reply_to_message.from_user.full_name

    duel_id = await db.create_duel(message.from_user.id, opponent_id, bet_type, bet_amount)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"⚔️ Duelni qabul qilish ({bet_amount:,} Pul)", callback_data=f"accept_duel_{duel_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"decline_duel_{duel_id}")
        ]
    ])

    await message.answer(
        f"⚔️ <b>1v1 MAFIA DUELI E'LON QILINDI!</b> ⚔️\n\n"
        f"👤 <b>Chaqiruvchi:</b> {message.from_user.full_name}\n"
        f"🎯 <b>Raqib:</b> {opponent_name}\n"
        f"💰 <b>Garov:</b> {bet_amount:,} Pul (Yutuq: <b>{bet_amount * 2:,} Pul</b>)\n\n"
        f"<i>Duelni boshlash uchun pastdagi tugmani bosing!</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("accept_duel_"))
async def handle_accept_duel(call: CallbackQuery):
    duel_id = int(call.data.replace("accept_duel_", ""))
    duel = await db.get_duel(duel_id)

    if not duel or duel["status"] != "pending":
        await call.answer("❌ Bu duel muddati tugagan yoki yakunlangan!", show_alert=True)
        return

    if duel["opponent_id"] != 0 and duel["opponent_id"] != call.from_user.id:
        await call.answer("⚠️ Bu duel faqat chaqirilgan shaxs uchun!", show_alert=True)
        return

    if duel["challenger_id"] == call.from_user.id:
        await call.answer("⚠️ O'z duelingizni o'zingiz qabul qila olmaysiz!", show_alert=True)
        return

    challenger = await db.get_user(duel["challenger_id"])
    opponent = await db.get_user(call.from_user.id)
    bet = duel["bet_amount"]

    if not challenger or challenger["pul"] < bet:
        await call.answer("❌ Chaqiruvchida garov uchun yetarli pul qolmagan!", show_alert=True)
        return

    if not opponent or opponent["pul"] < bet:
        await call.answer(f"❌ Sizda garov uchun {bet:,} Pul yetarli emas!", show_alert=True)
        return

    # Deduct bets from both
    await db.update_balance(challenger["id"], pul_diff=-bet)
    await db.update_balance(opponent["id"], pul_diff=-bet)

    await call.message.edit_text(
        f"⚔️ <b>DUEL BOSHLANDI!</b> ⚔️\n\n"
        f"👤 <b>{challenger['full_name']}</b> VS <b>{opponent['full_name']}</b>\n"
        f"💰 Umumiy bank: <b>{bet * 2:,} Pul</b>!\n\n"
        f"🎲 Zar tashlanmoqda...",
        parse_mode="HTML"
    )

    # Roll dice for both
    dice1 = await call.bot.send_dice(call.message.chat.id, emoji="🎲")
    await asyncio.sleep(2)
    dice2 = await call.bot.send_dice(call.message.chat.id, emoji="🎲")
    await asyncio.sleep(3)

    score1 = dice1.dice.value
    score2 = dice2.dice.value

    if score1 > score2:
        winner = challenger
        winner_score, loser_score = score1, score2
    elif score2 > score1:
        winner = opponent
        winner_score, loser_score = score2, score1
    else:
        # Tie - refund
        await db.update_balance(challenger["id"], pul_diff=bet)
        await db.update_balance(opponent["id"], pul_diff=bet)
        await db.resolve_duel(duel_id, 0)
        await call.message.answer(
            f"🤝 <b>DURRANG!</b> Har ikki o'yinchiga {score1} tushdi!\n"
            f"Garovlar hisoblarga qaytarildi."
        )
        return

    total_prize = bet * 2
    await db.update_balance(winner["id"], pul_diff=total_prize)
    await db.resolve_duel(duel_id, winner["id"])

    # Update quests & achievements
    await db.progress_quest(winner["id"], "win_duel", 1)
    await db.unlock_achievement(winner["id"], "duelist")

    await call.message.answer(
        f"🏆 <b>DUEL G'OLIBI: {winner['full_name']}!</b> 🏆\n\n"
        f"🎲 Natija: <b>{winner_score}</b> ga <b>{loser_score}</b>!\n"
        f"💰 Yutuq: <b>+{total_prize:,} Pul</b> {winner['full_name']} hisobiga o'tkazildi!",
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("decline_duel_"))
async def handle_decline_duel(call: CallbackQuery):
    duel_id = int(call.data.replace("decline_duel_", ""))
    duel = await db.get_duel(duel_id)

    if not duel or duel["status"] != "pending":
        await call.answer("Duel allaqachon yakunlangan!", show_alert=True)
        return

    if duel["opponent_id"] != 0 and duel["opponent_id"] != call.from_user.id:
        await call.answer("Faqat raqib rad eta oladi!", show_alert=True)
        return

    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("UPDATE duels SET status = 'declined' WHERE id = ?;", (duel_id,))
        await conn.commit()

    await call.message.edit_text("❌ <b>Duel rad etildi.</b>", parse_mode="HTML")
    await call.answer()
