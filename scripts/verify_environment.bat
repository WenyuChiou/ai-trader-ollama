@echo off
REM Environment Verification Script
REM Checks all prerequisites and installed components

setlocal enabledelayedexpansion

echo ========================================
echo Environment Verification
echo ========================================
echo.
echo This script checks:
echo   - Python installation and version
echo   - Ollama installation and service
echo   - Ollama model availability
echo   - Virtual environment
echo   - Python packages
echo   - Port availability
echo   - Directories and config files
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

REM Run Python verification script
python scripts\verify_environment.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %EXIT_CODE%

