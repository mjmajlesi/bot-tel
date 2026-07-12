@echo off
title Financial Political Bot
echo Running Financial and Political News Bot...
cd /d "%~dp0"
call venv\Scripts\python.exe news_bot.py
pause
