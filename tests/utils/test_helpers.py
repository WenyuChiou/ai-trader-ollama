"""
Test helper functions for AI-Trader tests
"""
import json
from pathlib import Path
from typing import Dict, Any


def load_test_data(filename: str) -> Dict[str, Any]:
    """Load test data from JSON file"""
    test_data_dir = Path(__file__).parent.parent.parent / "tests" / "data"
    file_path = test_data_dir / filename
    if file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def create_test_portfolio_state(cash: float = 10000.0, positions: Dict = None) -> Dict[str, Any]:
    """Create a test portfolio state"""
    if positions is None:
        positions = {}
    return {
        "cash": cash,
        "initial_value": cash,
        "positions": positions
    }


def create_test_order(symbol: str, action: str, quantity: int, price: float) -> Dict[str, Any]:
    """Create a test order"""
    return {
        "symbol": symbol,
        "action": action,
        "quantity": quantity,
        "price": price,
        "status": "PENDING"
    }


def assert_portfolio_state_valid(state: Dict[str, Any]):
    """Assert that portfolio state is valid"""
    assert "cash" in state
    assert "initial_value" in state
    assert "positions" in state
    assert isinstance(state["cash"], (int, float))
    assert isinstance(state["initial_value"], (int, float))
    assert isinstance(state["positions"], dict)

