# Tests Directory

This directory contains all tests for the AI-Trader system.

## Directory Structure

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for system components
├── e2e/              # End-to-end tests
├── utils/            # Test utilities and helpers
├── reports/          # Test reports and coverage
├── conftest.py       # Pytest configuration and fixtures
└── pytest.ini        # Pytest configuration file
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test category
```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v
```

### Run with coverage
```bash
pytest tests/ -v --cov=backend/src --cov-report=html
```

### Run specific test file
```bash
pytest tests/integration/test_agent_architecture.py -v
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions and classes
- Mock external dependencies
- Fast execution
- High coverage target

### Integration Tests (`tests/integration/`)
- Test component interactions
- Use real dependencies where possible
- Moderate execution time
- Focus on critical paths

### E2E Tests (`tests/e2e/`)
- Test complete workflows
- Use real system components
- Slower execution
- Critical user journeys

## Test Fixtures

Common fixtures are defined in `conftest.py`:
- `test_data_dir` - Path to test data directory
- `logs_dir` - Path to logs directory
- `test_portfolio_state` - Sample portfolio state
- `sample_market_data` - Sample market data
- `sample_positions` - Sample positions

## Test Utilities

Helper functions in `tests/utils/test_helpers.py`:
- `load_test_data()` - Load test data from JSON
- `create_test_portfolio_state()` - Create test portfolio
- `create_test_order()` - Create test order
- `assert_portfolio_state_valid()` - Validate portfolio state

## Writing Tests

### Example Unit Test
```python
def test_calculate_position_size():
    from src.agents.trader_agent import _calculate_position_size
    
    size = _calculate_position_size(
        symbol="NVDA",
        recommended_stocks=["NVDA"],
        portfolio_value=10000.0,
        last_price=500.0
    )
    
    assert size > 0
    assert size <= 100  # Max shares
```

### Example Integration Test
```python
def test_trading_cycle_execution():
    from src.orchestrator.trading_cycle import execute_daily_trade
    
    result = execute_daily_trade(
        start="2025-01-01",
        end="2025-01-02"
    )
    
    assert result["ok"] is True
    assert "portfolio" in result
```

## Test Reports

Test reports are generated in `tests/reports/`:
- Coverage reports: `tests/reports/coverage/`
- HTML reports: `tests/reports/test_report_YYYYMMDD.html`

## Notes

- Tests should be independent and not rely on execution order
- Use fixtures for common setup/teardown
- Mock external API calls to avoid rate limits
- Use test data directory for sample data files

