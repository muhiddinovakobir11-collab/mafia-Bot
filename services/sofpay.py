import logging
from typing import Optional, Dict, Any
import httpx
from config import SOFPAY_SHOP_KEY, SOFPAY_API_URL

logger = logging.getLogger("SofPayService")

class SofPayClient:
    def __init__(self, shop_key: str = SOFPAY_SHOP_KEY, base_url: str = SOFPAY_API_URL):
        self.shop_key = shop_key
        self.base_url = base_url.rstrip("/")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "X-Shop-Key": self.shop_key,
            "Content-Type": "application/json",
            "User-Agent": "MafiaBot-Payment/1.0"
        }

    async def create_transaction(self, amount: int, description: str = "") -> Optional[Dict[str, Any]]:
        """
        SofPay orqali yangi to'lov hisobini ochish.
        Javob:
        {
            "tx_id": "tx_...",
            "amount": 50037, # to'lanishi kerak bo'lgan summa (tiyinlar bilan)
            "original_amount": 50000,
            "status": "pending",
            "card_number": "5614 6810 1674 5774",
            "shop": "Aiobuna"
        }
        """
        url = f"{self.base_url}/transaction/create"
        payload = {
            "amount": int(amount),
            "description": description[:100]
        }
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, json=payload, headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and "transaction" in data:
                        return data["transaction"]
                logger.error(f"SofPay create_transaction xatolik: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"SofPay API ulanishda xatolik: {e}")
        return None

    async def get_transaction(self, tx_id: str) -> Optional[Dict[str, Any]]:
        """
        SofPay to'lov holatini tekshirish.
        """
        url = f"{self.base_url}/transaction/{tx_id}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("success") and "transaction" in data:
                        return data["transaction"]
                logger.warning(f"SofPay get_transaction javobi: {resp.status_code} - {resp.text}")
        except Exception as e:
            logger.error(f"SofPay get_transaction xatolik: {e}")
        return None

    async def cancel_transaction(self, tx_id: str) -> bool:
        """
        SofPay to'lovini bekor qilish.
        """
        url = f"{self.base_url}/transaction/{tx_id}/cancel"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(url, headers=self.headers)
                if resp.status_code == 200:
                    data = resp.json()
                    return bool(data.get("success"))
        except Exception as e:
            logger.error(f"SofPay cancel_transaction xatolik: {e}")
        return False

sofpay_client = SofPayClient()
