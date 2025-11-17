# Step 1: Install Dependencies
# 安装依赖和初始化环境

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Ollama - Step 1: Install Dependencies" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "[Step 1.1] Checking Python installation..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Python not found. Please install Python 3.10 or higher." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}
Write-Host "[OK] Python found: $pythonVersion" -ForegroundColor Green
Write-Host ""

Write-Host "[Step 1.2] Checking Ollama installation..." -ForegroundColor Yellow
$ollamaVersion = ollama --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARN] Ollama not found in PATH." -ForegroundColor Yellow
    Write-Host "Please install Ollama from: https://ollama.ai/" -ForegroundColor Yellow
    Write-Host "After installation, run: ollama pull deepseek-r1" -ForegroundColor Yellow
    Write-Host ""
    $continue = Read-Host "Continue anyway? (Y/N)"
    if ($continue -ne "Y" -and $continue -ne "y") {
        exit 1
    }
} else {
    Write-Host "[OK] Ollama found: $ollamaVersion" -ForegroundColor Green
    Write-Host ""
    Write-Host "[Step 1.2.1] Checking if deepseek-r1 model is available..." -ForegroundColor Yellow
    $models = ollama list 2>&1
    if ($models -match "deepseek-r1") {
        Write-Host "[OK] deepseek-r1 model is available" -ForegroundColor Green
    } else {
        Write-Host "[INFO] deepseek-r1 model not found. Pulling model..." -ForegroundColor Yellow
        ollama pull deepseek-r1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[OK] deepseek-r1 model pulled successfully" -ForegroundColor Green
        } else {
            Write-Host "[WARN] Failed to pull model. You can pull it later with: ollama pull deepseek-r1" -ForegroundColor Yellow
        }
    }
}
Write-Host ""

Write-Host "[Step 1.3] Creating virtual environment..." -ForegroundColor Yellow
$venvPath = Join-Path $ProjectRoot ".venv"
if (Test-Path $venvPath) {
    Write-Host "[INFO] Virtual environment already exists" -ForegroundColor Yellow
} else {
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Virtual environment created" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}
Write-Host ""

Write-Host "[Step 1.4] Activating virtual environment and installing dependencies..." -ForegroundColor Yellow
$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
if (Test-Path $activateScript) {
    & $activateScript
    Write-Host "[OK] Virtual environment activated" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Virtual environment activation script not found" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[Step 1.5] Installing Python dependencies..." -ForegroundColor Yellow
$requirementsFile = Join-Path $ProjectRoot "backend\requirements.txt"
if (Test-Path $requirementsFile) {
    pip install --upgrade pip
    pip install -r $requirementsFile
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Dependencies installed successfully" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Failed to install dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[ERROR] requirements.txt not found at: $requirementsFile" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "  Step 1 Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Run: .\scripts\setup_step2_configure.ps1" -ForegroundColor White
Write-Host "  2. Run: .\scripts\setup_step3_start_services.ps1" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue"

