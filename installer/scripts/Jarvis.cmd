@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Jarvis Python environment was not found.
  echo Try reinstalling Jarvis.
  pause
  exit /b 1
)

".venv\Scripts\python.exe" "src\ui_app.py"
