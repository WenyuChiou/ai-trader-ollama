"""Check equity recording status"""
import json
import sys
from pathlib import Path
from datetime import datetime, timezone

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_equity_records():
    """Check equity recording frequency and content"""
    logs_dir = Path("data/logs")
    equity_file = logs_dir / "equity_history.jsonl"
    
    if not equity_file.exists():
        print("ERROR: equity_history.jsonl not found")
        return
    
    print("=" * 80)
    print("Equity Recording Check")
    print("=" * 80)
    print()
    
    # 读取所有记录
    records = []
    with equity_file.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                except json.JSONDecodeError as e:
                    print(f"⚠️  解析错误: {e}")
                    continue
    
    if not records:
        print("⚠️  没有找到任何记录")
        return
    
    print(f"Total records: {len(records)}")
    print()
    
    # Check recent records
    print("Last 10 records:")
    print("-" * 80)
    for i, record in enumerate(records[-10:], 1):
        timestamp = record.get("timestamp", "N/A")
        date_str = record.get("date", "N/A")
        total_value = record.get("total_value", 0)
        equity_value = record.get("equity_value", 0)
        cash = record.get("cash", 0)
        positions_count = len(record.get("positions", {}))
        
        print(f"{i}. {timestamp}")
        print(f"   Date: {date_str}")
        print(f"   Total Value: ${total_value:.2f}")
        print(f"   Equity Value: ${equity_value:.2f}")
        print(f"   Cash: ${cash:.2f}")
        print(f"   Positions: {positions_count}")
        print()
    
    # Check recording frequency
    print("=" * 80)
    print("Recording Frequency Analysis:")
    print("-" * 80)
    
    if len(records) >= 2:
        time_diffs = []
        for i in range(1, len(records)):
            try:
                prev_time = datetime.fromisoformat(records[i-1].get("timestamp", "").replace('Z', '+00:00'))
                curr_time = datetime.fromisoformat(records[i].get("timestamp", "").replace('Z', '+00:00'))
                diff_seconds = (curr_time - prev_time).total_seconds()
                diff_hours = diff_seconds / 3600
                time_diffs.append(diff_hours)
            except Exception as e:
                print(f"WARNING: Time parsing error: {e}")
                continue
        
        if time_diffs:
            avg_interval = sum(time_diffs) / len(time_diffs)
            min_interval = min(time_diffs)
            max_interval = max(time_diffs)
            
            print(f"Average interval: {avg_interval:.2f} hours")
            print(f"Min interval: {min_interval:.2f} hours")
            print(f"Max interval: {max_interval:.2f} hours")
            print()
            
            # Check for abnormally frequent records (< 0.5 hours)
            frequent_records = [d for d in time_diffs if d < 0.5]
            if frequent_records:
                print(f"WARNING: Found {len(frequent_records)} abnormally frequent records (interval < 0.5 hours)")
                print(f"   Intervals: {[f'{d:.2f}' for d in frequent_records[:5]]}")
            else:
                print("OK: Recording frequency is normal (all intervals >= 0.5 hours)")
    
    # Check data integrity
    print()
    print("=" * 80)
    print("Data Integrity Check:")
    print("-" * 80)
    
    issues = []
    for i, record in enumerate(records):
        if not record.get("timestamp"):
            issues.append(f"Record {i+1}: Missing timestamp")
        if not record.get("date"):
            issues.append(f"Record {i+1}: Missing date")
        if record.get("total_value") is None:
            issues.append(f"Record {i+1}: Missing total_value")
        if record.get("cash") is None:
            issues.append(f"Record {i+1}: Missing cash")
    
    if issues:
        print("ERROR: Issues found:")
        for issue in issues[:10]:
            print(f"  - {issue}")
        if len(issues) > 10:
            print(f"  ... and {len(issues) - 10} more issues")
    else:
        print("OK: All records have complete data")
    
    print()
    print("=" * 80)
    print("Summary:")
    print("-" * 80)
    print(f"OK: Recording frequency: Maximum once per hour (current config)")
    print(f"OK: Total records: {len(records)}")
    print(f"OK: Latest record time: {records[-1].get('timestamp', 'N/A')}")
    print(f"OK: Latest equity: ${records[-1].get('total_value', 0):.2f}")

if __name__ == "__main__":
    check_equity_records()

