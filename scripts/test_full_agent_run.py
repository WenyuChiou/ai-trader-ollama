"""
Test full agent system run
This test verifies that the complete agent system can run a trading cycle
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_full_agent_run():
    """Test complete agent system run"""
    print("=" * 60)
    print("Full Agent System Run Test")
    print("=" * 60)
    print()
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.utils.trading_days import is_market_open
        
        print("[1/4] Testing imports...")
        print("✅ All modules imported successfully")
        print()
        
        print("[2/4] Loading configuration...")
        config_path = backend_dir / "config" / "config.json"
        import json
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        universe = config.get("universe", [])[:5]  # Use first 5 stocks for quick test
        tool_budget = config.get("discussion_tool_budget", 15)
        rounds = config.get("discussion_rounds", 3)
        min_tools = config.get("discussion_min_tools", 3)
        
        print(f"✅ Configuration loaded: {len(universe)} stocks, {rounds} rounds, {tool_budget} tool budget")
        print()
        
        print("[3/4] Checking market status...")
        is_open = is_market_open(None)
        print(f"✅ Market status: {'OPEN' if is_open else 'CLOSED'}")
        print()
        
        print("[4/4] Running trading cycle (this may take 5-10 minutes)...")
        print("   Note: This is a full cycle test. It will:")
        print("   - Run all 4 analysts (Market, Technical, Fundamental, Sentiment)")
        print("   - Run Discussion Coordinator")
        print("   - Run Risk Analyst")
        print("   - Run Trader Agent")
        print("   - Execute orders (if market open)")
        print()
        
        result = execute_daily_trade(
            rounds=rounds,
            auto_tools=True,
            tool_budget=tool_budget,
            min_tools=min_tools,
            universe=universe
        )
        
        print()
        print("=" * 60)
        print("Trading Cycle Completed Successfully!")
        print("=" * 60)
        print()
        
        # Check result structure
        required_keys = ["placed_orders", "conversations_count", "risk_report", "trader_decision"]
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            print(f"⚠️  Missing keys in result: {missing_keys}")
        else:
            print("✅ Result structure complete")
        
        # Check risk report
        if "risk_report" in result:
            risk_report = result["risk_report"]
            if "risk_score" in risk_report:
                print(f"✅ Risk score: {risk_report['risk_score']}")
            if "vix_risk_score" in risk_report:
                print(f"✅ VIX risk score: {risk_report['vix_risk_score']}")
            else:
                print("⚠️  VIX risk score not in risk report")
        
        print(f"✅ Placed orders: {len(result.get('placed_orders', []))}")
        print(f"✅ Conversations: {result.get('conversations_count', 0)}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Full agent run test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_full_agent_run()
    exit(0 if success else 1)

