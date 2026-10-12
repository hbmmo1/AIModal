"""
Theme — Dark & Light Theme cho AI Claw.
Hỗ trợ:
  - Dark Mode (mặc định) / Light Mode
  - UI Density: Material / Compact / Lite Compact / Super Compact
Chuẩn pattern 200CanvaTool với glassmorphism, vibrant accents, smooth transitions.
"""

# ============================================================
# Color Palettes
# ============================================================
COLORS_DARK = {
    "bg_primary": "#0b0f19",       # Slate 950 — nền chính tối sâu
    "bg_secondary": "#111827",     # Gray 900
    "bg_surface": "#1e293b",       # Slate 800 — card/panel
    "bg_surface_hover": "#283548", # Slate 700 hover
    "bg_elevated": "#334155",      # Slate 700 — elevated elements
    "bg_input": "#0f172a",         # Slate 900 — input fields

    "text_primary": "#f8fafc",     # Slate 50 — chữ chính sáng nét
    "text_secondary": "#cbd5e1",   # Slate 300 — chữ phụ tương phản cao
    "text_muted": "#94a3b8",       # Slate 400 — mô tả dễ đọc
    "text_disabled": "#64748b",    # Slate 500

    "accent_primary": "#6366f1",   # Indigo 500
    "accent_primary_hover": "#818cf8",  # Indigo 400
    "accent_secondary": "#06b6d4", # Cyan 500
    "accent_secondary_hover": "#22d3ee", # Cyan 400

    "success": "#22c55e",          # Green 500
    "success_bg": "#052e16",       # Green 950
    "warning": "#f59e0b",          # Amber 500
    "warning_bg": "#451a03",       # Amber 950
    "error": "#ef4444",            # Red 500
    "error_bg": "#450a0a",         # Red 950
    "info": "#3b82f6",             # Blue 500

    "border": "#2e3b52",           # Slate 700/800 — viền rõ nét
    "border_focus": "#6366f1",     # Indigo 500
    "border_subtle": "#1e293b",    # Subtle border

    "sidebar_bg": "#0d1321",       # Dark sidebar
    "sidebar_active": "#1e2b48",   # Active sidebar item
    "sidebar_hover": "#162035",    # Hover sidebar item

    "chat_user_bg": "#1e3a5f",     # User bubble
    "chat_ai_bg": "#1e293b",       # AI bubble
    "chat_system_bg": "#162032",   # System message
}

COLORS_LIGHT = {
    "bg_primary": "#f8fafc",       # Slate 50 — nền chính sáng nhẹ, sạch sẽ
    "bg_secondary": "#ffffff",     # White — nền header, pane, panels
    "bg_surface": "#ffffff",       # White — cards, groupbox, buttons
    "bg_surface_hover": "#f1f5f9", # Slate 100 — hover state
    "bg_elevated": "#e2e8f0",      # Slate 200 — border / elevated
    "bg_input": "#ffffff",         # White — input fields

    "text_primary": "#0f172a",     # Slate 900 — chữ chính đậm, cực rõ nét
    "text_secondary": "#334155",   # Slate 700 — chữ phụ rõ ràng, không bị mờ
    "text_muted": "#475569",       # Slate 600 — mô tả, ghi chú dễ đọc
    "text_disabled": "#94a3b8",    # Slate 400 — disabled text

    "accent_primary": "#4f46e5",   # Indigo 600
    "accent_primary_hover": "#6366f1",  # Indigo 500
    "accent_secondary": "#0891b2", # Cyan 600
    "accent_secondary_hover": "#06b6d4", # Cyan 500

    "success": "#16a34a",          # Green 600
    "success_bg": "#dcfce7",       # Green 100
    "warning": "#d97706",          # Amber 600
    "warning_bg": "#fef3c7",       # Amber 100
    "error": "#dc2626",            # Red 600
    "error_bg": "#fee2e2",         # Red 100
    "info": "#2563eb",             # Blue 600

    "border": "#cbd5e1",           # Slate 300 — viền rõ ràng, thanh lịch
    "border_focus": "#4f46e5",     # Indigo 600
    "border_subtle": "#e2e8f0",    # Slate 200

    "sidebar_bg": "#f1f5f9",       # Slate 100 — sidebar sáng tinh tế
    "sidebar_active": "#e0e7ff",   # Indigo 100 — active item
    "sidebar_hover": "#e2e8f0",    # Slate 200 — hover item

    "chat_user_bg": "#e0e7ff",     # Indigo 100 — soft user bubble
    "chat_ai_bg": "#ffffff",       # White — clean AI bubble
    "chat_system_bg": "#f8fafc",   # Slate 50
}

# Active COLORS dict — will be swapped by set_theme()
COLORS = dict(COLORS_DARK)

# ============================================================
# UI Density Configuration
# ============================================================
DENSITY_MATERIAL = "material"
DENSITY_COMPACT = "compact"
DENSITY_LITE_COMPACT = "lite_compact"
DENSITY_SUPER_COMPACT = "super_compact"

