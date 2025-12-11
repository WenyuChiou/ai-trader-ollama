#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 risk_report 中的 tool_calls
"""

import sys
import json
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

logs_dir = Path("data/logs")

print("=" * 80)
print("检查 risk_report 中的 tool_calls")
print("=" * 80)
print()

discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    risk_entries = [e for e in lines if e.get("agent") == "RiskAnalyst" and e.get("type") == "discussion"]
    
    if risk_entries:
        latest = risk_entries[-1]
        print(f"最新 Risk Analyst 输出:")
        print(f"  时间: {latest.get('timestamp')}")
        print()
        
        risk_report = latest.get("risk_report", {})
        if risk_report:
            print("risk_report 内容:")
            print(f"  tools_used: {risk_report.get('tools_used')}")
            tool_calls = risk_report.get("tool_calls", [])
            print(f"  tool_calls count: {len(tool_calls) if tool_calls else 0}")
            
            if tool_calls:
                print()
                print("  tool_calls 详情:")
                for i, tc in enumerate(tool_calls):
                    tool_name = tc.get("tool", "unknown")
                    result = tc.get("result", {})
                    print(f"    {i+1}. {tool_name}")
                    if tool_name == "vix_term":
                        print(f"       VIX Level: {result.get('vix')}")
                        print(f"       VIX Risk Score: {result.get('vix_risk_score')}")
            else:
                print()
                print("  ⚠️  tool_calls 为空或不存在")
                print(f"  risk_report keys: {list(risk_report.keys())[:20]}")
        else:
            print("  ⚠️  risk_report 不存在")

print()
print("=" * 80)



