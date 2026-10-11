@echo off
chcp 65001 >nul
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" "tools\refresh_index.py"
) else (
  python "tools\refresh_index.py"
)
if errorlevel 1 echo 更新失败，请检查 Python 是否可用。
pause
