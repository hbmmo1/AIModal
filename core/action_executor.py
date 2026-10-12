"""
Action Executor — Thực thi thao tác desktop (chuột/bàn phím/cửa sổ).
Thread-safe execution với stop/pause/resume qua Qt signals.
"""

import os
import sys
import time
import logging
import subprocess
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field, asdict
from PyQt6.QtCore import QObject, pyqtSignal, QThread

logger = logging.getLogger(__name__)


# ============================================================
# Action Types Constants
# ============================================================
ACTION_MOUSE_CLICK = "mouse_click"
ACTION_MOUSE_MOVE = "mouse_move"
ACTION_MOUSE_DRAG = "mouse_drag"
ACTION_KEY_PRESS = "key_press"
ACTION_TYPE_TEXT = "type_text"
ACTION_WAIT = "wait"
ACTION_SCROLL = "scroll"
ACTION_ACTIVATE_WINDOW = "activate_window"
ACTION_OPEN_APP = "open_application"

ACTION_NAMES = {
    ACTION_MOUSE_CLICK: "🖱️ Click chuột",
    ACTION_MOUSE_MOVE: "↗️ Di chuyển chuột",
    ACTION_MOUSE_DRAG: "🔀 Kéo thả chuột",
    ACTION_KEY_PRESS: "⌨️ Nhấn phím",
    ACTION_TYPE_TEXT: "📝 Gõ văn bản",
    ACTION_WAIT: "⏳ Chờ/Nghỉ",
    ACTION_SCROLL: "📜 Cuộn chuột",
    ACTION_ACTIVATE_WINDOW: "🪟 Kích hoạt cửa sổ",
    ACTION_OPEN_APP: "🚀 Mở ứng dụng",
}


@dataclass
class ActionStep:
    """Một bước hành động trong macro."""
    id: str = ""
    name: str = ""
    action_type: str = ACTION_MOUSE_CLICK
    enabled: bool = True
    delay_after_ms: int = 300

    # Mouse
    x: Optional[int] = None
    y: Optional[int] = None
    end_x: Optional[int] = None
    end_y: Optional[int] = None
    mouse_button: str = "left"
    click_count: int = 1

    # Keyboard
    key_string: str = "enter"
    key_repeat: int = 1

    # Text
    text_content: str = ""
    paste_mode: bool = False

    # Scroll
    scroll_amount: int = -3

    # Window
    window_title: str = ""

    # App
    target_path: str = ""

    def get_summary(self) -> str:
        """Mô tả ngắn gọn bước này."""
        if self.action_type == ACTION_MOUSE_CLICK:
            coord = f"({self.x}, {self.y})" if self.x is not None else "(vị trí hiện tại)"
            return f"Click {self.mouse_button} tại {coord}"
        elif self.action_type == ACTION_MOUSE_MOVE:
            return f"Di chuyển chuột đến ({self.x}, {self.y})"
        elif self.action_type == ACTION_MOUSE_DRAG:
            return f"Kéo từ ({self.x}, {self.y}) đến ({self.end_x}, {self.end_y})"
        elif self.action_type == ACTION_KEY_PRESS:
            return f"Nhấn phím: [{self.key_string.upper()}]"
        elif self.action_type == ACTION_TYPE_TEXT:
            preview = self.text_content[:30] + "..." if len(self.text_content) > 30 else self.text_content
            return f'Gõ: "{preview}"'
        elif self.action_type == ACTION_WAIT:
            return f"Chờ {self.delay_after_ms}ms"
        elif self.action_type == ACTION_SCROLL:
            direction = "xuống" if self.scroll_amount < 0 else "lên"
            return f"Cuộn {direction} {abs(self.scroll_amount)} nấc"
        elif self.action_type == ACTION_ACTIVATE_WINDOW:
            return f'Kích hoạt: "{self.window_title}"'
        elif self.action_type == ACTION_OPEN_APP:
            return f'Mở: "{self.target_path}"'
        return "Hành động không xác định"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "ActionStep":
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        clean = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**clean)


