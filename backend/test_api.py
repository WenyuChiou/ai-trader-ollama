#!/usr/bin/env python3
"""
Quick API test script
Tests basic API endpoints without starting the full server
"""
import sys
import os
from pathlib import Path

# Fix Windows encoding issues
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import json
from src.data.portfolio import Portfolio

def test_portfolio_initialization():
    """Test if portfolio can be initialized"""
    print("[TEST] Testing Portfolio initialization...")
    try:
        portfolio = Portfolio()
        print(f"  ✅ Portfolio initialized: ${portfolio.cash:,.2f} cash")
        return True
    except Exception as e:
        print(f"  ❌ Portfolio initialization failed: {e}")
        return False

def test_portfolio_state_file():
    """Test if portfolio state file exists and is valid"""
    print("[TEST] Testing portfolio state file...")
    state_file = ROOT / "data" / "logs" / "portfolio_state.json"
    
    if not state_file.exists():
        print(f"  ⚠️  Portfolio state file not found: {state_file}")
        print(f"     Run: python scripts/init_data.py")
        return False
    
    try:
        with state_file.open("r") as f:
            data = json.load(f)
        print(f"  ✅ Portfolio state file valid: ${data.get('cash', 0):,.2f} cash")
        return True
    except Exception as e:
        print(f"  ❌ Portfolio state file invalid: {e}")
        return False

def test_api_imports():
    """Test if API server can be imported"""
    print("[TEST] Testing API server imports...")
    try:
        from src.api.server import app
        print("  ✅ API server can be imported")
        return True
    except Exception as e:
        print(f"  ❌ API server import failed: {e}")
        return False

def main():
    print("=" * 60)
    print("Backend API Quick Test")
    print("=" * 60)
    print()
    
    results = []
    results.append(("Portfolio Initialization", test_portfolio_initialization()))
    results.append(("Portfolio State File", test_portfolio_state_file()))
    results.append(("API Server Imports", test_api_imports()))
    
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    all_passed = all(r for _, r in results)
    
    if all_passed:
        print()
        print("✅ All tests passed! Backend is ready.")
        print()
        print("Next steps:")
        print("  1. Start API server: python -m uvicorn src.api.server:app --reload")
        print("  2. Test in browser: http://localhost:8000")
        print("  3. Test endpoint: curl http://localhost:8000/api/portfolio/real-time")
    else:
        print()
        print("❌ Some tests failed. Please fix the issues above.")
        print()
        print("Common fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Run: python scripts/init_data.py")
        print("  - Check: backend/config/config.json exists")
        print("  - Check: backend/config/agents.yaml exists")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

