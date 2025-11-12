"""清理今天之前的 memory JSON 文件"""
import sys
from pathlib import Path
from datetime import date

# 修复 Windows 编码问题
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def cleanup_old_memory_files():
    """删除今天之前的 memory JSON 文件"""
    today = date.today().isoformat()
    print(f"Today: {today}")
    print("=" * 60)
    
    # 清理 daily memory
    daily_dir = Path("backend/data/logs/memory/daily")
    if daily_dir.exists():
        files = list(daily_dir.glob("*.json"))
        old_files = [f for f in files if f.stem < today]
        
        print(f"\nDaily memory files:")
        print(f"  Total: {len(files)} files")
        print(f"  To delete: {len(old_files)} files (before {today})")
        
        if old_files:
            print(f"\nDeleting old files:")
            for f in sorted(old_files):
                size_kb = f.stat().st_size / 1024
                print(f"  - {f.name} ({size_kb:.2f} KB)")
                f.unlink()
            print(f"\n✅ Deleted {len(old_files)} old daily memory files")
        else:
            print("  ✅ No old files to delete")
        
        # 显示剩余文件
        remaining = [f for f in daily_dir.glob("*.json") if f.stem >= today]
        if remaining:
            print(f"\nRemaining files:")
            for f in sorted(remaining):
                size_kb = f.stat().st_size / 1024
                print(f"  - {f.name} ({size_kb:.2f} KB)")
    
    # 清理 weekly memory（可选）
    weekly_dir = Path("backend/data/logs/memory/weekly")
    if weekly_dir.exists():
        files = list(weekly_dir.glob("*.json"))
        if files:
            print(f"\nWeekly memory files: {len(files)} files")
            print("  (Not deleting - weekly files are summaries)")
    
    # 清理 monthly memory（可选）
    monthly_dir = Path("backend/data/logs/memory/monthly")
    if monthly_dir.exists():
        files = list(monthly_dir.glob("*.json"))
        if files:
            print(f"\nMonthly memory files: {len(files)} files")
            print("  (Not deleting - monthly files are summaries)")
    
    print("\n" + "=" * 60)
    print("✅ Cleanup completed")

if __name__ == "__main__":
    cleanup_old_memory_files()

