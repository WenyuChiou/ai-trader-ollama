"""
Performance Analysis API Module
Provides endpoints for historical trading performance analysis
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import date, datetime, timedelta
from collections import defaultdict


def _get_project_logs_dir() -> Path:
    """Get the project logs directory"""
    import sys
    from pathlib import Path
    
    # Try to find project root
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "backend" / "src").exists():
            project_root = parent.parent if (parent / "backend").exists() else parent
            logs_dir = project_root / "data" / "logs"
            if logs_dir.exists():
                return logs_dir
    
    # Fallback: use relative path
    return Path("data/logs")


def _load_equity_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """Load equity history from equity_history.jsonl"""
    logs_dir = _get_project_logs_dir()
    equity_file = logs_dir / "equity_history.jsonl"
    
    if not equity_file.exists():
        return []
    
    records = []
    with equity_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line.strip())
                    record_date = record.get("date") or (record.get("timestamp", "").split("T")[0] if record.get("timestamp") else "")
                    
                    # Skip if no date found
                    if not record_date:
                        continue
                    
                    # Filter by date range (inclusive on both ends)
                    if start_date and record_date < start_date:
                        continue
                    if end_date and record_date > end_date:
                        continue
                    
                    records.append(record)
                except (json.JSONDecodeError, AttributeError, TypeError) as e:
                    # Skip malformed records
                    print(f"[Performance] Skipping malformed equity record: {e}")
                    continue
    
    # Sort by timestamp/date
    records.sort(key=lambda x: x.get("timestamp") or x.get("date", ""))
    
    # Apply limit
    if limit:
        records = records[-limit:]
    
    return records


def _load_filled_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    symbol: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Load filled orders from filled_orders.jsonl"""
    logs_dir = _get_project_logs_dir()
    filled_file = logs_dir / "filled_orders.jsonl"
    
    if not filled_file.exists():
        return []
    
    orders = []
    with filled_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    order = json.loads(line.strip())
                    
                    # Filter by symbol
                    if symbol and order.get("symbol") != symbol:
                        continue
                    
                    # Filter by date
                    order_date = order.get("placed_at", "").split("T")[0] if order.get("placed_at") else order.get("date", "")
                    
                    # Skip if no date found
                    if not order_date:
                        continue
                    
                    # Filter by date range (inclusive on both ends)
                    if start_date and order_date < start_date:
                        continue
                    if end_date and order_date > end_date:
                        continue
                    
                    orders.append(order)
                except (json.JSONDecodeError, AttributeError, TypeError) as e:
                    # Skip malformed orders
                    print(f"[Performance] Skipping malformed order: {e}")
                    continue
    
    # Sort by date
    orders.sort(key=lambda x: x.get("placed_at") or x.get("date", ""))
    
    return orders


