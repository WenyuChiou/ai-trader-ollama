#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查新闻工具是否被使用
"""
import json
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

convo_file = Path("data/logs/discussion_actions.jsonl")

if not convo_file.exists():
    print("❌ discussion_actions.jsonl 不存在")
    exit(1)

# 读取所有条目
all_entries = []
with convo_file.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            try:
                all_entries.append(json.loads(line))
            except:
                pass

print(f"📊 总条目数: {len(all_entries)}")

# 统计类型
type_counts = {}
for e in all_entries:
    t = e.get("type", "unknown")
    type_counts[t] = type_counts.get(t, 0) + 1

print(f"\n📋 类型统计:")
for t, count in sorted(type_counts.items()):
    print(f"  - {t}: {count}")

# 检查 tool 类型
tool_entries = [e for e in all_entries if e.get("type") == "tool"]
print(f"\n🔧 Tool 条目数: {len(tool_entries)}")

# 检查新闻工具
news_tools = []
for e in tool_entries:
    tool_name = e.get("tool_name", "").lower()
    content = e.get("content", "").lower()
    if "news" in tool_name or "news" in content or "plan_and_scan" in tool_name:
        news_tools.append(e)

print(f"\n📰 新闻工具条目数: {len(news_tools)}")

if news_tools:
    print(f"\n📰 新闻工具详情:")
    for i, e in enumerate(news_tools[-10:], 1):
        tool_name = e.get("tool_name", "N/A")
        agent = e.get("agent", "N/A")
        date = e.get("date", e.get("timestamp", "N/A"))
        content_preview = e.get("content", "")[:100]
        print(f"  {i}. {tool_name} by {agent} on {date}")
        print(f"     Content preview: {content_preview}...")
        print()
else:
    print("\n⚠️  没有找到新闻工具条目")
    print("\n可能的原因:")
    print("  1. Agent 没有使用新闻工具")
    print("  2. 工具调用失败")
    print("  3. tool_calls 数据没有正确写入")

# 检查 discussion 条目中的 tools_used
discussion_entries = [e for e in all_entries if e.get("type") == "discussion"]
print(f"\n💬 Discussion 条目数: {len(discussion_entries)}")

news_mentioned = []
for e in discussion_entries:
    tools_used = e.get("tools_used", [])
    agent = e.get("agent", "N/A")
    for tool in tools_used:
        if "news" in str(tool).lower() or "plan_and_scan" in str(tool).lower():
            news_mentioned.append({
                "agent": agent,
                "tool": tool,
                "date": e.get("date", e.get("timestamp", "N/A"))
            })

if news_mentioned:
    print(f"\n📰 Discussion 条目中提到的新闻工具: {len(news_mentioned)}")
    for item in news_mentioned[-5:]:
        print(f"  - {item['agent']} 使用了 {item['tool']} on {item['date']}")
else:
    print("\n⚠️  Discussion 条目中没有提到新闻工具")

