"""
Chat Panel — Giao diện chat AI với bubble messages.
Hỗ trợ tool calling, screenshot analysis, markdown rendering.
"""

import os
import logging
from datetime import datetime
from typing import Optional
from PIL import Image

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QLineEdit, QTextEdit, QScrollArea, QFrame, QSizePolicy, QFileDialog,
    QApplication, QMenu, QInputDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QObject
from PyQt6.QtGui import QFont, QTextCursor, QKeySequence, QShortcut, QPixmap

from ui.theme import (
    COLORS, get_chat_bubble_style, get_chat_flat_style, get_card_style, format_chat_content
)
from ui.toast import toast_success, toast_error, toast_warning, toast_info

logger = logging.getLogger(__name__)

def format_chat_timestamp(dt) -> str:
    """Format: Hôm nay, 14:30 | Hôm qua, 15:00 | T2, 24/10 09:00"""
    from datetime import datetime
    now = datetime.now()
    date_str = ""
    
    if dt.date() == now.date():
        date_str = "Hôm nay"
    elif (now.date() - dt.date()).days == 1:
        date_str = "Hôm qua"
    else:
        weekdays = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        wd = weekdays[dt.weekday()]
        date_str = f"{wd}, {dt.strftime('%d/%m')}"
        
    return f"{date_str}, {dt.strftime('%H:%M')}"

class ChatWorker(QThread):
    """Worker thread để gọi AI không block UI."""
    response_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, ai_engine, message: str, image=None, enable_tools: bool = True):
        super().__init__()
        self.ai_engine = ai_engine
        self.message = message
        self.image = image
        self.enable_tools = enable_tools

    def run(self):
        try:
            result = self.ai_engine.chat(
                self.message,
                image=self.image,
                enable_tools=self.enable_tools,
            )
            # Kiểm tra lỗi từ kết quả trả về (ví dụ: 404, 401, 503, missing key)
            if result.get("error"):
                error_text = result.get("text", "Lỗi không xác định từ AI.")
                self.error_occurred.emit(error_text)
            else:
                self.response_ready.emit(result)
        except Exception as e:
            logger.error(f"[ChatWorker] Exception: {e}", exc_info=True)
            self.error_occurred.emit(str(e))


class ChatBubble(QFrame):
    """Widget cho 1 tin nhắn chat (user hoặc AI)."""

    def __init__(self, text: str, is_user: bool = False, timestamp: str = "",
                 tool_calls: list = None, render_mode: str = "natural",
                 bubble_style: str = "bubble", parent=None):
        super().__init__(parent)
        self.raw_text = text
        self.is_user = is_user
        self.timestamp = timestamp
        self.tool_calls = tool_calls
        self.render_mode = render_mode
        self.bubble_style = bubble_style

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.setObjectName("chatBubbleUser" if is_user else "chatBubbleAI")

        outer = QHBoxLayout(self)
        outer.setContentsMargins(10, 8, 10, 8)
        outer.setSpacing(10)
        outer.setAlignment(Qt.AlignmentFlag.AlignTop)

        # === Avatar ===
        avatar_color = "#3b82f6" if is_user else "#8b5cf6"
        avatar_text = "B" if is_user else "🤖"
        avatar_size = 36

        self.avatar = QLabel(avatar_text)
        self.avatar.setFixedSize(avatar_size, avatar_size)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setStyleSheet(f"""
            background-color: {avatar_color};
            color: white;
            border-radius: {avatar_size // 2}px;
            font-size: {'12px' if is_user else '16px'};
            font-weight: 700;
            border: 2px solid {avatar_color}44;
        """)
        outer.addWidget(self.avatar, 0, Qt.AlignmentFlag.AlignTop)

        # === Content column ===
        content_col = QVBoxLayout()
        content_col.setContentsMargins(0, 0, 0, 0)
        content_col.setSpacing(4)

        # Sender label
        sender_name = "Bạn" if is_user else "AI Claw"
        self.sender_lbl = QLabel(sender_name)
        self.sender_lbl.setStyleSheet(f"""
            color: {avatar_color};
            font-size: 12px;
            font-weight: 700;
            border: none;
            background: transparent;
            padding: 0;
        """)
        content_col.addWidget(self.sender_lbl)

        # Message content
        self.content_lbl = QLabel()
        self.content_lbl.setWordWrap(True)
        self.content_lbl.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse |
            Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self.content_lbl.setStyleSheet(f"""
            color: {COLORS['text_primary']};
            border: none;
            background: transparent;
            padding: 0;
            font-size: 13px;
            line-height: 1.5;
        """)
        self._render_text()
        content_col.addWidget(self.content_lbl)

        # Tool calls (nếu có)
        if tool_calls:
            for tc in tool_calls:
                tool_label = QLabel(f"🔧 {tc.get('name', 'tool')}: {tc.get('args', {})}")
                tool_label.setStyleSheet(f"""
                    color: {COLORS['warning']};
                    font-size: 11px;
                    font-style: italic;
                    border: none;
                    background: transparent;
                    padding: 2px 0;
                """)
                tool_label.setWordWrap(True)
                content_col.addWidget(tool_label)

        # Timestamp
        if timestamp:
            time_label = QLabel(timestamp)
            time_label.setStyleSheet(f"""
                color: {COLORS['text_muted']};
                font-size: 10px;
                border: none;
                background: transparent;
                padding: 0;
            """)
            time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            content_col.addWidget(time_label)

        outer.addLayout(content_col, 1)
        self._apply_style()

    def _apply_style(self):
        self.setObjectName("chatBubbleUser" if self.is_user else "chatBubbleAI")
        if self.bubble_style == "flat":
            self.setStyleSheet(get_chat_flat_style(self.is_user))
        else:
            self.setStyleSheet(get_chat_bubble_style(self.is_user))
            
        avatar_color = "#3b82f6" if self.is_user else "#8b5cf6"
        if hasattr(self, 'sender_lbl'):
            self.sender_lbl.setStyleSheet(f"""
                color: {avatar_color};
                font-size: 12px;
                font-weight: 700;
                border: none;
                background: transparent;
                padding: 0;
            """)
        
        if hasattr(self, 'content_lbl'):
            self.content_lbl.setStyleSheet(f"""
                color: {COLORS['text_primary']};
                border: none;
                background: transparent;
                padding: 0;
                font-size: 13px;
                line-height: 1.5;
            """)

    def _render_text(self):
        if self.is_user:
            # User text: hiển thị trực tiếp PlainText chuẩn xác
            self.content_lbl.setTextFormat(Qt.TextFormat.PlainText)
            self.content_lbl.setText(self.raw_text or "")
        else:
            formatted_text, is_html = format_chat_content(self.raw_text or "", render_mode=self.render_mode)
            if is_html:
                self.content_lbl.setTextFormat(Qt.TextFormat.RichText)
            else:
                self.content_lbl.setTextFormat(Qt.TextFormat.PlainText)
            self.content_lbl.setText(formatted_text)

    def update_display(self, render_mode: str, bubble_style: str):
        """Cập nhật lại chế độ render và kiểu bong bóng."""
        self.render_mode = render_mode
        self.bubble_style = bubble_style
        self._apply_style()
        self._render_text()