def _calculate_statistics(
    equity_history: List[Dict[str, Any]],
    filled_orders: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Calculate performance statistics"""
    if not equity_history:
        return {
            "error": "No equity history data available"
        }
    
    # Get initial and current values
    initial_record = equity_history[0]
    latest_record = equity_history[-1]
    
    initial_value = float(initial_record.get("total_value", 0.0))
    current_value = float(latest_record.get("total_value", 0.0))
    
    # Calculate total return
    total_return = current_value - initial_value
    total_return_pct = (total_return / initial_value * 100.0) if initial_value > 0 else 0.0
    
    # Calculate annualized return (if we have enough data)
    annualized_return_pct = 0.0
    if len(equity_history) > 1:
        try:
            first_timestamp = equity_history[0].get("timestamp")
            first_date_str = equity_history[0].get("date", "")
            if first_timestamp:
                first_date = datetime.fromisoformat(first_timestamp.replace("Z", "+00:00"))
            elif first_date_str:
                first_date = datetime.fromisoformat(first_date_str + "T00:00:00+00:00")
            else:
                first_date = None
            
            last_timestamp = equity_history[-1].get("timestamp")
            last_date_str = equity_history[-1].get("date", "")
            if last_timestamp:
                last_date = datetime.fromisoformat(last_timestamp.replace("Z", "+00:00"))
            elif last_date_str:
                last_date = datetime.fromisoformat(last_date_str + "T00:00:00+00:00")
            else:
                last_date = None
            
            if first_date and last_date:
                days_diff = (last_date - first_date).days
                if days_diff > 0:
                    annualized_return_pct = ((current_value / initial_value) ** (365.0 / days_diff) - 1) * 100.0
        except (ValueError, TypeError, AttributeError) as e:
            # If date parsing fails, skip annualized return calculation
            print(f"[Performance] Failed to calculate annualized return: {e}")
            annualized_return_pct = 0.0
    
    # Calculate maximum drawdown
    max_drawdown = 0.0
    max_drawdown_pct = 0.0
    peak_value = initial_value
    
    for record in equity_history:
        value = float(record.get("total_value", 0.0))
        if value > peak_value:
            peak_value = value
        
        drawdown = peak_value - value
        drawdown_pct = (drawdown / peak_value * 100.0) if peak_value > 0 else 0.0
        
        if drawdown > max_drawdown:
            max_drawdown = drawdown
            max_drawdown_pct = drawdown_pct
    
    # Calculate win rate from filled orders
    sell_orders = [o for o in filled_orders if o.get("action") == "SELL" and o.get("realized_pnl") is not None]
    total_trades = len(sell_orders)
    winning_trades = len([o for o in sell_orders if float(o.get("realized_pnl", 0.0)) > 0])
    win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0
    
    # Calculate total realized P&L
    total_realized_pnl = sum(float(o.get("realized_pnl", 0.0)) for o in sell_orders)
    
    # Calculate average trade return
    avg_trade_return = (total_realized_pnl / total_trades) if total_trades > 0 else 0.0
    
    # Calculate Sharpe ratio (simplified, using daily returns)
    if len(equity_history) > 1:
        returns = []
        for i in range(1, len(equity_history)):
            prev_value = float(equity_history[i-1].get("total_value", 0.0))
            curr_value = float(equity_history[i].get("total_value", 0.0))
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                returns.append(daily_return)
        
        if returns:
            try:
                import statistics
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 0.0
                sharpe_ratio = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0.0  # Annualized
            except (ImportError, ValueError):
                # Fallback if statistics module not available or calculation fails
                if len(returns) > 1:
                    avg_return = sum(returns) / len(returns)
                    variance = sum((x - avg_return) ** 2 for x in returns) / (len(returns) - 1)
                    std_return = variance ** 0.5
                    sharpe_ratio = (avg_return / std_return * (252 ** 0.5)) if std_return > 0 else 0.0
                else:
                    sharpe_ratio = 0.0
        else:
            sharpe_ratio = 0.0
    else:
        sharpe_ratio = 0.0
    
    # Count trading days
    trading_days = len(set(r.get("date") or (r.get("timestamp", "").split("T")[0] if r.get("timestamp") else "") for r in equity_history))
    
    return {
        "initial_value": initial_value,
        "current_value": current_value,
        "total_return": total_return,
        "total_return_pct": round(total_return_pct, 2),
        "annualized_return_pct": round(annualized_return_pct, 2) if annualized_return_pct else None,
        "max_drawdown": round(max_drawdown, 2),
        "max_drawdown_pct": round(max_drawdown_pct, 2),
        "win_rate": round(win_rate, 2),
        "total_trades": total_trades,
        "winning_trades": winning_trades,
        "losing_trades": total_trades - winning_trades,
        "total_realized_pnl": round(total_realized_pnl, 2),
        "avg_trade_return": round(avg_trade_return, 2),
        "sharpe_ratio": round(sharpe_ratio, 3) if sharpe_ratio else None,
        "trading_days": trading_days,
        "data_points": len(equity_history)
    }


def get_performance_statistics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Get overall performance statistics"""
    try:
        # If no end_date specified, default to today to include today's data
        if end_date is None:
            end_date = date.today().isoformat()
        
        equity_history = _load_equity_history(start_date=start_date, end_date=end_date)
        filled_orders = _load_filled_orders(start_date=start_date, end_date=end_date)
        
        stats = _calculate_statistics(equity_history, filled_orders)
        
        # If stats contains an error, return it
        if "error" in stats:
            return {
                "ok": False,
                "error": stats["error"],
                "statistics": {},
                "period": {
                    "start_date": start_date,
                    "end_date": end_date
                }
            }
        
        return {
            "ok": True,
            "statistics": stats,
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }
    except Exception as e:
        import traceback
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "statistics": {},
            "period": {
                "start_date": start_date,
                "end_date": end_date
            }
        }


def get_trades_by_date(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: Optional[int] = None
) -> Dict[str, Any]:
    """Get trades grouped by date"""
    try:
        # If no end_date specified, default to today to include today's data
        if end_date is None:
            end_date = date.today().isoformat()
        
        filled_orders = _load_filled_orders(start_date=start_date, end_date=end_date)
        
        # Group by date
        trades_by_date = defaultdict(list)
        for order in filled_orders:
            order_date = order.get("placed_at", "").split("T")[0] if order.get("placed_at") else order.get("date", "")
            if order_date:
                trades_by_date[order_date].append(order)
        
        # Convert to list of date summaries
        date_summaries = []
        for date_str, orders in sorted(trades_by_date.items()):
            buy_orders = [o for o in orders if o.get("action") == "BUY"]
            sell_orders = [o for o in orders if o.get("action") == "SELL"]
            
            total_buy_value = sum(float(o.get("fill_price", 0.0)) * float(o.get("quantity", 0.0)) for o in buy_orders)
            total_sell_value = sum(float(o.get("fill_price", 0.0)) * float(o.get("quantity", 0.0)) for o in sell_orders)
            total_realized_pnl = sum(float(o.get("realized_pnl", 0.0)) for o in sell_orders if o.get("realized_pnl") is not None)
            
            date_summaries.append({
                "date": date_str,
                "total_orders": len(orders),
                "buy_orders": len(buy_orders),
                "sell_orders": len(sell_orders),
                "total_buy_value": round(total_buy_value, 2),
                "total_sell_value": round(total_sell_value, 2),
                "total_realized_pnl": round(total_realized_pnl, 2),
                "orders": orders[:limit] if limit else orders
            })
        
        # Apply limit to date summaries
        if limit:
            date_summaries = date_summaries[-limit:]
        
        return {
            "ok": True,
            "trades_by_date": date_summaries,
            "total_dates": len(date_summaries),
            "total_orders": len(filled_orders)
        }
    except Exception as e:
        import traceback
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "trades_by_date": [],
            "total_dates": 0,
            "total_orders": 0
        }


