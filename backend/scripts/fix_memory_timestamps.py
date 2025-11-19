#!/usr/bin/env python3
"""
Fix timestamp formats in memory files to use millisecond precision (3 decimal places).
"""
import sys
from pathlib import Path
import json

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from src.utils.timestamp_utils import normalize_timestamp


def fix_memory_file(file_path: Path):
    """Fix timestamps in a memory JSON file"""
    if not file_path.exists():
        print(f"[SKIP] File does not exist: {file_path}")
        return 0
    
    try:
        with file_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        fixed_count = 0
        
        # Fix top-level timestamp
        if "timestamp" in data and data["timestamp"]:
            try:
                old_ts = data["timestamp"]
                new_ts = normalize_timestamp(old_ts)
                if old_ts != new_ts:
                    data["timestamp"] = new_ts
                    fixed_count += 1
                    print(f"  Fixed timestamp: {old_ts} -> {new_ts}")
            except ValueError as e:
                print(f"  [WARN] Failed to normalize timestamp: {e}")
        
        if fixed_count > 0:
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
    """Main function to fix all memory files"""
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    memory_dir = project_root / "data" / "logs" / "memory"
    
    if not memory_dir.exists():
        print(f"[INFO] Memory directory does not exist: {memory_dir}")
        return
    
    print(f"[INFO] Fixing timestamps in {memory_dir}")
    print("=" * 60)
    
    total_fixed = 0
    
    # Fix all JSON files in memory directory
    json_files = list(memory_dir.glob("*.json"))
    
    for json_file in json_files:
        fixed = fix_memory_file(json_file)
        total_fixed += fixed
    
    print("=" * 60)
    print(f"[SUMMARY] Total timestamps fixed: {total_fixed}")


if __name__ == "__main__":
    main()

