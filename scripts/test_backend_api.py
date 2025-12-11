"""
Test Backend API endpoints
Quick test to verify backend is running and responding correctly
"""
import requests
import sys
import time

def test_backend_api():
    """Test backend API endpoints"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("Backend API Test")
    print("=" * 60)
    print()
    
    tests = [
        ("Health Check", f"{base_url}/api/health"),
        ("Root Endpoint", f"{base_url}/"),
        ("Market Status", f"{base_url}/api/market/is-open"),
        ("API Docs", f"{base_url}/docs"),
        ("System Info", f"{base_url}/api/system/info"),
    ]
    
    results = []
    
    for name, url in tests:
        try:
            print(f"Testing {name}...", end=" ")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ OK (200)")
                results.append((name, True))
            elif response.status_code == 404:
                print(f"⚠️  Not Found (404)")
                results.append((name, False))
            else:
                print(f"⚠️  Status {response.status_code}")
                results.append((name, False))
        except requests.exceptions.ConnectionError:
            print(f"❌ Connection Error (Backend not running?)")
            results.append((name, False))
        except requests.exceptions.Timeout:
            print(f"❌ Timeout")
            results.append((name, False))
        except Exception as e:
            print(f"❌ Error: {e}")
            results.append((name, False))
    
    print()
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All API tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("Make sure backend is running: scripts\\start_backend_auto.bat")
        return False

if __name__ == "__main__":
    # Wait a bit for backend to be ready
    print("Waiting for backend to be ready...")
    for i in range(10):
        try:
            response = requests.get("http://localhost:8000/api/health", timeout=2)
            if response.status_code == 200:
                print("✅ Backend is ready!")
                break
        except:
            pass
        time.sleep(1)
        if i == 4:
            print("Still waiting...")
    
    success = test_backend_api()
    sys.exit(0 if success else 1)

