import os
import time
import base64
import json
import sqlite3
import asyncio
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Tuple

from config import GITHUB_TOKEN, GITHUB_REPO, GITHUB_DB_BACKUP_PATH, DB_PATH

logger = logging.getLogger("DatabaseSync")

class DatabaseSyncManager:
    def __init__(self):
        self.token = GITHUB_TOKEN
        self.repo = GITHUB_REPO
        self.backup_path = GITHUB_DB_BACKUP_PATH
        self.db_path = Path(DB_PATH)
        self.last_backup_time: Optional[float] = None
        self.last_backup_status: str = "Hali bajarilmadi"
        self.last_backup_size: int = 0

    def is_configured(self) -> bool:
        return bool(self.token and self.repo and self.backup_path)

    def _sync_get_file_info(self) -> Tuple[Optional[str], Optional[bytes]]:
        """GitHub API orqali faylning sha va content ini oladi."""
        if not self.is_configured():
            return None, None

        url = f"https://api.github.com/repos/{self.repo}/contents/{self.backup_path}"
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "MafiaBot-DBSync"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as res:
                data = json.loads(res.read().decode("utf-8"))
                sha = data.get("sha")
                raw_content = None
                if data.get("content"):
                    raw_content = base64.b64decode(data["content"])
                elif data.get("download_url"):
                    dl_req = urllib.request.Request(
                        data["download_url"],
                        headers={
                            "Authorization": f"Bearer {self.token}",
                            "User-Agent": "MafiaBot-DBSync"
                        }
                    )
                    with urllib.request.urlopen(dl_req, timeout=30) as dl_res:
                        raw_content = dl_res.read()
                return sha, raw_content
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None, None
            logger.warning(f"GitHub API HTTP xatosi ({e.code}): {e.reason}")
            return None, None
        except Exception as e:
            logger.warning(f"GitHub API bilan bog'lanishda xato: {e}")
            return None, None

    def _sync_put_file(self, content_bytes: bytes, sha: Optional[str] = None) -> bool:
        """GitHub API orqali ma'lumotlar bazasini yuklaydi."""
        if not self.is_configured():
            return False

        url = f"https://api.github.com/repos/{self.repo}/contents/{self.backup_path}"
        b64_content = base64.b64encode(content_bytes).decode("utf-8")
        payload = {
            "message": f"Auto-sync database backup [{time.strftime('%Y-%m-%d %H:%M:%S')}]",
            "content": b64_content
        }
        if sha:
            payload["sha"] = sha

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github+json",
                "Content-Type": "application/json",
                "User-Agent": "MafiaBot-DBSync"
            },
            method="PUT"
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                return res.getcode() in (200, 201)
        except Exception as e:
            logger.warning(f"Baza yuklashda xatolik: {e}")
            return False

    async def restore_from_cloud(self) -> bool:
        """Bot ishga tushganda GitHub Cloud'dan eng so'nggi bazani tiklaydi."""
        if not self.is_configured():
            logger.info("ℹ️ GitHub token yoki repo sozlanmagan, lokal baza ishlatiladi.")
            return False

        logger.info("🔍 GitHub Cloud'dan so'nggi baza nusxasi tekshirilmoqda...")
        try:
            sha, content = await asyncio.to_thread(self._sync_get_file_info)
            if not content:
                logger.info("ℹ️ GitHub Cloud'da zaxira baza topilmadi. Mahalliy baza ishlatiladi.")
                return False

            # SQLite sarlavhasini tekshirish
            if not content.startswith(b"SQLite format 3\x00"):
                logger.warning("⚠️ Cloud'dagi fayl haqiqiy SQLite bazasi emas!")
                return False

            # Agar lokal baza mavjud bo'lsa va uning hajmi/vaqti solishtirilsa
            local_exists = self.db_path.exists()
            local_size = self.db_path.stat().st_size if local_exists else 0

            # Cloud bazani DB_PATH ga yozish
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.db_path, "wb") as f:
                f.write(content)

            self.last_backup_size = len(content)
            self.last_backup_status = "Cloud'dan tiklandi"
            logger.info(f"✅ Baza GitHub Cloud'dan muvaffaqiyatli tiklandi! ({len(content):,} bayt)")
            return True
        except Exception as e:
            logger.error(f"❌ Cloud'dan tiklashda kutilmagan xato: {e}")
            return False

    async def backup_to_cloud(self) -> bool:
        """Joriy SQLite bazasini xavfsiz holda GitHub Cloud'ga zaxira qiladi."""
        if not self.is_configured():
            return False

        if not self.db_path.exists():
            return False

        logger.info("📤 Baza GitHub Cloud'ga zaxiralanmoqda...")
        temp_backup = self.db_path.parent / "sync_temp_backup.db"
        try:
            # SQLite online backup API orqali toza nusxa olish
            def create_clean_dump():
                src = sqlite3.connect(str(self.db_path))
                dst = sqlite3.connect(str(temp_backup))
                src.backup(dst)
                src.close()
                dst.close()
                with open(temp_backup, "rb") as f:
                    return f.read()

            data = await asyncio.to_thread(create_clean_dump)

            # Mavjud faylning sha sini olish
            sha, _ = await asyncio.to_thread(self._sync_get_file_info)

            # Faylni GitHub ga yuklash
            success = await asyncio.to_thread(self._sync_put_file, data, sha)
            if success:
                self.last_backup_time = time.time()
                self.last_backup_size = len(data)
                self.last_backup_status = "Muvaffaqiyatli saqlandi"
                logger.info(f"✅ Baza GitHub Cloud'ga muvaffaqiyatli saqlandi! ({len(data):,} bayt)")
                return True
            else:
                self.last_backup_status = "Yuklashda xatolik yuz berdi"
                return False
        except Exception as e:
            logger.error(f"❌ Baza zaxiralashda xato: {e}")
            self.last_backup_status = f"Xato: {e}"
            return False
        finally:
            if temp_backup.exists():
                try:
                    temp_backup.unlink()
                except Exception:
                    pass

    async def run_auto_backup_loop(self, interval_seconds: int = 300):
        """Har 5 daqiqada avtomatik zaxiralab turuvchi orqa fon vazifasi."""
        await asyncio.sleep(60) # Bot ishga tushgach 1 daqiqa kutish
        while True:
            try:
                await self.backup_to_cloud()
            except Exception as e:
                logger.warning(f"Avto-zaxira tsiklida xato: {e}")
            await asyncio.sleep(interval_seconds)

db_sync = DatabaseSyncManager()
