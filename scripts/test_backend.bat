@echo off
REM Backend Test Suite
REM Tests backend core functionality without frontend dependency

setlocal enabledelayedexpansion

echo ========================================
echo Backend Test Suite
echo ========================================
echo.
echo This script tests backend functionality:
echo   - Ollama connection and model
echo   - Backend API modules
echo   - Agent system
echo   - Toolbox
echo   - Trading cycle
echo   - Logging system
echo.
echo Frontend tests are separate (run test_frontend.bat after this)
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

REM Run Python test script
echo Running backend tests...
echo.
python scripts\test_backend.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE%==0 (
    echo ========================================
    echo Backend tests completed successfully!
    echo ========================================
    echo.
    echo Next steps:
    echo   1. If backend API is not running, start it: scripts\start_backend_auto.bat
    echo   2. Run frontend tests: scripts\test_frontend.bat
    echo   3. Or run full system test: scripts\test_system.bat
) else (
    echo ========================================
    echo Backend tests failed!
    echo ========================================
    echo.
    echo Please fix backend issues before testing frontend.
    echo Run diagnose.bat for troubleshooting help.
)

echo.
pause
exit /b %EXIT_CODE%

