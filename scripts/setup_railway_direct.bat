@echo off
REM Direct Railway Upload Setup - Run as Administrator
REM This script sets up daily upload without exposing Railway URL in documentation

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

REM Check Railway URL configuration
python -c "from scripts.config_railway import get_railway_url; url = get_railway_url(); exit(0 if url else 1)" >nul 2>&1
if %errorLevel% neq 0 (
    echo [INFO] Railway URL not configured. Configuring now...
    echo.
    echo Please enter your Railway URL:
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
)

echo.
echo Setting up daily upload task...
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
echo Daily upload task has been scheduled.
echo Railway URL is configured privately (not in git).
echo.
pause