DENSITY_CONFIG = {
    DENSITY_MATERIAL: {
        "name": "Material",
        "icon": "📐",
        "desc": "Rộng rãi, chuẩn Material Design — thoáng mắt, dễ đọc",
        "padding_btn": "8px 16px",
        "padding_input": "8px 12px",
        "padding_card": "16px",
        "padding_cell": "8px 12px",
        "padding_sidebar": "14px 20px",
        "padding_chat": "12px 16px",
        "margin_group_top": "16px",
        "font_size": "13px",
        "font_size_small": "12px",
        "font_size_large": "14px",
        "border_radius": "8px",
        "border_radius_lg": "12px",
        "spacing": "12px",
        "min_btn_height": "20px",
        "avatar_size": "36",
        "scrollbar_width": "8px",
    },
    DENSITY_COMPACT: {
        "name": "Compact",
        "icon": "📦",
        "desc": "Giảm nhẹ padding, vẫn dễ đọc",
        "padding_btn": "6px 12px",
        "padding_input": "6px 10px",
        "padding_card": "12px",
        "padding_cell": "6px 10px",
        "padding_sidebar": "10px 16px",
        "padding_chat": "10px 14px",
        "margin_group_top": "12px",
        "font_size": "13px",
        "font_size_small": "11px",
        "font_size_large": "13px",
        "border_radius": "6px",
        "border_radius_lg": "10px",
        "spacing": "8px",
        "min_btn_height": "18px",
        "avatar_size": "32",
        "scrollbar_width": "6px",
    },
    DENSITY_LITE_COMPACT: {
        "name": "Lite Compact",
        "icon": "📋",
        "desc": "Nhỏ gọn vừa phải — tiết kiệm diện tích",
        "padding_btn": "4px 10px",
        "padding_input": "5px 8px",
        "padding_card": "10px",
        "padding_cell": "5px 8px",
        "padding_sidebar": "8px 14px",
        "padding_chat": "8px 12px",
        "margin_group_top": "10px",
        "font_size": "12px",
        "font_size_small": "10px",
        "font_size_large": "12px",
        "border_radius": "6px",
        "border_radius_lg": "8px",
        "spacing": "6px",
        "min_btn_height": "16px",
        "avatar_size": "28",
        "scrollbar_width": "5px",
    },
    DENSITY_SUPER_COMPACT: {
        "name": "Super Compact",
        "icon": "🔬",
        "desc": "Siêu nhỏ gọn — tối đa diện tích hiển thị",
        "padding_btn": "3px 8px",
        "padding_input": "4px 6px",
        "padding_card": "6px",
        "padding_cell": "3px 6px",
        "padding_sidebar": "6px 10px",
        "padding_chat": "6px 8px",
        "margin_group_top": "8px",
        "font_size": "11px",
        "font_size_small": "10px",
        "font_size_large": "11px",
        "border_radius": "4px",
        "border_radius_lg": "6px",
        "spacing": "4px",
        "min_btn_height": "14px",
        "avatar_size": "24",
        "scrollbar_width": "4px",
    },
}

# ============================================================
# Font Size Configuration
# ============================================================
FONT_SIZE_SMALL = "small"
FONT_SIZE_SLIGHTLY_SMALL = "slightly_small"
FONT_SIZE_MEDIUM = "medium"
FONT_SIZE_SLIGHTLY_LARGE = "slightly_large"
FONT_SIZE_LARGE = "large"
FONT_SIZE_EXTRA_LARGE = "extra_large"

FONT_SIZE_CONFIG = {
    FONT_SIZE_SMALL: {
        "name": "Nhỏ",
        "icon": "🔤",
        "desc": "Cỡ chữ nhỏ (11px) — tiết kiệm diện tích tối đa",
        "font_size": "11px",
        "font_size_small": "10px",
        "font_size_large": "12px",
        "font_size_title": "15px",
    },
    FONT_SIZE_SLIGHTLY_SMALL: {
        "name": "Hơi nhỏ",
        "icon": "🔤",
        "desc": "Cỡ chữ hơi nhỏ (12px) — gọn gàng, thanh thoát",
        "font_size": "12px",
        "font_size_small": "11px",
        "font_size_large": "13px",
        "font_size_title": "16px",
    },
    FONT_SIZE_MEDIUM: {
        "name": "Vừa phải (Mặc định)",
        "icon": "📐",
        "desc": "Cỡ chữ vừa chuẩn (13px) — cân bằng, dễ đọc",
        "font_size": "13px",
        "font_size_small": "12px",
        "font_size_large": "14px",
        "font_size_title": "17px",
    },
    FONT_SIZE_SLIGHTLY_LARGE: {
        "name": "Hơi lớn",
        "icon": "🔍",
        "desc": "Cỡ chữ hơi lớn (15px) — thoải mái cho mắt",
        "font_size": "15px",
        "font_size_small": "13px",
        "font_size_large": "16px",
        "font_size_title": "19px",
    },
    FONT_SIZE_LARGE: {
        "name": "Lớn",
        "icon": "🔍",
        "desc": "Cỡ chữ lớn (17px) — chữ to rõ ràng, không mỏi mắt",
        "font_size": "17px",
        "font_size_small": "14px",
        "font_size_large": "18px",
        "font_size_title": "21px",
    },
    FONT_SIZE_EXTRA_LARGE: {
        "name": "Rất lớn",
        "icon": "🔎",
        "desc": "Cỡ chữ rất lớn (19px) — dễ đọc từ xa",
        "font_size": "19px",
        "font_size_small": "16px",
        "font_size_large": "21px",
        "font_size_title": "24px",
    },
}

