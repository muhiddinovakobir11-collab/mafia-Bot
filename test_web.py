import asyncio
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from starlette.testclient import TestClient
from web.app import app
from database.db import db
from config import WEB_ADMIN_SECRET

async def run_web_tests():
    await db.init()
    client = TestClient(app)

    print("--- 1. Testing GET /login ---")
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "MAFIA BOT ADMIN" in resp.text
    print("Login page rendered successfully.")

    print("\n--- 2. Testing Login with Secret ---")
    login_resp = client.post("/login", data={"secret_key": WEB_ADMIN_SECRET}, follow_redirects=False)
    assert login_resp.status_code == 302
    assert login_resp.headers["location"] == "/"
    print("Login authentication verified.")

    print("\n--- 3. Testing GET Dashboard with Direct Secret Param ---")
    dash_resp = client.get(f"/?secret={WEB_ADMIN_SECRET}")
    assert dash_resp.status_code == 200
    assert "MAFIA BOT DASHBOARD" in dash_resp.text
    assert "Foydalanuvchilar" in dash_resp.text
    assert "Stars Paketlari" in dash_resp.text
    print("Dashboard rendered with full metrics and tabs.")

    print("\n--- 4. Testing POST /user/update_balance ---")
    admin_id = 8055412146
    # Update balance to 88,888 pul and 77 almaz
    upd_resp = client.post(
        f"/user/update_balance?secret={WEB_ADMIN_SECRET}",
        data={"user_id": admin_id, "pul": 88888, "almaz": 77},
        follow_redirects=False
    )
    assert upd_resp.status_code == 302
    user = await db.get_user(admin_id)
    assert user["pul"] == 88888
    assert user["almaz"] == 77
    print(f"Web balance update verified: pul={user['pul']}, almaz={user['almaz']}")

    print("\n--- 5. Testing POST /package/update ---")
    pkgs = await db.get_star_packages()
    first_pkg = pkgs[0]
    pkg_resp = client.post(
        f"/package/update?secret={WEB_ADMIN_SECRET}",
        data={
            "pkg_id": first_pkg["id"],
            "stars_price": 99,
            "amount": 50,
            "bonus": 10,
            "is_active": 1
        },
        follow_redirects=False
    )
    assert pkg_resp.status_code == 302
    pkg_updated = await db.get_package_by_id(first_pkg["id"])
    assert pkg_updated["stars_price"] == 99
    assert pkg_updated["amount"] == 50
    print(f"Web star package dynamic update verified: ⭐️ {pkg_updated['stars_price']}")

    print("\n✅ WEB ADMIN PANEL BARCHA TESTLARI MUVAFFAQIYATLI O'TDI!")

if __name__ == "__main__":
    asyncio.run(run_web_tests())
