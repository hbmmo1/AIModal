@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ========================================================
echo   BAT DAU DONG GOI AI CLAW (.EXE)
echo ========================================================
python build_exe.py
pause
