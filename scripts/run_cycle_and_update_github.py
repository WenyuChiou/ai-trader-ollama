#!/usr/bin/env python3
"""
Directly run a trading cycle and update GitHub Pages report
This script runs the trading cycle directly (no API needed)
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
import time

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

def run_trading_cycle_direct():
    """Run trading cycle directly"""
    print("=" * 60)
    print("Running Trading Cycle (Direct)")
    print("=" * 60)
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.utils.config_loader import load_config
        
        # Load config
        config = load_config()
        universe = config.get("universe", None)
        tool_budget = config.get("tool_budget", 10)
        rounds = config.get("rounds", 3)
        
        print(f"\n📊 Configuration:")
        print(f"   - Universe: {len(universe) if universe else 'All NASDAQ-100'}")
        print(f"   - Tool budget: {tool_budget}")
        print(f"   - Rounds: {rounds}")
        print(f"\n⏳ Starting trading cycle...")
        print(f"   This may take 2-5 minutes...\n")
        
        # Run trading cycle
        result = execute_daily_trade(
            rounds=rounds,
            auto_tools=True,
            tool_budget=tool_budget,
            universe=universe
        )
        
        print("\n✅ Trading cycle completed!")
        print(f"   Result: {result.get('status', 'completed')}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error running trading cycle: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_report():
    """Generate static report"""
    print("\n" + "=" * 60)
    print("Generating Report")
    print("=" * 60)
    
    import subprocess
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "generate_static_report.py"), "--output", str(ROOT / "frontend" / "report.html")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        
        print(result.stdout)
        if result.returncode == 0:
            return True
        else:
            print("❌ Report generation failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error generating report: {e}")
        return False

def main():
    print("\n" + "=" * 60)
    print("Update GitHub Pages with Trading Data")
    print("=" * 60)
    
    # Step 1: Run trading cycle
    print("\n[Step 1] Running trading cycle...")
    success = run_trading_cycle_direct()
    
    if not success:
        print("\n⚠️  Trading cycle did not complete successfully.")
        print("   Continuing to generate report with existing data...")
    
    # Wait for data to be written
    print("\n⏳ Waiting for data to be written to files...")
    time.sleep(5)
    
    # Step 2: Generate report
    print("\n[Step 2] Generating report...")
    if not generate_report():
        print("❌ Failed to generate report")
        return False
    
    # Step 3: Instructions
    print("\n" + "=" * 60)
    print("✅ Complete!")
    print("=" * 60)
    print("\n📊 Report generated: frontend/report.html")
    print("\n📤 To update GitHub Pages, run:")
    print("   git add frontend/report.html")
    print("   git commit -m \"Update report with latest trading data\"")
    print("   git push origin main")
    print("\n🌐 GitHub Pages will automatically update within a few minutes.")
    print("   View at: https://WenyuChiou.github.io/ai-trader-ollama/report.html")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

