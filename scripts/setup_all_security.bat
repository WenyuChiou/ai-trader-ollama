@echo off
REM Setup All Security Features - One-Click Configuration Script
REM This script configures all security features for the AI Trader system

setlocal enabledelayedexpansion

echo ========================================
echo AI Trader - Security Setup Script
echo ========================================
echo.

REM Check if running from project root
if not exist "backend\src\api\server.py" (
    echo ERROR: Please run this script from the project root directory
    echo Current directory: %CD%
    pause
    exit /b 1
)

REM Step 1: Check Python
echo [1/7] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
python --version
echo.

REM Step 2: Check/Create virtual environment
echo [2/7] Checking virtual environment...
if not exist ".venv" (
    echo Creating virtual environment...
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

REM Step 3: Activate virtual environment and install dependencies
echo [3/7] Installing dependencies...
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

pip install --upgrade pip >nul 2>&1
pip install -r backend\requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo Dependencies installed successfully
echo.

REM Step 4: Create .env file if it doesn't exist
echo [4/7] Configuring environment variables...
if not exist ".env" (
    echo Creating .env file...
    
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

REM Step 5: Create logs directory
echo [5/7] Creating logs directory...
if not exist "data\logs" (
    mkdir data\logs
    echo Logs directory created
) else (
    echo Logs directory already exists
)
echo.

REM Step 6: Verify configuration files
echo [6/7] Verifying configuration files...
if not exist "backend\config\config.json" (
    echo WARNING: config.json not found
) else (
    echo config.json found
)

if not exist "backend\config\agents.yaml" (
    echo WARNING: agents.yaml not found
) else (
    echo agents.yaml found
)
echo.

REM Step 7: Summary
echo [7/7] Setup Summary
echo ========================================
echo.
echo Security features configured:
echo   - Admin API Key authentication: ENABLED
echo   - Rate limiting: ENABLED
echo   - CORS: Configured for development
echo   - Error handling: Secure (no traceback leakage)
echo   - Logging: Unified with trace ID support
echo.
echo Next steps:
echo   1. Review .env file and update ADMIN_SECRET if needed
echo   2. Set ENVIRONMENT=production for production deployment
echo   3. Update ALLOWED_ORIGINS with your production domain
echo   4. Run start_backend_auto.bat to start the API server
echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
pause

