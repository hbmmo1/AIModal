"""
Image Generator — Tạo ảnh AI đa nhà cung cấp.
Hỗ trợ: Gemini Imagen, OpenAI DALL-E, Stability AI, Together AI (FLUX).
"""

import os
import io
import json
import time
import base64
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from PIL import Image

from core.key_manager import KeyManager
from core.model_registry import Provider

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "output", "images")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ============================================================
# Image Model Registry
# ============================================================

@dataclass
class ImageModelInfo:
    """Thông tin 1 mô hình sinh ảnh."""
    id: str
    name: str
    provider: str
    price_per_image: float       # USD / ảnh
    max_resolution: str          # vd: "1024x1024"
    supports_editing: bool       # Hỗ trợ chỉnh sửa ảnh
    supports_variations: bool    # Hỗ trợ tạo biến thể
    quality_rating: int          # 1-5
    speed_rating: int            # 1-5
    description: str = ""
    is_recommended: bool = False


IMAGE_MODELS: List[ImageModelInfo] = [
    # === GOOGLE GEMINI IMAGEN ===
    ImageModelInfo(
        id="imagen-4-ultra",
        name="Imagen 4 Ultra",
        provider=Provider.GEMINI,
        price_per_image=0.06,
        max_resolution="2048x2048",
        supports_editing=True,
        supports_variations=True,
        quality_rating=5,
        speed_rating=4,
        description="Flagship Google — photorealistic, text rendering tốt nhất",
        is_recommended=True,
    ),
    ImageModelInfo(
        id="imagen-4",
        name="Imagen 4",
        provider=Provider.GEMINI,
        price_per_image=0.04,
        max_resolution="1024x1024",
        supports_editing=True,
        supports_variations=True,
        quality_rating=5,
        speed_rating=4,
        description="Chất lượng cao, giá hợp lý — khuyên dùng",
        is_recommended=True,
    ),
    ImageModelInfo(
        id="imagen-3-fast",
        name="Imagen 3 Fast",
        provider=Provider.GEMINI,
        price_per_image=0.02,
        max_resolution="1024x1024",
        supports_editing=False,
        supports_variations=False,
        quality_rating=4,
        speed_rating=5,
        description="Nhanh nhất Google, giá rẻ",
    ),

    # === OPENAI DALL-E ===
    ImageModelInfo(
        id="dall-e-3",
        name="DALL-E 3",
        provider=Provider.OPENAI,
        price_per_image=0.04,
        max_resolution="1024x1792",
        supports_editing=False,
        supports_variations=False,
        quality_rating=5,
        speed_rating=4,
        description="Prompt understanding xuất sắc, sáng tạo cao",
        is_recommended=True,
    ),
    ImageModelInfo(
        id="dall-e-2",
        name="DALL-E 2",
        provider=Provider.OPENAI,
        price_per_image=0.02,
        max_resolution="1024x1024",
        supports_editing=True,
        supports_variations=True,
        quality_rating=3,
        speed_rating=5,
        description="Rẻ, nhanh, hỗ trợ edit/variations",
    ),
    ImageModelInfo(
        id="gpt-image-1",
        name="GPT Image 1",
        provider=Provider.OPENAI,
        price_per_image=0.02,
        max_resolution="1024x1024",
        supports_editing=True,
        supports_variations=False,
        quality_rating=5,
        speed_rating=4,
        description="Model mới nhất OpenAI — tích hợp GPT reasoning",
        is_recommended=True,
    ),

    # === STABILITY AI ===
    ImageModelInfo(
        id="sd3.5-large",
        name="Stable Diffusion 3.5 Large",
        provider="stability",
        price_per_image=0.065,
        max_resolution="1024x1024",
        supports_editing=True,
        supports_variations=False,
        quality_rating=5,
        speed_rating=3,
        description="Open-source flagship — artistic style đa dạng",
    ),
    ImageModelInfo(
        id="sd3.5-medium",
        name="Stable Diffusion 3.5 Medium",
        provider="stability",
        price_per_image=0.035,
        max_resolution="1024x1024",
        supports_editing=True,
        supports_variations=False,
        quality_rating=4,
        speed_rating=4,
        description="Cân bằng tốt giữa chất lượng và tốc độ",
    ),

    # === TOGETHER AI (FLUX) ===
    ImageModelInfo(
        id="flux-1.1-pro-ultra",
        name="FLUX 1.1 Pro Ultra",
        provider="together",
        price_per_image=0.06,
        max_resolution="2048x2048",
        supports_editing=False,
        supports_variations=False,
        quality_rating=5,
        speed_rating=3,
        description="Black Forest Labs — photorealistic cực đỉnh",
        is_recommended=True,
    ),
    ImageModelInfo(
        id="flux-schnell",
        name="FLUX Schnell (Nhanh)",
        provider="together",
        price_per_image=0.003,
        max_resolution="1024x1024",
        supports_editing=False,
        supports_variations=False,
        quality_rating=4,
        speed_rating=5,
        description="Rẻ nhất — 0.3¢/ảnh, tốc độ cực nhanh",
    ),
]

