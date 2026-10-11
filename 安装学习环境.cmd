@echo off
chcp 65001 >nul
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
python "tools\install_offline.py" --check-platform
if errorlevel 1 goto failed
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
  if errorlevel 1 goto failed
)
".venv\Scripts\python.exe" "tools\install_offline.py"
if errorlevel 1 goto failed
".venv\Scripts\python.exe" "tools\check_environment.py"
if errorlevel 1 goto failed
echo 学习环境准备完成，可运行「运行例题.cmd」。
pause
exit /b 0
:failed
echo 安装失败，请检查 Python 版本、本地安装包和上方报错后重试。此入口不联网。
pause
exit /b 1
