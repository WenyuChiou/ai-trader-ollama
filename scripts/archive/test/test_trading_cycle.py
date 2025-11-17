"""
测试完整的 trading cycle，找出为什么 Trader Agent 没有运行且没有存储聊天记录
"""
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

print("=" * 80)
print("测试完整的 Trading Cycle")
print("=" * 80)

# 1. 检查导入
print("\n1. 检查模块导入")
print("-" * 80)
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

# 2. 检查配置
print("\n2. 检查配置")
print("-" * 80)
try:
    from src.utils.config_loader import load_trading_config
    config = load_trading_config()
    print(f"✅ 配置加载成功")
    print(f"  - Universe: {len(config.get('universe', []))} 股票")
    print(f"  - Rounds: {config.get('rounds', 3)}")
    print(f"  - Tool budget: {config.get('tool_budget', 8)}")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    import traceback
    traceback.print_exc()

# 3. 检查数据目录
print("\n3. 检查数据目录")
print("-" * 80)
project_root = Path(__file__).parent.parent
logs_dir = project_root / "data" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)
convo_file = logs_dir / "discussion_actions.jsonl"

print(f"Logs 目录: {logs_dir}")
print(f"对话文件: {convo_file}")
print(f"对话文件存在: {convo_file.exists()}")

# 检查今天的 Trader Agent 条目数量
if convo_file.exists():
    import json
    today = __import__('datetime').date.today().isoformat()
    trader_count = 0
    total_count = 0
    with convo_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    entry = json.loads(line)
                    total_count += 1
                    if entry.get("agent") == "TraderAgent" and entry.get("date") == today:
                        trader_count += 1
                except:
                    pass
    print(f"今天的 Trader Agent 条目: {trader_count}")
    print(f"总对话条目: {total_count}")

# 4. 检查市场状态
print("\n4. 检查市场状态")
print("-" * 80)
try:
    from src.utils.trading_days import is_market_open
    import pytz
    from datetime import datetime
    
    et_tz = pytz.timezone('America/New_York')
    et_time = datetime.now(et_tz)
    market_open = is_market_open(None)
    
    print(f"当前美东时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"市场是否开放: {market_open}")
except Exception as e:
    print(f"❌ 市场状态检查失败: {e}")
    import traceback
    traceback.print_exc()

# 5. 运行 trading cycle（使用最小参数，快速测试）
print("\n5. 运行 Trading Cycle（测试模式）")
print("-" * 80)
print("⚠️  这将执行完整的 trading cycle，可能需要几分钟...")
print("⚠️  正在运行，请查看控制台输出...")

try:
    # 使用最小 universe 和 rounds 来快速测试
    result = execute_daily_trade(
        rounds=1,  # 只运行 1 轮，快速测试
        auto_tools=True,
        tool_budget=3,  # 减少工具预算
        min_tools=1,
        universe=["AAPL", "MSFT", "NVDA"]  # 只测试 3 只股票
    )
    
    print("\n✅ Trading Cycle 执行完成")
    print(f"  - Placed orders: {len(result.get('placed_orders', []))}")
    print(f"  - Conversations count: {result.get('conversations_count', 0)}")
    print(f"  - Result keys: {list(result.keys())[:10]}...")
    
    # 检查 Trader Agent 条目
    if convo_file.exists():
        import json
        today = __import__('datetime').date.today().isoformat()
        trader_entries = []
        with convo_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        if entry.get("agent") == "TraderAgent" and entry.get("date") == today:
                            trader_entries.append(entry)
                    except:
                        pass
        
        if trader_entries:
            latest = trader_entries[-1]
            print(f"\n✅ 找到 {len(trader_entries)} 个 Trader Agent 条目")
            print(f"  最新条目:")
            print(f"    - Summary: {latest.get('summary', 'N/A')[:100]}...")
            print(f"    - Stance: {latest.get('stance', 'N/A')}")
            print(f"    - Buy orders: {len(latest.get('decision', {}).get('buy_orders', []))}")
            print(f"    - Sell orders: {len(latest.get('decision', {}).get('sell_orders', []))}")
        else:
            print(f"\n❌ 没有找到 Trader Agent 条目")
            print(f"  检查控制台输出中是否有 '[TRADING CYCLE] ===== STEP 4: TRADER AGENT ======' 日志")
            print(f"  检查是否有 '[TRADING CYCLE] ✅ Wrote Trader Agent conversation entry' 日志")
    
except Exception as e:
    print(f"\n❌ Trading Cycle 执行失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n请检查上面的错误信息，特别是:")
    print("  1. 是否有 '[TRADING CYCLE] ===== STEP 4: TRADER AGENT ======' 日志")
    print("  2. 是否有 '[TRADING CYCLE] ❌ ERROR: Trader Agent failed' 日志")
    print("  3. 是否有 '[TRADING CYCLE] ✅ Wrote Trader Agent conversation entry' 日志")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

