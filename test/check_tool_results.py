#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
import sys
import io
import os
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 自动检测路径
if os.path.basename(os.getcwd()) == 'test':
    log_file = Path('../backend/data/logs/discussion_actions.jsonl')
else:
    log_file = Path('backend/data/logs/discussion_actions.jsonl')
entries = [json.loads(line) for line in log_file.open('r', encoding='utf-8')]

print("=" * 80)
print("检查工具结果")
print("=" * 80)

# 检查 Sentiment Analyst 的工具结果
print("\n1. Sentiment Analyst 工具结果:")
sentiment_tools = [e for e in entries if e.get('type') == 'tool' and 'Sentiment' in e.get('agent', '')]
for t in sentiment_tools:
    print(f"\n  Tool: {t.get('tool_name')}")
    content = t.get('content', '')
    print(f"  内容长度: {len(content)} 字符")
    print(f"  内容: {content[:200]}...")
    
    # 尝试解析
    if content.startswith('Tool used: '):
        json_part = content.split(':', 2)[2].strip() if ':' in content else ''
        if json_part:
            try:
                parsed = json.loads(json_part)
                print(f"  ✅ JSON 解析成功")
                if isinstance(parsed, dict) and 'ok' in parsed and 'result' in parsed:
                    result = parsed['result']
                    if isinstance(result, dict) and 'ok' in result and 'result' in result:
                        actual_result = result['result']
                        print(f"  ✅ 双重嵌套，实际结果键: {list(actual_result.keys())[:5]}")
                    else:
                        print(f"  ✅ 单层嵌套，结果键: {list(result.keys())[:5]}")
            except json.JSONDecodeError as e:
                print(f"  ❌ JSON 解析失败: {e}")
                print(f"  ⚠️ 可能被截断")

# 检查 discussion 条目
print("\n2. Sentiment Analyst Discussion 条目:")
sentiment_discussions = [e for e in entries if e.get('type') == 'discussion' and 'Sentiment' in e.get('agent', '')]
for d in sentiment_discussions:
    print(f"\n  Agent: {d.get('agent')}")
    print(f"  Tools Used: {d.get('tools_used', [])}")
    
    # 查找匹配的工具条目
    agent_normalized = d.get('agent', '').replace(' ', '')
    date_str = d.get('date', '')
    
    matching_tools = []
    for tool_entry in sentiment_tools:
        tool_agent = tool_entry.get('agent', '').replace(' ', '')
        tool_date = tool_entry.get('date', '')
        if agent_normalized.lower() == tool_agent.lower() and date_str == tool_date:
            tool_name = tool_entry.get('tool_name', '')
            if tool_name in d.get('tools_used', []):
                matching_tools.append(tool_name)
    
    print(f"  ✅ 找到匹配的工具: {matching_tools}")

# 检查截断的工具
print("\n3. 检查被截断的工具:")
truncated_tools = []
for e in entries:
    if e.get('type') == 'tool':
        content = e.get('content', '')
        if content.startswith('Tool used: '):
            json_part = content.split(':', 2)[2].strip() if ':' in content else ''
            if json_part:
                try:
                    json.loads(json_part)
                except json.JSONDecodeError:
                    truncated_tools.append({
                        'agent': e.get('agent'),
                        'tool': e.get('tool_name'),
                        'length': len(content),
                        'preview': content[-100:]
                    })

print(f"\n  被截断的工具数量: {len(truncated_tools)}")
for t in truncated_tools:
    print(f"  - {t['agent']} -> {t['tool']}: {t['length']} 字符")
    print(f"    末尾: ...{t['preview']}")

