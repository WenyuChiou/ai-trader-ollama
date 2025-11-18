# Test script for API connection monitor
# 测试API连接监控脚本
# Usage: powershell -ExecutionPolicy Bypass -File scripts\test_monitor_api.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  API Connection Monitor - Test Script" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "[TEST 1] Testing API connection check..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "[OK] API is online" -ForegroundColor Green
    } else {
        Write-Host "[WARN] API returned status code: $($response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[INFO] API is offline (expected for testing)" -ForegroundColor Gray
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "[TEST 2] Testing notification system..." -ForegroundColor Yellow

# Check if BurntToast is available
try {
    Import-Module BurntToast -ErrorAction Stop
    Write-Host "[OK] BurntToast module is available" -ForegroundColor Green
    Write-Host "[TEST] Sending test notification..." -ForegroundColor Gray
    New-BurntToastNotification `
        -Text "Test Notification", "This is a test notification from AI Trader monitor" `
        -AppId "AI Trader" `
        -Sound "Default" `
        -ErrorAction Stop | Out-Null
    Write-Host "[OK] Test notification sent successfully" -ForegroundColor Green
} catch {
    Write-Host "[INFO] BurntToast not available, will use alternative method" -ForegroundColor Yellow
    Write-Host "  To install: Install-Module -Name BurntToast -Scope CurrentUser" -ForegroundColor Gray
    Write-Host "[TEST] Using system sound..." -ForegroundColor Gray
    [System.Media.SystemSounds]::Exclamation.Play()
    Write-Host "[OK] System sound played" -ForegroundColor Green
}

Write-Host ""
Write-Host "[TEST 3] Testing restart function..." -ForegroundColor Yellow
Write-Host "[INFO] This test will check if restart script can be created" -ForegroundColor Gray

$BackendDir = Join-Path $ProjectRoot "backend"
$venvPath = Join-Path $ProjectRoot ".venv"
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"

if (Test-Path $activateScript) {
    Write-Host "[OK] Virtual environment found" -ForegroundColor Green
} else {
    Write-Host "[WARN] Virtual environment not found at: $venvPath" -ForegroundColor Yellow
}

if (Test-Path $BackendDir) {
    Write-Host "[OK] Backend directory found" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Backend directory not found: $BackendDir" -ForegroundColor Red
}

Write-Host ""
Write-Host "[TEST 4] Testing port check..." -ForegroundColor Yellow
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[INFO] Port 8000 is in use" -ForegroundColor Gray
    $processIds = $portInUse | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($processId in $processIds) {
        $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "  Process: $($proc.ProcessName) (PID: $processId)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "[INFO] Port 8000 is not in use" -ForegroundColor Gray
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Test Complete" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "To start monitoring:" -ForegroundColor Cyan
Write-Host "  .\scripts\monitor_api_connection.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run monitoring in background:" -ForegroundColor Cyan
Write-Host "  Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File scripts\monitor_api_connection.ps1'" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"

