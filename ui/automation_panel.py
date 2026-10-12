"""
Automation Panel — Giao diện tạo/chạy macro desktop automation.
Record, edit steps, run với loop config, hotkey controls.
"""

import os
import json
import uuid
import logging
from datetime import datetime
from typing import Optional, List

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFrame, QListWidget, QListWidgetItem, QGroupBox, QSpinBox,
    QComboBox, QLineEdit, QCheckBox, QProgressBar, QSplitter,
    QSizePolicy, QFileDialog, QMessageBox, QMenu
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor

from ui.theme import COLORS, get_card_style
from core.action_executor import (
    ActionExecutor, ActionStep, ExecutorWorker,
    ACTION_MOUSE_CLICK, ACTION_KEY_PRESS, ACTION_TYPE_TEXT,
    ACTION_WAIT, ACTION_SCROLL, ACTION_OPEN_APP, ACTION_ACTIVATE_WINDOW,
    ACTION_NAMES
)
from core.screen_analyzer import ScreenAnalyzer

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class AutomationPanel(QWidget):
    """Panel tạo và chạy macro tự động hoá desktop."""

    def __init__(self, action_executor: ActionExecutor, screen_analyzer: ScreenAnalyzer,
                 state_manager=None, parent=None):
        super().__init__(parent)
        self.executor = action_executor
        self.screen_analyzer = screen_analyzer
        self.state_manager = state_manager

        self.steps: List[ActionStep] = []
        self._worker: Optional[ExecutorWorker] = None

        self._setup_ui()
        self._setup_connections()

    def refresh_theme(self):
        """Cập nhật theme cho AutomationPanel."""
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        if hasattr(self, '_header'):
            self._header.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-bottom: 1px solid {COLORS['border']};")
        if hasattr(self, '_content'):
            self._content.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        if hasattr(self, '_left_panel'):
            self._left_panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                }}
            """)
        if hasattr(self, '_right_panel'):
            self._right_panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                }}
            """)
        if hasattr(self, '_exec_bar'):
            self._exec_bar.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_secondary']};
                    border-top: 1px solid {COLORS['border']};
                }}
            """)

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === HEADER ===
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

        title = QLabel("🖱️ Desktop Automation — Macro Builder")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(self._header)

        # === CONTENT ===
        self._content = QWidget()
        self._content.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        content_layout = QHBoxLayout(self._content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(16)

        # LEFT: Step list
        self._left_panel = self._create_step_list_panel()
        content_layout.addWidget(self._left_panel, 3)

        # RIGHT: Controls
        self._right_panel = self._create_controls_panel()
        content_layout.addWidget(self._right_panel, 2)

        layout.addWidget(self._content, 1)

        # === BOTTOM: Execution bar ===
        self._exec_bar = self._create_execution_bar()
        layout.addWidget(self._exec_bar)

    def _create_step_list_panel(self) -> QFrame:
        """Panel danh sách các bước."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Toolbar
        toolbar = QHBoxLayout()

        add_btn = QPushButton("➕ Thêm bước")
        add_btn.setObjectName("primaryButton")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_step)
        toolbar.addWidget(add_btn)

        remove_btn = QPushButton("🗑️ Xoá")
        remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        remove_btn.clicked.connect(self._remove_step)
        toolbar.addWidget(remove_btn)

        toolbar.addStretch()

        save_btn = QPushButton("💾 Lưu")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self._save_preset)
        toolbar.addWidget(save_btn)

        load_btn = QPushButton("📂 Mở")
        load_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        load_btn.clicked.connect(self._load_preset)
        toolbar.addWidget(load_btn)

        layout.addLayout(toolbar)

        # Step list
        self._step_list = QListWidget()
        self._step_list.setAlternatingRowColors(True)
        self._step_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self._step_list.currentRowChanged.connect(self._on_step_selected)
        layout.addWidget(self._step_list)

        return panel

    def _create_controls_panel(self) -> QFrame:
        """Panel điều khiển chi tiết bước."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Action type
        type_group = QGroupBox("Loại hành động")
        type_layout = QVBoxLayout(type_group)

        self._action_type_combo = QComboBox()
        for action_type, name in ACTION_NAMES.items():
            self._action_type_combo.addItem(name, action_type)
        self._action_type_combo.currentIndexChanged.connect(self._on_action_type_changed)
        type_layout.addWidget(self._action_type_combo)
        layout.addWidget(type_group)

        # Parameters
        params_group = QGroupBox("Thông số")
        params_layout = QVBoxLayout(params_group)

        # X, Y coordinates
        coord_row = QHBoxLayout()
        coord_row.addWidget(QLabel("X:"))
        self._x_spin = QSpinBox()
        self._x_spin.setRange(0, 9999)
        coord_row.addWidget(self._x_spin)
        coord_row.addWidget(QLabel("Y:"))
        self._y_spin = QSpinBox()
        self._y_spin.setRange(0, 9999)
        coord_row.addWidget(self._y_spin)

        pick_btn = QPushButton("🎯")
        pick_btn.setFixedSize(32, 32)
        pick_btn.setToolTip("Chọn toạ độ trên màn hình (F5)")
        pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pick_btn.clicked.connect(self._pick_coordinates)
        coord_row.addWidget(pick_btn)

        params_layout.addLayout(coord_row)

        # Key / Text input
        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("Phím (vd: enter, ctrl+c, tab)")
        params_layout.addWidget(QLabel("Phím / Văn bản:"))
        params_layout.addWidget(self._key_input)

        # Delay
        delay_row = QHBoxLayout()
        delay_row.addWidget(QLabel("Delay sau (ms):"))
        self._delay_spin = QSpinBox()
        self._delay_spin.setRange(0, 60000)
        self._delay_spin.setValue(300)
        self._delay_spin.setSingleStep(100)
        delay_row.addWidget(self._delay_spin)
        params_layout.addLayout(delay_row)

        # Apply button
        apply_btn = QPushButton("✅ Áp dụng thay đổi")
        apply_btn.setObjectName("primaryButton")
        apply_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_btn.clicked.connect(self._apply_step_changes)
        params_layout.addWidget(apply_btn)

        layout.addWidget(params_group)

        # Loop config
        loop_group = QGroupBox("Vòng lặp")
        loop_layout = QVBoxLayout(loop_group)

        loop_row = QHBoxLayout()
        loop_row.addWidget(QLabel("Số lần lặp:"))
        self._loop_spin = QSpinBox()
        self._loop_spin.setRange(1, 99999)
        self._loop_spin.setValue(1)
        loop_row.addWidget(self._loop_spin)
        loop_layout.addLayout(loop_row)

        delay_loop_row = QHBoxLayout()
        delay_loop_row.addWidget(QLabel("Delay giữa vòng (ms):"))
        self._loop_delay_spin = QSpinBox()
        self._loop_delay_spin.setRange(0, 60000)
        self._loop_delay_spin.setValue(500)
        self._loop_delay_spin.setSingleStep(100)
        delay_loop_row.addWidget(self._loop_delay_spin)
        loop_layout.addLayout(delay_loop_row)

        layout.addWidget(loop_group)

        layout.addStretch()
        return panel

    def _create_execution_bar(self) -> QFrame:
        """Thanh thực thi ở dưới."""
        bar = QFrame()
        bar.setFixedHeight(70)
        bar.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(12)

        # Progress
        self._progress = QProgressBar()
        self._progress.setValue(0)
        self._progress.setFixedHeight(8)
        self._progress.setTextVisible(False)

        # Status label
        self._status_label = QLabel("Sẵn sàng")
        self._status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; border: none;")

        # Buttons
        self._start_btn = QPushButton("▶️  Chạy (F8)")
        self._start_btn.setObjectName("successButton")
        self._start_btn.setFixedSize(120, 40)
        self._start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._start_btn.clicked.connect(self._start_execution)

        self._pause_btn = QPushButton("⏸️  Tạm dừng (F9)")
        self._pause_btn.setFixedSize(140, 40)
        self._pause_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._pause_btn.setEnabled(False)
        self._pause_btn.clicked.connect(self._toggle_pause)

        self._stop_btn = QPushButton("⏹️  Dừng (F10)")
        self._stop_btn.setObjectName("dangerButton")
        self._stop_btn.setFixedSize(120, 40)
        self._stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop_execution)

        info_layout = QVBoxLayout()
        info_layout.addWidget(self._progress)
        info_layout.addWidget(self._status_label)

        layout.addLayout(info_layout, 1)
        layout.addWidget(self._start_btn)
        layout.addWidget(self._pause_btn)
        layout.addWidget(self._stop_btn)

        return bar

    def _setup_connections(self):
        """Kết nối signals."""
        self.executor.step_started.connect(self._on_step_started)
        self.executor.step_completed.connect(self._on_step_completed)
        self.executor.step_error.connect(self._on_step_error)
        self.executor.execution_finished.connect(self._on_execution_finished)
        self.executor.progress_update.connect(self._on_progress)
        self.executor.log_message.connect(self._on_log)

    # ==================== Step Management ====================

    def _add_step(self):
        """Thêm bước mới."""
        action_type = self._action_type_combo.currentData() or ACTION_MOUSE_CLICK
        step = ActionStep(
            id=str(uuid.uuid4())[:8],
            name=ACTION_NAMES.get(action_type, "Bước mới"),
            action_type=action_type,
            delay_after_ms=self._delay_spin.value(),
            x=self._x_spin.value() or None,
            y=self._y_spin.value() or None,
            key_string=self._key_input.text() or "enter",
            text_content=self._key_input.text() if action_type == ACTION_TYPE_TEXT else "",
        )
        self.steps.append(step)
        self._refresh_step_list()

    def _remove_step(self):
        """Xoá bước đang chọn."""
        row = self._step_list.currentRow()
        if 0 <= row < len(self.steps):
            self.steps.pop(row)
            self._refresh_step_list()

    def _refresh_step_list(self):
        """Refresh danh sách bước."""
        self._step_list.clear()
        for i, step in enumerate(self.steps):
            icon = ACTION_NAMES.get(step.action_type, "⚡").split(" ")[0]
            text = f"{i + 1}. {icon} {step.get_summary()}  [{step.delay_after_ms}ms]"
            item = QListWidgetItem(text)
            if not step.enabled:
                item.setForeground(QColor(COLORS["text_disabled"]))
            self._step_list.addItem(item)

    def _on_step_selected(self, row: int):
        """Khi chọn 1 bước — load thông số vào controls."""
        if 0 <= row < len(self.steps):
            step = self.steps[row]
            # Find combo index
            for i in range(self._action_type_combo.count()):
                if self._action_type_combo.itemData(i) == step.action_type:
                    self._action_type_combo.setCurrentIndex(i)
                    break
            self._x_spin.setValue(step.x or 0)
            self._y_spin.setValue(step.y or 0)
            self._delay_spin.setValue(step.delay_after_ms)
            if step.action_type == ACTION_TYPE_TEXT:
                self._key_input.setText(step.text_content)
            elif step.action_type == ACTION_KEY_PRESS:
                self._key_input.setText(step.key_string)
            elif step.action_type == ACTION_OPEN_APP:
                self._key_input.setText(step.target_path)
            elif step.action_type == ACTION_ACTIVATE_WINDOW:
                self._key_input.setText(step.window_title)

    def _apply_step_changes(self):
        """Áp dụng thay đổi cho bước đang chọn."""
        row = self._step_list.currentRow()
        if 0 <= row < len(self.steps):
            step = self.steps[row]
            step.action_type = self._action_type_combo.currentData()
            step.x = self._x_spin.value() or None
            step.y = self._y_spin.value() or None
            step.delay_after_ms = self._delay_spin.value()
            step.name = ACTION_NAMES.get(step.action_type, "Bước")

            if step.action_type == ACTION_TYPE_TEXT:
                step.text_content = self._key_input.text()
            elif step.action_type == ACTION_KEY_PRESS:
                step.key_string = self._key_input.text()
            elif step.action_type == ACTION_OPEN_APP:
                step.target_path = self._key_input.text()
            elif step.action_type == ACTION_ACTIVATE_WINDOW:
                step.window_title = self._key_input.text()

            self._refresh_step_list()
            self._step_list.setCurrentRow(row)

    def _on_action_type_changed(self, index: int):
        """Update placeholder text theo action type."""
        action = self._action_type_combo.currentData()
        placeholders = {
            ACTION_MOUSE_CLICK: "Nút chuột (left/right/double)",
            ACTION_KEY_PRESS: "Phím (vd: enter, ctrl+c, tab)",
            ACTION_TYPE_TEXT: "Văn bản cần gõ",
            ACTION_OPEN_APP: "Đường dẫn app hoặc URL",
            ACTION_ACTIVATE_WINDOW: "Tên cửa sổ (vd: Chrome)",
        }
        self._key_input.setPlaceholderText(placeholders.get(action, "Tham số"))

    def _pick_coordinates(self):
        """Chọn toạ độ trên màn hình."""
        self._status_label.setText("🎯 Nhấn chuột vào vị trí muốn chọn (3 giây)...")
        main_window = self.window()
        if main_window:
            main_window.hide()

        QTimer.singleShot(3000, self._capture_cursor_pos)

    def _capture_cursor_pos(self):
        """Lấy vị trí cursor sau delay."""
        pos = self.screen_analyzer.get_cursor_position()
        self._x_spin.setValue(pos[0])
        self._y_spin.setValue(pos[1])

        main_window = self.window()
        if main_window:
            main_window.show()
            main_window.activateWindow()

        self._status_label.setText(f"🎯 Đã chọn toạ độ: ({pos[0]}, {pos[1]})")

    # ==================== Execution ====================

    def _start_execution(self):
        """Bắt đầu chạy macro."""
        if not self.steps:
            self._status_label.setText("⚠️ Chưa có bước nào!")
            return

        self._start_btn.setEnabled(False)
        self._pause_btn.setEnabled(True)
        self._stop_btn.setEnabled(True)
        self._progress.setValue(0)

        self._worker = ExecutorWorker(
            self.executor, self.steps,
            loop_count=self._loop_spin.value(),
            loop_delay_ms=self._loop_delay_spin.value()
        )
        self._worker.start()

    def _toggle_pause(self):
        """Bật/tắt tạm dừng."""
        self.executor.toggle_pause()
        if self.executor.is_paused:
            self._pause_btn.setText("▶️  Tiếp tục")
            self._status_label.setText("⏸️ Đã tạm dừng")
        else:
            self._pause_btn.setText("⏸️  Tạm dừng (F9)")
            self._status_label.setText("▶️ Đang chạy...")

    def _stop_execution(self):
        """Dừng macro."""
        self.executor.stop()

    def _on_step_started(self, index: int, desc: str):
        self._status_label.setText(f"▶️ Bước {index + 1}: {desc}")
        self._step_list.setCurrentRow(index)

    def _on_step_completed(self, index: int, status: str):
        pass

    def _on_step_error(self, index: int, error: str):
        self._status_label.setText(f"❌ Lỗi bước {index + 1}: {error}")

    def _on_execution_finished(self, status: str):
        self._start_btn.setEnabled(True)
        self._pause_btn.setEnabled(False)
        self._stop_btn.setEnabled(False)
        self._pause_btn.setText("⏸️  Tạm dừng (F9)")

        if status == "COMPLETED":
            self._status_label.setText("✅ Hoàn thành!")
            self._progress.setValue(100)
        elif status == "STOPPED":
            self._status_label.setText("⏹️ Đã dừng")
        else:
            self._status_label.setText(f"⚠️ Kết thúc: {status}")

    def _on_progress(self, current: int, total: int):
        if total > 0:
            self._progress.setValue(int(current / total * 100))

    def _on_log(self, message: str):
        logger.info(f"[Automation] {message}")

    # ==================== Save/Load ====================

    def _save_preset(self):
        """Lưu macro ra file JSON."""
        if not self.steps:
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Lưu Macro", os.path.join(BASE_DIR, "presets", "macro.json"),
            "JSON Files (*.json)"
        )
        if filepath:
            data = {
                "name": "Macro",
                "steps": [s.to_dict() for s in self.steps],
                "loop_count": self._loop_spin.value(),
                "loop_delay_ms": self._loop_delay_spin.value(),
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._status_label.setText(f"💾 Đã lưu: {os.path.basename(filepath)}")

    def _load_preset(self):
        """Load macro từ file JSON."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Mở Macro", os.path.join(BASE_DIR, "presets"),
            "JSON Files (*.json)"
        )
        if filepath:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.steps = [ActionStep.from_dict(s) for s in data.get("steps", [])]
            self._loop_spin.setValue(data.get("loop_count", 1))
            self._loop_delay_spin.setValue(data.get("loop_delay_ms", 500))
            self._refresh_step_list()
            self._status_label.setText(f"📂 Đã mở: {os.path.basename(filepath)}")
