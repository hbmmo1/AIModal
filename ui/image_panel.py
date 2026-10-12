"""
Image Panel — Giao diện tạo ảnh AI đa mô hình.
Chọn model, nhập prompt, chọn size, preview kết quả.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QComboBox, QGroupBox, QFrame, QScrollArea,
    QGridLayout, QSpinBox, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QPixmap, QImage

from ui.theme import COLORS, get_card_style
from core.image_generator import ImageGenerator, IMAGE_MODELS, SIZE_PRESETS, ImageModelInfo
from core.model_registry import PROVIDER_DISPLAY

logger = logging.getLogger(__name__)


class ImageGenWorker(QThread):
    """Worker thread tạo ảnh."""
    result_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)

    def __init__(self, generator, prompt, model_id, width, height, num_images, style):
        super().__init__()
        self.generator = generator
        self.prompt = prompt
        self.model_id = model_id
        self.width = width
        self.height = height
        self.num_images = num_images
        self.style = style

    def run(self):
        try:
            result = self.generator.generate(
                self.prompt, self.model_id, self.width, self.height,
                self.num_images, style=self.style
            )
            self.result_ready.emit(result)
        except Exception as e:
            self.error_occurred.emit(str(e))


class ImagePanel(QWidget):
    """Panel tạo ảnh AI."""

    def __init__(self, image_generator: ImageGenerator, parent=None):
        super().__init__(parent)
        self.generator = image_generator
        self._worker: Optional[ImageGenWorker] = None
        self._setup_ui()

    def refresh_theme(self):
        """Cập nhật theme cho ImagePanel."""
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        if hasattr(self, '_header'):
            self._header.setStyleSheet(f"background-color: {COLORS['bg_secondary']}; border-bottom: 1px solid {COLORS['border']};")
        if hasattr(self, '_content'):
            self._content.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        if hasattr(self, '_left_panel'):
            self._left_panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                }}
            """)
        if hasattr(self, '_right_panel'):
            self._right_panel.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 12px;
                }}
            """)

    def _setup_ui(self):
        self.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._header = QFrame()
        self._header.setFixedHeight(60)
        self._header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_secondary']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)
        header_layout = QHBoxLayout(self._header)
        header_layout.setContentsMargins(20, 0, 20, 0)

        title = QLabel("🎨 AI Image Generator — Tạo Ảnh AI")
        title.setFont(QFont("Segoe UI", 15, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        layout.addWidget(self._header)

        # Content
        self._content = QWidget()
        self._content.setStyleSheet(f"background-color: {COLORS['bg_primary']};")
        content_layout = QHBoxLayout(self._content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(16)

        # LEFT: Controls
        self._left_panel = self._create_controls()
        content_layout.addWidget(self._left_panel, 2)

        # RIGHT: Preview
        self._right_panel = self._create_preview()
        content_layout.addWidget(self._right_panel, 3)

        layout.addWidget(self._content, 1)

    def _create_controls(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Model selector
        model_group = QGroupBox("Mô hình AI ảnh")
        model_layout = QVBoxLayout(model_group)

        self._model_combo = QComboBox()
        for m in IMAGE_MODELS:
            prov = PROVIDER_DISPLAY.get(m.provider, {})
            icon = prov.get("icon", "⚡")
            stars = "⭐" if m.is_recommended else ""
            price = f"${m.price_per_image:.3f}/ảnh"
            quality = "●" * m.quality_rating + "○" * (5 - m.quality_rating)
            self._model_combo.addItem(
                f"{icon} {m.name}  [{price}]  {quality} {stars}", m.id
            )
        self._model_combo.currentIndexChanged.connect(self._on_model_changed)
        model_layout.addWidget(self._model_combo)

        self._model_desc = QLabel("")
        self._model_desc.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        self._model_desc.setWordWrap(True)
        model_layout.addWidget(self._model_desc)

        layout.addWidget(model_group)

        # Prompt
        prompt_group = QGroupBox("Mô tả ảnh (Prompt)")
        prompt_layout = QVBoxLayout(prompt_group)

        self._prompt_input = QTextEdit()
        self._prompt_input.setPlaceholderText(
            "Mô tả chi tiết ảnh bạn muốn tạo...\n\n"
            "VD: A cute robot cat sitting on a neon-lit desk, cyberpunk style, "
            "highly detailed, 4K, cinematic lighting"
        )
        self._prompt_input.setMaximumHeight(100)
        prompt_layout.addWidget(self._prompt_input)

        layout.addWidget(prompt_group)

        # Style & Size
        options_group = QGroupBox("Tuỳ chọn")
        options_layout = QVBoxLayout(options_group)

        # Style
        style_row = QHBoxLayout()
        style_row.addWidget(QLabel("Style:"))
        self._style_combo = QComboBox()
        self._style_combo.addItems([
            "Tự động", "Photorealistic", "Digital Art", "Anime",
            "Oil Painting", "Watercolor", "3D Render", "Pixel Art",
            "Minimalist", "Cinematic", "Fantasy", "Sketch"
        ])
        style_row.addWidget(self._style_combo, 1)
        options_layout.addLayout(style_row)

        # Size
        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Kích thước:"))
        self._size_combo = QComboBox()
        for name in SIZE_PRESETS.keys():
            self._size_combo.addItem(name)
        size_row.addWidget(self._size_combo, 1)
        options_layout.addLayout(size_row)

        # Number
        num_row = QHBoxLayout()
        num_row.addWidget(QLabel("Số ảnh:"))
        self._num_spin = QSpinBox()
        self._num_spin.setRange(1, 4)
        self._num_spin.setValue(1)
        num_row.addWidget(self._num_spin)
        num_row.addStretch()
        options_layout.addLayout(num_row)

        layout.addWidget(options_group)

        # Generate button
        self._gen_btn = QPushButton("🎨  Tạo ảnh")
        self._gen_btn.setObjectName("primaryButton")
        self._gen_btn.setFixedHeight(44)
        self._gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gen_btn.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._gen_btn.clicked.connect(self._generate)
        layout.addWidget(self._gen_btn)

        # Status
        self._status = QLabel("Sẵn sàng")
        self._status.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 11px;")
        layout.addWidget(self._status)

        layout.addStretch()

        # Init model description
        self._on_model_changed()

        return panel

    def _create_preview(self) -> QFrame:
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        preview_label = QLabel("Preview")
        preview_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 12px; font-weight: 600;")
        layout.addWidget(preview_label)

        # Scroll area for images
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        self._preview_container = QWidget()
        self._preview_layout = QVBoxLayout(self._preview_container)
        self._preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Placeholder
        self._placeholder = QLabel("🎨\n\nẢnh AI sẽ hiển thị ở đây\nNhập prompt và nhấn 'Tạo ảnh'")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(f"""
            color: {COLORS['text_muted']};
            font-size: 14px;
            padding: 60px;
            border: 2px dashed {COLORS['border']};
            border-radius: 12px;
        """)
        self._preview_layout.addWidget(self._placeholder)

        scroll.setWidget(self._preview_container)
        layout.addWidget(scroll, 1)

        # Save button
        save_row = QHBoxLayout()
        self._save_btn = QPushButton("💾 Lưu ảnh")
        self._save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save_image)
        save_row.addStretch()
        save_row.addWidget(self._save_btn)
        layout.addLayout(save_row)

        return panel

    def _on_model_changed(self):
        idx = self._model_combo.currentIndex()
        if 0 <= idx < len(IMAGE_MODELS):
            m = IMAGE_MODELS[idx]
            self._model_desc.setText(
                f"{m.description}\n"
                f"Max: {m.max_resolution} | "
                f"Edit: {'✅' if m.supports_editing else '❌'} | "
                f"Tốc độ: {'●' * m.speed_rating}{'○' * (5 - m.speed_rating)}"
            )

    def _generate(self):
        prompt = self._prompt_input.toPlainText().strip()
        if not prompt:
            self._status.setText("⚠️ Vui lòng nhập mô tả ảnh!")
            return

        model_id = self._model_combo.currentData()
        size_name = self._size_combo.currentText()
        width, height = SIZE_PRESETS.get(size_name, (1024, 1024))

        style = self._style_combo.currentText()
        if style == "Tự động":
            style = ""

        self._gen_btn.setEnabled(False)
        self._status.setText("🎨 Đang tạo ảnh... Vui lòng chờ...")

        self._worker = ImageGenWorker(
            self.generator, prompt, model_id, width, height,
            self._num_spin.value(), style
        )
        self._worker.result_ready.connect(self._on_result)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.start()

    def _on_result(self, result: dict):
        self._gen_btn.setEnabled(True)
        error = result.get("error")
        if error:
            self._status.setText(f"❌ {error}")
            return

        images = result.get("images", [])
        paths = result.get("paths", [])
        self._last_paths = paths

        if not images:
            self._status.setText("⚠️ Không nhận được ảnh")
            return

        # Clear preview
        while self._preview_layout.count() > 0:
            item = self._preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Show images
        for i, img in enumerate(images):
            # Convert PIL to QPixmap
            img_rgb = img.convert("RGB")
            data = img_rgb.tobytes("raw", "RGB")
            qimg = QImage(data, img_rgb.width, img_rgb.height,
                          img_rgb.width * 3, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qimg)

            # Scale to fit
            scaled = pixmap.scaled(600, 600, Qt.AspectRatioMode.KeepAspectRatio,
                                   Qt.TransformationMode.SmoothTransformation)

            label = QLabel()
            label.setPixmap(scaled)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"border: 1px solid {COLORS['border']}; border-radius: 8px; padding: 4px;")
            self._preview_layout.addWidget(label)

            if i < len(paths):
                path_label = QLabel(os.path.basename(paths[i]))
                path_label.setStyleSheet(f"color: {COLORS['text_muted']}; font-size: 10px;")
                path_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._preview_layout.addWidget(path_label)

        self._save_btn.setEnabled(True)
        self._status.setText(f"✅ Đã tạo {len(images)} ảnh thành công!")

    def _on_error(self, error: str):
        self._gen_btn.setEnabled(True)
        self._status.setText(f"❌ Lỗi: {error[:150]}")

    def _save_image(self):
        if hasattr(self, '_last_paths') and self._last_paths:
            folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu")
            if folder:
                import shutil
                for p in self._last_paths:
                    if os.path.exists(p):
                        shutil.copy2(p, folder)
                self._status.setText(f"💾 Đã lưu {len(self._last_paths)} ảnh vào {folder}")
