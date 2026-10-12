# 🤖 AI CLAW — Trợ Lý Tự Động Hoá Thông Minh

Nền tảng tự động hoá desktop tích hợp AI (Gemini), cho phép tự động hoá mọi quy trình lặp đi lặp lại — từ thao tác chuột/bàn phím, xử lý file hàng loạt, đến workflow nhiều bước.

## ✨ Tính năng chính

### 🤖 AI Chat Assistant
- Mô tả công việc bằng tiếng Việt → AI tạo kịch bản tự động hoá
- AI phân tích screenshot nhận diện element trên màn hình
- Chat history lưu trữ đầy đủ

### 🖱️ Desktop Automation
- Click, gõ phím, kéo thả, cuộn chuột tự động
- Record macro bằng hotkey
- Loop/lặp lại theo số lần hoặc thời gian

### 📁 Xử lý File hàng loạt
- AI đặt tên file thông minh
- Phân loại file tự động
- Tóm tắt nội dung document

### 🔄 Visual Workflow Editor (Phase 2)
- Kéo thả nodes tạo quy trình
- Kết hợp AI + Automation + File processing

## 🛠️ Cài Đặt & Chạy

### Yêu cầu
- Python 3.9+
- Windows 10/11

### Cài đặt thư viện
```powershell
pip install -r requirements.txt
```

### Khởi chạy
```powershell
python main.py
# hoặc nhấp đúp vào run_ai_claw.bat
```

### Cấu hình API Key
1. Sửa file `.env` và điền Gemini API Key:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```
2. Hoặc cấu hình trong Settings → API Keys trong ứng dụng.

## ⌨️ Phím tắt
| Phím | Chức năng |
|------|-----------|
| F8 | Bắt đầu chạy macro |
| F9 | Tạm dừng/Tiếp tục |
| F10 | Dừng hoàn toàn |
| Ctrl+Shift+S | Chụp screenshot + AI phân tích |
| Ctrl+Shift+A | Mở nhanh AI Chat |
