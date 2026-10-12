"""
AI Claw (300AIClaude) - Hộp Thoại Đăng Nhập Chuẩn Bảo Mật
"""

import os
import sys
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFrame
)

from ui.theme import COLORS, apply_titlebar_theme, get_current_theme
from core.state_manager import StateManager


class AIClawLoginDialog(QDialog):
    """Hộp thoại đăng nhập cho AI Claw."""

    def __init__(self, state_manager: StateManager = None, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager or StateManager()
        self.logged_in_user = None

        self.setWindowTitle("AI Claw — Xác Thực Đăng Nhập")
        self.setFixedSize(430, 490)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)
        self._init_ui()
        apply_titlebar_theme(self)

    def showEvent(self, event):
        super().showEvent(event)
        apply_titlebar_theme(self)

    def _init_ui(self):
        c = COLORS
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {c['bg_primary']};
                color: {c['text_primary']};
                font-family: 'Segoe UI', Arial, sans-serif;
            }}
            QLabel {{
                color: {c['text_primary']};
                font-size: 13px;
                font-weight: 500;
            }}
            QLineEdit {{
                background-color: {c['bg_input']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 10px 14px;
                color: {c['text_primary']};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border: 1.5px solid {c['accent_primary']};
                background-color: {c['bg_input']};
            }}
            QPushButton#btnLogin {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                color: #ffffff;
                font-weight: bold;
                font-size: 14px;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }}
            QPushButton#btnLogin:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {c['accent_primary_hover']}, stop:1 {c['accent_secondary_hover']});
            }}
            QPushButton#btnCancel {{
                background-color: {c['bg_surface']};
                color: {c['text_muted']};
                border: 1px solid {c['border']};
                border-radius: 8px;
                padding: 9px;
                font-size: 13px;
            }}
            QPushButton#btnCancel:hover {{
                background-color: {c['bg_surface_hover']};
                color: {c['text_primary']};
                border-color: {c['accent_primary']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(14)

        # Header Icon & Title
        lbl_icon = QLabel("🤖")
        lbl_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icon.setStyleSheet("font-size: 40px; margin-bottom: 0px;")
        layout.addWidget(lbl_icon)

        lbl_title = QLabel("AI CLAW AUTOMATION")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {c['accent_primary']}; letter-spacing: 1px;")
        layout.addWidget(lbl_title)

        lbl_sub = QLabel("Đăng nhập tài khoản để truy cập ứng dụng")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet(f"color: {c['text_muted']}; font-size: 12px; margin-bottom: 6px;")
        layout.addWidget(lbl_sub)

        # Input User - Trống hoàn toàn, không gợi ý hay để lộ tài khoản
        layout.addWidget(QLabel("Tên đăng nhập:"))
        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Nhập tên đăng nhập...")
        self.txt_user.returnPressed.connect(self._focus_password)
        layout.addWidget(self.txt_user)

        # Input Pass - Trống hoàn toàn
        layout.addWidget(QLabel("Mật khẩu:"))
        self.txt_pass = QLineEdit()
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setPlaceholderText("Nhập mật khẩu...")
        self.txt_pass.returnPressed.connect(self._do_login)
        layout.addWidget(self.txt_pass)

        # Error label
        self.lbl_error = QLabel("")
        self.lbl_error.setStyleSheet(f"color: {c['error']}; font-size: 12px; font-weight: bold;")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_error)

        layout.addSpacing(4)

        # Login button
        btn_login = QPushButton("🚀 ĐĂNG NHẬP")
        btn_login.setObjectName("btnLogin")
        btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_login.clicked.connect(self._do_login)
        layout.addWidget(btn_login)

        # Cancel button
        btn_cancel = QPushButton("Thoát")
        btn_cancel.setObjectName("btnCancel")
        btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cancel.clicked.connect(self.reject)
        layout.addWidget(btn_cancel)

        self.txt_user.setFocus()

    def _focus_password(self):
        if self.txt_user.text().strip():
            self.txt_pass.setFocus()
        else:
            self._do_login()

    def _do_login(self):
        u = self.txt_user.text().strip()
        p = self.txt_pass.text()

        if not u:
            self.lbl_error.setText("⚠️ Vui lòng nhập tên đăng nhập!")
            self.txt_user.setFocus()
            return

        if not p:
            self.lbl_error.setText("⚠️ Vui lòng nhập mật khẩu!")
            self.txt_pass.setFocus()
            return

        # Xác thực với SQLite database qua StateManager
        success, msg, user_info = self.state_manager.authenticate_user(u, p, device="Desktop App")
        if success:
            self.logged_in_user = user_info
            self.accept()
        else:
            self.lbl_error.setText(f"❌ {msg}")
            self.txt_pass.selectAll()
            self.txt_pass.setFocus()

