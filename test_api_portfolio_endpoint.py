#!/usr/bin/env python3
"""
测试 /api/portfolio/real-time 端点，确保能正确返回投资组合状态
"""
import sys
import os
import io
import json
import requests
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_api_endpoint():
    """测试 API 端点"""
    print("=" * 80)
    print("测试 /api/portfolio/real-time 端点")
    print("=" * 80)
    
    api_url = "http://127.0.0.1:8000/api/portfolio/real-time"
    
    print(f"\n[INFO] 请求 URL: {api_url}")
    print("[INFO] 发送 GET 请求...\n")
    
    try:
        response = requests.get(api_url, timeout=10)
        
        print(f"[RESPONSE] Status Code: {response.status_code}")
        print(f"[RESPONSE] Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n[SUCCESS] API 响应成功")
            print(f"  - ok: {data.get('ok', False)}")
            print(f"  - timestamp: {data.get('timestamp', 'N/A')}")
            print(f"  - cash: ${data.get('cash', 0):.2f}")
            print(f"  - equity_value: ${data.get('equity_value', 0):.2f}")
            print(f"  - total_value: ${data.get('total_value', 0):.2f}")
            print(f"  - total_pnl: ${data.get('total_pnl', 0):.2f}")
            print(f"  - positions: {len(data.get('positions', {}))} 个持仓")
            
            positions = data.get('positions', {})
            if positions:
                print("\n  持仓详情:")
                for symbol, pos_info in list(positions.items())[:5]:
                    if isinstance(pos_info, dict):
                        qty = pos_info.get('quantity', 0)
                        avg_cost = pos_info.get('avg_cost', 0)
                        current_price = pos_info.get('current_price', 0)
                        market_value = pos_info.get('market_value', 0)
                        print(f"    - {symbol}: {qty} shares @ ${avg_cost:.2f} (current: ${current_price:.2f}, value: ${market_value:.2f})")
            
            print("\n✅ API 端点工作正常，前端应该能正确显示数据")
            return True
        else:
            print(f"\n[ERROR] API 返回错误状态码: {response.status_code}")
            try:
                error_data = response.json()
                print(f"  - error: {error_data.get('error', 'N/A')}")
                print(f"  - message: {error_data.get('message', 'N/A')}")
            except:
                print(f"  - Response text: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"\n[ERROR] 无法连接到 API ({api_url})")
        print("  请确保后端 API 正在运行:")
        print("  cd backend && python -m uvicorn src.api.server:app --reload")
        return False
    except requests.exceptions.Timeout:
        print(f"\n[ERROR] 请求超时")
        return False
    except Exception as e:
        print(f"\n[ERROR] 请求失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_endpoint()
    sys.exit(0 if success else 1)

