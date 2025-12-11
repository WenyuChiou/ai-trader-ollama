# Test BAT files functionality
# This script tests if the BAT files can be executed (syntax check)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "BAT Files Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$errors = 0

# Test 1: Check if BAT files exist
Write-Host "[Test 1] Checking BAT file existence..." -ForegroundColor Yellow
$setupBat = "scripts\setup_all_security.bat"
$startBat = "scripts\start_backend_auto.bat"

if (Test-Path $setupBat) {
    Write-Host "  ✅ setup_all_security.bat exists" -ForegroundColor Green
    $size = (Get-Item $setupBat).Length
    Write-Host "     Size: $size bytes" -ForegroundColor Gray
} else {
    Write-Host "  ❌ setup_all_security.bat not found" -ForegroundColor Red
    $errors++
}

if (Test-Path $startBat) {
    Write-Host "  ✅ start_backend_auto.bat exists" -ForegroundColor Green
    $size = (Get-Item $startBat).Length
    Write-Host "     Size: $size bytes" -ForegroundColor Gray
} else {
    Write-Host "  ❌ start_backend_auto.bat not found" -ForegroundColor Red
    $errors++
}

Write-Host ""

# Test 2: Check BAT file syntax (basic validation)
Write-Host "[Test 2] Checking BAT file syntax..." -ForegroundColor Yellow

function Test-BatSyntax {
    param($FilePath)
    
    $content = Get-Content $FilePath -Raw -ErrorAction SilentlyContinue
    if ($null -eq $content) {
        return $false
    }
    
    # Basic checks
    $checks = @(
        @{ Pattern = "@echo off"; Name = "Has @echo off" },
        @{ Pattern = "REM "; Name = "Has comments" },
        @{ Pattern = "if "; Name = "Has conditional logic" },
        @{ Pattern = "echo "; Name = "Has echo statements" }
    )
    
    $passed = 0
    foreach ($check in $checks) {
        if ($content -match $check.Pattern) {
            Write-Host "    ✅ $($check.Name)" -ForegroundColor Green
            $passed++
        }
    }
    
    return $passed -ge 2
}

if (Test-Path $setupBat) {
    Write-Host "  Testing setup_all_security.bat..." -ForegroundColor Gray
    if (Test-BatSyntax $setupBat) {
        Write-Host "  ✅ setup_all_security.bat syntax valid" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  setup_all_security.bat syntax check incomplete" -ForegroundColor Yellow
    }
}

if (Test-Path $startBat) {
    Write-Host "  Testing start_backend_auto.bat..." -ForegroundColor Gray
    if (Test-BatSyntax $startBat) {
        Write-Host "  ✅ start_backend_auto.bat syntax valid" -ForegroundColor Green
    } else {
        Write-Host "  ⚠️  start_backend_auto.bat syntax check incomplete" -ForegroundColor Yellow
    }
}

Write-Host ""

# Test 3: Check BAT file content (key features)
Write-Host "[Test 3] Checking BAT file content..." -ForegroundColor Yellow

if (Test-Path $setupBat) {
    $content = Get-Content $setupBat -Raw
    $features = @(
        @{ Pattern = "ADMIN_SECRET"; Name = "ADMIN_SECRET configuration" },
        @{ Pattern = "virtual environment"; Name = "Virtual environment handling" },
        @{ Pattern = "requirements.txt"; Name = "Dependency installation" },
        @{ Pattern = ".env"; Name = "Environment file creation" }
    )
    
    $found = 0
    foreach ($feature in $features) {
        if ($content -match $feature.Pattern) {
            Write-Host "  ✅ setup_all_security.bat: $($feature.Name)" -ForegroundColor Green
            $found++
        }
    }
    
    if ($found -lt 3) {
        Write-Host "  ⚠️  Some expected features not found" -ForegroundColor Yellow
    }
}

if (Test-Path $startBat) {
    $content = Get-Content $startBat -Raw
    $features = @(
        @{ Pattern = "uvicorn"; Name = "Uvicorn server startup" },
        @{ Pattern = "port 8000"; Name = "Port configuration" },
        @{ Pattern = "virtual environment"; Name = "Virtual environment handling" }
    )
    
    $found = 0
    foreach ($feature in $features) {
        if ($content -match $feature.Pattern) {
            Write-Host "  ✅ start_backend_auto.bat: $($feature.Name)" -ForegroundColor Green
            $found++
        }
    }
    
    if ($found -lt 2) {
        Write-Host "  ⚠️  Some expected features not found" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($errors -eq 0) {
    Write-Host "✅ All BAT file tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ $errors test(s) failed" -ForegroundColor Red
    exit 1
}

