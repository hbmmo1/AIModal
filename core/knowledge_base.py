"""
Knowledge Base — Trí tuệ cá nhân / Cơ sở kiến thức riêng.
Cho phép người dùng nhập:
- Hỏi & Đáp (Q&A) cá nhân
- Kiến thức chuyên môn
- Nhận thức / Insight cá nhân
- Thông tin cá nhân (sở thích, công việc, mục tiêu)
AI sẽ sử dụng những kiến thức này để trả lời thông minh hơn.
"""

import os
import json
import sqlite3
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "config", "app_data.db")


# ============================================================
# Knowledge Categories
# ============================================================

KNOWLEDGE_CATEGORIES = {
    "personal_info": {
        "icon": "👤",
        "name": "Thông tin cá nhân",
        "description": "Tên, tuổi, nghề nghiệp, sở thích, mục tiêu...",
        "color": "#3b82f6",
    },
    "qa": {
        "icon": "❓",
        "name": "Hỏi & Đáp (Q&A)",
        "description": "Câu hỏi → câu trả lời đúng, AI sẽ học và nhớ",
        "color": "#22c55e",
    },
    "expertise": {
        "icon": "🎓",
        "name": "Kiến thức chuyên môn",
        "description": "Kiến thức lĩnh vực, chuyên ngành, kỹ năng",
        "color": "#8b5cf6",
    },
    "insight": {
        "icon": "💡",
        "name": "Nhận thức & Insight",
        "description": "Bài học kinh nghiệm, quan điểm, nguyên tắc sống",
        "color": "#f59e0b",
    },
    "instruction": {
        "icon": "📋",
        "name": "Hướng dẫn & Quy tắc",
        "description": "Cách AI nên trả lời, phong cách, quy tắc riêng",
        "color": "#06b6d4",
    },
    "reference": {
        "icon": "📚",
        "name": "Tài liệu tham khảo",
        "description": "Ghi chú, trích dẫn, thông tin tham khảo",
        "color": "#ec4899",
    },
}


@dataclass
class KnowledgeEntry:
    """1 mục kiến thức."""
    id: int = 0
    category: str = "qa"
    title: str = ""
    question: str = ""          # Câu hỏi (nếu là Q&A)
    answer: str = ""            # Câu trả lời / Nội dung kiến thức
    tags: str = ""              # Tags phân loại (comma-separated)
    priority: int = 5           # 1-10, 10 = quan trọng nhất
    enabled: bool = True
    usage_count: int = 0        # Số lần AI sử dụng
    created_at: str = ""
    updated_at: str = ""


