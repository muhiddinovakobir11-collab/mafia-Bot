import random
import asyncio
from aiogram import Router, F, Bot
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.filters import Command

from config import ADMIN_IDS
from database.db import db
from game.engine import game_manager
from game.roles import ROLES
from bot.keyboards import get_casino_menu_keyboard

router = Router()

# ==============================================================================
# 0. KAZINO ASOSIY MENYUSI
# ==============================================================================
@router.message(F.text.contains("Kazino & O'yinlar"))
@router.message(Command("games", "casino", "kazino"))
@router.message(F.text.lower().in_(["kazino", "casino", "games", "o'yinlar", "oyinlar"]))
async def show_casino_menu(message: Message):
    if message.chat.type in ["group", "supergroup"]:
        bot_info = await message.bot.get_me()
        bot_url = f"https://t.me/{bot_info.username}?start=games"
        group_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Botga o'tish ➔", url=bot_url)]
        ])
        await message.reply(
            "🎰 <b>Kazino va mini-o'yinlar shaxsiy lichkangizga yuborildi!</b>\n"
            "<i>O'yinlarni boshlash uchun pastdagi tugmani bosing:</i>",
            parse_mode="HTML",
            reply_markup=group_kb
        )
        try:
            user = await db.get_user(message.from_user.id)
            pul_bal = user["pul"] if user else 0
            almaz_bal = user["almaz"] if user else 0
            text = (
                f"🎰 <b>KAZINO VA MINI-O'YINLAR ZALI</b> 🎲\n\n"
                f"Mablag'ingiz: <b>{pul_bal:,} Pul</b> | 💎 <b>{almaz_bal} Almaz</b>\n\n"
                f"Bu yerda omadingizni sinab ko'rishingiz, do'stlaringiz bilan bellashishingiz yoki sovrinlar yutib olishingiz mumkin!\n\n"
                f"🎮 <b>O'yinni tanlang:</b>"
            )
            await message.bot.send_message(message.from_user.id, text, parse_mode="HTML", reply_markup=get_casino_menu_keyboard())
        except Exception:
            pass
        return

    user = await db.get_user(message.from_user.id)
    pul_bal = user["pul"] if user else 0
    almaz_bal = user["almaz"] if user else 0
    text = (
        f"🎰 <b>KAZINO VA MINI-O'YINLAR ZALI</b> 🎲\n\n"
        f"Mablag'ingiz: <b>{pul_bal:,} Pul</b> | 💎 <b>{almaz_bal} Almaz</b>\n\n"
        f"Bu yerda omadingizni sinab ko'rishingiz, do'stlaringiz bilan bellashishingiz yoki sovrinlar yutib olishingiz mumkin!\n\n"
        f"🎮 <b>O'yinni tanlang:</b>"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_casino_menu_keyboard())

@router.callback_query(F.data == "play_slot_fast")
async def play_slot_fast_cb(call: CallbackQuery):
    await call.answer()
    await play_slot_machine(call.message)

@router.callback_query(F.data == "play_darts_fast")
async def play_darts_fast_cb(call: CallbackQuery):
    await call.answer()
    await play_darts(call.message)

@router.callback_query(F.data == "play_dice_fast")
async def play_dice_fast_cb(call: CallbackQuery):
    await call.answer()
    await play_dice(call.message)

@router.callback_query(F.data == "duel_help_info")
async def duel_help_cb(call: CallbackQuery):
    text = (
        "⚔️ <b>DUEL JANGI QOIDALARI:</b>\n\n"
        "Guruhda yoki shaxsiyda boshqa o'yinchiga javob (reply) qilib:\n"
        "<code>/duel 500</code>\n\n"
        "buyrug'ini yuboring. Raqibingiz qabul qilsa, duel boshlanadi va g'olib barcha garovni oladi!"
    )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "marriage_info")
async def marriage_info_cb(call: CallbackQuery):
    text = (
        "💍 <b>NIKOH VA OILA TIZIMI:</b>\n\n"
        "O'z juftingizga turmush qurish taklifini bildirish uchun uning xabariga javob (reply) qilib:\n"
        "<code>/marry</code>\n\n"
        "buyrug'ini yuboring. Eslatma: Do'kondan <b>💍 Oltin Nikoh Uzugi</b> sotib olgan bo'lishingiz kerak!"
    )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "promo_code_enter")
async def promo_code_info_cb(call: CallbackQuery):
    text = (
        "🎟️ <b>PROMO-KODNI FAOLLASHTIRISH:</b>\n\n"
        "Botda promo-kodni faollashtirish uchun botga:\n"
        "<code>/promo KOD</code>\n\n"
        "deb yuboring (Masalan: <code>/promo START</code>)."
    )
    await call.message.answer(text, parse_mode="HTML")
    await call.answer()

