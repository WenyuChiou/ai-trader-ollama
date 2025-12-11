#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际验证修复是否生效 - 检查 API 日志和实际执行
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent.parent / "backend" / "src"))

logs_dir = Path("data/logs")

print("=" * 80)
print("实际验证修复是否生效")
print("=" * 80)
print()

# 1. 检查 Risk Analyst 是否调用了 VIX API
print("1. 检查 Risk Analyst 是否调用了 VIX API")
print("-" * 80)

discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    # 查找 Risk Analyst 的工具调用
    risk_tool_calls = [e for e in lines if e.get("agent") == "RiskAnalyst" and e.get("type") == "tool" and e.get("tool_name") == "vix_term"]
    
    if risk_tool_calls:
        latest_tool = risk_tool_calls[-1]
        print(f"   ✅ 找到 VIX API 调用:")
        print(f"      时间: {latest_tool.get('timestamp')}")
        tool_result = latest_tool.get("tool_result", {})
        vix_level = tool_result.get("vix")
        vix_risk = tool_result.get("vix_risk_score")
        print(f"      VIX Level: {vix_level}")
        print(f"      VIX Risk Score: {vix_risk}")
        
        if vix_risk is not None:
            print(f"      ✅ VIX API 调用成功，获取到 risk_score={vix_risk:.1f}")
        else:
            print(f"      ⚠️  VIX API 调用成功，但 risk_score 为 None")
    else:
        print(f"   ❌ 未找到 VIX API 调用记录")
        print(f"      可能原因:")
        print(f"        1. Risk Analyst 未调用 vix_term 工具")
        print(f"        2. 工具调用未记录到 conversation")
        print(f"        3. 需要执行一次新的 trading cycle")

print()

# 2. 检查 Risk Analyst 的 risk_score 是否被强制调整
print("2. 检查 Risk Analyst 的 risk_score 是否被强制调整")
print("-" * 80)

risk_entries = [e for e in lines if e.get("agent") == "RiskAnalyst" and e.get("type") == "discussion"]
if risk_entries:
    latest = risk_entries[-1]
    risk_score = latest.get("risk_score")
    vix_risk_score = latest.get("vix_risk_score")
    stance = latest.get("stance", "")
    
    print(f"   最新 Risk Analyst 输出:")
    print(f"     时间: {latest.get('timestamp')}")
    print(f"     Stance: {stance}")
    print(f"     Risk Score: {risk_score}")
    print(f"     VIX Risk Score: {vix_risk_score}")
    
    if risk_score is None:
        print(f"     ❌ risk_score 为 None - 数据未正确保存")
    elif vix_risk_score is None:
        print(f"     ⚠️  vix_risk_score 为 None - 可能未调用 VIX API")
    else:
        # 验证逻辑
        if vix_risk_score >= 6.0:
            if risk_score >= 5.0:
                print(f"     ✅ Risk Score 正确反映 VIX 风险: {risk_score:.1f} >= 5.0 (VIX={vix_risk_score:.1f})")
            else:
                print(f"     ❌ Risk Score 未正确反映 VIX 风险: {risk_score:.1f} < 5.0 (应该 >= 5.0, VIX={vix_risk_score:.1f})")
                print(f"     强制修复可能未生效")
        
        if stance.lower() == "low" and vix_risk_score >= 6.0:
            print(f"     ❌ Stance 仍然是 LOW，但 VIX risk >= 6.0，强制修复可能未生效")
        elif stance.lower() in ["medium", "medium-high", "high"]:
            print(f"     ✅ Stance 反映了风险: {stance}")
else:
    print("   ⚠️  没有找到 Risk Analyst 记录")

print()

# 3. 检查自动交易是否启动
print("3. 检查自动交易是否启动（需要用户确认）")
print("-" * 80)
print("   请执行以下步骤验证:")
print()
print("   步骤 1: 检查前端 Console")
print("     1. 打开前端页面")
print("     2. 按 F12 打开开发者工具")
print("     3. 切换到 Console 标签")
print("     4. 刷新页面")
print("     5. 查找以下日志:")
print("        - '[Auto Trade] Market status monitor started'")
print("        - '[Auto Trade] Market opened, starting auto-trade timer'")
print("        - '[Auto Trade] Timer started: executes every 30 minutes'")
print("        - '[Auto Trade] Executing first auto-trade cycle'")
print()
print("   步骤 2: 检查自动交易状态")
print("     1. 查看页面上的 'Auto Trade Status' 显示")
print("     2. 如果市场开放，应该显示 'Active' 或 'Active - Starting...'")
print("     3. 如果市场关闭，应该显示 'Market Closed - Manual Only'")
print()
print("   步骤 3: 等待自动交易执行")
print("     1. 如果市场开放，等待最多 2 分钟（首次执行）")
print("     2. 之后每 30 分钟执行一次")
print("     3. 查看 Console 中的 '[Auto Trade] ✓ Market is open, executing trade cycle...'")
print()

# 4. 检查最近的执行时间
print("4. 检查最近的执行时间")
print("-" * 80)

trader_entries = [e for e in lines if e.get("agent") in ["Trader Agent", "TraderAgent"]]
if trader_entries:
    latest = trader_entries[-1]
    latest_time = latest.get("timestamp", "")
    if latest_time:
        try:
            ts = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            diff_minutes = (now - ts).total_seconds() / 60
            
            print(f"   最新 Trader Agent 执行:")
            print(f"     时间: {latest_time}")
            print(f"     距离现在: {diff_minutes:.1f} 分钟")
            
            if diff_minutes < 35:
                print(f"     ✅ 最近有执行（{diff_minutes:.1f} 分钟前）")
                if 25 <= diff_minutes <= 35:
                    print(f"     ✅ 可能是自动交易（30分钟间隔）")
            else:
                print(f"     ⚠️  距离上次执行已超过 35 分钟")
                print(f"     可能原因:")
                print(f"       1. 市场关闭")
                print(f"       2. 自动交易未启动")
                print(f"       3. 需要手动触发一次")
        except:
            pass

print()
print("=" * 80)
print("验证完成")
print("=" * 80)
print()
print("总结:")
print("1. Risk Analyst VIX 修复:")
if risk_tool_calls:
    print("   ✅ VIX API 调用已实现")
    if risk_score is not None and vix_risk_score is not None:
        if vix_risk_score >= 6.0 and risk_score >= 5.0:
            print("   ✅ Risk Score 强制修复生效")
        else:
            print("   ⚠️  Risk Score 强制修复可能未完全生效")
    else:
        print("   ⚠️  数据保存不完整（risk_score 或 vix_risk_score 为 None）")
else:
    print("   ❌ 未找到 VIX API 调用记录 - 需要执行新的 trading cycle")

print("2. 自动交易修复:")
print("   ⚠️  需要用户检查前端 Console 确认")
print("   ⚠️  如果市场关闭，自动交易不会运行（正常行为）")





