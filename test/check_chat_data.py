#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查聊天记录和工具数据
"""
import json
import sys
import os
from pathlib import Path

if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 自动检测路径
if os.path.basename(os.getcwd()) == 'test':
    log_file = Path('../backend/data/logs/discussion_actions.jsonl')
else:
    log_file = Path('backend/data/logs/discussion_actions.jsonl')

if not log_file.exists():
    print("❌ 日志文件不存在:", log_file)
    sys.exit(1)

print("=" * 80)
print("检查聊天记录和工具数据")
print("=" * 80)
print(f"\n文件路径: {log_file}")
print(f"文件大小: {log_file.stat().st_size} bytes\n")

# 读取所有条目
entries = []
with log_file.open('r', encoding='utf-8') as f:
    for line_num, line in enumerate(f, 1):
        try:
            entry = json.loads(line.strip())
            entries.append(entry)
        except json.JSONDecodeError as e:
            print(f"⚠️ 第 {line_num} 行 JSON 解析失败: {e}")
            continue

print(f"总条目数: {len(entries)}\n")

# 按类型分类
by_type = {}
for entry in entries:
    entry_type = entry.get('type', 'unknown')
    if entry_type not in by_type:
        by_type[entry_type] = []
    by_type[entry_type].append(entry)

print("按类型统计:")
for entry_type, items in sorted(by_type.items()):
    print(f"  {entry_type}: {len(items)} 条")

# 检查 discussion 条目
print("\n" + "=" * 80)
print("Discussion 条目详情")
print("=" * 80)
discussions = by_type.get('discussion', [])
if discussions:
    print(f"\n找到 {len(discussions)} 条 discussion 条目:\n")
    for i, d in enumerate(discussions[-5:], 1):  # 显示最后5条
        agent = d.get('agent', 'Unknown')
        date = d.get('date', d.get('timestamp', 'No date'))
        content = d.get('content', '')
        tools_used = d.get('tools_used', [])
        print(f"{i}. Agent: {agent}")
        print(f"   Date: {date}")
        print(f"   Content length: {len(content)} chars")
        print(f"   Tools used: {tools_used}")
        print(f"   Content preview: {content[:100]}...")
        print()
else:
    print("\n❌ 没有找到 discussion 类型的条目！")

# 检查 tool 条目
print("=" * 80)
print("Tool 条目详情")
print("=" * 80)
tools = by_type.get('tool', [])
if tools:
    print(f"\n找到 {len(tools)} 条 tool 条目:\n")
    
    # 按工具名称分组
    by_tool_name = {}
    for t in tools:
        tool_name = t.get('tool_name', 'Unknown')
        if tool_name not in by_tool_name:
            by_tool_name[tool_name] = []
        by_tool_name[tool_name].append(t)
    
    print("按工具名称统计:")
    for tool_name, items in sorted(by_tool_name.items()):
        print(f"  {tool_name}: {len(items)} 条")
    
    print(f"\n最后 5 条工具条目:\n")
    for i, t in enumerate(tools[-5:], 1):
        tool_name = t.get('tool_name', 'Unknown')
        agent = t.get('agent', 'Unknown')
        date = t.get('date', t.get('timestamp', 'No date'))
        content = t.get('content', '')
        print(f"{i}. Tool: {tool_name}")
        print(f"   Agent: {agent}")
        print(f"   Date: {date}")
        print(f"   Content length: {len(content)} chars")
        
        # 检查内容是否被截断
        if content.startswith('Tool used: '):
            json_part = content.split(':', 2)[2].strip() if ':' in content else ''
            if json_part:
                try:
                    parsed = json.loads(json_part)
                    print(f"   ✅ JSON 格式正确")
                    if isinstance(parsed, dict) and 'ok' in parsed and 'result' in parsed:
                        result = parsed['result']
                        if isinstance(result, dict) and 'ok' in result and 'result' in result:
                            print(f"   ✅ 双重嵌套结构")
                        else:
                            print(f"   ✅ 单层嵌套结构")
                except json.JSONDecodeError:
                    print(f"   ⚠️ JSON 可能被截断")
        print()
else:
    print("\n❌ 没有找到 tool 类型的条目！")

# 检查数据完整性
print("=" * 80)
print("数据完整性检查")
print("=" * 80)

# 检查 discussion 和 tool 的匹配
if discussions and tools:
    print("\n检查 discussion 和 tool 的匹配情况:")
    for d in discussions[-3:]:  # 检查最后3条 discussion
        agent = d.get('agent', '')
        date = d.get('date', '')
        tools_used = d.get('tools_used', [])
        
        # 查找对应的 tool 条目
        matching_tools = [
            t for t in tools 
            if t.get('agent', '').replace(' ', '') == agent.replace(' ', '') 
            and t.get('date', '') == date
            and t.get('tool_name', '').lower() in [tu.lower() for tu in tools_used]
        ]
        
        print(f"\nDiscussion: {agent} ({date})")
        print(f"  Tools used: {tools_used}")
        print(f"  找到匹配的 tool 条目: {len(matching_tools)} 条")
        for mt in matching_tools:
            print(f"    - {mt.get('tool_name')}")

print("\n" + "=" * 80)
print("检查完成")
print("=" * 80)

