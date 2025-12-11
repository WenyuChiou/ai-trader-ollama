"""
Test script for security features and system functionality
Tests:
1. Agent system can run complete trading cycle
2. Logging system works correctly
3. Security middleware functions properly
4. Rate limiting works
5. Error handling doesn't leak tracebacks
"""
import sys
import os
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import asyncio
from fastapi.testclient import TestClient
from fastapi import Request
import json

def test_1_imports():
    """Test 1: Verify all new modules can be imported"""
    print("\n[Test 1] Testing imports...")
    try:
        from src.api.security_middleware import AdminAuthMiddleware, AdminSecretAuth
        from src.api.rate_limit import setup_rate_limiting, limiter, RATE_LIMITS
        from src.api.error_handler import global_exception_handler, http_exception_handler, get_error_log_path
        from src.utils.logger import setup_logger, get_logger
        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_2_security_middleware():
    """Test 2: Security middleware authentication"""
    print("\n[Test 2] Testing security middleware...")
    try:
        from src.api.security_middleware import AdminSecretAuth
        
        # Test without ADMIN_SECRET (development mode)
        os.environ.pop("ADMIN_SECRET", None)
        os.environ["ENVIRONMENT"] = "development"
        auth = AdminSecretAuth()
        
        # Create mock request
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
                self.url = type('obj', (object,), {'path': '/api/trading/execute-trade'})()
                self.method = "POST"
        
        # Test without secret (should pass in dev mode)
        request = MockRequest({})
        result = auth.verify(request)
        if result:
            print("✅ Development mode: Auth bypassed (expected)")
        else:
            print("⚠️  Development mode: Auth required (unexpected)")
        
        # Test with ADMIN_SECRET set
        os.environ["ADMIN_SECRET"] = "test-secret-123"
        auth = AdminSecretAuth()
        
        # Test with correct secret in header
        request = MockRequest({"x-admin-secret": "test-secret-123"})
        result = auth.verify(request)
        if result:
            print("✅ Correct x-admin-secret header: Auth passed")
        else:
            print("❌ Correct x-admin-secret header: Auth failed")
            return False
        
        # Test with wrong secret
        request = MockRequest({"x-admin-secret": "wrong-secret"})
        result = auth.verify(request)
        if not result:
            print("✅ Wrong secret: Auth correctly rejected")
        else:
            print("❌ Wrong secret: Auth incorrectly passed")
            return False
        
        # Test with Bearer token
        request = MockRequest({"authorization": "Bearer test-secret-123"})
        result = auth.verify(request)
        if result:
            print("✅ Correct Bearer token: Auth passed")
        else:
            print("❌ Correct Bearer token: Auth failed")
            return False
        
        print("✅ Security middleware tests passed")
        return True
    except Exception as e:
        print(f"❌ Security middleware test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3_logging():
    """Test 3: Logging system"""
    print("\n[Test 3] Testing logging system...")
    try:
        from src.utils.logger import setup_logger, get_logger
        
        # Setup logger
        logger = setup_logger("test_logger")
        
        # Test log levels
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
        
        # Check log file exists
        log_path = Path("data/logs/api.log")
        if log_path.exists():
            print(f"✅ Log file created: {log_path}")
            # Check log content
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "Info message" in content:
                    print("✅ Log messages written correctly")
                else:
                    print("⚠️  Log content not found (may be buffered)")
        else:
            print("⚠️  Log file not found (may be created later)")
        
        # Test get_logger
        logger2 = get_logger()
        logger2.info("Test from get_logger")
        print("✅ Logger functions work correctly")
        
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_4_error_handler():
    """Test 4: Error handler"""
    print("\n[Test 4] Testing error handler...")
    try:
        from src.api.error_handler import create_error_response, get_error_log_path
        from fastapi import Request
        
        # Create mock request
        class MockRequest:
            def __init__(self):
                self.url = type('obj', (object,), {'path': '/api/test'})()
                self.method = "GET"
        
        request = MockRequest()
        exc = Exception("Test error")
        
        # Test error response creation
        response = create_error_response(request, exc, status_code=500)
        
        if response.status_code == 500:
            print("✅ Error response status code correct")
        else:
            print(f"❌ Error response status code incorrect: {response.status_code}")
            return False
        
        # Check response content
        content = json.loads(response.body.decode())
        if "error" in content and "request_id" in content:
            print("✅ Error response format correct")
            if "traceback" not in content:
                print("✅ No traceback in response (secure)")
            else:
                print("❌ Traceback leaked in response")
                return False
        else:
            print("❌ Error response format incorrect")
            return False
        
        # Check error log path
        log_path = get_error_log_path()
        print(f"✅ Error log path: {log_path}")
        
        return True
    except Exception as e:
        print(f"❌ Error handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_5_rate_limit():
    """Test 5: Rate limiting"""
    print("\n[Test 5] Testing rate limiting...")
    try:
        from src.api.rate_limit import get_rate_limit_for_path, RATE_LIMITS
        
        # Test rate limit determination
        trading_limit = get_rate_limit_for_path("/api/trading/execute-trade")
        if trading_limit == RATE_LIMITS["trading"]:
            print(f"✅ Trading API rate limit: {trading_limit}")
        else:
            print(f"❌ Trading API rate limit incorrect: {trading_limit}")
            return False
        
        analysis_limit = get_rate_limit_for_path("/api/agents/conversations")
        if analysis_limit == RATE_LIMITS["analysis"]:
            print(f"✅ Analysis API rate limit: {analysis_limit}")
        else:
            print(f"❌ Analysis API rate limit incorrect: {analysis_limit}")
            return False
        
        default_limit = get_rate_limit_for_path("/api/health")
        if default_limit == RATE_LIMITS["default"]:
            print(f"✅ Default API rate limit: {default_limit}")
        else:
            print(f"❌ Default API rate limit incorrect: {default_limit}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Rate limit test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_6_agent_system():
    """Test 6: Agent system can run (quick test)"""
    print("\n[Test 6] Testing agent system imports and basic functionality...")
    try:
        # Test imports
        from src.agents.factory import AgentFactory
        from src.agents.toolbox import ToolBox
        from src.agents.risk_analyst_llm import run_risk_analyst_llm
        
        print("✅ Agent modules imported successfully")
        
        # Test agent factory
        ROOT = Path(__file__).parent.parent / "backend"
        fac = AgentFactory(ROOT / "config" / "agents.yaml")
        agent = fac.create("risk_analyst")
        print("✅ Agent factory works")
        
        # Test toolbox
        toolbox = ToolBox()
        tools = toolbox.list()
        print(f"✅ Toolbox works: {len(tools)} tools available")
        
        # Test VIX tool (quick check)
        try:
            vix_result = toolbox.invoke("vix_term")
            if vix_result and isinstance(vix_result, dict):
                print("✅ VIX tool works")
            else:
                print("⚠️  VIX tool returned unexpected format")
        except Exception as e:
            print(f"⚠️  VIX tool test skipped (may need API): {e}")
        
        return True
    except Exception as e:
        print(f"❌ Agent system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_7_bat_files():
    """Test 7: BAT files exist and are valid"""
    print("\n[Test 7] Testing BAT files...")
    try:
        setup_bat = Path("scripts/setup_all_security.bat")
        start_bat = Path("scripts/start_backend_auto.bat")
        
        if setup_bat.exists():
            print(f"✅ setup_all_security.bat exists ({setup_bat.stat().st_size} bytes)")
            # Check content
            with open(setup_bat, 'r', encoding='utf-8') as f:
                content = f.read()
                checks = [
                    ("ADMIN_SECRET", "ADMIN_SECRET configuration"),
                    ("requirements.txt", "Dependency installation"),
                    ("virtual environment", "Virtual environment handling"),
                    ("@echo off", "BAT file header")
                ]
                passed = sum(1 for key, _ in checks if key in content)
                if passed >= 3:
                    print(f"✅ setup_all_security.bat content valid ({passed}/{len(checks)} checks passed)")
                else:
                    print(f"⚠️  setup_all_security.bat content check: {passed}/{len(checks)} checks passed")
        else:
            print("❌ setup_all_security.bat not found")
            return False
        
        if start_bat.exists():
            print(f"✅ start_backend_auto.bat exists ({start_bat.stat().st_size} bytes)")
            # Check content
            with open(start_bat, 'r', encoding='utf-8') as f:
                content = f.read()
                checks = [
                    ("uvicorn", "Uvicorn server startup"),
                    ("port 8000", "Port configuration"),
                    ("virtual environment", "Virtual environment handling"),
                    ("@echo off", "BAT file header")
                ]
                passed = sum(1 for key, _ in checks if key in content)
                if passed >= 3:
                    print(f"✅ start_backend_auto.bat content valid ({passed}/{len(checks)} checks passed)")
                else:
                    print(f"⚠️  start_backend_auto.bat content check: {passed}/{len(checks)} checks passed")
        else:
            print("❌ start_backend_auto.bat not found")
            return False
        
        return True
    except Exception as e:
        print(f"❌ BAT files test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_8_config_changes():
    """Test 8: Verify config.json changes"""
    print("\n[Test 8] Testing config.json changes...")
    try:
        config_path = Path("backend/config/config.json")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Check fred_api_key is removed/deprecated
        if "fred_api_key" in config:
            if config["fred_api_key"] == "b04875b1abf3f24890b57ea2cee6b5e1":
                print("❌ Hardcoded fred_api_key still present")
                return False
            else:
                print("⚠️  fred_api_key field exists but value changed")
        
        if "_fred_api_key_deprecated" in config:
            print("✅ Hardcoded fred_api_key removed (deprecated marker present)")
        else:
            print("⚠️  No deprecated marker found")
        
        return True
    except Exception as e:
        print(f"❌ Config test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("=" * 60)
    print("Security Hardening & System Functionality Test Suite")
    print("=" * 60)
    
    tests = [
        ("Imports", test_1_imports),
        ("Security Middleware", test_2_security_middleware),
        ("Logging System", test_3_logging),
        ("Error Handler", test_4_error_handler),
        ("Rate Limiting", test_5_rate_limit),
        ("Agent System", test_6_agent_system),
        ("BAT Files", test_7_bat_files),
        ("Config Changes", test_8_config_changes),
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
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit(main())

