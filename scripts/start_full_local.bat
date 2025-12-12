@echo off
echo ========================================
echo AI Trader - Full Local Deployment
echo ========================================
echo.
echo This script will:
echo   1. Start the backend API server
echo   2. Start Cloudflare Tunnel
echo.
echo IMPORTANT: Keep both windows open!
echo.
pause

REM Start backend in new window
echo Starting backend...
start "AI Trader Backend" cmd /k "scripts\start_backend_local.bat"

REM Wait for backend to start
echo Waiting for backend to start...
timeout /t 8 /nobreak >nul

REM Start tunnel in new window
echo Starting Cloudflare Tunnel...
start "AI Trader Tunnel" cmd /k "scripts\start_cloudflare_tunnel.bat"

echo.
echo ========================================
echo Both services started!
echo ========================================
echo.
echo Next steps:
echo   1. Copy the Tunnel URL from the Tunnel window
echo   2. Go to Streamlit Cloud app settings
echo   3. Add Secret: API_BASE_URL = <your-tunnel-url>
echo   4. Your Streamlit app will connect automatically
echo.
echo Keep both windows open to keep services running.
echo.
pause

