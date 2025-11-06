"""
Backend API Test Script
======================
Tests all backend API endpoints for functionality and error handling
"""

import requests
import json
import sys
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, method, endpoint, expected_status=200, data=None):
    """Test a single API endpoint"""
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"  [SKIP] {name}: Unknown method {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"  [OK] {name}: {response.status_code}")
            return True
        else:
            print(f"  [FAIL] {name}: Expected {expected_status}, got {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] {name}: Connection refused (is server running?)")
        return False
    except requests.exceptions.Timeout:
        print(f"  [ERROR] {name}: Timeout")
        return False
    except Exception as e:
        print(f"  [ERROR] {name}: {str(e)}")
        return False

def main():
    print("\n" + "="*70)
    print("BACKEND API TESTING")
    print("="*70)
    print(f"Testing API at: {BASE_URL}")
    print(f"Test time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Test portfolio endpoints
    print("[Portfolio Endpoints]")
    results['portfolio_summary'] = test_endpoint(
        "Get Portfolio Summary", "GET", "/api/portfolio/summary"
    )
    results['portfolio_realtime'] = test_endpoint(
        "Get Real-time Portfolio", "GET", "/api/portfolio/real-time"
    )
    results['portfolio_positions'] = test_endpoint(
        "Get Portfolio Positions", "GET", "/api/portfolio/positions"
    )
    results['equity_history'] = test_endpoint(
        "Get Equity History", "GET", "/api/portfolio/equity-history"
    )
    print()
    
    # Test agent endpoints
    print("[Agent Endpoints]")
    results['agent_conversations'] = test_endpoint(
        "Get Agent Conversations", "GET", "/api/agents/conversations?limit=30"
    )
    print()
    
    # Test trading endpoints
    print("[Trading Endpoints]")
    results['pending_orders'] = test_endpoint(
        "Get Pending Orders", "GET", "/api/trading/pending-orders"
    )
    results['order_history'] = test_endpoint(
        "Get Order History", "GET", "/api/trading/order-history"
    )
    # Note: Not testing execute-trade as it triggers actual trading
    print("  [SKIP] Execute Trade: Skipped (would trigger actual trading)")
    print()
    
    # Summary
    print("="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        status = "[PASSED]" if result else "[FAILED]"
        print(f"  {status} {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed ({100*passed//total if total > 0 else 0}%)")
    
    if passed == total:
        print("\n[SUCCESS] All API tests passed!")
        return 0
    else:
        print("\n[PARTIAL] Some API tests failed. Check if server is running.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