# Active density, font size, theme
_current_density = DENSITY_MATERIAL
_current_font_size = FONT_SIZE_MEDIUM
_current_theme = "dark"


def set_theme(theme: str = "dark"):
    """Chuyển đổi theme (dark/light). Cập nhật COLORS dict toàn cục."""
    global COLORS, _current_theme
    _current_theme = theme
    source = COLORS_LIGHT if theme == "light" else COLORS_DARK
    COLORS.clear()
    COLORS.update(source)


def set_density(density: str = DENSITY_MATERIAL):
    """Đặt mật độ hiển thị."""
    global _current_density
    if density in DENSITY_CONFIG:
        _current_density = density


def get_density() -> dict:
    """Lấy config density hiện tại."""
    return DENSITY_CONFIG.get(_current_density, DENSITY_CONFIG[DENSITY_MATERIAL])


def set_font_size(size_key: str = FONT_SIZE_MEDIUM):
    """Đặt cỡ chữ hiển thị."""
    global _current_font_size
    if size_key in FONT_SIZE_CONFIG:
        _current_font_size = size_key


def get_font_size_config() -> dict:
    """Lấy config cỡ chữ hiện tại."""
    return FONT_SIZE_CONFIG.get(_current_font_size, FONT_SIZE_CONFIG[FONT_SIZE_MEDIUM])


def get_current_font_size_key() -> str:
    return _current_font_size


def get_current_theme() -> str:
    return _current_theme


def get_current_density_key() -> str:
    return _current_density


def apply_titlebar_theme(widget, theme: str = None):
    """
    Kích hoạt Windows DWM Dark Mode (1) hoặc Light Mode (0) cho thanh tiêu đề của cửa sổ / dialog.
    """
    import sys
    if sys.platform == "win32":
        try:
            import ctypes
            current = theme or _current_theme
            hwnd = int(widget.winId())
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            val = 1 if current == "dark" else 0
            value = ctypes.c_int(val)
            res = ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value), ctypes.sizeof(value)
            )
            if res != 0:
                ctypes.windll.dwmapi.DwmSetWindowAttribute(
                    hwnd, 19,
                    ctypes.byref(value), ctypes.sizeof(value)
                )
        except Exception as e:
            pass


