#!/usr/bin/env python3
"""
检查记录一致性：净值记录、已实现损益、仓位损益、时间戳记等
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from collections import defaultdict

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def get_logs_dir():
    """Get logs directory"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "backend" / "src").exists():
            project_root = parent.parent if (parent / "backend").exists() else parent
            logs_dir = project_root / "data" / "logs"
            break
    else:
        logs_dir = Path("data/logs")
    return logs_dir

def check_timestamp_format(timestamp: str, record_type: str, record_id: str) -> tuple[bool, Optional[str]]:
    """检查时间戳格式是否正确"""
    if not timestamp:
        return False, "Missing timestamp"
    
    # 检查是否以Z结尾（UTC时区）
    if not timestamp.endswith('Z'):
        # 检查是否有其他时区格式
        if '+' in timestamp or timestamp.count('-') > 2:
            return False, f"Timestamp should end with 'Z' (UTC), got: {timestamp}"
        else:
            return False, f"Timestamp missing timezone indicator, got: {timestamp}"
    
    # 尝试解析ISO 8601格式
    try:
        # 支持多种格式：YYYY-MM-DDTHH:MM:SS.fffZ 或 YYYY-MM-DDTHH:MM:SSZ
        if '.' in timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return True, None
    except ValueError as e:
        return False, f"Invalid ISO 8601 format: {e}"

