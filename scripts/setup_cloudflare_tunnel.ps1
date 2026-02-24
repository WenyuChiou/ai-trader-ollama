# Setup Cloudflare Named Tunnel for AI Trader
# One-time interactive setup — creates a persistent tunnel with a stable URL
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\setup_cloudflare_tunnel.ps1

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI Trader - Cloudflare Named Tunnel Setup" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

$tunnelName = "ai-trader"
$configDir = Join-Path $ProjectRoot "config"
$tunnelConfigFile = Join-Path $configDir "tunnel_config.json"

# ── Step 1: Check / Install cloudflared ──────────────────────────────────────

Write-Host "[1/6] Checking cloudflared..." -ForegroundColor Cyan

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Host "[WARN] cloudflared not found in PATH" -ForegroundColor Yellow
    $install = Read-Host "Install cloudflared via winget? (Y/n)"
    if ($install -ne "n" -and $install -ne "N") {
        Write-Host "Installing cloudflared..." -ForegroundColor Cyan
        winget install --id Cloudflare.cloudflared --accept-source-agreements --accept-package-agreements
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERROR] winget install failed. Download manually:" -ForegroundColor Red
            Write-Host "  https://github.com/cloudflare/cloudflared/releases" -ForegroundColor White
            Read-Host "Press Enter to exit"
            exit 1
        }
        # Refresh PATH
        $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("PATH", "User")
        $cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
        if (-not $cloudflared) {
            Write-Host "[ERROR] cloudflared still not found after install. Restart your terminal." -ForegroundColor Red
            Read-Host "Press Enter to exit"
            exit 1
        }
    } else {
        Write-Host "[ERROR] cloudflared is required. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host "[OK] cloudflared found: $(cloudflared --version)" -ForegroundColor Green
Write-Host ""

# ── Step 2: Authenticate with Cloudflare ─────────────────────────────────────

Write-Host "[2/6] Authenticating with Cloudflare..." -ForegroundColor Cyan

$certPath = Join-Path $env:USERPROFILE ".cloudflared\cert.pem"
if (Test-Path $certPath) {
    Write-Host "[OK] Already authenticated (cert.pem exists)" -ForegroundColor Green
} else {
    Write-Host "A browser window will open for Cloudflare login." -ForegroundColor Yellow
    Write-Host "Select the domain you want to use for the tunnel." -ForegroundColor Yellow
    Write-Host ""
    cloudflared tunnel login
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Authentication failed" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[OK] Authentication successful" -ForegroundColor Green
}
Write-Host ""

# ── Step 3: Create Named Tunnel ──────────────────────────────────────────────

Write-Host "[3/6] Creating named tunnel '$tunnelName'..." -ForegroundColor Cyan

# Check if tunnel already exists
$existingTunnel = cloudflared tunnel list --output json 2>$null | ConvertFrom-Json | Where-Object { $_.name -eq $tunnelName }
if ($existingTunnel) {
    $tunnelId = $existingTunnel.id
    Write-Host "[OK] Tunnel '$tunnelName' already exists (ID: $tunnelId)" -ForegroundColor Green
} else {
    $createOutput = cloudflared tunnel create $tunnelName 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create tunnel:" -ForegroundColor Red
        Write-Host $createOutput -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    # Extract tunnel ID from output
    $match = ($createOutput | Select-String -Pattern "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})")
    if (-not $match -or $match.Matches.Count -eq 0) {
        Write-Host "[ERROR] Could not parse tunnel ID from output:" -ForegroundColor Red
        Write-Host $createOutput -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    $tunnelId = $match.Matches[0].Value
    Write-Host "[OK] Tunnel created (ID: $tunnelId)" -ForegroundColor Green
}
Write-Host ""

# ── Step 4: Configure DNS Route ──────────────────────────────────────────────

Write-Host "[4/6] Setting up DNS route..." -ForegroundColor Cyan

$subdomain = Read-Host "Enter your subdomain (e.g., ai-trader.yourdomain.com)"
if ([string]::IsNullOrWhiteSpace($subdomain)) {
    Write-Host "[ERROR] Subdomain is required" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Creating DNS route: $subdomain -> tunnel $tunnelName" -ForegroundColor Yellow
$dnsOutput = cloudflared tunnel route dns $tunnelName $subdomain 2>&1
# Route may already exist — that's OK
if ($dnsOutput -match "already exists") {
    Write-Host "[OK] DNS route already exists for $subdomain" -ForegroundColor Green
} elseif ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] DNS route command output:" -ForegroundColor Yellow
    Write-Host $dnsOutput -ForegroundColor Yellow
    Write-Host "You may need to manually add a CNAME record for $subdomain -> $tunnelId.cfargotunnel.com" -ForegroundColor Yellow
} else {
    Write-Host "[OK] DNS route created" -ForegroundColor Green
}
Write-Host ""

# ── Step 5: Generate cloudflared config.yml ──────────────────────────────────

Write-Host "[5/6] Generating cloudflared config..." -ForegroundColor Cyan

$cloudflaredConfigDir = Join-Path $env:USERPROFILE ".cloudflared"
$cloudflaredConfig = Join-Path $cloudflaredConfigDir "config.yml"

$tunnelUrl = "https://$subdomain"

# Use forward slashes in credentials path for YAML compatibility
$credPath = "$cloudflaredConfigDir\$tunnelId.json".Replace('\', '/')

$configContent = @"
tunnel: $tunnelId
credentials-file: $credPath

ingress:
  - hostname: $subdomain
    service: http://localhost:8000
  - service: http_status:404
"@

$configContent | Out-File -FilePath $cloudflaredConfig -Encoding UTF8 -Force
Write-Host "[OK] Config written to $cloudflaredConfig" -ForegroundColor Green
Write-Host ""

# ── Step 6: Save tunnel info and update frontend ─────────────────────────────

Write-Host "[6/6] Saving tunnel config..." -ForegroundColor Cyan

# Ensure config dir exists
if (-not (Test-Path $configDir)) {
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# Save tunnel config JSON
$tunnelConfig = @{
    tunnel_name = $tunnelName
    tunnel_id   = $tunnelId
    subdomain   = $subdomain
    tunnel_url  = $tunnelUrl
    created_at  = (Get-Date -Format "yyyy-MM-ddTHH:mm:ss")
} | ConvertTo-Json -Depth 2

$tunnelConfig | Out-File -FilePath $tunnelConfigFile -Encoding UTF8 -Force
Write-Host "[OK] Saved tunnel config to $tunnelConfigFile" -ForegroundColor Green

# Update frontend/config.js production URL
$frontendConfig = Join-Path $ProjectRoot "frontend\config.js"
if (Test-Path $frontendConfig) {
    $content = Get-Content $frontendConfig -Raw -Encoding UTF8
    $updatedContent = $content -replace "production:\s*'[^']*'", "production: '$tunnelUrl'"
    $updatedContent | Set-Content $frontendConfig -Encoding UTF8 -Force
    Write-Host "[OK] Updated frontend/config.js production URL to $tunnelUrl" -ForegroundColor Green
} else {
    Write-Host "[WARN] frontend/config.js not found — update production URL manually" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Setup Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Tunnel Name:  $tunnelName" -ForegroundColor White
Write-Host "Tunnel ID:    $tunnelId" -ForegroundColor White
Write-Host "Public URL:   $tunnelUrl" -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Start the backend:  scripts\start_backend_local.bat" -ForegroundColor White
Write-Host "  2. Start the tunnel:   scripts\start_cloudflare_tunnel.bat" -ForegroundColor White
Write-Host "  3. Set up auto-start:  powershell -File scripts\setup_autostart.ps1" -ForegroundColor White
Write-Host "  4. Test from phone:    curl $tunnelUrl/api/health" -ForegroundColor White
Write-Host ""
Write-Host "NOTE: DNS changes may take up to 5 minutes to propagate." -ForegroundColor Yellow
Write-Host ""
Write-Host "Dashboard:    https://wenyuchiou.github.io/ai-trader-ollama/" -ForegroundColor Green
Write-Host ""

Read-Host "Press Enter to continue"