class KnowledgeBase:
    """
    Quản lý cơ sở kiến thức cá nhân.
    SQLite-backed, tìm kiếm nhanh, tích hợp AI context.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Khởi tạo bảng knowledge_base."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT DEFAULT 'qa',
                    title TEXT DEFAULT '',
                    question TEXT DEFAULT '',
                    answer TEXT DEFAULT '',
                    tags TEXT DEFAULT '',
                    priority INTEGER DEFAULT 5,
                    enabled INTEGER DEFAULT 1,
                    usage_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # FTS (Full-Text Search) table
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                    title, question, answer, tags,
                    content='knowledge_base',
                    content_rowid='id'
                )
            """)
            conn.commit()

    # ============================================================
    # CRUD Operations
    # ============================================================

    def add_entry(self, category: str, title: str = "", question: str = "",
                  answer: str = "", tags: str = "", priority: int = 5) -> int:
        """Thêm 1 mục kiến thức. Trả về ID."""
        now = datetime.now().isoformat()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO knowledge_base (category, title, question, answer, tags, priority, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (category, title, question, answer, tags, priority, now, now))
            entry_id = cursor.lastrowid

            # Update FTS
            cursor.execute("""
                INSERT INTO knowledge_fts (rowid, title, question, answer, tags)
                VALUES (?, ?, ?, ?, ?)
            """, (entry_id, title, question, answer, tags))

            conn.commit()
            logger.info(f"[KnowledgeBase] Đã thêm: [{category}] {title or question[:50]}")
            return entry_id

    def update_entry(self, entry_id: int, **kwargs) -> bool:
        """Cập nhật 1 mục kiến thức."""
        allowed_fields = {"category", "title", "question", "answer", "tags", "priority", "enabled"}
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False

        updates["updated_at"] = datetime.now().isoformat()
        set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [entry_id]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE knowledge_base SET {set_clause} WHERE id = ?", values)

            # Update FTS
            cursor.execute("DELETE FROM knowledge_fts WHERE rowid = ?", (entry_id,))
            cursor.execute("SELECT title, question, answer, tags FROM knowledge_base WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            if row:
                cursor.execute("""
                    INSERT INTO knowledge_fts (rowid, title, question, answer, tags)
                    VALUES (?, ?, ?, ?, ?)
                """, (entry_id, row["title"], row["question"], row["answer"], row["tags"]))

            conn.commit()
            return cursor.rowcount > 0

    def delete_entry(self, entry_id: int) -> bool:
        """Xoá 1 mục kiến thức."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_fts WHERE rowid = ?", (entry_id,))
            cursor.execute("DELETE FROM knowledge_base WHERE id = ?", (entry_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_entry(self, entry_id: int) -> Optional[Dict]:
        """Lấy 1 mục theo ID."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM knowledge_base WHERE id = ?", (entry_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_all_entries(self, category: str = None, enabled_only: bool = False) -> List[Dict]:
        """Lấy tất cả kiến thức, tuỳ chọn filter."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM knowledge_base WHERE 1=1"
            params = []
            if category:
                query += " AND category = ?"
                params.append(category)
            if enabled_only:
                query += " AND enabled = 1"
            query += " ORDER BY priority DESC, updated_at DESC"
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def search(self, query: str, limit: int = 20) -> List[Dict]:
        """Tìm kiếm kiến thức (Full-Text Search)."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # FTS search
            try:
                cursor.execute("""
                    SELECT kb.* FROM knowledge_base kb
                    JOIN knowledge_fts fts ON kb.id = fts.rowid
                    WHERE knowledge_fts MATCH ?
                    AND kb.enabled = 1
                    ORDER BY rank, kb.priority DESC
                    LIMIT ?
                """, (query, limit))
                results = [dict(row) for row in cursor.fetchall()]
                if results:
                    return results
            except Exception:
                pass

            # Fallback: LIKE search
            search_term = f"%{query}%"
            cursor.execute("""
                SELECT * FROM knowledge_base
                WHERE enabled = 1
                AND (title LIKE ? OR question LIKE ? OR answer LIKE ? OR tags LIKE ?)
                ORDER BY priority DESC
                LIMIT ?
            """, (search_term, search_term, search_term, search_term, limit))
            return [dict(row) for row in cursor.fetchall()]

    # ============================================================
    # AI Context Generation
    # ============================================================

    def build_ai_context(self, user_message: str = "", max_entries: int = 30) -> str:
        """
        Xây dựng context kiến thức cá nhân cho AI.
        Gồm: thông tin cá nhân + kiến thức relevant + Q&A liên quan.
        """
        sections = []

        # 1. Thông tin cá nhân (luôn include)
        personal = self.get_all_entries(category="personal_info", enabled_only=True)
        if personal:
            items = []
            for entry in personal[:10]:
                if entry["question"] and entry["answer"]:
                    items.append(f"- {entry['question']}: {entry['answer']}")
                elif entry["answer"]:
                    items.append(f"- {entry['title'] or 'Info'}: {entry['answer']}")
            if items:
                sections.append("## THÔNG TIN CÁ NHÂN CỦA NGƯỜI DÙNG:\n" + "\n".join(items))

        # 2. Hướng dẫn & Quy tắc (luôn include)
        instructions = self.get_all_entries(category="instruction", enabled_only=True)
        if instructions:
            items = []
            for entry in instructions[:10]:
                content = entry["answer"] or entry["question"]
                if content:
                    items.append(f"- {entry['title'] or ''}: {content}")
            if items:
                sections.append("## QUY TẮC PHẢI TUÂN THỦ:\n" + "\n".join(items))

        # 3. Kiến thức liên quan (search theo user message)
        if user_message:
            relevant = self.search(user_message, limit=10)
            if relevant:
                items = []
                for entry in relevant:
                    cat_info = KNOWLEDGE_CATEGORIES.get(entry["category"], {})
                    cat_icon = cat_info.get("icon", "📝")

                    if entry["question"] and entry["answer"]:
                        items.append(f"{cat_icon} Q: {entry['question']}\n   A: {entry['answer']}")
                    elif entry["answer"]:
                        items.append(f"{cat_icon} {entry['title']}: {entry['answer']}")

                    # Tăng usage count
                    self._increment_usage(entry["id"])

                if items:
                    sections.append("## KIẾN THỨC CÁ NHÂN LIÊN QUAN:\n" + "\n".join(items))

        # 4. Top kiến thức ưu tiên (priority cao)
        remaining = max_entries - sum(len(s.split("\n")) for s in sections)
        if remaining > 5:
            top = self.get_all_entries(enabled_only=True)
            top_entries = [e for e in top if e["priority"] >= 8][:remaining]
            if top_entries:
                items = []
                for entry in top_entries:
                    if entry["answer"]:
                        items.append(f"- [{entry['title'] or entry['category']}] {entry['answer'][:150]}")
                if items:
                    sections.append("## KIẾN THỨC QUAN TRỌNG:\n" + "\n".join(items))

        if not sections:
            return ""

        return (
            "\n\n--- BẮT ĐẦU KIẾN THỨC CÁ NHÂN ---\n"
            "Dưới đây là kiến thức, thông tin, nhận thức cá nhân của người dùng. "
            "Hãy sử dụng những thông tin này để trả lời phù hợp và cá nhân hoá hơn.\n\n"
            + "\n\n".join(sections)
            + "\n--- KẾT THÚC KIẾN THỨC CÁ NHÂN ---\n"
        )

    def _increment_usage(self, entry_id: int):
        """Tăng usage count."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE knowledge_base SET usage_count = usage_count + 1 WHERE id = ?",
                    (entry_id,)
                )
                conn.commit()
        except Exception:
            pass

    # ============================================================
    # Statistics
    # ============================================================

    def get_stats(self) -> Dict:
        """Thống kê knowledge base."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as total FROM knowledge_base")
            total = cursor.fetchone()["total"]

            cursor.execute("SELECT COUNT(*) as active FROM knowledge_base WHERE enabled = 1")
            active = cursor.fetchone()["active"]

            cursor.execute("SELECT SUM(usage_count) as total_usage FROM knowledge_base")
            row = cursor.fetchone()
            total_usage = row["total_usage"] or 0

            # Count per category
            cursor.execute("""
                SELECT category, COUNT(*) as cnt FROM knowledge_base
                GROUP BY category ORDER BY cnt DESC
            """)
            by_category = {row["category"]: row["cnt"] for row in cursor.fetchall()}

            return {
                "total": total,
                "active": active,
                "total_usage": total_usage,
                "by_category": by_category,
            }

    def clear_all(self):
        """Xoá toàn bộ kiến thức."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM knowledge_fts")
            cursor.execute("DELETE FROM knowledge_base")
            conn.commit()
            logger.info("[KnowledgeBase] Đã xoá toàn bộ kiến thức")

    # ============================================================
    # Import / Export
    # ============================================================

    def export_to_json(self, filepath: str):
        """Xuất kiến thức ra file JSON."""
        entries = self.get_all_entries()
        data = {"version": "1.0", "entries": entries, "exported_at": datetime.now().isoformat()}
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"[KnowledgeBase] Đã xuất {len(entries)} mục → {filepath}")

    def import_from_json(self, filepath: str) -> int:
        """Nhập kiến thức từ file JSON. Trả về số mục đã thêm."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        count = 0
        for entry in data.get("entries", []):
            self.add_entry(
                category=entry.get("category", "qa"),
                title=entry.get("title", ""),
                question=entry.get("question", ""),
                answer=entry.get("answer", ""),
                tags=entry.get("tags", ""),
                priority=entry.get("priority", 5),
            )
            count += 1

        logger.info(f"[KnowledgeBase] Đã nhập {count} mục từ {filepath}")
        return count
