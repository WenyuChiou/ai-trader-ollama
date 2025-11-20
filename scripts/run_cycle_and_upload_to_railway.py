#!/usr/bin/env python3
"""
Run trading cycle locally and upload data to Railway
Usage: python scripts/run_cycle_and_upload_to_railway.py
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

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
    print("Step 1: Running Trading Cycle (Local)")
    print("=" * 60)
    
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.utils.config_loader import load_config
        
        # Load config
        config = load_config()
        universe = config.get("universe", None)
        tool_budget = config.get("tool_budget", 10)
        rounds = config.get("rounds", 3)
        
        print(f"\nConfiguration:")
        print(f"   - Universe: {len(universe) if universe else 'All NASDAQ-100'}")
        print(f"   - Tool budget: {tool_budget}")
        print(f"   - Rounds: {rounds}")
        print(f"\nStarting trading cycle...")
        print(f"   This may take 2-5 minutes...\n")
        
        # Run trading cycle
        result = execute_daily_trade(
            rounds=rounds,
            auto_tools=True,
            tool_budget=tool_budget,
            universe=universe
        )
        
        print("\n[SUCCESS] Trading cycle completed!")
        print(f"   Result: {result.get('status', 'completed')}")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error running trading cycle: {e}")
        import traceback
        traceback.print_exc()
        return False

def upload_to_railway():
    """Upload data to Railway"""
    print("\n" + "=" * 60)
    print("Step 2: Uploading Data to Railway")
    print("=" * 60)
    
    try:
        # Import upload functions directly
        import requests
        import json
        from pathlib import Path
        
        # Get Railway URL from environment variable or use default
        RAILWAY_URL = os.environ.get("RAILWAY_URL", "")
        if not RAILWAY_URL:
            try:
                from scripts.config_railway import get_railway_url
                RAILWAY_URL = get_railway_url()
            except ImportError:
                pass
        if not RAILWAY_URL:
            print("[ERROR] Railway URL not configured. Please run: python scripts\\config_railway.py")
            return False
        
        # Find and read data files
        DATA_DIRS = [Path("data/logs"), Path("backend/data/logs")]
        
        def find_data_file(filename):
            for data_dir in DATA_DIRS:
                file_path = data_dir / filename
                if file_path.exists():
                    return file_path
            return None
        
        def read_jsonl_file(file_path):
            if not file_path or not file_path.exists():
                return []
            entries = []
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                entries.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
            except Exception as e:
                print(f"[WARNING] Failed to read {file_path}: {e}")
            return entries
        
        # Read all data files
        convo_file = find_data_file("discussion_actions.jsonl")
        trades_file = find_data_file("trades.jsonl")
        filled_file = find_data_file("filled_orders.jsonl")
        pending_file = find_data_file("pending_orders.jsonl")
        equity_file = find_data_file("equity_history.jsonl")
        portfolio_file = find_data_file("portfolio_state.json")
        
        conversations = read_jsonl_file(convo_file) if convo_file else []
        trades = read_jsonl_file(trades_file) if trades_file else []
        filled_orders = read_jsonl_file(filled_file) if filled_file else []
        pending_orders = read_jsonl_file(pending_file) if pending_file else []
        equity_history = read_jsonl_file(equity_file) if equity_file else []
        
        # Read portfolio_state.json (not JSONL, so read differently)
        portfolio_state = None
        if portfolio_file and portfolio_file.exists():
            try:
                with open(portfolio_file, 'r', encoding='utf-8') as f:
                    portfolio_state = json.load(f)
            except Exception as e:
                print(f"[WARNING] Failed to read portfolio_state.json: {e}")
        
        print(f"   Found {len(conversations)} conversations")
        print(f"   Found {len(trades)} trades")
        print(f"   Found {len(filled_orders)} filled orders")
        print(f"   Found {len(pending_orders)} pending orders")
        print(f"   Found {len(equity_history)} equity history records")
        print(f"   Found portfolio_state.json: {portfolio_state is not None}")
        
        # Prepare data
        data_dict = {}
        if conversations:
            data_dict["conversations"] = conversations
        if trades:
            data_dict["trades"] = trades
        if filled_orders:
            data_dict["filled_orders"] = filled_orders
        if pending_orders:
            data_dict["pending_orders"] = pending_orders
        if equity_history:
            data_dict["equity_history"] = equity_history
        if portfolio_state:
            data_dict["portfolio_state"] = portfolio_state
        
        if not data_dict:
            print("\n[WARNING] No new data to upload")
            return True
        
        # Upload
        print(f"\n   Uploading to: {RAILWAY_URL}/api/data/upload")
        response = requests.post(
            f"{RAILWAY_URL}/api/data/upload",
            json=data_dict,
            timeout=120,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("ok"):
                uploaded = result.get("uploaded", {})
                print(f"\n[SUCCESS] Data uploaded successfully!")
                print(f"   Uploaded: {uploaded}")
                return True
            else:
                print(f"\n[ERROR] Upload failed: {result.get('error')}")
                return False
        else:
            print(f"\n[ERROR] API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
    except Exception as e:
        print(f"\n[ERROR] Failed to upload data: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("\n" + "=" * 60)
    print("Run Trading Cycle & Upload to Railway")
    print("=" * 60)
    print("\nThis script will:")
    print("  1. Run a trading cycle locally")
    print("  2. Upload the generated data to Railway")
    print("  3. Update GitHub Pages with new data\n")
    
    # Step 1: Run trading cycle
    cycle_success = run_trading_cycle_direct()
    
    if not cycle_success:
        print("\n[ERROR] Trading cycle failed. Stopping.")
        return False
    
    # Step 2: Upload to Railway
    upload_success = upload_to_railway()
    
    if not upload_success:
        print("\n[WARNING] Upload failed, but trading cycle completed.")
        print("   You can manually upload later with:")
        print("   python scripts/upload_data_to_railway.py")
        return False
    
    print("\n" + "=" * 60)
    print("[SUCCESS] All steps completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Wait 1-2 minutes for Railway to process")
    print("  2. Refresh GitHub Pages:")
    print("     https://wenyuchiou.github.io/ai-trader-ollama/monitor.html")
    print("  3. You should see the new data!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

