#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合每日检查脚本
检查今天的所有记录（谈话内容、净值记录、持仓信息、记忆等）
评估自动交易的持续性和稳定性
"""
import sys
import io
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from collections import defaultdict
from typing import Dict, Any, List, Optional

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add project root to path
ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.equity_tracker import EquityTracker
from src.data.memory_manager import MemoryManager
from src.data.order_manager import OrderManager

def check_today_equity_records(logs_dir: Path, today: str) -> Dict[str, Any]:
    """Check today's equity records"""
    print("\n" + "="*80)
    print("📊 Today's Equity Records Check")
    print("="*80)
    
    equity_tracker = EquityTracker(root=str(logs_dir))
    records = equity_tracker.load_equity_history(start_date=today, end_date=today)
    
    print(f"\nDate: {today}")
    print(f"Total records: {len(records)}")
    
    if not records:
        return {"ok": False, "error": "No equity records found for today"}
    
    # Analyze records
    values = [r.get("total_value", 0) for r in records]
    cash_values = [r.get("cash", 0) for r in records]
    equity_values = [r.get("equity_value", 0) for r in records]
    
    # Check consistency
    issues = []
    for i, record in enumerate(records):
        total_value = record.get("total_value", 0)
        cash = record.get("cash", 0)
        equity_value = record.get("equity_value", 0)
        
        # Check if total_value = cash + equity_value
        calculated_total = cash + equity_value
        if abs(total_value - calculated_total) > 0.01:
            issues.append(f"Record {i+1}: total_value ({total_value:.2f}) != cash ({cash:.2f}) + equity_value ({equity_value:.2f})")
        
        # Check if positions have current_price
        positions = record.get("positions", {})
        positions_without_price = []
        for symbol, pos in positions.items():
            if isinstance(pos, dict) and "current_price" not in pos:
                positions_without_price.append(symbol)
        
        if positions_without_price:
            issues.append(f"Record {i+1}: Positions without current_price: {', '.join(positions_without_price)}")
    
    # Statistics
    stats = {
        "min_value": min(values) if values else 0,
        "max_value": max(values) if values else 0,
        "range": max(values) - min(values) if values else 0,
        "final_value": values[-1] if values else 0,
        "initial_value": values[0] if values else 0,
        "change": (values[-1] - values[0]) if len(values) > 1 else 0,
        "change_pct": ((values[-1] - values[0]) / values[0] * 100) if len(values) > 1 and values[0] > 0 else 0,
        "avg_cash": sum(cash_values) / len(cash_values) if cash_values else 0,
        "avg_equity": sum(equity_values) / len(equity_values) if equity_values else 0,
    }
    
    print(f"\nStatistics:")
    print(f"  Initial value: ${stats['initial_value']:.2f}")
    print(f"  Final value: ${stats['final_value']:.2f}")
    print(f"  Change: ${stats['change']:.2f} ({stats['change_pct']:.2f}%)")
    print(f"  Range: ${stats['range']:.2f}")
    print(f"  Average cash: ${stats['avg_cash']:.2f}")
    print(f"  Average equity: ${stats['avg_equity']:.2f}")
    
    if issues:
        print(f"\n⚠️  Issues found: {len(issues)}")
        for issue in issues[:10]:
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
    
    return {
        "ok": len(issues) == 0,
        "records_count": len(records),
        "stats": stats,
        "issues": issues
    }

