import time
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command

from database.db import db
from bot.keyboards import get_main_keyboard, get_profile_keyboard, get_shop_menu_keyboard, get_language_keyboard
from bot.locales import get_text, LANGUAGES
from game.roles import ROLES

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    full_name = message.from_user.full_name or ""

    args = message.text.split() if message.text else []

    # Check direct profile view deep link
    if len(args) > 1 and args[1] == "profile":
        u = await db.get_or_create_user(user_id, username, full_name)
        full_card = await build_full_profile_card(u)
        await message.answer(full_card, parse_mode="HTML", reply_markup=get_profile_keyboard())
        return
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

    # Handle deep link shortcuts
    if len(args) > 1:
        param = args[1].lower()
        if param == "profile":
            full_card = await build_full_profile_card(user)
            await message.answer(full_card, parse_mode="HTML", reply_markup=get_profile_keyboard())
            return
        elif param == "shop":
            from bot.handlers.shop import show_shop_menu
            await show_shop_menu(message)
            return
        elif param == "garage":
            from bot.handlers.extra_features import show_garage
            await show_garage(message)
            return
        elif param == "inventory":
            inv = await db.get_inventory(user_id)
            if not inv:
                await message.answer("🎒 <b>Sizning inventaringiz bo'sh!</b>\nDo'kondan buyumlar sotib oling.")
            else:
                txt = "🎒 <b>SIZNING INVENTARINGIZ:</b>\n\n"
                for it in inv:
                    txt += f"{it['icon']} <b>{it['name']}</b>: {it['quantity']} ta\n   <i>{it['description']}</i>\n\n"
                txt += "<i>Buyumlar o'yin boshlanganda yoki o'yin davomida avtomatik ishlatiladi.</i>"
                await message.answer(txt, parse_mode="HTML")
            return
        elif param == "games":
            from bot.handlers.extra_features import show_casino_menu
            await show_casino_menu(message)
            return
        elif param == "stars":
            from bot.handlers.stars_pay import show_stars_almaz_menu
            await show_stars_almaz_menu(message)
            return
        elif param == "card":
            from bot.handlers.card_pay import show_card_pay_menu
            await show_card_pay_menu(message)
            return
        elif param == "lang":
            await choose_language(message)
            return
        elif param == "box":
            from bot.handlers.extra_features import open_lootbox_menu
            await open_lootbox_menu(message)
            return
        elif param == "quests":
            from bot.handlers.quests_achievements import show_daily_quests
            await show_daily_quests(message)
            return
        elif param == "achievements":
            from bot.handlers.quests_achievements import show_achievements
            await show_achievements(message)
            return

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

async def build_full_profile_card(user: dict) -> str:
    user_id = user["id"]
    inv = await db.get_inventory(user_id)
    cars = [it for it in inv if it["code"].startswith("mashina_") and it["quantity"] > 0]
    items = [it for it in inv if not it["code"].startswith("mashina_") and it["quantity"] > 0]

    spouse_str = "Bo'ydoq"
    marriage = await db.get_marriage(user_id)
    if marriage and marriage.get("spouse"):
        spouse_str = f"💍 {marriage['spouse']['full_name']}"

    vip_str = "Yo'q"
    if user.get("vip_until", 0) > time.time():
        rem_days = max(1, int((user["vip_until"] - time.time()) / 86400))
        vip_str = f"👑 Faol ({rem_days} kun qoldi)"

    xp_needed = user["level"] * 150
    rep = user.get("rep") or 0
    bank_pul = user.get("bank_pul") or 0
    custom_title = user.get("custom_title") or "Oddiy fuqaro"

    if cars:
        car_names = ", ".join([f"{c['name']} ({c['quantity']}x)" for c in cars[:3]])
        cars_text = f"<b>{len(cars)} ta mashina</b> ({car_names})"
    else:
        cars_text = "<i>Yo'q (Garaj bo'sh)</i>"

    if items:
        item_names = ", ".join([f"{it['icon']} {it['name']} ({it['quantity']})" for it in items[:4]])
        items_text = f"<b>{len(items)} xil</b> ({item_names})"
    else:
        items_text = "<i>Inventar bo'sh</i>"

    winrate = round((user['games_won'] / user['games_played'] * 100), 1) if user['games_played'] > 0 else 0

    return (
        f"🎩 <b>MAFIA SHAXSIY PROFILI — TO'LIQ HISOBOT</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Ism:</b> <b>{user['full_name']}</b>\n"
        f"🆔 <b>ID:</b> <code>{user['id']}</code>\n"
        f"🎖 <b>Maqom:</b> <b>{custom_title}</b>\n"
        f"👑 <b>VIP Maqom:</b> <b>{vip_str}</b>\n"
        f"💍 <b>Oila / Jufti:</b> <b>{spouse_str}</b>\n\n"
        f"⭐ <b>Daraja:</b> <b>{user['level']}-bosqich</b>\n"
        f"⚡ <b>Tajriba (XP):</b> <b>{user['xp']:,}</b> / {xp_needed:,} XP\n"
        f"🌟 <b>Obro' (Rep):</b> <b>{rep}</b> ball\n\n"
        f"💰 <b>MABLAG'LAR:</b>\n"
        f"  💵 Cho'ntakda: <b>{user['pul']:,} Pul</b>\n"
        f"  🏦 Bank hisobida: <b>{bank_pul:,} Pul</b>\n"
        f"  💎 Olmoslar: <b>{user['almaz']:,} ta</b>\n\n"
        f"🚗 <b>MAFIA GARAJI:</b>\n"
        f"  🚘 {cars_text}\n\n"
        f"🎒 <b>INVENTAR:</b>\n"
        f"  📦 {items_text}\n\n"
        f"📊 <b>O'YIN STATISTIKASI:</b>\n"
        f"  ⚔️ Jami janglar: <b>{user['games_played']} ta</b>\n"
        f"  🏆 G'alabalar: <b>{user['games_won']} ta</b> (Winrate: <b>{winrate}%</b>)\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 <i>Pastdagi tugmalar orqali inventaringiz, garajingiz va do'konga o'ting:</i>"
    )

