@echo off
REM Test Full Stack: Backend + Frontend Integration
REM This script tests if the BAT files can properly start the backend and connect to frontend

setlocal enabledelayedexpansion

echo ========================================
echo Full Stack Integration Test
echo ========================================
echo.

REM Step 1: Check if backend is already running
echo [1/5] Checking if backend is already running...
netstat -ano | findstr ":8000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo WARNING: Port 8000 is already in use
    echo.
    echo Options:
    echo   1. Stop existing process and start fresh
    echo   2. Use existing backend (skip start)
    echo   3. Exit
    echo.
    set /p choice="Enter choice (1/2/3): "
    
    if "!choice!"=="1" (
        echo Stopping existing process...
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000" ^| findstr "LISTENING"') do (
            taskkill /F /PID %%a >nul 2>&1
        )
        echo Process stopped
        set "SKIP_START=0"
    ) else if "!choice!"=="2" (
        set "SKIP_START=1"
        echo Using existing backend
    ) else (
        echo Exiting...
        exit /b 0
    )
) else (
    set "SKIP_START=0"
    echo Port 8000 is available
)
echo.

REM Step 2: Start backend if needed
if "!SKIP_START!"=="0" (
    echo [2/5] Starting backend server...
    echo.
    echo Starting backend in background window...
    echo You should see a new window with the backend server.
    echo.
    
    REM Start backend in a new window
    start "AI Trader Backend" cmd /k "cd /d %~dp0.. && scripts\start_backend_auto.bat"
    
    echo Waiting for backend to start (30 seconds max)...
    timeout /t 2 /nobreak >nul
    
    REM Wait for backend to be ready
    set "BACKEND_READY=0"
    for /L %%i in (1,1,30) do (
        python -c "import requests; r = requests.get('http://localhost:8000/api/health', timeout=2); exit(0 if r.status_code == 200 else 1)" >nul 2>&1
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
) else (
    echo [2/5] Skipping backend start (using existing)
)

echo.

REM Step 3: Test backend API endpoints
echo [3/5] Testing backend API endpoints...
echo.

python -c "import requests; r = requests.get('http://localhost:8000/api/health'); print('Health Check:', 'OK' if r.status_code == 200 else 'FAILED')" 2>nul
if errorlevel 1 (
    echo ERROR: Failed to test health endpoint
    echo Make sure Python requests library is installed: pip install requests
    pause
    exit /b 1
)

python -c "import requests; r = requests.get('http://localhost:8000/api/market/is-open'); print('Market Status:', 'OK' if r.status_code == 200 else 'FAILED')" 2>nul

python -c "import requests; r = requests.get('http://localhost:8000/'); print('Root Endpoint:', 'OK' if r.status_code == 200 else 'FAILED')" 2>nul

echo.

REM Step 4: Test frontend files
echo [4/5] Checking frontend files...
if exist "frontend\monitor.html" (
    echo [OK] monitor.html exists
) else (
    echo [ERROR] monitor.html not found
    pause
    exit /b 1
)

if exist "frontend\index.html" (
    echo [OK] index.html exists
) else (
    echo [WARNING] index.html not found
)

if exist "frontend\config.js" (
    echo [OK] config.js exists
) else (
    echo [WARNING] config.js not found
)

echo.

REM Step 5: Open frontend in browser
echo [5/5] Opening frontend in browser...
echo.
echo Backend URL: http://localhost:8000
echo Frontend URL: file:///%CD:\=/%/frontend/monitor.html
echo.
echo Opening frontend in default browser...
echo.

REM Get absolute path and convert to file:// URL
set "FRONTEND_PATH=%CD%\frontend\monitor.html"
set "FRONTEND_PATH=!FRONTEND_PATH:\=/!"
set "FRONTEND_PATH=file:///!FRONTEND_PATH!"

start "" "!FRONTEND_PATH!"

echo ========================================
echo Test Summary
echo ========================================
echo.
echo Backend Status: Running on http://localhost:8000
echo Frontend: Opened in browser
echo.
echo Next Steps:
echo   1. Check the browser - frontend should load
echo   2. Verify frontend can connect to backend API
echo   3. Check backend window for any errors
echo   4. Test API endpoints in browser: http://localhost:8000/docs
echo.
echo To stop the backend:
echo   - Close the backend window, or
echo   - Press Ctrl+C in the backend window
echo.
echo ========================================
echo Test completed!
echo ========================================
echo.
pause

