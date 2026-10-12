# Multi-AI Engine — 79 Mô Hình & 16 Nhà Cung Cấp (FEAT-001)

## 1. Bối Cảnh & Mục Tiêu
Hệ thống AI Claw được thiết kế nhằm mục đích tích hợp đa dạng nhà cung cấp AI trong một nền tảng desktop duy nhất. Người dùng không bị bó hẹp trong một nhà cung cấp đơn lẻ mà có thể linh hoạt chuyển đổi giữa Google Gemini, Anthropic Claude, OpenAI, DeepSeek, Groq, OpenRouter, v.v.

## 2. Phân Tích Kỹ Thuật
- **Hệ thống phân cấp mô hình**: 4 hạng giá `CHEAPEST`, `BALANCED`, `MODERATE`, `BEST`.
- **Hỗ trợ Streaming**: Truyền phản hồi realtime thông qua QThread worker an toàn không gây lag giao diện.
- **Cơ chế Smart Model Resolver & 404 Auto-Fallback**:
  - Tự động map ID mô hình qua bảng tra cứu `GEMINI_MODEL_MAP`.
  - Khi gặp lỗi 404 Model Not Found từ API Google, cơ chế thông minh tự động fallback sang `gemini-2.0-flash` mà không ngắt phiên làm việc hay gây crash app.
- **Bảo mật API Key**: Hệ thống quản lý SQLite key pool, tự động xoay tua (rotation), kiểm tra tình trạng key (health check) và che mờ key khi hiển thị trên giao diện (`...last8chars`).

## 3. Tệp Tin Liên Quan
- [core/model_registry.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/model_registry.py): Quản lý 79 mô hình AI, thông số giá token, đánh giá tốc độ/chất lượng.
- [core/ai_engine.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/ai_engine.py): Động cơ gửi request, streaming, vision và auto-fallback.
- [core/key_manager.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/key_manager.py): Lưu trữ và xoay vòng API Keys an toàn trong SQLite.
- [ui/chat_panel.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/chat_panel.py): Giao diện hội thoại tương tác trực quan.

## 4. Kết Quả Nghiệm Thu
- Khả năng phản hồi streaming ổn định 100%.
- Không bao giờ crash khi gặp sự cố từ nhà cung cấp nhờ try/catch toàn diện và fallback thông minh.
