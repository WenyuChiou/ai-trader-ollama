@echo off
REM Delete and Recreate Daily Upload Task
echo ================================================
echo   Delete and Recreate AI-Trader Daily Upload Task
echo ================================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with admin rights
    echo.
    
    REM Delete existing task
    echo [1/2] Removing existing task (if any)...
    powershell -Command "Unregister-ScheduledTask -TaskName 'AI-Trader-Daily-Upload-Only' -Confirm:$false -ErrorAction SilentlyContinue"
    echo [OK] Old task removed
    echo.
    
    REM Create new task
    echo [2/2] Creating new scheduled task...
    cd /d "%~dp0.."
    powershell -ExecutionPolicy Bypass -File "%~dp0setup_daily_upload_simple.ps1"
    
) else (
    echo [INFO] Requesting admin rights...
    echo.
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
pause

