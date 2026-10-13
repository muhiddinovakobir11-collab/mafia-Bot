import urllib.parse
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
    waiting_for_deposit_pul = State()
    waiting_for_deposit_almaz = State()

@router.message(F.text.contains("Mafia Klani"))
@router.message(Command("clan"))
async def show_clan_menu(message: Message, user_id: int = None):
    if user_id is None:
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
        f"<i>Do'stlaringizni taklif qiling yoki xazinani to'ldirib klaningizni kuchaytiring!</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ A'zo taklif qilish", callback_data="clan_invite_link"),
            InlineKeyboardButton(text="🏆 Top Klanlar", callback_data="clan_top_view")
        ],
        [
            InlineKeyboardButton(text="💰 Xazinaga pul qo'shish", callback_data="clan_deposit_pul"),
            InlineKeyboardButton(text="💎 Almaz qo'shish", callback_data="clan_deposit_almaz")
        ],
        [
            InlineKeyboardButton(text="🚪 Klandan chiqish", callback_data="clan_leave_confirm")
        ]
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data == "clan_invite_link")
async def clan_invite_link_handler(call: CallbackQuery):
    user_id = call.from_user.id
    clan = await db.get_user_clan(user_id)
    if not clan:
        await call.answer("Siz hech qanday klan a'zosi emassiz!", show_alert=True)
        return

    bot_info = await call.bot.get_me()
    clan_link = f"https://t.me/{bot_info.username}?start=clan_{clan['id']}"
    share_text = f"Salom! Men tuzgan [{clan['tag']}] {clan['name']} nomli mafiya klaniga qo'shil va biz bilan birga g'alaba qozon! 🏰🔥"
    share_url = f"https://t.me/share/url?url={urllib.parse.quote(clan_link)}&text={urllib.parse.quote(share_text)}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Telegram orqali ulashish", url=share_url)],
        [InlineKeyboardButton(text="🔙 Orqaga", callback_data="clan_cancel")]
    ])

    text = (
        f"🏰 <b>[{clan['tag']}] {clan['name']} KLANIGA TAKLIF QILISH</b>\n\n"
        f"Do'stlaringizni klaningizga jalb qiling va eng qudratli mafiya oilasiga aylaning!\n\n"
        f"🔗 <b>Sizning klaningiz taklif havolasi:</b>\n"
        f"<code>{clan_link}</code>\n\n"
        f"👆 <i>Ushbu havolani do'stingizga yuboring yoki yuqoridagi <b>'Telegram orqali ulashish'</b> tugmasini bosing.\n"
        f"Do'stingiz ushbu havola orqali botga kirib Start bosishi bilanoq avtomatik klaningizga qo'shiladi!</i>"
    )
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await call.answer()

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
        f"Endi '🏰 Mafia Klani' menyusiga kirib, '➕ A'zo taklif qilish' tugmasi orqali do'stlaringizni klaningizga taklif qilishingiz mumkin.",
        parse_mode="HTML"
    )
    await state.clear()

