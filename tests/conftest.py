"""
Pytest configuration and shared fixtures for AI-Trader tests
"""
import pytest
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

# Add src to path
src_dir = backend_dir / "src"
sys.path.insert(0, str(src_dir))


@pytest.fixture
def test_data_dir():
    """Return path to test data directory"""
    return Path(__file__).parent.parent / "tests" / "data"


@pytest.fixture
def logs_dir():
    """Return path to logs directory"""
    return Path(__file__).parent.parent / "data" / "logs"


@pytest.fixture
def test_portfolio_state():
    """Return a test portfolio state"""
    return {
        "cash": 10000.0,
        "initial_value": 10000.0,
        "positions": {}
    }


@pytest.fixture
def sample_market_data():
    """Return sample market data for testing"""
    return {
        "symbols": ["NVDA", "MSFT", "AAPL"],
        "stocks": {
            "NVDA": {
                "price": 500.0,
                "volume": 1000000,
                "signal_score": 0.8
            },
            "MSFT": {
                "price": 400.0,
                "volume": 2000000,
                "signal_score": 0.7
            },
            "AAPL": {
                "price": 200.0,
                "volume": 3000000,
                "signal_score": 0.6
            }
        }
    }


@pytest.fixture
def sample_positions():
    """Return sample positions for testing"""
    return {
        "NVDA": {
            "quantity": 10,
            "avg_cost": 490.0,
            "total_cost": 4900.0
        },
        "MSFT": {
            "quantity": 20,
            "avg_cost": 395.0,
            "total_cost": 7900.0
        }
    }

