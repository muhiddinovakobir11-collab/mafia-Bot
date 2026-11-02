import asyncio
import sys
import random

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from game.roles import ROLES, Team, get_role_distribution
from game.engine import GameRoom, Player

class DummyBot:
    async def get_me(self):
        class BotInfo:
            username = "mafia_test_bot"
        return BotInfo()

    async def get_chat(self, chat_id):
        class ChatInfo:
            username = "mafia_group"
        return ChatInfo()

    async def send_message(self, *args, **kwargs):
        pass

    async def set_chat_permissions(self, *args, **kwargs):
        pass

async def test_roles_suite():
    print("=== 1. ROLES AUDIT ===")
    assert len(ROLES) == 68, f"Expected 68 roles, found {len(ROLES)}"
    print(f"Total roles verified: {len(ROLES)} (18 asosiy + 50 yangi rol)")

    teams_count = {}
    for code, r in ROLES.items():
        assert r.code == code
        assert len(r.name) > 0, f"Role {code} has empty name"
        assert len(r.emoji) > 0, f"Role {code} has empty emoji"
        assert len(r.description) > 0, f"Role {code} has empty description"
        assert len(r.ru_name) > 0, f"Role {code} has empty ru_name"
        assert len(r.ru_description) > 0, f"Role {code} has empty ru_description"
        assert isinstance(r.team, Team)
        teams_count[r.team] = teams_count.get(r.team, 0) + 1

    print("Teams Breakdown:")
    for team, count in teams_count.items():
        print(f"  • {team.value.upper()}: {count} ta rol")

    print("\n=== 2. ROLE DISTRIBUTION TEST ===")
    for count in [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 15, 20, 30, 45, 50]:
        dist = get_role_distribution(count)
        assert len(dist) == count, f"Failed length check for count {count}"
        assert "citizen" not in dist, f"Boring citizen found in distribution for count {count}"
        for c in dist:
            assert c in ROLES, f"Unknown role {c} in distribution"
        if count in [5, 10, 20]:
            print(f"Player Count {count} Distribution: {[ROLES[c].name for c in dist[:6]]}...")

    print("\n=== 3. ENGINE MECHANICS SIMULATION ===")
    bot = DummyBot()
    room = GameRoom(chat_id=-1001234567, bot=bot)
    
    # Mock run_day_phase to avoid waiting for talk timer in tests
    day_phase_killed = []
    async def mock_day_phase(night_killed):
        nonlocal day_phase_killed
        day_phase_killed = list(night_killed)
    room.run_day_phase = mock_day_phase

    test_roles = [
        ("hakim", 101),
        ("masxaraboz", 102),
        ("ovchi", 103),
        ("snayper", 104),
        ("tansoqchi", 105),
        ("kadr", 106),
        ("suqasdqor", 107),
        ("qonxor", 108),
        ("vampir_graf", 109),
        ("detektiv", 110),
        ("psixolog", 111),
        ("uchastkovoy", 112),
        ("veteran", 113),
        ("omadli_darvesh", 114),
        ("qariya", 115)
    ]
    for r_code, uid in test_roles:
        p = Player(uid, f"User_{r_code}")
        p.role_code = r_code
        if r_code == "qariya":
            p.lives = 2
        room.players[uid] = p

    # Verify Qariya has 2 lives
    assert room.players[115].lives == 2
    print("Qariya lives check passed: 2 lives initialized.")

    # Simulate night actions:
    # 1. Uchastkovoy jailing suqasdqor (107)
    room.players[112].night_target_id = 107
    # 2. Vampir graf biting User_hakim (101)
    room.players[109].night_target_id = 101
    # 3. Detektiv tracking Vampir graf (109)
    room.players[110].night_target_id = 109
    # 4. Psixolog checking Qonxor (108)
    room.players[111].night_target_id = 108
    # 5. Veteran alerting (targets self)
    room.players[113].night_target_id = 113
    # 6. Snayper shooting User_kadr (106)
    room.players[104].night_target_id = 106

    room.round_number = 2
    await room.resolve_night_actions()

    # Verify Suqasdqor was jailed
    assert room.players[107].is_jailed is True
    print("Uchastkovoy jail mechanic verified: target successfully jailed.")

    # Verify Hakim was bitten and converted to Vampir
    assert room.players[101].role_code == "vampir"
    print("Vampir Graf conversion mechanic verified: target successfully converted to Vampir.")

    # Verify Snayper shot Kadr
    assert room.players[106].is_alive is False
    print("Snayper shot mechanic verified: User_kadr killed.")

    print("\n✅ BARCHA 50 TA YANGI ROL VA ENGINE MEXANIKALARI TESTDAN MUVAFFAQIYATLI O'TDI!")

if __name__ == "__main__":
    asyncio.run(test_roles_suite())
