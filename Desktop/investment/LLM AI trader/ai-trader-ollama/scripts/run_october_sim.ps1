# 运行10月历史数据模拟（从backend目录运行）
# Usage: cd backend; .\scripts\run_october_sim.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Split-Path -Parent $ScriptDir

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  10月历史数据模拟" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# 检查后端API
Write-Host "[检查] 后端API状态..." -ForegroundColor Cyan
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/system/info" -Method GET -TimeoutSec 2 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✓ 后端API运行中" -ForegroundColor Green
    }
} catch {
    Write-Host "  ✗ 后端API未运行！" -ForegroundColor Red
    Write-Host "  请先启动后端API" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "模拟说明:" -ForegroundColor Yellow
Write-Host "  • 每5分钟模拟一天（10月共22个交易日）" -ForegroundColor White
Write-Host "  • 前端会自动显示更新" -ForegroundColor White
Write-Host "  • 按 Ctrl+C 可随时停止" -ForegroundColor White
Write-Host ""
Write-Host "前端地址: http://localhost:8080/monitor.html" -ForegroundColor Green
Write-Host ""

# 运行模拟脚本
Set-Location $BackendDir
python scripts\simulate_october_history.py

Write-Host ""
Write-Host "模拟完成或已停止" -ForegroundColor Yellow