class ChatPanel(QWidget):
    """Panel chat AI chính với quản lý phiên trò chuyện (Sessions / History)."""

    def __init__(self, ai_engine, state_manager, screen_analyzer, action_executor, parent=None):
        super().__init__(parent)
        self.ai_engine = ai_engine
        self.state_manager = state_manager
        self.screen_analyzer = screen_analyzer
        self.action_executor = action_executor

        self._bubbles: list[ChatBubble] = []
        self._worker: Optional[ChatWorker] = None
        self._pending_image: Optional[Image.Image] = None
        self._tool_loop_count: int = 0
        self._max_tool_loops: int = 5

        # Khởi tạo phiên trò chuyện hiện tại
        sessions = self.state_manager.get_all_chat_sessions()
        self._current_session_id = sessions[0]["id"] if sessions else self.state_manager.create_chat_session("Cuộc trò chuyện mới")

        self._setup_ui()
        self._load_history()

    def refresh_display_mode(self):
        """Làm mới toàn bộ tin nhắn chat theo cài đặt hiển thị mới."""
        render_mode = self.state_manager.get_app_setting("chat_render_mode", "natural")
        bubble_style = self.state_manager.get_app_setting("chat_bubble_style", "bubble")
        for bubble in self._bubbles:
            bubble.update_display(render_mode, bubble_style)

    def refresh_theme(self):
        """Cập nhật giao diện ChatPanel theo theme mới."""
        self.setStyleSheet(f"ChatPanel {{ background-color: {COLORS['bg_primary']}; }}")
        if hasattr(self, '_header'):
            self._header.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_secondary']}; border-bottom: 1px solid {COLORS['border']}; }}")
        if hasattr(self, '_scroll'):
            self._scroll.setStyleSheet(f"QScrollArea {{ background-color: {COLORS['bg_primary']}; border: none; }}")
        if hasattr(self, '_messages_widget'):
            self._messages_widget.setStyleSheet(f"QWidget#messagesWidget {{ background-color: {COLORS['bg_primary']}; }}")
        if hasattr(self, '_input_frame'):
            self._input_frame.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_surface']}; border-top: 1px solid {COLORS['border']}; }}")
        self._update_session_header()
        self.refresh_display_mode()

    def _setup_ui(self):
        """Thiết lập giao diện chat."""
        self.setStyleSheet(f"ChatPanel {{ background-color: {COLORS['bg_primary']}; }}")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # === HEADER ===
        self._header = QFrame()
        self._header.setFixedHeight(60)
        self._header.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_secondary']}; border-bottom: 1px solid {COLORS['border']}; }}")
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        header_layout.setSpacing(10)

        # Title + Session badge
        title_box = QHBoxLayout()
        title_box.setSpacing(10)

        title = QLabel("🤖 AI Chat")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title_box.addWidget(title)

        self._session_btn = QPushButton("💬 Cuộc trò chuyện")
        self._session_btn.setToolTip("Nhấn để đổi tên cuộc trò chuyện hiện tại")
        self._session_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._session_btn.setFixedHeight(30)
        self._session_btn.clicked.connect(self._rename_current_session)
        title_box.addWidget(self._session_btn)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        # Action buttons on top right
        # 1. New Chat button
        self._new_chat_btn = QPushButton("➕ Chat mới")
        self._new_chat_btn.setToolTip("Bắt đầu một cuộc trò chuyện mới")
        self._new_chat_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._new_chat_btn.setFixedHeight(34)
        self._new_chat_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_primary']};
                color: #ffffff;
                border: none;
                border-radius: 8px;
                padding: 4px 14px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['accent_primary_hover']};
            }}
        """)
        self._new_chat_btn.clicked.connect(self._new_chat)
        header_layout.addWidget(self._new_chat_btn)

        # 2. History manager button
        self._history_btn = QPushButton("📜 Lịch sử")
        self._history_btn.setToolTip("Xem danh sách, tìm kiếm, đổi tên hoặc mở lại các cuộc trò chuyện trước đó")
        self._history_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._history_btn.setFixedHeight(34)
        self._history_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px 14px;
                font-weight: 500;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_surface_hover']};
                border-color: {COLORS['accent_primary']};
            }}
        """)
        self._history_btn.clicked.connect(self._open_history_dialog)
        header_layout.addWidget(self._history_btn)

        # 3. Clear current chat button
        self._clear_btn = QPushButton("🗑️ Xoá chat")
        self._clear_btn.setToolTip("Xoá nội dung của cuộc trò chuyện hiện tại")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setFixedHeight(34)
        self._clear_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['error_bg']};
                color: {COLORS['error']};
                border: 1px solid {COLORS['error']}44;
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['error']};
                color: #ffffff;
            }}
        """)
        self._clear_btn.clicked.connect(self._clear_chat)
        header_layout.addWidget(self._clear_btn)

        layout.addWidget(self._header)

        # === CHAT MESSAGES AREA ===
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"QScrollArea {{ background-color: {COLORS['bg_primary']}; border: none; }}")

        self._messages_widget = QWidget()
        self._messages_widget.setObjectName("messagesWidget")
        self._messages_widget.setStyleSheet(f"QWidget#messagesWidget {{ background-color: {COLORS['bg_primary']}; }}")
        self._messages_layout = QVBoxLayout(self._messages_widget)
        self._messages_layout.setContentsMargins(20, 16, 20, 16)
        self._messages_layout.setSpacing(12)
        self._messages_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._scroll.setWidget(self._messages_widget)
        layout.addWidget(self._scroll, 1)

        # === TYPING INDICATOR ===
        self._typing_label = QLabel("")
        self._typing_label.setStyleSheet(f"""
            color: {COLORS['accent_secondary']};
            font-size: 12px;
            padding: 4px 24px;
            font-style: italic;
            background: transparent;
        """)
        self._typing_label.setVisible(False)
        layout.addWidget(self._typing_label)

        # === INPUT AREA ===
        self._input_frame = QFrame()
        self._input_frame.setStyleSheet(f"QFrame {{ background-color: {COLORS['bg_surface']}; border-top: 1px solid {COLORS['border']}; }}")
        input_layout = QHBoxLayout(self._input_frame)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(10)

        # Screenshot button
        screenshot_btn = QPushButton("📸")
        screenshot_btn.setFixedSize(40, 40)
        screenshot_btn.setToolTip("Chụp screenshot + gửi cho AI phân tích")
        screenshot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        screenshot_btn.clicked.connect(self._capture_screenshot)
        input_layout.addWidget(screenshot_btn)

        # Attach image button
        attach_btn = QPushButton("📎")
        attach_btn.setFixedSize(40, 40)
        attach_btn.setToolTip("Đính kèm ảnh")
        attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        attach_btn.clicked.connect(self._attach_image)
        input_layout.addWidget(attach_btn)

        # Pending image indicator
        self._image_indicator = QLabel("")
        self._image_indicator.setObjectName("mutedDesc")
        self._image_indicator.setVisible(False)

        # Text input
        self._input = QTextEdit()
        self._input.setObjectName("chatInput")
        self._input.setPlaceholderText("Nhập tin nhắn... (Enter để gửi, Shift+Enter xuống dòng)")
        self._input.setFixedHeight(44)
        input_layout.addWidget(self._input, 1)

        # Send button
        self._send_btn = QPushButton("Gửi  ➤")
        self._send_btn.setObjectName("primaryButton")
        self._send_btn.setFixedSize(80, 40)
        self._send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self._send_btn)

        layout.addWidget(self._image_indicator)
        layout.addWidget(self._input_frame)

        # Enter key shortcut
        self._input.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Handle Enter to send, Shift+Enter for newline."""
        from PyQt6.QtCore import QEvent
        if obj == self._input and event.type() == QEvent.Type.KeyPress:
            key_event = event
            if key_event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                if key_event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    return False  # Allow newline
                self._send_message()
                return True
        return super().eventFilter(obj, event)

    def _send_message(self):
        """Gửi tin nhắn."""
        text = self._input.toPlainText().strip()
        if not text and not self._pending_image:
            return

        if self._worker and self._worker.isRunning():
            toast_warning("AI đang xử lý yêu cầu, vui lòng đợi...", self)
            return  # Đang chờ response

        # Display user message
        timestamp = format_chat_timestamp(datetime.now())
        display_text = text
        if self._pending_image:
            display_text = f"📸 [Ảnh đính kèm]\n{text}" if text else "📸 [Ảnh đính kèm] Phân tích ảnh này"

        self._add_bubble(display_text, is_user=True, timestamp=timestamp)

        # Hiển thị thumbnail ảnh user gửi trong chat
        if self._pending_image:
            self._show_user_image_thumbnail(self._pending_image)

        # Save to history
        self.state_manager.save_chat_message(
            "user", display_text,
            session_id=self._current_session_id,
            has_image=self._pending_image is not None
        )
        self._update_session_header()

        # Clear input
        self._input.clear()
        self._input.setFixedHeight(44)

        # Kiểm tra API Key trước khi gọi AI
        active_key = self.ai_engine.api_key
        if not active_key:
            prov = self.ai_engine.provider
            from core.model_registry import PROVIDER_DISPLAY
            prov_name = PROVIDER_DISPLAY.get(prov, {}).get("name", prov)
            self._typing_label.setVisible(False)
            self._send_btn.setEnabled(True)
            self._add_bubble(
                f"⚠️ **Chưa có API Key**: Bạn chưa thiết lập API Key cho **{prov_name}**.\n\n"
                f"👉 Vui lòng nhấn vào nút **⚙️ Setting** (hoặc mở Cài đặt → tab API Keys) để thêm key trước khi trò chuyện.",
                is_user=False,
                timestamp=timestamp
            )
            toast_warning(f"Chưa có API Key cho {prov_name}. Vui lòng cấu hình trong Cài đặt!", self)
            self._pending_image = None
            self._image_indicator.setVisible(False)
            return

        # Show typing indicator
        self._typing_label.setText("🤖 AI Claw đang suy nghĩ...")
        self._typing_label.setVisible(True)
        self._send_btn.setEnabled(False)

        # Reset tool loop counter cho tin nhắn mới
        self._tool_loop_count = 0

        # Start AI worker
        message = text or "Hãy phân tích ảnh screenshot này và mô tả chi tiết nội dung trên màn hình."
        self._worker = ChatWorker(
            self.ai_engine, message,
            image=self._pending_image,
            enable_tools=True
        )
        self._worker.response_ready.connect(self._on_response)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

        # Reset pending image
        self._pending_image = None
        self._image_indicator.setVisible(False)

    def _show_user_image_thumbnail(self, image):
        """Hiển thị thumbnail ảnh user gửi trong chat."""
        try:
            from PIL import Image as PILImage
            img_data = self.screen_analyzer.convert_to_bytes(image)

            pixmap = QPixmap()
            pixmap.loadFromData(img_data)

            # Scale to thumbnail
            max_w = 300
            if pixmap.width() > max_w:
                pixmap = pixmap.scaledToWidth(max_w, Qt.TransformationMode.SmoothTransformation)

            thumb_label = QLabel()
            thumb_label.setPixmap(pixmap)
            thumb_label.setStyleSheet(f"""
                border: 2px solid {COLORS['accent_primary']};
                border-radius: 8px;
                padding: 3px;
                background: {COLORS['bg_surface']};
            """)

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(80, 0, 46, 0)  # Align with user bubbles (right side)
            container_layout.setSpacing(0)
            container_layout.addWidget(thumb_label, alignment=Qt.AlignmentFlag.AlignRight)

            # Append container directly
            self._messages_layout.addWidget(container)

            QTimer.singleShot(50, self._scroll_to_bottom)

        except Exception as e:
            logger.error(f"[ChatPanel] Lỗi hiển thị user image thumbnail: {e}")

    def _on_response(self, result: dict):
        """Handle AI response — hỗ trợ multi-step tool execution loop."""
        text = result.get("text", "")
        tool_calls = result.get("tool_calls", [])
        timestamp = format_chat_timestamp(datetime.now())

        # Execute tool calls (with confirmation check)
        tool_results = []
        screenshot_image = None

        if tool_calls:
            # Check confirmation mode
            confirm_mode = self.state_manager.get_app_setting("confirm_mode", "auto")

            for tc in tool_calls:
                tool_name = tc["name"]

                if tool_name == "take_screenshot":
                    # Screenshot luôn thực hiện, không cần hỏi
                    screenshot_image = self.screen_analyzer.capture_and_resize()
                    if screenshot_image:
                        tool_results.append({
                            "name": "take_screenshot",
                            "args": {},
                            "result": "📸 Đã chụp screenshot thành công"
                        })
                    else:
                        tool_results.append({
                            "name": "take_screenshot",
                            "args": {},
                            "result": "⚠️ Không thể chụp screenshot"
                        })
                else:
                    # Check xác nhận theo chế độ
                    should_execute = True

                    if confirm_mode == "always_ask":
                        should_execute = self._confirm_tool_execution(tool_name, tc.get("args", {}))
                    elif confirm_mode == "ask_first":
                        # Kiểm tra tool đã được duyệt chưa
                        if not hasattr(self, '_approved_tools'):
                            self._approved_tools = set()
                        if tool_name not in self._approved_tools:
                            should_execute = self._confirm_tool_execution(tool_name, tc.get("args", {}))
                            if should_execute:
                                self._approved_tools.add(tool_name)
                    # confirm_mode == "auto" -> should_execute = True (mặc định)

                    if should_execute:
                        tool_result = self.action_executor.execute_tool_call(tool_name, tc.get("args", {}))
                        tool_results.append({"name": tool_name, "args": tc.get("args", {}), "result": tool_result})
                    else:
                        tool_results.append({"name": tool_name, "args": tc.get("args", {}), "result": "❌ Người dùng từ chối thực hiện"})

        # Build display text
        display_text = text
        if tool_results:
            results_summary = "\n".join(
                [f"✅ {r['result']}" if not r['result'].startswith(("⚠️", "❌", "✅", "📸")) else r['result']
                 for r in tool_results]
            )
            if not display_text:
                display_text = f"Đã thực thi:\n{results_summary}"
            else:
                display_text = f"{display_text}\n\n{results_summary}"

        # Hiển thị tool calls (trừ take_screenshot — sẽ hiển thị thumbnail riêng)
        display_tool_calls = [
            {"name": tc["name"], "args": tc["args"]}
            for tc in tool_calls
            if tc["name"] != "take_screenshot"
        ] or None

        # Add AI bubble
        self._add_bubble(display_text, is_user=False, timestamp=timestamp, tool_calls=display_tool_calls)

        # Save to history
        self.state_manager.save_chat_message(
            "assistant", display_text,
            session_id=self._current_session_id,
            tool_calls=tool_calls
        )
        self._update_session_header()

        # Nếu có screenshot → hiển thị thumbnail + gửi lại cho AI phân tích
        if screenshot_image:
            self._show_screenshot_thumbnail(screenshot_image)
            self._followup_with_screenshot(screenshot_image)
        elif tool_results and self._tool_loop_count < self._max_tool_loops:
            # MULTI-STEP: Nếu có tool_results → gửi kết quả lại cho AI để quyết định bước tiếp
            self._continue_tool_loop(tool_results)
        else:
            # Hoàn tất — enable UI
            self._typing_label.setVisible(False)
            self._send_btn.setEnabled(True)
            QTimer.singleShot(100, self._scroll_to_bottom)

    def _continue_tool_loop(self, tool_results: list):
        """Gửi kết quả tool thực thi lại cho AI để thực hiện bước tiếp theo (multi-step)."""
        self._tool_loop_count += 1
        step = self._tool_loop_count

        # Build follow-up message chứa kết quả tool
        results_text = "\n".join([f"- {r['name']}: {r['result']}" for r in tool_results])
        followup = (
            f"Tôi đã thực hiện các thao tác ở bước {step}. Kết quả:\n{results_text}\n\n"
            f"Hãy tiếp tục thực hiện các bước còn lại nếu có. "
            f"Nếu tất cả đã hoàn thành, hãy tóm tắt kết quả bằng text (không gọi thêm tool)."
        )

        # Update typing indicator
        self._typing_label.setText(f"🤖 AI Claw đang thực hiện bước {step + 1}/{self._max_tool_loops}...")
        self._typing_label.setVisible(True)
        self._send_btn.setEnabled(False)

        # Gửi follow-up cho AI
        self._worker = ChatWorker(
            self.ai_engine, followup,
            image=None,
            enable_tools=True
        )
        self._worker.response_ready.connect(self._on_response)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _confirm_tool_execution(self, tool_name: str, args: dict) -> bool:
        """Hiện dialog xác nhận trước khi thực hiện tool."""
        from PyQt6.QtWidgets import QMessageBox

        args_text = "\n".join([f"  • {k}: {v}" for k, v in args.items()]) if args else "  (không có tham số)"

        reply = QMessageBox.question(
            self,
            "🛡️ Xác nhận hành động",
            f"AI muốn thực hiện:\n\n"
            f"🔧 Tool: {tool_name}\n"
            f"📝 Tham số:\n{args_text}\n\n"
            f"Bạn có cho phép thực hiện không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return reply == QMessageBox.StandardButton.Yes

    def _show_screenshot_thumbnail(self, image: Image.Image):
        """Hiển thị screenshot thumbnail trong chat (WebP cho nhẹ)."""
        try:
            # Convert sang format cấu hình (mặc định WebP) qua screen_analyzer
            img_data = self.screen_analyzer.convert_to_bytes(image)

            pixmap = QPixmap()
            pixmap.loadFromData(img_data)

            # Scale to thumbnail
            max_w = 400
            if pixmap.width() > max_w:
                pixmap = pixmap.scaledToWidth(max_w, Qt.TransformationMode.SmoothTransformation)

            # Create thumbnail widget
            thumb_label = QLabel()
            thumb_label.setPixmap(pixmap)
            thumb_label.setStyleSheet(f"""
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 4px;
                background: {COLORS['bg_surface']};
            """)

            caption = QLabel("📸 Screenshot đã chụp — đang gửi cho AI phân tích...")
            caption.setStyleSheet(f"""
                color: {COLORS['accent_secondary']};
                font-size: 11px;
                font-style: italic;
                border: none;
                background: transparent;
                padding: 2px 0;
            """)

            container = QWidget()
            container_layout = QVBoxLayout(container)
            container_layout.setContentsMargins(46, 0, 80, 0)  # Align with AI bubbles (avatar offset)
            container_layout.setSpacing(4)
            container_layout.addWidget(thumb_label)
            container_layout.addWidget(caption)

            # Store reference to caption for later update
            self._screenshot_caption = caption

            # Append container directly
            self._messages_layout.addWidget(container)

            QTimer.singleShot(50, self._scroll_to_bottom)

        except Exception as e:
            logger.error(f"[ChatPanel] Lỗi hiển thị screenshot thumbnail: {e}")

    def _followup_with_screenshot(self, image: Image.Image):
        """Gửi screenshot cho AI phân tích tiếp."""
        self._typing_label.setText("🤖 AI Claw đang phân tích screenshot...")
        self._typing_label.setVisible(True)
        self._send_btn.setEnabled(False)

        # Lấy tin nhắn cuối cùng của user để biết context
        last_user_msg = ""
        for msg in reversed(self.ai_engine.conversation_history):
            if msg.get("role") == "user":
                last_user_msg = msg.get("content", "")
                break

        followup_msg = (
            f"Đây là screenshot tôi vừa chụp. "
            f"Hãy phân tích nội dung trên màn hình và trả lời câu hỏi trước đó của người dùng: "
            f'"{last_user_msg}"'
        ) if last_user_msg else (
            "Đây là screenshot tôi vừa chụp. "
            "Hãy phân tích và mô tả chi tiết nội dung trên màn hình."
        )

        self._worker = ChatWorker(
            self.ai_engine, followup_msg,
            image=image,
            enable_tools=False  # Không cho gọi tool nữa — tránh loop vô hạn
        )
        self._worker.response_ready.connect(self._on_screenshot_analysis)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_screenshot_analysis(self, result: dict):
        """Handle kết quả phân tích screenshot từ AI."""
        self._typing_label.setVisible(False)
        self._send_btn.setEnabled(True)

        text = result.get("text", "")
        timestamp = datetime.now().strftime("%H:%M")

        # Cập nhật caption của thumbnail
        if hasattr(self, '_screenshot_caption') and self._screenshot_caption:
            self._screenshot_caption.setText("📸 Screenshot đã được phân tích ✓")

        # Add AI analysis bubble
        if text:
            self._add_bubble(text, is_user=False, timestamp=timestamp)

            # Save to history
            self.state_manager.save_chat_message("assistant", text, session_id=self._current_session_id)
            self._update_session_header()

        QTimer.singleShot(100, self._scroll_to_bottom)

    def _on_error(self, error: str):
        """Handle AI error."""
        self._typing_label.setVisible(False)
        self._send_btn.setEnabled(True)

        timestamp = format_chat_timestamp(datetime.now())
        error_msg = f"❌ **Lỗi phản hồi từ AI**: {error}\n\n💡 *Gợi ý: Hãy kiểm tra lại API Key hoặc đổi sang mô hình khác trong mục Cài đặt (⚙️ Setting).* "
        self._add_bubble(error_msg, is_user=False, timestamp=timestamp)
        toast_error(f"Lỗi AI: {error[:80]}", self)

    def _add_bubble(self, text: str, is_user: bool = False, timestamp: str = "",
                    tool_calls: list = None):
        """Thêm bubble chat mới."""
        render_mode = self.state_manager.get_app_setting("chat_render_mode", "natural")
        bubble_style = self.state_manager.get_app_setting("chat_bubble_style", "bubble")

        bubble = ChatBubble(
            text, is_user=is_user, timestamp=timestamp,
            tool_calls=tool_calls, render_mode=render_mode,
            bubble_style=bubble_style
        )
        self._bubbles.append(bubble)

        # Wrap in alignment frame
        wrapper = QHBoxLayout()
        wrapper.setContentsMargins(0, 0, 0, 0)
        if is_user:
            wrapper.addSpacing(80)
            wrapper.addWidget(bubble, 1)
        else:
            wrapper.addWidget(bubble, 1)
            wrapper.addSpacing(80)

        container = QWidget()
        container.setLayout(wrapper)

        # Append container directly
        self._messages_layout.addWidget(container)

        # Scroll to bottom
        QTimer.singleShot(50, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        """Cuộn xuống cuối tin nhắn mới nhất."""
        QApplication.processEvents()
        if self._messages_layout.count() > 0:
            last_item = self._messages_layout.itemAt(self._messages_layout.count() - 1)
            if last_item and last_item.widget():
                last_w = last_item.widget()
                target_y = last_w.geometry().bottom() - self._scroll.viewport().height() + 24
                sb = self._scroll.verticalScrollBar()
                sb.setValue(max(0, min(target_y, sb.maximum())))
                return
        sb = self._scroll.verticalScrollBar()
        sb.setValue(sb.maximum())

    def _capture_screenshot(self):
        """Chụp screenshot và đính kèm."""
        # Ẩn cửa sổ app tạm thời
        main_window = self.window()
        if main_window:
            main_window.hide()

        QTimer.singleShot(500, self._do_capture)

    def _do_capture(self):
        """Thực hiện chụp screenshot (sau khi ẩn cửa sổ)."""
        img = self.screen_analyzer.capture_and_resize()

        # Hiện lại cửa sổ
        main_window = self.window()
        if main_window:
            main_window.show()
            main_window.activateWindow()

        if img:
            self._pending_image = img
            self._image_indicator.setText("📸 Đã chụp screenshot — sẽ gửi kèm tin nhắn tiếp theo")
            self._image_indicator.setVisible(True)
            logger.info("[ChatPanel] Đã chụp screenshot")
        else:
            self._add_bubble("⚠️ Không thể chụp screenshot", is_user=False,
                             timestamp=datetime.now().strftime("%H:%M"))

    def _attach_image(self):
        """Đính kèm ảnh từ file."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Chọn ảnh", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp);;All Files (*)"
        )
        if filepath:
            try:
                self._pending_image = Image.open(filepath)
                filename = os.path.basename(filepath)
                self._image_indicator.setText(f"📎 {filename} — sẽ gửi kèm tin nhắn tiếp theo")
                self._image_indicator.setVisible(True)
            except Exception as e:
                self._add_bubble(f"⚠️ Không thể mở ảnh: {e}", is_user=False)

    # ============================================================
    # SESSION & HISTORY MANAGEMENT METHODS
    # ============================================================

    def _update_session_header(self):
        """Cập nhật tên session và số lượng lịch sử trên header."""
        if not hasattr(self, '_session_btn') or not hasattr(self, '_history_btn'):
            return

        session_info = self.state_manager.get_chat_session(self._current_session_id)
        title = session_info.get("title", "Cuộc trò chuyện") if session_info else "Cuộc trò chuyện"
        short_title = title[:22] + "..." if len(title) > 22 else title
        self._session_btn.setText(f"💬 {short_title} ✏️")

        self._session_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_surface']};
                color: {COLORS['accent_primary']};
                border: 1px solid {COLORS['accent_primary']}66;
                border-radius: 15px;
                padding: 2px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_surface_hover']};
                border-color: {COLORS['accent_primary']};
            }}
        """)

        all_sessions = self.state_manager.get_all_chat_sessions()
        self._history_btn.setText(f"📜 Lịch sử ({len(all_sessions)})")

    def _switch_session(self, session_id: str):
        """Chuyển sang một phiên chat khác."""
        self._current_session_id = session_id
        self._update_session_header()
        # Defer load history để dialog kịp close + layout kịp update
        QTimer.singleShot(150, self._load_history)

    def _new_chat(self):
        """Tạo một phiên chat mới hoàn toàn."""
        new_session_id = self.state_manager.create_chat_session("Cuộc trò chuyện mới")
        self.ai_engine.clear_history()
        self._switch_session(new_session_id)
        toast_success("Đã tạo cuộc trò chuyện mới!", self)

    def _rename_current_session(self):
        """Đổi tên phiên chat hiện tại."""
        session_info = self.state_manager.get_chat_session(self._current_session_id)
        current_title = session_info.get("title", "Cuộc trò chuyện") if session_info else "Cuộc trò chuyện"

        new_title, ok = QInputDialog.getText(
            self, "✏️ Đổi tên cuộc trò chuyện",
            "Nhập tên mới cho cuộc trò chuyện hiện tại:",
            QLineEdit.EchoMode.Normal,
            current_title
        )
        if ok and new_title.strip():
            self.state_manager.rename_chat_session(self._current_session_id, new_title.strip())
            self._update_session_header()
            toast_success(f"Đã đổi tên thành: \"{new_title.strip()}\"", self)

    def _open_history_dialog(self):
        """Mở dialog quản lý lịch sử các phiên chat (xem, mở, đổi tên, xoá)."""
        from ui.chat_history_dialog import ChatHistoryDialog
        dlg = ChatHistoryDialog(self.state_manager, current_session_id=self._current_session_id, parent=self)
        dlg.session_selected.connect(self._switch_session)
        dlg.new_chat_requested.connect(self._new_chat)
        dlg.history_cleared.connect(self._new_chat)
        dlg.exec()
        self._update_session_header()

    def _clear_bubble_widgets(self):
        """Xoá toàn bộ widget tin nhắn trên giao diện."""
        while self._messages_layout.count() > 0:
            item = self._messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._bubbles.clear()

    def _add_welcome_bubble(self):
        """Thêm tin nhắn chào mừng mặc định."""
        self._add_bubble(
            "Xin chào! Tôi là AI Claw — Trợ lý Tự động hoá Thông minh. 🤖\n\n"
            "Tôi có thể giúp bạn:\n"
            "- Tự động hoá thao tác trên máy tính (click chuột, gõ phím, mở ứng dụng)\n"
            "- Tạo workflow tự động từ yêu cầu bằng tiếng Việt\n"
            "- Xử lý file hàng loạt và phân tích màn hình\n\n"
            "Hãy nhập câu hỏi hoặc mô tả công việc bạn muốn thực hiện nhé!",
            is_user=False,
            timestamp=format_chat_timestamp(datetime.now())
        )

    def _clear_chat(self):
        """Xoá nội dung của phiên chat hiện tại (với hộp thoại xác nhận)."""
        reply = QMessageBox.question(
            self,
            "🗑️ Xác nhận xoá chat",
            "Bạn có chắc muốn xoá toàn bộ tin nhắn trong cuộc trò chuyện này không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        # Dừng worker nếu đang chạy
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self._worker = None
            self._typing_label.setVisible(False)
            self._send_btn.setEnabled(True)

        # Xoá UI & AI history
        self._clear_bubble_widgets()
        self.ai_engine.clear_history()

        # Xoá DB của session hiện tại
        self.state_manager.clear_chat_history(session_id=self._current_session_id)

        # Welcome message
        self._add_welcome_bubble()
        self._update_session_header()
        toast_info("Đã xoá tin nhắn của cuộc trò chuyện", self)

    def _load_history(self):
        """Load lịch sử chat của phiên hiện tại từ database."""
        # Dừng worker nếu đang chạy
        if self._worker and self._worker.isRunning():
            self._worker.terminate()
            self._worker.wait()
            self._worker = None
            self._typing_label.setVisible(False)
            self._send_btn.setEnabled(True)

        self._clear_bubble_widgets()
        self.ai_engine.clear_history()

        # Đảm bảo layout cập nhật sau khi clear
        QApplication.processEvents()

        history = self.state_manager.get_chat_history(session_id=self._current_session_id, limit=80)

        if not history:
            self._add_welcome_bubble()
            self._update_session_header()
            return

        for idx, msg in enumerate(history):
            is_user = msg["role"] == "user"
            created = msg.get("created_at", "")
            timestamp = ""
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    timestamp = format_chat_timestamp(dt)
                except ValueError:
                    pass

            tool_calls = None
            if msg.get("tool_calls"):
                try:
                    import json
                    tool_calls = json.loads(msg["tool_calls"]) if isinstance(msg["tool_calls"], str) else msg["tool_calls"]
                except Exception:
                    pass

            self._add_bubble(msg["content"], is_user=is_user, timestamp=timestamp, tool_calls=tool_calls)

            # Khôi phục context cho AI engine
            if msg.get("role") in ("user", "assistant"):
                self.ai_engine.conversation_history.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

            # processEvents mỗi 10 bubbles để tránh đơ UI khi load history dài
            if (idx + 1) % 10 == 0:
                QApplication.processEvents()

        self._update_session_header()
        QTimer.singleShot(200, self._scroll_to_bottom)
