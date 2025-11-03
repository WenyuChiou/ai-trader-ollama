# PowerShell script to check and help install Node.js
Write-Host "=== Node.js Installation Checker ===" -ForegroundColor Cyan
Write-Host ""

# Check if node is in PATH
$nodeInPath = Get-Command node -ErrorAction SilentlyContinue
if ($nodeInPath) {
    $nodeVersion = & node --version
    Write-Host "✅ Node.js is installed: $nodeVersion" -ForegroundColor Green
    $nodePath = $nodeInPath.Source
    Write-Host "   Location: $nodePath" -ForegroundColor Gray
} else {
    Write-Host "❌ Node.js is NOT in PATH" -ForegroundColor Red
}

# Check if npm is in PATH
$npmInPath = Get-Command npm -ErrorAction SilentlyContinue
if ($npmInPath) {
    $npmVersion = & npm --version
    Write-Host "✅ npm is installed: $npmVersion" -ForegroundColor Green
    $npmPath = $npmInPath.Source
    Write-Host "   Location: $npmPath" -ForegroundColor Gray
} else {
    Write-Host "❌ npm is NOT in PATH" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Checking Common Installation Locations ===" -ForegroundColor Cyan

# Check common Node.js installation paths
$commonPaths = @(
    "$env:ProgramFiles\nodejs",
    "${env:ProgramFiles(x86)}\nodejs",
    "$env:LOCALAPPDATA\nodejs",
    "$env:APPDATA\npm",
    "C:\nodejs"
)

$found = $false
foreach ($path in $commonPaths) {
    if (Test-Path $path) {
        Write-Host "✅ Found: $path" -ForegroundColor Green
        $nodeExe = Join-Path $path "node.exe"
        $npmCmd = Join-Path $path "npm.cmd"
        
        if (Test-Path $nodeExe) {
            $version = & $nodeExe --version
            Write-Host "   Node.js version: $version" -ForegroundColor Gray
        }
        
        if (Test-Path $npmCmd) {
            $version = & $npmCmd --version
            Write-Host "   npm version: $version" -ForegroundColor Gray
        }
        
        $found = $true
    }
}

if (-not $found) {
    Write-Host "❌ Node.js not found in common locations" -ForegroundColor Red
    Write-Host ""
    Write-Host "=== Installation Instructions ===" -ForegroundColor Yellow
    Write-Host "1. Download Node.js from: https://nodejs.org/" -ForegroundColor White
    Write-Host "2. Install the LTS version" -ForegroundColor White
    Write-Host "3. Restart PowerShell after installation" -ForegroundColor White
    Write-Host "4. Run this script again to verify" -ForegroundColor White
} else {
    Write-Host ""
    Write-Host "=== Next Steps ===" -ForegroundColor Yellow
    Write-Host "If Node.js is installed but not in PATH:" -ForegroundColor White
    Write-Host "1. Add the Node.js directory to your system PATH" -ForegroundColor White
    Write-Host "2. Restart PowerShell" -ForegroundColor White
    Write-Host "3. Run: cd frontend && npm install" -ForegroundColor White
}

Write-Host ""

