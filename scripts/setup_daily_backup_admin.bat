@echo off
REM Setup Daily Backup Scheduled Task (Admin Required)
REM This batch file runs the PowerShell script with administrator privileges

echo ================================================
echo   Daily Backup Setup
echo ================================================
echo.
echo This script requires administrator privileges.
echo Please click "Yes" when prompted by UAC.
echo.

REM Get the directory where this batch file is located
set "SCRIPT_DIR=%~dp0"

REM Run PowerShell script with administrator privileges
powershell -ExecutionPolicy Bypass -Command "Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File \"%SCRIPT_DIR%setup_daily_backup.ps1\"' -Verb RunAs -Wait"

pause

