@echo off
chcp 65001 >nul 2>&1
echo ================================================
echo   AI-Trader 定时任务设置
echo ================================================
echo.
echo 此脚本将创建定时任务，每天 18:00 自动上传数据到 Railway
echo 需要管理员权限
echo.

REM Check for admin rights
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] 已获得管理员权限
    echo.
    cd /d "%~dp0"
    echo [1/2] 删除旧任务（如果存在）...
    powershell -Command "Unregister-ScheduledTask -TaskName 'AI-Trader-Daily-Upload-Only' -Confirm:$false -ErrorAction SilentlyContinue"
    echo [OK] 旧任务已删除
    echo.
    echo [2/2] 创建新定时任务...
    powershell -ExecutionPolicy Bypass -File "scripts\setup_daily_upload_simple.ps1"
    echo.
    echo ================================================
    echo   设置完成！
    echo ================================================
    echo.
    echo 定时任务详情:
    powershell -Command "Get-ScheduledTask -TaskName 'AI-Trader-Daily-Upload-Only' -ErrorAction SilentlyContinue | Format-List TaskName, State, NextRunTime"
    echo.
    echo 任务将在每个工作日 18:00 自动运行
    echo.
) else (
    echo [INFO] 正在请求管理员权限...
    echo.
    REM Re-run with admin rights
    powershell -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

pause

