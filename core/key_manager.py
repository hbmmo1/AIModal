"""
Key Manager — Quản lý API Keys đa nhà cung cấp (Multi-Provider).
Hỗ trợ: Gemini, OpenAI, Anthropic (Claude), DeepSeek, Qwen.
- Thêm/Xoá/Kiểm tra/Luân chuyển API Keys theo từng provider
- Tự động rotation khi hết Quota (429 / Resource Exhausted)
- Tự động nhận diện provider từ key format
- Quota tracking per key
- Sync từ config.yaml + .env
"""

import os
import sqlite3
import yaml
import logging
import warnings
from datetime import datetime
from typing import List, Dict, Optional

from core.model_registry import Provider, PROVIDER_DISPLAY, registry as model_registry

warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google_genai").setLevel(logging.ERROR)

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "config", "app_data.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config", "config.yaml")
ENV_PATH = os.path.join(BASE_DIR, ".env")


class KeyManager:
    """
    Quản lý API Keys đa nhà cung cấp:
    - Mỗi key gắn với 1 provider (gemini, openai, anthropic, deepseek, qwen)
    - Tự động nhận diện provider từ format key
    - Luân chuyển key trong cùng provider khi hết quota
    - Kiểm tra sức khoẻ key theo từng provider
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()
        self._sync_initial_keys()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Khởi tạo bảng lưu trữ API Keys trong SQLite."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    api_key TEXT UNIQUE,
                    provider TEXT DEFAULT 'gemini',
                    status TEXT DEFAULT 'AVAILABLE',
                    is_active INTEGER DEFAULT 0,
                    request_count INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0,
                    last_status_msg TEXT DEFAULT '',
                    last_checked_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Migrate: nếu bảng cũ gemini_api_keys tồn tại, chuyển data sang
            try:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gemini_api_keys'")
                if cursor.fetchone():
                    cursor.execute("""
                        INSERT OR IGNORE INTO api_keys (api_key, provider, status, is_active, request_count, error_count, last_status_msg, last_checked_at, created_at)
                        SELECT api_key, 'gemini', status, is_active, request_count, error_count, last_status_msg, last_checked_at, created_at
                        FROM gemini_api_keys
                    """)
                    cursor.execute("DROP TABLE IF EXISTS gemini_api_keys")
                    logger.info("[KeyManager] Đã migrate dữ liệu từ bảng cũ gemini_api_keys → api_keys")
            except Exception:
                pass
            conn.commit()

    def _sync_initial_keys(self):
        """Đồng bộ API keys từ .env và config.yaml vào database."""
        keys_to_add = []

        # 1. Đọc từ .env — tất cả provider keys
        try:
            if os.path.exists(ENV_PATH):
                from dotenv import dotenv_values
                env_vars = dotenv_values(ENV_PATH)
                
                env_mappings = {
                    "GEMINI_API_KEY": Provider.GEMINI,
                    "OPENAI_API_KEY": Provider.OPENAI,
                    "ANTHROPIC_API_KEY": Provider.ANTHROPIC,
                    "DEEPSEEK_API_KEY": Provider.DEEPSEEK,
                    "QWEN_API_KEY": Provider.QWEN,
                    "MISTRAL_API_KEY": Provider.MISTRAL,
                    "COHERE_API_KEY": Provider.COHERE,
                    "META_API_KEY": Provider.META,
                    "XAI_API_KEY": Provider.XAI,
                }
                for env_name, provider in env_mappings.items():
                    key = env_vars.get(env_name, "").strip()
                    if key and not key.startswith("YOUR_") and not key.startswith("your_"):
                        keys_to_add.append((key, provider))
        except Exception as e:
            logger.debug(f"Không thể đọc .env: {e}")

        # 2. Đọc từ config.yaml
        try:
            if os.path.exists(CONFIG_PATH):
                with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                    
                    # Gemini key
                    gemini_key = cfg.get("gemini", {}).get("api_key", "").strip()
                    if gemini_key and not gemini_key.startswith("YOUR_"):
                        if not any(k == gemini_key for k, _ in keys_to_add):
                            keys_to_add.append((gemini_key, Provider.GEMINI))
                    
                    # Provider keys section
                    providers_cfg = cfg.get("providers", {})
                    for prov_name, prov_cfg in providers_cfg.items():
                        if isinstance(prov_cfg, dict):
                            prov_key = prov_cfg.get("api_key", "").strip()
                            if prov_key and not prov_key.startswith("YOUR_"):
                                if not any(k == prov_key for k, _ in keys_to_add):
                                    keys_to_add.append((prov_key, prov_name))
        except Exception as e:
            logger.debug(f"Không thể đọc config.yaml: {e}")

        for key, provider in keys_to_add:
            self.add_key(key, provider)

    def load_keys(self):
        """Tải và đồng bộ lại danh sách API Keys từ .env và config.yaml."""
        self._sync_initial_keys()
        logger.info("[KeyManager] Đã tải lại danh sách API Keys thành công.")

    def reload_keys(self):
        """Alias cho load_keys."""
        self.load_keys()

    def _detect_provider(self, api_key: str) -> str:
        """Tự động nhận diện provider từ format key."""
        key = api_key.strip()
        if key.startswith("AIza"):
            return Provider.GEMINI
        elif key.startswith("sk-ant-"):
            return Provider.ANTHROPIC
        elif key.startswith("xai-"):
            return Provider.XAI
        return ""

    def add_key(self, api_key: str, provider: str = "") -> bool:
        """Thêm 1 API key với provider chỉ định. Trả về True nếu thành công."""
        key = api_key.strip()
        if not key:
            return False
        
        # Auto-detect provider nếu chưa chỉ định
        if not provider:
            provider = self._detect_provider(key)
            if not provider:
                provider = Provider.GEMINI  # Default fallback
        
        with self._get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT OR IGNORE INTO api_keys (api_key, provider) VALUES (?, ?)",
                    (key, provider)
                )
                if cursor.rowcount > 0:
                    # Đảm bảo provider có ít nhất 1 key active
                    cursor.execute(
                        "SELECT COUNT(*) as cnt FROM api_keys WHERE provider = ? AND is_active = 1",
                        (provider,)
                    )
                    if cursor.fetchone()["cnt"] == 0:
                        cursor.execute(
                            "UPDATE api_keys SET is_active = 1 WHERE api_key = ?", (key,)
                        )
                    conn.commit()
                    logger.info(f"[KeyManager] Đã thêm key [{PROVIDER_DISPLAY.get(provider, {}).get('name', provider)}]: ...{key[-8:]}")
                    return True
            except sqlite3.IntegrityError:
                pass
            conn.commit()
        return False

    def add_keys_bulk(self, keys_text: str, provider: str = "") -> int:
        """Thêm nhiều keys (mỗi dòng 1 key). Trả về số key thêm thành công."""
        keys = [k.strip() for k in keys_text.strip().split("\n") if k.strip()]
        added = 0
        for key in keys:
            if self.add_key(key, provider):
                added += 1
        return added

    def remove_key(self, api_key: str) -> bool:
        """Xoá 1 API key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Lấy provider trước khi xoá
            cursor.execute("SELECT provider FROM api_keys WHERE api_key = ?", (api_key,))
            row = cursor.fetchone()
            provider = row["provider"] if row else ""
            
            cursor.execute("DELETE FROM api_keys WHERE api_key = ?", (api_key,))
            removed = cursor.rowcount > 0
            
            if removed and provider:
                # Đảm bảo provider vẫn có key active
                cursor.execute(
                    "SELECT COUNT(*) as cnt FROM api_keys WHERE provider = ? AND is_active = 1",
                    (provider,)
                )
                if cursor.fetchone()["cnt"] == 0:
                    cursor.execute(
                        "UPDATE api_keys SET is_active = 1 WHERE id = (SELECT MIN(id) FROM api_keys WHERE provider = ? AND status = 'AVAILABLE')",
                        (provider,)
                    )
            conn.commit()
        return removed

    def get_active_key(self, provider: str = None) -> Optional[str]:
        """Lấy API key đang active cho provider chỉ định (hoặc bất kỳ)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if provider:
                cursor.execute(
                    "SELECT api_key FROM api_keys WHERE provider = ? AND is_active = 1 LIMIT 1",
                    (provider,)
                )
            else:
                cursor.execute("SELECT api_key FROM api_keys WHERE is_active = 1 LIMIT 1")
            row = cursor.fetchone()
            if row:
                return row["api_key"]

            # Fallback: Lấy key đầu tiên có trạng thái AVAILABLE hoặc bất kỳ key nào của provider
            if provider:
                cursor.execute(
                    "SELECT api_key FROM api_keys WHERE provider = ? AND status != 'INVALID' ORDER BY (CASE WHEN status='AVAILABLE' THEN 0 ELSE 1 END), id ASC LIMIT 1",
                    (provider,)
                )
            else:
                cursor.execute("SELECT api_key FROM api_keys WHERE status != 'INVALID' ORDER BY (CASE WHEN status='AVAILABLE' THEN 0 ELSE 1 END), id ASC LIMIT 1")
            fallback_row = cursor.fetchone()
            if fallback_row:
                try:
                    cursor.execute("UPDATE api_keys SET is_active = 1 WHERE api_key = ?", (fallback_row["api_key"],))
                    conn.commit()
                except Exception:
                    pass
                return fallback_row["api_key"]

            return None

    def set_active_key(self, api_key: str) -> bool:
        """Đặt 1 key làm active (chỉ trong cùng provider)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Lấy provider
            cursor.execute("SELECT provider FROM api_keys WHERE api_key = ?", (api_key,))
            row = cursor.fetchone()
            if not row:
                return False
            provider = row["provider"]
            
            # Deactivate tất cả key cùng provider, rồi activate key này
            cursor.execute("UPDATE api_keys SET is_active = 0 WHERE provider = ?", (provider,))
            cursor.execute("UPDATE api_keys SET is_active = 1 WHERE api_key = ?", (api_key,))
            conn.commit()
            return True

    def rotate_to_next(self, failed_key: str = None, error_msg: str = "", provider: str = None) -> Optional[str]:
        """Luân chuyển sang key tiếp theo (cùng provider) khi key hiện tại lỗi."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            if failed_key:
                # Lấy provider từ failed key
                cursor.execute("SELECT provider FROM api_keys WHERE api_key = ?", (failed_key,))
                row = cursor.fetchone()
                if row:
                    provider = row["provider"]
                
                cursor.execute(
                    "UPDATE api_keys SET status = 'QUOTA_EXCEEDED', error_count = error_count + 1, "
                    "last_status_msg = ?, last_checked_at = ?, is_active = 0 WHERE api_key = ?",
                    (error_msg, datetime.now().isoformat(), failed_key)
                )

            # Tìm key AVAILABLE tiếp theo (cùng provider)
            if provider:
                cursor.execute(
                    "SELECT api_key FROM api_keys WHERE provider = ? AND status = 'AVAILABLE' AND is_active = 0 ORDER BY request_count ASC LIMIT 1",
                    (provider,)
                )
            else:
                cursor.execute(
                    "SELECT api_key FROM api_keys WHERE status = 'AVAILABLE' AND is_active = 0 ORDER BY request_count ASC LIMIT 1"
                )
            
            row = cursor.fetchone()
            if row:
                new_key = row["api_key"]
                if provider:
                    cursor.execute("UPDATE api_keys SET is_active = 0 WHERE provider = ?", (provider,))
                cursor.execute("UPDATE api_keys SET is_active = 1 WHERE api_key = ?", (new_key,))
                conn.commit()
                logger.info(f"[KeyManager] Đã luân chuyển sang key mới: ...{new_key[-8:]}")
                return new_key

            # Nếu không còn key AVAILABLE nào khác: Phục hồi lại key để người dùng có thể thử lại sau khi hồi quota
            if failed_key:
                cursor.execute("UPDATE api_keys SET is_active = 1 WHERE api_key = ?", (failed_key,))
            elif provider:
                cursor.execute(
                    "UPDATE api_keys SET is_active = 1 WHERE provider = ? AND status != 'INVALID' ORDER BY request_count ASC LIMIT 1",
                    (provider,)
                )
            else:
                cursor.execute(
                    "UPDATE api_keys SET is_active = 1 WHERE status != 'INVALID' ORDER BY request_count ASC LIMIT 1"
                )
            conn.commit()
            logger.warning(f"[KeyManager] Tất cả key cho {provider or 'hệ thống'} đều đang chạm ngưỡng quota/rate limit. Đã giữ key active để thử lại.")
            return None

    def increment_request(self, api_key: str):
        """Tăng request count cho key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE api_keys SET request_count = request_count + 1 WHERE api_key = ?",
                (api_key,)
            )
            conn.commit()

    def get_all_keys(self, provider: str = None) -> List[Dict]:
        """Lấy danh sách tất cả keys (tuỳ chọn filter theo provider)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if provider:
                cursor.execute("SELECT * FROM api_keys WHERE provider = ? ORDER BY provider, id", (provider,))
            else:
                cursor.execute("SELECT * FROM api_keys ORDER BY provider, id")
            return [dict(row) for row in cursor.fetchall()]

    def get_providers_with_keys(self) -> List[str]:
        """Lấy danh sách providers đã có key."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT provider FROM api_keys ORDER BY provider")
            return [row["provider"] for row in cursor.fetchall()]

    def reset_all_quotas(self, provider: str = None):
        """Reset trạng thái keys về AVAILABLE."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if provider:
                cursor.execute(
                    "UPDATE api_keys SET status = 'AVAILABLE', error_count = 0, last_status_msg = '' WHERE provider = ?",
                    (provider,)
                )
            else:
                cursor.execute(
                    "UPDATE api_keys SET status = 'AVAILABLE', error_count = 0, last_status_msg = ''"
                )
            conn.commit()
            logger.info(f"[KeyManager] Đã reset quota {'tất cả' if not provider else provider} API keys")

    def reset_key_quota(self, api_key: str):
        """Reset 1 key về AVAILABLE."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE api_keys SET status = 'AVAILABLE', error_count = 0, last_status_msg = '' WHERE api_key = ?",
                (api_key,)
            )
            conn.commit()

    def check_key_health(self, api_key: str) -> Dict:
        """Kiểm tra sức khỏe API key bằng cách gọi API thử."""
        # Lấy provider
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT provider FROM api_keys WHERE api_key = ?", (api_key,))
            row = cursor.fetchone()
            provider = row["provider"] if row else self._detect_provider(api_key) or Provider.GEMINI

        result = {"key": api_key, "provider": provider, "status": "UNKNOWN", "message": ""}

        try:
            if provider == Provider.GEMINI:
                result = self._check_gemini_key(api_key)
            elif provider == Provider.OPENAI:
                result = self._check_openai_key(api_key)
            elif provider == Provider.ANTHROPIC:
                result = self._check_anthropic_key(api_key)
            elif provider == Provider.DEEPSEEK:
                result = self._check_deepseek_key(api_key)
            elif provider == Provider.QWEN:
                result = self._check_qwen_key(api_key)
            else:
                result["message"] = "Provider không xác định"

            # Cập nhật DB
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE api_keys SET status = ?, last_status_msg = ?, last_checked_at = ? WHERE api_key = ?",
                    (result["status"], result["message"], datetime.now().isoformat(), api_key)
                )
                conn.commit()

        except Exception as e:
            result["status"] = "ERROR"
            result["message"] = str(e)[:200]

        result["provider"] = provider
        return result

    def _check_gemini_key(self, api_key: str) -> Dict:
        """Kiểm tra Gemini key."""
        from google import genai
        client = genai.Client(api_key=api_key)
        
        # Thử với các model nhẹ và ổn định nhất của Gemini
        check_models = ["gemini-3.5-flash-lite", "gemini-3.1-flash-lite", "gemini-flash-lite-latest", "gemini-2.5-flash-lite"]
        last_err = None
        for m in check_models:
            try:
                response = client.models.generate_content(
                    model=m,
                    contents="Respond with only: OK"
                )
                if response and response.text:
                    return {"key": api_key, "status": "AVAILABLE", "message": f"✅ Key hoạt động ({m})"}
            except Exception as e:
                err_str = str(e)
                last_err = err_str
                if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str.upper() or "QUOTA" in err_str.upper():
                    return {"key": api_key, "status": "QUOTA_EXCEEDED", "message": "Hết quota / Rate limit"}
                elif "API_KEY_INVALID" in err_str.upper() or "400" in err_str or "401" in err_str or "403" in err_str:
                    return {"key": api_key, "status": "INVALID", "message": "Key không hợp lệ"}
                continue

        return {"key": api_key, "status": "ERROR", "message": (last_err[:150] if last_err else "Không nhận được response")}

    def _check_openai_key(self, api_key: str) -> Dict:
        """Kiểm tra OpenAI key."""
        import requests
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5},
            timeout=15
        )
        if resp.status_code == 200:
            return {"key": api_key, "status": "AVAILABLE", "message": "✅ Key hoạt động"}
        elif resp.status_code == 429:
            return {"key": api_key, "status": "QUOTA_EXCEEDED", "message": "Hết quota"}
        elif resp.status_code in (401, 403):
            return {"key": api_key, "status": "INVALID", "message": "Key không hợp lệ"}
        return {"key": api_key, "status": "ERROR", "message": f"HTTP {resp.status_code}"}

    def _check_anthropic_key(self, api_key: str) -> Dict:
        """Kiểm tra Anthropic key."""
        import requests
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json={
                "model": "claude-haiku-3-5-20241022",
                "max_tokens": 5,
                "messages": [{"role": "user", "content": "Say OK"}]
            },
            timeout=15
        )
        if resp.status_code == 200:
            return {"key": api_key, "status": "AVAILABLE", "message": "✅ Key hoạt động"}
        elif resp.status_code == 429:
            return {"key": api_key, "status": "QUOTA_EXCEEDED", "message": "Hết quota"}
        elif resp.status_code in (401, 403):
            return {"key": api_key, "status": "INVALID", "message": "Key không hợp lệ"}
        return {"key": api_key, "status": "ERROR", "message": f"HTTP {resp.status_code}"}

    def _check_deepseek_key(self, api_key: str) -> Dict:
        """Kiểm tra DeepSeek key."""
        import requests
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "deepseek-chat", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5},
            timeout=15
        )
        if resp.status_code == 200:
            return {"key": api_key, "status": "AVAILABLE", "message": "✅ Key hoạt động"}
        elif resp.status_code == 429:
            return {"key": api_key, "status": "QUOTA_EXCEEDED", "message": "Hết quota"}
        elif resp.status_code in (401, 403):
            return {"key": api_key, "status": "INVALID", "message": "Key không hợp lệ"}
        return {"key": api_key, "status": "ERROR", "message": f"HTTP {resp.status_code}"}

    def _check_qwen_key(self, api_key: str) -> Dict:
        """Kiểm tra Qwen key."""
        import requests
        resp = requests.post(
            "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "qwen-turbo", "messages": [{"role": "user", "content": "Say OK"}], "max_tokens": 5},
            timeout=15
        )
        if resp.status_code == 200:
            return {"key": api_key, "status": "AVAILABLE", "message": "✅ Key hoạt động"}
        elif resp.status_code == 429:
            return {"key": api_key, "status": "QUOTA_EXCEEDED", "message": "Hết quota"}
        elif resp.status_code in (401, 403):
            return {"key": api_key, "status": "INVALID", "message": "Key không hợp lệ"}
        return {"key": api_key, "status": "ERROR", "message": f"HTTP {resp.status_code}"}

    @property
    def key_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM api_keys")
            return cursor.fetchone()["cnt"]

    @property
    def available_count(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM api_keys WHERE status = 'AVAILABLE'")
            return cursor.fetchone()["cnt"]

    def get_provider_key_count(self, provider: str) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM api_keys WHERE provider = ?", (provider,))
            return cursor.fetchone()["cnt"]

    def get_key_quota_summary(self, provider: str = None) -> Dict:
        """Trả về tổng hợp quota info: số key, trạng thái, tổng request đã dùng."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if provider:
                cursor.execute(
                    "SELECT COUNT(*) as total, "
                    "SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) as available, "
                    "SUM(CASE WHEN status = 'QUOTA_EXCEEDED' THEN 1 ELSE 0 END) as exhausted, "
                    "SUM(CASE WHEN status = 'INVALID' THEN 1 ELSE 0 END) as invalid, "
                    "SUM(request_count) as total_requests, "
                    "SUM(error_count) as total_errors "
                    "FROM api_keys WHERE provider = ?",
                    (provider,)
                )
            else:
                cursor.execute(
                    "SELECT COUNT(*) as total, "
                    "SUM(CASE WHEN status = 'AVAILABLE' THEN 1 ELSE 0 END) as available, "
                    "SUM(CASE WHEN status = 'QUOTA_EXCEEDED' THEN 1 ELSE 0 END) as exhausted, "
                    "SUM(CASE WHEN status = 'INVALID' THEN 1 ELSE 0 END) as invalid, "
                    "SUM(request_count) as total_requests, "
                    "SUM(error_count) as total_errors "
                    "FROM api_keys"
                )
            row = cursor.fetchone()
            return {
                "total_keys": row["total"] or 0,
                "available": row["available"] or 0,
                "exhausted": row["exhausted"] or 0,
                "invalid": row["invalid"] or 0,
                "total_requests": row["total_requests"] or 0,
                "total_errors": row["total_errors"] or 0,
            }

    def get_key_details(self, api_key: str) -> Optional[Dict]:
        """Lấy chi tiết 1 key bao gồm request_count, error_count, status."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM api_keys WHERE api_key = ?", (api_key,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # Backward compatibility
    def add_keys(self, keys_text: str) -> int:
        """Backward compatible — thêm Gemini keys."""
        return self.add_keys_bulk(keys_text, Provider.GEMINI)

