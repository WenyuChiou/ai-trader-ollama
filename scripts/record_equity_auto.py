#!/usr/bin/env python3
"""
Auto-generated script for AITrader-EquityRecording
Automatically records portfolio equity every 30 minutes (only during market hours)
"""
from __future__ import annotations
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

import requests
import json
from datetime import datetime

def main():
    """Main function to record equity (only during market hours)"""
    # CRITICAL: 检查市场是否开盘，收盘后不记录
    try:
        from src.utils.trading_days import is_market_open
        if not is_market_open(None):
            print(f"[EQUITY RECORD] Market is closed, skipping equity recording (will resume at next market open)")
            return 0  # 正常退出，不记录错误
    except Exception as e:
        print(f"[EQUITY RECORD WARNING] Failed to check market status: {e}, proceeding with record")
    
    try:
        # Get current portfolio
        response = requests.get("http://localhost:8000/api/portfolio/real-time", timeout=10)
        if response.status_code == 200:
            portfolio = response.json()
            if portfolio.get("ok"):
                # Record equity
                equity_data = {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "timestamp": datetime.now().isoformat() + "Z",
                    "cash": portfolio.get("cash", 0),
                    "equity_value": portfolio.get("equity_value", 0),
                    "total_value": portfolio.get("total_value", 0),
                    "total_pnl": portfolio.get("total_pnl", 0),
                    "total_pnl_pct": portfolio.get("total_pnl_pct", 0),
                    "positions_detail": portfolio.get("positions_detail", {})
                }
                
                record_response = requests.post(
                    "http://localhost:8000/api/portfolio/record-equity",
                    json=equity_data,
                    timeout=10
                )
                
                if record_response.status_code == 200:
                    result = record_response.json()
                    if result.get("ok"):
                        print(f"[EQUITY RECORD] Successfully recorded: ${equity_data['total_value']:.2f}")
                        return 0
                    else:
                        print(f"[EQUITY RECORD] API returned error: {result.get('error', 'Unknown')}")
                        return 1
                else:
                    print(f"[EQUITY RECORD] Failed to record: HTTP {record_response.status_code}")
                    return 1
            else:
                print(f"[EQUITY RECORD] API returned error: {portfolio.get('error', 'Unknown')}")
                return 1
        else:
            print(f"[EQUITY RECORD] API unavailable: HTTP {response.status_code}")
            return 1
    except requests.exceptions.ConnectionError:
        print(f"[EQUITY RECORD] Cannot connect to API server (http://localhost:8000)")
        print(f"[EQUITY RECORD] Make sure the API server is running")
        return 1
    except Exception as e:
        print(f"[EQUITY RECORD] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())