def check_equity_history_consistency(logs_dir: Path) -> Dict[str, Any]:
    """检查净值记录一致性"""
    print("\n" + "="*80)
    print("📊 Equity History Consistency Check")
    print("="*80)
    
    equity_file = logs_dir / "equity_history.jsonl"
    if not equity_file.exists():
        return {"ok": False, "error": "equity_history.jsonl not found"}
    
    records = []
    issues = []
    
    with equity_file.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line.strip())
                records.append((line_num, record))
            except json.JSONDecodeError as e:
                issues.append(f"Line {line_num}: JSON parse error: {e}")
                continue
    
    print(f"Total records: {len(records)}")
    
    # 检查必需字段
    required_fields = ["date", "timestamp", "cash", "equity_value", "total_value", "total_pnl", "total_pnl_pct"]
    for line_num, record in records:
        # 检查必需字段
        for field in required_fields:
            if field not in record:
                issues.append(f"Line {line_num}: Missing required field '{field}'")
        
        # 检查时间戳格式
        if "timestamp" in record:
            is_valid, error = check_timestamp_format(record["timestamp"], "equity", f"line_{line_num}")
            if not is_valid:
                issues.append(f"Line {line_num}: {error}")
        
        # 检查日期格式
        if "date" in record:
            try:
                datetime.strptime(record["date"], "%Y-%m-%d")
            except ValueError:
                issues.append(f"Line {line_num}: Invalid date format '{record['date']}', expected YYYY-MM-DD")
        
        # 检查数值一致性
        cash = float(record.get("cash", 0))
        equity_value = float(record.get("equity_value", 0))
        total_value = float(record.get("total_value", 0))
        calculated_total = cash + equity_value
        
        # 允许小的浮点误差（0.01）
        if abs(total_value - calculated_total) > 0.01:
            issues.append(f"Line {line_num}: total_value ({total_value:.2f}) != cash ({cash:.2f}) + equity_value ({equity_value:.2f}) = {calculated_total:.2f}")
        
        # 检查仓位数据一致性
        if "positions" in record and isinstance(record["positions"], dict):
            for symbol, pos_data in record["positions"].items():
                if not isinstance(pos_data, dict):
                    continue
                
                quantity = float(pos_data.get("quantity", 0))
                avg_cost = float(pos_data.get("avg_cost", 0))
                current_price = float(pos_data.get("current_price", 0))
                market_value = float(pos_data.get("market_value", 0))
                unrealized_pnl = float(pos_data.get("unrealized_pnl", 0))
                unrealized_pnl_pct = float(pos_data.get("unrealized_pnl_pct", 0))
                
                # 检查market_value计算
                calculated_market_value = quantity * current_price
                if abs(market_value - calculated_market_value) > 0.01:
                    issues.append(f"Line {line_num}, {symbol}: market_value ({market_value:.2f}) != quantity ({quantity}) * current_price ({current_price:.2f}) = {calculated_market_value:.2f}")
                
                # 检查unrealized_pnl计算
                calculated_unrealized_pnl = (current_price - avg_cost) * quantity
                if abs(unrealized_pnl - calculated_unrealized_pnl) > 0.01:
                    issues.append(f"Line {line_num}, {symbol}: unrealized_pnl ({unrealized_pnl:.2f}) != (current_price - avg_cost) * quantity = {calculated_unrealized_pnl:.2f}")
                
                # 检查unrealized_pnl_pct计算
                cost_basis = avg_cost * quantity
                if cost_basis > 0:
                    calculated_pct = (unrealized_pnl / cost_basis) * 100.0
                    if abs(unrealized_pnl_pct - calculated_pct) > 0.01:
                        issues.append(f"Line {line_num}, {symbol}: unrealized_pnl_pct ({unrealized_pnl_pct:.2f}%) != (unrealized_pnl / cost_basis) * 100 = {calculated_pct:.2f}%")
    
    # 检查时间戳顺序
    timestamps = []
    for line_num, record in records:
        if "timestamp" in record:
            try:
                ts = datetime.fromisoformat(record["timestamp"].replace('Z', '+00:00'))
                timestamps.append((line_num, ts))
            except:
                pass
    
    if len(timestamps) > 1:
        for i in range(1, len(timestamps)):
            if timestamps[i][1] < timestamps[i-1][1]:
                issues.append(f"Line {timestamps[i][0]}: Timestamp out of order (earlier than line {timestamps[i-1][0]})")
    
    # 显示最后几条记录
    print("\nLast 5 records:")
    print("-" * 80)
    for line_num, record in records[-5:]:
        date = record.get("date", "N/A")
        timestamp = record.get("timestamp", "N/A")[:19] if record.get("timestamp") else "N/A"
        total_value = record.get("total_value", 0)
        cash = record.get("cash", 0)
        equity_value = record.get("equity_value", 0)
        total_pnl = record.get("total_pnl", 0)
        positions_count = len(record.get("positions", {}))
        print(f"  Line {line_num}: {date} {timestamp} | Total=${total_value:.2f} (Cash=${cash:.2f} + Equity=${equity_value:.2f}) | P&L=${total_pnl:.2f} | Positions={positions_count}")
    
    return {
        "ok": len(issues) == 0,
        "records_count": len(records),
        "issues": issues,
        "issues_count": len(issues)
    }

