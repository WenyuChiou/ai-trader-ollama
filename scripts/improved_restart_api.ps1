# Improved API Restart Script (更可靠的重啟)
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\improved_restart_api.ps1
# 改进点：
# 1. 更彻底的进程停止（包括所有 Python 进程中的 uvicorn）
# 2. 更长的等待时间（最多 10 秒）
# 3. 验证端口是否真的释放

Write-Host "Restarting API (improved mode)..." -ForegroundColor Cyan
Write-Host ""

# Step 1: Stop processes on port 8000
Write-Host "[1] Stopping processes on port 8000..." -ForegroundColor Yellow
$pids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique

if ($pids) {
    Write-Host "  Found $($pids.Count) process(es) on port 8000" -ForegroundColor White
    $pids | ForEach-Object { 
        $p = Get-Process -Id $_ -ErrorAction SilentlyContinue
        if ($p -and $p.ProcessName -ne "Idle") {
            Write-Host "    Stopping PID $_ ($($p.ProcessName))..." -ForegroundColor Yellow
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "  No processes found on port 8000" -ForegroundColor Gray
}

# Step 2: Stop all uvicorn processes (more thorough)
Write-Host ""
Write-Host "[2] Stopping all uvicorn processes..." -ForegroundColor Yellow
$uvicornProcs = Get-Process | Where-Object { 
    try {
        $cmdLine = (Get-CimInstance Win32_Process -Filter "ProcessId = $($_.Id)").CommandLine
        $cmdLine -like "*uvicorn*" -or $cmdLine -like "*backend.src.api.server*"
    } catch {
        $false
    }
} -ErrorAction SilentlyContinue

if ($uvicornProcs) {
    Write-Host "  Found $($uvicornProcs.Count) uvicorn process(es)" -ForegroundColor White
    foreach ($proc in $uvicornProcs) {
        Write-Host "    Stopping PID $($proc.Id) ($($proc.ProcessName))..." -ForegroundColor Yellow
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "  No uvicorn processes found" -ForegroundColor Gray
}

# Step 3: Wait for port to be released (increased wait time)
Write-Host ""
Write-Host "[3] Waiting for port 8000 to be released..." -ForegroundColor Yellow
$waitCount = 0
$maxWait = 20  # 10 seconds (20 * 0.5)
$portReleased = $false

while ($waitCount -lt $maxWait) {
    Start-Sleep -Milliseconds 500
    $inUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if (-not $inUse) {
        $portReleased = $true
        Write-Host "  Port 8000 is free after $($waitCount * 0.5) seconds" -ForegroundColor Green
        break
    }
    $waitCount++
    if ($waitCount % 4 -eq 0) {
        Write-Host "    Still waiting... ($($waitCount * 0.5) seconds)" -ForegroundColor Gray
    }
}

if (-not $portReleased) {
    Write-Host "  WARNING: Port 8000 still in use after $($maxWait * 0.5) seconds!" -ForegroundColor Red
    Write-Host "  You may need to manually stop the process" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  To find and stop manually:" -ForegroundColor Yellow
    Write-Host "    Get-NetTCPConnection -LocalPort 8000 | Select-Object OwningProcess" -ForegroundColor White
    Write-Host "    Stop-Process -Id <PID> -Force" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Aborted." -ForegroundColor Red
        exit 1
    }
}

# Step 4: Start new API
Write-Host ""
Write-Host "[4] Starting new API server..." -ForegroundColor Yellow
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

# Get local IP for display
$localIP = $null
try {
    $ipAddresses = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue
    foreach ($ip in $ipAddresses) {
        if ($ip.InterfaceAlias -notlike "*Loopback*" -and 
            $ip.IPAddress -notlike "169.254.*" -and
            $ip.IPAddress -notlike "127.*") {
            $localIP = $ip.IPAddress
            break
        }
    }
} catch {
    # Ignore errors
}

$cmd = @"
cd '$ProjectRoot'
if (Test-Path '.venv\Scripts\Activate.ps1') { 
    Write-Host 'Activating virtual environment...' -ForegroundColor Cyan
    . '.venv\Scripts\Activate.ps1' 
}
Write-Host 'Starting uvicorn server...' -ForegroundColor Cyan
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
"@

Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $cmd | Out-Null

Write-Host "  [OK] API server starting in new window" -ForegroundColor Green
Write-Host ""
Write-Host "Access:" -ForegroundColor Cyan
Write-Host "  Local: http://127.0.0.1:8000/docs" -ForegroundColor White
if ($localIP) {
    Write-Host "  Share: http://${localIP}:8000/docs" -ForegroundColor Yellow
} else {
    Write-Host "  Share: Run .\scripts\get_share_link.ps1 to get share link" -ForegroundColor Gray
}
Write-Host ""
Write-Host "Note: Check the new PowerShell window for startup logs" -ForegroundColor Yellow
Write-Host ""

