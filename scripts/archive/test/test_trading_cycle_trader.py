"""
测试 Trading Cycle 中 Trader Agent 的调用和聊天记录存储
"""
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

print("=" * 60)
print("测试 Trading Cycle - Trader Agent 调用和聊天记录")
print("=" * 60)

# 1. 检查必要的模块是否可以导入
print("\n1. 检查模块导入")
print("-" * 60)
try:
    from src.orchestrator.trading_cycle import execute_daily_trade
    print("✅ execute_daily_trade 导入成功")
except Exception as e:
    print(f"❌ execute_daily_trade 导入失败: {e}")
    sys.exit(1)

try:
    from src.agents.trader_agent import run_trader
    print("✅ run_trader 导入成功")
except Exception as e:
    print(f"❌ run_trader 导入失败: {e}")
    sys.exit(1)

# 2. 检查日志文件
print("\n2. 检查日志文件")
print("-" * 60)
from src.orchestrator.trading_cycle import _get_project_logs_dir

logs_dir = _get_project_logs_dir()
convo_file = logs_dir / "discussion_actions.jsonl"

print(f"日志目录: {logs_dir}")
print(f"对话文件: {convo_file}")
print(f"对话文件存在: {convo_file.exists()}")

if convo_file.exists():
    import json
    with convo_file.open("r", encoding="utf-8") as f:
        lines = f.readlines()
    print(f"对话文件总行数: {len(lines)}")
    
    # 检查今天的 Trader Agent 条目
    from datetime import date
    today = date.today().isoformat()
    trader_entries = []
    for line in lines:
        if line.strip():
            try:
                entry = json.loads(line)
                if entry.get("agent") == "TraderAgent" and entry.get("date") == today:
                    trader_entries.append(entry)
            except:
                pass
    print(f"今天的 Trader Agent 条目: {len(trader_entries)}")
    if trader_entries:
        latest = trader_entries[-1]
        print(f"最新条目:")
        print(f"  - Summary: {latest.get('summary', 'N/A')[:100]}...")
        print(f"  - Buy orders: {len(latest.get('decision', {}).get('buy_orders', []))}")
        print(f"  - Sell orders: {len(latest.get('decision', {}).get('sell_orders', []))}")

# 3. 检查 execute_daily_trade 的完整流程
print("\n3. 检查 execute_daily_trade 流程")
print("-" * 60)
print("检查关键步骤:")
print("  - Step 1: Market data fetch")
print("  - Step 2: Analyst Discussion")
print("  - Step 3: Risk Analyst")
print("  - Step 4: Trader Agent (这是我们要检查的)")
print("  - Step 5: Order execution")

# 4. 检查是否有条件导致提前返回
print("\n4. 检查可能导致提前返回的条件")
print("-" * 60)

# 检查 portfolio 是否存在
portfolio_file = logs_dir / "portfolio_state.json"
if portfolio_file.exists():
    print(f"✅ Portfolio 文件存在: {portfolio_file}")
    try:
        from src.data.portfolio import Portfolio
        portfolio = Portfolio.load(str(portfolio_file))
        print(f"  - Cash: ${portfolio.cash:.2f}")
        print(f"  - Positions: {len(portfolio._positions)}")
    except Exception as e:
        print(f"⚠️  Portfolio 加载失败: {e}")
else:
    print(f"⚠️  Portfolio 文件不存在: {portfolio_file}")

# 5. 检查市场状态
print("\n5. 检查市场状态")
print("-" * 60)
from src.utils.trading_days import is_market_open
import pytz
from datetime import datetime

et_tz = pytz.timezone('America/New_York')
et_time = datetime.now(et_tz)
market_open = is_market_open(None)

print(f"当前美东时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"市场是否开放: {market_open}")

# 6. 模拟一个最小化的 trading cycle 调用
print("\n6. 模拟最小化 Trading Cycle 调用")
print("-" * 60)
print("注意: 这将运行完整的 trading cycle，可能需要较长时间")
print("建议: 检查控制台输出中的 [TRADING CYCLE] 日志")

# 不实际运行，只检查代码路径
print("代码路径检查:")
print("  - execute_daily_trade() 被调用")
print("  - 执行到 Step 4: TRADER AGENT")
print("  - 调用 run_trader()")
print("  - 写入 Trader Agent conversation entry")

print("\n" + "=" * 60)
print("诊断总结")
print("=" * 60)
print("如果 Trader Agent 没有运行，可能的原因:")
print("  1. execute_daily_trade() 在调用 run_trader() 之前就返回了")
print("  2. run_trader() 抛出异常但被捕获了（应该会看到错误日志）")
print("  3. 代码执行到 run_trader() 但函数内部提前返回了")
print("  4. 聊天记录写入失败（应该会看到错误日志）")
print("\n建议:")
print("  1. 检查控制台输出，查找 '[TRADING CYCLE] ===== STEP 4: TRADER AGENT ======'")
print("  2. 检查是否有 '[TRADING CYCLE] ✅ Trader Agent completed successfully' 或错误信息")
print("  3. 检查是否有 '[TRADING CYCLE] ✅ Wrote Trader Agent conversation entry'")
print("  4. 如果都没有，说明代码在 Step 4 之前就退出了")

