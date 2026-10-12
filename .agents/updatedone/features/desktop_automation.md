# Desktop Automation & Visual Workflow Engine (FEAT-002)

## 1. Bối Cảnh & Mục Tiêu
Cung cấp khả năng tự động hoá mọi tác vụ lặp đi lặp lại trên máy tính desktop: điều khiển chuột, bàn phím, kích hoạt phím tắt, chụp ảnh màn hình phân tích ngữ cảnh, và phối hợp thành các chuỗi workflow phức tạp.

## 2. Phân Tích Kỹ Thuật
- **Action Executor**:
  - Tích hợp PyAutoGUI và Win32 API để click chuột, di chuyển con trỏ chuột theo toạ độ tuyệt đối/tương đối, cuộn trang, nhập liệu ký tự tiếng Việt Unicode an toàn.
  - Tích hợp cơ chế Fail-Safe góc màn hình chống treo chuột ngoài tầm kiểm soát.
- **Visual Workflow Runner**:
  - Quản lý các bước thực thi dưới dạng JSON schema định nghĩa trong `workflows/` và `presets/`.
  - Hỗ trợ các khối lệnh: `click`, `move`, `type_text`, `hotkey`, `delay`, `screenshot`, `condition`.
  - Theo dõi tiến độ từng bước trực quan trên UI với thanh tiến trình và thông báo kết quả.

## 3. Tệp Tin Liên Quan
- [core/action_executor.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/action_executor.py): Thực thi điều khiển chuột, bàn phím an toàn.
- [core/workflow_models.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/core/workflow_models.py): Khai báo mô hình dữ liệu workflow và action.
- [ui/automation_panel.py](file:///c:/Intel/Laragon/www/300_Python/301_AIClaude/ui/automation_panel.py): Giao diện thiết lập và chạy kịch bản tự động hoá.

## 4. Kết Quả Nghiệm Thu
- Tự động hoá chính xác, không trượt toạ độ, ghi nhận log đầy đủ từng bước thao tác.
