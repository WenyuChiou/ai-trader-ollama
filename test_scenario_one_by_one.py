#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
逐个测试情境脚本
测试开盘与收盘状态的agent loop
"""
import sys
import io
import json
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project paths
backend_dir = Path(__file__).parent / "backend"
project_root = Path(__file__).parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

from backend.src.orchestrator.trading_cycle import execute_daily_trade, _get_project_logs_dir
from backend.src.utils.trading_days import is_market_open

def test_scenario_1():
    """Scenario 1: Trading Hours (Market Open) - 测试开盘时生成订单"""
    print("\n" + "="*80)
    print("SCENARIO 1: TRADING HOURS (Market Open)")
    print("="*80)
    print()
    
    # 使用有数据的日期：2025-11-12 (Wednesday, trading day)
    test_date = "2025-11-12"
    print(f"[TEST] Using date: {test_date} (Wednesday - trading day with historical data)")
    print()
    
    # 检查当前市场状态
    now = datetime.now()
    current_market_status = is_market_open(now)
    print(f"[MARKET STATUS] Current time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"[MARKET STATUS] Market is currently: {'OPEN' if current_market_status else 'CLOSED'}")
    print()
    
    try:
        result = execute_daily_trade(
            start=test_date,
            end=test_date,
            tool_budget=10,
            min_tools=3
        )
        
        print("\n" + "="*80)
        print("[RESULT] Scenario 1 completed")
        print("="*80)
        print(f"  - Final stance: {result.get('final_stance', 'unknown')}")
        print(f"  - Placed orders: {len(result.get('placed_orders', []))}")
        print(f"  - Executed trades: {len(result.get('executed_trades', []))}")
        print()
        
        # Check orders
        placed_orders = result.get('placed_orders', [])
        if placed_orders:
            print("[ORDERS] Placed orders:")
            for i, order in enumerate(placed_orders[:5], 1):
                symbol = order.get('symbol', '?')
                action = order.get('action', '?')
                status = order.get('status', '?')
                order_type = order.get('order_type', 'N/A')
                market_order = order.get('market_order', False)
                print(f"  {i}. {action} {symbol}: status={status}, type={order_type}, market_order={market_order}")
            if len(placed_orders) > 5:
                print(f"  ... and {len(placed_orders) - 5} more orders")
            print()
            
            # Check order types
            market_orders = [o for o in placed_orders if o.get('order_type') == 'MARKET' or o.get('market_order')]
            filled_orders = [o for o in placed_orders if o.get('status') == 'FILLED']
            pending_orders = [o for o in placed_orders if o.get('status') == 'PENDING']
            
            print("[VERIFICATION]")
            if len(market_orders) == len(placed_orders):
                print(f"  [OK] All {len(placed_orders)} orders are MARKET orders")
            else:
                print(f"  [FAIL] Only {len(market_orders)}/{len(placed_orders)} orders are MARKET orders")
            
            if len(filled_orders) == len(placed_orders):
                print(f"  [OK] All {len(placed_orders)} orders are FILLED (no PENDING)")
            else:
                print(f"  [FAIL] {len(pending_orders)} orders are PENDING (should be 0 for market orders)")
        else:
            print("[INFO] No orders generated (may be expected if market is closed)")
        
        # Check conversations
        logs_dir = _get_project_logs_dir()
        convo_file = logs_dir / "discussion_actions.jsonl"
        if convo_file.exists():
            conversations = []
            with open(convo_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        try:
                            conv = json.loads(line)
                            conversations.append(conv)
                        except:
                            pass
            
            trader_entries = [e for e in conversations if e.get("agent") == "TraderAgent"]
            if trader_entries:
                latest_trader = trader_entries[-1]
                trader_content = latest_trader.get("content", "")
                
                print("\n[VERIFICATION] TraderAgent Summary:")
                if "Market is currently OPEN" in trader_content:
                    print("  [OK] Market OPEN status mentioned")
                elif "Market is currently CLOSED" in trader_content:
                    print("  [OK] Market CLOSED status mentioned")
                else:
                    print("  [WARN] Market status not clearly mentioned")
                
                if "MARKET ORDERS" in trader_content or "market orders" in trader_content.lower():
                    print("  [OK] MARKET ORDERS mentioned")
                else:
                    print("  [WARN] MARKET ORDERS not mentioned")
                
                if "NO PENDING" in trader_content or "no pending" in trader_content.lower():
                    print("  [OK] NO PENDING orders mentioned")
                else:
                    print("  [WARN] NO PENDING not mentioned")
        
        print("\n[SCENARIO 1: COMPLETED]")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Scenario 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*80)
    print("Testing Scenarios One by One")
    print("="*80)
    print()
    
    # Test Scenario 1
    test_scenario_1()
    
    print("\n" + "="*80)
    print("[TEST] Completed")
    print("="*80)


