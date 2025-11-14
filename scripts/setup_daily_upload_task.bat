@echo off
REM Setup Daily Upload Task - Easy Method
REM This batch file will request admin rights and create the scheduled task

echo ================================================
echo   AI-Trader Daily Upload Task Setup
echo ================================================
echo.
echo This will create a Windows scheduled task to upload data daily at 18:00.
echo Admin rights are required to create scheduled tasks.
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with admin rights
    echo.
    cd /d "%~dp0.."
    powershell -ExecutionPolicy Bypass -File "%~dp0setup_daily_upload_simple.ps1"
) else (
    echo [INFO] Requesting admin rights...
    echo.
    REM Re-run with admin rights
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
echo ================================================
echo   Setup Complete!
echo ================================================
echo.
pause

