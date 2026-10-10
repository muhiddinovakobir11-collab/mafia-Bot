import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command

from database.db import db
from game.engine import game_manager
from bot.keyboards import get_lobby_keyboard
from config import MIN_PLAYERS, ADMIN_IDS

router = Router()

def format_lobby_text(room) -> str:
    player_names = ", ".join([p.tag for p in room.players.values()]) if room.players else "Hozircha hech kim yo'q"
    return (
        f"📌 <b>Ro'yxatdan o'tish davom etmoqda!</b>\n\n"
        f"👥 <b>Ro'yxatdan o'tganlar:</b>\n{player_names}\n\n"
        f"📊 <b>Jami:</b> {len(room.players)} kishi.\n\n"
        f"<i>Kamida {MIN_PLAYERS} kishi to'plangach, guruh admini yoki o'yin yaratuvchisi '🚀 O'yinni boshlash' tugmasini bosib start qilishi mumkin.</i>"
    )

async def check_admin_permission(bot, chat_id: int, user_id: int, creator_id: int) -> bool:
    if user_id in ADMIN_IDS or user_id == creator_id:
        return True
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        if member.status in ["creator", "administrator"]:
            return True
    except Exception:
        pass
    return False

@router.message(Command("game"))
@router.message(Command("mafia"))
async def start_game_cmd(message: Message):
    if message.chat.type == "private":
        bot_info = await message.bot.get_me()
        add_url = f"https://t.me/{bot_info.username}?startgroup=true"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Guruhga qo'shish", url=add_url)]
        ])
        await message.answer(
            "⚠️ <b>Mafiya faqat Telegram guruhlarida o'ynaladi!</b>\n\n"
            "Botni guruhingizga qo'shing va u yerda <b>/game</b> buyrug'ini yuboring.",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return

    chat_id = message.chat.id
    existing_room = game_manager.get_room(chat_id)

    if existing_room:
        if existing_room.state != "LOBBY":
            await message.answer("⚠️ <b>Guruhda ayni paytda o'yin davom etmoqda!</b>\nO'yin tugashini kuting.")
            return
        else:
            await message.answer("⚠️ <b>O'yinga qabul allaqachon boshlangan!</b> Tepada qadalgan (pinned) xabarga qarang.")
            return

    # Check if user is banned
    user = await db.get_or_create_user(message.from_user.id, message.from_user.username or "", message.from_user.full_name or "")
    if user.get("is_banned"):
        await message.answer("🚫 <b>Siz botdan bloklangansiz va o'yin yarata olmaysiz!</b>")
        return

    # Create new game room
    room = game_manager.create_room(chat_id, message.bot)
    room.creator_id = message.from_user.id
    # Creator automatically joins
    room.add_player(message.from_user.id, message.from_user.full_name, message.from_user.username or "")

    # Send lobby message
    msg = await message.answer(
        format_lobby_text(room),
        reply_markup=get_lobby_keyboard(chat_id),
        parse_mode="HTML"
    )
    room.lobby_message_id = msg.message_id

    # Automatically pin the message to match the user screenshot!
    try:
        await message.bot.pin_chat_message(chat_id=chat_id, message_id=msg.message_id, disable_notification=True)
        room.pinned_message_id = msg.message_id
    except Exception as e:
        print(f"[Auto-pin Error in chat {chat_id}]: {e}")

@router.callback_query(F.data.startswith("join_"))
async def handle_join(call: CallbackQuery):
    chat_id = int(call.data.replace("join_", ""))
    room = game_manager.get_room(chat_id)

    if not room or room.state != "LOBBY":
        await call.answer("❌ O'yin boshlanib ketgan yoki mavjud emas!", show_alert=True)
        return

    user = await db.get_or_create_user(call.from_user.id, call.from_user.username or "", call.from_user.full_name or "")
    if user.get("is_banned"):
        await call.answer("🚫 Siz botdan bloklangansiz!", show_alert=True)
        return

    group_url = await room.get_group_link()
    group_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔵 Guruhga qaytish ➔", url=group_url)]
    ])

    if call.from_user.id in room.players:
        await call.answer("Siz allaqachon bu o'yinga qo'shilgansiz!", show_alert=False)
        try:
            await call.bot.send_message(
                call.from_user.id,
                "ℹ️ <b>Siz allaqachon bu o'yinga qo'shilgansiz!</b>\n\nO'yin boshlanishini guruhda kuting.",
                reply_markup=group_kb,
                parse_mode="HTML"
            )
        except Exception:
            pass
        return

    added = room.add_player(call.from_user.id, call.from_user.full_name, call.from_user.username or "")
    if not added:
        await call.answer("Siz allaqachon bu o'yinga qo'shilgansiz!", show_alert=False)
        return

    await call.answer("✅ Muvaffaqiyatli qo'shildingiz!")

    # Send DM to user matching TrueMafia with "Guruhga qaytish" button
    try:
        await call.bot.send_message(
            call.from_user.id,
            "✅ <b>Muvaffaqiyatli qo'shildingiz!</b>\n\n"
            "Siz o'yin ro'yxatiga kiritildingiz. O'yin boshlanganda maxfiy rolingiz shu yerga yuboriladi.\n"
            "Guruhga qaytib, o'yin boshlanishini kuting!",
            reply_markup=group_kb,
            parse_mode="HTML"
        )
    except Exception:
        bot_info = await call.bot.get_me()
        await call.answer(
            f"✅ Siz qo'shildingiz! Bot sizga rolingizni yuborishi uchun botga start bosing: @{bot_info.username}",
            show_alert=True
        )

    # Update pinned lobby message text with real-time list
    try:
        if room.lobby_message_id:
            await room.bot.edit_message_text(
                format_lobby_text(room),
                chat_id=chat_id,
                message_id=room.lobby_message_id,
                reply_markup=get_lobby_keyboard(chat_id),
                parse_mode="HTML"
            )
    except Exception:
        pass

