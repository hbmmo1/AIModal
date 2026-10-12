"""
Model Registry — Sổ đăng ký toàn bộ AI providers & models (Cập nhật 2026).
Hỗ trợ: Gemini, OpenAI (ChatGPT), Anthropic (Claude), DeepSeek, Qwen,
         Mistral, Cohere, Meta (Llama), xAI (Grok), Kimi (Moonshot),
         GLM (Zhipu), MiniMax, Doubao (ByteDance), Amazon Nova,
         NVIDIA (Nemotron), Falcon (TII).
Phân loại: Rẻ nhất, Cân bằng, Giá vừa phải, Tốt nhất.
"""

import logging
from dataclasses import dataclass
from typing import List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================
# Enums
# ============================================================

class Provider(str, Enum):
    """Nhà cung cấp AI."""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    MISTRAL = "mistral"
    COHERE = "cohere"
    META = "meta"
    XAI = "xai"
    KIMI = "kimi"
    GLM = "glm"
    MINIMAX = "minimax"
    DOUBAO = "doubao"
    AMAZON = "amazon"
    NVIDIA = "nvidia"
    FALCON = "falcon"


class ModelTier(str, Enum):
    """Phân hạng mô hình theo giá/chất lượng."""
    CHEAPEST = "cheapest"
    BALANCED = "balanced"
    MODERATE = "moderate"
    BEST = "best"


TIER_DISPLAY = {
    ModelTier.CHEAPEST: {"icon": "💚", "name": "Rẻ nhất", "desc": "Tiết kiệm tối đa, tốc độ nhanh", "color": "#22c55e"},
    ModelTier.BALANCED: {"icon": "💙", "name": "Cân bằng", "desc": "Nhanh + Rẻ + Tốt — Khuyên dùng", "color": "#3b82f6"},
    ModelTier.MODERATE: {"icon": "💜", "name": "Giá vừa phải", "desc": "Chất lượng cao, đa năng", "color": "#8b5cf6"},
    ModelTier.BEST:     {"icon": "💎", "name": "Tốt nhất", "desc": "Flagship, thông minh nhất", "color": "#f59e0b"},
}


PROVIDER_DISPLAY = {
    Provider.GEMINI:    {"icon": "✨", "name": "Google Gemini", "color": "#4285f4", "key_prefix": "AIza", "key_env": "GEMINI_API_KEY"},
    Provider.OPENAI:    {"icon": "🟢", "name": "OpenAI (ChatGPT)", "color": "#10a37f", "key_prefix": "sk-", "key_env": "OPENAI_API_KEY"},
    Provider.ANTHROPIC: {"icon": "🟠", "name": "Anthropic (Claude)", "color": "#d97706", "key_prefix": "sk-ant-", "key_env": "ANTHROPIC_API_KEY"},
    Provider.DEEPSEEK:  {"icon": "🔵", "name": "DeepSeek", "color": "#2563eb", "key_prefix": "sk-", "key_env": "DEEPSEEK_API_KEY"},
    Provider.QWEN:      {"icon": "🟣", "name": "Qwen (Alibaba)", "color": "#7c3aed", "key_prefix": "sk-", "key_env": "QWEN_API_KEY"},
    Provider.MISTRAL:   {"icon": "🔶", "name": "Mistral AI", "color": "#f97316", "key_prefix": "", "key_env": "MISTRAL_API_KEY"},
    Provider.COHERE:    {"icon": "🔷", "name": "Cohere", "color": "#0ea5e9", "key_prefix": "", "key_env": "COHERE_API_KEY"},
    Provider.META:      {"icon": "🦙", "name": "Meta (Llama)", "color": "#6366f1", "key_prefix": "", "key_env": "META_API_KEY"},
    Provider.XAI:       {"icon": "⚡", "name": "xAI (Grok)", "color": "#e11d48", "key_prefix": "xai-", "key_env": "XAI_API_KEY"},
    Provider.KIMI:      {"icon": "🌙", "name": "Kimi (Moonshot)", "color": "#8b5cf6", "key_prefix": "", "key_env": "KIMI_API_KEY"},
    Provider.GLM:       {"icon": "🧩", "name": "GLM (Zhipu AI)", "color": "#059669", "key_prefix": "", "key_env": "GLM_API_KEY"},
    Provider.MINIMAX:   {"icon": "🔮", "name": "MiniMax", "color": "#d946ef", "key_prefix": "", "key_env": "MINIMAX_API_KEY"},
    Provider.DOUBAO:    {"icon": "🌊", "name": "Doubao (ByteDance)", "color": "#0284c7", "key_prefix": "", "key_env": "DOUBAO_API_KEY"},
    Provider.AMAZON:    {"icon": "📦", "name": "Amazon Nova", "color": "#f59e0b", "key_prefix": "", "key_env": "AWS_API_KEY"},
    Provider.NVIDIA:    {"icon": "💚", "name": "NVIDIA (Nemotron)", "color": "#76b900", "key_prefix": "", "key_env": "NVIDIA_API_KEY"},
    Provider.FALCON:    {"icon": "🦅", "name": "Falcon (TII)", "color": "#dc2626", "key_prefix": "", "key_env": "FALCON_API_KEY"},
}


# ============================================================
# Model Info Dataclass
# ============================================================