@router.message(F.text.contains("Profil & Balans"))
@router.message(Command("profile", "balans", "balance", "pulim"))
@router.message(F.text.lower().in_(["balans", "profil", "pulim", "hisob", "profile", "balance"]))
async def show_profile(message: Message):
    user = await db.get_or_create_user(
        message.from_user.id,
        message.from_user.username or "",
        message.from_user.full_name or ""
    )
    if user.get("is_banned"):
        await message.answer("🚫 <b>Sizning hisobingiz bloklangan!</b>")
        return

    marriage = await db.get_marriage(user["id"])
    spouse_str = f"💍 {marriage['spouse']['full_name']}" if (marriage and marriage.get("spouse")) else "Bo'ydoq"

    if message.chat.type in ["group", "supergroup"]:
        bot_info = await message.bot.get_me()
        bot_url = f"https://t.me/{bot_info.username}?start=profile"
        group_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Botga o'tish ➔", url=bot_url)]
        ])
        group_text = (
            f"👤 <b>O'YINCHI MA'LUMOTI</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 <b>ID:</b> <code>{user['id']}</code>\n"
            f"👤 <b>Ism:</b> <b>{user['full_name']}</b>\n"
            f"💰 <b>Pul:</b> <b>{user['pul']:,} Pul</b>\n"
            f"💎 <b>Almaz:</b> <b>{user['almaz']:,} ta</b>\n"
            f"💍 <b>Parasi:</b> <b>{spouse_str}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📩 <i>Qolgan barcha ma'lumotlar bot lichkasiga yuborildi!</i>"
        )
        await message.reply(group_text, parse_mode="HTML", reply_markup=group_kb)

        # Also send full card to DM!
        try:
            full_card = await build_full_profile_card(user)
            await message.bot.send_message(user["id"], full_card, parse_mode="HTML", reply_markup=get_profile_keyboard())
        except Exception:
            pass
        return

    # In DM (private chat): show full card
    full_card = await build_full_profile_card(user)
    await message.answer(full_card, parse_mode="HTML", reply_markup=get_profile_keyboard())

@router.message(Command("inventory", "inventar", "narsalar", "items", "sumka"))
async def cmd_inventory_group(message: Message):
    bot_info = await message.bot.get_me()
    bot_url = f"https://t.me/{bot_info.username}?start=inventory"
    if message.chat.type in ["group", "supergroup"]:
        group_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🤖 Botga o'tish ➔", url=bot_url)]
        ])
        await message.reply(
            "🎒 <b>Inventaringiz shaxsiy lichkangizga yuborildi!</b>\n"
            "<i>Inventarni ko'rish uchun pastdagi tugmani bosing:</i>",
            parse_mode="HTML",
            reply_markup=group_kb
        )
        try:
            inv = await db.get_inventory(message.from_user.id)
            if not inv:
                dm_txt = "🎒 <b>Sizning inventaringiz bo'sh!</b>\nDo'kondan buyumlar sotib oling."
            else:
                dm_txt = "🎒 <b>SIZNING INVENTARINGIZ:</b>\n\n"
                for it in inv:
                    dm_txt += f"{it['icon']} <b>{it['name']}</b>: {it['quantity']} ta\n   <i>{it['description']}</i>\n\n"
                dm_txt += "<i>Buyumlar o'yin boshlanganda yoki o'yin davomida avtomatik ishlatiladi.</i>"
            await message.bot.send_message(message.from_user.id, dm_txt, parse_mode="HTML")
        except Exception:
            pass
        return

    # In DM:
    inv = await db.get_inventory(message.from_user.id)
    if not inv:
        await message.answer("🎒 <b>Sizning inventaringiz bo'sh!</b>\nDo'kondan buyumlar sotib oling.")
        return
    txt = "🎒 <b>SIZNING INVENTARINGIZ:</b>\n\n"
    for it in inv:
        txt += f"{it['icon']} <b>{it['name']}</b>: {it['quantity']} ta\n   <i>{it['description']}</i>\n\n"
    txt += "<i>Buyumlar o'yin boshlanganda yoki o'yin davomida avtomatik ishlatiladi.</i>"
    await message.answer(txt, parse_mode="HTML")

