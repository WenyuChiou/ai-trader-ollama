@echo off
REM Get script directory and project root
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"
if exist ".venv\Scripts\activate.bat" call .venv\Scripts\activate.bat
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