def check_today_conversations(logs_dir: Path, today: str) -> Dict[str, Any]:
    """Check today's conversation records"""
    print("\n" + "="*80)
    print("💬 Today's Conversation Records Check")
    print("="*80)
    
    convo_file = logs_dir / "discussion_actions.jsonl"
    if not convo_file.exists():
        return {"ok": False, "error": "discussion_actions.jsonl not found"}
    
    records = []
    with convo_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line.strip())
                    if record.get("date") == today:
                        records.append(record)
                except:
                    pass
    
    print(f"\nDate: {today}")
    print(f"Total conversation entries: {len(records)}")
    
    if not records:
        return {"ok": False, "error": "No conversation records found for today"}
    
    # Analyze by agent and type
    by_agent = defaultdict(int)
    by_type = defaultdict(int)
    errors = []
    
    for record in records:
        agent = record.get("agent", "Unknown")
        entry_type = record.get("type", "unknown")
        by_agent[agent] += 1
        by_type[entry_type] += 1
        
        # Check for errors
        if "error" in record.get("content", "").lower() or "error" in str(record.get("tool_result", "")).lower():
            errors.append(f"{agent} - {entry_type}")
    
    print(f"\nBy Agent:")
    for agent, count in sorted(by_agent.items(), key=lambda x: -x[1]):
        print(f"  {agent}: {count}")
    
    print(f"\nBy Type:")
    for entry_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        print(f"  {entry_type}: {count}")
    
    if errors:
        print(f"\n⚠️  Potential errors found: {len(errors)}")
        for error in errors[:5]:
            print(f"  - {error}")
    
    return {
        "ok": True,
        "entries_count": len(records),
        "by_agent": dict(by_agent),
        "by_type": dict(by_type),
        "errors": errors
    }

def check_today_memory(logs_dir: Path, today: str) -> Dict[str, Any]:
    """Check today's memory"""
    print("\n" + "="*80)
    print("🧠 Today's Memory Check")
    print("="*80)
    
    memory_manager = MemoryManager(root=str(logs_dir))
    memory_file = memory_manager.daily_dir / f"{today}.json"
    
    if not memory_file.exists():
        return {"ok": False, "error": f"Memory file not found: {memory_file.name}"}
    
    with memory_file.open("r", encoding="utf-8") as f:
        memory = json.load(f)
    
    print(f"\nDate: {today}")
    print(f"Memory file exists: ✅")
    
    # Check required fields
    required_fields = ["date", "market_view", "market_analysis", "discussion", "risk_report", "decision", "portfolio_snapshot"]
    missing_fields = [f for f in required_fields if f not in memory]
    
    if missing_fields:
        print(f"\n⚠️  Missing fields: {', '.join(missing_fields)}")
    
    # Check portfolio snapshot
    portfolio_snapshot = memory.get("portfolio_snapshot", {})
    print(f"\nPortfolio Snapshot:")
    print(f"  Cash: ${portfolio_snapshot.get('cash', 0):.2f}")
    print(f"  Equity Value: ${portfolio_snapshot.get('equity_value', 0):.2f}")
    print(f"  Total Value: ${portfolio_snapshot.get('total_value', 0):.2f}")
    print(f"  Positions: {len(portfolio_snapshot.get('positions', {}))}")
    
    # Check executed trades
    executed_trades = memory.get("executed_trades", [])
    print(f"\nExecuted Trades: {len(executed_trades)}")
    if executed_trades:
        buy_count = sum(1 for t in executed_trades if t.get("action", "").upper() == "BUY")
        sell_count = sum(1 for t in executed_trades if t.get("action", "").upper() == "SELL")
        print(f"  Buy: {buy_count}, Sell: {sell_count}")
    
    return {
        "ok": len(missing_fields) == 0,
        "has_memory": True,
        "missing_fields": missing_fields,
        "portfolio_snapshot": portfolio_snapshot,
        "executed_trades_count": len(executed_trades)
    }

