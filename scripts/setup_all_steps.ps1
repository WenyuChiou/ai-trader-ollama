# Complete Setup Script - Run All Steps
# 一键完成所有设置步骤

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Ollama - Complete Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will run all setup steps:" -ForegroundColor Yellow
Write-Host "  1. Install Dependencies" -ForegroundColor White
Write-Host "  2. Configure System" -ForegroundColor White
Write-Host "  3. Start Services" -ForegroundColor White
Write-Host ""
$confirm = Read-Host "Continue? (Y/N)"

if ($confirm -ne "Y" -and $confirm -ne "y") {
    Write-Host "Setup cancelled." -ForegroundColor Yellow
    exit 0
}

Write-Host ""

# Step 1
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Running Step 1: Install Dependencies" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
& "$PSScriptRoot\setup_step1_install_dependencies.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Step 1 failed. Please fix errors and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Press Enter to continue to Step 2..."
Read-Host

# Step 2
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Running Step 2: Configure System" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
& "$PSScriptRoot\setup_step2_configure.ps1"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Step 2 failed. Please fix errors and try again." -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Press Enter to continue to Step 3..."
Read-Host

# Step 3
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Running Step 3: Start Services" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
& "$PSScriptRoot\setup_step3_start_services.ps1"

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "System is ready to use!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Access Points:" -ForegroundColor Cyan
Write-Host "  🌐 API Server: http://localhost:8000" -ForegroundColor White
Write-Host "  📊 API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host "  🎨 Frontend: Open frontend\monitor.html in your browser" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to exit"

