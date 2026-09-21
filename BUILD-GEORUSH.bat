@echo off
setlocal
cd /d "%~dp0"
title Build GEORUSH SEO v1.0.0

echo ==========================================
echo      GEORUSH SEO v1.0.0 - BUILD
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" goto CREATE_VENV

.venv\Scripts\python.exe -m pip --version >nul 2>&1
if errorlevel 1 (
  echo Existing virtual environment has no working pip.
  echo Recreating .venv...
  rmdir /S /Q ".venv"
  goto CREATE_VENV
)
goto INSTALL

:CREATE_VENV
echo Creating clean Python virtual environment...
python -m venv .venv
if errorlevel 1 (
  echo ERROR: Could not create virtual environment.
  echo Install Python 3.11+ and enable Add Python to PATH.
  pause
  exit /b 1
)

:INSTALL
echo Bootstrapping pip...
.venv\Scripts\python.exe -m ensurepip --upgrade >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python ensurepip failed.
  pause
  exit /b 1
)

echo Upgrading pip...
.venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto FAIL

echo Installing GEORUSH dependencies...
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto FAIL

echo Installing PyInstaller...
.venv\Scripts\python.exe -m pip install pyinstaller
if errorlevel 1 goto FAIL

echo Building Windows EXE...
.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm GEORUSH-SEO.spec
if errorlevel 1 goto FAIL

if exist "dist\GEORUSH-SEO.exe" (
  copy /Y "dist\GEORUSH-SEO.exe" ".\GEORUSH-SEO.exe" >nul
  echo.
  echo ==========================================
  echo BUILD SUCCESSFUL
  echo dist\GEORUSH-SEO.exe
  echo ==========================================
  pause
  exit /b 0
)

:FAIL
echo.
echo BUILD FAILED. Review the output above.
pause
exit /b 1
endlocal