def get_symbol_analysis(
    symbol: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict[str, Any]:
    """Get performance analysis by symbol"""
    try:
        # If no end_date specified, default to today to include today's data
        if end_date is None:
            end_date = date.today().isoformat()
        
        if not symbol:
            # Get all symbols
            filled_orders = _load_filled_orders(start_date=start_date, end_date=end_date)
            symbols = set(o.get("symbol") for o in filled_orders if o.get("symbol"))
            
            symbol_stats = []
            for sym in sorted(symbols):
                sym_orders = _load_filled_orders(start_date=start_date, end_date=end_date, symbol=sym)
                stats = _calculate_symbol_stats(sym, sym_orders)
                symbol_stats.append(stats)
            
            return {
                "ok": True,
                "symbols": symbol_stats,
                "total_symbols": len(symbol_stats)
            }
        else:
            # Get specific symbol
            symbol_orders = _load_filled_orders(start_date=start_date, end_date=end_date, symbol=symbol)
            stats = _calculate_symbol_stats(symbol, symbol_orders)
            
            return {
                "ok": True,
                "symbol": stats
            }
    except Exception as e:
        import traceback
        return {
            "ok": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "symbols": [],
            "total_symbols": 0
        }


def _calculate_symbol_stats(symbol: str, orders: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate statistics for a specific symbol"""
    buy_orders = [o for o in orders if o.get("action") == "BUY"]
    sell_orders = [o for o in orders if o.get("action") == "SELL"]
    
    total_buy_quantity = sum(float(o.get("quantity", 0.0)) for o in buy_orders)
    total_sell_quantity = sum(float(o.get("quantity", 0.0)) for o in sell_orders)
    
    total_buy_cost = sum(float(o.get("fill_price", 0.0)) * float(o.get("quantity", 0.0)) for o in buy_orders)
    total_sell_proceeds = sum(float(o.get("fill_price", 0.0)) * float(o.get("quantity", 0.0)) for o in sell_orders)
    
    total_realized_pnl = sum(float(o.get("realized_pnl", 0.0)) for o in sell_orders if o.get("realized_pnl") is not None)
    
    # Calculate win rate for this symbol
    symbol_sell_orders = [o for o in sell_orders if o.get("realized_pnl") is not None]
    symbol_winning_trades = len([o for o in symbol_sell_orders if float(o.get("realized_pnl", 0.0)) > 0])
    symbol_win_rate = (symbol_winning_trades / len(symbol_sell_orders) * 100.0) if symbol_sell_orders else 0.0
    
    # Calculate average holding period (simplified - days between first buy and last sell)
    avg_holding_days = None
    if buy_orders and sell_orders:
        first_buy_date = min(o.get("placed_at", "").split("T")[0] if o.get("placed_at") else o.get("date", "") for o in buy_orders)
        last_sell_date = max(o.get("placed_at", "").split("T")[0] if o.get("placed_at") else o.get("date", "") for o in sell_orders)
        if first_buy_date and last_sell_date:
            try:
                # Handle date strings that might not have time component
                if "T" in first_buy_date:
                    first_date = datetime.fromisoformat(first_buy_date.replace("Z", "+00:00"))
                else:
                    first_date = datetime.fromisoformat(first_buy_date + "T00:00:00+00:00")
                
                if "T" in last_sell_date:
                    last_date = datetime.fromisoformat(last_sell_date.replace("Z", "+00:00"))
                else:
                    last_date = datetime.fromisoformat(last_sell_date + "T00:00:00+00:00")
                
                avg_holding_days = (last_date - first_date).days
            except (ValueError, TypeError, AttributeError) as e:
                # If date parsing fails, skip avg_holding_days calculation
                print(f"[Performance] Failed to calculate avg_holding_days for {symbol}: {e}")
                pass
    
    return {
        "symbol": symbol,
        "total_trades": len(orders),
        "buy_orders": len(buy_orders),
        "sell_orders": len(sell_orders),
        "total_buy_quantity": round(total_buy_quantity, 2),
        "total_sell_quantity": round(total_sell_quantity, 2),
        "total_buy_cost": round(total_buy_cost, 2),
        "total_sell_proceeds": round(total_sell_proceeds, 2),
        "total_realized_pnl": round(total_realized_pnl, 2),
        "realized_pnl_pct": round((total_realized_pnl / total_buy_cost * 100.0) if total_buy_cost > 0 else 0.0, 2),
        "win_rate": round(symbol_win_rate, 2),
        "avg_holding_days": avg_holding_days,
        "orders": orders
    }

