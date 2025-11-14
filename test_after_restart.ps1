#!/usr/bin/env pwsh
# 重启后功能测试脚本

Write-Host "`n=== 重启后功能测试 ===" -ForegroundColor Cyan

# 1. 检查API状态
Write-Host "`n[1/5] 检查API状态..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/market/status" -TimeoutSec 5
    Write-Host "   ✅ API响应正常" -ForegroundColor Green
    Write-Host "   市场状态: $($status.is_open)" -ForegroundColor White
} catch {
    Write-Host "   ❌ API未响应，请检查API是否运行" -ForegroundColor Red
    exit 1
}

# 2. 检查投资组合
Write-Host "`n[2/5] 检查投资组合..." -ForegroundColor Yellow
try {
    $portfolio = Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/state" -TimeoutSec 5
    Write-Host "   ✅ 投资组合信息获取成功" -ForegroundColor Green
    Write-Host "   现金: `$$([math]::Round($portfolio.cash, 2))" -ForegroundColor White
    Write-Host "   总价值: `$$([math]::Round($portfolio.total_value, 2))" -ForegroundColor White
    Write-Host "   持仓数量: $($portfolio.positions_count)" -ForegroundColor White
} catch {
    Write-Host "   ❌ 无法获取投资组合信息" -ForegroundColor Red
}

# 3. 检查订单状态
Write-Host "`n[3/5] 检查订单状态..." -ForegroundColor Yellow
try {
    $trades = Invoke-RestMethod -Uri "http://localhost:8000/api/trades/recent?limit=20" -TimeoutSec 5
    $pending = ($trades.trades | Where-Object { $_.status -eq 'PENDING' }).Count
    $filled = ($trades.trades | Where-Object { $_.status -eq 'FILLED' }).Count
    Write-Host "   ✅ 订单信息获取成功" -ForegroundColor Green
    Write-Host "   PENDING订单: $pending" -ForegroundColor $(if ($pending -eq 0) { 'Green' } else { 'Yellow' })
    Write-Host "   FILLED订单: $filled" -ForegroundColor Green
    
    if ($pending -gt 0) {
        Write-Host "   ⚠️  发现 $pending 个PENDING订单（可能是旧的订单）" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ❌ 无法获取订单信息" -ForegroundColor Red
}

# 4. 运行一次交易循环测试
Write-Host "`n[4/5] 运行交易循环测试..." -ForegroundColor Yellow
Write-Host "   提示: 这将执行一次完整的交易循环（约60-100秒）" -ForegroundColor White
$response = Read-Host "   是否现在执行？(Y/N)"
if ($response -eq 'Y' -or $response -eq 'y') {
    try {
        Write-Host "   正在执行交易循环..." -ForegroundColor White
        $result = Invoke-RestMethod -Uri "http://localhost:8000/api/trading/execute-trade" -Method POST -TimeoutSec 120
        Write-Host "   ✅ 交易循环执行成功" -ForegroundColor Green
        Write-Host "   订单数量: $($result.placed_orders.Count)" -ForegroundColor White
    } catch {
        Write-Host "   ❌ 交易循环执行失败: $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "   跳过交易循环测试" -ForegroundColor Yellow
}

# 5. 验证修复
Write-Host "`n[5/5] 验证修复..." -ForegroundColor Yellow
Write-Host "   请检查以下项目:" -ForegroundColor White
Write-Host "   1. 新创建的订单状态应该是FILLED（不是PENDING）" -ForegroundColor White
Write-Host "   2. BUY订单不会超过可用现金" -ForegroundColor White
Write-Host "   3. SELL订单不会超过持仓数量" -ForegroundColor White
Write-Host "   4. 日志中显示持仓详细信息" -ForegroundColor White

Write-Host "`n=== 测试完成 ===" -ForegroundColor Green
Write-Host "`n详细测试指南请查看: docs/TESTING_GUIDE_AFTER_RESTART.md" -ForegroundColor Cyan

