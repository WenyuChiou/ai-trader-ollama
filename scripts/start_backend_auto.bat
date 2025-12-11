@echo off
REM Auto Start Backend API Server
REM Automatically handles virtual environment, dependencies, and port conflicts

setlocal enabledelayedexpansion

echo ========================================
echo AI Trader - Backend Auto Start
echo ========================================
echo.

REM Check if running from project root
if not exist "backend\src\api\server.py" (
    echo ERROR: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Step 1: Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)
python --version
echo.

REM Step 2: Check/Create virtual environment
echo [2/6] Checking virtual environment...
if not exist ".venv" (
    echo Virtual environment not found. Creating...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created
) else (
    echo Virtual environment found
)
echo.

REM Step 3: Activate virtual environment
echo [3/6] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Step 4: Check and install dependencies
echo [4/6] Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
    echo Dependencies installed
) else (
    echo Dependencies already installed
)
echo.

REM Step 5: Check port 8000
echo [5/6] Checking port 8000...
netstat -ano | findstr ":8000" >nul 2>&1
if not errorlevel 1 (
    echo WARNING: Port 8000 is already in use
    echo.
    echo Options:
    echo   1. Stop the existing process and use port 8000
    echo   2. Use a different port (8001)
    echo   3. Exit
    echo.
    set /p choice="Enter choice (1/2/3): "
    
    if "!choice!"=="1" (
        echo Stopping process on port 8000...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
            taskkill /F /PID %%a >nul 2>&1
        )
        echo Process stopped
        set "PORT=8000"
    ) else if "!choice!"=="2" (
        set "PORT=8001"
        echo Using port 8001 instead
    ) else (
        echo Exiting...
        exit /b 0
    )
) else (
    set "PORT=8000"
    echo Port 8000 is available
)
echo.

REM Step 6: Start API server
echo [6/6] Starting API server...
echo ========================================
echo API Server starting on port %PORT%
echo API Documentation: http://localhost:%PORT%/docs
echo Health Check: http://localhost:%PORT%/api/health
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port %PORT% --reload

REM If we get here, server stopped
echo.
echo API server stopped
pause

