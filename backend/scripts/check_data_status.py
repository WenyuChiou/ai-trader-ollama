#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查系统数据状态：chat历史、持仓信息、净值记录等
"""
import json
import sys
import io
from pathlib import Path
from datetime import date, datetime
from collections import defaultdict

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = Path(__file__).resolve().parents[2]
LOGS_DIR = ROOT / "data" / "logs"

def check_portfolio():
    """检查持仓信息"""
    print("\n" + "="*80)
    print("📊 Portfolio State")
    print("="*80)
    
    portfolio_file = LOGS_DIR / "portfolio_state.json"
    if not portfolio_file.exists():
        print("❌ Portfolio state file not found")
        return
    
    data = json.loads(portfolio_file.read_text(encoding="utf-8"))
    
    cash = data.get("cash", 0)
    initial_value = data.get("initial_value", 0)
    total_value = data.get("total_value", 0)
    positions = data.get("positions", {})
    snapshot = data.get("snapshot", {})
    
    print(f"✅ File exists: {portfolio_file}")
    print(f"💰 Cash: ${cash:.2f}")
    print(f"📈 Initial Value: ${initial_value:.2f}")
    print(f"💵 Total Value: ${total_value:.2f}")
    print(f"📊 Equity Value: ${total_value - cash:.2f}")
    print(f"📉 Total P&L: ${total_value - initial_value:.2f} ({(total_value - initial_value) / initial_value * 100:.2f}%)")
    print(f"\n📦 Positions: {len(positions)}")
    
    total_position_value = 0
    for symbol, pos in positions.items():
        qty = pos.get("quantity", 0)
        avg_cost = pos.get("avg_cost", 0)
        total_cost = pos.get("total_cost", 0)
        market_value = qty * avg_cost  # 使用avg_cost作为近似值
        total_position_value += market_value
        print(f"  {symbol:6s}: {qty:4d} shares @ ${avg_cost:8.2f} avg, Cost=${total_cost:10.2f}")
    
    print(f"\n💼 Total Position Value: ${total_position_value:.2f}")
    print(f"💵 Cash + Positions: ${cash + total_position_value:.2f}")
    
    if snapshot:
        snapshot_total = snapshot.get("total_value", 0)
        snapshot_equity = snapshot.get("equity_value", 0)
        snapshot_cash = snapshot.get("cash", cash)
        print(f"\n📸 Snapshot:")
        print(f"  Total Value: ${snapshot_total:.2f}")
        print(f"  Equity Value: ${snapshot_equity:.2f}")
        print(f"  Cash: ${snapshot_cash:.2f}")
        print(f"  Consistency: {'✅' if abs(snapshot_total - (snapshot_cash + snapshot_equity)) < 0.01 else '❌'} (diff: ${abs(snapshot_total - (snapshot_cash + snapshot_equity)):.2f})")

def check_discussion_actions():
    """检查讨论历史记录"""
    print("\n" + "="*80)
    print("💬 Discussion Actions")
    print("="*80)
    
    discussion_file = LOGS_DIR / "discussion_actions.jsonl"
    if not discussion_file.exists():
        print("❌ Discussion actions file not found")
        return
    
    lines = discussion_file.read_text(encoding="utf-8").strip().split("\n")
    print(f"✅ File exists: {discussion_file}")
    print(f"📝 Total records: {len(lines)}")
    
    # 统计今天的记录
    today = date.today().isoformat()
    today_records = []
    analysts = defaultdict(int)
    
    for line in lines:
        try:
            data = json.loads(line)
            record_date = data.get("date", "")
            if record_date.startswith(today):
                today_records.append(data)
            # 统计analyst（可能是agent字段）
            analyst = data.get("analyst") or data.get("agent", "Unknown")
            analysts[analyst] += 1
        except:
            pass
    
    print(f"\n📅 Today ({today}) records: {len(today_records)}")
    print("📊 By analyst:")
    for analyst, count in sorted(analysts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {analyst}: {count} records")
    
    print(f"\n📋 Last 5 records:")
    for i, line in enumerate(lines[-5:] if len(lines) > 5 else lines):
        try:
            data = json.loads(line)
            analyst = data.get("analyst") or data.get("agent", "Unknown")
            record_date = data.get("date", "N/A")
            summary = data.get("summary", data.get("content", ""))[:80]
            print(f"  {i+1}. {analyst} ({record_date}): {summary}...")
        except Exception as e:
            print(f"  {i+1}. [Parse error: {e}]")

def check_equity_history():
    """检查净值历史记录"""
    print("\n" + "="*80)
    print("📈 Equity History")
    print("="*80)
    
    equity_file = LOGS_DIR / "equity_history.jsonl"
    if not equity_file.exists():
        print("❌ Equity history file not found")
        return
    
    lines = equity_file.read_text(encoding="utf-8").strip().split("\n")
    print(f"✅ File exists: {equity_file}")
    print(f"📊 Total records: {len(lines)}")
    
    # 统计今天的记录
    today = date.today().isoformat()
    today_records = [json.loads(l) for l in lines if json.loads(l).get("date", "").startswith(today)]
    print(f"📅 Today ({today}) records: {len(today_records)}")
    
    print(f"\n📋 Last 5 records:")
    for i, line in enumerate(lines[-5:] if len(lines) > 5 else lines):
        try:
            data = json.loads(line)
            date_str = data.get("date", "N/A")
            timestamp = data.get("timestamp", "N/A")[:19] if len(data.get("timestamp", "")) > 19 else data.get("timestamp", "N/A")
            total_value = data.get("total_value", 0)
            cash = data.get("cash", 0)
            equity_value = data.get("equity_value", 0)
            print(f"  {i+1}. {date_str} {timestamp}: Total=${total_value:.2f}, Cash=${cash:.2f}, Equity=${equity_value:.2f}")
        except Exception as e:
            print(f"  {i+1}. [Parse error: {e}]")

def check_filled_orders():
    """检查已成交订单"""
    print("\n" + "="*80)
    print("✅ Filled Orders")
    print("="*80)
    
    filled_file = LOGS_DIR / "filled_orders.jsonl"
    if not filled_file.exists():
        print("❌ Filled orders file not found")
        return
    
    lines = filled_file.read_text(encoding="utf-8").strip().split("\n")
    print(f"✅ File exists: {filled_file}")
    print(f"📊 Total records: {len(lines)}")
    
    # 统计今天的记录
    today = date.today().isoformat()
    today_records = [json.loads(l) for l in lines if json.loads(l).get("date", "").startswith(today)]
    print(f"📅 Today ({today}) records: {len(today_records)}")
    
    # 统计买卖订单
    buy_count = sum(1 for r in today_records if r.get("action", "").upper() == "BUY")
    sell_count = sum(1 for r in today_records if r.get("action", "").upper() == "SELL")
    print(f"  Buy orders: {buy_count}")
    print(f"  Sell orders: {sell_count}")
    
    print(f"\n📋 Last 5 records:")
    for i, line in enumerate(lines[-5:] if len(lines) > 5 else lines):
        try:
            data = json.loads(line)
            record_date = data.get("date", "N/A")
            action = data.get("action", "N/A")
            symbol = data.get("symbol", "N/A")
            quantity = data.get("quantity", 0)
            price = data.get("price", 0)
            print(f"  {i+1}. {record_date} {action} {symbol} x{quantity} @ ${price:.2f}")
        except Exception as e:
            print(f"  {i+1}. [Parse error: {e}]")

def check_memory_files():
    """检查记忆文件"""
    print("\n" + "="*80)
    print("🧠 Memory Files")
    print("="*80)
    
    memory_dir = LOGS_DIR / "memory" / "daily"
    if not memory_dir.exists():
        print("❌ Memory directory not found")
        return
    
    files = sorted(memory_dir.glob("*.json"), reverse=True)
    print(f"✅ Directory exists: {memory_dir}")
    print(f"📊 Total memory files: {len(files)}")
    
    print(f"\n📋 Last 5 memory files:")
    for i, f in enumerate(files[:5]):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            date_str = data.get("date", f.stem)
            discussion = data.get("discussion", {})
            stance = discussion.get("final_stance", "N/A")
            decision = data.get("decision", {})
            buy_count = len(decision.get("buy_orders", []))
            sell_count = len(decision.get("sell_orders", []))
            portfolio_snapshot = data.get("portfolio_snapshot", {})
            portfolio_value = portfolio_snapshot.get("total_value", 0)
            print(f"  {i+1}. {date_str}: Stance={stance}, Buy={buy_count}, Sell={sell_count}, Portfolio=${portfolio_value:.2f}")
        except Exception as e:
            print(f"  {i+1}. {f.name}: [Parse error: {e}]")

def main():
    """主函数"""
    print("="*80)
    print("🔍 System Data Status Check")
    print("="*80)
    print(f"📁 Logs directory: {LOGS_DIR}")
    
    check_portfolio()
    check_discussion_actions()
    check_equity_history()
    check_filled_orders()
    check_memory_files()
    
    print("\n" + "="*80)
    print("✅ Check completed")
    print("="*80)

if __name__ == "__main__":
    main()

