# QUY TẮC PHÁT TRIỂN & ĐÓNG GÓI CHO DỰ ÁN AI CLAW

---

## 1. QUY TẮC ĐÓNG GÓI ỨNG DỤNG (.EXE) — BẮT BUỘC TUÂN THỦ

1. **KHÔNG TỰ Ý ĐÓNG GÓI KHI CHƯA CÓ YÊU CẦU**:
   - Trong quá trình phát triển, sửa lỗi, cập nhật tính năng: **TUYỆT ĐỐI KHÔNG** tự ý chạy `build_exe.bat` hoặc lệnh PyInstaller khi người dùng chưa yêu cầu bằng lệnh cụ thể.
   - Chỉ kiểm thử mã nguồn bằng cách chạy trực tiếp qua Python hoặc file `run_ai_claw.bat`.

2. **CÁC LỆNH ĐÓNG GÓI ĐƯỢC CHỈ ĐỊNH RÕ RÀNG**:
   - Khi người dùng yêu cầu: **`tạo exe`** → `cmd.exe /c build_exe.bat` → `dist\AIClaw\`
   - Khi người dùng yêu cầu: **`tạo exe zip`** → `cmd.exe /c build_exe.bat zip`

---

## 2. QUY TẮC PHÁT TRIỂN CODE

### 2.1. UTF-8 TOÀN DIỆN
- Mọi file Python phải dùng encoding UTF-8.
- Console output phải cấu hình UTF-8 (`sys.stdout.reconfigure(encoding='utf-8')`).

### 2.2. ERROR HANDLING BẮT BUỘC
- Mọi module phải có `try/except` và ghi log chi tiết (`logger.error(..., exc_info=True)`).
- Crash handler toàn cục đã cấu hình trong `main.py` → ghi `error_log.txt`.
- Khi thêm tính năng mới: **luôn wrap trong try/except**, log lỗi, hiện toast thay vì crash.

### 2.3. THREAD SAFETY — CRITICAL
- **Main thread CHỈ chạy UI** (Qt event loop).
- **Heavy operations PHẢI chạy trên QThread/Worker**:
  - AI API calls → `ChatWorker` (QThread)
  - Model testing → `ModelTestWorker` (QThread)
  - API key health check → `KeyCheckWorker` (QThread)
  - Screenshot capture → OK trên main (nhẹ, ~50ms)
- **Giao tiếp thread ↔ UI qua Qt signals/slots** — KHÔNG trực tiếp gọi UI methods từ worker.
- **processEvents()**: Gọi `QApplication.processEvents()` giữa các vòng lặp nặng (tạo 65+ widgets).

### 2.4. CHỐNG ĐÔNG UI (NOT RESPONDING) — CRITICAL
Đây là vấn đề đã xảy ra nhiều lần. BẮT BUỘC tuân thủ:

```python
# SAI — Block UI thread, gây đơ
def __init__(self):
    self._setup_ui()
    self._load_heavy_data()  # Block main thread!

# ĐÚNG — Defer heavy work sau khi UI hiện
def __init__(self):
    self._setup_ui()
    # KHÔNG gọi _load_data ở đây

def showEvent(self, event):
    super().showEvent(event)
    QTimer.singleShot(50, self._deferred_load)
```

**Checklist chống đơ:**
- `QComboBox.blockSignals(True)` khi thêm nhiều items → `blockSignals(False)` sau.
- KHÔNG gọi DB queries (`get_provider_key_count()`) trong vòng lặp tạo UI.
- Tạo 10+ widgets → dùng `processEvents()` giữa các batch.
- Dialog constructor KHÔNG gọi `_load_data()` — defer sang `showEvent()`.
- `QTimer.singleShot(50, callback)` cho deferred initialization.

### 2.5. API KEY SECURITY
- Không hardcode API key. Đọc từ `.env` hoặc SQLite DB.
- API key luôn được mask khi hiển thị: `...last8chars`.

### 2.6. PATTERN CHUẨN
- Tuân thủ cấu trúc `core/` + `ui/`.
- `core/`: Logic thuần, không import PyQt6.
- `ui/`: Giao diện, import từ `core/`.

---

## 3. CẤU TRÚC DỰ ÁN

```
300AIClaude/
├── main.py                    # Entry point + crash handler
├── core/
│   ├── model_registry.py      # 65 models, 16 providers (singleton)
│   ├── ai_engine.py           # GeminiAIEngine — multi-provider
│   ├── key_manager.py         # SQLite-based API key management
│   ├── screen_analyzer.py     # Screenshot capture + WebP convert
│   ├── state_manager.py       # App state + chat history (SQLite)
│   ├── action_executor.py     # Mouse/keyboard automation
│   ├── image_generator.py     # AI image generation
│   ├── knowledge_base.py      # RAG knowledge base
│   └── workflow_models.py     # Automation workflow definitions
├── ui/
│   ├── theme.py               # Dark/Light themes, 4 density modes
│   ├── main_window.py         # Sidebar + stacked panels
│   ├── chat_panel.py          # Chat UI + screenshot + image
│   ├── settings_dialog.py     # 5 tabs: Models/API/Display/Screenshot/General
│   ├── automation_panel.py    # Automation workflows
│   ├── image_panel.py         # Image generation
│   ├── knowledge_panel.py     # Knowledge base UI
│   ├── log_viewer.py          # Log viewer
│   └── toast.py               # Toast notifications
├── config/                    # Config files
├── output/                    # Generated outputs
├── screenshots/               # Screenshot files
└── workflows/                 # Saved workflows
```

---

## 4. HỆ THỐNG THEME & GIAO DIỆN

### 4.1. Theme
- **Dark Mode** (mặc định): Nền `#0b0f19`, chữ `#f8fafc`
- **Light Mode**: Nền `#ffffff`, chữ `#0f172a`
- Chuyển qua `set_theme('dark'|'light')` → `build_stylesheet()` → `app.setStyleSheet()`
- Accent: Indigo (`#6366f1`) + Cyan (`#06b6d4`)

