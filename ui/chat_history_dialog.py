"""
Chat History Dialog — Quản lý lịch sử các phiên trò chuyện.
Cho phép xem danh sách, mở lại, đổi tên, tạo mới và xoá lịch sử chat.
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QWidget, QFrame, QMessageBox,
    QInputDialog, QApplication, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from ui.theme import COLORS, apply_titlebar_theme
from ui.toast import toast_success, toast_info, toast_warning

logger = logging.getLogger(__name__)


class SessionCard(QFrame):
    """Card hiển thị 1 phiên trò chuyện."""

    open_requested = pyqtSignal(str)
    rename_requested = pyqtSignal(str, str)
    delete_requested = pyqtSignal(str)

    def __init__(self, session_data: dict, is_current: bool = False, parent=None):
        super().__init__(parent)
        self.session_data = session_data
        self.session_id = session_data.get("id", "")
        self.title = session_data.get("title", "Cuộc trò chuyện")
        self.is_current = is_current

        self._setup_ui()

    def _setup_ui(self):
        self.setObjectName("sessionCard")
        border_color = COLORS['accent_primary'] if self.is_current else COLORS['border']
        bg_color = f"{COLORS['accent_primary']}10" if self.is_current else COLORS['bg_surface']

        self.setStyleSheet(f"""
            QFrame#sessionCard {{
                background-color: {bg_color};
                border: 1.5px solid {border_color};
                border-radius: 10px;
                padding: 10px 14px;
            }}
            QFrame#sessionCard:hover {{
                background-color: {COLORS['bg_surface_hover']};
                border-color: {COLORS['accent_primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # Top row: Title + Badges
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Icon + Title
        title_lbl = QLabel(f"💬 {self.title}")
        title_lbl.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold if self.is_current else QFont.Weight.DemiBold))
        title_lbl.setStyleSheet(f"color: {COLORS['accent_primary'] if self.is_current else COLORS['text_primary']}; border: none; background: transparent;")
        title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        top_row.addWidget(title_lbl, 1)

        # Current active badge
        if self.is_current:
            active_badge = QLabel("Đang mở")
            active_badge.setStyleSheet(f"""
                background-color: {COLORS['accent_primary']};
                color: #ffffff;
                border-radius: 6px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 600;
                border: none;
            """)
            top_row.addWidget(active_badge)

        # Message count badge
        msg_count = self.session_data.get("msg_count", 0)
        count_badge = QLabel(f"📊 {msg_count} tin")
        count_badge.setStyleSheet(f"""
            background-color: {COLORS['bg_elevated']};
            color: {COLORS['text_secondary']};
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            border: none;
        """)
        top_row.addWidget(count_badge)

        layout.addLayout(top_row)

        # Middle row: Last message preview + Timestamp
        mid_row = QHBoxLayout()
        mid_row.setSpacing(8)

        last_msg = self.session_data.get("last_message", "")
        if last_msg:
            # Clean preview
            preview = last_msg.replace("\n", " ")[:90]
            if len(last_msg) > 90:
                preview += "..."
        else:
            preview = "(Chưa có tin nhắn nào)"

        preview_lbl = QLabel(preview)
        preview_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-style: italic; border: none; background: transparent;")
        preview_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        mid_row.addWidget(preview_lbl, 1)

        # Time
        raw_time = self.session_data.get("updated_at", "") or self.session_data.get("created_at", "")
        formatted_time = ""
        if raw_time:
            try:
                # Handle ISO format or SQLite timestamp
                clean_time = raw_time.replace("T", " ")[:19]
                dt = datetime.strptime(clean_time, "%Y-%m-%d %H:%M:%S")
                formatted_time = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                formatted_time = raw_time[:16]

        if formatted_time:
            time_lbl = QLabel(f"🕒 {formatted_time}")
            time_lbl.setStyleSheet(f"color: {COLORS['text_disabled']}; font-size: 11px; border: none; background: transparent;")
            mid_row.addWidget(time_lbl)

        layout.addLayout(mid_row)

        # Bottom row: Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        btn_row.addStretch()

        # Open button
        open_btn = QPushButton("🚀 Mở đoạn chat" if not self.is_current else "👁️ Xem đoạn chat")
        open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_btn.setFixedHeight(30)
        open_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 600;
                padding: 4px 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_primary_hover']};
            }}
        """)
        open_btn.clicked.connect(lambda: self.open_requested.emit(self.session_id))
        btn_row.addWidget(open_btn)

        # Rename button
        rename_btn = QPushButton("✏️ Đổi tên")
        rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rename_btn.setFixedHeight(30)
        rename_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 12px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_surface_hover']};
                border-color: {COLORS['accent_primary']};
            }}
        """)
        rename_btn.clicked.connect(self._on_rename_clicked)
        btn_row.addWidget(rename_btn)

        # Delete button
        del_btn = QPushButton("🗑️ Xoá")
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setFixedHeight(30)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error_bg']};
                color: {COLORS['error']};
                border: 1px solid {COLORS['error']}44;
                border-radius: 6px;
                font-size: 12px;
                padding: 4px 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: #ffffff;
            }}
        """)
        del_btn.clicked.connect(self._on_delete_clicked)
        btn_row.addWidget(del_btn)

        layout.addLayout(btn_row)

    def _on_rename_clicked(self):
        new_title, ok = QInputDialog.getText(
            self, "✏️ Đổi tên cuộc trò chuyện",
            "Nhập tên mới cho cuộc trò chuyện này:",
            QLineEdit.EchoMode.Normal,
            self.title
        )
        if ok and new_title.strip():
            self.rename_requested.emit(self.session_id, new_title.strip())

    def _on_delete_clicked(self):
        reply = QMessageBox.question(
            self,
            "🗑️ Xác nhận xoá",
            f"Bạn có chắc muốn xoá cuộc trò chuyện:\n\n💬 \"{self.title}\"\n\nToàn bộ tin nhắn trong phiên này sẽ bị xoá vĩnh viễn.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_requested.emit(self.session_id)


class ChatHistoryDialog(QDialog):
    """Dialog quản lý toàn bộ lịch sử các phiên trò chuyện."""

    session_selected = pyqtSignal(str)   # session_id
    new_chat_requested = pyqtSignal()    # Tạo phiên mới
    history_cleared = pyqtSignal()       # Đã xoá toàn bộ

    def __init__(self, state_manager, current_session_id: str = "default", parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.current_session_id = current_session_id

        self.setWindowTitle("📜 Lịch sử Cuộc trò chuyện — AI Claw")
        self.setMinimumSize(720, 560)
        self.resize(780, 620)
        self.setSizeGripEnabled(True)

        self._setup_ui()
        self._load_sessions()

    def showEvent(self, event):
        super().showEvent(event)
        apply_titlebar_theme(self)

    def _setup_ui(self):
        self.setStyleSheet(f"QDialog {{ background-color: {COLORS['bg_primary']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(14)

        # === Header Bar ===
        header_bar = QFrame()
        header_bar.setObjectName("dialogHeader")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(12, 10, 12, 10)

        title = QLabel("📜 Lịch sử các Cuộc trò chuyện")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Nút tạo mới ngay tại header
        new_btn = QPushButton("➕ Cuộc trò chuyện mới")
        new_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_btn.setFixedHeight(36)
        new_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_primary_hover']};
            }}
        """)
        new_btn.clicked.connect(self._on_new_chat)
        header_layout.addWidget(new_btn)

        layout.addWidget(header_bar)

        # === Search Bar ===
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm theo tên cuộc trò chuyện hoặc nội dung tin nhắn...")
        self._search_input.setFixedHeight(38)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 0 14px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self._filter_sessions)
        self._search_input.textChanged.connect(lambda: self._search_timer.start())
        search_row.addWidget(self._search_input, 1)

        clear_search_btn = QPushButton("✕")
        clear_search_btn.setFixedSize(38, 38)
        clear_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_search_btn.setToolTip("Xoá tìm kiếm")
        clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_surface_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        clear_search_btn.clicked.connect(lambda: self._search_input.clear())
        search_row.addWidget(clear_search_btn)

        layout.addLayout(search_row)

        # === Scroll Area of Sessions ===
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 8, 0)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch()

        self._scroll.setWidget(self._cards_container)
        layout.addWidget(self._scroll, 1)

        # === Bottom Actions Bar ===
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(10)

        self._stats_lbl = QLabel("Đang tải danh sách...")
        self._stats_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px;")
        bottom_row.addWidget(self._stats_lbl)

        bottom_row.addStretch()

        # Clear all button
        clear_all_btn = QPushButton("🗑️ Xoá tất cả lịch sử")
        clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_all_btn.setFixedHeight(36)
        clear_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error_bg']};
                color: {COLORS['error']};
                border: 1px solid {COLORS['error']}44;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
                padding: 6px 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: #ffffff;
            }}
        """)
        clear_all_btn.clicked.connect(self._on_clear_all)
        bottom_row.addWidget(clear_all_btn)

        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setFixedSize(90, 36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_surface_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        bottom_row.addWidget(close_btn)

        layout.addLayout(bottom_row)

    def _load_sessions(self):
        """Tải và hiển thị danh sách tất cả các phiên chat."""
        try:
            self._all_sessions = self.state_manager.get_all_chat_sessions()
        except Exception as e:
            logger.error(f"[ChatHistoryDialog] Lỗi tải sessions: {e}")
            self._all_sessions = []

        self._filter_sessions()

    def _filter_sessions(self):
        """Lọc và render danh sách card phiên chat."""
        query = self._search_input.text().strip().lower()

        # Clear layout (giữ lại stretch item ở cuối)
        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = []
        for s in self._all_sessions:
            title = s.get("title", "").lower()
            last_msg = (s.get("last_message", "") or "").lower()
            if not query or query in title or query in last_msg:
                filtered.append(s)

        if not filtered:
            empty_lbl = QLabel(
                "🔍 Không tìm thấy cuộc trò chuyện nào phù hợp." if query
                else "📭 Chưa có lịch sử trò chuyện nào. Hãy bắt đầu cuộc trò chuyện mới!"
            )
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 13px; padding: 40px 0;")
            self._cards_layout.insertWidget(0, empty_lbl)
            self._stats_lbl.setText("Tổng cộng: 0 cuộc trò chuyện")
            return

        for s in filtered:
            is_current = (s.get("id") == self.current_session_id)
            card = SessionCard(s, is_current=is_current)
            card.open_requested.connect(self._on_open_session)
            card.rename_requested.connect(self._on_rename_session)
            card.delete_requested.connect(self._on_delete_session)

            count = self._cards_layout.count()
            self._cards_layout.insertWidget(count - 1, card)

        self._stats_lbl.setText(f"Hiển thị {len(filtered)} / {len(self._all_sessions)} cuộc trò chuyện")

    def _on_open_session(self, session_id: str):
        """Mở phiên chat được chọn."""
        self.session_selected.emit(session_id)
        self.accept()

    def _on_rename_session(self, session_id: str, new_title: str):
        """Xử lý đổi tên phiên chat."""
        try:
            self.state_manager.rename_chat_session(session_id, new_title)
            toast_success(f"Đã đổi tên thành: \"{new_title}\"", self)
            self._load_sessions()
        except Exception as e:
            logger.error(f"[ChatHistoryDialog] Lỗi đổi tên: {e}")
            toast_warning(f"Lỗi đổi tên: {e}", self)

    def _on_delete_session(self, session_id: str):
        """Xoá 1 phiên chat."""
        try:
            self.state_manager.delete_chat_session(session_id)
            toast_info("Đã xoá cuộc trò chuyện thành công", self)
            # Nếu xoá đúng phiên hiện tại -> phát tín hiệu tạo mới
            if session_id == self.current_session_id:
                self.new_chat_requested.emit()
            self._load_sessions()
        except Exception as e:
            logger.error(f"[ChatHistoryDialog] Lỗi xoá session: {e}")
            toast_warning(f"Lỗi xoá cuộc trò chuyện: {e}", self)

    def _on_new_chat(self):
        """Tạo cuộc trò chuyện mới."""
        self.new_chat_requested.emit()
        self.accept()

    def _on_clear_all(self):
        """Xoá toàn bộ lịch sử chat."""
        reply = QMessageBox.question(
            self,
            "⚠️ Cảnh báo xoá toàn bộ",
            "Bạn có chắc chắn muốn XOÁ TOÀN BỘ tất cả các cuộc trò chuyện?\n\nHành động này không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.state_manager.clear_all_chat_sessions()
                toast_info("Đã xoá toàn bộ lịch sử trò chuyện", self)
                self.history_cleared.emit()
                self._load_sessions()
            except Exception as e:
                logger.error(f"[ChatHistoryDialog] Lỗi xoá toàn bộ: {e}")
                toast_warning(f"Lỗi xoá: {e}", self)