def check_filled_orders_consistency(logs_dir: Path) -> Dict[str, Any]:
    """检查已成交订单一致性（已实现损益）"""
    print("\n" + "="*80)
    print("💰 Filled Orders Consistency Check (Realized P&L)")
    print("="*80)
    
    filled_file = logs_dir / "filled_orders.jsonl"
    if not filled_file.exists():
        return {"ok": False, "error": "filled_orders.jsonl not found"}
    
    records = []
    issues = []
    
    with filled_file.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line.strip())
                records.append((line_num, record))
            except json.JSONDecodeError as e:
                issues.append(f"Line {line_num}: JSON parse error: {e}")
                continue
    
    print(f"Total orders: {len(records)}")
    
    # 统计订单类型
    buy_orders = [r for _, r in records if r.get("action") == "BUY"]
    sell_orders = [r for _, r in records if r.get("action") == "SELL"]
    print(f"  BUY orders: {len(buy_orders)}")
    print(f"  SELL orders: {len(sell_orders)}")
    
    # 检查必需字段
    required_fields = ["order_id", "placed_at", "symbol", "action", "quantity", "fill_price", "status"]
    for line_num, record in records:
        # 检查必需字段
        for field in required_fields:
            if field not in record:
                issues.append(f"Line {line_num}: Missing required field '{field}'")
        
        # 检查时间戳格式
        if "placed_at" in record:
            is_valid, error = check_timestamp_format(record["placed_at"], "filled_order", record.get("order_id", f"line_{line_num}"))
            if not is_valid:
                issues.append(f"Line {line_num}: placed_at {error}")
        
        # 检查SELL订单的已实现损益字段
        if record.get("action") == "SELL":
            sell_required_fields = ["realized_pnl", "realized_pnl_pct", "cost_basis", "proceeds"]
            for field in sell_required_fields:
                if field not in record:
                    issues.append(f"Line {line_num} (SELL): Missing required field '{field}'")
            
            # 检查已实现损益计算
            if all(field in record for field in ["realized_pnl", "cost_basis", "proceeds"]):
                cost_basis = float(record.get("cost_basis", 0))
                proceeds = float(record.get("proceeds", 0))
                realized_pnl = float(record.get("realized_pnl", 0))
                calculated_pnl = proceeds - cost_basis
                
                if abs(realized_pnl - calculated_pnl) > 0.01:
                    issues.append(f"Line {line_num} (SELL): realized_pnl ({realized_pnl:.2f}) != proceeds ({proceeds:.2f}) - cost_basis ({cost_basis:.2f}) = {calculated_pnl:.2f}")
            
            # 检查百分比计算
            if all(field in record for field in ["realized_pnl_pct", "realized_pnl", "cost_basis"]):
                cost_basis = float(record.get("cost_basis", 0))
                realized_pnl = float(record.get("realized_pnl", 0))
                realized_pnl_pct = float(record.get("realized_pnl_pct", 0))
                
                if cost_basis > 0:
                    calculated_pct = (realized_pnl / cost_basis) * 100.0
                    if abs(realized_pnl_pct - calculated_pct) > 0.01:
                        issues.append(f"Line {line_num} (SELL): realized_pnl_pct ({realized_pnl_pct:.2f}%) != (realized_pnl / cost_basis) * 100 = {calculated_pct:.2f}%")
        
        # 检查BUY订单不应该有已实现损益
        if record.get("action") == "BUY":
            if "realized_pnl" in record and record.get("realized_pnl") != 0:
                issues.append(f"Line {line_num} (BUY): BUY orders should not have realized_pnl, got: {record.get('realized_pnl')}")
    
    # 显示最后几条SELL订单（包含已实现损益）
    print("\nLast 5 SELL orders (with realized P&L):")
    print("-" * 80)
    sell_records = [(ln, r) for ln, r in records if r.get("action") == "SELL"]
    for line_num, record in sell_records[-5:]:
        symbol = record.get("symbol", "N/A")
        quantity = record.get("quantity", 0)
        fill_price = record.get("fill_price", 0)
        realized_pnl = record.get("realized_pnl", 0)
        realized_pnl_pct = record.get("realized_pnl_pct", 0)
        cost_basis = record.get("cost_basis", 0)
        proceeds = record.get("proceeds", 0)
        placed_at = record.get("placed_at", "N/A")[:19] if record.get("placed_at") else "N/A"
        print(f"  Line {line_num}: {placed_at} | SELL {quantity} {symbol} @ ${fill_price:.2f} | P&L=${realized_pnl:.2f} ({realized_pnl_pct:+.2f}%) | Cost=${cost_basis:.2f} → Proceeds=${proceeds:.2f}")
    
    return {
        "ok": len(issues) == 0,
        "orders_count": len(records),
        "buy_orders": len(buy_orders),
        "sell_orders": len(sell_orders),
        "issues": issues,
        "issues_count": len(issues)
    }

