@echo off
chcp 65001 >nul 2>&1
title AI Claw - Tro Ly Tu Dong Hoa Thong Minh
cd /d "%~dp0"
python main.py
if errorlevel 1 (
    echo.
    echo [LOI] Ung dung da ket thuc voi loi. Xem error_log.txt de biet chi tiet.
    pause
)
