# Packaging Rules for AI Claw

## PyInstaller Build
- Only build when user explicitly requests with `tạo exe` command
- Use `--onedir` mode (not `--onefile`) for faster startup
- Include all `config/` files as data
- Include `workflows/` and `presets/` directories
- Set `--windowed` flag to hide console window
- Set app icon with `--icon=app_icon.ico`

## Dependencies
- Bundle `google-genai` and all AI dependencies
- FFmpeg is NOT required for this project
- Ensure `mss` screenshot library is bundled correctly on Windows
