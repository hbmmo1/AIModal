"""
AI Engine — Bộ xử lý trung tâm Multi-Provider cho AI Claw.
Hỗ trợ: Gemini, OpenAI (ChatGPT), Anthropic (Claude), DeepSeek, Qwen.
- Multi-turn conversation với context memory
- Tool calling / Function calling
- Vision analysis cho screenshots  
- Auto-retry + key rotation khi quota hết
- Chuyển đổi provider/model linh hoạt
"""

import os
import io
import re
import json
import time
import logging
import warnings
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from PIL import Image

from core.key_manager import KeyManager
from core.model_registry import (
    Provider, ModelInfo, ModelTier, PROVIDER_DISPLAY,
    registry as model_registry
)

warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAX_RETRIES = 3


def clean_markdown(text: str) -> str:
    """Làm sạch markdown formatting nặng cho hiển thị UI thân thiện."""
    if not text:
        return ""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        if re.match(r'^\s*\|?\s*[-:]+\s*\|', line):
            continue
        if line.strip().startswith('|') and line.strip().endswith('|'):
            cells = [c.strip() for c in line.strip().strip('|').split('|') if c.strip()]
            if cells:
                cleaned.append(' • ' + ' | '.join(cells))
        else:
            cleaned.append(line)
    return '\n'.join(cleaned).strip()


# ============================================================
# Mapping Model ID sang Model API thực tế của Google
# ============================================================
GEMINI_MODEL_MAP = {
    # Gemini 3.7 Series
    "gemini-3.7-flash-high": "gemini-3.7-flash",
    "gemini-3.7-flash-medium": "gemini-3.7-flash",
    "gemini-3.7-flash-low": "gemini-3.5-flash-lite",
    "gemini-3.7-flash": "gemini-3.7-flash",
    # Gemini 3.6 Series
    "gemini-3.6-flash-high": "gemini-3.6-flash",
    "gemini-3.6-flash-medium": "gemini-3.6-flash",
    "gemini-3.6-flash-low": "gemini-3.5-flash-lite",
    "gemini-3.6-flash": "gemini-3.6-flash",
    # Gemini 3.5 Series
    "gemini-3.5-flash-high": "gemini-3.5-flash",
    "gemini-3.5-flash-medium": "gemini-3.5-flash",
    "gemini-3.5-flash-low": "gemini-3.5-flash-lite",
    "gemini-3.5-flash": "gemini-3.5-flash",
    "gemini-3.5-flash-lite": "gemini-3.5-flash-lite",
    # Gemini 3.1 Series
    "gemini-3.1-pro-high": "gemini-3.1-pro-preview",
    "gemini-3.1-pro-medium": "gemini-3.1-pro-preview",
    "gemini-3.1-pro-low": "gemini-3.1-pro-preview",
    "gemini-3.1-pro": "gemini-3.1-pro-preview",
    "gemini-3.1-flash-lite": "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview": "gemini-3.1-flash-lite",
    # Gemini 2.5 Series
    "gemini-2.5-flash": "gemini-2.5-flash",
    "gemini-2.5-flash-lite": "gemini-2.5-flash-lite",
    "gemini-2.5-pro": "gemini-2.5-pro",
    # Aliases
    "gemini-flash": "gemini-flash-latest",
    "gemini-flash-lite": "gemini-flash-lite-latest",
    "gemini-pro": "gemini-pro-latest",
    "gemini-flash-latest": "gemini-flash-latest",
    "gemini-flash-lite-latest": "gemini-flash-lite-latest",
    "gemini-pro-latest": "gemini-pro-latest",
    # Legacy fallbacks
    "gemini-2.0-flash": "gemini-3.5-flash",
    "gemini-2.0-flash-lite": "gemini-3.5-flash-lite",
    "gemini-2.0-pro-exp-02-05": "gemini-3.1-pro-preview",
    "gemini-1.5-flash": "gemini-3.5-flash-lite",
    "gemini-1.5-flash-8b": "gemini-3.5-flash-lite",
    "gemini-1.5-pro": "gemini-2.5-pro",
}


def resolve_gemini_api_model(model_name: str) -> str:
    """Trả về model ID tương thích với Google GenAI API endpoint."""
    return GEMINI_MODEL_MAP.get(model_name, model_name)


