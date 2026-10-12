# Kế Hoạch Nâng Cấp & Hoàn Thiện Canva Tool Studio

## Tổng Quan Mục Tiêu
Bản nâng cấp toàn diện giải quyết triệt để các yêu cầu:
1. **Backup Code**: Tạo bản sao lưu an toàn toàn bộ mã nguồn hiện tại.
2. **Khắc phục triệt để lag/đơ/Not Responding**: Tối ưu hóa đa luồng nền (QThread, throttling tín hiệu progress, giải phóng main GUI thread).
3. **Mặc định chuyển đổi Video giữ 94% độ nét**: Cấu hình mặc định độ nét 94% (CRF 19 - Sắc nét chuẩn studio) cho video và hiển thị trực quan.
4. **Nén PPTX & Video an toàn 100% cho Microsoft Office & WPS Office**:
   - Đóng gói chuẩn OpenXML Zip (bảo toàn cấu trúc `[Content_Types].xml`, `_rels`, timestamp chuẩn, đường dẫn forward-slash).
   - Nén video nhúng: Ép chuẩn H.264 High/Main Profile Level 4.1, `pix_fmt=yuv420p`, kích thước chẵn (even dimensions), AAC stereo audio, `+faststart` moov atom, bảo toàn định dạng tệp và mối quan hệ slide XML.
   - Nén ảnh nhúng: Baseline JPEG & chuẩn PNG (RGB/RGBA), không làm sai lệch cấu trúc slide.
5. **Hệ thống Quản lý Tài khoản & Xác thực Đăng nhập**:
   - Mặc định: **TẮT** (không bắt buộc đăng nhập khi vào app).
   - Khi BẬT: Đăng nhập tài khoản mặc định `admin`/`admin` (không hiển thị lộ thông tin ở gợi ý/placeholder).
   - Bảng quản trị tài khoản trong Cài đặt: Thêm, sửa, xoá tài khoản, đổi mật khẩu, theo dõi số lần đăng nhập, lần đăng nhập cuối cùng, nhật ký đăng nhập chi tiết.
6. **Giao diện Sáng / Tối tối ưu độ tương phản**:
   - Giao diện Sáng (Light): Nền sáng nhẹ/trắng thanh thoát, màu chữ đậm tương phản cao, tuyệt đối không bị chìm màu.
   - Giao diện Tối (Dark): Nền tối sang trọng, màu chữ sáng rõ, sắc nét.
7. **Nút cuộn (Scrollbar) tự động trong Cài đặt**:
   - Thiết lập `QScrollArea` với cơ chế cuộn thông minh (chỉ hiển thị thanh cuộn khi nội dung vượt quá chiều cao màn hình, ẩn khi đủ không gian).
8. **Tiện ích Floating Mini Bar**:
   - Thanh công cụ nổi tiện lợi trên màn hình, kéo thả tự do, tự động mờ khi không chạm (Auto-Dimming), nút mở rộng bung to lại cửa sổ chính. Nút bật/tắt Float Bar trực tiếp trên HeaderBar.
9. **Cấu hình Vị trí Toast Notification**:
   - Mặc định: **Góc phải dưới cùng (Bottom-Right)**.
   - Hỗ trợ tuỳ chỉnh trong Cài đặt: Góc phải trên/dưới, Góc trái trên/dưới, Chính giữa trên/dưới.
10. **Tài liệu & Quy tắc**:
    - Tạo/cập nhật `Update1.md` liệt kê chi tiết toàn bộ tính năng.
    - Cập nhật quy tắc chống lỗi tương tự vào `GEMINI.md`.

---

## Các Thay Đổi Cụ Thể

### 1. Sao Lưu Toàn Bộ Mã Nguồn
- Tạo thư mục `backup/canva_tool_backup_latest/` hoặc gói nén sao lưu đầy đủ hiện trạng.

### 2. Tối Ưu Hiệu Năng & Chống Đơ Lag (Anti-Freeze Architecture)
- Throttling tín hiệu tiến độ trong `VideoBatchWorker` và `PPTXBatchWorker` (tối đa 15-20 updates/giây thay vì phát tín hiệu liên tục theo từng dòng ffmpeg stderr làm nghẽn Qt Event Loop).
- Đảm bảo toàn bộ tác vụ đĩa nặng, tính toán kích thước, dò bitrate, trích xuất zip đều chạy 100% trong Background Thread `QThread`.

### 3. Video Engine & Mặc Định 94% Độ Nét
- Cập nhật `canva_tool/config.py` và `canva_tool/core/settings_manager.py`:
  - `video_crf`: Đặt mặc định 19 (tương đương 94% độ nét mắt thường không phân biệt được so với gốc).
  - Cập nhật UI Slider trong `MediaStudioView` hiển thị mức `94% (CRF 19 - Sắc nét tối ưu)`.

