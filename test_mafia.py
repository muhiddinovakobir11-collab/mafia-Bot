import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
from config import ADMIN_IDS, WEB_ADMIN_SECRET
from database.db import db
from game.roles import get_role_distribution, ROLES, Team
from game.levels import get_reward_for_level

async def test_all():
    print("--- 1. Testing Database & Migration ---")
    await db.init()
    print("Database initialized successfully.")

    print("\n--- 2. Testing User & Admin Initialization ---")
    admin_id = 8055412146
    user = await db.get_or_create_user(admin_id, username="admin_user", full_name="Bosh Admin")
    # Reset for clean test run
    await db.set_balance(admin_id, pul=1000, almaz=5)
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("UPDATE users SET level = 1, xp = 0 WHERE id = ?;", (admin_id,))
        await conn.execute("DELETE FROM user_inventory WHERE user_id = ?;", (admin_id,))
        await conn.commit()


    user = await db.get_user(admin_id)
    assert user["is_admin"] == 1, f"Expected admin, got {user['is_admin']}"
    assert user["id"] == admin_id
    assert user["pul"] == 1000
    assert user["almaz"] == 5
    print(f"Admin verified: ID={user['id']}, is_admin={user['is_admin']}, pul={user['pul']}, almaz={user['almaz']}")

    print("\n--- 3. Testing Balance Updates & Ban ---")
    await db.update_balance(admin_id, pul_diff=5000, almaz_diff=20)
    u_updated = await db.get_user(admin_id)
    assert u_updated["pul"] == 6000
    assert u_updated["almaz"] == 25
    print(f"Updated balance: pul={u_updated['pul']}, almaz={u_updated['almaz']}")


    await db.set_ban(admin_id, True)
    assert (await db.get_user(admin_id))["is_banned"] == 1
    await db.set_ban(admin_id, False)
    assert (await db.get_user(admin_id))["is_banned"] == 0
    print("Ban / Unban toggle verified.")

    print("\n--- 4. Testing Level Up & Rewards ---")
    # Add XP to trigger level up to 2 (requires 150 XP)
    res_lvl2 = await db.add_xp(admin_id, 160)
    assert res_lvl2["leveled_up"] is True
    assert res_lvl2["new_level"] == 2
    print(f"Level 2 reached: reward={res_lvl2['rewards']}")

    # Add XP to trigger level up to 3 (requires 300 XP)
    res_lvl3 = await db.add_xp(admin_id, 320)
    assert res_lvl3["leveled_up"] is True
    assert res_lvl3["new_level"] == 3
    print(f"Level 3 reached: reward={res_lvl3['rewards']}")
    # Check if level 3 gave 10 almaz
    has_10_almaz = any(r.get("almaz") == 10 for r in res_lvl3["rewards"])
    assert has_10_almaz, "Level 3 must grant 10 almaz as specified!"
    print("Level 3 reward of 10 Almaz verified successfully!")

    print("\n--- 5. Testing Role Distribution (No boring passive citizens) ---")
    for count in [3, 4, 5, 7, 10, 12]:
        roles = get_role_distribution(count)
        assert len(roles) == count
        for r_code in roles:
            assert r_code in ROLES, f"Unknown role {r_code}"
            assert r_code != "citizen", "Plain citizen role must NOT be used!"
        print(f"Player count {count} -> Roles: {[ROLES[r].name for r in roles]}")

    print("\n--- 6. Testing Shop Items & Inventory ---")
    items = await db.get_items()
    assert len(items) >= 10
    print(f"Total items in shop: {len(items)}")

    # Add item to inventory and consume
    await db.add_inventory_item(admin_id, "qalqon", 2)
    inv = await db.get_inventory(admin_id)
    assert any(it["code"] == "qalqon" and it["quantity"] == 2 for it in inv)
    await db.consume_inventory_item(admin_id, "qalqon", 1)
    inv_after = await db.get_inventory(admin_id)
    assert any(it["code"] == "qalqon" and it["quantity"] == 1 for it in inv_after)
    print("Shop item purchase & inventory consumption verified.")

    print("\n--- 7. Testing Star Packages ---")
    pkgs = await db.get_star_packages()
    assert len(pkgs) >= 8
    print(f"Star packages available: {len(pkgs)}")
    # Update package price test
    await db.update_star_package(pkgs[0]["id"], stars_price=35, amount=15, bonus=3, title="💎 15 Almaz (+3 bonus)")
    updated_pkg = await db.get_package_by_id(pkgs[0]["id"])
    assert updated_pkg["stars_price"] == 35
    print(f"Star package #{pkgs[0]['id']} dynamic price update verified: ⭐️ {updated_pkg['stars_price']}")

    print("\n✅ BARCHA TESTLAR MUVAFFAQIYATLI O'TDI!")

if __name__ == "__main__":
    asyncio.run(test_all())
