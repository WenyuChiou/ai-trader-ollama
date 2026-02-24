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

REM Determine tunnel mode: Named Tunnel (preferred) or Ad-Hoc (fallback)
set "TUNNEL_CONFIG=%~dp0..\config\tunnel_config.json"

if exist "%TUNNEL_CONFIG%" (
    echo.
    echo ========================================
    echo Starting Named Tunnel...
    echo ========================================
    echo.
    echo Using persistent named tunnel with stable URL.
    echo The tunnel URL is configured in config\tunnel_config.json.
    echo.
    echo Press Ctrl+C to stop the tunnel
    echo ========================================
    echo.

    REM Named tunnel uses the config.yml in %USERPROFILE%\.cloudflared\
    cloudflared tunnel run ai-trader
) else (
    echo.
    echo ========================================
    echo WARNING: Named tunnel not configured!
    echo ========================================
    echo.
    echo Falling back to ad-hoc tunnel (random URL, changes on restart).
    echo.
    echo To set up a persistent named tunnel with a stable URL, run:
    echo   powershell -ExecutionPolicy Bypass -File scripts\setup_cloudflare_tunnel.ps1
    echo.
    echo IMPORTANT: Copy the Tunnel URL shown below!
    echo.
    echo Press Ctrl+C to stop the tunnel
    echo ========================================
    echo.

    cloudflared tunnel --url http://localhost:8000
)

pause
