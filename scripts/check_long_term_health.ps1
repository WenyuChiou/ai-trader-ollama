# Check Long-Term Running System Health
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\check_long_term_health.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Long-Term Running Health Check" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$issues = @()
$warnings = @()

# 1. Check API Server Status
Write-Host "[1] Checking API Server Status..." -ForegroundColor Yellow
$task = Get-ScheduledTask -TaskName "AITraderAPI" -ErrorAction SilentlyContinue
if ($task) {
    $taskInfo = Get-ScheduledTaskInfo -TaskName "AITraderAPI"
    $status = $taskInfo.State
    if ($status -eq "Running") {
        Write-Host "  ✅ API Server is running" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  API Server is not running (Status: $status)" -ForegroundColor Yellow
        $warnings += "API Server is not running"
    }
} else {
    Write-Host "  ❌ API Server task not found" -ForegroundColor Red
    $issues += "API Server task not configured"
}

# Check API health
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8000/api/health" -TimeoutSec 5 -ErrorAction Stop
    if ($response.StatusCode -eq 200) {
        Write-Host "  ✅ API is responding" -ForegroundColor Green
    }
} catch {
    Write-Host "  ❌ API is not responding" -ForegroundColor Red
    $issues += "API is not responding"
}

# 2. Check Disk Space
Write-Host ""
Write-Host "[2] Checking Disk Space..." -ForegroundColor Yellow
$dataSize = 0
if (Test-Path "data\logs") {
    $dataSize = (Get-ChildItem -Path "data\logs" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1GB
    Write-Host "  Data directory size: $([math]::Round($dataSize, 2)) GB" -ForegroundColor White
    
    if ($dataSize -gt 10) {
        Write-Host "  ⚠️  WARNING: Data directory exceeds 10 GB" -ForegroundColor Red
        $warnings += "Data directory is very large ($([math]::Round($dataSize, 2)) GB)"
    } elseif ($dataSize -gt 5) {
        Write-Host "  ⚠️  Data directory is getting large" -ForegroundColor Yellow
        $warnings += "Data directory is large ($([math]::Round($dataSize, 2)) GB)"
    } else {
        Write-Host "  ✅ Data directory size is acceptable" -ForegroundColor Green
    }
} else {
    Write-Host "  ⚠️  Data directory not found" -ForegroundColor Yellow
}

# Check log files
$logSize = 0
if (Test-Path "logs") {
    $logSize = (Get-ChildItem -Path "logs" -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
    Write-Host "  Log files size: $([math]::Round($logSize, 2)) MB" -ForegroundColor White
    
    if ($logSize -gt 100) {
        Write-Host "  ⚠️  WARNING: Log files exceed 100 MB" -ForegroundColor Yellow
        $warnings += "Log files are large ($([math]::Round($logSize, 2)) MB)"
    }
}

# 3. Check Scheduled Tasks
Write-Host ""
Write-Host "[3] Checking Scheduled Tasks..." -ForegroundColor Yellow
$uploadTask = Get-ScheduledTask -TaskName "AI-Trader-Daily-Upload-Simple" -ErrorAction SilentlyContinue
if ($uploadTask) {
    Write-Host "  ✅ Daily upload task configured" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Daily upload task not configured" -ForegroundColor Yellow
    $warnings += "Daily upload task not configured"
}

$maintenanceTask = Get-ScheduledTask -TaskName "AI-Trader-Weekly-Maintenance" -ErrorAction SilentlyContinue
if ($maintenanceTask) {
    Write-Host "  ✅ Weekly maintenance task configured" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Weekly maintenance task not configured" -ForegroundColor Yellow
    $warnings += "Weekly maintenance task not configured"
}

# 4. Check Old Files
Write-Host ""
Write-Host "[4] Checking for Old Files..." -ForegroundColor Yellow
$oldBackups = Get-ChildItem -Path "data\logs" -Filter "portfolio_state_backup_*.json" -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) }
if ($oldBackups) {
    Write-Host "  ⚠️  Found $($oldBackups.Count) old backup files (>7 days)" -ForegroundColor Yellow
    $warnings += "$($oldBackups.Count) old backup files found"
} else {
    Write-Host "  ✅ No old backup files found" -ForegroundColor Green
}

# 5. Check Portfolio State
Write-Host ""
Write-Host "[5] Checking Portfolio State..." -ForegroundColor Yellow
if (Test-Path "data\logs\portfolio_state.json") {
    try {
        $portfolio = Get-Content "data\logs\portfolio_state.json" | ConvertFrom-Json
        $positions = $portfolio.positions
        $cash = $portfolio.cash
        $totalValue = $portfolio.total_value
        
        Write-Host "  Cash: `$$([math]::Round($cash, 2))" -ForegroundColor White
        Write-Host "  Total Value: `$$([math]::Round($totalValue, 2))" -ForegroundColor White
        Write-Host "  Positions: $($positions.PSObject.Properties.Count)" -ForegroundColor White
        
        if ($positions.PSObject.Properties.Count -gt 0) {
            Write-Host "  ✅ Portfolio has positions" -ForegroundColor Green
        } else {
            Write-Host "  ℹ️  Portfolio is 100% cash" -ForegroundColor Gray
        }
    } catch {
        Write-Host "  ⚠️  Failed to read portfolio state" -ForegroundColor Yellow
        $warnings += "Portfolio state file may be corrupted"
    }
} else {
    Write-Host "  ⚠️  Portfolio state file not found" -ForegroundColor Yellow
    $warnings += "Portfolio state file not found"
}

# 6. Summary
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Health Check Summary" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if ($issues.Count -eq 0 -and $warnings.Count -eq 0) {
    Write-Host "✅ System is healthy and ready for long-term running!" -ForegroundColor Green
} else {
    if ($issues.Count -gt 0) {
        Write-Host "❌ Issues found:" -ForegroundColor Red
        foreach ($issue in $issues) {
            Write-Host "  - $issue" -ForegroundColor Red
        }
        Write-Host ""
    }
    
    if ($warnings.Count -gt 0) {
        Write-Host "⚠️  Warnings:" -ForegroundColor Yellow
        foreach ($warning in $warnings) {
            Write-Host "  - $warning" -ForegroundColor Yellow
        }
        Write-Host ""
    }
}

Write-Host "Recommendations:" -ForegroundColor Cyan
Write-Host "  - Run cleanup: powershell -ExecutionPolicy Bypass -File scripts\cleanup_repo.ps1" -ForegroundColor Gray
Write-Host "  - Check logs: Get-Content logs\api_task.log -Tail 50" -ForegroundColor Gray
Write-Host "  - Setup maintenance: powershell -ExecutionPolicy Bypass -File scripts\setup_long_term_running.ps1" -ForegroundColor Gray
Write-Host ""

