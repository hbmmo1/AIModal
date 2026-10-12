# 🤖 AI CLAW — Nền tảng Tự động hoá Thông minh bằng AI

**Mục tiêu**: Xây dựng ứng dụng desktop Python (PyQt6) tích hợp Gemini AI, cho phép người dùng tự động hoá mọi quy trình lặp đi lặp lại trên desktop — từ thao tác chuột/bàn phím, xử lý file hàng loạt, đến workflow nhiều bước — tất cả được AI hỗ trợ tối ưu.

> [!IMPORTANT]
> **Pattern**: Dự án theo chuẩn cấu trúc của `200CanvaTool` & `100AISupport` (có `GEMINI.md`, `README.md`, `requirements.txt`, `.agents/rules/`, `build_exe.bat`, cấu trúc thư mục `core/`, `ui/`).

---

## 📋 User Review Required

> [!WARNING]
> **Phạm vi Phase 1**: Dự án rất lớn (5 module chính + AI engine + workflow visual). Đề xuất triển khai **Phase 1 MVP** trước với core foundation + 2-3 module chính, rồi mở rộng dần.

> [!IMPORTANT]
> **API Key**: Sẽ dùng cùng pattern `KeyManager` multi-key rotation từ `100AISupport` + hỗ trợ `.env` file. Gemini API key hiện có: `AIzaSyDAC3R0AwvYZGEcpWicsvU913GK_Orj79M`

---

## 🏗️ Kiến trúc Tổng thể

```mermaid
graph TB
    subgraph UI["🎨 UI Layer (PyQt6)"]
        MainHub["Main Hub Dashboard"]
        ChatPanel["AI Chat Panel"]
        WorkflowEditor["Workflow Visual Editor"]
        AutomationPanel["Automation Panel"]
        FileProcessor["File Processor Panel"]
        SettingsPanel["Settings & API Keys"]
    end

    subgraph Core["⚙️ Core Engine"]
        AIEngine["Gemini AI Engine"]
        KeyMgr["Key Manager (Multi-Key Rotation)"]
        ActionExecutor["Action Executor (Mouse/Keyboard)"]
        WorkflowRunner["Workflow Runner"]
        FileEngine["File Processing Engine"]
        ScreenAnalyzer["Screen Analyzer (Vision AI)"]
        Scheduler["Task Scheduler"]
    end

    subgraph Data["💾 Data Layer"]
        SQLite["SQLite Database"]
        Workflows["Workflow JSON Files"]
        Config["config.yaml + .env"]
        Logs["Execution Logs"]
    end

    UI --> Core
    Core --> Data
    AIEngine --> KeyMgr
    WorkflowRunner --> ActionExecutor
    WorkflowRunner --> FileEngine
    WorkflowRunner --> AIEngine
    ScreenAnalyzer --> AIEngine
```

---

## 📁 Cấu trúc Thư mục

