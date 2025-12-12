@echo off
REM Quick Start Script
REM Starts backend and frontend with verification

setlocal enabledelayedexpansion

echo ========================================
echo AI Trader - Quick Start
echo ========================================
echo.
echo This script will:
echo   1. Check environment
echo   2. Start Ollama (if needed)
echo   3. Start backend API
echo   4. Verify backend is ready
echo   5. Open frontend in browser
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

REM Step 2: Check virtual environment
echo [2/6] Checking virtual environment...
if not exist ".venv" (
    echo ERROR: Virtual environment not found
    echo Please run: scripts\install.bat first
    pause
    exit /b 1
)
echo Virtual environment found
echo.

REM Step 3: Check Ollama
echo [3/6] Checking Ollama service...
python -c "import requests; r = requests.get('http://localhost:11434/api/version', timeout=2); exit(0 if r.status_code == 200 else 1)" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama service is not running
    echo Please start Ollama in a separate terminal: ollama serve
    echo.
    set /p continue="Continue anyway? (Y/N): "
    if /i not "!continue!"=="Y" (
        exit /b 1
    )
) else (
    echo Ollama service is running
)
echo.

REM Step 4: Check port 8000
echo [4/6] Checking port 8000...
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo Port 8000 is already in use
    echo Options:
    echo   1. Stop existing process and use port 8000
    echo   2. Use a different port (8001)
    echo   3. Exit
    echo.
    set /p choice="Enter choice (1/2/3): "
    
    if "!choice!"=="1" (
        echo Stopping process on port 8000...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
            taskkill /F /PID %%a >nul 2>&1
        )
        set "PORT=8000"
    ) else if "!choice!"=="2" (
        set "PORT=8001"
    ) else (
        exit /b 0
    )
) else (
    set "PORT=8000"
    echo Port 8000 is available
)
echo.

REM Step 5: Start backend
echo [5/6] Starting backend API server...
echo Starting backend in background window...
start "AI Trader Backend" cmd /k "cd /d %~dp0.. && call .venv\Scripts\activate.bat && cd backend && python -m uvicorn src.api.server:app --host 0.0.0.0 --port %PORT% --reload"

echo Waiting for backend to start (30 seconds max)...
timeout /t 2 /nobreak >nul

REM Wait for backend to be ready
set "BACKEND_READY=0"
for /L %%i in (1,1,30) do (
    python -c "import requests; r = requests.get('http://localhost:%PORT%/api/health', timeout=2); exit(0 if r.status_code == 200 else 1)" >nul 2>&1
    if not errorlevel 1 (
        set "BACKEND_READY=1"
        echo Backend is ready!
        goto :backend_ready
    )
    timeout /t 1 /nobreak >nul
    if %%i==5 echo   Still waiting... (5s)
    if %%i==10 echo   Still waiting... (10s)
    if %%i==15 echo   Still waiting... (15s)
    if %%i==20 echo   Still waiting... (20s)
    if %%i==25 echo   Still waiting... (25s)
)

:backend_ready
if "!BACKEND_READY!"=="0" (
    echo ERROR: Backend failed to start within 30 seconds
    echo Please check the backend window for errors
    pause
    exit /b 1
)

REM Step 6: Verify backend and open frontend
echo [6/6] Verifying backend and opening frontend...
python -c "import requests; r = requests.get('http://localhost:%PORT%/api/health'); print('Backend Health:', 'OK' if r.status_code == 200 else 'FAILED')" 2>nul

echo.
echo ========================================
echo System Started Successfully!
echo ========================================
echo.
echo Backend URL: http://localhost:%PORT%
echo API Docs: http://localhost:%PORT%/docs
echo Frontend: Opening in browser...
echo.

REM Open frontend
set "FRONTEND_PATH=%CD%\frontend\monitor.html"
set "FRONTEND_PATH=!FRONTEND_PATH:\=/!"
set "FRONTEND_PATH=file:///!FRONTEND_PATH!"
start "" "!FRONTEND_PATH!"

echo Frontend opened in browser
echo.
echo To stop the backend, close the backend window or press Ctrl+C
echo.
pause