# ==============================================================================
# 1. KAZINO SLOT MASHINASI (/slot <pul>)
# ==============================================================================
@router.message(Command("slot"))
@router.message(Command("casino"))
async def play_slot_machine(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return

    args = message.text.split() if message.text else []
    bet = 200
    if len(args) > 1 and args[1].isdigit():
        bet = max(50, int(args[1]))

    if user["pul"] < bet:
        await message.answer(f"❌ Garov tikish uchun hisobingizda kamida <b>{bet:,} Pul</b> bo'lishi kerak!\nSizda: {user['pul']:,} Pul.")
        return

    # Deduct bet
    await db.update_balance(user_id, pul_diff=-bet)

    # Roll slot animation
    dice_msg = await message.answer_dice(emoji="🎰")
    await asyncio.sleep(2.5)

    val = dice_msg.dice.value
    # Telegram slot values: 64 is Jackpot 777! 1, 22, 43 are triple icons.
    if val == 64:
        win = bet * 10
        await db.update_balance(user_id, pul_diff=win, almaz_diff=5)
        await message.reply(
            f"🎉🎰 <b>JACKPOT 777! QOYILMAQOM G'ALABA!</b> 🎰🎉\n\n"
            f"💰 <b>+{win:,} Pul</b> va 💎 <b>+5 Almaz</b> yutib oldingiz!"
        )
    elif val in (1, 22, 43):
        win = bet * 4
        await db.update_balance(user_id, pul_diff=win)
        await message.reply(
            f"🌟 <b>Ajoyib kombinatsiya!</b>\n\n"
            f"💰 <b>+{win:,} Pul</b> yutib oldingiz (4x yutuq)!"
        )
    elif val in (16, 32, 48):
        win = int(bet * 1.5)
        await db.update_balance(user_id, pul_diff=win)
        await message.reply(
            f"✨ <b>Kichik yutuq!</b>\n\n"
            f"💰 <b>+{win:,} Pul</b> qaytarildi (1.5x)!"
        )
    else:
        await message.reply(
            f"😢 <b>Omadingiz kelmadi.</b>\n"
            f"Yutqazildi: <b>{bet:,} Pul</b>. Yana bir bor urinib ko'ring!"
        )

# ==============================================================================
# 2. DARTS MINI-O'YINI (/darts <pul>)
# ==============================================================================
@router.message(Command("darts"))
async def play_darts(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return

    args = message.text.split() if message.text else []
    bet = 200
    if len(args) > 1 and args[1].isdigit():
        bet = max(50, int(args[1]))

    if user["pul"] < bet:
        await message.answer(f"❌ Mablag' yetarli emas! Sizda: {user['pul']:,} Pul.")
        return

    await db.update_balance(user_id, pul_diff=-bet)
    dice_msg = await message.answer_dice(emoji="🎯")
    await asyncio.sleep(2.5)

    val = dice_msg.dice.value
    if val == 6: # Bullseye
        win = bet * 3
        await db.update_balance(user_id, pul_diff=win)
        await message.reply(f"🎯 <b>MARKAZGA URILDI! QOYIL!</b>\n💰 <b>+{win:,} Pul</b> yutib oldingiz!")
    elif val in (4, 5):
        win = int(bet * 1.8)
        await db.update_balance(user_id, pul_diff=win)
        await message.reply(f"🎯 <b>Nishonga tegdi!</b>\n💰 <b>+{win:,} Pul</b> yutib oldingiz!")
    else:
        await message.reply(f"❌ Nishon chetidan o'tdi. Yutqazildi: <b>{bet:,} Pul</b>.")

# ==============================================================================
# 3. KUBIK MINI-O'YINI (/dice <pul>)
# ==============================================================================
@router.message(Command("dice"))
async def play_dice(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return

    args = message.text.split() if message.text else []
    bet = 200
    if len(args) > 1 and args[1].isdigit():
        bet = max(50, int(args[1]))

    if user["pul"] < bet:
        await message.answer(f"❌ Mablag' yetarli emas! Sizda: {user['pul']:,} Pul.")
        return

    await db.update_balance(user_id, pul_diff=-bet)
    dice_msg = await message.answer_dice(emoji="🎲")
    await asyncio.sleep(2.5)

    val = dice_msg.dice.value
    if val == 6:
        win = int(bet * 2.5)
        await db.update_balance(user_id, pul_diff=win)
        await message.reply(f"🎲 <b>6 TUSHDI! SUPER G'ALABA!</b>\n💰 <b>+{win:,} Pul</b> yutib oldingiz!")
    elif val in (4, 5):
        win = int(bet * 1.5)
        await db.update_balance(user_id, pul_diff=win)
        await message.reply(f"🎲 <b>G'alaba! ({val} tushdi)</b>\n💰 <b>+{win:,} Pul</b> yutib oldingiz!")
    else:
        await message.reply(f"🎲 <b>{val} tushdi.</b> Yutqazildi: <b>{bet:,} Pul</b>.")

# ==============================================================================
# 4. PROMO-KODLAR TIZIMI (/promo <kod>)
# ==============================================================================
@router.message(Command("promo"))
async def handle_promo_code(message: Message):
    args = message.text.split() if message.text else []
    if len(args) < 2:
        await message.answer("🎟️ <b>Promo-kodni faollashtirish uchun:</b>\n<code>/promo KOD</code> deb yuboring.")
        return

    code = args[1].strip()
    res = await db.use_promo_code(message.from_user.id, code)

    if not res["success"]:
        await message.answer(f"❌ {res['error']}")
        return

    p = res["promo"]
    msg = (
        f"🎉 <b>PROMO-KOD MUVAFFAQIYATLI FAOLLASHTIRILDI!</b>\n\n"
        f"🎁 <b>Sizga berildi:</b>\n"
        f"💰 <b>+{p['reward_pul']:,} Pul</b>\n"
        f"💎 <b>+{p['reward_almaz']} Almaz</b>\n"
        f"⚡ <b>+{p['reward_xp']} XP</b>\n\n"
        f"<i>Balansingiz to'ldirildi!</i>"
    )
    await message.answer(msg, parse_mode="HTML")

@router.message(Command("addpromo"))
async def handle_add_promo(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    args = message.text.split()
    if len(args) < 4:
        await message.answer("ℹ️ <b>Format:</b> <code>/addpromo KOD PUL ALMAZ [LIMIT]</code>\nMasalan: <code>/addpromo MAFIA77 1000 10 50</code>")
        return

    code = args[1].upper()
    pul = int(args[2])
    almaz = int(args[3])
    limit = int(args[4]) if len(args) > 4 else 100

    await db.create_promo_code(code, pul, almaz, xp=50, max_uses=limit)
    await message.answer(f"✅ Yangi promo-kod yaratildi:\nKod: <code>{code}</code>\nPul: <b>{pul:,}</b>, Almaz: <b>{almaz}</b>, Limit: <b>{limit}</b> ta.")

# ==============================================================================
# 5. TELEFON RAQAMNI ULASH & VERIFIKATSIYA (/phone)
# ==============================================================================
@router.message(Command("phone"))
@router.message(F.text == "📞 Telefon raqamni ulash")
async def request_phone_contact(message: Message):
    if message.chat.type != "private":
        await message.answer("⚠️ Telefon raqamni faqat botning shaxsiy xabarida ulashingiz mumkin!")
        return

    user = await db.get_user(message.from_user.id)
    if user and user.get("phone_number"):
        await message.answer(f"✅ <b>Telefon raqamingiz allaqachon ulangan:</b>\n<code>{user['phone_number']}</code>")
        return

    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Kontaktni ulash (+1,000 Pul)", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "📞 <b>HISOBNI TASDIQLASH VA SOVG'A OLISH</b>\n\n"
        "Telefon raqamingizni ulab profilingizni xavfsiz qiling va darhol **+1,000 Pul** sovg'asini oling!\n\n"
        "<i>Quyidagi tugmani bosing:</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.message(F.contact)
async def process_user_contact(message: Message):
    contact = message.contact
    if not contact:
        return

    user_id = message.from_user.id
    phone = contact.phone_number
    if not phone.startswith("+"):
        phone = "+" + phone

    user = await db.get_user(user_id)
    already_had_phone = bool(user and user.get("phone_number"))

    await db.set_user_phone(user_id, phone)

    if not already_had_phone:
        await db.update_balance(user_id, pul_diff=1000)
        from bot.keyboards import get_main_keyboard
        is_admin = user_id in ADMIN_IDS
        await message.answer(
            f"🎉 <b>TABRIKLAYMIZ! TELEFON RAQAMINGIZ ULANDI!</b>\n\n"
            f"📱 Raqam: <code>{phone}</code>\n"
            f"🎁 Sovg'a sifatida hisobingizga <b>+1,000 Pul</b> qo'shildi!",
            reply_markup=get_main_keyboard(is_admin),
            parse_mode="HTML"
        )
    else:
        from bot.keyboards import get_main_keyboard
        is_admin = user_id in ADMIN_IDS
        await message.answer(
            f"✅ <b>Telefon raqamingiz yangilandi:</b> <code>{phone}</code>",
            reply_markup=get_main_keyboard(is_admin),
            parse_mode="HTML"
        )

# ==============================================================================
# 6 & 7. OMAD SANDIG'I (LOOTBOX - /box)
# ==============================================================================
@router.message(Command("box"))
@router.message(Command("chest"))
async def open_lootbox_menu(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Bronza Sandiq (💰 500 Pul)", callback_data="open_box_bronze")],
        [InlineKeyboardButton(text="💎 Oltin Sandiq (💎 5 Almaz)", callback_data="open_box_gold")]
    ])
    await message.answer(
        "🎁 <b>OMAD SANDIQLARI (LOOTBOX)</b>\n\n"
        "Sandiqlarni ochib tasodifiy qimmatbaho artefaktlar, katta pullar, almazlar yoki VIP status yutib oling!\n\n"
        "<i>Qaysi sandiqni ochishni xohlaysiz?</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("open_box_"))
async def process_open_box(call: CallbackQuery):
    box_type = call.data.replace("open_box_", "")
    user_id = call.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return

    if box_type == "bronze":
        price = 500
        if user["pul"] < price:
            await call.answer("❌ Mablag' yetarli emas! 500 Pul kerak.", show_alert=True)
            return
        await db.update_balance(user_id, pul_diff=-price)

        # Rewards pool for bronze
        prizes = [
            ("pul", 300, "💰 300 Pul"),
            ("pul", 800, "💰 800 Pul (+300 sof foyda!)"),
            ("pul", 1500, "💰 1,500 Pul (3x yutuq!)"),
            ("almaz", 2, "💎 2 Almaz"),
            ("item", "qalqon", "🛡️ Qalqon (Bronjilet)"),
            ("item", "durbin", "🔍 Durbin")
        ]
        chosen = random.choice(prizes)
        if chosen[0] == "pul":
            await db.update_balance(user_id, pul_diff=chosen[1])
        elif chosen[0] == "almaz":
            await db.update_balance(user_id, almaz_diff=chosen[1])
        elif chosen[0] == "item":
            await db.add_inventory_item(user_id, chosen[1], 1)

        await call.answer("🎉 Sandiq ochildi!", show_alert=True)
        await call.message.edit_text(
            f"📦 <b>BRONZA SANDIQ OCHILDI!</b>\n\n"
            f"Sizga tushgan sovg'a:\n"
            f"🎁 <b>{chosen[2]}</b>!\n\n"
            f"<i>Inventar va balansingiz to'ldirildi.</i>",
            parse_mode="HTML"
        )

    elif box_type == "gold":
        price = 5
        if user["almaz"] < price:
            await call.answer("❌ Almaz yetarli emas! 5 Almaz kerak.", show_alert=True)
            return
        await db.update_balance(user_id, almaz_diff=-price)

        # Rewards pool for gold
        prizes = [
            ("almaz", 10, "💎 10 Almaz (2x yutuq!)"),
            ("almaz", 25, "💎 25 Almaz (5x JACKPOT!)"),
            ("pul", 5000, "💰 5,000 Pul"),
            ("item", "niqob", "🎭 Niqob (Soxta Shaxs)"),
            ("item", "vip_7", "👑 VIP Status (7 kunlik)"),
            ("item", "extra_vote", "🗳️ +2 Ovoz kuchi")
        ]
        chosen = random.choice(prizes)
        if chosen[0] == "almaz":
            await db.update_balance(user_id, almaz_diff=chosen[1])
        elif chosen[0] == "pul":
            await db.update_balance(user_id, pul_diff=chosen[1])
        elif chosen[0] == "item":
            if chosen[1] == "vip_7":
                import time
                new_vip = max(int(time.time()), user.get("vip_until", 0)) + (7 * 86400)
                import aiosqlite
                async with aiosqlite.connect(db.db_path) as conn:
                    await conn.execute("UPDATE users SET vip_until = ? WHERE id = ?;", (new_vip, user_id))
                    await conn.commit()
            else:
                await db.add_inventory_item(user_id, chosen[1], 1)

        await call.answer("🎉 Oltin sandiq ochildi!", show_alert=True)
        await call.message.edit_text(
            f"💎 <b>OLTIN SANDIQ OCHILDI!</b>\n\n"
            f"Sizga tushgan sovg'a:\n"
            f"🎁 <b>{chosen[2]}</b>!\n\n"
            f"<i>Tabriklaymiz!</i>",
            parse_mode="HTML"
        )

# ==============================================================================
# 8. ANONIM XABAR / MAXFIY E'TIROF (/anon <matn>)
# ==============================================================================
@router.message(Command("anon"))
async def send_anonymous_message(message: Message, bot: Bot):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("🕵️‍♂️ <b>Anonim xabar yuborish uchun:</b>\n<code>/anon <xabaringiz></code> deb yozing.")
        return

    content = args[1].strip()
    if len(content) > 300:
        await message.answer("⚠️ Xabar matni 300 ta belgidan oshmasligi kerak!")
        return

    # Delete the original message if in group to keep anonymity
    if message.chat.type != "private":
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(
            f"🕵️‍♂️ <b>GURUHGA ANONIM XABAR:</b>\n\n"
            f"<i>\"{content}\"</i>\n\n"
            f"👤 <i>Muallif shaxsi maxfiy tutildi.</i>",
            parse_mode="HTML"
        )
    else:
        await message.answer("⚠️ Anonim xabar yozish buyrug'ini o'yin guruhida yuboring!")

# ==============================================================================
# 9. GURUH REYTINGI VA STATISTIKASI (/gtop)
# ==============================================================================
@router.message(Command("gtop"))
async def show_group_stats_cmd(message: Message):
    if message.chat.type == "private":
        await message.answer("⚠️ Bu buyruq Telegram guruhlarida ishlaydi!")
        return

    stats = await db.get_group_stats(message.chat.id)
    await message.answer(
        f"📊 <b>GURUH O'YINLARI STATISTIKASI:</b>\n\n"
        f"👥 Guruh: <b>{message.chat.title}</b>\n"
        f"🎮 Jami o'ynalgan o'yinlar: <b>{stats['total_games']} ta</b>\n"
        f"👤 Qatnashgan umumiy o'yinchilar: <b>{stats['total_players']} kishi</b>\n\n"
        f"<i>Yangi o'yinni boshlash uchun /game buyrug'ini yuboring!</i>",
        parse_mode="HTML"
    )

# ==============================================================================
# 10. GURUH SOZLAMALARI VA ROLLAR (/gsettings, /roles)
# ==============================================================================
@router.message(Command("gsettings"))
async def show_group_settings(message: Message):
    from config import MIN_PLAYERS, LOBBY_TIMEOUT, NIGHT_TIMEOUT, DAY_TALK_TIMEOUT, VOTE_TIMEOUT
    await message.answer(
        f"⚙️ <b>O'YIN TIZIMI SOZLAMALARI:</b>\n\n"
        f"👥 Minimal o'yinchilar soni: <b>{MIN_PLAYERS} kishi</b>\n"
        f"⏳ Lobi yig'ilish vaqti: <b>{LOBBY_TIMEOUT} soniya</b>\n"
        f"🌑 Tun davomiyligi: <b>{NIGHT_TIMEOUT} soniya</b>\n"
        f"☀️ Kunduzgi muhokama: <b>{DAY_TALK_TIMEOUT} soniya</b>\n"
        f"⚖️ Ovoz berish vaqti: <b>{VOTE_TIMEOUT} soniya</b>\n"
        f"🔇 Tungi avto-mute: <b>Yoqilgan ✅</b>",
        parse_mode="HTML"
    )

# ==============================================================================
# 11. PUL VA ALMAZ O'TKAZISH (/pay, /otkazish, /payalmaz)
# ==============================================================================
async def extract_transfer_target_and_amount(message: Message):
    target_id = None
    target_name = ""
    amount = 0

    text = message.text or message.caption or ""
    tokens = text.split()

    # 1. First priority: reply_to_message
    if message.reply_to_message and message.reply_to_message.from_user:
        if not message.reply_to_message.from_user.is_bot:
            target_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.full_name
            # Find the first positive number anywhere in tokens
            for t in tokens:
                clean_t = t.replace(",", "").replace(".", "").replace("pul", "").replace("almaz", "").strip()
                if clean_t.isdigit() and int(clean_t) > 0:
                    amount = int(clean_t)
                    break
            return target_id, target_name, amount

    # 2. Second priority: mentions in text or entities
    if message.entities:
        for ent in message.entities:
            if ent.type == "text_mention" and ent.user:
                if not ent.user.is_bot:
                    target_id = ent.user.id
                    target_name = ent.user.full_name
                    break
            elif ent.type == "mention":
                uname = text[ent.offset:ent.offset + ent.length].replace("@", "").strip()
                u = await db.get_user_by_username(uname)
                if u:
                    target_id = u["id"]
                    target_name = u["full_name"]
                    break

    # Check for @username in tokens if not yet found
    if not target_id:
        for t in tokens:
            if t.startswith("@"):
                u = await db.get_user_by_username(t.replace("@", "").strip())
                if u:
                    target_id = u["id"]
                    target_name = u["full_name"]
                    break

    # Find the amount in tokens
    for t in tokens:
        clean_t = t.replace(",", "").replace(".", "").replace("pul", "").replace("almaz", "").strip()
        if clean_t.isdigit() and int(clean_t) > 0:
            amount = int(clean_t)
            break

    return target_id, target_name, amount

@router.message(Command("pay", "otkazish", "otkaz", "utkazish", "pulber", "givemoney", "send", "transfer", "perevod", "pul"))
@router.message(F.text.lower().startswith(("otkazish", "o'tkazish", "pul otkazish", "pul o'tkazish", "pul berish", "pay ")))
async def handle_pay(message: Message):
    target_id, target_name, amount = await extract_transfer_target_and_amount(message)

    if not target_id:
        await message.answer(
            "💸 <b>Pul o'tkazish (sovg'a qilish) uchun:</b>\n"
            "1. Foydalanuvchi xabariga javob berib (reply): <code>/otkazish 1000</code> (yoki <code>/pay 1000</code>)\n"
            "2. Yoki: <code>/otkazish @username 1000</code> deb yuboring.",
            parse_mode="HTML"
        )
        return

    if target_id == message.from_user.id:
        await message.answer("⚠️ O'zingizga pul o'tkaza olmaysiz!")
        return

    if amount <= 0:
        await message.answer("⚠️ O'tkazmoqchi bo'lgan pul miqdorini yozing!\nMasalan: <code>/otkazish 1000</code>")
        return

    res = await db.transfer_pul(message.from_user.id, target_id, amount)
    if not res["success"]:
        await message.answer(f"❌ {res['error']}")
        return

    await message.answer(
        f"🎁 <b>MUVAFFAQIYATLI O'TKAZDINGIZ!</b>\n\n"
        f"👤 <b>O'tkazuvchi:</b> {message.from_user.full_name}\n"
        f"🎯 <b>Qabul qiluvchi:</b> {target_name}\n"
        f"💰 <b>O'tkazilgan mablag':</b> {amount:,} Pul\n\n"
        f"<i>Hisoblar muvaffaqiyatli yangilandi!</i>",
        parse_mode="HTML"
    )

@router.message(Command("payalmaz", "pay_almaz", "givealmaz", "almazber", "almazotkazish", "almaz_otkazish", "almaz"))
@router.message(F.text.lower().startswith(("almaz otkazish", "almaz o'tkazish", "almaz berish", "payalmaz ")))
async def handle_pay_almaz(message: Message):
    target_id, target_name, amount = await extract_transfer_target_and_amount(message)

    if not target_id:
        await message.answer(
            "💎 <b>Almaz o'tkazish (sovg'a qilish) uchun:</b>\n"
            "1. Foydalanuvchi xabariga javob berib (reply): <code>/payalmaz 5</code>\n"
            "2. Yoki: <code>/payalmaz @username 5</code> deb yuboring.",
            parse_mode="HTML"
        )
        return

    if target_id == message.from_user.id:
        await message.answer("⚠️ O'zingizga almaz o'tkaza olmaysiz!")
        return

    if amount <= 0:
        await message.answer("⚠️ O'tkazmoqchi bo'lgan almaz miqdorini yozing!\nMasalan: <code>/payalmaz 5</code>")
        return

    res = await db.transfer_almaz(message.from_user.id, target_id, amount)
    if not res["success"]:
        await message.answer(f"❌ {res['error']}")
        return

    await message.answer(
        f"🎁 <b>MUVAFFAQIYATLI O'TKAZDINGIZ!</b>\n\n"
        f"👤 <b>O'tkazuvchi:</b> {message.from_user.full_name}\n"
        f"🎯 <b>Qabul qiluvchi:</b> {target_name}\n"
        f"💎 <b>O'tkazilgan almaz:</b> {amount:,} Almaz\n\n"
        f"<i>Hisoblar muvaffaqiyatli yangilandi!</i>",
        parse_mode="HTML"
    )

# ==============================================================================
# 12. BANK TIZIMI (/bank, /bank dep <miqdor>, /bank with <miqdor>)
# ==============================================================================
@router.message(Command("bank"))
async def handle_bank(message: Message):
    args = message.text.split()
    user = await db.get_user(message.from_user.id)
    if not user:
        return

    pul = user.get("pul", 0)
    bank_pul = user.get("bank_pul") or 0

    if len(args) == 1:
        await message.answer(
            f"🏦 <b>MAFIA SHAHAR MARKAZIY BANKI</b>\n\n"
            f"💵 <b>Cho'ntagingizdagi naqd pul:</b> {pul:,} Pul\n"
            f"🏦 <b>Bank seyfidagi pul:</b> {bank_pul:,} Pul\n\n"
            f"💡 <i>Bankdagi pullarni o'g'rilar o'g'irlay olmaydi!</i>\n\n"
            f"📥 Pul qo'yish: <code>/bank dep 1000</code>\n"
            f"📤 Pul yechish: <code>/bank with 1000</code>"
        )
        return

    action = args[1].lower()
    if len(args) < 3 or not args[2].isdigit():
        await message.answer("⚠️ Format: <code>/bank dep 1000</code> yoki <code>/bank with 1000</code>")
        return

    amount = int(args[2])
    if action in ["dep", "deposit"]:
        res = await db.bank_deposit(message.from_user.id, amount)
        if not res["success"]:
            await message.answer(f"❌ {res['error']}")
            return
        await message.answer(f"🏦 <b>Bankka qo'yildi:</b> +{amount:,} Pul!\nSeyfingizda: <b>{(bank_pul + amount):,} Pul</b>.")
    elif action in ["with", "withdraw"]:
        res = await db.bank_withdraw(message.from_user.id, amount)
        if not res["success"]:
            await message.answer(f"❌ {res['error']}")
            return
        await message.answer(f"💵 <b>Bankdan yechildi:</b> +{amount:,} Pul!\nCho'ntagingizda: <b>{(pul + amount):,} Pul</b>.")

# ==============================================================================
# 13. NIKOH VA OILA TIZIMI (/marry, /turmush, /divorce)
# ==============================================================================
async def extract_marry_target(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.is_bot:
            return "bot", "", ""
        return (
            message.reply_to_message.from_user.id,
            message.reply_to_message.from_user.full_name,
            message.reply_to_message.from_user.username or ""
        )

    if message.entities:
        for ent in message.entities:
            if ent.type == "text_mention" and ent.user:
                if ent.user.is_bot:
                    return "bot", "", ""
                return ent.user.id, ent.user.full_name, ent.user.username or ""
            elif ent.type == "mention":
                uname = (message.text or "")[ent.offset:ent.offset + ent.length].replace("@", "").strip()
                u = await db.get_user_by_username(uname)
                if u:
                    return u["id"], u["full_name"], u.get("username", "")

    tokens = (message.text or "").split()
    for t in tokens:
        if t.startswith("@"):
            u = await db.get_user_by_username(t.replace("@", "").strip())
            if u:
                return u["id"], u["full_name"], u.get("username", "")

    return None, "", ""

@router.message(Command("marry", "turmush", "nikoh", "uylanish", "uylan", "oilaviy", "svadba"))
@router.message(F.text.lower().in_(["marry", "turmush", "nikoh", "uylanish", "oilaviy", "/marry", "/turmush", "/nikoh"]))
async def handle_marry_proposal(message: Message):
    target_id, target_name, target_username = await extract_marry_target(message)

    if target_id == "bot":
        await message.answer("🤖 Bot bilan turmush qura olmaysiz!")
        return

    if not target_id:
        await message.answer(
            "💍 <b>Turmush qurish uchun:</b>\n"
            "1. Sevgan insoningizning xabariga javob berib (reply): <code>/marry</code> (yoki <code>/turmush</code>)\n"
            "2. Yoki: <code>/marry @username</code> deb yuboring!",
            parse_mode="HTML"
        )
        return

    if target_id == message.from_user.id:
        await message.answer("⚠️ O'zingizga turmushga chiqa olmaysiz!")
        return

    # Check if already married
    m1 = await db.get_marriage(message.from_user.id)
    if m1 and m1.get("spouse"):
        spouse_id = m1["spouse"].get("id")
        if spouse_id == target_id:
            await message.answer("❤️ Siz allaqachon bir-biringiz bilan oila qurgansiz! Baxtli bo'ling!")
            return
        await message.answer(
            f"💍 <b>SIZ ALLAQACHON OILALISIZ!</b>\n\n"
            f"❤️ <b>Turmush o'rtog'ingiz:</b> {m1['spouse'].get('full_name', 'Turmush o\'rtog\'i')}\n\n"
            f"<i>Yangi nikoh qurish uchun avval <code>/divorce</code> (ajrashish) deb yozing.</i>",
            parse_mode="HTML"
        )
        return

    m2 = await db.get_marriage(target_id)
    if m2 and m2.get("spouse"):
        await message.answer("⚠️ Bu inson allaqachon boshqa birov bilan oila qurgan! Avval u ajrashishi kerak.")
        return

    # Auto create users so balances and IDs are primed
    await db.get_or_create_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name or "")
    await db.get_or_create_user(target_id, target_username, target_name)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💍 Roziman (Ha)", callback_data=f"ans_marry_yes_{message.from_user.id}_{target_id}"),
            InlineKeyboardButton(text="❌ Rad etaman", callback_data=f"ans_marry_no_{message.from_user.id}_{target_id}")
        ]
    ])

    await message.answer(
        f"💖 <b>SEVGI IZHORI VA NIKOH TAKLIFI!</b> 💖\n\n"
        f"👤 <b>{message.from_user.full_name}</b> sizga, <b>{target_name}</b>ga turmush qurish taklifini bildirdi!\n\n"
        f"<i>Rozimisiz? Pastdagi tugmani bosing:</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("ans_marry_"))
async def process_marry_answer(call: CallbackQuery):
    parts = call.data.split("_")
    ans = parts[2]
    proposer_id = int(parts[3])
    target_id = int(parts[4])

    if call.from_user.id != target_id:
        await call.answer("⚠️ Bu taklif sizga yuborilmagan!", show_alert=True)
        return

    if ans == "no":
        await call.message.edit_text("💔 <b>Afsus, nikoh taklifi rad etildi.</b>", parse_mode="HTML")
        return

    proposer_u = await db.get_or_create_user(proposer_id)
    await db.get_or_create_user(target_id, call.from_user.username or "", call.from_user.full_name or "")

    inv = await db.get_inventory(proposer_id)
    has_ring = any(it["code"] == "nikoh_uzuk" and it["quantity"] > 0 for it in inv)
    ring_note = ""
    if has_ring:
        await db.consume_inventory_item(proposer_id, "nikoh_uzuk", 1)
        ring_note = "💍 <i>Oltin nikoh uzugi taqildi!</i>"
    elif proposer_u.get("pul", 0) >= 500:
        await db.update_balance(proposer_id, pul_diff=-500)
        ring_note = "💰 <i>Nikoh rasmiylashtirish uchun 500 Pul to'landi.</i>"
    else:
        ring_note = "💖 <i>Haqiqiy sevgi bebaho! Nikoh bepul rasmiylashtirildi!</i>"

    await db.marry_users(proposer_id, target_id)

    proposer = await db.get_user(proposer_id)
    p_name = proposer["full_name"] if proposer else "Kuyov"
    t_name = call.from_user.full_name

    await call.message.edit_text(
        f"🎉💍 <b>TO'Y TABRIKLARI! YANGI OILA VUJUDGA KELDI!</b> 💍🎉\n\n"
        f"🤵 <b>Kuyov:</b> {p_name}\n"
        f"👰 <b>Kelin:</b> {t_name}\n\n"
        f"{ring_note}\n"
        f"✨ <i>Ikkalangiz ham baxtli bo'ling! Birgalikda o'ynaganda qo'shimcha baxtli oila bonusi beriladi!</i>",
        parse_mode="HTML"
    )
    await call.answer("💍 Tabriklaymiz, nikoh muvaffaqiyatli tuzildi!")

@router.message(Command("divorce", "ajrashish", "taloq"))
async def handle_divorce(message: Message):
    m = await db.get_marriage(message.from_user.id)
    if not m:
        await message.answer("⚠️ Siz hali oila qurmaysiz. Turmush qurish uchun: <code>/marry</code>")
        return

    await db.divorce_users(message.from_user.id)
    await message.answer("💔 <b>Nikoh bekor qilindi. Siz endi rasman ajrashdingiz.</b>")

# ==============================================================================
# 14. CHO'NTAKKESARLIK / TALONCHILIK (/rob)
# ==============================================================================
ROB_COOLDOWNS = {}

@router.message(Command("rob"))
async def handle_robbery(message: Message):
    user_id = message.from_user.id
    now = asyncio.get_event_loop().time()

    if user_id in ROB_COOLDOWNS and (now - ROB_COOLDOWNS[user_id]) < 180:
        left = int(180 - (now - ROB_COOLDOWNS[user_id]))
        await message.answer(f"⏳ <b>Politsiya qidirmoqda!</b> Yana <b>{left} soniya</b>dan so'ng tunashga chiqa olasiz.")
        return

    target_id = None
    target_name = ""
    if message.reply_to_message and not message.reply_to_message.from_user.is_bot:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.full_name
    else:
        args = message.text.split()
        if len(args) > 1:
            u = await db.get_user_by_username(args[1])
            if u:
                target_id = u["id"]
                target_name = u["full_name"]

    if not target_id or target_id == user_id:
        await message.answer("🥷 <b>Biror kishini tunash uchun:</b>\nUning xabariga reply qilib <code>/rob</code> deb yuboring.")
        return

    target_u = await db.get_user(target_id)
    if not target_u or target_u.get("pul", 0) < 300:
        await message.answer("❌ Bu o'yinchining cho'ntagida arzirli pul yo'q!")
        return

    # Check target alarm / signalizatsiya
    t_inv = await db.get_inventory(target_id)
    has_alarm = any(it["code"] == "signalizatsiya" and it["quantity"] > 0 for it in t_inv)
    ROB_COOLDOWNS[user_id] = now

    if has_alarm:
        await db.consume_inventory_item(target_id, "signalizatsiya", 1)
        fine = 500
        await db.update_balance(user_id, pul_diff=-fine)
        await message.answer(
            f"🚨 <b>SIGNALIZATSIYA ISHLAB KETDI!</b>\n\n"
            f"{target_name}ning cho'ntagidagi xavfsizlik tizimi sizni fosh qildi!\n"
            f"Politsiya sizga <b>{fine:,} Pul</b> jarima soldi!"
        )
        return

    # 50% chance
    if random.random() < 0.5:
        stolen = random.randint(100, min(1000, int(target_u["pul"] * 0.3)))
        await db.update_balance(target_id, pul_diff=-stolen)
        await db.update_balance(user_id, pul_diff=stolen)
        await message.answer(
            f"🥷 <b>OMADLI TALONCHILIK!</b>\n\n"
            f"Siz bildirmasdan {target_name}ning cho'ntagidan <b>+{stolen:,} Pul</b> o'g'irlab qochdingiz!"
        )
    else:
        fine = 300
        await db.update_balance(user_id, pul_diff=-fine)
        await message.answer(
            f"👮‍♂️ <b>QO'LGA TUSHINGIZ!</b>\n\n"
            f"Talonchilik muvaffaqiyatsiz yakunlandi, politsiya sizni ushlab <b>{fine:,} Pul</b> jarima undirdi."
        )

# ==============================================================================
# 15. OBRO' VA KARMA TIZIMI (/rep + / /rep -)
# ==============================================================================
@router.message(Command("rep"))
@router.message(F.text.in_(["+rep", "-rep", "+1", "-1", "+REP", "-REP"]))
async def handle_reputation(message: Message):
    if not message.reply_to_message or message.reply_to_message.from_user.is_bot:
        await message.answer("⭐ <b>Obro' berish uchun:</b>\nFoydalanuvchi xabariga reply (javob) qilib <code>/rep +</code> yoki <code>+rep</code> (pasaytirish uchun <code>/rep -</code> yoki <code>-rep</code>) deb yozing.")
        return

    target_id = message.reply_to_message.from_user.id
    if target_id == message.from_user.id:
        await message.answer("⚠️ O'zingizga obro' bera olmaysiz!")
        return

    raw_text = (message.text or "").strip().lower()
    delta = 1
    if raw_text in ["-rep", "-1"] or raw_text.startswith("-") or "minus" in raw_text:
        delta = -1
    else:
        args = message.text.split()
        if len(args) > 1 and args[1] in ["-", "--", "minus"]:
            delta = -1

    res = await db.change_rep(message.from_user.id, target_id, delta)
    if not res["success"]:
        await message.answer(f"❌ {res['error']}")
        return

    sign = "+1" if delta > 0 else "-1"
    target_name = message.reply_to_message.from_user.full_name
    await message.answer(
        f"⭐ <b>OBRO' (REPUTATSIYA) O'ZGARDI!</b>\n\n"
        f"👤 {target_name}ga <b>{sign} Obro'</b> berildi!"
    )

# ==============================================================================
# 16. GARAJ VA MAFIA MASHINALARI (/garage, /givecar)
# ==============================================================================
CAR_DEFINITIONS = [
    ("mashina_rolls", "👑 Rolls-Royce Phantom ('Don Karleone')", "50% suiqasddan qochish"),
    ("mashina_porsche", "🏎️ Porsche 911 Turbo S", "40% suiqasddan qochish"),
    ("mashina_gelik", "🚙 Mercedes-Benz G63 ('Gelik')", "35% suiqasddan qochish"),
    ("mashina_bmw", "🏎️ BMW M5 F90", "30% suiqasddan qochish"),
    ("mashina_malibu", "🚔 Chevrolet Malibu 2 ('Black')", "25% suiqasddan qochish"),
    ("mashina_kaban", "🚘 Mercedes W140 ('Kaban')", "20% suiqasddan qochish"),
    ("mashina_monza", "🚗 Chevrolet Monza", "18% suiqasddan qochish"),
    ("mashina_gentra", "🚙 Chevrolet Gentra ('Qora Gentra')", "15% suiqasddan qochish"),
    ("mashina_nexia", "🚙 Daewoo Nexia 2 ('Xalqona')", "12% suiqasddan qochish"),
    ("mashina_matiz", "🚗 Daewoo Matiz ('Tezkor')", "10% suiqasddan qochish"),
]

@router.message(Command("garage", "garaj", "mashinalar", "moshinalar", "avtopark"))
@router.message(F.text.lower().in_(["garage", "garaj", "mashinalar", "moshinalar", "avtopark", "/garage", "/garaj", "/mashinalar"]))
async def show_garage(message: Message):
    inv = await db.get_inventory(message.from_user.id)
    inv_map = {it["code"]: it["quantity"] for it in inv}

    cars_txt = []
    for code, title, stat in CAR_DEFINITIONS:
        cnt = inv_map.get(code, 0)
        if cnt > 0:
            cars_txt.append(f"• <b>{title}</b> ({cnt} ta) — <i>{stat}</i>")

    if not cars_txt:
        garage_text = (
            "🚗 <b>SIZNING GARAJIYINGIZ BO'SH!</b>\n\n"
            "Sizda hali mashina yo'q. Mashinalar kechasi mafiya yoki qotil hujumidan **qochib qolish** imkonini beradi!\n\n"
            "<i>Mashinalarni 🛍️ Do'kondan xarid qilishingiz yoki do'stlaringizdan sovg'a olishingiz mumkin.</i>"
        )
    else:
        garage_text = (
            f"🚗 <b>SIZNING MAFIYA GARAJIYINGIZ:</b>\n\n" +
            "\n".join(cars_txt) +
            "\n\n✨ <i>Ushbu avtomobillar o'yinda passiv himoya sifatida avtomatik ishlaydi!</i>\n"
            "🎁 <i>Do'stingizga mashina sovg'a qilish uchun uning xabariga reply qilib <code>/givecar</code> deb yozing!</i>"
        )

    if message.chat.type in ["group", "supergroup"]:
        bot_info = await message.bot.get_me()
        bot_url = f"https://t.me/{bot_info.username}?start=garage"
        group_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Botga o'tish ➔", url=bot_url)]
        ])
        await message.reply(
            "🚗 <b>Garajingiz va mashinalaringiz ro'yxati shaxsiy lichkangizga yuborildi!</b>\n"
            "<i>Garajni ko'rish uchun pastdagi tugmani bosing:</i>",
            parse_mode="HTML",
            reply_markup=group_kb
        )
        try:
            await message.bot.send_message(message.from_user.id, garage_text, parse_mode="HTML")
        except Exception:
            pass
        return

    await message.answer(garage_text, parse_mode="HTML")

