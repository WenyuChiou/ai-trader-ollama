"""
诊断为什么 Trader Agent 没有执行交易
"""
import sys
import io
from pathlib import Path

# Fix encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from datetime import datetime
import pytz
from src.utils.trading_days import is_market_open, is_trading_day

print("=" * 60)
print("诊断：为什么 Trader Agent 没有执行交易")
print("=" * 60)

# 1. 检查市场状态
print("\n1. 市场状态检查")
print("-" * 60)
et_tz = pytz.timezone('America/New_York')
et_time = datetime.now(et_tz)
print(f"当前美东时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
print(f"今天是交易日: {is_trading_day(et_time.date())}")
print(f"市场是否开放: {is_market_open(None)}")

current_time = et_time.time()
market_open_time = datetime.strptime("09:30", "%H:%M").time()
market_close_time = datetime.strptime("16:00", "%H:%M").time()
print(f"当前时间: {current_time.strftime('%H:%M:%S')}")
print(f"交易时间: {market_open_time.strftime('%H:%M')} - {market_close_time.strftime('%H:%M')} ET")

if market_open_time <= current_time < market_close_time:
    print("✅ 时间在交易时间内")
else:
    print("❌ 时间不在交易时间内")

# 2. 检查今天是否有订单
print("\n2. 订单检查")
print("-" * 60)
from src.data.order_manager import OrderManager

# Get project root
project_root = Path(__file__).parent.parent
logs_dir = project_root / "data" / "logs"
logs_dir.mkdir(parents=True, exist_ok=True)

order_manager = OrderManager(root=logs_dir)
today = datetime.now().date().isoformat()

# 检查 pending 订单
pending_orders = order_manager.load_pending_orders(order_date=today)
print(f"今天的 pending 订单: {len(pending_orders)}")

# 检查 filled 订单
filled_file = logs_dir / "filled_orders.jsonl"
today_has_filled = False
if filled_file.exists():
    import json
    with filled_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    order = json.loads(line)
                    order_date = order.get("date") or order.get("created_at", "").split("T")[0]
                    if order_date == today:
                        today_has_filled = True
                        break
                except:
                    pass

print(f"今天是否有 filled 订单: {today_has_filled}")

if len(pending_orders) > 0 or today_has_filled:
    print("⚠️  今天已经有订单，系统可能跳过创建新订单（防止重复）")
else:
    print("✅ 今天没有订单，应该可以创建新订单")

# 3. 检查 portfolio 状态
print("\n3. Portfolio 状态检查")
print("-" * 60)
try:
    from src.data.portfolio import Portfolio
    portfolio_file = logs_dir / "portfolio_state.json"
    if portfolio_file.exists():
        portfolio = Portfolio.load(str(portfolio_file))
        print(f"Portfolio 现金: ${portfolio.cash:.2f}")
        print(f"Portfolio 净值: ${portfolio.value({}):.2f}")
        print(f"持仓数量: {len(portfolio._positions)}")
        
        if portfolio.cash <= 0:
            print("❌ Portfolio 现金为 0 或负数，无法买入")
        else:
            print("✅ Portfolio 有可用现金")
    else:
        print("⚠️  Portfolio 文件不存在")
except Exception as e:
    print(f"⚠️  无法加载 Portfolio: {e}")

# 4. 检查最近的 Trader Agent 决策
print("\n4. 最近的 Trader Agent 决策")
print("-" * 60)
convo_file = logs_dir / "discussion_actions.jsonl"
if convo_file.exists():
    import json
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
        decision = latest.get("decision", {})
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        print(f"找到 {len(trader_entries)} 个 Trader Agent 条目")
        print(f"最新决策:")
        print(f"  - 买入订单: {len(buy_orders)}")
        print(f"  - 卖出订单: {len(sell_orders)}")
        print(f"  - Summary: {latest.get('summary', 'N/A')[:200]}...")
        
        if len(buy_orders) == 0 and len(sell_orders) == 0:
            print("❌ Trader Agent 没有生成任何订单")
            print(f"  - Rationale: {decision.get('rationale', 'N/A')[:200]}...")
        else:
            print("✅ Trader Agent 生成了订单")
    else:
        print("⚠️  今天没有 Trader Agent 条目")
else:
    print("⚠️  对话文件不存在")

# 5. 总结
print("\n" + "=" * 60)
print("诊断总结")
print("=" * 60)

issues = []
if not is_market_open(None):
    issues.append("市场状态显示关闭（可能是时区问题或不在交易时间）")
if len(pending_orders) > 0 or today_has_filled:
    issues.append("今天已经有订单，系统可能跳过创建新订单")
try:
    portfolio = Portfolio.load(str(portfolio_file))
    if portfolio.cash <= 0:
        issues.append("Portfolio 现金为 0 或负数")
except:
    pass

if issues:
    print("发现的问题:")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")
else:
    print("✅ 没有发现明显问题")
    print("可能的原因:")
    print("  - Trader Agent 没有推荐股票")
    print("  - 所有推荐股票的仓位计算为 0（现金不足、仓位限制等）")
    print("  - 市场分析建议 HOLD")

print("\n建议:")
print("  1. 检查控制台日志中的 [TRADER] 和 [TRADING CYCLE] 消息")
print("  2. 查看 discussion_actions.jsonl 中 Trader Agent 的决策详情")
print("  3. 确认市场状态判断是否正确（时区、交易时间）")
print("  4. 检查是否有足够的可用现金")