# ============================================================
# Stylesheet Generator
# ============================================================
def build_stylesheet() -> str:
    """Xây dựng stylesheet dựa trên COLORS, density và font size hiện tại."""
    C = COLORS
    D = get_density()
    F = get_font_size_config()

    return f"""
/* ============================================================
   GLOBAL RESET & TYPOGRAPHY
   ============================================================ */
* {{
    font-family: 'Segoe UI', 'Inter', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
    font-size: {F['font_size']};
    outline: none;
}}

QMainWindow, QDialog {{
    background-color: {C['bg_primary']};
    color: {C['text_primary']};
}}

/* Central & Content Containers */
QWidget#centralWidget, QWidget#contentWidget, QStackedWidget {{
    background-color: {C['bg_primary']};
    color: {C['text_primary']};
}}

/* Main Panels */
ChatPanel, AutomationPanel, ImagePanel, KnowledgePanel, LogViewer, QWidget#dashboardPage {{
    background-color: {C['bg_primary']};
    color: {C['text_primary']};
}}

/* Scroll Area & Viewport */
QScrollArea {{
    background-color: {C['bg_primary']};
    border: none;
}}
QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
    background-color: {C['bg_primary']};
    color: {C['text_primary']};
}}

QFrame#dialogHeader {{
    background-color: {C['bg_secondary']};
    border-bottom: 1px solid {C['border']};
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
}}

QLabel#dialogTitle {{
    color: {C['text_primary']};
    font-size: 16px;
    font-weight: 700;
}}

QLabel {{
    color: {C['text_primary']};
}}

/* ============================================================
   SCROLLBARS
   ============================================================ */
QScrollBar:vertical {{
    background: {C['bg_input']};
    width: {D['scrollbar_width']};
    margin: 0;
    border-radius: {int(D['scrollbar_width'].replace('px',''))//2}px;
}}
QScrollBar::handle:vertical {{
    background: {C['bg_elevated']};
    min-height: 24px;
    border-radius: {int(D['scrollbar_width'].replace('px',''))//2}px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['text_disabled']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}

QScrollBar:horizontal {{
    background: {C['bg_input']};
    height: {D['scrollbar_width']};
    margin: 0;
    border-radius: {int(D['scrollbar_width'].replace('px',''))//2}px;
}}
QScrollBar::handle:horizontal {{
    background: {C['bg_elevated']};
    min-width: 24px;
    border-radius: {int(D['scrollbar_width'].replace('px',''))//2}px;
}}
QScrollBar::handle:horizontal:hover {{ background: {C['text_disabled']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0px; }}

/* ============================================================
   BUTTONS
   ============================================================ */
QPushButton {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: {D['border_radius']};
    padding: {D['padding_btn']};
    font-size: {D['font_size']};
    font-weight: 500;
    min-height: {D['min_btn_height']};
}}
QPushButton:hover {{
    background-color: {C['bg_surface_hover']};
    border-color: {C['accent_primary']};
    color: {C['text_primary']};
}}
QPushButton:pressed {{
    background-color: {C['accent_primary']};
    color: #ffffff;
}}
QPushButton:disabled {{
    background-color: {C['bg_secondary']};
    color: {C['text_disabled']};
    border-color: {C['border']};
}}

QPushButton#primaryButton, QPushButton[class="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {C['accent_primary']}, stop:1 {C['accent_primary_hover']});
    color: #ffffff;
    border: none;
    font-weight: 600;
}}
QPushButton#primaryButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {C['accent_primary_hover']}, stop:1 {C['accent_primary']});
}}

QPushButton#dangerButton {{
    background-color: {C['error_bg']};
    color: {C['error']};
    border: 1px solid {C['error']};
}}
QPushButton#dangerButton:hover {{
    background-color: {C['error']};
    color: #ffffff;
}}

QPushButton#successButton {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {C['success']}, stop:1 {C['success']});
    color: #ffffff;
    border: none;
}}

/* ============================================================
   INPUT FIELDS
   ============================================================ */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background-color: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: {D['border_radius']};
    padding: {D['padding_input']};
    font-size: {D['font_size']};
    selection-background-color: {C['accent_primary']};
    selection-color: #ffffff;
}}
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
    border-color: {C['accent_primary']};
    background-color: {C['bg_input']};
}}
QLineEdit:disabled {{
    background-color: {C['bg_secondary']};
    color: {C['text_disabled']};
}}

QTextEdit#chatInput {{
    border-radius: {D['border_radius_lg']};
    padding: {D['padding_input']};
    font-size: {D['font_size_large']};
    min-height: 40px;
    max-height: 120px;
}}

/* ============================================================
   COMBO BOX
   ============================================================ */
QComboBox {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: {D['border_radius']};
    padding: {D['padding_btn']};
    min-height: {D['min_btn_height']};
}}
QComboBox:hover {{ border-color: {C['accent_primary']}; }}
QComboBox::drop-down {{
    border: none;
    width: 24px;
}}
QComboBox::down-arrow {{
    image: none;
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {C['text_secondary']};
}}
QComboBox QAbstractItemView {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: {D['border_radius']};
    padding: 4px;
    selection-background-color: {C['accent_primary']};
    selection-color: #ffffff;
}}

/* ============================================================
   SPIN BOX & SLIDER
   ============================================================ */
QSpinBox, QDoubleSpinBox {{
    background-color: {C['bg_input']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    padding: 4px 8px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{ border-color: {C['accent_primary']}; }}

QSlider::groove:horizontal {{
    height: 6px;
    background: {C['border']};
    border-radius: 3px;
}}
QSlider::handle:horizontal {{
    background: {C['accent_primary']};
    width: 16px;
    height: 16px;
    margin: -5px 0;
    border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{ background: {C['accent_primary_hover']}; }}
QSlider::sub-page:horizontal {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C['accent_primary']}, stop:1 {C['accent_secondary']});
    border-radius: 3px;
}}

/* ============================================================
   TAB WIDGET
   ============================================================ */
QTabWidget {{
    background-color: {C['bg_primary']};
}}
QTabWidget::pane {{
    border: 1px solid {C['border']};
    border-radius: {D['border_radius']};
    background-color: {C['bg_primary']};
    padding: 6px;
}}
QTabBar::tab {{
    background-color: transparent;
    color: {C['text_secondary']};
    padding: {D['padding_cell']};
    font-size: {D['font_size']};
    font-weight: 500;
    border-bottom: 2px solid transparent;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    min-height: 28px;
}}
QTabBar::tab:hover {{
    color: {C['text_primary']};
    background-color: {C['bg_surface_hover']};
}}
QTabBar::tab:selected {{
    color: {C['accent_primary']};
    background-color: {C['bg_surface']};
    border-bottom: 2px solid {C['accent_primary']};
    font-weight: 600;
}}

/* ============================================================
   TABLE & LIST
   ============================================================ */
QTableWidget, QTableView {{
    background-color: {C['bg_surface']};
    alternate-background-color: {C['bg_primary']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: {D['border_radius']};
    gridline-color: {C['border']};
    selection-background-color: {C['chat_user_bg']};
    selection-color: {C['text_primary']};
}}
QHeaderView::section {{
    background-color: {C['bg_surface_hover']};
    color: {C['text_secondary']};
    padding: {D['padding_cell']};
    border: none;
    border-bottom: 1px solid {C['border']};
    font-weight: 600;
    font-size: {D['font_size_small']};
}}

QListWidget {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: {D['border_radius']};
    padding: 4px;
    outline: none;
}}
QListWidget::item {{
    padding: {D['padding_cell']};
    border-radius: 6px;
    margin: 2px 0;
}}
QListWidget::item:hover {{
    background-color: {C['bg_surface_hover']};
}}
QListWidget::item:selected {{
    background-color: {C['chat_user_bg']};
    color: {C['text_primary']};
}}

/* ============================================================
   GROUP BOX
   ============================================================ */
QGroupBox {{
    background-color: {C['bg_surface']};
    border: 1px solid {C['border']};
    border-radius: 10px;
    margin-top: {D['margin_group_top']};
    padding: 16px 14px 14px 14px;
    font-weight: 600;
    color: {C['text_primary']};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 4px 12px;
    background-color: {C['bg_secondary']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    color: {C['text_primary']};
    font-size: {D['font_size_small']};
    font-weight: 600;
}}

/* ============================================================
   CHECK BOX & RADIO BUTTON
   ============================================================ */
QCheckBox {{
    spacing: 8px;
    color: {C['text_primary']};
    background: transparent;
}}
QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 2px solid {C['bg_elevated']};
    background-color: {C['bg_input']};
}}
QCheckBox::indicator:checked {{
    background-color: {C['accent_primary']};
    border-color: {C['accent_primary']};
}}
QCheckBox::indicator:hover {{ border-color: {C['accent_primary']}; }}

QRadioButton {{
    spacing: 8px;
    color: {C['text_primary']};
    font-size: {D['font_size']};
    font-weight: 500;
    background: transparent;
}}
QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border-radius: 9px;
    border: 2px solid {C['bg_elevated']};
    background-color: {C['bg_input']};
}}
QRadioButton::indicator:checked {{
    background-color: {C['accent_primary']};
    border-color: {C['accent_primary']};
}}
QRadioButton::indicator:hover {{
    border-color: {C['accent_primary']};
}}

QLabel#mutedDesc, QLabel.mutedDesc {{
    color: {C['text_muted']};
    font-size: 11px;
}}

/* ============================================================
   PROGRESS BAR
   ============================================================ */
QProgressBar {{
    background-color: {C['bg_surface']};
    border: none;
    border-radius: 6px;
    text-align: center;
    color: {C['text_primary']};
    font-size: {D['font_size_small']};
    height: 12px;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {C['accent_primary']}, stop:1 {C['accent_secondary']});
    border-radius: 6px;
}}

/* ============================================================
   TOOLTIPS
   ============================================================ */
QToolTip {{
    background-color: {C['bg_surface']};
    color: {C['text_primary']};
    border: 1px solid {C['bg_elevated']};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: {D['font_size_small']};
}}

/* ============================================================
   MENU & MENU BAR
   ============================================================ */
QMenuBar {{
    background-color: transparent;
    color: {C['text_secondary']};
    border: none;
    padding: 2px 8px;
    font-size: {D['font_size_small']};
}}
QMenuBar::item {{
    background: transparent;
    padding: 6px 12px;
    border-radius: 6px;
    color: {C['text_secondary']};
    font-weight: 500;
}}
QMenuBar::item:selected {{
    background-color: {C['sidebar_active']};
    color: {C['text_primary']};
}}
QMenuBar::item:pressed {{
    background-color: {C['accent_primary']};
    color: #ffffff;
}}

QMenu {{
    background-color: {C['bg_secondary']};
    color: {C['text_primary']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    padding: 6px 4px;
}}
QMenu::item {{
    background-color: transparent;
    color: {C['text_primary']};
    padding: 7px 28px 7px 16px;
    border-radius: 6px;
    font-size: {D['font_size_small']};
}}
QMenu::item:selected {{
    background-color: {C['accent_primary']};
    color: #ffffff;
}}
QMenu::item:disabled {{
    color: {C['text_disabled']};
    background-color: transparent;
}}
QMenu::separator {{
    height: 1px;
    background: {C['border']};
    margin: 4px 8px;
}}

/* ============================================================
   SPLITTER
   ============================================================ */
QSplitter::handle {{
    background-color: {C['border']};
    width: 2px;
    height: 2px;
}}
QSplitter::handle:hover {{ background-color: {C['accent_primary']}; }}

/* ============================================================
   STATUS BAR
   ============================================================ */
QStatusBar {{
    background-color: {C['bg_primary']};
    color: {C['text_secondary']};
    border-top: 1px solid {C['border']};
    font-size: {D['font_size_small']};
    padding: 2px 8px;
}}
QStatusBar::item {{ border: none; }}

/* ============================================================
   LABEL
   ============================================================ */
QLabel {{
    color: {C['text_primary']};
}}
QLabel#titleLabel {{
    font-size: 18px;
    font-weight: 700;
}}
QLabel#subtitleLabel {{
    font-size: {D['font_size_large']};
    font-weight: 600;
    color: {C['text_secondary']};
}}
QLabel#statLabel {{
    font-size: 24px;
    font-weight: 700;
    color: {C['accent_primary']};
}}
QLabel#errorLabel {{
    color: {C['error']};
    font-size: {D['font_size_small']};
}}
QLabel#successLabel {{
    color: {C['success']};
    font-size: {D['font_size_small']};
}}
QLabel#mutedLabel {{
    color: {C['text_muted']};
    font-size: {D['font_size_small']};
}}
"""


