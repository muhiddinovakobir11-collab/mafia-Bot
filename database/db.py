import aiosqlite
import time
from typing import Optional, List, Dict, Any, Tuple
from config import DB_PATH, ADMIN_IDS

DEFAULT_ITEMS = [
    ("qalqon", "🛡️ Qalqon (Bronjilet)", "🛡️", "Tungi bitta suiqasddan 100% himoya qiladi (1 martalik).", 2500, 5, 1),
    ("durbin", "🔍 Durbin (Ayg'oqchi)", "🔍", "Kechasi istalgan bitta o'yinchining rolini bilish (1 martalik).", 3500, 8, 1),
    ("extra_vote", "🗳️ +2 Ovoz (Katta ta'sir)", "🗳️", "Kunduzgi sud ovozida sizga +2 ta qo'shimcha ovoz kuchi beradi.", 2000, 4, 1),
    ("niqob", "🎭 Niqob (Soxta shaxs)", "🎭", "Komissar tekshirganda 'Tinch aholi' bo'lib ko'rinadi (1 o'yin).", 3000, 6, 1),
    ("zardob", "💉 Zardob (Antidot)", "💉", "Ximik zahari yoki Vampir chaqishidan to'liq shifo beradi.", 1800, 3, 1),
    ("adrenalin", "⚡ Adrenalin", "⚡", "O'ldirilsa ham darhol halok bo'lmaydi, ertasi kuni ovoz bera oladi.", 4000, 10, 1),
    ("mute", "🤫 Sukunat ichimligi", "🤫", "Keyingi kunduzgi bahsda tanlangan o'yinchini gapirishdan to'xtatadi.", 2200, 5, 1),
    ("omadli_tanga", "🎲 Omadli tanga", "🎲", "35% ehtimol bilan tunda o'qdan yoki kunduzi osilishdan qutqaradi.", 5000, 12, 1),
    ("hujjat", "📁 Qalbaki Hujjatlar", "📁", "Komissar tekshiruvidan to'liq himoya (Hujjatlar).", 2500, 5, 1),
    ("osilish_himoya", "⚖️ Osilishdan himoya", "⚖️", "Kunduzgi osilishdan 1 marta qutqaradi.", 3000, 6, 1),
    ("qotil_himoya", "⛑️ Qotildan himoya", "⛑️", "Maniak suiqasdidam 1 marta himoya.", 3000, 6, 1),
    ("miltiq", "🔫 Miltiq (Vintovka)", "🔫", "Tunda qo'shimcha o'q uzish imkoniyati.", 4500, 10, 1),
    ("qopqon_himoya", "🪤 Qopqondan himoya", "🪤", "Kechasi tuzoqlardan himoya.", 2000, 4, 1),
    ("qahramon_himoya", "🔰 Qahramondan himoya", "🔰", "Qahramon hujumidan himoya.", 2500, 5, 1),
    ("vip_7", "👑 VIP Status (7 kun)", "👑", "Ism yonida 👑 toji, 1.5x XP va Pul, har kuni 2 tadan bepul Almaz.", 0, 25, 1),
    ("vip_30", "👑 VIP Status (30 kun)", "👑", "Ism yonida 👑 toji, 1.5x XP va Pul, har kuni 2 tadan bepul Almaz.", 0, 75, 1),
    ("nikoh_uzuk", "💍 Oltin Nikoh Uzugi", "💍", "Sevgan insoningiz bilan turmush qurish uchun uzuk.", 5000, 10, 1),
    ("mashina_matiz", "🚗 Daewoo Matiz ('Tezkor')", "🚗", "Kichik va chaqqon shahar mashinasi. Tungi suiqasddan 10% qochish imkoniyati.", 5000, 10, 1),
    ("mashina_nexia", "🚙 Daewoo Nexia 2 ('Xalqona')", "🚙", "Haqiqiy xalqona mashina. Tungi suiqasddan 12% qochish imkoniyati.", 7000, 15, 1),
    ("mashina_gentra", "🚙 Chevrolet Gentra ('Qora Gentra')", "🚙", "Mafiozlarning sevimli mashinasi. Tungi suiqasddan 15% qochish imkoniyati.", 10000, 20, 1),
    ("mashina_monza", "🚗 Chevrolet Monza", "🚗", "Zamonaviy shahar mashinasi. Tungi suiqasddan 18% qochish imkoniyati.", 12000, 25, 1),
    ("mashina_kaban", "🚘 Mercedes W140 ('Kaban')", "🚘", "Klassik 90-yillar afsonasi. Tungi suiqasddan 20% qochish imkoniyati.", 15000, 30, 1),
    ("mashina_malibu", "🚔 Chevrolet Malibu 2 ('Black Edition')", "🚔", "Hashamatli biznes sedan. Tungi suiqasddan 25% qochish imkoniyati.", 22000, 45, 1),
    ("mashina_bmw", "🏎️ BMW M5 F90", "🏎️", "Tezkor mafiya poygachisi. Tungi suiqasddan 30% qochish imkoniyati.", 30000, 60, 1),
    ("mashina_gelik", "🚙 Mercedes-Benz G63 ('Gelik / G-Wagen')", "🚙", "Zirhlangan mafiya jipi. Tungi suiqasddan 35% qochish imkoniyati.", 50000, 100, 1),
    ("mashina_porsche", "🏎️ Porsche 911 Turbo S", "🏎️", "Gipertezlikdagi sportkar. Tungi suiqasddan 40% qochish imkoniyati.", 80000, 150, 1),
    ("mashina_rolls", "👑 Rolls-Royce Phantom ('Don Karleone')", "👑", "Eng hashamatli mafioz limuzini. Tungi suiqasddan 50% qochish imkoniyati!", 150000, 300, 1),
    ("signalizatsiya", "🚨 O'g'rilikdan signalizatsiya", "🚨", "Cho'ntakkesarlardan 100% himoya (1 martalik).", 2000, 4, 1),
]