def check_portfolio_state_consistency(logs_dir: Path) -> Dict[str, Any]:
    """检查portfolio_state.json一致性"""
    print("\n" + "="*80)
    print("💼 Portfolio State Consistency Check")
    print("="*80)
    
    portfolio_file = logs_dir / "portfolio_state.json"
    if not portfolio_file.exists():
        return {"ok": False, "error": "portfolio_state.json not found"}
    
    try:
        with portfolio_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception as e:
        return {"ok": False, "error": f"Failed to parse portfolio_state.json: {e}"}
    
    issues = []
    
    # 检查必需字段
    required_fields = ["cash", "initial_value", "total_value"]
    for field in required_fields:
        if field not in state:
            issues.append(f"Missing required field '{field}'")
    
    # 检查数值一致性
    cash = float(state.get("cash", 0))
    initial_value = float(state.get("initial_value", 0))
    total_value = float(state.get("total_value", 0))
    
    # 计算equity_value
    equity_value = 0.0
    if "positions" in state:
        for symbol, pos_data in state["positions"].items():
            if isinstance(pos_data, dict):
                quantity = float(pos_data.get("quantity", 0))
                avg_cost = float(pos_data.get("avg_cost", 0))
                # 使用avg_cost作为当前价格（如果没有current_price）
                current_price = float(pos_data.get("current_price", avg_cost))
                equity_value += quantity * current_price
    
    calculated_total = cash + equity_value
    
    if abs(total_value - calculated_total) > 0.01:
        issues.append(f"total_value ({total_value:.2f}) != cash ({cash:.2f}) + calculated_equity ({equity_value:.2f}) = {calculated_total:.2f}")
    
    # 检查total_pnl计算
    if "total_pnl" in state:
        total_pnl = float(state.get("total_pnl", 0))
        calculated_pnl = total_value - initial_value
        if abs(total_pnl - calculated_pnl) > 0.01:
            issues.append(f"total_pnl ({total_pnl:.2f}) != total_value ({total_value:.2f}) - initial_value ({initial_value:.2f}) = {calculated_pnl:.2f}")
    
    print(f"Cash: ${cash:.2f}")
    print(f"Initial Value: ${initial_value:.2f}")
    print(f"Total Value: ${total_value:.2f}")
    print(f"Calculated Equity Value: ${equity_value:.2f}")
    print(f"Positions: {len(state.get('positions', {}))}")
    
    return {
        "ok": len(issues) == 0,
        "issues": issues,
        "issues_count": len(issues)
    }

def main():
    """Main function"""
    logs_dir = get_logs_dir()
    
    print("="*80)
    print("🔍 Record Consistency Check")
    print("="*80)
    print(f"Logs directory: {logs_dir}")
    
    results = {}
    
    # 检查净值记录
    equity_result = check_equity_history_consistency(logs_dir)
    results["equity_history"] = equity_result
    
    # 检查已成交订单
    filled_result = check_filled_orders_consistency(logs_dir)
    results["filled_orders"] = filled_result
    
    # 检查portfolio状态
    portfolio_result = check_portfolio_state_consistency(logs_dir)
    results["portfolio_state"] = portfolio_result
    
    # 总结
    print("\n" + "="*80)
    print("📋 Summary")
    print("="*80)
    
    total_issues = 0
    for check_name, result in results.items():
        if result.get("ok"):
            print(f"✅ {check_name}: OK")
        else:
            if "error" in result:
                print(f"❌ {check_name}: {result['error']}")
            else:
                issues_count = result.get("issues_count", 0)
                total_issues += issues_count
                if issues_count > 0:
                    print(f"⚠️  {check_name}: {issues_count} issues found")
                    # 显示前5个问题
                    for issue in result.get("issues", [])[:5]:
                        print(f"   - {issue}")
                    if issues_count > 5:
                        print(f"   ... and {issues_count - 5} more issues")
                else:
                    print(f"✅ {check_name}: OK")
    
    if total_issues == 0:
        print("\n✅ All checks passed! Records are consistent.")
        return 0
    else:
        print(f"\n⚠️  Total issues found: {total_issues}")
        print("Please review the issues above and fix them.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

