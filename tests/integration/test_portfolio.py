"""
Integration tests for Portfolio and Position Management
Tests position recording, equity tracking, P&L calculation, visualization
"""
import pytest
from pathlib import Path
import sys
import json
import tempfile
import shutil

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))


@pytest.mark.integration
class TestPortfolio:
    """Test portfolio management"""
    
    def test_portfolio_creation(self):
        """Test portfolio can be created"""
        from src.data.portfolio import Portfolio
        
        portfolio = Portfolio()
        assert portfolio is not None
        assert portfolio.cash == 10000.0
        assert len(portfolio._positions) == 0
    
    def test_portfolio_add_position(self):
        """Test adding position to portfolio"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        position = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        portfolio._positions["NVDA"] = position
        
        assert "NVDA" in portfolio._positions
        assert portfolio._positions["NVDA"].quantity == 10
        assert portfolio._positions["NVDA"].avg_cost == 500.0
        assert portfolio._positions["NVDA"].total_cost == 5000.0
    
    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        
        last_prices = {"NVDA": 510.0}
        # value() returns total value (cash + equity), equity_value() returns only equity
        equity_value = portfolio.equity_value(last_prices)
        total_value = portfolio.value(last_prices)
        
        assert equity_value == 5100.0  # 10 * 510
        assert total_value == 15100.0  # 10000 (cash) + 5100 (equity)
    
    def test_portfolio_pnl_calculation(self):
        """Test portfolio P&L calculation"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        
        last_prices = {"NVDA": 510.0}
        pnl = portfolio.total_pnl(last_prices)
        
        assert pnl == 100.0  # (510 - 500) * 10
    
    def test_position_pnl_calculation(self):
        """Test individual position P&L calculation"""
        from src.data.portfolio import Portfolio, Position
        
        portfolio = Portfolio()
        portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        
        pnl = portfolio.get_position_pnl("NVDA", 510.0)
        
        assert pnl["unrealized_pnl"] == 100.0
        assert pnl["unrealized_pnl_pct"] == 2.0  # (510-500)/500 * 100
    
    def test_portfolio_state_save_load(self, tmp_path):
        """Test portfolio state save and load"""
        from src.data.portfolio import Portfolio, Position
        import json
        
        # Create portfolio
        portfolio = Portfolio()
        portfolio.cash = 5000.0
        portfolio._positions["NVDA"] = Position(symbol="NVDA", quantity=10, avg_cost=500.0, total_cost=5000.0)
        
        # Save state
        state_file = tmp_path / "portfolio_state.json"
        state = {
            "cash": portfolio.cash,
            "initial_value": portfolio.initial_value,
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": getattr(pos, "total_cost", pos.avg_cost * pos.quantity)
                }
                for symbol, pos in portfolio._positions.items()
            }
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2)
        
        # Load state
        with open(state_file, 'r', encoding='utf-8') as f:
            loaded_state = json.load(f)
        
        assert loaded_state["cash"] == 5000.0
        assert "NVDA" in loaded_state["positions"]
        assert loaded_state["positions"]["NVDA"]["quantity"] == 10
    
    def test_equity_tracking_structure(self):
        """Test equity tracking structure"""
        from src.data.equity_tracker import EquityTracker
        from pathlib import Path
        
        # Use temporary directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            tracker = EquityTracker(root=Path(tmpdir))
            
            snapshot = {
                "cash": 5000.0,
                "equity_value": 5000.0,
                "total_value": 10000.0,
                "positions_detail": {}
            }
            
            # Test recording
            tracker.record_daily_equity(
                date_str="2025-01-01",
                portfolio_snapshot=snapshot
            )
            
            # Verify file was created
            equity_file = Path(tmpdir) / "equity_history.jsonl"
            assert equity_file.exists()
            
            # Verify content
            with open(equity_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) > 0
                record = json.loads(lines[0])
                assert record["date"] == "2025-01-01"
                assert record["total_value"] == 10000.0

