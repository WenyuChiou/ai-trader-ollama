#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查订单总金额是否超过可用现金
"""
import sys
import json
import io
from pathlib import Path
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def load_jsonl(file_path: Path) -> list:
    """加载JSONL文件"""
    if not file_path.exists():
        return []
    entries = []
    with file_path.open('r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return entries

def check_cash_vs_orders():
    """检查订单总金额与可用现金的关系"""
    logs_dir = Path("data/logs")
    
    print("=" * 80)
    print("现金与订单金额检查")
    print("=" * 80)
    
    # 1. 读取Portfolio状态
    portfolio_file = logs_dir / "portfolio_state.json"
    portfolio_state = {}
    if portfolio_file.exists():
        with portfolio_file.open('r', encoding='utf-8') as f:
            portfolio_state = json.load(f)
    
    cash = portfolio_state.get('cash', 0)
    positions = portfolio_state.get('positions', {})
    
    # 计算持仓市值（粗略估算）
    total_position_value = 0
    for symbol, pos_data in positions.items():
        if isinstance(pos_data, dict):
            qty = pos_data.get('quantity', 0)
            avg_cost = pos_data.get('avg_cost', 0)
            # 使用平均成本作为当前价格（粗略估算）
            total_position_value += qty * avg_cost
    
    portfolio_value = cash + total_position_value
    
    print(f"\n💰 Portfolio状态:")
    print(f"  - 现金: ${cash:.2f}")
    print(f"  - 持仓市值（估算）: ${total_position_value:.2f}")
    print(f"  - 总净值: ${portfolio_value:.2f}")
    
    # 计算可用现金（假设20%储备）
    MIN_CASH_RESERVE_RATIO = 0.20
    required_cash_reserve = portfolio_value * MIN_CASH_RESERVE_RATIO
    available_for_trading = max(0, cash - required_cash_reserve)
    
    print(f"\n💵 现金计算:")
    print(f"  - 所需现金储备 (20%): ${required_cash_reserve:.2f}")
    print(f"  - 可用现金: ${available_for_trading:.2f}")
    
    # 2. 读取pending订单
    pending_file = logs_dir / "pending_orders.jsonl"
    pending_orders = load_jsonl(pending_file)
    
    # 计算pending订单总金额
    total_pending_cost = 0
    buy_orders = []
    for order in pending_orders:
        if order.get('action', '').upper() == 'BUY':
            quantity = order.get('quantity', 0)
            limit_price = order.get('limit_price', 0)
            cost = quantity * limit_price
            total_pending_cost += cost
            buy_orders.append({
                'symbol': order.get('symbol', ''),
                'quantity': quantity,
                'limit_price': limit_price,
                'cost': cost
            })
    
    print(f"\n📦 Pending订单:")
    print(f"  - BUY订单数: {len(buy_orders)}")
    print(f"  - 总金额: ${total_pending_cost:.2f}")
    
    # 3. 对比
    print(f"\n🔍 对比分析:")
    print(f"  - 可用现金: ${available_for_trading:.2f}")
    print(f"  - Pending订单总金额: ${total_pending_cost:.2f}")
    
    if total_pending_cost > available_for_trading:
        excess = total_pending_cost - available_for_trading
        print(f"\n  ⚠️  订单总金额超过可用现金 ${excess:.2f}!")
        print(f"     超出比例: {(excess / available_for_trading * 100) if available_for_trading > 0 else 'N/A'}%")
        
        # 显示最大的订单
        buy_orders_sorted = sorted(buy_orders, key=lambda x: x['cost'], reverse=True)
        print(f"\n  最大的10个订单:")
        for i, order in enumerate(buy_orders_sorted[:10], 1):
            print(f"    {i}. {order['symbol']}: {order['quantity']} 股 @ ${order['limit_price']:.2f} = ${order['cost']:.2f}")
    else:
        print(f"\n  ✅ 订单总金额在可用现金范围内")
        remaining = available_for_trading - total_pending_cost
        print(f"     剩余可用现金: ${remaining:.2f}")
    
    # 4. 检查是否有现金为负的情况
    if cash < 0:
        print(f"\n  ⚠️  警告：现金为负数 ${cash:.2f}!")
    
    if available_for_trading <= 0:
        print(f"\n  ⚠️  警告：可用现金为 ${available_for_trading:.2f}，不应该创建新订单!")
    
    print("=" * 80)

if __name__ == "__main__":
    try:
        check_cash_vs_orders()
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

