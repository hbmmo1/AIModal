# Khắc Phục Lỗi SQLite Migration & NameError Qt Widgets (FIX-003, FIX-004)

## 1. Chi Tiết Lỗi SQLite Migration (`api_keys`)
- **Triệu chứng**: `sqlite3.OperationalError: no such table: gemini_api_keys`.
- **Nguyên nhân**: Ban đầu hệ thống chỉ lưu API Key của Gemini trong bảng `gemini_api_keys`. Khi nâng cấp lên Multi-AI 16 Providers, hệ thống chuyển sang bảng chung `api_keys`. Các phiên bản cũ khi khởi chạy gặp lỗi do chưa có cơ chế migration tự động.
- **Khắc phục**: Viết hàm auto-migration trong [core/key_manager.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/key_manager.py), tự động kiểm tra tồn tại của bảng cũ và sao chép dữ liệu sang cấu trúc mới trước khi vận hành.

## 2. Chi Tiết Lỗi NameError Thiếu Import Qt Widgets
- **Triệu chứng**: `NameError: name 'QGroupBox' is not defined` hoặc `name 'QGridLayout' is not defined`.
- **Nguyên nhân**: Quá trình mở rộng giao diện nhanh dẫn đến thiếu khai báo import trực tiếp từ `PyQt6.QtWidgets`.
- **Khắc phục**: Bổ sung đầy đủ các widget hay thiếu: `QGroupBox`, `QGridLayout`, `QScrollArea`, `QSpinBox`, `QSlider`, `QRadioButton`, `QButtonGroup`, `QSizePolicy` trong [ui/main_window.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/main_window.py) và [ui/knowledge_panel.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/knowledge_panel.py). Đưa vào Checklist kiểm thử bắt buộc trước khi commit.
