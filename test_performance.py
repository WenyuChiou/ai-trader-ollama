#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试前端性能优化效果"""
import time
import requests
import json

API_BASE = "http://127.0.0.1:8000"

def test_endpoint(endpoint, limit=None):
    """测试单个端点的响应时间"""
    url = f"{API_BASE}{endpoint}"
    if limit:
        url += f"?limit={limit}"
    
    start = time.time()
    try:
        r = requests.get(url, timeout=10)
        elapsed = (time.time() - start) * 1000
        size = len(r.content) if r.ok else 0
        return {
            "ok": r.ok,
            "status": r.status_code,
            "time_ms": round(elapsed, 2),
            "size_kb": round(size / 1024, 2),
            "data": r.json() if r.ok else None
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "time_ms": (time.time() - start) * 1000
        }

def main():
    import sys
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    print("=" * 60)
    print("Performance Test - API Response Time")
    print("=" * 60)
    
    endpoints = [
        ("/api/portfolio/real-time", None),
        ("/api/portfolio/equity-history", 60),
        ("/api/agents/conversations", 30),
        ("/api/trades/recent", 30),
        ("/api/backend/status", None),
        ("/api/agents/status", None),
        ("/api/tools/list", None),
        ("/api/system/info", None),
    ]
    
    results = []
    for endpoint, limit in endpoints:
        result = test_endpoint(endpoint, limit)
        results.append((endpoint, result))
        status = "✓" if result.get("ok") else "✗"
        time_str = f"{result.get('time_ms', 0):.2f}ms"
        size_str = f"{result.get('size_kb', 0):.2f}KB" if result.get('size_kb') else ""
        print(f"{status} {endpoint:<40} {time_str:>10} {size_str:>10}")
    
    print("\n" + "=" * 60)
    total_time = sum(r.get("time_ms", 0) for _, r in results)
    print(f"总响应时间: {total_time:.2f}ms")
    print(f"平均响应时间: {total_time / len(results):.2f}ms")
    
    # Check if performance requirements are met (total time < 2 seconds)
    if total_time < 2000:
        print("OK Performance test passed: total response time < 2s")
    else:
        print("FAIL Performance test failed: total response time >= 2s")
    
    return results

if __name__ == "__main__":
    main()