# ============================================================
# Tool Definitions cho Function Calling
# ============================================================
AUTOMATION_TOOLS = [
    {
        "name": "click_at",
        "description": "Thực hiện click chuột tại toạ độ (x, y) trên màn hình desktop. Chỉ gọi khi người dùng yêu cầu thao tác click chuột cụ thể.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Toạ độ X"},
                "y": {"type": "integer", "description": "Toạ độ Y"},
                "button": {"type": "string", "enum": ["left", "right", "double"], "description": "Nút chuột"}
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "type_text",
        "description": "Gõ văn bản vào vị trí con trỏ bàn phím trên desktop. Chỉ gọi khi người dùng yêu cầu gõ/nhập liệu vào một ứng dụng.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Văn bản cần gõ"},
                "interval": {"type": "number", "description": "Khoảng cách giữa các phím (giây)"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "press_key",
        "description": "Nhấn phím hoặc tổ hợp phím trên bàn phím máy tính. Chỉ gọi khi người dùng yêu cầu nhấn phím (vd: enter, tab, ctrl+c).",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {"type": "string", "description": "Phím cần nhấn (vd: enter, tab, ctrl+c, alt+f4)"}
            },
            "required": ["key"]
        }
    },
    {
        "name": "take_screenshot",
        "description": "Chụp ảnh màn hình máy tính hiện tại. Chỉ gọi khi người dùng yêu cầu chụp hoặc phân tích màn hình.",
        "parameters": {"type": "object", "properties": {}}
    },
    {
        "name": "open_application",
        "description": "Khởi chạy một phần mềm hoặc mở một đường dẫn URL trên máy tính. CHỈ gọi khi người dùng yêu cầu mở ứng dụng hoặc trang web cụ thể.",
        "parameters": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Đường dẫn/tên ứng dụng hoặc URL trang web cần mở"}
            },
            "required": ["target"]
        }
    },
    {
        "name": "wait_seconds",
        "description": "Tạm dừng kịch bản trong một khoảng thời gian.",
        "parameters": {
            "type": "object",
            "properties": {
                "seconds": {"type": "number", "description": "Số giây cần chờ"}
            },
            "required": ["seconds"]
        }
    },
    {
        "name": "scroll",
        "description": "Cuộn chuột lên hoặc xuống trên màn hình.",
        "parameters": {
            "type": "object",
            "properties": {
                "amount": {"type": "integer", "description": "Số nấc cuộn (âm = xuống, dương = lên)"},
                "x": {"type": "integer", "description": "Toạ độ X (tuỳ chọn)"},
                "y": {"type": "integer", "description": "Toạ độ Y (tuỳ chọn)"}
            },
            "required": ["amount"]
        }
    },
    {
        "name": "create_workflow",
        "description": "Tạo kịch bản tự động hoá từ danh sách các bước. Chỉ gọi khi người dùng yêu cầu lưu/tạo workflow.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Tên workflow"},
                "steps": {
                    "type": "array",
                    "items": {"type": "object", "properties": {"action": {"type": "string"}, "params": {"type": "object"}}},
                    "description": "Danh sách các bước"
                }
            },
            "required": ["name", "steps"]
        }
    }
]


