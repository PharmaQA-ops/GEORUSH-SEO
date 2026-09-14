@echo off
setlocal
cd /d "%~dp0"
title Install GEORUSH SEO

echo ==========================================
echo       GEORUSH SEO - Desktop Setup
echo ==========================================
echo.
echo This setup installs GEORUSH only on this laptop.
echo.
python --version >nul 2>&1
if errorlevel 1 (
    echo Python was not found.
    echo.
    echo Please install Python 3.11 or newer, then run this file again.
    echo During Python setup, enable "Add Python to PATH".
    start "" "https://www.python.org/downloads/windows/"
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating GEORUSH environment...
    python -m venv .venv
)

echo Installing GEORUSH components...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo Setup failed. Please contact the GEORUSH administrator.
    pause
    exit /b 1
)

echo.
echo Setup complete.
echo You can now double-click GEORUSH-SEO-START.bat.
pause
endlocal
