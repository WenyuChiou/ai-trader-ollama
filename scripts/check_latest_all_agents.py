#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查最新的所有 Agent 输出
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
print("检查最新的所有 Agent 输出")
print("=" * 80)
print()

discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    # 找到最新的 Risk Analyst 和 Trader Agent 输出
    risk_entries = [e for e in lines if e.get("agent") == "RiskAnalyst" and e.get("type") == "discussion"]
    trader_entries = [e for e in lines if e.get("agent") in ["TraderAgent", "Trader Agent"] and e.get("type") == "discussion"]
    
    print("1. Risk Analyst 最新输出:")
    print("-" * 80)
    if risk_entries:
        latest_risk = risk_entries[-1]
        print(f"  时间: {latest_risk.get('timestamp')}")
        print(f"  Stance: {latest_risk.get('stance')}")
        print(f"  Risk Score: {latest_risk.get('risk_score')}")
        print(f"  VIX Risk Score: {latest_risk.get('vix_risk_score')}")
        print(f"  VIX Level: {latest_risk.get('vix_level')}")
        print()
        
        # 检查 risk_report
        risk_report = latest_risk.get("risk_report", {})
        if risk_report:
            print("  risk_report 内容:")
            print(f"    overall_risk_level: {risk_report.get('overall_risk_level')}")
            print(f"    risk_score: {risk_report.get('risk_score')}")
            print(f"    vix_risk_score: {risk_report.get('vix_risk_score')}")
            print(f"    vix_risk_source: {risk_report.get('vix_risk_source')}")
            print(f"    vix_level: {risk_report.get('vix_level')}")
    else:
        print("  ⚠️  未找到 Risk Analyst 记录")
    
    print()
    print("2. Trader Agent 最新输出:")
    print("-" * 80)
    if trader_entries:
        latest_trader = trader_entries[-1]
        print(f"  时间: {latest_trader.get('timestamp')}")
        print(f"  Stance: {latest_trader.get('stance')}")
        print(f"  VIX Risk: {latest_trader.get('vix_risk')}")
        print(f"  Summary: {latest_trader.get('summary', '')[:200]}...")
    else:
        print("  ⚠️  未找到 Trader Agent 记录")
    
    print()
    print("3. 验证结果:")
    print("-" * 80)
    
    if risk_entries:
        latest_risk = risk_entries[-1]
        risk_score = latest_risk.get("risk_score")
        vix_risk_score = latest_risk.get("vix_risk_score")
        stance = latest_risk.get("stance", "").lower()
        
        print("  Risk Analyst:")
        if vix_risk_score is None:
            print("    ❌ VIX Risk Score 为 None - 修复未生效")
        else:
            print(f"    ✅ VIX Risk Score 有值: {vix_risk_score}")
            
            if vix_risk_score >= 6.0:
                if risk_score >= 5.0:
                    print(f"    ✅ Risk Score 正确: {risk_score} >= 5.0")
                else:
                    print(f"    ❌ Risk Score 不正确: {risk_score} < 5.0 (应该 >= 5.0)")
                
                if stance in ["medium", "medium-high", "high"]:
                    print(f"    ✅ Stance 正确: {stance}")
                else:
                    print(f"    ❌ Stance 不正确: {stance} (应该是至少 MEDIUM)")
    
    if trader_entries:
        latest_trader = trader_entries[-1]
        vix_risk = latest_trader.get("vix_risk")
        print()
        print("  Trader Agent:")
        if vix_risk is not None:
            print(f"    ✅ VIX Risk 有值: {vix_risk}")
        else:
            print(f"    ⚠️  VIX Risk 为 None")

print()
print("=" * 80)