DEFAULT_STAR_PACKAGES = [
    ("almaz", 25, 12, 0, "💎 12 Almaz", 1),
    ("almaz", 50, 25, 5, "💎 30 Almaz (+5 bonus)", 1),
    ("almaz", 100, 65, 15, "💎 80 Almaz (+15 bonus)", 1),
    ("almaz", 250, 175, 50, "💎 225 Almaz (+50 bonus)", 1),
    ("almaz", 500, 400, 150, "💎 550 Almaz (+150 bonus)", 1),
    ("pul", 25, 10000, 1000, "💰 11,000 Pul", 1),
    ("pul", 50, 25000, 5000, "💰 30,000 Pul (+5,000 bonus)", 1),
    ("pul", 100, 60000, 15000, "💰 75,000 Pul (+15,000 bonus)", 1),
    ("pul", 250, 180000, 50000, "💰 230,000 Pul (+50,000 bonus)", 1),
]

DEFAULT_CARD_PACKAGES = [
    ("almaz", 10, 0, 1000, "💎 10 Almaz", 1),
    ("almaz", 50, 5, 5000, "💎 55 Almaz (+5 bonus)", 1),
    ("almaz", 100, 15, 10000, "💎 115 Almaz (+15 bonus)", 1),
    ("almaz", 250, 50, 25000, "💎 300 Almaz (+50 bonus)", 1),
    ("almaz", 500, 150, 50000, "💎 650 Almaz (+150 bonus)", 1),
    ("pul", 100, 0, 500, "💰 100 Pul", 1),
    ("pul", 200, 0, 1000, "💰 200 Pul", 1),
    ("pul", 1000, 50, 5000, "💰 1,050 Pul (+50 bonus)", 1),
    ("pul", 2500, 200, 10000, "💰 2,700 Pul (+200 bonus)", 1),
    ("pul", 7000, 700, 25000, "💰 7,700 Pul (+700 bonus)", 1),
    ("pul", 15000, 2000, 50000, "💰 17,000 Pul (+2,000 bonus)", 1),
    ("vip", 30, 0, 15000, "👑 VIP Status (30 kun)", 1),
]

