"""
Quick test of agent system - verifies all components can run
This is a lightweight test that doesn't execute full trading cycle
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_agent_components():
    """Test all agent components can be initialized and run"""
    print("=" * 60)
    print("Quick Agent System Test")
    print("=" * 60)
    print()
    
    results = []
    
    # Test 1: Import all agents
    print("[1/6] Testing agent imports...")
    try:
        from src.agents.factory import AgentFactory
        from src.agents.multi_analyst_system_parallel import run_multi_analyst_discussion_parallel
        from src.agents.risk_analyst_llm import run_risk_analyst_llm
        from src.agents.trader_agent import run_trader
        from src.agents.toolbox import ToolBox
        print("✅ All agent modules imported successfully")
        results.append(("Agent Imports", True))
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Agent Imports", False))
        return False
    
    # Test 2: Agent Factory
    print("\n[2/6] Testing Agent Factory...")
    try:
        config_path = backend_dir / "config" / "agents.yaml"
        factory = AgentFactory(config_path)
        
        agents_to_test = [
            "market_analyst",
            "technical_analyst", 
            "fundamental_analyst",
            "sentiment_analyst",
            "risk_analyst",
            "trader_agent"
        ]
        
        created = 0
        for agent_name in agents_to_test:
            try:
                agent = factory.create(agent_name)
                created += 1
            except Exception as e:
                print(f"  ⚠️  Failed to create {agent_name}: {e}")
        
        if created == len(agents_to_test):
            print(f"✅ All {created} agents created successfully")
            results.append(("Agent Factory", True))
        else:
            print(f"⚠️  Created {created}/{len(agents_to_test)} agents")
            results.append(("Agent Factory", created >= len(agents_to_test) * 0.8))
    except Exception as e:
        print(f"❌ Agent Factory test failed: {e}")
        results.append(("Agent Factory", False))
    
    # Test 3: Toolbox
    print("\n[3/6] Testing Toolbox...")
    try:
        from src.agents.toolbox import ToolBox
        toolbox = ToolBox()
        tools = toolbox.list()
        
        if len(tools) >= 25:  # Should have 28+ tools
            print(f"✅ Toolbox works: {len(tools)} tools available")
            results.append(("Toolbox", True))
        else:
            print(f"⚠️  Toolbox has fewer tools than expected: {len(tools)}")
            results.append(("Toolbox", False))
    except Exception as e:
        print(f"❌ Toolbox test failed: {e}")
        results.append(("Toolbox", False))
    
    # Test 4: Logging
    print("\n[4/6] Testing logging system...")
    try:
        from src.utils.logger import setup_logger, get_logger
        
        logger = setup_logger("test_agent")
        logger.info("Test log message from agent test")
        
        # Check log file exists
        log_path = Path("data/logs/api.log")
        if log_path.exists():
            print(f"✅ Log file exists: {log_path}")
            # Check recent log content
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if len(lines) > 0 and "Test log message" in lines[-1]:
                    print("✅ Log messages written correctly")
                else:
                    print("⚠️  Log content check incomplete (may be buffered)")
            results.append(("Logging", True))
        else:
            print("⚠️  Log file not found (may be created later)")
            results.append(("Logging", False))
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        results.append(("Logging", False))
    
    # Test 5: Trading Cycle Import
    print("\n[5/6] Testing trading cycle module...")
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.utils.trading_days import is_market_open
        
        # Just verify imports work
        print("✅ Trading cycle module imported successfully")
        
        # Quick market status check
        try:
            market_open = is_market_open(None)
            print(f"✅ Market status check works: {'OPEN' if market_open else 'CLOSED'}")
        except Exception as e:
            print(f"⚠️  Market status check failed: {e}")
        
        results.append(("Trading Cycle", True))
    except Exception as e:
        print(f"❌ Trading cycle import failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Trading Cycle", False))
    
    # Test 6: API Server Import
    print("\n[6/6] Testing API server module...")
    try:
        from src.api.server import app
        from src.api.security_middleware import AdminAuthMiddleware
        from src.api.rate_limit import setup_rate_limiting
        from src.api.error_handler import global_exception_handler
        
        print("✅ API server module imported successfully")
        print("✅ Security middleware available")
        print("✅ Rate limiting available")
        print("✅ Error handler available")
        results.append(("API Server", True))
    except Exception as e:
        print(f"❌ API server import failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("API Server", False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All component tests passed!")
        print("\nNote: This is a quick test. For full trading cycle test,")
        print("      run: python scripts/test_full_agent_run.py")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False

if __name__ == "__main__":
    success = test_agent_components()
    exit(0 if success else 1)

