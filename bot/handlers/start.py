import time
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command

from database.db import db
from bot.keyboards import get_main_keyboard, get_profile_keyboard, get_shop_menu_keyboard
from game.roles import ROLES

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or ""

    # Check deep join
    args = message.text.split() if message.text else []
    if len(args) > 1 and args[1].startswith("join_"):
        try:
            raw_id = args[1].replace("join_", "")
            target_chat_id = int(raw_id)
            from game.engine import game_manager
            from bot.keyboards import get_lobby_keyboard
            from bot.handlers.group_game import format_lobby_text

            u = await db.get_or_create_user(user_id, username, full_name)
            if u.get("is_banned"):
                await message.answer("🚫 <b>Siz botdan bloklangansiz va o'yinda ishtirok eta olmaysiz!</b>")
                return

            room = game_manager.get_room(target_chat_id)
            if not room and target_chat_id > 0:
                room = game_manager.get_room(-target_chat_id)
                if not room:
                    try:
                        room = game_manager.get_room(int(f"-100{target_chat_id}"))
                    except Exception:
                        pass
            if not room and target_chat_id < 0:
                room = game_manager.get_room(abs(target_chat_id))

            if room and room.state == "LOBBY":
                group_url = await room.get_group_link()
                dm_buttons = [
                    [InlineKeyboardButton(text="🔵 Guruhga qaytish ➔", url=group_url)]
                ]
                if user_id == room.creator_id or user_id in [8055412146]:
                    dm_buttons.insert(0, [
                        InlineKeyboardButton(text="🚀 O'yinni boshlash", callback_data=f"forcestart_{room.chat_id}"),
                        InlineKeyboardButton(text="🤖 +Bot qo'shish", callback_data=f"addbot_{room.chat_id}")
                    ])
                group_kb = InlineKeyboardMarkup(inline_keyboard=dm_buttons)

                if user_id in room.players:
                    msg = (
                        "ℹ️ <b>Siz allaqachon ushbu o'yinga qo'shilgansiz!</b>\n\n"
                        "O'yin boshlanishini guruhda kuting."
                    )
                    if user_id == room.creator_id:
                        msg += "\n\n👑 <b>Siz o'yin tashkilotchisisiz!</b> O'yinni boshlash uchun pastdagi tugmani bosing:"
                    await message.answer(msg, reply_markup=group_kb, parse_mode="HTML")
                    return

                added = room.add_player(user_id, full_name, username)
                if added:
                    msg = (
                        "✅ <b>Muvaffaqiyatli qo'shildingiz!</b>\n\n"
                        "Siz o'yin ro'yxatiga kiritildingiz. O'yin boshlanganda maxfiy rolingiz shu yerga yuboriladi.\n"
                    )
                    if user_id == room.creator_id:
                        msg += "\n👑 <b>Siz o'yin tashkilotchisisiz!</b> O'yinchilar to'plangach, pastdagi <b>'🚀 O'yinni boshlash'</b> tugmasini bosing:"
                    else:
                        msg += "Guruhga qaytib, o'yin boshlanishini kuting!"

                    await message.answer(msg, reply_markup=group_kb, parse_mode="HTML")
                    try:
                        if room.lobby_message_id:
                            await room.bot.edit_message_text(
                                format_lobby_text(room),
                                chat_id=room.chat_id,
                                message_id=room.lobby_message_id,
                                reply_markup=get_lobby_keyboard(room.chat_id),
                                parse_mode="HTML"
                            )
                    except Exception as e:
                        print(f"[Edit lobby error]: {e}")
                    return
            else:
                await message.answer(
                    "⚠️ <b>Bu o'yin allaqachon boshlangan yoki yakunlangan!</b>\n\n"
                    "Yangi o'yinga qo'shilish uchun guruhda /game yuboring.",
                    parse_mode="HTML"
                )
                return
        except Exception as e:
            print(f"[Deep join error]: {e}")

    # Check referral
    referred_by = 0
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            ref_id = int(args[1].replace("ref_", ""))
            if ref_id != user_id:
                referred_by = ref_id
        except ValueError:
            pass

    user = await db.get_or_create_user(user_id, username, full_name, referred_by)

    # Check clan invite
    if len(args) > 1 and args[1].startswith("clan_"):
        try:
            raw_clan_id = int(args[1].replace("clan_", ""))
            target_clan = await db.get_clan(raw_clan_id)
            if not target_clan:
                await message.answer("❌ <b>Bunday klan topilmadi yoki u allaqachon tarqatilgan!</b>", parse_mode="HTML")
            else:
                user_clan = await db.get_user_clan(user_id)
                if user_clan:
                    if user_clan["id"] == raw_clan_id:
                        await message.answer(
                            f"ℹ️ <b>Siz allaqachon [{target_clan['tag']}] {target_clan['name']} klanining a'zosisiz!</b>",
                            parse_mode="HTML"
                        )
                    else:
                        await message.answer(
                            f"⚠️ <b>Siz allaqachon boshqa klan ([{user_clan['tag']}] {user_clan['name']}) a'zosisiz!</b>\n\n"
                            f"Yangi klanga qo'shilish uchun avval amaldagi klaningizdan chiqishingiz kerak.",
                            parse_mode="HTML"
                        )
                else:
                    success = await db.join_clan(user_id, raw_clan_id)
                    if success:
                        await message.answer(
                            f"🎉 <b>TABRIKLAYMIZ!</b> 🏰\n\n"
                            f"Siz muvaffaqiyatli <b>[{target_clan['tag']}] {target_clan['name']}</b> klaniga a'zo bo'ldingiz!\n"
                            f"Klaningiz bilan birgalikda eng cho'qqiga chiqing! 🔥",
                            parse_mode="HTML"
                        )
                        # Notify clan owner
                        try:
                            if target_clan.get("owner_id") and target_clan["owner_id"] != user_id:
                                await message.bot.send_message(
                                    target_clan["owner_id"],
                                    f"👥 <b>Klaningizga yangi a'zo qo'shildi!</b>\n\n"
                                    f"👤 Yangi a'zo: <b>{full_name}</b> (@{username})\n"
                                    f"🏰 Klaningiz qudrati oshmoqda! 🔥",
                                    parse_mode="HTML"
                                )
                        except Exception as e:
                            print(f"[Clan notify owner error]: {e}")
                    else:
                        await message.answer("❌ Klanga qo'shilishda xatolik yuz berdi.", parse_mode="HTML")
        except Exception as e:
            print(f"[Clan invite deep link error]: {e}")

    # If new user and has referrer, reward referrer
    if referred_by and user.get("created_at") and user.get("referred_by") == referred_by:
        await db.update_balance(referred_by, pul_diff=500, almaz_diff=2)
        try:
            await message.bot.send_message(
                referred_by,
                f"🤝 <b>Yangi do'st taklif qilindi!</b>\n"
                f"Sizning referal havolangiz orqali <b>{full_name}</b> botga qo'shildi!\n"
                f"🎁 Sizga <b>500 💰 Pul</b> va <b>2 💎 Almaz</b> berildi!"
            )
        except Exception:
            pass

    is_admin = bool(user.get("is_admin", 0))

    welcome_text = (
        f"👋 <b>Assalomu alaykum, {full_name}!</b>\n\n"
        f"🎭 <b>Universal Mafia Boti</b>ga xush kelibsiz!\n\n"
        f"Bu yerda siz do'stlaringiz bilan qizg'in va interaktiv Mafiya o'yinlarini o'ynashingiz, "
        f"darajangizni ko'tarib 💰 Pul va 💎 Almazlar yutib olishingiz mumkin!\n\n"
        f"🎮 O'yinni boshlash uchun botni Telegram guruhingizga qo'shing va <b>/game</b> buyrug'ini yuboring.\n\n"
        f"<i>Quyidagi menyu orqali profilingiz, do'kon va xizmatlardan foydalanishingiz mumkin:</i>"
    )
    await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_keyboard(is_admin))

