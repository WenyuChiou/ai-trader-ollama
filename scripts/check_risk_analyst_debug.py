#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 Risk Analyst 的调试信息
"""

import sys
import json
from pathlib import Path

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

logs_dir = Path("data/logs")

print("=" * 80)
print("检查 Risk Analyst 调试信息")
print("=" * 80)
print()

# 检查最新的 Risk Analyst 输出
discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    risk_entries = [e for e in lines if e.get("agent") == "RiskAnalyst" and e.get("type") == "discussion"]
    
    if risk_entries:
        latest = risk_entries[-1]
        print("最新 Risk Analyst 输出:")
        print(f"  时间: {latest.get('timestamp')}")
        print(f"  Stance: {latest.get('stance')}")
        print(f"  Risk Score: {latest.get('risk_score')}")
        print(f"  VIX Risk Score: {latest.get('vix_risk_score')}")
        print(f"  VIX Level: {latest.get('vix_level')}")
        print()
        
        # 检查 risk_report
        risk_report = latest.get("risk_report", {})
        if risk_report:
            print("risk_report 内容:")
            print(f"  overall_risk_level: {risk_report.get('overall_risk_level')}")
            print(f"  risk_score: {risk_report.get('risk_score')}")
            print(f"  vix_risk_score: {risk_report.get('vix_risk_score')}")
            print(f"  vix_risk_source: {risk_report.get('vix_risk_source')}")
            print(f"  vix_level: {risk_report.get('vix_level')}")
            print()
        
        # 检查工具调用
        tool_calls = [e for e in lines if e.get("agent") == "RiskAnalyst" and e.get("type") == "tool"]
        vix_tool_calls = [e for e in tool_calls if e.get("tool_name") == "vix_term"]
        
        if vix_tool_calls:
            latest_vix_tool = vix_tool_calls[-1]
            print("最新 VIX 工具调用:")
            print(f"  时间: {latest_vix_tool.get('timestamp')}")
            tool_result = latest_vix_tool.get("tool_result", {})
            print(f"  VIX Level: {tool_result.get('vix')}")
            print(f"  VIX Risk Score: {tool_result.get('vix_risk_score')}")
            print()
        else:
            print("⚠️  未找到 VIX 工具调用记录")
            print()
        
        # 检查时间差
        risk_time = latest.get("timestamp")
        if risk_time and vix_tool_calls:
            vix_time = vix_tool_calls[-1].get("timestamp")
            if risk_time and vix_time:
                from datetime import datetime
                try:
                    risk_dt = datetime.fromisoformat(risk_time.replace('Z', '+00:00'))
                    vix_dt = datetime.fromisoformat(vix_time.replace('Z', '+00:00'))
                    diff = (risk_dt - vix_dt).total_seconds()
                    print(f"时间差: Risk Analyst ({risk_time}) 和 VIX 工具调用 ({vix_time}) 相差 {diff:.1f} 秒")
                    if abs(diff) > 60:
                        print("  ⚠️  时间差较大，可能不是同一次执行")
                except:
                    pass
    else:
        print("⚠️  未找到 Risk Analyst 记录")

print()
print("=" * 80)
print("检查完成")
print("=" * 80)



