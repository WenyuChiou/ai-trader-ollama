# Test GitHub Pages Connection
# This script tests if the GitHub Pages website is accessible

Write-Host "`n=== Testing GitHub Pages Connection ===" -ForegroundColor Cyan
Write-Host ""

$url = "https://WenyuChiou.github.io/ai-trader-ollama/monitor.html"

Write-Host "Testing URL: $url" -ForegroundColor Yellow
Write-Host ""

try {
    $response = Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 10
    
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ SUCCESS: Website is accessible!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Status Code: $($response.StatusCode)" -ForegroundColor Green
        Write-Host "Status: $($response.StatusDescription)" -ForegroundColor Green
        Write-Host ""
        Write-Host "🌐 Open in browser:" -ForegroundColor Cyan
        Write-Host "   $url" -ForegroundColor White
        Write-Host ""
        Write-Host "📋 Next steps:" -ForegroundColor Cyan
        Write-Host "   1. Open the URL in your browser" -ForegroundColor White
        Write-Host "   2. Check if the dashboard loads correctly" -ForegroundColor White
        Write-Host "   3. Verify read-only mode is enabled (no trading buttons)" -ForegroundColor White
        Write-Host "   4. Check if data loads from backend API" -ForegroundColor White
        Write-Host ""
    } else {
        Write-Host "⚠️  WARNING: Unexpected status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ ERROR: Cannot connect to website" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Possible causes:" -ForegroundColor Yellow
    Write-Host "   1. GitHub Pages not yet deployed (wait 1-2 minutes)" -ForegroundColor White
    Write-Host "   2. GitHub Pages not enabled in repository settings" -ForegroundColor White
    Write-Host "   3. Network connection issue" -ForegroundColor White
    Write-Host "   4. URL is incorrect" -ForegroundColor White
    Write-Host ""
    Write-Host "Check GitHub Actions:" -ForegroundColor Cyan
    Write-Host "   https://github.com/WenyuChiou/ai-trader-ollama/actions" -ForegroundColor White
    Write-Host ""
}

Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""

