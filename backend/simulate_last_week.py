# simulate_last_week.py
"""
模拟运行上周五天（周一到周五）的完整交易循环
- 每天运行完整的交易循环（开盘前挂单）
- 收盘后检查挂单是否成交
- 持续更新 Portfolio 状态
"""
from __future__ import annotations
import sys
from pathlib import Path
from datetime import date, timedelta
import json

# 添加 backend 到 path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger
from src.data.order_manager import OrderManager
from scripts.check_pending_orders import check_and_execute_pending_orders


def get_last_week_dates() -> list[date]:
    """获取上周的工作日（周一到周五）"""
    today = date.today()
    
    # 找到上周一
    days_since_monday = (today.weekday() + 7) % 7  # 0 = Monday
    last_monday = today - timedelta(days=days_since_monday + 7)
    
    # 获取上周一到周五
    week_dates = []
    for i in range(5):
        day = last_monday + timedelta(days=i)
        week_dates.append(day)
    
    return week_dates


def load_portfolio_state(state_file: Path) -> tuple[Portfolio, TradeLogger]:
    """加载 Portfolio 和 TradeLogger 状态"""
    portfolio = Portfolio(cash=10000.0)
    trade_logger = TradeLogger()
    
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                state = json.load(f)
            portfolio = Portfolio(cash=state.get("cash", 10000.0))
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
            print(f"[LOADED] Portfolio state from {state_file}")
            print(f"  Cash: ${portfolio.cash:.2f}")
            print(f"  Positions: {len(portfolio._positions)}")
        except Exception as e:
            print(f"[WARN] Failed to load portfolio state: {e}, using default")
    
    return portfolio, trade_logger


def save_portfolio_state(portfolio: Portfolio, state_file: Path):
    """保存 Portfolio 状态"""
    try:
        state_file.parent.mkdir(parents=True, exist_ok=True)
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
            "last_updated": date.today().isoformat(),
        }
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(portfolio_state, f, indent=2, ensure_ascii=False)
        print(f"[SAVED] Portfolio state to {state_file}")
    except Exception as e:
        print(f"[WARN] Failed to save portfolio state: {e}")