@router.callback_query(F.data.startswith("leave_"))
async def handle_leave(call: CallbackQuery):
    chat_id = int(call.data.replace("leave_", ""))
    room = game_manager.get_room(chat_id)

    if not room or room.state != "LOBBY":
        await call.answer("❌ O'yin mavjud emas!", show_alert=True)
        return

    removed = room.remove_player(call.from_user.id)
    if not removed:
        await call.answer("⚠️ Siz ro'yxatda emassiz!", show_alert=True)
        return

    await call.answer("🚪 Siz o'yindan chiqdingiz.")

    # Update lobby message
    try:
        if room.lobby_message_id:
            await room.bot.edit_message_text(
                format_lobby_text(room),
                chat_id=chat_id,
                message_id=room.lobby_message_id,
                reply_markup=get_lobby_keyboard(chat_id),
                parse_mode="HTML"
            )
    except Exception:
        pass

@router.callback_query(F.data.startswith("forcestart_"))
async def handle_force_start(call: CallbackQuery):
    chat_id = int(call.data.replace("forcestart_", ""))
    room = game_manager.get_room(chat_id)

    if not room or room.state != "LOBBY":
        await call.answer("❌ O'yin mavjud emas!", show_alert=True)
        return

    # Check admin permission
    can_start = await check_admin_permission(call.bot, chat_id, call.from_user.id, room.creator_id)
    if not can_start:
        await call.answer("⚠️ Faqat guruh admini yoki o'yin yaratuvchisi o'yinni boshlashi mumkin!", show_alert=True)
        return

    if len(room.players) < MIN_PLAYERS:
        await call.answer(
            f"❌ O'yinni boshlash uchun kamida {MIN_PLAYERS} kishi kerak! Hozirda {len(room.players)} kishi bor.",
            show_alert=True
        )
        return

    if room.lobby_task and not room.lobby_task.done():
        room.lobby_task.cancel()

    await call.answer("🚀 O'yin boshlanmoqda...")
    await room.start_game()

@router.message(Command("startgame"))
@router.message(Command("start_game"))
async def cmd_startgame(message: Message):
    if message.chat.type == "private":
        return

    chat_id = message.chat.id
    room = game_manager.get_room(chat_id)
    if not room or room.state != "LOBBY":
        await message.answer("⚠️ Boshlash uchun faol ro'yxatga olish mavjud emas. Yangi o'yin uchun /game yuboring.")
        return

    can_start = await check_admin_permission(message.bot, chat_id, message.from_user.id, room.creator_id)
    if not can_start:
        await message.answer("⚠️ Faqat guruh admini yoki o'yin yaratuvchisi o'yinni boshlashi mumkin!")
        return

    if len(room.players) < MIN_PLAYERS:
        await message.answer(f"❌ O'yinni boshlash uchun kamida {MIN_PLAYERS} kishi kerak! Hozirda {len(room.players)} kishi bor.")
        return

    if room.lobby_task and not room.lobby_task.done():
        room.lobby_task.cancel()

    await message.answer("🚀 O'yin boshlanmoqda...")
    await room.start_game()

