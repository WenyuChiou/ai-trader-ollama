#!/usr/bin/env python3
"""
测试多个日期的模拟：检查是否执行了交易
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

def get_trading_days(start_date, end_date):
    """获取交易日（排除周末）"""
    trading_days = []
    current = start_date
    while current <= end_date:
        # 0 = Monday, 6 = Sunday
        if current.weekday() < 5:  # Monday to Friday
            trading_days.append(current)
        current += timedelta(days=1)
    return trading_days

def test_multiple_dates():
    """测试多个日期"""
    print("=" * 80)
    print("测试多个日期的模拟交易")
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
        except Exception as e:
            print(f"[WARN] 读取 config.json 失败，使用默认清单: {e}")
    
    # 测试 10 月的多个交易日
    start_date = date(2024, 10, 1)
    end_date = date(2024, 10, 31)
    trading_days = get_trading_days(start_date, end_date)
    
    print(f"\n[INFO] 测试日期范围: {start_date} ~ {end_date}")
    print(f"[INFO] 交易日数量: {len(trading_days)}")
    print(f"[INFO] 测试前 5 个交易日: {[d.isoformat() for d in trading_days[:5]]}")
    print(f"\n开始测试...\n")
    
    results = []
    for i, trade_date in enumerate(trading_days[:5], 1):  # 只测试前 5 天
        print(f"\n{'='*80}")
        print(f"测试 {i}/5: {trade_date.isoformat()}")
        print(f"{'='*80}")
        
        trade_date_str = trade_date.isoformat()
        window_start = (trade_date - timedelta(days=10)).isoformat()
        window_end = (trade_date + timedelta(days=1)).isoformat()
        
        try:
            result = execute_daily_trade(
                start=window_start,
                end=window_end,
                universe=universe[:20]  # 只使用前 20 只股票加快测试
            )
            
            decision = result.get('decision', {})
            buy_orders = decision.get('buy_orders', [])
            sell_orders = decision.get('sell_orders', [])
            stance = decision.get('stance', 'N/A')
            rationale = decision.get('rationale', 'N/A')
            
            print(f"\n[RESULT] 日期: {trade_date_str}")
            print(f"  - Stance: {stance}")
            print(f"  - Rationale: {rationale[:100] if rationale else 'N/A'}")
            print(f"  - 买入订单: {len(buy_orders)} 笔")
            print(f"  - 卖出订单: {len(sell_orders)} 笔")
            
            if buy_orders:
                print(f"  - 买入股票: {', '.join([o['symbol'] for o in buy_orders[:5]])}")
            if sell_orders:
                print(f"  - 卖出股票: {', '.join([o['symbol'] for o in sell_orders[:5]])}")
            
            results.append({
                'date': trade_date_str,
                'stance': stance,
                'buy_orders': len(buy_orders),
                'sell_orders': len(sell_orders),
                'has_orders': len(buy_orders) > 0 or len(sell_orders) > 0,
            })
            
        except Exception as e:
            print(f"[ERROR] {trade_date_str} 执行失败: {e}")
            results.append({
                'date': trade_date_str,
                'error': str(e),
            })
    
    # 总结
    print(f"\n{'='*80}")
    print("测试总结")
    print(f"{'='*80}")
    
    successful = [r for r in results if 'error' not in r]
    with_orders = [r for r in successful if r.get('has_orders', False)]
    neutral_only = [r for r in successful if r.get('stance') == 'neutral' and not r.get('has_orders', False)]
    
    print(f"\n总测试天数: {len(results)}")
    print(f"成功执行: {len(successful)}")
    print(f"有订单生成: {len(with_orders)}")
    print(f"Neutral 且无订单: {len(neutral_only)}")
    
    if neutral_only:
        print(f"\n⚠️  以下日期是 neutral 且没有订单:")
        for r in neutral_only:
            print(f"  - {r['date']}: {r.get('rationale', 'N/A')[:80]}")
    
    if with_orders:
        print(f"\n✓ 以下日期有订单生成:")
        for r in with_orders:
            print(f"  - {r['date']}: {r['buy_orders']} 买入, {r['sell_orders']} 卖出")
    
    return results

if __name__ == "__main__":
    results = test_multiple_dates()
    sys.exit(0)

