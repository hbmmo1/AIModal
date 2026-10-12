"""
Floating Quick Access Widget — Nút nổi truy cập nhanh trên màn hình Desktop.
Tính năng:
  - Luôn nổi trên cùng (Always on top)
  - Kéo thả tự do bất kỳ vị trí nào trên màn hình desktop, tự động lưu vị trí
  - Tự động làm mờ khi không kích hoạt (inactive), sáng rõ 100% khi hover chuột
  - Nút 🪟 mở rộng cửa sổ chính (kích hoạt & đưa cửa sổ ứng dụng lên trên cùng)
  - Nút 📸 chụp ảnh màn hình nhanh
  - Nút 💬 mở AI Chat
  - Nút ⚙️ mở Cài đặt
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLabel,
    QGraphicsOpacityEffect, QApplication, QFrame
)
from PyQt6.QtCore import (
    Qt, QPoint, QPropertyAnimation, QEasingCurve, pyqtSignal, QTimer
)
from PyQt6.QtGui import QFont, QCursor, QMouseEvent

from ui.theme import COLORS
from core.state_manager import StateManager

logger = logging.getLogger(__name__)


class FloatingQuickAccessWidget(QWidget):
    """Thanh nổi truy cập nhanh (Floating Dock/Pill)."""

    expand_requested = pyqtSignal()
    screenshot_requested = pyqtSignal()
    chat_requested = pyqtSignal()
    settings_requested = pyqtSignal()
    closed_requested = pyqtSignal()

    INACTIVE_OPACITY = 0.38
    ACTIVE_OPACITY = 1.0

    def __init__(self, state_manager: StateManager = None, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager or StateManager()
        self._is_dragging = False
        self._drag_start_position = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)

        self._setup_ui()
        self._setup_opacity()
        self._restore_position()

    def _setup_ui(self):
        self.setFixedHeight(48)
        self.setCursor(Qt.CursorShape.SizeAllCursor)

        # Outer layout
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(0)

        # Container frame
        self._frame = QFrame()
        self._frame.setObjectName("floatFrame")
        self._update_frame_style()

        frame_layout = QHBoxLayout(self._frame)
        frame_layout.setContentsMargins(10, 4, 10, 4)
        frame_layout.setSpacing(6)

        # Drag handle / App Logo Icon
        self._logo_lbl = QLabel("🤖")
        self._logo_lbl.setFont(QFont("Segoe UI Emoji", 14))
        self._logo_lbl.setStyleSheet("background: transparent; border: none;")
        self._logo_lbl.setToolTip("AI Claw Quick Access (Kéo để di chuyển)")
        frame_layout.addWidget(self._logo_lbl)

        # Separator line
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(1)
        sep.setStyleSheet(f"background-color: {COLORS['border']}; margin: 6px 2px;")
        frame_layout.addWidget(sep)

        # 1. Expand / Restore Window Button
        self.btn_expand = self._create_pill_button(
            "🪟", "Mở rộng / Hiện cửa sổ chính AI Claw", self.expand_requested.emit, is_primary=True
        )
        frame_layout.addWidget(self.btn_expand)

        # 2. Quick Screenshot Button
        self.btn_snap = self._create_pill_button(
            "📸", "Chụp màn hình nhanh gửi AI", self.screenshot_requested.emit
        )
        frame_layout.addWidget(self.btn_snap)

        # 3. AI Chat Button
        self.btn_chat = self._create_pill_button(
            "💬", "Mở khung trò chuyện AI Chat", self.chat_requested.emit
        )
        frame_layout.addWidget(self.btn_chat)

        # 4. Settings Button
        self.btn_settings = self._create_pill_button(
            "⚙️", "Mở Cài đặt hệ thống & Models", self.settings_requested.emit
        )
        frame_layout.addWidget(self.btn_settings)

        # 5. Hide Button
        self.btn_hide = self._create_pill_button(
            "✕", "Ẩn nút nổi", self._handle_hide, is_close=True
        )
        frame_layout.addWidget(self.btn_hide)

        main_layout.addWidget(self._frame)

    def _update_frame_style(self):
        c = COLORS
        self._frame.setStyleSheet(f"""
            QFrame#floatFrame {{
                background-color: {c['bg_surface']};
                border: 1.5px solid {c['accent_primary']};
                border-radius: 20px;
            }}
        """)

    def _create_pill_button(self, icon_text: str, tooltip: str, callback, is_primary=False, is_close=False) -> QPushButton:
        c = COLORS
        btn = QPushButton(icon_text)
        btn.setToolTip(tooltip)
        btn.setFixedSize(32, 32)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFont(QFont("Segoe UI Emoji", 12))

        if is_primary:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent_primary']}, stop:1 {c['accent_secondary']});
                    color: #ffffff;
                    border: none;
                    border-radius: 16px;
                }}
                QPushButton:hover {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {c['accent_primary_hover']}, stop:1 {c['accent_secondary_hover']});
                }}
            """)
        elif is_close:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {c['text_muted']};
                    border: none;
                    border-radius: 16px;
                    font-size: 11px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {c['error']}33;
                    color: {c['error']};
                }}
            """)
        else:
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {c['bg_elevated']};
                    color: {c['text_primary']};
                    border: 1px solid {c['border']};
                    border-radius: 16px;
                }}
                QPushButton:hover {{
                    background-color: {c['bg_surface_hover']};
                    border-color: {c['accent_primary']};
                    color: {c['accent_primary']};
                }}
            """)

        btn.clicked.connect(callback)
        return btn

    def _setup_opacity(self):
        """Hiệu ứng làm mờ khi không kích hoạt và sáng khi hover."""
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(self.INACTIVE_OPACITY)
        self.setGraphicsEffect(self._opacity_effect)

        self._anim = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    def enterEvent(self, event):
        """Khi chuột rê vào widget -> Sáng 100%."""
        super().enterEvent(event)
        self._anim.stop()
        self._anim.setStartValue(self._opacity_effect.opacity())
        self._anim.setEndValue(self.ACTIVE_OPACITY)
        self._anim.start()

    def leaveEvent(self, event):
        """Khi chuột rời khỏi widget -> Làm mờ."""
        super().leaveEvent(event)
        if not self._is_dragging:
            self._anim.stop()
            self._anim.setStartValue(self._opacity_effect.opacity())
            self._anim.setEndValue(self.INACTIVE_OPACITY)
            self._anim.start()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._drag_start_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        if self._is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_start_position
            self.move(new_pos)
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        if self._is_dragging:
            self._is_dragging = False
            self._save_position()
            event.accept()
        super().mouseReleaseEvent(event)

    def _save_position(self):
        """Lưu vị trí nút nổi vào database."""
        try:
            self.state_manager.set_app_setting("float_pos_x", str(self.x()))
            self.state_manager.set_app_setting("float_pos_y", str(self.y()))
        except Exception as e:
            logger.error(f"Lỗi lưu vị trí float widget: {e}")

    def _restore_position(self):
        """Phục hồi vị trí đã lưu của nút nổi."""
        try:
            saved_x = self.state_manager.get_app_setting("float_pos_x", "")
            saved_y = self.state_manager.get_app_setting("float_pos_y", "")
            if saved_x and saved_y:
                self.move(int(saved_x), int(saved_y))
            else:
                # Default: Bottom-right screen corner
                screen = QApplication.primaryScreen()
                if screen:
                    geom = screen.availableGeometry()
                    self.move(geom.width() - 320, geom.height() - 100)
        except Exception as e:
            logger.warning(f"Không thể khôi phục vị trí float widget: {e}")

    def _handle_hide(self):
        self.hide()
        self.state_manager.set_app_setting("float_widget_enabled", "0")
        self.closed_requested.emit()

    def update_theme(self):
        """Cập nhật màu sắc khi đổi theme."""
        self._update_frame_style()
