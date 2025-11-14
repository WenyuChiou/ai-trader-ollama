@echo off
REM Remove Daily Upload Task (Admin Required)
echo ================================================
echo   Remove AI-Trader Daily Upload Task
echo ================================================
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with admin rights
    echo.
    echo Removing task: AI-Trader-Daily-Upload-Only
    powershell -Command "Unregister-ScheduledTask -TaskName 'AI-Trader-Daily-Upload-Only' -Confirm:$false -ErrorAction SilentlyContinue"
    if %errorLevel% == 0 (
        echo [SUCCESS] Task removed!
    ) else (
        echo [INFO] Task may not exist or already removed
    )
) else (
    echo [INFO] Requesting admin rights...
    echo.
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

echo.
pause