class GeminiAIEngine:
    """
    Bộ xử lý trung tâm Multi-Provider AI cho AI Claw.
    Hỗ trợ Gemini, OpenAI, Anthropic, DeepSeek, Qwen.
    """

    def __init__(
        self,
        api_key: str = "",
        model_name: str = "",
        key_manager: Optional[KeyManager] = None,
        tool_executor: Optional[Callable] = None,
    ):
        self.key_mgr = key_manager or KeyManager()

        if api_key and api_key != "YOUR_GEMINI_API_KEY_HERE":
            self.key_mgr.add_key(api_key)

        # Lấy model mặc định từ registry
        if not model_name:
            default = model_registry.get_default_model()
            model_name = default.id if default else "gemini-3.6-flash"
        
        self.model_name = model_name
        self._model_info = model_registry.get_model(model_name)
        self.tool_executor = tool_executor
        self.client = None
        self.chat_session = None
        self.conversation_history: List[Dict] = []
        self.persona = self._load_persona()
        self.knowledge_base = None  # Set by MainWindow
        self.screen_analyzer = None  # Set by MainWindow — dùng để convert ảnh sang WebP

        self._init_client()

    @property
    def provider(self) -> str:
        """Provider hiện tại."""
        if self._model_info:
            return self._model_info.provider
        return Provider.GEMINI

    @property
    def api_key(self) -> str:
        return self.key_mgr.get_active_key(self.provider) or ""

    @property
    def model_info(self) -> Optional[ModelInfo]:
        return self._model_info

    def _load_persona(self) -> str:
        """Load system prompt persona."""
        persona_path = os.path.join(BASE_DIR, "config", "persona.txt")
        try:
            if os.path.exists(persona_path):
                with open(persona_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
        except Exception as e:
            logger.warning(f"Không thể đọc persona.txt: {e}")
        return "Bạn là AI Claw — Trợ lý Tự động hoá Thông minh. Trả lời bằng tiếng Việt."

    def _build_system_prompt(self, user_message: str = "") -> str:
        """
        Xây dựng system prompt = persona + kiến thức cá nhân.
        Kiến thức cá nhân được search theo user_message để lấy context phù hợp.
        """
        system = self.persona

        if self.knowledge_base:
            try:
                kb_context = self.knowledge_base.build_ai_context(user_message)
                if kb_context:
                    system = f"{self.persona}\n\n{kb_context}"
            except Exception as e:
                logger.debug(f"[AI Engine] Không thể load kiến thức cá nhân: {e}")

        return system

    def _init_client(self):
        """Khởi tạo client theo provider hiện tại."""
        active_key = self.api_key
        if not active_key:
            logger.warning(f"[AI Engine] Chưa có API key cho {self.provider}. Vui lòng thêm key trong Settings.")
            self.client = None
            return

        try:
            if self.provider == Provider.GEMINI:
                from google import genai
                self.client = genai.Client(api_key=active_key, http_options={'timeout': 60000})
            else:
                # OpenAI-compatible providers dùng requests trực tiếp
                self.client = True  # Marker: connected
            
            prov_name = PROVIDER_DISPLAY.get(self.provider, {}).get("name", self.provider)
            logger.info(f"[AI Engine] Đã kết nối {prov_name} ({self.model_name}) với key ...{active_key[-8:]}")
        except Exception as e:
            logger.error(f"[AI Engine] Lỗi khởi tạo client: {e}")
            self.client = None

    def _reinit_with_key(self, new_key: str):
        """Tái khởi tạo client với key mới."""
        try:
            if self.provider == Provider.GEMINI:
                from google import genai
                self.client = genai.Client(api_key=new_key, http_options={'timeout': 60000})
            else:
                self.client = True
            self.chat_session = None
            logger.info(f"[AI Engine] Đã chuyển sang key mới: ...{new_key[-8:]}")
        except Exception as e:
            logger.error(f"[AI Engine] Lỗi reinit client: {e}")

    def set_model(self, model_id: str, provider: str = None):
        """Đổi model (có thể đổi cả provider)."""
        info = model_registry.get_model(model_id)
        if not info:
            prov = provider or model_registry.detect_provider_from_model_id(model_id) or self.provider
            info = model_registry.register_dynamic_model(model_id, prov)

        old_provider = self.provider
        
        self.model_name = model_id
        self._model_info = info
        self.chat_session = None
        
        # Nếu đổi provider hoặc client chưa kết nối → reinit client với key của provider đó
        if (info and info.provider != old_provider) or self.client is None:
            self._init_client()
        
        prov_name = PROVIDER_DISPLAY.get(self.provider, {}).get("name", self.provider)
        display_name = info.name if info else model_id
        logger.info(f"[AI Engine] Đã đổi sang: {prov_name} / {display_name}")

    def set_model_by_tier(self, tier: str, provider: str = None):
        """Đổi model theo tier (cheapest, balanced, moderate, best)."""
        if tier == ModelTier.CHEAPEST:
            model = model_registry.get_cheapest_model(provider)
        elif tier == ModelTier.BALANCED:
            model = model_registry.get_balanced_model(provider)
        elif tier == ModelTier.BEST:
            model = model_registry.get_best_model(provider)
        else:
            model = model_registry.get_balanced_model(provider)
        
        if model:
            self.set_model(model.id)

    def set_tool_executor(self, executor: Callable):
        """Đặt callback thực thi tool calls."""
        self.tool_executor = executor

    def clear_history(self):
        """Xoá lịch sử hội thoại trong bộ nhớ đệm AI."""
        self.conversation_history = []
        self.chat_session = None
        logger.info("[AI Engine] Đã xoá bộ nhớ đệm hội thoại.")

    # ============================================================
    # CHAT — Unified interface cho tất cả providers
    # ============================================================

    def chat(
        self,
        message: str,
        image: Optional[Image.Image] = None,
        enable_tools: bool = True,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """Gửi tin nhắn — tự động route đến đúng provider."""
        if not self.client:
            self._init_client()
            if not self.client:
                prov_name = PROVIDER_DISPLAY.get(self.provider, {}).get("name", self.provider)
                return {
                    "text": f"⚠️ Chưa có API key cho {prov_name}. Vui lòng thêm key trong Settings.",
                    "tool_calls": [], "error": True
                }

        # Route đến provider phù hợp
        if self.provider == Provider.GEMINI:
            return self._chat_gemini(message, image, enable_tools, temperature)
        elif self.provider in (Provider.OPENAI, Provider.DEEPSEEK, Provider.QWEN):
            return self._chat_openai_compatible(message, image, enable_tools, temperature)
        elif self.provider == Provider.ANTHROPIC:
            return self._chat_anthropic(message, image, enable_tools, temperature)
        else:
            return {"text": f"⚠️ Provider '{self.provider}' chưa được hỗ trợ.", "tool_calls": [], "error": True}

    # ============================================================
    # GEMINI Provider
    # ============================================================

    def _chat_gemini(self, message: str, image=None, enable_tools=True, temperature=0.7) -> Dict:
        result = {"text": "", "tool_calls": [], "error": False}
        target_model = resolve_gemini_api_model(self.model_name)

        for attempt in range(MAX_RETRIES):
            try:
                from google import genai
                from google.genai import types

                contents = self._build_gemini_contents(message, image)
                config = self._build_gemini_config(temperature, enable_tools, message)

                try:
                    response = self.client.models.generate_content(
                        model=target_model, contents=contents, config=config,
                    )
                except Exception as api_err:
                    err_str = str(api_err)
                    if "404" in err_str or "NOT_FOUND" in err_str.upper() or "not available" in err_str.lower():
                        logger.warning(f"[AI Engine] Model '{target_model}' không khả dụng (404), tự động fallback sang 'gemini-3.5-flash-lite'")
                        target_model = "gemini-3.5-flash-lite"
                        try:
                            response = self.client.models.generate_content(
                                model=target_model, contents=contents, config=config,
                            )
                        except Exception as fb_err:
                            if "404" in str(fb_err) or "NOT_FOUND" in str(fb_err).upper():
                                logger.warning("[AI Engine] Model 'gemini-3.5-flash-lite' không khả dụng, tiếp tục fallback sang 'gemini-flash-lite-latest'")
                                target_model = "gemini-flash-lite-latest"
                                response = self.client.models.generate_content(
                                    model=target_model, contents=contents, config=config,
                                )
                            else:
                                raise fb_err
                    else:
                        raise api_err

                if not response or not response.candidates:
                    result["text"] = "⚠️ AI không trả lời. Vui lòng thử lại."
                    result["error"] = True
                    return result

                candidate = response.candidates[0]
                tool_calls, text_parts = [], []

                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        tool_calls.append({"name": fc.name, "args": dict(fc.args) if fc.args else {}})
                    elif hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)

                result["text"] = clean_markdown("\n".join(text_parts))
                result["tool_calls"] = tool_calls
                self._save_to_history(message, result, image)
                self.key_mgr.increment_request(self.api_key)
                return result

            except Exception as e:
                if not self._handle_retry(e, attempt, result):
                    return result

        return result

    def _build_gemini_contents(self, message, image=None):
        from google.genai import types
        contents = []
        for msg in self.conversation_history[-20:]:
            content_text = (msg.get("content") or "").strip()
            if not content_text:
                continue
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=content_text)]))
        
        parts = []
        if image:
            img_data, mime = self._convert_image(image)
            parts.append(types.Part.from_bytes(data=img_data, mime_type=mime))
        parts.append(types.Part.from_text(text=message.strip() or "Hãy hỗ trợ tôi."))
        contents.append(types.Content(role="user", parts=parts))
        return contents

    def _build_gemini_config(self, temperature, enable_tools, user_message=""):
        from google.genai import types
        system_prompt = self._build_system_prompt(user_message)
        config = types.GenerateContentConfig(
            temperature=temperature, top_p=0.95, max_output_tokens=8192,
            system_instruction=system_prompt,
        )
        if enable_tools and self._model_info and self._model_info.supports_tools:
            tools = []
            for tool_def in AUTOMATION_TOOLS:
                tools.append(types.Tool(
                    function_declarations=[types.FunctionDeclaration(
                        name=tool_def["name"], description=tool_def["description"],
                        parameters=tool_def.get("parameters"),
                    )]
                ))
            config.tools = tools
        return config

    # ============================================================
    # OPENAI-Compatible Provider (OpenAI, DeepSeek, Qwen)
    # ============================================================

    def _chat_openai_compatible(self, message, image=None, enable_tools=True, temperature=0.7) -> Dict:
        """Chat qua OpenAI-compatible API (OpenAI, DeepSeek, Qwen)."""
        import requests
        result = {"text": "", "tool_calls": [], "error": False}

        # Xác định API base URL
        api_urls = {
            Provider.OPENAI: "https://api.openai.com/v1/chat/completions",
            Provider.DEEPSEEK: "https://api.deepseek.com/chat/completions",
            Provider.QWEN: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/chat/completions",
        }
        url = api_urls.get(self.provider, api_urls[Provider.OPENAI])

        for attempt in range(MAX_RETRIES):
            try:
                active_key = self.api_key
                headers = {
                    "Authorization": f"Bearer {active_key}",
                    "Content-Type": "application/json",
                }

                # Build messages
                system_prompt = self._build_system_prompt(message)
                messages = [{"role": "system", "content": system_prompt}]
                for msg in self.conversation_history[-20:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

                # Current message
                if image and self.provider == Provider.OPENAI:
                    # OpenAI Vision
                    import base64
                    img_data, mime = self._convert_image(image)
                    img_b64 = base64.b64encode(img_data).decode()
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                            {"type": "text", "text": message}
                        ]
                    })
                else:
                    messages.append({"role": "user", "content": message})

                payload = {
                    "model": self.model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": 8192,
                }

                # Tools (function calling) — OpenAI format
                if enable_tools and self._model_info and self._model_info.supports_tools:
                    openai_tools = []
                    for tool_def in AUTOMATION_TOOLS:
                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": tool_def["name"],
                                "description": tool_def["description"],
                                "parameters": tool_def.get("parameters", {}),
                            }
                        })
                    payload["tools"] = openai_tools

                resp = requests.post(url, headers=headers, json=payload, timeout=60)

                if resp.status_code != 200:
                    error_body = resp.text[:300]
                    if resp.status_code == 429:
                        raise Exception(f"429 Rate Limited: {error_body}")
                    raise Exception(f"HTTP {resp.status_code}: {error_body}")

                data = resp.json()
                choice = data.get("choices", [{}])[0]
                msg_data = choice.get("message", {})

                # Text
                result["text"] = clean_markdown(msg_data.get("content", "") or "")

                # Tool calls
                tool_calls_data = msg_data.get("tool_calls", [])
                for tc in tool_calls_data:
                    func = tc.get("function", {})
                    args = {}
                    try:
                        args = json.loads(func.get("arguments", "{}"))
                    except Exception:
                        pass
                    result["tool_calls"].append({"name": func.get("name", ""), "args": args})

                self._save_to_history(message, result, image)
                self.key_mgr.increment_request(active_key)
                return result

            except Exception as e:
                if not self._handle_retry(e, attempt, result):
                    return result

        return result

    # ============================================================
    # ANTHROPIC Provider (Claude)
    # ============================================================

    def _chat_anthropic(self, message, image=None, enable_tools=True, temperature=0.7) -> Dict:
        """Chat qua Anthropic API (Claude)."""
        import requests
        result = {"text": "", "tool_calls": [], "error": False}

        for attempt in range(MAX_RETRIES):
            try:
                active_key = self.api_key
                headers = {
                    "x-api-key": active_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                }

                # Build messages
                messages = []
                for msg in self.conversation_history[-20:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})

                # Current message
                if image:
                    import base64
                    img_data, mime = self._convert_image(image)
                    img_b64 = base64.b64encode(img_data).decode()
                    messages.append({
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": mime, "data": img_b64}},
                            {"type": "text", "text": message}
                        ]
                    })
                else:
                    messages.append({"role": "user", "content": message})

                payload = {
                    "model": self.model_name,
                    "max_tokens": 8192,
                    "system": self._build_system_prompt(message),
                    "messages": messages,
                    "temperature": temperature,
                }

                # Tools
                if enable_tools and self._model_info and self._model_info.supports_tools:
                    claude_tools = []
                    for tool_def in AUTOMATION_TOOLS:
                        claude_tools.append({
                            "name": tool_def["name"],
                            "description": tool_def["description"],
                            "input_schema": tool_def.get("parameters", {}),
                        })
                    payload["tools"] = claude_tools

                resp = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload, timeout=60)

                if resp.status_code != 200:
                    error_body = resp.text[:300]
                    if resp.status_code == 429:
                        raise Exception(f"429 Rate Limited: {error_body}")
                    raise Exception(f"HTTP {resp.status_code}: {error_body}")

                data = resp.json()
                content_blocks = data.get("content", [])

                text_parts = []
                for block in content_blocks:
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        result["tool_calls"].append({
                            "name": block.get("name", ""),
                            "args": block.get("input", {})
                        })

                result["text"] = clean_markdown("\n".join(text_parts))
                self._save_to_history(message, result, image)
                self.key_mgr.increment_request(active_key)
                return result

            except Exception as e:
                if not self._handle_retry(e, attempt, result):
                    return result

        return result

    # ============================================================
    # Shared helpers
    # ============================================================

    def _convert_image(self, image: Image.Image) -> tuple:
        """
        Convert PIL Image sang bytes theo cấu hình screen_analyzer.
        Mặc định WebP 100% nếu không có screen_analyzer.
        Returns: (bytes_data, mime_type)
        """
        if self.screen_analyzer:
            img_bytes = self.screen_analyzer.convert_to_bytes(image)
            mime = self.screen_analyzer.get_mime_type()
            return img_bytes, mime
        else:
            # Fallback: WebP 100%
            buf = io.BytesIO()
            image.save(buf, format="WEBP", quality=100)
            buf.seek(0)
            return buf.read(), "image/webp"

    def _handle_retry(self, error: Exception, attempt: int, result: dict) -> bool:
        """Handle retry logic. Returns True if should continue retrying."""
        error_str = str(error)
        logger.warning(f"[AI Engine] Lỗi lần {attempt + 1}/{MAX_RETRIES}: {error_str[:150]}")

        # 1. 401 Unauthorized / Invalid API Key -> Thử rotate key khác nếu có, nếu không thì dừng ngay
        if "401" in error_str or "API_KEY_INVALID" in error_str or "Unauthorized" in error_str:
            current_key = self.api_key
            new_key = self.key_mgr.rotate_to_next(current_key, "Invalid API key (401)", self.provider)
            if new_key:
                self._reinit_with_key(new_key)
                return True
            prov_name = PROVIDER_DISPLAY.get(self.provider, {}).get("name", self.provider)
            result["text"] = f"⚠️ API Key cho {prov_name} không hợp lệ hoặc đã hết hạn (HTTP 401). Vui lòng cấu hình lại trong Cài đặt."
            result["error"] = True
            return False

        # 2. 429 Rate Limit / Quota Exceeded -> Rotate key hoặc exponential backoff
        if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str.upper() or "rate" in error_str.lower() or "quota" in error_str.lower():
            current_key = self.api_key
            new_key = self.key_mgr.rotate_to_next(current_key, "Quota exceeded (429)", self.provider)
            if new_key and new_key != current_key:
                self._reinit_with_key(new_key)
                return True

            # Nếu chỉ có 1 key hoặc không có key thay thế: chờ ngắn rồi retry nếu còn lượt attempt
            if attempt < MAX_RETRIES - 1:
                wait_secs = (attempt + 1) * 3
                logger.info(f"[AI Engine] Đang đợi {wait_secs}s để API Key hồi quota/rate-limit trước khi thử lại...")
                time.sleep(wait_secs)
                return True

            prov_name = PROVIDER_DISPLAY.get(self.provider, {}).get("name", self.provider)
            result["text"] = (
                f"⚠️ API Key cho **{prov_name}** đã đạt giới hạn Quota hoặc Rate Limit (HTTP 429 Resource Exhausted).\n\n"
                f"💡 **Cách khắc phục**:\n"
                f"1. **Chờ 10-30 giây**: Tài khoản miễn phí thường bị giới hạn lượt gọi/phút (RPM). Sau 30s bạn có thể chat tiếp bình thường.\n"
                f"2. **Thêm API Key dự phòng**: Vào **Cài đặt ⚙️ ➔ Tab 🔑 API Keys** để thêm thêm key. Hệ thống sẽ tự động luân chuyển khi một key đầy quota.\n"
                f"3. **Chuyển mô hình**: Thử chuyển sang các mô hình nhẹ hơn như `gemini-2.0-flash-lite` hoặc các Provider khác (OpenAI, DeepSeek, Qwen...)."
            )
            result["error"] = True
            return False

        # 3. 404 Model Not Found -> Không lặp vô ích
        if "404" in error_str or "NOT_FOUND" in error_str:
            result["text"] = f"⚠️ Mô hình '{self.model_name}' không tìm thấy hoặc không hỗ trợ trên tài khoản của bạn (HTTP 404).\n\n💡 Hãy bấm '✨ Quét Models khả dụng theo Key' trong Cài đặt để xem danh sách model phù hợp với key hiện tại."
            result["error"] = True
            return False

        # 4. 503 Unavailable / Model đang quá tải -> Retry giới hạn
        if "503" in error_str or "UNAVAILABLE" in error_str.upper() or "high demand" in error_str.lower():
            if attempt < MAX_RETRIES - 1:
                time.sleep(min(2 ** attempt, 4))
                return True
            result["text"] = f"⚠️ Mô hình đang quá tải tạm thời (HTTP 503). Vui lòng thử lại sau vài giây."
            result["error"] = True
            return False

        # 5. Timeout / Connection error
        if "timeout" in error_str.lower() or "connectionerror" in error_str.lower() or "connecttimeout" in error_str.lower():
            if attempt < MAX_RETRIES - 1:
                time.sleep(min(2 ** attempt, 4))
                return True
            result["text"] = f"⚠️ Không thể kết nối đến máy chủ AI. Kiểm tra mạng internet của bạn."
            result["error"] = True
            return False

        # 6. Lỗi chung khác
        if attempt < MAX_RETRIES - 1:
            time.sleep(min(2 ** attempt, 4))
            return True

        result["text"] = f"⚠️ Lỗi kết nối AI: {error_str[:200]}"
        result["error"] = True
        return False

    def _save_to_history(self, message: str, result: dict, image=None):
        """Lưu vào conversation history."""
        self.conversation_history.append({
            "role": "user", "content": message,
            "timestamp": datetime.now().isoformat(),
            "has_image": image is not None
        })

        assistant_content = (result.get("text") or "").strip()
        if not assistant_content and result.get("tool_calls"):
            calls_desc = ", ".join([f"{tc['name']}({tc.get('args', {})})" for tc in result["tool_calls"]])
            assistant_content = f"Đã thực hiện: {calls_desc}"
        elif not assistant_content:
            assistant_content = "Đã hoàn thành yêu cầu."

        self.conversation_history.append({
            "role": "assistant", "content": assistant_content,
            "timestamp": datetime.now().isoformat(),
            "tool_calls": result.get("tool_calls", [])
        })

    # ============================================================
    # Public API
    # ============================================================

    def quick_test(self, model_id: str) -> bool:
        """Quick test: tạm chuyển model, gửi 1 tin nhắn test, trả về True nếu OK."""
        old_model = self.model_name
        old_provider = self.provider
        old_client = self.client
        old_api_key = self.api_key

        try:
            # Tạm chuyển sang model cần test
            self.set_model(model_id)
            if not self.client:
                return False

            # Gửi tin nhắn test đơn giản (không lưu history)
            if self.provider == Provider.GEMINI:
                target_model = resolve_gemini_api_model(self.model_name)
                try:
                    response = self.client.models.generate_content(
                        model=target_model,
                        contents="Respond only with the word OK"
                    )
                except Exception as api_err:
                    if "404" in str(api_err) or "NOT_FOUND" in str(api_err).upper():
                        logger.warning(f"[AI Engine] Quick test 404 cho '{target_model}', fallback sang 'gemini-3.5-flash-lite'")
                        try:
                            response = self.client.models.generate_content(
                                model="gemini-3.5-flash-lite",
                                contents="Respond only with the word OK"
                            )
                        except Exception:
                            response = self.client.models.generate_content(
                                model="gemini-flash-lite-latest",
                                contents="Respond only with the word OK"
                            )
                    else:
                        raise api_err
                return bool(response and response.text)

            elif self.provider == Provider.OPENAI or self.provider in (
                Provider.DEEPSEEK, Provider.QWEN, Provider.XAI,
                Provider.KIMI, Provider.GLM, Provider.MINIMAX,
                Provider.DOUBAO, Provider.MISTRAL
            ):
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": "Respond only with OK"}],
                    max_tokens=10,
                )
                return bool(response and response.choices)

            elif self.provider == Provider.ANTHROPIC:
                response = self.client.messages.create(
                    model=self.model_name,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Respond only with OK"}]
                )
                return bool(response and response.content)

            return False

        except Exception as e:
            logger.warning(f"[AI Engine] Quick test failed for {model_id}: {e}")
            raise
        finally:
            # Khôi phục lại model cũ
            self.set_model(old_model)
            self.client = old_client

    def fetch_live_models_from_api(self, provider: str = "") -> List[Dict[str, Any]]:
        """
        Truy vấn trực tiếp danh sách mô hình khả dụng từ API tương ứng với key đang kích hoạt.
        Trả về danh sách dict các model: [{"id": "...", "name": "...", "description": "...", "provider": "..."}, ...]
        """
        import requests
        prov = provider or self.provider
        active_key = self.key_mgr.get_active_key(prov)
        if not active_key:
            return []

        models_list = []

        if prov == Provider.GEMINI:
            try:
                from google import genai
                client = genai.Client(api_key=active_key)
                for m in client.models.list():
                    m_id = m.name.replace("models/", "") if hasattr(m, "name") else str(m)
                    display_name = getattr(m, "display_name", "") or m_id
                    desc = getattr(m, "description", "") or ""
                    supported_actions = getattr(m, "supported_actions", []) or getattr(m, "supported_generation_methods", [])
                    # Chỉ lấy các model hỗ trợ generateContent hoặc bidi
                    if not supported_actions or any(a in supported_actions for a in ["generateContent", "bidiGenerateContent"]):
                        models_list.append({
                            "id": m_id,
                            "name": display_name,
                            "provider": Provider.GEMINI,
                            "description": desc,
                            "actions": supported_actions
                        })
            except Exception as e:
                logger.error(f"[AI Engine] Lỗi fetch models Gemini: {e}")
                raise

        elif prov in (Provider.OPENAI, Provider.DEEPSEEK, Provider.QWEN, Provider.XAI, Provider.MISTRAL, Provider.KIMI, Provider.GLM, Provider.MINIMAX, Provider.DOUBAO):
            api_urls = {
                Provider.OPENAI: "https://api.openai.com/v1/models",
                Provider.DEEPSEEK: "https://api.deepseek.com/models",
                Provider.QWEN: "https://dashscope-intl.aliyuncs.com/compatible-mode/v1/models",
                Provider.XAI: "https://api.x.ai/v1/models",
                Provider.MISTRAL: "https://api.mistral.ai/v1/models",
                Provider.KIMI: "https://api.moonshot.cn/v1/models",
                Provider.GLM: "https://open.bigmodel.cn/api/paas/v4/models",
                Provider.MINIMAX: "https://api.minimax.chat/v1/models",
            }
            url = api_urls.get(prov, "https://api.openai.com/v1/models")
            headers = {"Authorization": f"Bearer {active_key}"}
            try:
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    for item in data.get("data", []):
                        m_id = item.get("id", "")
                        models_list.append({
                            "id": m_id,
                            "name": m_id,
                            "provider": prov,
                            "description": f"Model khả dụng trên tài khoản {prov}",
                            "actions": ["chat"]
                        })
            except Exception as e:
                logger.error(f"[AI Engine] Lỗi fetch models {prov}: {e}")
                raise

        return models_list

    def chat_simple(self, message: str) -> str:
        """Chat đơn giản không tool calling."""
        result = self.chat(message, enable_tools=False)
        return result.get("text", "")

    def analyze_screenshot(self, image: Image.Image, prompt: str = "") -> Dict[str, Any]:
        """Phân tích screenshot bằng Vision AI."""
        default_prompt = (
            "Hãy phân tích screenshot này. Mô tả:\n"
            "1. Ứng dụng/trang web đang mở là gì?\n"
            "2. Các element UI chính và vị trí ước lượng (x, y)\n"
            "3. Trạng thái hiện tại\n"
            "4. Đề xuất hành động tiếp theo"
        )
        full_prompt = f"{prompt}\n\n{default_prompt}" if prompt else default_prompt
        return self.chat(full_prompt, image=image, enable_tools=False)

    def generate_workflow(self, description: str) -> Dict[str, Any]:
        """AI tạo workflow từ mô tả tiếng Việt."""
        prompt = (
            f"Hãy tạo kịch bản tự động hoá cho yêu cầu sau:\n\n"
            f"'{description}'\n\n"
            f"Trả lời theo JSON: "
            f'{{"name": "Tên", "steps": [{{"action": "loại hành động", "params": {{}}, "description": "mô tả"}}]}}\n'
            f"Actions: click_at, type_text, press_key, open_application, wait_seconds, scroll"
        )
        return self.chat(prompt, enable_tools=True)


    def get_history(self) -> List[Dict]:
        return self.conversation_history.copy()

    def get_status(self) -> Dict:
        """Lấy trạng thái AI engine."""
        prov_info = PROVIDER_DISPLAY.get(self.provider, {})
        model_display = self._model_info.name if self._model_info else self.model_name
        tier_display = ""
        if self._model_info:
            from core.model_registry import TIER_DISPLAY
            td = TIER_DISPLAY.get(self._model_info.tier, {})
            tier_display = f"{td.get('icon', '')} {td.get('name', '')}"

        return {
            "connected": self.client is not None,
            "provider": self.provider,
            "provider_name": prov_info.get("name", self.provider),
            "provider_icon": prov_info.get("icon", "⚡"),
            "model": self.model_name,
            "model_name": model_display,
            "model_tier": tier_display,
            "api_key": f"...{self.api_key[-8:]}" if self.api_key else "Chưa có",
            "total_keys": self.key_mgr.key_count,
            "available_keys": self.key_mgr.available_count,
            "history_count": len(self.conversation_history),
            "supports_vision": self._model_info.supports_vision if self._model_info else False,
            "supports_tools": self._model_info.supports_tools if self._model_info else False,
        }