@router.message(F.text.contains("Profil & Balans"))
@router.message(Command("profile"))
async def show_profile(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or ""
    )
    if user.get("is_banned"):
        await message.answer("🚫 <b>Sizning hisobingiz bloklangan!</b>")
        return

    vip_str = "Yo'q"
    if user.get("vip_until", 0) > time.time():
        rem_days = max(1, int((user["vip_until"] - time.time()) / 86400))
        vip_str = f"👑 Faol ({rem_days} kun qoldi)"

    xp_needed = user["level"] * 150

    spouse_str = "Bo'ydoq"
    marriage = await db.get_marriage(user["id"])
    if marriage and marriage.get("spouse"):
        spouse_str = f"💍 {marriage['spouse']['full_name']}"

    bank_pul = user.get("bank_pul") or 0
    rep = user.get("rep") or 0

    prof_text = (
        f"🎩 <b>MAFIA SHAXSIY PROFILI</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Ism:</b> <b>{user['full_name']}</b>\n"
        f"🆔 <b>ID:</b> <code>{user['id']}</code>\n"
        f"👑 <b>VIP Maqom:</b> <b>{vip_str}</b>\n"
        f"💍 <b>Oila:</b> <b>{spouse_str}</b>\n\n"
        f"🎖 <b>Daraja:</b> <b>{user['level']}-bosqich</b>\n"
        f"⚡ <b>Tajriba (XP):</b> <b>{user['xp']:,}</b> / {xp_needed:,} XP\n"
        f"⭐ <b>Obro' (Rep):</b> <b>{rep}</b> ball\n\n"
        f"💰 <b>MABLAG'LAR:</b>\n"
        f"  💵 Cho'ntakda: <b>{user['pul']:,} Pul</b>\n"
        f"  🏦 Bank hisobida: <b>{bank_pul:,} Pul</b>\n"
        f"  💎 Olmoslar: <b>{user['almaz']:,} ta</b>\n\n"
        f"🎲 <b>O'YIN STATISTIKASI:</b>\n"
        f"  ⚔️ Jami janglar: <b>{user['games_played']} ta</b>\n"
        f"  🏆 G'alabalar: <b>{user['games_won']} ta</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <i>Pastdagi tugmalar orqali inventaringiz va do'konga o'ting:</i>"
    )
    await message.answer(prof_text, parse_mode="HTML", reply_markup=get_profile_keyboard())

