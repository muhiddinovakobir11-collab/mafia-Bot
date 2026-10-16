import asyncio
import random
import time
import aiosqlite
from typing import Dict, List, Optional, Any
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ChatPermissions

from game.roles import ROLES, Team, get_role_distribution
from database.db import db
from game.levels import format_level_up_message
from config import MIN_PLAYERS, LOBBY_TIMEOUT, NIGHT_TIMEOUT, DAY_TALK_TIMEOUT, VOTE_TIMEOUT

class Player:
    def __init__(self, user_id: int, full_name: str, username: str = ""):
        self.user_id = user_id
        self.full_name = full_name
        self.username = username
        self.role_code: str = ""
        self.is_alive: bool = True
        self.has_shield: bool = False
        self.has_mask: bool = False
        self.extra_votes: int = 0
        self.is_poisoned: bool = False
        self.is_muted: bool = False
        self.night_target_id: Optional[int] = None
        self.vote_target_id: Optional[int] = None
        self.is_bot: bool = False
        self.afk_rounds: int = 0
        self.self_heal_count: int = 0

    @property
    def tag(self) -> str:
        safe_name = (self.full_name or "O'yinchi").replace("<", "&lt;").replace(">", "&gt;")
        if self.is_bot:
            return f"<b>{safe_name}</b>"
        if self.username:
            return f'<a href="https://t.me/{self.username}">{safe_name}</a> (@{self.username})'
        return f'<a href="tg://user?id={self.user_id}">{safe_name}</a>'

