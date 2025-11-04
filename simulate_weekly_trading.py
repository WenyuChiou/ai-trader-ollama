#!/usr/bin/env python3
"""
模拟上周一到周五的完整交易过程

- 使用 universe 中的股票
- 初始资金：10000 美金
- 可以买入股票和反向ETF（如 SQQQ, SPXU, SH, PSQ 等）
- 每天运行一次完整的交易循环
- 保持 Portfolio 状态连续
"""
from __future__ import annotations
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# 添加 backend 目录到路径
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger


def get_last_week_dates() -> List[str]:
    """
    获取上周一到周五的日期列表（YYYY-MM-DD格式）
    假设今天运行，获取上周的交易日
    """
    today = datetime.now()
    
    # 计算上周一的日期
    # today.weekday() 返回 0-6（0=Monday, 6=Sunday）
    days_since_monday = today.weekday()
    last_monday = today - timedelta(days=days_since_monday + 7)  # 上周一
    
    # 生成上周一到周五的日期列表
    dates = []
    for i in range(5):  # 周一到周五
        date = last_monday + timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))
    
    return dates


def load_universe() -> List[str]:
    """从 config.json 加载股票 universe"""
    config_path = ROOT / "config" / "config.json"
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            universe = config.get("universe", [])
            
            # 添加常见的反向ETF选项（用于对冲）
            inverse_etfs = [
                "SQQQ",   # 3x Short QQQ (对冲 NASDAQ)
                "SPXU",   # 3x Short S&P 500
                "SH",     # Short S&P 500
                "PSQ",    # Short QQQ
                "SDS",    # 2x Short S&P 500
                "DOG",    # Short Dow 30
            ]
            
            # 将反向ETF添加到 universe（如果不存在）
            for etf in inverse_etfs:
                if etf not in universe:
                    universe.append(etf)
            
            return universe
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        # 默认返回一些股票
        return ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN", "SQQQ", "SPXU"]


def print_day_header(day: int, date: str):
    """打印每日标题"""
    print("\n" + "="*80)
    print(f" DAY {day}: {date} ({datetime.strptime(date, '%Y-%m-%d').strftime('%A')})")
    print("="*80)


def print_portfolio_summary(portfolio: Portfolio, last_prices: Dict[str, float], day: int):
    """打印投资组合摘要"""
    print(f"\n--- Portfolio Summary (End of Day {day}) ---")
    print(f"Cash: ${portfolio.cash:.2f}")
    print(f"Equity Value: ${portfolio.equity_value(last_prices):.2f}")
    print(f"Total Value: ${portfolio.value(last_prices):.2f}")
    print(f"Total P&L: ${portfolio.total_pnl(last_prices):.2f} ({portfolio.total_pnl_pct(last_prices):.2f}%)")
    
    if portfolio._positions:
        print(f"\nPositions ({len(portfolio._positions)}):")
        for symbol, pos in portfolio._positions.items():
            current_price = last_prices.get(symbol, pos.avg_cost)
            pnl = (current_price - pos.avg_cost) * pos.quantity
            pnl_pct = ((current_price - pos.avg_cost) / pos.avg_cost * 100) if pos.avg_cost > 0 else 0
            print(f"  {symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f} avg → ${current_price:.2f} "
                  f"(P&L: ${pnl:.2f}, {pnl_pct:.2f}%)")
    else:
        print("No positions")


