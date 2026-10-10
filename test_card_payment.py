import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from database.db import db
from starlette.testclient import TestClient
from web.app import app

client = TestClient(app)

async def test_card_system():
    print("--- 1. Testing Card Packages & Seeding ---")
    await db.init()
    packages = await db.get_card_packages()
    assert len(packages) >= 10, f"Expected at least 10 packages, got {len(packages)}"

    pkg_10_almaz = next(p for p in packages if p["package_type"] == "almaz" and p["amount"] == 10)
    assert pkg_10_almaz["price_uzs"] == 1000, f"Expected 1000 UZS, got {pkg_10_almaz['price_uzs']}"
    print(f"Verified 10 Almaz package: {pkg_10_almaz['title']} = {pkg_10_almaz['price_uzs']} so'm")

    print("\n--- 2. Testing Card Settings ---")
    await db.set_card_details("8600 1234 5678 9012", "Sardor M.", "Kapitalbank")
    card_info = await db.get_card_details()
    assert card_info["card_number"] == "8600 1234 5678 9012"
    assert card_info["card_holder"] == "Sardor M."
    print("Card settings saved and verified.")

    print("\n--- 3. Testing Card Transaction Creation & Manual/Admin Approval ---")
    test_user_id = 999999
    await db.get_or_create_user(test_user_id, username="test_card_user", full_name="Test Card User")
    await db.set_balance(test_user_id, pul=0, almaz=0)

    import uuid
    tx_id = f"TX_TEST_{uuid.uuid4().hex[:8]}"
    await db.create_card_transaction(
        user_id=test_user_id,
        package_id=pkg_10_almaz["id"],
        tx_id=tx_id,
        item_type="almaz",
        item_amount=10,
        price_uzs=1000,
        unique_amount=1018,
        card_number=card_info["card_number"],
        card_holder=card_info["card_holder"]
    )

    tx = await db.get_card_transaction(tx_id)
    assert tx is not None
    assert tx["status"] == "pending"
    assert tx["unique_amount"] == 1018

    # Approve transaction
    comp = await db.complete_card_transaction(tx_id)
    assert comp is not None
    assert comp["status"] == "completed"

    user = await db.get_user(test_user_id)
    assert user["almaz"] == 10, f"Expected 10 almaz, got {user['almaz']}"
    print(f"Transaction completed: user almaz = {user['almaz']}")

    print("\n--- 4. Testing SofPay Style REST API (/api/v1/transaction/create) ---")
    resp_create = client.post("/api/v1/transaction/create", json={
        "amount": 1000,
        "user_id": test_user_id,
        "description": "10 Almaz Test"
    })
    assert resp_create.status_code == 200, resp_create.text
    data_create = resp_create.json()
    assert data_create["success"] is True
    api_tx = data_create["transaction"]
    api_tx_id = api_tx["tx_id"]
    print(f"SofPay API Created TX: {api_tx_id}, amount: {api_tx['amount']} UZS, card: {api_tx['card_number']}")

    # Check status via GET
    resp_get = client.get(f"/api/v1/transaction/{api_tx_id}")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["transaction"]["status"] == "pending"

    # Test Auto-SMS Webhook Notification (/api/v1/transaction/notify)
    resp_notify = client.post("/api/v1/transaction/notify", json={
        "tx_id": api_tx_id,
        "amount": api_tx["amount"]
    })
    assert resp_notify.status_code == 200, resp_notify.text
    assert resp_notify.json()["success"] is True

    # Verify user received additional 10 almaz
    user_after = await db.get_user(test_user_id)
    assert user_after["almaz"] == 20, f"Expected 20 almaz, got {user_after['almaz']}"
    print(f"SMS Webhook Auto-Approval verified! User total almaz: {user_after['almaz']}")

    print("\n✅ BARCHA KARTA VA SOFPAY REST API TESTLARI 100% MUVAFFAQIYATLI O'TDI!")

if __name__ == "__main__":
    asyncio.run(test_card_system())
