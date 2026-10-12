"""
Log Viewer — Xem nhật ký thực thi & Console log realtime.
Hỗ trợ:
- Tab 1: Nhật Ký Hoạt Động (Execution logs từ database)
- Tab 2: Console Log Realtime (Bật/Tắt toggle, Xoá lịch sử, Copy log)
"""

import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QComboBox,
    QLineEdit, QFrame, QMessageBox, QTabWidget, QPlainTextEdit,
    QCheckBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QObject, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QTextCursor

from ui.theme import COLORS
from ui.toast import toast_success, toast_info

logger = logging.getLogger(__name__)


class QtLogEmitter(QObject):
    """Emitter phát Qt Signal khi có log mới."""
    log_record = pyqtSignal(str)


class QtLogHandler(logging.Handler):
    """Logging handler chuyển record sang Qt signal."""

    def __init__(self, emitter: QtLogEmitter):
        super().__init__()
        self.emitter = emitter
        self.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"))

    def emit(self, record):
        try:
            msg = self.format(record)
            self.emitter.log_record.emit(msg)
        except Exception:
            pass


# Global emitter & handler instance
_global_log_emitter = QtLogEmitter()
_global_log_handler = QtLogHandler(_global_log_emitter)
logging.getLogger().addHandler(_global_log_handler)


