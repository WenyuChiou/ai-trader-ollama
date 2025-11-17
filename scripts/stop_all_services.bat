@echo off
echo ========================================
echo 停止所有 AI Trader 服务
echo ========================================
echo.

echo [1] 查找并停止 uvicorn 进程（后端 API 服务器）...
taskkill /F /FI "WINDOWTITLE eq *uvicorn*" 2>nul
taskkill /F /FI "WINDOWTITLE eq *API Server*" 2>nul
taskkill /F /FI "WINDOWTITLE eq *Backend*" 2>nul

echo.
echo [2] 查找并停止 Python HTTP 服务器（前端）...
taskkill /F /FI "WINDOWTITLE eq *Frontend*" 2>nul
taskkill /F /FI "WINDOWTITLE eq *http.server*" 2>nul

echo.
echo [3] 查找并停止占用端口 8000 的进程（后端）...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :8000 ^| findstr LISTENING') do (
    echo   停止进程 PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo [4] 查找并停止占用端口 3000 的进程（前端）...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :3000 ^| findstr LISTENING') do (
    echo   停止进程 PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo.
echo ========================================
echo 所有服务已停止
echo ========================================
echo.
pause
