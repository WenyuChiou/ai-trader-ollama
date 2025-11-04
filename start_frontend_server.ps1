# 启动前端服务器脚本
# 确保在正确的目录启动

$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$FrontendDir = Join-Path $ScriptRoot "frontend"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  启动前端服务器" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $FrontendDir)) {
    Write-Host "错误: frontend 目录不存在!" -ForegroundColor Red
    Write-Host "路径: $FrontendDir" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

$MonitorFile = Join-Path $FrontendDir "monitor.html"
if (-not (Test-Path $MonitorFile)) {
    Write-Host "错误: monitor.html 文件不存在!" -ForegroundColor Red
    Write-Host "路径: $MonitorFile" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "前端目录: $FrontendDir" -ForegroundColor Green
Write-Host "监控文件: $MonitorFile" -ForegroundColor Green
Write-Host "文件存在: $(Test-Path $MonitorFile)" -ForegroundColor Green
Write-Host ""
Write-Host "启动服务器在端口 8080..." -ForegroundColor Cyan
Write-Host "访问地址: http://localhost:8080/monitor.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "按 Ctrl+C 停止服务器" -ForegroundColor Yellow
Write-Host ""

# 切换到前端目录
Set-Location $FrontendDir

# 启动服务器
python -m http.server 8080

Write-Host ""
Write-Host "服务器已停止" -ForegroundColor Yellow
Read-Host "Press Enter to exit"

