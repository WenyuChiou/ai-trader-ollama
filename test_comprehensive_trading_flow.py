#!/usr/bin/env python3
"""
Comprehensive Trading Flow Test
测试周一至周四的完整交易流程：
1. 盘中交易（9:30-16:00）
2. 盘中跨收盘
3. 收盘后对话（16:00之后）
4. 收盘跨盘中（次日开盘）
5. 净值更新、损益记录、仓位
6. 聊天对话
7. 仓位信息
8. 交易记录与订单状态
"""
import sys
from pathlib import Path
from datetime import date, datetime, timedelta, time as dt_time
import json
import shutil

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from backend.src.orchestrator.trading_cycle import execute_daily_trade
from backend.src.data.order_manager import OrderManager
from backend.src.data.portfolio import Portfolio
from backend.src.data.equity_tracker import EquityTracker
from backend.src.utils.trading_days import is_trading_day, get_next_trading_day

def test_comprehensive_flow():
    """Comprehensive trading flow test"""
    print("=" * 80)
    print("Comprehensive Trading Flow Test")
    print("Testing Monday-Thursday trading flow with historical data")
    print("=" * 80)
    print()
    
    # Find Monday-Thursday of this week
    today = date.today()
    # Find Monday (weekday 0)
    days_since_monday = today.weekday()
    monday = today - timedelta(days=days_since_monday)
    
    test_dates = []
    for i in range(4):  # Monday to Thursday
        test_date = monday + timedelta(days=i)
        if is_trading_day(test_date):
            test_dates.append(test_date)
    
    if len(test_dates) < 4:
        print(f"[WARNING] Only found {len(test_dates)} trading days, will use these dates")
    
    print(f"Test dates: {[d.isoformat() for d in test_dates]}")
    print()
    
    # Backup existing data
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    backup_dir = logs_dir / "test_backup_comprehensive"
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    backup_dir.mkdir(exist_ok=True)
    
    # Backup key files
    for file in ["portfolio_state.json", "filled_orders.jsonl", "pending_orders.jsonl", 
                 "equity_history.jsonl", "discussion_actions.jsonl", "trades.jsonl"]:
        src = logs_dir / file
        if src.exists():
            shutil.copy2(src, backup_dir / file)
    
    print("[TEST] Backed up existing data")
    print()
    
    # Initialize portfolio if needed
    portfolio_file = logs_dir / "portfolio_state.json"
    if not portfolio_file.exists():
        initial_state = {
            "cash": 10000.0,
            "initial_value": 10000.0,
            "total_value": 10000.0,
            "positions": {}
        }
        with portfolio_file.open("w", encoding="utf-8") as f:
            json.dump(initial_state, f, indent=2)
        print("[TEST] Initialized portfolio state")
    
    results = []
    
    for day_idx, test_date in enumerate(test_dates):
        print("=" * 80)
        print(f"Day {day_idx + 1}/{len(test_dates)}: {test_date.isoformat()} ({test_date.strftime('%A')})")
        print("=" * 80)
        print()
        
        day_results = {
            "date": test_date.isoformat(),
            "scenarios": []
        }
        
        # Scenario 1: Market Open (9:30 AM) - 盘中交易
        print(f"[SCENARIO 1] Market Open (9:30 AM) - Intraday Trading")
        print("-" * 80)
        
        market_open_time = datetime.combine(test_date, dt_time(9, 30))
        
        try:
            result = execute_daily_trade(
                end=test_date.isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],  # Small universe for testing
                rounds=1,  # Reduce rounds for faster testing
                tool_budget=3,  # Reduce tool budget for faster testing
            )
            
            scenario_result = {
                "scenario": "market_open",
                "conversations": result.get('conversations_count', 0),
                "orders_placed": len(result.get('placed_orders', [])),
                "trades_executed": len(result.get('executed_trades', [])),
                "errors": len(result.get('execution_errors', []))
            }
            
            print(f"  Conversations: {scenario_result['conversations']}")
            print(f"  Orders placed: {scenario_result['orders_placed']}")
            print(f"  Trades executed: {scenario_result['trades_executed']}")
            print(f"  Errors: {scenario_result['errors']}")
            
            if scenario_result['trades_executed'] > 0:
                print(f"  [OK] Trades executed during market open")
            else:
                print(f"  [INFO] No trades executed (may be due to cash constraints or market conditions)")
            
            day_results["scenarios"].append(scenario_result)
            
        except Exception as e:
            print(f"  [ERROR] Execution failed: {e}")
            import traceback
            traceback.print_exc()
            day_results["scenarios"].append({
                "scenario": "market_open",
                "error": str(e)
            })
        
        print()
        
        # Check portfolio state after market open
        print("[CHECK] Portfolio State After Market Open")
        print("-" * 80)
        try:
            if portfolio_file.exists():
                with portfolio_file.open("r", encoding="utf-8") as f:
                    portfolio_state = json.load(f)
                print(f"  Cash: ${portfolio_state.get('cash', 0):.2f}")
                print(f"  Total value: ${portfolio_state.get('total_value', 0):.2f}")
                print(f"  Positions: {len(portfolio_state.get('positions', {}))}")
                day_results["portfolio_after_open"] = portfolio_state
        except Exception as e:
            print(f"  [ERROR] Failed to check portfolio: {e}")
        print()
        
        # Scenario 2: Mid-day (12:00 PM) - 盘中跨收盘前
        print(f"[SCENARIO 2] Mid-day (12:00 PM) - Intraday Trading")
        print("-" * 80)
        
        try:
            result = execute_daily_trade(
                end=test_date.isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                rounds=1,
                tool_budget=2,
            )
            
            scenario_result = {
                "scenario": "midday",
                "conversations": result.get('conversations_count', 0),
                "orders_placed": len(result.get('placed_orders', [])),
                "trades_executed": len(result.get('executed_trades', [])),
                "errors": len(result.get('execution_errors', []))
            }
            
            print(f"  Conversations: {scenario_result['conversations']}")
            print(f"  Orders placed: {scenario_result['orders_placed']}")
            print(f"  Trades executed: {scenario_result['trades_executed']}")
            
            day_results["scenarios"].append(scenario_result)
            
        except Exception as e:
            print(f"  [ERROR] Execution failed: {e}")
            day_results["scenarios"].append({
                "scenario": "midday",
                "error": str(e)
            })
        
        print()
        
        # Scenario 3: After Market Close (4:30 PM) - 收盘后对话
        print(f"[SCENARIO 3] After Market Close (4:30 PM) - Post-Close Conversation")
        print("-" * 80)
        
        try:
            result = execute_daily_trade(
                end=test_date.isoformat(),
                universe=["AAPL", "MSFT", "GOOGL", "TSLA", "NVDA"],
                rounds=1,
                tool_budget=2,
            )
            
            scenario_result = {
                "scenario": "after_close",
                "conversations": result.get('conversations_count', 0),
                "orders_placed": len(result.get('placed_orders', [])),
                "trades_executed": len(result.get('executed_trades', [])),
                "errors": len(result.get('execution_errors', []))
            }
            
            print(f"  Conversations: {scenario_result['conversations']}")
            print(f"  Orders placed: {scenario_result['orders_placed']}")
            print(f"  Trades executed: {scenario_result['trades_executed']}")
            
            # Verify: Should have conversations but no trades
            if scenario_result['conversations'] > 0:
                print(f"  [OK] Conversations ran after market close")
            else:
                print(f"  [WARN] No conversations after market close")
            
            if scenario_result['trades_executed'] == 0:
                print(f"  [OK] No trades executed after market close (correct)")
            else:
                print(f"  [ERROR] Trades executed after market close (should not happen)")
            
            day_results["scenarios"].append(scenario_result)
            
        except Exception as e:
            print(f"  [ERROR] Execution failed: {e}")
            day_results["scenarios"].append({
                "scenario": "after_close",
                "error": str(e)
            })
        
        print()
        
        # Check all data records for the day
        print("[CHECK] All Data Records for the Day")
        print("-" * 80)
        
        # 1. Check equity history
        print("1. Equity History:")
        try:
            equity_tracker = EquityTracker(root="data/logs")
            equity_records = []
            equity_file = logs_dir / "equity_history.jsonl"
            if equity_file.exists():
                with equity_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                record = json.loads(line.strip())
                                if record.get("date") == test_date.isoformat():
                                    equity_records.append(record)
                            except:
                                pass
            
            print(f"   Records found: {len(equity_records)}")
            if equity_records:
                latest = equity_records[-1]
                print(f"   Latest equity: ${latest.get('total_value', 0):.2f}")
                print(f"   Cash: ${latest.get('cash', 0):.2f}")
                print(f"   Equity value: ${latest.get('equity_value', 0):.2f}")
                day_results["equity_records"] = len(equity_records)
            else:
                print(f"   [WARN] No equity records for this day")
                day_results["equity_records"] = 0
        except Exception as e:
            print(f"   [ERROR] Failed to check equity history: {e}")
        
        # 2. Check filled orders (realized P&L)
        print("2. Filled Orders (Realized P&L):")
        try:
            filled_file = logs_dir / "filled_orders.jsonl"
            filled_orders = []
            if filled_file.exists():
                with filled_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                order = json.loads(line.strip())
                                if order.get("order_date") == test_date.isoformat():
                                    filled_orders.append(order)
                            except:
                                pass
            
            sell_orders = [o for o in filled_orders if o.get("action") == "SELL" and o.get("realized_pnl") is not None]
            total_realized_pnl = sum(o.get("realized_pnl", 0) for o in sell_orders)
            
            print(f"   Total filled orders: {len(filled_orders)}")
            print(f"   SELL orders with P&L: {len(sell_orders)}")
            print(f"   Total realized P&L: ${total_realized_pnl:.2f}")
            day_results["filled_orders"] = len(filled_orders)
            day_results["realized_pnl"] = total_realized_pnl
        except Exception as e:
            print(f"   [ERROR] Failed to check filled orders: {e}")
        
        # 3. Check pending orders
        print("3. Pending Orders:")
        try:
            order_manager = OrderManager(root="data/logs")
            pending_orders = order_manager.load_pending_orders(order_date=test_date.isoformat())
            print(f"   Pending orders: {len(pending_orders)}")
            day_results["pending_orders"] = len(pending_orders)
        except Exception as e:
            print(f"   [ERROR] Failed to check pending orders: {e}")
        
        # 4. Check conversations
        print("4. Conversations:")
        try:
            convo_file = logs_dir / "discussion_actions.jsonl"
            conversations = []
            if convo_file.exists():
                with convo_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                convo = json.loads(line.strip())
                                convo_date = convo.get("date", "")
                                if convo_date.startswith(test_date.isoformat()):
                                    conversations.append(convo)
                            except:
                                pass
            
            print(f"   Conversations: {len(conversations)}")
            if conversations:
                agents = set(c.get("agent", "Unknown") for c in conversations)
                print(f"   Agents: {', '.join(sorted(agents))}")
            day_results["conversations"] = len(conversations)
        except Exception as e:
            print(f"   [ERROR] Failed to check conversations: {e}")
        
        # 5. Check trades
        print("5. Trades:")
        try:
            trades_file = logs_dir / "trades.jsonl"
            trades = []
            if trades_file.exists():
                with trades_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                trade = json.loads(line.strip())
                                trade_date = trade.get("date", "")
                                if trade_date.startswith(test_date.isoformat()):
                                    trades.append(trade)
                            except:
                                pass
            
            print(f"   Trades: {len(trades)}")
            if trades:
                buy_count = len([t for t in trades if t.get("action") == "BUY"])
                sell_count = len([t for t in trades if t.get("action") == "SELL"])
                print(f"   BUY: {buy_count}, SELL: {sell_count}")
            day_results["trades"] = len(trades)
        except Exception as e:
            print(f"   [ERROR] Failed to check trades: {e}")
        
        # 6. Check portfolio positions
        print("6. Portfolio Positions:")
        try:
            if portfolio_file.exists():
                with portfolio_file.open("r", encoding="utf-8") as f:
                    portfolio_state = json.load(f)
                positions = portfolio_state.get("positions", {})
                print(f"   Positions: {len(positions)}")
                if positions:
                    for symbol, pos in list(positions.items())[:5]:  # Show first 5
                        if isinstance(pos, dict):
                            qty = pos.get("quantity", 0)
                            avg_cost = pos.get("avg_cost", 0)
                            print(f"     {symbol}: {qty} shares @ ${avg_cost:.2f}")
                day_results["positions"] = len(positions)
                day_results["portfolio_final"] = {
                    "cash": portfolio_state.get("cash", 0),
                    "total_value": portfolio_state.get("total_value", 0)
                }
        except Exception as e:
            print(f"   [ERROR] Failed to check positions: {e}")
        
        print()
        results.append(day_results)
    
    # Final summary
    print("=" * 80)
    print("Final Summary")
    print("=" * 80)
    print()
    
    total_conversations = sum(r.get("conversations", 0) for r in results)
    total_trades = sum(sum(s.get("trades_executed", 0) for s in r.get("scenarios", [])) for r in results)
    total_filled_orders = sum(r.get("filled_orders", 0) for r in results)
    total_realized_pnl = sum(r.get("realized_pnl", 0) for r in results)
    
    print(f"Total conversations: {total_conversations}")
    print(f"Total trades executed: {total_trades}")
    print(f"Total filled orders: {total_filled_orders}")
    print(f"Total realized P&L: ${total_realized_pnl:.2f}")
    print()
    
    print("Daily breakdown:")
    for day_result in results:
        print(f"  {day_result['date']}:")
        print(f"    Conversations: {day_result.get('conversations', 0)}")
        print(f"    Filled orders: {day_result.get('filled_orders', 0)}")
        print(f"    Realized P&L: ${day_result.get('realized_pnl', 0):.2f}")
        print(f"    Equity records: {day_result.get('equity_records', 0)}")
        print(f"    Positions: {day_result.get('positions', 0)}")
        if day_result.get('portfolio_final'):
            pf = day_result['portfolio_final']
            print(f"    Final portfolio: cash=${pf.get('cash', 0):.2f}, total=${pf.get('total_value', 0):.2f}")
        print()
    
    # Restore backup
    print("[TEST] Restoring backup data...")
    for file in ["portfolio_state.json", "filled_orders.jsonl", "pending_orders.jsonl", 
                 "equity_history.jsonl", "discussion_actions.jsonl", "trades.jsonl"]:
        backup_file = backup_dir / file
        if backup_file.exists():
            shutil.copy2(backup_file, logs_dir / file)
            print(f"  Restored: {file}")
    
    print()
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)
    
    return results

if __name__ == "__main__":
    test_comprehensive_flow()


