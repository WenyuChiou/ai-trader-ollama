"""
Integration tests for P&L Tracking
Tests real-time P&L calculation, position P&L, total P&L, P&L history, and percentage calculations
"""
import pytest
from pathlib import Path
import sys
import json
import tempfile

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))


@pytest.mark.integration
class TestPnLTracking:
    """Test P&L tracking functionality"""
    
    def test_real_time_pnl_calculation(self):
        """Test real-time P&L calculation"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        portfolio.cash = 5000.0
        portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        portfolio._positions["MSFT"] = Position(symbol="MSFT", quantity=5, avg_cost=400.0, total_cost=2000.0)
        
        last_prices = {"NVDA": 510.0, "MSFT": 390.0}
        
        # Calculate real-time P&L
        total_pnl = portfolio.total_pnl(last_prices)
        equity_value = portfolio.equity_value(last_prices)
        total_value = portfolio.value(last_prices)
        
        # NVDA: (510 - 500) * 10 = 100
        # MSFT: (390 - 400) * 5 = -50
        # Total P&L: 100 - 50 = 50
        assert total_pnl == 50.0
        assert equity_value == 7050.0  # (510 * 10) + (390 * 5)
        assert total_value == 12050.0  # 5000 (cash) + 7050 (equity)
    
    def test_position_pnl_calculation(self):
        """Test individual position P&L calculation"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        
        # Test profitable position
        pnl = portfolio.get_position_pnl("NVDA", 510.0)
        assert pnl["unrealized_pnl"] == 100.0
        assert pnl["unrealized_pnl_pct"] == pytest.approx(2.0, rel=0.01)  # (510-500)/500 * 100
        
        # Test losing position
        pnl = portfolio.get_position_pnl("NVDA", 490.0)
        assert pnl["unrealized_pnl"] == -100.0
        assert pnl["unrealized_pnl_pct"] == pytest.approx(-2.0, rel=0.01)  # (490-500)/500 * 100
    
    def test_total_pnl_calculation(self):
        """Test total P&L calculation including multiple positions"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        portfolio.cash = 10000.0
        portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        portfolio._positions["MSFT"] = Position(symbol="MSFT", quantity=5, avg_cost=400.0, total_cost=2000.0)
        portfolio._positions["AAPL"] = Position(symbol="AAPL", quantity=20, avg_cost=150.0, total_cost=3000.0)
        
        last_prices = {
            "NVDA": 510.0,  # +100
            "MSFT": 390.0,  # -50
            "AAPL": 155.0   # +100
        }
        
        total_pnl = portfolio.total_pnl(last_prices)
        assert total_pnl == 150.0  # 100 - 50 + 100
        
        # Test total P&L percentage
        initial_value = portfolio.initial_value
        current_value = portfolio.value(last_prices)
        pnl_pct = ((current_value - initial_value) / initial_value) * 100
        assert pnl_pct == pytest.approx(1.5, rel=0.01)  # 150 / 10000 * 100
    
    def test_pnl_history_recording(self):
        """Test P&L history recording"""
        from src.data.equity_tracker import EquityTracker
        from src.data.portfolio import Portfolio, Position
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = EquityTracker(root=Path(tmpdir))
            portfolio = Portfolio()
            portfolio.cash = 5000.0
            portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
            
            last_prices = {"NVDA": 510.0}
            
            # Create snapshot
            snapshot = {
                "cash": portfolio.cash,
                "equity_value": portfolio.equity_value(last_prices),
                "total_value": portfolio.value(last_prices),
                "total_pnl": portfolio.total_pnl(last_prices),
                "positions_detail": {
                    "NVDA": {
                        "quantity": 10,
                        "avg_cost": 500.0,
                        "current_price": 510.0,
                        "unrealized_pnl": 100.0,
                        "unrealized_pnl_pct": 2.0
                    }
                }
            }
            
            # Record P&L history
            tracker.record_daily_equity(
                date_str="2025-01-01",
                portfolio_snapshot=snapshot
            )
            
            # Verify recording
            equity_file = Path(tmpdir) / "equity_history.jsonl"
            assert equity_file.exists()
            
            with open(equity_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) > 0
                record = json.loads(lines[0])
                assert record["date"] == "2025-01-01"
                assert record["total_value"] == 10100.0
                assert record.get("total_pnl") == 100.0
    
    def test_pnl_percentage_calculation(self):
        """Test P&L percentage calculation accuracy"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        portfolio.cash = 10000.0
        portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        
        # Test various price scenarios
        test_cases = [
            (510.0, 100.0, 2.0),   # +2% gain
            (520.0, 200.0, 4.0),   # +4% gain
            (490.0, -100.0, -2.0), # -2% loss
            (480.0, -200.0, -4.0), # -4% loss
            (500.0, 0.0, 0.0),     # No change
        ]
        
        for current_price, expected_pnl, expected_pct in test_cases:
            pnl = portfolio.get_position_pnl("NVDA", current_price)
            assert pnl["unrealized_pnl"] == pytest.approx(expected_pnl, rel=0.01)
            assert pnl["unrealized_pnl_pct"] == pytest.approx(expected_pct, rel=0.01)
    
    def test_multiple_positions_pnl_aggregation(self):
        """Test P&L aggregation across multiple positions"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        portfolio.cash = 10000.0
        
        # Add multiple positions with different P&L scenarios
        portfolio._positions["PROFIT"] = Position(symbol="PROFIT", quantity=10, avg_cost=100.0, total_cost=1000.0)
        portfolio._positions["LOSS"] = Position(symbol="LOSS", quantity=5, avg_cost=200.0, total_cost=1000.0)
        portfolio._positions["NEUTRAL"] = Position(symbol="NEUTRAL", quantity=20, avg_cost=50.0, total_cost=1000.0)
        
        last_prices = {
            "PROFIT": 110.0,   # +100 P&L
            "LOSS": 180.0,     # -100 P&L
            "NEUTRAL": 50.0    # 0 P&L
        }
        
        total_pnl = portfolio.total_pnl(last_prices)
        assert total_pnl == 0.0  # +100 - 100 + 0 = 0
        
        # Test individual position P&L
        profit_pnl = portfolio.get_position_pnl("PROFIT", 110.0)
        loss_pnl = portfolio.get_position_pnl("LOSS", 180.0)
        neutral_pnl = portfolio.get_position_pnl("NEUTRAL", 50.0)
        
        assert profit_pnl["unrealized_pnl"] == 100.0
        assert loss_pnl["unrealized_pnl"] == -100.0
        assert neutral_pnl["unrealized_pnl"] == 0.0