class LogViewer(QWidget):
    """Widget xem nhật ký thực thi & Console Log."""

    def __init__(self, state_manager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self._console_enabled = False
        if self.state_manager:
            saved_setting = self.state_manager.get_app_setting("enable_console_log", "false")
            self._console_enabled = (saved_setting.lower() == "true")

        self._setup_ui()
        self._load_logs()

        # Kết nối log stream
        _global_log_emitter.log_record.connect(self._on_log_received)

        # Auto refresh execution logs mỗi 10s
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._load_logs)
        self._timer.start(10000)

    def refresh_theme(self):
        """Cập nhật theme cho LogViewer."""
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        if hasattr(self, '_header'):
            self._header.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-bottom: 1px solid {COLORS['border']};")
        if hasattr(self, '_content'):
            self._content.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        if hasattr(self, '_table'):
            self._table.setStyleSheet(f"QTableWidget {{ background-color: {COLORS['bg_surface']}; color: {COLORS['text_primary']}; gridline-color: {COLORS['border']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
        self._load_logs()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = QFrame()
        self._header.setFixedHeight(60)
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("📋 Activity & Console Logs — Nhật Ký Hoạt Động & Hệ Thống")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        header_layout.addWidget(title)

        header_layout.addStretch()
        layout.addWidget(self._header)

        # Content container with Tabs
        self._content = QWidget()
        self._content.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        content_layout = QVBoxLayout(self._content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(10)

        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_activity_logs_tab(), "📋 Nhật Ký Hoạt Động")
        self._tabs.addTab(self._create_console_logs_tab(), "🖥️ Console Log (Terminal)")
        content_layout.addWidget(self._tabs)

        layout.addWidget(self._content, 1)

    def _create_activity_logs_tab(self) -> QWidget:
        """Tab 1: Bảng nhật ký hoạt động (Execution Logs)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)

        filter_lbl = QLabel("Lọc trạng thái:")
        filter_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 500;")
        toolbar.addWidget(filter_lbl)

        self._filter_combo = QComboBox()
        self._filter_combo.addItems(["Tất cả", "SUCCESS", "ERROR", "WARNING"])
        self._filter_combo.setFixedWidth(130)
        self._filter_combo.currentIndexChanged.connect(self._load_logs)
        toolbar.addWidget(self._filter_combo)

        toolbar.addStretch()

        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setFixedHeight(32)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: {COLORS['bg_surface_hover']};
            }}
        """)
        refresh_btn.clicked.connect(self._load_logs)
        toolbar.addWidget(refresh_btn)

        clear_btn = QPushButton("🗑️ Xoá tất cả Logs")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setFixedHeight(32)
        clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['error']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: #ffffff;
                border-color: {COLORS['error']};
            }}
        """)
        clear_btn.clicked.connect(self._clear_logs)
        toolbar.addWidget(clear_btn)

        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["Thời gian", "Workflow", "Hành động", "Chi tiết", "Trạng thái", "Thời lượng"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(0, 140)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(1, 130)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(2, 130)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(4, 90)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(5, 90)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setStyleSheet(f"QTableWidget {{ background-color: {COLORS['bg_surface']}; color: {COLORS['text_primary']}; gridline-color: {COLORS['border']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")

        layout.addWidget(self._table, 1)

        # Stats bar
        self._stats_label = QLabel("Tổng: 0 logs")
        self._stats_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self._stats_label)

        return tab

    def _create_console_logs_tab(self) -> QWidget:
        """Tab 2: Console Log Realtime (Bật/Tắt, Xoá lịch sử)."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        # Toggle Bật/Tắt (mặc định TẮT)
        self._console_toggle = QCheckBox("🔘 Bật ghi Console Log")
        self._console_toggle.setChecked(self._console_enabled)
        self._console_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self._console_toggle.setStyleSheet(f"""
            QCheckBox {{
                color: {COLORS['text_primary']};
                font-size: 13px;
                font-weight: 600;
            }}
            QCheckBox::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid {COLORS['border']};
            }}
            QCheckBox::indicator:checked {{
                background-color: {COLORS['accent_primary']};
                border-color: {COLORS['accent_primary']};
            }}
        """)
        self._console_toggle.toggled.connect(self._on_console_toggle_changed)
        toolbar.addWidget(self._console_toggle)

        self._auto_scroll_chk = QCheckBox("Tự động cuộn")
        self._auto_scroll_chk.setChecked(True)
        self._auto_scroll_chk.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
        toolbar.addWidget(self._auto_scroll_chk)

        toolbar.addStretch()

        copy_btn = QPushButton("📋 Copy Console")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setFixedHeight(32)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: {COLORS['bg_surface_hover']};
            }}
        """)
        copy_btn.clicked.connect(self._copy_console_logs)
        toolbar.addWidget(copy_btn)

        clear_console_btn = QPushButton("🗑️ Xoá lịch sử Console")
        clear_console_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_console_btn.setFixedHeight(32)
        clear_console_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['error']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 14px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: #ffffff;
                border-color: {COLORS['error']};
            }}
        """)
        clear_console_btn.clicked.connect(self._clear_console_logs)
        toolbar.addWidget(clear_console_btn)

        layout.addLayout(toolbar)

        # Terminal Output Box
        self._console_text = QPlainTextEdit()
        self._console_text.setReadOnly(True)
        self._console_text.setMaximumBlockCount(2500)
        self._console_text.setFont(QFont("Consolas", 10))
        self._console_text.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: #0b0f19;
                color: #38bdf8;
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px;
                line-height: 1.4;
            }}
        """)

        initial_msg = (
            "[HỆ THỐNG CONSOLE LOG]\n"
            f"- Trạng thái: {'ĐANG BẬT' if self._console_enabled else 'ĐANG TẮT (Mặc định)'}\n"
            "- Hướng dẫn: Đánh dấu chọn '🔘 Bật ghi Console Log' ở trên để theo dõi toàn bộ log realtime từ ứng dụng.\n"
            f"{'=' * 75}\n"
        )
        self._console_text.setPlainText(initial_msg)
        layout.addWidget(self._console_text, 1)

        # Status footer
        self._console_status_lbl = QLabel(
            f"Trạng thái: {'🟢 Đang ghi log realtime' if self._console_enabled else '⚪ Đang TẮT (Tiết kiệm tài nguyên CPU/RAM)'}"
        )
        self._console_status_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self._console_status_lbl)

        return tab

    def _on_console_toggle_changed(self, checked: bool):
        """Xử lý bật / tắt console log."""
        self._console_enabled = checked
        if self.state_manager:
            self.state_manager.set_app_setting("enable_console_log", "true" if checked else "false")

        status_text = "🟢 Đang ghi log realtime" if checked else "⚪ Đang TẮT (Tiết kiệm tài nguyên CPU/RAM)"
        self._console_status_lbl.setText(f"Trạng thái: {status_text}")

        if checked:
            toast_info("🖥️ Đã BẬT ghi nhận Console Log realtime", self)
            self._console_text.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] >>> CONSOLE LOG ĐÃ ĐƯỢC BẬT <<<")
        else:
            toast_info("🖥️ Đã TẮT ghi nhận Console Log", self)
            self._console_text.appendPlainText(f"[{datetime.now().strftime('%H:%M:%S')}] >>> CONSOLE LOG ĐÃ ĐƯỢC TẮT <<<")

    def _on_log_received(self, log_line: str):
        """Nhận log mới và append vào console text edit."""
        if not self._console_enabled or not hasattr(self, '_console_text'):
            return

        self._console_text.appendPlainText(log_line)
        if hasattr(self, '_auto_scroll_chk') and self._auto_scroll_chk.isChecked():
            self._console_text.moveCursor(QTextCursor.MoveOperation.End)

    def _clear_console_logs(self):
        """Xoá sạch màn hình console log."""
        self._console_text.clear()
        self._console_text.setPlainText(
            f"[CONSOLE ĐÃ ĐƯỢC XOÁ SẠCH LÚC {datetime.now().strftime('%H:%M:%S')}]\n{'=' * 75}\n"
        )
        toast_success("🗑️ Đã xoá lịch sử Console Log thành công.", self)

    def _copy_console_logs(self):
        """Copy toàn bộ console logs vào clipboard."""
        text = self._console_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            toast_success("📋 Đã copy toàn bộ Console Log vào Clipboard!", self)

    def _load_logs(self):
        """Load logs từ database."""
        if not hasattr(self, '_table'):
            return

        filter_status = self._filter_combo.currentText()
        logs = self.state_manager.get_execution_logs(limit=500)

        if filter_status != "Tất cả":
            logs = [l for l in logs if l.get("status") == filter_status]

        self._table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            # Thời gian
            created = log.get("created_at", "")
            self._table.setItem(row, 0, QTableWidgetItem(created[:19] if created else ""))

            # Workflow
            self._table.setItem(row, 1, QTableWidgetItem(log.get("workflow_name", "")))

            # Hành động
            self._table.setItem(row, 2, QTableWidgetItem(log.get("action_type", "")))

            # Chi tiết
            self._table.setItem(row, 3, QTableWidgetItem(log.get("action_detail", "")))

            # Trạng thái
            status = log.get("status", "")
            status_item = QTableWidgetItem(status)
            color_map = {
                "SUCCESS": COLORS["success"],
                "ERROR": COLORS["error"],
                "WARNING": COLORS["warning"],
            }
            status_item.setForeground(QColor(color_map.get(status, COLORS["text_muted"])))
            self._table.setItem(row, 4, status_item)

            # Thời lượng
            duration = log.get("duration_ms", 0)
            self._table.setItem(row, 5, QTableWidgetItem(f"{duration}ms" if duration else ""))

        self._stats_label.setText(f"Tổng: {len(logs)} logs")

    def _clear_logs(self):
        """Xoá tất cả execution logs."""
        reply = QMessageBox.question(
            self, "Xoá logs",
            "Bạn có chắc muốn xoá tất cả nhật ký hoạt động?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.state_manager.clear_execution_logs()
            self._load_logs()
            toast_success("🗑️ Đã xoá toàn bộ Activity Logs!", self)
