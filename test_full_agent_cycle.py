"""
测试完整的Agent流程执行时间
"""
import sys
import time
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
from src.data.portfolio import Portfolio

def test_full_agent_cycle():
    """测试完整的Agent流程"""
    print("=" * 80)
    print("测试完整的Agent流程执行时间")
    print("=" * 80)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 记录开始时间
    start_time = time.time()
    
    try:
        # 执行完整的交易周期
        print("[TEST] 开始执行交易周期...")
        print("[TEST] 这包括:")
        print("  1. 市场数据获取")
        print("  2. 多Agent讨论 (Market, Technical, Fundamental, Sentiment)")
        print("  3. Risk Analyst分析")
        print("  4. Trader Agent决策")
        print("  5. 订单执行")
        print()
        
        result = execute_daily_trade(
            rounds=3,  # 3轮讨论
            auto_tools=True,
            tool_budget=8,
            min_tools=3,
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
            
            # 显示各阶段时间（如果可用）
            if "timing" in result:
                timing = result["timing"]
                print("各阶段耗时:")
                for stage, duration in timing.items():
                    print(f"  - {stage}: {duration:.2f}秒")
        
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
    test_full_agent_cycle()

