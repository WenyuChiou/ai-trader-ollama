#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查新闻工具结果的内容格式
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

# 检查新闻工具条目
news_tools = [e for e in all_entries if e.get("type") == "tool" and "news" in e.get("tool_name", "").lower()]

print(f"📰 找到 {len(news_tools)} 个新闻工具条目\n")

for i, e in enumerate(news_tools[:3], 1):
    print(f"=== Entry {i} ===")
    print(f"Agent: {e.get('agent')}")
    print(f"Tool: {e.get('tool_name')}")
    print(f"Date: {e.get('date')}")
    
    content = e.get("content", "")
    print(f"\nContent length: {len(content)}")
    print(f"Content preview (first 300 chars):")
    print(content[:300])
    print("...")
    
    # 尝试解析 JSON
    try:
        # 查找 JSON 部分（从 "Tool used: news_scan: " 之后）
        if "Tool used:" in content:
            json_start = content.find("{")
            if json_start > 0:
                json_str = content[json_start:]
                # 尝试找到完整的 JSON
                parsed = json.loads(json_str)
                print(f"\n✅ JSON 解析成功!")
                print(f"Keys: {list(parsed.keys())}")
                if "hits" in parsed:
                    hits = parsed["hits"]
                    print(f"Hits count: {len(hits)}")
                    if len(hits) > 0:
                        print(f"First hit keys: {list(hits[0].keys())}")
                        print(f"First hit title: {hits[0].get('title', 'N/A')[:80]}")
                else:
                    print("⚠️  No 'hits' key in result")
            else:
                print("⚠️  No JSON found in content")
        else:
            print("⚠️  Content doesn't start with 'Tool used:'")
    except json.JSONDecodeError as je:
        print(f"\n❌ JSON 解析失败: {je}")
        print(f"Error position: {je.pos}")
        if je.pos < len(content):
            print(f"Context: ...{content[max(0, je.pos-50):je.pos+50]}...")
    except Exception as ex:
        print(f"\n❌ 解析错误: {ex}")
    
    print("\n" + "="*60 + "\n")