@router.message(Command("lang", "language", "til"))
@router.message(F.text.contains("Tilni tanlash"))
@router.callback_query(F.data == "open_lang_select")
async def choose_language(event: Message | CallbackQuery):
    text = (
        "🌐 <b>Iltimos, o'zingizga qulay tilni tanlang:</b>\n"
        "<i>Пожалуйста, выберите язык / Please select your preferred language:</i>"
    )
    kb = get_language_keyboard()
    is_cb = isinstance(event, CallbackQuery)
    chat_type = event.message.chat.type if is_cb else event.chat.type
    bot = event.bot

    if chat_type in ["group", "supergroup"]:
        if not is_cb:
            bot_info = await bot.get_me()
            bot_url = f"https://t.me/{bot_info.username}?start=lang"
            group_kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🤖 Botga o'tish ➔", url=bot_url)]
            ])
            await event.reply("🌐 <b>Tilni tanlash menyusi bot lichkasiga yuborildi!</b>", parse_mode="HTML", reply_markup=group_kb)
        try:
            await bot.send_message(event.from_user.id, text, parse_mode="HTML", reply_markup=kb)
            if is_cb:
                await event.answer("🌐 Til tanlash menyusi shaxsiy lichkangizga yuborildi!", show_alert=False)
        except Exception:
            if is_cb:
                bot_info = await bot.get_me()
                await event.answer(f"⚠️ Avval @{bot_info.username} ga kirib Start bosing!", show_alert=True)
        return

    if is_cb:
        try:
            await event.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        except Exception:
            await event.message.answer(text, parse_mode="HTML", reply_markup=kb)
        await event.answer()
    else:
        await event.answer(text, parse_mode="HTML", reply_markup=kb)

@router.callback_query(F.data.startswith("set_lang_"))
async def set_lang_callback(call: CallbackQuery):
    lang_code = call.data.replace("set_lang_", "")
    await db.set_user_language(call.from_user.id, lang_code)
    u = await db.get_user(call.from_user.id)
    is_admin = bool(u.get("is_admin", 0)) if u else False

    msg = get_text("lang_selected", lang_code)
    if call.message.chat.type in ["group", "supergroup"]:
        try:
            await call.bot.send_message(
                call.from_user.id,
                f"{msg}\n✅ {LANGUAGES.get(lang_code, 'O\'zbekcha')}",
                reply_markup=get_main_keyboard(is_admin, lang=lang_code),
                parse_mode="HTML"
            )
            await call.answer("✅ Til o'zgartirildi!", show_alert=False)
        except Exception:
            await call.answer("✅ Til o'zgartirildi!", show_alert=False)
        return

    await call.message.edit_text(msg, parse_mode="HTML")
    await call.message.answer(
        f"✅ {LANGUAGES.get(lang_code, 'O\'zbekcha')}",
        reply_markup=get_main_keyboard(is_admin, lang=lang_code)
    )
    await call.answer()

@router.callback_query(F.data == "my_garage_cb")
async def show_my_garage_cb(call: CallbackQuery):
    user_id = call.from_user.id
    inv = await db.get_inventory(user_id)
    inv_map = {it["code"]: it["quantity"] for it in inv}
    from bot.handlers.extra_features import CAR_DEFINITIONS
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

    if call.message.chat.type in ["group", "supergroup"]:
        try:
            await call.bot.send_message(user_id, garage_text, parse_mode="HTML")
            await call.answer("🚗 Garajingiz shaxsiy lichkangizga yuborildi!", show_alert=False)
        except Exception:
            bot_info = await call.bot.get_me()
            await call.answer(f"⚠️ Avval @{bot_info.username} ga kirib Start bosing!", show_alert=True)
        return

    await call.message.answer(garage_text, parse_mode="HTML")
    await call.answer()

@router.callback_query(F.data == "my_inventory")
async def show_inventory_cb(call: CallbackQuery):
    user_id = call.from_user.id
    inv = await db.get_inventory(user_id)
    if not inv:
        txt = "🎒 <b>Sizning inventaringiz bo'sh!</b>\nDo'kondan buyumlar sotib oling."
    else:
        txt = "🎒 <b>SIZNING INVENTARINGIZ:</b>\n\n"
        for it in inv:
            txt += f"{it['icon']} <b>{it['name']}</b>: {it['quantity']} ta\n   <i>{it['description']}</i>\n\n"
        txt += "<i>Buyumlar o'yin boshlanganda yoki o'yin davomida avtomatik ishlatiladi.</i>"

    if call.message.chat.type in ["group", "supergroup"]:
        try:
            await call.bot.send_message(user_id, txt, parse_mode="HTML")
            await call.answer("🎒 Inventaringiz shaxsiy lichkangizga yuborildi!", show_alert=False)
        except Exception:
            bot_info = await call.bot.get_me()
            await call.answer(f"⚠️ Avval @{bot_info.username} ga kirib Start bosing!", show_alert=True)
        return

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
