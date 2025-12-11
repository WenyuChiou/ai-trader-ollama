#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行一次 trading cycle
"""

import sys
import requests
import json
import time

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 80)
print("执行 Trading Cycle")
print("=" * 80)
print()

try:
    url = "http://127.0.0.1:8000/api/trading/execute-trade"
    print(f"调用 API: {url}")
    print("发送 POST 请求...")
    
    response = requests.post(url, json={}, timeout=600)  # 10分钟超时
    
    print(f"状态码: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Trading cycle 执行成功")
        print()
        print("结果摘要:")
        if isinstance(result, dict):
            print(f"  Action: {result.get('action', 'N/A')}")
            print(f"  Buy Orders: {len(result.get('buy_orders', []))}")
            print(f"  Sell Orders: {len(result.get('sell_orders', []))}")
    else:
        print(f"❌ Trading cycle 执行失败")
        print(f"响应: {response.text[:500]}")
        
except requests.exceptions.ConnectionError:
    print("❌ 无法连接到 API")
    print("   请确认 API 是否正在运行")
except requests.exceptions.Timeout:
    print("⚠️  请求超时（可能需要更长时间）")
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)

