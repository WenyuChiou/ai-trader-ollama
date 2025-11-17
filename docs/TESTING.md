# Testing Guide

## Test Structure

```
tests/
├── unit/              # Unit tests
├── integration/       # Integration tests
├── e2e/              # End-to-end tests
├── utils/            # Test utilities
└── reports/          # Test reports
```

## Running Tests

### All Tests
```bash
pytest tests/ -v
```

### Specific Category
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v
```

### With Coverage
```bash
pytest tests/ -v --cov=backend/src --cov-report=html
```

## Test Categories

### Unit Tests
- Test individual functions/classes
- Mock external dependencies
- Fast execution

### Integration Tests
- Test component interactions
- Use real dependencies where possible
- Moderate execution time

### E2E Tests
- Test complete workflows
- Use real system components
- Slower execution

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
```

### Example Integration Test
```python
def test_trading_cycle():
    from src.orchestrator.trading_cycle import execute_daily_trade
    
    result = execute_daily_trade(
        start="2025-01-01",
        end="2025-01-02"
    )
    
    assert result["ok"] is True
```

## Test Fixtures

Common fixtures in `tests/conftest.py`:
- `test_data_dir`: Test data directory
- `logs_dir`: Logs directory
- `test_portfolio_state`: Sample portfolio
- `sample_market_data`: Sample market data
- `sample_positions`: Sample positions

## Test Reports

Reports generated in `tests/reports/`:
- Coverage: `tests/reports/coverage/`
- HTML: `tests/reports/test_report_YYYYMMDD.html`

## See Also
- [Quick Start Guide](QUICK_START.md)
- [Architecture Documentation](ARCHITECTURE.md)

