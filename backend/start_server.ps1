# 启动 AI Trader API 服务器（前台运行，可以看到所有输出）
# 使用方法: .\start_server.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader API Server" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API Address: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Current Directory: $PWD" -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting server..." -ForegroundColor Cyan
Write-Host ""

# 切换到 backend 目录
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendDir = Join-Path $scriptPath ".." | Resolve-Path
Set-Location $backendDir

# 启动服务器（前台运行）
python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 --reload

Write-Host ""
Write-Host "Server stopped." -ForegroundColor Yellow

