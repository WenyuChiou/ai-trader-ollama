@echo off
REM Setup Railway Daily Upload Task (Run as Administrator)
REM This batch file will request admin privileges and run the PowerShell setup script

echo ================================================
echo   Railway Daily Upload Task Setup
echo ================================================
echo.
echo This will set up a daily task to upload data to Railway
echo Task will run at 18:00 (6 PM) on weekdays only
echo.

REM Get the script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%.."
cd /d "%PROJECT_ROOT%"

REM Run PowerShell script with admin privileges
powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"%SCRIPT_DIR%setup_railway_task.ps1\" -RailwayURL \"https://web-production-b42d6.up.railway.app\" -Time \"18:00\" -WeekdaysOnly' -Verb RunAs"

echo.
echo Please follow the prompts in the Administrator PowerShell window
echo.
pause