class Database:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path

    async def init(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("PRAGMA synchronous=NORMAL;")
            await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                phone_number TEXT DEFAULT '',
                pul INTEGER DEFAULT 1000,
                almaz INTEGER DEFAULT 5,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                is_banned INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                vip_until INTEGER DEFAULT 0,
                last_daily_bonus INTEGER DEFAULT 0,
                custom_title TEXT DEFAULT '',
                last_will TEXT DEFAULT '',
                referred_by INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Migrations for columns
            for col, col_type in [
                ("phone_number", "TEXT DEFAULT ''"),
                ("last_active", "TEXT DEFAULT ''"),
                ("rep", "INTEGER DEFAULT 0"),
                ("bank_pul", "INTEGER DEFAULT 0"),
                ("spouse_id", "INTEGER DEFAULT 0"),
                ("car", "TEXT DEFAULT ''"),
                ("language", "TEXT DEFAULT 'uz'"),
            ]:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {col} {col_type};")
                except Exception:
                    pass

            # Marriages
            await db.execute("""
            CREATE TABLE IF NOT EXISTS marriages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER UNIQUE,
                user2_id INTEGER UNIQUE,
                wedding_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                love_points INTEGER DEFAULT 0
            );
            """)

            # Group Settings
            await db.execute("""
            CREATE TABLE IF NOT EXISTS group_settings (
                chat_id INTEGER PRIMARY KEY,
                talk_time INTEGER DEFAULT 50,
                vote_time INTEGER DEFAULT 40,
                night_time INTEGER DEFAULT 40,
                is_anonymous_vote INTEGER DEFAULT 0,
                is_antispam INTEGER DEFAULT 1,
                disabled_roles TEXT DEFAULT ''
            );
            """)

            # Rep logs
            await db.execute("""
            CREATE TABLE IF NOT EXISTS rep_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER,
                to_user_id INTEGER,
                change INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Promo Codes
            await db.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                code TEXT PRIMARY KEY,
                reward_pul INTEGER DEFAULT 0,
                reward_almaz INTEGER DEFAULT 0,
                reward_xp INTEGER DEFAULT 0,
                max_uses INTEGER DEFAULT 100,
                used_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS user_promo_uses (
                user_id INTEGER,
                code TEXT,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, code)
            );
            """)


            await db.execute("""
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                name TEXT,
                icon TEXT,
                description TEXT,
                price_pul INTEGER DEFAULT 0,
                price_almaz INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS user_inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                item_code TEXT,
                quantity INTEGER DEFAULT 0,
                UNIQUE(user_id, item_code)
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS star_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_type TEXT,
                stars_price INTEGER,
                amount INTEGER,
                bonus INTEGER DEFAULT 0,
                title TEXT,
                is_active INTEGER DEFAULT 1
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS card_packages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_type TEXT,
                amount INTEGER,
                bonus INTEGER DEFAULT 0,
                price_uzs INTEGER,
                title TEXT,
                is_active INTEGER DEFAULT 1
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS card_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tx_id TEXT UNIQUE,
                user_id INTEGER,
                package_id INTEGER,
                item_type TEXT,
                item_amount INTEGER,
                price_uzs INTEGER,
                unique_amount INTEGER,
                card_number TEXT,
                card_holder TEXT,
                status TEXT DEFAULT 'pending',
                proof_file_id TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS game_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                winner_team TEXT,
                player_count INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Clans & Clan Members
            await db.execute("""
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                tag TEXT,
                description TEXT DEFAULT '',
                owner_id INTEGER,
                treasury_pul INTEGER DEFAULT 0,
                treasury_almaz INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                xp INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS clan_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_id INTEGER,
                user_id INTEGER UNIQUE,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Tournaments
            await db.execute("""
            CREATE TABLE IF NOT EXISTS tournaments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                entry_fee_stars INTEGER DEFAULT 0,
                entry_fee_pul INTEGER DEFAULT 0,
                prize_pool_pul INTEGER DEFAULT 0,
                prize_pool_almaz INTEGER DEFAULT 0,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Achievements
            await db.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                code TEXT PRIMARY KEY,
                title TEXT,
                icon TEXT,
                description TEXT,
                reward_pul INTEGER DEFAULT 0,
                reward_almaz INTEGER DEFAULT 0
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS user_achievements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                achievement_code TEXT,
                unlocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, achievement_code)
            );
            """)

            # Daily Quests
            await db.execute("""
            CREATE TABLE IF NOT EXISTS daily_quests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE,
                title TEXT,
                description TEXT,
                target_count INTEGER DEFAULT 1,
                reward_pul INTEGER DEFAULT 0,
                reward_almaz INTEGER DEFAULT 0,
                reward_xp INTEGER DEFAULT 0
            );
            """)

            await db.execute("""
            CREATE TABLE IF NOT EXISTS user_quest_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                quest_code TEXT,
                progress INTEGER DEFAULT 0,
                is_claimed INTEGER DEFAULT 0,
                date_key TEXT,
                UNIQUE(user_id, quest_code, date_key)
            );
            """)

            # 1v1 Duels
            await db.execute("""
            CREATE TABLE IF NOT EXISTS duels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                challenger_id INTEGER,
                opponent_id INTEGER,
                bet_type TEXT,
                bet_amount INTEGER,
                status TEXT DEFAULT 'pending',
                winner_id INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)

            # Seed default settings if not exists
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('almaz_to_pul_rate', '500');")

            # Seed default items
            for item in DEFAULT_ITEMS:
                await db.execute("""
                    INSERT OR IGNORE INTO items (code, name, icon, description, price_pul, price_almaz, is_active)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, item)

            # Seed default achievements
            default_achievements = [
                ("first_blood", "🩸 Birinchi Qadam", "🩸", "O'yinda ilk bor g'alaba qozonish", 1000, 2),
                ("sherlock", "🕵️‍♂️ Buyuk Sherlok", "🕵️‍♂️", "Komissar bo'lib mafiyani fosh qilish", 2500, 5),
                ("godfather", "🎩 Don Karleone", "🎩", "Mafiya safida 5 marta g'alaba qozonish", 5000, 15),
                ("survivor", "🛡️ Omon Qoluvchi", "🛡️", "10 ta o'yinda tirik qolish", 3000, 10),
                ("rich_boss", "💼 Katta Boy", "💼", "50,000 Pul to'plash", 5000, 20),
                ("clan_maker", "🏰 Oila Asoschisi", "🏰", "Shaxsiy Mafiya klanini tuzish", 2000, 5),
                ("duelist", "⚔️ Chaqqon Mergan", "⚔️", "3 ta 1v1 duelda g'alaba qozonish", 3000, 5),
                ("lucky", "🎰 Omadli O'yinchi", "🎰", "Kunlik omad charxpalagidan yutish", 1000, 2),
            ]
            for ach in default_achievements:
                await db.execute("""
                    INSERT OR IGNORE INTO achievements (code, title, icon, description, reward_pul, reward_almaz)
                    VALUES (?, ?, ?, ?, ?, ?);
                """, ach)

            # Seed default daily quests
            default_quests = [
                ("play_game", "🎮 Jang Maydoni", "Bugun 1 ta o'yinda qatnashing", 1, 500, 0, 30),
                ("win_game", "🏆 G'alaba Lazzati", "Bugun 1 ta o'yinda g'alaba qozoning", 1, 1000, 1, 50),
                ("spin_bonus", "🎁 Omadli Kun", "Kunlik bonusni oling", 1, 300, 0, 20),
                ("win_duel", "⚔️ Duel G'olibi", "1v1 Duelda raqibingizni mag'lub eting", 1, 1000, 2, 40),
            ]
            for q in default_quests:
                await db.execute("""
                    INSERT OR IGNORE INTO daily_quests (code, title, description, target_count, reward_pul, reward_almaz, reward_xp)
                    VALUES (?, ?, ?, ?, ?, ?, ?);
                """, q)


            # Seed default star packages
            for pkg in DEFAULT_STAR_PACKAGES:
                await db.execute("""
                    INSERT OR IGNORE INTO star_packages (package_type, stars_price, amount, bonus, title, is_active)
                    SELECT ?, ?, ?, ?, ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM star_packages WHERE package_type = ? AND stars_price = ?
                    );
                """, (pkg[0], pkg[1], pkg[2], pkg[3], pkg[4], pkg[5], pkg[0], pkg[1]))

            # Seed default settings for card payment
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card_number', '8600 0000 0000 0000');")
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card_holder', 'MAFIA ADMIN');")
            await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('card_bank', 'Kapitalbank / Uzcard');")

            # Seed default promo codes
            await db.execute("""
                INSERT OR IGNORE INTO promo_codes (code, reward_pul, reward_almaz, reward_xp, max_uses, used_count)
                VALUES ('MAFIA2026', 500, 5, 50, 500, 0);
            """)

            # Seed default card packages
            for c_pkg in DEFAULT_CARD_PACKAGES:
                await db.execute("""
                    INSERT OR IGNORE INTO card_packages (package_type, amount, bonus, price_uzs, title, is_active)
                    SELECT ?, ?, ?, ?, ?, ?
                    WHERE NOT EXISTS (
                        SELECT 1 FROM card_packages WHERE package_type = ? AND price_uzs = ? AND amount = ?
                    );
                """, (c_pkg[0], c_pkg[1], c_pkg[2], c_pkg[3], c_pkg[4], c_pkg[5], c_pkg[0], c_pkg[3], c_pkg[1]))

            # Ensure admin status for ADMIN_IDS
            for aid in ADMIN_IDS:
                await db.execute("UPDATE users SET is_admin = 1 WHERE id = ?;", (aid,))

            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE id = ?;", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_or_create_user(self, user_id: int, username: str = "", full_name: str = "", referred_by: int = 0) -> Dict[str, Any]:
        user = await self.get_user(user_id)
        if user:
            # Update username, full_name, and last_active
            async with aiosqlite.connect(self.db_path) as db:
                is_admin = 1 if user_id in ADMIN_IDS else user.get("is_admin", 0)
                await db.execute(
                    "UPDATE users SET username = ?, full_name = ?, is_admin = ?, last_active = CURRENT_TIMESTAMP WHERE id = ?;",
                    (username or user.get("username", ""), full_name or user.get("full_name", ""), is_admin, user_id)
                )
                await db.commit()
            return await self.get_user(user_id) # type: ignore

        is_admin = 1 if user_id in ADMIN_IDS else 0
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (id, username, full_name, pul, almaz, level, xp, is_admin, referred_by)
                VALUES (?, ?, ?, 1000, 5, 1, 0, ?, ?);
            """, (user_id, username, full_name, is_admin, referred_by))
            await db.commit()
        return await self.get_user(user_id) # type: ignore

    async def update_balance(self, user_id: int, pul_diff: int = 0, almaz_diff: int = 0) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users
                SET pul = MAX(0, pul + ?), almaz = MAX(0, almaz + ?)
                WHERE id = ?;
            """, (pul_diff, almaz_diff, user_id))
            await db.commit()
            return True

    async def set_balance(self, user_id: int, pul: Optional[int] = None, almaz: Optional[int] = None) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            if pul is not None and almaz is not None:
                await db.execute("UPDATE users SET pul = ?, almaz = ? WHERE id = ?;", (pul, almaz, user_id))
            elif pul is not None:
                await db.execute("UPDATE users SET pul = ? WHERE id = ?;", (pul, user_id))
            elif almaz is not None:
                await db.execute("UPDATE users SET almaz = ? WHERE id = ?;", (almaz, user_id))
            await db.commit()
            return True

    async def set_ban(self, user_id: int, is_banned: bool) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET is_banned = ? WHERE id = ?;", (1 if is_banned else 0, user_id))
            await db.commit()
            return True

    async def add_xp(self, user_id: int, xp_amount: int) -> Dict[str, Any]:
        """
        Adds XP and handles level progression.
        Returns level up info if leveled up.
        """
        user = await self.get_user(user_id)
        if not user:
            return {"leveled_up": False}

        current_level = user["level"]
        current_xp = user["xp"] + xp_amount

        # XP calculation formula: next_level_req = level * 250
        def xp_for_level(lvl: int) -> int:
            return lvl * 250

        leveled_up = False
        rewards = []

        while current_xp >= xp_for_level(current_level):
            current_xp -= xp_for_level(current_level)
            current_level += 1
            leveled_up = True

            # Balanced rewards per level
            if current_level == 2:
                rewards.append({"pul": 50, "almaz": 1, "item": None, "msg": "50 💰 Pul va 1 💎 Almaz"})
                await self.update_balance(user_id, pul_diff=50, almaz_diff=1)
            elif current_level == 3:
                rewards.append({"pul": 100, "almaz": 2, "item": None, "msg": "100 💰 Pul va 2 💎 Almaz"})
                await self.update_balance(user_id, pul_diff=100, almaz_diff=2)
            elif current_level == 4:
                rewards.append({"pul": 150, "almaz": 3, "item": None, "msg": "150 💰 Pul va 3 💎 Almaz"})
                await self.update_balance(user_id, pul_diff=150, almaz_diff=3)
            elif current_level == 5:
                rewards.append({"pul": 250, "almaz": 5, "item": "qalqon", "msg": "250 💰 Pul, 5 💎 Almaz va 🛡️ Qalqon"})
                await self.update_balance(user_id, pul_diff=250, almaz_diff=5)
                await self.add_inventory_item(user_id, "qalqon", 1)
            else:
                p = current_level * 40
                a = max(1, current_level // 2)
                rewards.append({"pul": p, "almaz": a, "item": None, "msg": f"{a} 💎 Almaz va {p} 💰 Pul"})
                await self.update_balance(user_id, pul_diff=p, almaz_diff=a)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET level = ?, xp = ? WHERE id = ?;", (current_level, current_xp, user_id))
            await db.commit()

        return {
            "leveled_up": leveled_up,
            "new_level": current_level,
            "rewards": rewards,
            "current_xp": current_xp,
            "needed_xp": xp_for_level(current_level)
        }

    async def set_user_language(self, user_id: int, language: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET language = ? WHERE id = ?;", (language, user_id))
            await db.commit()
            return True

    async def get_user_language(self, user_id: int) -> str:
        user = await self.get_user(user_id)
        if user and user.get("language"):
            return user["language"]
        return "uz"

    async def edit_user_profile(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        custom_title: Optional[str] = None,
        level: Optional[int] = None,
        xp: Optional[int] = None,
        rep: Optional[int] = None,
        vip_days: Optional[int] = None,
        pul: Optional[int] = None,
        almaz: Optional[int] = None
    ) -> bool:
        user = await self.get_user(user_id)
        if not user:
            return False

        fields = []
        params = []
        if full_name is not None and full_name.strip():
            fields.append("full_name = ?")
            params.append(full_name.strip())
        if custom_title is not None:
            fields.append("custom_title = ?")
            params.append(custom_title.strip())
        if level is not None:
            fields.append("level = ?")
            params.append(level)
        if xp is not None:
            fields.append("xp = ?")
            params.append(xp)
        if rep is not None:
            fields.append("rep = ?")
            params.append(rep)
        if pul is not None:
            fields.append("pul = ?")
            params.append(pul)
        if almaz is not None:
            fields.append("almaz = ?")
            params.append(almaz)
        if vip_days is not None:
            now = int(time.time())
            current_vip = user.get("vip_until") or 0
            base = max(now, current_vip)
            new_vip = base + (vip_days * 86400) if vip_days > 0 else 0
            fields.append("vip_until = ?")
            params.append(new_vip)

        if not fields:
            return True

        params.append(user_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?;", params)
            await db.commit()
            return True

    async def get_user_cars(self, user_id: int) -> List[Dict[str, Any]]:
        inv = await self.get_inventory(user_id)
        return [it for it in inv if it["code"].startswith("mashina_") and it["quantity"] > 0]

    async def get_items(self, only_active: bool = True) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            q = "SELECT * FROM items WHERE is_active = 1;" if only_active else "SELECT * FROM items;"
            async with db.execute(q) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_item_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM items WHERE code = ?;", (code,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_item(self, code: str, name: str, price_pul: int, price_almaz: int, description: str, is_active: int = 1) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE items
                SET name = ?, price_pul = ?, price_almaz = ?, description = ?, is_active = ?
                WHERE code = ?;
            """, (name, price_pul, price_almaz, description, is_active, code))
            await db.commit()
            return True

    async def get_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT i.code, i.name, i.icon, i.description, inv.quantity
                FROM user_inventory inv
                JOIN items i ON inv.item_code = i.code
                WHERE inv.user_id = ? AND inv.quantity > 0;
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def add_inventory_item(self, user_id: int, item_code: str, quantity: int = 1) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO user_inventory (user_id, item_code, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id, item_code)
                DO UPDATE SET quantity = quantity + ?;
            """, (user_id, item_code, quantity, quantity))
            await db.commit()
            return True

    async def consume_inventory_item(self, user_id: int, item_code: str, quantity: int = 1) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT quantity FROM user_inventory WHERE user_id = ? AND item_code = ?;", (user_id, item_code)) as cursor:
                row = await cursor.fetchone()
                if not row or row["quantity"] < quantity:
                    return False
            await db.execute("""
                UPDATE user_inventory
                SET quantity = quantity - ?
                WHERE user_id = ? AND item_code = ?;
            """, (quantity, user_id, item_code))
            await db.commit()
            return True

    async def get_star_packages(self, pkg_type: Optional[str] = None, only_active: bool = True) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM star_packages WHERE 1=1"
            params = []
            if pkg_type:
                query += " AND package_type = ?"
                params.append(pkg_type)
            if only_active:
                query += " AND is_active = 1"
            query += " ORDER BY stars_price ASC;"
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    async def get_package_by_id(self, package_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM star_packages WHERE id = ?;", (package_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def update_star_package(self, pkg_id: int, stars_price: int, amount: int, bonus: int, title: str, is_active: int = 1) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE star_packages
                SET stars_price = ?, amount = ?, bonus = ?, title = ?, is_active = ?
                WHERE id = ?;
            """, (stars_price, amount, bonus, title, is_active, pkg_id))
            await db.commit()
            return True

    async def get_setting(self, key: str, default: str = "") -> str:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT value FROM settings WHERE key = ?;", (key,)) as cursor:
                row = await cursor.fetchone()
                return row["value"] if row else default

    async def set_setting(self, key: str, value: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value;
            """, (key, str(value)))
            await db.commit()
            return True

    async def search_users(self, query: str = "", limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if query.strip():
                q = f"%{query.strip()}%"
                async with db.execute("""
                    SELECT * FROM users
                    WHERE id LIKE ? OR username LIKE ? OR full_name LIKE ? OR phone_number LIKE ?
                    ORDER BY id DESC LIMIT ? OFFSET ?;
                """, (q, q, q, q, limit, offset)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]
            else:
                async with db.execute("SELECT * FROM users ORDER BY id DESC LIMIT ? OFFSET ?;", (limit, offset)) as cursor:
                    rows = await cursor.fetchall()
                    return [dict(r) for r in rows]

    async def count_users(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users;") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_stats(self) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*), SUM(pul), SUM(almaz) FROM users;") as cursor:
                user_row = await cursor.fetchone()
            async with db.execute("SELECT COUNT(*) FROM game_logs;") as cursor:
                game_row = await cursor.fetchone()
            return {
                "total_users": user_row[0] if user_row else 0,
                "total_pul": user_row[1] if user_row and user_row[1] else 0,
                "total_almaz": user_row[2] if user_row and user_row[2] else 0,
                "total_games": game_row[0] if game_row else 0
            }

    async def record_game_end(self, chat_id: int, winner_team: str, player_count: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO game_logs (chat_id, winner_team, player_count)
                VALUES (?, ?, ?);
            """, (chat_id, winner_team, player_count))
            await db.commit()

    async def get_leaderboard(self, order_by: str = "games_won", limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            valid_orders = ["games_won", "level", "pul", "almaz"]
            col = order_by if order_by in valid_orders else "games_won"
            async with db.execute(f"SELECT * FROM users ORDER BY {col} DESC LIMIT ?;", (limit,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]

    # --- LAST WILL (VASIYATNOMA) ---
    async def set_last_will(self, user_id: int, will_text: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET last_will = ? WHERE id = ?;", (will_text.strip(), user_id))
            await db.commit()
            return True

    async def get_last_will(self, user_id: int) -> str:
        u = await self.get_user(user_id)
        return u.get("last_will", "") if u else ""

    # --- CLANS (MAFIA OILALARI) ---
    async def create_clan(self, owner_id: int, name: str, tag: str, description: str = "") -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            # Check if user already has a clan
            async with db.execute("SELECT clan_id FROM clan_members WHERE user_id = ?;", (owner_id,)) as cur:
                if await cur.fetchone():
                    return None
            try:
                cur = await db.execute("""
                    INSERT INTO clans (name, tag, description, owner_id)
                    VALUES (?, ?, ?, ?);
                """, (name, tag, description, owner_id))
                clan_id = cur.lastrowid
                await db.execute("""
                    INSERT INTO clan_members (clan_id, user_id, role)
                    VALUES (?, ?, 'owner');
                """, (clan_id, owner_id))
                await db.commit()
                return clan_id
            except Exception:
                return None

    async def get_user_clan(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT c.*, m.role as member_role
                FROM clan_members m
                JOIN clans c ON m.clan_id = c.id
                WHERE m.user_id = ?;
            """, (user_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def get_clan(self, clan_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM clans WHERE id = ?;", (clan_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def get_clan_members(self, clan_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT u.id, u.full_name, u.username, u.level, m.role, m.joined_at
                FROM clan_members m
                JOIN users u ON m.user_id = u.id
                WHERE m.clan_id = ?;
            """, (clan_id,)) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def join_clan(self, user_id: int, clan_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT 1 FROM clan_members WHERE user_id = ?;", (user_id,)) as cur:
                if await cur.fetchone():
                    return False
            await db.execute("""
                INSERT INTO clan_members (clan_id, user_id, role)
                VALUES (?, ?, 'member');
            """, (clan_id, user_id))
            await db.commit()
            return True

    async def leave_clan(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM clan_members WHERE user_id = ?;", (user_id,))
            await db.commit()
            return True

    async def delete_clan(self, clan_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM clans WHERE id = ?;", (clan_id,))
            await db.execute("DELETE FROM clan_members WHERE clan_id = ?;", (clan_id,))
            await db.commit()
            return True

    async def deposit_clan(self, clan_id: int, pul: int = 0, almaz: int = 0) -> Tuple[bool, bool, int]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT level, treasury_pul FROM clans WHERE id = ?;", (clan_id,)) as cur:
                row = await cur.fetchone()
                if not row:
                    return False, False, 1
                old_lvl = row["level"]
                total_pul = row["treasury_pul"] + pul

            new_lvl = 1
            if total_pul >= 100000:
                new_lvl = 5
            elif total_pul >= 50000:
                new_lvl = 4
            elif total_pul >= 25000:
                new_lvl = 3
            elif total_pul >= 10000:
                new_lvl = 2

            leveled_up = (new_lvl > old_lvl)
            await db.execute("""
                UPDATE clans
                SET treasury_pul = treasury_pul + ?, treasury_almaz = treasury_almaz + ?, level = ?
                WHERE id = ?;
            """, (pul, almaz, new_lvl, clan_id))
            await db.commit()
            return True, leveled_up, new_lvl

    async def get_top_clans(self, limit: int = 10) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT c.*, COUNT(m.id) as member_count
                FROM clans c
                LEFT JOIN clan_members m ON c.id = m.clan_id
                GROUP BY c.id
                ORDER BY c.treasury_pul DESC, c.level DESC
                LIMIT ?;
            """, (limit,)) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    # --- ACHIEVEMENTS (YUTUQLAR) ---
    async def get_achievements_with_user(self, user_id: int) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT a.*, (ua.unlocked_at IS NOT NULL) as is_unlocked
                FROM achievements a
                LEFT JOIN user_achievements ua ON a.code = ua.achievement_code AND ua.user_id = ?;
            """, (user_id,)) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def unlock_achievement(self, user_id: int, code: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM achievements WHERE code = ?;", (code,)) as cur:
                ach = await cur.fetchone()
                if not ach:
                    return None
            try:
                await db.execute("""
                    INSERT INTO user_achievements (user_id, achievement_code)
                    VALUES (?, ?);
                """, (user_id, code))
                await db.commit()
            except Exception:
                return None # already unlocked

            # Award reward
            ach_dict = dict(ach)
            await self.update_balance(user_id, pul_diff=ach_dict["reward_pul"], almaz_diff=ach_dict["reward_almaz"])
            return ach_dict

    # --- DAILY QUESTS (KUNLIK TOPSHIRIQLAR) ---
    async def get_daily_quests_for_user(self, user_id: int) -> List[Dict[str, Any]]:
        import datetime
        today_key = datetime.date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT q.*, COALESCE(p.progress, 0) as user_progress, COALESCE(p.is_claimed, 0) as is_claimed
                FROM daily_quests q
                LEFT JOIN user_quest_progress p ON q.code = p.quest_code AND p.user_id = ? AND p.date_key = ?;
            """, (user_id, today_key)) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def progress_quest(self, user_id: int, quest_code: str, increment: int = 1) -> bool:
        import datetime
        today_key = datetime.date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO user_quest_progress (user_id, quest_code, progress, is_claimed, date_key)
                VALUES (?, ?, ?, 0, ?)
                ON CONFLICT(user_id, quest_code, date_key)
                DO UPDATE SET progress = progress + ?;
            """, (user_id, quest_code, increment, today_key, increment))
            await db.commit()
            return True

    async def claim_quest_reward(self, user_id: int, quest_code: str) -> Optional[Dict[str, Any]]:
        import datetime
        today_key = datetime.date.today().isoformat()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT q.*, p.progress, p.is_claimed
                FROM daily_quests q
                JOIN user_quest_progress p ON q.code = p.quest_code
                WHERE p.user_id = ? AND p.quest_code = ? AND p.date_key = ?;
            """, (user_id, quest_code, today_key)) as cur:
                row = await cur.fetchone()
                if not row or row["progress"] < row["target_count"] or row["is_claimed"]:
                    return None
            await db.execute("""
                UPDATE user_quest_progress
                SET is_claimed = 1
                WHERE user_id = ? AND quest_code = ? AND date_key = ?;
            """, (user_id, quest_code, today_key))
            await db.commit()

        q_dict = dict(row)
        await self.update_balance(user_id, pul_diff=q_dict["reward_pul"], almaz_diff=q_dict["reward_almaz"])
        if q_dict.get("reward_xp"):
            await self.add_xp(user_id, q_dict["reward_xp"])
        return q_dict

    # --- 1v1 DUELS ---
    async def create_duel(self, challenger_id: int, opponent_id: int, bet_type: str, bet_amount: int) -> Optional[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("""
                INSERT INTO duels (challenger_id, opponent_id, bet_type, bet_amount, status)
                VALUES (?, ?, ?, ?, 'pending');
            """, (challenger_id, opponent_id, bet_type, bet_amount))
            await db.commit()
            return cur.lastrowid

    async def get_duel(self, duel_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM duels WHERE id = ?;", (duel_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def resolve_duel(self, duel_id: int, winner_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE duels
                SET status = 'finished', winner_id = ?
                WHERE id = ?;
            """, (winner_id, duel_id))
            await db.commit()
            return True

    # --- KARTA TO'LOVLARI (UZCARD / HUMO - SOFPAY USLUBIDA) ---
    async def get_card_packages(self, only_active: bool = True) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = "SELECT * FROM card_packages WHERE is_active = 1 ORDER BY price_uzs ASC;" if only_active else "SELECT * FROM card_packages ORDER BY price_uzs ASC;"
            async with db.execute(query) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def get_card_package(self, package_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM card_packages WHERE id = ?;", (package_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def update_card_package(self, package_id: int, price_uzs: int, amount: int, bonus: int, is_active: int = 1) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE card_packages
                SET price_uzs = ?, amount = ?, bonus = ?, is_active = ?
                WHERE id = ?;
            """, (price_uzs, amount, bonus, is_active, package_id))
            await db.commit()
            return True

    async def get_card_details(self) -> Dict[str, str]:
        number = await self.get_setting("card_number", "8600 0000 0000 0000")
        holder = await self.get_setting("card_holder", "MAFIA ADMIN")
        bank = await self.get_setting("card_bank", "Kapitalbank / Uzcard")
        return {"card_number": number, "card_holder": holder, "card_bank": bank}

    async def set_card_details(self, card_number: str, card_holder: str, card_bank: str = "") -> bool:
        await self.set_setting("card_number", card_number)
        await self.set_setting("card_holder", card_holder)
        if card_bank:
            await self.set_setting("card_bank", card_bank)
        return True

    async def create_card_transaction(
        self,
        user_id: int,
        package_id: int,
        tx_id: str,
        item_type: str,
        item_amount: int,
        price_uzs: int,
        unique_amount: int,
        card_number: str,
        card_holder: str
    ) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cur = await db.execute("""
                INSERT INTO card_transactions (
                    tx_id, user_id, package_id, item_type, item_amount,
                    price_uzs, unique_amount, card_number, card_holder, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending');
            """, (
                tx_id, user_id, package_id, item_type, item_amount,
                price_uzs, unique_amount, card_number, card_holder
            ))
            await db.commit()
            return cur.lastrowid

    async def get_card_transaction(self, tx_id: str) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM card_transactions WHERE tx_id = ?;", (tx_id,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def get_card_transactions(self, limit: int = 50, status: Optional[str] = None) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if status:
                query = "SELECT t.*, u.full_name, u.username FROM card_transactions t LEFT JOIN users u ON t.user_id = u.id WHERE t.status = ? ORDER BY t.id DESC LIMIT ?;"
                args = (status, limit)
            else:
                query = "SELECT t.*, u.full_name, u.username FROM card_transactions t LEFT JOIN users u ON t.user_id = u.id ORDER BY t.id DESC LIMIT ?;"
                args = (limit,)
            async with db.execute(query, args) as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def set_card_tx_proof(self, tx_id: str, file_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE card_transactions
                SET proof_file_id = ?
                WHERE tx_id = ?;
            """, (file_id, tx_id))
            await db.commit()
            return True

    async def complete_card_transaction(self, tx_id: str) -> Optional[Dict[str, Any]]:
        tx = await self.get_card_transaction(tx_id)
        if not tx or tx["status"] != "pending":
            return None

        now = int(time.time())
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE card_transactions
                SET status = 'completed', completed_at = CURRENT_TIMESTAMP
                WHERE tx_id = ?;
            """, (tx_id,))
            await db.commit()

        # Give items to user
        user_id = tx["user_id"]
        item_type = tx["item_type"]
        amount = tx["item_amount"]

        if item_type == "almaz":
            await self.update_balance(user_id, almaz_diff=amount)
        elif item_type == "pul":
            await self.update_balance(user_id, pul_diff=amount)
        elif item_type == "vip":
            user = await self.get_user(user_id)
            current_vip = user.get("vip_until", 0) if user else 0
            new_vip = max(now, current_vip) + (amount * 86400)
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("UPDATE users SET vip_until = ? WHERE id = ?;", (new_vip, user_id))
                await db.commit()

        # Unlock rich_boss achievement check
        if tx["price_uzs"] >= 25000:
            await self.unlock_achievement(user_id, "rich_boss")

        tx["status"] = "completed"
        return tx

    async def cancel_card_transaction(self, tx_id: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE card_transactions
                SET status = 'cancelled'
                WHERE tx_id = ? AND status = 'pending';
            """, (tx_id,))
            await db.commit()
            return True

    # --- USER DATA & PHONE VERIFICATION ---
    async def set_user_phone(self, user_id: int, phone: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET phone_number = ? WHERE id = ?;", (phone, user_id))
            await db.commit()
            return True

    # --- PROMO CODES ---
    async def create_promo_code(self, code: str, pul: int, almaz: int, xp: int = 50, max_uses: int = 100) -> bool:
        code_clean = code.strip().upper()
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO promo_codes (code, reward_pul, reward_almaz, reward_xp, max_uses, used_count)
                VALUES (?, ?, ?, ?, ?, 0);
            """, (code_clean, pul, almaz, xp, max_uses))
            await db.commit()
            return True

    async def get_promo_codes(self) -> List[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM promo_codes ORDER BY created_at DESC;") as cur:
                rows = await cur.fetchall()
                return [dict(r) for r in rows]

    async def use_promo_code(self, user_id: int, code: str) -> Dict[str, Any]:
        code_clean = code.strip().upper()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Check if user already used
            async with db.execute("SELECT 1 FROM user_promo_uses WHERE user_id = ? AND code = ?;", (user_id, code_clean)) as cur:
                if await cur.fetchone():
                    return {"success": False, "error": "Siz bu promo-kodni allaqachon ishlatgansiz!"}

            # Check promo code
            async with db.execute("SELECT * FROM promo_codes WHERE code = ?;", (code_clean,)) as cur:
                promo = await cur.fetchone()
                if not promo:
                    return {"success": False, "error": "Bunday promo-kod topilmadi yoki muddati o'tgan!"}
                p_dict = dict(promo)
                if p_dict["used_count"] >= p_dict["max_uses"]:
                    return {"success": False, "error": "Ushbu promo-kodning barcha nusxalari ishlatib bo'lingan!"}

            # Apply
            await db.execute("INSERT INTO user_promo_uses (user_id, code) VALUES (?, ?);", (user_id, code_clean))
            await db.execute("UPDATE promo_codes SET used_count = used_count + 1 WHERE code = ?;", (code_clean,))
            await db.commit()

        await self.update_balance(user_id, pul_diff=p_dict["reward_pul"], almaz_diff=p_dict["reward_almaz"])
        if p_dict["reward_xp"]:
            await self.add_xp(user_id, p_dict["reward_xp"])

        return {"success": True, "promo": p_dict}

    async def get_group_stats(self, chat_id: int) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT COUNT(*) as total_games, SUM(player_count) as total_players FROM game_logs WHERE chat_id = ?;", (chat_id,)) as cur:
                row = await cur.fetchone()
                total_games = row["total_games"] if row else 0
                total_players = row["total_players"] if row else 0
                return {"total_games": total_games, "total_players": total_players}

    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        clean_user = username.replace("@", "").strip().lower()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE LOWER(username) = ?;", (clean_user,)) as cur:
                row = await cur.fetchone()
                return dict(row) if row else None

    async def transfer_pul(self, from_user_id: int, to_user_id: int, amount: int) -> Dict[str, Any]:
        if amount <= 0:
            return {"success": False, "error": "Miqdor 0 dan katta bo'lishi kerak!"}
        if from_user_id == to_user_id:
            return {"success": False, "error": "O'zingizga pul o'tkaza olmaysiz!"}

        from_u = await self.get_or_create_user(from_user_id)
        if not from_u or from_u.get("pul", 0) < amount:
            curr_pul = from_u.get("pul", 0) if from_u else 0
            return {"success": False, "error": f"Mablag' yetarli emas! Sizning balansingizda: {curr_pul:,} Pul mavjud."}

        to_u = await self.get_or_create_user(to_user_id)

        await self.update_balance(from_user_id, pul_diff=-amount)
        await self.update_balance(to_user_id, pul_diff=amount)
        return {"success": True, "amount": amount}

    async def transfer_almaz(self, from_user_id: int, to_user_id: int, amount: int) -> Dict[str, Any]:
        if amount <= 0:
            return {"success": False, "error": "Miqdor 0 dan katta bo'lishi kerak!"}
        if from_user_id == to_user_id:
            return {"success": False, "error": "O'zingizga almaz o'tkaza olmaysiz!"}

        from_u = await self.get_or_create_user(from_user_id)
        if not from_u or from_u.get("almaz", 0) < amount:
            curr_almaz = from_u.get("almaz", 0) if from_u else 0
            return {"success": False, "error": f"Almazlaringiz yetarli emas! Sizda: {curr_almaz:,} Almaz bor."}

        to_u = await self.get_or_create_user(to_user_id)

        await self.update_balance(from_user_id, almaz_diff=-amount)
        await self.update_balance(to_user_id, almaz_diff=amount)
        return {"success": True, "amount": amount}

    async def transfer_item(self, from_user_id: int, to_user_id: int, item_code: str, quantity: int = 1) -> Dict[str, Any]:
        if from_user_id == to_user_id:
            return {"success": False, "error": "O'zingizga sovg'a qila olmaysiz!"}

        inv = await self.get_inventory(from_user_id)
        has_item = any(it["code"] == item_code and it["quantity"] >= quantity for it in inv)
        if not has_item:
            return {"success": False, "error": "Sizda ushbu mashina / buyum mavjud emas!"}

        to_u = await self.get_or_create_user(to_user_id)

        item_info = await self.get_item(item_code)
        await self.consume_inventory_item(from_user_id, item_code, quantity)
        await self.add_inventory_item(to_user_id, item_code, quantity)
        return {"success": True, "item": item_info}

    async def bank_deposit(self, user_id: int, amount: int) -> Dict[str, Any]:
        if amount <= 0:
            return {"success": False, "error": "Miqdor 0 dan katta bo'lishi kerak!"}
        u = await self.get_user(user_id)
        if not u or u.get("pul", 0) < amount:
            return {"success": False, "error": "Cho'ntagingizda yetarli naqd pul yo'q!"}

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users
                SET pul = pul - ?, bank_pul = COALESCE(bank_pul, 0) + ?
                WHERE id = ?;
            """, (amount, amount, user_id))
            await db.commit()
        return {"success": True, "amount": amount}

    async def bank_withdraw(self, user_id: int, amount: int) -> Dict[str, Any]:
        if amount <= 0:
            return {"success": False, "error": "Miqdor 0 dan katta bo'lishi kerak!"}
        u = await self.get_user(user_id)
        if not u or (u.get("bank_pul") or 0) < amount:
            return {"success": False, "error": "Bank hisobingizda yetarli pul yo'q!"}

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users
                SET pul = pul + ?, bank_pul = bank_pul - ?
                WHERE id = ?;
            """, (amount, amount, user_id))
            await db.commit()
        return {"success": True, "amount": amount}

    async def get_marriage(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("""
                SELECT * FROM marriages WHERE user1_id = ? OR user2_id = ?;
            """, (user_id, user_id)) as cur:
                row = await cur.fetchone()
                if not row:
                    return None
                m = dict(row)
                spouse_id = m["user2_id"] if m["user1_id"] == user_id else m["user1_id"]
                spouse = await self.get_user(spouse_id)
                m["spouse"] = spouse or {"id": spouse_id, "full_name": "Turmush o'rtog'i"}
                return m

    async def marry_users(self, user1_id: int, user2_id: int) -> bool:
        await self.get_or_create_user(user1_id)
        await self.get_or_create_user(user2_id)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM marriages WHERE user1_id IN (?, ?) OR user2_id IN (?, ?);", (user1_id, user2_id, user1_id, user2_id))
            await db.execute("""
                INSERT INTO marriages (user1_id, user2_id) VALUES (?, ?);
            """, (user1_id, user2_id))
            await db.execute("UPDATE users SET spouse_id = ? WHERE id = ?;", (user2_id, user1_id))
            await db.execute("UPDATE users SET spouse_id = ? WHERE id = ?;", (user1_id, user2_id))
            await db.commit()
            return True

    async def divorce_users(self, user_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM marriages WHERE user1_id = ? OR user2_id = ?;", (user_id, user_id))
            await db.execute("UPDATE users SET spouse_id = 0 WHERE id = ? OR spouse_id = ?;", (user_id, user_id))
            await db.commit()
            return True

    async def change_rep(self, from_user_id: int, to_user_id: int, delta: int) -> Dict[str, Any]:
        if from_user_id == to_user_id:
            return {"success": False, "error": "O'zingizga obro' bera olmaysiz!"}

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO rep_logs (from_user_id, to_user_id, change) VALUES (?, ?, ?);
            """, (from_user_id, to_user_id, delta))
            await db.execute("""
                UPDATE users SET rep = COALESCE(rep, 0) + ? WHERE id = ?;
            """, (delta, to_user_id))
            await db.commit()
        return {"success": True}

    async def get_group_settings(self, chat_id: int) -> Dict[str, Any]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM group_settings WHERE chat_id = ?;", (chat_id,)) as cur:
                row = await cur.fetchone()
                if row:
                    return dict(row)
                return {
                    "chat_id": chat_id,
                    "talk_time": 50,
                    "vote_time": 40,
                    "night_time": 40,
                    "is_anonymous_vote": 0,
                    "is_antispam": 1,
                    "disabled_roles": ""
                }

    async def update_group_settings(self, chat_id: int, **kwargs):
        settings = await self.get_group_settings(chat_id)
        settings.update(kwargs)
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO group_settings
                (chat_id, talk_time, vote_time, night_time, is_anonymous_vote, is_antispam, disabled_roles)
                VALUES (?, ?, ?, ?, ?, ?, ?);
            """, (
                chat_id,
                settings["talk_time"],
                settings["vote_time"],
                settings["night_time"],
                settings["is_anonymous_vote"],
                settings["is_antispam"],
                settings["disabled_roles"]
            ))
            await db.commit()

db = Database()

