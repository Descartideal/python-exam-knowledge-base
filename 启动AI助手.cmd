@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "tools\local_assistant\launch.py"
) else (
  python "tools\local_assistant\launch.py"
)
if errorlevel 1 pause
