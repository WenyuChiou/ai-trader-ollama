@echo off
REM Setup Daily Upload Task (Simple Version - Run as Administrator)
REM This batch file sets up a daily task to upload data to Railway ONCE per day
REM IMPORTANT: This script must be run as Administrator!

echo ================================================
echo   AI-Trader Daily Upload Setup (Simple)
echo ================================================
echo.
echo This will set up a daily task to upload local data to Railway.
echo The task will run automatically ONCE per day at a specified time.
echo.
echo IMPORTANT: This script must be run as Administrator!
echo.
pause

powershell -ExecutionPolicy Bypass -File "%~dp0setup_daily_upload_simple.ps1"

pause

