"""
测试带持仓状态的Agent流程
"""
import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add backend to path
project_root = Path(__file__).resolve().parent
backend_dir = project_root / "backend"
backend_src = backend_dir / "src"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(backend_src))

# Change to backend directory
import os
os.chdir(backend_dir)

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio, Position

def test_with_positions():
    """测试带持仓状态的Agent流程"""
    print("=" * 80)
    print("测试带持仓状态的Agent流程")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 创建带持仓的Portfolio
    portfolio = Portfolio(initial_value=10000.0)
    portfolio.cash = 5000.0  # 剩余现金5000
    
    # 添加一些持仓（模拟已有持仓）
    test_positions = [
        ("NVDA", 5, 150.0),   # 5股 @ $150
        ("AAPL", 10, 180.0),  # 10股 @ $180
        ("MSFT", 8, 350.0),   # 8股 @ $350
    ]
    
    for symbol, qty, avg_cost in test_positions:
        portfolio._positions[symbol] = Position(
            symbol=symbol,
            quantity=qty,
            avg_cost=avg_cost,
            total_cost=avg_cost * qty
        )
        print(f"[TEST] Added position: {symbol} - {qty} shares @ ${avg_cost:.2f} (total: ${avg_cost * qty:.2f})")
    
    print(f"[TEST] Portfolio state: cash=${portfolio.cash:.2f}, positions={len(portfolio._positions)}")
    print()
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 执行完整的交易周期（传入portfolio）
        print("[TEST] 开始执行交易周期（带持仓状态）...")
        print("[TEST] 这包括:")
        print("  1. 市场数据获取")
        print("  2. 多Agent讨论 (会看到当前持仓)")
        print("  3. Risk Analyst分析 (会分析当前持仓风险)")
        print("  4. Trader Agent决策 (会考虑当前持仓)")
        print("  5. 订单执行")
        print()
        
        result = execute_daily_trade(
            rounds=3,
            auto_tools=True,
            tool_budget=8,
            min_tools=3,
            portfolio=portfolio,  # 传入带持仓的portfolio
        )
        
        # 记录结束时间
        end_time = time.time()
        elapsed_time = end_time - start_time
        
        # 计算时间
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)
        milliseconds = int((elapsed_time % 1) * 1000)
        
        print()
        print("=" * 80)
        print("执行完成!")
        print("=" * 80)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"总耗时: {minutes}分 {seconds}秒 {milliseconds}毫秒")
        print(f"总耗时（秒）: {elapsed_time:.2f}秒")
        print()
        
        # 显示结果摘要
        if result:
            conversations = result.get("conversations", [])
            placed_orders = result.get("placed_orders", [])
            buy_orders = result.get("buy_orders", [])
            sell_orders = result.get("sell_orders", [])
            
            print("结果摘要:")
            print(f"  - 对话数量: {len(conversations)}")
            print(f"  - 订单数量: {len(placed_orders)}")
            print(f"  - 买入订单: {len(buy_orders)}")
            print(f"  - 卖出订单: {len(sell_orders)}")
            print()
            
            # 显示最终portfolio状态
            if portfolio:
                print("最终Portfolio状态:")
                print(f"  - 现金: ${portfolio.cash:.2f}")
                print(f"  - 持仓数量: {len(portfolio._positions)}")
                for symbol, pos in portfolio._positions.items():
                    print(f"    {symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f}")
        
        return elapsed_time
        
    except Exception as e:
        end_time = time.time()
        elapsed_time = end_time - start_time
        print()
        print("=" * 80)
        print("执行出错!")
        print("=" * 80)
        print(f"错误: {e}")
        print(f"耗时: {elapsed_time:.2f}秒")
        import traceback
        traceback.print_exc()
        return elapsed_time

if __name__ == "__main__":
    test_with_positions()

