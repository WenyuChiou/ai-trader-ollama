@echo off
REM 设置每日数据上传定时任务
REM 需要管理员权限运行

echo ================================================
echo   设置每日数据上传定时任务
echo ================================================
echo.
echo 此脚本将设置每天 18:00（工作日）自动上传数据到 Railway
echo.
echo 注意：需要管理员权限
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [错误] 需要管理员权限！
    echo 请右键点击此文件，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo [信息] 正在设置定时任务...
echo.

powershell -ExecutionPolicy Bypass -File "%~dp0setup_railway_upload_auto.ps1"

if %errorLevel% equ 0 (
    echo.
    echo [成功] 定时任务设置完成！
    echo.
    echo 任务将在每个工作日 18:00 自动运行
    echo.
    echo 验证设置：
    echo   Get-ScheduledTask -TaskName "AI-Trader-Railway-Daily-Upload"
    echo.
    echo 手动测试：
    echo   python scripts\upload_data_to_railway.py
    echo.
) else (
    echo.
    echo [错误] 设置失败，请检查错误信息
    echo.
)

pause

