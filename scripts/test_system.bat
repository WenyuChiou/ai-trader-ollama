@echo off
REM Complete System Test Suite
REM Runs both backend and frontend tests in sequence
REM Backend tests must pass before frontend tests run

setlocal enabledelayedexpansion

echo ========================================
echo Complete System Test Suite
echo ========================================
echo.
echo This will test both backend and frontend:
echo   1. Backend tests (must pass first)
echo   2. Frontend tests (runs only if backend passes)
echo.
echo You can also run tests separately:
echo   - scripts\test_backend.bat (backend only)
echo   - scripts\test_frontend.bat (frontend only, requires backend running)
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
echo Running complete system tests...
echo.
python scripts\test_system.py

set "EXIT_CODE=%ERRORLEVEL%"

echo.
if %EXIT_CODE%==0 (
    echo ========================================
    echo All system tests passed!
    echo ========================================
    echo.
    echo System is ready to use!
    echo Next steps:
    echo   1. Start backend: scripts\start_backend_auto.bat
    echo   2. Open frontend: frontend\monitor.html
) else (
    echo ========================================
    echo System tests failed!
    echo ========================================
    echo.
    echo Please check the test output above for details.
    echo Run diagnose.bat for troubleshooting help.
)

echo.
pause
exit /b %EXIT_CODE%

