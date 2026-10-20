from aiogram import Router, F
from aiogram.types import CallbackQuery
from game.engine import game_manager
from game.roles import ROLES, Team

router = Router()

@router.callback_query(F.data.startswith("act_"))
async def handle_night_action(call: CallbackQuery):
    parts = call.data.split("_")
    chat_id = int(parts[1])
    target_id = int(parts[2])

    room = game_manager.get_room(chat_id)
    if not room or room.state != "NIGHT":
        await call.answer("❌ Tungi harakatlar vaqti tugagan!", show_alert=True)
        return

    player = room.get_player(call.from_user.id)
    if not player or not player.is_alive:
        await call.answer("❌ Siz tirik emassiz!", show_alert=True)
        return

    target = room.get_player(target_id)
    if not target or not target.is_alive:
        await call.answer("❌ Tanlangan o'yinchi tirik emas!", show_alert=True)
        return

    player.night_target_id = target_id
    r = ROLES.get(player.role_code)

    await call.answer("✅ Tanlovingiz qabul qilindi!", show_alert=False)
    await call.message.edit_text(
        f"🎯 <b>Tungi tanlovingiz qabul qilindi!</b>\n\n"
        f"Siz <b>{target.full_name}</b>ni tanladingiz.\n"
        f"Tong otishini kuting...",
        parse_mode="HTML"
    )

    # Sync with Mafia teammates in secret DM
    if r and r.team == Team.MAFIA:
        for teammate in room.get_alive_players():
            if teammate.user_id != player.user_id and ROLES[teammate.role_code].team == Team.MAFIA:
                await room.send_dm(
                    teammate.user_id,
                    f"👥 <b>Mafiya sherigingiz {player.full_name}</b> bu kecha nishon qilib <b>{target.full_name}</b>ni tanladi!"
                )

    # Smart Night: if all active roles completed their choice, wake town up early!
    if room.check_all_night_actions_done() and room.night_event:
        room.night_event.set()

