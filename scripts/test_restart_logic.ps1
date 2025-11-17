# Test script to verify restart logic
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\test_restart_logic.ps1

Write-Host "=== Testing Restart Script Logic ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check current processes on port 8000
Write-Host "[1] Checking processes on port 8000..." -ForegroundColor Yellow
$pids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($pids) {
    Write-Host "  Found processes: $($pids -join ', ')" -ForegroundColor Green
    foreach ($pid in $pids) {
        $p = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($p) {
            $procPath = $p.Path
            Write-Host "    PID $pid : $($p.ProcessName) - $procPath" -ForegroundColor White
            Write-Host "      CommandLine: $($p.CommandLine)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  No processes found on port 8000" -ForegroundColor Gray
}

Write-Host ""

# Step 2: Test stop logic (same as restart script)
Write-Host "[2] Testing stop logic..." -ForegroundColor Yellow
if ($pids) {
    $pids | ForEach-Object { 
        $p = Get-Process -Id $_ -ErrorAction SilentlyContinue
        if ($p -and $p.ProcessName -ne "Idle") {
            Write-Host "  Would stop PID $_ ($($p.ProcessName))" -ForegroundColor Yellow
            # Don't actually stop, just show what would happen
        }
    }
} else {
    Write-Host "  No processes to stop" -ForegroundColor Gray
}

Write-Host ""

# Step 3: Check all Python processes
Write-Host "[3] Checking all Python processes..." -ForegroundColor Yellow
$pythonProcs = Get-Process | Where-Object { 
    $_.ProcessName -like "*python*" -or 
    $_.CommandLine -like "*uvicorn*" -or 
    $_.CommandLine -like "*backend.src.api.server*" 
} -ErrorAction SilentlyContinue

if ($pythonProcs) {
    Write-Host "  Found Python processes:" -ForegroundColor Green
    foreach ($proc in $pythonProcs) {
        Write-Host "    PID $($proc.Id): $($proc.ProcessName)" -ForegroundColor White
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            if ($cmdLine) {
                Write-Host "      CommandLine: $cmdLine" -ForegroundColor Gray
            }
        } catch {
            Write-Host "      (Could not get command line)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  No Python processes found" -ForegroundColor Gray
}

Write-Host ""

# Step 4: Test wait logic
Write-Host "[4] Testing wait logic..." -ForegroundColor Yellow
$waitCount = 0
$maxWait = 10
while ($waitCount -lt $maxWait) {
    $inUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if (-not $inUse) {
        Write-Host "  Port 8000 is free after $($waitCount * 0.5) seconds" -ForegroundColor Green
        break
    }
    Write-Host "  Port 8000 still in use (wait $($waitCount * 0.5) seconds)..." -ForegroundColor Yellow
    Start-Sleep -Milliseconds 500
    $waitCount++
}

if ($waitCount -ge $maxWait) {
    Write-Host "  Port 8000 still in use after $($maxWait * 0.5) seconds!" -ForegroundColor Red
}

Write-Host ""

# Step 5: Check for uvicorn processes specifically
Write-Host "[5] Checking for uvicorn processes..." -ForegroundColor Yellow
$uvicornProcs = Get-Process | Where-Object { 
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdLine -like "*uvicorn*" -or $cmdLine -like "*backend.src.api.server*"
    } catch {
        $false
    }
} -ErrorAction SilentlyContinue

if ($uvicornProcs) {
    Write-Host "  Found uvicorn processes:" -ForegroundColor Green
    foreach ($proc in $uvicornProcs) {
        Write-Host "    PID $($proc.Id): $($proc.ProcessName)" -ForegroundColor White
        try {
            $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($proc.Id)").CommandLine
            Write-Host "      CommandLine: $cmdLine" -ForegroundColor Gray
        } catch {
            Write-Host "      (Could not get command line)" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "  No uvicorn processes found" -ForegroundColor Gray
}

Write-Host ""
Write-Host "=== Test Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Recommendations:" -ForegroundColor Yellow
Write-Host "  1. If processes are found but not stopped, the stop logic may need improvement" -ForegroundColor White
Write-Host "  2. If port 8000 is still in use after waiting, increase wait time" -ForegroundColor White
Write-Host "  3. Consider stopping all Python processes that match uvicorn pattern" -ForegroundColor White