def check_portfolio_state(logs_dir: Path) -> Dict[str, Any]:
    """Check current portfolio state"""
    print("\n" + "="*80)
    print("💼 Current Portfolio State Check")
    print("="*80)
    
    portfolio_file = logs_dir / "portfolio_state.json"
    if not portfolio_file.exists():
        return {"ok": False, "error": "portfolio_state.json not found"}
    
    with portfolio_file.open("r", encoding="utf-8") as f:
        portfolio = json.load(f)
    
    cash = portfolio.get("cash", 0)
    total_value = portfolio.get("total_value", 0)
    positions = portfolio.get("positions", {})
    
    print(f"\nCurrent State:")
    print(f"  Cash: ${cash:.2f}")
    print(f"  Total Value: ${total_value:.2f}")
    print(f"  Positions: {len(positions)}")
    
    # Check positions
    issues = []
    total_equity_value = 0
    for symbol, pos in positions.items():
        if isinstance(pos, dict):
            quantity = pos.get("quantity", 0)
            avg_cost = pos.get("avg_cost", 0)
            current_price = pos.get("current_price")
            market_value = pos.get("market_value", 0)
            
            if current_price is None:
                issues.append(f"{symbol}: Missing current_price")
            
            if market_value > 0:
                total_equity_value += market_value
            
            print(f"\n  {symbol}:")
            print(f"    Quantity: {quantity}")
            print(f"    Avg Cost: ${avg_cost:.2f}")
            print(f"    Current Price: ${current_price:.2f}" if current_price else f"    Current Price: N/A")
            print(f"    Market Value: ${market_value:.2f}")
    
    calculated_total = cash + total_equity_value
    if abs(total_value - calculated_total) > 0.01:
        issues.append(f"Total value mismatch: recorded={total_value:.2f}, calculated={calculated_total:.2f}")
    
    if issues:
        print(f"\n⚠️  Issues found: {len(issues)}")
        for issue in issues:
            print(f"  - {issue}")
    
    return {
        "ok": len(issues) == 0,
        "cash": cash,
        "total_value": total_value,
        "positions_count": len(positions),
        "issues": issues
    }

def check_today_trades(logs_dir: Path, today: str) -> Dict[str, Any]:
    """Check today's trades"""
    print("\n" + "="*80)
    print("📈 Today's Trades Check")
    print("="*80)
    
    filled_file = logs_dir / "filled_orders.jsonl"
    if not filled_file.exists():
        return {"ok": True, "trades_count": 0, "message": "No filled_orders.jsonl file"}
    
    filled_orders = []
    try:
        with filled_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        order = json.loads(line.strip())
                        filled_orders.append(order)
                    except:
                        pass
    except Exception as e:
        return {"ok": False, "error": f"Failed to read filled_orders.jsonl: {e}"}
    
    today_trades = [o for o in filled_orders if o.get("order_date") == today or 
                    (o.get("fill_result", {}).get("fill_date") == today)]
    
    print(f"\nDate: {today}")
    print(f"Total filled orders today: {len(today_trades)}")
    
    if not today_trades:
        return {"ok": True, "trades_count": 0, "message": "No trades today"}
    
    # Analyze trades
    by_action = defaultdict(int)
    by_symbol = defaultdict(int)
    total_volume = 0
    total_pnl = 0
    
    for trade in today_trades:
        action = trade.get("action", "Unknown")
        symbol = trade.get("symbol", "Unknown")
        quantity = trade.get("quantity", 0)
        fill_price = trade.get("fill_result", {}).get("fill_price") or trade.get("fill_price", 0)
        realized_pnl = trade.get("realized_pnl") or trade.get("fill_result", {}).get("realized_pnl", 0)
        
        by_action[action] += 1
        by_symbol[symbol] += 1
        total_volume += quantity * fill_price
        total_pnl += realized_pnl
    
    print(f"\nBy Action:")
    for action, count in sorted(by_action.items(), key=lambda x: -x[1]):
        print(f"  {action}: {count}")
    
    print(f"\nBy Symbol:")
    for symbol, count in sorted(by_symbol.items(), key=lambda x: -x[1]):
        print(f"  {symbol}: {count}")
    
    print(f"\nTotal Volume: ${total_volume:.2f}")
    print(f"Total Realized P&L: ${total_pnl:.2f}")
    
    return {
        "ok": True,
        "trades_count": len(today_trades),
        "by_action": dict(by_action),
        "by_symbol": dict(by_symbol),
        "total_volume": total_volume,
        "total_pnl": total_pnl
    }

