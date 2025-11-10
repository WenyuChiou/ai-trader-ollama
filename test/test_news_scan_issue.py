#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试 news_scan 为什么没有关键词
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sys
# 自动检测路径
import os
if os.path.basename(os.getcwd()) == 'test':
    sys.path.insert(0, '../backend')
else:
    sys.path.insert(0, 'backend')

from src.agents.toolbox import ToolBox

print("=" * 80)
print("测试 news_scan 关键词问题")
print("=" * 80)

toolbox = ToolBox()

# 测试1: 完全没有参数
print("\n1. 测试完全没有参数:")
result = toolbox.invoke('news_scan')
print(f"   结果: {result}")
print(f"   ok: {result.get('ok')}")
if result.get('ok') and isinstance(result.get('result'), dict):
    print(f"   result: {result.get('result')}")

# 测试2: 只有空列表
print("\n2. 测试只有空列表 keywords=[]:")
result = toolbox.invoke('news_scan', keywords=[])
print(f"   结果: {result}")
print(f"   ok: {result.get('ok')}")
if result.get('ok') and isinstance(result.get('result'), dict):
    print(f"   result: {result.get('result')}")

# 测试3: 使用 tickers
print("\n3. 测试使用 tickers=['NVDA']:")
result = toolbox.invoke('news_scan', tickers=['NVDA'])
print(f"   结果: {result}")
print(f"   ok: {result.get('ok')}")
if result.get('ok') and isinstance(result.get('result'), dict):
    print(f"   result.hits 数量: {len(result.get('result', {}).get('hits', []))}")

# 测试4: 使用 symbols
print("\n4. 测试使用 symbols=['AAPL']:")
result = toolbox.invoke('news_scan', symbols=['AAPL'])
print(f"   结果: {result}")
print(f"   ok: {result.get('ok')}")
if result.get('ok') and isinstance(result.get('result'), dict):
    print(f"   result.hits 数量: {len(result.get('result', {}).get('hits', []))}")

# 测试5: 模拟 LLM 可能传递的参数格式
print("\n5. 测试模拟 LLM 调用（空 args）:")
result = toolbox.invoke('news_scan', **{})
print(f"   结果: {result}")
print(f"   ok: {result.get('ok')}")
if result.get('ok') and isinstance(result.get('result'), dict):
    print(f"   result: {result.get('result')}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

