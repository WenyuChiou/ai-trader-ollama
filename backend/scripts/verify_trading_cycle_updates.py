#!/usr/bin/env python3
"""
验证 Trading Cycle 更新是否生效
检查数据文件是否包含新格式的数据
"""
import json
from pathlib import Path
from datetime import datetime, timezone

# 获取项目根目录
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
logs_dir = project_root / "data" / "logs"
jsonl_file = logs_dir / "discussion_actions.jsonl"

# Fix encoding for Windows console
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("=" * 80)
print("TRADING CYCLE Update Verification")
print("=" * 80)
print(f"\n检查文件: {jsonl_file}")
print(f"文件存在: {jsonl_file.exists()}\n")

if not jsonl_file.exists():
    print("❌ 文件不存在！")
    exit(1)

# 读取所有行
with jsonl_file.open('r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"总行数: {len(lines)}\n")

# 分析最后50条
print("=" * 80)
print("最后50条条目分析:")
print("=" * 80)

stats = {
    "RiskAnalyst": [],
    "DiscussionRound_1": [],
    "DiscussionRound_2": [],
    "DiscussionRound_3": [],
    "TraderAgent_with_decision": [],
    "TraderAgent_without_decision": [],
    "DiscussionCoordinator_round0": [],
    "Other": []
}

for i, line in enumerate(lines[-50:], 1):
    try:
        entry = json.loads(line.strip())
        agent = entry.get("agent", "Unknown")
        round_num = entry.get("round", 0)
        date = entry.get("date", "Unknown")
        timestamp = entry.get("timestamp", "")
        
        # 计算时间差（如果是最近的）
        age_str = ""
        if timestamp:
            try:
                entry_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                now = datetime.now(timezone.utc)
                age = now - entry_time
                if age.days > 0:
                    age_str = f" ({age.days}天前)"
                elif age.seconds >= 3600:
                    age_str = f" ({age.seconds // 3600}小时前)"
                elif age.seconds >= 60:
                    age_str = f" ({age.seconds // 60}分钟前)"
                else:
                    age_str = f" (刚刚)"
            except:
                pass
        
        if agent == "RiskAnalyst":
            stats["RiskAnalyst"].append({
                "date": date,
                "round": round_num,
                "has_risk_report": "risk_report" in entry,
                "age": age_str
            })
            print(f"\n{i}. ✅ RiskAnalyst (round: {round_num}, date: {date}{age_str})")
            if "risk_report" in entry:
                risk_report = entry.get("risk_report", {})
                risk_level = risk_report.get("overall_risk_level", risk_report.get("risk_level", "N/A"))
                risk_score = risk_report.get("risk_score", "N/A")
                print(f"   - risk_report: ✅ Yes (risk_level: {risk_level}, risk_score: {risk_score})")
            else:
                print(f"   - risk_report: ❌ Missing")
        elif agent == "DiscussionCoordinator":
            if round_num == 1:
                stats["DiscussionRound_1"].append({"date": date, "age": age_str})
                print(f"\n{i}. ✅ Discussion Round 1 (date: {date}{age_str})")
            elif round_num == 2:
                stats["DiscussionRound_2"].append({"date": date, "age": age_str})
                print(f"\n{i}. ✅ Discussion Round 2 (date: {date}{age_str})")
            elif round_num == 3:
                stats["DiscussionRound_3"].append({"date": date, "age": age_str})
                print(f"\n{i}. ✅ Discussion Round 3 (date: {date}{age_str})")
            elif round_num == 0:
                stats["DiscussionCoordinator_round0"].append({"date": date, "age": age_str})
                print(f"\n{i}. ⚠️  DiscussionCoordinator (round=0, date: {date}{age_str}) - 旧格式")
        elif agent == "TraderAgent":
            if "decision" in entry:
                stats["TraderAgent_with_decision"].append({
                    "date": date,
                    "has_buy_orders": "buy_orders" in entry.get("decision", {}),
                    "has_sell_orders": "sell_orders" in entry.get("decision", {}),
                    "age": age_str
                })
                print(f"\n{i}. ✅ TraderAgent (date: {date}{age_str})")
                decision = entry.get("decision", {})
                buy_count = len(decision.get("buy_orders", []))
                sell_count = len(decision.get("sell_orders", []))
                print(f"   - decision: ✅ Yes (buy_orders: {buy_count}, sell_orders: {sell_count})")
                print(f"   - buy_orders_count: {entry.get('buy_orders_count', 'N/A')}")
                print(f"   - sell_orders_count: {entry.get('sell_orders_count', 'N/A')}")
            else:
                stats["TraderAgent_without_decision"].append({"date": date, "age": age_str})
                print(f"\n{i}. ⚠️  TraderAgent (date: {date}{age_str}) - 缺少 decision 字段")
        else:
            stats["Other"].append({"agent": agent, "date": date, "age": age_str})
    except Exception as e:
        print(f"\n{i}. ❌ Error parsing line: {e}")

print("\n" + "=" * 80)
print("统计摘要:")
print("=" * 80)
print(f"RiskAnalyst 条目: {len(stats['RiskAnalyst'])}")
print(f"  - 有 risk_report: {sum(1 for s in stats['RiskAnalyst'] if s.get('has_risk_report'))}")
print(f"Discussion Round 1 条目: {len(stats['DiscussionRound_1'])}")
print(f"Discussion Round 2 条目: {len(stats['DiscussionRound_2'])}")
print(f"Discussion Round 3 条目: {len(stats['DiscussionRound_3'])}")
print(f"DiscussionCoordinator (round=0): {len(stats['DiscussionCoordinator_round0'])} - 旧格式")
print(f"TraderAgent (有 decision): {len(stats['TraderAgent_with_decision'])}")
print(f"TraderAgent (无 decision): {len(stats['TraderAgent_without_decision'])} - 旧格式")
print(f"其他条目: {len(stats['Other'])}")

print("\n" + "=" * 80)
print("诊断结果:")
print("=" * 80)

issues = []
if len(stats['RiskAnalyst']) == 0:
    issues.append("❌ 没有 RiskAnalyst 条目 - 后端可能未重启或写入失败")
if len(stats['DiscussionRound_1']) == 0 and len(stats['DiscussionRound_2']) == 0 and len(stats['DiscussionRound_3']) == 0:
    issues.append("❌ 没有 Discussion Round 1/2/3 条目 - 后端可能未重启或写入失败")
if len(stats['TraderAgent_with_decision']) == 0:
    issues.append("❌ 没有 TraderAgent (有 decision) 条目 - 后端可能未重启或写入失败")

if len(stats['DiscussionCoordinator_round0']) > 0 and len(stats['DiscussionRound_1']) == 0:
    issues.append("⚠️  只有旧格式的 DiscussionCoordinator (round=0)，没有新格式的 Round 1/2/3")

if len(stats['TraderAgent_without_decision']) > 0:
    issues.append("⚠️  有旧格式的 TraderAgent (无 decision 字段)")

if issues:
    print("\n发现的问题:")
    for issue in issues:
        print(f"  {issue}")
    print("\n建议:")
    print("  1. 重启后端服务器")
    print("  2. 执行新的交易循环")
    print("  3. 再次运行此脚本验证")
else:
    print("\n✅ 所有新格式数据都已找到！")
    print("  - RiskAnalyst 条目存在")
    print("  - Discussion Round 1/2/3 条目存在")
    print("  - TraderAgent (有 decision) 条目存在")
    print("\n如果前端仍显示旧版本，请：")
    print("  1. 强制刷新浏览器 (Ctrl+F5)")
    print("  2. 检查浏览器控制台，确认 API 返回的数据格式")

print("\n" + "=" * 80)
print("最近的数据:")
print("=" * 80)

# 显示最近的数据（按时间排序）
recent_entries = []
for line in lines[-20:]:
    try:
        entry = json.loads(line.strip())
        agent = entry.get("agent", "Unknown")
        round_num = entry.get("round", 0)
        timestamp = entry.get("timestamp", "")
        if timestamp:
            try:
                entry_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                recent_entries.append((entry_time, agent, round_num, entry))
            except:
                pass
    except:
        pass

recent_entries.sort(key=lambda x: x[0], reverse=True)

print("\n最近10条（按时间排序）:")
for i, (entry_time, agent, round_num, entry) in enumerate(recent_entries[:10], 1):
    age = datetime.now(timezone.utc) - entry_time
    if age.days > 0:
        age_str = f"{age.days}天前"
    elif age.seconds >= 3600:
        age_str = f"{age.seconds // 3600}小时前"
    elif age.seconds >= 60:
        age_str = f"{age.seconds // 60}分钟前"
    else:
        age_str = "刚刚"
    
    print(f"{i}. {agent} (round: {round_num}) - {age_str}")
    if agent == "RiskAnalyst" and "risk_report" in entry:
        print(f"   ✅ 包含 risk_report")
    elif agent == "TraderAgent" and "decision" in entry:
        print(f"   ✅ 包含 decision")
    elif agent == "DiscussionCoordinator" and round_num > 0:
        print(f"   ✅ Round {round_num} 条目")
