"""
Settings Dialog — Cài đặt Multi-Provider AI Models & API Keys.
Hỗ trợ: Gemini, OpenAI (ChatGPT), Anthropic (Claude), DeepSeek, Qwen.
Phân loại: Rẻ nhất, Cân bằng, Giá vừa phải, Tốt nhất.
"""

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QComboBox, QGroupBox, QTextEdit, QTabWidget,
    QWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QCheckBox, QFrame, QRadioButton, QButtonGroup,
    QScrollArea, QGridLayout, QSizePolicy, QSlider, QSpinBox,
    QApplication
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from ui.theme import (
    COLORS, get_card_style, set_theme, set_density,
    get_current_theme, get_current_density_key, build_stylesheet,
    apply_titlebar_theme,
    DENSITY_CONFIG, DENSITY_MATERIAL, DENSITY_COMPACT, DENSITY_LITE_COMPACT, DENSITY_SUPER_COMPACT
)
from core.key_manager import KeyManager
from core.model_registry import (
    Provider, ModelTier, ModelInfo,
    PROVIDER_DISPLAY, TIER_DISPLAY,
    registry as model_registry
)
from ui.toast import toast_success, toast_error, toast_warning, toast_info, TOAST_POSITIONS, get_saved_toast_position

logger = logging.getLogger(__name__)


class AddUserDialog(QDialog):
    """Hộp thoại thêm tài khoản người dùng mới."""

    def __init__(self, state_manager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.setWindowTitle("➕ Thêm Tài Khoản Mới")
        self.setFixedSize(390, 370)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._setup_ui()
        apply_titlebar_theme(self)

    def _setup_ui(self):
        c = COLORS
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['bg_primary']}; color: {c['text_primary']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; font-weight: 500; }}
            QLineEdit, QComboBox {{
                background-color: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px 10px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {c['accent_primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Username
        layout.addWidget(QLabel("Tên đăng nhập:"))
        self.txt_username = QLineEdit()
        self.txt_username.setPlaceholderText("VD: nhanvien1, quanly...")
        layout.addWidget(self.txt_username)

        # Display Name
        layout.addWidget(QLabel("Tên hiển thị:"))
        self.txt_display_name = QLineEdit()
        self.txt_display_name.setPlaceholderText("VD: Nguyễn Văn A")
        layout.addWidget(self.txt_display_name)

        # Password
        layout.addWidget(QLabel("Mật khẩu:"))
        self.txt_password = QLineEdit()
        self.txt_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_password.setPlaceholderText("••••••••")
        layout.addWidget(self.txt_password)

        # Role
        layout.addWidget(QLabel("Vai trò (Role):"))
        self.combo_role = QComboBox()
        self.combo_role.addItem("Quản trị viên (admin)", "admin")
        self.combo_role.addItem("Người dùng (user)", "user")
        layout.addWidget(self.combo_role)

        layout.addSpacing(6)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Huỷ")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Tạo tài khoản")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 18px;
            }}
        """)
        save_btn.clicked.connect(self._handle_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _handle_save(self):
        u = self.txt_username.text().strip()
        dn = self.txt_display_name.text().strip()
        p = self.txt_password.text()
        role = self.combo_role.currentData()

        if not u:
            toast_warning("Tên đăng nhập không được để trống!", self)
            self.txt_username.setFocus()
            return
        if not p:
            toast_warning("Mật khẩu không được để trống!", self)
            self.txt_password.setFocus()
            return

        success, msg = self.state_manager.create_user(u, p, display_name=dn, role=role)
        if success:
            toast_success(msg, self.parent())
            self.accept()
        else:
            toast_error(msg, self)


class EditUserDialog(QDialog):
    """Hộp thoại sửa thông tin tài khoản người dùng."""

    def __init__(self, state_manager, user_data: dict, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.user_data = user_data
        self.setWindowTitle(f"✏️ Sửa Tài Khoản: {user_data.get('username')}")
        self.setFixedSize(390, 320)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._setup_ui()
        apply_titlebar_theme(self)

    def _setup_ui(self):
        c = COLORS
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['bg_primary']}; color: {c['text_primary']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; font-weight: 500; }}
            QLineEdit, QComboBox {{
                background-color: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px 10px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border-color: {c['accent_primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Username (read only)
        layout.addWidget(QLabel(f"Tên đăng nhập: <b>{self.user_data.get('username')}</b>"))

        # Display Name
        layout.addWidget(QLabel("Tên hiển thị:"))
        self.txt_display_name = QLineEdit()
        self.txt_display_name.setText(self.user_data.get("display_name", ""))
        layout.addWidget(self.txt_display_name)

        # Role
        layout.addWidget(QLabel("Vai trò (Role):"))
        self.combo_role = QComboBox()
        self.combo_role.addItem("Quản trị viên (admin)", "admin")
        self.combo_role.addItem("Người dùng (user)", "user")
        curr_role = self.user_data.get("role", "admin")
        idx = 0 if curr_role == "admin" else 1
        self.combo_role.setCurrentIndex(idx)
        layout.addWidget(self.combo_role)

        # Active Status
        self.cb_active = QCheckBox("Tài khoản đang hoạt động (Active)")
        self.cb_active.setChecked(bool(self.user_data.get("is_active", 1)))
        layout.addWidget(self.cb_active)

        layout.addSpacing(6)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Huỷ")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Lưu thay đổi")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 18px;
            }}
        """)
        save_btn.clicked.connect(self._handle_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _handle_save(self):
        dn = self.txt_display_name.text().strip()
        role = self.combo_role.currentData()
        active = 1 if self.cb_active.isChecked() else 0

        success, msg = self.state_manager.update_user(
            self.user_data["id"], display_name=dn, role=role, is_active=active
        )
        if success:
            toast_success("Cập nhật thông tin tài khoản thành công!", self.parent())
            self.accept()
        else:
            toast_error(msg, self)


class ChangePasswordDialog(QDialog):
    """Hộp thoại đổi mật khẩu tài khoản."""

    def __init__(self, state_manager, user_data: dict, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self.user_data = user_data
        self.setWindowTitle(f"🔑 Đổi Mật Khẩu: {user_data.get('username')}")
        self.setFixedSize(390, 260)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._setup_ui()
        apply_titlebar_theme(self)

    def _setup_ui(self):
        c = COLORS
        self.setStyleSheet(f"""
            QDialog {{ background-color: {c['bg_primary']}; color: {c['text_primary']}; }}
            QLabel {{ color: {c['text_primary']}; font-size: 13px; font-weight: 500; }}
            QLineEdit {{
                background-color: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 6px;
                padding: 8px 10px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {c['accent_primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        layout.addWidget(QLabel(f"Tài khoản: <b>{self.user_data.get('username')}</b>"))

        layout.addWidget(QLabel("Mật khẩu mới:"))
        self.txt_new_pass = QLineEdit()
        self.txt_new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_new_pass.setPlaceholderText("Nhập mật khẩu mới...")
        layout.addWidget(self.txt_new_pass)

        layout.addWidget(QLabel("Xác nhận mật khẩu mới:"))
        self.txt_confirm_pass = QLineEdit()
        self.txt_confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_confirm_pass.setPlaceholderText("Nhập lại mật khẩu mới...")
        layout.addWidget(self.txt_confirm_pass)

        layout.addSpacing(6)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Huỷ")
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("🔑 Đổi mật khẩu")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                padding: 8px 18px;
            }}
        """)
        save_btn.clicked.connect(self._handle_save)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _handle_save(self):
        p1 = self.txt_new_pass.text()
        p2 = self.txt_confirm_pass.text()

        if not p1:
            toast_warning("Mật khẩu mới không được để trống!", self)
            self.txt_new_pass.setFocus()
            return

        if p1 != p2:
            toast_error("Mật khẩu xác nhận không khớp!", self)
            self.txt_confirm_pass.selectAll()
            self.txt_confirm_pass.setFocus()
            return

        success, msg = self.state_manager.change_user_password(self.user_data["id"], p1)
        if success:
            toast_success("Đổi mật khẩu thành công!", self.parent())
            self.accept()
        else:
            toast_error(msg, self)


class KeyCheckWorker(QThread):
    """Worker thread để check API key health."""
    result_ready = pyqtSignal(dict)

    def __init__(self, key_manager: KeyManager, api_key: str):
        super().__init__()
        self.key_manager = key_manager
        self.api_key = api_key

    def run(self):
        result = self.key_manager.check_key_health(self.api_key)
        self.result_ready.emit(result)


class ModelTestWorker(QThread):
    """Worker thread để test model hoạt động."""
    result_ready = pyqtSignal(str, bool, str)  # model_id, success, message

    def __init__(self, ai_engine, model_id: str, parent=None):
        super().__init__(parent)
        self.ai_engine = ai_engine
        self.model_id = model_id

    def run(self):
        try:
            import time
            start = time.time()
            result = self.ai_engine.quick_test(self.model_id)
            elapsed = time.time() - start
            if result:
                self.result_ready.emit(self.model_id, True, f"Phản hồi trong {elapsed:.2f}s")
            else:
                self.result_ready.emit(self.model_id, False, "Mô hình không trả về phản hồi.")
        except Exception as e:
            err_str = str(e)
            if "401" in err_str or "API_KEY_INVALID" in err_str or "Unauthorized" in err_str:
                msg = "API Key không hợp lệ hoặc đã hết hạn (HTTP 401)."
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota" in err_str:
                msg = "Hết hạn mức Quota hoặc bị giới hạn tần suất (HTTP 429)."
            elif "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
                msg = "Mô hình đang quá tải tạm thời từ nhà cung cấp (HTTP 503)."
            elif "404" in err_str or "NOT_FOUND" in err_str:
                msg = "Mô hình không khả dụng trên tài khoản này (HTTP 404)."
            else:
                msg = err_str[:120]
            self.result_ready.emit(self.model_id, False, msg)


class FetchLiveModelsWorker(QThread):
    """Worker thread truy vấn danh sách models khả dụng từ API."""
    models_ready = pyqtSignal(str, list)  # provider, list_of_models
    error_occurred = pyqtSignal(str, str)  # provider, error_message

    def __init__(self, ai_engine, provider: str = "", parent=None):
        super().__init__(parent)
        self.ai_engine = ai_engine
        self.provider = provider

    def run(self):
        try:
            models = self.ai_engine.fetch_live_models_from_api(self.provider)
            self.models_ready.emit(self.provider, models)
        except Exception as e:
            self.error_occurred.emit(self.provider, str(e))

class BulkTestWorker(QThread):
    """Worker thread để test nhiều model tuần tự nhằm tránh rate limit và không đơ UI."""
    test_result_ready = pyqtSignal(str, bool, str)  # model_id, success, message
    test_started = pyqtSignal(str) # model_id
    finished_all = pyqtSignal()

    def __init__(self, ai_engine, model_ids: list, parent=None):
        super().__init__(parent)
        self.ai_engine = ai_engine
        self.model_ids = model_ids
        self._is_running = True

    def run(self):
        import time
        for model_id in self.model_ids:
            if not self._is_running:
                break
            
            self.test_started.emit(model_id)
            try:
                start = time.time()
                result = self.ai_engine.quick_test(model_id)
                elapsed = time.time() - start
                if result:
                    self.test_result_ready.emit(model_id, True, f"Phản hồi trong {elapsed:.2f}s")
                else:
                    self.test_result_ready.emit(model_id, False, "Mô hình không trả về phản hồi.")
            except Exception as e:
                err_str = str(e)
                if "401" in err_str or "API_KEY_INVALID" in err_str or "Unauthorized" in err_str:
                    msg = "API Key không hợp lệ (HTTP 401)."
                elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "Quota" in err_str:
                    msg = "Hết hạn mức Quota (HTTP 429)."
                elif "503" in err_str or "UNAVAILABLE" in err_str or "high demand" in err_str.lower():
                    msg = "Mô hình đang quá tải (HTTP 503)."
                elif "404" in err_str or "NOT_FOUND" in err_str:
                    msg = "Mô hình không khả dụng (HTTP 404)."
                else:
                    msg = err_str[:120]
                self.test_result_ready.emit(model_id, False, msg)
                
            # Tránh rate limit
            time.sleep(1)
            
        self.finished_all.emit()

    def stop(self):
        self._is_running = False


class AvailableModelsDialog(QDialog):
    """Dialog hiển thị danh sách models khả dụng với API Key thực tế của tài khoản."""
    model_selected = pyqtSignal(str)  # model_id

    def __init__(self, provider: str, models: list, ai_engine, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.models = models
        self.ai_engine = ai_engine
        self.setWindowTitle(f"✨ Danh Sách Mô Hình Khả Dụng — {PROVIDER_DISPLAY.get(provider, {}).get('name', provider)}")
        self.resize(840, 580)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']}; color: {COLORS['text_primary']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Info
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        h_layout = QHBoxLayout(header)
        prov_info = PROVIDER_DISPLAY.get(self.provider, {})
        h_lbl = QLabel(f"<b>{prov_info.get('icon', '⚡')} {prov_info.get('name', self.provider)}</b> — Tìm thấy <b>{len(self.models)}</b> mô hình tương thích với API Key của bạn.")
        h_lbl.setStyleSheet(f"font-size: 13px; color: {COLORS['text_primary']};")
        h_layout.addWidget(h_lbl)
        layout.addWidget(header)

        # Search box
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("🔍 Nhập từ khoá để tìm kiếm model (VD: flash, pro, gpt, 3.6, preview)...")
        self._search_input.setFixedHeight(36)
        self._search_input.textChanged.connect(self._filter_table)
        layout.addWidget(self._search_input)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(3)
        self._table.setHorizontalHeaderLabels(["Tên Mô Hình (Model ID)", "Tính năng hỗ trợ", "Thao tác"])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(0, 310)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().resizeSection(2, 290)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                gridline-color: {COLORS['border']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(self._table, 1)

        self._populate_table(self.models)

        # Bottom row
        bottom = QHBoxLayout()
        bottom.addStretch()
        close_btn = QPushButton("Đóng")
        close_btn.setFixedHeight(36)
        close_btn.setFixedWidth(100)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: {COLORS['bg_surface_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        bottom.addWidget(close_btn)
        layout.addLayout(bottom)

    def _populate_table(self, models_to_show):
        self._table.setRowCount(len(models_to_show))
        for row, m in enumerate(models_to_show):
            m_id = m.get("id", "")
            actions = m.get("actions", [])
            actions_text = ", ".join(actions) if actions else "Chat, Generate Content"

            # Col 0: Model ID
            id_item = QTableWidgetItem(m_id)
            id_item.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
            self._table.setItem(row, 0, id_item)

            # Col 1: Actions
            act_item = QTableWidgetItem(actions_text)
            act_item.setForeground(QColor(COLORS["text_secondary"]))
            self._table.setItem(row, 1, act_item)

            # Col 2: Action buttons container
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 2, 4, 2)
            btn_layout.setSpacing(6)

            # Test button
            t_btn = QPushButton("🧪 Test")
            t_btn.setFixedSize(65, 26)
            t_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            t_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_input']};
                    color: {COLORS['accent_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['accent_secondary']}22;
                    border-color: {COLORS['accent_secondary']};
                }}
            """)
            t_btn.clicked.connect(lambda _, mid=m_id, btn=t_btn: self._test_single_model(mid, btn))
            btn_layout.addWidget(t_btn)

            # Select / Use button
            s_btn = QPushButton("🚀 Sử dụng")
            s_btn.setFixedSize(85, 26)
            s_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            s_btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_primary_hover']});
                    color: #ffffff;
                    border: none;
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 700;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['accent_primary_hover']}, stop:1 {COLORS['accent_primary']});
                }}
            """)
            s_btn.clicked.connect(lambda _, mid=m_id: self._select_and_close(mid))
            btn_layout.addWidget(s_btn)

            # Default button
            d_btn = QPushButton("⭐ Mặc định")
            d_btn.setFixedSize(85, 26)
            d_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            d_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['warning']}22;
                    color: {COLORS['warning']};
                    border: 1px solid {COLORS['warning']};
                    border-radius: 4px;
                    font-size: 11px;
                    font-weight: 600;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['warning']}44;
                }}
            """)
            d_btn.clicked.connect(lambda _, mid=m_id: self._set_default_and_close(mid))
            btn_layout.addWidget(d_btn)

            self._table.setCellWidget(row, 2, btn_widget)

    def _filter_table(self, query: str):
        query = query.strip().lower()
        if not query:
            self._populate_table(self.models)
            return
        filtered = [m for m in self.models if query in m.get("id", "").lower() or query in m.get("name", "").lower()]
        self._populate_table(filtered)

    def _test_single_model(self, model_id: str, btn: QPushButton):
        btn.setText("⏳ ...")
        btn.setEnabled(False)
        model_registry.register_dynamic_model(model_id, self.provider)
        worker = ModelTestWorker(self.ai_engine, model_id, self)
        def on_res(mid, ok, msg):
            if ok:
                btn.setText("✅ OK")
                btn.setStyleSheet(f"background-color: {COLORS['success']}22; color: {COLORS['success']}; border: 1px solid {COLORS['success']}; border-radius: 4px; font-size: 11px; font-weight: 600;")
                toast_success(f"🎉 Model '{model_id}' hoạt động rất tốt! ({msg})", self)
            else:
                btn.setText("❌ Lỗi")
                btn.setStyleSheet(f"background-color: {COLORS['error']}22; color: {COLORS['error']}; border: 1px solid {COLORS['error']}; border-radius: 4px; font-size: 11px; font-weight: 600;")
                toast_error(f"❌ Test thất bại với '{model_id}': {msg}", self)
            btn.setEnabled(True)
        worker.result_ready.connect(on_res)
        worker.start()

    def _select_and_close(self, model_id: str):
        model_registry.register_dynamic_model(model_id, self.provider)
        self.model_selected.emit(model_id)
        self.accept()

    def _set_default_and_close(self, model_id: str):
        model_registry.register_dynamic_model(model_id, self.provider)
        model_registry.set_default_model(model_id)
        self.model_selected.emit(model_id)
        if self.parent() and hasattr(self.parent(), 'state_manager'):
            self.parent().state_manager.set_app_setting("default_model", model_id)
        if self.parent():
            toast_success(f"🌟 Đã đặt {model_id} làm mô hình mặc định.", self.parent())
        self.accept()


class ScannedModelCard(QFrame):
    """Card hiển thị 1 model được quét trực tiếp từ API Key."""
    use_requested = pyqtSignal(str, str)       # model_id, provider
    test_requested = pyqtSignal(str)           # model_id
    default_requested = pyqtSignal(str, str)   # model_id, provider

    def __init__(self, model_data: dict, provider: str, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.model_data = model_data
        self.model_id = model_data.get("id", "")
        self.provider = provider
        self._is_active = is_active
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(6)

        # Row 1: Provider Icon + Model ID + Active Badge + Action Buttons
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        prov = PROVIDER_DISPLAY.get(self.provider, {})
        name_lbl = QLabel(f"{prov.get('icon', '⚡')} <b>{self.model_id}</b>")
        name_lbl.setTextFormat(Qt.TextFormat.RichText)
        name_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; border: none; background: transparent;")
        row1.addWidget(name_lbl)

        # Badge Active
        self._active_badge = QLabel("✅ Đang dùng")
        self._active_badge.setStyleSheet(f"""
            background-color: {COLORS['success']}22;
            color: {COLORS['success']};
            border-radius: 6px;
            padding: 2px 8px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid {COLORS['success']}44;
        """)
        self._active_badge.setVisible(self._is_active)
        row1.addWidget(self._active_badge)

        row1.addStretch()

        # Test button
        self._test_btn = QPushButton("🧪 Test")
        self._test_btn.setFixedSize(65, 28)
        self._test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['accent_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']}22;
                border-color: {COLORS['accent_secondary']};
            }}
        """)
        self._test_btn.clicked.connect(lambda: self.test_requested.emit(self.model_id))
        row1.addWidget(self._test_btn)

        # Use button
        use_btn = QPushButton("🚀 Sử dụng ngay")
        use_btn.setFixedSize(115, 28)
        use_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        use_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_primary_hover']});
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 700;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['accent_primary_hover']}, stop:1 {COLORS['accent_primary']});
            }}
        """)
        use_btn.clicked.connect(lambda: self.use_requested.emit(self.model_id, self.provider))
        row1.addWidget(use_btn)

        # Default button
        def_btn = QPushButton("⭐ Mặc định")
        def_btn.setFixedSize(85, 28)
        def_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        def_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['warning']}22;
                color: {COLORS['warning']};
                border: 1px solid {COLORS['warning']}44;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['warning']}44;
                border-color: {COLORS['warning']};
            }}
        """)
        def_btn.clicked.connect(lambda: self.default_requested.emit(self.model_id, self.provider))
        row1.addWidget(def_btn)

        layout.addLayout(row1)

        # Row 2: Description & actions
        actions = self.model_data.get("actions", [])
        act_text = ", ".join(actions) if actions else "Chat, Generate Content"
        desc_text = self.model_data.get("description", "") or f"Hỗ trợ: {act_text}"
        desc = QLabel(f"• Tính năng: {act_text}" + (f" — {desc_text}" if desc_text and desc_text != act_text else ""))
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px; border: none; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

    def _update_style(self):
        border_color = COLORS['accent_primary'] if self._is_active else COLORS['border']
        bg_color = COLORS['sidebar_active'] if self._is_active else COLORS['bg_surface']
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: {'2px' if self._is_active else '1px'} solid {border_color};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {COLORS['accent_secondary']};
                background-color: {COLORS['bg_surface_hover']};
            }}
        """)

    def set_active(self, is_active: bool):
        self._is_active = is_active
        self._active_badge.setVisible(is_active)
        self._update_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.use_requested.emit(self.model_id, self.provider)
        super().mousePressEvent(event)

    def set_test_state(self, state: str, message: str = ""):
        if state == "testing":
            self._test_btn.setText("⏳ ...")
            self._test_btn.setEnabled(False)
        elif state == "success":
            self._test_btn.setText("✅ OK")
            self._test_btn.setToolTip(f"OK: {message}")
            self._test_btn.setEnabled(True)
            self._test_btn.setStyleSheet(f"background-color: {COLORS['success']}22; color: {COLORS['success']}; border: 1px solid {COLORS['success']}; border-radius: 6px; font-size: 11px; font-weight: 600;")
        elif state == "failed":
            self._test_btn.setText("❌ Lỗi")
            self._test_btn.setToolTip(f"Lỗi: {message}")
            self._test_btn.setEnabled(True)
            self._test_btn.setStyleSheet(f"background-color: {COLORS['error']}22; color: {COLORS['error']}; border: 1px solid {COLORS['error']}; border-radius: 6px; font-size: 11px; font-weight: 600;")


class ModelCard(QFrame):
    """Widget thẻ model đẹp với thông tin chi tiết."""
    clicked = pyqtSignal(str)  # model_id
    test_requested = pyqtSignal(str)  # model_id

    def __init__(self, model_info: ModelInfo, is_active: bool = False, parent=None):
        super().__init__(parent)
        self.model_info = model_info
        self._is_active = is_active
        self._setup_ui()
        self._update_style()

    def _setup_ui(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(95)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Row 1: Provider icon + Name + Tier badge + Test button
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        prov = PROVIDER_DISPLAY.get(self.model_info.provider, {})
        name_label = QLabel(f"{prov.get('icon', '⚡')} {self.model_info.name}")
        name_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        name_label.setStyleSheet(f"color: {COLORS['text_primary']}; border: none; background: transparent;")
        row1.addWidget(name_label)

        # Release date
        if self.model_info.release_date:
            date_lbl = QLabel(self.model_info.release_date)
            date_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none; background: transparent;")
            row1.addWidget(date_lbl)

        row1.addStretch()

        tier = self.model_info.get_tier_display()
        tier_badge = QLabel(f"{tier['icon']} {tier['name']}")
        tier_badge.setStyleSheet(f"""
            background-color: {tier['color']}22;
            color: {tier['color']};
            border-radius: 8px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid {tier['color']}44;
        """)
        row1.addWidget(tier_badge)

        self._active_badge = QLabel("✅ Đang dùng")
        self._active_badge.setStyleSheet(f"""
            background-color: {COLORS['success']}22;
            color: {COLORS['success']};
            border-radius: 8px;
            padding: 4px 12px;
            font-size: 11px;
            font-weight: 600;
            border: 1px solid {COLORS['success']}44;
        """)
        self._active_badge.setVisible(self._is_active)
        row1.addWidget(self._active_badge)

        if self.model_info.is_recommended:
            rec_badge = QLabel("⭐ Khuyên dùng")
            rec_badge.setStyleSheet(f"""
                background-color: {COLORS['warning']}22;
                color: {COLORS['warning']};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 11px;
                font-weight: 600;
                border: 1px solid {COLORS['warning']}44;
            """)
            row1.addWidget(rec_badge)

        # Test button
        self._test_btn = QPushButton("🧪 Test")
        self._test_btn.setFixedSize(75, 28)
        self._test_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['accent_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 2px 8px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']}22;
                border-color: {COLORS['accent_secondary']};
            }}
        """)
        self._test_btn.clicked.connect(lambda: self.test_requested.emit(self.model_info.id))
        row1.addWidget(self._test_btn)

        layout.addLayout(row1)

        # Row 2: Description
        desc = QLabel(self.model_info.description)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; border: none; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Row 3: Specs — Price + Ratings + Capabilities
        row3 = QHBoxLayout()
        row3.setSpacing(12)

        price_text = self.model_info.get_price_display()
        price_lbl = QLabel(f"💰 {price_text}")
        price_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none; background: transparent;")
        row3.addWidget(price_lbl)

        # Rating bars
        ratings = [
            ("⚡", self.model_info.speed_rating, "Tốc độ"),
            ("🧠", self.model_info.quality_rating, "Chất lượng"),
            ("💵", self.model_info.cost_rating, "Tiết kiệm"),
        ]
        for icon, val, tip in ratings:
            stars = "●" * val + "○" * (5 - val)
            r_lbl = QLabel(f"{icon}{stars}")
            r_lbl.setToolTip(f"{tip}: {val}/5")
            r_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none; background: transparent;")
            row3.addWidget(r_lbl)

        # Capabilities
        caps = []
        if self.model_info.supports_vision:
            caps.append("👁️")
        if self.model_info.supports_tools:
            caps.append("🔧")
        if caps:
            cap_lbl = QLabel(" ".join(caps))
            cap_lbl.setToolTip("👁️ Vision | 🔧 Function Calling")
            cap_lbl.setStyleSheet(f"font-size: 12px; border: none; background: transparent;")
            row3.addWidget(cap_lbl)

        # Context length
        ctx = self.model_info.max_context
        ctx_display = f"{ctx // 1000}K" if ctx < 1000000 else f"{ctx // 1000000}M"
        ctx_lbl = QLabel(f"📝 {ctx_display}")
        ctx_lbl.setToolTip(f"Max context: {ctx:,} tokens")
        ctx_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; border: none; background: transparent;")
        row3.addWidget(ctx_lbl)

        row3.addStretch()
        layout.addLayout(row3)

    def _update_style(self):
        border_color = COLORS['accent_primary'] if self._is_active else COLORS['border']
        bg_color = COLORS['sidebar_active'] if self._is_active else COLORS['bg_surface']
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {bg_color};
                border: {'2px' if self._is_active else '1px'} solid {border_color};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {COLORS['accent_primary']};
                background-color: {COLORS['bg_surface_hover']};
            }}
        """)

    def set_active(self, is_active: bool):
        """Cập nhật trạng thái đang dùng mà không cần tạo lại Widget."""
        self._is_active = is_active
        self._active_badge.setVisible(is_active)
        self._update_style()

    def mousePressEvent(self, event):
        """Click vào card để chọn model."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.model_info.id)
        super().mousePressEvent(event)

    def set_test_state(self, state: str, message: str = ""):
        """Cập nhật trạng thái test trên button."""
        if state == "testing":
            self._test_btn.setText("⏳ Đang test...")
            self._test_btn.setToolTip("Đang gửi tin nhắn test tới API...")
            self._test_btn.setEnabled(False)
        elif state == "success":
            self._test_btn.setText("✅ OK")
            self._test_btn.setToolTip(f"Test thành công: {message}")
            self._test_btn.setEnabled(True)
            self._test_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['success']}22;
                    color: {COLORS['success']};
                    border: 1px solid {COLORS['success']};
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px 8px;
                }}
            """)
        elif state == "failed":
            self._test_btn.setText("❌ Lỗi")
            self._test_btn.setToolTip(f"Lỗi: {message}")
            self._test_btn.setEnabled(True)
            self._test_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['error']}22;
                    color: {COLORS['error']};
                    border: 1px solid {COLORS['error']};
                    border-radius: 6px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 2px 8px;
                }}
            """)
        elif state == "idle":
            self._test_btn.setText("🧪 Test")
            self._test_btn.setEnabled(True)