@router.message(Command("givecar", "giftcar", "moshinasovga", "mashinasovga", "avtosovga", "moshinaotkazish", "mashinaotkazish"))
@router.message(F.text.lower().startswith(("moshina sovga", "mashina sovga", "moshina otkazish", "mashina otkazish")))
async def handle_give_car(message: Message):
    target_id = None
    target_name = ""

    if message.reply_to_message and not message.reply_to_message.from_user.is_bot:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.full_name
    elif message.entities:
        for ent in message.entities:
            if ent.type == "text_mention" and ent.user:
                if not ent.user.is_bot:
                    target_id = ent.user.id
                    target_name = ent.user.full_name
                    break
            elif ent.type == "mention":
                uname = (message.text or "")[ent.offset:ent.offset + ent.length].replace("@", "").strip()
                u = await db.get_user_by_username(uname)
                if u:
                    target_id = u["id"]
                    target_name = u["full_name"]
                    break

    if not target_id:
        args = message.text.split() if message.text else []
        for a in args:
            if a.startswith("@"):
                u = await db.get_user_by_username(a.replace("@", "").strip())
                if u:
                    target_id = u["id"]
                    target_name = u["full_name"]
                    break

    if not target_id:
        await message.answer(
            "🎁 <b>Mashina sovg'a qilish uchun:</b>\n"
            "1. Foydalanuvchi xabariga javob berib (reply): <code>/givecar</code>\n"
            "2. Yoki: <code>/givecar @username</code> deb yuboring."
        )
        return

    if target_id == message.from_user.id:
        await message.answer("⚠️ O'zingizga mashina sovg'a qila olmaysiz!")
        return

    inv = await db.get_inventory(message.from_user.id)
    inv_map = {it["code"]: it for it in inv if it["code"].startswith("mashina_") and it["quantity"] > 0}

    if not inv_map:
        await message.answer("❌ <b>Sizda sovg'a qilish uchun birorta ham mashina yo'q!</b>\nAvval 🛍️ Do'kondan mashina xarid qiling.")
        return

    # Check if a specific car was named in command
    args = message.text.split()
    chosen_car_code = None
    if len(args) > 1 and not args[1].startswith("@"):
        query = args[1].lower()
        for code in inv_map:
            if query in code:
                chosen_car_code = code
                break
    elif len(args) > 2 and args[1].startswith("@"):
        query = args[2].lower()
        for code in inv_map:
            if query in code:
                chosen_car_code = code
                break

    if chosen_car_code:
        res = await db.transfer_item(message.from_user.id, target_id, chosen_car_code, 1)
        if not res["success"]:
            await message.answer(f"❌ {res['error']}")
            return

        car_name = inv_map[chosen_car_code]["name"]
        await message.answer(
            f"🎁 <b>MUVAFFAQIYATLI O'TKAZDINGIZ!</b>\n\n"
            f"👤 <b>O'tkazuvchi:</b> {message.from_user.full_name}\n"
            f"🎯 <b>Qabul qiluvchi:</b> {target_name}\n"
            f"🚘 <b>Sovg'a qilingan mashina:</b> {car_name}!\n\n"
            f"<i>Yangi egasi o'z garajida ko'rishi mumkin (/garage)!</i>",
            parse_mode="HTML"
        )
        return

    # If no specific car specified, show inline keyboard with user's available cars
    buttons = []
    for code, it in inv_map.items():
        buttons.append([
            InlineKeyboardButton(
                text=f"{it['name']} ({it['quantity']} ta)",
                callback_data=f"givecar_{target_id}_{code}"
            )
        ])

    kb = InlineKeyboardMarkup(inline_keyboard=buttons)
    await message.answer(
        f"🎁 <b>{target_name} ga qaysi mashinangizni sovg'a qilmoqchisiz?</b>\nPastdan birini tanlang:",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("givecar_"))
