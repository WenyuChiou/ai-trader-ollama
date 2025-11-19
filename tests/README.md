# Test Suite Documentation

**Language**: [English](README.md) | [中文版](README_zh.md)

---

## Overview

This directory contains the complete test suite for the AI-Trader Ollama system. All tests are organized by type and follow pytest conventions.

## Directory Structure

```
tests/
├── integration/             # Integration tests for system components
│   ├── test_agent_architecture.py  # Agent system tests
│   ├── test_portfolio.py            # Portfolio management tests
│   ├── test_memory.py               # Memory system tests
│   ├── test_api.py                  # API endpoint tests
│   ├── test_analysis_targets.py    # Analysis target validation tests
│   └── test_trading_cycle_quick.py  # Quick trading cycle test (order recording)
├── e2e/                     # End-to-end tests
│   └── test_frontend.py             # Frontend integration tests
├── utils/                   # Test utilities and helpers
│   └── test_helpers.py              # Shared test utilities
├── conftest.py              # Pytest configuration and shared fixtures
├── pytest.ini               # Pytest settings
├── README.md                # This file (English)
└── README_zh.md             # Chinese version
```

## Prerequisites

- Python 3.10 or higher
- Virtual environment activated
- Dependencies installed: `pip install -r backend/requirements.txt`
- Ollama running (for tests that require LLM)
- Backend API running (for API tests)

## Running Tests

### Run All Tests

```powershell
# From project root
pytest tests/ -v

# Or with more details
pytest tests/ -v --tb=short
```

### Run Specific Test Categories

```powershell
# Integration tests only
pytest tests/integration/ -v

# End-to-end tests only
pytest tests/e2e/ -v

# Specific test file
pytest tests/integration/test_portfolio.py -v

# Specific test function
pytest tests/integration/test_portfolio.py::test_portfolio_creation -v
```

### Run with Coverage

```powershell
# Install pytest-cov if not already installed
pip install pytest-cov

# Run tests with coverage
pytest tests/ --cov=backend/src --cov-report=html --cov-report=term-missing

# View HTML coverage report
# Open htmlcov/index.html in your browser
```

### Run Tests in Parallel

```powershell
# Install pytest-xdist if not already installed
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -n 4 -v
```

## Test Categories

### Integration Tests (`tests/integration/`)

**Purpose**: Test component interactions and system integration

**Test Files**:
- `test_agent_architecture.py` - Tests agent system, tool calls, and coordination
- `test_portfolio.py` - Tests portfolio management, position tracking, and P&L calculations
- `test_memory.py` - Tests memory system, RAG functionality, and memory retrieval
- `test_api.py` - Tests API endpoints, data parsing, and response formats
- `test_analysis_targets.py` - Tests analysis target validation (holdings, recommended stocks, indices)
- `test_trading_cycle_quick.py` - **CRITICAL**: Quick trading cycle test for order recording verification

**Characteristics**:
- Use real dependencies where possible
- Moderate execution time
- May require Ollama for LLM-related tests
- May require API server for API tests

### End-to-End Tests (`tests/e2e/`)

**Purpose**: Test complete workflows from start to finish

**Test Files**:
- `test_frontend.py` - Tests frontend integration, data display, and user interactions

**Characteristics**:
- Use real system components
- Slower execution time
- Require full system setup (API server, frontend)
- Test complete user workflows

### Test Utilities (`tests/utils/`)

**Purpose**: Shared utilities and helpers for tests

**Files**:
- `test_helpers.py` - Common test functions, fixtures, and utilities

## Test Fixtures

Common fixtures are defined in `tests/conftest.py`:

- `test_data_dir` - Test data directory path
- `logs_dir` - Logs directory path
- `test_portfolio_state` - Sample portfolio state for testing
- `sample_market_data` - Sample market data for testing
- `sample_positions` - Sample positions for testing

## Writing Tests

### Example Integration Test

```python
def test_portfolio_creation():
    """Test portfolio creation and initialization"""
    from src.data.portfolio import Portfolio
    
    portfolio = Portfolio(initial_cash=10000.0)
    
    assert portfolio.cash == 10000.0
    assert portfolio.total_value == 10000.0
    assert len(portfolio._positions) == 0
```

### Example API Test

```python
def test_api_health_endpoint(client):
    """Test API health check endpoint"""
    response = client.get("/api/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
```

### Best Practices

1. **Use Descriptive Names**: Test function names should clearly describe what is being tested
2. **Arrange-Act-Assert**: Structure tests with clear sections
3. **Isolate Tests**: Each test should be independent and not rely on other tests
4. **Use Fixtures**: Reuse common setup code via fixtures
5. **Mock External Dependencies**: Mock external APIs and services when possible
6. **Clean Up**: Clean up test data after tests complete

## Test Status

### Current Status (Main Branch)

✅ **~28 tests passing** (100% pass rate)

**Test Breakdown**:
- **Integration Tests**: ~25 tests passing
  - Agent Architecture: 6 tests ✅
  - Portfolio Management: 7 tests ✅
  - Memory System: 5 tests ✅
  - API Endpoints: 5 tests ✅
  - Analysis Targets: 1 test ✅
  - Trading Cycle Quick Test: 1 test ✅ (order recording verification)
- **E2E Tests**: 4/4 passing
  - Frontend Integration: 4 tests ✅

### Test Coverage

Current test coverage focuses on:
- Core functionality (portfolio, agents, memory)
- API endpoints
- Data consistency
- System integration

Areas that may need additional tests:
- Edge cases and error handling
- Performance and load testing
- Long-term running scenarios

## Continuous Integration

Tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r backend/requirements.txt
      - run: pytest tests/ -v
```

## Troubleshooting

### Issue: ModuleNotFoundError

**Error**: `ModuleNotFoundError: No module named 'src'`

**Solution**: Ensure you're running tests from the project root:
```powershell
cd ai-trader-ollama
pytest tests/ -v
```

### Issue: Ollama Connection Error

**Error**: `ConnectionError: Ollama service not available`

**Solution**: Start Ollama service before running tests:
```powershell
ollama serve
```

### Issue: API Server Not Running

**Error**: `ConnectionError: API server not available`

**Solution**: Start API server before running API tests:
```powershell
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000
```

## Key Test Files

For detailed information about critical test files and their priorities, see:
- **[Key Test Files Guide](../docs/KEY_TEST_FILES.md)** - Complete guide to critical, important, and supporting tests

**Quick Reference**:
- **Critical Tests** (run before deployment):
  - `test_trading_cycle_quick.py` - Order recording verification
  - `test_portfolio.py` - Portfolio & P&L calculations
  - `test_agent_architecture.py` - Agent system & tools

## Related Documentation

- [Key Test Files Guide](../docs/KEY_TEST_FILES.md) - **Critical test files and priority guide** ⭐
- [Testing Guide](../docs/TESTING.md) - Comprehensive testing documentation
- [Test Scripts Guide](../docs/TEST_SCRIPTS_GUIDE.md) - Guide for independent test scripts
- [Test Results](../docs/TEST_RESULTS.md) - Latest test execution results
- [Quick Start Guide](../docs/QUICK_START.md) - Installation and setup
- [Architecture Documentation](../docs/ARCHITECTURE.md) - System architecture

## Contributing

When adding new tests:

1. Follow the existing test structure and naming conventions
2. Add tests to the appropriate category (integration/e2e/utils)
3. Update this README if adding new test categories
4. Ensure tests pass before submitting PR
5. Add docstrings to test functions explaining what is being tested
