#!/usr/bin/env python3
"""
Run a trading cycle and update GitHub Pages report
"""
from __future__ import annotations
import sys
import os
import time
from pathlib import Path
import requests
import json

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def check_api_running():
    """Check if backend API is running"""
    try:
        response = requests.get("http://localhost:8000/api/status", timeout=5)
        if response.status_code == 200:
            return True
    except:
        pass
    return False

def run_trading_cycle():
    """Run a trading cycle via API"""
    print("=" * 60)
    print("Running Trading Cycle")
    print("=" * 60)
    
    try:
        print("\n📡 Calling API endpoint: /api/trading/execute-trade")
        response = requests.post(
            "http://localhost:8000/api/trading/execute-trade",
            json={},
            timeout=600,  # 10 minutes timeout
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("✅ Trading cycle completed successfully!")
                return True
            else:
                print(f"❌ Trading cycle failed: {data.get('error', 'Unknown error')}")
                return False
        elif response.status_code == 429:
            print("⚠️  Trading cycle is already running. Please wait...")
            return False
        else:
            print(f"❌ API returned status {response.status_code}: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout (trading cycle took too long)")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to API. Is the backend running?")
        print("   Start it with: python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
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
        
        if result.returncode == 0:
            print(result.stdout)
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
    
    # Step 1: Check API
    print("\n[Step 1] Checking if backend API is running...")
    if not check_api_running():
        print("❌ Backend API is not running!")
        print("\nPlease start the backend API first:")
        print("  python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000")
        return False
    print("✅ Backend API is running")
    
    # Step 2: Run trading cycle
    print("\n[Step 2] Running trading cycle...")
    print("⏳ This may take 1-5 minutes...")
    success = run_trading_cycle()
    
    if not success:
        print("\n⚠️  Trading cycle did not complete successfully.")
        print("   Continuing to generate report with existing data...")
    
    # Wait a bit for data to be written
    print("\n⏳ Waiting for data to be written...")
    time.sleep(3)
    
    # Step 3: Generate report
    print("\n[Step 3] Generating report...")
    if not generate_report():
        print("❌ Failed to generate report")
        return False
    
    # Step 4: Instructions for committing
    print("\n" + "=" * 60)
    print("Next Steps")
    print("=" * 60)
    print("\n✅ Report generated: frontend/report.html")
    print("\nTo update GitHub Pages, run:")
    print("  git add frontend/report.html")
    print("  git commit -m \"Update report with latest trading data\"")
    print("  git push origin main")
    print("\nGitHub Pages will automatically update within a few minutes.")
    
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

