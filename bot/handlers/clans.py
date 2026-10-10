from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.db import db

router = Router()

class ClanFSM(StatesGroup):
    waiting_for_clan_name = State()
    waiting_for_clan_tag = State()
    waiting_for_deposit_amount = State()

@router.message(F.text.contains("Mafia Klani"))
@router.message(Command("clan"))
async def show_clan_menu(message: Message):
    user_id = message.from_user.id
    clan = await db.get_user_clan(user_id)

    if not clan:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏰 Yangi Klan tuzish (💰 5,000 Pul)", callback_data="clan_create_start")],
            [InlineKeyboardButton(text="🏆 Top Klanlar Reytingi", callback_data="clan_top_view")]
        ])
        await message.answer(
            "🏰 <b>MAFIA KLANLARI VA OILALARI</b>\n\n"
            "Siz hozircha hech qanday klan a'zosi emassiz.\n"
            "O'z mafiya oilangizni tuzib, do'stlaringizni to'plang va umumiy xazinani boyiting!",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    members = await db.get_clan_members(clan["id"])
    members_str = "\n".join([f"• <b>{m['full_name']}</b> ({m['role'].upper()}) - {m['level']}-daraja" for m in members])

    text = (
        f"🏰 <b>KLAN: [{clan['tag']}] {clan['name']}</b>\n\n"
        f"🎖 <b>Klan Darajasi:</b> {clan['level']}-daraja\n"
        f"👑 <b>Sizning mavqeingiz:</b> {clan['member_role'].upper()}\n"
        f"💰 <b>Klan Xazinasi:</b> {clan['treasury_pul']:,} Pul | 💎 {clan['treasury_almaz']} Almaz\n\n"
        f"👥 <b>Klan a'zolari ({len(members)} kishi):</b>\n{members_str}\n\n"
        f"<i>Xazinaga pul qo'shib klan darajasini oshiring!</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Xazinaga pul qo'shish", callback_data="clan_deposit_pul"),
            InlineKeyboardButton(text="💎 Almaz qo'shish", callback_data="clan_deposit_almaz")
        ],
        [
            InlineKeyboardButton(text="🏆 Top Klanlar", callback_data="clan_top_view"),
            InlineKeyboardButton(text="🚪 Klandan chiqish", callback_data="clan_leave_confirm")
        ]
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "clan_create_start")
async def clan_create_init(call: CallbackQuery, state: FSMContext):
    user = await db.get_user(call.from_user.id)
    if user["pul"] < 5000:
        await call.answer("❌ Klan tuzish uchun 5,000 Pul kerak! Sizda mablag' yetarli emas.", show_alert=True)
        return

    await state.set_state(ClanFSM.waiting_for_clan_name)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="clan_cancel")]
    ])
    await call.message.edit_text(
        "🏰 <b>YANGI KLAN TUZISH</b>\n\n"
        "Klanning nomini yozib yuboring (Masalan: <i>Karleone Oilasi</i> yoki <i>Toshkent Sindikati</i>):",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.message(ClanFSM.waiting_for_clan_name)
async def clan_received_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if len(name) < 3 or len(name) > 30:
        await message.answer("⚠️ Klan nomi 3 tadan 30 tagacha harfdan iborat bo'lishi kerak!")
        return
    await state.update_data(clan_name=name)
    await state.set_state(ClanFSM.waiting_for_clan_tag)
    await message.answer(
        f"✅ Klan nomi: <b>{name}</b>\n\n"
        f"Endi klan uchun qisqa teg (TAG) yozing (Masalan: <code>UZB</code>, <code>DON</code>, <code>MAFIA</code>):",
        parse_mode="HTML"
    )

@router.message(ClanFSM.waiting_for_clan_tag)
async def clan_received_tag(message: Message, state: FSMContext):
    tag = message.text.strip().upper()
    if len(tag) < 2 or len(tag) > 6:
        await message.answer("⚠️ Klan tegi 2 tadan 6 tagacha belgidan iborat bo'lishi kerak!")
        return

    data = await state.get_data()
    name = data.get("clan_name")

    user = await db.get_user(message.from_user.id)
    if user["pul"] < 5000:
        await message.answer("❌ Mablag'ingiz yetarli emas!")
        await state.clear()
        return

    # Deduct 5000 pul and create clan
    await db.update_balance(user["id"], pul_diff=-5000)
    clan_id = await db.create_clan(user["id"], name, tag)

    if not clan_id:
        await db.update_balance(user["id"], pul_diff=5000) # refund
        await message.answer("❌ Bunday nomdagi klan allaqachon mavjud yoki xatolik yuz berdi!")
        await state.clear()
        return

    await db.unlock_achievement(user["id"], "clan_maker")
    await message.answer(
        f"🎉 <b>TABRIKLAYMIZ! KLANINGIZ TUZILDI!</b> 🏰\n\n"
        f"Nomi: <b>[{tag}] {name}</b>\n"
        f"Siz ushbu klanning asoschisi va boshlig'isiz!\n\n"
        f"Do'stlaringizni klaningizga taklif qiling.",
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data == "clan_top_view")
async def view_top_clans(call: CallbackQuery):
    top_clans = await db.get_top_clans(10)
    if not top_clans:
        await call.answer("Hozircha klanlar mavjud emas!", show_alert=True)
        return

    text = "🏆 <b>ENG KUCHLI MAFIA KLANLARI TOP-10</b> 🏆\n\n"
    for i, c in enumerate(top_clans, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += (
            f"{medal} <b>[{c['tag']}] {c['name']}</b>\n"
            f"   👥 {c['member_count']} a'zo | 💰 Xazina: {c['treasury_pul']:,} Pul | {c['level']}-daraja\n\n"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="clan_cancel")]
    ])
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "clan_cancel")
async def clan_cancel_cb(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await show_clan_menu(call.message)
    await call.answer()
