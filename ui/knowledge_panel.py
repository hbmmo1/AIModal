"""
Knowledge Panel — Giao diện quản lý Trí tuệ / Kiến thức cá nhân.
Thêm, sửa, xoá, tìm kiếm, import/export Q&A và kiến thức.
"""

import os
import logging
from datetime import datetime

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QLineEdit, QComboBox, QGroupBox, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox,
    QTabWidget, QSplitter, QMessageBox, QFileDialog,
    QSizePolicy, QScrollArea, QGridLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.theme import COLORS, get_card_style
from core.knowledge_base import KnowledgeBase, KNOWLEDGE_CATEGORIES
from ui.toast import toast_success, toast_error, toast_warning, toast_info

logger = logging.getLogger(__name__)


class KnowledgePanel(QWidget):
    """Panel quản lý kiến thức cá nhân."""

    knowledge_updated = pyqtSignal()

    def __init__(self, knowledge_base: KnowledgeBase, parent=None):
        super().__init__(parent)
        self.kb = knowledge_base
        self._editing_id = None  # ID entry đang edit
        self._setup_ui()
        self._refresh_table()
        self._refresh_stats()

    def refresh_theme(self):
        """Cập nhật theme cho KnowledgePanel."""
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        if hasattr(self, '_header'):
            self._header.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-bottom: 1px solid {COLORS['border']};")
        if hasattr(self, '_form_panel'):
            self._form_panel.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_primary']}; }}")
        if hasattr(self, '_list_panel'):
            self._list_panel.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_primary']}; }}")
        if hasattr(self, '_table'):
            self._table.setStyleSheet(f"QTableWidget {{ background-color: {COLORS['bg_surface']}; color: {COLORS['text_primary']}; gridline-color: {COLORS['border']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
        self._refresh_table()

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

        title = QLabel("🧠 Trí Tuệ Cá Nhân — Personal Knowledge Base")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Import / Export
        import_btn = QPushButton("📥 Nhập")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.setFixedHeight(32)
        import_btn.clicked.connect(self._import_json)
        import_btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {COLORS['text_secondary']}; border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 4px 14px; font-size: 12px; font-weight: 500; }}
            QPushButton:hover {{ border-color: {COLORS['accent_primary']}; color: {COLORS['text_primary']}; }}
        """)
        header_layout.addWidget(import_btn)

        export_btn = QPushButton("📤 Xuất")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.setFixedHeight(32)
        export_btn.clicked.connect(self._export_json)
        export_btn.setStyleSheet(import_btn.styleSheet())
        header_layout.addWidget(export_btn)

        layout.addWidget(self._header)

        # Content — Splitter
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setStyleSheet(f"QSplitter {{ background-color: {COLORS['bg_primary']}; }}")

        # LEFT: Entry form + Category cards
        self._form_panel = self._create_form_panel()
        self._splitter.addWidget(self._form_panel)

        # RIGHT: Table + Search
        self._list_panel = self._create_list_panel()
        self._splitter.addWidget(self._list_panel)

        self._splitter.setSizes([400, 600])
        layout.addWidget(self._splitter, 1)

    def _create_form_panel(self) -> QFrame:
        """Panel nhập kiến thức."""
        panel = QFrame()
        panel.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_primary']}; }}")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)

        # Category selector — Visual cards
        cat_label = QLabel("Chọn danh mục:")
        cat_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; font-weight: 600;")
        layout.addWidget(cat_label)

        cat_grid = QGridLayout()
        cat_grid.setSpacing(6)
        self._cat_buttons = {}
        row, col = 0, 0
        for cat_id, cat_info in KNOWLEDGE_CATEGORIES.items():
            btn = QPushButton(f"{cat_info['icon']} {cat_info['name']}")
            btn.setToolTip(cat_info['description'])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(38)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {cat_info['color']}11;
                    color: {COLORS['text_secondary']};
                    border: 1px solid {cat_info['color']}33;
                    border-radius: 8px;
                    font-size: 12px;
                    font-weight: 500;
                    padding: 4px 10px;
                }}
                QPushButton:checked {{
                    background-color: {cat_info['color']}33;
                    color: {cat_info['color']};
                    border-color: {cat_info['color']};
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    border-color: {cat_info['color']};
                }}
            """)
            btn.clicked.connect(lambda checked, cid=cat_id: self._select_category(cid))
            self._cat_buttons[cat_id] = btn
            cat_grid.addWidget(btn, row, col)
            col += 1
            if col >= 2:
                col = 0
                row += 1

        layout.addLayout(cat_grid)

        # Default select Q&A
        self._current_category = "qa"
        self._cat_buttons["qa"].setChecked(True)

        # Title
        layout.addWidget(QLabel("Tiêu đề:"))
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Tiêu đề ngắn gọn (tuỳ chọn)")
        layout.addWidget(self._title_input)

        # Question
        layout.addWidget(QLabel("Câu hỏi / Chủ đề:"))
        self._question_input = QTextEdit()
        self._question_input.setPlaceholderText(
            "Nhập câu hỏi hoặc chủ đề...\n"
            "VD: Tên tôi là gì?\nVD: Nguyên tắc làm việc của tôi"
        )
        self._question_input.setMaximumHeight(80)
        layout.addWidget(self._question_input)

        # Answer
        layout.addWidget(QLabel("Câu trả lời / Nội dung kiến thức:"))
        self._answer_input = QTextEdit()
        self._answer_input.setPlaceholderText(
            "Nhập câu trả lời hoặc kiến thức...\n"
            "VD: Tên tôi là Nguyễn Văn A\n"
            "VD: Luôn kiểm tra kỹ trước khi gửi"
        )
        self._answer_input.setMaximumHeight(100)
        layout.addWidget(self._answer_input)

        # Tags + Priority
        meta_row = QHBoxLayout()

        meta_row.addWidget(QLabel("Tags:"))
        self._tags_input = QLineEdit()
        self._tags_input.setPlaceholderText("tag1, tag2, tag3")
        self._tags_input.setMaximumWidth(180)
        meta_row.addWidget(self._tags_input)

        meta_row.addWidget(QLabel("Ưu tiên:"))
        self._priority_spin = QSpinBox()
        self._priority_spin.setRange(1, 10)
        self._priority_spin.setValue(5)
        self._priority_spin.setToolTip("10 = quan trọng nhất, luôn được AI sử dụng")
        meta_row.addWidget(self._priority_spin)

        layout.addLayout(meta_row)

        # Buttons
        btn_row = QHBoxLayout()

        self._save_btn = QPushButton("💾 Lưu kiến thức")
        self._save_btn.setObjectName("primaryButton")
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setFixedHeight(38)
        self._save_btn.clicked.connect(self._save_entry)
        btn_row.addWidget(self._save_btn)

        self._clear_btn = QPushButton("🗑️ Xoá form")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_form)
        btn_row.addWidget(self._clear_btn)

        layout.addLayout(btn_row)

        # Stats card
        self._stats_frame = QFrame()
        self._stats_frame.setStyleSheet(f"""
            QFrame {{
                {get_card_style()}
            }}
        """)
        stats_layout = QVBoxLayout(self._stats_frame)
        stats_layout.setContentsMargins(12, 8, 12, 8)
        self._stats_label = QLabel("")
        self._stats_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none;")
        self._stats_label.setWordWrap(True)
        stats_layout.addWidget(self._stats_label)
        layout.addWidget(self._stats_frame)

        layout.addStretch()
        return panel

    def _create_list_panel(self) -> QFrame:
        """Panel danh sách kiến thức."""
        panel = QFrame()
        panel.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_primary']}; }}")

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Search bar
        search_row = QHBoxLayout()

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Tìm kiếm kiến thức...")
        self._search_input.textChanged.connect(self._on_search)
        search_row.addWidget(self._search_input, 1)

        self._filter_combo = QComboBox()
        self._filter_combo.addItem("📋 Tất cả", "")
        for cat_id, cat_info in KNOWLEDGE_CATEGORIES.items():
            self._filter_combo.addItem(f"{cat_info['icon']} {cat_info['name']}", cat_id)
        self._filter_combo.currentIndexChanged.connect(self._refresh_table)
        self._filter_combo.setMinimumWidth(160)
        search_row.addWidget(self._filter_combo)

        layout.addLayout(search_row)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(["", "Tiêu đề", "Câu hỏi", "Câu trả lời", "Ưu tiên", "Dùng", "Hành động"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(0, 36)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(1, 130)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(4, 65)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(5, 55)
        self._table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(6, 110)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        self._table.setStyleSheet(f"QTableWidget {{ background-color: {COLORS['bg_surface']}; color: {COLORS['text_primary']}; gridline-color: {COLORS['border']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")

        layout.addWidget(self._table)

        # Bottom row
        bottom = QHBoxLayout()
        self._count_label = QLabel("0 mục")
        self._count_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        bottom.addWidget(self._count_label)
        bottom.addStretch()

        clear_all_btn = QPushButton("🗑️ Xoá tất cả")
        clear_all_btn.setObjectName("dangerButton")
        clear_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_all_btn.clicked.connect(self._clear_all)
        bottom.addWidget(clear_all_btn)

        layout.addLayout(bottom)

        return panel

    # ============================================================
    # Actions
    # ============================================================

    def _select_category(self, cat_id: str):
        """Chọn category."""
        self._current_category = cat_id
        for cid, btn in self._cat_buttons.items():
            btn.setChecked(cid == cat_id)

    def _save_entry(self):
        """Lưu / Cập nhật kiến thức."""
        question = self._question_input.toPlainText().strip()
        answer = self._answer_input.toPlainText().strip()

        if not question and not answer:
            toast_warning("Vui lòng nhập câu hỏi hoặc nội dung kiến thức.", self)
            return

        title = self._title_input.text().strip()
        tags = self._tags_input.text().strip()
        priority = self._priority_spin.value()

        if self._editing_id:
            # Update
            self.kb.update_entry(
                self._editing_id,
                category=self._current_category,
                title=title, question=question, answer=answer,
                tags=tags, priority=priority
            )
            self._editing_id = None
            self._save_btn.setText("💾 Lưu kiến thức")
        else:
            # Add new
            self.kb.add_entry(
                category=self._current_category,
                title=title, question=question, answer=answer,
                tags=tags, priority=priority
            )

        self._clear_form()
        self._refresh_table()
        self._refresh_stats()
        self.knowledge_updated.emit()

    def _clear_form(self):
        """Clear form."""
        self._title_input.clear()
        self._question_input.clear()
        self._answer_input.clear()
        self._tags_input.clear()
        self._priority_spin.setValue(5)
        self._editing_id = None
        self._save_btn.setText("💾 Lưu kiến thức")

    def _on_row_double_clicked(self, index):
        """Double click → edit entry."""
        row = index.row()
        entry_id = self._table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if not entry_id:
            return

        entry = self.kb.get_entry(entry_id)
        if not entry:
            return

        # Load vào form
        self._editing_id = entry_id
        self._select_category(entry["category"])
        self._title_input.setText(entry.get("title", ""))
        self._question_input.setPlainText(entry.get("question", ""))
        self._answer_input.setPlainText(entry.get("answer", ""))
        self._tags_input.setText(entry.get("tags", ""))
        self._priority_spin.setValue(entry.get("priority", 5))
        self._save_btn.setText("✏️ Cập nhật")

    def _delete_entry(self, entry_id: int):
        reply = QMessageBox.question(
            self, "Xoá kiến thức", "Bạn có chắc muốn xoá mục này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.kb.delete_entry(entry_id)
            self._refresh_table()
            self._refresh_stats()
            self.knowledge_updated.emit()

    def _on_search(self, text: str):
        """Tìm kiếm realtime."""
        if not text.strip():
            self._refresh_table()
            return
        results = self.kb.search(text.strip())
        self._populate_table(results)

    def _refresh_table(self):
        """Refresh bảng kiến thức."""
        cat_filter = self._filter_combo.currentData()
        entries = self.kb.get_all_entries(category=cat_filter if cat_filter else None)
        self._populate_table(entries)

    def _populate_table(self, entries: list):
        """Điền dữ liệu vào bảng."""
        self._table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            cat_info = KNOWLEDGE_CATEGORIES.get(entry["category"], {})

            # Icon (hidden data: ID)
            icon_item = QTableWidgetItem(cat_info.get("icon", "📝"))
            icon_item.setData(Qt.ItemDataRole.UserRole, entry["id"])
            self._table.setItem(row, 0, icon_item)

            # Title
            self._table.setItem(row, 1, QTableWidgetItem(entry.get("title", "")[:40]))

            # Question
            q = entry.get("question", "")
            self._table.setItem(row, 2, QTableWidgetItem(q[:60] + ("..." if len(q) > 60 else "")))

            # Answer
            a = entry.get("answer", "")
            self._table.setItem(row, 3, QTableWidgetItem(a[:60] + ("..." if len(a) > 60 else "")))

            # Priority
            p_item = QTableWidgetItem(str(entry.get("priority", 5)))
            if entry.get("priority", 5) >= 8:
                p_item.setForeground(QColor(COLORS["warning"]))
            self._table.setItem(row, 4, p_item)

            # Usage count
            self._table.setItem(row, 5, QTableWidgetItem(str(entry.get("usage_count", 0))))

            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(6)

            edit_btn = QPushButton("✏️")
            edit_btn.setFixedSize(34, 28)
            edit_btn.setToolTip("Sửa")
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_surface']};
                    color: {COLORS['text_primary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_primary']};
                    color: #ffffff;
                    border-color: {COLORS['accent_primary']};
                }}
            """)
            edit_btn.clicked.connect(lambda _, eid=entry["id"]: self._edit_entry(eid))
            action_layout.addWidget(edit_btn)

            del_btn = QPushButton("🗑️")
            del_btn.setFixedSize(34, 28)
            del_btn.setToolTip("Xoá")
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_surface']};
                    color: {COLORS['error']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['error']};
                    color: #ffffff;
                    border-color: {COLORS['error']};
                }}
            """)
            del_btn.clicked.connect(lambda _, eid=entry["id"]: self._delete_entry(eid))
            action_layout.addWidget(del_btn)

            self._table.setCellWidget(row, 6, action_widget)

        self._count_label.setText(f"{len(entries)} mục")

    def _edit_entry(self, entry_id: int):
        """Load entry vào form để sửa."""
        entry = self.kb.get_entry(entry_id)
        if not entry:
            return
        self._editing_id = entry_id
        self._select_category(entry["category"])
        self._title_input.setText(entry.get("title", ""))
        self._question_input.setPlainText(entry.get("question", ""))
        self._answer_input.setPlainText(entry.get("answer", ""))
        self._tags_input.setText(entry.get("tags", ""))
        self._priority_spin.setValue(entry.get("priority", 5))
        self._save_btn.setText("✏️ Cập nhật")

    def _refresh_stats(self):
        """Refresh thống kê."""
        stats = self.kb.get_stats()
        cat_lines = []
        for cat_id, count in stats.get("by_category", {}).items():
            cat_info = KNOWLEDGE_CATEGORIES.get(cat_id, {})
            cat_lines.append(f"{cat_info.get('icon', '📝')} {cat_info.get('name', cat_id)}: {count}")

        self._stats_label.setText(
            f"📊 Thống kê:\n"
            f"Tổng: {stats['total']} mục | Đang bật: {stats['active']}\n"
            f"AI đã sử dụng: {stats['total_usage']} lần\n"
            + ("\n".join(cat_lines) if cat_lines else "Chưa có kiến thức nào")
        )

    def _import_json(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "Nhập kiến thức", "", "JSON Files (*.json)")
        if filepath:
            count = self.kb.import_from_json(filepath)
            toast_success(f"Đã nhập {count} mục kiến thức", self)
            self._refresh_table()
            self._refresh_stats()

    def _export_json(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Xuất kiến thức", "knowledge_export.json", "JSON Files (*.json)"
        )
        if filepath:
            self.kb.export_to_json(filepath)
            toast_success(f"Đã xuất kiến thức ra file", self)

    def _clear_all(self):
        reply = QMessageBox.question(
            self, "Xoá tất cả", "Bạn có chắc muốn xoá TOÀN BỘ kiến thức cá nhân?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.kb.clear_all()
            self._refresh_table()
            self._refresh_stats()
