#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化系统数据
- 初始化 Portfolio（重置为初始资金）
- 清空或初始化 Memory
- 清空交易记录
- 初始化 Equity Tracker

使用方式:
    python scripts/init_data.py              # 初始化所有数据（会询问确认）
    python scripts/init_data.py --force     # 强制初始化（不询问）
    python scripts/init_data.py --reset-portfolio  # 只重置 Portfolio
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
    """初始化 Portfolio 状态"""
    state_file = ROOT / "data" / "logs" / "portfolio_state.json"
    
    if state_file.exists() and not force:
        print(f"\n⚠️  Portfolio 状态文件已存在: {state_file}")
        print(f"   初始资金: ${initial_cash:,.2f}")
        response = input("   是否重置? (y/N): ").strip().lower()
        if response != 'y':
            print("   [跳过] Portfolio 初始化")
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
    
    print(f"✅ Portfolio 已初始化")
    print(f"   文件: {state_file}")
    print(f"   初始资金: ${initial_cash:,.2f}")
    return True


def init_memory(force: bool = False) -> bool:
    """初始化 Memory 目录"""
    memory_dir = ROOT / "data" / "logs" / "memory"
    
    if memory_dir.exists() and not force:
        print(f"\n⚠️  Memory 目录已存在: {memory_dir}")
        print(f"   包含 {len(list(memory_dir.rglob('*.json')))} 个记忆文件")
        response = input("   是否清空? (y/N): ").strip().lower()
        if response != 'y':
            print("   [跳过] Memory 初始化")
            return False
    
    # 备份旧数据（如果存在）
    if memory_dir.exists():
        backup_dir = ROOT / "data" / "logs" / f"memory_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\n📦 备份旧 Memory 到: {backup_dir}")
        shutil.move(str(memory_dir), str(backup_dir))
    
    # 创建新目录结构
    memory_dir.mkdir(parents=True, exist_ok=True)
    (memory_dir / "daily").mkdir(exist_ok=True)
    (memory_dir / "weekly").mkdir(exist_ok=True)
    (memory_dir / "monthly").mkdir(exist_ok=True)
    (memory_dir / "index").mkdir(exist_ok=True)
    
    # 初始化索引文件
    index_file = memory_dir / "index" / "daily_index.json"
    index_data = {
        "initialized_at": datetime.now().isoformat(),
        "entries": [],
    }
    with index_file.open("w", encoding="utf-8") as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Memory 已初始化")
    print(f"   目录: {memory_dir}")
    return True


def init_trade_logs(force: bool = False) -> bool:
    """初始化交易记录"""
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
            print(f"\n⚠️  以下日志文件已存在:")
            for f in existing:
                print(f"   - {f}")
            response = input("   是否清空? (y/N): ").strip().lower()
            if response != 'y':
                print("   [跳过] 交易记录初始化")
                return False
    
    # 备份旧日志（如果存在）
    for log_file in log_files:
        log_path = logs_dir / log_file
        if log_path.exists():
            backup_path = logs_dir / f"{log_file}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"   备份: {log_file} -> {backup_path.name}")
            shutil.move(str(log_path), str(backup_path))
    
    # 创建空的日志文件
    for log_file in log_files:
        log_path = logs_dir / log_file
        log_path.touch()
    
    print(f"✅ 交易记录已初始化")
    print(f"   日志目录: {logs_dir}")
    return True


def main():
    parser = argparse.ArgumentParser(description="初始化 AI Trader 系统数据")
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制初始化（不询问确认）",
    )
    parser.add_argument(
        "--reset-portfolio",
        action="store_true",
        help="只重置 Portfolio",
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10000.0,
        help="初始资金（默认: 10000.0）",
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print(" AI Trader - 数据初始化")
    print("=" * 80)
    print()
    print(f"初始资金: ${args.initial_cash:,.2f}")
    print()
    
    if args.reset_portfolio:
        # 只重置 Portfolio
        init_portfolio(initial_cash=args.initial_cash, force=args.force)
    else:
        # 初始化所有数据
        print("📋 将初始化以下内容:")
        print("   1. Portfolio 状态")
        print("   2. Memory 目录")
        print("   3. 交易记录日志")
        print()
        
        if not args.force:
            response = input("⚠️  这将会清空/重置现有数据，是否继续? (y/N): ").strip().lower()
            if response != 'y':
                print("\n❌ 已取消")
                return 1
        
        results = []
        results.append(("Portfolio", init_portfolio(initial_cash=args.initial_cash, force=True)))
        results.append(("Memory", init_memory(force=True)))
        results.append(("Trade Logs", init_trade_logs(force=True)))
        
        print()
        print("=" * 80)
        print(" 初始化完成")
        print("=" * 80)
        
        for name, success in results:
            status = "✅" if success else "⚠️"
            print(f"{status} {name}")
        
        print()
        print("💡 提示:")
        print("   - 现在可以运行交易循环: python scripts/run_daily_trading.py")
        print("   - 查看监控: python scripts/run_monitoring_and_optimization.py")
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

