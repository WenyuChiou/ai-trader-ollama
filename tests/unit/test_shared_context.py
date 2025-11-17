"""
Unit tests for SharedContext
"""
import pytest
from backend.src.utils.shared_context import SharedContext


@pytest.mark.unit
class TestSharedContext:
    """Test SharedContext class"""
    
    def test_shared_context_initialization(self):
        """Test SharedContext initialization"""
        context = SharedContext()
        assert len(context.agent_insights) == 0
        assert len(context.tool_results) == 0
        assert len(context.preliminary_conclusions) == 0
    
    def test_add_insight(self):
        """Test adding insights"""
        context = SharedContext()
        
        context.add_insight("Market Analyst", "stance", "bullish")
        context.add_insight("Market Analyst", "key_points", ["point1", "point2"])
        
        assert "Market Analyst" in context.agent_insights
        assert "stance" in context.agent_insights["Market Analyst"]
        assert "key_points" in context.agent_insights["Market Analyst"]
        assert context.agent_insights["Market Analyst"]["stance"]["data"] == "bullish"
    
    def test_get_relevant_insights(self):
        """Test getting relevant insights"""
        context = SharedContext()
        
        context.add_insight("Market Analyst", "stance", "bullish")
        context.add_insight("Technical Analyst", "stance", "neutral")
        context.add_insight("Market Analyst", "key_points", ["point1"])
        
        relevant = context.get_relevant_insights("Technical Analyst", ["stance", "key_points"])
        
        assert "Market Analyst_stance" in relevant
        assert relevant["Market Analyst_stance"] == "bullish"
        assert "Market Analyst_key_points" in relevant
    
    def test_tool_result_sharing(self):
        """Test tool result sharing"""
        context = SharedContext()
        
        result = {"ok": True, "data": "test_data"}
        context.add_tool_result("get_market_indices", result)
        
        retrieved = context.get_tool_result("get_market_indices")
        assert retrieved == result
        
        assert context.get_tool_result("nonexistent_tool") is None
    
    def test_market_data(self):
        """Test market data storage"""
        context = SharedContext()
        
        market_data = {"symbols": ["NVDA", "MSFT"], "vix": 20}
        context.set_market_data(market_data)
        
        retrieved = context.get_market_data()
        assert retrieved == market_data
    
    def test_preliminary_conclusions(self):
        """Test preliminary conclusions"""
        context = SharedContext()
        
        context.add_preliminary_conclusion("market_trend", "upward")
        context.add_preliminary_conclusion("risk_level", "low")
        
        conclusions = context.get_preliminary_conclusions()
        assert "market_trend" in conclusions
        assert conclusions["market_trend"]["value"] == "upward"
    
    def test_summary(self):
        """Test summary generation"""
        context = SharedContext()
        
        context.add_insight("Market Analyst", "stance", "bullish")
        context.add_tool_result("get_market_indices", {"ok": True})
        context.add_preliminary_conclusion("trend", "up")
        
        summary = context.get_summary()
        
        assert summary["agents_count"] == 1
        assert summary["tool_results_count"] == 1
        assert summary["preliminary_conclusions_count"] == 1
        assert "Market Analyst" in summary["agents"]
    
    def test_clear(self):
        """Test clearing context"""
        context = SharedContext()
        
        context.add_insight("Market Analyst", "stance", "bullish")
        context.add_tool_result("tool1", {"ok": True})
        context.add_preliminary_conclusion("key", "value")
        
        assert len(context.agent_insights) > 0
        assert len(context.tool_results) > 0
        assert len(context.preliminary_conclusions) > 0
        
        context.clear()
        
        assert len(context.agent_insights) == 0
        assert len(context.tool_results) == 0
        assert len(context.preliminary_conclusions) == 0

