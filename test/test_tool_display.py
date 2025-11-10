#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具结果显示和解析
"""
import json
import sys
import io
from pathlib import Path
from datetime import datetime

# 修复 Windows 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def test_tool_parsing():
    """测试工具结果解析"""
    # 自动检测路径
    import os
    if os.path.basename(os.getcwd()) == 'test':
        log_file = Path('../backend/data/logs/discussion_actions.jsonl')
    else:
        log_file = Path('backend/data/logs/discussion_actions.jsonl')
    
    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        return
    
    print("=" * 80)
    print("测试工具结果显示和解析")
    print("=" * 80)
    
    # 读取所有条目
    entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"⚠️ JSON 解析错误: {e}")
                continue
    
    print(f"\n📊 总条目数: {len(entries)}")
    
    # 按类型分组
    tool_entries = [e for e in entries if e.get('type') == 'tool']
    discussion_entries = [e for e in entries if e.get('type') == 'discussion']
    
    print(f"🔧 Tool 条目: {len(tool_entries)}")
    print(f"💬 Discussion 条目: {len(discussion_entries)}")
    
    # 检查最近的 tool 条目
    print("\n" + "=" * 80)
    print("最近的 Tool 条目（最后 10 个）:")
    print("=" * 80)
    
    for entry in tool_entries[-10:]:
        agent = entry.get('agent', 'Unknown')
        tool_name = entry.get('tool_name', 'Unknown')
        content = entry.get('content', '')
        timestamp = entry.get('timestamp', '')
        
        print(f"\n🔧 {agent} -> {tool_name}")
        print(f"   时间: {timestamp}")
        print(f"   内容长度: {len(content)} 字符")
        
        # 检查内容格式
        if content.startswith('Tool used: '):
            print(f"   ✅ 格式: 'Tool used: ...'")
        elif content.strip().startswith('{'):
            print(f"   ✅ 格式: 直接 JSON")
        elif content.startswith(', {'):
            print(f"   ⚠️ 格式: 以 ', {{' 开头（可能截断）")
        else:
            print(f"   ⚠️ 格式: 其他格式")
        
        # 尝试解析 JSON
        json_str = None
        if content.strip().startswith('{'):
            json_str = content.strip()
        elif content.startswith(', {'):
            # 尝试找到第一个 {
            first_brace = content.find('{')
            if first_brace >= 0:
                json_str = content[first_brace:]
        elif '{' in content:
            # 尝试提取 JSON
            json_match = __import__('re').search(r'\{.*\}', content, __import__('re').DOTALL)
            if json_match:
                json_str = json_match.group(0)
        
        if json_str:
            try:
                parsed = json.loads(json_str)
                print(f"   ✅ JSON 解析成功")
                
                # 检查嵌套结构
                if isinstance(parsed, dict):
                    if 'ok' in parsed and 'result' in parsed:
                        print(f"   📦 包含嵌套: ok/result")
                        result = parsed['result']
                        if isinstance(result, dict) and 'ok' in result and 'result' in result:
                            print(f"   📦 双重嵌套: ok/result/result")
                
                # 显示键
                if isinstance(parsed, dict):
                    keys = list(parsed.keys())[:10]
                    print(f"   🔑 键: {', '.join(keys)}{'...' if len(parsed) > 10 else ''}")
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON 解析失败: {e}")
                # 尝试找到最后一个完整的对象
                brace_count = 0
                last_valid_pos = -1
                for i, char in enumerate(json_str):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_valid_pos = i
                            break
                
                if last_valid_pos > 0:
                    try:
                        truncated = json_str[:last_valid_pos + 1]
                        parsed = json.loads(truncated)
                        print(f"   ⚠️ 截断 JSON，但可以解析前 {last_valid_pos + 1} 字符")
                    except:
                        print(f"   ❌ 即使截断也无法解析")
    
    # 检查 discussion 条目中的 tools_used
    print("\n" + "=" * 80)
    print("Discussion 条目中的工具使用情况:")
    print("=" * 80)
    
    for entry in discussion_entries[-5:]:
        agent = entry.get('agent', 'Unknown')
        tools_used = entry.get('tools_used', [])
        timestamp = entry.get('timestamp', '')
        
        print(f"\n💬 {agent}")
        print(f"   时间: {timestamp}")
        if tools_used:
            print(f"   🔧 Tools Used: {', '.join(tools_used)}")
            
            # 查找对应的 tool 条目
            agent_normalized = agent.replace(' ', '')
            date_str = timestamp.split('T')[0] if 'T' in timestamp else ''
            
            matching_tools = []
            for tool_entry in tool_entries:
                tool_agent = tool_entry.get('agent', '')
                tool_agent_normalized = tool_agent.replace(' ', '')
                tool_date = tool_entry.get('timestamp', '').split('T')[0] if 'T' in tool_entry.get('timestamp', '') else ''
                
                if (agent_normalized.lower() == tool_agent_normalized.lower() and 
                    date_str == tool_date):
                    tool_name = tool_entry.get('tool_name', '')
                    if tool_name.lower() in [t.lower() for t in tools_used]:
                        matching_tools.append(tool_name)
            
            if matching_tools:
                print(f"   ✅ 找到匹配的工具条目: {', '.join(matching_tools)}")
            else:
                print(f"   ⚠️ 未找到匹配的工具条目")
        else:
            print(f"   ⚠️ 没有 tools_used 字段")
    
    # 检查 Discussion Coordinator 的 JSON
    print("\n" + "=" * 80)
    print("Discussion Coordinator 条目:")
    print("=" * 80)
    
    coordinators = [e for e in discussion_entries if 'coordinator' in e.get('agent', '').lower()]
    for entry in coordinators[-3:]:
        agent = entry.get('agent', 'Unknown')
        content = entry.get('content', '')
        timestamp = entry.get('timestamp', '')
        
        print(f"\n🤖 {agent}")
        print(f"   时间: {timestamp}")
        print(f"   内容长度: {len(content)} 字符")
        print(f"   内容预览: {content[:200]}...")
        
        # 检查是否包含 JSON
        if '{' in content and '"' in content:
            print(f"   ✅ 包含 JSON 结构")
            # 尝试提取 JSON
            json_match = __import__('re').search(r'\{.*\}', content, __import__('re').DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    parsed = json.loads(json_str)
                    print(f"   ✅ JSON 可以解析")
                    print(f"   🔑 键: {', '.join(list(parsed.keys())[:10])}")
                except json.JSONDecodeError as e:
                    print(f"   ❌ JSON 解析失败: {e}")
        else:
            print(f"   ⚠️ 不包含 JSON 结构")

if __name__ == '__main__':
    test_tool_parsing()