class SettingsDialog(QDialog):
    """Dialog cài đặt Multi-Provider toàn diện."""

    model_changed = pyqtSignal(str)  # model_id
    display_settings_changed = pyqtSignal()
    theme_changed = pyqtSignal()  # Emitted when theme or density changes

    def __init__(self, key_manager: KeyManager, ai_engine, config: dict,
                 state_manager=None, screen_analyzer=None, parent=None):
        super().__init__(parent)
        self.key_manager = key_manager
        self.ai_engine = ai_engine
        self.config = config
        self.state_manager = state_manager
        self.screen_analyzer = screen_analyzer
        self._check_workers = []
        self._init_start_time = None
        self._scanned_models = []
        self._scanned_provider = ""
        self._scanned_cards = {}

        self.setWindowTitle("⚙️ Cài đặt — AI Claw Multi-AI")
        self.setWindowFlags(
            self.windowFlags()
            | Qt.WindowType.WindowMaximizeButtonHint
            | Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setMinimumSize(900, 600)
        self.resize(1060, 780)
        self.setSizeGripEnabled(True)

        self._setup_ui()
        # KHÔNG gọi _load_data() ở đây — defer sau khi dialog hiện

    def showEvent(self, event):
        """Khi dialog hiện → bắt đầu load data (deferred) + cập nhật titlebar theme."""
        super().showEvent(event)
        apply_titlebar_theme(self)
        if not hasattr(self, '_data_loaded') or not self._data_loaded:
            self._data_loaded = True
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, self._deferred_load_data)

    def _deferred_load_data(self):
        """Load data sau khi UI đã hiện — tránh freeze."""
        import time
        start = time.time()
        try:
            self._load_data()
            elapsed = time.time() - start
            logger.info(f"[Settings] Data loaded in {elapsed:.2f}s")
        except Exception as e:
            logger.error(f"[Settings] CRITICAL: _load_data crashed: {e}", exc_info=True)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Title Header Bar
        header_bar = QFrame()
        header_bar.setObjectName("dialogHeader")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(14, 10, 14, 10)

        title = QLabel("⚙️ Cài đặt — AI Claw Multi-AI")
        title.setObjectName("dialogTitle")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        header_layout.addWidget(title)

        header_layout.addStretch()

        sub_tag = QLabel("Tự Động Hoá & Multi-Model")
        sub_tag.setObjectName("mutedDesc")
        header_layout.addWidget(sub_tag)

        layout.addWidget(header_bar)

        # Tạo tất cả tabs ngay (chỉ tạo container — KHÔNG load data)
        self._tabs = QTabWidget()
        self._tabs.addTab(self._create_models_tab(), "🤖 Chọn Mô Hình AI")
        self._tabs.addTab(self._create_api_tab(), "🔑 API Keys")
        self._tabs.addTab(self._create_display_tab(), "💬 Tuỳ chọn Hiển thị")
        self._tabs.addTab(self._create_screenshot_tab(), "📸 Screenshot")
        self._tabs.addTab(self._create_auth_tab(), "👤 Tài Khoản & Bảo Mật")
        self._tabs.addTab(self._create_general_tab(), "🔧 Cài đặt chung")
        layout.addWidget(self._tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        close_btn = QPushButton("Đóng")
        close_btn.setObjectName("closeDialogBtn")
        close_btn.setFixedSize(110, 38)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    # ============================================================
    # TAB 1: MODEL SELECTION
    # ============================================================

    def _create_models_tab(self) -> QWidget:
        """Tab chọn mô hình AI với phân loại tier."""
        tab = QWidget()
        tab.setObjectName("modelsTab")
        tab.setStyleSheet(f"QWidget#modelsTab {{ background-color: {COLORS['bg_primary']}; }}")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # === QUICK SELECT — Chọn nhanh theo phân hạng ===
        quick_group = QGroupBox("⚡ Chọn nhanh theo phân hạng")
        quick_layout = QHBoxLayout(quick_group)
        quick_layout.setSpacing(8)

        for tier_value in [ModelTier.CHEAPEST, ModelTier.BALANCED, ModelTier.MODERATE, ModelTier.BEST]:
            tier_info = TIER_DISPLAY[tier_value]
            btn = QPushButton(f"{tier_info['icon']} {tier_info['name']}")
            btn.setToolTip(tier_info['desc'])
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(42)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {tier_info['color']}1a;
                    color: {tier_info['color']};
                    border: 1px solid {tier_info['color']}44;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 13px;
                    padding: 0 18px;
                }}
                QPushButton:hover {{
                    background-color: {tier_info['color']}33;
                    border-color: {tier_info['color']};
                }}
            """)
            btn.clicked.connect(lambda _, t=tier_value: self._select_tier(t))
            quick_layout.addWidget(btn)

        layout.addWidget(quick_group)

        # === PROVIDER FILTER ===
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("Lọc theo nhà cung cấp:"))

        self._provider_filter = QComboBox()
        self._provider_filter.blockSignals(True)  # Block signals khi đang thêm items
        self._provider_filter.addItem("🌐 Tất cả", "")
        for prov in Provider:
            info = PROVIDER_DISPLAY.get(prov, {})
            if not info:
                continue
            # KHÔNG gọi DB ở đây — key_count sẽ được cập nhật sau trong _load_data
            self._provider_filter.addItem(f"{info['icon']} {info['name']}", prov)
        self._provider_filter.blockSignals(False)
        self._provider_filter.currentIndexChanged.connect(self._refresh_model_cards)
        self._provider_filter.setMinimumWidth(230)
        filter_row.addWidget(self._provider_filter)

        # Button: Quét models khả dụng theo key
        scan_btn = QPushButton("✨ Quét Models khả dụng theo Key")
        scan_btn.setToolTip("Truy vấn trực tiếp danh sách mô hình mà tài khoản / API Key hiện tại của bạn được phép dùng")
        scan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        scan_btn.setFixedHeight(34)
        scan_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_secondary']}1a;
                color: {COLORS['accent_secondary']};
                border: 1px solid {COLORS['accent_secondary']}44;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_secondary']};
                color: #ffffff;
                border-color: {COLORS['accent_secondary']};
            }}
        """)
        scan_btn.clicked.connect(self._scan_available_models)
        filter_row.addWidget(scan_btn)

        # Button: Test tất cả
        test_all_btn = QPushButton("🧪 Test Toàn Bộ")
        test_all_btn.setToolTip("Kiểm tra toàn bộ mô hình (đang hiển thị) có API Key")
        test_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_all_btn.setFixedHeight(34)
        test_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['success']}1a;
                color: {COLORS['success']};
                border: 1px solid {COLORS['success']}44;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 4px 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['success']};
                color: #ffffff;
                border-color: {COLORS['success']};
            }}
        """)
        test_all_btn.clicked.connect(self._test_all_models)
        filter_row.addWidget(test_all_btn)

        filter_row.addStretch()

        # Current model display
        self._current_model_label = QLabel("")
        self._current_model_label.setStyleSheet(f"""
            color: {COLORS['accent_primary']};
            font-size: 13px;
            font-weight: 600;
        """)
        filter_row.addWidget(self._current_model_label)

        layout.addLayout(filter_row)

        # === SEARCH & CUSTOM MODEL ROW ===
        search_row = QHBoxLayout()
        search_row.setSpacing(8)

        self._model_search_input = QLineEdit()
        self._model_search_input.setPlaceholderText("🔍 Tìm kiếm model theo tên, ID, hoặc tính năng (VD: flash, pro, claude, gpt, vision, deepseek, qwen...)...")
        self._model_search_input.setFixedHeight(36)
        self._model_search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 0 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent_primary']};
            }}
        """)
        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(150)
        self._search_timer.timeout.connect(self._refresh_model_cards)
        self._model_search_input.textChanged.connect(lambda: self._search_timer.start())
        search_row.addWidget(self._model_search_input, 1)

        # Clear search button
        clear_search_btn = QPushButton("✕")
        clear_search_btn.setToolTip("Xoá tìm kiếm")
        clear_search_btn.setFixedSize(36, 36)
        clear_search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_surface_hover']};
                color: {COLORS['text_primary']};
            }}
        """)
        clear_search_btn.clicked.connect(lambda: self._model_search_input.clear())
        search_row.addWidget(clear_search_btn)

        # Button: Nhập Model ID tuỳ chỉnh
        custom_model_btn = QPushButton("➕ Nhập Model ID")
        custom_model_btn.setToolTip("Nhập bất kỳ Model ID nào để sử dụng với API Key mặc định của Provider tương ứng")
        custom_model_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        custom_model_btn.setFixedHeight(36)
        custom_model_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']}1a;
                color: {COLORS['accent_primary']};
                border: 1px solid {COLORS['accent_primary']}44;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 0 14px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_primary']};
                color: #ffffff;
                border-color: {COLORS['accent_primary']};
            }}
        """)
        custom_model_btn.clicked.connect(self._open_custom_model_dialog)
        search_row.addWidget(custom_model_btn)

        layout.addLayout(search_row)

        # === MODEL CARDS SCROLL AREA ===
        self._models_scroll = QScrollArea()
        self._models_scroll.setWidgetResizable(True)
        self._models_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._models_scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")

        self._cards_container = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_container)
        self._cards_layout.setContentsMargins(0, 0, 8, 0)
        self._cards_layout.setSpacing(8)

        self._models_scroll.setWidget(self._cards_container)
        layout.addWidget(self._models_scroll, 1)

        # === BOTTOM BUTTONS ===
        bottom_row = QHBoxLayout()

        set_default_btn = QPushButton("⭐ Đặt làm mặc định")
        set_default_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        set_default_btn.setFixedHeight(38)
        set_default_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_primary_hover']});
                color: #ffffff;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 13px;
                padding: 6px 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {COLORS['accent_primary_hover']}, stop:1 {COLORS['accent_primary']});
            }}
            QPushButton:pressed {{
                background-color: {COLORS['accent_primary']};
            }}
        """)
        set_default_btn.clicked.connect(self._set_as_default)
        bottom_row.addWidget(set_default_btn)

        reload_btn = QPushButton("🔄 Tải lại Models")
        reload_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reload_btn.setFixedHeight(38)
        reload_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                font-weight: 500;
                font-size: 13px;
                padding: 6px 16px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_surface_hover']};
                border-color: {COLORS['accent_primary']};
            }}
        """)
        reload_btn.clicked.connect(self._reload_models)
        bottom_row.addWidget(reload_btn)

        bottom_row.addStretch()

        self._model_stats_label = QLabel("")
        self._model_stats_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        bottom_row.addWidget(self._model_stats_label)

        layout.addLayout(bottom_row)

        return tab

    def _refresh_model_cards(self):
        """Refresh danh sách model cards — grouped by provider, expandable."""
        import time
        t0 = time.time()

        # Clear existing
        self._model_cards = {}
        self._scanned_cards = {}
        while self._cards_layout.count() > 0:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # ProcessEvents sau khi clear để UI không đơ
        QApplication = __import__('PyQt6.QtWidgets', fromlist=['QApplication']).QApplication
        QApplication.processEvents()

        # Get filter & search query
        provider_filter = self._provider_filter.currentData()
        search_text = self._model_search_input.text().strip().lower() if hasattr(self, '_model_search_input') else ""

        if provider_filter:
            models = model_registry.get_models_by_provider(provider_filter)
        else:
            models = model_registry.get_all_models()

        if search_text:
            models = [
                m for m in models
                if search_text in m.id.lower()
                or search_text in m.name.lower()
                or search_text in m.description.lower()
                or search_text in m.provider.lower()
                or search_text in PROVIDER_DISPLAY.get(m.provider, {}).get('name', '').lower()
            ]

        current_model = self.ai_engine.model_name
        current_model_info = model_registry.get_model(current_model)
        current_provider = current_model_info.provider if current_model_info else self.ai_engine.provider

        # Sort by current_model, then recommended, then score
        tier_order = {ModelTier.BALANCED: 0, ModelTier.CHEAPEST: 1, ModelTier.MODERATE: 2, ModelTier.BEST: 3}
        models.sort(key=lambda m: (
            0 if m.id == current_model else 1,
            0 if m.is_recommended else 1,
            tier_order.get(m.tier, 9),
            -m.get_overall_score()
        ))

        # Group by provider
        from collections import OrderedDict
        grouped = OrderedDict()
        
        # Đảm bảo Provider của model mặc định nằm trên cùng
        if current_provider:
            grouped[current_provider] = []

        for model in models:
            if model.provider not in grouped:
                grouped[model.provider] = []
            grouped[model.provider].append(model)

        # Khi chọn "Tất cả": hiện 3 model/provider, nút expand xem hết (nếu đang search thì hiện toàn bộ)
        SHOW_INITIAL = 999 if (provider_filter or search_text) else 3

        card_count = 0

        for provider_key, provider_models in grouped.items():
            # Provider header
            if not provider_filter:
                prov_info = PROVIDER_DISPLAY.get(provider_key, {})
                model_count = len(provider_models)

                header_widget = QWidget()
                header_layout = QHBoxLayout(header_widget)
                header_layout.setContentsMargins(4, 8, 4, 2)
                header_layout.setSpacing(8)

                header_lbl = QLabel(f"{prov_info.get('icon', '⚡')} {prov_info.get('name', provider_key)} ({model_count})")
                header_lbl.setStyleSheet(f"""
                    color: {prov_info.get('color', COLORS['text_primary'])};
                    font-size: 14px;
                    font-weight: 700;
                """)
                header_layout.addWidget(header_lbl)
                header_layout.addStretch()

                self._cards_layout.addWidget(header_widget)

            # Determine how many to show initially
            show_count = min(SHOW_INITIAL, len(provider_models))

            # Render visible cards
            for model in provider_models[:show_count]:
                card = ModelCard(model, is_active=(model.id == current_model))
                card.clicked.connect(self._on_model_card_clicked)
                card.test_requested.connect(self._test_model)
                self._model_cards[model.id] = card
                self._cards_layout.addWidget(card)
                card_count += 1

            # Hidden cards container (expand)
            if len(provider_models) > SHOW_INITIAL:
                hidden_container = QWidget()
                hidden_layout = QVBoxLayout(hidden_container)
                hidden_layout.setContentsMargins(0, 0, 0, 0)
                hidden_layout.setSpacing(8)
                hidden_container.setVisible(False)

                for model in provider_models[SHOW_INITIAL:]:
                    card = ModelCard(model, is_active=(model.id == current_model))
                    card.clicked.connect(self._on_model_card_clicked)
                    card.test_requested.connect(self._test_model)
                    self._model_cards[model.id] = card
                    hidden_layout.addWidget(card)
                    card_count += 1

                self._cards_layout.addWidget(hidden_container)

                # Expand button
                remain = len(provider_models) - SHOW_INITIAL
                expand_btn = QPushButton(f"▼ Xem thêm {remain} model...")
                expand_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                expand_btn.setFixedHeight(28)
                expand_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        color: {COLORS['accent_secondary']};
                        border: 1px dashed {COLORS['border']};
                        border-radius: 6px;
                        font-size: 11px;
                        font-weight: 600;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['accent_secondary']}11;
                        border-color: {COLORS['accent_secondary']};
                    }}
                """)

                def toggle_expand(checked=False, container=hidden_container, btn=expand_btn, count=remain):
                    is_visible = container.isVisible()
                    container.setVisible(not is_visible)
                    if is_visible:
                        btn.setText(f"▼ Xem thêm {count} model...")
                    else:
                        btn.setText(f"▲ Thu gọn")

                expand_btn.clicked.connect(toggle_expand)
                self._cards_layout.addWidget(expand_btn)

            # processEvents sau mỗi provider group để UI responsive
            QApplication.processEvents()

        self._cards_layout.addStretch()

        # Nhóm mô hình lỗi (Error Group) - ẩn mặc định
        self._error_group_widget = QWidget()
        self._error_group_layout = QVBoxLayout(self._error_group_widget)
        self._error_group_layout.setContentsMargins(0, 16, 0, 0)
        self._error_group_layout.setSpacing(8)
        
        err_header = QLabel("❌ Các mô hình bị lỗi / không khả dụng")
        err_header.setStyleSheet(f"color: {COLORS['error']}; font-size: 14px; font-weight: 700;")
        self._error_group_layout.addWidget(err_header)
        
        self._error_group_widget.setVisible(False)
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, self._error_group_widget)

        # Nhóm mô hình vừa quét theo Key (Scanned Models Section)
        if hasattr(self, '_scanned_models') and self._scanned_models:
            self._render_scanned_models_section()

        # Update current model label
        current_info = model_registry.get_model(current_model)
        if current_info:
            prov = PROVIDER_DISPLAY.get(current_info.provider, {})
            self._current_model_label.setText(
                f"Đang dùng: {prov.get('icon', '')} {current_info.name}"
            )

        # Stats
        all_models = model_registry.get_all_models()
        providers_with_keys = self.key_manager.get_providers_with_keys()
        self._model_stats_label.setText(
            f"Tổng: {len(all_models)} mô hình | "
            f"Providers có key: {len(providers_with_keys)}/{model_registry.get_provider_count()}"
        )

        elapsed = time.time() - t0
        logger.info(f"[Settings] _refresh_model_cards: {card_count} cards in {elapsed:.2f}s")

    def _render_scanned_models_section(self):
        """Hiển thị danh sách các model vừa quét được từ API Key bên dưới danh sách model."""
        if not hasattr(self, '_scanned_models') or not self._scanned_models:
            return

        provider = self._scanned_provider or self.ai_engine.provider
        prov_info = PROVIDER_DISPLAY.get(provider, {})
        current_model = self.ai_engine.model_name
        search_text = self._model_search_input.text().strip().lower() if hasattr(self, '_model_search_input') else ""

        models_to_render = self._scanned_models
        if search_text:
            models_to_render = [
                m for m in self._scanned_models
                if search_text in m.get("id", "").lower()
                or search_text in m.get("name", "").lower()
                or search_text in m.get("description", "").lower()
                or search_text in provider.lower()
                or search_text in prov_info.get("name", "").lower()
            ]

        if not models_to_render and search_text:
            return

        self._scanned_group_widget = QWidget()
        layout = QVBoxLayout(self._scanned_group_widget)
        layout.setContentsMargins(0, 16, 0, 8)
        layout.setSpacing(8)

        # Header Frame
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['accent_secondary']}22, stop:1 {COLORS['bg_surface']});
                border: 1px solid {COLORS['accent_secondary']}44;
                border-radius: 8px;
                padding: 6px;
            }}
        """)
        h_layout = QHBoxLayout(hdr_frame)
        h_layout.setContentsMargins(10, 6, 10, 6)

        title_lbl = QLabel(f"✨ <b>Mô hình khả dụng từ API Key</b> — {prov_info.get('icon', '⚡')} {prov_info.get('name', provider)} ({len(models_to_render)} models)")
        title_lbl.setTextFormat(Qt.TextFormat.RichText)
        title_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        h_layout.addWidget(title_lbl)

        h_layout.addStretch()

        hide_btn = QPushButton("✕ Ẩn danh sách quét")
        hide_btn.setFixedSize(130, 26)
        hide_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        hide_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_muted']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']}22;
                color: {COLORS['error']};
                border-color: {COLORS['error']};
            }}
        """)
        hide_btn.clicked.connect(self._clear_scanned_models)
        h_layout.addWidget(hide_btn)

        layout.addWidget(hdr_frame)

        self._scanned_cards = {}
        for m in models_to_render:
            m_id = m.get("id", "")
            is_active = (m_id == current_model)
            card = ScannedModelCard(m, provider, is_active=is_active)
            card.use_requested.connect(self._activate_scanned_model)
            card.test_requested.connect(self._test_model)
            card.default_requested.connect(self._set_scanned_as_default)
            self._scanned_cards[m_id] = card
            layout.addWidget(card)

        # Chèn trước stretch cuối cùng
        insert_idx = max(0, self._cards_layout.count() - 1)
        self._cards_layout.insertWidget(insert_idx, self._scanned_group_widget)

    def _open_custom_model_dialog(self):
        """Mở dialog cho phép nhập bất kỳ Model ID nào để sử dụng với API Key mặc định của Provider tương ứng."""
        dlg = QDialog(self)
        dlg.setWindowTitle("➕ Thêm & Sử Dụng Model ID Tuỳ Chỉnh")
        dlg.resize(480, 260)
        dlg.setStyleSheet(f"background-color: {COLORS['bg_primary']}; color: {COLORS['text_primary']};")

        d_layout = QVBoxLayout(dlg)
        d_layout.setContentsMargins(20, 20, 20, 20)
        d_layout.setSpacing(14)

        info_lbl = QLabel(
            "Nhập tên / ID mô hình bất kỳ. Hệ thống sẽ tự động liên kết và dùng <b>API Key mặc định</b> của Nhà cung cấp tương ứng."
        )
        info_lbl.setTextFormat(Qt.TextFormat.RichText)
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; line-height: 1.4;")
        d_layout.addWidget(info_lbl)

        # Provider selection
        p_row = QHBoxLayout()
        p_label = QLabel("Nhà cung cấp:")
        p_label.setFixedWidth(110)
        p_row.addWidget(p_label)
        p_combo = QComboBox()
        for prov in Provider:
            info = PROVIDER_DISPLAY.get(prov, {})
            if info:
                p_combo.addItem(f"{info['icon']} {info['name']}", prov)
        
        # Pre-select based on current filter or engine provider
        cur_prov = self._provider_filter.currentData() or self.ai_engine.provider
        idx = p_combo.findData(cur_prov)
        if idx >= 0:
            p_combo.setCurrentIndex(idx)
        p_row.addWidget(p_combo, 1)
        d_layout.addLayout(p_row)

        # Model ID Input
        m_row = QHBoxLayout()
        m_label = QLabel("Model ID:")
        m_label.setFixedWidth(110)
        m_row.addWidget(m_label)
        m_input = QLineEdit()
        m_input.setPlaceholderText("VD: gemini-2.5-flash, gpt-4.5-preview, claude-3-7-sonnet-20250219...")
        m_input.setFixedHeight(36)
        m_row.addWidget(m_input, 1)
        d_layout.addLayout(m_row)

        # Tự động nhận diện Provider khi người dùng gõ Model ID
        def on_mid_changed(text):
            detected = model_registry.detect_provider_from_model_id(text)
            if detected:
                c_idx = p_combo.findData(detected)
                if c_idx >= 0:
                    p_combo.setCurrentIndex(c_idx)

        m_input.textChanged.connect(on_mid_changed)

        d_layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Huỷ")
        cancel_btn.setFixedHeight(34)
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(dlg.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("🚀 Sử Dụng Ngay")
        save_btn.setObjectName("primaryButton")
        save_btn.setFixedHeight(34)
        save_btn.setFixedWidth(140)
        
        def do_save():
            mid = m_input.text().strip()
            if not mid:
                toast_warning("Vui lòng nhập Model ID!", dlg)
                return
            sel_prov = p_combo.currentData()
            model_registry.register_dynamic_model(mid, sel_prov, name=mid, description="Mô hình tuỳ chỉnh do người dùng nhập")
            dlg.accept()
            self._on_model_card_clicked(mid)
            self._refresh_model_cards()

        save_btn.clicked.connect(do_save)
        btn_row.addWidget(save_btn)
        d_layout.addLayout(btn_row)

        dlg.exec()

    def _clear_scanned_models(self):
        """Xoá danh sách models đã quét khỏi view."""
        self._scanned_models = []
        if hasattr(self, '_scanned_group_widget') and self._scanned_group_widget:
            self._scanned_group_widget.setVisible(False)
            self._scanned_group_widget.deleteLater()
            self._scanned_group_widget = None
        self._scanned_cards = {}

    def _activate_scanned_model(self, model_id: str, provider: str):
        """Kích hoạt và sử dụng model được quét từ API Key."""
        model_registry.register_dynamic_model(model_id, provider)
        self._on_model_card_clicked(model_id)

    def _set_scanned_as_default(self, model_id: str, provider: str):
        """Đặt model được quét làm mặc định."""
        model_registry.register_dynamic_model(model_id, provider)
        model_registry.set_default_model(model_id)
        if hasattr(self, 'state_manager'):
            self.state_manager.set_app_setting("default_model", model_id)
        self.ai_engine.set_model(model_id)
        self.model_changed.emit(model_id)
        
        # Cập nhật UI
        for c_id, card in getattr(self, '_model_cards', {}).items():
            card.set_active(c_id == model_id)
        for c_id, card in getattr(self, '_scanned_cards', {}).items():
            card.set_active(c_id == model_id)
            
        prov_info = PROVIDER_DISPLAY.get(provider, {})
        if hasattr(self, '_current_model_label'):
            self._current_model_label.setText(f"Mô hình đang chọn: {prov_info.get('icon', '')} {model_id}")
            
        toast_success(f"🌟 Đã đặt {model_id} làm mô hình mặc định.", self)

    def _test_model(self, model_id: str):
        """Test model có hoạt động không."""
        model_info = model_registry.get_model(model_id)
        provider = model_info.provider if model_info else (self._scanned_provider or self.ai_engine.provider)
        if not model_info:
            model_info = model_registry.register_dynamic_model(model_id, provider)

        # Check key
        active_key = self.key_manager.get_active_key(provider)
        if not active_key:
            prov = PROVIDER_DISPLAY.get(provider, {})
            toast_warning(f"Chưa có API Key cho {prov.get('name', '')}. Thêm key trước.", self)
            return

        toast_info(f"🧪 Đang test {model_info.name}...", self)

        if hasattr(self, '_scanned_cards') and model_id in self._scanned_cards:
            self._scanned_cards[model_id].set_test_state("testing")
        if hasattr(self, '_model_cards') and model_id in self._model_cards:
            self._model_cards[model_id].set_test_state("testing")

        worker = ModelTestWorker(self.ai_engine, model_id)
        worker.result_ready.connect(self._on_test_result)
        self._check_workers.append(worker)
        worker.start()

    def _on_test_result(self, model_id: str, success: bool, message: str):
        """Handle kết quả test model."""
        model_info = model_registry.get_model(model_id)
        name = model_info.name if model_info else model_id
        if hasattr(self, '_scanned_cards') and model_id in self._scanned_cards:
            self._scanned_cards[model_id].set_test_state("success" if success else "failed", message)
        if hasattr(self, '_model_cards') and model_id in self._model_cards:
            self._handle_test_result(model_id, success, message)

        if success:
            toast_success(f"🧪 {name}: {message}", self)
        else:
            toast_error(f"🧪 {name}: {message}", self)

    def _on_model_card_clicked(self, model_id: str):
        """Khi click vào model card hoặc nút sử dụng → kích hoạt model."""
        model_info = model_registry.get_model(model_id)
        provider = model_info.provider if model_info else (self._scanned_provider or self.ai_engine.provider)
        if not model_info:
            model_info = model_registry.register_dynamic_model(model_id, provider)

        # Kiểm tra có key cho provider không
        active_key = self.key_manager.get_active_key(provider)
        if not active_key:
            prov_info = PROVIDER_DISPLAY.get(provider, {})
            reply = QMessageBox.question(
                self, "Chưa có API Key",
                f"Bạn chưa có API key cho {prov_info.get('name', provider)}.\n\n"
                f"Chuyển sang tab 'API Keys' để thêm key?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Switch to API tab
                if hasattr(self, '_tabs'):
                    self._tabs.setCurrentIndex(1)
            return

        # Kích hoạt model
        self.ai_engine.set_model(model_id)
        if hasattr(self, 'state_manager'):
            self.state_manager.set_app_setting("default_model", model_id)
            
        # Cập nhật UI mà không cần tải lại toàn bộ
        for c_id, card in getattr(self, '_model_cards', {}).items():
            card.set_active(c_id == model_id)
        for c_id, card in getattr(self, '_scanned_cards', {}).items():
            card.set_active(c_id == model_id)
            
        prov_info = PROVIDER_DISPLAY.get(provider, {})
        if hasattr(self, '_current_model_label'):
            self._current_model_label.setText(f"Mô hình đang chọn: {prov_info.get('icon', '')} {model_info.name}")
            
        self.model_changed.emit(model_id)
        toast_success(f"🚀 Đã chuyển sang mô hình: {model_info.name}", self)
        logger.info(f"[Settings] Đã chuyển sang: {prov_info.get('icon', '')} {model_info.name}")

    def _select_tier(self, tier: str):
        """Chọn nhanh model theo tier."""
        # Ưu tiên provider đang có key
        providers_with_keys = self.key_manager.get_providers_with_keys()
        
        # Tìm model theo tier, ưu tiên provider có key
        models = model_registry.get_models_by_tier(tier)
        if not models:
            toast_info("Không tìm thấy mô hình phù hợp.", self)
            return

        # Ưu tiên: recommended > có key > overall score
        def sort_key(m):
            has_key = 1 if m.provider in providers_with_keys else 0
            return (-int(m.is_recommended), -has_key, -m.get_overall_score())

        models.sort(key=sort_key)
        best = models[0]

        # Kiểm tra key
        if best.provider not in providers_with_keys:
            # Tìm model cùng tier nhưng có key
            for m in models:
                if m.provider in providers_with_keys:
                    best = m
                    break

        if best.provider not in providers_with_keys:
            prov = PROVIDER_DISPLAY.get(best.provider, {})
            toast_warning(
                f"Cần API Key — Model phù hợp nhất: {best.name} ({prov.get('name', '')}). Vui lòng thêm key.",
                self
            )
            return

        self.ai_engine.set_model(best.id)
        if hasattr(self, 'state_manager'):
            self.state_manager.set_app_setting("default_model", best.id)
            
        # Cập nhật UI mà không cần tải lại toàn bộ
        for c_id, card in getattr(self, '_model_cards', {}).items():
            card.set_active(c_id == best.id)
            
        prov_info = PROVIDER_DISPLAY.get(best.provider, {})
        if hasattr(self, '_current_model_label'):
            self._current_model_label.setText(f"Mô hình đang chọn: {prov_info.get('icon', '')} {best.name}")
            
        self.model_changed.emit(best.id)

        tier_info = TIER_DISPLAY.get(tier, {})
        toast_success(
            f"{tier_info.get('icon', '')} {tier_info.get('name', tier)} — {best.get_display_name()}",
            self
        )

    def _set_as_default(self):
        """Đặt model hiện tại làm mặc định."""
        current = self.ai_engine.model_name
        model_registry.set_default_model(current)
        if hasattr(self, 'state_manager'):
            self.state_manager.set_app_setting("default_model", current)
        info = model_registry.get_model(current)
        name = info.name if info else current
        toast_success(f"⭐ Đã đặt {name} làm mô hình mặc định.", self)

    def _test_model(self, model_id: str):
        """Test kết nối và tính hợp lệ của model và API Key."""
        info = model_registry.get_model(model_id)
        model_name = info.name if info else model_id
        provider = info.provider if info else Provider.GEMINI
        prov_info = PROVIDER_DISPLAY.get(provider, {})
        prov_name = prov_info.get("name", provider)

        # 1. Kiểm tra xem đã có API Key chưa
        active_key = self.key_manager.get_active_key(provider)
        if not active_key:
            toast_warning(
                f"⚠️ Chưa có API Key cho {prov_name}!\nVui lòng vào tab '🔑 API Keys' để thêm key trước khi test.",
                self
            )
            return

        # Cập nhật state trên card button
        if hasattr(self, '_model_cards') and model_id in self._model_cards:
            self._model_cards[model_id].set_test_state("testing")

        toast_info(f"⏳ Đang gửi request test tới {model_name}...", self)

        # 2. Khởi chạy ModelTestWorker trên QThread
        self._test_worker = ModelTestWorker(self.ai_engine, model_id, self)
        self._test_worker.result_ready.connect(
            lambda mid, ok, msg: self._on_model_test_result(mid, ok, msg, model_name, prov_name, active_key)
        )
        self._test_worker.start()

    def _on_model_test_result(self, model_id: str, success: bool, message: str, model_name: str, prov_name: str, key: str):
        """Hiển thị kết quả test chi tiết."""
        # Cập nhật button trên card
        if hasattr(self, '_model_cards') and model_id in self._model_cards:
            self._handle_test_result(model_id, success, message)

        masked_key = f"...{key[-8:]}" if len(key) >= 8 else key
        if success:
            toast_success(
                f"🎉 TEST THÀNH CÔNG!\n• Mô hình: {model_name}\n• Nhà cung cấp: {prov_name}\n• Key: {masked_key} (Đang hoạt động tốt)\n• {message}",
                self
            )
        else:
            toast_error(
                f"❌ TEST THẤT BẠI!\n• Mô hình: {model_name}\n• Nhà cung cấp: {prov_name}\n• Key: {masked_key}\n• Chi tiết lỗi: {message}",
                self
            )

    def _test_all_models(self):
        """Test tất cả mô hình đang hiển thị và có API Key."""
        models_to_test = []
        for model_id, card in self._model_cards.items():
            if card.isVisible():
                info = model_registry.get_model(model_id)
                if info and self.key_manager.get_active_key(info.provider):
                    models_to_test.append(model_id)
                        
        if not models_to_test:
            toast_warning("Không có mô hình nào khả dụng để test (chưa có API Key).", self)
            return
            
        reply = QMessageBox.question(
            self, "Xác nhận Test Toàn Bộ",
            f"Hệ thống sẽ test tuần tự {len(models_to_test)} mô hình.\nViệc này có thể mất vài phút. Bạn có muốn tiếp tục?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
            
        toast_info(f"🚀 Bắt đầu test {len(models_to_test)} mô hình...", self)
        
        self._bulk_test_worker = BulkTestWorker(self.ai_engine, models_to_test, self)
        self._bulk_test_worker.test_started.connect(
            lambda mid: self._model_cards[mid].set_test_state("testing") if mid in self._model_cards else None
        )
        self._bulk_test_worker.test_result_ready.connect(
            lambda mid, ok, msg: self._handle_test_result(mid, ok, msg) if mid in self._model_cards else None
        )
        self._bulk_test_worker.finished_all.connect(
            lambda: toast_success("🎉 Đã hoàn tất test toàn bộ mô hình!", self)
        )
        self._bulk_test_worker.start()

    def _handle_test_result(self, model_id: str, success: bool, message: str):
        card = self._model_cards.get(model_id)
        if not card:
            return
            
        card.set_test_state("success" if success else "failed", message)
        
        if not success and hasattr(self, '_error_group_layout'):
            # Chuyển thẻ model vào nhóm lỗi
            self._error_group_widget.setVisible(True)
            self._error_group_layout.addWidget(card)

    def _reload_models(self):
        """Tải lại danh sách models."""
        model_registry.reload_models()
        self._refresh_model_cards()
        count = model_registry.get_model_count()
        providers = model_registry.get_provider_count()
        toast_success(f"🔄 Đã tải {count} models từ {providers} providers", self)

    def _scan_available_models(self):
        """Quét và liệt kê danh sách models khả dụng trực tiếp từ API của Provider."""
        provider = self._provider_filter.currentData() or self.ai_engine.provider
        prov_info = PROVIDER_DISPLAY.get(provider, {})
        prov_name = prov_info.get("name", provider)

        active_key = self.key_manager.get_active_key(provider)
        if not active_key:
            toast_warning(
                f"⚠️ Chưa có API Key cho {prov_name}!\nVui lòng vào tab '🔑 API Keys' để thêm key trước khi quét models.",
                self
            )
            return

        toast_info(f"⏳ Đang kết nối tới API {prov_name} để quét danh sách models khả dụng...", self)

        self._scan_worker = FetchLiveModelsWorker(self.ai_engine, provider, self)
        self._scan_worker.models_ready.connect(self._on_live_models_ready)
        self._scan_worker.error_occurred.connect(self._on_live_models_error)
        self._scan_worker.start()

    def _on_live_models_ready(self, provider: str, models: list):
        if not models:
            toast_warning("Không tìm thấy model nào từ API hoặc API Key không đủ quyền.", self)
            return
        
        # Đăng ký dynamic các models mới vào registry
        for m in models:
            m_id = m.get("id", "")
            if m_id:
                model_registry.register_dynamic_model(
                    m_id, provider,
                    name=m.get("name", m_id),
                    description=m.get("description", "")
                )

        self._scanned_models = models
        self._scanned_provider = provider
        self._refresh_model_cards()

        # Cuộn xuống danh sách vừa quét trong scroll area
        if hasattr(self, '_models_scroll') and self._models_scroll:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(150, lambda: self._models_scroll.verticalScrollBar().setValue(
                self._models_scroll.verticalScrollBar().maximum()
            ))

        toast_success(f"🎉 Đã tìm thấy {len(models)} mô hình khả dụng! Danh sách đã hiển thị bên dưới.", self)
        
        # Mở popup chi tiết đồng thời
        dlg = AvailableModelsDialog(provider, models, self.ai_engine, self)
        dlg.model_selected.connect(self._on_model_card_clicked)
        dlg.exec()

    def _on_live_models_error(self, provider: str, error_msg: str):
        toast_error(f"❌ Lỗi quét models từ API: {error_msg[:120]}", self)

    def _copy_key(self, api_key: str):
        """Copy 1 key vào clipboard."""
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(api_key)
        toast_info(f"📋 Đã copy key ...{api_key[-8:]}", self)

    def _copy_all_keys(self):
        """Copy tất cả keys vào clipboard."""
        from PyQt6.QtWidgets import QApplication
        keys = self.key_manager.get_all_keys()
        if not keys:
            toast_warning("Chưa có key nào.", self)
            return
        lines = []
        for k in keys:
            prov = PROVIDER_DISPLAY.get(k.get("provider", ""), {}).get("name", "?")
            lines.append(f"[{prov}] {k['api_key']}")
        QApplication.clipboard().setText("\n".join(lines))
        toast_success(f"📋 Đã copy {len(keys)} keys vào clipboard", self)

    # ============================================================
    # TAB 2: API KEYS
    # ============================================================

    def _create_api_tab(self) -> QWidget:
        """Tab quản lý API Keys đa provider."""
        tab = QWidget()
        tab.setObjectName("apiTab")
        tab.setStyleSheet(f"QWidget#apiTab {{ background-color: {COLORS['bg_primary']}; }}")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Add key section
        add_group = QGroupBox("Thêm API Key")
        add_layout = QVBoxLayout(add_group)

        # Provider selector
        prov_row = QHBoxLayout()
        prov_row.addWidget(QLabel("Nhà cung cấp:"))

        self._add_provider_combo = QComboBox()
        for prov in Provider:
            info = PROVIDER_DISPLAY.get(prov, {})
            if not info:
                continue
            self._add_provider_combo.addItem(f"{info['icon']} {info['name']}", prov)
        self._add_provider_combo.setMinimumWidth(200)
        self._add_provider_combo.currentIndexChanged.connect(self._update_key_placeholder)
        prov_row.addWidget(self._add_provider_combo)
        prov_row.addStretch()
        add_layout.addLayout(prov_row)

        # Key input
        key_row = QHBoxLayout()
        self._key_input = QTextEdit()
        self._key_input.setPlaceholderText("Nhập API Key (mỗi dòng 1 key)...\nVD: AIzaSyxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        self._key_input.setMaximumHeight(70)
        key_row.addWidget(self._key_input)

        btn_col = QVBoxLayout()
        add_btn = QPushButton("➕ Thêm")
        add_btn.setObjectName("primaryButton")
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.clicked.connect(self._add_keys)
        btn_col.addWidget(add_btn)

        reset_btn = QPushButton("🔄 Reset Quota")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self._reset_quotas)
        btn_col.addWidget(reset_btn)
        btn_col.addStretch()

        key_row.addLayout(btn_col)
        add_layout.addLayout(key_row)

        layout.addWidget(add_group)

        # Key table
        keys_group = QGroupBox("Danh sách API Keys (Tất cả providers)")
        keys_layout = QVBoxLayout(keys_group)

        self._keys_table = QTableWidget()
        self._keys_table.setColumnCount(6)
        self._keys_table.setHorizontalHeaderLabels(["Provider", "API Key", "Trạng thái", "Requests", "Active", "Hành động"])
        self._keys_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._keys_table.horizontalHeader().resizeSection(0, 140)
        self._keys_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self._keys_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._keys_table.horizontalHeader().resizeSection(2, 110)
        self._keys_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._keys_table.horizontalHeader().resizeSection(3, 70)
        self._keys_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._keys_table.horizontalHeader().resizeSection(4, 50)
        self._keys_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._keys_table.horizontalHeader().resizeSection(5, 150)
        self._keys_table.setAlternatingRowColors(True)
        self._keys_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._keys_table.setStyleSheet(f"QTableWidget {{ background-color: {COLORS['bg_surface']}; color: {COLORS['text_primary']}; gridline-color: {COLORS['border']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}")
        keys_layout.addWidget(self._keys_table)

        # Copy all keys button
        copy_row = QHBoxLayout()
        copy_all_btn = QPushButton("📋 Copy tất cả Keys")
        copy_all_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_all_btn.clicked.connect(self._copy_all_keys)
        copy_row.addWidget(copy_all_btn)
        copy_row.addStretch()
        keys_layout.addLayout(copy_row)

        layout.addWidget(keys_group)

        # Quota Summary Section
        quota_group = QGroupBox("📊 Thống kê sử dụng Quota")
        quota_layout = QVBoxLayout(quota_group)
        self._quota_summary_label = QLabel("Đang tải thông tin quota...")
        self._quota_summary_label.setWordWrap(True)
        self._quota_summary_label.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            font-size: 13px;
            padding: 8px;
            background: {COLORS['bg_surface']};
            border: 1px solid {COLORS['border']};
            border-radius: 8px;
        """)
        quota_layout.addWidget(self._quota_summary_label)
        layout.addWidget(quota_group)

        return tab

    def _update_key_placeholder(self):
        """Cập nhật placeholder theo provider được chọn."""
        provider = self._add_provider_combo.currentData()
        info = PROVIDER_DISPLAY.get(provider, {})
        prefix = info.get("key_prefix", "")
        name = info.get("name", "")
        env_var = info.get("key_env", "")
        self._key_input.setPlaceholderText(
            f"Nhập {name} API Key (mỗi dòng 1 key)...\n"
            f"Prefix: {prefix}xxx...\n"
            f"Hoặc set biến môi trường: {env_var}"
        )

    # ============================================================
    # TAB 3: DISPLAY SETTINGS
    # ============================================================

    def _create_display_tab(self) -> QWidget:
        """Tab tuỳ chọn hiển thị Chat + Theme + Density."""
        tab = QWidget()
        tab.setObjectName("displayTab")
        tab.setStyleSheet(f"QWidget#displayTab {{ background-color: {COLORS['bg_primary']}; }}")

        # Dùng ScrollArea vì tab này dài
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: transparent; }}")
        inner = QWidget()
        inner.setObjectName("displayInner")
        inner.setStyleSheet(f"QWidget#displayInner {{ background-color: {COLORS['bg_primary']}; }}")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # ===== 0. Giao diện sáng / tối (Theme) =====
        theme_group = QGroupBox("🎨 Giao diện (Theme)")
        theme_layout = QVBoxLayout(theme_group)
        theme_layout.setSpacing(8)

        current_theme = self.state_manager.get_app_setting("app_theme", "dark") if self.state_manager else "dark"
        self._theme_btn_group = QButtonGroup(self)

        theme_options = [
            ("dark", "🌙 Giao diện tối (Dark Mode — MẶC ĐỊNH)",
             "Nền tối, dễ chịu cho mắt, phù hợp làm việc ban đêm."),
            ("light", "☀️ Giao diện sáng (Light Mode)",
             "Nền trắng sáng sủa, rõ ràng, phù hợp ban ngày.")
        ]

        self._theme_radios = {}
        for t_key, t_title, t_desc in theme_options:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)

            radio = QRadioButton(t_title)
            radio.setChecked(current_theme == t_key)
            radio.toggled.connect(lambda checked: self._on_theme_setting_changed() if checked else None)
            self._theme_btn_group.addButton(radio)
            self._theme_radios[t_key] = radio

            desc_lbl = QLabel(t_desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")

            row_layout.addWidget(radio)
            row_layout.addWidget(desc_lbl)
            theme_layout.addWidget(row_widget)

        layout.addWidget(theme_group)

        # ===== 0b. Mật độ hiển thị (UI Density) =====
        density_group = QGroupBox("📐 Mật độ hiển thị (UI Density)")
        density_layout = QVBoxLayout(density_group)
        density_layout.setSpacing(8)

        current_density = self.state_manager.get_app_setting("ui_density", DENSITY_MATERIAL) if self.state_manager else DENSITY_MATERIAL
        self._density_btn_group = QButtonGroup(self)

        density_options = [
            (DENSITY_MATERIAL, f"{DENSITY_CONFIG[DENSITY_MATERIAL]['icon']} {DENSITY_CONFIG[DENSITY_MATERIAL]['name']} (MẶC ĐỊNH)",
             DENSITY_CONFIG[DENSITY_MATERIAL]['desc']),
            (DENSITY_COMPACT, f"{DENSITY_CONFIG[DENSITY_COMPACT]['icon']} {DENSITY_CONFIG[DENSITY_COMPACT]['name']}",
             DENSITY_CONFIG[DENSITY_COMPACT]['desc']),
            (DENSITY_LITE_COMPACT, f"{DENSITY_CONFIG[DENSITY_LITE_COMPACT]['icon']} {DENSITY_CONFIG[DENSITY_LITE_COMPACT]['name']}",
             DENSITY_CONFIG[DENSITY_LITE_COMPACT]['desc']),
            (DENSITY_SUPER_COMPACT, f"{DENSITY_CONFIG[DENSITY_SUPER_COMPACT]['icon']} {DENSITY_CONFIG[DENSITY_SUPER_COMPACT]['name']}",
             DENSITY_CONFIG[DENSITY_SUPER_COMPACT]['desc']),
        ]

        self._density_radios = {}
        for d_key, d_title, d_desc in density_options:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)

            radio = QRadioButton(d_title)
            radio.setChecked(current_density == d_key)
            radio.toggled.connect(lambda checked: self._on_theme_setting_changed() if checked else None)
            self._density_btn_group.addButton(radio)
            self._density_radios[d_key] = radio

            desc_lbl = QLabel(d_desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")

            row_layout.addWidget(radio)
            row_layout.addWidget(desc_lbl)
            density_layout.addWidget(row_widget)

        layout.addWidget(density_group)

        # ===== 0c. Cỡ chữ hiển thị (Font Size) =====
        font_group = QGroupBox("🔤 Cỡ chữ hiển thị (Font Size)")
        font_layout = QVBoxLayout(font_group)
        font_layout.setSpacing(8)

        from ui.theme import (
            FONT_SIZE_SMALL, FONT_SIZE_SLIGHTLY_SMALL, FONT_SIZE_MEDIUM,
            FONT_SIZE_SLIGHTLY_LARGE, FONT_SIZE_LARGE, FONT_SIZE_EXTRA_LARGE,
            FONT_SIZE_CONFIG, set_font_size
        )

        current_font = self.state_manager.get_app_setting("app_font_size", FONT_SIZE_MEDIUM) if self.state_manager else FONT_SIZE_MEDIUM
        self._font_btn_group = QButtonGroup(self)

        font_options = [
            (FONT_SIZE_SMALL, f"{FONT_SIZE_CONFIG[FONT_SIZE_SMALL]['icon']} {FONT_SIZE_CONFIG[FONT_SIZE_SMALL]['name']} (11px)",
             FONT_SIZE_CONFIG[FONT_SIZE_SMALL]['desc']),
            (FONT_SIZE_SLIGHTLY_SMALL, f"{FONT_SIZE_CONFIG[FONT_SIZE_SLIGHTLY_SMALL]['icon']} {FONT_SIZE_CONFIG[FONT_SIZE_SLIGHTLY_SMALL]['name']} (12px)",
             FONT_SIZE_CONFIG[FONT_SIZE_SLIGHTLY_SMALL]['desc']),
            (FONT_SIZE_MEDIUM, f"{FONT_SIZE_CONFIG[FONT_SIZE_MEDIUM]['icon']} {FONT_SIZE_CONFIG[FONT_SIZE_MEDIUM]['name']} (13px — MẶC ĐỊNH)",
             FONT_SIZE_CONFIG[FONT_SIZE_MEDIUM]['desc']),
            (FONT_SIZE_SLIGHTLY_LARGE, f"{FONT_SIZE_CONFIG[FONT_SIZE_SLIGHTLY_LARGE]['icon']} {FONT_SIZE_CONFIG[FONT_SIZE_SLIGHTLY_LARGE]['name']} (15px)",
             FONT_SIZE_CONFIG[FONT_SIZE_SLIGHTLY_LARGE]['desc']),
            (FONT_SIZE_LARGE, f"{FONT_SIZE_CONFIG[FONT_SIZE_LARGE]['icon']} {FONT_SIZE_CONFIG[FONT_SIZE_LARGE]['name']} (17px)",
             FONT_SIZE_CONFIG[FONT_SIZE_LARGE]['desc']),
            (FONT_SIZE_EXTRA_LARGE, f"{FONT_SIZE_CONFIG[FONT_SIZE_EXTRA_LARGE]['icon']} {FONT_SIZE_CONFIG[FONT_SIZE_EXTRA_LARGE]['name']} (19px)",
             FONT_SIZE_CONFIG[FONT_SIZE_EXTRA_LARGE]['desc']),
        ]

        self._font_radios = {}
        for f_key, f_title, f_desc in font_options:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)

            radio = QRadioButton(f_title)
            radio.setChecked(current_font == f_key)
            radio.toggled.connect(lambda checked: self._on_theme_setting_changed() if checked else None)
            self._font_btn_group.addButton(radio)
            self._font_radios[f_key] = radio

            desc_lbl = QLabel(f_desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")

            row_layout.addWidget(radio)
            row_layout.addWidget(desc_lbl)
            font_layout.addWidget(row_widget)

        layout.addWidget(font_group)

        # ===== 1. Chế độ hiển thị văn bản (Text Render Mode) =====
        render_group = QGroupBox("🌿 Chế độ hiển thị nội dung tin nhắn (Message Render Mode)")
        render_layout = QVBoxLayout(render_group)
        render_layout.setSpacing(10)

        current_mode = self.state_manager.get_app_setting("chat_render_mode", "natural") if self.state_manager else "natural"

        self._render_btn_group = QButtonGroup(self)

        modes = [
            ("natural", "🌿 Dạng Văn bản tự nhiên (Khuyến nghị — MẶC ĐỊNH)",
             "Lọc sạch toàn bộ ký tự markdown thô (**chữ đậm**, ### tiêu đề, `code`...), câu từ suôn mượt, tự nhiên, êm dịu."),
            ("markdown", "🌟 Dạng Markdown chuẩn (Rich Text)",
             "Render đầy đủ cú pháp: in đậm thật, in nghiêng, code block có khung nền riêng biệt, danh sách bullet point tròn."),
            ("icon_rich", "✨ Dạng Text kèm icon sinh động",
             "Văn bản tự nhiên được tự động chèn thêm các icon trực quan sinh động theo từng đầu mục."),
            ("raw", "📄 Dạng Text thông thường (Nguyên bản)",
             "Giữ nguyên văn bản thô chưa qua xử lý.")
        ]

        self._mode_radios = {}
        for mode_key, title, desc in modes:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)

            radio = QRadioButton(title)
            radio.setChecked(current_mode == mode_key)
            radio.toggled.connect(lambda checked: self._on_display_setting_changed() if checked else None)
            self._render_btn_group.addButton(radio)
            self._mode_radios[mode_key] = radio

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")

            row_layout.addWidget(radio)
            row_layout.addWidget(desc_lbl)
            render_layout.addWidget(row_widget)

        layout.addWidget(render_group)

        # ===== 2. Kiểu bong bóng tin nhắn (Bubble Style) =====
        bubble_group = QGroupBox("💬 Kiểu bong bóng giao diện (Bubble Style)")
        bubble_layout = QVBoxLayout(bubble_group)
        bubble_layout.setSpacing(8)

        current_bubble = self.state_manager.get_app_setting("chat_bubble_style", "bubble") if self.state_manager else "bubble"
        self._bubble_btn_group = QButtonGroup(self)

        bubble_options = [
            ("bubble", "💬 Bong bóng Chat (ChatBubble hiện đại — MẶC ĐỊNH)",
             "Hộp thoại có avatar, bo góc hiện đại, phân biệt rõ User và AI."),
            ("flat", "📜 Dạng Văn bản phẳng (Compact Flat)",
             "Giao diện phẳng tối giản, không dùng bong bóng lớn, tiết kiệm tối đa diện tích hiển thị.")
        ]

        self._bubble_radios = {}
        for b_key, b_title, b_desc in bubble_options:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)

            radio = QRadioButton(b_title)
            radio.setChecked(current_bubble == b_key)
            radio.toggled.connect(lambda checked: self._on_display_setting_changed() if checked else None)
            self._bubble_btn_group.addButton(radio)
            self._bubble_radios[b_key] = radio

            desc_lbl = QLabel(b_desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")

            row_layout.addWidget(radio)
            row_layout.addWidget(desc_lbl)
            bubble_layout.addWidget(row_widget)

        layout.addWidget(bubble_group)

        # ===== 3. Live Preview =====
        preview_group = QGroupBox("👁️ Xem trước hiển thị trực tiếp (Live Preview)")
        preview_layout = QVBoxLayout(preview_group)

        self._preview_bubble_frame = QFrame()
        self._preview_bubble_layout = QVBoxLayout(self._preview_bubble_frame)
        self._preview_bubble_layout.setContentsMargins(14, 12, 14, 12)
        self._preview_bubble_layout.setSpacing(6)

        self._preview_sender_lbl = QLabel("🤖 AI Claw")
        self._preview_sender_lbl.setStyleSheet(f"color: {COLORS['accent_primary']}; font-size: 12px; font-weight: 700;")
        self._preview_bubble_layout.addWidget(self._preview_sender_lbl)

        self._preview_content_lbl = QLabel()
        self._preview_content_lbl.setWordWrap(True)
        self._preview_content_lbl.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px; line-height: 1.5;")
        self._preview_bubble_layout.addWidget(self._preview_content_lbl)

        preview_layout.addWidget(self._preview_bubble_frame)
        layout.addWidget(preview_group)

        self._update_preview()

        # ===== 4. Vị trí thông báo (Toast Notification Position) =====
        toast_group = QGroupBox("🔔 Vị trí thông báo (Toast Notification Position)")
        toast_layout = QVBoxLayout(toast_group)
        toast_layout.setSpacing(8)

        current_toast_pos = self.state_manager.get_app_setting("toast_position", "bottom-right") if self.state_manager else "bottom-right"
        self._toast_btn_group = QButtonGroup(self)
        self._toast_radios = {}

        toast_grid = QGridLayout()
        toast_grid.setSpacing(8)

        positions_list = [
            ("top-left", "↖️ Góc trái trên cùng", 0, 0),
            ("top-center", "⬆️ Giữa trên cùng", 0, 1),
            ("top-right", "↗️ Góc phải trên cùng", 0, 2),
            ("bottom-left", "↙️ Góc trái dưới cùng", 1, 0),
            ("bottom-center", "⬇️ Giữa dưới cùng", 1, 1),
            ("bottom-right", "↘️ Góc phải dưới cùng (MẶC ĐỊNH)", 1, 2),
        ]

        for p_key, p_title, r_idx, c_idx in positions_list:
            radio = QRadioButton(p_title)
            radio.setChecked(current_toast_pos == p_key)
            radio.toggled.connect(lambda checked: self._on_toast_pos_changed() if checked else None)
            self._toast_btn_group.addButton(radio)
            self._toast_radios[p_key] = radio
            toast_grid.addWidget(radio, r_idx, c_idx)

        toast_layout.addLayout(toast_grid)

        test_row = QHBoxLayout()
        test_toast_btn = QPushButton("🧪 Thử nghiệm vị trí thông báo")
        test_toast_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        test_toast_btn.setFixedHeight(30)
        test_toast_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']}1a;
                color: {COLORS['accent_primary']};
                border: 1px solid {COLORS['accent_primary']}44;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                padding: 0 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_primary']};
                color: #ffffff;
            }}
        """)
        test_toast_btn.clicked.connect(self._test_toast_notification)
        test_row.addWidget(test_toast_btn)
        test_row.addStretch()
        toast_layout.addLayout(test_row)

        layout.addWidget(toast_group)

        # ===== 5. Nút nổi truy cập nhanh (Floating Quick Access) =====
        float_group = QGroupBox("📌 Nút nổi truy cập nhanh (Floating Quick Access Widget)")
        float_layout = QVBoxLayout(float_group)
        float_layout.setSpacing(6)

        is_float_on = self.state_manager.get_app_setting("float_widget_enabled", "1") != "0" if self.state_manager else True
        self._float_widget_cb = QCheckBox("Hiển thị thanh nút nổi truy cập nhanh trên màn hình Desktop (Mặc định: Bật)")
        self._float_widget_cb.setChecked(is_float_on)
        self._float_widget_cb.toggled.connect(self._on_float_widget_toggled)
        float_layout.addWidget(self._float_widget_cb)

        float_desc = QLabel("Thanh nút nổi cho phép chụp ảnh màn hình, mở AI Chat và mở rộng cửa sổ ứng dụng từ bất kỳ đâu trên màn hình Desktop. Tự động làm mờ khi không dùng.")
        float_desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")
        float_desc.setWordWrap(True)
        float_layout.addWidget(float_desc)

        layout.addWidget(float_group)

        layout.addStretch()

        scroll.setWidget(inner)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab

    def _get_selected_render_mode(self) -> str:
        for mode_key, radio in self._mode_radios.items():
            if radio.isChecked():
                return mode_key
        return "natural"

    def _get_selected_bubble_style(self) -> str:
        for b_key, radio in self._bubble_radios.items():
            if radio.isChecked():
                return b_key
        return "bubble"

    def _on_display_setting_changed(self):
        render_mode = self._get_selected_render_mode()
        bubble_style = self._get_selected_bubble_style()

        if self.state_manager:
            self.state_manager.set_app_setting("chat_render_mode", render_mode)
            self.state_manager.set_app_setting("chat_bubble_style", bubble_style)

        self._update_preview()
        self.display_settings_changed.emit()

    def _get_selected_theme(self) -> str:
        for t_key, radio in self._theme_radios.items():
            if radio.isChecked():
                return t_key
        return "dark"

    def _get_selected_density(self) -> str:
        for d_key, radio in self._density_radios.items():
            if radio.isChecked():
                return d_key
        return DENSITY_MATERIAL

    def _get_selected_font_size(self) -> str:
        from ui.theme import FONT_SIZE_MEDIUM
        if hasattr(self, '_font_radios'):
            for f_key, radio in self._font_radios.items():
                if radio.isChecked():
                    return f_key
        return FONT_SIZE_MEDIUM

    def _on_theme_setting_changed(self):
        """Lưu và áp dụng theme/density/font size khi thay đổi nhanh, mượt."""
        if not self.state_manager:
            return

        theme = self._get_selected_theme()
        density = self._get_selected_density()
        font_size = self._get_selected_font_size()

        self.state_manager.set_app_setting("app_theme", theme)
        self.state_manager.set_app_setting("ui_density", density)
        self.state_manager.set_app_setting("app_font_size", font_size)

        # Áp dụng ngay
        from ui.theme import set_theme, set_density, set_font_size, build_stylesheet, apply_titlebar_theme
        set_theme(theme)
        set_density(density)
        set_font_size(font_size)

        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet())

        # Update Windows titlebar theme
        apply_titlebar_theme(self)

        # Update preview in display tab
        self._update_preview()

        self.theme_changed.emit()

    def _update_preview(self):
        render_mode = self._get_selected_render_mode()
        bubble_style = self._get_selected_bubble_style()

        from ui.theme import format_chat_content, get_chat_bubble_style, get_chat_flat_style

        if bubble_style == "flat":
            self._preview_bubble_frame.setStyleSheet(get_chat_flat_style(is_user=False))
        else:
            self._preview_bubble_frame.setStyleSheet(get_chat_bubble_style(is_user=False))

        sample_raw = (
            "Chào bạn! Tôi là **AI Claw** — Trợ lý Tự động hoá Thông minh.\n\n"
            "Tôi có thể giúp bạn:\n"
            "- **Tự động hoá thao tác** (click chuột, gõ phím, mở app)\n"
            "- **Tạo workflow tự động** từ yêu cầu tiếng Việt\n"
            "- **Xử lý file hàng loạt** và phân tích màn hình\n\n"
            "Bạn cần hỗ trợ công việc gì hôm nay?"
        )

        formatted_text, is_html = format_chat_content(sample_raw, render_mode=render_mode)
        if is_html:
            self._preview_content_lbl.setTextFormat(Qt.TextFormat.RichText)
        else:
            self._preview_content_lbl.setTextFormat(Qt.TextFormat.PlainText)
        self._preview_content_lbl.setText(formatted_text)

    def _on_toast_pos_changed(self):
        """Lưu vị trí thông báo toast."""
        if not hasattr(self, '_toast_radios') or not self.state_manager:
            return
        for p_key, radio in self._toast_radios.items():
            if radio.isChecked():
                self.state_manager.set_app_setting("toast_position", p_key)
                break

    def _test_toast_notification(self):
        """Bắn toast thử nghiệm vị trí."""
        toast_success("🔔 Thông báo thử nghiệm tại vị trí đã chọn!", self)

    def _on_float_widget_toggled(self, checked: bool):
        """Bật/tắt nút nổi truy cập nhanh (Floating Widget)."""
        if self.state_manager:
            self.state_manager.set_app_setting("float_widget_enabled", "1" if checked else "0")
        parent = self.parent()
        if parent and hasattr(parent, "toggle_floating_widget"):
            parent.toggle_floating_widget(checked)

    # ============================================================
    # TAB 4: SCREENSHOT SETTINGS
    # ============================================================

    def _create_screenshot_tab(self) -> QWidget:
        """Tab cài đặt chụp screenshot: chọn màn hình, định dạng ảnh, chất lượng."""
        tab = QWidget()
        tab.setObjectName("screenshotTab")
        tab.setStyleSheet(f"QWidget#screenshotTab {{ background-color: {COLORS['bg_primary']}; }}")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # ===== 1. Chọn màn hình chụp =====
        monitor_group = QGroupBox("🖥️ Chọn màn hình chụp (Monitor Selection)")
        monitor_layout = QVBoxLayout(monitor_group)
        monitor_layout.setSpacing(10)

        current_monitor = self.state_manager.get_app_setting("screenshot_monitor", "all") if self.state_manager else "all"

        self._monitor_btn_group = QButtonGroup(self)

        # Hiển thị số màn hình phát hiện được
        monitor_count = 1
        if self.screen_analyzer:
            monitor_count = self.screen_analyzer.get_monitor_count()

        monitor_info = QLabel(f"Phát hiện: {monitor_count} màn hình")
        monitor_info.setStyleSheet(f"color: {COLORS['accent_secondary']}; font-size: 12px; font-weight: 600;")
        monitor_layout.addWidget(monitor_info)

        monitor_modes = [
            ("all", "🖥️🖥️ Tất cả màn hình (MẶC ĐỊNH)",
             "Chụp toàn bộ các màn hình gộp lại thành 1 ảnh."),
            ("left", "◀️ Màn hình bên TRÁI",
             "Chỉ chụp màn hình có vị trí bên trái nhất."),
            ("right", "▶️ Màn hình bên PHẢI",
             "Chỉ chụp màn hình có vị trí bên phải nhất."),
            ("primary", "⭐ Màn hình chính (Primary)",
             "Chỉ chụp màn hình chính (màn hình số 1).")
        ]

        self._monitor_radios = {}
        for m_key, m_title, m_desc in monitor_modes:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)

            radio = QRadioButton(m_title)
            radio.setChecked(current_monitor == m_key)
            radio.toggled.connect(self._on_screenshot_setting_changed)
            self._monitor_btn_group.addButton(radio)
            self._monitor_radios[m_key] = radio

            # Disable left/right nếu chỉ có 1 màn hình
            if monitor_count <= 1 and m_key in ("left", "right"):
                radio.setEnabled(False)

            desc_lbl = QLabel(m_desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")

            row_layout.addWidget(radio)
            row_layout.addWidget(desc_lbl)
            monitor_layout.addWidget(row_widget)

        layout.addWidget(monitor_group)

        # ===== 2. Định dạng ảnh (Image Format) =====
        format_group = QGroupBox("🖼️ Định dạng ảnh gửi cho AI (Image Format)")
        format_layout = QVBoxLayout(format_group)
        format_layout.setSpacing(10)

        current_format = self.state_manager.get_app_setting("screenshot_format", "webp") if self.state_manager else "webp"

        self._format_btn_group = QButtonGroup(self)

        format_options = [
            ("webp", "🌟 WebP (Khuyến nghị — MẶC ĐỊNH)",
             "Nhẹ nhất, chất lượng tốt, tiết kiệm băng thông và token AI. Hỗ trợ bởi Gemini, OpenAI, Claude."),
            ("png", "📷 PNG (Không mất chất lượng)",
             "Lossless, không nén chất lượng nhưng file lớn hơn nhiều."),
            ("jpeg", "📸 JPEG (Nén mạnh)",
             "File nhỏ, phù hợp khi cần tiết kiệm tối đa. Không hỗ trợ trong suốt.")
        ]

        self._format_radios = {}
        for f_key, f_title, f_desc in format_options:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)

            radio = QRadioButton(f_title)
            radio.setChecked(current_format == f_key)
            radio.toggled.connect(self._on_screenshot_setting_changed)
            self._format_btn_group.addButton(radio)
            self._format_radios[f_key] = radio

            desc_lbl = QLabel(f_desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")

            row_layout.addWidget(radio)
            row_layout.addWidget(desc_lbl)
            format_layout.addWidget(row_widget)

        layout.addWidget(format_group)

        # ===== 3. Chất lượng ảnh (Image Quality) =====
        quality_group = QGroupBox("⚡ Chất lượng ảnh (Image Quality)")
        quality_layout = QVBoxLayout(quality_group)
        quality_layout.setSpacing(8)

        current_quality = int(self.state_manager.get_app_setting("screenshot_quality", "100")) if self.state_manager else 100

        quality_desc = QLabel("Chất lượng nén cho WebP và JPEG (không áp dụng cho PNG). 100% = chất lượng tối đa.")
        quality_desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        quality_desc.setWordWrap(True)
        quality_layout.addWidget(quality_desc)

        # Slider + SpinBox row
        slider_row = QHBoxLayout()
        slider_row.setSpacing(12)

        self._quality_slider = QSlider(Qt.Orientation.Horizontal)
        self._quality_slider.setRange(10, 100)
        self._quality_slider.setValue(current_quality)
        self._quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self._quality_slider.setTickInterval(10)
        self._quality_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {COLORS['bg_elevated']};
                height: 6px;
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['accent_primary']};
                width: 18px;
                height: 18px;
                margin: -6px 0;
                border-radius: 9px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['accent_primary_hover']};
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent_primary']};
                border-radius: 3px;
            }}
        """)
        slider_row.addWidget(self._quality_slider, 1)

        self._quality_spin = QSpinBox()
        self._quality_spin.setRange(10, 100)
        self._quality_spin.setValue(current_quality)
        self._quality_spin.setSuffix("%")
        self._quality_spin.setFixedWidth(80)
        self._quality_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 13px;
            }}
        """)
        slider_row.addWidget(self._quality_spin)

        quality_layout.addLayout(slider_row)

        # Sync slider <-> spinbox
        self._quality_slider.valueChanged.connect(self._quality_spin.setValue)
        self._quality_spin.valueChanged.connect(self._quality_slider.setValue)
        self._quality_slider.valueChanged.connect(self._on_screenshot_setting_changed)

        # Preset buttons
        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        preset_row.addWidget(QLabel("Đặt nhanh:"))

        for q_val, q_label in [(100, "100% (Tốt nhất)"), (85, "85% (Cân bằng)"), (60, "60% (Nhẹ)"), (30, "30% (Siêu nhẹ)")]:
            btn = QPushButton(q_label)
            btn.setFixedHeight(28)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_surface']};
                    color: {COLORS['text_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 2px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['accent_primary']};
                    color: {COLORS['text_primary']};
                }}
            """)
            btn.clicked.connect(lambda checked, v=q_val: self._set_quality_preset(v))
            preset_row.addWidget(btn)

        preset_row.addStretch()
        quality_layout.addLayout(preset_row)

        layout.addWidget(quality_group)

        layout.addStretch()
        return tab

    def _get_selected_monitor_mode(self) -> str:
        for m_key, radio in self._monitor_radios.items():
            if radio.isChecked():
                return m_key
        return "all"

    def _get_selected_image_format(self) -> str:
        for f_key, radio in self._format_radios.items():
            if radio.isChecked():
                return f_key
        return "webp"

    def _set_quality_preset(self, value: int):
        """Set quality từ preset button."""
        self._quality_slider.setValue(value)
        self._quality_spin.setValue(value)

    def _on_screenshot_setting_changed(self):
        """Lưu cài đặt screenshot khi thay đổi."""
        if not self.state_manager:
            return

        monitor_mode = self._get_selected_monitor_mode()
        image_format = self._get_selected_image_format()
        quality = self._quality_slider.value()

        self.state_manager.set_app_setting("screenshot_monitor", monitor_mode)
        self.state_manager.set_app_setting("screenshot_format", image_format)
        self.state_manager.set_app_setting("screenshot_quality", str(quality))

        # Áp dụng ngay cho screen_analyzer
        if self.screen_analyzer:
            self.screen_analyzer.set_monitor_mode(monitor_mode)
            self.screen_analyzer.set_image_format(image_format)
            self.screen_analyzer.set_image_quality(quality)

    # ============================================================
    # TAB 5: AUTHENTICATION & USER MANAGEMENT
    # ============================================================

    def _create_auth_tab(self) -> QWidget:
        """Tab Quản Lý Tài Khoản & Bảo Mật."""
        tab = QWidget()
        tab.setObjectName("authTab")
        tab.setStyleSheet(f"QWidget#authTab {{ background-color: {COLORS['bg_primary']}; }}")

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner = QWidget()
        inner.setObjectName("authInner")
        inner.setStyleSheet(f"QWidget#authInner {{ background-color: {COLORS['bg_primary']}; }}")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # 1. Bật/Tắt Xác Thực Đăng Nhập
        auth_switch_group = QGroupBox("🔒 Chính sách bảo mật & Xác thực")
        as_layout = QVBoxLayout(auth_switch_group)
        as_layout.setSpacing(8)

        is_auth = self.state_manager.is_auth_enabled() if self.state_manager else False

        self._auth_toggle_cb = QCheckBox("Bật xác thực đăng nhập khi mở ứng dụng (Mặc định: TẮT — không cần đăng nhập)")
        self._auth_toggle_cb.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        self._auth_toggle_cb.setChecked(is_auth)
        self._auth_toggle_cb.toggled.connect(self._on_auth_toggled)
        as_layout.addWidget(self._auth_toggle_cb)

        auth_desc = QLabel(
            "• Khi TẮT: Ứng dụng mở trực tiếp vào giao diện chính mà không cần nhập tài khoản.\n"
            "• Khi BẬT: Ứng dụng hiển thị màn hình đăng nhập bảo mật. Tài khoản quản trị ban đầu là admin / admin (không hiển thị gợi ý trên giao diện đăng nhập)."
        )
        auth_desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; line-height: 1.4; margin-left: 26px;")
        auth_desc.setWordWrap(True)
        as_layout.addWidget(auth_desc)
        layout.addWidget(auth_switch_group)

        # 2. Danh sách tài khoản người dùng
        users_group = QGroupBox("👥 Danh sách tài khoản người dùng")
        users_layout = QVBoxLayout(users_group)
        users_layout.setSpacing(10)

        # User Table Action Bar
        u_top_row = QHBoxLayout()
        add_user_btn = QPushButton("➕ Thêm tài khoản mới")
        add_user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_user_btn.setFixedHeight(34)
        add_user_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['accent_primary']}, stop:1 {COLORS['accent_secondary']});
                color: #ffffff;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                padding: 0 16px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLORS['accent_primary_hover']}, stop:1 {COLORS['accent_secondary_hover']});
            }}
        """)
        add_user_btn.clicked.connect(self._open_add_user_dialog)
        u_top_row.addWidget(add_user_btn)

        reload_users_btn = QPushButton("🔄 Làm mới")
        reload_users_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reload_users_btn.setFixedHeight(34)
        reload_users_btn.clicked.connect(self._refresh_users_table)
        u_top_row.addWidget(reload_users_btn)
        u_top_row.addStretch()

        users_layout.addLayout(u_top_row)

        # Table
        self._users_table = QTableWidget()
        self._users_table.setColumnCount(7)
        self._users_table.setHorizontalHeaderLabels([
            "ID", "Tên đăng nhập", "Tên hiển thị", "Vai trò", "Đăng nhập lần cuối", "Số lần", "Thao tác"
        ])
        self._users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._users_table.horizontalHeader().resizeSection(0, 45)
        self._users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._users_table.horizontalHeader().resizeSection(1, 130)
        self._users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self._users_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._users_table.horizontalHeader().resizeSection(3, 90)
        self._users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self._users_table.horizontalHeader().resizeSection(4, 150)
        self._users_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._users_table.horizontalHeader().resizeSection(5, 80)
        self._users_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self._users_table.horizontalHeader().resizeSection(6, 200)
        self._users_table.verticalHeader().setVisible(False)
        self._users_table.setAlternatingRowColors(True)
        self._users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._users_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                gridline-color: {COLORS['border']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        users_layout.addWidget(self._users_table)
        layout.addWidget(users_group)

        # 3. Nhật ký Đăng nhập (Login Logs)
        logs_group = QGroupBox("📜 Lịch sử & Nhật ký Đăng nhập (Login Logs)")
        logs_layout = QVBoxLayout(logs_group)
        logs_layout.setSpacing(10)

        l_top_row = QHBoxLayout()
        refresh_logs_btn = QPushButton("🔄 Tải lại nhật ký")
        refresh_logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_logs_btn.clicked.connect(self._refresh_login_logs_table)
        l_top_row.addWidget(refresh_logs_btn)

        clear_logs_btn = QPushButton("🗑️ Xoá lịch sử nhật ký")
        clear_logs_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_logs_btn.clicked.connect(self._clear_login_logs_action)
        l_top_row.addWidget(clear_logs_btn)
        l_top_row.addStretch()

        logs_layout.addLayout(l_top_row)

        self._login_logs_table = QTableWidget()
        self._login_logs_table.setColumnCount(5)
        self._login_logs_table.setHorizontalHeaderLabels([
            "Thời gian", "Tài khoản", "Kết quả", "Thiết bị", "Chi tiết"
        ])
        self._login_logs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._login_logs_table.horizontalHeader().resizeSection(0, 150)
        self._login_logs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._login_logs_table.horizontalHeader().resizeSection(1, 130)
        self._login_logs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        self._login_logs_table.horizontalHeader().resizeSection(2, 110)
        self._login_logs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._login_logs_table.horizontalHeader().resizeSection(3, 130)
        self._login_logs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._login_logs_table.verticalHeader().setVisible(False)
        self._login_logs_table.setAlternatingRowColors(True)
        self._login_logs_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                gridline-color: {COLORS['border']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)
        logs_layout.addWidget(self._login_logs_table)
        layout.addWidget(logs_group)

        scroll.setWidget(inner)
        tab_layout = QVBoxLayout(tab)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.addWidget(scroll)
        return tab

    def _on_auth_toggled(self, checked: bool):
        """Bật / Tắt xác thực đăng nhập."""
        if self.state_manager:
            self.state_manager.set_auth_enabled(checked)
            if checked:
                toast_success("🔒 Đã BẬT xác thực đăng nhập khi mở app!", self)
            else:
                toast_info("🔓 Đã TẮT xác thực đăng nhập. Ứng dụng sẽ vào thẳng màn hình chính.", self)

    def _refresh_users_table(self):
        """Nạp lại danh sách tài khoản."""
        if not hasattr(self, '_users_table') or not self.state_manager:
            return

        users = self.state_manager.get_all_users()
        self._users_table.setRowCount(len(users))

        for row, u in enumerate(users):
            u_id = u.get("id", 0)
            uname = u.get("username", "")
            dname = u.get("display_name", "") or uname
            role = u.get("role", "admin")
            last_login = u.get("last_login_at", "")
            if last_login and "T" in last_login:
                last_login = last_login.replace("T", " ")[:19]
            elif not last_login:
                last_login = "Chưa đăng nhập"

            count = u.get("login_count", 0)

            # Col 0: ID
            item_id = QTableWidgetItem(str(u_id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._users_table.setItem(row, 0, item_id)

            # Col 1: Username
            item_uname = QTableWidgetItem(uname)
            item_uname.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self._users_table.setItem(row, 1, item_uname)

            # Col 2: Display Name
            self._users_table.setItem(row, 2, QTableWidgetItem(dname))

            # Col 3: Role
            role_item = QTableWidgetItem("Admin 👑" if role == "admin" else "User 👤")
            role_item.setForeground(QColor(COLORS["accent_primary"] if role == "admin" else COLORS["text_secondary"]))
            self._users_table.setItem(row, 3, role_item)

            # Col 4: Last Login
            self._users_table.setItem(row, 4, QTableWidgetItem(last_login))

            # Col 5: Login Count
            item_cnt = QTableWidgetItem(f"{count} lần")
            item_cnt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._users_table.setItem(row, 5, item_cnt)

            # Col 6: Action Buttons
            act_widget = QWidget()
            act_layout = QHBoxLayout(act_widget)
            act_layout.setContentsMargins(2, 2, 2, 2)
            act_layout.setSpacing(4)

            # Edit info button
            btn_edit = QPushButton("✏️ Sửa")
            btn_edit.setFixedHeight(26)
            btn_edit.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_edit.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px 6px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['accent_primary']};
                    color: {COLORS['accent_primary']};
                }}
            """)
            btn_edit.clicked.connect(lambda _, ud=u: self._open_edit_user_dialog(ud))
            act_layout.addWidget(btn_edit)

            # Change password button
            btn_pwd = QPushButton("🔑 Đổi MK")
            btn_pwd.setFixedHeight(26)
            btn_pwd.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_pwd.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    font-size: 11px;
                    padding: 2px 6px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS['accent_secondary']};
                    color: {COLORS['accent_secondary']};
                }}
            """)
            btn_pwd.clicked.connect(lambda _, ud=u: self._open_change_password_dialog(ud))
            act_layout.addWidget(btn_pwd)

            # Delete button
            btn_del = QPushButton("🗑️")
            btn_del.setFixedSize(26, 26)
            btn_del.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_del.setToolTip(f"Xoá tài khoản {uname}")
            btn_del.setStyleSheet(f"""
                QPushButton {{
                    background-color: {COLORS['bg_surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 4px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {COLORS['error']}22;
                    border-color: {COLORS['error']};
                    color: {COLORS['error']};
                }}
            """)
            btn_del.clicked.connect(lambda _, ud=u: self._delete_user_action(ud))
            act_layout.addWidget(btn_del)

            self._users_table.setCellWidget(row, 6, act_widget)

    def _open_add_user_dialog(self):
        """Mở dialog thêm tài khoản."""
        dlg = AddUserDialog(self.state_manager, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_users_table()

    def _open_edit_user_dialog(self, user_data: dict):
        """Mở dialog sửa tài khoản."""
        dlg = EditUserDialog(self.state_manager, user_data, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_users_table()

    def _open_change_password_dialog(self, user_data: dict):
        """Mở dialog đổi mật khẩu."""
        dlg = ChangePasswordDialog(self.state_manager, user_data, self)
        dlg.exec()

    def _delete_user_action(self, user_data: dict):
        """Xoá tài khoản."""
        uname = user_data.get("username", "")
        uid = user_data.get("id", 0)

        reply = QMessageBox.question(
            self, "Xác nhận xoá tài khoản",
            f"Bạn có chắc chắn muốn xoá tài khoản '{uname}' không?\nHành động này không thể hoàn tác!",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            success, msg = self.state_manager.delete_user(uid)
            if success:
                toast_success(msg, self)
                self._refresh_users_table()
            else:
                toast_error(msg, self)

    def _refresh_login_logs_table(self):
        """Nạp lại nhật ký đăng nhập."""
        if not hasattr(self, '_login_logs_table') or not self.state_manager:
            return

        logs = self.state_manager.get_login_logs(limit=100)
        self._login_logs_table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            t_str = log.get("login_time", "")
            if t_str and "T" in t_str:
                t_str = t_str.replace("T", " ")[:19]

            uname = log.get("username", "")
            status = log.get("status", "SUCCESS")
            device = log.get("ip_or_device", "Local Desktop")
            msg = log.get("message", "")

            # Time
            self._login_logs_table.setItem(row, 0, QTableWidgetItem(t_str))

            # Username
            self._login_logs_table.setItem(row, 1, QTableWidgetItem(uname))

            # Status
            item_status = QTableWidgetItem("✅ Thành công" if status == "SUCCESS" else "❌ Thất bại")
            item_status.setForeground(QColor(COLORS["success"] if status == "SUCCESS" else COLORS["error"]))
            item_status.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self._login_logs_table.setItem(row, 2, item_status)

            # Device
            self._login_logs_table.setItem(row, 3, QTableWidgetItem(device))

            # Message
            self._login_logs_table.setItem(row, 4, QTableWidgetItem(msg))

    def _clear_login_logs_action(self):
        """Xoá toàn bộ nhật ký đăng nhập."""
        reply = QMessageBox.question(
            self, "Xoá nhật ký", "Bạn có chắc chắn muốn xoá toàn bộ lịch sử đăng nhập?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.state_manager.clear_login_logs():
                toast_success("Đã xoá toàn bộ nhật ký đăng nhập!", self)
                self._refresh_login_logs_table()
            else:
                toast_error("Không thể xoá nhật ký đăng nhập.", self)

    # ============================================================
    # TAB 6: GENERAL
    # ============================================================

    def _create_general_tab(self) -> QWidget:
        """Tab cài đặt chung — bao gồm chế độ xác nhận hành động."""
        tab = QWidget()
        tab.setObjectName("generalTab")
        tab.setStyleSheet(f"QWidget#generalTab {{ background-color: {COLORS['bg_primary']}; }}")
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(16)

        # ===== Chế độ xác nhận hành động (Execution Confirmation) =====
        confirm_group = QGroupBox("🛡️ Chế độ xác nhận hành động (Execution Confirmation)")
        confirm_layout = QVBoxLayout(confirm_group)
        confirm_layout.setSpacing(10)

        current_confirm = self.state_manager.get_app_setting("confirm_mode", "auto") if self.state_manager else "auto"

        self._confirm_btn_group = QButtonGroup(self)

        confirm_modes = [
            ("auto", "⚡ Tự động thực hiện ngay (MẶC ĐỊNH)",
             "AI thực hiện hành động NGAY LẬP TỨC khi ban yêu cầu, không hỏi xác nhận. Nhanh và tiện nhất."),
            ("ask_first", "🟡 Hỏi lần đầu",
             "AI hỏi xác nhận LẦN ĐẦU cho mỗi loại hành động mới. Sau khi đồng ý, thực hiện tương tự mà không cần hỏi lại."),
            ("always_ask", "🔴 Luôn hỏi xác nhận",
             "AI LUÔN hỏi xác nhận trước khi thực hiện bất kỳ hành động nào. An toàn nhất nhưng chậm hơn.")
        ]

        self._confirm_radios = {}
        for c_key, c_title, c_desc in confirm_modes:
            row_widget = QWidget()
            row_layout = QVBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 2, 0, 2)
            row_layout.setSpacing(2)

            radio = QRadioButton(c_title)
            radio.setChecked(current_confirm == c_key)
            radio.toggled.connect(self._on_confirm_mode_changed)
            self._confirm_btn_group.addButton(radio)
            self._confirm_radios[c_key] = radio

            desc_lbl = QLabel(c_desc)
            desc_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; margin-left: 24px;")
            desc_lbl.setWordWrap(True)

            row_layout.addWidget(radio)
            row_layout.addWidget(desc_lbl)
            confirm_layout.addWidget(row_widget)

        layout.addWidget(confirm_group)

        # AI Status
        status_group = QGroupBox("Trạng thái AI Engine")
        status_layout = QVBoxLayout(status_group)
        self._ai_status_label = QLabel("Loading...")
        self._ai_status_label.setWordWrap(True)
        self._ai_status_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        status_layout.addWidget(self._ai_status_label)
        layout.addWidget(status_group)

        # Hotkeys
        auto_group = QGroupBox("Phím tắt")
        auto_layout = QVBoxLayout(auto_group)
        hotkeys_info = QLabel(
            "• F8 — Bắt đầu chạy macro\n"
            "• F9 — Tạm dừng / Tiếp tục\n"
            "• F10 — Dừng hoàn toàn\n"
            "• Ctrl+Shift+S — Chụp screenshot + AI phân tích\n"
            "• Ctrl+Shift+A — Mở nhanh AI Chat"
        )
        hotkeys_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; padding: 8px;")
        auto_layout.addWidget(hotkeys_info)
        layout.addWidget(auto_group)

        # About
        about_group = QGroupBox("Thông tin ứng dụng")
        about_layout = QVBoxLayout(about_group)
        about_text = QLabel(
            "🤖 AI Claw v1.1.0 — Multi-AI Edition\n"
            "Nền tảng Tự Động Hoá Thông Minh\n\n"
            "Hỗ trợ: Gemini • ChatGPT • Claude • DeepSeek • Qwen\n"
            "Built with PyQt6 + Python"
        )
        about_text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        about_layout.addWidget(about_text)
        layout.addWidget(about_group)

        layout.addStretch()
        return tab

    def _on_confirm_mode_changed(self):
        """Lưu chế độ xác nhận hành động."""
        if not self.state_manager:
            return
        for c_key, radio in self._confirm_radios.items():
            if radio.isChecked():
                self.state_manager.set_app_setting("confirm_mode", c_key)
                break

    # ============================================================
    # DATA OPERATIONS
    # ============================================================

    def _load_data(self):
        """Load dữ liệu — deferred, chạy sau khi UI hiện."""
        import time
        from PyQt6.QtWidgets import QApplication

        # Cập nhật provider filter combo với key counts
        if hasattr(self, '_provider_filter'):
            t0 = time.time()
            self._provider_filter.blockSignals(True)
            for i in range(1, self._provider_filter.count()):
                prov = self._provider_filter.itemData(i)
                if prov:
                    info = PROVIDER_DISPLAY.get(prov, {})
                    key_count = self.key_manager.get_provider_key_count(prov)
                    suffix = f" ({key_count} keys)" if key_count > 0 else ""
                    self._provider_filter.setItemText(i, f"{info.get('icon', '⚡')} {info.get('name', prov)}{suffix}")
            self._provider_filter.blockSignals(False)
            logger.debug(f"[Settings] Provider filter updated in {time.time() - t0:.3f}s")

        QApplication.processEvents()

        if hasattr(self, '_keys_table'):
            t0 = time.time()
            self._refresh_keys_table()
            logger.debug(f"[Settings] Keys table refreshed in {time.time() - t0:.3f}s")

        QApplication.processEvents()

        if hasattr(self, '_cards_layout'):
            self._refresh_model_cards()  # Đã có timing bên trong

        QApplication.processEvents()

        if hasattr(self, '_users_table'):
            self._refresh_users_table()

        QApplication.processEvents()

        if hasattr(self, '_login_logs_table'):
            self._refresh_login_logs_table()

        QApplication.processEvents()

        if hasattr(self, '_ai_status_label'):
            self._update_ai_status()

    def _refresh_keys_table(self):
        """Refresh bảng API keys."""
        keys = self.key_manager.get_all_keys()
        self._keys_table.setRowCount(len(keys))

        for row, key_data in enumerate(keys):
            provider = key_data.get("provider", "gemini")
            api_key = key_data["api_key"]

            # Provider
            prov_info = PROVIDER_DISPLAY.get(provider, {})
            prov_item = QTableWidgetItem(f"{prov_info.get('icon', '⚡')} {prov_info.get('name', provider)}")
            prov_item.setForeground(QColor(prov_info.get("color", COLORS["text_primary"])))
            self._keys_table.setItem(row, 0, prov_item)

            # API Key (masked)
            masked = f"...{api_key[-12:]}" if len(api_key) > 12 else api_key
            key_item = QTableWidgetItem(masked)
            key_item.setData(Qt.ItemDataRole.UserRole, api_key)
            self._keys_table.setItem(row, 1, key_item)

            # Status
            status = key_data.get("status", "UNKNOWN")
            status_item = QTableWidgetItem(status)
            color_map = {
                "AVAILABLE": COLORS["success"], "QUOTA_EXCEEDED": COLORS["warning"],
                "INVALID": COLORS["error"], "ERROR": COLORS["error"],
            }
            status_item.setForeground(QColor(color_map.get(status, COLORS["text_muted"])))
            self._keys_table.setItem(row, 2, status_item)

            # Requests
            self._keys_table.setItem(row, 3, QTableWidgetItem(str(key_data.get("request_count", 0))))

            # Active
            self._keys_table.setItem(row, 4, QTableWidgetItem("✅" if key_data.get("is_active") else ""))

            # Actions
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(2, 2, 2, 2)
            action_layout.setSpacing(4)

            for icon, tip, callback in [
                ("📝", "Copy key", lambda _, k=api_key: self._copy_key(k)),
                ("🔍", "Kiểm tra key", lambda _, k=api_key: self._check_key(k)),
                ("⚡", "Kích hoạt", lambda _, k=api_key: self._activate_key(k)),
                ("🗑️", "Xoá", lambda _, k=api_key: self._delete_key(k)),
            ]:
                btn = QPushButton(icon)
                btn.setFixedSize(32, 28)
                btn.setToolTip(tip)
                btn.setCursor(Qt.CursorShape.PointingHandCursor)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['bg_surface']};
                        border: 1px solid {COLORS['border']};
                        border-radius: 4px;
                        font-size: 12px;
                    }}
                    QPushButton:hover {{
                        border-color: {COLORS['accent_primary']};
                        background-color: {COLORS['bg_surface_hover']};
                    }}
                """)
                btn.clicked.connect(callback)
                action_layout.addWidget(btn)

            self._keys_table.setCellWidget(row, 5, action_widget)

        # Cập nhật quota summary
        self._update_quota_summary()

    def _update_quota_summary(self):
        """Cập nhật thông tin quota tổng hợp."""
        try:
            if not hasattr(self, '_quota_summary_label'):
                return
            summary = self.key_manager.get_key_quota_summary()
            providers_with_keys = self.key_manager.get_providers_with_keys()

            lines = []
            lines.append(
                f"🔑 Tổng: {summary['total_keys']} key(s) — "
                f"✅ Khả dụng: {summary['available']} | "
                f"⚠️ Hết quota: {summary['exhausted']} | "
                f"❌ Không hợp lệ: {summary['invalid']}"
            )
            lines.append(f"📈 Tổng requests đã dùng: {summary['total_requests']} | Lỗi: {summary['total_errors']}")

            if providers_with_keys:
                lines.append("")
                for prov in providers_with_keys:
                    prov_summary = self.key_manager.get_key_quota_summary(prov)
                    prov_info = PROVIDER_DISPLAY.get(prov, {})
                    prov_name = prov_info.get("name", prov)
                    prov_icon = prov_info.get("icon", "⚡")
                    lines.append(
                        f"  {prov_icon} {prov_name}: "
                        f"{prov_summary['total_keys']} key(s), "
                        f"{prov_summary['total_requests']} req, "
                        f"✅{prov_summary['available']} ⚠️{prov_summary['exhausted']} ❌{prov_summary['invalid']}"
                    )

            self._quota_summary_label.setText("\n".join(lines))
        except Exception as e:
            logger.error(f"[SettingsDialog] Lỗi cập nhật quota summary: {e}")

    def _add_keys(self):
        """Thêm API keys."""
        text = self._key_input.toPlainText().strip()
        if not text:
            return
        provider = self._add_provider_combo.currentData()
        added = self.key_manager.add_keys_bulk(text, provider)
        if added > 0:
            prov_info = PROVIDER_DISPLAY.get(provider, {})
            toast_success(f"Đã thêm {added} key(s) cho {prov_info.get('name', provider)}", self)
            self._key_input.clear()
            self._refresh_keys_table()
            self._refresh_model_cards()
            self.ai_engine._init_client()
            self._update_ai_status()
        else:
            toast_warning("Không có key hợp lệ nào được thêm.", self)

    def _check_key(self, api_key: str):
        worker = KeyCheckWorker(self.key_manager, api_key)
        worker.result_ready.connect(self._on_check_result)
        self._check_workers.append(worker)
        worker.start()

    def _on_check_result(self, result: dict):
        prov = PROVIDER_DISPLAY.get(result.get("provider", ""), {}).get("name", "?")
        status = result.get('status', '?')
        msg = result.get('message', '')
        if status == 'AVAILABLE':
            toast_success(f"Key hoạt động — {prov}", self)
        else:
            toast_warning(f"{prov}: {status} — {msg}", self)
        self._refresh_keys_table()

    def _activate_key(self, api_key: str):
        self.key_manager.set_active_key(api_key)
        self.ai_engine._init_client()
        self._refresh_keys_table()
        self._update_ai_status()

    def _delete_key(self, api_key: str):
        reply = QMessageBox.question(
            self, "Xoá API Key", f"Xoá key ...{api_key[-8:]}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.key_manager.remove_key(api_key)
            self._refresh_keys_table()

    def _reset_quotas(self):
        self.key_manager.reset_all_quotas()
        toast_success("Đã reset quota tất cả API keys", self)
        self._refresh_keys_table()

    def _update_ai_status(self):
        """Cập nhật thông tin AI engine."""
        status = self.ai_engine.get_status()
        text = (
            f"🔗 Kết nối: {'✅ Sẵn sàng' if status['connected'] else '❌ Chưa kết nối'}\n"
            f"{status.get('provider_icon', '⚡')} Provider: {status.get('provider_name', '?')}\n"
            f"🤖 Model: {status.get('model_name', '?')} {status.get('model_tier', '')}\n"
            f"🔑 API Key: {status['api_key']}\n"
            f"📊 Tổng keys: {status['total_keys']} | Khả dụng: {status['available_keys']}\n"
            f"👁️ Vision: {'✅' if status.get('supports_vision') else '❌'} | "
            f"🔧 Tools: {'✅' if status.get('supports_tools') else '❌'}\n"
            f"💬 Lịch sử: {status['history_count']} tin nhắn"
        )
        self._ai_status_label.setText(text)
