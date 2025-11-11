# Fast API Restart Script (日常使用 - 快速重啟)
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
# 或直接雙擊執行（如果執行政策允許）

Write-Host "Restarting API (fast mode)..." -ForegroundColor Cyan

# Quick stop
$pids = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess -Unique
if ($pids) {
    $pids | ForEach-Object { 
        $p = Get-Process -Id $_ -ErrorAction SilentlyContinue
        if ($p -and $p.ProcessName -ne "Idle") {
            Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue
        }
    }
}

# Quick wait (max 2 seconds)
$waitCount = 0
while ($waitCount -lt 4) {
    Start-Sleep -Milliseconds 500
    $inUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
    if (-not $inUse) { break }
    $waitCount++
}

# Start new API
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
if (Test-Path '.venv\Scripts\Activate.ps1') { . '.venv\Scripts\Activate.ps1' }
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
"@

Start-Process powershell -ArgumentList "-ExecutionPolicy", "Bypass", "-NoExit", "-Command", $cmd | Out-Null
Write-Host "[OK] API restarted" -ForegroundColor Green
Write-Host ""
Write-Host "Access:" -ForegroundColor Cyan
Write-Host "  Local: http://127.0.0.1:8000/docs" -ForegroundColor White
if ($localIP) {
    Write-Host "  Share: http://${localIP}:8000/docs" -ForegroundColor Yellow
} else {
    Write-Host "  Share: Run .\scripts\get_share_link.ps1 to get share link" -ForegroundColor Gray
}
Write-Host ""

