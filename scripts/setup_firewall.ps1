# Setup Windows Firewall for AI Trader API
# Usage: Run as Administrator: .\scripts\setup_firewall.ps1

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Windows Firewall Setup for AI Trader" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[ERROR] This script must be run as Administrator" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "Then run: .\scripts\setup_firewall.ps1" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[INFO] Running as Administrator" -ForegroundColor Green
Write-Host ""

# Check if rule already exists
$existingRule = Get-NetFirewallRule -DisplayName "AI Trader API" -ErrorAction SilentlyContinue

if ($existingRule) {
    Write-Host "[INFO] Firewall rule already exists" -ForegroundColor Yellow
    Write-Host "Removing old rule..." -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName "AI Trader API" -ErrorAction SilentlyContinue
}

# Add firewall rule for port 8000 (API)
Write-Host "[SETUP] Adding firewall rule for port 8000 (API)..." -ForegroundColor Cyan
try {
    New-NetFirewallRule -DisplayName "AI Trader API" `
        -Direction Inbound `
        -LocalPort 8000 `
        -Protocol TCP `
        -Action Allow `
        -Profile Any `
        -Description "Allow access to AI Trader API server on port 8000"
    
    Write-Host "[OK] Firewall rule added for port 8000" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to add firewall rule: $_" -ForegroundColor Red
}

# Add firewall rule for port 3000 (Frontend)
Write-Host "[SETUP] Adding firewall rule for port 3000 (Frontend)..." -ForegroundColor Cyan
try {
    New-NetFirewallRule -DisplayName "AI Trader Frontend" `
        -Direction Inbound `
        -LocalPort 3000 `
        -Protocol TCP `
        -Action Allow `
        -Profile Any `
        -Description "Allow access to AI Trader Frontend on port 3000"
    
    Write-Host "[OK] Firewall rule added for port 3000" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to add firewall rule: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Firewall rules added:" -ForegroundColor Green
Write-Host "  - Port 8000 (API)" -ForegroundColor White
Write-Host "  - Port 3000 (Frontend)" -ForegroundColor White
Write-Host ""
Write-Host "You can now share your API with others on the same network!" -ForegroundColor Green
Write-Host ""
Write-Host "Run .\scripts\get_share_link.ps1 to get shareable links" -ForegroundColor Yellow
Write-Host ""

Read-Host "Press Enter to continue"

