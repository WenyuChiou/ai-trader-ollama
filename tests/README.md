# Tests Directory

This directory contains all tests for the AI-Trader system.

## ⚠️ Branch-Specific Tests

**Important**: Test files differ between branches!

### Main Branch (`main`)

**Test Coverage**: Core system tests only (production-ready features)

**Test Files**:
- `tests/integration/` - Core system integration tests
  - `test_agent_architecture.py` - Agent system tests
  - `test_portfolio.py` - Portfolio management tests
  - `test_memory.py` - Memory system tests
  - `test_api.py` - API endpoint tests
- `tests/e2e/` - End-to-end tests
  - `test_frontend.py` - Frontend integration tests

**Does NOT Include**:
- ❌ `tests/unit/` - Optimization component tests (only in feature branch)
- ❌ Optimization components (ToolCoordinator, SharedContext, BudgetAllocator)

**Total Tests**: ~28 tests

**Purpose**: Tests for stable, production-ready features

### Feature Branch (`feature/system-optimization`)

**Test Coverage**: All tests including optimization components

**Test Files**:
- `tests/integration/` - Core system integration tests (same as main)
- `tests/e2e/` - End-to-end tests (same as main)
- `tests/unit/` - **Optimization component unit tests** (feature branch only)
  - `test_tool_coordinator.py` - ToolCoordinator tests
  - `test_shared_context.py` - SharedContext tests
  - `test_budget_allocator.py` - BudgetAllocator tests

**Additional Components** (feature branch only):
- `backend/src/utils/tool_coordinator.py`
- `backend/src/utils/shared_context.py`
- `backend/src/utils/budget_allocator.py`
- `backend/src/agents/multi_analyst_system_parallel.py`

**Total Tests**: ~48 tests

**Purpose**: Tests for new optimization features under development

### Checking Your Current Branch

**To check which branch you're on**:
```bash
git branch
# or
git status
```

**If you see `* main`**: You're on main branch (core tests only, ~28 tests)
**If you see `* feature/system-optimization`**: You're on feature branch (all tests, ~48 tests)

---

## Directory Structure

```
tests/
├── integration/       # Integration tests for system components
├── e2e/              # End-to-end tests
├── utils/            # Test utilities and helpers
├── reports/          # Test reports and coverage
├── conftest.py       # Pytest configuration and fixtures
└── pytest.ini        # Pytest configuration file
```

**Note**: `tests/unit/` directory only exists in `feature/system-optimization` branch.

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test category
```bash
# Integration tests only
pytest tests/integration/ -v

# E2E tests only
pytest tests/e2e/ -v
```

**Note**: Unit tests (`pytest tests/unit/ -v`) are only available in `feature/system-optimization` branch.

### Run with coverage
```bash
pytest tests/ -v --cov=backend/src --cov-report=html
```

### Run specific test file
```bash
pytest tests/integration/test_agent_architecture.py -v
```

## Test Categories

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

## Notes

- Tests should be independent and not rely on execution order
- Use fixtures for common setup/teardown
- Mock external API calls to avoid rate limits
- Use test data directory for sample data files
