# Quy Chuẩn Tái Sử Dụng Kỹ Thuật Đa Dự Án Desktop Python & AI

Tài liệu đúc kết các quy chuẩn thiết kế, cấu trúc hệ thống và bài học kinh nghiệm có thể áp dụng cho bất kỳ dự án Python Desktop (PyQt6 / CustomTkinter) kết hợp AI nào:

---

## 1. Kiến Trúc Phân Lớp Sạch Sẽ (Clean Layered Architecture)
- Tách bạch tuyệt đối giữa `core/` (logic thuần, xử lý API, DB, automation, không import Qt/UI) và `ui/` (chỉ giao diện, tương tác widget, import từ core).
- Main thread luôn dành riêng cho UI event loop. Mọi tác vụ nặng (gọi AI API, test model, I/O mạng, xử lý file) bắt buộc chạy trên `QThread` / Worker riêng.

## 2. Tiêu Chuẩn Chống Treo Đơ Giao Diện (Zero-Freeze Standards)
- **Deferred Load**: Constructor của Dialog/Window chỉ tạo khung widget, không gọi hàm load data nặng. Luôn hoãn nạp data sang sự kiện `showEvent()` kết hợp `QTimer.singleShot(50, self._load_data)`.
- **Signal Guarding**: Luôn gọi `widget.blockSignals(True)` trước khi nạp batch items vào ComboBox, ListWidget và `blockSignals(False)` sau đó.
- **Process Events**: Gọi `QApplication.processEvents()` giữa các vòng lặp tạo 10+ widgets.

## 3. Tiêu Chuẩn Bảo Mật & API Key Pool
- Không bao giờ lưu cứng API Key trong code. Lưu trong SQLite mã hoá hoặc `.env`.
- Mask key trên UI: chỉ hiển thị `...last8chars`.
- Đảm bảo cơ chế tự động xoay vòng key khi gặp rate limit (429) và fallback khi model 404.

## 4. Quản Lý Hồ Sơ Kỹ Thuật Tập Trung (.agents/updatedone)
- Loại bỏ các thư mục phân mảnh (`new*`, `update*`, `guide*`), tập trung vào thư mục duy nhất `.agents/updatedone/`.
- Đi kèm SPA Dashboard Viewer (`index.html`) xem offline độc lập, tra cứu markdown trực quan.
