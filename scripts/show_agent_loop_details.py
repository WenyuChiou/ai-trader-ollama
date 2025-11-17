#!/usr/bin/env python3
"""
显示 Agent Loop 的详细执行信息
包括工具调用、Agent响应等
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
import json

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

def show_agent_loop_details():
    """显示最近的 Agent Loop 执行详情"""
    logs_dir = ROOT / "data" / "logs"
    discussion_file = logs_dir / "discussion_actions.jsonl"
    
    if not discussion_file.exists():
        print("❌ 未找到讨论记录文件")
        return
    
    print("=" * 80)
    print("  📊 Agent Loop 详细执行记录")
    print("=" * 80)
    
    # 读取最近的记录
    entries = []
    try:
        with discussion_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except:
                        continue
    except Exception as e:
        print(f"❌ 读取文件错误: {e}")
        return
    
    if not entries:
        print("❌ 没有找到讨论记录")
        return
    
    # 只显示最近的20条
    recent_entries = entries[-20:]
    
    print(f"\n📝 最近 {len(recent_entries)} 条记录 (共 {len(entries)} 条):\n")
    
    # 按Agent分组显示
    agents_summary = {}
    tool_calls = []
    
    for entry in recent_entries:
        agent = entry.get("agent", "Unknown")
        entry_type = entry.get("type", "unknown")
        
        if agent not in agents_summary:
            agents_summary[agent] = {
                "count": 0,
                "tools": [],
                "stances": [],
                "entries": []
            }
        
        agents_summary[agent]["count"] += 1
        agents_summary[agent]["entries"].append(entry)
        
        if entry_type == "tool":
            tool_name = entry.get("tool_name", "unknown")
            agents_summary[agent]["tools"].append(tool_name)
            tool_calls.append({
                "agent": agent,
                "tool": tool_name,
                "timestamp": entry.get("timestamp", "")
            })
        
        stance = entry.get("stance")
        if stance:
            agents_summary[agent]["stances"].append(stance)
    
    # 显示Agent摘要
    print("=" * 80)
    print("  🤖 Agent 执行摘要")
    print("=" * 80)
    
    for agent, summary in agents_summary.items():
        print(f"\n  📌 {agent}:")
        print(f"    - 记录数: {summary['count']}")
        if summary['stances']:
            unique_stances = list(set(summary['stances']))
            print(f"    - Stances: {', '.join(unique_stances)}")
        if summary['tools']:
            unique_tools = list(set(summary['tools']))
            print(f"    - 工具调用: {len(summary['tools'])} 次")
            print(f"    - 工具列表: {', '.join(unique_tools)}")
    
    # 显示工具调用详情
    print("\n" + "=" * 80)
    print("  🔧 工具调用详情")
    print("=" * 80)
    
    tool_stats = {}
    for tool_call in tool_calls:
        tool_name = tool_call['tool']
        if tool_name not in tool_stats:
            tool_stats[tool_name] = {
                "count": 0,
                "agents": set()
            }
        tool_stats[tool_name]["count"] += 1
        tool_stats[tool_name]["agents"].add(tool_call['agent'])
    
    print(f"\n  总工具调用: {len(tool_calls)} 次")
    print(f"  不同工具: {len(tool_stats)} 种\n")
    
    for tool, stats in sorted(tool_stats.items(), key=lambda x: x[1]['count'], reverse=True):
        agents_list = ', '.join(stats['agents'])
        print(f"  - {tool}: {stats['count']} 次 (by {agents_list})")
    
    # 显示最近的详细记录
    print("\n" + "=" * 80)
    print("  📋 最近执行记录详情")
    print("=" * 80)
    
    for i, entry in enumerate(recent_entries[-10:], 1):  # 只显示最后10条
        agent = entry.get("agent", "Unknown")
        entry_type = entry.get("type", "unknown")
        timestamp = entry.get("timestamp", "N/A")
        
        print(f"\n  [{i}] {agent} ({entry_type}) - {timestamp}")
        
        if entry_type == "tool":
            tool_name = entry.get("tool_name", "unknown")
            tool_args = entry.get("tool_args", {})
            print(f"      🔧 Tool: {tool_name}")
            if tool_args:
                print(f"      📝 Args: {json.dumps(tool_args, ensure_ascii=False)[:100]}")
        elif entry_type == "discussion":
            stance = entry.get("stance", "N/A")
            summary = entry.get("summary", "")
            tools_used = entry.get("tools_used", [])
            print(f"      📊 Stance: {stance}")
            if tools_used:
                print(f"      🔧 Tools Used: {', '.join(tools_used)}")
            if summary:
                preview = summary[:150] + "..." if len(summary) > 150 else summary
                print(f"      💬 Summary: {preview}")

if __name__ == "__main__":
    show_agent_loop_details()

