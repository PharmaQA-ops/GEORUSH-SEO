@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pip install pyinstaller
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm GEORUSH-SEO.spec
if exist "dist\GEORUSH-SEO.exe" (
  copy /Y "dist\GEORUSH-SEO.exe" ".\GEORUSH-SEO.exe" >nul
  echo.
  echo GEORUSH-SEO.exe created successfully.
) else (
  echo.
  echo Build failed. Check the output above.
)
pause
endlocal
