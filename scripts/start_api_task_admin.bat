@echo off
REM Start API using Task Scheduler (with admin rights, no NSSM needed)
REM This batch file will request administrator privileges automatically

echo ================================================
echo   AI Trader API - Task Scheduler Setup
echo ================================================
echo.
echo This script requires administrator privileges.
echo.
echo Press any key to continue (UAC prompt will appear)...
pause >nul

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
    echo.
    REM Run PowerShell script
    powershell -ExecutionPolicy Bypass -File "%~dp0start_api_task_scheduler.ps1"
) else (
    echo [ERROR] Administrator privileges required
    echo.
    echo Please run this script as administrator:
    echo   1. Right-click this file
    echo   2. Select "Run as administrator"
    echo.
    pause
)

