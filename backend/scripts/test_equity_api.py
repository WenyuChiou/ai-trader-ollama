#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试净值 API 返回的数据
"""
import sys
import io
import requests
import json
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def test_equity_api(base_url="http://localhost:8000"):
    """测试净值 API"""
    print("="*80)
    print("🔍 测试净值 API")
    print("="*80)
    
    # 测试不同时间范围
    test_cases = [
        {"name": "默认（最近60条）", "params": {}},
        {"name": "最近1天", "params": {"period": "day"}},
        {"name": "最近1周", "params": {"period": "week"}},
        {"name": "最近1月", "params": {"period": "month"}},
        {"name": "2025-11-20", "params": {"start_date": "2025-11-20", "end_date": "2025-11-20"}},
    ]
    
    for test_case in test_cases:
        print(f"\n📊 测试: {test_case['name']}")
        print("-" * 80)
        
        try:
            url = f"{base_url}/api/portfolio/equity-history"
            params = test_case['params']
            params['limit'] = 1000  # 获取更多数据
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                continue
            
            data = response.json()
            
            if not data.get("ok"):
                print(f"❌ API 返回错误: {data.get('error', 'Unknown')}")
                continue
            
            records = data.get("records", [])
            print(f"✅ 返回 {len(records)} 条记录")
            
            if records:
                # 分析数据
                values = [r.get("total_value", 0) for r in records]
                valid_values = [v for v in values if v > 0]
                
                if valid_values:
                    min_val = min(valid_values)
                    max_val = max(valid_values)
                    value_range = max_val - min_val
                    
                    print(f"  净值范围: ${min_val:.2f} - ${max_val:.2f}")
                    print(f"  净值变化: ${value_range:.2f}")
                    print(f"  有效值数量: {len(valid_values)}/{len(values)}")
                    
                    if value_range < 0.01:
                        print(f"  ⚠️  警告: 所有值几乎相同，图表会显示为直线")
                    
                    # 显示前3条和后3条
                    print(f"\n  前3条记录:")
                    for i, record in enumerate(records[:3], 1):
                        print(f"    {i}. {record.get('timestamp', 'N/A')}: ${record.get('total_value', 0):.2f}")
                    
                    if len(records) > 3:
                        print(f"\n  后3条记录:")
                        for i, record in enumerate(records[-3:], len(records)-2):
                            print(f"    {i}. {record.get('timestamp', 'N/A')}: ${record.get('total_value', 0):.2f}")
                else:
                    print(f"  ⚠️  警告: 没有有效的净值数据")
            else:
                print(f"  ⚠️  没有数据")
        
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到 {base_url}")
            print(f"   请确保后端服务正在运行")
            break
        except Exception as e:
            print(f"❌ 错误: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    import sys
    
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    test_equity_api(base_url)

