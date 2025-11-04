# simulate_weekly_pending_orders.py
"""
模拟上周五天的挂单策略完整流程
- 每天开盘前：运行 trading_cycle（挂限价单）
- 每天收盘后：运行 check_pending_orders.py（检查成交并执行）
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Windows 编码修复
if sys.platform == "win32":
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

# 添加 backend 到 path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger
from src.data.memory_manager import MemoryManager
from src.data.equity_tracker import EquityTracker
from scripts.check_pending_orders import check_and_execute_pending_orders


def get_last_week_dates() -> list[str]:
    """获取上周一到周五的日期"""
    today = date.today()
    
    # 计算上周五（如果今天是周一，上周五是5天前；如果是周二，上周五是6天前，以此类推）
    days_since_friday = (today.weekday() + 3) % 7  # 0=Monday, 4=Friday
    if days_since_friday == 0:
        days_since_friday = 7  # 如果今天是周一，上周五是7天前
    
    last_friday = today - timedelta(days=days_since_friday)
    
    # 从上周一到上周五
    last_monday = last_friday - timedelta(days=4)
    
    week_dates = []
    current = last_monday
    while current <= last_friday:
        # 只包含工作日（周一到周五）
        if current.weekday() < 5:  # 0=Monday, 4=Friday
            week_dates.append(current.isoformat())
        current += timedelta(days=1)
    
    return week_dates


def simulate_weekly_trading(
    dates: list[str] | None = None,
    initial_cash: float = 10000.0,
    portfolio_state_file: Path | None = None,
) -> dict:
    """
    模拟一周的交易
    
    参数:
    - dates: 日期列表（YYYY-MM-DD），如果为 None 则使用上周一到周五
    - initial_cash: 初始现金
    - portfolio_state_file: Portfolio 状态文件路径
    """
    if dates is None:
        dates = get_last_week_dates()
    
    print(f"\n{'='*80}")
    print(f"📅 Simulating Weekly Trading: {dates[0]} to {dates[-1]}")
    print(f"{'='*80}\n")
    
    # 初始化
    portfolio = Portfolio(cash=initial_cash)
    trade_logger = TradeLogger()
    # memory_manager 和 equity_tracker 会在 execute_daily_trade 内部创建
    
    # 加载初始 Portfolio 状态（如果存在）
    if portfolio_state_file and portfolio_state_file.exists():
        try:
            import json
            with open(portfolio_state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            portfolio = Portfolio(cash=state.get("cash", initial_cash))
            # 恢复持仓
            for symbol, pos_info in state.get("positions", {}).items():
                if isinstance(pos_info, dict):
                    qty = pos_info.get("quantity", 0)
                    avg_cost = pos_info.get("avg_cost", 0)
                    if qty > 0 and avg_cost > 0:
                        from src.data.portfolio import Position
                        portfolio._positions[symbol] = Position(
                            symbol=symbol,
                            quantity=qty,
                            avg_cost=avg_cost,
                            total_cost=qty * avg_cost,
                        )
            print(f"[LOADED] Portfolio state from {portfolio_state_file}")
            print(f"  Cash: ${portfolio.cash:.2f}")
            print(f"  Positions: {len(portfolio._positions)} stocks\n")
        except Exception as e:
            print(f"[WARN] Failed to load portfolio state: {e}, using default\n")
    
    # 每天的交易记录
    daily_results = []
    
    for i, trade_date in enumerate(dates):
        day_num = i + 1
        print(f"\n{'='*80}")
        print(f"📆 Day {day_num}/{len(dates)}: {trade_date}")
        print(f"{'='*80}\n")
        
        # --- Step 1: 开盘前挂单（模拟 09:00） ---
        print(f"[STEP 1] 🔹 Pre-Market: Place Limit Orders (09:00)")
        print(f"{'-'*80}\n")
        
        try:
            # 运行交易循环（会挂限价单）
            # 使用 trade_date 的前一天作为分析日期（因为今天分析昨天的数据）
            if i == 0:
                # 第一天：使用 trade_date 的前一天作为分析日期
                analysis_date = (date.fromisoformat(trade_date) - timedelta(days=1)).isoformat()
            else:
                # 后续天：使用前一个交易日期作为分析日期
                analysis_date = dates[i-1]
            
            # 计算日期范围（用于获取市场数据）
            # start: 30天前（用于计算技术指标）
            start_date = (date.fromisoformat(analysis_date) - timedelta(days=30)).isoformat()
            
            result = execute_daily_trade(
                start=start_date,
                end=analysis_date,  # 分析日期（昨天的收盘数据）
                universe=None,  # 使用默认 universe
                portfolio=portfolio,
                trade_logger=trade_logger,
            )
            
            print(f"\n[ORDER PLACEMENT SUMMARY]")
            placed_orders = result.get("placed_orders", [])
            if placed_orders:
                print(f"  ✅ Placed {len(placed_orders)} limit orders:")
                for order in placed_orders:
                    print(f"     {order['action']} {order['symbol']} x{order['quantity']} @ limit ${order['limit_price']:.2f}")
            else:
                print(f"  ⚪ No orders placed")
            
            # 记录当天状态
            from src.data.market_data import get_multi_prices
            universe = result.get("symbols", ["AAPL", "MSFT", "NVDA", "TSLA", "GOOGL"])
            end_date_for_prices = trade_date  # 使用当天日期获取最新价格
            try:
                last_prices = {}
                for symbol in universe:
                    try:
                        prices = get_multi_prices([symbol], start=end_date_for_prices, end=end_date_for_prices, interval="1d")
                        if symbol in prices and not prices[symbol].empty:
                            last_prices[symbol] = float(prices[symbol]["Close"].iloc[-1])
                    except:
                        pass
            except:
                last_prices = {}
            
            portfolio_value = portfolio.value(last_prices) if last_prices else portfolio.cash
            
            daily_result = {
                "date": trade_date,
                "day": day_num,
                "placed_orders": len(placed_orders),
                "portfolio_cash": portfolio.cash,
                "portfolio_value": portfolio_value,
                "positions_count": len(portfolio._positions),
                "analysis_result": result,
            }
            
        except Exception as e:
            print(f"[ERROR] Failed to place orders: {e}")
            import traceback
            traceback.print_exc()
            daily_result = {
                "date": trade_date,
                "day": day_num,
                "error": str(e),
            }
            daily_results.append(daily_result)
            continue
        
        # --- Step 2: 收盘后检查成交（模拟 16:30） ---
        print(f"\n[STEP 2] 🔹 After-Market Close: Check Order Fills (16:30)")
        print(f"{'-'*80}\n")
        
        try:
            # 检查当天的挂单是否成交
            fill_result = check_and_execute_pending_orders(
                check_date=trade_date,
                portfolio_state_file=None,  # 不保存状态，使用内存中的 portfolio
            )
            
            # 更新 portfolio（check_pending_orders 会修改传入的 portfolio）
            # 但因为我们传入的是 None，它会创建新的 portfolio
            # 所以我们需要手动调用 check_pending_orders 的逻辑
            
            # 或者，我们可以直接从 fill_result 中获取信息
            print(f"\n[FILL CHECK SUMMARY]")
            print(f"  Pending Orders: {fill_result['pending_count']}")
            print(f"  ✅ Filled: {fill_result['filled_count']}")
            print(f"  ❌ Rejected: {fill_result['rejected_count']}")
            
            if fill_result['executed_trades']:
                print(f"\n  Executed Trades:")
                for trade in fill_result['executed_trades']:
                    print(f"     {trade['action']} {trade['symbol']} x{trade['quantity']} @ ${trade['price']:.2f}")
            
            daily_result["filled_orders"] = fill_result["filled_count"]
            daily_result["rejected_orders"] = fill_result["rejected_count"]
            daily_result["executed_trades"] = fill_result["executed_trades"]
            
            # 重新计算 Portfolio 价值（因为可能有新的交易）
            portfolio_value = portfolio.value(last_prices) if last_prices else portfolio.cash
            daily_result["portfolio_value_after"] = portfolio_value
            
        except Exception as e:
            print(f"[ERROR] Failed to check order fills: {e}")
            import traceback
            traceback.print_exc()
            daily_result["fill_check_error"] = str(e)
        
        daily_results.append(daily_result)
        
        # 打印当天总结
        print(f"\n[DAY {day_num} SUMMARY]")
        print(f"  Date: {trade_date}")
        print(f"  Cash: ${portfolio.cash:.2f}")
        print(f"  Portfolio Value: ${portfolio_value:.2f}")
        print(f"  Positions: {len(portfolio._positions)} stocks")
        if portfolio._positions:
            print(f"  Holdings:")
            for symbol, pos in portfolio._positions.items():
                current_price = last_prices.get(symbol, pos.avg_cost)
                market_value = pos.quantity * current_price
                pnl = (current_price - pos.avg_cost) * pos.quantity
                print(f"    {symbol}: {pos.quantity} shares @ ${current_price:.2f} (value: ${market_value:.2f}, P&L: ${pnl:.2f})")
    
    # 最终总结
    print(f"\n{'='*80}")
    print(f"📊 WEEKLY TRADING SUMMARY")
    print(f"{'='*80}\n")
    
    print(f"Period: {dates[0]} to {dates[-1]}")
    print(f"\nFinal Portfolio:")
    print(f"  Cash: ${portfolio.cash:.2f}")
    print(f"  Portfolio Value: ${portfolio_value:.2f}")
    print(f"  Total Return: ${portfolio_value - initial_cash:.2f} ({((portfolio_value / initial_cash) - 1) * 100:.2f}%)")
    print(f"  Positions: {len(portfolio._positions)} stocks")
    
    if portfolio._positions:
        print(f"\nFinal Holdings:")
        for symbol, pos in portfolio._positions.items():
            current_price = last_prices.get(symbol, pos.avg_cost) if 'last_prices' in locals() else pos.avg_cost
            market_value = pos.quantity * current_price
            pnl = (current_price - pos.avg_cost) * pos.quantity
            pnl_pct = ((current_price / pos.avg_cost) - 1) * 100 if pos.avg_cost > 0 else 0
            print(f"  {symbol}: {pos.quantity} shares")
            print(f"    Avg Cost: ${pos.avg_cost:.2f}")
            print(f"    Current: ${current_price:.2f}")
            print(f"    Value: ${market_value:.2f}")
            print(f"    P&L: ${pnl:.2f} ({pnl_pct:.2f}%)")
    
    print(f"\nDaily Summary:")
    for dr in daily_results:
        print(f"  {dr['date']}: Placed {dr.get('placed_orders', 0)} orders, "
              f"Filled {dr.get('filled_orders', 0)}, "
              f"Portfolio Value: ${dr.get('portfolio_value_after', dr.get('portfolio_value', 0)):.2f}")
    
    # 保存 Portfolio 状态
    if portfolio_state_file:
        try:
            portfolio_state_file.parent.mkdir(parents=True, exist_ok=True)
            portfolio_state = {
                "cash": portfolio.cash,
                "positions": {
                    symbol: {
                        "quantity": pos.quantity,
                        "avg_cost": pos.avg_cost,
                        "total_cost": pos.total_cost,
                    }
                    for symbol, pos in portfolio._positions.items()
                },
                "last_updated": dates[-1],
            }
            import json
            with open(portfolio_state_file, "w", encoding="utf-8") as f:
                json.dump(portfolio_state, f, indent=2, ensure_ascii=False)
            print(f"\n[SAVED] Portfolio state to {portfolio_state_file}")
        except Exception as e:
            print(f"\n[WARN] Failed to save portfolio state: {e}")
    
    return {
        "dates": dates,
        "initial_cash": initial_cash,
        "final_cash": portfolio.cash,
        "final_portfolio_value": portfolio_value,
        "total_return": portfolio_value - initial_cash,
        "total_return_pct": ((portfolio_value / initial_cash) - 1) * 100,
        "daily_results": daily_results,
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simulate weekly trading with pending order strategy")
    parser.add_argument("--dates", nargs="+", help="Trading dates (YYYY-MM-DD), if not provided, uses last week Mon-Fri")
    parser.add_argument("--cash", type=float, default=10000.0, help="Initial cash")
    parser.add_argument("--state-file", type=str, default="data/logs/weekly_simulation_state.json", help="Portfolio state file")
    
    args = parser.parse_args()
    
    state_file = Path(args.state_file) if args.state_file else None
    dates = args.dates if args.dates else None
    
    result = simulate_weekly_trading(
        dates=dates,
        initial_cash=args.cash,
        portfolio_state_file=state_file,
    )
    
    print(f"\n{'='*80}")
    print(f"✅ Simulation Complete!")
    print(f"{'='*80}\n")