async def process_give_car_callback(call: CallbackQuery):
    parts = call.data.split("_")
    target_id = int(parts[1])
    car_code = "_".join(parts[2:])

    sender_id = call.from_user.id
    target_u = await db.get_user(target_id)
    target_name = target_u["full_name"] if target_u else "Foydalanuvchi"

    res = await db.transfer_item(sender_id, target_id, car_code, 1)
    if not res["success"]:
        await call.answer(f"❌ {res['error']}", show_alert=True)
        return

    item_info = await db.get_item(car_code)
    car_name = item_info["name"] if item_info else car_code

    await call.message.edit_text(
        f"🎁 <b>MUVAFFAQIYATLI O'TKAZDINGIZ!</b>\n\n"
        f"👤 <b>O'tkazuvchi:</b> {call.from_user.full_name}\n"
        f"🎯 <b>Qabul qiluvchi:</b> {target_name}\n"
        f"🚘 <b>Sovg'a qilingan mashina:</b> {car_name}!\n\n"
        f"<i>Yangi egasi o'z garajida ko'rishi mumkin (/garage)!</i>",
        parse_mode="HTML"
    )
    await call.answer("✅ Mashina muvaffaqiyatli sovg'a qilindi!")

# ==============================================================================
# 17. OMAD CHARXPALAGI (/spin)
# ==============================================================================
@router.message(Command("spin"))
async def handle_fortune_spin(message: Message):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    if not user:
        return

    import time
    now = int(time.time())
    last_bonus = user.get("last_daily_bonus", 0)
    if (now - last_bonus) < 86400:
        left_h = int((86400 - (now - last_bonus)) // 3600)
        left_m = int(((86400 - (now - last_bonus)) % 3600) // 60)
        await message.answer(f"⏳ <b>Charxpalakni kunda 1 marta aylantirish mumkin!</b>\nKeyingi urinish: <b>{left_h} soat {left_m} daqiqa</b>dan so'ng.")
        return

    rewards = [
        ("pul", 300, "💰 300 Pul"),
        ("pul", 800, "💰 800 Pul"),
        ("pul", 2000, "💰 2,000 Pul (Katta yutuq!)"),
        ("almaz", 2, "💎 2 Almaz"),
        ("almaz", 5, "💎 5 Almaz"),
        ("item", "qalqon", "🛡️ Qalqon"),
        ("item", "nikoh_uzuk", "💍 Oltin Nikoh Uzugi!")
    ]
    r = random.choice(rewards)

    if r[0] == "pul":
        await db.update_balance(user_id, pul_diff=r[1])
    elif r[0] == "almaz":
        await db.update_balance(user_id, almaz_diff=r[1])
    elif r[0] == "item":
        await db.add_inventory_item(user_id, r[1], 1)

    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("UPDATE users SET last_daily_bonus = ? WHERE id = ?;", (now, user_id))
        await conn.commit()

    msg = await message.answer("🎡 <i>Charxpalak aylanmoqda...</i>")
    await asyncio.sleep(2)
    await msg.edit_text(
        f"🎡 <b>OMAD CHARXPALAGI TO'XTADI!</b>\n\n"
        f"🎉 Sizga tushgan yutuq:\n"
        f"🎁 <b>{r[2]}</b>!\n\n"
        f"<i>Ertaga yana qaytib keling!</i>",
        parse_mode="HTML"
    )

# ==============================================================================
# 18. GURUH ADMINI UCHUN INTERAKTIV SOZLAMALAR (/settings)
# ==============================================================================
@router.message(Command("settings"))
async def interactive_group_settings(message: Message, bot: Bot):
    if message.chat.type == "private":
        await message.answer("⚙️ Bu buyruq Telegram guruhlarida ishlaydi!")
        return

    chat_id = message.chat.id
    settings = await db.get_group_settings(chat_id)

    antispam_txt = "Yoqilgan ✅" if settings.get("is_antispam") else "O'chirilgan ❌"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"☀️ Muhokama: {settings['talk_time']}s", callback_data=f"set_talk_{chat_id}"),
            InlineKeyboardButton(text=f"🌑 Tun: {settings['night_time']}s", callback_data=f"set_night_{chat_id}")
        ],
        [
            InlineKeyboardButton(text=f"⚖️ Ovoz: {settings['vote_time']}s", callback_data=f"set_vote_{chat_id}"),
            InlineKeyboardButton(text=f"🛡️ Antispam: {antispam_txt}", callback_data=f"set_spam_{chat_id}")
        ]
    ])

    await message.answer(
        f"⚙️ <b>GURUH MAFIA SOZLAMALARI:</b>\n\n"
        f"Guruh: <b>{message.chat.title}</b>\n\n"
        f"<i>O'zgartirish uchun kerakli tugmani bosing:</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("set_"))
async def toggle_setting_callback(call: CallbackQuery):
    parts = call.data.split("_")
    action = parts[1]
    chat_id = int(parts[2])

    settings = await db.get_group_settings(chat_id)

    if action == "talk":
        new_val = 30 if settings["talk_time"] == 60 else (60 if settings["talk_time"] == 40 else 40)
        await db.update_group_settings(chat_id, talk_time=new_val)
    elif action == "night":
        new_val = 25 if settings["night_time"] == 45 else (45 if settings["night_time"] == 35 else 35)
        await db.update_group_settings(chat_id, night_time=new_val)
    elif action == "vote":
        new_val = 25 if settings["vote_time"] == 45 else (45 if settings["vote_time"] == 35 else 35)
        await db.update_group_settings(chat_id, vote_time=new_val)
    elif action == "spam":
        new_val = 0 if settings["is_antispam"] else 1
        await db.update_group_settings(chat_id, is_antispam=new_val)

    settings = await db.get_group_settings(chat_id)
    antispam_txt = "Yoqilgan ✅" if settings.get("is_antispam") else "O'chirilgan ❌"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"☀️ Muhokama: {settings['talk_time']}s", callback_data=f"set_talk_{chat_id}"),
            InlineKeyboardButton(text=f"🌑 Tun: {settings['night_time']}s", callback_data=f"set_night_{chat_id}")
        ],
        [
            InlineKeyboardButton(text=f"⚖️ Ovoz: {settings['vote_time']}s", callback_data=f"set_vote_{chat_id}"),
            InlineKeyboardButton(text=f"🛡️ Antispam: {antispam_txt}", callback_data=f"set_spam_{chat_id}")
        ]
    ])

    await call.message.edit_reply_markup(reply_markup=kb)
    await call.answer("✅ Sozlama yangilandi!")

