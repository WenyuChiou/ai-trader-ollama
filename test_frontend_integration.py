#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试前端集成：对话显示和净值更新"""
import sys
import io
import json
from pathlib import Path

# 强制 UTF-8 输出
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

print("=" * 60)
print("前端集成测试：对话显示和净值更新")
print("=" * 60)
print()

# 1. 检查对话文件
print("[1] 检查对话文件...")
conv_file = Path("data/logs/discussion_actions.jsonl")
if conv_file.exists():
    with conv_file.open("r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]
    print(f"  ✅ 对话文件存在: {conv_file}")
    print(f"  ✅ 对话数量: {len(lines)}")
    
    # 显示最后3条对话
    if lines:
        print(f"\n  最后3条对话:")
        for i, line in enumerate(lines[-3:], 1):
            try:
                entry = json.loads(line.strip())
                agent = entry.get("agent", entry.get("agent_name", "Unknown"))
                content = entry.get("content", entry.get("message", ""))
                content_preview = content[:50] + "..." if len(content) > 50 else content
                print(f"    {i}. {agent}: {content_preview}")
            except Exception as e:
                print(f"    {i}. [解析错误: {e}]")
else:
    print(f"  ❌ 对话文件不存在: {conv_file}")
    print("  ⚠️  需要运行交易循环生成对话")

print()

# 2. 检查投资组合状态
print("[2] 检查投资组合状态...")
portfolio_file = Path("data/logs/portfolio_state.json")
if portfolio_file.exists():
    with portfolio_file.open("r", encoding="utf-8") as f:
        state = json.load(f)
    print(f"  ✅ Portfolio state 存在: {portfolio_file}")
    print(f"  ✅ Cash: ${state.get('cash', 0):.2f}")
    print(f"  ✅ Total Value: ${state.get('total_value', 0):.2f}")
    print(f"  ✅ Equity Value: ${state.get('equity_value', 0):.2f}")
    print(f"  ✅ Positions: {len(state.get('positions', {}))}")
    
    positions = state.get('positions', {})
    if positions:
        print(f"\n  持仓详情:")
        for symbol, pos in list(positions.items())[:5]:
            qty = pos.get('quantity', 0)
            cost = pos.get('avg_cost', 0)
            value = pos.get('current_value', 0)
            print(f"    {symbol}: {qty} shares @ ${cost:.2f} = ${value:.2f}")
else:
    print(f"  ❌ Portfolio state 不存在: {portfolio_file}")
    print("  ⚠️  需要运行交易循环生成状态")

print()

# 3. 测试 API 端点（如果服务器运行）
print("[3] 测试 API 端点...")
try:
    import requests
    
    base_url = "http://127.0.0.1:8000"
    
    # 测试对话端点
    try:
        response = requests.get(f"{base_url}/api/agents/conversations?limit=5", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 对话端点正常 (HTTP {response.status_code})")
            print(f"  ✅ 返回对话数量: {data.get('count', len(data.get('conversations', [])))}")
        else:
            print(f"  ⚠️  对话端点返回 HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  对话端点无法连接: {e}")
        print("     (API 服务器可能未运行)")
    
    # 测试净值端点
    try:
        response = requests.get(f"{base_url}/api/portfolio/real-time", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 净值端点正常 (HTTP {response.status_code})")
            if data.get('ok'):
                print(f"  ✅ Total Value: ${data.get('total_value', 0):.2f}")
                print(f"  ✅ Equity Value: ${data.get('equity_value', 0):.2f}")
                print(f"  ✅ Cash: ${data.get('cash', 0):.2f}")
            else:
                print(f"  ⚠️  端点返回错误: {data.get('error', 'Unknown')}")
        else:
            print(f"  ⚠️  净值端点返回 HTTP {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ⚠️  净值端点无法连接: {e}")
        print("     (API 服务器可能未运行)")
        
except ImportError:
    print("  ⚠️  requests 模块未安装，跳过 API 测试")
    print("     安装: pip install requests")

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
print()
print("建议:")
print("1. 如果对话文件为空，运行: python -m uvicorn src.api.server:app")
print("   然后在浏览器中打开前端并点击 Initialize")
print("2. 如果 API 端点无法连接，确保后端服务器正在运行")
print("3. 刷新前端页面查看对话和净值更新")

