@echo off
echo ========================================
echo AI Trader - Start Cloudflare Tunnel
echo ========================================
echo.

REM Check if cloudflared is installed
where cloudflared >nul 2>&1
if errorlevel 1 (
    echo ERROR: cloudflared not found!
    echo.
    echo Please install Cloudflare Tunnel:
    echo   winget install --id Cloudflare.cloudflared
    echo.
    echo Or download from: https://github.com/cloudflare/cloudflared/releases
    pause
    exit /b 1
)

REM Check if backend is running
echo Checking if backend is running on localhost:8000...
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo WARNING: Backend does not seem to be running!
    echo Please start the backend first: scripts\start_backend_local.bat
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

echo.
echo ========================================
echo Starting Cloudflare Tunnel...
echo ========================================
echo.
echo IMPORTANT: Copy the Tunnel URL shown below!
echo.
echo Then set it as API_BASE_URL in Streamlit Cloud:
echo   1. Go to your Streamlit Cloud app settings
echo   2. Add Secret: API_BASE_URL = <your-tunnel-url>
echo.
echo Press Ctrl+C to stop the tunnel
echo ========================================
echo.

cloudflared tunnel --url http://localhost:8000

pause

