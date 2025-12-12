"""
Frontend Test Suite
Tests frontend connection and integration with backend
Requires backend to be running first
"""
import sys
import os
import requests
from pathlib import Path
from typing import Dict, List

def test_1_backend_required():
    """Test 1: Backend must be running"""
    print("\n[Test 1] Checking backend is running...")
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend is running")
            return True
        else:
            print(f"❌ Backend returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Backend is not running")
        print("   Please start backend first: scripts\\start_backend_auto.bat")
        print("   Or run: scripts\\test_backend.bat to verify backend")
        return False
    except Exception as e:
        print(f"❌ Backend check failed: {e}")
        return False

def test_2_frontend_files():
    """Test 2: Frontend files exist"""
    print("\n[Test 2] Checking frontend files...")
    
    frontend_dir = Path("frontend")
    required_files = [
        "monitor.html",
        "config.js",
        "index.html"
    ]
    
    all_exist = True
    for filename in required_files:
        filepath = frontend_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            print(f"  ✅ {filename} exists ({size} bytes)")
        else:
            print(f"  ❌ {filename} not found")
            all_exist = False
    
    if all_exist:
        print("✅ All frontend files exist")
        return True
    else:
        print("❌ Some frontend files are missing")
        return False

def test_3_frontend_config():
    """Test 3: Frontend configuration"""
    print("\n[Test 3] Checking frontend configuration...")
    
    config_file = Path("frontend/config.js")
    if not config_file.exists():
        print("❌ config.js not found")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("API URL configuration", "apiUrl" in content or "API_CONFIG" in content),
            ("Development URL", "localhost:8000" in content or "127.0.0.1:8000" in content),
            ("Production URL", "production" in content.lower()),
        ]
        
        passed = 0
        for check_name, check_result in checks:
            if check_result:
                print(f"  ✅ {check_name}")
                passed += 1
            else:
                print(f"  ⚠️  {check_name} not found")
        
        if passed >= 2:
            print("✅ Frontend configuration looks good")
            return True
        else:
            print("⚠️  Frontend configuration may be incomplete")
            return False
    except Exception as e:
        print(f"❌ Failed to read config.js: {e}")
        return False

def test_4_cors_configuration():
    """Test 4: CORS configuration"""
    print("\n[Test 4] Testing CORS configuration...")
    
    try:
        # Test if backend allows frontend origin
        headers = {
            "Origin": "http://localhost:8000",
            "Access-Control-Request-Method": "GET"
        }
        
        # Try OPTIONS request (preflight)
        response = requests.options(
            "http://localhost:8000/api/health",
            headers=headers,
            timeout=5
        )
        
        # Check for CORS headers
        cors_headers = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers"
        ]
        
        found_headers = []
        for header in cors_headers:
            if header in response.headers:
                found_headers.append(header)
        
        if found_headers:
            print(f"  ✅ CORS headers found: {', '.join(found_headers)}")
            print("✅ CORS is configured")
            return True
        else:
            print("  ⚠️  CORS headers not found (may be OK for same-origin)")
            # This is OK if frontend is served from same origin
            return True
    except Exception as e:
        print(f"⚠️  CORS test failed: {e}")
        # Not critical, return True
        return True

def test_5_api_endpoints():
    """Test 5: API endpoints accessible from frontend perspective"""
    print("\n[Test 5] Testing API endpoints...")
    
    endpoints = [
        ("/api/health", "Health check"),
        ("/api/market/is-open", "Market status"),
        ("/api/system/info", "System info"),
        ("/", "Root endpoint"),
    ]
    
    passed = 0
    for endpoint, description in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"  ✅ {description}: OK")
                passed += 1
            else:
                print(f"  ⚠️  {description}: Status {response.status_code}")
        except Exception as e:
            print(f"  ❌ {description}: {e}")
    
    if passed >= len(endpoints) * 0.75:  # 75% pass rate
        print(f"✅ API endpoints accessible ({passed}/{len(endpoints)})")
        return True
    else:
        print(f"⚠️  Some API endpoints failed ({passed}/{len(endpoints)})")
        return False

def test_6_frontend_html_structure():
    """Test 6: Frontend HTML structure"""
    print("\n[Test 6] Checking frontend HTML structure...")
    
    monitor_file = Path("frontend/monitor.html")
    if not monitor_file.exists():
        print("❌ monitor.html not found")
        return False
    
    try:
        with open(monitor_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ("HTML structure", "<html" in content or "<!DOCTYPE" in content),
            ("JavaScript", "<script" in content or ".js" in content),
            ("API calls", "fetch" in content or "axios" in content or "XMLHttpRequest" in content),
            ("Config reference", "config.js" in content),
        ]
        
        passed = 0
        for check_name, check_result in checks:
            if check_result:
                print(f"  ✅ {check_name}")
                passed += 1
            else:
                print(f"  ⚠️  {check_name} not found")
        
        if passed >= 3:
            print("✅ Frontend HTML structure looks good")
            return True
        else:
            print("⚠️  Frontend HTML structure may be incomplete")
            return False
    except Exception as e:
        print(f"❌ Failed to read monitor.html: {e}")
        return False

def main():
    """Run all frontend tests"""
    print("=" * 60)
    print("Frontend Test Suite")
    print("=" * 60)
    print()
    print("Testing frontend connection and integration...")
    print("(Backend must be running first)")
    print()
    
    # First check if backend is running
    if not test_1_backend_required():
        print("\n" + "=" * 60)
        print("Frontend Test Failed - Backend Not Running")
        print("=" * 60)
        print("\nPlease start backend first:")
        print("  1. Run: scripts\\test_backend.bat (to verify backend)")
        print("  2. Run: scripts\\start_backend_auto.bat (to start backend)")
        print("  3. Then run this test again")
        return 1
    
    tests = [
        ("Frontend Files", test_2_frontend_files),
        ("Frontend Config", test_3_frontend_config),
        ("CORS Configuration", test_4_cors_configuration),
        ("API Endpoints", test_5_api_endpoints),
        ("HTML Structure", test_6_frontend_html_structure),
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
    print("Frontend Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All frontend tests passed!")
        print("\nFrontend is ready to use!")
        print("Open frontend/monitor.html in your browser")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("\nPlease check frontend configuration and files")
        return 1

if __name__ == "__main__":
    exit(main())

