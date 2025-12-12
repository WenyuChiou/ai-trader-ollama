@echo off
REM System Diagnosis Tool
REM Automatically detects common issues and provides fixes

setlocal enabledelayedexpansion

echo ========================================
echo System Diagnosis Tool
echo ========================================
echo.
echo This tool will check:
echo   - Python installation and version
echo   - Ollama installation and service
echo   - Virtual environment
echo   - Python dependencies
echo   - Port availability
echo   - Configuration files
echo   - Environment setup
echo.

REM Check if running from project root
if not exist "backend\src\api\server.py" (
    echo ERROR: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Run Python diagnosis script
python scripts\diagnose.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %EXIT_CODE%

