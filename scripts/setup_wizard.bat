@echo off
REM Interactive Setup Wizard
REM Guides users through initial configuration

setlocal enabledelayedexpansion

echo ========================================
echo AI Trader - Setup Wizard
echo ========================================
echo.
echo This wizard will help you configure:
echo   - Admin API Key (ADMIN_SECRET)
echo   - CORS settings (ALLOWED_ORIGINS)
echo   - Environment (development/production)
echo   - Optional API keys (FRED_API_KEY)
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

REM Check virtual environment
if not exist ".venv" (
    echo WARNING: Virtual environment not found
    echo Please run scripts\install.bat first
    echo.
    set /p continue="Continue anyway? (Y/N): "
    if /i not "!continue!"=="Y" (
        exit /b 1
    )
)

REM Run Python wizard script
python scripts\setup_wizard.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
pause
exit /b %EXIT_CODE%