### 4.2. UI Density & Cỡ chữ (Font Size)
- **UI Density (4 chế độ)**: Material (Mặc định), Compact, Lite Compact, Super Compact
- **Font Size (6 cỡ chữ)**:
  - `small`: Nhỏ (11px)
  - `slightly_small`: Hơi nhỏ (12px)
  - `medium`: Vừa phải (13px — MẶC ĐỊNH)
  - `slightly_large`: Hơi lớn (15px)
  - `large`: Lớn (17px)
  - `extra_large`: Rất lớn (19px)

### 4.3. COLORS Dict — 30 keys
Luôn dùng `COLORS['key']` thay vì hardcode hex:
```python
# SAI
label.setStyleSheet("color: #f8fafc;")

# ĐÚNG — tự động đổi theo theme
label.setStyleSheet(f"color: {COLORS['text_primary']};")
```

**Keys bắt buộc**: `bg_primary`, `bg_surface`, `bg_surface_hover`, `bg_input`, `text_primary`, `text_secondary`, `text_muted`, `accent_primary`, `accent_secondary`, `border`, `border_focus`, `success`, `warning`, `error`, `info`, `sidebar_active`, `sidebar_bg`, `chat_user_bg`, `chat_ai_bg`.

### 4.4. Quy tắc giao diện
- **Title window**: Sử dụng emoji + tên rõ ràng (VD: `"⚙️ Cài đặt — AI Claw Multi-AI"`)
- **Dialog**: Phải có khung `dialogHeader` nền theo theme, nút đóng, hỗ trợ resize nếu nội dung nhiều
- **Font**: Segoe UI, size 12-18px cho tiêu đề, 11-12px cho nội dung
- **Border radius**: 6-10px cho cards/buttons, 4px cho inputs
- **Spacing**: Dùng `setSpacing(8-12)`, `setContentsMargins(12-16, ...)`
- **Card style**: `bg_surface` + border `1px solid` + `border-radius: 10px` + hover effect
- **Badges**: Background `{color}22`, text `{color}`, border `{color}44`, radius `8px`

---

## 5. MODEL REGISTRY — 79 MODELS / 16 PROVIDERS

### 5.1. Providers & Models nổi bật (Cập nhật 2026)
- **Google Gemini (16 models)**:
  - Gemini 3.7 Flash (High / Medium / Low Fast)
  - Gemini 3.6 Flash (High / Medium / Low Fast)
  - Gemini 3.5 Flash (High / Medium / Low Fast)
  - Gemini 3.1 Pro (High / Medium / Low)
  - Gemini 2.0 Flash / Flash Lite, Gemini 1.5 Flash / Pro (Official API)
- **Anthropic Claude (7 models)**:
  - Claude Sonnet 4.6 (Thinking), Claude Opus 4.6 (Thinking), Sonnet 4, Haiku 3.5, Opus 4
- **OpenAI (8 models)**:
  - GPT-OSS 120B (Medium), GPT-4.1 (Mini/Nano), GPT-4o (Mini), o3-mini, o4-mini
- **Smart Model Resolver & 404 Auto-Fallback**:
  - Khi gửi request Google GenAI: Map model qua `GEMINI_MODEL_MAP` và nếu gặp 404 NOT_FOUND thì tự động chuyển sang `gemini-2.0-flash` mà không crash hoặc lặp lỗi 5 lần.

