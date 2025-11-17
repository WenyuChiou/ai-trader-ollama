@echo off
REM Setup Daily Upload Task (Run as Administrator)
REM This batch file should be run as administrator to set up daily data upload to Railway

echo ================================================
echo   AI-Trader Daily Upload Setup
echo ================================================
echo.
echo This will set up a daily task to upload local data to Railway.
echo The task will run automatically every day at a specified time.
echo.
echo IMPORTANT: This script must be run as Administrator!
echo.
pause

powershell -ExecutionPolicy Bypass -File "%~dp0schedule_daily_upload_only.ps1"

pause
