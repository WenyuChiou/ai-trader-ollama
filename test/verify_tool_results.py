#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证工具结果数据流
"""
import json
import sys
from pathlib import Path

if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except:
        pass

# 自动检测路径
import os
if os.path.basename(os.getcwd()) == 'test':
    log_file = Path("../backend/data/logs/discussion_actions.jsonl")
else:
    log_file = Path("backend/data/logs/discussion_actions.jsonl")
if not log_file.exists():
    print("日志文件不存在")
    sys.exit(1)

# 读取所有工具条目
tools = []
with log_file.open("r", encoding="utf-8") as f:
    for line in f:
        try:
            entry = json.loads(line.strip())
            if entry.get("type") == "tool":
                tools.append(entry)
        except:
            continue

print(f"找到 {len(tools)} 个工具条目\n")

# 检查每个工具的结果
for tool in tools[-5:]:  # 检查最近5个
    agent = tool.get("agent")
    tool_name = tool.get("tool_name")
    content = tool.get("content", "")
    
    print(f"=== {agent} -> {tool_name} ===")
    
    # 解析内容
    if content.startswith("Tool used: "):
        tool_text = content[len("Tool used: "):]
        colon_idx = tool_text.find(":")
        if colon_idx > 0:
            result_text = tool_text[colon_idx + 1:].strip()
            
            # 尝试解析 JSON
            try:
                parsed = json.loads(result_text)
                # 递归提取 result
                while isinstance(parsed, dict) and "ok" in parsed and "result" in parsed:
                    parsed = parsed["result"]
                
                print(f"  [OK] 解析成功")
                print(f"  数据类型: {type(parsed).__name__}")
                if isinstance(parsed, dict):
                    keys = list(parsed.keys())
                    print(f"  数据键: {keys[:10]}")
                    # 显示一些值
                    for key in keys[:3]:
                        value = parsed[key]
                        if isinstance(value, (int, float)):
                            print(f"    {key}: {value}")
                        elif isinstance(value, str):
                            print(f"    {key}: {value[:50]}")
                        elif isinstance(value, list):
                            print(f"    {key}: Array({len(value)} items)")
                        else:
                            print(f"    {key}: {type(value).__name__}")
            except json.JSONDecodeError as e:
                print(f"  [FAIL] JSON 解析失败: {e}")
                print(f"  内容长度: {len(result_text)}")
                print(f"  内容预览: {result_text[:100]}")
    print()

