"""
Toast Notification — Thông báo hiện đại kiểu toast/snackbar.
Slide-in animation, auto-dismiss, nhiều loại (success, error, warning, info).
Hỗ trợ stacking (nhiều toast cùng lúc).
"""

import logging
from PyQt6.QtWidgets import (
    QWidget, QLabel, QHBoxLayout, QPushButton,
    QGraphicsOpacityEffect, QApplication
)
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QPoint,
    QEasingCurve, pyqtSignal, QSequentialAnimationGroup,
    QParallelAnimationGroup
)
from PyQt6.QtGui import QFont, QColor

from ui.theme import COLORS

logger = logging.getLogger(__name__)


# ============================================================
# Toast Types
# ============================================================

TOAST_STYLES = {
    "success": {
        "icon": "✅",
        "bg": "#0d3320",
        "border": "#22c55e",
        "text": "#86efac",
        "accent": "#22c55e",
    },
    "error": {
        "icon": "❌",
        "bg": "#3b1118",
        "border": "#ef4444",
        "text": "#fca5a5",
        "accent": "#ef4444",
    },
    "warning": {
        "icon": "⚠️",
        "bg": "#3b2e0a",
        "border": "#f59e0b",
        "text": "#fcd34d",
        "accent": "#f59e0b",
    },
    "info": {
        "icon": "ℹ️",
        "bg": "#0c1f3d",
        "border": "#3b82f6",
        "text": "#93c5fd",
        "accent": "#3b82f6",
    },
}

# Quản lý danh sách toast đang hiển thị (global)
_active_toasts: list = []
TOAST_SPACING = 8
TOAST_BOTTOM_MARGIN = 20
TOAST_RIGHT_MARGIN = 20


TOAST_POSITIONS = {
    "bottom-right": "↘️ Góc phải dưới cùng (Mặc định)",
    "bottom-left": "↙️ Góc trái dưới cùng",
    "top-right": "↗️ Góc phải trên cùng",
    "top-left": "↖️ Góc trái trên cùng",
    "top-center": "⬆️ Giữa trên cùng",
    "bottom-center": "⬇️ Giữa dưới cùng",
}


def get_saved_toast_position() -> str:
    """Lấy vị trí toast notification đã lưu."""
    try:
        from core.state_manager import StateManager
        sm = StateManager()
        return sm.get_app_setting("toast_position", "bottom-right")
    except Exception:
        return "bottom-right"


