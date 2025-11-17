"""
Unit tests for Budget Allocator
"""
import pytest
from backend.src.utils.budget_allocator import allocate_tool_budget, get_market_conditions


@pytest.mark.unit
class TestBudgetAllocator:
    """Test budget allocation"""
    
    def test_default_allocation(self):
        """Test default budget allocation"""
        allocation = allocate_tool_budget({}, total_budget=15)
        
        assert sum(allocation.values()) == 15
        assert all(budget >= 1 for budget in allocation.values())
        assert "market" in allocation
        assert "technical" in allocation
        assert "fundamental" in allocation
        assert "sentiment" in allocation
    
    def test_high_volatility_allocation(self):
        """Test allocation for high volatility"""
        conditions = {"vix": 30, "volatility": "high"}
        allocation = allocate_tool_budget(conditions, total_budget=15)
        
        # High volatility should favor technical and sentiment
        assert allocation["technical"] >= allocation["fundamental"]
        assert sum(allocation.values()) == 15
    
    def test_low_volatility_allocation(self):
        """Test allocation for low volatility"""
        conditions = {"vix": 10, "volatility": "low"}
        allocation = allocate_tool_budget(conditions, total_budget=15)
        
        # Low volatility should favor fundamentals
        assert allocation["fundamental"] >= allocation["technical"]
        assert sum(allocation.values()) == 15
    
    def test_high_news_allocation(self):
        """Test allocation for high news volume"""
        conditions = {"news_count": 15}
        allocation = allocate_tool_budget(conditions, total_budget=15)
        
        # High news should favor sentiment
        assert allocation["sentiment"] >= 4
        assert sum(allocation.values()) == 15
    
    def test_earnings_season_allocation(self):
        """Test allocation for earnings season"""
        conditions = {"earnings_count": 10}
        allocation = allocate_tool_budget(conditions, total_budget=15)
        
        # Earnings season should favor fundamentals
        assert allocation["fundamental"] >= 4
        assert sum(allocation.values()) == 15
    
    def test_get_market_conditions(self):
        """Test market conditions extraction"""
        market_view = {
            "vix_term": {"current": 26},  # > 25 to trigger "high" volatility
            "news": [{"title": "News 1"}, {"title": "News 2"}]
        }
        
        conditions = get_market_conditions(market_view)
        
        assert conditions["vix"] == 26
        assert conditions["news_count"] == 2
        assert conditions["volatility"] == "high"
    
    def test_get_market_conditions_defaults(self):
        """Test market conditions with missing data"""
        market_view = {}
        
        conditions = get_market_conditions(market_view)
        
        assert conditions["vix"] == 20  # Default
        assert conditions["news_count"] == 0
        assert conditions["volatility"] == "normal"

