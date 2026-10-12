"""
AI Claw — Nền tảng Tự Động Hoá Thông Minh bằng AI
Entry point chính.
"""

import os
import sys
import io
import traceback
import yaml
import logging
from datetime import datetime

# =====================================================================
# TỰ ĐỘNG CẤU HÌNH CHUẨN UTF-8 TOÀN DIỆN CHO WINDOWS CMD / POWERSHELL
# =====================================================================
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
os.environ["QT_LOGGING_RULES"] = "qt.qpa.window=false"

# =====================================================================
# PATCH AN TOÀN CHO OPENCV / PYSCREEZE / PYAUTOGUI
# =====================================================================
try:
    import cv2
    if not hasattr(cv2, '__version__') or cv2.__version__ is None:
        cv2.__version__ = "5.0.0"
except Exception:
    pass


if sys.platform == "win32":
    try:
        os.system("chcp 65001 >nul 2>&1")
    except Exception:
        pass

    try:
        if hasattr(sys.stdout, "buffer"):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
        if hasattr(sys.stderr, "buffer"):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    except Exception:
        pass


# =====================================================================
# CẤU HÌNH LOGGING
# =====================================================================
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
for h in root_logger.handlers[:]:
    root_logger.removeHandler(h)

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S")
console_handler.setFormatter(formatter)
root_logger.addHandler(console_handler)

logger = logging.getLogger("AIClaw")


# =====================================================================
# HELPER FUNCTIONS
# =====================================================================
def get_app_dir() -> str:
    """Returns the base directory of the application whether running as script or frozen .exe."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def log_exception_to_file(exc_type, exc_value, exc_traceback):
    """Writes detailed crash logs to error_log.txt and shows error dialog."""
    app_dir = get_app_dir()
    log_path = os.path.join(app_dir, "error_log.txt")

    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = "".join(tb_lines)

    log_entry = (
        f"\n{'=' * 70}\n"
        f"CRASH REPORT - {timestamp_str}\n"
        f"Platform: {sys.platform} | Python: {sys.version}\n"
        f"Executable: {sys.executable}\n"
        f"App Dir: {app_dir}\n"
        f"Error: {exc_type.__name__}: {exc_value}\n"
        f"{'-' * 70}\n"
        f"{tb_text}"
        f"{'=' * 70}\n"
    )

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception:
        pass

    # 1. Try displaying Qt GUI Dialog
    dialog_shown = False
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)

        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle("Lỗi Ứng Dụng (Application Error)")
        msg.setText(f"Đã xảy ra sự cố trong ứng dụng:\n\n{exc_type.__name__}: {exc_value}")
        msg.setInformativeText(f"Chi tiết lỗi đã được ghi vào:\n{log_path}")
        msg.setDetailedText(tb_text)
        msg.exec()
        dialog_shown = True
    except Exception:
        pass

    # 2. Fallback to console
    if not dialog_shown:
        print(f"\n{'=' * 50}")
        print(f"LỖI NGHIÊM TRỌNG: {exc_type.__name__}: {exc_value}")
        print(f"Chi tiết lỗi: {log_path}")
        print(f"{'=' * 50}\n")



def check_auth_requirement() -> bool:
    """Kiểm tra chính sách đăng nhập (Mặc định: TẮT — không cần đăng nhập)."""
    if os.environ.get("HB_AUTH_BYPASS") == "1" or "--sso" in sys.argv or "--bypass-login" in sys.argv:
        return False

    try:
        from core.state_manager import StateManager
        sm = StateManager()
        return sm.is_auth_enabled()
    except Exception as e:
        logger.warning(f"Lỗi kiểm tra auth requirement: {e}")
        return False


def load_config() -> dict:
    """Load cấu hình từ config.yaml."""
    config_path = os.path.join(get_app_dir(), "config", "config.yaml")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Không thể đọc config.yaml: {e}")
    return {}


def load_env():
    """Load biến môi trường từ .env."""
    env_path = os.path.join(get_app_dir(), ".env")
    if os.path.exists(env_path):
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
        except Exception:
            # Fallback manual parse
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            os.environ[key.strip()] = value.strip()
            except Exception:
                pass


# =====================================================================
# MAIN
# =====================================================================
def main():
    logger.info("=" * 55)
    logger.info("   🤖 AI CLAW — Trợ Lý Tự Động Hoá Thông Minh")
    logger.info("   Phiên bản 1.0.0 | Powered by Google Gemini AI")
    logger.info("=" * 55)

    # Load .env
    load_env()

    # Load config
    config = load_config()
    logger.info(f"[Config] Đã tải cấu hình từ config.yaml")

    # Khởi tạo PyQt6 Application
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from ui.theme import DARK_STYLESHEET, set_theme, set_density, set_font_size, build_stylesheet
    from ui.main_window import MainWindow
    from core.state_manager import StateManager

    app = QApplication(sys.argv)
    app.setApplicationName("AI Claw")
    app.setOrganizationName("AIClaw")

    # Load saved theme/density/font size before applying stylesheet
    try:
        _sm = StateManager()
        _saved_theme = _sm.get_app_setting("app_theme", "dark")
        _saved_density = _sm.get_app_setting("ui_density", "material")
        _saved_font = _sm.get_app_setting("app_font_size", "medium")
        set_theme(_saved_theme)
        set_density(_saved_density)
        set_font_size(_saved_font)
        logger.info(f"[Theme] Loaded: theme={_saved_theme}, density={_saved_density}, font={_saved_font}")
    except Exception as e:
        logger.warning(f"[Theme] Không load được settings: {e}")

    # Apply theme
    app.setStyleSheet(build_stylesheet())

    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Kiểm tra Đăng Nhập 2 Tầng
    from ui.login_dialog import AIClawLoginDialog
    if check_auth_requirement():
        login_dlg = AIClawLoginDialog()
        if login_dlg.exec() != AIClawLoginDialog.DialogCode.Accepted:
            sys.exit(0)

    # Create main window
    window = MainWindow(config=config)
    window.show()

    logger.info("[App] Ứng dụng đã khởi động thành công!")
    logger.info("[App] Sử dụng tab 'AI Chat' để bắt đầu trò chuyện với AI")

    sys.exit(app.exec())


if __name__ == "__main__":
    sys.excepthook = log_exception_to_file
    try:
        main()
    except Exception as e:
        log_exception_to_file(type(e), e, e.__traceback__)
