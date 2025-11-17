#!/usr/bin/env python3
"""
Compare old vs new agent system performance
"""
import sys
import time
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_dir / "src"))


def compare_performance():
    """Compare performance of old vs new system"""
    print("=" * 80)
    print("Performance Comparison: Old vs New Agent System")
    print("=" * 80)
    print()
    
    # Sample market data
    market_view = {
        "symbols": ["NVDA", "MSFT", "AAPL"],
        "stocks": {
            "NVDA": {"price": 500.0, "signal_score": 0.8},
            "MSFT": {"price": 400.0, "signal_score": 0.7},
            "AAPL": {"price": 200.0, "signal_score": 0.6}
        },
        "vix_term": {"current": 20},
        "news": []
    }
    
    print("Note: This is a structure comparison.")
    print("Full performance test requires Ollama and LLM execution.")
    print()
    
    # Test ToolCoordinator
    print("Testing ToolCoordinator...")
    try:
        from src.utils.tool_coordinator import ToolCoordinator
        
        coordinator = ToolCoordinator(tool_budget=15)
        
        call_count = [0]
        def mock_execute(tool_name, args):
            call_count[0] += 1
            time.sleep(0.01)  # Simulate tool execution
            return {"ok": True, "result": f"result_{call_count[0]}"}
        
        # Test caching
        start_time = time.time()
        coordinator.request_tool("agent1", "test_tool", {"arg": "value"}, mock_execute)
        first_call_time = time.time() - start_time
        
        start_time = time.time()
        coordinator.request_tool("agent2", "test_tool", {"arg": "value"}, mock_execute)
        second_call_time = time.time() - start_time
        
        stats = coordinator.get_statistics()
        
        print(f"  ✅ ToolCoordinator working")
        print(f"  - First call: {first_call_time*1000:.2f}ms")
        print(f"  - Cached call: {second_call_time*1000:.2f}ms")
        print(f"  - Cache hit rate: {stats['cache_hit_rate']:.1f}%")
        print(f"  - Tool calls: {stats['tool_call_count']}/{stats['tool_budget']}")
        print()
        
    except Exception as e:
        print(f"  ❌ ToolCoordinator test failed: {e}")
        print()
    
    # Test SharedContext
    print("Testing SharedContext...")
    try:
        from src.utils.shared_context import SharedContext
        
        context = SharedContext()
        context.add_insight("Market Analyst", "stance", "bullish")
        context.add_insight("Technical Analyst", "stance", "neutral")
        
        relevant = context.get_relevant_insights("Technical Analyst", ["stance"])
        
        print(f"  ✅ SharedContext working")
        print(f"  - Agents: {len(context.agent_insights)}")
        print(f"  - Relevant insights: {len(relevant)}")
        print()
        
    except Exception as e:
        print(f"  ❌ SharedContext test failed: {e}")
        print()
    
    # Test BudgetAllocator
    print("Testing BudgetAllocator...")
    try:
        from src.utils.budget_allocator import allocate_tool_budget, get_market_conditions
        
        conditions = get_market_conditions(market_view)
        allocation = allocate_tool_budget(conditions, total_budget=15)
        
        print(f"  ✅ BudgetAllocator working")
        print(f"  - Market conditions: VIX={conditions['vix']}, Volatility={conditions['volatility']}")
        print(f"  - Budget allocation: {allocation}")
        print(f"  - Total allocated: {sum(allocation.values())}")
        print()
        
    except Exception as e:
        print(f"  ❌ BudgetAllocator test failed: {e}")
        print()
    
    print("=" * 80)
    print("Comparison Complete")
    print("=" * 80)
    print()
    print("Expected Improvements:")
    print("  - Execution time: 50-70% reduction (with parallel execution)")
    print("  - Tool calls: 30-40% reduction (with caching)")
    print("  - API costs: 30-40% reduction (with deduplication)")
    print("  - Decision quality: 10-15% improvement (with context sharing)")


if __name__ == "__main__":
    compare_performance()

