@echo off
cd /d "%~dp0"
echo [SYSTEM] Starting AI Hedge Fund Server...
call .venv\Scripts\python.exe main.py >> server.log 2>&1