class GameRoom:
    def __init__(self, chat_id: int, bot: Bot):
        self.chat_id = chat_id
        self.bot = bot
        self.state: str = "LOBBY" # LOBBY, NIGHT, DAY_TALK, DAY_VOTE, GAME_OVER
        self.players: Dict[int, Player] = {}
        self.lovers: List[int] = []
        self.lobby_task: Optional[asyncio.Task] = None
        self.round_number: int = 0
        self.lobby_message_id: Optional[int] = None
        self.pinned_message_id: Optional[int] = None
        self.creator_id: int = 0
        self.lobby_timer: int = LOBBY_TIMEOUT
        self.night_event: Optional[asyncio.Event] = None
        self.vote_event: Optional[asyncio.Event] = None
        self.talk_event: Optional[asyncio.Event] = None
        self.vote_message_id: Optional[int] = None

    def check_all_night_actions_done(self) -> bool:
        alive = self.get_alive_players()
        for p in alive:
            r = ROLES.get(p.role_code)
            if r and r.action_type != "none":
                if not p.is_bot and p.night_target_id is None:
                    return False
        return True

    def check_all_votes_done(self) -> bool:
        alive = self.get_alive_players()
        for p in alive:
            if not p.is_bot and p.vote_target_id is None:
                return False
        return True

    def get_alive_players(self) -> List[Player]:
        return [p for p in self.players.values() if p.is_alive]

    def get_player(self, user_id: int) -> Optional[Player]:
        return self.players.get(user_id)

    def add_player(self, user_id: int, full_name: str, username: str = "") -> bool:
        if self.state != "LOBBY":
            return False
        if user_id in self.players:
            return False
        self.players[user_id] = Player(user_id, full_name, username)
        return True

    def add_ai_bot(self) -> Optional[Player]:
        if self.state != "LOBBY":
            return None
        bot_names = ["Alex", "Diana", "Mark", "Elena", "Viktor", "Sara", "Timur", "Kamila", "Felix", "Alina"]
        used_names = [p.full_name.replace("🤖 Bot ", "") for p in self.players.values()]
        available = [n for n in bot_names if n not in used_names]
        chosen = available[0] if available else f"Bot_{random.randint(10, 99)}"
        bot_id = -random.randint(100000, 999999)
        p = Player(bot_id, f"🤖 Bot {chosen}", "")
        p.is_bot = True
        self.players[bot_id] = p
        return p

    def remove_player(self, user_id: int) -> bool:
        if self.state != "LOBBY":
            return False
        if user_id in self.players:
            del self.players[user_id]
            return True
        return False

    async def get_group_link(self) -> str:
        if hasattr(self, "_group_link") and self._group_link:
            return self._group_link

        # 1. Try chat username or invite link
        try:
            chat = await self.bot.get_chat(self.chat_id)
            if chat.username:
                link = f"https://t.me/{chat.username}"
                if self.lobby_message_id:
                    link += f"/{self.lobby_message_id}"
                self._group_link = link
                return link
            if chat.invite_link:
                self._group_link = chat.invite_link
                return chat.invite_link
        except Exception:
            pass

        # 2. Try export / create invite link if bot has rights
        try:
            link = await self.bot.export_chat_invite_link(self.chat_id)
            if link:
                self._group_link = link
                return link
        except Exception:
            pass

        try:
            invite = await self.bot.create_chat_invite_link(self.chat_id)
            if invite and invite.invite_link:
                self._group_link = invite.invite_link
                return invite.invite_link
        except Exception:
            pass

        # 3. Supergroup internal deep link
        clean_id = str(self.chat_id).replace("-100", "").replace("-", "")
        msg_id = self.lobby_message_id or 1
        fallback_link = f"https://t.me/c/{clean_id}/{msg_id}"
        self._group_link = fallback_link
        return fallback_link

    async def broadcast_group(self, text: str, reply_markup=None):
        try:
            return await self.bot.send_message(self.chat_id, text, parse_mode="HTML", reply_markup=reply_markup)
        except Exception as e:
            print(f"[Group Error {self.chat_id}]: {e}")
            return None

    async def send_dm(self, user_id: int, text: str, reply_markup=None):
        if user_id < 0:
            return None # Virtual AI bots don't receive telegram messages
        try:
            return await self.bot.send_message(user_id, text, parse_mode="HTML", reply_markup=reply_markup)
        except Exception as e:
            print(f"[DM Error to {user_id}]: {e}")
            return None

    async def start_game(self):
        if self.pinned_message_id:
            try:
                await self.bot.unpin_chat_message(self.chat_id, self.pinned_message_id)
            except Exception:
                pass

        if len(self.players) < MIN_PLAYERS:
            await self.broadcast_group(
                f"❌ <b>O'yin bekor qilindi!</b>\nYetarli o'yinchi yig'ilmadi (kamida {MIN_PLAYERS} kishi kerak edi)."
            )
            game_manager.remove_room(self.chat_id)
            return

        self.state = "STARTING"
        player_list = list(self.players.values())
        random.shuffle(player_list)

        role_codes = get_role_distribution(len(player_list))
        random.shuffle(role_codes)

        group_url = await self.get_group_link()
        group_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Перейти в группу", url=group_url)]
        ])

        # 1. Pre-assign roles to all players
        for p, role_code in zip(player_list, role_codes):
            p.role_code = role_code

        # 2. Process inventory items and send private role assignments
        for p in player_list:
            role_code = p.role_code
            r_info = ROLES[role_code]

            # Check inventory for shield or mask
            inv = await db.get_inventory(p.user_id)
            for it in inv:
                if it["code"] == "qalqon" and it["quantity"] > 0:
                    p.has_shield = True
                    await db.consume_inventory_item(p.user_id, "qalqon", 1)
                elif it["code"] == "niqob" and it["quantity"] > 0:
                    p.has_mask = True
                    await db.consume_inventory_item(p.user_id, "niqob", 1)
                elif it["code"] == "extra_vote" and it["quantity"] > 0:
                    p.extra_votes += 2
                    await db.consume_inventory_item(p.user_id, "extra_vote", 1)

            # Send private message to player with their role matching TrueMafia format
            shield_txt = "\n🛡️ <i>Защитный щит активирован!</i>" if p.has_shield else ""
            mask_txt = "\n🎭 <i>Маска мафии активирована!</i>" if p.has_mask else ""
            vote_txt = "\n🗳️ <i>Дополнительные голоса: +2!</i>" if p.extra_votes > 0 else ""

            role_title = r_info.ru_name or r_info.name
            role_desc = r_info.ru_description or r_info.description

            team_info = ""
            if r_info.team == Team.MAFIA:
                mafia_team = [
                    m.full_name for m in player_list
                    if m.user_id != p.user_id and m.role_code in ROLES and ROLES[m.role_code].team == Team.MAFIA
                ]
                if mafia_team:
                    team_info = f"\n\n👥 <b>Ваши сообщники:</b> {', '.join(mafia_team)}"
            elif p.role_code == "serjant":
                komissars = [m.full_name for m in player_list if m.role_code == "komissar"]
                if komissars:
                    team_info = f"\n\n🕵️‍♂️ <b>Ваш Комиссар:</b> {', '.join(komissars)}"

            dm_text = (
                f"<b>Вы - {r_info.emoji} {role_title}!</b>\n"
                f"{role_desc}"
                f"{team_info}"
                f"{shield_txt}{mask_txt}{vote_txt}"
            )
            await self.send_dm(p.user_id, dm_text, reply_markup=group_kb)

        # Announce game start in group
        names = "\n".join([f"👤 {idx+1}. {p.tag}" for idx, p in enumerate(self.players.values())])
        await self.broadcast_group(
            f"🎬 <b>MAFIYA O'YINI BOSHLANDI!</b>\n\n"
            f"Barcha o'yinchilar shaxsiy xabarda o'z rollarini qabul qilishdi.\n\n"
            f"📋 <b>Ishtirokchilar ro'yxati ({len(self.players)} kishi):</b>\n{names}\n\n"
            f"🌑 <b>Shahar uzra qora tun tushmoqda... Hamma ko'zlarini yumadi!</b>"
        )

        await asyncio.sleep(3)
        await self.run_night_phase()

    async def run_night_phase(self):
        self.round_number += 1
        self.state = "NIGHT"
        self.night_event = asyncio.Event()

        settings = await db.get_group_settings(self.chat_id)
        night_time = settings.get("night_time", NIGHT_TIMEOUT)

        # Reset night targets
        for p in self.get_alive_players():
            p.night_target_id = None

        if self.round_number == 1:
            await self.broadcast_group(
                f"🌑 <b>1-TUN: TANISHUV TUNI!</b> 🌑\n\n"
                f"Shahar uzra dastlabki qorong'ulik tushmoqda...\n"
                f"🤝 <i>Bu kecha qon to'kilmaydi — Mafiya o'z sheriklari bilan tanishadi, maxsus kuchlar esa shaharni ko'zdan kechiradi!</i>\n"
                f"Barcha maxsus rollar bot shaxsiy xabarida o'z tanlovlarini amalga oshirsin!\n"
                f"<i>(🤫 Qoidabuzarlikning oldini olish uchun guruhda xabar yozish tonggacha cheklandi!)</i>\n"
                f"⏳ <b>Vaqt:</b> {night_time} soniya."
            )
        else:
            await self.broadcast_group(
                f"🌑 <b>{self.round_number}-TUN BOSHLANDI!</b> 🌑\n\n"
                f"Shaharda qonxo'rlar va maxfiy kuchlar uyg'onmoqda...\n"
                f"Barcha maxsus rollar bot shaxsiy xabarida o'z tanlovlarini amalga oshirsin!\n"
                f"<i>(🤫 Qoidabuzarlikning oldini olish uchun guruhda xabar yozish tonggacha cheklandi!)</i>\n"
                f"⏳ <b>Vaqt:</b> {night_time} soniya."
            )

        # 1. Tungi Avto-Mute (Auto-Mute at Night in Groups)
        if self.chat_id < 0:
            try:
                await self.bot.set_chat_permissions(
                    self.chat_id,
                    ChatPermissions(can_send_messages=False)
                )
            except Exception:
                pass

        alive = self.get_alive_players()
        for p in alive:
            r_info = ROLES.get(p.role_code)
            if not r_info or r_info.action_type == "none":
                continue

            # Intelligent target list
            if r_info.team == Team.MAFIA:
                targets = [t for t in alive if t.user_id != p.user_id and ROLES.get(t.role_code) and ROLES[t.role_code].team != Team.MAFIA]
                if not targets:
                    targets = [t for t in alive if t.user_id != p.user_id]
            elif r_info.code == "laborant":
                targets = list(alive)
            else:
                targets = [t for t in alive if t.user_id != p.user_id]

            if p.is_bot:
                if targets:
                    p.night_target_id = random.choice(targets).user_id
                continue

            # Build inline target buttons
            buttons = []
            row = []
            for t in targets:
                row.append(InlineKeyboardButton(text=f"🎯 {t.full_name[:14]}", callback_data=f"act_{self.chat_id}_{t.user_id}"))
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            if row:
                buttons.append(row)

            kb = InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
            if self.round_number == 1 and r_info.team in [Team.MAFIA, Team.MANIAC]:
                prompt_text = (
                    f"🌑 <b>TUN #{self.round_number} (Tanishuv tuni)</b>\n"
                    f"Siz: {r_info.emoji} <b>{r_info.name}</b>\n\n"
                    f"🤝 <i>Bu kecha tanishuv tuni bo'lgani sababli qotillik sodir bo'lmaydi.</i>\n"
                    f"Shubhangizdagi o'yinchini nishonga oling:"
                )
            else:
                prompt_text = (
                    f"🌑 <b>TUN #{self.round_number}</b>\n"
                    f"Siz: {r_info.emoji} <b>{r_info.name}</b>\n\n"
                    f"{r_info.night_prompt}"
                )
            await self.send_dm(p.user_id, prompt_text, reply_markup=kb)

        night_start = time.time()
        # Smart Night: check if all choices ready (e.g. only bots)
        if self.check_all_night_actions_done():
            self.night_event.set()

        # Wait for night timer or early trigger
        try:
            await asyncio.wait_for(self.night_event.wait(), timeout=night_time)
        except asyncio.TimeoutError:
            pass

        # Minimum suspense duration so night doesn't feel instant (at least 15s)
        elapsed = time.time() - night_start
        min_night_pause = min(15, night_time)
        if elapsed < min_night_pause:
            await asyncio.sleep(min_night_pause - elapsed)

        await self.broadcast_group("🌅 <b>Tong otmoqda... Shahar uyg'onmoqda!</b>")
        await asyncio.sleep(2)

        # Resolve night actions
        await self.resolve_night_actions()

    async def resolve_night_actions(self):
        alive = self.get_alive_players()
        alive_map = {p.user_id: p for p in alive}

        # 1. Check Kazanova and Ogri (distraction / theft)
        distracted_user_ids = set()
        for p in alive:
            if p.role_code in ["kazanova", "ogri"] and p.night_target_id in alive_map:
                distracted_user_ids.add(p.night_target_id)
                actor_title = "Kazanova" if p.role_code == "kazanova" else "O'g'ri"
                await self.send_dm(
                    p.night_target_id,
                    f"💃 <b>{actor_title} sizni chalg'itdi (tunab ketdi)!</b> Bu kecha hech qanday harakat qila olmadingiz."
                )

        # 2. Check Laborant heal (max 1 self-heal)
        healed_user_id = None
        for p in alive:
            if p.role_code == "laborant" and p.user_id not in distracted_user_ids:
                if p.night_target_id == p.user_id:
                    if p.self_heal_count >= 1:
                        await self.send_dm(p.user_id, "⚠️ <i>Siz o'zingizni bir o'yinda faqat 1 marta davolay olasiz! Davolash ish bermadi.</i>")
                    else:
                        p.self_heal_count += 1
                        healed_user_id = p.night_target_id
                else:
                    healed_user_id = p.night_target_id

        # 3. Kupidon: link lovers on Round 1
        for p in alive:
            if p.role_code == "kupidon" and self.round_number == 1 and not self.lovers:
                if p.night_target_id and p.night_target_id in alive_map:
                    t1_id = p.night_target_id
                    others = [o.user_id for o in alive if o.user_id != t1_id]
                    if others:
                        t2_id = random.choice(others)
                        self.lovers = [t1_id, t2_id]
                        l1 = alive_map[t1_id]
                        l2 = alive_map[t2_id]
                        await self.send_dm(t1_id, f"💘 <b>Kupidon kamoni sizni bog'ladi!</b>\nSizning sevgan yoringiz: <b>{l2.full_name}</b>!\nAgar biringiz o'lsangiz, ikkinchingiz ham qayg'udan vafot etasiz!")
                        await self.send_dm(t2_id, f"💘 <b>Kupidon kamoni sizni bog'ladi!</b>\nSizning sevgan yoringiz: <b>{l1.full_name}</b>!\nAgar biringiz o'lsangiz, ikkinchingiz ham qayg'udan vafot etasiz!")

        # 4. Mafia/Don kill target
        mafia_target_id = None
        for p in alive:
            if p.role_code in ["don", "mafia"] and p.user_id not in distracted_user_ids:
                if p.night_target_id:
                    mafia_target_id = p.night_target_id
                    break

        # 5. Qotil (Maniac) kill target
        maniac_target_id = None
        for p in alive:
            if p.role_code == "kotil" and p.user_id not in distracted_user_ids:
                maniac_target_id = p.night_target_id

        # 6. Ximik poison target
        for p in alive:
            if p.role_code == "ximik" and p.user_id not in distracted_user_ids:
                if p.night_target_id in alive_map:
                    alive_map[p.night_target_id].is_poisoned = True
                    await self.send_dm(p.night_target_id, "🧪 <i>Siz kimyoviy moddadan zaharlandingiz! Agar zardob olmasangiz, kun oxirida halok bo'lasiz...</i>")

        # 7. Advokat (Mafiya Himoyachisi)
        lawyer_target_id = None
        for p in alive:
            if p.role_code == "advokat" and p.user_id not in distracted_user_ids:
                lawyer_target_id = p.night_target_id

        # 8. Shpion (Spy) investigation report
        for p in alive:
            if p.role_code == "shpion" and p.user_id not in distracted_user_ids:
                if p.night_target_id and p.night_target_id in alive_map:
                    target_player = alive_map[p.night_target_id]
                    visitors = [v.full_name for v in alive if v.user_id != p.user_id and v.night_target_id == target_player.user_id]
                    if visitors:
                        vis_txt = ", ".join(visitors)
                        await self.send_dm(p.user_id, f"🕶️ <b>Ayg'oqchilik hisoboti:</b>\n{target_player.full_name}ning uyiga bu kecha <b>{vis_txt}</b> keldi!")
                    else:
                        await self.send_dm(p.user_id, f"🕶️ <b>Ayg'oqchilik hisoboti:</b>\n{target_player.full_name}ning uyiga bu kecha hech kim kelmadi.")

        # 9. Komissar investigation reports (also shared with Serjant)
        for p in alive:
            if p.role_code == "komissar" and p.user_id not in distracted_user_ids:
                if p.night_target_id in alive_map:
                    target_player = alive_map[p.night_target_id]
                    t_role = ROLES[target_player.role_code]
                    if target_player.has_mask or target_player.user_id == lawyer_target_id:
                        report = "🔍 <b>Tekshiruv natijasi:</b> Bu shaxs toza, shahar fuqarosi!"
                    elif t_role.team == Team.MAFIA:
                        report = f"🚨 <b>Tekshiruv natijasi:</b> DIQQAT! {target_player.full_name} — <b>MAFIYA a'zosi!</b>"
                    elif t_role.team == Team.MANIAC:
                        report = f"🚨 <b>Tekshiruv natijasi:</b> DIQQAT! {target_player.full_name} — <b>QONXO'R QOTIL!</b>"
                    else:
                        report = f"🔍 <b>Tekshiruv natijasi:</b> {target_player.full_name} — Tinch shahar vakili."
                    await self.send_dm(p.user_id, report)
                    for s in alive:
                        if s.role_code == "serjant":
                            await self.send_dm(s.user_id, f"🕵️‍♂️ <b>Komissar surishtiruvi hisoboti:</b>\n{report}")

        # 10. Sehrgar (Nekromant / Tirilish)
        for p in alive:
            if p.role_code == "sehrgar" and p.user_id not in distracted_user_ids:
                if p.night_target_id and p.night_target_id in self.players:
                    t_dead = self.players[p.night_target_id]
                    if not t_dead.is_alive:
                        t_dead.is_alive = True
                        await self.broadcast_group(
                            f"🧙‍♂️ <b>SEHRGAR MO'JIZASI!</b>\n"
                            f"Sehrgar o'lim komasidagi {t_dead.tag}ni tiriltirib hayotga qaytardi!"
                        )
                        break

        # Collect victims (1-tunda, ya'ni Tanishuv tunida qotillik sodir bo'lmaydi)
        killed_ids = set()
        if self.round_number > 1:
            if mafia_target_id and mafia_target_id in alive_map:
                killed_ids.add(mafia_target_id)
            if maniac_target_id and maniac_target_id in alive_map:
                killed_ids.add(maniac_target_id)

        # Check if saved by heal, shield or items
        actually_killed: List[Player] = []
        for vid in killed_ids:
            victim = alive_map[vid]
            if vid == healed_user_id:
                continue
            if victim.has_shield:
                victim.has_shield = False
                await self.send_dm(vid, "🛡️ <b>Qalqoningiz bu kecha sizni o'limdan saqlab qoldi!</b>")
                continue

            inv = await db.get_inventory(vid)
            # Protection from Maniac
            if vid == maniac_target_id:
                has_maniac_prot = any(it["code"] == "qotil_himoya" and it["quantity"] > 0 for it in inv)
                if has_maniac_prot:
                    await db.consume_inventory_item(vid, "qotil_himoya", 1)
                    await self.send_dm(vid, "⛑️ <b>Qotilga qarshi himoyangiz sizni Maniak hujumidan saqlab qoldi!</b>")
                    continue

            # Omadli tanga chance
            has_lucky_coin = any(it["code"] == "omadli_tanga" and it["quantity"] > 0 for it in inv)
            if has_lucky_coin and random.random() < 0.35:
                await self.send_dm(vid, "🎲 <b>Omadli tanga tufayli suiqasddan mo'jizaviy qutulib qoldingiz!</b>")
                continue

            # Mashinalar orqali suiqasddan qochish ehtimoli
            car_rates = [
                ("mashina_rolls", 0.50, "👑 Rolls-Royce Phantom"),
                ("mashina_porsche", 0.40, "🏎️ Porsche 911"),
                ("mashina_gelik", 0.35, "🚙 Mercedes Gelik"),
                ("mashina_bmw", 0.30, "🏎️ BMW M5 F90"),
                ("mashina_malibu", 0.25, "🚔 Chevrolet Malibu 2"),
                ("mashina_kaban", 0.20, "🚘 Mercedes W140 ('Kaban')"),
                ("mashina_monza", 0.18, "🚗 Chevrolet Monza"),
                ("mashina_gentra", 0.15, "🚙 Chevrolet Gentra"),
                ("mashina_nexia", 0.12, "🚙 Daewoo Nexia 2"),
                ("mashina_matiz", 0.10, "🚗 Daewoo Matiz"),
            ]
            car_escaped = False
            for car_code, chance, car_title in car_rates:
                if any(it["code"] == car_code and it["quantity"] > 0 for it in inv):
                    if random.random() < chance:
                        await self.send_dm(vid, f"🏎️ <b>{car_title} mashinangizda gazni bosib, tungi suiqasddan qochib qoldingiz!</b>")
                        car_escaped = True
                        break
            if car_escaped:
                continue

            victim.is_alive = False
            actually_killed.append(victim)

            # Konchi explosion revenge!
            if victim.role_code == "konchi":
                killer_id = mafia_target_id if vid == mafia_target_id else maniac_target_id
                if killer_id and killer_id in alive_map and killer_id != vid:
                    killer = alive_map[killer_id]
                    killer.is_alive = False
                    actually_killed.append(killer)

        # Sergeant promotion if Komissar dead
        komissar_dead = any(p.role_code == "komissar" and not p.is_alive for p in self.players.values())
        if komissar_dead:
            for p in self.get_alive_players():
                if p.role_code == "serjant":
                    p.role_code = "komissar"
                    await self.send_dm(p.user_id, "⭐ <b>Komissar halok bo'ldi!</b> Endi siz shahar Komissarisiz va har kecha tekshira olasiz!")

        # Announce morning results
        await self.run_day_phase(actually_killed)

    async def run_day_phase(self, night_killed: List[Player]):
        self.state = "DAY_TALK"
        morning_msg = f"☀️ <b>{self.round_number}-KUN YORISHDI!</b> ☀️\n\n"

        if night_killed:
            victims_str = "\n".join([f"⚰️ {p.tag} ({ROLES[p.role_code].emoji} <b>{ROLES[p.role_code].name}</b>)" for p in night_killed])
            morning_msg += f"💀 <b>KECHASI QOTILLIK SODIR BO'LDI! HALOK BO'LGANLAR:</b>\n{victims_str}\n\n"
        else:
            if self.round_number == 1:
                morning_msg += "🎉 <b>Tanishuv tuni ortda qoldi! Barcha fuqarolar omon!</b>\nEndi bir-biringiz bilan fikr almashib, oramizdagi Mafiyani fosh qilish vaqti keldi!\n\n"
            else:
                morning_msg += "🎉 <b>Xushxabar!</b> Bu kecha hech kim qurbon bo'lmadi, shahar omon qoldi!\n\n"

        alive = self.get_alive_players()
        morning_msg += f"👥 <b>Tirik qolganlar ({len(alive)} kishi):</b>\n"
        morning_msg += "\n".join([f"• {p.tag}" for p in alive])

        settings = await db.get_group_settings(self.chat_id)
        talk_time = min(25, settings.get("talk_time", DAY_TALK_TIMEOUT))
        morning_msg += f"\n\n💬 <b>Tonggi muhokama:</b> {talk_time} soniya.\n<i>(Shundan so'ng shahar sudi (ovoz berish) o'zi avtomatik boshlanadi!)</i>"
        # Kunduzi guruh a'zolariga yozishga ruxsat beriladi (Unmute)
        if self.chat_id < 0:
            try:
                await self.bot.set_chat_permissions(
                    self.chat_id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True
                    )
                )
            except Exception:
                pass

        early_vote_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="⚖️ Ovoz berishni darhol boshlash", callback_data=f"early_vote_{self.chat_id}")]
        ])
        await self.broadcast_group(morning_msg, reply_markup=early_vote_kb)

        # Broadcast Last Will if any killed player left one!
        if night_killed:
            for victim in night_killed:
                will = await db.get_last_will(victim.user_id)
                if will:
                    await self.broadcast_group(
                        f"📜 <b>{victim.tag}ning So'nggi Vasiyatnomasi:</b>\n"
                        f"<i>\"{will}\"</i>"
                    )

        # Check win condition immediately
        if await self.check_win_condition():
            return

        # Day discussion timer with /vote early skip support
        self.talk_event = asyncio.Event()
        try:
            await asyncio.wait_for(self.talk_event.wait(), timeout=talk_time)
        except asyncio.TimeoutError:
            pass

        # Transition to Voting phase
        await self.run_voting_phase()

    async def run_voting_phase(self):
        self.state = "DAY_VOTE"
        alive = self.get_alive_players()

        settings = await db.get_group_settings(self.chat_id)
        vote_time = settings.get("vote_time", VOTE_TIMEOUT)

        # Reset votes and assign AI bot votes
        for p in alive:
            p.vote_target_id = None
            if p.is_bot:
                targets = [t for t in alive if t.user_id != p.user_id]
                if targets and random.random() > 0.3:
                    p.vote_target_id = random.choice(targets).user_id
                else:
                    p.vote_target_id = -1

        buttons = []
        row = []
        for p in alive:
            row.append(InlineKeyboardButton(text=f"⚖️ {p.full_name[:12]}", callback_data=f"vote_{self.chat_id}_{p.user_id}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        buttons.append([InlineKeyboardButton(text="⏭️ O'tkazib yuborish (Skip)", callback_data=f"vote_{self.chat_id}_skip")])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        msg = await self.broadcast_group(
            f"⚖️ <b>SUD VA OVOZ BERISH BOSHLANDI!</b> ⚖️\n\n"
            f"Shubha ostidagi kimsani osish uchun pastdagi tugmalar orqali ovoz bering!\n"
            f"🏛️ <i>Rais ovozi 2 barobar kuchga ega!</i>\n"
            f"⏳ <b>Vaqt:</b> {vote_time} soniya.",
            reply_markup=kb
        )
        if msg:
            self.vote_message_id = msg.message_id

        vote_start = time.time()
        self.vote_event = asyncio.Event()
        if self.check_all_votes_done():
            self.vote_event.set()

        try:
            await asyncio.wait_for(self.vote_event.wait(), timeout=vote_time)
        except asyncio.TimeoutError:
            pass

        # Minimum suspense duration so voting doesn't vanish instantly
        elapsed = time.time() - vote_start
        min_vote_pause = min(10, vote_time)
        if elapsed < min_vote_pause:
            await asyncio.sleep(min_vote_pause - elapsed)

        await self.tally_votes()

    async def tally_votes(self):
        alive = self.get_alive_players()
        alive_map = {p.user_id: p for p in alive}

        # Anti-AFK check
        for p in alive:
            if not p.is_bot:
                if p.vote_target_id is None:
                    p.afk_rounds += 1
                else:
                    p.afk_rounds = 0
                if p.afk_rounds >= 2 and p.is_alive:
                    p.is_alive = False
                    await self.broadcast_group(
                        f"💤 <b>AFK O'YINCHI CHETLATILDI!</b>\n"
                        f"{p.tag} ketma-ket 2 marta ovoz berishda qatnashmagani uchun o'yindan chetlatildi!"
                    )

        vote_counts: Dict[int, int] = {}
        skip_count = 0

        for p in alive:
            if not p.is_alive:
                continue
            if p.vote_target_id == -1:
                skip_count += 1
            elif p.vote_target_id in alive_map:
                weight = 1
                if p.role_code == "rais":
                    weight += 1 # Rais 2x vote
                weight += p.extra_votes # Extra vote items
                vote_counts[p.vote_target_id] = vote_counts.get(p.vote_target_id, 0) + weight

        # Check max vote
        executed_player: Optional[Player] = None
        if vote_counts:
            sorted_votes = sorted(vote_counts.items(), key=lambda x: x[1], reverse=True)
            top_target_id, top_votes = sorted_votes[0]

            # Need at least 2 votes to lynch
            if top_votes > skip_count and top_votes >= 2:
                # Check for tie
                if len(sorted_votes) > 1 and sorted_votes[1][1] == top_votes:
                    await self.broadcast_group(
                        f"⚖️ <b>Ovozlar teng keldi!</b> ({top_votes} ta ovoz).\nHech kim osilmadi, shahar qarorga kela olmadi."
                    )
                else:
                    candidate = alive_map[top_target_id]

                    # 10s Defense phase / Oqlanish nutqi
                    await self.broadcast_group(
                        f"⚖️ <b>SUDNING DASTLABKI HUKMI!</b>\n\n"
                        f"Ko'pchilik ovozi bilan {candidate.tag} osilish arafasida!\n"
                        f"⏳ <b>10 soniya oqlanish va so'nggi so'z beriladi...</b>"
                    )
                    await asyncio.sleep(10)

                    # Check osilish_himoya (Защита от повешения)
                    inv = await db.get_inventory(candidate.user_id)
                    has_rope_prot = any(it["code"] == "osilish_himoya" and it["quantity"] > 0 for it in inv)
                    if has_rope_prot:
                        await db.consume_inventory_item(candidate.user_id, "osilish_himoya", 1)
                        await self.broadcast_group(
                            f"⚖️ <b>HIMOYA ISHLADI! ARQON UZILIB KETDI!</b>\n\n"
                            f"{candidate.tag}ning bo'ynidagi arqon uzildi! U mo'jizaviy tarzda dor ostidan omon qoldi!"
                        )
                    else:
                        candidate.is_alive = False
                        executed_player = candidate
                        r = ROLES[executed_player.role_code]
                        await self.broadcast_group(
                            f"🪢 <b>SHAHAR SUDI HUKMI IJRO ETILDI!</b>\n\n"
                            f"{executed_player.tag} dorga osildi!\n"
                            f"Uning roli: {r.emoji} <b>{r.name}</b> edi!"
                        )

                        # Last will on lynching
                        will = await db.get_last_will(executed_player.user_id)
                        if will:
                            await self.broadcast_group(
                                f"📜 <b>{executed_player.tag}ning Dor Ostidagi So'nggi Vasiyati:</b>\n"
                                f"<i>\"{will}\"</i>"
                            )

                        # Terrorist blast check on vote
                        if executed_player.role_code == "terrorist":
                            voters = [p for p in alive if p.vote_target_id == executed_player.user_id and p.is_alive and p.user_id != executed_player.user_id]
                            if voters:
                                t_vic = random.choice(voters)
                                t_vic.is_alive = False
                                await self.broadcast_group(
                                    f"🧨 <b>TERRORIST PORTLASHI!</b>\n"
                                    f"Terrorist osilish arafasida o'ziga ovoz bergan {t_vic.tag}ni ham portlatib yubordi!"
                                )

                        # Konchi blast check on vote
                        if executed_player.role_code == "konchi":
                            voters = [p for p in alive if p.vote_target_id == executed_player.user_id and p.is_alive]
                            if voters:
                                victim = voters[0]
                                victim.is_alive = False
                                await self.broadcast_group(
                                    f"💣 <b>KONCHI PORTLASHI!</b>\n"
                                    f"Konchi o'lar chog'ida o'ziga ovoz bergan {victim.tag}ni ham portlatib yubordi!"
                                )
            else:
                await self.broadcast_group("⚖️ <b>Sud natijasi:</b> Yetarli ovoz to'planmadi yoki 'O'tkazib yuborish' tanlandi. Hech kim osilmadi.")
        else:
            await self.broadcast_group("⚖️ Hech kim ovoz bermadi. Sud yakunlandi.")

        # Check poison death at end of day (with zardob antidote check)
        for p in self.get_alive_players():
            if p.is_poisoned:
                inv = await db.get_inventory(p.user_id)
                has_zardob = any(it["code"] == "zardob" and it["quantity"] > 0 for it in inv)
                if has_zardob:
                    await db.consume_inventory_item(p.user_id, "zardob", 1)
                    p.is_poisoned = False
                    await self.send_dm(p.user_id, "💊 <b>Zardob sizni zahar ta'siridan qutqardi!</b>")
                    continue
                p.is_alive = False
                p.is_poisoned = False
                await self.broadcast_group(
                    f"🧪 <b>Zahar ta'siri!</b>\n{p.tag} Ximikning halokatli zahari tufayli jon berdi!"
                )

        # Check lovers heartbreak
        if self.lovers:
            dead_lovers = [uid for uid in self.lovers if uid in alive_map and not alive_map[uid].is_alive]
            if dead_lovers:
                for uid in self.lovers:
                    if uid in alive_map and alive_map[uid].is_alive:
                        alive_map[uid].is_alive = False
                        await self.broadcast_group(
                            f"💔 <b>SEVGI FOJIASI!</b>\n"
                            f"{alive_map[uid].tag} sevgilisining o'limiga dosh berolmay qalb alamidan jon berdi!"
                        )

        if await self.check_win_condition():
            return

        # Start next night
        await asyncio.sleep(4)
        await self.run_night_phase()

    async def check_win_condition(self) -> bool:
        alive = self.get_alive_players()
        mafia_count = sum(1 for p in alive if ROLES[p.role_code].team == Team.MAFIA)
        maniac_count = sum(1 for p in alive if ROLES[p.role_code].team == Team.MANIAC)
        vampire_count = sum(1 for p in alive if ROLES[p.role_code].team == Team.VAMPIRE)
        citizen_count = sum(1 for p in alive if ROLES[p.role_code].team == Team.CITIZEN)
        total_alive = len(alive)

        winner: Optional[str] = None
        winner_team: Optional[Team] = None

        if total_alive == 0:
            winner = "🤝 <b>DURRANG!</b> Hamma halok bo'ldi, g'olib yo'q."
            winner_team = Team.NEUTRAL
        elif len(self.lovers) == 2 and total_alive == 2 and set(self.lovers) == set([p.user_id for p in alive]):
            winner = "💘 <b>SEVISHGANLAR G'ALABA QOZONDI!</b>\nIkki oshiq barcha xavflardan omon qolib, g'alabaga erishdi!"
            winner_team = Team.NEUTRAL
        elif mafia_count >= (total_alive - mafia_count) and maniac_count == 0 and vampire_count == 0:
            # 1-raund kunduzgi muhokama va sud paytida o'yin birdan tugab qolmasligi uchun
            if self.round_number <= 1 and self.state in ["DAY_TALK", "DAY_VOTE"] and citizen_count > 0:
                return False
            winner = "🎩 <b>MAFIYA G'ALABA QOZONDI!</b>\nShahar to'liq mafiya nazorati ostiga o'tdi!"
            winner_team = Team.MAFIA
        elif mafia_count == 0 and maniac_count == 0 and vampire_count == 0:
            winner = "🏆 <b>SHAHAR FUQAROLARI G'ALABA QOZONDI!</b>\nBarcha yovuzlar va qotillar yo'q qilindi!"
            winner_team = Team.CITIZEN
        elif maniac_count == 1 and total_alive <= 2:
            winner = "🔪 <b>QOTIL (MANIAK) G'ALABA QOZONDI!</b>\nU hammadan omon qolib, qonli qasosini oldi!"
            winner_team = Team.MANIAC
        elif vampire_count >= 1 and mafia_count == 0 and citizen_count == 0:
            winner = "🧛‍♂️ <b>VAMPIRLAR G'ALABA QOZONDI!</b>\nZulmat saltanati qaror topdi!"
            winner_team = Team.VAMPIRE

        if winner:
            self.state = "GAME_OVER"
            await self.end_game(winner, winner_team)
            return True
        return False

    def format_player_end_game_card(
        self,
        player_tag: str,
        pul_diff: int,
        xp_diff: int,
        user_data: Dict[str, Any],
        inventory: List[Dict[str, Any]],
        active_role: str = "Нет",
        has_sponsor_bonus: bool = False
    ) -> str:
        inv_map = {item["code"]: item["quantity"] for item in inventory}

        pul = user_data.get("pul", 0)
        almaz = user_data.get("almaz", 0)
        gold = 0

        qalqon = inv_map.get("qalqon", 0)
        hujjat = inv_map.get("hujjat", 0)
        osilish = inv_map.get("osilish_himoya", 0)
        qotil = inv_map.get("qotil_himoya", 0)
        miltiq = inv_map.get("miltiq", 0)
        zardob = inv_map.get("zardob", 0)
        niqob = inv_map.get("niqob", 0)
        qopqon = inv_map.get("qopqon_himoya", 0)
        qahramon = inv_map.get("qahramon_himoya", 0)

        games_won = user_data.get("games_won", 0)
        games_played = user_data.get("games_played", 0)

        pul_sign = f"{pul_diff}" if pul_diff <= 0 else f"{pul_diff}"
        xp_sign = f"{xp_diff}" if xp_diff <= 0 else f"{xp_diff}"
        bonus_msg = "✅ <b>Вы подписаны на канал: Награда x2 получена!</b>" if has_sponsor_bonus else "Если вы подпишетесь на канал , вы получите награду x2!"

        card = (
            f"🏁 <b>Игра окончена.</b>\n"
            f"Вам начислено 💵 {pul_sign} и 🎯 {xp_sign}!\n\n"
            f"👤 {player_tag}\n\n"
            f"💵 Доллары: {pul}\n"
            f"💎 Алмазы: {almaz}\n"
            f"💰 Золото: {gold}\n\n"
            f"🛡 Защита: {qalqon}\n"
            f"📁 Документы: {hujjat}\n"
            f"⚖️ Защита от повешения: {osilish}\n"
            f"⛑️ Защита от убийцы: {qotil}\n"
            f"🔫 Винтовка: {miltiq}\n"
            f"💊 Защита от зелья: {zardob}\n"
            f"🎭 Маска: {niqob}\n"
            f"🪤 Защита от скольжения: {qopqon}\n"
            f"🔰 Защита от героя: {qahramon}\n\n"
            f"🎯 Победы: {games_won}\n"
            f"🎲 Всего игр: {games_played}\n\n"
            f"🃏 Активные роли: {active_role}\n\n"
            f"{bonus_msg}"
        )
        return card

    async def end_game(self, winner_announcement: str, winner_team: Optional[Team]):
        # Categorize winners and losers/dead with tags
        winners = []
        losers_and_dead = []

        for p in self.players.values():
            r = ROLES[p.role_code]
            is_winner = (winner_team and r.team == winner_team)
            status_text = "✅ Tirik" if p.is_alive else "💀 O'lgan"
            if is_winner:
                winners.append(f"• 🏆 {p.tag} — {r.emoji} <b>{r.name}</b> ({status_text})")
            else:
                losers_and_dead.append(f"• 💀 {p.tag} — {r.emoji} <b>{r.name}</b> ({status_text})")

        winners_text = "\n".join(winners) if winners else "<i>Hech kim g'olib bo'lmadi</i>"
        losers_text = "\n".join(losers_and_dead) if losers_and_dead else "<i>Mag'lublar yo'q</i>"
        player_cards = []

        # Distribute XP, Pul and update quests
        for p in self.players.values():
            r = ROLES[p.role_code]
            is_winner = (winner_team and r.team == winner_team)

            if is_winner:
                base_pul = 30 if p.is_alive else 20
                base_xp = 30 if p.is_alive else 20
            else:
                base_pul = 5
                base_xp = 5

            if p.is_bot:
                card_text = self.format_player_end_game_card(
                    player_tag=p.tag,
                    pul_diff=base_pul,
                    xp_diff=base_xp,
                    user_data={"pul": 1000, "almaz": 5, "games_won": 1, "games_played": 1},
                    inventory=[],
                    active_role="🤖 Бот"
                )
                player_cards.append((p.user_id, card_text))
                continue

            # Check sponsor channel for x2 bonus
            has_sponsor = False
            from config import SPONSOR_CHANNEL
            if SPONSOR_CHANNEL:
                try:
                    cm = await self.bot.get_chat_member(chat_id=SPONSOR_CHANNEL, user_id=p.user_id)
                    if cm.status in ["member", "administrator", "creator"]:
                        has_sponsor = True
                except Exception:
                    pass

            if has_sponsor:
                base_pul *= 2
                base_xp = base_xp * 2 if base_xp > 0 else base_xp

            # Check VIP status for 1.5x multiplier
            u = await db.get_user(p.user_id)
            is_vip = u and u.get("vip_until", 0) > time.time()
            if is_vip:
                base_xp = int(base_xp * 1.5) if base_xp > 0 else base_xp
                base_pul = int(base_pul * 1.5)

            await db.update_balance(p.user_id, pul_diff=base_pul)
            xp_res = await db.add_xp(p.user_id, max(0, base_xp))

            # Quests & Achievements
            await db.progress_quest(p.user_id, "play_game", 1)
            if is_winner:
                await db.progress_quest(p.user_id, "win_game", 1)
                await db.unlock_achievement(p.user_id, "first_blood")
                if r.team == Team.MAFIA:
                    await db.unlock_achievement(p.user_id, "godfather")
                if r.team == Team.CITIZEN and p.role_code == "komissar":
                    await db.unlock_achievement(p.user_id, "sherlock")

            # Update stats
            async with aiosqlite.connect(db.db_path) as conn:
                won_add = 1 if is_winner else 0
                await conn.execute("""
                    UPDATE users
                    SET games_played = games_played + 1, games_won = games_won + ?
                    WHERE id = ?;
                """, (won_add, p.user_id))
                await conn.commit()

            # Format player end-game card matching user template with player tag
            updated_u = await db.get_user(p.user_id) or {}
            inv = await db.get_inventory(p.user_id)
            active_role = "👑 VIP" if is_vip else (updated_u.get("custom_title") or "Нет")

            card_text = self.format_player_end_game_card(
                player_tag=p.tag,
                pul_diff=base_pul,
                xp_diff=base_xp,
                user_data=updated_u,
                inventory=inv,
                active_role=active_role,
                has_sponsor_bonus=has_sponsor
            )
            player_cards.append((p.user_id, card_text))

            # Send to player's private chat (DM)
            await self.send_dm(p.user_id, card_text)

            # If user leveled up, send notification to DM
            if xp_res.get("leveled_up"):
                for r_item in xp_res.get("rewards", []):
                    msg = format_level_up_message(xp_res["new_level"], r_item["msg"])
                    await self.send_dm(p.user_id, msg)

        # Record in DB logs
        await db.record_game_end(self.chat_id, winner_team.value if winner_team else "none", len(self.players))

        # O'yin tugaganda guruhdagi mute butunlay yechiladi
        if self.chat_id < 0:
            try:
                await self.bot.set_chat_permissions(
                    self.chat_id,
                    ChatPermissions(
                        can_send_messages=True,
                        can_send_media_messages=True,
                        can_send_other_messages=True
                    )
                )
            except Exception:
                pass

        final_msg = (
            f"🏁 <b>O'yin yakunlandi!</b>\n\n"
            f"{winner_announcement}\n\n"
            f"🏆 <b>G'OLIBLAR (YUTGANLAR):</b>\n"
            f"{winners_text}\n\n"
            f"💀 <b>HALOK BO'LGANLAR VA MAG'LUBLAR:</b>\n"
            f"{losers_text}\n\n"
            f"📩 <i>Har bir o'yinchining shaxsiy hisoboti, pul va darajalari shaxsiy lichkasiga yuborildi!</i>"
        )
        await self.broadcast_group(final_msg)

        game_manager.remove_room(self.chat_id)

class GameManager:
    def __init__(self):
        self.rooms: Dict[int, GameRoom] = {}

    def get_room(self, chat_id: int) -> Optional[GameRoom]:
        return self.rooms.get(chat_id)

    def create_room(self, chat_id: int, bot: Bot) -> GameRoom:
        room = GameRoom(chat_id, bot)
        self.rooms[chat_id] = room
        return room

    def remove_room(self, chat_id: int):
        if chat_id in self.rooms:
            del self.rooms[chat_id]

game_manager = GameManager()