# Backward compatibility — DARK_STYLESHEET now generated dynamically
DARK_STYLESHEET = build_stylesheet()


# ============================================================
# Helper functions for dynamic styling
# ============================================================

def get_card_style(bg_color: str = None, border_color: str = None,
                   border_radius: int = 12) -> str:
    """Style cho card/panel glassmorphism."""
    bg = bg_color or COLORS['bg_surface']
    bd = border_color or COLORS['bg_elevated']
    D = get_density()
    return f"""
        background-color: {bg};
        border: 1px solid {bd};
        border-radius: {border_radius}px;
        padding: {D['padding_card']};
    """


def get_badge_style(color: str, bg_color: str = None) -> str:
    """Style cho badge/tag nhỏ."""
    if not bg_color:
        bg_color = color + "22"
    return f"""
        background-color: {bg_color};
        color: {color};
        border: 1px solid {color}44;
        border-radius: 8px;
        padding: 4px 12px;
        font-size: {get_density()['font_size_small']};
        font-weight: 600;
    """


def get_sidebar_button_style(is_active: bool = False) -> str:
    """Style cho sidebar navigation button."""
    D = get_density()
    C = COLORS
    if is_active:
        return f"""
            QPushButton {{
                background-color: {C['sidebar_active']};
                color: {C['accent_primary_hover']};
                border: none;
                border-left: 3px solid {C['accent_primary']};
                border-radius: 0px;
                padding: {D['padding_sidebar']};
                text-align: left;
                font-size: {D['font_size']};
                font-weight: 600;
            }}
        """
    return f"""
        QPushButton {{
            background-color: transparent;
            color: {C['text_secondary']};
            border: none;
            border-left: 3px solid transparent;
            border-radius: 0px;
            padding: {D['padding_sidebar']};
            text-align: left;
            font-size: {D['font_size']};
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {C['sidebar_hover']};
            color: {C['text_primary']};
            border-left: 3px solid {C['bg_elevated']};
        }}
    """


