from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import db

router = Router()

class WillFSM(StatesGroup):
    waiting_for_will_text = State()

# --- 1. DAILY QUESTS ---

@router.message(F.text.contains("Kunlik Missiyalar"))
@router.message(Command("quests"))
async def show_daily_quests(message: Message):
    user_id = message.from_user.id
    quests = await db.get_daily_quests_for_user(user_id)

    text = "🎯 <b>BUGUNGI KUNLIK MISSIYALAR VA SOVG'ALAR:</b>\n\n"
    buttons = []

    for q in quests:
        prog = min(q["user_progress"], q["target_count"])
        is_done = (prog >= q["target_count"])
        is_claimed = bool(q["is_claimed"])

        status_str = "✅ Olingan" if is_claimed else ("🎁 Tayyor!" if is_done else f"{prog}/{q['target_count']}")

        almaz_str = f", <b>{q['reward_almaz']} Almaz</b>" if q['reward_almaz'] else ""
        xp_str = f", <b>+{q['reward_xp']} XP</b>" if q['reward_xp'] else ""
        text += (
            f"• <b>{q['title']}</b> ({status_str})\n"
            f"   <i>{q['description']}</i>\n"
            f"   🎁 Sovg'a: <b>{q['reward_pul']:,} Pul</b>{almaz_str}{xp_str}\n\n"
        )

        if is_done and not is_claimed:
            buttons.append([InlineKeyboardButton(text=f"🎁 {q['title']} sovg'asini olish!", callback_data=f"claim_q_{q['code']}")])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("claim_q_"))
async def handle_claim_quest(call: CallbackQuery):
    code = call.data.replace("claim_q_", "")
    res = await db.claim_quest_reward(call.from_user.id, code)

    if not res:
        await call.answer("❌ Bu topshiriq hali bajarilmagan yoki sovg'asi olingan!", show_alert=True)
        return

    await call.answer("🎉 Sovg'a hisobingizga qo'shildi!", show_alert=True)
    await call.message.answer(
        f"🎉 <b>TABRIKLAYMIZ! TOPSHIRIQ SOVG'ASI OLINDI!</b>\n\n"
        f"Siz <b>{res['title']}</b> topshirig'ini bajardingiz!\n"
        f"💰 <b>+{res['reward_pul']:,} Pul</b> va 💎 <b>+{res['reward_almaz']} Almaz</b> berildi!"
    )

# --- 2. ACHIEVEMENTS & MEDALS ---

@router.message(F.text == "🏅 Kasbiy Yutuqlar")
@router.message(Command("achievements"))
async def show_achievements(message: Message):
    user_id = message.from_user.id
    achievements = await db.get_achievements_with_user(user_id)

    unlocked_count = sum(1 for a in achievements if a["is_unlocked"])
    text = (
        f"🏅 <b>KASBIY YUTUQLAR VA MEDALLAR ({unlocked_count}/{len(achievements)})</b>\n\n"
        f"O'yinlarda ko'proq g'alaba qozoning va qimmatbaho medallarni oching:\n\n"
    )

    for a in achievements:
        status_icon = "🌟 [OCHILGAN]" if a["is_unlocked"] else "🔒 [QULFLANGAN]"
        text += (
            f"{a['icon']} <b>{a['title']}</b> — {status_icon}\n"
            f"   <i>{a['description']}</i>\n"
            f"   🎁 Sovg'a: <b>{a['reward_pul']:,} Pul</b> | 💎 <b>{a['reward_almaz']} Almaz</b>\n\n"
        )

    await message.answer(text, parse_mode="HTML")

# --- 3. LAST WILL (VASIYATNOMA) ---

@router.message(Command("will"))
@router.message(Command("vasiyat"))
async def show_last_will_menu(message: Message):
    current_will = await db.get_last_will(message.from_user.id)
    will_text = f"<i>\"{current_will}\"</i>" if current_will else "<i>Hozircha vasiyatnoma yozilmagan.</i>"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Yangi Vasiyatnoma yozish", callback_data="will_edit_start")],
        [InlineKeyboardButton(text="🗑️ Vasiyatnomani o'chirish", callback_data="will_delete")]
    ])

    await message.answer(
        f"📜 <b>SIZNING SO'NGGI VASIYATNOMAINGIZ:</b>\n\n"
        f"{will_text}\n\n"
        f"💡 <b>Qanday ishlaydi?</b>\n"
        f"Agar siz o'yinda tunda o'ldirilsangiz yoki dorga osilsangiz, bot ushbu xatingizni "
        f"guruhdagi barcha o'yinchilarga e'lon qiladi (gumonlaringiz va qasosingizni qoldiring!).",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "will_edit_start")
async def will_edit_prompt(call: CallbackQuery, state: FSMContext):
    await state.set_state(WillFSM.waiting_for_will_text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="will_cancel")]
    ])
    await call.message.edit_text(
        "✍️ <b>Vasiyatnomangiz matnini ushbu chatga yozib yuboring:</b>\n"
        "<i>(Masalan: Meni o'ldirgan kimsa aniq Alisher, Komissar uni zudlik bilan tekshirsin!)</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.message(WillFSM.waiting_for_will_text)
async def will_received_text(message: Message, state: FSMContext):
    text = message.text.strip()
    if len(text) > 300:
        await message.answer("⚠️ Vasiyatnoma matni 300 ta belgidan oshmasligi kerak!")
        return

    await db.set_last_will(message.from_user.id, text)
    await message.answer(
        f"✅ <b>Vasiyatnomangiz saqlandi!</b>\n\n"
        f"<i>\"{text}\"</i>\n\n"
        f"O'yinda halok bo'lganingizda ushbu xat guruhga taqdim etiladi.",
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data == "will_delete")
async def will_delete_cb(call: CallbackQuery):
    await db.set_last_will(call.from_user.id, "")
    await call.answer("🗑️ Vasiyatnoma o'chirildi!", show_alert=True)
    await call.message.edit_text("🗑️ <b>Vasiyatnomangiz muvaffaqiyatli o'chirildi.</b>")

@router.callback_query(F.data == "will_cancel")
async def will_cancel_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_last_will_menu(call.message)
    await call.answer()

# --- 4. VOICE CHAT GUIDE ---

@router.message(Command("voice"))
@router.message(Command("voicechat"))
async def voice_chat_guide(message: Message):
    text = (
        "🎙️ <b>TELEGRAM OVOZLI CHAT (VOICE CHAT) MAFIA QOIDALARI:</b>\n\n"
        "O'yinni haqiqiy jonli hayotdagi kabi qizg'in o'tkazish uchun guruhingizda Voice Chatni yoqing!\n\n"
        "1. Guruh ma'muri ovozli chatni ochadi.\n"
        "2. <b>🌑 Tunda:</b> Hamma o'yinchilar mikrofoni o'chiriladi (mute qilinadi) va maxfiy harakatlar botda bajariladi.\n"
        "3. <b>☀️ Kunduzi:</b> Bot tong otganini e'lon qilgach, hamma mikrofonni yoqib kim mafiya ekanligini jonli bahslashadi!\n"
        "4. <b>⚖️ Ovoz berishda:</b> Har bir kishi navbat bilan 30 soniyadan o'zini oqlash yoki boshqani ayblash nutqini so'zlaydi.\n\n"
        "<i>Ovozli chatda o'ynash odatdagi yozishmadan 10 barobar qiziqroq va emotsional bo'ladi!</i>"
    )
    await message.answer(text, parse_mode="HTML")
