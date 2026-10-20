import os
import random
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from config import WEB_ADMIN_SECRET, ADMIN_IDS
from database.db import db
from game.engine import game_manager

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

app = FastAPI(title="Mafia Bot Web Admin Panel & Payment Gateway")
app.add_middleware(SessionMiddleware, secret_key="mafia_super_session_secret_key")

templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Dependency to check admin login
def require_admin(request: Request):
    # Check session or query param
    secret = request.query_params.get("secret")
    if secret == WEB_ADMIN_SECRET:
        request.session["is_admin"] = True
        return True

    if request.session.get("is_admin"):
        return True

    return False

@app.get("/health")
@app.get("/ping")
async def health_check():
    return JSONResponse({
        "status": "ok",
        "service": "mafia-bot",
        "alive": True
    })

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"error": None})

@app.post("/login", response_class=HTMLResponse)
async def process_login(request: Request, secret_key: str = Form(...)):
    if secret_key.strip() == WEB_ADMIN_SECRET:
        request.session["is_admin"] = True
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html", context={"error": "Noto'g'ri maxfiy kalit!"})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

@app.get("/webapp", response_class=HTMLResponse)
async def webapp_page(request: Request):
    return templates.TemplateResponse(request=request, name="webapp.html", context={})


@app.get("/", response_class=HTMLResponse)
async def admin_dashboard(request: Request, q: str = ""):
    if not require_admin(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    stats = await db.get_stats()
    users = await db.search_users(query=q, limit=50)
    items = await db.get_items(only_active=False)
    star_pkgs = await db.get_star_packages(only_active=False)
    rate = await db.get_setting("almaz_to_pul_rate", "500")

    # Card payment data
    card_pkgs = await db.get_card_packages(only_active=False)
    card_txs = await db.get_card_transactions(limit=50)
    card_info = await db.get_card_details()

    active_games = []
    for chat_id, room in game_manager.rooms.items():
        active_games.append({
            "chat_id": chat_id,
            "state": room.state,
            "round": room.round_number,
            "players_count": len(room.players),
            "alive_count": len(room.get_alive_players())
        })

    return templates.TemplateResponse(request=request, name="index.html", context={
        "stats": stats,
        "users": users,
        "items": items,
        "star_pkgs": star_pkgs,
        "card_pkgs": card_pkgs,
        "card_txs": card_txs,
        "card_info": card_info,
        "exchange_rate": rate,
        "active_games": active_games,
        "search_query": q,
        "admin_secret": WEB_ADMIN_SECRET
    })


@app.post("/user/update_balance")
async def update_user_balance(
    request: Request,
    user_id: int = Form(...),
    pul: int = Form(...),
    almaz: int = Form(...)
):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    await db.set_balance(user_id, pul=pul, almaz=almaz)
    return RedirectResponse(url=f"/?msg=Foydalanuvchi+{user_id}+balansi+yangilandi", status_code=status.HTTP_302_FOUND)

@app.post("/user/toggle_ban")
async def toggle_user_ban(request: Request, user_id: int = Form(...), ban_status: int = Form(...)):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    await db.set_ban(user_id, is_banned=bool(ban_status))
    return RedirectResponse(url=f"/?msg=Ban+holati+o'zgartirildi", status_code=status.HTTP_302_FOUND)

@app.post("/package/update")
async def update_package(
    request: Request,
    pkg_id: int = Form(...),
    stars_price: int = Form(...),
    amount: int = Form(...),
    bonus: int = Form(...),
    is_active: int = Form(...)
):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    pkg = await db.get_package_by_id(pkg_id)
    if pkg:
        title = f"💎 {amount} Almaz (+{bonus} bonus)" if pkg["package_type"] == "almaz" else f"💰 {amount:,} Pul (+{bonus:,} bonus)"
        await db.update_star_package(pkg_id, stars_price, amount, bonus, title, is_active)

    return RedirectResponse(url="/?msg=Stars+paketi+yangilandi", status_code=status.HTTP_302_FOUND)

@app.post("/item/update")
async def update_item_route(
    request: Request,
    code: str = Form(...),
    name: str = Form(...),
    price_pul: int = Form(...),
    price_almaz: int = Form(...),
    description: str = Form(...),
    is_active: int = Form(...)
):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    await db.update_item(code, name, price_pul, price_almaz, description, is_active)
    return RedirectResponse(url="/?msg=Do'kon+buyumi+yangilandi", status_code=status.HTTP_302_FOUND)

@app.post("/settings/exchange_rate")
async def update_exchange_rate(request: Request, rate: int = Form(...)):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    await db.set_setting("almaz_to_pul_rate", str(rate))
    return RedirectResponse(url="/?msg=Valyuta+kursi+yangilandi", status_code=status.HTTP_302_FOUND)


# --- KARTA ADMIN ROUTES ---
@app.post("/admin/card_settings/update")
async def update_card_settings(
    request: Request,
    card_number: str = Form(...),
    card_holder: str = Form(...),
    card_bank: str = Form(...)
):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    await db.set_card_details(card_number.strip(), card_holder.strip(), card_bank.strip())
    return RedirectResponse(url="/?tab=cards&msg=Karta+sozlamalari+saqlandi", status_code=status.HTTP_302_FOUND)

@app.post("/admin/card_package/update")
async def update_card_package_route(
    request: Request,
    pkg_id: int = Form(...),
    price_uzs: int = Form(...),
    amount: int = Form(...),
    bonus: int = Form(...),
    is_active: int = Form(...)
):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    await db.update_card_package(pkg_id, price_uzs, amount, bonus, is_active)
    return RedirectResponse(url="/?tab=cards&msg=Karta+paketi+yangilandi", status_code=status.HTTP_302_FOUND)

@app.post("/admin/card_transaction/approve")
async def approve_card_transaction_route(request: Request, tx_id: str = Form(...)):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    res = await db.complete_card_transaction(tx_id)
    if not res:
        return RedirectResponse(url="/?tab=cards&error=To'lov+topilmadi+yoki+allaqachon+bajarilgan", status_code=status.HTTP_302_FOUND)

    return RedirectResponse(url=f"/?tab=cards&msg=To'lov+{tx_id}+muvaffaqiyatli+tasdiqlandi", status_code=status.HTTP_302_FOUND)

@app.post("/admin/card_transaction/cancel")
async def cancel_card_transaction_route(request: Request, tx_id: str = Form(...)):
    if not require_admin(request):
        raise HTTPException(status_code=403, detail="Ruxsat berilmagan")

    await db.cancel_card_transaction(tx_id)
    return RedirectResponse(url=f"/?tab=cards&msg=To'lov+{tx_id}+bekor+qilindi", status_code=status.HTTP_302_FOUND)


# --- SOFPAY REST API (O'ZIMIZNING TO'LOV SHLYUZIMIZ) ---
@app.post("/api/v1/transaction/create")
async def api_create_transaction(payload: dict = Body(...)):
    amount = payload.get("amount", 1000)
    user_id = payload.get("user_id", 0)
    description = payload.get("description", "Mafia Bot To'lov")

    card_info = await db.get_card_details()
    tx_id = f"tx_{random.randint(10000000, 99999999)}"
    unique_offset = random.randint(7, 49)
    final_amount = int(amount) + unique_offset

    # Determine amount of almaz (1000 UZS = 10 Almaz)
    almaz_amount = int((amount / 1000) * 10)

    await db.create_card_transaction(
        user_id=user_id,
        package_id=0,
        tx_id=tx_id,
        item_type="almaz",
        item_amount=almaz_amount,
        price_uzs=int(amount),
        unique_amount=final_amount,
        card_number=card_info["card_number"],
        card_holder=card_info["card_holder"]
    )

    return JSONResponse({
        "success": True,
        "transaction": {
            "tx_id": tx_id,
            "amount": final_amount,
            "original_amount": int(amount),
            "status": "pending",
            "card_number": card_info["card_number"],
            "card_holder": card_info["card_holder"],
            "description": description,
            "shop": "Universal Mafia"
        }
    })

@app.get("/api/v1/transaction/{tx_id}")
async def api_get_transaction(tx_id: str):
    tx = await db.get_card_transaction(tx_id)
    if not tx:
        return JSONResponse({"success": False, "error": "Transaction not found"}, status_code=404)

    return JSONResponse({
        "success": True,
        "transaction": {
            "tx_id": tx["tx_id"],
            "amount": tx["unique_amount"],
            "original_amount": tx["price_uzs"],
            "status": tx["status"],
            "card_number": tx["card_number"],
            "paid_at": tx.get("completed_at")
        }
    })

@app.post("/api/v1/transaction/{tx_id}/cancel")
async def api_cancel_transaction(tx_id: str):
    tx = await db.get_card_transaction(tx_id)
    if not tx:
        return JSONResponse({"success": False, "error": "Transaction not found"}, status_code=404)

    await db.cancel_card_transaction(tx_id)
    return JSONResponse({"success": True, "status": "cancelled"})

@app.post("/api/v1/transaction/notify")
async def api_notify_transaction(payload: dict = Body(...)):
    """
    Android SMS Gateway yoki Bank webhook orqali avtomatik tasdiqlash.
    0% komissiya, 100% avtomat.
    """
    tx_id = payload.get("tx_id")
    unique_amount = payload.get("amount")

    target_tx = None
    if tx_id:
        target_tx = await db.get_card_transaction(tx_id)
    elif unique_amount:
        # Match by unique amount
        pending_txs = await db.get_card_transactions(limit=10, status="pending")
        for p in pending_txs:
            if p["unique_amount"] == int(unique_amount):
                target_tx = p
                break

    if target_tx and target_tx["status"] == "pending":
        res = await db.complete_card_transaction(target_tx["tx_id"])
        return JSONResponse({"success": True, "message": "Transaction completed", "tx_id": target_tx["tx_id"]})

    return JSONResponse({"success": False, "message": "No matching pending transaction found"}, status_code=404)

@app.post("/api/v1/sofpay/webhook")
@app.post("/api/v1/webhook/sofpay")
async def sofpay_webhook(payload: dict = Body(...)):
    """
    SofPay rasmiy Webhook qabul qiluvchi endpoint.
    Payload:
    {
        "tx_id": "tx_8d77ed9ed24148871a7",
        "amount": 50037,
        "status": "completed",
        "card_last4": "5774",
        "shop_name": "Aiobuna",
        "description": "Buyurtma #123",
        "paid_at": "2026-05-03T16:42:11"
    }
    """
    tx_id = payload.get("tx_id")
    status_str = payload.get("status")

    if not tx_id:
        return JSONResponse({"success": False, "error": "tx_id missing"}, status_code=400)

    if status_str == "completed":
        target_tx = await db.get_card_transaction(tx_id)
        if target_tx and target_tx["status"] == "pending":
            comp = await db.complete_card_transaction(tx_id)
            if comp:
                # Notify user and admin via Telegram bot
                try:
                    from config import BOT_TOKEN, ADMIN_IDS
                    from aiogram import Bot
                    bot = Bot(token=BOT_TOKEN)
                    user_msg = (
                        f"🎉 <b>TO'LOV MUVAFFAQIYATLI QABUL QILINDI!</b>\n\n"
                        f"🆔 To'lov: <code>#{tx_id}</code>\n"
                        f"📦 Mahsulot: <b>+{comp['item_amount']:,} {comp['item_type'].upper()}</b>\n"
                        f"💵 Summa: <b>{comp['unique_amount']:,} so'm</b>\n\n"
                        f"Hisobingiz to'ldirildi. O'yinda omad tilaymiz! 🎲"
                    )
                    await bot.send_message(chat_id=comp["user_id"], text=user_msg, parse_mode="HTML")

                    for aid in ADMIN_IDS:
                        admin_msg = (
                            f"💰 <b>SOFPAY TO'LOV KELDI!</b>\n\n"
                            f"🆔 TX: <code>#{tx_id}</code>\n"
                            f"👤 O'yinchi: <code>{comp['user_id']}</code>\n"
                            f"💵 Summa: <b>{comp['unique_amount']:,} so'm</b>\n"
                            f"📦 Berildi: {comp['item_amount']:,} {comp['item_type'].upper()}"
                        )
                        await bot.send_message(chat_id=aid, text=admin_msg, parse_mode="HTML")
                    await bot.session.close()
                except Exception:
                    pass

                return JSONResponse({"success": True, "message": "Transaction completed and credited", "tx_id": tx_id})

    return JSONResponse({"success": True, "message": "Webhook received", "status": status_str})


