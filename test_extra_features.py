import asyncio
import os
import sys

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from database.db import db, BATTLE_PASS_TIERS

async def test_extra_features():
    print("=== TESTING EXTRA FEATURES ===")
    user_id = 999888777
    import aiosqlite
    async with aiosqlite.connect(db.db_path) as conn:
        await conn.execute("DELETE FROM battle_pass WHERE user_id = ?;", (user_id,))
        await conn.execute("DELETE FROM users WHERE id = ?;", (user_id,))
        await conn.commit()

    user = await db.get_or_create_user(user_id, "test_hero", "Test Hero")
    await db.update_balance(user_id, pul_diff=500000, almaz_diff=250)

    # 1. Battle Pass
    bp = await db.get_or_create_battle_pass(user_id)
    assert bp["season"] == 1
    assert bp["tier"] == 1
    print("1. Battle Pass initialized:", bp)

    # Add Battle Pass XP
    res_xp = await db.add_battle_pass_xp(user_id, 120)
    assert res_xp["leveled_up"] is True
    assert res_xp["new_tier"] == 2
    print("2. Battle Pass XP addition & Tier Up verified: Tier 2")

    # Upgrade to Gold Pass
    res_gold = await db.upgrade_battle_pass_gold(user_id)
    assert res_gold["success"] is True
    print("3. Battle Pass Gold Pass upgrade verified")

    # Claim Free & Gold Tier 1
    res_claim_f = await db.claim_battle_pass_tier(user_id, 1, is_gold=False)
    assert res_claim_f["success"] is True
    res_claim_g = await db.claim_battle_pass_tier(user_id, 1, is_gold=True)
    assert res_claim_g["success"] is True
    print("4. Tier 1 Free and Gold reward claimed successfully")

    # 2. Coin Flip
    flip_res = await db.play_coin_flip(user_id, "burgut", 1000)
    assert flip_res["success"] is True
    assert flip_res["outcome"] in ("burgut", "panja")
    print("5. Coin Flip executed successfully:", flip_res)

    # 3. Mystery Chests
    chest_b = await db.open_mystery_chest(user_id, "bronze")
    assert chest_b["success"] is True
    print("6. Bronze Chest reward:", chest_b["reward_desc"])

    chest_g = await db.open_mystery_chest(user_id, "gold")
    assert chest_g["success"] is True
    print("7. Gold Chest reward:", chest_g["reward_desc"])

    # 4. VIP & Custom Title
    vip_res = await db.buy_vip_days(user_id, 7, 25)
    assert vip_res["success"] is True
    title_res = await db.set_custom_title(user_id, "Afsonaviy Don")
    assert title_res["success"] is True
    assert title_res["title"] == "Afsonaviy Don"
    print("8. VIP purchase and Custom Title verified: «Afsonaviy Don»")

    # 5. Extended User Stats
    stats = await db.get_extended_user_stats(user_id)
    assert stats["is_vip"] is True
    assert stats["user"]["custom_title"] == "Afsonaviy Don"
    print("9. Extended Stats verified successfully:", stats["user"]["custom_title"], "VIP days left:", stats["vip_days_left"])

    print("\n✅ BARCHA YANGI XUSUSIYATLAR VA MINIO'YINLAR TESTDAN 100% O'TDI!")

if __name__ == "__main__":
    asyncio.run(test_extra_features())