def get_chat_bubble_style(is_user: bool = False) -> str:
    """Style cho chat bubble."""
    D = get_density()
    C = COLORS
    obj_name = "chatBubbleUser" if is_user else "chatBubbleAI"
    if is_user:
        return f"""
            QFrame#{obj_name} {{
                background-color: {C['chat_user_bg']};
                border: 1px solid {C['accent_primary']};
                border-radius: 14px 14px 4px 14px;
                padding: {D['padding_chat']};
            }}
            QFrame#{obj_name} QLabel {{
                border: none;
                background: transparent;
            }}
        """
    return f"""
        QFrame#{obj_name} {{
            background-color: {C['chat_ai_bg']};
            border: 1px solid {C['bg_elevated']};
            border-radius: 14px 14px 14px 4px;
            padding: {D['padding_chat']};
        }}
        QFrame#{obj_name} QLabel {{
            border: none;
            background: transparent;
        }}
    """


def get_chat_flat_style(is_user: bool = False) -> str:
    """Style cho tin nhắn dạng phẳng tối giản (Compact Flat)."""
    D = get_density()
    C = COLORS
    obj_name = "chatBubbleUser" if is_user else "chatBubbleAI"
    border_color = f"{C['accent_primary']}44" if is_user else f"{C['bg_elevated']}44"
    return f"""
        QFrame#{obj_name} {{
            background-color: transparent;
            border-bottom: 1px solid {border_color};
            border-radius: 0px;
            padding: {D['padding_chat']};
        }}
        QFrame#{obj_name} QLabel {{
            border: none;
            background: transparent;
        }}
    """


def get_topbar_style() -> str:
    """Style cho top header bar tích hợp menu & action buttons."""
    return f"""
        QFrame#topHeaderBar {{
            background-color: {COLORS['bg_primary']};
            border-bottom: 1px solid {COLORS['border']};
        }}
    """