@router.callback_query(F.data.startswith("vote_"))
async def handle_day_vote(call: CallbackQuery):
    parts = call.data.split("_")
    chat_id = int(parts[1])
    target_str = parts[2]

    room = game_manager.get_room(chat_id)
    if not room or room.state != "DAY_VOTE":
        await call.answer("❌ Ovoz berish bosqichi faol emas!", show_alert=True)
        return

    voter = room.get_player(call.from_user.id)
    if not voter or not voter.is_alive:
        await call.answer("❌ Faqat tirik o'yinchilar ovoz bera oladi!", show_alert=True)
        return

    if target_str == "skip":
        voter.vote_target_id = -1
        await call.answer("✅ Siz hech kimni tanlamadingiz (Skip)!")
    else:
        target_id = int(target_str)
        target = room.get_player(target_id)
        if not target or not target.is_alive:
            await call.answer("❌ Tanlangan o'yinchi tirik emas!", show_alert=True)
            return

        voter.vote_target_id = target_id
        await call.answer(f"✅ Siz {target.full_name} ga ovoz berdingiz!")

    # Live update voting buttons so the whole group sees the counts
    try:
        vote_counts = {}
        skip_cnt = 0
        for pl in room.get_alive_players():
            if pl.vote_target_id == -1:
                skip_cnt += 1
            elif pl.vote_target_id:
                vote_counts[pl.vote_target_id] = vote_counts.get(pl.vote_target_id, 0) + 1

        new_buttons = []
        new_row = []
        for p in room.get_alive_players():
            c = vote_counts.get(p.user_id, 0)
            c_txt = f" ({c})" if c > 0 else ""
            new_row.append(InlineKeyboardButton(text=f"⚖️ {p.full_name[:10]}{c_txt}", callback_data=f"vote_{chat_id}_{p.user_id}"))
            if len(new_row) == 2:
                new_buttons.append(new_row)
                new_row = []
        if new_row:
            new_buttons.append(new_row)

        skip_label = f"⏭️ Skip ({skip_cnt})" if skip_cnt > 0 else "⏭️ O'tkazib yuborish (Skip)"
        new_buttons.append([InlineKeyboardButton(text=skip_label, callback_data=f"vote_{chat_id}_skip")])

        await call.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=new_buttons))
    except Exception:
        pass

    # Smart Vote: if all alive players have voted, trigger early tally!
    if room.check_all_votes_done() and room.vote_event:
        room.vote_event.set()

@router.message(Command("vote"))
@router.message(Command("sud"))
async def cmd_skip_talk_to_vote(message: Message):
    if message.chat.type == "private":
        return
    room = game_manager.get_room(message.chat.id)
    if not room or room.state != "DAY_TALK":
        return
    if hasattr(room, "talk_event") and room.talk_event and not room.talk_event.is_set():
        room.talk_event.set()
        await message.answer("⚖️ <b>Muhokama to'xtatildi, ovoz berish boshlanmoqda!</b>")

@router.callback_query(F.data.startswith("addbot_"))
async def handle_add_bot(call: CallbackQuery):
    chat_id = int(call.data.replace("addbot_", ""))
    room = game_manager.get_room(chat_id)

    if not room or room.state != "LOBBY":
        await call.answer("❌ O'yin mavjud emas!", show_alert=True)
        return

    bot_player = room.add_ai_bot()
    if not bot_player:
        await call.answer("⚠️ Bot qo'shib bo'lmadi!", show_alert=True)
        return

    await call.answer(f"🤖 {bot_player.full_name} qo'shildi!")

    try:
        if room.lobby_message_id:
            await room.bot.edit_message_text(
                format_lobby_text(room),
                chat_id=chat_id,
                message_id=room.lobby_message_id,
                reply_markup=get_lobby_keyboard(chat_id),
                parse_mode="HTML"
            )
    except Exception:
        pass

@router.message(Command("addbot"))
async def handle_addbot_cmd(message: Message):
    if message.chat.type == "private":
        return
    room = game_manager.get_room(message.chat.id)
    if not room or room.state != "LOBBY":
        await message.answer("⚠️ Avval <b>/game</b> buyrug'i orqali yangi o'yin oching!")
        return
    bot_player = room.add_ai_bot()
    if bot_player:
        await message.answer(f"🤖 <b>{bot_player.full_name}</b> o'yinga qo'shildi!")
        try:
            if room.lobby_message_id:
                await room.bot.edit_message_text(
                    format_lobby_text(room),
                    chat_id=message.chat.id,
                    message_id=room.lobby_message_id,
                    reply_markup=get_lobby_keyboard(message.chat.id),
                    parse_mode="HTML"
                )
        except Exception:
            pass

@router.message(Command("stop"))
async def handle_stop_game(message: Message):
    if message.chat.type == "private":
        return
    room = game_manager.get_room(message.chat.id)
    if not room:
        await message.answer("⚠️ Guruhda faol o'yin yo'q.")
        return
    can_stop = await check_admin_permission(message.bot, message.chat.id, message.from_user.id, room.creator_id)
    if not can_stop:
        await message.answer("⚠️ Faqat guruh admini o'yinni to'xtata oladi!")
        return
    room.state = "GAME_OVER"
    game_manager.remove_room(message.chat.id)
    try:
        from aiogram.types import ChatPermissions
        await message.bot.set_chat_permissions(
            message.chat.id,
            ChatPermissions(can_send_messages=True, can_send_media_messages=True, can_send_other_messages=True)
        )
    except Exception:
        pass
    await message.answer("🛑 <b>O'yin admin tomonidan to'xtatildi.</b>")

