@echo off
REM verify.bat — Pre-release verification script
REM Runs all quality gates locally before tagging a release.
REM
REM Usage: scripts\verify.bat

setlocal enabledelayedexpansion

echo ============================================================
echo  AI Trader - Pre-Release Verification
echo ============================================================
echo.

set PASS=0
set FAIL=0
set PROJECT_ROOT=%~dp0..

REM --- 1. Python check ---
echo [1/6] Checking Python...
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL: Python not found
    set /a FAIL+=1
) else (
    echo   PASS: Python found
    set /a PASS+=1
)

REM --- 2. Unit tests ---
echo.
echo [2/6] Running unit tests...
cd /d "%PROJECT_ROOT%\tests"
python -m pytest unit/ -v --tb=short 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL: Unit tests failed
    set /a FAIL+=1
) else (
    echo   PASS: All unit tests passed
    set /a PASS+=1
)

REM --- 3. Ruff lint ---
echo.
echo [3/6] Running ruff lint on new code...
cd /d "%PROJECT_ROOT%"
python -m ruff check backend/src/utils/trading_mode.py backend/src/utils/config_schema.py backend/src/utils/correlation.py backend/src/utils/logger.py backend/src/api/response_models.py backend/src/api/error_handler.py --select=E,F,W --ignore=E501,E402,F401,W605 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL: Lint errors found
    set /a FAIL+=1
) else (
    echo   PASS: Lint clean
    set /a PASS+=1
)

REM --- 4. Config validation ---
echo.
echo [4/6] Validating config schema...
cd /d "%PROJECT_ROOT%"
python -c "import sys; sys.path.insert(0,'backend'); from src.utils.config_schema import validate_config_file; validate_config_file('backend/config/config.json'); print('  PASS: config.json validates')" 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL: Config validation failed
    set /a FAIL+=1
) else (
    set /a PASS+=1
)

REM --- 5. OpenAPI contract ---
echo.
echo [5/6] Verifying OpenAPI contract...
cd /d "%PROJECT_ROOT%"
python -c "import sys; sys.path.insert(0,'backend'); from src.api.server import app; s=app.openapi(); assert s['info']['title']=='AI Trader API'; print(f'  PASS: OpenAPI schema OK ({len(s[\"paths\"])} endpoints)')" 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL: OpenAPI contract broken
    set /a FAIL+=1
) else (
    set /a PASS+=1
)

REM --- 6. Safety defaults ---
echo.
echo [6/6] Verifying safety defaults...
cd /d "%PROJECT_ROOT%"
python -c "import sys; sys.path.insert(0,'backend'); from src.utils.trading_mode import resolve_trading_mode; m=resolve_trading_mode(); assert m.value=='READ_ONLY', f'Expected READ_ONLY, got {m.value}'; print('  PASS: Default mode is READ_ONLY')" 2>&1
if %ERRORLEVEL% neq 0 (
    echo   FAIL: Safety default check failed
    set /a FAIL+=1
) else (
    set /a PASS+=1
)

REM --- Summary ---
echo.
echo ============================================================
echo  Results: %PASS% passed, %FAIL% failed
echo ============================================================

if %FAIL% gtr 0 (
    echo.
    echo  *** VERIFICATION FAILED — DO NOT RELEASE ***
    echo.
    exit /b 1
) else (
    echo.
    echo  All checks passed. Ready for release.
    echo.
    exit /b 0
)