```
300AIClaude/
├── main.py                          # Entry point (chuẩn pattern)
├── requirements.txt                 # Dependencies
├── README.md                        # Hướng dẫn sử dụng
├── GEMINI.md                        # Quy tắc phát triển cho AI
├── run_ai_claw.bat                  # Batch launcher
├── build_exe.bat                    # PyInstaller builder
├── .env                             # API keys (gitignored)
│
├── .agents/
│   └── rules/
│       └── packaging_rules.md       # Quy tắc đóng gói
│
├── config/
│   ├── config.yaml                  # Cấu hình chính
│   ├── app_data.db                  # SQLite database
│   └── persona.txt                  # AI persona / system prompt
│
├── core/
│   ├── __init__.py
│   ├── ai_engine.py                 # Gemini AI Engine (chat + tool calling)
│   ├── key_manager.py               # Multi API Key Manager + Rotation
│   ├── action_executor.py           # Mouse/Keyboard automation engine
│   ├── screen_analyzer.py           # Screenshot + Gemini Vision analysis
│   ├── file_processor.py            # Batch file processing with AI
│   ├── workflow_runner.py           # Workflow execution engine
│   ├── workflow_models.py           # Workflow/Node/Action data models
│   ├── scheduler.py                 # Task scheduling (cron-like)
│   └── state_manager.py            # App state + execution history (SQLite)
│
├── ui/
│   ├── __init__.py
│   ├── theme.py                     # Tailwind Dark Theme (chuẩn 200CanvaTool)
│   ├── main_window.py               # Main Hub Window
│   ├── chat_panel.py                # AI Chat Assistant Panel
│   ├── workflow_editor.py           # Visual Workflow Editor (drag & drop)
│   ├── automation_panel.py          # Desktop Automation Panel
│   ├── file_panel.py                # File Processor Panel
│   ├── settings_dialog.py           # Settings & API Key Management
│   ├── node_widgets.py              # Visual node widgets for workflow
│   └── log_viewer.py                # Execution log viewer
│
├── workflows/                       # Saved workflow JSON files
│   └── examples/
│       ├── web_scraping.json
│       ├── file_rename_batch.json
│       └── auto_form_fill.json
│
└── presets/                         # Preset configurations
    └── default_actions.json
```

---

## 🔧 Proposed Changes — Phase 1 MVP

### Component 1: Foundation & Configuration

#### [NEW] [main.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/main.py)
- Entry point chuẩn pattern (UTF-8 config, error logging, crash dialog)
- Khởi tạo QApplication + MainWindow
- Exception handler toàn cục ghi `error_log.txt`

#### [NEW] [.env](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/.env)
- `GEMINI_API_KEY=AIzaSyDAC3R0AwvYZGEcpWicsvU913GK_Orj79M`

#### [NEW] [config/config.yaml](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/config/config.yaml)
- Cấu hình Gemini (api_key, model_name, temperature)
- Cấu hình automation (default delays, hotkeys)
- Cấu hình app (theme, language)

#### [NEW] [requirements.txt](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/requirements.txt)
```
PyQt6>=6.6.0
google-genai>=1.0.0
Pillow>=10.2.0
pyautogui>=0.9.54
pyperclip>=1.8.2
pywin32>=306
pygetwindow>=0.0.9
pynput>=1.7.6
keyboard>=0.13.5
pyyaml>=6.0.1
python-dotenv>=1.0.0
requests>=2.31.0
mss>=9.0.0
```

#### [NEW] [GEMINI.md](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/GEMINI.md)
- Quy tắc phát triển (không tự build exe, test trước khi commit)

#### [NEW] [README.md](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/README.md)
- Hướng dẫn cài đặt, chạy, sử dụng

#### [NEW] [run_ai_claw.bat](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/run_ai_claw.bat)
- Batch file khởi chạy nhanh

---

### Component 2: Core AI Engine

#### [NEW] [core/ai_engine.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/ai_engine.py)
- **GeminiEngine class** tích hợp `google-genai` SDK
- Multi-turn conversation với context memory
- **Tool calling / Function calling** — AI có thể gọi các hàm tự động hoá
- Gemini Vision — phân tích screenshot
- System prompt persona tùy chỉnh
- Auto-retry 5 lần + key rotation khi quota hết
- Hỗ trợ models: `gemini-3.6-flash`, `gemini-3.7-flash`, `gemini-pro-latest`

#### [NEW] [core/key_manager.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/key_manager.py)
- Pattern từ `100AISupport` — SQLite-backed multi-key management
- Add/Remove/Check/Rotate keys
- Quota tracking per key
- Sync từ `config.yaml` + `.env`

#### [NEW] [core/state_manager.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/state_manager.py)
- SQLite database cho:
  - Execution history (workflow runs, kết quả)
  - Chat history (lưu hội thoại AI)
  - Statistics (số lần chạy, thời gian tiết kiệm)

---

### Component 3: Automation Engine

