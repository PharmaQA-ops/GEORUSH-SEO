@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" "georush_desktop.py"
  exit /b 0
)
if exist "GEORUSH-SEO.exe" (
  start "" "GEORUSH-SEO.exe"
  exit /b 0
)
if exist "pythonw.exe" (
  start "" "pythonw.exe" "georush_desktop.py"
  exit /b 0
)
python "georush_desktop.py"
endlocal