@dataclass
class ModelInfo:
    """Thông tin chi tiết 1 mô hình AI."""
    id: str
    name: str
    provider: str
    tier: str
    input_price: float = 0.0
    output_price: float = 0.0
    max_context: int = 128000
    max_output: int = 8192
    supports_vision: bool = False
    supports_tools: bool = False
    supports_streaming: bool = True
    speed_rating: int = 3
    quality_rating: int = 3
    cost_rating: int = 3
    description: str = ""
    release_date: str = ""
    is_default: bool = False
    is_recommended: bool = False
    enabled: bool = True

    def get_display_name(self) -> str:
        prov = PROVIDER_DISPLAY.get(self.provider, {})
        return f"{prov.get('icon', '⚡')} {self.name}"

    def get_tier_display(self) -> dict:
        return TIER_DISPLAY.get(self.tier, {"icon": "⚡", "name": "?", "desc": "", "color": "#64748b"})

    def get_price_display(self) -> str:
        if self.input_price == 0 and self.output_price == 0:
            return "🆓 Miễn phí"
        return f"${self.input_price:.2f} / ${self.output_price:.2f} per 1M tokens"

    def get_overall_score(self) -> float:
        return (self.speed_rating + self.quality_rating + self.cost_rating) / 3.0


# ============================================================
# Full Model Registry — CẬP NHẬT 2026
# ============================================================

