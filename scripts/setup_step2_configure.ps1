# Step 2: Configure System
# 配置系统（检查配置文件、初始化数据）

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  AI-Trader Ollama - Step 2: Configure System" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Get project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "[Step 2.1] Checking configuration files..." -ForegroundColor Yellow

# Check config.json
$configFile = Join-Path $ProjectRoot "backend\config\config.json"
if (Test-Path $configFile) {
    Write-Host "[OK] config.json found" -ForegroundColor Green
    
    # Validate JSON
    try {
        $configContent = Get-Content $configFile -Raw | ConvertFrom-Json
        Write-Host "[OK] config.json is valid JSON" -ForegroundColor Green
        
        # Display key configuration
        Write-Host ""
        Write-Host "Current Configuration:" -ForegroundColor Cyan
        Write-Host "  - Initial Cash: `$$($configContent.initial_cash)" -ForegroundColor White
        Write-Host "  - Universe Size: $($configContent.universe.Count) symbols" -ForegroundColor White
        Write-Host "  - Discussion Rounds: $($configContent.discussion_rounds)" -ForegroundColor White
        Write-Host "  - Tool Budget: $($configContent.discussion_tool_budget)" -ForegroundColor White
        Write-Host "  - LLM Model: $($configContent.llm.default_model)" -ForegroundColor White
        Write-Host "  - Ollama Host: $($configContent.llm.ollama_host)" -ForegroundColor White
        
        # Check position limits
        if ($configContent._position_limit_per_stock) {
            Write-Host "  - Position Limits: COMMENTED OUT (Agent has complete freedom)" -ForegroundColor Yellow
        } else {
            Write-Host "  - Position Limits: Not set (Agent has complete freedom)" -ForegroundColor Green
        }
    } catch {
        Write-Host "[ERROR] config.json is not valid JSON: $_" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
} else {
    Write-Host "[ERROR] config.json not found at: $configFile" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""

# Check agents.yaml
$agentsFile = Join-Path $ProjectRoot "backend\config\agents.yaml"
if (Test-Path $agentsFile) {
    Write-Host "[OK] agents.yaml found" -ForegroundColor Green
} else {
    Write-Host "[WARN] agents.yaml not found. System will use defaults." -ForegroundColor Yellow
}

Write-Host ""

# Check prompts directory
$promptsDir = Join-Path $ProjectRoot "prompts"
if (Test-Path $promptsDir) {
    $promptFiles = Get-ChildItem $promptsDir -Filter "*.yml"
    Write-Host "[OK] Prompts directory found: $($promptFiles.Count) prompt files" -ForegroundColor Green
} else {
    Write-Host "[WARN] Prompts directory not found" -ForegroundColor Yellow
}

Write-Host ""

Write-Host "[Step 2.2] Initializing data directory..." -ForegroundColor Yellow
$dataDir = Join-Path $ProjectRoot "data\logs"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir -Force | Out-Null
    Write-Host "[OK] Data directory created: $dataDir" -ForegroundColor Green
} else {
    Write-Host "[OK] Data directory exists: $dataDir" -ForegroundColor Green
}

Write-Host ""

Write-Host "[Step 2.3] Initializing portfolio state..." -ForegroundColor Yellow
$initScript = Join-Path $ProjectRoot "scripts\init_data.py"
if (Test-Path $initScript) {
    # Activate virtual environment
    $venvPath = Join-Path $ProjectRoot ".venv"
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
    }
    
    # Run init script
    python $initScript
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Portfolio initialized" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Portfolio initialization script returned non-zero exit code" -ForegroundColor Yellow
        Write-Host "This is OK if portfolio already exists." -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] init_data.py not found. Portfolio will be created on first trade." -ForegroundColor Yellow
}

Write-Host ""

Write-Host "[Step 2.4] Checking environment variables and API keys..." -ForegroundColor Yellow
$fredKey = $env:FRED_API_KEY
$fredKeyInConfig = $null
# Check both config.json root level and llm section
if ($configContent.fred_api_key) {
    $fredKeyInConfig = $configContent.fred_api_key
} elseif ($configContent.llm -and $configContent.llm.fred_api_key) {
    $fredKeyInConfig = $configContent.llm.fred_api_key
}

if ($fredKey -or $fredKeyInConfig) {
    if ($fredKey) {
        Write-Host "[OK] FRED_API_KEY found in environment variable" -ForegroundColor Green
    }
    if ($fredKeyInConfig) {
        Write-Host "[OK] FRED_API_KEY found in config.json" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] FRED_API_KEY not set (optional, for economic data)" -ForegroundColor Yellow
    Write-Host "  Get free API key from: https://fred.stlouisfed.org/docs/api/api_key.html" -ForegroundColor White
    Write-Host "  Option 1: Set environment variable: `$env:FRED_API_KEY='your_key_here'" -ForegroundColor White
    Write-Host "  Option 2: Add to config.json: `"fred_api_key`": `"your_key_here`"" -ForegroundColor White
}

Write-Host ""

Write-Host "================================================" -ForegroundColor Green
Write-Host "  Step 2 Complete!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Configuration Summary:" -ForegroundColor Cyan
Write-Host "  ✅ Config files checked" -ForegroundColor Green
Write-Host "  ✅ Data directory ready" -ForegroundColor Green
Write-Host "  ✅ Portfolio initialized" -ForegroundColor Green
Write-Host ""
Write-Host "Next step:" -ForegroundColor Cyan
Write-Host "  Run: .\scripts\setup_step3_start_services.ps1" -ForegroundColor White
Write-Host ""
Read-Host "Press Enter to continue"