@router.callback_query(F.data == "my_inventory")
async def show_inventory_cb(call: CallbackQuery):
    user_id = call.from_user.id
    inv = await db.get_inventory(user_id)
    if not inv:
        await call.message.answer("🎒 <b>Sizning inventaringiz bo'sh!</b>\nDo'kondan buyumlar sotib oling.")
        await call.answer()
        return

    txt = "🎒 <b>SIZNING INVENTARINGIZ:</b>\n\n"
    for it in inv:
        txt += f"{it['icon']} <b>{it['name']}</b>: {it['quantity']} ta\n   <i>{it['description']}</i>\n\n"
    txt += "<i>Buyumlar o'yin boshlanganda yoki o'yin davomida avtomatik ishlatiladi.</i>"
    await call.message.answer(txt, parse_mode="HTML")
    await call.answer()

@router.message(F.text.contains("Kunlik bonus"))
@router.message(Command("bonus"))
async def daily_bonus(message: Message):
    user = await db.get_or_create_user(message.from_user.id)
    now = int(time.time())
    last_bonus = user.get("last_daily_bonus", 0)

    # 24 hours cooldown
    if now - last_bonus < 86400:
        remaining_hours = int((86400 - (now - last_bonus)) / 3600)
        remaining_mins = int(((86400 - (now - last_bonus)) % 3600) / 60)
        await message.answer(
            f"⏳ <b>Kunlik bonusni allaqachon olgansiz!</b>\n"
            f"Keyingi bonus <b>{remaining_hours} soat {remaining_mins} daqiqa</b>dan so'ng beriladi."
        )
        return

    # Random prize: 500-1500 pul, 1-3 almaz
    won_pul = random.choice([500, 750, 1000, 1500])
    won_almaz = random.choice([1, 2, 3])

    await db.update_balance(user["id"], pul_diff=won_pul, almaz_diff=won_almaz)
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("UPDATE users SET last_daily_bonus = ? WHERE id = ?;", (now, user["id"]))
        await conn.commit()

    await message.answer(
        f"🎰 <b>OMAD G'ILDIRAGI AYLANDI!</b> 🎰\n\n"
        f"Tabriklaymiz, sizning bugungi yutug'ingiz:\n"
        f"💰 <b>+{won_pul:,} Pul</b>\n"
        f"💎 <b>+{won_almaz} Almaz</b>\n\n"
        f"<i>Ertaga yana kiring va yangi sovg'alarga ega bo'ling!</i>"
    )

