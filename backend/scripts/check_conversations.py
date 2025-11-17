#!/usr/bin/env python3
"""
检查 discussion_actions.jsonl 文件内容，确认是否有新格式的数据
"""
import json
from pathlib import Path

# 获取项目根目录
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
logs_dir = project_root / "data" / "logs"
jsonl_file = logs_dir / "discussion_actions.jsonl"

print(f"Checking: {jsonl_file}")
print(f"File exists: {jsonl_file.exists()}\n")

if not jsonl_file.exists():
    print("❌ File not found!")
    exit(1)

# 读取最后50行
with jsonl_file.open('r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines: {len(lines)}\n")
print("=" * 80)
print("Last 20 entries:")
print("=" * 80)

# 分析最后20条
stats = {
    "RiskAnalyst": 0,
    "DiscussionRound": 0,
    "TraderAgent": 0,
    "DiscussionCoordinator_round0": 0,
    "DiscussionCoordinator_round123": 0,
    "Other": 0
}

for i, line in enumerate(lines[-20:], 1):
    try:
        entry = json.loads(line.strip())
        agent = entry.get("agent", "Unknown")
        round_num = entry.get("round", 0)
        date = entry.get("date", "Unknown")
        
        print(f"\n{i}. {agent} (round: {round_num}, date: {date})")
        
        if agent == "RiskAnalyst":
            stats["RiskAnalyst"] += 1
            risk_report = entry.get("risk_report", {})
            print(f"   ✅ RiskAnalyst entry found")
            print(f"   - risk_report: {'Yes' if risk_report else 'No'}")
        elif agent == "DiscussionCoordinator":
            if round_num > 0:
                stats["DiscussionCoordinator_round123"] += 1
                print(f"   ✅ Discussion Round {round_num} entry found")
            else:
                stats["DiscussionCoordinator_round0"] += 1
                print(f"   ⚠️  DiscussionCoordinator with round=0 (old format)")
        elif agent == "TraderAgent":
            stats["TraderAgent"] += 1
            decision = entry.get("decision", {})
            print(f"   ✅ TraderAgent entry found")
            print(f"   - decision: {'Yes' if decision else 'No'}")
            print(f"   - buy_orders_count: {entry.get('buy_orders_count', 'N/A')}")
            print(f"   - sell_orders_count: {entry.get('sell_orders_count', 'N/A')}")
        else:
            stats["Other"] += 1
    except Exception as e:
        print(f"   ❌ Error parsing line: {e}")

print("\n" + "=" * 80)
print("Summary:")
print("=" * 80)
print(f"RiskAnalyst entries: {stats['RiskAnalyst']}")
print(f"Discussion Round 1/2/3 entries: {stats['DiscussionCoordinator_round123']}")
print(f"DiscussionCoordinator (round=0): {stats['DiscussionCoordinator_round0']}")
print(f"TraderAgent entries: {stats['TraderAgent']}")
print(f"Other entries: {stats['Other']}")

print("\n" + "=" * 80)
print("Diagnosis:")
print("=" * 80)

if stats['RiskAnalyst'] == 0:
    print("❌ No RiskAnalyst entries found - backend may not have restarted")
if stats['DiscussionCoordinator_round123'] == 0:
    print("❌ No Discussion Round 1/2/3 entries found - backend may not have restarted")
if stats['TraderAgent'] == 0:
    print("❌ No TraderAgent entries found")
elif stats['TraderAgent'] > 0:
    # Check if TraderAgent has decision field
    traider_entries = [json.loads(line) for line in lines[-20:] if json.loads(line).get("agent") == "TraderAgent"]
    if traider_entries and not traider_entries[0].get("decision"):
        print("⚠️  TraderAgent entries exist but missing 'decision' field - may be old format")

if stats['RiskAnalyst'] > 0 and stats['DiscussionCoordinator_round123'] > 0:
    print("✅ New format data found - backend has been updated!")
else:
    print("⚠️  Old format data detected - please restart backend server and run a new trading cycle")

