@echo off
REM AI Trader - Cloudflare Tunnel Task Wrapper
REM Used by Task Scheduler to start tunnel after backend is ready
REM Waits for backend health check before starting tunnel

cd /d "%~dp0.."

set "LOG_DIR=%CD%\logs"
set "LOG_FILE=%LOG_DIR%\tunnel_task.log"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

echo [%date% %time%] Tunnel wrapper starting... >> "%LOG_FILE%"

REM Wait for backend to be ready (up to 120 seconds)
set /a RETRIES=0
set /a MAX_RETRIES=24

:wait_loop
curl -s http://localhost:8000/api/health >nul 2>&1
if not errorlevel 1 goto :backend_ready

set /a RETRIES+=1
if %RETRIES% geq %MAX_RETRIES% (
    echo [%date% %time%] ERROR: Backend not ready after 120s, starting tunnel anyway >> "%LOG_FILE%"
    goto :start_tunnel
)

echo [%date% %time%] Waiting for backend... attempt %RETRIES%/%MAX_RETRIES% >> "%LOG_FILE%"
timeout /t 5 /nobreak >nul
goto :wait_loop

:backend_ready
echo [%date% %time%] Backend is ready >> "%LOG_FILE%"

:start_tunnel
echo [%date% %time%] Starting Cloudflare tunnel... >> "%LOG_FILE%"

REM Check if named tunnel is configured
if exist "%CD%\config\tunnel_config.json" (
    echo [%date% %time%] Using named tunnel >> "%LOG_FILE%"
    cloudflared tunnel run ai-trader >> "%LOG_FILE%" 2>&1
) else (
    echo [%date% %time%] WARNING: Named tunnel not configured, using ad-hoc >> "%LOG_FILE%"
    cloudflared tunnel --url http://localhost:8000 >> "%LOG_FILE%" 2>&1
)

echo [%date% %time%] Tunnel process exited >> "%LOG_FILE%"
