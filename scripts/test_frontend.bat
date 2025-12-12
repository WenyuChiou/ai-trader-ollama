@echo off
REM Frontend Test Suite
REM Tests frontend connection and integration with backend
REM Requires backend to be running first

setlocal enabledelayedexpansion

echo ========================================
echo Frontend Test Suite
echo ========================================
echo.
echo This script tests frontend functionality:
echo   - Frontend files existence
echo   - Frontend configuration
echo   - CORS configuration
echo   - API endpoint accessibility
echo   - HTML structure
echo.
echo IMPORTANT: Backend must be running first!
echo   Run scripts\test_backend.bat to verify backend
echo   Run scripts\start_backend_auto.bat to start backend
echo.

REM Check if running from project root
if not exist "frontend\monitor.html" (
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

REM Run Python test script
echo Running frontend tests...
echo.
python scripts\test_frontend.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE%==0 (
    echo ========================================
    echo Frontend tests completed successfully!
    echo ========================================
    echo.
    echo Frontend is ready to use!
    echo Open frontend\monitor.html in your browser
) else (
    echo ========================================
    echo Frontend tests failed!
    echo ========================================
    echo.
    echo Please check:
    echo   1. Backend is running (scripts\start_backend_auto.bat)
    echo   2. Frontend files exist (frontend\monitor.html)
    echo   3. Frontend configuration (frontend\config.js)
    echo.
    echo Run diagnose.bat for troubleshooting help.
)

echo.
pause
exit /b %EXIT_CODE%

