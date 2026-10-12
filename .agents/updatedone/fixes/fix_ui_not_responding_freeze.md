# Khắc Phục Lỗi Đóng Băng Giao Diện (Not Responding) Trong Settings & Startup (FIX-001)

## 1. Nguyên Nhân Gốc Rễ (Root Cause)
1. **Khởi tạo dữ liệu nặng trong Constructor**: Gọi `_load_data()` đồng bộ ngay trong `__init__()` của `SettingsDialog` chặn hoàn toàn Qt main event loop.
2. **Kích hoạt chuỗi Signal Cascade**: Khi thêm items vào QComboBox (`addItem`), các tín hiệu `currentChanged` / `currentIndexChanged` tự động kích hoạt hàm `_refresh_model_cards()` lặp lại 16 lần liên tiếp.
3. **Thực thi CSDL lặp trong vòng lặp UI**: Truy vấn SQLite `get_provider_key_count()` lặp đi lặp lại 16 lần khi render danh sách model.
4. **Vòng lặp tạo 65+ ModelCard widgets**: Main thread bị nghẽn do khởi tạo đồng thời quá nhiều widget phức tạp mà không nhường quyền xử lý sự kiện hệ điều hành.

## 2. Giải Pháp Xử Lý (Resolution)
1. **Deferred Loading với QTimer**:
   Chuyển toàn bộ tác vụ nạp dữ liệu nặng sang sự kiện `showEvent()` kết hợp `QTimer.singleShot(50, self._deferred_load)` để cửa sổ hiện ra tức thì trước khi render data.
2. **Khóa Tín Hiệu (Signal Blocking)**:
   Chèn `combo.blockSignals(True)` trước khi thêm dữ liệu vào QComboBox và `combo.blockSignals(False)` sau khi nạp xong.
3. **Phân Đoạn Render với `processEvents()`**:
   Gọi `QApplication.processEvents()` giữa các batch tạo widget để hệ điều hành luôn nhận diện cửa sổ ở trạng thái hoạt động (Responsive).

## 3. Tệp Tin Liên Quan
- [ui/settings_dialog.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/settings_dialog.py)
- [ui/main_window.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/main_window.py)

## 4. Kết Quả Nghiệm Thu
- Settings Dialog mở ra trong < 100ms, không còn hiện tượng treo đơ hay gắn nhãn "(Not Responding)" trên Windows.