def generate_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on check results"""
    recommendations = []
    
    # Equity records
    equity_result = results.get("equity", {})
    if equity_result.get("records_count", 0) < 10:
        recommendations.append("⚠️  Equity records: Less than 10 records today. Consider checking recording frequency.")
    
    if equity_result.get("issues"):
        recommendations.append("⚠️  Equity records: Found data consistency issues. Review and fix.")
    
    # Conversations
    convo_result = results.get("conversations", {})
    if convo_result.get("entries_count", 0) == 0:
        recommendations.append("⚠️  Conversations: No conversation records today. Check if trading cycle is running.")
    
    if convo_result.get("errors"):
        recommendations.append("⚠️  Conversations: Found potential errors in conversation logs. Review.")
    
    # Memory
    memory_result = results.get("memory", {})
    if not memory_result.get("has_memory"):
        recommendations.append("❌ Memory: No memory file for today. Critical issue - trading cycle may not be saving memory.")
    
    if memory_result.get("missing_fields"):
        recommendations.append(f"⚠️  Memory: Missing fields: {', '.join(memory_result['missing_fields'])}")
    
    # Portfolio state
    portfolio_result = results.get("portfolio", {})
    if portfolio_result.get("issues"):
        recommendations.append("⚠️  Portfolio: Found issues in portfolio state. Review and fix.")
    
    # Trades
    trades_result = results.get("trades", {})
    if trades_result.get("trades_count", 0) == 0:
        recommendations.append("ℹ️  Trades: No trades executed today. This is normal if market conditions don't warrant trading.")
    
    # General recommendations
    recommendations.append("✅ Regular monitoring: Set up automated daily checks to ensure system health.")
    recommendations.append("✅ Backup: Ensure daily backups of portfolio_state.json and equity_history.jsonl.")
    recommendations.append("✅ Error handling: Review error logs regularly to catch issues early.")
    
    return recommendations

def main():
    """Main function"""
    print("="*80)
    print("🔍 Comprehensive Daily Check - Auto Trading System")
    print("="*80)
    
    today = date.today().isoformat()
    print(f"\nChecking records for: {today}")
    
    # Try multiple possible locations
    possible_paths = [
        ROOT / "backend" / "data" / "logs",
        ROOT / "data" / "logs",
        Path("backend/data/logs"),
        Path("data/logs"),
    ]
    
    logs_dir = None
    for path in possible_paths:
        if path.exists() and (path / "equity_history.jsonl").exists():
            logs_dir = path
            break
    
    if not logs_dir:
        print(f"❌ Error: Could not find logs directory. Tried:")
        for path in possible_paths:
            print(f"   - {path.absolute()}")
        sys.exit(1)
    
    print(f"Using logs directory: {logs_dir.absolute()}")
    if not logs_dir.exists():
        print(f"❌ Error: Logs directory not found: {logs_dir}")
        sys.exit(1)
    
    results = {}
    
    # Run all checks
    results["equity"] = check_today_equity_records(logs_dir, today)
    results["conversations"] = check_today_conversations(logs_dir, today)
    results["memory"] = check_today_memory(logs_dir, today)
    results["portfolio"] = check_portfolio_state(logs_dir)
    results["trades"] = check_today_trades(logs_dir, today)
    
    # Generate recommendations
    print("\n" + "="*80)
    print("💡 Recommendations for Long-term Auto Trading")
    print("="*80)
    
    recommendations = generate_recommendations(results)
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec}")
    
    # Summary
    print("\n" + "="*80)
    print("📋 Summary")
    print("="*80)
    
    all_ok = True
    for category, result in results.items():
        status = "✅" if result.get("ok", False) else "❌"
        print(f"{status} {category.upper()}: {'OK' if result.get('ok') else 'ISSUES FOUND'}")
        if not result.get("ok"):
            all_ok = False
    
    if all_ok:
        print("\n✅ All checks passed! System appears healthy for long-term auto trading.")
    else:
        print("\n⚠️  Some issues found. Please review recommendations above.")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main())

