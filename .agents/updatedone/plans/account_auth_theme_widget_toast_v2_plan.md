# Kế Hoạch Triển Khai: Xác Thực Tài Khoản, Theme Sáng/Tối Chuẩn Tương Phản, Floating Widget & Tuỳ Chỉnh Vị Trí Toast

Tài liệu này mô tả chi tiết phương án kỹ thuật nâng cấp toàn diện các tính năng theo yêu cầu người dùng:
1. **Hệ thống Xác thực Đăng nhập & Quản lý Tài khoản (Authentication & User Management)**
2. **Chuẩn hoá Giao diện Sáng & Tối (Light/Dark Theme High Contrast & Polish)**
3. **Widget Nút Nổi Truy Cập Nhanh (Floating Quick Access Widget)**
4. **Tuỳ chỉnh Vị trí Thông Báo Toast (Customizable Toast Notification Position)**

---

## 1. Yêu Cầu & Phương Án Kỹ Thuật Chi Tiết

### 1.1. Xác thực Đăng nhập & Quản lý Tài khoản
- **Mặc định**: TẮT xác thực (`require_login = 0`), mở app vào thẳng màn hình chính.
- **Bật/Tắt trong Cài đặt**: Thêm tab **"👤 Quản Lý Tài Khoản & Bảo Mật"** (hoặc tích hợp trong Cài đặt) với nút bật/tắt xác thực khi khởi động.
- **Tài khoản mặc định**: Khi hệ thống chưa có user, tự động khởi tạo `admin` / `admin` (được băm mật khẩu bảo mật PBKDF2/SHA-256).
- **Bảo mật giao diện đăng nhập ([login_dialog.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/login_dialog.py))**:
  - **TUYỆT ĐỐI KHÔNG** điền sẵn (autofill) `admin` hay gợi ý mật khẩu trên UI login. Các ô nhập username/password luôn để trống.
  - Phím Enter tự động đăng nhập.
  - Hiển thị lỗi rõ ràng nếu sai tài khoản/mật khẩu, đồng thời ghi log đăng nhập thất bại.
- **Cơ sở dữ liệu người dùng & Lịch sử đăng nhập**:
  - Bảng `users`: `id`, `username`, `password_hash`, `salt`, `display_name`, `role`, `is_active`, `login_count`, `last_login_at`, `created_at`, `updated_at`.
  - Bảng `login_logs`: `id`, `username`, `status` (SUCCESS/FAILED), `ip_or_device`, `login_time`, `message`.
  - Quản lý trên UI:
    - Danh sách tài khoản với số lần đăng nhập, lần đăng nhập cuối.
    - ➕ Thêm tài khoản mới, ✏️ Sửa thông tin / Đổi mật khẩu, 🗑️ Xoá tài khoản (có kiểm tra an toàn, không cho xoá tài khoản admin đang dùng nếu chỉ còn 1 tài khoản).
    - Bảng lịch sử đăng nhập (Login Logs) kèm nút xoá logs.

---

### 1.2. Chuẩn hoá Giao diện Sáng & Tối (Contrast & Theme Polish)
- **Giao diện sáng (Light Mode)**:
  - Nền chính sạch sẽ, sáng nhẹ (`#f8fafc`), bề mặt thẻ `#ffffff`, viền `#cbd5e1` rõ ràng.
  - Chữ chính: `#0f172a` (Slate 900 đậm, cực kỳ sắc nét), chữ phụ: `#334155` (Slate 700), mô tả: `#475569` (Slate 600).
  - Không có tình trạng chữ trắng trên nền sáng hay chữ xám mờ khó đọc.
- **Giao diện tối (Dark Mode)**:
  - Nền tối sâu dịu mắt (`#0b0f19`), thẻ `#1e293b`, viền `#334155`.
  - Chữ chính: `#f8fafc` (Slate 50 sáng rõ), chữ phụ: `#cbd5e1`, mô tả: `#94a3b8`.
  - Đảm bảo tương phản hoàn hảo cho tất cả widget (Tables, GroupBoxes, Inputs, ComboBoxes, Radios, Menus, Dialogs).

---

