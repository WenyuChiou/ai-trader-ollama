# Simple API Test Script
Write-Host "`n=== API Test ===" -ForegroundColor Cyan

# Test 1: API Status
Write-Host "`n[1] Testing API Status..." -ForegroundColor Yellow
try {
    $status = Invoke-RestMethod -Uri "http://localhost:8000/api/market/status" -TimeoutSec 5
    Write-Host "   OK - API is responding" -ForegroundColor Green
    Write-Host "   Market open: $($status.is_open)" -ForegroundColor White
} catch {
    Write-Host "   FAILED - API not responding" -ForegroundColor Red
    exit 1
}

# Test 2: Portfolio
Write-Host "`n[2] Testing Portfolio..." -ForegroundColor Yellow
try {
    $portfolio = Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/state" -TimeoutSec 5
    Write-Host "   OK - Portfolio loaded" -ForegroundColor Green
    Write-Host "   Cash: `$$([math]::Round($portfolio.cash, 2))" -ForegroundColor White
    Write-Host "   Total Value: `$$([math]::Round($portfolio.total_value, 2))" -ForegroundColor White
    Write-Host "   Positions: $($portfolio.positions_count)" -ForegroundColor White
} catch {
    Write-Host "   FAILED - Cannot get portfolio" -ForegroundColor Red
}

# Test 3: Recent Trades
Write-Host "`n[3] Testing Recent Trades..." -ForegroundColor Yellow
try {
    $trades = Invoke-RestMethod -Uri "http://localhost:8000/api/trades/recent?limit=10" -TimeoutSec 5
    $pending = ($trades.trades | Where-Object { $_.status -eq 'PENDING' }).Count
    $filled = ($trades.trades | Where-Object { $_.status -eq 'FILLED' }).Count
    Write-Host "   OK - Trades loaded" -ForegroundColor Green
    Write-Host "   PENDING: $pending" -ForegroundColor $(if ($pending -eq 0) { 'Green' } else { 'Yellow' })
    Write-Host "   FILLED: $filled" -ForegroundColor Green
} catch {
    Write-Host "   FAILED - Cannot get trades" -ForegroundColor Red
}

Write-Host "`n=== Test Complete ===" -ForegroundColor Green
Write-Host "`nNext Steps:" -ForegroundColor Cyan
Write-Host "1. Open frontend: http://localhost:8080/monitor.html" -ForegroundColor White
Write-Host "2. Click 'Run Analysis' or 'Start Trading'" -ForegroundColor White
Write-Host "3. Check that all new orders are FILLED (not PENDING)" -ForegroundColor White
Write-Host "4. Check that cash usage is correct" -ForegroundColor White
Write-Host "5. Check that sell orders don't exceed position quantities" -ForegroundColor White

