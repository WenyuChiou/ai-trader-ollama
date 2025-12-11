#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实际验证修复是否生效
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

# 1. 验证 Risk Analyst VIX 风险评分修复
print("1. 验证 Risk Analyst VIX 风险评分修复")
print("-" * 80)

try:
    from tools.sentiment_tools import vix_term_structure, vix_risk_score
    
    # 获取当前 VIX 数据
    vix_data = vix_term_structure()
    if vix_data:
        vix_level = vix_data.get("vix")
        vix_risk = vix_risk_score(vix_data)
        print(f"   当前 VIX Level: {vix_level}")
        print(f"   当前 VIX Risk Score: {vix_risk}")
        print(f"   预期: Risk Analyst 的 risk_score 应该 >= {max(3.5, vix_risk - 0.5):.1f}")
    else:
        print("   ⚠️  无法获取 VIX 数据")
        vix_risk = None
except Exception as e:
    print(f"   ❌ 错误: {e}")
    vix_risk = None

# 检查最新的 Risk Analyst 输出
discussion_file = logs_dir / "discussion_actions.jsonl"
if discussion_file.exists():
    with open(discussion_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f if l.strip()]
    
    risk_entries = [e for e in lines if e.get("agent") == "RiskAnalyst"]
    
    if risk_entries:
        latest = risk_entries[-1]
        timestamp = latest.get("timestamp", "")
        stance = latest.get("stance", "")
        risk_score = latest.get("risk_score")
        vix_risk_from_report = latest.get("vix_risk_score")
        
        print(f"\n   最新 Risk Analyst 输出:")
        print(f"     时间: {timestamp}")
        print(f"     Stance: {stance}")
        print(f"     Risk Score: {risk_score}")
        print(f"     VIX Risk Score: {vix_risk_from_report}")
        
        # 验证
        if vix_risk is not None and vix_risk_from_report is not None:
            if abs(vix_risk_from_report - vix_risk) < 0.1:
                print(f"     ✅ VIX Risk Score 正确传递: {vix_risk_from_report:.1f}")
            else:
                print(f"     ⚠️  VIX Risk Score 不匹配: 报告={vix_risk_from_report:.1f}, 实际={vix_risk:.1f}")
        
        if risk_score is not None:
            if vix_risk is not None and vix_risk >= 6.0:
                if risk_score >= 5.0:
                    print(f"     ✅ Risk Score 正确反映 VIX 风险: {risk_score:.1f} >= 5.0 (VIX risk={vix_risk:.1f})")
                else:
                    print(f"     ❌ Risk Score 未正确反映 VIX 风险: {risk_score:.1f} < 5.0 (应该 >= 5.0, VIX risk={vix_risk:.1f})")
            elif vix_risk is not None and vix_risk >= 4.0:
                if risk_score >= 3.5:
                    print(f"     ✅ Risk Score 正确反映 VIX 风险: {risk_score:.1f} >= 3.5 (VIX risk={vix_risk:.1f})")
                else:
                    print(f"     ⚠️  Risk Score 可能未完全反映 VIX 风险: {risk_score:.1f} < 3.5 (VIX risk={vix_risk:.1f})")
            else:
                print(f"     ℹ️  VIX Risk Score 较低 ({vix_risk:.1f if vix_risk else 'N/A'})，Risk Score={risk_score:.1f} 可能正常")
        
        if stance and stance.upper() == "LOW" and vix_risk is not None and vix_risk >= 6.0:
            print(f"     ❌ Stance 仍然是 LOW，但 VIX risk >= 6.0，应该至少是 MEDIUM")
        elif stance and stance.upper() in ["MEDIUM", "MEDIUM-HIGH", "HIGH"]:
            print(f"     ✅ Stance 反映了风险: {stance}")
    else:
        print("   ⚠️  没有找到 Risk Analyst 记录")
else:
    print("   ⚠️  discussion_actions.jsonl 不存在")

print()

# 2. 验证自动交易修复
print("2. 验证自动交易修复")
print("-" * 80)

