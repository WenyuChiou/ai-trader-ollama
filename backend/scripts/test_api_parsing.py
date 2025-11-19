#!/usr/bin/env python3
"""
测试所有API端点是否能正确解析统一的数据格式
"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

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

def test_timestamp_parsing(timestamp_str: str) -> tuple[bool, Optional[str]]:
    """测试时间戳解析"""
    if not timestamp_str:
        return False, "Empty timestamp"
    
    # 检查是否以Z结尾
    if not timestamp_str.endswith('Z'):
        return False, f"Timestamp missing 'Z' suffix: {timestamp_str}"
    
    # 尝试解析ISO 8601格式
    try:
        # 支持多种格式
        if '.' in timestamp_str:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
        return True, None
    except ValueError as e:
        return False, f"Invalid ISO 8601 format: {e}"

def test_equity_history_parsing():
    """测试equity_history.jsonl的解析"""
    print("\n" + "="*80)
    print("📊 Testing Equity History Parsing")
    print("="*80)
    
    logs_dir = get_logs_dir()
    equity_file = logs_dir / "equity_history.jsonl"
    
    if not equity_file.exists():
        print("⚠️  equity_history.jsonl not found, skipping test")
        return {"ok": True, "skipped": True}
    
    issues = []
    records_parsed = 0
    
    with equity_file.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line.strip())
                records_parsed += 1
                
                # 测试时间戳解析
                if "timestamp" in record:
                    is_valid, error = test_timestamp_parsing(record["timestamp"])
                    if not is_valid:
                        issues.append(f"Line {line_num}: {error}")
                
                # 测试必需字段
                required_fields = ["date", "timestamp", "cash", "equity_value", "total_value"]
                for field in required_fields:
                    if field not in record:
                        issues.append(f"Line {line_num}: Missing required field '{field}'")
                
                # 测试数值类型
                numeric_fields = ["cash", "equity_value", "total_value", "total_pnl", "total_pnl_pct"]
                for field in numeric_fields:
                    if field in record:
                        try:
                            float(record[field])
                        except (ValueError, TypeError):
                            issues.append(f"Line {line_num}: Invalid numeric value for '{field}': {record[field]}")
                
            except json.JSONDecodeError as e:
                issues.append(f"Line {line_num}: JSON parse error: {e}")
    
    print(f"✅ Parsed {records_parsed} records")
    if issues:
        print(f"⚠️  Found {len(issues)} issues:")
        for issue in issues[:10]:  # 只显示前10个
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")
        return {"ok": False, "issues": issues, "records_parsed": records_parsed}
    else:
        print("✅ All records parsed successfully")
        return {"ok": True, "records_parsed": records_parsed}

def test_filled_orders_parsing():
    """测试filled_orders.jsonl的解析"""
    print("\n" + "="*80)
    print("💰 Testing Filled Orders Parsing")
    print("="*80)
    
    logs_dir = get_logs_dir()
    filled_file = logs_dir / "filled_orders.jsonl"
    
    if not filled_file.exists():
        print("⚠️  filled_orders.jsonl not found, skipping test")
        return {"ok": True, "skipped": True}
    
    issues = []
    orders_parsed = 0
    
    with filled_file.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if not line.strip():
                continue
            try:
                order = json.loads(line.strip())
                orders_parsed += 1
                
                # 测试时间戳解析
                if "placed_at" in order:
                    is_valid, error = test_timestamp_parsing(order["placed_at"])
                    if not is_valid:
                        issues.append(f"Line {line_num}: placed_at {error}")
                
                if "filled_at" in order and order["filled_at"]:
                    is_valid, error = test_timestamp_parsing(order["filled_at"])
                    if not is_valid:
                        issues.append(f"Line {line_num}: filled_at {error}")
                
                # 测试必需字段
                required_fields = ["order_id", "placed_at", "symbol", "action", "quantity", "fill_price", "status"]
                for field in required_fields:
                    if field not in order:
                        issues.append(f"Line {line_num}: Missing required field '{field}'")
                
                # 测试SELL订单的已实现损益字段
                if order.get("action") == "SELL":
                    sell_required_fields = ["realized_pnl", "realized_pnl_pct", "cost_basis", "proceeds"]
                    for field in sell_required_fields:
                        if field not in order:
                            issues.append(f"Line {line_num} (SELL): Missing required field '{field}'")
                
            except json.JSONDecodeError as e:
                issues.append(f"Line {line_num}: JSON parse error: {e}")
    
    print(f"✅ Parsed {orders_parsed} orders")
    if issues:
        print(f"⚠️  Found {len(issues)} issues:")
        for issue in issues[:10]:
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")
        return {"ok": False, "issues": issues, "orders_parsed": orders_parsed}
    else:
        print("✅ All orders parsed successfully")
        return {"ok": True, "orders_parsed": orders_parsed}

def test_api_endpoint_compatibility():
    """测试API端点兼容性（模拟API调用）"""
    print("\n" + "="*80)
    print("🔌 Testing API Endpoint Compatibility")
    print("="*80)
    
    logs_dir = get_logs_dir()
    equity_file = logs_dir / "equity_history.jsonl"
    filled_file = logs_dir / "filled_orders.jsonl"
    
    issues = []
    
    # 测试1: equity-history API端点格式
    if equity_file.exists():
        try:
            from src.data.equity_tracker import EquityTracker
            equity_tracker = EquityTracker(root=str(logs_dir))
            records = equity_tracker.load_equity_history(limit=10)
            
            # 验证返回格式
            for record in records:
                if "timestamp" not in record:
                    issues.append(f"Equity record missing 'timestamp': {record.get('date', 'N/A')}")
                elif not record["timestamp"].endswith('Z'):
                    issues.append(f"Equity record timestamp missing 'Z': {record['timestamp']}")
            
            print(f"✅ Equity history API format: OK ({len(records)} records tested)")
        except Exception as e:
            issues.append(f"Equity history API test failed: {e}")
            print(f"❌ Equity history API format: FAILED - {e}")
    
    # 测试2: trades/recent API端点格式
    if filled_file.exists():
        try:
            trades = []
            with filled_file.open("r", encoding="utf-8") as f:
                f.seek(0, 2)
                file_size = f.tell()
                position = max(0, file_size - 1024 * 100)
                f.seek(position)
                lines = f.readlines()
                
                for line in reversed(lines[-10:]):
                    if line.strip():
                        try:
                            trade = json.loads(line.strip())
                            trades.append(trade)
                        except json.JSONDecodeError:
                            continue
            
            # 验证返回格式
            for trade in trades:
                if "placed_at" not in trade:
                    issues.append(f"Trade missing 'placed_at': {trade.get('order_id', 'N/A')}")
                elif not trade["placed_at"].endswith('Z'):
                    issues.append(f"Trade placed_at missing 'Z': {trade['placed_at']}")
            
            print(f"✅ Trades API format: OK ({len(trades)} trades tested)")
        except Exception as e:
            issues.append(f"Trades API test failed: {e}")
            print(f"❌ Trades API format: FAILED - {e}")
    
    if issues:
        print(f"⚠️  Found {len(issues)} compatibility issues:")
        for issue in issues[:10]:
            print(f"   - {issue}")
        if len(issues) > 10:
            print(f"   ... and {len(issues) - 10} more issues")
        return {"ok": False, "issues": issues}
    else:
        print("✅ All API endpoints compatible with data format")
        return {"ok": True}

def main():
    """Main function"""
    print("="*80)
    print("🧪 API Data Parsing Test")
    print("="*80)
    
    results = {}
    
    # 测试equity history解析
    equity_result = test_equity_history_parsing()
    results["equity_history"] = equity_result
    
    # 测试filled orders解析
    filled_result = test_filled_orders_parsing()
    results["filled_orders"] = filled_result
    
    # 测试API端点兼容性
    api_result = test_api_endpoint_compatibility()
    results["api_compatibility"] = api_result
    
    # 总结
    print("\n" + "="*80)
    print("📋 Summary")
    print("="*80)
    
    all_ok = True
    for test_name, result in results.items():
        if result.get("ok"):
            print(f"✅ {test_name}: OK")
        else:
            all_ok = False
            if "skipped" in result:
                print(f"⚠️  {test_name}: SKIPPED (file not found)")
            else:
                print(f"❌ {test_name}: FAILED ({len(result.get('issues', []))} issues)")
    
    if all_ok:
        print("\n✅ All tests passed! APIs can correctly parse the data format.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