ALL_MODELS: List[ModelInfo] = [
    # ==================== GOOGLE GEMINI (2026) ====================
    # --- Gemini 3.7 Series ---
    ModelInfo(
        id="gemini-3.7-flash-high",
        name="Gemini 3.7 Flash High (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=5, cost_rating=5,
        description="Thế hệ mới nhất — thinking level High, siêu tốc + reasoning sâu. KHUYÊN DÙNG!",
        is_default=True, is_recommended=True,
        release_date="2026-08",
    ),
    ModelInfo(
        id="gemini-3.7-flash-medium",
        name="Gemini 3.7 Flash Medium (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Thinking level Medium — cân bằng tốc độ phản hồi và độ thông minh",
        release_date="2026-08",
    ),
    ModelInfo(
        id="gemini-3.7-flash-low",
        name="Gemini 3.7 Flash Low (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.CHEAPEST,
        input_price=0.10, output_price=0.40,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Thinking level Low — siêu nhanh, độ trễ tối thiểu",
        release_date="2026-08",
    ),

    # --- Gemini 3.6 Series ---
    ModelInfo(
        id="gemini-3.6-flash-high",
        name="Gemini 3.6 Flash High (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=5, cost_rating=5,
        description="Flash 3.6 thinking cao — phân tích dữ liệu & mã nguồn chuẩn xác",
        release_date="2026-06",
    ),
    ModelInfo(
        id="gemini-3.6-flash-medium",
        name="Gemini 3.6 Flash Medium (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Flash 3.6 cân bằng — khuyên dùng cho tác vụ tự động hoá",
        is_recommended=True,
        release_date="2026-06",
    ),
    ModelInfo(
        id="gemini-3.6-flash-low",
        name="Gemini 3.6 Flash Low (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.CHEAPEST,
        input_price=0.10, output_price=0.40,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Flash 3.6 độ trễ thấp — phản hồi chớp nhoáng",
        release_date="2026-06",
    ),

    # --- Gemini 3.5 Series ---
    ModelInfo(
        id="gemini-3.5-flash-high",
        name="Gemini 3.5 Flash High (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Flash 3.5 thinking cao — đa năng",
        release_date="2026-03",
    ),
    ModelInfo(
        id="gemini-3.5-flash-medium",
        name="Gemini 3.5 Flash Medium (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Flash 3.5 cân bằng — ổn định",
        release_date="2026-03",
    ),
    ModelInfo(
        id="gemini-3.5-flash-low",
        name="Gemini 3.5 Flash Low (Fast)",
        provider=Provider.GEMINI,
        tier=ModelTier.CHEAPEST,
        input_price=0.10, output_price=0.40,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Flash 3.5 tiết kiệm — tốc độ cao",
        release_date="2026-03",
    ),
    ModelInfo(
        id="gemini-3.5-flash-lite",
        name="Gemini 3.5 Flash Lite",
        provider=Provider.GEMINI,
        tier=ModelTier.CHEAPEST,
        input_price=0.075, output_price=0.30,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Official Google API — siêu nhẹ, cực nhanh, phản hồi tức thì",
        is_recommended=True,
        release_date="2026-03",
    ),

    # --- Gemini 3.1 Series ---
    ModelInfo(
        id="gemini-3.1-pro-high",
        name="Gemini 3.1 Pro High",
        provider=Provider.GEMINI,
        tier=ModelTier.BEST,
        input_price=1.25, output_price=5.00,
        max_context=2097152, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=3, quality_rating=5, cost_rating=2,
        description="Pro 3.1 deep reasoning — xử lý bài toán học thuật và lập trình phức tạp",
        release_date="2026-01",
    ),
    ModelInfo(
        id="gemini-3.1-pro-medium",
        name="Gemini 3.1 Pro Medium",
        provider=Provider.GEMINI,
        tier=ModelTier.MODERATE,
        input_price=1.25, output_price=5.00,
        max_context=2097152, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Pro 3.1 suy luận logic & coding chuyên sâu",
        release_date="2026-01",
    ),
    ModelInfo(
        id="gemini-3.1-pro-low",
        name="Gemini 3.1 Pro Low",
        provider=Provider.GEMINI,
        tier=ModelTier.MODERATE,
        input_price=1.00, output_price=4.00,
        max_context=2097152, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=3,
        description="Pro 3.1 tốc độ ổn định — ngữ cảnh lớn 2M tokens",
        release_date="2026-01",
    ),
    ModelInfo(
        id="gemini-3.1-flash-lite",
        name="Gemini 3.1 Flash Lite",
        provider=Provider.GEMINI,
        tier=ModelTier.CHEAPEST,
        input_price=0.075, output_price=0.30,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Official Google API — tốc độ xử lý cao, chi phí cực thấp",
        is_recommended=True,
        release_date="2026-01",
    ),

    # --- Gemini Latest Aliases ---
    ModelInfo(
        id="gemini-flash-latest",
        name="Gemini Flash (Latest)",
        provider=Provider.GEMINI,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=5, cost_rating=5,
        description="Official Google API — tự động trỏ tới bản Flash mới nhất",
        release_date="2026-08",
    ),
    ModelInfo(
        id="gemini-flash-lite-latest",
        name="Gemini Flash Lite (Latest)",
        provider=Provider.GEMINI,
        tier=ModelTier.CHEAPEST,
        input_price=0.075, output_price=0.30,
        max_context=1048576, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Official Google API — tự động trỏ tới bản Flash Lite mới nhất",
        release_date="2026-08",
    ),
    ModelInfo(
        id="gemini-pro-latest",
        name="Gemini Pro (Latest)",
        provider=Provider.GEMINI,
        tier=ModelTier.BEST,
        input_price=1.25, output_price=5.00,
        max_context=2097152, max_output=65536,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=2,
        description="Official Google API — tự động trỏ tới bản Pro mới nhất",
        release_date="2026-08",
    ),

    # ==================== OPENAI / ChatGPT (2026) ====================
    ModelInfo(
        id="gpt-4.1",
        name="GPT-4.1",
        provider=Provider.OPENAI,
        tier=ModelTier.MODERATE,
        input_price=2.00, output_price=8.00,
        max_context=1048576, max_output=32768,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Flagship OpenAI — coding & reasoning cực mạnh",
        is_recommended=True,
        release_date="2025-04",
    ),
    ModelInfo(
        id="gpt-4.1-mini",
        name="GPT-4.1 Mini",
        provider=Provider.OPENAI,
        tier=ModelTier.BALANCED,
        input_price=0.40, output_price=1.60,
        max_context=1048576, max_output=32768,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=4,
        description="Nhẹ, nhanh, giá hợp lý — khuyên dùng",
        is_recommended=True,
        release_date="2025-04",
    ),
    ModelInfo(
        id="gpt-4.1-nano",
        name="GPT-4.1 Nano",
        provider=Provider.OPENAI,
        tier=ModelTier.CHEAPEST,
        input_price=0.10, output_price=0.40,
        max_context=1048576, max_output=32768,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Rẻ nhất OpenAI — tác vụ nhẹ",
        release_date="2025-04",
    ),
    ModelInfo(
        id="gpt-4o",
        name="GPT-4o",
        provider=Provider.OPENAI,
        tier=ModelTier.MODERATE,
        input_price=2.50, output_price=10.00,
        max_context=128000, max_output=16384,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Đa năng, vision mạnh",
        release_date="2024-05",
    ),
    ModelInfo(
        id="gpt-4o-mini",
        name="GPT-4o Mini",
        provider=Provider.OPENAI,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=128000, max_output=16384,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Rẻ mà mạnh — cân bằng tốt",
        release_date="2024-07",
    ),
    ModelInfo(
        id="o3-mini",
        name="o3-mini (Reasoning)",
        provider=Provider.OPENAI,
        tier=ModelTier.BEST,
        input_price=1.10, output_price=4.40,
        max_context=200000, max_output=100000,
        supports_vision=False, supports_tools=True,
        speed_rating=3, quality_rating=5, cost_rating=3,
        description="Reasoning model — suy luận logic cực mạnh",
        release_date="2025-01",
    ),
    ModelInfo(
        id="gpt-oss-120b",
        name="GPT-OSS 120B (Medium)",
        provider=Provider.OPENAI,
        tier=ModelTier.BALANCED,
        input_price=0.20, output_price=0.80,
        max_context=131072, max_output=16384,
        supports_vision=False, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=5,
        description="Mô hình mã nguồn mở 120B tham số — linh hoạt, mạnh mẽ",
        release_date="2026-05",
    ),
    ModelInfo(
        id="o4-mini",
        name="o4-mini (Reasoning)",
        provider=Provider.OPENAI,
        tier=ModelTier.BEST,
        input_price=1.10, output_price=4.40,
        max_context=200000, max_output=100000,
        supports_vision=True, supports_tools=True,
        speed_rating=3, quality_rating=5, cost_rating=3,
        description="Reasoning mới nhất — multimodal reasoning",
        release_date="2025-04",
    ),

    # ==================== ANTHROPIC / Claude (2026) ====================
    ModelInfo(
        id="claude-sonnet-4-6",
        name="Claude Sonnet 4.6 (Thinking)",
        provider=Provider.ANTHROPIC,
        tier=ModelTier.MODERATE,
        input_price=3.00, output_price=15.00,
        max_context=200000, max_output=64000,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Thinking model thế hệ mới — coding chuyên sâu và logic siêu việt. KHUYÊN DÙNG!",
        is_recommended=True,
        release_date="2026-06",
    ),
    ModelInfo(
        id="claude-opus-4-6",
        name="Claude Opus 4.6 (Thinking)",
        provider=Provider.ANTHROPIC,
        tier=ModelTier.BEST,
        input_price=15.00, output_price=75.00,
        max_context=200000, max_output=64000,
        supports_vision=True, supports_tools=True,
        speed_rating=3, quality_rating=5, cost_rating=1,
        description="Flagship Thinking — giải quyết bài toán phức tạp nhất",
        release_date="2026-06",
    ),
    ModelInfo(
        id="claude-sonnet-4-20250514",
        name="Claude Sonnet 4",
        provider=Provider.ANTHROPIC,
        tier=ModelTier.MODERATE,
        input_price=3.00, output_price=15.00,
        max_context=200000, max_output=64000,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Mạnh nhất coding + reasoning",
        release_date="2025-05",
    ),
    ModelInfo(
        id="claude-haiku-3-5-20241022",
        name="Claude 3.5 Haiku",
        provider=Provider.ANTHROPIC,
        tier=ModelTier.BALANCED,
        input_price=0.80, output_price=4.00,
        max_context=200000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=4,
        description="Nhanh, rẻ — chất lượng vẫn tốt",
        release_date="2024-10",
    ),
    ModelInfo(
        id="claude-opus-4-20250514",
        name="Claude Opus 4",
        provider=Provider.ANTHROPIC,
        tier=ModelTier.BEST,
        input_price=15.00, output_price=75.00,
        max_context=200000, max_output=32000,
        supports_vision=True, supports_tools=True,
        speed_rating=2, quality_rating=5, cost_rating=1,
        description="Flagship — deep reasoning, phức tạp nhất",
        release_date="2025-05",
    ),
    ModelInfo(
        id="claude-3-5-sonnet-20241022",
        name="Claude 3.5 Sonnet v2",
        provider=Provider.ANTHROPIC,
        tier=ModelTier.MODERATE,
        input_price=3.00, output_price=15.00,
        max_context=200000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Đời trước Sonnet 4 — vẫn rất mạnh",
        release_date="2024-10",
    ),
    ModelInfo(
        id="claude-3-haiku-20240307",
        name="Claude 3 Haiku",
        provider=Provider.ANTHROPIC,
        tier=ModelTier.CHEAPEST,
        input_price=0.25, output_price=1.25,
        max_context=200000, max_output=4096,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Rẻ nhất Claude — siêu nhanh",
        release_date="2024-03",
    ),

    # ==================== xAI / Grok ====================
    ModelInfo(
        id="grok-3",
        name="Grok 3",
        provider=Provider.XAI,
        tier=ModelTier.BEST,
        input_price=3.00, output_price=15.00,
        max_context=131072, max_output=16384,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=2,
        description="Flagship xAI — reasoning & math cực mạnh",
        release_date="2025-02",
    ),
    ModelInfo(
        id="grok-3-mini",
        name="Grok 3 Mini",
        provider=Provider.XAI,
        tier=ModelTier.BALANCED,
        input_price=0.30, output_price=0.50,
        max_context=131072, max_output=16384,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Rẻ, nhanh — thinking model nhỏ gọn",
        is_recommended=True,
        release_date="2025-02",
    ),
    ModelInfo(
        id="grok-3-fast",
        name="Grok 3 Fast",
        provider=Provider.XAI,
        tier=ModelTier.BALANCED,
        input_price=5.00, output_price=25.00,
        max_context=131072, max_output=16384,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=5, cost_rating=2,
        description="Grok 3 tốc độ cao — latency thấp",
        release_date="2025-04",
    ),
    ModelInfo(
        id="grok-2",
        name="Grok 2",
        provider=Provider.XAI,
        tier=ModelTier.MODERATE,
        input_price=2.00, output_price=10.00,
        max_context=131072, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=3,
        description="Thế hệ trước — vẫn mạnh",
        release_date="2024-08",
    ),

    # ==================== DEEPSEEK ====================
    ModelInfo(
        id="deepseek-chat",
        name="DeepSeek V3",
        provider=Provider.DEEPSEEK,
        tier=ModelTier.CHEAPEST,
        input_price=0.27, output_price=1.10,
        max_context=65536, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=5,
        description="Siêu rẻ, coding mạnh — giá kinh ngạc",
        is_recommended=True,
        release_date="2025-03",
    ),
    ModelInfo(
        id="deepseek-reasoner",
        name="DeepSeek R1 (Reasoning)",
        provider=Provider.DEEPSEEK,
        tier=ModelTier.BALANCED,
        input_price=0.55, output_price=2.19,
        max_context=65536, max_output=8192,
        supports_vision=False, supports_tools=False,
        speed_rating=3, quality_rating=5, cost_rating=4,
        description="Reasoning cực mạnh, giá rẻ kinh ngạc",
        release_date="2025-01",
    ),
    ModelInfo(
        id="deepseek-coder",
        name="DeepSeek Coder V2",
        provider=Provider.DEEPSEEK,
        tier=ModelTier.CHEAPEST,
        input_price=0.14, output_price=0.28,
        max_context=128000, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Chuyên coding — siêu rẻ",
        release_date="2024-06",
    ),

    # ==================== QWEN (Alibaba) ====================
    ModelInfo(
        id="qwen-plus",
        name="Qwen Plus",
        provider=Provider.QWEN,
        tier=ModelTier.BALANCED,
        input_price=0.80, output_price=2.00,
        max_context=131072, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=4,
        description="Đa năng, tiếng Việt tốt",
        release_date="2025-01",
    ),
    ModelInfo(
        id="qwen-turbo",
        name="Qwen Turbo",
        provider=Provider.QWEN,
        tier=ModelTier.CHEAPEST,
        input_price=0.30, output_price=0.60,
        max_context=131072, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Nhanh, rẻ — tác vụ đơn giản",
        release_date="2024-09",
    ),
    ModelInfo(
        id="qwen-max",
        name="Qwen Max",
        provider=Provider.QWEN,
        tier=ModelTier.BEST,
        input_price=2.40, output_price=9.60,
        max_context=131072, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=3, quality_rating=5, cost_rating=3,
        description="Flagship Qwen — thông minh nhất",
        release_date="2025-01",
    ),
    ModelInfo(
        id="qwen-long",
        name="Qwen Long",
        provider=Provider.QWEN,
        tier=ModelTier.BALANCED,
        input_price=0.50, output_price=2.00,
        max_context=1000000, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=4,
        description="Context dài 1M tokens — phân tích tài liệu lớn",
        release_date="2024-11",
    ),
    ModelInfo(
        id="qwen-vl-max",
        name="Qwen VL Max",
        provider=Provider.QWEN,
        tier=ModelTier.MODERATE,
        input_price=3.00, output_price=9.00,
        max_context=131072, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=3, quality_rating=5, cost_rating=3,
        description="Vision chuyên sâu — OCR & image understanding",
        release_date="2025-01",
    ),

    # ==================== MISTRAL AI ====================
    ModelInfo(
        id="mistral-large-latest",
        name="Mistral Large",
        provider=Provider.MISTRAL,
        tier=ModelTier.MODERATE,
        input_price=2.00, output_price=6.00,
        max_context=128000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Flagship Mistral — coding + multilingual xuất sắc",
        is_recommended=True,
        release_date="2025-01",
    ),
    ModelInfo(
        id="mistral-small-latest",
        name="Mistral Small",
        provider=Provider.MISTRAL,
        tier=ModelTier.BALANCED,
        input_price=0.10, output_price=0.30,
        max_context=128000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Rẻ nhất, nhanh nhất Mistral — rất tốt",
        release_date="2025-01",
    ),
    ModelInfo(
        id="codestral-latest",
        name="Codestral (Code)",
        provider=Provider.MISTRAL,
        tier=ModelTier.MODERATE,
        input_price=0.30, output_price=0.90,
        max_context=256000, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=5, cost_rating=4,
        description="Chuyên coding — 80+ ngôn ngữ lập trình",
        release_date="2025-01",
    ),
    ModelInfo(
        id="mistral-medium-latest",
        name="Mistral Medium",
        provider=Provider.MISTRAL,
        tier=ModelTier.MODERATE,
        input_price=0.40, output_price=2.00,
        max_context=128000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=4,
        description="Cân bằng giữa Large và Small",
        release_date="2024-12",
    ),

    # ==================== COHERE ====================
    ModelInfo(
        id="command-r-plus",
        name="Command R+",
        provider=Provider.COHERE,
        tier=ModelTier.MODERATE,
        input_price=2.50, output_price=10.00,
        max_context=128000, max_output=4096,
        supports_vision=False, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=3,
        description="RAG mạnh, enterprise-grade",
        release_date="2024-04",
    ),
    ModelInfo(
        id="command-r",
        name="Command R",
        provider=Provider.COHERE,
        tier=ModelTier.BALANCED,
        input_price=0.15, output_price=0.60,
        max_context=128000, max_output=4096,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Rẻ, RAG tốt",
        release_date="2024-04",
    ),

    # ==================== META / Llama ====================
    ModelInfo(
        id="meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
        name="Llama 4 Maverick 17B",
        provider=Provider.META,
        tier=ModelTier.BALANCED,
        input_price=0.27, output_price=0.85,
        max_context=1048576, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=5,
        description="Llama 4 mới nhất — open-source, vision, tools",
        is_recommended=True,
        release_date="2025-04",
    ),
    ModelInfo(
        id="meta-llama/Llama-4-Scout-17B-16E-Instruct",
        name="Llama 4 Scout 17B",
        provider=Provider.META,
        tier=ModelTier.BALANCED,
        input_price=0.18, output_price=0.35,
        max_context=512000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Llama 4 nhỏ — nhanh, rẻ",
        release_date="2025-04",
    ),
    ModelInfo(
        id="meta-llama/Llama-3.3-70B-Instruct-Turbo",
        name="Llama 3.3 70B",
        provider=Provider.META,
        tier=ModelTier.BALANCED,
        input_price=0.60, output_price=0.60,
        max_context=131072, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=4,
        description="Open-source mạnh, giá tốt",
        release_date="2024-12",
    ),
    ModelInfo(
        id="meta-llama/Llama-3.1-405B-Instruct-Turbo",
        name="Llama 3.1 405B",
        provider=Provider.META,
        tier=ModelTier.BEST,
        input_price=3.50, output_price=3.50,
        max_context=131072, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=2, quality_rating=5, cost_rating=2,
        description="Lớn nhất open-source — 405B params",
        release_date="2024-07",
    ),
    ModelInfo(
        id="meta-llama/Llama-3.1-8B-Instruct-Turbo",
        name="Llama 3.1 8B",
        provider=Provider.META,
        tier=ModelTier.CHEAPEST,
        input_price=0.05, output_price=0.08,
        max_context=131072, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Siêu rẻ, siêu nhanh — tác vụ nhẹ",
        release_date="2024-07",
    ),

    # ==================== KIMI (Moonshot AI) ====================
    ModelInfo(
        id="kimi-k2",
        name="Kimi K2",
        provider=Provider.KIMI,
        tier=ModelTier.BEST,
        input_price=2.00, output_price=8.00,
        max_context=131072, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Flagship Kimi — MoE architecture cực mạnh",
        is_recommended=True,
        release_date="2025-06",
    ),
    ModelInfo(
        id="moonshot-v1-128k",
        name="Moonshot V1 128K",
        provider=Provider.KIMI,
        tier=ModelTier.MODERATE,
        input_price=0.80, output_price=2.40,
        max_context=128000, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=4,
        description="Context dài 128K — phân tích tài liệu",
        release_date="2024-03",
    ),
    ModelInfo(
        id="moonshot-v1-32k",
        name="Moonshot V1 32K",
        provider=Provider.KIMI,
        tier=ModelTier.BALANCED,
        input_price=0.34, output_price=1.00,
        max_context=32000, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Cân bằng — context vừa phải",
        release_date="2024-03",
    ),
    ModelInfo(
        id="moonshot-v1-8k",
        name="Moonshot V1 8K",
        provider=Provider.KIMI,
        tier=ModelTier.CHEAPEST,
        input_price=0.17, output_price=0.50,
        max_context=8000, max_output=4096,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Rẻ nhất Kimi — tác vụ đơn giản",
        release_date="2024-03",
    ),

    # ==================== GLM (Zhipu AI) ====================
    ModelInfo(
        id="glm-4-plus",
        name="GLM-4 Plus",
        provider=Provider.GLM,
        tier=ModelTier.BEST,
        input_price=1.50, output_price=5.00,
        max_context=128000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Flagship GLM — Chinese & English xuất sắc",
        is_recommended=True,
        release_date="2025-01",
    ),
    ModelInfo(
        id="glm-4-flash",
        name="GLM-4 Flash",
        provider=Provider.GLM,
        tier=ModelTier.CHEAPEST,
        input_price=0.00, output_price=0.00,
        max_context=128000, max_output=4096,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="MIỄN PHÍ — nhanh, cơ bản",
        release_date="2024-08",
    ),
    ModelInfo(
        id="glm-4-long",
        name="GLM-4 Long",
        provider=Provider.GLM,
        tier=ModelTier.BALANCED,
        input_price=0.14, output_price=0.14,
        max_context=1000000, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=5,
        description="Context siêu dài 1M — phân tích tài liệu lớn",
        release_date="2024-08",
    ),
    ModelInfo(
        id="glm-4-air",
        name="GLM-4 Air",
        provider=Provider.GLM,
        tier=ModelTier.BALANCED,
        input_price=0.07, output_price=0.07,
        max_context=128000, max_output=4096,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Cân bằng — rẻ, nhanh",
        release_date="2024-06",
    ),
    ModelInfo(
        id="glm-4-airx",
        name="GLM-4 AirX",
        provider=Provider.GLM,
        tier=ModelTier.BALANCED,
        input_price=0.14, output_price=0.14,
        max_context=8192, max_output=4096,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Tốc độ cao — inference nhanh nhất",
        release_date="2024-06",
    ),

    # ==================== MINIMAX ====================
    ModelInfo(
        id="abab7-chat",
        name="MiniMax abab7",
        provider=Provider.MINIMAX,
        tier=ModelTier.MODERATE,
        input_price=1.00, output_price=3.00,
        max_context=245760, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=3,
        description="Flagship MiniMax — creative writing & reasoning",
        is_recommended=True,
        release_date="2025-01",
    ),
    ModelInfo(
        id="abab6.5s-chat",
        name="MiniMax abab6.5s",
        provider=Provider.MINIMAX,
        tier=ModelTier.BALANCED,
        input_price=0.17, output_price=0.17,
        max_context=245760, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Nhanh, rẻ — context dài 245K",
        release_date="2024-07",
    ),
    ModelInfo(
        id="abab6.5t-chat",
        name="MiniMax abab6.5t",
        provider=Provider.MINIMAX,
        tier=ModelTier.CHEAPEST,
        input_price=0.07, output_price=0.07,
        max_context=8192, max_output=4096,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Rẻ nhất MiniMax — tác vụ đơn giản",
        release_date="2024-07",
    ),

    # ==================== DOUBAO (ByteDance / Seed) ====================
    ModelInfo(
        id="doubao-1.5-pro-32k",
        name="Doubao 1.5 Pro",
        provider=Provider.DOUBAO,
        tier=ModelTier.MODERATE,
        input_price=0.56, output_price=2.24,
        max_context=32000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=5, cost_rating=4,
        description="Flagship Doubao — đa năng, reasoning mạnh",
        is_recommended=True,
        release_date="2025-03",
    ),
    ModelInfo(
        id="doubao-1.5-lite-32k",
        name="Doubao 1.5 Lite",
        provider=Provider.DOUBAO,
        tier=ModelTier.CHEAPEST,
        input_price=0.14, output_price=0.14,
        max_context=32000, max_output=8192,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Rẻ nhất Doubao — siêu tiết kiệm",
        release_date="2025-03",
    ),
    ModelInfo(
        id="doubao-pro-32k",
        name="Doubao Pro (v1)",
        provider=Provider.DOUBAO,
        tier=ModelTier.BALANCED,
        input_price=0.56, output_price=2.24,
        max_context=32000, max_output=4096,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=4,
        description="Thế hệ trước — vẫn tốt",
        release_date="2024-08",
    ),
    ModelInfo(
        id="doubao-lite-32k",
        name="Doubao Lite (v1)",
        provider=Provider.DOUBAO,
        tier=ModelTier.CHEAPEST,
        input_price=0.04, output_price=0.04,
        max_context=32000, max_output=4096,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Siêu rẻ — giá chỉ $0.04/1M",
        release_date="2024-08",
    ),

    # ==================== AMAZON NOVA ====================
    ModelInfo(
        id="amazon.nova-pro-v1:0",
        name="Amazon Nova Pro",
        provider=Provider.AMAZON,
        tier=ModelTier.MODERATE,
        input_price=0.80, output_price=3.20,
        max_context=300000, max_output=5120,
        supports_vision=True, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=4,
        description="Nova Pro — đa năng, multimodal",
        is_recommended=True,
        release_date="2024-12",
    ),
    ModelInfo(
        id="amazon.nova-lite-v1:0",
        name="Amazon Nova Lite",
        provider=Provider.AMAZON,
        tier=ModelTier.BALANCED,
        input_price=0.06, output_price=0.24,
        max_context=300000, max_output=5120,
        supports_vision=True, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Rẻ — multimodal cơ bản",
        release_date="2024-12",
    ),
    ModelInfo(
        id="amazon.nova-micro-v1:0",
        name="Amazon Nova Micro",
        provider=Provider.AMAZON,
        tier=ModelTier.CHEAPEST,
        input_price=0.035, output_price=0.14,
        max_context=128000, max_output=5120,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=2, cost_rating=5,
        description="Rẻ nhất Nova — text only, siêu nhanh",
        release_date="2024-12",
    ),

    # ==================== NVIDIA (Nemotron) ====================
    ModelInfo(
        id="nvidia/llama-3.1-nemotron-ultra-253b-v1",
        name="Nemotron Ultra 253B",
        provider=Provider.NVIDIA,
        tier=ModelTier.BEST,
        input_price=3.50, output_price=5.00,
        max_context=131072, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=3, quality_rating=5, cost_rating=2,
        description="Flagship NVIDIA — reasoning cực mạnh",
        is_recommended=True,
        release_date="2025-03",
    ),
    ModelInfo(
        id="nvidia/llama-3.1-nemotron-70b-instruct",
        name="Nemotron 70B",
        provider=Provider.NVIDIA,
        tier=ModelTier.BALANCED,
        input_price=0.88, output_price=0.88,
        max_context=131072, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=4, quality_rating=4, cost_rating=4,
        description="Cân bằng — fine-tuned Llama 3.1",
        release_date="2024-10",
    ),
    ModelInfo(
        id="nvidia/nemotron-mini-4b-instruct",
        name="Nemotron Mini 4B",
        provider=Provider.NVIDIA,
        tier=ModelTier.CHEAPEST,
        input_price=0.04, output_price=0.04,
        max_context=4096, max_output=4096,
        supports_vision=False, supports_tools=False,
        speed_rating=5, quality_rating=2, cost_rating=5,
        description="Siêu nhẹ 4B — edge deployment",
        release_date="2024-08",
    ),

    # ==================== FALCON (TII - UAE) ====================
    ModelInfo(
        id="tiiuae/falcon-3-10b-instruct",
        name="Falcon 3 10B",
        provider=Provider.FALCON,
        tier=ModelTier.BALANCED,
        input_price=0.10, output_price=0.10,
        max_context=32000, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=4, cost_rating=5,
        description="Falcon 3 mới nhất — open-source, nhanh",
        is_recommended=True,
        release_date="2024-12",
    ),
    ModelInfo(
        id="tiiuae/falcon-3-7b-instruct",
        name="Falcon 3 7B",
        provider=Provider.FALCON,
        tier=ModelTier.CHEAPEST,
        input_price=0.05, output_price=0.05,
        max_context=32000, max_output=8192,
        supports_vision=False, supports_tools=True,
        speed_rating=5, quality_rating=3, cost_rating=5,
        description="Nhỏ gọn 7B — siêu rẻ",
        release_date="2024-12",
    ),
    ModelInfo(
        id="tiiuae/falcon-3-1b-instruct",
        name="Falcon 3 1B",
        provider=Provider.FALCON,
        tier=ModelTier.CHEAPEST,
        input_price=0.02, output_price=0.02,
        max_context=8192, max_output=4096,
        supports_vision=False, supports_tools=False,
        speed_rating=5, quality_rating=2, cost_rating=5,
        description="Siêu nhẹ 1B — edge, tác vụ cơ bản",
        release_date="2024-12",
    ),
]


