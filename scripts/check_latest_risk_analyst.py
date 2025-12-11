#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最新的 Risk Analyst 输出详情
"""

import sys
import json
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

logs_dir = Path("data/logs")

print("=" * 80)
print("检查最新的 Risk Analyst 输出详情")
print("=" * 80)
print()

discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    # 找到最新的 Risk Analyst 输出
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
            print("risk_report 详细内容:")
            print(f"  overall_risk_level: {risk_report.get('overall_risk_level')}")
            print(f"  risk_score: {risk_report.get('risk_score')}")
            print(f"  vix_risk_score: {risk_report.get('vix_risk_score')}")
            print(f"  vix_risk_source: {risk_report.get('vix_risk_source')}")
            print(f"  vix_level: {risk_report.get('vix_level')}")
            print()
            
            # 检查分析内容
            analysis = risk_report.get("analysis", "")
            if analysis:
                print(f"  分析内容: {analysis[:200]}...")
                print()
        
        # 检查工具调用
        tool_calls = [e for e in lines if e.get("agent") == "RiskAnalyst" and e.get("type") == "tool"]
        
        # 找到与最新 Risk Analyst 时间接近的工具调用
        risk_time = latest.get("timestamp")
        if risk_time:
            try:
                risk_dt = datetime.fromisoformat(risk_time.replace('Z', '+00:00'))
                
                # 找到时间最接近的工具调用
                closest_tool = None
                min_diff = float('inf')
                for tool_call in tool_calls:
                    tool_time = tool_call.get("timestamp")
                    if tool_time:
                        try:
                            tool_dt = datetime.fromisoformat(tool_time.replace('Z', '+00:00'))
                            diff = abs((risk_dt - tool_dt).total_seconds())
                            if diff < min_diff:
                                min_diff = diff
                                closest_tool = tool_call
                        except:
                            pass
                
                if closest_tool and min_diff < 300:  # 5分钟内
                    print(f"相关工具调用 (时间差: {min_diff:.1f}秒):")
                    print(f"  工具: {closest_tool.get('tool_name')}")
                    print(f"  时间: {closest_tool.get('timestamp')}")
                    tool_result = closest_tool.get("tool_result", {})
                    if isinstance(tool_result, dict):
                        print(f"  VIX Level: {tool_result.get('vix')}")
                        print(f"  VIX Risk Score: {tool_result.get('vix_risk_score')}")
                    print()
                else:
                    print("⚠️  未找到相关的工具调用（5分钟内）")
                    print()
            except:
                pass
        
        # 验证结果
        print("=" * 80)
        print("验证结果:")
        print("=" * 80)
        
        vix_risk_score = latest.get("vix_risk_score")
        risk_score = latest.get("risk_score")
        stance = latest.get("stance", "").lower()
        
        if vix_risk_score is None:
            print("❌ VIX Risk Score 为 None - 修复未生效")
            print("   可能原因:")
            print("   1. VIX API 调用失败")
            print("   2. vix_term_structure() 返回 None")
            print("   3. 数据未正确保存")
        else:
            print(f"✅ VIX Risk Score 有值: {vix_risk_score}")
            
            if vix_risk_score >= 6.0:
                if risk_score >= 5.0:
                    print(f"✅ Risk Score 正确反映 VIX 风险: {risk_score} >= 5.0")
                else:
                    print(f"❌ Risk Score 未正确反映 VIX 风险: {risk_score} < 5.0 (应该 >= 5.0)")
                
                if stance in ["medium", "medium-high", "high"]:
                    print(f"✅ Stance 正确反映风险: {stance}")
                elif stance == "low":
                    print(f"❌ Stance 仍然是 LOW，应该至少是 MEDIUM")
            elif vix_risk_score >= 4.0:
                if risk_score >= 3.5:
                    print(f"✅ Risk Score 正确反映 VIX 风险: {risk_score} >= 3.5")
                else:
                    print(f"⚠️  Risk Score 可能未完全反映 VIX 风险: {risk_score} < 3.5")
    else:
        print("⚠️  未找到 Risk Analyst 记录")

print()
print("=" * 80)