class ActionExecutor(QObject):
    """
    Engine thực thi hành động desktop.
    Chạy trên worker thread, giao tiếp qua Qt signals.
    """

    # Signals
    step_started = pyqtSignal(int, str)       # step_index, description
    step_completed = pyqtSignal(int, str)     # step_index, status
    step_error = pyqtSignal(int, str)         # step_index, error_message
    execution_finished = pyqtSignal(str)      # final_status
    progress_update = pyqtSignal(int, int)    # current_step, total_steps
    log_message = pyqtSignal(str)             # message

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._paused = False
        self._stop_requested = False

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def is_paused(self) -> bool:
        return self._paused

    def stop(self):
        """Yêu cầu dừng execution."""
        self._stop_requested = True
        self._paused = False
        logger.info("[ActionExecutor] Đã yêu cầu dừng")

    def pause(self):
        """Tạm dừng execution."""
        self._paused = True
        logger.info("[ActionExecutor] Đã tạm dừng")

    def resume(self):
        """Tiếp tục execution."""
        self._paused = False
        logger.info("[ActionExecutor] Đã tiếp tục")

    def toggle_pause(self):
        """Bật/tắt tạm dừng."""
        if self._paused:
            self.resume()
        else:
            self.pause()

    def execute_steps(self, steps: List[ActionStep], loop_count: int = 1, loop_delay_ms: int = 500):
        """
        Thực thi danh sách các bước hành động.
        Chạy trên thread gọi (nên gọi từ QThread worker).
        """
        import pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.05

        self._running = True
        self._paused = False
        self._stop_requested = False

        total_steps = len([s for s in steps if s.enabled])
        self.log_message.emit(f"🚀 Bắt đầu thực thi {total_steps} bước, lặp {loop_count} lần")

        try:
            for loop_idx in range(loop_count):
                if self._stop_requested:
                    break

                if loop_count > 1:
                    self.log_message.emit(f"🔄 Vòng lặp {loop_idx + 1}/{loop_count}")

                step_num = 0
                for i, step in enumerate(steps):
                    if self._stop_requested:
                        break

                    # Chờ khi bị pause
                    while self._paused and not self._stop_requested:
                        time.sleep(0.1)

                    if not step.enabled:
                        continue

                    step_num += 1
                    desc = step.get_summary()
                    self.step_started.emit(i, desc)
                    self.progress_update.emit(step_num, total_steps)

                    try:
                        self._execute_single_step(step)
                        self.step_completed.emit(i, "SUCCESS")
                    except Exception as e:
                        error_msg = str(e)
                        self.step_error.emit(i, error_msg)
                        self.log_message.emit(f"❌ Lỗi bước {step_num}: {error_msg}")
                        logger.error(f"Lỗi thực thi bước {i}: {error_msg}")

                    # Delay sau mỗi bước
                    if step.delay_after_ms > 0 and not self._stop_requested:
                        time.sleep(step.delay_after_ms / 1000.0)

                # Delay giữa các vòng lặp
                if loop_idx < loop_count - 1 and loop_delay_ms > 0 and not self._stop_requested:
                    time.sleep(loop_delay_ms / 1000.0)

            status = "STOPPED" if self._stop_requested else "COMPLETED"
            self.log_message.emit(f"✅ Hoàn thành ({status})")
            self.execution_finished.emit(status)

        except Exception as e:
            self.log_message.emit(f"💥 Lỗi nghiêm trọng: {str(e)}")
            self.execution_finished.emit("ERROR")
        finally:
            self._running = False

    def _execute_single_step(self, step: ActionStep):
        """Thực thi 1 bước hành động."""
        import pyautogui

        if step.action_type == ACTION_MOUSE_CLICK:
            x = step.x if step.x is not None else pyautogui.position().x
            y = step.y if step.y is not None else pyautogui.position().y
            btn = step.mouse_button if step.mouse_button in ("left", "right", "middle") else "left"

            if step.mouse_button == "double":
                pyautogui.doubleClick(x, y)
            else:
                for _ in range(step.click_count):
                    pyautogui.click(x, y, button=btn)
                    if step.click_count > 1:
                        time.sleep(0.05)

        elif step.action_type == ACTION_MOUSE_MOVE:
            x = step.x or 0
            y = step.y or 0
            pyautogui.moveTo(x, y, duration=0.2)

        elif step.action_type == ACTION_MOUSE_DRAG:
            sx, sy = step.x or 0, step.y or 0
            ex, ey = step.end_x or 0, step.end_y or 0
            pyautogui.moveTo(sx, sy, duration=0.1)
            pyautogui.drag(ex - sx, ey - sy, duration=0.3)

        elif step.action_type == ACTION_KEY_PRESS:
            key_str = step.key_string.strip()
            for _ in range(max(1, step.key_repeat)):
                if "+" in key_str:
                    # Tổ hợp phím: ctrl+c, alt+tab, ...
                    keys = [k.strip() for k in key_str.split("+")]
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(key_str)

        elif step.action_type == ACTION_TYPE_TEXT:
            if step.paste_mode:
                import pyperclip
                pyperclip.copy(step.text_content)
                pyautogui.hotkey("ctrl", "v")
            else:
                pyautogui.write(step.text_content, interval=0.02)

        elif step.action_type == ACTION_WAIT:
            time.sleep(step.delay_after_ms / 1000.0)

        elif step.action_type == ACTION_SCROLL:
            x = step.x if step.x is not None else None
            y = step.y if step.y is not None else None
            if x is not None and y is not None:
                pyautogui.scroll(step.scroll_amount, x=x, y=y)
            else:
                pyautogui.scroll(step.scroll_amount)

        elif step.action_type == ACTION_ACTIVATE_WINDOW:
            try:
                import pygetwindow as gw
                windows = gw.getWindowsWithTitle(step.window_title)
                if windows:
                    win = windows[0]
                    if win.isMinimized:
                        win.restore()
                    win.activate()
                    time.sleep(0.3)
                else:
                    logger.warning(f"Không tìm thấy cửa sổ: {step.window_title}")
            except Exception as e:
                logger.warning(f"Lỗi activate window: {e}")

        elif step.action_type == ACTION_OPEN_APP:
            target = step.target_path.strip()
            if target.startswith(("http://", "https://")):
                import webbrowser
                webbrowser.open(target)
            elif os.path.exists(target):
                subprocess.Popen(target, shell=True)
            else:
                subprocess.Popen(target, shell=True)
            time.sleep(1.0)  # Chờ app khởi động

    def execute_tool_call(self, tool_name: str, args: Dict) -> str:
        """
        Thực thi 1 tool call từ AI (function calling).
        Trả về kết quả dạng text.
        """
        import pyautogui

        try:
            if tool_name == "click_at":
                x, y = args.get("x", 0), args.get("y", 0)
                button = args.get("button", "left")
                if button == "double":
                    pyautogui.doubleClick(x, y)
                else:
                    pyautogui.click(x, y, button=button)
                return f"✅ Đã click {button} tại ({x}, {y})"

            elif tool_name == "type_text":
                text = args.get("text", "")
                interval = args.get("interval", 0.02)
                import pyperclip
                pyperclip.copy(text)
                pyautogui.hotkey("ctrl", "v")
                return f'✅ Đã gõ văn bản: "{text[:50]}..."' if len(text) > 50 else f'✅ Đã gõ: "{text}"'

            elif tool_name == "press_key":
                key = args.get("key", "enter")
                if "+" in key:
                    keys = [k.strip() for k in key.split("+")]
                    pyautogui.hotkey(*keys)
                else:
                    pyautogui.press(key)
                return f"✅ Đã nhấn phím: {key.upper()}"

            elif tool_name == "take_screenshot":
                # Trả marker đặc biệt — ChatPanel sẽ xử lý chụp + gửi AI phân tích
                return "__TAKE_SCREENSHOT__"

            elif tool_name == "open_application":
                target = args.get("target", "")
                if target.startswith(("http://", "https://")):
                    import webbrowser
                    webbrowser.open(target)
                else:
                    subprocess.Popen(target, shell=True)
                return f'✅ Đã mở: "{target}"'

            elif tool_name == "wait_seconds":
                seconds = args.get("seconds", 1)
                time.sleep(seconds)
                return f"✅ Đã chờ {seconds}s"

            elif tool_name == "scroll":
                amount = args.get("amount", -3)
                x, y = args.get("x"), args.get("y")
                if x is not None and y is not None:
                    pyautogui.scroll(amount, x=x, y=y)
                else:
                    pyautogui.scroll(amount)
                direction = "xuống" if amount < 0 else "lên"
                return f"✅ Đã cuộn {direction} {abs(amount)} nấc"

            elif tool_name == "create_workflow":
                name = args.get("name", "Workflow mới")
                steps = args.get("steps", [])
                return f'✅ Đã tạo workflow "{name}" với {len(steps)} bước'

            else:
                return f"⚠️ Tool không xác định: {tool_name}"

        except Exception as e:
            return f"❌ Lỗi thực thi {tool_name}: {str(e)}"


class ExecutorWorker(QThread):
    """Worker thread để chạy ActionExecutor không block UI."""

    def __init__(self, executor: ActionExecutor, steps: List[ActionStep],
                 loop_count: int = 1, loop_delay_ms: int = 500, parent=None):
        super().__init__(parent)
        self.executor = executor
        self.steps = steps
        self.loop_count = loop_count
        self.loop_delay_ms = loop_delay_ms

    def run(self):
        self.executor.execute_steps(self.steps, self.loop_count, self.loop_delay_ms)