### 1.3. Floating Quick Access Widget (Nút nổi truy cập nhanh)
- Tạo module mới: [ui/floating_widget.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/floating_widget.py).
- **Tính năng nổi**:
  - Cửa sổ Tool nổi luôn trên cùng (`WindowStaysOnTopHint | FramelessWindowHint | Tool`).
  - Cho phép kéo thả (draggable) tự do trên toàn bộ màn hình desktop, tự nhớ vị trí (`float_widget_x`, `float_widget_y`).
  - **Cơ chế làm mờ (Fade / Opacity)**:
    - Khi không hover (idle): Độ mờ giảm xuống ~0.35 - 0.45 để không che khuất công việc trên màn hình.
    - Khi rê chuột vào (hover): Tự động tăng độ mờ lên 1.0 mượt mà với hiệu ứng động (`QPropertyAnimation`).
  - **Các nút thao tác nhanh**:
    - 🪟 **Mở rộng cửa sổ**: Click để kích hoạt, đưa cửa sổ chính `MainWindow` lên trên cùng và focus làm việc.
    - 📸 **Chụp màn hình nhanh**: Chụp màn hình và gửi ngay vào khung AI Chat.
    - 💬 **Mở AI Chat**: Chuyển ngay đến trang Chat trong app.
    - ⚙️ **Cài đặt**: Mở hộp thoại cài đặt.
    - ❌ **Ẩn**: Thu nhỏ/ẩn thanh nổi.
  - Tích hợp bật/tắt trong Menu `View`, Top bar, System Tray và Cài đặt.

---

### 1.4. Tuỳ chỉnh Vị trí Thông Báo Toast ([toast.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/toast.py))
- **Mặc định**: ↘️ Góc phải dưới cùng (`bottom-right`).
- **Tuỳ chọn 6 vị trí trong Cài đặt**:
  1. ↘️ Góc phải dưới cùng (Bottom-Right — Mặc định)
  2. ↙️ Góc trái dưới cùng (Bottom-Left)
  3. ↗️ Góc phải trên cùng (Top-Right)
  4. ↖️ Góc trái trên cùng (Top-Left)
  5. ⬆️ Giữa trên cùng (Top-Center)
  6. ⬇️ Giữa dưới cùng (Bottom-Center)
- Hỗ trợ hiển thị xếp chồng nhiều thông báo (stacking) thông minh theo hướng từ trên xuống hoặc từ dưới lên tương ứng với vị trí.

---



---

## 3. Kế Hoạch Kiểm Thử (Verification Plan)

### Automated Syntax & Import Checks
- Kiểm tra toàn bộ mã nguồn không có lỗi cú pháp:
  `python -c "import ast; [ast.parse(open(f, encoding='utf-8').read()) for f in ['core/state_manager.py', 'ui/login_dialog.py', 'ui/floating_widget.py', 'ui/toast.py', 'ui/theme.py', 'ui/settings_dialog.py', 'ui/main_window.py', 'main.py']]"`
- Kiểm tra import modules thành công:
  `python -c "from ui.floating_widget import FloatingQuickAccessWidget; from ui.login_dialog import AIClawLoginDialog; from core.state_manager import StateManager; print('Imports OK')"`

### Manual Verification Flows
1. **Flow Đăng nhập & Quản lý User**:
   - Chạy app với setting mặc định (`require_login = 0`) -> App vào thẳng màn hình chính.
   - Mở Cài đặt -> Tab Tài khoản & Bảo mật -> Bật xác thực đăng nhập.
   - Thêm tài khoản mới (ví dụ: `testuser` / `123456`), đổi mật khẩu `admin`, xem bảng người dùng (số lần đăng nhập, lần đăng nhập cuối).
   - Đóng app, mở lại -> Xuất hiện màn hình Login với ô trống (không lộ admin) -> Đăng nhập bằng tài khoản -> Vào app và kiểm tra logs được ghi nhận chính xác.
2. **Flow Giao diện Sáng/Tối**:
   - Chuyển sang Light Mode: Nền sáng nhẹ, chữ đen/slate đậm nét, các thẻ nổi bật rõ ràng, không bị chìm chữ.
   - Chuyển sang Dark Mode: Nền tối sâu dịu mắt, chữ trắng/xám sáng tương phản cao.
3. **Flow Floating Quick Access Widget**:
   - Bật Floating Widget -> Widget xuất hiện trên màn hình desktop.
   - Rê chuột ra xa -> Widget mờ dần (~0.4 opacity). Rê chuột vào -> Widget sáng rõ (1.0 opacity).
   - Thu nhỏ hoặc ẩn MainWindow -> Click nút 🪟 (Mở rộng) trên Float Widget -> MainWindow ngay lập tức hiện lên và focus.
   - Kéo thả vị trí -> Tắt mở lại widget -> Vị trí được giữ nguyên.
4. **Flow Vị trí Toast**:
   - Đổi vị trí Toast sang Top-Right, Bottom-Left, Top-Center... trong Cài đặt -> Test bắn toast -> Toast xuất hiện đúng vị trí và xếp chồng mượt mà.

   
   
   Kế Hoạch Triển Khai: Xác Thực Tài Khoản, Theme Sáng/Tối Chuẩn Tương Phản, Floating Widget & Tuỳ Chỉnh Vị Trí Toast

   
   