@router.message(F.text.contains("Reyting & Top"))
@router.message(Command("top"))
async def show_leaderboard(message: Message):
    top_winners = await db.get_leaderboard("games_won", 10)
    top_levels = await db.get_leaderboard("level", 5)

    text = "🏆 <b>ENG KUCHLI O'YINCHILAR TOP REYTINGI</b> 🏆\n\n"
    text += "🥇 <b>Eng ko'p g'alaba qozonganlar:</b>\n"
    for i, u in enumerate(top_winners, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} <b>{u['full_name']}</b> — {u['games_won']} ta g'alaba ({u['level']}-daraja)\n"

    text += "\n🎖 <b>Eng yuqori darajadagilar:</b>\n"
    for i, u in enumerate(top_levels, 1):
        text += f"⭐ {i}. <b>{u['full_name']}</b> — {u['level']}-daraja ({u['xp']} XP)\n"

    text += "\n<i>Har hafta eng yaxshi o'yinchilarga qimmatbaho almaz sovg'alari beriladi!</i>"
    await message.answer(text, parse_mode="HTML")

@router.message(F.text.contains("Do'stlarni taklif"))
@router.message(Command("ref"))
async def referral_link(message: Message):
    bot_info = await message.bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{message.from_user.id}"

    text = (
        f"🤝 <b>DO'STLARNI TAKLIF QILISH DASTURI</b>\n\n"
        f"Har bir taklif qilgan do'stingiz uchun sizga:\n"
        f"💰 <b>500 Pul</b> va 💎 <b>2 Almaz</b> beriladi!\n\n"
        f"🔗 <b>Sizning shaxsiy referal havolangiz:</b>\n"
        f"<code>{ref_link}</code>\n\n"
        f"<i>Ushbu havolani do'stlaringizga va guruhlarga ulashing!</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text.contains("O'yin qoidalari"))
@router.message(Command("roles"))
async def game_roles_help(message: Message):
    text = "📖 <b>O'YINNING BARCHA AKTIV ROLLARI VA QOIDALARI:</b>\n\n"
    for code, r in ROLES.items():
        text += f"{r.emoji} <b>{r.name}</b> ({r.team.value.upper()}):\n"
        text += f"   <i>{r.description}</i>\n\n"

    text += (
        "💡 <b>Eslatma:</b> Botda zerikarli tinch aholi roli yo'q! "
        "Har bir o'yinchi maxsus qobiliyatli va kuchli rolga ega bo'ladi."
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("help", "commands", "komandalar", "buyruqlar"))
async def show_all_commands(message: Message):
    text = (
        "📜 <b>MAFIA BOT — BARCHA BUYRUQLAR RO'YXATI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎮 <b>O'YIN BUYRUQLARI (Guruhda):</b>\n"
        "  • <code>/game</code> yoki <code>/mafia</code> — Guruhda yangi o'yin ro'yxatdan o'tishini ochish\n"
        "  • <code>/boshlash</code> yoki <code>/startgame</code> — O'yinni darhol boshlash (kamida 3 kishi)\n"
        "  • <code>/addbot</code> — O'yinga virtual AI bot qo'shish\n"
        "  • <code>/stop</code> — O'yinni to'xtatish (admin/tashkilotchi)\n"
        "  • <code>/roles</code> — Barcha qahramonlar va ularning vazifalari\n\n"
        "💰 <b>MOLIYA VA SOVG'ALAR:</b>\n"
        "  • <code>/pay @user summa</code> — Do'stingizga naqd pul o'tkazish\n"
        "  • <code>/payalmaz @user miqdor</code> — Do'stingizga olmos o'tkazish\n"
        "  • <code>/bank depozit summa</code> — Pulni bankka qo'yish (xavfsiz saqlash)\n"
        "  • <code>/rob @user</code> — Boshqa o'yinchidan pul o'g'irlashga urinish\n"
        "  • <code>/rep +</code> yoki <code>/rep -</code> — O'yinchiga obro' (reputatsiya) berish/olish\n\n"
        "🚗 <b>GARAJ VA AVTOMOBILLAR:</b>\n"
        "  • <code>/garage</code> yoki <code>/mashinalar</code> — Garajingizdagi avtomobillarni ko'rish\n"
        "  • <code>/givecar @user</code> — Do'stingizga avtomobil sovg'a qilish\n\n"
        "💍 <b>OILA VA NIKOH:</b>\n"
        "  • <code>/marry</code> — Xabarga reply qilib, turmush qurish taklif qilish\n"
        "  • <code>/divorce</code> — Nikohni bekor qilish (ajrashish)\n\n"
        "🎰 <b>KAZINO VA O'YINLAR:</b>\n"
        "  • <code>/games</code> — Kazino zali asosiy menyusi\n"
        "  • <code>/slot summa</code> — Slot mashinasini aylantirish\n"
        "  • <code>/darts summa</code> — Darts musobaqasi\n"
        "  • <code>/dice summa</code> — Omadli kubik tashlash\n"
        "  • <code>/spin</code> — Omad charxpalagini aylantirish\n"
        "  • <code>/box</code> — Qimmatbaho sandiqlarni ochish (Lootbox)\n"
        "  • <code>/duel @user summa</code> — O'yinchi bilan 1v1 duel jangi\n\n"
        "🏰 <b>KLANLAR VA REYTING:</b>\n"
        "  • <code>/clans</code> — Klanlar ro'yxati va boshqaruvi\n"
        "  • <code>/top</code> — Eng kuchli mafiozlar reytingi\n"
        "  • <code>/gtop</code> — Guruh statistikasi\n"
        "  • <code>/ref</code> — Shaxsiy referal havolangiz (do'stlarni chaqirib pul ishlash)\n"
        "  • <code>/bonus</code> — Kunlik bepul bonusni olish\n\n"
        "⚙️ <b>SOZLAMALAR:</b>\n"
        "  • <code>/settings</code> — Guruhning vaqt va qoidalarini sozlash\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 <i>Guruhda o'yin boshlash uchun: <code>/game</code> buyrug'ini yuboring!</i>"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(F.text == "➕ Botni guruhga qo'shish")
async def add_to_group(message: Message):
    bot_info = await message.bot.get_me()
    add_url = f"https://t.me/{bot_info.username}?startgroup=true"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Guruhga qo'shish", url=add_url)]
    ])
    await message.answer(
        "👥 <b>Botni o'z guruhingizga qo'shing va do'stlaringiz bilan birga o'ynang!</b>\n\n"
        "Guruhga qo'shgach, botga admin huquqini bering va <b>/game</b> buyrug'ini yuboring.",
        reply_markup=kb
    )
