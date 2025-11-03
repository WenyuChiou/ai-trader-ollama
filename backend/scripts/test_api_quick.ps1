# Quick API Test Script
# Tests if API can be started and responds correctly

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Quick API Test" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$backendDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

# Step 1: Check port
Write-Host "Step 1: Checking port 8000..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    $pid = ($portInUse | Select-Object -First 1).OwningProcess
    Write-Host "  Port 8000 is in use by process $pid" -ForegroundColor Red
    Write-Host "  Run: .\check_port.ps1 to free the port" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "  Port 8000 is available" -ForegroundColor Green
    Write-Host ""
}

# Step 2: Test Python imports
Write-Host "Step 2: Testing Python imports..." -ForegroundColor Yellow
try {
    Push-Location $backendDir
    $result = python -c "from src.api.server import app; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Python imports: OK" -ForegroundColor Green
    } else {
        Write-Host "  Python imports: FAILED" -ForegroundColor Red
        Write-Host "  $result" -ForegroundColor Red
    }
} catch {
    Write-Host "  Python imports: ERROR - $_" -ForegroundColor Red
} finally {
    Pop-Location
}
Write-Host ""

# Step 3: Test API test script
Write-Host "Step 3: Running backend test script..." -ForegroundColor Yellow
try {
    Push-Location $backendDir
    $testResult = python test_api.py 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Backend tests: PASSED" -ForegroundColor Green
    } else {
        Write-Host "  Backend tests: FAILED" -ForegroundColor Red
        Write-Host $testResult -ForegroundColor Red
    }
} catch {
    Write-Host "  Backend tests: ERROR - $_" -ForegroundColor Red
} finally {
    Pop-Location
}
Write-Host ""

# Step 4: Check if API is already running
Write-Host "Step 4: Testing API endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/" -TimeoutSec 3 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  API is already running!" -ForegroundColor Green
        $content = $response.Content | ConvertFrom-Json
        Write-Host "  Version: $($content.version)" -ForegroundColor Green
        Write-Host ""
        Write-Host "API is ready!" -ForegroundColor Green
    }
} catch {
    if ($portInUse) {
        Write-Host "  API endpoint not responding (port in use but no response)" -ForegroundColor Yellow
        Write-Host "  You may need to kill the process using port 8000" -ForegroundColor Yellow
    } else {
        Write-Host "  API is not running (this is OK if you haven't started it yet)" -ForegroundColor Gray
        Write-Host ""
        Write-Host "To start API:" -ForegroundColor Cyan
        Write-Host "  cd $backendDir" -ForegroundColor White
        Write-Host "  python -m uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
    }
}

Write-Host ""
Read-Host "Press Enter to exit"

