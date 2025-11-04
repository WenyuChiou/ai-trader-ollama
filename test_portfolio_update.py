#!/usr/bin/env python3
"""
测试投资组合状态更新和前端显示
"""
import sys
import os
import io
import json
from pathlib import Path
from datetime import date, timedelta

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 确保在 backend 目录
backend_dir = Path(__file__).parent
os.chdir(str(backend_dir))
sys.path.insert(0, str(backend_dir))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio

def test_portfolio_update():
    """测试投资组合更新"""
    print("=" * 80)
    print("测试投资组合状态更新")
    print("=" * 80)
    
    # 从 config.json 读取股票清单
    config_path = backend_dir / "config" / "config.json"
    universe = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]  # 默认值
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    universe = config_data["universe"][:20]  # 只使用前20只加快测试
                    print(f"[INFO] 使用 config.json 中的股票清单: {len(universe)} 只股票")
        except Exception as e:
            print(f"[WARN] 读取 config.json 失败，使用默认清单: {e}")
    
    # 选择测试日期
    trade_date = date(2024, 10, 1)
    trade_date_str = trade_date.isoformat()
    window_start = (trade_date - timedelta(days=10)).isoformat()
    window_end = (trade_date + timedelta(days=1)).isoformat()
    
    print(f"\n[INFO] 测试日期: {trade_date_str}")
    print(f"[INFO] 时间窗口: {window_start} ~ {window_end}")
    print(f"\n开始执行交易循环...\n")
    
    # 检查初始状态
    logs_dir = backend_dir / "data" / "logs"
    portfolio_state_file = logs_dir / "portfolio_state.json"
    
    print("[BEFORE] 检查初始投资组合状态:")
    if portfolio_state_file.exists():
        with open(portfolio_state_file, 'r', encoding='utf-8') as f:
            before_state = json.load(f)
            print(f"  - Cash: ${before_state.get('cash', 0):.2f}")
            print(f"  - Equity Value: ${before_state.get('equity_value', 0):.2f}")
            print(f"  - Total Value: ${before_state.get('total_value', 0):.2f}")
            print(f"  - Positions: {len(before_state.get('positions', {}))}")
    else:
        print("  - portfolio_state.json 不存在（这是正常的，如果是首次运行）")
    
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
        
        # 检查订单
        decision = result.get('decision', {})
        buy_orders = decision.get('buy_orders', [])
        sell_orders = decision.get('sell_orders', [])
        placed_orders = result.get('placed_orders', [])
        
        print(f"\n[ORDERS] 买入订单: {len(buy_orders)} 笔")
        print(f"[ORDERS] 卖出订单: {len(sell_orders)} 笔")
        print(f"[ORDERS] 实际挂单: {len(placed_orders)} 笔")
        
        if placed_orders:
            print("\n  挂单详情:")
            for order in placed_orders[:5]:
                symbol = order.get('symbol', 'N/A')
                action = order.get('action', 'N/A')
                qty = order.get('quantity', 0)
                limit_price = order.get('limit_price', 0)
                status = order.get('status', 'N/A')
                print(f"    - {action} {symbol}: {qty} shares @ ${limit_price:.2f} ({status})")
        
        # 检查更新后的状态
        print("\n[AFTER] 检查更新后的投资组合状态:")
        if portfolio_state_file.exists():
            with open(portfolio_state_file, 'r', encoding='utf-8') as f:
                after_state = json.load(f)
                print(f"  - Cash: ${after_state.get('cash', 0):.2f}")
                print(f"  - Equity Value: ${after_state.get('equity_value', 0):.2f}")
                print(f"  - Total Value: ${after_state.get('total_value', 0):.2f}")
                print(f"  - Total P&L: ${after_state.get('total_pnl', 0):.2f}")
                print(f"  - Positions: {len(after_state.get('positions', {}))}")
                
                positions = after_state.get('positions', {})
                if positions:
                    print("\n  持仓详情:")
                    for symbol, pos_info in list(positions.items())[:5]:
                        qty = pos_info.get('quantity', 0)
                        avg_cost = pos_info.get('avg_cost', 0)
                        current_price = pos_info.get('current_price', 0)
                        print(f"    - {symbol}: {qty} shares @ ${avg_cost:.2f} (current: ${current_price:.2f})")
                
                # 比较前后状态
                if portfolio_state_file.exists() and 'before_state' in locals():
                    cash_diff = after_state.get('cash', 0) - before_state.get('cash', 10000.0)
                    equity_diff = after_state.get('equity_value', 0) - before_state.get('equity_value', 0)
                    total_diff = after_state.get('total_value', 0) - before_state.get('total_value', 10000.0)
                    
                    print("\n[CHANGES] 状态变化:")
                    print(f"  - Cash 变化: ${cash_diff:.2f}")
                    print(f"  - Equity 变化: ${equity_diff:.2f}")
                    print(f"  - Total Value 变化: ${total_diff:.2f}")
                    
                    if abs(cash_diff) > 0.01 or abs(equity_diff) > 0.01:
                        print("\n✅ 投资组合状态已更新！前端应该能看到变化。")
                    else:
                        print("\n⚠️  投资组合状态没有变化（可能是没有订单或订单未执行）")
        else:
            print("  ⚠️  portfolio_state.json 不存在（可能保存失败）")
        
        # 检查交易记录
        trades_file = logs_dir / "trades.jsonl"
        print(f"\n[TRADES] 检查 trades.jsonl:")
        if trades_file.exists():
            trades = []
            try:
                with open(trades_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            trade = json.loads(line)
                            if trade.get('order_date') == trade_date_str or trade.get('date') == trade_date_str:
                                trades.append(trade)
                print(f"  ✓ 文件存在，包含 {len(trades)} 笔 {trade_date_str} 的交易")
                if trades:
                    print("  前 3 个交易:")
                    for trade in trades[:3]:
                        symbol = trade.get('symbol', 'N/A')
                        action = trade.get('action', 'N/A')
                        qty = trade.get('quantity', 0)
                        price = trade.get('price', 0)
                        status = trade.get('status', 'N/A')
                        print(f"    - {action} {symbol}: {qty} shares @ ${price:.2f} ({status})")
            except Exception as e:
                print(f"  ✗ 读取失败: {e}")
        else:
            print(f"  ✗ 文件不存在")
        
        print("\n" + "=" * 80)
        print("测试完成")
        print("=" * 80)
        print("\n💡 前端检查:")
        print("  1. 打开前端页面: http://127.0.0.1:8080/monitor.html")
        print("  2. 检查 Total Portfolio Value 是否更新")
        print("  3. 检查 Current Holdings 是否显示新持仓")
        print("  4. 检查 Execution Details 是否显示已成交订单")
        print("  5. 检查 Equity Value 和 Cash 是否正确更新")
        
        return {
            'success': True,
            'buy_orders': len(buy_orders),
            'sell_orders': len(sell_orders),
            'placed_orders': len(placed_orders),
            'portfolio_state_exists': portfolio_state_file.exists(),
        }
        
    except Exception as e:
        print(f"\n[ERROR] 执行失败: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    result = test_portfolio_update()
    sys.exit(0 if result.get('success') else 1)