def get_menubar_style() -> str:
    """Style cho thanh QMenuBar."""
    C = COLORS
    D = get_density()
    return f"""
        QMenuBar {{
            background: transparent;
            color: {C['text_secondary']};
            border: none;
            padding: 2px 8px;
            font-size: {D['font_size_small']};
        }}
        QMenuBar::item {{
            background: transparent;
            padding: 6px 12px;
            border-radius: 6px;
            color: {C['text_secondary']};
            font-weight: 500;
        }}
        QMenuBar::item:selected {{
            background-color: {C['sidebar_active']};
            color: {C['text_primary']};
        }}
        QMenuBar::item:pressed {{
            background-color: {C['accent_primary']};
            color: #ffffff;
        }}
    """


def get_menu_style() -> str:
    """Style cho popup QMenu."""
    C = COLORS
    D = get_density()
    return f"""
        QMenu {{
            background-color: {C['bg_secondary']};
            color: {C['text_primary']};
            border: 1px solid {C['border']};
            border-radius: 8px;
            padding: 6px 4px;
        }}
        QMenu::item {{
            background-color: transparent;
            color: {C['text_primary']};
            padding: 7px 28px 7px 16px;
            border-radius: 6px;
            font-size: {D['font_size_small']};
        }}
        QMenu::item:selected {{
            background-color: {C['accent_primary']};
            color: #ffffff;
        }}
        QMenu::item:disabled {{
            color: {C['text_disabled']};
            background-color: transparent;
        }}
        QMenu::separator {{
            height: 1px;
            background: {C['border']};
            margin: 4px 8px;
        }}
    """