def print_daily_result(result: Dict[str, Any], day: int):
    """打印每日交易结果"""
    print(f"\n--- Trading Results (Day {day}) ---")
    
    decision = result.get("decision", {})
    action = decision.get("action", "HOLD")
    stance = result.get("stance", "neutral")
    
    print(f"Final Stance: {stance}")
    print(f"Trader Action: {action}")
    
    buy_orders = decision.get("buy_orders", [])
    sell_orders = decision.get("sell_orders", [])
    
    if buy_orders:
        print(f"\nBuy Orders ({len(buy_orders)}):")
        for order in buy_orders:
            print(f"  {order.get('symbol')}: {order.get('quantity')} shares @ ${order.get('buy_price', 0):.2f} "
                  f"(Total: ${order.get('total_cost', 0):.2f})")
    
    if sell_orders:
        print(f"\nSell Orders ({len(sell_orders)}):")
        for order in sell_orders:
            print(f"  {order.get('symbol')}: {order.get('quantity')} shares @ ${order.get('sell_price', 0):.2f} "
                  f"(Total: ${order.get('total_proceeds', 0):.2f})")
    
    executed = result.get("executed_trades", [])
    if executed:
        print(f"\nExecuted Trades ({len(executed)}):")
        for trade in executed[:5]:  # 只显示前5个
            print(f"  {trade.get('action')} {trade.get('symbol')}: {trade.get('quantity')} shares @ ${trade.get('price', 0):.2f}")
    
    errors = result.get("execution_errors", [])
    if errors:
        print(f"\nExecution Errors ({len(errors)}):")
        for error in errors[:3]:  # 只显示前3个错误
            print(f"  {error}")


