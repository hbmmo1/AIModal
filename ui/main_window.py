"""
Main Window — Hub chính của AI Claw.
Sidebar navigation + stacked panels + status bar.
"""

import os
import sys
import logging
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QStackedWidget, QFrame, QSizePolicy, QStatusBar,
    QSystemTrayIcon, QMenu, QMenuBar, QApplication, QMessageBox,
    QDialog, QTextEdit, QFileDialog, QGroupBox, QScrollArea
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QFont, QAction, QKeySequence

from ui.theme import (
    DARK_STYLESHEET, COLORS, get_sidebar_button_style, get_card_style,
    get_topbar_style, get_topbar_action_btn_style, build_stylesheet,
    apply_titlebar_theme, get_menubar_style, get_menu_style
)
from ui.toast import toast_success, toast_error, toast_warning, toast_info
from core.model_registry import PROVIDER_DISPLAY
from ui.chat_panel import ChatPanel
from ui.automation_panel import AutomationPanel
from ui.settings_dialog import SettingsDialog
from ui.log_viewer import LogViewer
from ui.image_panel import ImagePanel
from ui.knowledge_panel import KnowledgePanel
from ui.floating_widget import FloatingQuickAccessWidget

from core.ai_engine import GeminiAIEngine
from core.key_manager import KeyManager
from core.state_manager import StateManager
from core.action_executor import ActionExecutor
from core.screen_analyzer import ScreenAnalyzer
from core.image_generator import ImageGenerator
from core.knowledge_base import KnowledgeBase

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """Main Hub Window cho AI Claw."""

    def __init__(self, config: dict = None):
        super().__init__()
        self.config = config or {}

        # Khởi tạo Core Components
        self.key_manager = KeyManager()
        self.state_manager = StateManager()
        self.action_executor = ActionExecutor()
        self.screen_analyzer = ScreenAnalyzer()
        self.image_generator = ImageGenerator(key_manager=self.key_manager)
        self.knowledge_base = KnowledgeBase()

        # Khởi tạo AI Engine
        gemini_cfg = self.config.get("gemini", {})
        default_model = self.state_manager.get_app_setting("default_model", gemini_cfg.get("model_name", "gemini-3.7-flash-high"))
        
        self.ai_engine = GeminiAIEngine(
            api_key=gemini_cfg.get("api_key", ""),
            model_name=default_model,
            key_manager=self.key_manager,
        )
        self.ai_engine.set_tool_executor(self.action_executor.execute_tool_call)
        self.ai_engine.knowledge_base = self.knowledge_base
        self.ai_engine.screen_analyzer = self.screen_analyzer

        # Load cài đặt screenshot đã lưu
        self._load_screenshot_settings()

        # UI State
        self._current_page = 0
        self._sidebar_buttons: list[QPushButton] = []
        self.floating_widget = None

        self._setup_ui()
        self._setup_status_bar()
        self._setup_connections()
        self._update_status()
        self._apply_dark_titlebar()
        self._init_floating_widget()

        # Auto-refresh status mỗi 30s
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_status)
        self._status_timer.start(30000)

    def _apply_dark_titlebar(self):
        """Kích hoạt Windows DWM Dark Mode hoặc Light Mode cho thanh tiêu đề cửa sổ."""
        apply_titlebar_theme(self)

    def _setup_ui(self):
        """Thiết lập giao diện chính."""
        self.setWindowTitle("🤖 AI Claw — Trợ Lý Tự Động Hoá Thông Minh")
        self.setMinimumSize(1200, 750)
        self.resize(1400, 850)

        # Central widget
        self._central = QWidget()
        self._central.setObjectName("centralWidget")
        self.setCentralWidget(self._central)

        main_layout = QVBoxLayout(self._central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # === TOP HEADER BAR (Menu & Action Buttons) ===
        top_bar = self._create_top_header_bar()
        main_layout.addWidget(top_bar)

        # === MAIN CONTENT (Sidebar + Stack) ===
        self._content_widget = QWidget()
        self._content_widget.setObjectName("contentWidget")
        content_layout = QHBoxLayout(self._content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # === SIDEBAR ===
        sidebar = self._create_sidebar()
        content_layout.addWidget(sidebar)

        # === CONTENT AREA ===
        self.stack = QStackedWidget()
        self.stack.setObjectName("mainStack")

        # Page 0: AI Chat
        self.chat_panel = ChatPanel(
            ai_engine=self.ai_engine,
            state_manager=self.state_manager,
            screen_analyzer=self.screen_analyzer,
            action_executor=self.action_executor,
        )
        self.stack.addWidget(self.chat_panel)

        # Page 1: Automation
        self.automation_panel = AutomationPanel(
            action_executor=self.action_executor,
            screen_analyzer=self.screen_analyzer,
            state_manager=self.state_manager,
        )
        self.stack.addWidget(self.automation_panel)

        # Page 2: Image Generator
        self.image_panel = ImagePanel(image_generator=self.image_generator)
        self.stack.addWidget(self.image_panel)

        # Page 3: Knowledge Base
        self.knowledge_panel = KnowledgePanel(knowledge_base=self.knowledge_base)
        self.stack.addWidget(self.knowledge_panel)

        # Page 4: Dashboard
        self.dashboard_page = self._create_dashboard()
        self.stack.addWidget(self.dashboard_page)

        # Page 5: Log Viewer
        self.log_viewer = LogViewer(state_manager=self.state_manager)
        self.stack.addWidget(self.log_viewer)

        content_layout.addWidget(self.stack)
        main_layout.addWidget(self._content_widget, 1)

        # Default: Show AI Chat
        self._navigate_to(0)

    def _create_top_header_bar(self) -> QFrame:
        """Tạo thanh Top Header Bar tích hợp Menu & Quick Action Buttons."""
        top_bar = QFrame()
        top_bar.setObjectName("topHeaderBar")
        top_bar.setFixedHeight(42)
        top_bar.setStyleSheet(get_topbar_style())

        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(6)

        # 1. Mini App Title
        logo_lbl = QLabel("🤖 AI CLAW")
        logo_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        logo_lbl.setStyleSheet(f"color: {COLORS['accent_primary']}; border: none; padding-right: 4px;")
        layout.addWidget(logo_lbl)

        # 2. Menu Bar
        self._menu_bar = QMenuBar()
        self._menu_bar.setObjectName("topMenuBar")
        self._menu_bar.setStyleSheet(get_menubar_style())

        # --- Menu: File ---
        file_menu = self._menu_bar.addMenu("📁 File")
        file_menu.setStyleSheet(get_menu_style())

        act_open_wf = QAction("📂 Mở Kịch bản Workflow...", self)
        act_open_wf.triggered.connect(lambda: self._navigate_to(1))
        file_menu.addAction(act_open_wf)

        act_save_chat = QAction("💾 Xuất Lịch sử Chat...", self)
        act_save_chat.triggered.connect(self._handle_export_chat)
        file_menu.addAction(act_save_chat)

        file_menu.addSeparator()

        act_restart = QAction("🔄 Khởi động lại (Restart)", self)
        act_restart.triggered.connect(self._handle_restart)
        file_menu.addAction(act_restart)

        act_exit = QAction("❌ Thoát", self)
        act_exit.setShortcut("Alt+F4")
        act_exit.triggered.connect(self.close)
        file_menu.addAction(act_exit)

        # --- Menu: Edit ---
        edit_menu = self._menu_bar.addMenu("✏️ Edit")
        edit_menu.setStyleSheet(get_menu_style())

        act_clear_chat = QAction("🗑️ Xoá Cuộc trò chuyện", self)
        act_clear_chat.triggered.connect(lambda: self.chat_panel._clear_chat())
        edit_menu.addAction(act_clear_chat)

        act_reset = QAction("♻️ Reset Quota & AI State", self)
        act_reset.triggered.connect(self._handle_reset)
        edit_menu.addAction(act_reset)

        act_reload = QAction("🔃 Tải lại Cấu hình & Keys", self)
        act_reload.triggered.connect(self._handle_reload)
        edit_menu.addAction(act_reload)

        # --- Menu: View ---
        view_menu = self._menu_bar.addMenu("👁️ View")
        view_menu.setStyleSheet(get_menu_style())

        pages = [
            ("🤖 AI Chat", 0),
            ("🖱️ Automation Desktop", 1),
            ("🎨 Tạo ảnh AI", 2),
            ("🧠 Trí tuệ CÁ NHÂN", 3),
            ("📊 Dashboard", 4),
            ("📋 Activity Log", 5),
        ]
        for p_name, p_idx in pages:
            act_page = QAction(p_name, self)
            act_page.triggered.connect(lambda checked, idx=p_idx: self._navigate_to(idx))
            view_menu.addAction(act_page)

        view_menu.addSeparator()
        act_fullscreen = QAction("⛶ Bật / Tắt Toàn màn hình", self)
        act_fullscreen.setShortcut("F11")
        act_fullscreen.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(act_fullscreen)

        act_float = QAction("📌 Bật / Tắt Nút nổi Desktop", self)
        act_float.triggered.connect(self._toggle_float_from_btn)
        view_menu.addAction(act_float)

        # --- Menu: Settings ---
        settings_menu = self._menu_bar.addMenu("⚙️ Settings")
        settings_menu.setStyleSheet(get_menu_style())

        act_settings = QAction("⚙️ Cài đặt Đa Mô Hình & Keys...", self)
        act_settings.setShortcut("Ctrl+,")
        act_settings.triggered.connect(self._open_settings)
        settings_menu.addAction(act_settings)

        act_display_settings = QAction("💬 Tuỳ chọn Hiển thị Chat...", self)
        act_display_settings.triggered.connect(self._open_settings)
        settings_menu.addAction(act_display_settings)

        # --- Menu: Support ---
        support_menu = self._menu_bar.addMenu("❓ Support")
        support_menu.setStyleSheet(get_menu_style())

        act_help = QAction("❓ Hướng dẫn sử dụng & Phím tắt", self)
        act_help.setShortcut("F1")
        act_help.triggered.connect(self._handle_support)
        support_menu.addAction(act_help)

        act_logs = QAction("📋 Xem Nhật ký Hoạt động", self)
        act_logs.triggered.connect(lambda: self._navigate_to(5))
        support_menu.addAction(act_logs)

        act_about = QAction("ℹ️ Giới thiệu AI Claw", self)
        act_about.triggered.connect(self._handle_support)
        support_menu.addAction(act_about)

        self._top_menus = [file_menu, edit_menu, view_menu, settings_menu, support_menu]

        layout.addWidget(self._menu_bar)
        layout.addStretch()

        # 3. Quick Action Buttons on Top Bar
        self._topbar_action_btns = []
        self._topbar_actions = [
            ("📌 Float", "Bật/tắt thanh nút nổi thao tác nhanh trên Desktop", self._toggle_float_from_btn, "normal"),
            ("🔄 Restart", "Khởi động lại ứng dụng nhanh chóng", self._handle_restart, "warning"),
            ("♻️ Reset", "Reset Quota API Keys & bộ nhớ đệm AI", self._handle_reset, "normal"),
            ("🔃 Reload", "Tải lại cấu hình và nạp lại API Keys", self._handle_reload, "normal"),
            ("📸 Screenshot", "Chụp screenshot màn hình và gửi cho AI", self._handle_screenshot, "normal"),
            ("⚙️ Setting", "Mở cài đặt AI models & hiển thị", self._open_settings, "primary"),
            ("❓ Support", "Xem hướng dẫn và phím tắt", self._handle_support, "normal"),
        ]

        for text, tooltip, callback, variant in self._topbar_actions:
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setStyleSheet(get_topbar_action_btn_style(variant))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(28)
            btn.clicked.connect(callback)
            layout.addWidget(btn)
            self._topbar_action_btns.append((btn, variant))

        return top_bar

    def _create_sidebar(self) -> QFrame:
        """Tạo sidebar navigation."""
        self._sidebar_frame = QFrame()
        self._sidebar_frame.setObjectName("sidebarFrame")
        self._sidebar_frame.setFixedWidth(220)
        self._sidebar_frame.setStyleSheet(f"""
            QFrame#sidebarFrame {{
                background-color: {COLORS['sidebar_bg']};
                border-right: 1px solid {COLORS['border']};
            }}
        """)

        layout = QVBoxLayout(self._sidebar_frame)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo / App Title
        self._logo_frame = QFrame()
        self._logo_frame.setObjectName("logoFrame")
        self._logo_frame.setStyleSheet(f"""
            QFrame#logoFrame {{
                background-color: transparent;
                border-bottom: 1px solid {COLORS['border']};
                padding: 16px;
            }}
        """)
        logo_layout = QVBoxLayout(self._logo_frame)
        logo_layout.setContentsMargins(20, 20, 20, 16)

        self._logo_title = QLabel("🤖 AI Claw")
        self._logo_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        self._logo_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
        logo_layout.addWidget(self._logo_title)

        self._logo_subtitle = QLabel("Tự Động Hoá Thông Minh")
        self._logo_subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
        logo_layout.addWidget(self._logo_subtitle)

        layout.addWidget(self._logo_frame)

        # Navigation buttons
        nav_items = [
            ("🤖  AI Chat", "Trò chuyện với AI trợ lý"),
            ("🖱️  Automation", "Tự động hoá desktop"),
            ("🎨  Tạo ảnh AI", "Tạo ảnh bằng nhiều model AI"),
            ("🧠  Trí tuệ CÁ NHÂN", "Kiến thức & nhận thức cá nhân"),
            ("📊  Dashboard", "Tổng quan & thống kê"),
            ("📋  Activity Log", "Nhật ký hoạt động"),
        ]

        layout.addSpacing(8)

        for i, (text, tooltip) in enumerate(nav_items):
            btn = QPushButton(text)
            btn.setToolTip(tooltip)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFixedHeight(44)
            btn.clicked.connect(lambda checked, idx=i: self._navigate_to(idx))
            self._sidebar_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # Bottom section — Settings & Status
        self._bottom_sidebar_frame = QFrame()
        self._bottom_sidebar_frame.setObjectName("bottomSidebarFrame")
        self._bottom_sidebar_frame.setStyleSheet(f"border-top: 1px solid {COLORS['border']};")
        bottom_layout = QVBoxLayout(self._bottom_sidebar_frame)
        bottom_layout.setContentsMargins(8, 8, 8, 8)
        bottom_layout.setSpacing(4)

        # AI Status indicator
        self._ai_status_label = QLabel("● AI: Đang kết nối...")
        self._ai_status_label.setStyleSheet(f"color: {COLORS['warning']}; font-size: 11px; padding: 4px 12px;")
        bottom_layout.addWidget(self._ai_status_label)

        # Settings button
        self._settings_btn = QPushButton("⚙️  Cài đặt")
        self._settings_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                padding: 10px 20px;
                text-align: left;
                font-size: 13px;
            }}
            QPushButton:hover {{
                color: {COLORS['text_primary']};
                background-color: {COLORS['sidebar_hover']};
            }}
        """)
        self._settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._settings_btn.clicked.connect(self._open_settings)
        bottom_layout.addWidget(self._settings_btn)

        layout.addWidget(self._bottom_sidebar_frame)

        return self._sidebar_frame

    def _create_dashboard(self) -> QWidget:
        """Tạo trang Dashboard thống kê."""
        page = QWidget()
        page.setObjectName("dashboardPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(24)

        # Header
        header = QLabel("📊 Dashboard — Tổng Quan")
        header.setObjectName("titleLabel")
        header.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        layout.addWidget(header)

        # Stats cards
        stats_row = QHBoxLayout()
        stats_row.setSpacing(16)

        self._stat_cards = {}
        stats_data = [
            ("total_runs", "🚀 Tổng lần chạy", "0", COLORS["accent_primary"]),
            ("success_rate", "✅ Tỷ lệ thành công", "N/A", COLORS["success"]),
            ("time_saved", "⏱️ Thời gian tiết kiệm", "0s", COLORS["accent_secondary"]),
            ("total_chats", "💬 Tin nhắn AI", "0", COLORS["warning"]),
        ]

        for key, title, value, color in stats_data:
            card = self._create_stat_card(title, value, color)
            stats_row.addWidget(card)
            self._stat_cards[key] = card

        layout.addLayout(stats_row)

        # Welcome text
        welcome = QLabel(
            "🤖 Chào mừng đến với AI Claw!\n\n"
            "• Chuyển sang tab 'AI Chat' để trò chuyện với AI trợ lý\n"
            "• Mô tả công việc bằng tiếng Việt → AI sẽ tạo kịch bản tự động hoá\n"
            "• Sử dụng tab 'Automation' để tạo/chạy macro desktop\n"
            "• Nhấn Ctrl+Shift+S để chụp screenshot + AI phân tích"
        )
        welcome.setStyleSheet(f"""
            {get_card_style()}
            color: {COLORS['text_secondary']};
            font-size: 14px;
            line-height: 1.8;
        """)
        welcome.setWordWrap(True)
        layout.addWidget(welcome)

        layout.addStretch()

        return page

    def _create_stat_card(self, title: str, value: str, color: str) -> QFrame:
        """Tạo thẻ thống kê."""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
            }}
            QFrame:hover {{
                border-color: {color};
            }}
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(8)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 500; border: none;")
        card_layout.addWidget(title_lbl)

        value_lbl = QLabel(value)
        value_lbl.setObjectName("statValue")
        value_lbl.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: 700; border: none;")
        card_layout.addWidget(value_lbl)

        return card

    def _setup_status_bar(self):
        """Thiết lập status bar."""
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)

        self._status_model = QLabel("Model: —")
        self._status_keys = QLabel("Keys: —")
        self._status_tasks = QLabel("Tasks: 0")

        for lbl in [self._status_model, self._status_keys, self._status_tasks]:
            lbl.setStyleSheet("color: #64748b; font-size: 11px; padding: 0 8px;")

        status_bar.addWidget(self._status_model)
        status_bar.addWidget(self._status_keys)
        status_bar.addPermanentWidget(self._status_tasks)

    def _setup_connections(self):
        """Kết nối signals."""
        self.action_executor.log_message.connect(self._on_executor_log)

    def _navigate_to(self, index: int):
        """Chủển trang."""
        self._current_page = index
        self.stack.setCurrentIndex(index)

        # Update sidebar active state
        for i, btn in enumerate(self._sidebar_buttons):
            btn.setStyleSheet(get_sidebar_button_style(is_active=(i == index)))

    def _open_settings(self):
        """Mở Settings dialog."""
        import time
        logger.info("[MainWindow] Opening Settings dialog...")
        t0 = time.time()

        try:
            dialog = SettingsDialog(
                key_manager=self.key_manager,
                ai_engine=self.ai_engine,
                config=self.config,
                state_manager=self.state_manager,
                screen_analyzer=self.screen_analyzer,
                parent=self,
            )
            t1 = time.time()
            logger.info(f"[MainWindow] Settings dialog created in {t1 - t0:.2f}s")

            dialog.display_settings_changed.connect(self.chat_panel.refresh_display_mode)
            dialog.theme_changed.connect(self._apply_theme)
            dialog.exec()

            t2 = time.time()
            logger.info(f"[MainWindow] Settings dialog closed (total {t2 - t0:.2f}s)")
        except Exception as e:
            logger.error(f"[MainWindow] CRASH in Settings dialog: {e}", exc_info=True)

        self._update_status()
        self._load_screenshot_settings()  # Reload cài đặt screenshot sau khi đóng dialog

    def _handle_restart(self):
        """Khởi động lại ứng dụng."""
        reply = QMessageBox.question(
            self, "Khởi động lại",
            "Bạn có chắc chắn muốn khởi động lại AI Claw?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            import subprocess
            python_exe = sys.executable
            app_file = os.path.abspath(sys.argv[0])
            subprocess.Popen([python_exe, app_file])
            QApplication.quit()

    def _handle_reset(self):
        """Reset trạng thái và Quotas API keys."""
        reply = QMessageBox.question(
            self, "Reset Trạng Thái",
            "Bạn có muốn reset Quota toàn bộ API keys và làm mới kết nối AI Engine?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.key_manager.reset_all_quotas()
                self.ai_engine.clear_history()
                self.ai_engine._init_client()
                self._update_status()
                toast_success("♻️ Đã reset thành công Quotas và kết nối AI Engine.", self)
            except Exception as e:
                logger.error(f"[MainWindow] Lỗi reset: {e}", exc_info=True)
                toast_error(f"Lỗi reset: {e}", self)

    def _handle_reload(self):
        """Tải lại danh sách API keys và cấu hình."""
        try:
            self.key_manager.load_keys()
            self.ai_engine._init_client()
            self._update_status()
            if hasattr(self, 'chat_panel'):
                self.chat_panel.refresh_display_mode()
            toast_success("🔃 Đã tải lại danh sách API Keys và cấu hình thành công!", self)
        except Exception as e:
            logger.error(f"[MainWindow] Lỗi tải lại: {e}", exc_info=True)
            toast_error(f"Lỗi tải lại cấu hình: {e}", self)

    def _handle_screenshot(self):
        """Chụp nhanh screenshot và mở AI Chat."""
        self._navigate_to(0)
        self.chat_panel._capture_screenshot()

    def _handle_export_chat(self):
        """Xuất lịch sử chat ra file text."""
        history = self.state_manager.get_chat_history(limit=500)
        if not history:
            QMessageBox.information(self, "Xuất Chat", "Chưa có lịch sử chat để xuất.")
            return
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Lưu Lịch Sử Chat", "ai_claw_chat_history.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    for msg in history:
                        sender = "Bạn" if msg["role"] == "user" else "AI Claw"
                        f.write(f"[{msg.get('created_at', '')}] {sender}:\n{msg.get('content', '')}\n\n")
                QMessageBox.information(self, "Xuất Chat", f"✅ Đã lưu lịch sử chat vào:\n{filepath}")
            except Exception as e:
                QMessageBox.warning(self, "Lỗi", f"Không thể lưu file: {e}")

    def _toggle_fullscreen(self):
        """Bật / Tắt chế độ toàn màn hình."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _handle_support(self):
        """Mở hộp thoại Trợ giúp, Hướng dẫn & Phím tắt."""
        dialog = QDialog(self)
        dialog.setWindowTitle("❓ Hỗ Trợ & Hướng Dẫn Sử Dụng — AI Claw")
        dialog.setMinimumSize(600, 480)
        dialog.resize(650, 520)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("🤖 AI Claw — Trợ Lý Tự Động Hoá Thông Minh")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        layout.addWidget(title)

        desc = QLabel(
            "Nền tảng tự động hoá máy tính thông minh kết hợp đa mô hình AI (Gemini, ChatGPT, Claude, DeepSeek, Qwen).\n"
            "Hỗ trợ điều khiển chuột/phím, tạo ảnh, tra cứu nhận thức và phân tích màn hình theo thời gian thực."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; line-height: 1.5;")
        layout.addWidget(desc)

        # Phím tắt
        hotkeys_group = QGroupBox("⌨️ Danh Sách Phím Tắt Tiện Ích")
        hotkeys_layout = QVBoxLayout(hotkeys_group)
        hotkeys_text = QLabel(
            "• <b>Ctrl+Shift+S</b> : Chụp screenshot và gửi AI phân tích ngay\n"
            "• <b>Ctrl+Shift+A</b> : Chuyển nhanh sang tab AI Chat\n"
            "• <b>F8</b> : Bắt đầu chạy kịch bản tự động hoá\n"
            "• <b>F9</b> : Tạm dừng / Tiếp tục macro\n"
            "• <b>F10</b> : Dừng khẩn cấp toàn bộ tác vụ\n"
            "• <b>F11</b> : Bật / Tắt toàn màn hình\n"
            "• <b>Enter</b> : Gửi tin nhắn chat\n"
            "• <b>Shift+Enter</b> : Xuống dòng trong khung chat"
        )
        hotkeys_text.setTextFormat(Qt.TextFormat.RichText)
        hotkeys_text.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 12px; line-height: 1.6;")
        hotkeys_layout.addWidget(hotkeys_text)
        layout.addWidget(hotkeys_group)

        # Quick Tips
        tips_group = QGroupBox("💡 Mẹo Sử Dụng Hiệu Quả")
        tips_layout = QVBoxLayout(tips_group)
        tips_text = QLabel(
            "• Đổi kiểu hiển thị tin nhắn (Văn bản tự nhiên / Markdown) trong <b>⚙️ Cài đặt → Tuỳ chọn Hiển thị</b>.\n"
            "• Dùng nút <b>🔄 Restart</b> trên thanh công cụ để khởi động lại app khi cần nạp lại tài nguyên.\n"
            "• Bấm <b>🔃 Reload</b> sau khi cập nhật file <code>.env</code> hoặc danh sách API keys mới."
        )
        tips_text.setTextFormat(Qt.TextFormat.RichText)
        tips_text.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px; line-height: 1.5;")
        tips_layout.addWidget(tips_text)
        layout.addWidget(tips_group)

        layout.addStretch()

        close_btn = QPushButton("Đã hiểu")
        close_btn.setObjectName("primaryButton")
        close_btn.setFixedHeight(36)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)

        dialog.exec()

    def _update_status(self):
        """Cập nhật status bar và AI indicator."""
        status = self.ai_engine.get_status()

        # Status bar
        prov_icon = status.get('provider_icon', '⚡')
        model_name = status.get('model_name', status['model'])
        self._status_model.setText(f"{prov_icon} {model_name}")
        self._status_keys.setText(f"Keys: {status['available_keys']}/{status['total_keys']}")

        # AI status indicator
        if status["connected"]:
            prov_name = status.get('provider_name', 'AI')
            tier = status.get('model_tier', '')
            self._ai_status_label.setText(f"● {prov_name}\n  {model_name} {tier}")
            self._ai_status_label.setStyleSheet(f"color: {COLORS['success']}; font-size: 11px; padding: 4px 12px;")
        else:
            self._ai_status_label.setText("○ AI: Chưa kết nối")
            self._ai_status_label.setStyleSheet(f"color: {COLORS['error']}; font-size: 11px; padding: 4px 12px;")

        # Dashboard stats
        try:
            stats = self.state_manager.get_dashboard_stats()
            for key, card in self._stat_cards.items():
                value_lbl = card.findChild(QLabel, "statValue")
                if value_lbl and key in stats:
                    value_lbl.setText(str(stats[key]))
        except Exception:
            pass

    def _on_executor_log(self, message: str):
        """Handle log từ executor."""
        logger.info(f"[Executor] {message}")

    def closeEvent(self, event):
        """Xử lý đóng ứng dụng."""
        reply = QMessageBox.question(
            self, "Xác nhận thoát",
            "Bạn có muốn thoát AI Claw?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

    def _load_screenshot_settings(self):
        """Load cài đặt screenshot đã lưu từ database và áp dụng cho screen_analyzer."""
        try:
            monitor_mode = self.state_manager.get_app_setting("screenshot_monitor", "all")
            image_format = self.state_manager.get_app_setting("screenshot_format", "webp")
            image_quality = self.state_manager.get_app_setting("screenshot_quality", "100")

            self.screen_analyzer.set_monitor_mode(monitor_mode)
            self.screen_analyzer.set_image_format(image_format)
            self.screen_analyzer.set_image_quality(int(image_quality))
        except Exception as e:
            logger.warning(f"[MainWindow] Lỗi load screenshot settings: {e}")

    def _apply_theme(self):
        """Rebuild và áp dụng stylesheet khi theme/density thay đổi."""
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.theme import build_stylesheet, get_sidebar_button_style, get_topbar_style, get_topbar_action_btn_style, apply_titlebar_theme
            app = QApplication.instance()
            if app:
                app.setStyleSheet(build_stylesheet())

            # Cập nhật Windows titlebar theme
            apply_titlebar_theme(self)

            # Refresh sidebar
            if hasattr(self, '_sidebar_frame'):
                self._sidebar_frame.setStyleSheet(f"""
                    QFrame#sidebarFrame {{
                        background-color: {COLORS['sidebar_bg']};
                        border-right: 1px solid {COLORS['border']};
                    }}
                """)
            if hasattr(self, '_logo_frame'):
                self._logo_frame.setStyleSheet(f"""
                    QFrame#logoFrame {{
                        background-color: transparent;
                        border-bottom: 1px solid {COLORS['border']};
                        padding: 16px;
                    }}
                """)
            if hasattr(self, '_logo_title'):
                self._logo_title.setStyleSheet(f"color: {COLORS['text_primary']}; background: transparent;")
            if hasattr(self, '_logo_subtitle'):
                self._logo_subtitle.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px; background: transparent;")
            if hasattr(self, '_bottom_sidebar_frame'):
                self._bottom_sidebar_frame.setStyleSheet(f"border-top: 1px solid {COLORS['border']};")
            if hasattr(self, '_settings_btn'):
                self._settings_btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: {COLORS['text_secondary']};
                        border: none;
                        padding: 10px 20px;
                        text-align: left;
                        font-size: 13px;
                    }}
                    QPushButton:hover {{
                        color: {COLORS['text_primary']};
                        background-color: {COLORS['sidebar_hover']};
                    }}
                """)

            # Refresh sidebar nav buttons
            current_idx = self.stack.currentIndex() if hasattr(self, 'stack') else 0
            for i, btn in enumerate(self._sidebar_buttons):
                btn.setStyleSheet(get_sidebar_button_style(is_active=(i == current_idx)))

            # Refresh topbar
            top_bar = self.findChild(QFrame, "topHeaderBar")
            if top_bar:
                top_bar.setStyleSheet(get_topbar_style())

            # Refresh topbar menu & popups
            if hasattr(self, '_menu_bar'):
                self._menu_bar.setStyleSheet(get_menubar_style())
            if hasattr(self, '_top_menus'):
                for m in self._top_menus:
                    m.setStyleSheet(get_menu_style())

            # Refresh topbar action buttons
            if hasattr(self, '_topbar_action_btns'):
                for btn, variant in self._topbar_action_btns:
                    btn.setStyleSheet(get_topbar_action_btn_style(variant))

            # Refresh child panels
            if hasattr(self, 'chat_panel') and hasattr(self.chat_panel, 'refresh_theme'):
                self.chat_panel.refresh_theme()
            elif hasattr(self, 'chat_panel'):
                self.chat_panel.refresh_display_mode()

            if hasattr(self, 'automation_panel') and hasattr(self.automation_panel, 'refresh_theme'):
                self.automation_panel.refresh_theme()

            if hasattr(self, 'image_panel') and hasattr(self.image_panel, 'refresh_theme'):
                self.image_panel.refresh_theme()

            if hasattr(self, 'knowledge_panel') and hasattr(self.knowledge_panel, 'refresh_theme'):
                self.knowledge_panel.refresh_theme()

            if hasattr(self, 'log_viewer') and hasattr(self.log_viewer, 'refresh_theme'):
                self.log_viewer.refresh_theme()

            # Dashboard page uses global stylesheet #dashboardPage

            # Refresh Floating Widget theme
            if hasattr(self, 'floating_widget') and self.floating_widget:
                self.floating_widget.update_theme()

            # Update status indicator
            self._update_status()

            logger.info("[MainWindow] Đã áp dụng theme mới toàn diện")
        except Exception as e:
            logger.error(f"[MainWindow] Lỗi áp dụng theme: {e}")

    def _init_floating_widget(self):
        """Khởi tạo thanh nút nổi truy cập nhanh (Floating Quick Access Widget)."""
        try:
            self.floating_widget = FloatingQuickAccessWidget(state_manager=self.state_manager)
            self.floating_widget.expand_requested.connect(self.restore_and_focus_window)
            self.floating_widget.screenshot_requested.connect(self._handle_screenshot)
            self.floating_widget.chat_requested.connect(self._handle_float_chat)
            self.floating_widget.settings_requested.connect(self._open_settings)

            is_enabled = self.state_manager.get_app_setting("float_widget_enabled", "1") != "0"
            if is_enabled:
                self.floating_widget.show()
                logger.info("[MainWindow] Floating Quick Access Widget đã khởi chạy")
        except Exception as e:
            logger.error(f"[MainWindow] Lỗi khởi tạo FloatingWidget: {e}", exc_info=True)

    def restore_and_focus_window(self):
        """Mở rộng và đưa cửa sổ chính lên trên cùng màn hình."""
        if self.isMinimized():
            self.showNormal()
        else:
            self.show()
        self.raise_()
        self.activateWindow()

    def _handle_float_chat(self):
        """Mở cửa sổ chính và focus vào khung Chat."""
        self.restore_and_focus_window()
        self._navigate_to(0)
        if hasattr(self, 'chat_panel') and hasattr(self.chat_panel, 'txt_input'):
            self.chat_panel.txt_input.setFocus()

    def toggle_floating_widget(self, enable: bool):
        """Bật / Tắt hiển thị floating widget."""
        if not hasattr(self, 'floating_widget') or not self.floating_widget:
            return
        if enable:
            self.floating_widget.show()
            self.floating_widget.raise_()
        else:
            self.floating_widget.hide()

    def _toggle_float_from_btn(self):
        """Bật / Tắt float widget từ nút trên thanh topbar / menu."""
        if not hasattr(self, 'floating_widget') or not self.floating_widget:
            return
        is_visible = self.floating_widget.isVisible()
        new_state = not is_visible
        self.toggle_floating_widget(new_state)
        self.state_manager.set_app_setting("float_widget_enabled", "1" if new_state else "0")
        if new_state:
            toast_success("📌 Đã hiển thị nút nổi truy cập nhanh trên Desktop!", self)
        else:
            toast_info("📌 Đã ẩn nút nổi truy cập nhanh.", self)

    def closeEvent(self, event):
        """Đóng ứng dụng và giải phóng floating widget."""
        try:
            if hasattr(self, 'floating_widget') and self.floating_widget:
                self.floating_widget.close()
        except Exception:
            pass
        super().closeEvent(event)
