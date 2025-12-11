#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 VIX 工具调用记录
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
print("检查 VIX 工具调用记录")
print("=" * 80)
print()

discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    # 找到所有 VIX 工具调用
    vix_tools = [e for e in lines if e.get("tool_name") == "vix_term"]
    
    print(f"总共找到 {len(vix_tools)} 个 VIX 工具调用")
    print()
    
    # 找到 Risk Analyst 的 VIX 工具调用
    risk_vix_tools = [e for e in vix_tools if e.get("agent") == "RiskAnalyst"]
    
    print(f"Risk Analyst 的 VIX 工具调用: {len(risk_vix_tools)}")
    print()
    
    if risk_vix_tools:
        # 显示最近的几个
        recent = risk_vix_tools[-5:]
        for i, tool in enumerate(recent):
            print(f"{i+1}. 时间: {tool.get('timestamp')}")
            result = tool.get("tool_result", {})
            print(f"   VIX Level: {result.get('vix')}")
            print(f"   VIX Risk Score: {result.get('vix_risk_score')}")
            print()
    
    # 找到最新的 Risk Analyst 输出
    risk_entries = [e for e in lines if e.get("agent") == "RiskAnalyst" and e.get("type") == "discussion"]
    if risk_entries:
        latest_risk = risk_entries[-1]
        risk_time = latest_risk.get("timestamp")
        print(f"最新 Risk Analyst 输出时间: {risk_time}")
        
        # 找到时间最接近的工具调用
        if risk_time and risk_vix_tools:
            try:
                risk_dt = datetime.fromisoformat(risk_time.replace('Z', '+00:00'))
                closest_tool = None
                min_diff = float('inf')
                for tool in risk_vix_tools:
                    tool_time = tool.get("timestamp")
                    if tool_time:
                        try:
                            tool_dt = datetime.fromisoformat(tool_time.replace('Z', '+00:00'))
                            diff = abs((risk_dt - tool_dt).total_seconds())
                            if diff < min_diff:
                                min_diff = diff
                                closest_tool = tool
                        except:
                            pass
                
                if closest_tool:
                    print(f"最接近的工具调用 (时间差: {min_diff:.1f}秒):")
                    print(f"  时间: {closest_tool.get('timestamp')}")
                    result = closest_tool.get("tool_result", {})
                    print(f"  VIX Level: {result.get('vix')}")
                    print(f"  VIX Risk Score: {result.get('vix_risk_score')}")
                    
                    if min_diff < 300:  # 5分钟内
                        print(f"  ✅ 时间差合理，应该是同一次执行")
                    else:
                        print(f"  ⚠️  时间差较大 ({min_diff/60:.1f}分钟)，可能不是同一次执行")
            except:
                pass

print()
print("=" * 80)



