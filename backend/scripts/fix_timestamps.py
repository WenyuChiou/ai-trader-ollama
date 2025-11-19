#!/usr/bin/env python3
"""
Fix timestamp formats in data files to use millisecond precision (3 decimal places).

This script normalizes all timestamps in data files to the standard format:
YYYY-MM-DDTHH:MM:SS.fffZ (millisecond precision, UTC timezone)
"""
import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.utils.timestamp_utils import normalize_timestamp, ensure_timestamp_has_z_suffix


def fix_jsonl_file(file_path: Path, timestamp_fields: list[str] = ["timestamp", "placed_at", "filled_at", "ts"]):
    """Fix timestamps in a JSONL file"""
    if not file_path.exists():
        print(f"[SKIP] File does not exist: {file_path}")
        return 0
    
    fixed_count = 0
    lines = []
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    lines.append(line)
                    continue
                
                try:
                    record = json.loads(line)
                    modified = False
                    
                    for field in timestamp_fields:
                        if field in record and record[field]:
                            try:
                                old_ts = record[field]
                                new_ts = normalize_timestamp(old_ts)
                                if old_ts != new_ts:
                                    record[field] = new_ts
                                    modified = True
                                    fixed_count += 1
                            except ValueError:
                                # If normalization fails, at least ensure Z suffix
                                if not record[field].endswith('Z'):
                                    record[field] = ensure_timestamp_has_z_suffix(record[field])
                                    modified = True
                                    fixed_count += 1
                    
                    if modified:
                        lines.append(json.dumps(record, ensure_ascii=False) + "\n")
                    else:
                        lines.append(line)
                        
                except json.JSONDecodeError as e:
                    print(f"[WARN] Line {line_num}: JSON decode error: {e}")
                    lines.append(line)
        
        # Write back if any fixes were made
        if fixed_count > 0:
            with file_path.open("w", encoding="utf-8") as f:
                f.writelines(lines)
            print(f"[OK] Fixed {fixed_count} timestamps in {file_path.name}")
        else:
            print(f"[OK] No fixes needed in {file_path.name}")
        
        return fixed_count
        
    except Exception as e:
        print(f"[ERROR] Failed to process {file_path}: {e}")
        return 0


def fix_json_file(file_path: Path, timestamp_fields: list[str] = ["timestamp"]):
    """Fix timestamps in a JSON file"""
    if not file_path.exists():
        print(f"[SKIP] File does not exist: {file_path}")
        return 0
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        fixed_count = 0
        modified = False
        
        for field in timestamp_fields:
            if field in data and data[field]:
                try:
                    old_ts = data[field]
                    new_ts = normalize_timestamp(old_ts)
                    if old_ts != new_ts:
                        data[field] = new_ts
                        modified = True
                        fixed_count += 1
                except ValueError:
                    # If normalization fails, at least ensure Z suffix
                    if not data[field].endswith('Z'):
                        data[field] = ensure_timestamp_has_z_suffix(data[field])
                        modified = True
                        fixed_count += 1
        
        if modified:
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"[OK] Fixed {fixed_count} timestamps in {file_path.name}")
        else:
            print(f"[OK] No fixes needed in {file_path.name}")
        
        return fixed_count
        
    except Exception as e:
        print(f"[ERROR] Failed to process {file_path}: {e}")
        return 0


def main():
    """Main function to fix all data files"""
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    logs_dir = project_root / "data" / "logs"
    
    if not logs_dir.exists():
        print(f"[ERROR] Logs directory does not exist: {logs_dir}")
        return
    
    print(f"[INFO] Fixing timestamps in {logs_dir}")
    print("=" * 60)
    
    total_fixed = 0
    
    # Fix JSONL files
    jsonl_files = [
        ("equity_history.jsonl", ["timestamp"]),
        ("discussion_actions.jsonl", ["timestamp"]),
        ("filled_orders.jsonl", ["placed_at", "filled_at", "timestamp"]),
        ("pending_orders.jsonl", ["placed_at", "timestamp"]),
        ("trades.jsonl", ["timestamp", "placed_at", "filled_at"]),
    ]
    
    for filename, fields in jsonl_files:
        file_path = logs_dir / filename
        fixed = fix_jsonl_file(file_path, fields)
        total_fixed += fixed
    
    # Fix JSON files
    json_files = [
        ("portfolio_state.json", ["timestamp"]),
    ]
    
    for filename, fields in json_files:
        file_path = logs_dir / filename
        fixed = fix_json_file(file_path, fields)
        total_fixed += fixed
    
    print("=" * 60)
    print(f"[SUMMARY] Total timestamps fixed: {total_fixed}")


if __name__ == "__main__":
    main()

