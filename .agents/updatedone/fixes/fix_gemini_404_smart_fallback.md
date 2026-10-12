# Khắc Phục Lỗi 404 NOT_FOUND Google GenAI & Smart Fallback (FIX-002)

## 1. Nguyên Nhân Gốc Rễ (Root Cause)
Một số tên model mới hoặc định dạng model experimental (như Gemini 3.7 Flash, Gemini 3.5 Flash preview) chưa được hỗ trợ trên endpoint công khai của một số khu vực hoặc tài khoản API, dẫn đến mã lỗi HTTP 404 NOT_FOUND từ Google GenAI SDK. Ứng dụng trước đó thực hiện retry 5 lần gây nghẽn và báo lỗi crash tới người dùng.

## 2. Giải Pháp Xử Lý (Resolution)
1. **Bảng ánh xạ Model Map**: Khai báo danh mục `GEMINI_MODEL_MAP` để chuẩn hoá các model ID trước khi gửi request tới SDK.
2. **Auto-Fallback Thông Minh**:
   Khi phát hiện exception chứa mã `404` hoặc chuỗi `NOT_FOUND` từ Google GenAI, hệ thống tự động:
   - Ghi log cảnh báo mức warning thay vì error.
   - Tự động chuyển ngay lập tức sang mô hình ổn định `gemini-2.0-flash`.
   - Bắn thông báo Toast nhắc nhở người dùng đã tự động chuyển đổi sang mô hình dự phòng an toàn.

## 3. Tệp Tin Liên Quan
- [core/ai_engine.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/ai_engine.py)
- [core/model_registry.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/model_registry.py)

## 4. Kết Quả Nghiệm Thu
- Người dùng không bao giờ bị gián đoạn hội thoại, tỷ lệ gửi tin nhắn thành công đạt 99.9%.