#### [NEW] [core/action_executor.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/action_executor.py)
- **ActionExecutor class** — thực thi thao tác desktop:
  - Mouse: click, double-click, drag, scroll, move
  - Keyboard: key press, key combo, type text, paste
  - Window: activate, resize, minimize, maximize
  - Wait: delay, wait for image, wait for window
- Thread-safe execution với stop/pause/resume
- Hotkey listener (F8 start, F9 pause, F10 stop)

#### [NEW] [core/screen_analyzer.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/screen_analyzer.py)
- Chụp screenshot bằng `mss` (nhanh hơn pyautogui)
- Gửi screenshot lên Gemini Vision để:
  - Nhận diện vị trí element (nút, textbox, menu...)
  - Mô tả nội dung màn hình
  - Đề xuất hành động tiếp theo
- OCR đơn giản qua Gemini Vision

#### [NEW] [core/workflow_models.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/workflow_models.py)
- **Node types** (dataclasses):
  - `TriggerNode` — điểm bắt đầu (manual, schedule, hotkey)
  - `ActionNode` — thao tác (click, type, wait, open app...)
  - `AINode` — gọi Gemini AI (chat, vision, summarize, translate...)
  - `FileNode` — xử lý file (rename, move, compress, convert...)
  - `ConditionNode` — rẽ nhánh IF/ELSE
  - `LoopNode` — vòng lặp
  - `WebNode` — web actions (open URL, scrape, fill form)
- **Workflow** — danh sách nodes liên kết (graph structure)
- Serialization JSON (save/load)

#### [NEW] [core/workflow_runner.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/workflow_runner.py)
- Thực thi workflow step-by-step
- Hỗ trợ conditional branching & loops
- Real-time progress callbacks
- Error handling + retry logic
- Execution log

#### [NEW] [core/file_processor.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/file_processor.py)
- Batch file operations:
  - AI rename (Gemini phân tích nội dung → gợi ý tên)
  - AI classify (phân loại file vào thư mục)
  - AI summarize (tóm tắt nội dung document)
  - Bulk convert (format chuyển đổi)
- Progress tracking

#### [NEW] [core/scheduler.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/core/scheduler.py)
- Schedule workflow runs (one-time, recurring)
- Cron-like scheduling
- Background execution

---

### Component 4: UI Layer (PyQt6 — Tailwind Dark Theme)

#### [NEW] [ui/theme.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/theme.py)
- Tailwind Dark theme chuẩn `200CanvaTool`:
  - Background: `#0b0f19` (Slate 950)
  - Surface: `#1e293b` (Slate 800)
  - Primary accent: `#6366f1` (Indigo 500)
  - Secondary accent: `#06b6d4` (Cyan 500)
  - Success/Error/Warning colors
  - Glassmorphism cards, smooth transitions
  - Modern typography (Segoe UI / Inter)

#### [NEW] [ui/main_window.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/main_window.py)
- **Main Hub** với sidebar navigation:
  - 🤖 **AI Chat** — Trợ lý AI (hỏi → AI tự thực hiện)
  - 🔄 **Workflows** — Visual workflow editor
  - 🖱️ **Automation** — Desktop automation
  - 📁 **File Processing** — Xử lý file hàng loạt
  - ⚙️ **Settings** — Cài đặt & API keys
- Status bar (AI status, running tasks, stats)
- System tray icon

#### [NEW] [ui/chat_panel.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/chat_panel.py)
- Chat UI hiện đại (bubble messages)
- Người dùng mô tả bằng tiếng Việt → AI tạo workflow
- AI có thể **thực thi trực tiếp** hành động (với xác nhận)
- Hiển thị tool calls (AI đang làm gì)
- Markdown rendering trong chat
- Lưu/load lịch sử hội thoại

