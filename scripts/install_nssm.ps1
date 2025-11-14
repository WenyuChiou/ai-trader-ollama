# Auto-install NSSM (Non-Sucking Service Manager)
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\install_nssm.ps1

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  NSSM Installation" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$nssmDir = "C:\nssm"
$nssmPath = "$nssmDir\nssm.exe"

# Check if already installed
if (Test-Path $nssmPath) {
    Write-Host "[INFO] NSSM already installed at $nssmPath" -ForegroundColor Green
    & $nssmPath version
    Write-Host ""
    Write-Host "NSSM is ready to use!" -ForegroundColor Green
    Read-Host "Press Enter to continue"
    exit 0
}

Write-Host "[INSTALL] Installing NSSM..." -ForegroundColor Cyan
Write-Host ""

# Create directory
if (-not (Test-Path $nssmDir)) {
    Write-Host "[CREATE] Creating directory: $nssmDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $nssmDir -Force | Out-Null
}

# Download NSSM
$nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
$zipPath = "$env:TEMP\nssm-2.24.zip"

Write-Host "[DOWNLOAD] Downloading NSSM from $nssmUrl" -ForegroundColor Yellow
Write-Host "This may take a moment..." -ForegroundColor Gray

try {
    # Use Invoke-WebRequest to download
    Invoke-WebRequest -Uri $nssmUrl -OutFile $zipPath -UseBasicParsing
    Write-Host "[OK] Download completed" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Failed to download NSSM: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual installation:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://nssm.cc/download" -ForegroundColor White
    Write-Host "  2. Extract to: C:\nssm\" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

# Extract ZIP
Write-Host "[EXTRACT] Extracting NSSM..." -ForegroundColor Yellow
try {
    # Find the correct architecture (win64 or win32)
    $extractDir = "$env:TEMP\nssm-extract"
    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
    }
    Expand-Archive -Path $zipPath -DestinationPath $extractDir -Force
    
    # Copy the correct version (prefer win64, fallback to win32)
    $win64Path = Join-Path $extractDir "nssm-2.24\win64\nssm.exe"
    $win32Path = Join-Path $extractDir "nssm-2.24\win32\nssm.exe"
    
    if (Test-Path $win64Path) {
        Copy-Item -Path $win64Path -Destination $nssmPath -Force
        Write-Host "[OK] Extracted win64 version" -ForegroundColor Green
    } elseif (Test-Path $win32Path) {
        Copy-Item -Path $win32Path -Destination $nssmPath -Force
        Write-Host "[OK] Extracted win32 version" -ForegroundColor Green
    } else {
        throw "Could not find nssm.exe in extracted files"
    }
    
    # Cleanup
    Remove-Item -Path $extractDir -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path $zipPath -Force -ErrorAction SilentlyContinue
    
} catch {
    Write-Host "[ERROR] Failed to extract NSSM: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual installation:" -ForegroundColor Yellow
    Write-Host "  1. Download from: https://nssm.cc/download" -ForegroundColor White
    Write-Host "  2. Extract to: C:\nssm\" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Read-Host "Press Enter to exit"
    exit 1
}

# Verify installation
if (Test-Path $nssmPath) {
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "  Installation Successful!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "NSSM installed at: $nssmPath" -ForegroundColor Green
    & $nssmPath version
    Write-Host ""
    Write-Host "Next step:" -ForegroundColor Cyan
    Write-Host "  Run: powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host "[ERROR] Installation failed - nssm.exe not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Read-Host "Press Enter to continue"

