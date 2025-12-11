#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
详细检查最新的对话记录
"""

import sys
import json
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logs_dir = Path("data/logs")

print("=" * 80)
print("详细检查最新的对话记录")
print("=" * 80)
print()

discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    # 找到最新的 5 条记录
    print("最新的 10 条记录:")
    print("-" * 80)
    recent = lines[-10:] if len(lines) >= 10 else lines
    for i, entry in enumerate(recent, 1):
        timestamp = entry.get("timestamp", "N/A")
        agent = entry.get("agent", "N/A")
        entry_type = entry.get("type", "N/A")
        print(f"{i}. [{timestamp}] {agent} ({entry_type})")
        if entry_type == "discussion":
            stance = entry.get("stance", "N/A")
            risk_score = entry.get("risk_score", "N/A")
            vix_risk_score = entry.get("vix_risk_score", "N/A")
            print(f"   Stance: {stance}, Risk Score: {risk_score}, VIX Risk Score: {vix_risk_score}")
        elif entry_type == "tool":
            tool_name = entry.get("tool_name", "N/A")
            print(f"   Tool: {tool_name}")
        print()
    
    # 找到最新的 Risk Analyst 记录
    print("=" * 80)
    print("最新的 Risk Analyst 记录:")
    print("-" * 80)
    risk_entries = [e for e in lines if e.get("agent") == "RiskAnalyst"]
    if risk_entries:
        latest_risk = risk_entries[-1]
        print(f"时间: {latest_risk.get('timestamp')}")
        print(f"类型: {latest_risk.get('type')}")
        print(f"Stance: {latest_risk.get('stance')}")
        print(f"Risk Score: {latest_risk.get('risk_score')}")
        print(f"VIX Risk Score: {latest_risk.get('vix_risk_score')}")
        print(f"VIX Level: {latest_risk.get('vix_level')}")
        print()
        
        # 检查 risk_report
        risk_report = latest_risk.get("risk_report", {})
        if risk_report:
            print("risk_report 字段:")
            for key in risk_report.keys():
                value = risk_report[key]
                if key == "tool_calls":
                    print(f"  {key}: {len(value) if isinstance(value, list) else 'N/A'} 项")
                    if isinstance(value, list) and value:
                        for tc in value:
                            tool_name = tc.get("tool", "unknown")
                            result = tc.get("result", {})
                            print(f"    - {tool_name}: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
                elif key == "tools_used":
                    print(f"  {key}: {value}")
                elif isinstance(value, (dict, list)):
                    print(f"  {key}: {type(value).__name__} ({len(value) if isinstance(value, (dict, list)) else 'N/A'} 项)")
                else:
                    print(f"  {key}: {value}")
        else:
            print("  ⚠️  risk_report 不存在")
    else:
        print("  ⚠️  未找到 Risk Analyst 记录")
    
    # 找到最新的 Trader Agent 记录
    print()
    print("=" * 80)
    print("最新的 Trader Agent 记录:")
    print("-" * 80)
    trader_entries = [e for e in lines if e.get("agent") in ["TraderAgent", "Trader Agent"]]
    if trader_entries:
        latest_trader = trader_entries[-1]
        print(f"时间: {latest_trader.get('timestamp')}")
        print(f"类型: {latest_trader.get('type')}")
        print(f"Stance: {latest_trader.get('stance')}")
        print(f"VIX Risk: {latest_trader.get('vix_risk')}")
        summary = latest_trader.get('summary', '')
        if summary:
            print(f"Summary: {summary[:200]}...")
    else:
        print("  ⚠️  未找到 Trader Agent 记录")

print()
print("=" * 80)



