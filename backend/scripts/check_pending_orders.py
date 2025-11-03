# scripts/check_pending_orders.py
"""
收盤後檢查掛單是否成交
- 檢查前一天的掛單
- 根據當天的 High/Low 判斷是否成交
- 執行成交的訂單，更新 Portfolio
"""
from __future__ import annotations
import sys
from pathlib import Path

# 添加 backend 到 path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from datetime import date, timedelta, datetime
from src.data.order_manager import OrderManager
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger


def check_and_execute_pending_orders(
    check_date: str | None = None,
    portfolio_state_file: Path | None = None,
    portfolio: Portfolio | None = None,
) -> dict:
    """
    檢查並執行待處理的掛單
    
    參數:
    - check_date: 檢查的日期（默認為昨天）
    - portfolio_state_file: Portfolio 狀態文件路徑
    - portfolio: 可選的 Portfolio 實例（如果提供，會直接使用並更新）
    """
    # 確定檢查日期（默認為昨天，因為今天可能還在交易中）
    if check_date is None:
        check_date = (date.today() - timedelta(days=1)).isoformat()
    
    print(f"[CHECK ORDERS] Checking pending orders for {check_date}")
    
    # 初始化
    order_manager = OrderManager(root="data/logs")
    
    # 加載 Portfolio 和 Trade Logger
    trade_logger = TradeLogger()
    
    # 如果传入了 portfolio，使用它；否则从文件加载或创建新的
    if portfolio is None:
        if portfolio_state_file and portfolio_state_file.exists():
            try:
                import json
                with open(portfolio_state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                portfolio = Portfolio(cash=state.get("cash", 10000.0))
                # 恢復持倉
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
            except Exception as e:
                print(f"[WARN] Failed to load portfolio state: {e}, using default")
                portfolio = Portfolio()
        else:
            portfolio = Portfolio()
    
    # 加載該日期的待處理訂單
    pending_orders = order_manager.load_pending_orders(order_date=check_date)
    
    if not pending_orders:
        print(f"[CHECK ORDERS] No pending orders found for {check_date}")
        return {
            "checked_date": check_date,
            "pending_count": 0,
            "filled_count": 0,
            "rejected_count": 0,
            "executed_trades": [],
        }
    
    print(f"[CHECK ORDERS] Found {len(pending_orders)} pending orders")
    
    executed_trades = []
    filled_count = 0
    rejected_count = 0
    
    # 檢查每個訂單
    for order in pending_orders:
        symbol = order["symbol"]
        action = order["action"]
        quantity = order["quantity"]
        limit_price = order["limit_price"]
        
        # 檢查是否成交
        fill_result = order_manager.check_order_fill(order, check_date)
        
        if fill_result["filled"]:
            # 訂單已成交
            fill_price = fill_result["fill_price"]
            daily_high = fill_result["daily_high"]
            daily_low = fill_result["daily_low"]
            
            print(f"[FILLED] {action} {symbol} x{quantity} @ ${fill_price:.2f} (daily range: ${daily_low:.2f}-${daily_high:.2f})")
            
            try:
                # 執行交易
                if action == "BUY":
                    # 檢查現金
                    total_cost = fill_price * quantity
                    if total_cost > portfolio.cash:
                        # 現金不足，減少數量
                        from math import floor
                        max_qty = floor(portfolio.cash / fill_price)
                        if max_qty > 0:
                            quantity = max_qty
                            total_cost = fill_price * quantity
                            print(f"[ADJUST] Reduced quantity to {quantity} due to cash limit")
                        else:
                            print(f"[SKIP] Insufficient cash for {symbol}")
                            order_manager.mark_order_filled(order, {
                                "filled": False,
                                "fill_price": None,
                                "fill_reason": "Insufficient cash",
                                "daily_high": daily_high,
                                "daily_low": daily_low,
                            })
                            rejected_count += 1
                            continue
                    
                    portfolio.buy(symbol, quantity, fill_price)
                    
                    trade_logger.log(
                        symbol=symbol,
                        action="BUY",
                        price=fill_price,
                        quantity=quantity,
                        amount=total_cost,
                        status="SUCCESS",
                        reason=f"Order filled: {fill_result['fill_reason']}",
                        rationale=f"Limit order executed (limit: ${limit_price:.2f}, daily low: ${daily_low:.2f})",
                    )
                    
                    executed_trades.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "price": fill_price,
                        "quantity": quantity,
                        "amount": total_cost,
                        "status": "FILLED",
                        "limit_price": limit_price,
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                        "fill_reason": fill_result["fill_reason"],
                        "order_date": order.get("order_date"),
                        "filled_at": datetime.now().isoformat(),
                    })
                
                elif action == "SELL":
                    # 檢查持倉
                    pos = portfolio.get_position(symbol)
                    if not pos or pos.quantity < quantity:
                        print(f"[SKIP] Insufficient position for {symbol}")
                        order_manager.mark_order_filled(order, {
                            "filled": False,
                            "fill_price": None,
                            "fill_reason": "Insufficient position",
                            "daily_high": daily_high,
                            "daily_low": daily_low,
                        })
                        rejected_count += 1
                        continue
                    
                    total_proceeds = fill_price * quantity
                    portfolio.sell(symbol, quantity, fill_price)
                    
                    trade_logger.log(
                        symbol=symbol,
                        action="SELL",
                        price=fill_price,
                        quantity=quantity,
                        amount=total_proceeds,
                        status="SUCCESS",
                        reason=f"Order filled: {fill_result['fill_reason']}",
                        rationale=f"Limit order executed (limit: ${limit_price:.2f}, daily high: ${daily_high:.2f})",
                    )
                    
                    executed_trades.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "price": fill_price,
                        "quantity": quantity,
                        "amount": total_proceeds,
                        "status": "FILLED",
                        "limit_price": limit_price,
                        "daily_high": daily_high,
                        "daily_low": daily_low,
                        "fill_reason": fill_result["fill_reason"],
                        "order_date": order.get("order_date"),
                        "filled_at": datetime.now().isoformat(),
                    })
                
                # 標記訂單為已成交
                order_manager.mark_order_filled(order, fill_result)
                filled_count += 1
                
            except Exception as e:
                print(f"[ERROR] Failed to execute {action} {symbol}: {e}")
                order_manager.mark_order_filled(order, {
                    "filled": False,
                    "fill_price": None,
                    "fill_reason": f"Execution error: {e}",
                    "daily_high": fill_result.get("daily_high"),
                    "daily_low": fill_result.get("daily_low"),
                })
                rejected_count += 1
        
        else:
            # 訂單未成交
            print(f"[REJECTED] {action} {symbol}: {fill_result['fill_reason']}")
            order_manager.mark_order_filled(order, fill_result)
            rejected_count += 1
    
    # 保存 Portfolio 狀態（如果提供了文件路径）
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
                "last_updated": date.today().isoformat(),
            }
            import json
            with open(portfolio_state_file, "w", encoding="utf-8") as f:
                json.dump(portfolio_state, f, indent=2, ensure_ascii=False)
            print(f"[SAVED] Portfolio state saved to {portfolio_state_file}")
        except Exception as e:
            print(f"[WARN] Failed to save portfolio state: {e}")
    
    print(f"[SUMMARY] Checked {len(pending_orders)} orders: {filled_count} filled, {rejected_count} rejected")
    
    # === 記錄成交明細和更新每日淨值（成交後） ===
    portfolio_snapshot = None
    if executed_trades:
        try:
            from src.data.equity_tracker import EquityTracker
            from src.data.memory_manager import MemoryManager
            
            equity_tracker = EquityTracker(root="data/logs")
            memory_manager = MemoryManager(root="data/logs")
            
            # 獲取當前價格（用於計算市值和 P&L）
            from src.tools.market_tools import fetch_market_batch
            last_prices = {}
            try:
                held_symbols = list(portfolio._positions.keys())
                if held_symbols:
                    market_data = fetch_market_batch.invoke({
                        "symbols": held_symbols,
                        "start": check_date,
                        "end": check_date,
                    })
                    stocks = market_data.get("stocks", {})
                    for symbol in held_symbols:
                        if symbol in stocks:
                            last_prices[symbol] = float(stocks[symbol].get("price", 0))
            except Exception as e:
                print(f"[WARN] Failed to fetch current prices: {e}, using cost basis")
                # 使用成本價作為後備
                for symbol, pos in portfolio._positions.items():
                    last_prices[symbol] = pos.avg_cost
            
            # 計算 Portfolio 快照（成交後）
            portfolio_value = portfolio.value(last_prices) if last_prices else portfolio.cash
            equity_value = portfolio.equity_value(last_prices) if last_prices else 0.0
            total_pnl = portfolio.total_pnl(last_prices) if last_prices else 0.0
            total_pnl_pct = portfolio.total_pnl_pct(last_prices) if last_prices else 0.0
            
            # 獲取持倉詳情（使用實際價格）
            positions_detail = {}
            for symbol, pos in portfolio._positions.items():
                current_price = last_prices.get(symbol, pos.avg_cost)
                positions_detail[symbol] = {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": pos.total_cost,
                    "current_price": current_price,
                    "market_value": pos.quantity * current_price,
                    "unrealized_pnl": (current_price - pos.avg_cost) * pos.quantity,
                    "unrealized_pnl_pct": ((current_price - pos.avg_cost) / pos.avg_cost * 100) if pos.avg_cost > 0 else 0,
                }
            
            # Portfolio 快照（成交後）
            portfolio_snapshot = {
                "cash": portfolio.cash,
                "positions": {sym: info["quantity"] for sym, info in positions_detail.items()},
                "positions_detail": positions_detail,
                "total_value": portfolio_value,
                "equity_value": equity_value,
                "total_pnl": total_pnl,
                "total_pnl_pct": total_pnl_pct,
            }
            
            # 更新每日記憶（添加成交明細）
            try:
                daily_memory = memory_manager.load_daily_memory(check_date)
                if daily_memory:
                    # 合併成交明細（可能當天已經有掛單記錄）
                    existing_trades = daily_memory.get("executed_trades", [])
                    # 將新成交的訂單添加到列表
                    for trade in executed_trades:
                        # 檢查是否已存在（避免重複）
                        if not any(
                            t.get("symbol") == trade["symbol"] and 
                            t.get("action") == trade["action"] and 
                            t.get("order_date") == trade.get("order_date")
                            for t in existing_trades
                        ):
                            existing_trades.append(trade)
                    
                    daily_memory["executed_trades"] = existing_trades
                    daily_memory["executed_trades_count"] = len(existing_trades)
                    daily_memory["portfolio_snapshot"] = portfolio_snapshot  # 更新為成交後的快照
                    
                    # 重新保存每日記憶
                    memory_file = memory_manager.daily_dir / f"{check_date}.json"
                    with memory_file.open("w", encoding="utf-8") as f:
                        import json
                        json.dump(daily_memory, f, ensure_ascii=False, indent=2)
                    
                    print(f"[MEMORY] Updated daily memory with {len(executed_trades)} executed trades")
                else:
                    print(f"[WARN] Daily memory not found for {check_date}, cannot update")
            except Exception as e:
                print(f"[WARN] Failed to update daily memory: {e}")
                import traceback
                traceback.print_exc()
            
            # 記錄每日淨值（成交後）- 這會覆蓋掛單時的記錄
            equity_tracker.record_daily_equity(
                date_str=check_date,
                portfolio_snapshot=portfolio_snapshot,
            )
            
            print(f"[EQUITY] Recorded post-execution equity for {check_date}: ${portfolio_value:.2f} (P&L: ${total_pnl:.2f}, {total_pnl_pct:.2f}%)")
            
        except Exception as e:
            print(f"[WARN] Failed to record equity/memory: {e}")
            import traceback
            traceback.print_exc()
    
    return {
        "checked_date": check_date,
        "pending_count": len(pending_orders),
        "filled_count": filled_count,
        "rejected_count": rejected_count,
        "executed_trades": executed_trades,  # 完整的成交明細（買進賣出）
        "portfolio_snapshot": portfolio_snapshot,  # 成交後的 Portfolio 快照
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Check and execute pending orders after market close")
    parser.add_argument("--date", type=str, help="Date to check (YYYY-MM-DD, defaults to yesterday)")
    parser.add_argument("--state-file", type=str, default="data/logs/portfolio_state.json", help="Portfolio state file path")
    
    args = parser.parse_args()
    
    state_file = Path(args.state_file) if args.state_file else None
    result = check_and_execute_pending_orders(
        check_date=args.date,
        portfolio_state_file=state_file,
    )
    
    print("\n=== Order Check Summary ===")
    print(f"Date: {result['checked_date']}")
    print(f"Pending Orders: {result['pending_count']}")
    print(f"Filled: {result['filled_count']}")
    print(f"Rejected: {result['rejected_count']}")
    print(f"Executed Trades: {len(result['executed_trades'])}")
