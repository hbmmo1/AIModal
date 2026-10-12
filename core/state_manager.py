"""
State Manager — Quản lý trạng thái ứng dụng và lịch sử thực thi.
SQLite-backed storage cho chat history, execution logs, statistics.
"""

import os
import json
import sqlite3
import logging
import hashlib
import secrets
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "config", "app_data.db")


class StateManager:
    """Quản lý trạng thái ứng dụng, lịch sử chat, execution logs, người dùng & xác thực."""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Khởi tạo database schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Chat sessions metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Chat history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT DEFAULT 'default',
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    has_image INTEGER DEFAULT 0,
                    tool_calls TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Execution logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    workflow_name TEXT,
                    action_type TEXT,
                    action_detail TEXT,
                    status TEXT DEFAULT 'SUCCESS',
                    error_message TEXT DEFAULT '',
                    duration_ms INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Statistics
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    stat_key TEXT UNIQUE,
                    stat_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Application settings
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT UNIQUE,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Saved workflows metadata
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS workflows (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    file_path TEXT,
                    run_count INTEGER DEFAULT 0,
                    last_run_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    salt TEXT NOT NULL,
                    display_name TEXT DEFAULT '',
                    role TEXT DEFAULT 'admin',
                    is_active INTEGER DEFAULT 1,
                    login_count INTEGER DEFAULT 0,
                    last_login_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Login history & logs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS login_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    status TEXT DEFAULT 'SUCCESS',
                    ip_or_device TEXT DEFAULT 'Local Desktop',
                    message TEXT DEFAULT '',
                    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Auto-seed default admin account if users table is empty
            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            if cursor.fetchone()["cnt"] == 0:
                salt = secrets.token_hex(16)
                pwd_hash = hashlib.sha256(f"{salt}admin".encode("utf-8")).hexdigest()
                now_iso = datetime.now().isoformat()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, salt, display_name, role, is_active, login_count, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?)",
                    ("admin", pwd_hash, salt, "Administrator", "admin", now_iso, now_iso)
                )

            conn.commit()

    # ==================== Chat History & Sessions ====================

    def create_chat_session(self, title: str = "Cuộc trò chuyện mới") -> str:
        """Tạo một phiên trò chuyện mới."""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:19]}"
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title, now_iso, now_iso)
            )
            conn.commit()
        return session_id

    def get_all_chat_sessions(self) -> List[Dict]:
        """Lấy tất cả các phiên chat kèm số lượng tin nhắn và tin nhắn gần nhất."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Đảm bảo các session cũ trong chat_history có mặt trong chat_sessions
            cursor.execute("""
                INSERT OR IGNORE INTO chat_sessions (id, title, created_at, updated_at)
                SELECT DISTINCT session_id,
                       CASE WHEN session_id = 'default' THEN 'Cuộc trò chuyện mặc định' ELSE 'Đoạn chat ' || substr(session_id, 9, 15) END,
                       min(created_at), max(created_at)
                FROM chat_history
                WHERE session_id IS NOT NULL AND session_id != ''
                GROUP BY session_id
            """)
            conn.commit()

            cursor.execute("""
                SELECT s.id, s.title, s.created_at, s.updated_at,
                       COUNT(h.id) AS msg_count,
                       (SELECT content FROM chat_history WHERE session_id = s.id ORDER BY id DESC LIMIT 1) AS last_message
                FROM chat_sessions s
                LEFT JOIN chat_history h ON s.id = h.session_id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_chat_session(self, session_id: str) -> Optional[Dict]:
        """Lấy thông tin của 1 session chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM chat_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def rename_chat_session(self, session_id: str, new_title: str):
        """Đổi tên phiên chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
                (new_title.strip() or "Cuộc trò chuyện", datetime.now().isoformat(), session_id)
            )
            conn.commit()

    def delete_chat_session(self, session_id: str):
        """Xoá 1 phiên chat và toàn bộ tin nhắn thuộc phiên đó."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
            cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            conn.commit()

    def clear_all_chat_sessions(self):
        """Xoá toàn bộ phiên chat và lịch sử."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_sessions")
            cursor.execute("DELETE FROM chat_history")
            conn.commit()

    def save_chat_message(self, role: str, content: str, session_id: str = "default",
                          has_image: bool = False, tool_calls: list = None):
        """Lưu tin nhắn chat và tự động cập nhật tên session theo tin nhắn đầu."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            now_iso = datetime.now().isoformat()

            # Đảm bảo session tồn tại
            cursor.execute("SELECT id, title FROM chat_sessions WHERE id = ?", (session_id,))
            session_row = cursor.fetchone()

            if not session_row:
                auto_title = "Cuộc trò chuyện"
                if role == "user" and content:
                    auto_title = content[:35].replace("\n", " ").strip()
                cursor.execute(
                    "INSERT INTO chat_sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                    (session_id, auto_title, now_iso, now_iso)
                )
            else:
                current_title = session_row["title"]
                # Nếu tiêu đề là mặc định và là tin nhắn user đầu tiên -> tự động đặt tên theo câu hỏi
                if role == "user" and content and (current_title in ("Cuộc trò chuyện mới", "default", "Cuộc trò chuyện mặc định")):
                    new_title = content[:35].replace("\n", " ").strip()
                    cursor.execute(
                        "UPDATE chat_sessions SET title = ?, updated_at = ? WHERE id = ?",
                        (new_title, now_iso, session_id)
                    )
                else:
                    cursor.execute(
                        "UPDATE chat_sessions SET updated_at = ? WHERE id = ?",
                        (now_iso, session_id)
                    )

            # Thêm tin nhắn
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, content, has_image, tool_calls, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (session_id, role, content, 1 if has_image else 0, json.dumps(tool_calls or [], ensure_ascii=False), now_iso)
            )
            conn.commit()

    def get_chat_history(self, session_id: str = "default", limit: int = 100) -> List[Dict]:
        """Lấy lịch sử chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
            rows = [dict(row) for row in cursor.fetchall()]
            rows.reverse()  # Oldest first
            return rows

    def clear_chat_history(self, session_id: str = "default"):
        """Xoá lịch sử tin nhắn của một session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM chat_history WHERE session_id = ?", (session_id,))
            cursor.execute("UPDATE chat_sessions SET updated_at = ? WHERE id = ?", (datetime.now().isoformat(), session_id))
            conn.commit()

    def get_chat_sessions(self) -> List[str]:
        """Lấy danh sách các ID session chat."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM chat_sessions ORDER BY updated_at DESC")
            return [row["id"] for row in cursor.fetchall()]

    # ==================== Execution Logs ====================

    def log_execution(self, workflow_name: str, action_type: str, action_detail: str,
                      status: str = "SUCCESS", error_message: str = "", duration_ms: int = 0):
        """Ghi log thực thi."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO execution_logs (workflow_name, action_type, action_detail, status, error_message, duration_ms) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (workflow_name, action_type, action_detail, status, error_message, duration_ms)
            )
            conn.commit()

    def get_execution_logs(self, limit: int = 200, workflow_name: str = None) -> List[Dict]:
        """Lấy logs thực thi."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            if workflow_name:
                cursor.execute(
                    "SELECT * FROM execution_logs WHERE workflow_name = ? ORDER BY created_at DESC LIMIT ?",
                    (workflow_name, limit)
                )
            else:
                cursor.execute(
                    "SELECT * FROM execution_logs ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )
            return [dict(row) for row in cursor.fetchall()]

    def clear_execution_logs(self):
        """Xoá tất cả logs."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM execution_logs")
            conn.commit()

    # ==================== Statistics ====================

    def set_stat(self, key: str, value: str):
        """Lưu/cập nhật thống kê."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO app_stats (stat_key, stat_value, updated_at) VALUES (?, ?, ?)",
                (key, value, datetime.now().isoformat())
            )
            conn.commit()

    def get_stat(self, key: str, default: str = "0") -> str:
        """Lấy thống kê."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stat_value FROM app_stats WHERE stat_key = ?", (key,))
            row = cursor.fetchone()
            return row["stat_value"] if row else default

    def increment_stat(self, key: str, amount: int = 1):
        """Tăng giá trị thống kê."""
        current = int(self.get_stat(key, "0"))
        self.set_stat(key, str(current + amount))

    def get_all_stats(self) -> Dict[str, str]:
        """Lấy tất cả thống kê."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT stat_key, stat_value FROM app_stats")
            return {row["stat_key"]: row["stat_value"] for row in cursor.fetchall()}

    # ==================== Dashboard Stats ====================

    def get_dashboard_stats(self) -> Dict:
        """Lấy thống kê cho dashboard."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Tổng số lần chạy
            cursor.execute("SELECT COUNT(*) as cnt FROM execution_logs")
            total_runs = cursor.fetchone()["cnt"]

            # Số lần thành công
            cursor.execute("SELECT COUNT(*) as cnt FROM execution_logs WHERE status = 'SUCCESS'")
            success_runs = cursor.fetchone()["cnt"]

            # Tổng thời gian đã tiết kiệm (ước lượng: mỗi action trung bình 5s nếu làm thủ công)
            cursor.execute("SELECT COUNT(*) as cnt FROM execution_logs WHERE status = 'SUCCESS'")
            time_saved_seconds = cursor.fetchone()["cnt"] * 5

            # Số tin nhắn chat
            cursor.execute("SELECT COUNT(*) as cnt FROM chat_history")
            total_chats = cursor.fetchone()["cnt"]

            # Workflow count
            cursor.execute("SELECT COUNT(*) as cnt FROM workflows")
            total_workflows = cursor.fetchone()["cnt"]

            return {
                "total_runs": total_runs,
                "success_runs": success_runs,
                "success_rate": f"{(success_runs / total_runs * 100):.0f}%" if total_runs > 0 else "N/A",
                "time_saved": self._format_time(time_saved_seconds),
                "total_chats": total_chats,
                "total_workflows": total_workflows,
            }

    @staticmethod
    def _format_time(seconds: int) -> str:
        """Format thời gian đẹp."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            mins = (seconds % 3600) // 60
            return f"{hours}h {mins}m"

    # ==================== Application Settings ====================

    def set_app_setting(self, key: str, value: str):
        """Lưu hoặc cập nhật cài đặt ứng dụng."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO app_settings (setting_key, setting_value, updated_at) VALUES (?, ?, ?)",
                (key, str(value), datetime.now().isoformat())
            )
            conn.commit()

    def get_app_setting(self, key: str, default: str = "") -> str:
        """Lấy giá trị cài đặt ứng dụng."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM app_settings WHERE setting_key = ?", (key,))
            row = cursor.fetchone()
            return row["setting_value"] if row else default

    # ==================== Authentication & User Management ====================

    def is_auth_enabled(self) -> bool:
        """Kiểm tra xác thực đăng nhập có bật không (mặc định: False / 0)."""
        return self.get_app_setting("require_login", "0") == "1"

    def set_auth_enabled(self, enabled: bool):
        """Bật/tắt xác thực đăng nhập khi khởi động."""
        self.set_app_setting("require_login", "1" if enabled else "0")

    @staticmethod
    def hash_password(password: str, salt: str = None) -> tuple[str, str]:
        """Tạo mật khẩu băm kèm salt bảo mật."""
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
        return pwd_hash, salt

    @staticmethod
    def verify_password(password: str, expected_hash: str, salt: str) -> bool:
        """Xác thực mật khẩu với hash đã lưu."""
        pwd_hash = hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()
        return pwd_hash == expected_hash

    def log_login_attempt(self, username: str, status: str = "SUCCESS", device: str = "Local Desktop", message: str = ""):
        """Ghi nhật ký lần đăng nhập."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO login_logs (username, status, ip_or_device, message, login_time) VALUES (?, ?, ?, ?, ?)",
                    (username, status, device, message, datetime.now().isoformat())
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Lỗi ghi log đăng nhập: {e}")

    def authenticate_user(self, username: str, password: str, device: str = "Local Desktop") -> tuple[bool, str, Optional[Dict]]:
        """Xác thực đăng nhập tài khoản. Trả về (success, message, user_info)."""
        username = username.strip()
        if not username:
            return False, "Vui lòng nhập tên đăng nhập!", None

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (username,))
            row = cursor.fetchone()

            if not row:
                self.log_login_attempt(username, status="FAILED", device=device, message="Tài khoản không tồn tại")
                return False, "Tài khoản không tồn tại trong hệ thống!", None

            user = dict(row)
            if not user.get("is_active", 1):
                self.log_login_attempt(username, status="FAILED", device=device, message="Tài khoản bị vô hiệu hoá")
                return False, "Tài khoản này đã bị vô hiệu hoá!", None

            if not self.verify_password(password, user["password_hash"], user["salt"]):
                self.log_login_attempt(username, status="FAILED", device=device, message="Sai mật khẩu")
                return False, "Mật khẩu đăng nhập không chính xác!", None

            # Đăng nhập thành công -> Cập nhật thống kê
            now_iso = datetime.now().isoformat()
            cursor.execute(
                "UPDATE users SET login_count = login_count + 1, last_login_at = ?, updated_at = ? WHERE id = ?",
                (now_iso, now_iso, user["id"])
            )
            conn.commit()

            self.log_login_attempt(username, status="SUCCESS", device=device, message="Đăng nhập thành công")
            user["login_count"] = user.get("login_count", 0) + 1
            user["last_login_at"] = now_iso
            return True, "Đăng nhập thành công!", user

    def get_all_users(self) -> List[Dict]:
        """Lấy danh sách tất cả tài khoản người dùng."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, username, display_name, role, is_active, login_count,
                       last_login_at, created_at, updated_at
                FROM users
                ORDER BY id ASC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """Lấy thông tin tài khoản theo ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def create_user(self, username: str, password: str, display_name: str = "", role: str = "admin") -> tuple[bool, str]:
        """Tạo tài khoản mới."""
        username = username.strip()
        display_name = display_name.strip() or username
        if not username:
            return False, "Tên đăng nhập không được để trống!"
        if len(username) < 2:
            return False, "Tên đăng nhập phải có ít nhất 2 ký tự!"
        if len(password) < 1:
            return False, "Mật khẩu không được để trống!"

        pwd_hash, salt = self.hash_password(password)
        now_iso = datetime.now().isoformat()

        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO users (username, password_hash, salt, display_name, role, is_active, login_count, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, 1, 0, ?, ?)",
                    (username, pwd_hash, salt, display_name, role, now_iso, now_iso)
                )
                conn.commit()
                return True, f"Tạo tài khoản '{username}' thành công!"
        except sqlite3.IntegrityError:
            return False, f"Tài khoản '{username}' đã tồn tại!"
        except Exception as e:
            return False, f"Lỗi tạo tài khoản: {e}"

    def update_user(self, user_id: int, display_name: str = None, role: str = None, is_active: int = None) -> tuple[bool, str]:
        """Cập nhật thông tin tài khoản."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Không tìm thấy tài khoản!"

            updates = []
            params = []
            if display_name is not None:
                updates.append("display_name = ?")
                params.append(display_name.strip())
            if role is not None:
                updates.append("role = ?")
                params.append(role.strip())
            if is_active is not None:
                updates.append("is_active = ?")
                params.append(int(is_active))

            if not updates:
                return True, "Không có thay đổi nào."

            updates.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            params.append(user_id)

            sql = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(sql, tuple(params))
            conn.commit()
            return True, "Cập nhật tài khoản thành công!"

    def change_user_password(self, user_id: int, new_password: str) -> tuple[bool, str]:
        """Đổi mật khẩu cho tài khoản."""
        if len(new_password) < 1:
            return False, "Mật khẩu mới không được để trống!"

        pwd_hash, salt = self.hash_password(new_password)
        now_iso = datetime.now().isoformat()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET password_hash = ?, salt = ?, updated_at = ? WHERE id = ?",
                (pwd_hash, salt, now_iso, user_id)
            )
            if cursor.rowcount == 0:
                return False, "Không tìm thấy tài khoản!"
            conn.commit()
            return True, "Đổi mật khẩu thành công!"

    def delete_user(self, user_id: int) -> tuple[bool, str]:
        """Xoá tài khoản người dùng."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as cnt FROM users")
            total = cursor.fetchone()["cnt"]
            if total <= 1:
                return False, "Không thể xoá tài khoản cuối cùng trong hệ thống!"

            cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Không tìm thấy tài khoản!"
            uname = row["username"]

            cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
            conn.commit()
            return True, f"Đã xoá tài khoản '{uname}' thành công!"

    def get_login_logs(self, limit: int = 100) -> List[Dict]:
        """Lấy danh sách nhật ký đăng nhập."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM login_logs ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def clear_login_logs(self) -> bool:
        """Xoá toàn bộ nhật ký đăng nhập."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM login_logs")
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Lỗi xoá login logs: {e}")
            return False


