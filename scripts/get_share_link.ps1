# Quick script to get shareable links
# Usage: .\scripts\get_share_link.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Share Links for AI Trader" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get local IP address
$localIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*" -and $_.IPAddress -notlike "169.254.*"} | Select-Object -First 1).IPAddress

if (-not $localIP) {
    Write-Host "[ERROR] Could not detect IP address" -ForegroundColor Red
    Write-Host "Please check your network connection" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Your IP Address: $localIP" -ForegroundColor Green
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Share These Links:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
$apiDocLink = "http://$localIP:8000/docs"
$apiStatusLink = "http://$localIP:8000/api/agents/status"
$portfolioLink = "http://$localIP:8000/api/portfolio/real-time"
$frontendLink = "http://$localIP:3000/monitor.html"

Write-Host "API Documentation:" -ForegroundColor Yellow
Write-Host "  http://${localIP}:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "API Status:" -ForegroundColor Yellow
Write-Host "  http://${localIP}:8000/api/agents/status" -ForegroundColor White
Write-Host ""
Write-Host "Portfolio Status:" -ForegroundColor Yellow
Write-Host "  http://${localIP}:8000/api/portfolio/real-time" -ForegroundColor White
Write-Host ""
Write-Host "Frontend Dashboard (if started):" -ForegroundColor Yellow
Write-Host "  http://${localIP}:3000/monitor.html" -ForegroundColor White
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Important Notes:" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Make sure API is running with --host 0.0.0.0" -ForegroundColor White
Write-Host "2. Users must be on the same network (WiFi/LAN)" -ForegroundColor White
Write-Host "3. Windows Firewall may block access - allow port 8000" -ForegroundColor White
Write-Host "4. For internet access, use ngrok or deploy to cloud" -ForegroundColor White
Write-Host ""

# Check if port 8000 is in use
$portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "[OK] Port 8000 is in use (API might be running)" -ForegroundColor Green
} else {
    Write-Host "[WARN] Port 8000 is not in use (API might not be running)" -ForegroundColor Yellow
    Write-Host "Start API with: .\scripts\start_api_stable_bypass.ps1" -ForegroundColor White
}

Write-Host ""
Read-Host "Press Enter to continue"

