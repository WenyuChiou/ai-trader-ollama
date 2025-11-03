# PowerShell script to check if backend API is running
# Fix encoding issues
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
chcp 65001 | Out-Null

Write-Host "=== Backend API Status Check ===" -ForegroundColor Cyan
Write-Host ""

# Check port 8000
Write-Host "Checking port 8000..." -ForegroundColor Yellow
$port8000 = netstat -ano | findstr ":8000"
if ($port8000) {
    Write-Host "✅ Port 8000 is in use" -ForegroundColor Green
    $port8000 | ForEach-Object {
        $parts = $_ -split '\s+'
        if ($parts.Count -gt 0) {
            $pid = $parts[-1]
            if ($pid -match '^\d+$') {
                $process = Get-Process -Id $pid -ErrorAction SilentlyContinue
                if ($process) {
                    Write-Host "   Process: $($process.ProcessName) (PID: $pid)" -ForegroundColor Gray
                }
            }
        }
    }
} else {
    Write-Host "❌ Port 8000 is NOT in use" -ForegroundColor Red
}

Write-Host ""
Write-Host "Testing API endpoint..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -Method GET -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
    Write-Host "✅ Backend API is RUNNING and responding!" -ForegroundColor Green
    Write-Host "   Status Code: $($response.StatusCode)" -ForegroundColor Gray
    
    try {
        $json = $response.Content | ConvertFrom-Json
        Write-Host "   API Message: $($json.message)" -ForegroundColor Gray
        Write-Host "   Version: $($json.version)" -ForegroundColor Gray
    } catch {
        Write-Host "   Response: $($response.Content.Substring(0, [Math]::Min(100, $response.Content.Length)))..." -ForegroundColor Gray
    }
    
    Write-Host ""
    Write-Host "✅ API is ready to accept requests!" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend API is NOT responding" -ForegroundColor Red
    Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Gray
    Write-Host ""
    Write-Host "=== Next Steps ===" -ForegroundColor Yellow
    Write-Host "1. Start the API:" -ForegroundColor White
    Write-Host "   cd backend\scripts" -ForegroundColor Cyan
    Write-Host "   .\start_api_background.ps1" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "2. Or start manually:" -ForegroundColor White
    Write-Host "   cd backend" -ForegroundColor Cyan
    Write-Host "   python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Cyan
}

Write-Host ""

