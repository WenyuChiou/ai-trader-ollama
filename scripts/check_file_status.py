#!/usr/bin/env python3
"""Check the status of discussion_actions.jsonl file"""
import sys
import io
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_file_status():
    """Check the status of discussion_actions.jsonl"""
    log_file = Path('data/logs/discussion_actions.jsonl')
    
    print("=" * 60)
    print("FILE STATUS CHECK")
    print("=" * 60)
    
    if not log_file.exists():
        print("[ERROR] File does not exist!")
        return
    
    # File basic info
    stat = log_file.stat()
    file_size = stat.st_size
    last_modified = datetime.fromtimestamp(stat.st_mtime)
    
    print(f"\n1. FILE INFORMATION:")
    print(f"   Path: {log_file.absolute()}")
    print(f"   Size: {file_size:,} bytes ({file_size / 1024 / 1024:.2f} MB)")
    print(f"   Last Modified: {last_modified.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Age: {(datetime.now() - last_modified).total_seconds() / 3600:.2f} hours ago")
    
    # Read and analyze file
    with log_file.open('r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n2. FILE CONTENT:")
    print(f"   Total lines: {len(lines)}")
    print(f"   Non-empty lines: {len([l for l in lines if l.strip()])}")
    
    # Parse entries
    entries = []
    for line in lines:
        if line.strip():
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError:
                pass
    
    print(f"   Valid entries: {len(entries)}")
    
    # Analyze by type
    types = Counter(e.get('type', 'unknown') for e in entries)
    print(f"\n3. ENTRY TYPES:")
    for entry_type, count in types.items():
        print(f"   - {entry_type}: {count}")
    
    # Analyze by agent
    agents = Counter(e.get('agent', 'unknown') for e in entries)
    print(f"\n4. AGENTS:")
    for agent, count in sorted(agents.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {agent}: {count}")
    
    # Analyze by date
    dates = Counter(e.get('date', 'unknown') for e in entries)
    print(f"\n5. DATES:")
    for date_str in sorted(dates.keys()):
        print(f"   - {date_str}: {dates[date_str]} entries")
    
    # Recent entries
    print(f"\n6. RECENT ENTRIES (last 5):")
    for i, entry in enumerate(reversed(entries[-5:]), 1):
        timestamp = entry.get('timestamp', '')[:19] if entry.get('timestamp') else 'N/A'
        entry_type = entry.get('type', 'unknown')
        agent = entry.get('agent', 'unknown')
        print(f"   {i}. [{timestamp}] {entry_type} - {agent}")
    
    # Check API reading path
    print(f"\n7. API READING PATH:")
    print(f"   API uses: _get_project_logs_dir() / 'discussion_actions.jsonl'")
    print(f"   Expected: {Path(__file__).parent.parent / 'data' / 'logs' / 'discussion_actions.jsonl'}")
    
    # Verify path match
    api_path = Path(__file__).parent.parent / 'data' / 'logs' / 'discussion_actions.jsonl'
    if api_path.exists() and api_path.samefile(log_file):
        print(f"   [OK] Path matches!")
    else:
        print(f"   [WARN] Path may differ (check API code)")

if __name__ == "__main__":
    check_file_status()

