"""Check equity history data for Performance Analysis"""
import json
import sys
from pathlib import Path
from datetime import date, timedelta

# Fix Windows encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def check_equity_data():
    """Check equity history data"""
    # Try to find project root
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "backend" / "src").exists():
            project_root = parent.parent if (parent / "backend").exists() else parent
            logs_dir = project_root / "data" / "logs"
            break
    else:
        logs_dir = Path("data/logs")
    
    equity_file = logs_dir / "equity_history.jsonl"
    
    print("=" * 80)
    print("Equity History Data Check")
    print("=" * 80)
    print(f"Logs directory: {logs_dir}")
    print(f"Equity file: {equity_file}")
    print(f"File exists: {equity_file.exists()}")
    print()
    
    if not equity_file.exists():
        print("ERROR: equity_history.jsonl not found!")
        return
    
    # Read all records
    records = []
    with equity_file.open("r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if line.strip():
                try:
                    record = json.loads(line.strip())
                    records.append(record)
                except json.JSONDecodeError as e:
                    print(f"⚠️  Line {line_num}: Parse error: {e}")
                    continue
    
    print(f"Total records: {len(records)}")
    print()
    
    if not records:
        print("⚠️  No records found in equity_history.jsonl")
        return
    
    # Group by date
    dates = {}
    for record in records:
        record_date = record.get("date") or (record.get("timestamp", "").split("T")[0] if record.get("timestamp") else "")
        if record_date:
            if record_date not in dates:
                dates[record_date] = []
            dates[record_date].append(record)
    
    print(f"Unique dates: {len(dates)}")
    print(f"Date range: {min(dates.keys())} to {max(dates.keys())}")
    print()
    
    # Show last 10 records
    print("Last 10 records:")
    print("-" * 80)
    for i, record in enumerate(records[-10:], 1):
        timestamp = record.get("timestamp", "N/A")
        date_str = record.get("date", "N/A")
        total_value = record.get("total_value", 0)
        equity_value = record.get("equity_value", 0)
        cash = record.get("cash", 0)
        positions_count = len(record.get("positions", {}))
        
        print(f"{i}. {date_str} {timestamp[:19] if len(timestamp) > 19 else timestamp}")
        print(f"   Total Value: ${total_value:.2f}")
        print(f"   Equity Value: ${equity_value:.2f}")
        print(f"   Cash: ${cash:.2f}")
        print(f"   Positions: {positions_count}")
        print()
    
    # Check date range for Performance Analysis
    today = date.today().isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    last_7_days = (date.today() - timedelta(days=7)).isoformat()
    
    print("=" * 80)
    print("Date Range Check (for Performance Analysis)")
    print("=" * 80)
    print(f"Today: {today}")
    print(f"Yesterday: {yesterday}")
    print(f"Last 7 days start: {last_7_days}")
    print()
    
    # Check records in different date ranges
    today_records = [r for r in records if r.get("date") == today or (r.get("timestamp", "").split("T")[0] == today)]
    yesterday_records = [r for r in records if r.get("date") == yesterday or (r.get("timestamp", "").split("T")[0] == yesterday)]
    last_7_days_records = [r for r in records if (r.get("date") and r.get("date") >= last_7_days) or (r.get("timestamp", "").split("T")[0] >= last_7_days if r.get("timestamp") else False)]
    
    print(f"Records today: {len(today_records)}")
    print(f"Records yesterday: {len(yesterday_records)}")
    print(f"Records in last 7 days: {len(last_7_days_records)}")
    print()
    
    # Show records by date
    print("Records by date (last 7 days):")
    print("-" * 80)
    for check_date in sorted(dates.keys())[-7:]:
        count = len(dates[check_date])
        first_record = dates[check_date][0]
        total_value = first_record.get("total_value", 0)
        print(f"  {check_date}: {count} records, Total Value: ${total_value:.2f}")

if __name__ == "__main__":
    check_equity_data()

