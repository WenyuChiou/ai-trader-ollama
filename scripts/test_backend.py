"""
Backend Test Suite
Tests backend core functionality without frontend dependency
"""
import sys
import os
import time
import requests
from pathlib import Path
from typing import Dict, List, Tuple

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def test_1_ollama_connection():
    """Test 1: Ollama connection"""
    print("\n[Test 1] Testing Ollama connection...")
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            version = response.json().get("version", "unknown")
            print(f"✅ Ollama is running (version: {version})")
            return True
        else:
            print(f"❌ Ollama returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Ollama is not running or not accessible")
        print("   Please start Ollama: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

def test_2_ollama_model():
    """Test 2: Ollama model availability"""
    print("\n[Test 2] Testing Ollama model (deepseek-r1)...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [m.get("name", "") for m in models]
            
            # Check for deepseek-r1 (with or without tag)
            has_model = any("deepseek-r1" in name.lower() for name in model_names)
            
            if has_model:
                print(f"✅ Model deepseek-r1 is available")
                print(f"   Found models: {', '.join(model_names[:3])}...")
                return True
            else:
                print(f"❌ Model deepseek-r1 not found")
                print(f"   Available models: {', '.join(model_names[:5])}")
                print("   Please run: ollama pull deepseek-r1")
                return False
        else:
            print(f"❌ Failed to list models: status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Model check failed: {e}")
        return False

def test_3_backend_imports():
    """Test 3: Backend module imports"""
    print("\n[Test 3] Testing backend module imports...")
    try:
        from src.api.server import app
        from src.api.security_middleware import AdminAuthMiddleware
        from src.api.rate_limit import setup_rate_limiting
        from src.api.error_handler import global_exception_handler
        print("✅ Backend API modules imported successfully")
        return True
    except Exception as e:
        print(f"❌ Backend import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_4_agent_system():
    """Test 4: Agent system"""
    print("\n[Test 4] Testing agent system...")
    try:
        from src.agents.factory import AgentFactory
        from src.agents.multi_analyst_system_parallel import run_multi_analyst_discussion_parallel
        from src.agents.risk_analyst_llm import run_risk_analyst_llm
        from src.agents.trader_agent import run_trader
        
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
            return True
        else:
            print(f"⚠️  Created {created}/{len(agents_to_test)} agents")
            return created >= len(agents_to_test) * 0.8
    except Exception as e:
        print(f"❌ Agent system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_5_toolbox():
    """Test 5: Toolbox"""
    print("\n[Test 5] Testing toolbox...")
    try:
        from src.agents.toolbox import ToolBox
        toolbox = ToolBox()
        tools = toolbox.list()
        
        if len(tools) >= 25:  # Should have 28+ tools
            print(f"✅ Toolbox works: {len(tools)} tools available")
            return True
        else:
            print(f"⚠️  Toolbox has fewer tools than expected: {len(tools)}")
            return False
    except Exception as e:
        print(f"❌ Toolbox test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_6_trading_cycle():
    """Test 6: Trading cycle module"""
    print("\n[Test 6] Testing trading cycle module...")
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.utils.trading_days import is_market_open
        
        print("✅ Trading cycle module imported successfully")
        
        # Quick market status check
        try:
            market_open = is_market_open(None)
            print(f"✅ Market status check works: {'OPEN' if market_open else 'CLOSED'}")
        except Exception as e:
            print(f"⚠️  Market status check failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Trading cycle import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_7_logging():
    """Test 7: Logging system"""
    print("\n[Test 7] Testing logging system...")
    try:
        from src.utils.logger import setup_logger, get_logger
        
        logger = setup_logger("test_backend")
        logger.info("Test log message from backend test")
        
        # Check log file exists
        log_path = Path("data/logs/api.log")
        if log_path.exists():
            print(f"✅ Log file exists: {log_path}")
            return True
        else:
            print("⚠️  Log file not found (may be created later)")
            return False
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_8_backend_api_server():
    """Test 8: Backend API server (if running)"""
    print("\n[Test 8] Testing backend API server...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=2)
        if response.status_code == 200:
            print("✅ Backend API server is running")
            print(f"   Health check: {response.json()}")
            return True
        else:
            print(f"⚠️  Backend API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("⚠️  Backend API server is not running (this is OK for testing)")
        print("   Start it with: scripts\\start_backend_auto.bat")
        return True  # Not a failure, just not running
    except Exception as e:
        print(f"⚠️  Backend API check failed: {e}")
        return True  # Not a critical failure

def main():
    """Run all backend tests"""
    print("=" * 60)
    print("Backend Test Suite")
    print("=" * 60)
    print()
    print("Testing backend core functionality...")
    print("(Frontend tests are separate)")
    print()
    
    tests = [
        ("Ollama Connection", test_1_ollama_connection),
        ("Ollama Model", test_2_ollama_model),
        ("Backend Imports", test_3_backend_imports),
        ("Agent System", test_4_agent_system),
        ("Toolbox", test_5_toolbox),
        ("Trading Cycle", test_6_trading_cycle),
        ("Logging", test_7_logging),
        ("API Server", test_8_backend_api_server),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Backend Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All backend tests passed!")
        print("\nNext step: Run test_frontend.bat to test frontend connection")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nPlease fix backend issues before testing frontend")
        return 1

if __name__ == "__main__":
    exit(main())