### 4. PPTX Engine An Toàn Tuyệt Đối Cho Microsoft Office & WPS
- Cập nhật `canva_tool/core/pptx_engine.py`:
  - Đảm bảo video nén trong PPTX luôn có kích thước chẵn (`-vf "scale=trunc(iw/2)*2:trunc(ih/2)*2"`), pixel format `yuv420p`, profile `high`, level `4.1`, audio `aac` 44.1k/48k stereo, container flag `+faststart`.
  - Tối ưu ảnh với chế độ Baseline JPEG và RGB/RGBA PNG, tránh làm hỏng slide XML parser của WPS/PowerPoint.
  - Viết lại zip đóng gói PPTX đảm bảo thứ tự `[Content_Types].xml` chuẩn, kiểm tra `testzip()` tự động.

### 5. Quản Lý Tài Khoản & Cài Đặt Hệ Thống
- Tạo mô-đun quản lý xác thực `canva_tool/core/auth_manager.py`:
  - Quản lý tài khoản (admin, user), mã hóa hash mật khẩu, lưu trữ `auth_data.json`.
  - Lưu trữ lịch sử đăng nhập (thời gian, tài khoản, trạng thái), đếm số lần đăng nhập, lần đăng nhập cuối.
- Cập nhật `canva_tool/ui/login_dialog.py`:
  - Xóa bỏ text gợi ý `admin`/`admin` mặc định khỏi ô nhập.
  - Tích hợp xác thực với `AuthManager`.
- Tạo Dialog / Giao diện Cài Đặt Toàn Diện `canva_tool/ui/settings_dialog.py` (hoặc Tab Cài Đặt) bao gồm:
  - Bật / Tắt yêu cầu đăng nhập (Mặc định: TẮT).
  - Bảng quản trị tài khoản: Thêm, Sửa thông tin & Mật khẩu, Xoá tài khoản, Xem lịch sử và số lần đăng nhập.
  - Cấu hình vị trí Toast Notification (Mặc định: Góc phải dưới cùng).
  - Cài đặt giao diện & Chế độ Float Mini Bar.
  - Sử dụng `QScrollArea` cuộn mượt mà chỉ khi nội dung vượt quá kích thước màn hình.

### 6. Giao Diện & Tiện Ích Floating Mini Bar
- Cập nhật `canva_tool/ui/theme_engine.py`: Rà soát và tinh chỉnh độ tương phản màu sắc cho Light Mode & Dark Mode.
- Nâng cấp `canva_tool/ui/widgets/floating_mini_bar.py` và kết nối với HeaderBar / MainWindow.
- Nâng cấp `canva_tool/ui/widgets/toast_notification.py` hỗ trợ vị trí linh hoạt theo cài đặt.

### 7. Cập Nhật Tài Liệu & Note GEMINI.md
- Tạo `Update1.md` tổng hợp toàn diện chức năng.
- Bổ sung kinh nghiệm xử lý lỗi & quy chuẩn kỹ thuật vào `GEMINI.md`.

---

## Kế Hoạch Kiểm Thử (Verification Plan)
1. **Kiểm tra Unit Tests**: Chạy `python -m unittest discover tests` đảm bảo 100% tests vượt qua.
2. **Kiểm tra Xác thực & Cài đặt**:
   - Kiểm tra khi `require_login = False` (mặc định): App vào thẳng không cần login.
   - Khi `require_login = True`: Hiện login dialog không có thông tin gợi ý, đăng nhập đúng vào được, ghi nhận số lần và thời gian đăng nhập.
   - Thêm/sửa/xóa tài khoản thành công trong Cài đặt.
3. **Kiểm tra Chuyển đổi Video**:
   - Mặc định 94% độ nét (CRF 19).
   - Kiểm tra lệnh FFmpeg xuất ra chuẩn H.264 / `yuv420p` / `+faststart`.
4. **Kiểm tra PPTX Optimizer**:
   - Kiểm tra giải nén, tối ưu media và đóng gói PPTX.
   - Đảm bảo tệp PPTX sau khi nén có thể mở mượt mà trên Microsoft PowerPoint & WPS Office không báo lỗi định dạng hay media error.
5. **Kiểm tra Giao diện Sáng/Tối & Scrollbar**:
   - Chuyển đổi theme Light / Dark mượt mà, văn bản rõ nét tương phản chuẩn.
   - Thu nhỏ cửa sổ Settings kiểm tra thanh cuộn chỉ xuất hiện khi cần thiết.