def get_topbar_action_btn_style(variant: str = "normal") -> str:
    """Style cho các nút bấm nhanh trên Top Bar."""
    C = COLORS
    D = get_density()
    base_padding = D['padding_btn']

    variants = {
        "primary": (C['bg_surface'], C['accent_primary_hover'], C['bg_elevated'],
                    C['accent_primary'], "#ffffff", C['accent_primary']),
        "warning": (C['bg_surface'], C['warning'], C['bg_elevated'],
                    C['warning_bg'], C['warning'], C['warning']),
        "danger": (C['bg_surface'], C['error'], C['bg_elevated'],
                   C['error_bg'], C['error'], C['error']),
        "success": (C['bg_surface'], C['success'], C['bg_elevated'],
                    C['success_bg'], C['success'], C['success']),
    }

    if variant in variants:
        bg, fg, bd, h_bg, h_fg, h_bd = variants[variant]
        return f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: 1px solid {bd};
                border-radius: 6px;
                padding: {base_padding};
                font-size: {D['font_size_small']};
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {h_bg};
                color: {h_fg};
                border-color: {h_bd};
            }}
        """

    # Normal variant
    return f"""
        QPushButton {{
            background-color: {C['sidebar_hover']};
            color: {C['text_secondary']};
            border: 1px solid {C['border']};
            border-radius: 6px;
            padding: {base_padding};
            font-size: {D['font_size_small']};
            font-weight: 500;
        }}
        QPushButton:hover {{
            background-color: {C['bg_surface']};
            color: {C['text_primary']};
            border-color: {C['text_disabled']};
        }}
        QPushButton:pressed {{
            background-color: {C['bg_elevated']};
        }}
    """


def format_chat_content(text: str, render_mode: str = "natural") -> tuple[str, bool]:
    """
    Format nội dung chat theo chế độ:
    - 'natural': Văn bản thuần tự nhiên (MẶC ĐỊNH), lọc sạch toàn bộ ký tự markdown kỹ thuật (**bold**, #, `, table...).
    - 'markdown': Render Rich Text HTML (in đậm thật, code block, bullet list, tiêu đề).
    - 'icon_rich': Dạng văn bản tự nhiên có chèn thêm icon sinh động theo từng mục.
    - 'raw': Giữ nguyên văn bản thô.

    Returns:
        tuple[str, bool]: (formatted_text, is_rich_html)
    """
    import html
    import re

    if not text:
        return "", False

    if render_mode == "raw":
        return text, False

    if render_mode == "natural":
        # 1. Bỏ code blocks formatting markers nhưng giữ nội dung
        t = re.sub(r'```[a-zA-Z0-9_-]*\n?(.*?)```', r'\1', text, flags=re.DOTALL)
        # 2. Bỏ inline code `code`
        t = re.sub(r'`([^`]+)`', r'\1', t)
        # 3. Bỏ **bold** và *italic* và __bold__ và _italic_ và ~~strikethrough~~
        t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)
        t = re.sub(r'\*(.+?)\*', r'\1', t)
        t = re.sub(r'__(.+?)__', r'\1', t)
        t = re.sub(r'_(.+?)_', r'\1', t)
        t = re.sub(r'~~(.+?)~~', r'\1', t)
        # 4. Bỏ header markers (# Header -> Header)
        t = re.sub(r'^\s*#{1,6}\s*', '', t, flags=re.MULTILINE)
        # 5. Chuẩn hóa bullet lists (- item, * item, + item -> • item)
        t = re.sub(r'^\s*[-*+]\s+', '• ', t, flags=re.MULTILINE)
        # 6. Bỏ bảng markdown table separator |---|---|
        lines = []
        for line in t.split('\n'):
            if re.match(r'^\s*\|?\s*[-:]+\s*\|', line):
                continue
            if line.strip().startswith('|') and line.strip().endswith('|'):
                cells = [c.strip() for c in line.strip().strip('|').split('|') if c.strip()]
                if cells:
                    lines.append('• ' + ' | '.join(cells))
            else:
                lines.append(line)
        t = '\n'.join(lines)
        # 7. Bỏ dòng trống liên tiếp
        t = re.sub(r'\n{3,}', '\n\n', t)
        return t.strip(), False

    elif render_mode == "icon_rich":
        # Chế độ tự nhiên nhưng thêm icon sinh động
        clean_text, _ = format_chat_content(text, render_mode="natural")
        lines = clean_text.split('\n')
        rich_lines = []
        icon_cycle = ["📌", "⚡", "✨", "💡", "🎯", "🔧", "🚀", "🔍", "✅", "📊"]
        icon_idx = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('•'):
                icon = icon_cycle[icon_idx % len(icon_cycle)]
                icon_idx += 1
                rich_lines.append(f"  {icon} " + stripped[1:].strip())
            else:
                rich_lines.append(line)
        return '\n'.join(rich_lines).strip(), False

    elif render_mode == "markdown":
        C = COLORS
        # Render sang Rich Text HTML an toàn
        code_blocks = []
        def _save_code_block(match):
            lang = match.group(1) or ""
            code_content = match.group(2)
            code_blocks.append((lang, code_content))
            return f"___CODE_BLOCK_{len(code_blocks)-1}___"

        raw_processed = re.sub(r'```([a-zA-Z0-9_-]*)\n?(.*?)```', _save_code_block, text, flags=re.DOTALL)

        # Escape HTML
        safe_text = html.escape(raw_processed)

        # Inline code
        safe_text = re.sub(
            r'`([^`]+)`',
            rf'<code style="background-color:{C["bg_input"]}; color:{C["accent_secondary"]}; padding:2px 6px; border-radius:4px; font-family:Consolas, Monaco, monospace; font-size:12px; border:1px solid {C["border"]};">\1</code>',
            safe_text
        )

        # Bold & Italic
        safe_text = re.sub(r'\*\*(.+?)\*\*', rf'<b style="color:{C["text_primary"]}; font-weight:700;">\1</b>', safe_text)
        safe_text = re.sub(r'\*(.+?)\*', rf'<i style="color:{C["text_secondary"]};">\1</i>', safe_text)

        # Headers
        safe_text = re.sub(r'^\s*###\s+(.+)$', rf'<div style="font-size:13px; font-weight:700; color:{C["accent_primary_hover"]}; margin-top:6px; margin-bottom:3px;">\1</div>', safe_text, flags=re.MULTILINE)
        safe_text = re.sub(r'^\s*##\s+(.+)$', rf'<div style="font-size:14px; font-weight:700; color:{C["accent_primary_hover"]}; margin-top:8px; margin-bottom:4px;">\1</div>', safe_text, flags=re.MULTILINE)
        safe_text = re.sub(r'^\s*#\s+(.+)$', rf'<div style="font-size:15px; font-weight:700; color:{C["accent_primary_hover"]}; margin-top:10px; margin-bottom:6px;">\1</div>', safe_text, flags=re.MULTILINE)

        # Bullets
        safe_text = re.sub(r'^\s*[-*+]\s+(.+)$', rf'<div style="margin-left:8px; margin-bottom:3px;"><span style="color:{C["accent_primary"]}; font-weight:bold;">•</span> \1</div>', safe_text, flags=re.MULTILINE)

        # Restore code blocks
        for idx, (lang, code_content) in enumerate(code_blocks):
            escaped_code = html.escape(code_content.strip())
            lang_badge = f"<span style='color:{C['text_muted']}; font-size:11px; float:right;'>{lang}</span>" if lang else ""
            block_html = (
                f"<div style='background-color:{C['bg_input']}; border:1px solid {C['border']}; border-radius:8px; padding:8px 12px; margin:6px 0; font-family:Consolas, Monaco, monospace; font-size:12px; color:{C['text_primary']}; white-space:pre-wrap; line-height:1.4;'>"
                f"{lang_badge}"
                f"<div>{escaped_code}</div>"
                f"</div>"
            )
            safe_text = safe_text.replace(f"___CODE_BLOCK_{idx}___", block_html)

        # Convert remaining newlines
        safe_text = safe_text.replace('\n', '<br/>')
        safe_text = re.sub(r'(</div>)<br/>', r'\1', safe_text)
        safe_text = re.sub(r'<br/>(<div>|<div )', r'\1', safe_text)

        return safe_text, True

    return text, False
