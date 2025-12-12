@echo off
echo ========================================
echo AI Trader - Start Local Backend
echo ========================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: scripts\install.bat
    pause
    exit /b 1
)

REM Check if backend directory exists
if not exist "backend" (
    echo ERROR: Backend directory not found!
    pause
    exit /b 1
)

echo Starting backend on http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

cd backend
call ..\venv\Scripts\activate.bat

REM Check if uvicorn is installed
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo ERROR: uvicorn not found!
    echo Installing uvicorn...
    pip install uvicorn[standard]
)

echo Starting FastAPI server...
uvicorn src.api.server:app --host 0.0.0.0 --port 8000

pause

