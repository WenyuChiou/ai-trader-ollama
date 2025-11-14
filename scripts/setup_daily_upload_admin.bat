@echo off
REM Setup Daily Upload Task with Admin Rights
REM This batch file will request admin rights and run the PowerShell script

echo ================================================
echo   AI-Trader Daily Upload Setup (Admin Required)
echo ================================================
echo.
echo This will create a Windows scheduled task to upload data daily.
echo Admin rights are required to create scheduled tasks.
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with admin rights
    echo.
    powershell -ExecutionPolicy Bypass -File "%~dp0schedule_daily_upload_only.ps1"
) else (
    echo [INFO] Requesting admin rights...
    echo.
    REM Re-run with admin rights
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

pause