# ============================================================
# Registry
# ============================================================

class ModelRegistry:
    """Quản lý & tra cứu model registry."""

    def __init__(self):
        self._models = {m.id: m for m in ALL_MODELS}

    def register_dynamic_model(
        self,
        model_id: str,
        provider: str,
        name: str = "",
        description: str = "",
        supports_vision: bool = True,
        supports_tools: bool = True
    ) -> ModelInfo:
        """Đăng ký dynamic model (từ quét live API) vào registry nếu chưa có."""
        if model_id in self._models:
            return self._models[model_id]
        
        info = ModelInfo(
            id=model_id,
            name=name or model_id,
            provider=provider,
            tier=ModelTier.BALANCED,
            description=description or f"Mô hình quét trực tiếp từ API Key {provider}",
            max_context=128000,
            input_price=0.0,
            output_price=0.0,
            speed_rating=4,
            quality_rating=4,
            cost_rating=4,
            supports_vision=supports_vision,
            supports_tools=supports_tools,
            is_recommended=False,
            release_date="Live API",
        )
        self._models[model_id] = info
        logger.info(f"[ModelRegistry] Đã đăng ký dynamic model: {model_id} ({provider})")
        return info

    def get_model(self, model_id: str) -> Optional[ModelInfo]:
        return self._models.get(model_id)

    def get_all_models(self) -> List[ModelInfo]:
        return list(self._models.values())

    def get_models_by_provider(self, provider: str) -> List[ModelInfo]:
        return [m for m in self._models.values() if m.provider == provider]

    def get_models_by_tier(self, tier: str) -> List[ModelInfo]:
        return [m for m in self._models.values() if m.tier == tier]

    def get_providers(self) -> List[str]:
        return list(set(m.provider for m in self._models.values()))

    def get_default_model(self) -> Optional[ModelInfo]:
        for m in self._models.values():
            if m.is_default:
                return m
        return list(self._models.values())[0] if self._models else None

    def get_recommended_models(self) -> List[ModelInfo]:
        return [m for m in self._models.values() if m.is_recommended]

    def get_cheapest_model(self, provider: str = None) -> Optional[ModelInfo]:
        models = self.get_models_by_provider(provider) if provider else list(self._models.values())
        return min(models, key=lambda m: m.input_price) if models else None

    def get_best_model(self, provider: str = None) -> Optional[ModelInfo]:
        models = self.get_models_by_provider(provider) if provider else list(self._models.values())
        return max(models, key=lambda m: m.quality_rating) if models else None

    def get_balanced_model(self, provider: str = None) -> Optional[ModelInfo]:
        models = self.get_models_by_provider(provider) if provider else list(self._models.values())
        return max(models, key=lambda m: m.get_overall_score()) if models else None

    def get_provider_info(self, provider: str) -> dict:
        return PROVIDER_DISPLAY.get(provider, {"icon": "⚡", "name": provider, "color": "#64748b", "key_prefix": "", "key_env": ""})

    def detect_provider_from_key(self, api_key: str) -> Optional[str]:
        key = api_key.strip()
        if key.startswith("AIza"):
            return Provider.GEMINI
        elif key.startswith("sk-ant-"):
            return Provider.ANTHROPIC
        elif key.startswith("xai-"):
            return Provider.XAI
        elif key.startswith("sk-"):
            return None
        return None

    def detect_provider_from_model_id(self, model_id: str) -> Optional[str]:
        """Tự động phát hiện provider từ tên/id của model."""
        mid = model_id.lower()
        if "gemini" in mid:
            return Provider.GEMINI
        elif any(k in mid for k in ["gpt", "o1", "o3", "o4", "text-embedding", "dall-e", "davinci"]):
            return Provider.OPENAI
        elif "claude" in mid:
            return Provider.ANTHROPIC
        elif "deepseek" in mid:
            return Provider.DEEPSEEK
        elif any(k in mid for k in ["qwen", "qwq"]):
            return Provider.QWEN
        elif any(k in mid for k in ["grok", "xai"]):
            return Provider.XAI
        elif any(k in mid for k in ["mistral", "mixtral", "codestral"]):
            return Provider.MISTRAL
        elif any(k in mid for k in ["kimi", "moonshot"]):
            return Provider.KIMI
        elif any(k in mid for k in ["glm", "zhipu"]):
            return Provider.GLM
        elif "minimax" in mid:
            return Provider.MINIMAX
        elif "doubao" in mid:
            return Provider.DOUBAO
        return None

    def set_default_model(self, model_id: str):
        for m in self._models.values():
            m.is_default = (m.id == model_id)

    def get_vision_models(self) -> List[ModelInfo]:
        return [m for m in self._models.values() if m.supports_vision]

    def get_tool_models(self) -> List[ModelInfo]:
        return [m for m in self._models.values() if m.supports_tools]

    def search_models(self, query: str) -> List[ModelInfo]:
        q = query.lower()
        return [m for m in self._models.values()
                if q in m.id.lower() or q in m.name.lower() or q in m.description.lower()]

    def reload_models(self):
        """Reload/refresh model list."""
        self._models = {m.id: m for m in ALL_MODELS}
        logger.info(f"[ModelRegistry] Đã reload {len(self._models)} models")

    def get_model_count(self) -> int:
        return len(self._models)

    def get_provider_count(self) -> int:
        return len(set(m.provider for m in self._models.values()))


# Singleton registry
registry = ModelRegistry()