def simulate_week(
    start_date: str | None = None,
    end_date: str | None = None,
    state_file: Path | None = None,
):
    """
    模拟运行一周的交易
    
    参数:
    - start_date: 开始日期 (YYYY-MM-DD)，如果为 None，使用上周一
    - end_date: 结束日期 (YYYY-MM-DD)，如果为 None，使用上周五
    - state_file: Portfolio 状态文件路径
    """
    # 确定日期范围
    if start_date and end_date:
        dates = []
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
        current = start
        while current <= end:
            # 只包含工作日（周一到周五）
            if current.weekday() < 5:
                dates.append(current)
            current += timedelta(days=1)
    else:
        dates = get_last_week_dates()
    
    print(f"\n{'='*60}")
    print(f"📅 Simulating Trading Week: {dates[0]} to {dates[-1]}")
    print(f"{'='*60}\n")
    
    # 初始化状态文件
    if state_file is None:
        state_file = Path("data/logs/portfolio_state.json")
    
    # 加载初始 Portfolio 状态
    portfolio, trade_logger = load_portfolio_state(state_file)
    initial_cash = portfolio.cash
    
    # 每天的交易结果
    daily_results = []
    
    for i, trading_date in enumerate(dates):
        date_str = trading_date.isoformat()
        print(f"\n{'='*60}")
        print(f"📊 Day {i+1}/{len(dates)}: {date_str} ({trading_date.strftime('%A')})")
        print(f"{'='*60}\n")
        
        # === Step 1: 开盘前挂单（09:00） ===
        print(f"[{date_str}] Step 1: Pre-market analysis and order placement (09:00)")
        print("-" * 60)
        
        # 计算分析日期（使用前一天的数据）
        analysis_date = (trading_date - timedelta(days=1)).isoformat()
        start_date = analysis_date
        end_date = date_str
        
        try:
            # 运行交易循环（开盘前挂单）
            result = execute_daily_trade(
                start=start_date,
                end=end_date,
                portfolio=portfolio,
                trade_logger=trade_logger,
                universe=None,  # 使用默认 universe
            )
            
            print(f"\n[SUMMARY] Trading cycle completed for {date_str}")
            print(f"  Stance: {result.get('stance', 'N/A')}")
            print(f"  Placed Orders: {len(result.get('placed_orders', []))}")
            print(f"  Execution Errors: {len(result.get('execution_errors', []))}")
            
            # 更新 Portfolio（注意：此时订单只是挂单，尚未成交）
            # Portfolio 会在收盘后检查时更新
            portfolio_snapshot = result.get("portfolio", {})
            print(f"  Portfolio Value: ${portfolio_snapshot.get('total_value', 0):.2f}")
            print(f"  Cash: ${portfolio_snapshot.get('cash', 0):.2f}")
            
            daily_results.append({
                "date": date_str,
                "result": result,
                "orders_placed": len(result.get("placed_orders", [])),
            })
            
        except Exception as e:
            print(f"[ERROR] Trading cycle failed for {date_str}: {e}")
            import traceback
            traceback.print_exc()
            continue
        
        # === Step 2: 收盘后检查成交（16:30） ===
        print(f"\n[{date_str}] Step 2: Check pending orders after market close (16:30)")
        print("-" * 60)
        
        try:
            # 检查当天的挂单是否成交
            fill_result = check_and_execute_pending_orders(
                check_date=date_str,
                portfolio_state_file=state_file,
            )
            
            print(f"\n[FILL SUMMARY] {date_str}")
            print(f"  Pending Orders Checked: {fill_result['pending_count']}")
            print(f"  Filled: {fill_result['filled_count']}")
            print(f"  Rejected: {fill_result['rejected_count']}")
            print(f"  Executed Trades: {len(fill_result['executed_trades'])}")
            
            # 重新加载 Portfolio 状态（因为 check_pending_orders 会更新它）
            portfolio, trade_logger = load_portfolio_state(state_file)
            
            daily_results[-1]["fill_result"] = fill_result
            daily_results[-1]["filled_orders"] = fill_result["filled_count"]
            daily_results[-1]["rejected_orders"] = fill_result["rejected_count"]
            
        except Exception as e:
            print(f"[ERROR] Order fill check failed for {date_str}: {e}")
            import traceback
            traceback.print_exc()
        
        # 保存当前状态（用于下一轮）
        save_portfolio_state(portfolio, state_file)
    
    # === 最终总结 ===
    print(f"\n{'='*60}")
    print(f"📊 WEEKLY SIMULATION SUMMARY")
    print(f"{'='*60}\n")
    
    print(f"Trading Period: {dates[0]} to {dates[-1]} ({len(dates)} days)")
    print(f"\nInitial Capital: ${initial_cash:.2f}")
    print(f"Final Cash: ${portfolio.cash:.2f}")
    print(f"Final Portfolio Value: ${portfolio.value({}):.2f}")
    
    # 计算总盈亏
    final_value = portfolio.cash + sum(
        pos.total_cost for pos in portfolio._positions.values()
    )
    total_pnl = final_value - initial_cash
    total_pnl_pct = (total_pnl / initial_cash) * 100 if initial_cash > 0 else 0
    
    print(f"Total P&L: ${total_pnl:.2f} ({total_pnl_pct:+.2f}%)")
    
    print(f"\nDaily Breakdown:")
    print(f"{'Date':<12} {'Orders':<8} {'Filled':<8} {'Rejected':<10} {'Portfolio Value':<15}")
    print("-" * 60)
    for day_result in daily_results:
        date_str = day_result["date"]
        orders = day_result["orders_placed"]
        filled = day_result.get("filled_orders", 0)
        rejected = day_result.get("rejected_orders", 0)
        portfolio_val = day_result["result"].get("portfolio", {}).get("total_value", 0)
        print(f"{date_str:<12} {orders:<8} {filled:<8} {rejected:<10} ${portfolio_val:<14.2f}")
    
    # 持仓总结
    if portfolio._positions:
        print(f"\nFinal Positions:")
        print(f"{'Symbol':<10} {'Quantity':<10} {'Avg Cost':<12} {'Total Cost':<12}")
        print("-" * 50)
        for symbol, pos in portfolio._positions.items():
            print(f"{symbol:<10} {pos.quantity:<10} ${pos.avg_cost:<11.2f} ${pos.total_cost:<11.2f}")
    
    print(f"\n{'='*60}")
    print(f"✅ Simulation Complete")
    print(f"{'='*60}\n")
    
    return {
        "dates": [d.isoformat() for d in dates],
        "initial_cash": initial_cash,
        "final_cash": portfolio.cash,
        "final_value": final_value,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "daily_results": daily_results,
        "final_positions": {
            symbol: {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "total_cost": pos.total_cost,
            }
            for symbol, pos in portfolio._positions.items()
        },
    }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Simulate last week's trading")
    parser.add_argument("--start", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--state-file", type=str, default="data/logs/portfolio_state.json", help="Portfolio state file")
    
    args = parser.parse_args()
    
    state_file = Path(args.state_file) if args.state_file else None
    
    result = simulate_week(
        start_date=args.start,
        end_date=args.end,
        state_file=state_file,
    )
    
    # 保存结果到文件
    output_file = Path("data/logs/weekly_simulation_result.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Results saved to {output_file}")

