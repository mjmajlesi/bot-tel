@echo off
title AI News Bot - Daily Persian Digest
echo ========================================
echo   AI News Bot - Daily Persian Digest
echo ========================================
echo.

cd /d "%~dp0"
call venv\Scripts\python.exe news_bot.py
pause

echo.
echo Press any key to exit...
pause >nul