def simulate_weekly_trading():
    """模拟上周一到周五的完整交易过程"""
    print("\n" + "="*80)
    print(" WEEKLY TRADING SIMULATION")
    print(" Last Week (Monday - Friday)")
    print("="*80)
    
    # 获取上周日期
    dates = get_last_week_dates()
    print(f"\nSimulating trading for:")
    for i, date in enumerate(dates, 1):
        day_name = datetime.strptime(date, '%Y-%m-%d').strftime('%A')
        print(f"  Day {i}: {date} ({day_name})")
    
    # 加载 universe
    universe = load_universe()
    print(f"\nUniverse: {len(universe)} symbols")
    print(f"  Stocks: {[s for s in universe if s not in ['SQQQ', 'SPXU', 'SH', 'PSQ', 'SDS', 'DOG']][:10]}...")
    print(f"  Inverse ETFs: {[s for s in universe if s in ['SQQQ', 'SPXU', 'SH', 'PSQ', 'SDS', 'DOG']]}")
    
    # 初始化投资组合
    initial_cash = 10000.0
    portfolio = Portfolio(cash=initial_cash, initial_value=initial_cash)
    trade_logger = TradeLogger()
    
    print(f"\nInitial Capital: ${initial_cash:.2f}")
    
    # 存储每日结果
    daily_results: List[Dict[str, Any]] = []
    
    # 模拟每一天
    for day_num, date in enumerate(dates, 1):
        print_day_header(day_num, date)
        
        # 计算日期范围（使用前180天作为历史数据窗口）
        start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=180)).strftime('%Y-%m-%d')
        end_date = date
        
        print(f"\nData Window: {start_date} to {end_date}")
        print(f"Analysis Date: {date}")
        
        try:
            # 执行每日交易循环（开盘前挂单）
            print(f"\n[Executing daily trading cycle...]")
            print(f"[NOTE] Orders will be placed (pending), fills checked after market close")
            result = execute_daily_trade(
                universe=universe,
                start=start_date,
                end=end_date,
                rounds=3,  # 讨论轮数
                auto_tools=True,
                tool_budget=2,  # 工具预算
                portfolio=portfolio,  # 使用同一个 portfolio，保持连续状态
                trade_logger=trade_logger,
            )
            
            # 收盘后检查挂单是否成交
            print(f"\n[Checking pending orders after market close...]")
            from src.data.order_manager import OrderManager
            from scripts.check_pending_orders import check_and_execute_pending_orders
            
            order_manager = OrderManager(root="data/logs")
            pending_orders = order_manager.load_pending_orders(order_date=date)
            
            fill_result = None
            if pending_orders:
                # 检查当天的挂单是否成交（傳入當前 portfolio 實例）
                fill_result = check_and_execute_pending_orders(
                    check_date=date,
                    portfolio_state_file=Path("data/logs/portfolio_state.json"),
                    portfolio=portfolio,  # 傳入當前 portfolio，避免重複加載
                )
                print(f"  Orders checked: {fill_result['pending_count']}")
                print(f"  Filled: {fill_result['filled_count']}")
                print(f"  Rejected: {fill_result['rejected_count']}")
                print(f"  Executed trades: {len(fill_result.get('executed_trades', []))}")
                
                # 更新 Portfolio（check_pending_orders 已經更新了 portfolio）
                # Portfolio 狀態已保存在文件中，但我們需要更新內存中的實例
                if fill_result.get('portfolio_snapshot'):
                    portfolio_snapshot = fill_result['portfolio_snapshot']
                    portfolio.cash = portfolio_snapshot.get('cash', portfolio.cash)
                    # 持倉已在 check_pending_orders 中更新
            else:
                print(f"  No pending orders to check")
            
            # 保存每日结果（先保存，然后再更新）
            daily_results.append({
                "day": day_num,
                "date": date,
                "result": result,
            })
            
            # 保存成交明細到每日結果
            if fill_result:
                daily_results[-1]["fill_result"] = fill_result
                daily_results[-1]["executed_trades"] = fill_result.get("executed_trades", [])
                daily_results[-1]["filled_orders"] = fill_result["filled_count"]
                daily_results[-1]["rejected_orders"] = fill_result["rejected_count"]
            
            # 打印每日结果
            print_daily_result(result, day_num)
            
            # 获取最新价格（用于计算组合价值）
            # 方法1：从 buy_orders/sell_orders 获取价格
            last_prices = {}
            
            buy_orders = result.get("decision", {}).get("buy_orders", [])
            sell_orders = result.get("decision", {}).get("sell_orders", [])
            
            for order in buy_orders:
                symbol = order.get("symbol")
                price = order.get("buy_price")
                if symbol and price:
                    last_prices[symbol] = float(price)
            
            for order in sell_orders:
                symbol = order.get("symbol")
                price = order.get("sell_price")
                if symbol and price:
                    last_prices[symbol] = float(price)
            
            # 方法2：对于已有持仓的股票，如果没有获取到价格，从市场数据获取
            from src.tools.market_tools import fetch_market_batch
            try:
                # 获取所有持仓股票的最新价格
                held_symbols = list(portfolio._positions.keys())
                if held_symbols:
                    missing_symbols = [s for s in held_symbols if s not in last_prices]
                    if missing_symbols:
                        # 获取这些股票的当天价格
                        market_data = fetch_market_batch.invoke({
                            "symbols": missing_symbols,
                            "start": date,
                            "end": date,
                        })
                        stocks = market_data.get("stocks", {})
                        for symbol in missing_symbols:
                            if symbol in stocks:
                                try:
                                    price = float(stocks[symbol].get("price", 0))
                                    if price > 0:
                                        last_prices[symbol] = price
                                except Exception:
                                    pass
            except Exception as e:
                # 如果获取失败，使用平均成本作为后备
                print(f"  [WARN] Failed to fetch prices for some symbols: {e}")
            
            # 方法3：对于仍然没有价格的持仓，使用平均成本
            for symbol, pos in portfolio._positions.items():
                if symbol not in last_prices:
                    last_prices[symbol] = pos.avg_cost
            
            # 打印投资组合摘要
            if last_prices:
                print_portfolio_summary(portfolio, last_prices, day_num)
            
            # 更新每日結果中的 last_prices（用於後續總結）
            if last_prices:
                daily_results[-1]["last_prices"] = last_prices
            
            # 生成每日报告
            try:
                from scripts.generate_daily_report import generate_daily_report, print_daily_report
                daily_report = generate_daily_report(date)
                if "error" not in daily_report:
                    print_daily_report(daily_report)
            except Exception as e:
                print(f"  [WARN] Failed to generate daily report: {e}")
            
            print(f"\n[Day {day_num} completed]")
            
        except Exception as e:
            print(f"\n[ERROR] Day {day_num} failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            # 继续下一天
            continue
    
    # 打印周总结
    print("\n" + "="*80)
    print(" WEEKLY SUMMARY")
    print("="*80)
    
    # 獲取最終價格（從最後一天的結果或從市場獲取）
    final_last_prices = {}
    if daily_results:
        # 嘗試從最後一天的結果獲取價格
        final_last_prices = daily_results[-1].get("last_prices", {})
    
    # 如果沒有，嘗試從市場獲取當前價格
    if not final_last_prices and portfolio._positions:
        try:
            from src.tools.market_tools import fetch_market_batch
            held_symbols = list(portfolio._positions.keys())
            market_data = fetch_market_batch.invoke({
                "symbols": held_symbols,
                "start": dates[-1],  # 最後一天的日期
                "end": dates[-1],
            })
            stocks = market_data.get("stocks", {})
            for symbol in held_symbols:
                if symbol in stocks:
                    final_last_prices[symbol] = float(stocks[symbol].get("price", 0))
        except Exception:
            pass
    
    # 如果還是沒有，使用成本價
    if not final_last_prices:
        for symbol, pos in portfolio._positions.items():
            final_last_prices[symbol] = pos.avg_cost
    
    final_portfolio_value = portfolio.value(final_last_prices) if final_last_prices else portfolio.cash
    final_pnl = portfolio.total_pnl(final_last_prices) if final_last_prices else 0.0
    final_pnl_pct = portfolio.total_pnl_pct(final_last_prices) if final_last_prices else 0.0
    
    print(f"\nInitial Capital: ${initial_cash:.2f}")
    print(f"Final Portfolio Value: ${final_portfolio_value:.2f}")
    print(f"Total P&L: ${final_pnl:.2f} ({final_pnl_pct:.2f}%)")
    print(f"Cash Remaining: ${portfolio.cash:.2f}")
    print(f"Equity Value: ${portfolio.equity_value(final_last_prices) if final_last_prices else 0.0:.2f}")
    
    if portfolio._positions:
        print(f"\nFinal Positions ({len(portfolio._positions)}):")
        for symbol, pos in portfolio._positions.items():
            current_price = final_last_prices.get(symbol, pos.avg_cost) if final_last_prices else pos.avg_cost
            pnl = (current_price - pos.avg_cost) * pos.quantity
            pnl_pct = ((current_price - pos.avg_cost) / pos.avg_cost * 100) if pos.avg_cost > 0 else 0
            print(f"  {symbol}: {pos.quantity} shares @ ${pos.avg_cost:.2f} avg "
                  f"(Current: ${current_price:.2f}, P&L: ${pnl:.2f}, {pnl_pct:.2f}%)")
    
    # 统计每日交易
    total_trades = 0
    total_buys = 0
    total_sells = 0
    
    for daily in daily_results:
        # 優先使用 fill_result 中的 executed_trades（實際成交的）
        executed = daily.get("executed_trades", [])
        if not executed:
            # 如果沒有，嘗試從 result 中獲取（可能是掛單信息）
            executed = daily.get("result", {}).get("executed_trades", [])
        total_trades += len([t for t in executed if t.get("status") == "FILLED"])
        total_buys += len([t for t in executed if t.get("action") == "BUY" and t.get("status") == "FILLED"])
        total_sells += len([t for t in executed if t.get("action") == "SELL" and t.get("status") == "FILLED"])
    
    print(f"\nTrading Statistics:")
    print(f"  Total Trades: {total_trades}")
    print(f"  Buy Orders: {total_buys}")
    print(f"  Sell Orders: {total_sells}")
    print(f"  Days with Trades: {len([d for d in daily_results if d.get('executed_trades') or d.get('filled_orders', 0) > 0])}")
    
    print("\n" + "="*80)
    print(" SIMULATION COMPLETE")
    print("="*80 + "\n")
    
    # 保存结果到文件
    output_file = ROOT / "data" / "logs" / "weekly_simulation.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    summary = {
        "simulation_date": datetime.now().isoformat(),
        "week_dates": dates,
        "initial_capital": initial_cash,
        "final_portfolio_value": final_portfolio_value,
        "total_pnl": final_pnl,
        "total_pnl_pct": final_pnl_pct,
        "final_cash": portfolio.cash,
        "final_positions": {
            symbol: {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "total_cost": pos.total_cost,
            }
            for symbol, pos in portfolio._positions.items()
        },
        "trading_stats": {
            "total_trades": total_trades,
            "total_buys": total_buys,
            "total_sells": total_sells,
        },
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"Results saved to: {output_file}")


if __name__ == "__main__":
    try:
        simulate_weekly_trading()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPTED] Simulation stopped by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FATAL ERROR] Simulation failed: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

