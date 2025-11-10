#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试前端运行 agent 的速度
模拟前端的主要 API 调用，测量响应时间
"""
import time
import requests
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# 设置 Windows 终端编码
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

API_BASE = "http://127.0.0.1:8000"
TIMEOUT = 30

def test_api_speed(endpoint: str, method: str = "GET", data: Optional[Dict] = None, name: str = None) -> Optional[Dict]:
    """测试 API 端点速度"""
    if name is None:
        name = endpoint
    
    try:
        url = f"{API_BASE}{endpoint}"
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            return None
        
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            return {
                "success": True,
                "elapsed": elapsed,
                "data": result,
                "status_code": response.status_code
            }
        else:
            return {
                "success": False,
                "elapsed": elapsed,
                "error": f"HTTP {response.status_code}",
                "status_code": response.status_code
            }
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "elapsed": TIMEOUT,
            "error": "Timeout"
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "elapsed": 0,
            "error": "Connection Error"
        }
    except Exception as e:
        return {
            "success": False,
            "elapsed": 0,
            "error": str(e)
        }

def check_order_status():
    """检查订单状态，找出非交易时段却显示为 filled 的订单"""
    print("\n" + "="*80)
    print("  检查订单状态（非交易时段 filled 问题）")
    print("="*80)
    
    # 1. 检查市场状态
    market_result = test_api_speed("/api/market/is-open", name="市场状态")
    if market_result and market_result.get("success"):
        is_open = market_result["data"].get("open", False)
        print(f"市场状态: {'开盘' if is_open else '收盘'}")
    else:
        print("无法获取市场状态")
        return
    
    # 2. 获取订单数据
    orders_result = test_api_speed("/api/trades/recent?limit=100", name="订单列表")
    if not orders_result or not orders_result.get("success"):
        print(f"无法获取订单数据: {orders_result.get('error', 'Unknown')}")
        return
    
    orders = orders_result["data"].get("trades", [])
    print(f"找到 {len(orders)} 条订单记录")
    
    # 3. 分析订单状态
    filled_orders = [o for o in orders if o.get("status", "").upper() == "FILLED"]
    pending_orders = [o for o in orders if o.get("status", "").upper() == "PENDING"]
    
    print(f"\n订单状态统计:")
    print(f"  FILLED: {len(filled_orders)}")
    print(f"  PENDING: {len(pending_orders)}")
    
    # 4. 检查非交易时段的 filled 订单
    if not is_open:
        print(f"\n[检查] 当前市场收盘，检查是否有不应该 filled 的订单:")
        
        suspicious_orders = []
        for order in filled_orders:
            order_date = order.get("order_date")
            filled_at = order.get("filled_at")
            placed_at = order.get("placed_at")
            
            # 检查订单日期是否是今天或未来
            from datetime import date
            today = date.today().isoformat()
            
            if order_date and order_date > today:
                suspicious_orders.append({
                    "order": order,
                    "reason": f"订单日期是未来 ({order_date})"
                })
            elif not filled_at and not placed_at:
                suspicious_orders.append({
                    "order": order,
                    "reason": "缺少时间戳"
                })
        
        if suspicious_orders:
            print(f"  [WARNING] 发现 {len(suspicious_orders)} 个可疑订单:")
            for item in suspicious_orders[:5]:  # 只显示前5个
                order = item["order"]
                print(f"    - {order.get('symbol')} {order.get('side')} {order.get('quantity')} @ ${order.get('price', 0):.2f}")
                print(f"      原因: {item['reason']}")
                print(f"      订单日期: {order.get('order_date')}")
                print(f"      Filled at: {order.get('filled_at')}")
        else:
            print("  [OK] 未发现可疑订单")
    
    # 5. 检查订单时间戳
    print(f"\n订单时间戳分析:")
    for order in filled_orders[:5]:  # 检查前5个
        symbol = order.get("symbol", "?")
        order_date = order.get("order_date", "?")
        filled_at = order.get("filled_at", "?")
        placed_at = order.get("placed_at", "?")
        print(f"  {symbol}: order_date={order_date}, placed_at={placed_at}, filled_at={filled_at}")

def test_frontend_agent_speed():
    """测试前端 agent 运行速度"""
    print("="*80)
    print("  前端 Agent 运行速度测试")
    print("="*80)
    print(f"API Base: {API_BASE}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试的 API 端点（按前端实际调用顺序）
    endpoints = [
        ("/api/market/is-open", "GET", None, "市场状态"),
        ("/api/agents/status", "GET", None, "Agent 状态"),
        ("/api/tools/list", "GET", None, "工具列表"),
        ("/api/system/info", "GET", None, "系统信息"),
        ("/api/agents/conversations?limit=20", "GET", None, "对话数据"),
        ("/api/trades/recent?limit=30", "GET", None, "订单数据"),
        ("/api/portfolio/current", "GET", None, "投资组合"),
        ("/api/portfolio/equity-history?limit=100", "GET", None, "净值历史"),
    ]
    
    results = []
    total_time = 0
    
    print("\n开始测试...")
    for endpoint, method, data, name in endpoints:
        result = test_api_speed(endpoint, method, data, name)
        if result:
            elapsed = result.get("elapsed", 0)
            success = result.get("success", False)
            status = "[OK]" if success else "[FAIL]"
            
            if success:
                total_time += elapsed
                # 获取数据大小
                data_size = len(json.dumps(result.get("data", {})).encode('utf-8'))
                print(f"{status} {name:20s} {elapsed:6.2f}s ({data_size/1024:.1f} KB)")
            else:
                error = result.get("error", "Unknown")
                print(f"{status} {name:20s} {elapsed:6.2f}s (错误: {error})")
            
            results.append({
                "name": name,
                "endpoint": endpoint,
                "elapsed": elapsed,
                "success": success
            })
        else:
            print(f"[FAIL] {name:20s} 测试失败")
            results.append({
                "name": name,
                "endpoint": endpoint,
                "elapsed": 0,
                "success": False
            })
    
    # 总结
    print("\n" + "="*80)
    print("  测试总结")
    print("="*80)
    
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]
    
    if successful:
        avg_time = sum(r["elapsed"] for r in successful) / len(successful)
        max_time = max(r["elapsed"] for r in successful)
        min_time = min(r["elapsed"] for r in successful)
        
        print(f"成功: {len(successful)}/{len(results)}")
        print(f"总时间: {total_time:.2f}s")
        print(f"平均时间: {avg_time:.2f}s")
        print(f"最快: {min_time:.2f}s")
        print(f"最慢: {max_time:.2f}s")
        
        # 找出最慢的端点
        slowest = max(successful, key=lambda x: x["elapsed"])
        print(f"\n最慢的端点: {slowest['name']} ({slowest['elapsed']:.2f}s)")
        
        if total_time > 5:
            print(f"\n[WARNING] 总响应时间较长 ({total_time:.2f}s)，可能影响用户体验")
            print("  建议:")
            print("  1. 检查网络延迟")
            print("  2. 检查后端服务器性能")
            print("  3. 考虑使用缓存或并行请求优化")
    
    if failed:
        print(f"\n失败: {len(failed)}/{len(results)}")
        for r in failed:
            print(f"  - {r['name']}: {r['endpoint']}")
    
    return results

def main():
    try:
        # 1. 测试前端 agent 速度
        results = test_frontend_agent_speed()
        
        # 2. 检查订单状态问题
        check_order_status()
        
        return 0
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        return 1
    except Exception as e:
        print(f"\n\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

