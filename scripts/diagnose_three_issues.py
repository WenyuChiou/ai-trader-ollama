#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断三个问题：
1. 没有自动交易
2. 订单没有执行
3. Risk Analyst 风险评分问题
"""

import sys
import os
import json
from pathlib import Path
from datetime import datetime, timezone

# Add backend/src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "backend" / "src"))

try:
    from src.tools.sentiment_tools import vix_term_structure, vix_risk_score
    from src.utils.trading_days import is_market_open
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

print("=" * 60)
print("诊断三个问题")
print("=" * 60)
print()

# 1. 检查 VIX 风险评分
print("1. 检查 VIX 风险评分")
print("-" * 60)
try:
    vix_data = vix_term_structure()
    if vix_data:
        vix_level = vix_data.get("vix")
        vix_risk = vix_risk_score(vix_data)
        print(f"   VIX Level: {vix_level}")
        print(f"   VIX Risk Score: {vix_risk}")
        print(f"   预期: 如果 VIX >= 23, risk_score 应该是 6.0")
    else:
        print("   ⚠️ 无法获取 VIX 数据")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print()

# 2. 检查市场状态
print("2. 检查市场状态")
print("-" * 60)
try:
    market_open = is_market_open(None)
    print(f"   市场是否开放: {market_open}")
    now = datetime.now(timezone.utc)
    print(f"   当前 UTC 时间: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}")
except Exception as e:
    print(f"   ❌ 错误: {e}")

print()

# 3. 检查最近的订单记录
print("3. 检查最近的订单记录")
print("-" * 60)
logs_dir = project_root / "data" / "logs"
filled_orders_file = logs_dir / "filled_orders.jsonl"
pending_orders_file = logs_dir / "pending_orders.jsonl"

if filled_orders_file.exists():
    try:
        with open(filled_orders_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            if lines:
                last_order = json.loads(lines[-1])
                print(f"   最后填充的订单:")
                print(f"     Symbol: {last_order.get('symbol')}")
                print(f"     Action: {last_order.get('action')}")
                print(f"     Quantity: {last_order.get('quantity')}")
                print(f"     Status: {last_order.get('status')}")
                print(f"     Placed At: {last_order.get('placed_at')}")
                print(f"   总订单数: {len(lines)}")
            else:
                print("   ⚠️ filled_orders.jsonl 为空")
    except Exception as e:
        print(f"   ❌ 读取错误: {e}")
else:
    print("   ⚠️ filled_orders.jsonl 不存在")

if pending_orders_file.exists():
    try:
        with open(pending_orders_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            if lines:
                print(f"   ⚠️ 有 {len(lines)} 个待处理订单")
                for i, line in enumerate(lines[-3:], 1):  # 显示最后3个
                    order = json.loads(line)
                    print(f"     {i}. {order.get('symbol')} {order.get('action')} x{order.get('quantity')} - {order.get('status')}")
            else:
                print("   ✓ pending_orders.jsonl 为空（无待处理订单）")
    except Exception as e:
        print(f"   ❌ 读取错误: {e}")
else:
    print("   ✓ pending_orders.jsonl 不存在（无待处理订单）")

print()

# 4. 检查最近的对话记录
print("4. 检查最近的对话记录")
print("-" * 60)
conversations_dir = logs_dir / "conversations"
if conversations_dir.exists():
    conv_files = sorted(conversations_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if conv_files:
        latest_conv = conv_files[0]
        print(f"   最新对话文件: {latest_conv.name}")
        try:
            with open(latest_conv, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
                if lines:
                    # 查找 Risk Analyst 的输出
                    risk_analyst_found = False
                    for line in reversed(lines[-50:]):  # 检查最后50行
                        try:
                            entry = json.loads(line)
                            if entry.get("agent") == "Risk Analyst":
                                risk_analyst_found = True
                                print(f"   找到 Risk Analyst 输出:")
                                print(f"     时间: {entry.get('timestamp')}")
                                stance = entry.get("stance", "N/A")
                                risk_score = entry.get("risk_score", "N/A")
                                print(f"     Stance: {stance}")
                                print(f"     Risk Score: {risk_score}")
                                if "vix_risk_score" in entry:
                                    print(f"     VIX Risk Score: {entry.get('vix_risk_score')}")
                                break
                        except:
                            pass
                    if not risk_analyst_found:
                        print("   ⚠️ 未找到 Risk Analyst 输出")
                else:
                    print("   ⚠️ 对话文件为空")
        except Exception as e:
            print(f"   ❌ 读取错误: {e}")
    else:
        print("   ⚠️ 没有对话文件")
else:
    print("   ⚠️ conversations 目录不存在")

print()
print("=" * 60)
print("诊断完成")
print("=" * 60)

