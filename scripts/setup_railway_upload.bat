@echo off
REM Setup Railway Daily Upload Task
REM This script configures Railway URL and sets up daily upload task

echo ================================================
echo   Railway Daily Upload Setup
echo ================================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script must be run as Administrator
    echo Please right-click and select "Run as Administrator"
    pause
    exit /b 1
)

REM Get project root directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

echo Step 1: Configure Railway URL
echo.
echo Please enter your Railway URL (e.g., https://your-app.up.railway.app)
echo.
set /p RAILWAY_URL="Railway URL: "
if "%RAILWAY_URL%"=="" (
    echo [ERROR] Railway URL is required
    pause
    exit /b 1
)
python scripts\config_railway.py "%RAILWAY_URL%"
if %errorLevel% neq 0 (
    echo [ERROR] Failed to configure Railway URL
    pause
    exit /b 1
)

echo.
echo Step 2: Set up daily upload task
echo.
powershell -ExecutionPolicy Bypass -File "scripts\schedule_railway_upload.ps1"

if %errorLevel% neq 0 (
    echo [ERROR] Failed to set up scheduled task
    pause
    exit /b 1
)

echo.
echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo Railway URL has been configured.
echo Daily upload task has been scheduled.
echo.
pause

