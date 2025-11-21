# Fix API Service - Remove and reinstall if needed
# 修复 API 服务 - 删除并重新安装（如果需要）

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader API - Service Fix" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
Set-Location $ProjectRoot

$serviceName = "AITraderAPI"
$nssmPath = Join-Path $ProjectRoot "tools\nssm\nssm.exe"

# Check if service exists
$existingService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue

if ($existingService) {
    Write-Host "[INFO] Service '$serviceName' found" -ForegroundColor Yellow
    Write-Host "  Status: $($existingService.Status)" -ForegroundColor Gray
    Write-Host ""
    
    # Try to stop service
    Write-Host "[ACTION] Stopping service..." -ForegroundColor Cyan
    try {
        Stop-Service -Name $serviceName -Force -ErrorAction Stop
        Start-Sleep -Seconds 3
        Write-Host "[OK] Service stopped" -ForegroundColor Green
    } catch {
        Write-Host "[WARNING] Could not stop service: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    
    # Remove service using NSSM
    if (Test-Path $nssmPath) {
        Write-Host "[ACTION] Removing service..." -ForegroundColor Cyan
        & $nssmPath remove $serviceName confirm 2>&1 | Out-Null
        Start-Sleep -Seconds 2
        
        # Verify removal
        $checkService = Get-Service -Name $serviceName -ErrorAction SilentlyContinue
        if (-not $checkService) {
            Write-Host "[OK] Service removed" -ForegroundColor Green
        } else {
            Write-Host "[WARNING] Service still exists, may need manual removal" -ForegroundColor Yellow
        }
    } else {
        Write-Host "[ERROR] NSSM not found at: $nssmPath" -ForegroundColor Red
        Write-Host "Please run: scripts\start_api_service_admin.bat" -ForegroundColor Yellow
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[INFO] Service '$serviceName' does not exist" -ForegroundColor Green
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Next Steps" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Service has been removed. To reinstall:" -ForegroundColor Yellow
Write-Host "  1. Run: scripts\start_api_service_admin.bat" -ForegroundColor Cyan
Write-Host "  2. Follow the installation prompts" -ForegroundColor Cyan
Write-Host ""
Write-Host "Or use Task Scheduler instead (recommended):" -ForegroundColor Yellow
Write-Host "  1. Run: scripts\start_api_task_admin.bat" -ForegroundColor Cyan
Write-Host "  2. Choose (I)nstall, then (S)tart" -ForegroundColor Cyan
Write-Host ""

Read-Host "Press Enter to exit"

