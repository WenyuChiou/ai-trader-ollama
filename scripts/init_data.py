#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Initialize system data
- Initialize Portfolio (reset to initial cash)
- Clear or initialize Memory
- Clear trade logs
- Initialize Equity Tracker

Usage:
    python scripts/init_data.py              # Initialize all data (will prompt for confirmation)
    python scripts/init_data.py --force     # Force initialization (no prompts)
    python scripts/init_data.py --reset-portfolio  # Reset Portfolio only
"""
from __future__ import annotations
import sys
import os
import json
import shutil
from pathlib import Path
from datetime import date, datetime
import argparse

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.portfolio import Portfolio


def init_portfolio(initial_cash: float = 10000.0, force: bool = False) -> bool:
    """Initialize Portfolio state"""
    state_file = ROOT / "data" / "logs" / "portfolio_state.json"
    
    if state_file.exists() and not force:
        print(f"\n⚠️  Portfolio state file already exists: {state_file}")
        print(f"   Initial cash: ${initial_cash:,.2f}")
        response = input("   Reset? (y/N): ").strip().lower()
        if response != 'y':
            print("   [SKIP] Portfolio initialization")
            return False
    
    portfolio = Portfolio(cash=initial_cash, initial_value=initial_cash)
    
    state = {
        "cash": portfolio.cash,
        "initial_value": portfolio.initial_value,
        "positions": {},
        "last_updated": datetime.now().isoformat(),
        "initialized_at": datetime.now().isoformat(),
    }
    
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with state_file.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Portfolio initialized")
    print(f"   File: {state_file}")
    print(f"   Initial cash: ${initial_cash:,.2f}")
    return True


def init_memory(force: bool = False) -> bool:
    """Initialize Memory directory"""
    memory_dir = ROOT / "data" / "logs" / "memory"
    
    if memory_dir.exists() and not force:
        print(f"\n⚠️  Memory directory already exists: {memory_dir}")
        print(f"   Contains {len(list(memory_dir.rglob('*.json')))} memory files")
        response = input("   Clear? (y/N): ").strip().lower()
        if response != 'y':
            print("   [SKIP] Memory initialization")
            return False
    
    # Backup old data (if exists)
    if memory_dir.exists():
        backup_dir = ROOT / "data" / "logs" / f"memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n📦 Backing up old Memory to: {backup_dir}")
        shutil.move(str(memory_dir), str(backup_dir))
    
    # Create new directory structure
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "daily").mkdir(exist_ok=True)
    (memory_dir / "weekly").mkdir(exist_ok=True)
    (memory_dir / "monthly").mkdir(exist_ok=True)
    (memory_dir / "index").mkdir(exist_ok=True)
    
    # Initialize index file
    index_file = memory_dir / "index" / "daily_index.json"
    index_data = {
        "initialized_at": datetime.now().isoformat(),
        "entries": [],
    }
    with index_file.open("w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Memory initialized")
    print(f"   Directory: {memory_dir}")
    return True


def init_trade_logs(force: bool = False) -> bool:
    """Initialize trade logs"""
    logs_dir = ROOT / "data" / "logs"
    
    log_files = [
        "trades.jsonl",
        "pending_orders.jsonl",
        "filled_orders.jsonl",
        "equity_history.jsonl",
        "real_time_snapshots.jsonl",
        "monitoring.jsonl",
        "discussion_actions.jsonl",
    ]
    
    if not force:
        existing = [f for f in log_files if (logs_dir / f).exists()]
        if existing:
            print(f"\n⚠️  The following log files already exist:")
            for f in existing:
                print(f"   - {f}")
            response = input("   Clear? (y/N): ").strip().lower()
            if response != 'y':
                print("   [SKIP] Trade logs initialization")
                return False
    
    # Backup old logs (if exist)
    for log_file in log_files:
        log_path = logs_dir / log_file
        if log_path.exists():
            backup_path = logs_dir / f"{log_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"   Backup: {log_file} -> {backup_path.name}")
            shutil.move(str(log_path), str(backup_path))
    
    # Create empty log files
    for log_file in log_files:
        log_path = logs_dir / log_file
        log_path.touch()
    
    print(f"✅ Trade logs initialized")
    print(f"   Logs directory: {logs_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(description="Initialize AI Trader system data")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force initialization (no confirmation prompts)",
    )
    parser.add_argument(
        "--reset-portfolio",
        action="store_true",
        help="Reset Portfolio only",
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10000.0,
        help="Initial cash (default: 10000.0)",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(" AI Trader - Data Initialization")
    print("=" * 80)
    print()
    print(f"Initial cash: ${args.initial_cash:,.2f}")
    print()
    
    if args.reset_portfolio:
        # Reset Portfolio only
        init_portfolio(initial_cash=args.initial_cash, force=args.force)
    else:
        # Initialize all data
        print("📋 Will initialize the following:")
        print("   1. Portfolio state")
        print("   2. Memory directory")
        print("   3. Trade log files")
        print()
        
        if not args.force:
            response = input("⚠️  This will clear/reset existing data. Continue? (y/N): ").strip().lower()
            if response != 'y':
                print("\n❌ Cancelled")
                return 1
        
        results = []
        results.append(("Portfolio", init_portfolio(initial_cash=args.initial_cash, force=True)))
        results.append(("Memory", init_memory(force=True)))
        results.append(("Trade Logs", init_trade_logs(force=True)))
        
        print()
        print("=" * 80)
        print(" Initialization Complete")
        print("=" * 80)
        
        for name, success in results:
            status = "✅" if success else "⚠️"
            print(f"{status} {name}")
        
        print()
        print("💡 Tips:")
        print("   - You can now run trading cycle: python scripts/run_daily_trading.py")
        print("   - View monitoring: python scripts/run_monitoring_and_optimization.py")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ User cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

