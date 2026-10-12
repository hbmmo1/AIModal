# Hệ Thống Xác Thực & Quản Lý Tài Khoản Bảo Mật PBKDF2 (FEAT-006)

## 1. Bối Cảnh & Mục Tiêu
Bảo vệ dữ liệu người dùng và các API Key nhạy cảm trong môi trường desktop đa người dùng. Hệ thống cho phép bật/tắt yêu cầu đăng nhập linh hoạt theo nhu cầu cá nhân hoặc môi trường doanh nghiệp.

## 2. Phân Tích Kỹ Thuật
- **Cơ chế Bật/Tắt linh hoạt**:
  - Mặc định: `require_login = 0` (Tắt) — mở app vào thẳng màn hình làm việc tiện lợi.
  - Khi bật: Yêu cầu xác thực tài khoản qua hộp thoại đăng nhập bảo mật.
- **Tiêu chuẩn Bảo mật Giao diện Login**:
  - Tuyệt đối không tự động điền (autofill) `admin` hay mật khẩu mẫu, các trường nhập luôn để trống để tránh lộ lọt thông tin.
  - Mật khẩu được băm (hash) bằng thuật toán chuẩn công nghiệp `PBKDF2-HMAC-SHA256` với salt ngẫu nhiên 16 bytes và 100.000 vòng lặp.
- **Quản lý Tài khoản & Nhật ký Truy cập**:
  - CRUD tài khoản: Thêm, sửa, đổi mật khẩu, vô hiệu hoá hoặc xoá tài khoản.
  - Ghi nhận nhật ký đăng nhập chi tiết (thời gian, trạng thái, thiết bị, lỗi sai mật khẩu).

## 3. Tệp Tin Liên Quan
- [ui/login_dialog.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/login_dialog.py): Hộp thoại đăng nhập an toàn, giao diện hiện đại.
- [core/state_manager.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/state_manager.py): Bảng CSDL SQLite `users`, `login_logs`, mã hoá PBKDF2.
- [ui/settings_dialog.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/settings_dialog.py): Tab quản lý tài khoản & công tắc bảo mật.
- [main.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/main.py): Cổng kiểm tra xác thực trước khi hiển thị MainWindow.

## 4. Kết Quả Nghiệm Thu
- Đăng nhập bảo mật, chuyển giao diện mượt mà không crash, phòng chống tấn công brute-force cơ bản.
