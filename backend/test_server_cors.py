#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test actual running server for CORS headers"""
import requests
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_server():
    """Test actual running server"""
    print("="*60)
    print("Testing Actual Server (http://127.0.0.1:8000)")
    print("="*60)
    
    endpoints = [
        ("/", "Root"),
        ("/api/agents/status", "Agents Status"),
        ("/api/tools/list", "Tools List"),
    ]
    
    all_passed = True
    
    for path, name in endpoints:
        print(f"\n{'-'*60}")
        print(f"Testing: {name} ({path})")
        print(f"{'-'*60}")
        
        try:
            r = requests.get(f"http://127.0.0.1:8000{path}", timeout=3)
            print(f"Status Code: {r.status_code}")
            
            # Check CORS headers
            cors_origin = r.headers.get("Access-Control-Allow-Origin", "NOT FOUND")
            cors_methods = r.headers.get("Access-Control-Allow-Methods", "NOT FOUND")
            
            print(f"CORS Headers:")
            print(f"  Access-Control-Allow-Origin: {cors_origin}")
            print(f"  Access-Control-Allow-Methods: {cors_methods}")
            
            if cors_origin == "*":
                print(f"[PASS] {name} has CORS headers")
                if r.status_code == 200:
                    print(f"[PASS] {name} returns 200")
                else:
                    print(f"[WARNING] {name} returns {r.status_code}")
                    print(f"Response: {r.text[:200]}")
            else:
                print(f"[FAIL] {name} missing CORS headers!")
                all_passed = False
                if r.status_code != 200:
                    print(f"[FAIL] {name} returns {r.status_code}")
                    print(f"Response: {r.text[:200]}")
                    
        except requests.exceptions.ConnectionError:
            print(f"[ERROR] Cannot connect to server!")
            print(f"   Please start the server:")
            print(f"   cd backend")
            print(f"   python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 --reload")
            all_passed = False
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("[SUCCESS] All endpoints have CORS headers!")
    else:
        print("[FAILURE] Some endpoints are missing CORS headers")
        print("\nPossible issues:")
        print("1. Server is not running")
        print("2. Server was not restarted after code changes")
        print("3. Server is running old code")
    print(f"{'='*60}")
    
    return all_passed

if __name__ == "__main__":
    success = test_server()
    sys.exit(0 if success else 1)