#### [NEW] [ui/workflow_editor.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/workflow_editor.py)
- **Visual Canvas** kéo-thả nodes (QGraphicsView)
- Node palette sidebar (drag để thêm node)
- Kết nối nodes bằng đường nối (connection wires)
- Node inspector panel (chỉnh thuộc tính node)
- Zoom/Pan canvas
- Save/Load workflow
- AI suggestion — Gemini gợi ý cải thiện workflow
- Run/Stop/Pause workflow trực tiếp

#### [NEW] [ui/automation_panel.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/automation_panel.py)
- Quick macro recorder (record mouse/keyboard)
- Step list editor (add/edit/delete steps)
- Screen picker (chọn tọa độ trên màn hình)
- AI-assisted: chụp screenshot → AI nhận diện element
- Loop config (count/infinite/time-based)
- Hotkey controls

#### [NEW] [ui/file_panel.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/file_panel.py)
- Drag & drop file/folder
- File list table (tên gốc, tên AI đề xuất, trạng thái)
- AI operations: rename, classify, summarize
- Preview kết quả trước khi apply
- Progress bar

#### [NEW] [ui/settings_dialog.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/settings_dialog.py)
- API Key management (multi-key, check quota, rotation)
- Model selection (dropdown)
- Theme selection
- Hotkey configuration
- General settings

#### [NEW] [ui/log_viewer.py](file:///c:/Intel/Laragon/www/PythonAll/300AIClaude/ui/log_viewer.py)
- Real-time execution log
- Filter by level (INFO/WARNING/ERROR)
- Searchable
- Export log

---

### Component 5: Example Workflows & Presets

#### [NEW] workflows/examples/
- `web_scraping.json` — Mở Chrome → Navigate → Scrape data
- `file_rename_batch.json` — Quét thư mục → AI đặt tên → Rename
- `auto_form_fill.json` — Mở form → AI điền thông tin

#### [NEW] presets/
- `default_actions.json` — Preset mặc định cho action executor

---

## 🚀 Phân Phase Triển khai

### **Phase 1 — Foundation + Core (Triển khai ngay)**
1. Foundation files (main.py, config, requirements, GEMINI.md, README.md, bat files)
2. Core AI Engine (ai_engine.py, key_manager.py, state_manager.py)
3. Core Automation (action_executor.py, screen_analyzer.py, workflow_models.py)
4. UI Foundation (theme.py, main_window.py)
5. AI Chat Panel (chat_panel.py) — Module đầu tiên hoạt động
6. Automation Panel (automation_panel.py) — Module desktop automation
7. Settings Dialog (settings_dialog.py)

### **Phase 2 — Workflow Engine (Sau Phase 1)**
8. Workflow Runner (workflow_runner.py)
9. Visual Workflow Editor (workflow_editor.py)
10. File Processor (file_processor.py, file_panel.py)
11. Example workflows

### **Phase 3 — Advanced Features (Mở rộng)**
12. Scheduler (scheduler.py)
13. Log viewer (log_viewer.py)
14. Build exe (build_exe.bat, .spec file)
15. Advanced AI features (multi-agent, function calling chains)

---

## ✅ Verification Plan

### Automated Tests
```powershell
# Chạy ứng dụng
python main.py

# Test AI engine
python -c "from core.ai_engine import GeminiAIEngine; e = GeminiAIEngine(); print(e.chat('Xin chào'))"
```

### Manual Verification
- Mở app → kiểm tra giao diện hiển thị đúng theme
- Chat với AI → kiểm tra nhận/gửi tin nhắn
- Tạo macro → record → play back
- Chụp screenshot → AI phân tích
- Save/Load workflow JSON

---

## Open Questions

> [!IMPORTANT]
> 1. **Persona AI**: AI Claw nên có persona gì? (Trợ lý chuyên nghiệp / Bạn bè thân thiện / Kỹ thuật viên)
> 2. **Ngôn ngữ giao diện**: Toàn bộ tiếng Việt hay song ngữ Việt-Anh?
> 3. **System tray**: Có cần chạy nền (minimize to tray) để chờ hotkey không?
