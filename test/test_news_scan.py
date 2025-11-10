#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新闻扫描功能
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

from src.tools.news_tools import news_scan
import json

print("=" * 80)
print("测试新闻扫描功能")
print("=" * 80)

# 测试1: 使用关键词
print("\n1. 测试使用关键词 ['NVDA', 'AAPL']:")
try:
    result = news_scan(
        keywords=['NVDA', 'AAPL'],
        max_articles=5,
        recency_days=7
    )
    print(f"   结果类型: {type(result)}")
    if isinstance(result, dict):
        print(f"   键: {list(result.keys())}")
        print(f"   hits 数量: {len(result.get('hits', []))}")
        print(f"   queries: {result.get('queries', [])}")
        if result.get('hits'):
            print(f"\n   前3条新闻:")
            for i, hit in enumerate(result.get('hits', [])[:3], 1):
                print(f"     {i}. {hit.get('title', 'N/A')[:80]}")
                print(f"        {hit.get('link', 'N/A')[:80]}")
                print(f"        Source: {hit.get('source', 'N/A')}")
        else:
            print("   ⚠️ 没有找到新闻")
    else:
        print(f"   结果: {result}")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

# 测试2: 空关键词（应该返回空结果）
print("\n2. 测试空关键词 []:")
try:
    result = news_scan(
        keywords=[],
        max_articles=5
    )
    print(f"   结果: {json.dumps(result, indent=2, ensure_ascii=False)[:200]}")
except Exception as e:
    print(f"   ❌ 错误: {e}")

# 测试3: 通过 ToolBox 调用
print("\n3. 测试通过 ToolBox 调用:")
try:
    from src.agents.toolbox import ToolBox
    toolbox = ToolBox()
    result = toolbox.invoke('news_scan', keywords=['NVDA'], max_articles=3)
    print(f"   结果类型: {type(result)}")
    if isinstance(result, dict):
        print(f"   ok: {result.get('ok')}")
        if result.get('ok'):
            inner_result = result.get('result', {})
            print(f"   result.hits 数量: {len(inner_result.get('hits', []))}")
            print(f"   result.queries: {inner_result.get('queries', [])}")
            if inner_result.get('hits'):
                print(f"\n   前2条新闻:")
                for i, hit in enumerate(inner_result.get('hits', [])[:2], 1):
                    print(f"     {i}. {hit.get('title', 'N/A')[:60]}")
        else:
            print(f"   错误: {result.get('error')}")
except Exception as e:
    print(f"   ❌ 错误: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)

