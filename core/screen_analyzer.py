"""
Screen Analyzer — Chụp screenshot và phân tích bằng Gemini Vision.
Dùng mss cho tốc độ chụp nhanh, PIL để xử lý ảnh.
Hỗ trợ: chọn màn hình (trái/phải/tất cả), chuyển đổi WebP, cấu hình chất lượng.
"""

import os
import io
import logging
from datetime import datetime
from typing import Optional, Dict, Tuple, List
from PIL import Image

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCREENSHOT_DIR = os.path.join(BASE_DIR, "screenshots")

# Monitor mode constants
MONITOR_ALL = "all"          # Tất cả màn hình (mặc định)
MONITOR_LEFT = "left"        # Màn hình bên trái
MONITOR_RIGHT = "right"      # Màn hình bên phải
MONITOR_PRIMARY = "primary"  # Màn hình chính

# Image format constants
IMG_FORMAT_WEBP = "webp"
IMG_FORMAT_PNG = "png"
IMG_FORMAT_JPEG = "jpeg"


class ScreenAnalyzer:
    """Chụp screenshot và phân tích bằng AI Vision."""

    def __init__(self):
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)

        # Cấu hình mặc định
        self.monitor_mode = MONITOR_ALL      # all / left / right / primary
        self.image_format = IMG_FORMAT_WEBP   # webp / png / jpeg
        self.image_quality = 100              # 1-100 (cho webp/jpeg)

    def set_monitor_mode(self, mode: str):
        """Đặt chế độ chụp màn hình."""
        if mode in (MONITOR_ALL, MONITOR_LEFT, MONITOR_RIGHT, MONITOR_PRIMARY):
            self.monitor_mode = mode
            logger.info(f"[ScreenAnalyzer] Monitor mode: {mode}")

    def set_image_format(self, fmt: str):
        """Đặt định dạng ảnh đầu ra."""
        if fmt in (IMG_FORMAT_WEBP, IMG_FORMAT_PNG, IMG_FORMAT_JPEG):
            self.image_format = fmt
            logger.info(f"[ScreenAnalyzer] Image format: {fmt}")

    def set_image_quality(self, quality: int):
        """Đặt chất lượng ảnh (1-100)."""
        self.image_quality = max(1, min(100, quality))
        logger.info(f"[ScreenAnalyzer] Image quality: {self.image_quality}")

    def get_monitor_list(self) -> List[Dict]:
        """Lấy danh sách các màn hình có sẵn."""
        try:
            import mss
            with mss.mss() as sct:
                monitors = []
                # sct.monitors[0] = toàn bộ, [1] = primary, [2]+ = secondary
                for i, m in enumerate(sct.monitors):
                    if i == 0:
                        monitors.append({
                            "index": i, "name": "Tất cả màn hình",
                            "left": m["left"], "top": m["top"],
                            "width": m["width"], "height": m["height"]
                        })
                    else:
                        monitors.append({
                            "index": i, "name": f"Màn hình {i}",
                            "left": m["left"], "top": m["top"],
                            "width": m["width"], "height": m["height"]
                        })
                return monitors
        except Exception as e:
            logger.error(f"[ScreenAnalyzer] Lỗi lấy danh sách monitor: {e}")
            return []

    def get_monitor_count(self) -> int:
        """Đếm số màn hình vật lý (không kể combined)."""
        try:
            import mss
            with mss.mss() as sct:
                return len(sct.monitors) - 1  # Trừ monitors[0] (combined)
        except Exception:
            return 1

    def _resolve_monitor(self):
        """
        Xác định monitor region dựa trên self.monitor_mode.
        Returns: dict {"left", "top", "width", "height"} hoặc None (toàn bộ)
        """
        try:
            import mss
            with mss.mss() as sct:
                num_physical = len(sct.monitors) - 1  # monitors[0] = combined

                if self.monitor_mode == MONITOR_ALL or num_physical <= 1:
                    return sct.monitors[0]

                if self.monitor_mode == MONITOR_PRIMARY:
                    return sct.monitors[1]

                # Sắp xếp theo vị trí left để xác định trái/phải
                physical = [(i, sct.monitors[i]) for i in range(1, len(sct.monitors))]
                physical.sort(key=lambda x: x[1]["left"])

                if self.monitor_mode == MONITOR_LEFT:
                    return physical[0][1]
                elif self.monitor_mode == MONITOR_RIGHT:
                    return physical[-1][1]

                # Fallback
                return sct.monitors[0]

        except Exception as e:
            logger.error(f"[ScreenAnalyzer] Lỗi resolve monitor: {e}")
            return None

    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None,
                       save: bool = False) -> Optional[Image.Image]:
        """
        Chụp screenshot theo cấu hình monitor_mode hoặc vùng chỉ định.

        Args:
            region: (x, y, width, height) hoặc None để dùng monitor_mode
            save: Lưu screenshot vào thư mục screenshots/

        Returns:
            PIL Image hoặc None nếu lỗi
        """
        try:
            import mss
            with mss.mss() as sct:
                if region:
                    monitor = {"left": region[0], "top": region[1],
                               "width": region[2], "height": region[3]}
                else:
                    monitor = self._resolve_monitor() or sct.monitors[0]

                screenshot = sct.grab(monitor)
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")

                if save:
                    filepath = self._save_image(img)
                    logger.info(f"[ScreenAnalyzer] Đã lưu screenshot: {filepath}")

                return img

        except Exception as e:
            logger.error(f"[ScreenAnalyzer] Lỗi chụp screenshot: {e}")
            return None

    def capture_and_resize(self, max_width: int = 1280, max_height: int = 720,
                           region: Optional[Tuple[int, int, int, int]] = None) -> Optional[Image.Image]:
        """
        Chụp screenshot và resize để gửi lên AI Vision (tiết kiệm token).
        """
        img = self.capture_screen(region)
        if img is None:
            return None

        # Resize giữ tỷ lệ
        w, h = img.size
        if w > max_width or h > max_height:
            ratio = min(max_width / w, max_height / h)
            new_size = (int(w * ratio), int(h * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)

        return img

    def convert_to_bytes(self, image: Image.Image,
                         fmt: Optional[str] = None,
                         quality: Optional[int] = None) -> bytes:
        """
        Chuyển đổi PIL Image sang bytes theo định dạng cấu hình.

        Args:
            image: PIL Image
            fmt: Override format (None = dùng self.image_format)
            quality: Override quality (None = dùng self.image_quality)

        Returns:
            Image bytes
        """
        fmt = fmt or self.image_format
        quality = quality if quality is not None else self.image_quality

        buf = io.BytesIO()

        if fmt == IMG_FORMAT_WEBP:
            image.save(buf, format="WEBP", quality=quality, method=4)
        elif fmt == IMG_FORMAT_JPEG:
            # JPEG không hỗ trợ alpha
            if image.mode == "RGBA":
                image = image.convert("RGB")
            image.save(buf, format="JPEG", quality=quality, optimize=True)
        else:
            # PNG — lossless, không dùng quality
            image.save(buf, format="PNG", optimize=True)

        buf.seek(0)
        return buf.read()

    def get_mime_type(self, fmt: Optional[str] = None) -> str:
        """Trả về MIME type cho format hiện tại."""
        fmt = fmt or self.image_format
        return {
            IMG_FORMAT_WEBP: "image/webp",
            IMG_FORMAT_PNG: "image/png",
            IMG_FORMAT_JPEG: "image/jpeg",
        }.get(fmt, "image/png")

    def get_file_extension(self, fmt: Optional[str] = None) -> str:
        """Trả về file extension cho format hiện tại."""
        fmt = fmt or self.image_format
        return {
            IMG_FORMAT_WEBP: ".webp",
            IMG_FORMAT_PNG: ".png",
            IMG_FORMAT_JPEG: ".jpg",
        }.get(fmt, ".png")

    def _save_image(self, image: Image.Image) -> str:
        """Lưu ảnh theo định dạng cấu hình."""
        ext = self.get_file_extension()
        filename = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}{ext}"
        filepath = os.path.join(SCREENSHOT_DIR, filename)

        img_bytes = self.convert_to_bytes(image)
        with open(filepath, "wb") as f:
            f.write(img_bytes)

        return filepath

    def get_cursor_position(self) -> Tuple[int, int]:
        """Lấy vị trí cursor hiện tại."""
        try:
            import pyautogui
            pos = pyautogui.position()
            return (pos.x, pos.y)
        except Exception:
            return (0, 0)

    def get_screen_size(self) -> Tuple[int, int]:
        """Lấy kích thước màn hình."""
        try:
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[0]
                return (monitor["width"], monitor["height"])
        except Exception:
            return (1920, 1080)

    def get_pixel_color(self, x: int, y: int) -> Optional[Tuple[int, int, int]]:
        """Lấy màu pixel tại toạ độ (x, y)."""
        try:
            img = self.capture_screen(region=(x, y, 1, 1))
            if img:
                return img.getpixel((0, 0))
        except Exception:
            pass
        return None
