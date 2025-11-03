# Node.js Installation Guide

## Problem
If you see the error: `無法辨識 'npm' 詞彙是否為 Cmdlet...`, it means Node.js/npm is not installed or not in your PATH.

## Solution 1: Install Node.js (Recommended)

1. **Download Node.js**:
   - Visit: https://nodejs.org/
   - Download the LTS (Long Term Support) version
   - This includes both Node.js and npm

2. **Install Node.js**:
   - Run the installer
   - Accept the default options (it will add Node.js to PATH)
   - Restart your terminal/PowerShell after installation

3. **Verify Installation**:
   ```powershell
   node --version
   npm --version
   ```

4. **Install Frontend Dependencies**:
   ```powershell
   cd frontend
   npm install
   ```

## Solution 2: Use Direct Path (If Node.js is Already Installed)

If Node.js is installed but not in PATH, you can use the full path:

```powershell
# Try these locations:
& "C:\Program Files\nodejs\npm.cmd" install
# or
& "C:\Program Files (x86)\nodejs\npm.cmd" install
```

## Solution 3: Add Node.js to PATH Manually

1. Find your Node.js installation directory (usually `C:\Program Files\nodejs\`)
2. Add it to your system PATH:
   - Open System Properties → Environment Variables
   - Edit "Path" under System Variables
   - Add: `C:\Program Files\nodejs\`
   - Restart PowerShell

## Quick Check Script

Run this in PowerShell to check for Node.js:

```powershell
# Check common locations
$locations = @(
    "$env:ProgramFiles\nodejs",
    "${env:ProgramFiles(x86)}\nodejs",
    "$env:LOCALAPPDATA\nodejs",
    "$env:APPDATA\npm"
)

foreach ($loc in $locations) {
    if (Test-Path $loc) {
        Write-Host "Found: $loc"
    }
}
```

## Alternative: Use Chocolatey (If You Have It)

```powershell
choco install nodejs
```

## After Installation

Once Node.js is installed, run:

```powershell
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

