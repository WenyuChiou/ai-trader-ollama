#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试工具结果从后端到前端的完整流程
"""
import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 设置 Windows 终端编码
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

def test_backend_storage():
    """测试后端存储的工具结果"""
    print("="*80)
    print("  1. 检查后端存储的工具结果")
    print("="*80)
    
    log_file = Path("backend/data/logs/discussion_actions.jsonl")
    if not log_file.exists():
        print("[FAIL] 日志文件不存在")
        return False
    
    tool_entries = []
    with log_file.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "tool":
                    tool_entries.append(entry)
            except:
                continue
    
    print(f"[OK] 找到 {len(tool_entries)} 个工具条目")
    
    if not tool_entries:
        print("[WARNING] 没有工具条目，请先运行一次交易循环")
        return False
    
    # 检查最近的几个工具条目
    print("\n最近的工具条目:")
    for entry in tool_entries[-5:]:
        agent = entry.get("agent", "Unknown")
        tool_name = entry.get("tool_name", "unknown")
        content = entry.get("content", "")
        
        # 检查内容格式
        has_tool_used = content.startswith("Tool used: ")
        has_json = "{" in content
        
        print(f"\n  - {agent} -> {tool_name}")
        print(f"    Content length: {len(content)}")
        print(f"    Has 'Tool used:': {has_tool_used}")
        print(f"    Has JSON: {has_json}")
        
        # 尝试解析 JSON
        if has_json:
            try:
                json_match = content.split(":", 2)[2] if ":" in content else content
                json_match = json_match.strip()
                if json_match.startswith("{"):
                    parsed = json.loads(json_match)
                    # 检查嵌套结构
                    nested_level = 0
                    current = parsed
                    while isinstance(current, dict) and "ok" in current and "result" in current:
                        nested_level += 1
                        current = current["result"]
                    
                    print(f"    Nested levels: {nested_level}")
                    print(f"    Final data type: {type(current).__name__}")
                    if isinstance(current, dict):
                        print(f"    Final data keys: {list(current.keys())[:5]}")
            except Exception as e:
                print(f"    JSON parse error: {e}")
    
    return True

def test_api_response():
    """测试 API 返回的数据格式"""
    print("\n" + "="*80)
    print("  2. 检查 API 返回的数据格式")
    print("="*80)
    
    try:
        import requests
        response = requests.get("http://127.0.0.1:8000/api/agents/conversations?limit=50", timeout=5)
        if response.status_code == 200:
            data = response.json()
            conversations = data.get("conversations", [])
            tool_entries = [c for c in conversations if c.get("type") == "tool"]
            
            print(f"[OK] API 返回 {len(conversations)} 条对话，其中 {len(tool_entries)} 条是工具条目")
            
            if tool_entries:
                print("\nAPI 返回的工具条目示例:")
                entry = tool_entries[-1]
                print(f"  Agent: {entry.get('agent')}")
                print(f"  Tool: {entry.get('tool_name')}")
                print(f"  Content length: {len(entry.get('content', ''))}")
                print(f"  Content preview: {entry.get('content', '')[:200]}")
                return True
            else:
                print("[WARNING] API 没有返回工具条目")
                return False
        else:
            print(f"[FAIL] API 返回错误: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("[SKIP] 后端服务器未运行，跳过 API 测试")
        return None
    except Exception as e:
        print(f"[FAIL] API 测试失败: {e}")
        return False

def test_frontend_parsing():
    """测试前端解析逻辑（模拟）"""
    print("\n" + "="*80)
    print("  3. 测试前端解析逻辑（模拟）")
    print("="*80)
    
    log_file = Path("backend/data/logs/discussion_actions.jsonl")
    if not log_file.exists():
        print("[SKIP] 日志文件不存在")
        return False
    
    # 读取一个工具条目
    tool_entry = None
    with log_file.open("r", encoding="utf-8") as f:
        for line in f:
            try:
                entry = json.loads(line.strip())
                if entry.get("type") == "tool":
                    tool_entry = entry
                    break
            except:
                continue
    
    if not tool_entry:
        print("[SKIP] 没有找到工具条目")
        return False
    
    content = tool_entry.get("content", "")
    print(f"原始内容: {content[:150]}...")
    
    # 模拟前端 parseToolInfo 函数
    if not content.startswith("Tool used: "):
        print("[FAIL] 内容格式不正确（应该以 'Tool used: ' 开头）")
        return False
    
    tool_text = content.substring("Tool used: ".length) if hasattr(content, 'substring') else content[len("Tool used: "):]
    colon_index = tool_text.find(":")
    if colon_index == -1:
        print("[FAIL] 找不到工具名和结果的分隔符")
        return False
    
    tool_name = tool_text[:colon_index].strip()
    tool_result_text = tool_text[colon_index + 1:].strip()
    
    print(f"工具名: {tool_name}")
    print(f"结果文本长度: {len(tool_result_text)}")
    
    # 尝试解析 JSON（处理可能被截断的情况）
    try:
        json_match = tool_result_text
        if json_match.startswith("{"):
            # 尝试完整解析
            try:
                parsed = json.loads(json_match)
            except json.JSONDecodeError:
                # 如果解析失败，可能是被截断了，尝试修复
                # 找到最后一个完整的对象
                brace_count = 0
                last_valid_pos = -1
                for i, char in enumerate(json_match):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            last_valid_pos = i
                            break
                
                if last_valid_pos > 0:
                    # 尝试解析到最后一个完整对象
                    try:
                        parsed = json.loads(json_match[:last_valid_pos + 1])
                        print(f"[WARNING] JSON 被截断，解析到位置 {last_valid_pos + 1}")
                    except:
                        print(f"[FAIL] 无法修复截断的 JSON")
                        return False
                else:
                    print(f"[FAIL] JSON 格式不完整")
                    return False
            
            print(f"[OK] JSON 解析成功")
            
            # 递归提取 result
            result_data = parsed
            nested_level = 0
            while isinstance(result_data, dict) and "ok" in result_data and "result" in result_data:
                nested_level += 1
                result_data = result_data["result"]
            
            print(f"嵌套层数: {nested_level}")
            print(f"最终数据类型: {type(result_data).__name__}")
            if isinstance(result_data, dict):
                print(f"最终数据键: {list(result_data.keys())[:10]}")
                print(f"[OK] 前端应该能正确解析并显示这些数据")
                return True
            else:
                print(f"[WARNING] 最终数据不是字典: {result_data}")
                return False
    except json.JSONDecodeError as e:
        print(f"[FAIL] JSON 解析失败: {e}")
        print(f"问题: 数据可能被截断（旧数据是500字符限制，新数据是2000字符）")
        print(f"建议: 运行新的交易循环以生成完整数据")
        return False
    except Exception as e:
        print(f"[FAIL] 解析过程出错: {e}")
        return False

def main():
    print("="*80)
    print("  工具结果数据流测试")
    print("="*80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = []
    
    # 1. 检查后端存储
    results.append(("后端存储", test_backend_storage()))
    
    # 2. 检查 API 响应
    api_result = test_api_response()
    if api_result is not None:
        results.append(("API 响应", api_result))
    
    # 3. 测试前端解析
    results.append(("前端解析", test_frontend_parsing()))
    
    # 总结
    print("\n" + "="*80)
    print("  测试总结")
    print("="*80)
    
    for name, success in results:
        status = "[PASS]" if success else "[FAIL]" if success is False else "[SKIP]"
        print(f"{status} {name}")
    
    passed = sum(1 for _, success in results if success is True)
    total = len(results)
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有测试通过！工具结果数据流正常")
        return 0
    else:
        print(f"\n[WARNING] 有 {total - passed} 个测试失败或跳过")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