### 5.2. Model Tiers
- 💚 Rẻ nhất (`CHEAPEST`)
- 💙 Cân bằng (`BALANCED`) — Khuyên dùng
- 💜 Giá vừa (`MODERATE`)
- 💛 Tốt nhất (`BEST`)

### 5.3. ModelInfo Fields
```python
ModelInfo(
    id="model-id",           # ID gửi API
    name="Display Name",     # Tên hiển thị
    provider=Provider.XXX,   # Enum provider
    tier=ModelTier.XXX,      # Phân hạng giá
    description="...",       # Mô tả ngắn
    max_context=128000,      # Max tokens
    input_price=0.15,        # $/1M input tokens
    output_price=0.60,       # $/1M output tokens
    speed_rating=4,          # 1-5
    quality_rating=4,        # 1-5
    cost_rating=5,           # 1-5
    supports_vision=True,    # Hỗ trợ ảnh
    supports_tools=True,     # Function calling
    is_recommended=True,     # Khuyên dùng
    release_date="2025-06",  # Tháng phát hành
)
```

---

## 6. SETTINGS DIALOG — 5 TABS

### Tab 1: 🤖 Chọn Mô Hình AI
- Quick select theo tier (4 buttons)
- Provider filter dropdown
- ModelCard widgets (grouped by provider, expandable 3→all)
- Nút 🧪 Test trên mỗi card
- Nút ⭐ Đặt mặc định, 🔄 Tải lại

### Tab 2: 🔑 API Keys
- Thêm/xóa/check keys
- Bảng keys với provider, status, health check

### Tab 3: 💬 Tuỳ chọn Hiển thị
- Theme (Dark/Light)
- Density (Material/Compact/Lite/Super)
- Display mode (Plain/Markdown/HTML)

### Tab 4: 📸 Screenshot
- Monitor selection (Left/Right/Both)
- Image format (WebP/PNG/JPEG)
- Quality slider

### Tab 5: 🔧 Cài đặt chung
- Confirm mode (Auto/Ask First/Always Ask)
- Other preferences

---

## 7. LỖI ĐÃ GẶP & LƯU Ý — PHẢI TRÁNH LẶP LẠI

### 7.1. Lỗi Import thiếu (NameError)
```
NameError: name 'QGroupBox' is not defined  → main_window.py
NameError: name 'QGridLayout' is not defined → knowledge_panel.py
```
**Quy tắc**: Khi dùng bất kỳ Qt widget nào, PHẢI kiểm tra đã import chưa. Danh sách hay quên:
`QGroupBox`, `QGridLayout`, `QScrollArea`, `QSpinBox`, `QSlider`, `QRadioButton`, `QButtonGroup`, `QSizePolicy`

### 7.2. Settings Dialog đơ (Not Responding)
```
Nguyên nhân 1: _load_data() gọi trong constructor → block main thread
Nguyên nhân 2: QComboBox.addItem() trigger signal → _refresh_model_cards() gọi 16 lần
Nguyên nhân 3: get_provider_key_count() DB query x16 trong vòng lặp UI creation
Nguyên nhân 4: Lazy-load dùng removeTab/insertTab → cascade currentChanged
```
**Đã fix bằng**: Deferred loading qua `showEvent()` + `blockSignals()` + `processEvents()`.

### 7.3. DB Migration
```
sqlite3.OperationalError: no such table: gemini_api_keys
```
**Đã fix**: Migration code trong `key_manager.py` tự động chuyển `gemini_api_keys` → `api_keys`.

### 7.4. Thread crash
```
QObject::connect: Cannot queue arguments of type 'QTextCursor'
```
**Quy tắc**: KHÔNG gọi UI methods từ worker thread. Dùng signal → slot.

---

## 8. CHECKLIST TRƯỚC KHI COMMIT

- [ ] Syntax check: `python -c "import ast; ast.parse(open('file.py', encoding='utf-8').read())"`
- [ ] Import check: `python -c "import module_name"`
- [ ] COLORS keys: Tất cả `COLORS['key']` phải tồn tại trong cả COLORS_DARK và COLORS_LIGHT
- [ ] Thread safety: Heavy ops trên QThread, UI methods chỉ trên main thread
- [ ] processEvents(): Có gọi khi tạo 10+ widgets trong vòng lặp
- [ ] blockSignals(): Có dùng khi add items vào QComboBox
- [ ] try/except: Mọi method có thể fail phải wrap
- [ ] Logger: Mọi exception phải log (`logger.error(..., exc_info=True)`)
- [ ] No hardcode colors: Dùng `COLORS['key']` thay vì hex trực tiếp
- [ ] Dialog resize: Dialogs lớn phải có maximize button + size grip
