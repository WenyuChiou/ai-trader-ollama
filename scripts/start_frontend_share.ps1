# Start frontend server for sharing
# Usage: .\scripts\start_frontend_share.ps1

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$FrontendDir = Join-Path $ProjectRoot "frontend"

# Get local IP address
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object -First 1).IPAddress

if (-not $localIP) {
    Write-Host "[ERROR] Could not detect IP address" -ForegroundColor Red
    exit 1
}

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Starting Frontend Server (Shareable)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend Directory: $FrontendDir" -ForegroundColor Gray
Write-Host ""
Write-Host "Local Access:" -ForegroundColor Cyan
Write-Host "  http://localhost:3000/monitor.html" -ForegroundColor Green
Write-Host ""
Write-Host "Share with others (same network):" -ForegroundColor Cyan
Write-Host "  http://$localIP:3000/monitor.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "Starting server..." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""

cd $FrontendDir
python -m http.server 3000 --bind 0.0.0.0

