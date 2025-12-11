#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最新的 Risk Analyst 记录的详细信息
"""

import sys
import json
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

convo_file = Path("data/logs/discussion_actions.jsonl")

if not convo_file.exists():
    print("❌ discussion_actions.jsonl 不存在")
    sys.exit(1)

print("=" * 80)
print("检查最新的 Risk Analyst 记录")
print("=" * 80)
print()

# 读取所有记录
all_entries = []
with convo_file.open("r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            all_entries.append(entry)
        except json.JSONDecodeError:
            continue

# 筛选 Risk Analyst 的 discussion 类型记录
risk_analyst_entries = [
    e for e in all_entries
    if e.get("agent") == "RiskAnalyst" and e.get("type") == "discussion"
]

if not risk_analyst_entries:
    print("❌ 没有找到 Risk Analyst 记录")
    sys.exit(1)

# 获取最新的记录
latest = risk_analyst_entries[-1]

print(f"最新记录时间: {latest.get('timestamp')}")
print(f"日期: {latest.get('date')}")
print()

print("1. 直接字段:")
print("-" * 80)
print(f"  vix_risk_score: {latest.get('vix_risk_score')}")
print(f"  vix_level: {latest.get('vix_level')}")
print(f"  risk_score: {latest.get('risk_score')}")
print(f"  stance: {latest.get('stance')}")
print()

print("2. risk_report 字段:")
print("-" * 80)
risk_report = latest.get("risk_report", {})
if risk_report:
    print(f"  risk_report.vix_risk_score: {risk_report.get('vix_risk_score')}")
    print(f"  risk_report.vix_level: {risk_report.get('vix_level')}")
    print(f"  risk_report.vix_risk_source: {risk_report.get('vix_risk_source')}")
    print(f"  risk_report.risk_score: {risk_report.get('risk_score')}")
    print(f"  risk_report.overall_risk_level: {risk_report.get('overall_risk_level')}")
    print(f"  risk_report.tool_calls count: {len(risk_report.get('tool_calls', []))}")
    
    # 检查 tool_calls 中的 VIX 数据
    tool_calls = risk_report.get("tool_calls", [])
    vix_tools = [tc for tc in tool_calls if tc.get("tool") == "vix_term"]
    if vix_tools:
        print()
        print("  3. tool_calls 中的 VIX 数据:")
        print("-" * 80)
        for i, vix_tool in enumerate(vix_tools):
            result = vix_tool.get("result", {})
            # 处理嵌套结构
            actual_result = result
            while isinstance(actual_result, dict) and "ok" in actual_result and "result" in actual_result:
                actual_result = actual_result["result"]
            print(f"    VIX Tool {i+1}:")
            print(f"      vix: {actual_result.get('vix')}")
            print(f"      vix_risk_score: {actual_result.get('vix_risk_score')}")
else:
    print("  ❌ risk_report 为空或不存在")
print()

print("=" * 80)