# 检查最近的 Trader Agent 记录（看是否有自动交易执行）
if discussion_file.exists():
    trader_entries = [e for e in lines if e.get("agent") in ["Trader Agent", "TraderAgent"]]
    
    if trader_entries:
        # 检查最近几次执行
        recent_traders = trader_entries[-5:]
        print(f"   最近的 Trader Agent 执行次数: {len(recent_traders)}")
        
        # 检查执行时间间隔
        if len(recent_traders) >= 2:
            times = []
            for entry in recent_traders:
                ts_str = entry.get("timestamp", "")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                        times.append(ts)
                    except:
                        pass
            
            if len(times) >= 2:
                intervals = []
                for i in range(1, len(times)):
                    diff = (times[i] - times[i-1]).total_seconds() / 60
                    intervals.append(diff)
                
                print(f"   执行间隔: {[f'{i:.1f}分钟' for i in intervals]}")
                
                # 检查是否有接近30分钟的间隔（自动交易）
                auto_trade_intervals = [i for i in intervals if 25 <= i <= 35]
                if auto_trade_intervals:
                    print(f"     ✅ 发现自动交易间隔: {[f'{i:.1f}分钟' for i in auto_trade_intervals]}")
                else:
                    print(f"     ⚠️  未发现30分钟间隔的自动交易")
                    print(f"     可能原因:")
                    print(f"       1. 市场关闭")
                    print(f"       2. 自动交易未启动")
                    print(f"       3. 手动交易干扰")
        
        # 检查最新执行
        latest = recent_traders[-1]
        latest_time = latest.get("timestamp", "")
        print(f"\n   最新执行:")
        print(f"     时间: {latest_time}")
        print(f"     Buy orders: {latest.get('buy_orders_count', 0)}")
        print(f"     Actual created: {latest.get('actual_buy_orders_created', 0)}")
        
        # 检查是否在交易时间内
        if latest_time:
            try:
                ts = datetime.fromisoformat(latest_time.replace('Z', '+00:00'))
                import pytz
                et_tz = pytz.timezone('America/New_York')
                et_time = ts.astimezone(et_tz)
                hour = et_time.hour
                minute = et_time.minute
                market_open = (9 * 60 + 30) <= (hour * 60 + minute) < (16 * 60)
                print(f"     ET 时间: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                print(f"     市场是否开放: {market_open}")
            except:
                pass
    else:
        print("   ⚠️  没有找到 Trader Agent 记录")

print()

# 3. 检查前端自动交易状态（需要用户确认）
print("3. 前端自动交易状态（需要用户确认）")
print("-" * 80)
print("   请检查前端页面:")
print("   1. 打开浏览器开发者工具 (F12)")
print("   2. 查看 Console 日志:")
print("      - 应该看到: '[Auto Trade] Market status monitor started'")
print("      - 应该看到: '[Auto Trade] Timer started: executes every 30 minutes'")
print("      - 应该看到: '[Auto Trade] Market opened, starting auto-trade timer'")
print("   3. 检查 autoTradeStatus 元素显示的状态")
print("   4. 如果市场开放，应该显示 'Active' 或 'Active - Starting...'")
print("   5. 如果市场关闭，应该显示 'Market Closed - Manual Only'")

print()
print("=" * 80)
print("验证完成")
print("=" * 80)
print()
print("总结:")
print("1. Risk Analyst:")
if vix_risk is not None and risk_score is not None:
    if vix_risk >= 6.0 and risk_score >= 5.0:
        print("   ✅ VIX 风险评分修复生效")
    elif vix_risk >= 6.0:
        print("   ❌ VIX 风险评分修复未完全生效")
    else:
        print("   ℹ️  VIX 风险较低，无法验证强制修复")
else:
    print("   ⚠️  无法验证（缺少数据）")

print("2. 自动交易:")
print("   ⚠️  需要用户检查前端 Console 日志确认")
print("   ⚠️  如果市场关闭，自动交易不会运行（这是正常行为）")





