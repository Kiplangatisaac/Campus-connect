@echo off
echo ========================================
echo KyU Campus Connect - Windows Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.11+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Node.js is not installed or not in PATH.
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo All prerequisites found!
echo.

REM Create installation directory
set INSTALL_DIR=%LOCALAPPDATA%\CampusConnect
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

echo Copying files...
xc /E /I /Y "%~dp0..\..\backend" "%INSTALL_DIR%\backend"
xc /E /I /Y "%~dp0..\..\frontend\build" "%INSTALL_DIR%\frontend\build"

echo Creating Python virtual environment...
python -m venv "%INSTALL_DIR%\venv"
call "%INSTALL_DIR%\venv\Scripts\activate.bat"

echo Installing dependencies...
pip install -r "%INSTALL_DIR%\backend\requirements.txt"

echo Creating shortcuts...
echo @echo off > "%INSTALL_DIR%\start.bat"
echo cd /d "%INSTALL_DIR%" >> "%INSTALL_DIR%\start.bat"
echo call venv\Scripts\activate.bat >> "%INSTALL_DIR%\start.bat"
echo cd backend >> "%INSTALL_DIR%\start.bat"
echo start "" http://localhost:8000 >> "%INSTALL_DIR%\start.bat"
echo uvicorn main:app --host 0.0.0.0 --port 8000 >> "%INSTALL_DIR%\start.bat"

echo.
echo Installation complete!
echo.
echo To start Campus Connect:
echo   1. Open Command Prompt
echo   2. Run: "%INSTALL_DIR%\start.bat"
echo   3. Open browser to http://localhost:8000
echo.
echo Or search for "Campus Connect" in Start Menu.
echo.
pause