@router.callback_query(F.data == "clan_deposit_pul")
async def clan_deposit_pul_start(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    clan = await db.get_user_clan(user_id)
    if not clan:
        await call.answer("Siz klanda emassiz!", show_alert=True)
        return
    user = await db.get_user(user_id)
    await state.set_state(ClanFSM.waiting_for_deposit_pul)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="clan_cancel")]
    ])
    await call.message.edit_text(
        f"💰 <b>KLAN XAZINASIGA PUL QO'SHISH</b>\n\n"
        f"Sizning balansingiz: <b>{user['pul']:,} Pul</b>\n\n"
        f"Klan xazinasiga qancha pul qo'shmoqchisiz? Miqdorni son bilan yozing:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.message(ClanFSM.waiting_for_deposit_pul)
async def clan_deposit_pul_received(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Iltimos, musbat butun son kiriting (masalan: 1000):")
        return

    user = await db.get_user(user_id)
    if user["pul"] < amount:
        await message.answer(f"❌ Mablag'ingiz yetarli emas! Sizda {user['pul']:,} Pul bor.")
        return

    clan = await db.get_user_clan(user_id)
    if not clan:
        await message.answer("❌ Siz klan a'zosi emassiz.")
        await state.clear()
        return

    await db.update_balance(user_id, pul_diff=-amount)
    await db.deposit_clan(clan["id"], pul=amount)
    await state.clear()
    await message.answer(
        f"✅ <b>Klan xazinasiga {amount:,} Pul muvaffaqiyatli qo'shildi!</b>\n"
        f"Klaningiz qudrati oshdi! 🏰",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "clan_deposit_almaz")
async def clan_deposit_almaz_start(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    clan = await db.get_user_clan(user_id)
    if not clan:
        await call.answer("Siz klanda emassiz!", show_alert=True)
        return
    user = await db.get_user(user_id)
    await state.set_state(ClanFSM.waiting_for_deposit_almaz)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="clan_cancel")]
    ])
    await call.message.edit_text(
        f"💎 <b>KLAN XAZINASIGA ALMAZ QO'SHISH</b>\n\n"
        f"Sizning balansingiz: <b>{user['almaz']:,} Almaz</b>\n\n"
        f"Klan xazinasiga qancha almaz qo'shmoqchisiz? Miqdorni son bilan yozing:",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.message(ClanFSM.waiting_for_deposit_almaz)
async def clan_deposit_almaz_received(message: Message, state: FSMContext):
    user_id = message.from_user.id
    try:
        amount = int(message.text.strip())
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await message.answer("⚠️ Iltimos, musbat butun son kiriting (masalan: 5):")
        return

    user = await db.get_user(user_id)
    if user["almaz"] < amount:
        await message.answer(f"❌ Almazlaringiz yetarli emas! Sizda {user['almaz']:,} Almaz bor.")
        return

    clan = await db.get_user_clan(user_id)
    if not clan:
        await message.answer("❌ Siz klan a'zosi emassiz.")
        await state.clear()
        return

    await db.update_balance(user_id, almaz_diff=-amount)
    await db.deposit_clan(clan["id"], almaz=amount)
    await state.clear()
    await message.answer(
        f"✅ <b>Klan xazinasiga {amount:,} Almaz muvaffaqiyatli qo'shildi!</b>\n"
        f"Klaningiz qudrati oshdi! 💎🏰",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "clan_leave_confirm")
async def clan_leave_confirm_handler(call: CallbackQuery):
    user_id = call.from_user.id
    clan = await db.get_user_clan(user_id)
    if not clan:
        await call.answer("Siz klanda emassiz!", show_alert=True)
        return
    is_owner = (clan["owner_id"] == user_id)
    warning = (
        "⚠️ <b>Diqqat!</b> Siz ushbu klanning boshlig'isiz. Agar klandan chiqsangiz, klan butunlay tarqatiladi va o'chiriladi!"
        if is_owner else
        "Rostdan ham klandan chiqmoqchimisiz?"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚪 Ha, chiqish", callback_data="clan_leave_action"),
            InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="clan_cancel")
        ]
    ])
    await call.message.edit_text(
        f"⚠️ <b>KLANDAN CHIQISH</b>\n\n{warning}",
        reply_markup=kb,
        parse_mode="HTML"
    )
    await call.answer()

@router.callback_query(F.data == "clan_leave_action")
async def clan_leave_action_handler(call: CallbackQuery):
    user_id = call.from_user.id
    clan = await db.get_user_clan(user_id)
    if not clan:
        await call.answer("Siz klanda emassiz!", show_alert=True)
        return
    if clan["owner_id"] == user_id:
        await db.delete_clan(clan["id"])
        await call.message.edit_text("🗑 <b>Klaningiz tarqatildi va o'chirildi.</b>", parse_mode="HTML")
    else:
        await db.leave_clan(user_id)
        await call.message.edit_text("🚪 <b>Siz klandan muvaffaqiyatli chiqdingiz.</b>", parse_mode="HTML")
    await call.answer()

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
    clan = await db.get_user_clan(call.from_user.id)
    if not clan:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏰 Yangi Klan tuzish (💰 5,000 Pul)", callback_data="clan_create_start")],
            [InlineKeyboardButton(text="🏆 Top Klanlar Reytingi", callback_data="clan_top_view")]
        ])
        await call.message.edit_text(
            "🏰 <b>MAFIA KLANLARI VA OILALARI</b>\n\n"
            "Siz hozircha hech qanday klan a'zosi emassiz.\n"
            "O'z mafiya oilangizni tuzib, do'stlaringizni to'plang va umumiy xazinani boyiting!",
            reply_markup=kb,
            parse_mode="HTML"
        )
    else:
        members = await db.get_clan_members(clan["id"])
        members_str = "\n".join([f"• <b>{m['full_name']}</b> ({m['role'].upper()}) - {m['level']}-daraja" for m in members])

        text = (
            f"🏰 <b>KLAN: [{clan['tag']}] {clan['name']}</b>\n\n"
            f"🎖 <b>Klan Darajasi:</b> {clan['level']}-daraja\n"
            f"👑 <b>Sizning mavqeingiz:</b> {clan['member_role'].upper()}\n"
            f"💰 <b>Klan Xazinasi:</b> {clan['treasury_pul']:,} Pul | 💎 {clan['treasury_almaz']} Almaz\n\n"
            f"👥 <b>Klan a'zolari ({len(members)} kishi):</b>\n{members_str}\n\n"
            f"<i>Do'stlaringizni taklif qiling yoki xazinani to'ldirib klaningizni kuchaytiring!</i>"
        )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ A'zo taklif qilish", callback_data="clan_invite_link"),
                InlineKeyboardButton(text="🏆 Top Klanlar", callback_data="clan_top_view")
            ],
            [
                InlineKeyboardButton(text="💰 Xazinaga pul qo'shish", callback_data="clan_deposit_pul"),
                InlineKeyboardButton(text="💎 Almaz qo'shish", callback_data="clan_deposit_almaz")
            ],
            [
                InlineKeyboardButton(text="🚪 Klandan chiqish", callback_data="clan_leave_confirm")
            ]
        ])
        await call.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await call.answer()
