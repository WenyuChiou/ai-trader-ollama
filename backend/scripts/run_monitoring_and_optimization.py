# scripts/run_monitoring_and_optimization.py
"""
每日监控和优化脚本
- 生成监控报告
- 生成优化建议
- 可设置为定时任务（例如：每日收盘后运行）
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

# Fix Windows encoding and ensure immediate output
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        try:
            sys.stdout.reconfigure(line_buffering=True)
        except:
            pass

# Force immediate flushing
import functools
print = functools.partial(print, flush=True)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

print("[INIT] Script starting...")
print(f"[INIT] Working directory: {ROOT}")
sys.stdout.flush()

def main():
    """运行监控和优化报告"""
    import argparse
    
    print("[MAIN] Parsing arguments...")
    parser = argparse.ArgumentParser(description="Run monitoring and optimization reports")
    parser.add_argument("--days", type=int, default=7, help="Days for monitoring report (default: 7)")
    parser.add_argument("--optimize-days", type=int, default=30, help="Days for optimization analysis (default: 30)")
    parser.add_argument("--monitoring-only", action="store_true", help="Only run monitoring report")
    parser.add_argument("--optimization-only", action="store_true", help="Only run optimization report")
    
    args = parser.parse_args()
    print(f"[MAIN] Arguments parsed: days={args.days}, optimize_days={args.optimize_days}")
    
    print("\n" + "="*80)
    print(" AI-Trader: Monitoring & Optimization Report")
    print("="*80)
    print(f"Monitoring Period: Last {args.days} days")
    print(f"Optimization Period: Last {args.optimize_days} days")
    print("="*80 + "\n")
    
    try:
        if not args.optimization_only:
            # 运行监控报告
            print("[1/2] Running Monitoring Report...")
            print("-" * 80)
            
            try:
                print("[INFO] Step 1: Importing monitoring_system module...")
                from scripts import monitoring_system
                print("[✓] Module imported successfully")
                
                print("[INFO] Step 2: Importing TradingMonitor class...")
                from scripts.monitoring_system import TradingMonitor
                print("[✓] TradingMonitor class imported")
                
                print("[INFO] Step 3: Creating TradingMonitor instance...")
                print("        (This may take a moment to initialize MemoryManager, EquityTracker, etc.)")
                monitor = TradingMonitor()
                print("[✓] Monitor initialized successfully\n")
                
                print(f"[INFO] Step 4: Generating monitoring report for last {args.days} days...")
                print("        (Loading data, this may take a moment...)\n")
                monitor.print_monitoring_report(days=args.days)
                print("\n[✓] Monitoring report completed successfully")
            except Exception as e:
                print(f"\n❌ [ERROR] Monitoring report failed: {e}")
                import traceback
                print("\nFull traceback:")
                traceback.print_exc()
                return 1
        
        if not args.monitoring_only:
            # 运行优化报告
            print("\n[2/2] Running Optimization Report...")
            print("-" * 80)
            
            try:
                print("[INFO] Step 1: Importing optimization_system module...")
                from scripts import optimization_system
                print("[✓] Module imported successfully")
                
                print("[INFO] Step 2: Importing TradingOptimizer class...")
                from scripts.optimization_system import TradingOptimizer
                print("[✓] TradingOptimizer class imported")
                
                print("[INFO] Step 3: Creating TradingOptimizer instance...")
                print("        (This may take a moment to initialize MemoryManager, EquityTracker, etc.)")
                optimizer = TradingOptimizer()
                print("[✓] Optimizer initialized successfully\n")
                
                print(f"[INFO] Step 4: Analyzing performance for last {args.optimize_days} days...")
                print("        (Loading data and calculating metrics, this may take a moment...)\n")
                optimizer.print_optimization_report(days=args.optimize_days)
                print("\n[✓] Optimization report completed successfully")
            except Exception as e:
                print(f"\n❌ [ERROR] Optimization report failed: {e}")
                import traceback
                print("\nFull traceback:")
                traceback.print_exc()
                return 1
        
        print("\n" + "="*80)
        print("[SUCCESS] All reports completed successfully!")
        print("="*80)
        return 0
        
    except KeyboardInterrupt:
        print("\n[INFO] Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code if exit_code is not None else 0)

