@echo off
REM One-Click Installation Script
REM Installs all dependencies and sets up the environment

setlocal enabledelayedexpansion

echo ========================================
echo AI Trader - One-Click Installation
echo ========================================
echo.
echo This script will:
echo   1. Check Python and Ollama installation
echo   2. Create virtual environment
echo   3. Install Python dependencies
echo   4. Check/Install Ollama model
echo   5. Initialize data directories
echo   6. Create default configuration files
echo.

REM Check if running from project root
if not exist "backend\src\api\server.py" (
    echo ERROR: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Step 1: Check Python
echo [1/8] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Step 2: Check Ollama
echo [2/8] Checking Ollama installation...
ollama --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Ollama not found in PATH
    echo Please install Ollama from: https://ollama.ai/
    echo After installation, run: ollama pull deepseek-r1
    echo.
    set /p continue="Continue anyway? (Y/N): "
    if /i not "!continue!"=="Y" (
        exit /b 1
    )
) else (
    ollama --version
    echo.
    echo Checking Ollama model (deepseek-r1)...
    ollama list | findstr /i "deepseek-r1" >nul 2>&1
    if errorlevel 1 (
        echo Model not found. Pulling deepseek-r1...
        ollama pull deepseek-r1
        if errorlevel 1 (
            echo WARNING: Failed to pull model. You can pull it later with: ollama pull deepseek-r1
        ) else (
            echo Model pulled successfully
        )
    ) else (
        echo Model deepseek-r1 is available
    )
)
echo.

REM Step 3: Create virtual environment
echo [3/8] Creating virtual environment...
if not exist ".venv" (
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
) else (
    echo Virtual environment already exists
)
echo.

REM Step 4: Activate virtual environment
echo [4/8] Activating virtual environment...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)
echo Virtual environment activated
echo.

REM Step 5: Upgrade pip
echo [5/8] Upgrading pip...
pip install --upgrade pip >nul 2>&1
echo pip upgraded
echo.

REM Step 6: Install dependencies
echo [6/8] Installing Python dependencies...
echo This may take a few minutes...
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Step 7: Initialize data directories
echo [7/8] Initializing data directories...
if not exist "data\logs" (
    mkdir data\logs
    echo Created data\logs directory
)
if not exist "data\backups" (
    mkdir data\backups
    echo Created data\backups directory
)
echo Data directories initialized
echo.

REM Step 8: Create default .env if not exists
echo [8/8] Checking configuration files...
if not exist ".env" (
    echo Creating default .env file...
    
    REM Generate random admin secret
    set "ADMIN_SECRET=%RANDOM%%RANDOM%%RANDOM%%RANDOM%"
    
    (
        echo # Security Configuration
        echo ADMIN_SECRET=!ADMIN_SECRET!
        echo ALLOWED_ORIGINS=http://localhost:*,https://wenyuchiou.github.io
        echo.
        echo # Environment
        echo ENVIRONMENT=development
        echo LOG_LEVEL=INFO
        echo.
        echo # API Keys ^(Optional^)
        echo # FRED_API_KEY=your_fred_api_key_here
        echo.
        echo # Ollama Configuration ^(Optional^)
        echo # OLLAMA_BASE_URL=http://localhost:11434
    ) > .env
    
    echo .env file created with generated ADMIN_SECRET
    echo IMPORTANT: Save your ADMIN_SECRET: !ADMIN_SECRET!
) else (
    echo .env file already exists, skipping creation
)
echo.

REM Summary
echo ========================================
echo Installation Summary
echo ========================================
echo.
echo Installation completed successfully!
echo.
echo Next steps:
echo   1. Run: scripts\setup_wizard.bat (for first-time configuration)
echo   2. Run: scripts\verify_environment.bat (to verify installation)
echo   3. Run: scripts\test_backend.bat (to test backend)
echo   4. Run: scripts\start_backend_auto.bat (to start the system)
echo.
echo For detailed setup guide, see: docs\INSTALLATION.md
echo.
pause