IMAGE_MODELS_DICT = {m.id: m for m in IMAGE_MODELS}


# ============================================================
# Size presets
# ============================================================

SIZE_PRESETS = {
    "1:1 (1024x1024)": (1024, 1024),
    "16:9 (1792x1024)": (1792, 1024),
    "9:16 (1024x1792)": (1024, 1792),
    "4:3 (1024x768)": (1024, 768),
    "3:4 (768x1024)": (768, 1024),
    "3:2 (1536x1024)": (1536, 1024),
}


# ============================================================
# Image Generator
# ============================================================

class ImageGenerator:
    """Tạo ảnh AI đa provider."""

    def __init__(self, key_manager: KeyManager):
        self.key_mgr = key_manager

    def get_available_models(self) -> List[ImageModelInfo]:
        """Lấy models có key khả dụng."""
        available = []
        for model in IMAGE_MODELS:
            provider = model.provider
            if provider in (Provider.GEMINI, Provider.OPENAI):
                if self.key_mgr.get_active_key(provider):
                    available.append(model)
            elif provider == "stability":
                if os.environ.get("STABILITY_API_KEY") or self.key_mgr.get_active_key("stability"):
                    available.append(model)
            elif provider == "together":
                if os.environ.get("TOGETHER_API_KEY") or self.key_mgr.get_active_key("together"):
                    available.append(model)
        return available

    def get_all_models(self) -> List[ImageModelInfo]:
        return IMAGE_MODELS

    def generate(
        self,
        prompt: str,
        model_id: str = "imagen-4",
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        negative_prompt: str = "",
        style: str = "",
    ) -> Dict[str, Any]:
        """
        Tạo ảnh từ prompt.
        
        Returns:
            Dict: images (list PIL.Image), paths (list str), model, error
        """
        model_info = IMAGE_MODELS_DICT.get(model_id)
        if not model_info:
            return {"images": [], "paths": [], "error": f"Model '{model_id}' không tồn tại"}

        full_prompt = f"{style} {prompt}".strip() if style else prompt

        try:
            if model_info.provider == Provider.GEMINI:
                return self._generate_gemini(full_prompt, model_id, width, height, num_images)
            elif model_info.provider == Provider.OPENAI:
                return self._generate_openai(full_prompt, model_id, width, height, num_images)
            elif model_info.provider == "stability":
                return self._generate_stability(full_prompt, model_id, width, height, negative_prompt)
            elif model_info.provider == "together":
                return self._generate_together(full_prompt, model_id, width, height, num_images)
            else:
                return {"images": [], "paths": [], "error": f"Provider '{model_info.provider}' chưa hỗ trợ"}
        except Exception as e:
            logger.error(f"[ImageGen] Lỗi: {e}")
            return {"images": [], "paths": [], "error": str(e)[:300]}

    def _generate_gemini(self, prompt, model_id, width, height, num_images) -> Dict:
        """Tạo ảnh bằng Gemini Imagen."""
        from google import genai
        from google.genai import types

        api_key = self.key_mgr.get_active_key(Provider.GEMINI)
        if not api_key:
            return {"images": [], "paths": [], "error": "Chưa có Gemini API key"}

        client = genai.Client(api_key=api_key)

        # Gemini image generation via generateContent with image output
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            )
        )

        images = []
        paths = []

        if response and response.candidates:
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    img_data = part.inline_data.data
                    img = Image.open(io.BytesIO(img_data))
                    images.append(img)
                    path = self._save_image(img, model_id)
                    paths.append(path)

        if not images:
            return {"images": [], "paths": [], "error": "Gemini không trả về ảnh. Thử prompt khác."}

        self.key_mgr.increment_request(api_key)
        return {"images": images, "paths": paths, "model": model_id, "error": None}

    def _generate_openai(self, prompt, model_id, width, height, num_images) -> Dict:
        """Tạo ảnh bằng OpenAI DALL-E / GPT Image."""
        api_key = self.key_mgr.get_active_key(Provider.OPENAI)
        if not api_key:
            return {"images": [], "paths": [], "error": "Chưa có OpenAI API key"}

        # Chọn size gần nhất OpenAI hỗ trợ
        size = "1024x1024"
        if width > height:
            size = "1792x1024"
        elif height > width:
            size = "1024x1792"

        payload = {
            "model": model_id,
            "prompt": prompt,
            "n": min(num_images, 4),
            "size": size,
            "response_format": "b64_json",
        }

        if model_id == "dall-e-3":
            payload["quality"] = "hd"

        resp = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=120,
        )

        if resp.status_code != 200:
            return {"images": [], "paths": [], "error": f"OpenAI lỗi: {resp.text[:200]}"}

        data = resp.json()
        images, paths = [], []
        for item in data.get("data", []):
            b64 = item.get("b64_json", "")
            if b64:
                img_bytes = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_bytes))
                images.append(img)
                paths.append(self._save_image(img, model_id))

        self.key_mgr.increment_request(api_key)
        return {"images": images, "paths": paths, "model": model_id, "error": None}

    def _generate_stability(self, prompt, model_id, width, height, negative_prompt) -> Dict:
        """Tạo ảnh bằng Stability AI."""
        api_key = os.environ.get("STABILITY_API_KEY") or self.key_mgr.get_active_key("stability")
        if not api_key:
            return {"images": [], "paths": [], "error": "Chưa có Stability API key"}

        model_map = {
            "sd3.5-large": "sd3.5-large",
            "sd3.5-medium": "sd3.5-medium",
        }

        resp = requests.post(
            "https://api.stability.ai/v2beta/stable-image/generate/sd3",
            headers={"Authorization": f"Bearer {api_key}", "Accept": "image/*"},
            files={"none": ""},
            data={
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "model": model_map.get(model_id, "sd3.5-medium"),
                "output_format": "png",
                "aspect_ratio": "1:1",
            },
            timeout=120,
        )

        if resp.status_code != 200:
            return {"images": [], "paths": [], "error": f"Stability lỗi: {resp.text[:200]}"}

        img = Image.open(io.BytesIO(resp.content))
        path = self._save_image(img, model_id)
        return {"images": [img], "paths": [path], "model": model_id, "error": None}

    def _generate_together(self, prompt, model_id, width, height, num_images) -> Dict:
        """Tạo ảnh bằng Together AI (FLUX)."""
        api_key = os.environ.get("TOGETHER_API_KEY") or self.key_mgr.get_active_key("together")
        if not api_key:
            return {"images": [], "paths": [], "error": "Chưa có Together AI API key"}

        model_map = {
            "flux-1.1-pro-ultra": "black-forest-labs/FLUX.1.1-pro",
            "flux-schnell": "black-forest-labs/FLUX.1-schnell-Free",
        }

        resp = requests.post(
            "https://api.together.xyz/v1/images/generations",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model_map.get(model_id, "black-forest-labs/FLUX.1-schnell-Free"),
                "prompt": prompt,
                "width": width,
                "height": height,
                "n": min(num_images, 4),
                "response_format": "b64_json",
            },
            timeout=120,
        )

        if resp.status_code != 200:
            return {"images": [], "paths": [], "error": f"Together lỗi: {resp.text[:200]}"}

        data = resp.json()
        images, paths = [], []
        for item in data.get("data", []):
            b64 = item.get("b64_json", "")
            if b64:
                img_bytes = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_bytes))
                images.append(img)
                paths.append(self._save_image(img, model_id))

        return {"images": images, "paths": paths, "model": model_id, "error": None}

    def _save_image(self, img: Image.Image, model_id: str) -> str:
        """Lưu ảnh vào thư mục output."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"{model_id}_{timestamp}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        img.save(filepath, format="PNG")
        logger.info(f"[ImageGen] Đã lưu: {filepath}")
        return filepath
