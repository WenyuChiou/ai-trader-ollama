#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具信息提取
模拟前端的 parseToolInfo 和工具结果匹配逻辑，验证提取是否正确
"""
import json
import sys
import os
import io
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

# 修复 Windows 编码问题
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 自动检测路径
if os.path.basename(os.getcwd()) == 'test':
    log_file = Path('../backend/data/logs/discussion_actions.jsonl')
else:
    log_file = Path('backend/data/logs/discussion_actions.jsonl')

def parse_tool_info(content: str) -> Optional[Dict[str, Any]]:
    """
    模拟前端的 parseToolInfo 函数
    从工具内容字符串中提取工具名称和结果
    """
    if not content or not isinstance(content, str):
        return None
    
    # 支持两种格式：
    # 1. "Tool used: tool_name: {...}" (旧格式)
    # 2. 直接 JSON 格式: "{...}" 或包含 JSON 的字符串
    tool_text = ''
    if content.startswith('Tool used: '):
        tool_text = content[len('Tool used: '):]
    else:
        # 如果不是 "Tool used: " 格式，尝试直接解析 JSON
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                json_str = json_match.group(0)
                # 如果 JSON 可能被截断，尝试修复
                parsed = None
                try:
                    parsed = json.loads(json_str)
                except json.JSONDecodeError:
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
                            parsed = json.loads(json_str[:last_valid_pos + 1])
                        except:
                            parsed = None
                
                if parsed:
                    # 处理双重嵌套：{"ok": true, "result": {"ok": true, "result": {...}}}
                    while isinstance(parsed, dict) and 'ok' in parsed and 'result' in parsed:
                        parsed = parsed['result']
                    
                    # 尝试从 parsed 中提取工具名
                    tool_name = parsed.get('tool') or parsed.get('name') or parsed.get('tool_name') or 'Unknown'
                    return {
                        'name': tool_name,
                        'result': parsed,
                        'full': content
                    }
        except Exception as e:
            pass
        
        # 如果无法解析，返回 None
        return None
    
    # 解析工具信息，支持多种格式：
    # 1. "news_scan: 10 hits, queries=['AAPL'], samples=[...]"
    # 2. "vix_term: VIX=17.17, VIX3M=20.38, ratio=1.187"
    # 3. "fear_greed: ok"
    # 4. "get_market_indices: {...}" (JSON格式)
    colon_index = tool_text.find(':')
    if colon_index == -1:
        # 如果没有冒号，整个字符串是工具名
        return {
            'name': tool_text.strip(),
            'result': '',
            'full': tool_text.strip()
        }
    
    tool_name = tool_text[:colon_index].strip()
    tool_result = tool_text[colon_index + 1:].strip()
    
    # 尝试解析 JSON 格式的结果
    try:
        json_match = re.search(r'\{[\s\S]*\}', tool_result)
        if json_match:
            json_str = json_match.group(0)
            # 如果 JSON 可能被截断，尝试修复
            parsed = None
            try:
                parsed = json.loads(json_str)
            except json.JSONDecodeError:
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
                        parsed = json.loads(json_str[:last_valid_pos + 1])
                    except:
                        parsed = None
            
            if parsed:
                # 处理双重嵌套：{"ok": true, "result": {"ok": true, "result": {...}}}
                while isinstance(parsed, dict) and 'ok' in parsed and 'result' in parsed:
                    parsed = parsed['result']
                tool_result = parsed
    except Exception as e:
        pass
    
    # 确保 result 是对象而不是字符串（如果可能）
    final_result = tool_result
    if isinstance(tool_result, str) and tool_result.strip().startswith('{'):
        try:
            parsed = json.loads(tool_result)
            # 处理嵌套的 ok/result 结构
            while isinstance(parsed, dict) and 'ok' in parsed and 'result' in parsed:
                parsed = parsed['result']
            final_result = parsed
        except:
            final_result = tool_result
    elif isinstance(tool_result, dict):
        # 如果已经是对象，处理嵌套的 ok/result 结构
        while isinstance(tool_result, dict) and 'ok' in tool_result and 'result' in tool_result:
            tool_result = tool_result['result']
        final_result = tool_result
    
    return {
        'name': tool_name,
        'result': final_result,
        'full': tool_text.strip()
    }

def normalize_agent_name(agent_name: str) -> str:
    """标准化 agent 名称：移除空格"""
    return agent_name.replace(' ', '')

def match_tool_entries(discussion_entry: Dict, tool_entries: List[Dict]) -> List[Dict]:
    """
    匹配讨论条目对应的工具条目
    模拟前端的匹配逻辑
    """
    if discussion_entry.get('type') != 'discussion':
        return []
    
    # 标准化 agent 名称
    agent_normalized = normalize_agent_name(discussion_entry.get('agent', ''))
    discussion_date = discussion_entry.get('date') or (discussion_entry.get('timestamp', '').split('T')[0] if discussion_entry.get('timestamp') else '')
    
    # 获取讨论条目使用的工具列表
    tools_used = discussion_entry.get('tools_used', [])
    if not tools_used:
        return []
    
    tools_used_lower = [t.lower() for t in tools_used]
    
    matched_tools = []
    for tool_entry in tool_entries:
        if tool_entry.get('type') != 'tool':
            continue
        
        # 标准化 tool 条目的 agent 名称
        tool_agent_normalized = normalize_agent_name(tool_entry.get('agent', ''))
        
        # 匹配 agent 名称
        agent_match = (agent_normalized == tool_agent_normalized or 
                      agent_normalized.lower() == tool_agent_normalized.lower())
        
        # 匹配日期
        tool_date = tool_entry.get('date') or (tool_entry.get('timestamp', '').split('T')[0] if tool_entry.get('timestamp') else '')
        date_match = discussion_date and tool_date and (discussion_date == tool_date)
        
        if agent_match and date_match:
            # 检查工具名称是否在 tools_used 列表中
            entry_tool_name = (tool_entry.get('tool_name') or '').lower()
            is_tool_used = any(
                entry_tool_name == used_tool or
                entry_tool_name in used_tool or
                used_tool in entry_tool_name
                for used_tool in tools_used_lower
            )
            
            if is_tool_used:
                matched_tools.append(tool_entry)
    
    return matched_tools

def format_result_summary(result: Any, max_depth: int = 2, current_depth: int = 0) -> str:
    """格式化结果摘要"""
    if current_depth >= max_depth:
        return "..."
    
    if result is None:
        return "None"
    elif isinstance(result, bool):
        return str(result)
    elif isinstance(result, (int, float)):
        return str(result)
    elif isinstance(result, str):
        if len(result) > 100:
            return result[:100] + "..."
        return result
    elif isinstance(result, list):
        if len(result) == 0:
            return "[]"
        return f"[{len(result)} items: {', '.join([format_result_summary(item, max_depth, current_depth + 1) for item in result[:3]])}{'...' if len(result) > 3 else ''}]"
    elif isinstance(result, dict):
        keys = list(result.keys())
        if len(keys) == 0:
            return "{}"
        summary = ", ".join([f"{k}: {format_result_summary(result[k], max_depth, current_depth + 1)}" for k in keys[:5]])
        return f"{{{summary}{'...' if len(keys) > 5 else ''}}}"
    else:
        return str(type(result).__name__)

def test_tool_extraction():
    """测试工具信息提取"""
    print("=" * 80)
    print("测试工具信息提取")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"日志文件: {log_file}")
    print()
    
    if not log_file.exists():
        print(f"❌ 日志文件不存在: {log_file}")
        print("   请先运行一次交易循环以生成日志文件")
        return
    
    # 读取所有条目
    entries = []
    try:
        with log_file.open('r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entry = json.loads(line)
                        entries.append(entry)
                    except json.JSONDecodeError as e:
                        print(f"⚠️ JSON 解析错误: {e}")
                        continue
    except Exception as e:
        print(f"❌ 读取文件失败: {e}")
        return
    
    print(f"✅ 读取了 {len(entries)} 条记录")
    print()
    
    # 分离工具条目和讨论条目
    tool_entries = [e for e in entries if e.get('type') == 'tool']
    discussion_entries = [e for e in entries if e.get('type') == 'discussion']
    
    print(f"工具条目: {len(tool_entries)}")
    print(f"讨论条目: {len(discussion_entries)}")
    print()
    
    # 用于存储测试结果的列表
    parse_results = []
    match_results = []
    nested_check_results = []
    truncated_check_results = []
    
    # 测试 1: 解析工具信息
    print("=" * 80)
    print("测试 1: 解析工具信息 (parseToolInfo)")
    print("=" * 80)
    
    parse_success = 0
    parse_failed = 0
    parse_no_result = 0
    
    for i, tool_entry in enumerate(tool_entries, 1):
        agent = tool_entry.get('agent', 'Unknown')
        tool_name = tool_entry.get('tool_name', 'unknown')
        content = tool_entry.get('content', '')
        date = tool_entry.get('date', '')
        
        tool_info = parse_tool_info(content)
        
        # 记录解析结果
        result_data = {
            '序号': i,
            'Agent': agent,
            '工具名称': tool_name,
            '日期': date,
            '内容长度': len(content),
            '解析状态': '',
            '结果类型': '',
            '结果键数量': 0,
            '是否截断': False,
            'JSON完整性': '',
            '结果摘要': ''
        }
        
        if tool_info:
            result_data['解析状态'] = '✅ 成功'
            
            if tool_info['result']:
                result_type = type(tool_info['result']).__name__
                result_data['结果类型'] = result_type
                
                # 检查是否是字符串（可能是截断的 JSON）
                if isinstance(tool_info['result'], str):
                    result_data['是否截断'] = True
                    # 尝试再次解析
                    try:
                        json_match = re.search(r'\{[\s\S]*\}', tool_info['result'])
                        if json_match:
                            json_str = json_match.group(0)
                            open_braces = json_str.count('{')
                            close_braces = json_str.count('}')
                            result_data['JSON完整性'] = f"{open_braces} 个 {{ vs {close_braces} 个 }}"
                            
                            if open_braces == close_braces:
                                parsed = json.loads(json_str)
                                while isinstance(parsed, dict) and 'ok' in parsed and 'result' in parsed:
                                    parsed = parsed['result']
                                if isinstance(parsed, dict):
                                    result_data['结果类型'] = 'dict (parsed)'
                                    result_data['结果键数量'] = len(parsed)
                                    result_data['结果摘要'] = format_result_summary(parsed)[:100]
                    except Exception:
                        pass
                    result_data['结果摘要'] = str(tool_info['result'])[:100] + "..."
                elif isinstance(tool_info['result'], dict):
                    result_data['结果键数量'] = len(tool_info['result'])
                    keys = list(tool_info['result'].keys())[:5]
                    result_data['结果摘要'] = f"键: {', '.join(keys)}{'...' if len(tool_info['result']) > 5 else ''}"
                elif isinstance(tool_info['result'], list):
                    result_data['结果键数量'] = len(tool_info['result'])
                    result_data['结果摘要'] = f"数组 ({len(tool_info['result'])} items)"
                else:
                    result_data['结果摘要'] = str(tool_info['result'])[:100]
                
                parse_success += 1
            else:
                result_data['解析状态'] = '⚠️ 无结果'
                result_data['结果类型'] = 'None'
                parse_no_result += 1
        else:
            result_data['解析状态'] = '❌ 失败'
            parse_failed += 1
        
        parse_results.append(result_data)
    
    # 创建 DataFrame 并显示
    df_parse = pd.DataFrame(parse_results)
    print("\n解析结果汇总 (DataFrame):")
    print(df_parse.to_string(index=False))
    print(f"\n解析统计:")
    print(f"  ✅ 成功: {parse_success}")
    print(f"  ⚠️ 无结果: {parse_no_result}")
    print(f"  ❌ 失败: {parse_failed}")
    
    # 测试 2: 匹配工具条目与讨论条目
    print("\n" + "=" * 80)
    print("测试 2: 匹配工具条目与讨论条目")
    print("=" * 80)
    
    match_success = 0
    match_failed = 0
    
    for i, discussion_entry in enumerate(discussion_entries, 1):
        agent = discussion_entry.get('agent', 'Unknown')
        tools_used = discussion_entry.get('tools_used', [])
        date = discussion_entry.get('date', '')
        
        if not tools_used:
            continue
        
        matched_tools = match_tool_entries(discussion_entry, tool_entries)
        
        # 记录匹配结果
        match_data = {
            '序号': i,
            'Agent': agent,
            '日期': date,
            '使用的工具数': len(tools_used),
            '工具列表': ', '.join(tools_used),
            '匹配到的工具数': len(matched_tools),
            '匹配状态': '✅ 成功' if matched_tools else '❌ 失败',
            '匹配的工具': ''
        }
        
        if matched_tools:
            matched_tool_names = []
            for tool_entry in matched_tools:
                tool_name = tool_entry.get('tool_name', 'unknown')
                tool_content = tool_entry.get('content', '')
                tool_info = parse_tool_info(tool_content)
                
                if tool_info and tool_info['result']:
                    result_type = type(tool_info['result']).__name__
                    matched_tool_names.append(f"{tool_name} ({result_type})")
                else:
                    matched_tool_names.append(f"{tool_name} (⚠️无法解析)")
            
            match_data['匹配的工具'] = ', '.join(matched_tool_names)
            match_success += 1
        else:
            match_failed += 1
        
        match_results.append(match_data)
    
    # 创建 DataFrame 并显示
    df_match = pd.DataFrame(match_results)
    if len(df_match) > 0:
        print("\n匹配结果汇总 (DataFrame):")
        print(df_match.to_string(index=False))
    print(f"\n匹配统计:")
    print(f"  ✅ 成功: {match_success}")
    print(f"  ❌ 失败: {match_failed}")
    
    # 测试 3: 检查嵌套结构处理
    print("\n" + "=" * 80)
    print("测试 3: 检查嵌套 ok/result 结构处理")
    print("=" * 80)
    
    nested_count = 0
    for tool_entry in tool_entries:
        agent = tool_entry.get('agent', 'Unknown')
        tool_name = tool_entry.get('tool_name', 'unknown')
        content = tool_entry.get('content', '')
        
        nested_data = {
            'Agent': agent,
            '工具名称': tool_name,
            '是否包含嵌套': 'ok' in content and 'result' in content,
            '嵌套处理状态': '',
            '最终结果类型': ''
        }
        
        if 'ok' in content and 'result' in content:
            tool_info = parse_tool_info(content)
            if tool_info and tool_info['result']:
                nested_data['最终结果类型'] = type(tool_info['result']).__name__
                # 检查是否还有嵌套的 ok/result
                if isinstance(tool_info['result'], dict):
                    if 'ok' in tool_info['result'] and 'result' in tool_info['result']:
                        nested_count += 1
                        nested_data['嵌套处理状态'] = '⚠️ 未处理'
                    else:
                        nested_data['嵌套处理状态'] = '✅ 已处理'
                else:
                    nested_data['嵌套处理状态'] = '✅ 已处理'
            else:
                nested_data['嵌套处理状态'] = '❌ 解析失败'
        else:
            nested_data['嵌套处理状态'] = 'N/A (无嵌套)'
        
        nested_check_results.append(nested_data)
    
    # 创建 DataFrame 并显示
    df_nested = pd.DataFrame(nested_check_results)
    print("\n嵌套结构检查结果 (DataFrame):")
    print(df_nested.to_string(index=False))
    
    if nested_count == 0:
        print("\n✅ 所有嵌套结构都已正确处理")
    else:
        print(f"\n⚠️ 发现 {nested_count} 个未处理的嵌套结构")
    
    # 测试 4: 检查截断 JSON
    print("\n" + "=" * 80)
    print("测试 4: 检查截断 JSON 处理")
    print("=" * 80)
    
    truncated_count = 0
    for tool_entry in tool_entries:
        agent = tool_entry.get('agent', 'Unknown')
        tool_name = tool_entry.get('tool_name', 'unknown')
        content = tool_entry.get('content', '')
        
        truncated_data = {
            'Agent': agent,
            '工具名称': tool_name,
            '内容长度': len(content),
            '是否截断': False,
            '截断类型': '',
            '处理状态': ''
        }
        
        # 检查是否以 ', {' 开头或 JSON 不完整
        is_truncated = content.strip().startswith(', {') or (content.count('{') != content.count('}'))
        truncated_data['是否截断'] = is_truncated
        
        if is_truncated:
            truncated_count += 1
            if content.strip().startswith(', {'):
                truncated_data['截断类型'] = '以 ", {" 开头'
            else:
                open_braces = content.count('{')
                close_braces = content.count('}')
                truncated_data['截断类型'] = f'括号不匹配 ({open_braces} vs {close_braces})'
            
            tool_info = parse_tool_info(content)
            if tool_info and tool_info['result']:
                if isinstance(tool_info['result'], dict):
                    truncated_data['处理状态'] = '✅ 成功解析为对象'
                elif isinstance(tool_info['result'], str):
                    truncated_data['处理状态'] = '⚠️ 仍为字符串'
                else:
                    truncated_data['处理状态'] = f'✅ 解析为 {type(tool_info["result"]).__name__}'
            else:
                truncated_data['处理状态'] = '❌ 无法处理'
        
        truncated_check_results.append(truncated_data)
    
    # 创建 DataFrame 并显示
    df_truncated = pd.DataFrame(truncated_check_results)
    # 只显示截断的条目
    df_truncated_filtered = df_truncated[df_truncated['是否截断'] == True]
    if len(df_truncated_filtered) > 0:
        print("\n截断 JSON 检查结果 (DataFrame):")
        print(df_truncated_filtered.to_string(index=False))
    
    if truncated_count == 0:
        print("\n✅ 未发现截断的 JSON")
    else:
        print(f"\n发现 {truncated_count} 个可能截断的 JSON，已尝试处理")
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    # 创建总结 DataFrame
    summary_data = {
        '指标': [
            '总工具条目',
            '总讨论条目',
            '解析成功数',
            '解析无结果数',
            '解析失败数',
            '解析成功率',
            '匹配成功数',
            '匹配失败数',
            '匹配成功率',
            '嵌套结构检查',
            '截断JSON数量'
        ],
        '数值': [
            len(tool_entries),
            len(discussion_entries),
            parse_success,
            parse_no_result,
            parse_failed,
            f"{parse_success * 100 // max(1, parse_success + parse_failed + parse_no_result)}%",
            match_success,
            match_failed,
            f"{match_success * 100 // max(1, match_success + match_failed)}%" if (match_success + match_failed) > 0 else "N/A",
            f"{nested_count} 个未处理" if nested_count > 0 else "全部已处理",
            truncated_count
        ]
    }
    
    df_summary = pd.DataFrame(summary_data)
    print("\n测试总结 (DataFrame):")
    print(df_summary.to_string(index=False))
    
    # 保存到 CSV（可选）
    try:
        output_dir = Path('test/output')
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        df_parse.to_csv(output_dir / f'tool_extraction_parse_{timestamp}.csv', index=False, encoding='utf-8-sig')
        if len(df_match) > 0:
            df_match.to_csv(output_dir / f'tool_extraction_match_{timestamp}.csv', index=False, encoding='utf-8-sig')
        df_nested.to_csv(output_dir / f'tool_extraction_nested_{timestamp}.csv', index=False, encoding='utf-8-sig')
        df_truncated.to_csv(output_dir / f'tool_extraction_truncated_{timestamp}.csv', index=False, encoding='utf-8-sig')
        df_summary.to_csv(output_dir / f'tool_extraction_summary_{timestamp}.csv', index=False, encoding='utf-8-sig')
        
        print(f"\n✅ 结果已保存到: {output_dir}")
        print(f"   - tool_extraction_parse_{timestamp}.csv")
        print(f"   - tool_extraction_match_{timestamp}.csv")
        print(f"   - tool_extraction_nested_{timestamp}.csv")
        print(f"   - tool_extraction_truncated_{timestamp}.csv")
        print(f"   - tool_extraction_summary_{timestamp}.csv")
    except Exception as e:
        print(f"\n⚠️ 保存 CSV 文件失败: {e}")
    
    print()
    print("=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == '__main__':
    test_tool_extraction()