@router.message(Command("role"))
@router.message(Command("rol"))
@router.message(Command("myrole"))
async def cmd_myrole(message: Message):
    if message.chat.type == "private":
        return
    room = game_manager.get_room(message.chat.id)
    if not room or room.state in ["LOBBY", "GAME_OVER"]:
        await message.reply("⚠️ Hozirda faol o'yin yo'q.")
        return
    player = room.get_player(message.from_user.id)
    if not player:
        await message.reply("⚠️ Siz bu o'yinda qatnashmayapsiz.")
        return
    from game.roles import ROLES
    r_info = ROLES.get(player.role_code)
    if not r_info:
        return
    status_txt = "✅ Tiriksiz" if player.is_alive else "💀 Halok bo'lgansiz"
    role_text = (
        f"🎭 <b>Sizning rolingiz:</b> {r_info.emoji} <b>{r_info.name}</b> ({status_txt})\n\n"
        f"{r_info.description}"
    )
    try:
        await message.bot.send_message(message.from_user.id, role_text, parse_mode="HTML")
        await message.reply("📩 Rolingiz shaxsiy xabarga (DM) yuborildi!")
    except Exception:
        await message.reply("⚠️ Bot shaxsiy xabariga start bosing, shunda rolingizni ko'ra olasiz!")

@router.message(Command("alive"))
@router.message(Command("players"))
@router.message(Command("tiriklar"))
async def cmd_alive_players(message: Message):
    if message.chat.type == "private":
        return
    room = game_manager.get_room(message.chat.id)
    if not room or room.state in ["LOBBY", "GAME_OVER"]:
        await message.reply("⚠️ Hozirda faol o'yin yo'q.")
        return
    from game.roles import ROLES
    alive = room.get_alive_players()
    dead = [p for p in room.players.values() if not p.is_alive]
    text = f"📋 <b>O'yin holati ({room.round_number}-raund):</b>\n\n"
    text += f"👥 <b>Tiriklar ({len(alive)}):</b>\n"
    text += "\n".join([f"• {p.tag}" for p in alive])
    if dead:
        text += f"\n\n💀 <b>Halok bo'lganlar ({len(dead)}):</b>\n"
        text += "\n".join([f"• ⚰️ {p.tag} ({ROLES[p.role_code].emoji} {ROLES[p.role_code].name})" for p in dead])
    await message.answer(text, parse_mode="HTML")

@router.message(Command("rules"))
@router.message(Command("qoidalar"))
async def cmd_game_rules(message: Message):
    rules_text = (
        "📖 <b>MAFIYA O'YINI QOIDALARI:</b>\n\n"
        "🏙️ Shahar aholisi ikki lagerga bo'lingan: Tinch fuqarolar va Mafiya to'dasi.\n\n"
        "🌑 <b>TUN:</b> Shahar uxlaydi. Don va Mafiya qurbon tanlaydi, Komissar tekshiradi, Shifokor qutqaradi, Qotil suiqasd qiladi.\n"
        "☀️ <b>KUN:</b> Tungi qurbonlar e'lon qilinadi, shahar fuqarolari muhokama boshlaydi.\n"
        "⚖️ <b>SUD VA OVOZ BERISH:</b> Gumonlanuvchini osish uchun ovoz beriladi. Ko'pchilik ovoz olgan o'yinchiga 10 soniya oqlanish nutqi beriladi va u dorga osiladi.\n\n"
        "🤫 <b>Asosiy qoida:</b> Halok bo'lganlar o'yin tugaguncha guruhda gapira olmaydi (Мертвые молчат)!"
    )
    await message.answer(rules_text, parse_mode="HTML")

@router.message(F.chat.type.in_(["group", "supergroup"]))
async def group_messages_filter(message: Message):
    if not message.from_user:
        return
    room = game_manager.get_room(message.chat.id)
    if not room or room.state in ["LOBBY", "GAME_OVER"]:
        return

    # 1. "Мертвые молчат" rule: Dead players cannot speak during active game!
    player = room.get_player(message.from_user.id)
    if player and not player.is_alive:
        try:
            await message.delete()
        except Exception:
            pass
        return

    # 2. Anti-spam URL deletion
    settings = await db.get_group_settings(message.chat.id)
    if settings.get("is_antispam") and message.text:
        text = message.text.lower()
        if "http://" in text or "https://" in text or "t.me/" in text:
            is_adm = await check_admin_permission(message.bot, message.chat.id, message.from_user.id, 0)
            if not is_adm:
                try:
                    await message.delete()
                except Exception:
                    pass
                return

