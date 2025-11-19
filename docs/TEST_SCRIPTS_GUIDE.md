# Test Scripts Guide

## Overview

To avoid overwriting trading records during testing, we have created independent test scripts.

## Script List

### 1. `scripts/test_news_tools.py` - News Tools Testing

**Purpose**: Independently test news tools without running trading cycles

**Features**:
- ✅ Tests only news tool functionality
- ✅ Does not overwrite any trading records or position data
- ✅ Does not run trading cycles
- ✅ Test results saved to `data/logs/news_test_results.json`

**Usage**:
```bash
# Run from project root
python scripts/test_news_tools.py
```

**Test Content**:
- `news_scan`: Keyword-based news search
- `plan_and_scan_news`: LLM-generated queries and news search
- `fetch_jin10_news`: Fetch news from Jin10 data

**Output**:
- Console displays test results
- Test results saved to `data/logs/news_test_results.json`

---

### 2. `scripts/verify_portfolio.py` - Portfolio Record Verification

**Purpose**: Verify consistency between `portfolio_state.json` and `equity_history.jsonl`

**Features**:
- ✅ Read-only operations, does not modify any data
- ✅ Checks consistency of positions, cash, and total value
- ✅ Displays detailed difference reports

**Usage**:
```bash
# Run from project root
python scripts/verify_portfolio.py
```

**Check Content**:
1. Data Loading: Check if files exist
2. Basic Information: Display timestamp, cash, total value, position count
3. Position Comparison: Compare position differences between two files
4. Cash Consistency: Check if cash is consistent
5. Total Value Consistency: Check if total value is consistent

**Output Example**:
```
============================================================
Portfolio Record Verification
============================================================

1. Loading data...
✅ Data loaded successfully

2. Basic Information:
   portfolio_state.json:
     - Timestamp: 2025-11-18T21:55:02.516Z
     - Cash: $13.20
     - Total Value: $9997.48
     - Position Count: 10

   equity_history.jsonl (latest record):
     - Date: 2025-11-18
     - Cash: $13.20
     - Total Value: $9997.48
     - Position Count: 10

3. Position Comparison:
   Common Positions: 10 symbols
     Symbols: AAPL, AMZN, BKR, MAR, NVDA, PSQ, SQQQ, SPXL, TQQQ, TSLA

4. Cash Consistency:
   ✅ Cash consistent (difference: $0.00)

5. Total Value Consistency:
   ✅ Total value consistent (difference: $0.00)

6. Verification Summary:
   ✅ Portfolio records are consistent
```

---

## Important Notes

### ⚠️ Do NOT Use `scripts/run_daily_trading.py` for Testing

**Reason**:
- `run_daily_trading.py` runs complete trading cycles
- Will overwrite `portfolio_state.json`
- Will create new trading records
- Will affect position data

**Correct Approach**:
- Test news tools: Use `scripts/test_news_tools.py`
- Verify portfolio: Use `scripts/verify_portfolio.py`
- Actual trading: Use `scripts/run_daily_trading.py`

---

## File Locations

All scripts are located in the `scripts/` directory:
```
ai-trader-ollama/
├── scripts/
│   ├── test_news_tools.py      # News tools testing
│   ├── verify_portfolio.py     # Portfolio verification
│   └── run_daily_trading.py    # Actual trading (DO NOT use for testing)
└── data/
    └── logs/
        ├── portfolio_state.json
        ├── equity_history.jsonl
        └── news_test_results.json  # Test results
```

---

## Troubleshooting

### Issue 1: ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Ensure running from project root:
```bash
cd ai-trader-ollama
python scripts/test_news_tools.py
```

### Issue 2: UnicodeEncodeError (Windows)

**Error**: `UnicodeEncodeError: 'cp950' codec can't encode character`

**Solution**: Scripts include UTF-8 encoding support. If issues persist, set environment variable:
```powershell
$env:PYTHONIOENCODING="utf-8"
python scripts/test_news_tools.py
```

### Issue 3: File Not Found

**Error**: `portfolio_state.json does not exist or cannot be loaded`

**Solution**: Check file path:
```bash
# Windows PowerShell
Test-Path "data\logs\portfolio_state.json"

# Linux/Mac
test -f data/logs/portfolio_state.json
```

---

## Best Practices

1. **Backup Before Testing**: Backup important data before testing
2. **Use Independent Scripts**: Use independent test scripts for testing
3. **Verify Results**: Verify data consistency after testing
4. **Record Tests**: Save test results for future analysis

---

## Additional Test Scripts

### Python Test Scripts

Located in `scripts/` directory:
- `test_api_fgi.py` - Test Fear & Greed Index API
- `test_api_server.py` - Test API server endpoints
- `test_frontend_features.py` - Test frontend features
- `test_market_status.py` - Test market status checking
- `test_railway_data.py` - Test Railway data upload
- `test_report_generation.py` - Test report generation

### PowerShell Test Scripts

Located in `scripts/` directory:
- `test_monitor_api.ps1` - Test monitor API connection
- `test_github_pages.ps1` - Test GitHub Pages deployment

### Integration Tests

Located in `tests/integration/` directory:
- `test_agent_architecture.py` - Agent system integration tests
- `test_api.py` - API endpoint integration tests
- `test_memory.py` - Memory system integration tests
- `test_portfolio.py` - Portfolio management integration tests

### End-to-End Tests

Located in `tests/e2e/` directory:
- `test_frontend.py` - Frontend end-to-end tests

---

## Running Tests

### Run All Tests
```powershell
# From project root
pytest tests/ -v
```

### Run Specific Test Category
```powershell
# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v
```

### Run with Coverage
```powershell
pytest tests/ -v --cov=backend/src --cov-report=html
```

---

## See Also

- [Testing Guide](TESTING.md) - Complete testing documentation
- [Quick Start Guide](QUICK_START.md) - Installation and setup
- [Architecture Documentation](ARCHITECTURE.md) - System architecture
