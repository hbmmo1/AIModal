# Theme Tương Phản Chuẩn WCAG, 4 Chế Độ Density & Toast Tùy Biến (FEAT-007, FEAT-008)

## 1. Bối Cảnh & Mục Tiêu
Nâng cao tính thẩm mỹ và công thái học của giao diện người dùng, đảm bảo hiển thị sắc nét trên cả màn hình độ phân giải cao và màn hình nhỏ gọn, với màu sắc tương phản cao không gây mỏi mắt.

## 2. Phân Tích Kỹ Thuật
- **Hệ thống Theme Sáng / Tối tương phản cao**:
  - Dark Theme: Nền `#0b0f19`, bề mặt `#111827`, chữ `#f8fafc`.
  - Light Theme: Nền `#ffffff`, bề mặt `#f8fafc`, chữ `#0f172a` (loại bỏ hoàn toàn hiện tượng chữ mờ hoặc chìm nền).
  - Bảng màu `COLORS` 30 keys chuẩn hoá, tự động chuyển đổi qua `build_stylesheet()`.
- **4 Chế độ UI Density**:
  - `Material` (Chuẩn rộng rãi), `Compact` (Gọn gàng), `Lite Compact` (Nhẹ nhàng), `Super Compact` (Siêu gọn cho màn hình nhỏ).
  - 6 cỡ chữ từ `small` (11px) đến `extra_large` (19px).
- **Toast Notification 6 Vị Trí Tuỳ Chọn**:
  - Hỗ trợ 6 góc hiển thị: Top-Left, Top-Right, Top-Center, Bottom-Left, Bottom-Right, Bottom-Center.
  - Hàng đợi thông báo thông minh (queue), tự động tính toán toạ độ không bị đè lấn lên nhau, hiệu ứng fade-in / fade-out mượt mà.

## 3. Tệp Tin Liên Quan
- [ui/theme.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/theme.py): Bảng màu, typography, density tokens và stylesheet builder.
- [ui/toast.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/toast.py): Động cơ toast thông báo nổi đa vị trí.
- [ui/settings_dialog.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/settings_dialog.py): Tab cài đặt hiển thị và tuỳ chọn vị trí toast.

## 4. Kết Quả Nghiệm Thu
- Chuyển theme tức thì không nháy màn hình, thông báo toast xuất hiện đúng toạ độ đã cấu hình.
