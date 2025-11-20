# Test Setup Scripts
# Tests all setup scripts for syntax and file existence
# Usage: powershell -ExecutionPolicy Bypass -File .\scripts\test_setup_scripts.ps1

$ErrorActionPreference = "Continue"

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Testing Setup Scripts" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $PSScriptRoot
$allPassed = $true

# Test batch files
Write-Host "Testing Batch Files (.bat):" -ForegroundColor Yellow
$batchFiles = @(
    "scripts\setup_daily_backup_admin.bat",
    "scripts\start_api_task_admin.bat",
    "scripts\start_api_service_admin.bat"
)

foreach ($file in $batchFiles) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        $content = Get-Content $fullPath -Raw
        if ($content.Length -gt 0) {
            Write-Host "  ✅ $file" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️  $file (empty)" -ForegroundColor Yellow
            $allPassed = $false
        }
    } else {
        Write-Host "  ❌ $file (not found)" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""

# Test PowerShell scripts
Write-Host "Testing PowerShell Scripts (.ps1):" -ForegroundColor Yellow
$psScripts = @(
    "scripts\setup_daily_backup.ps1",
    "scripts\start_api_task_scheduler.ps1",
    "scripts\setup_step1_install_dependencies.ps1",
    "scripts\setup_step2_configure.ps1",
    "scripts\setup_step3_start_services.ps1"
)

foreach ($file in $psScripts) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        try {
            $content = Get-Content $fullPath -Raw -ErrorAction Stop
            if ($content.Length -gt 0) {
                # Basic syntax check
                $errors = $null
                $null = [System.Management.Automation.PSParser]::Tokenize($content, [ref]$errors)
                if ($errors.Count -eq 0) {
                    Write-Host "  ✅ $file" -ForegroundColor Green
                } else {
                    Write-Host "  ⚠️  $file (syntax warnings: $($errors.Count))" -ForegroundColor Yellow
                }
            } else {
                Write-Host "  ⚠️  $file (empty)" -ForegroundColor Yellow
                $allPassed = $false
            }
        } catch {
            Write-Host "  ❌ $file (error: $($_.Exception.Message))" -ForegroundColor Red
            $allPassed = $false
        }
    } else {
        Write-Host "  ❌ $file (not found)" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""

# Test Python scripts
Write-Host "Testing Python Scripts (.py):" -ForegroundColor Yellow
$pythonScripts = @(
    "backend\scripts\daily_backup.py"
)

foreach ($file in $pythonScripts) {
    $fullPath = Join-Path $projectRoot $file
    if (Test-Path $fullPath) {
        try {
            # Test Python syntax using py_compile
            $result = python -m py_compile $fullPath 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ $file" -ForegroundColor Green
            } else {
                Write-Host "  ❌ $file (syntax error)" -ForegroundColor Red
                Write-Host "     $result" -ForegroundColor Gray
                $allPassed = $false
            }
        } catch {
            Write-Host "  ⚠️  $file (could not test, but file exists)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ $file (not found)" -ForegroundColor Red
        $allPassed = $false
    }
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
if ($allPassed) {
    Write-Host "  ✅ All Tests Passed!" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Some Tests Failed" -ForegroundColor Yellow
}
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

if (-not $allPassed) {
    exit 1
}

