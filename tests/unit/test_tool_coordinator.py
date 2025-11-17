"""
Unit tests for ToolCoordinator
"""
import pytest
from backend.src.utils.tool_coordinator import ToolCoordinator


@pytest.mark.unit
class TestToolCoordinator:
    """Test ToolCoordinator class"""
    
    def test_tool_coordinator_initialization(self):
        """Test ToolCoordinator initialization"""
        coordinator = ToolCoordinator(tool_budget=15)
        assert coordinator.tool_budget == 15
        assert coordinator.tool_call_count == 0
        assert len(coordinator.tool_cache) == 0
    
    def test_cache_key_generation(self):
        """Test cache key generation"""
        coordinator = ToolCoordinator()
        
        key1 = coordinator._generate_cache_key("test_tool", {"arg1": "value1"})
        key2 = coordinator._generate_cache_key("test_tool", {"arg1": "value1"})
        key3 = coordinator._generate_cache_key("test_tool", {"arg1": "value2"})
        
        assert key1 == key2  # Same args should generate same key
        assert key1 != key3   # Different args should generate different key
    
    def test_tool_request_caching(self):
        """Test tool request caching"""
        coordinator = ToolCoordinator(tool_budget=15)
        
        call_count = [0]
        
        def mock_execute(tool_name, args):
            call_count[0] += 1
            return {"ok": True, "result": f"result_{call_count[0]}"}
        
        # First call
        result1 = coordinator.request_tool("agent1", "test_tool", {"arg": "value"}, mock_execute)
        assert call_count[0] == 1
        assert result1["cached"] is False
        
        # Second call with same args (should use cache)
        result2 = coordinator.request_tool("agent2", "test_tool", {"arg": "value"}, mock_execute)
        assert call_count[0] == 1  # Should not increment
        assert result2["cached"] is True
    
    def test_tool_budget_enforcement(self):
        """Test tool budget enforcement"""
        coordinator = ToolCoordinator(tool_budget=2)
        
        def mock_execute(tool_name, args):
            return {"ok": True, "result": "result"}
        
        # First two calls should succeed
        result1 = coordinator.request_tool("agent1", "tool1", {}, mock_execute)
        result2 = coordinator.request_tool("agent2", "tool2", {}, mock_execute)
        
        assert result1["ok"] is True
        assert result2["ok"] is True
        
        # Third call should fail (budget exceeded)
        result3 = coordinator.request_tool("agent3", "tool3", {}, mock_execute)
        assert result3["ok"] is False
        assert "budget exceeded" in result3["error"].lower()
    
    def test_statistics(self):
        """Test statistics generation"""
        coordinator = ToolCoordinator(tool_budget=10)
        
        def mock_execute(tool_name, args):
            return {"ok": True, "result": "result"}
        
        # Make some calls
        coordinator.request_tool("agent1", "tool1", {}, mock_execute)
        coordinator.request_tool("agent2", "tool1", {}, mock_execute)  # Should cache
        
        stats = coordinator.get_statistics()
        
        assert stats["tool_call_count"] == 1
        assert stats["cache_hits"] == 1
        assert stats["cache_misses"] == 1
        assert stats["cache_hit_rate"] == 50.0
    
    def test_reset(self):
        """Test coordinator reset"""
        coordinator = ToolCoordinator(tool_budget=10)
        
        def mock_execute(tool_name, args):
            return {"ok": True, "result": "result"}
        
        coordinator.request_tool("agent1", "tool1", {}, mock_execute)
        
        assert coordinator.tool_call_count > 0
        assert len(coordinator.tool_cache) > 0
        
        coordinator.reset()
        
        assert coordinator.tool_call_count == 0
        assert len(coordinator.tool_cache) == 0

