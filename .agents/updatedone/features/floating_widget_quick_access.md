# Floating Quick Access Mini Widget (FEAT-005)

## 1. Bối Cảnh & Mục Tiêu
Cung cấp thanh công cụ mini nổi trên màn hình (Always on Top) giúp người dùng gọi nhanh các tác vụ AI Claw ngay cả khi đang làm việc trên các ứng dụng khác (trình duyệt, Office, IDE) mà không cần phóng to cửa sổ chính.

## 2. Phân Tích Kỹ Thuật
- **Frameless & Always-on-Top Window**:
  - Sử dụng cờ `Qt.WindowType.FramelessWindowHint` và `Qt.WindowType.WindowStaysOnTopHint`.
  - Hỗ trợ nền mờ viền bo tròn hiện đại, bóng đổ nổi bật.
- **Kéo thả tự do (Draggable Window)**:
  - Bắt sự kiện `mousePressEvent` và `mouseMoveEvent` cho phép kéo di chuyển widget khắp màn hình mượt mà.
  - Lưu vị trí toạ độ vào SQLite để tự động khôi phục khi mở lại app.
- **Các nút chức năng nhanh**:
  - 📸 Chụp màn hình & gửi nhanh vào Chat.
  - 💬 Hiện/Ẩn cửa sổ chính tức thì.
  - ⚡ Kích hoạt kịch bản tự động hoá nhanh.
  - ⚙️ Mở Cài đặt nhanh.

## 3. Tệp Tin Liên Quan
- [ui/floating_widget.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/floating_widget.py): Widget mini nổi độc lập.
- [ui/main_window.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/main_window.py): Đồng bộ trạng thái giữa Floating Widget và Main Window.

## 4. Kết Quả Nghiệm Thu
- Widget chuyển động trơn tru, không lag CPU, ghim nổi ổn định trên mọi cửa sổ Windows.