class ToastNotification(QWidget):
    """
    Toast notification widget hiện đại.
    - Slide-in từ hướng phù hợp
    - Auto-dismiss sau N giây
    - Click để đóng
    - Stacking (nhiều toast cùng lúc) theo 6 vị trí cấu hình
    """

    closed = pyqtSignal()

    def __init__(
        self,
        message: str,
        toast_type: str = "info",
        duration_ms: int = 3500,
        parent: QWidget = None,
    ):
        # Dùng main window làm parent nếu không chỉ định
        if parent is None:
            parent = self._find_main_window()
        super().__init__(parent)

        self._message = message
        self._type = toast_type
        self._duration = duration_ms
        self._style = TOAST_STYLES.get(toast_type, TOAST_STYLES["info"])
        self._target_pos = QPoint(0, 0)

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
            | Qt.WindowType.BypassWindowManagerHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._setup_ui()
        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self._opacity_effect)

    @staticmethod
    def _find_main_window():
        """Tìm main window."""
        for w in QApplication.topLevelWidgets():
            if w.objectName() == "MainWindow" or w.__class__.__name__ == "MainWindow":
                return w
        widgets = QApplication.topLevelWidgets()
        return widgets[0] if widgets else None

    def _setup_ui(self):
        """Thiết lập giao diện toast."""
        self.setMinimumHeight(48)
        self.setMinimumWidth(320)
        self.setMaximumWidth(520)

        style = self._style
        self.setStyleSheet(f"""
            QWidget#toastBody {{
                background-color: {style['bg']};
                border: 1px solid {style['border']}88;
                border-left: 5px solid {style['border']};
                border-radius: 10px;
            }}
        """)

        # Main body
        body = QWidget()
        body.setObjectName("toastBody")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(14, 10, 10, 10)
        body_layout.setSpacing(10)

        # Icon
        icon_label = QLabel(style["icon"])
        icon_label.setFont(QFont("Segoe UI Emoji", 14))
        icon_label.setFixedWidth(24)
        icon_label.setStyleSheet("background: transparent; border: none;")
        body_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignTop)

        # Message
        msg_label = QLabel(self._message)
        msg_label.setFont(QFont("Segoe UI", 10))
        msg_label.setStyleSheet(f"color: {style['text']}; background: transparent; border: none; line-height: 1.4;")
        msg_label.setWordWrap(True)
        body_layout.addWidget(msg_label, 1)

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(22, 22)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {style['text']}88;
                border: none;
                border-radius: 11px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {style['border']}33;
                color: {style['text']};
            }}
        """)
        close_btn.clicked.connect(self.dismiss)
        body_layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignTop)

        # Progress bar (auto-dismiss indicator)
        self._progress_bar = QWidget(body)
        self._progress_bar.setFixedHeight(3)
        self._progress_bar.setStyleSheet(f"""
            background-color: {style['accent']};
            border-radius: 1px;
        """)

        # Outer layout
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(body)

    def show_toast(self):
        """Hiển thị toast với animation."""
        global _active_toasts
        _active_toasts.append(self)

        self.adjustSize()
        self._position_toast()
        self.show()

        # Fade in
        self._fade_in = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_in.setDuration(250)
        self._fade_in.setStartValue(0.0)
        self._fade_in.setEndValue(1.0)
        self._fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade_in.start()

        # Slide in based on position
        pos_key = get_saved_toast_position()
        if "left" in pos_key:
            start_pos = QPoint(self._target_pos.x() - 50, self._target_pos.y())
        elif "top-center" in pos_key:
            start_pos = QPoint(self._target_pos.x(), self._target_pos.y() - 30)
        elif "bottom-center" in pos_key:
            start_pos = QPoint(self._target_pos.x(), self._target_pos.y() + 30)
        else:
            start_pos = QPoint(self._target_pos.x() + 50, self._target_pos.y())

        self._slide_in = QPropertyAnimation(self, b"pos")
        self._slide_in.setDuration(280)
        self._slide_in.setStartValue(start_pos)
        self._slide_in.setEndValue(self._target_pos)
        self._slide_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.move(start_pos)
        self._slide_in.start()

        # Progress bar animation
        if self._duration > 0:
            self._progress_timer = QTimer(self)
            self._progress_elapsed = 0
            self._progress_interval = 30
            self._progress_timer.timeout.connect(self._update_progress)
            self._progress_timer.start(self._progress_interval)

            # Auto dismiss
            self._dismiss_timer = QTimer(self)
            self._dismiss_timer.setSingleShot(True)
            self._dismiss_timer.timeout.connect(self.dismiss)
            self._dismiss_timer.start(self._duration)

    def _update_progress(self):
        """Cập nhật progress bar."""
        self._progress_elapsed += self._progress_interval
        ratio = max(0, 1.0 - self._progress_elapsed / self._duration)
        bar_width = int(self.width() * ratio)
        self._progress_bar.setFixedWidth(max(0, bar_width))
        self._progress_bar.move(0, self.height() - 4)

        if ratio <= 0:
            self._progress_timer.stop()

    def _position_toast(self):
        """Tính vị trí toast (hỗ trợ 6 vị trí + stacking)."""
        parent = self.parent()
        if not parent:
            parent = self._find_main_window()
        if not parent:
            return

        # Lấy window geometry
        if hasattr(parent, 'window') and parent.window():
            parent = parent.window()
        parent_rect = parent.geometry()

        self.adjustSize()
        w = max(self.width(), 320)
        h = max(self.height(), 48)

        # Tính tổng height của các toast đang hiển thị
        total_offset = 0
        for t in _active_toasts:
            if t is not self and t.isVisible():
                total_offset += t.height() + TOAST_SPACING

        pos_key = get_saved_toast_position()

        if pos_key == "top-left":
            x = parent_rect.x() + TOAST_RIGHT_MARGIN
            y = parent_rect.y() + TOAST_BOTTOM_MARGIN + total_offset
        elif pos_key == "top-right":
            x = parent_rect.x() + parent_rect.width() - w - TOAST_RIGHT_MARGIN
            y = parent_rect.y() + TOAST_BOTTOM_MARGIN + total_offset
        elif pos_key == "top-center":
            x = parent_rect.x() + (parent_rect.width() - w) // 2
            y = parent_rect.y() + TOAST_BOTTOM_MARGIN + total_offset
        elif pos_key == "bottom-left":
            x = parent_rect.x() + TOAST_RIGHT_MARGIN
            y = parent_rect.y() + parent_rect.height() - h - TOAST_BOTTOM_MARGIN - total_offset
        elif pos_key == "bottom-center":
            x = parent_rect.x() + (parent_rect.width() - w) // 2
            y = parent_rect.y() + parent_rect.height() - h - TOAST_BOTTOM_MARGIN - total_offset
        else:  # bottom-right (Mặc định)
            x = parent_rect.x() + parent_rect.width() - w - TOAST_RIGHT_MARGIN
            y = parent_rect.y() + parent_rect.height() - h - TOAST_BOTTOM_MARGIN - total_offset

        self.move(x, y)
        self._target_pos = QPoint(x, y)

    def dismiss(self):
        """Đóng toast với animation."""
        # Stop timers
        if hasattr(self, '_dismiss_timer') and self._dismiss_timer.isActive():
            self._dismiss_timer.stop()
        if hasattr(self, '_progress_timer') and self._progress_timer.isActive():
            self._progress_timer.stop()

        # Fade out
        self._fade_out = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_out.setDuration(200)
        self._fade_out.setStartValue(1.0)
        self._fade_out.setEndValue(0.0)
        self._fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        self._fade_out.finished.connect(self._on_dismissed)
        self._fade_out.start()

    def _on_dismissed(self):
        """Sau khi animation kết thúc."""
        global _active_toasts
        if self in _active_toasts:
            _active_toasts.remove(self)
        self.closed.emit()
        self.close()

    def mousePressEvent(self, event):
        """Click để đóng."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dismiss()
        super().mousePressEvent(event)


# ============================================================
# Convenience functions (thay thế QMessageBox)
# ============================================================

def toast_success(message: str, parent=None, duration_ms: int = 3000):
    """Hiển thị toast thành công."""
    t = ToastNotification(message, "success", duration_ms, parent)
    t.show_toast()
    return t


def toast_error(message: str, parent=None, duration_ms: int = 5000):
    """Hiển thị toast lỗi."""
    t = ToastNotification(message, "error", duration_ms, parent)
    t.show_toast()
    return t


def toast_warning(message: str, parent=None, duration_ms: int = 4000):
    """Hiển thị toast cảnh báo."""
    t = ToastNotification(message, "warning", duration_ms, parent)
    t.show_toast()
    return t


def toast_info(message: str, parent=None, duration_ms: int = 3500):
    """Hiển thị toast thông tin."""
    t = ToastNotification(message, "info", duration_ms, parent)
    t.show_toast()
    return t
