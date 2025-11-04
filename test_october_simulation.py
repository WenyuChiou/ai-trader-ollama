#!/usr/bin/env python3
"""
测试 10 月模拟：检查是否执行了交易
"""
import sys
import os
import io
from pathlib import Path
from datetime import date, timedelta
import json

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 确保在 backend 目录
backend_dir = Path(__file__).parent
os.chdir(str(backend_dir))
sys.path.insert(0, str(backend_dir))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.order_manager import OrderManager
from src.data.portfolio import Portfolio
from src.data.order_executor import get_current_or_open_price

def test_october_simulation():
    """测试 10 月某一天的交易"""
    print("=" * 80)
    print("测试 10 月模拟交易")
    print("=" * 80)
    
    # 从 config.json 读取股票清单
    config_path = backend_dir / "config" / "config.json"
    universe = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]  # 默认值
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    universe = config_data["universe"]
                    print(f"[INFO] 使用 config.json 中的股票清单: {len(universe)} 只股票")
                else:
                    print(f"[INFO] config.json 中没有 universe，使用默认清单: {len(universe)} 只股票")
        except Exception as e:
            print(f"[WARN] 读取 config.json 失败，使用默认清单: {e}")
    else:
        print(f"[INFO] config.json 不存在，使用默认清单: {len(universe)} 只股票")
    
    # 选择 2024-10-01 作为测试日期（10 月的第一个交易日）
    trade_date = date(2024, 10, 1)
    trade_date_str = trade_date.isoformat()
    
    print(f"\n[INFO] 测试日期: {trade_date_str}")
    print(f"[INFO] 股票清单: {universe[:10]}... (共 {len(universe)} 只)")
    
    # 设置时间窗口（10 天前到 1 天后）
    window_start = (trade_date - timedelta(days=10)).isoformat()
    window_end = (trade_date + timedelta(days=1)).isoformat()
    
    print(f"\n[INFO] 时间窗口: {window_start} ~ {window_end}")
    print(f"[INFO] 开始执行交易循环...\n")
    
    try:
        # 执行交易循环
        result = execute_daily_trade(
            start=window_start,
            end=window_end,
            universe=universe
        )
        
        print("\n" + "=" * 80)
        print("交易循环执行结果")
        print("=" * 80)
        
        # 检查结果
        print(f"\n[RESULT] 市场数据: {'✓' if result.get('market_view') else '✗'}")
        print(f"[RESULT] 市场分析: {'✓' if result.get('market_analysis') else '✗'}")
        print(f"[RESULT] 讨论对话: {'✓' if result.get('conversation') else '✗'}")
        print(f"[RESULT] 风险报告: {'✓' if result.get('risk_report') else '✗'}")
        print(f"[RESULT] 交易决策: {'✓' if result.get('decision') else '✗'}")
        
        # 检查订单
        decision = result.get('decision', {})
        buy_orders = decision.get('buy_orders', [])
        sell_orders = decision.get('sell_orders', [])
        placed_orders = result.get('placed_orders', [])
        
        print(f"\n[DECISION] 完整决策内容:")
        print(f"  - Stance: {decision.get('stance', 'N/A')}")
        print(f"  - Rationale: {decision.get('rationale', 'N/A')[:200] if decision.get('rationale') else 'N/A'}")
        print(f"  - 决策键: {list(decision.keys())}")
        
        print(f"\n[ORDERS] 买入订单建议: {len(buy_orders)} 笔")
        if buy_orders:
            print("  前 5 个买入订单:")
            for order in buy_orders[:5]:
                symbol = order.get('symbol', 'N/A')
                qty = order.get('quantity', 0)
                price = order.get('buy_price', 0)
                print(f"    - {symbol}: {qty} shares @ ${price:.2f}")
        else:
            print("  ⚠️  没有买入订单建议")
        
        print(f"\n[ORDERS] 卖出订单建议: {len(sell_orders)} 笔")
        if sell_orders:
            print("  前 5 个卖出订单:")
            for order in sell_orders[:5]:
                symbol = order.get('symbol', 'N/A')
                qty = order.get('quantity', 0)
                price = order.get('sell_price', 0)
                print(f"    - {symbol}: {qty} shares @ ${price:.2f}")
        else:
            print("  ⚠️  没有卖出订单建议")
        
        print(f"\n[ORDERS] 实际挂单: {len(placed_orders)} 笔")
        if placed_orders:
            print("  前 5 个挂单:")
            for order in placed_orders[:5]:
                symbol = order.get('symbol', 'N/A')
                action = order.get('action', 'N/A')
                qty = order.get('quantity', 0)
                limit_price = order.get('limit_price', 0)
                print(f"    - {action} {symbol}: {qty} shares @ limit ${limit_price:.2f}")
        
        # 检查 pending_orders.jsonl
        logs_dir = backend_dir / "data" / "logs"
        pending_orders_file = logs_dir / "pending_orders.jsonl"
        
        print(f"\n[FILES] 检查 pending_orders.jsonl:")
        if pending_orders_file.exists():
            pending_orders = []
            try:
                with open(pending_orders_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            order = json.loads(line)
                            if order.get('order_date') == trade_date_str:
                                pending_orders.append(order)
                print(f"  ✓ 文件存在，包含 {len(pending_orders)} 笔 {trade_date_str} 的订单")
                if pending_orders:
                    print("  前 3 个订单:")
                    for order in pending_orders[:3]:
                        symbol = order.get('symbol', 'N/A')
                        action = order.get('action', 'N/A')
                        qty = order.get('quantity', 0)
                        limit_price = order.get('limit_price', 0)
                        status = order.get('status', 'N/A')
                        print(f"    - {action} {symbol}: {qty} shares @ ${limit_price:.2f} ({status})")
            except Exception as e:
                print(f"  ✗ 读取失败: {e}")
        else:
            print(f"  ✗ 文件不存在")
        
        # 检查 discussion_actions.jsonl
        convo_file = logs_dir / "discussion_actions.jsonl"
        print(f"\n[FILES] 检查 discussion_actions.jsonl:")
        if convo_file.exists():
            conversations = []
            try:
                with open(convo_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            conv = json.loads(line)
                            if conv.get('date') == trade_date_str:
                                conversations.append(conv)
                print(f"  ✓ 文件存在，包含 {len(conversations)} 条 {trade_date_str} 的对话")
                if conversations:
                    print("  对话类型统计:")
                    agent_counts = {}
                    for conv in conversations:
                        agent = conv.get('agent', 'Unknown')
                        agent_counts[agent] = agent_counts.get(agent, 0) + 1
                    for agent, count in agent_counts.items():
                        print(f"    - {agent}: {count} 条")
            except Exception as e:
                print(f"  ✗ 读取失败: {e}")
        else:
            print(f"  ✗ 文件不存在")
        
        # 检查订单结算
        filled_orders_file = logs_dir / "filled_orders.jsonl"
        print(f"\n[FILES] 检查 filled_orders.jsonl:")
        if filled_orders_file.exists():
            filled_orders = []
            try:
                with open(filled_orders_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            order = json.loads(line)
                            if order.get('order_date') == trade_date_str:
                                filled_orders.append(order)
                print(f"  ✓ 文件存在，包含 {len(filled_orders)} 笔 {trade_date_str} 的已成交订单")
                if filled_orders:
                    print("  前 3 个已成交订单:")
                    for order in filled_orders[:3]:
                        symbol = order.get('symbol', 'N/A')
                        action = order.get('action', 'N/A')
                        qty = order.get('quantity', 0)
                        fill_price = order.get('fill_price', 0)
                        print(f"    - {action} {symbol}: {qty} shares @ ${fill_price:.2f}")
            except Exception as e:
                print(f"  ✗ 读取失败: {e}")
        else:
            print(f"  ✗ 文件不存在（这是正常的，如果订单还没结算）")
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        
        return {
            'success': True,
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'placed_orders': len(placed_orders),
            'pending_orders_file': pending_orders_file.exists(),
            'conversations_file': convo_file.exists(),
        }
        
    except Exception as e:
        print(f"\n[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_october_simulation()
    sys.exit(0 if result.get('success') else 1)
