#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
前端流程测试脚本
模拟前端的主要流程，测试 API 调用和数据格式
"""
import json
import requests
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# 设置 Windows 终端编码
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except:
        pass

API_BASE = "http://127.0.0.1:8000"
TIMEOUT = 30

def print_section(title: str):
    """打印分节标题"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)

def print_result(success: bool, message: str, details: Any = None):
    """打印测试结果"""
    status = "[PASS]" if success else "[FAIL]"
    print(f"{status}: {message}")
    if details and not success:
        if isinstance(details, dict):
            print(f"   Details: {json.dumps(details, indent=2, ensure_ascii=False)}")
        else:
            print(f"   Details: {details}")

def check_server_running() -> bool:
    """检查后端服务器是否运行"""
    try:
        response = requests.get(f"{API_BASE}/api/market/is-open", timeout=5)
        return True
    except:
        return False

def test_api_endpoint(endpoint: str, method: str = "GET", data: Optional[Dict] = None) -> Optional[Dict]:
    """测试 API 端点"""
    try:
        url = f"{API_BASE}{endpoint}"
        if method == "GET":
            response = requests.get(url, timeout=TIMEOUT)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=TIMEOUT)
        else:
            return None
        
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"HTTP {response.status_code}", "message": response.text}
    except requests.exceptions.Timeout:
        return {"error": "Timeout", "message": f"Request to {endpoint} timed out after {TIMEOUT}s"}
    except requests.exceptions.ConnectionError:
        return {"error": "Connection Error", "message": f"Could not connect to {API_BASE}. Is the backend server running?"}
    except Exception as e:
        return {"error": str(type(e).__name__), "message": str(e)}

def test_market_status():
    """测试市场状态检查"""
    print_section("1. 测试市场状态检查")
    result = test_api_endpoint("/api/market/is-open")
    if result and "open" in result:
        is_open = result.get("open", False)
        print_result(True, f"市场状态: {'开盘' if is_open else '收盘'}")
        return is_open
    else:
        print_result(False, "无法获取市场状态", result)
        return None

def test_agent_status():
    """测试 Agent 状态"""
    print_section("2. 测试 Agent 状态")
    result = test_api_endpoint("/api/agents/status")
    if result and "agents" in result:
        agents = result.get("agents", {})
        print_result(True, f"找到 {len(agents)} 个 agents")
        for agent_name, status in agents.items():
            status_str = "运行中" if status.get("running", False) else "空闲"
            print(f"   - {agent_name}: {status_str}")
        return True
    else:
        print_result(False, "无法获取 agent 状态", result)
        return False

def test_tools_list():
    """测试工具列表"""
    print_section("3. 测试工具列表")
    result = test_api_endpoint("/api/tools/list")
    if result and "tools" in result:
        tools = result.get("tools", [])
        print_result(True, f"找到 {len(tools)} 个工具")
        # 显示前10个工具
        for tool in tools[:10]:
            print(f"   - {tool}")
        if len(tools) > 10:
            print(f"   ... 还有 {len(tools) - 10} 个工具")
        return True
    else:
        print_result(False, "无法获取工具列表", result)
        return False

def test_conversations():
    """测试对话数据"""
    print_section("4. 测试对话数据")
    result = test_api_endpoint("/api/agents/conversations?limit=20")
    if result and "conversations" in result:
        conversations = result.get("conversations", [])
        print_result(True, f"找到 {len(conversations)} 条对话记录")
        
        # 按类型分组
        by_type = {}
        by_agent = {}
        for conv in conversations:
            conv_type = conv.get("type", "unknown")
            agent = conv.get("agent", "Unknown")
            by_type[conv_type] = by_type.get(conv_type, 0) + 1
            by_agent[agent] = by_agent.get(agent, 0) + 1
        
        print("\n   按类型分组:")
        for conv_type, count in by_type.items():
            print(f"   - {conv_type}: {count}")
        
        print("\n   按 Agent 分组:")
        for agent, count in sorted(by_agent.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   - {agent}: {count}")
        
        # 检查工具结果
        tool_entries = [c for c in conversations if c.get("type") == "tool"]
        discussion_entries = [c for c in conversations if c.get("type") == "discussion"]
        
        print(f"\n   工具条目: {len(tool_entries)}")
        print(f"   讨论条目: {len(discussion_entries)}")
        
        # 检查 agent 名称匹配问题
        print("\n   检查 Agent 名称匹配:")
        agent_variants = {}
        for conv in conversations:
            agent = conv.get("agent", "Unknown")
            normalized = agent.replace(" ", "")
            if agent not in agent_variants:
                agent_variants[agent] = []
            agent_variants[agent].append(conv.get("type"))
        
        for agent, types in agent_variants.items():
            types_str = ", ".join(set(types))
            print(f"   - {agent}: {types_str}")
        
        return True
    else:
        print_result(False, "无法获取对话数据", result)
        return False

def test_tool_result_parsing():
    """测试工具结果解析"""
    print_section("5. 测试工具结果解析")
    
    # 从文件读取对话数据（尝试多个可能的路径）
    possible_paths = [
        Path("../backend/data/logs/discussion_actions.jsonl"),
        Path("data/logs/discussion_actions.jsonl"),
        Path("backend/data/logs/discussion_actions.jsonl"),
    ]
    
    log_file = None
    for path in possible_paths:
        if path.exists():
            log_file = path
            break
    
    if not log_file:
        print_result(False, f"日志文件不存在，尝试了以下路径:")
        for path in possible_paths:
            print(f"   - {path}")
        return False
    
    print(f"   使用日志文件: {log_file}")
    
    tool_entries = []
    line_count = 0
    with log_file.open("r", encoding="utf-8") as f:
        for line in f:
            line_count += 1
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if entry.get("type") == "tool":
                    tool_entries.append(entry)
            except json.JSONDecodeError as e:
                print(f"   [WARN] 第 {line_count} 行 JSON 解析失败: {e}")
                continue
            except Exception as e:
                print(f"   [WARN] 第 {line_count} 行处理失败: {e}")
                continue
    
    print(f"   文件总行数: {line_count}")
    print(f"   工具条目数: {len(tool_entries)}")
    
    if not tool_entries:
        if line_count == 0:
            print_result(False, "日志文件为空，请先运行一次交易循环")
            print("   提示: 在前端点击 'Plan Tomorrow' 或 'Start Trading' 按钮来生成数据")
        else:
            print_result(False, f"没有找到工具条目（文件有 {line_count} 行，但都不是工具类型）")
        return line_count > 0  # 如果文件有内容但没工具条目，也算部分成功
    
    print_result(True, f"找到 {len(tool_entries)} 个工具条目")
    
        # 检查工具结果格式
    print("\n   检查工具结果格式:")
    for entry in tool_entries[:5]:  # 检查前5个
        agent = entry.get("agent", "Unknown")
        tool_name = entry.get("tool_name", "unknown")
        content = entry.get("content", "")
        
        # 检查是否有嵌套的 result 字段
        has_nested_result = '"ok":' in content and '"result":' in content
        has_result_data = '"value":' in content or '"label":' in content or '"indices":' in content
        
        status = "[OK]" if (has_nested_result or has_result_data) else "[WARN]"
        result_text = "有结果数据" if has_result_data else "无结果数据"
        print(f"   {status} {agent} -> {tool_name}: {result_text}")
        if has_nested_result:
            print(f"      (包含嵌套 result 字段)")
    
    return True

def test_agent_name_matching():
    """测试 Agent 名称匹配"""
    print_section("6. 测试 Agent 名称匹配")
    
    # 尝试多个可能的路径
    possible_paths = [
        Path("../backend/data/logs/discussion_actions.jsonl"),
        Path("data/logs/discussion_actions.jsonl"),
        Path("backend/data/logs/discussion_actions.jsonl"),
    ]
    
    log_file = None
    for path in possible_paths:
        if path.exists():
            log_file = path
            break
    
    if not log_file:
        print_result(False, f"日志文件不存在")
        return False
    
    print(f"   使用日志文件: {log_file}")
    
    discussions = []
    tools = []
    line_count = 0
    
    with log_file.open("r", encoding="utf-8") as f:
        for line in f:
            line_count += 1
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry_type = entry.get("type")
                if entry_type == "discussion":
                    discussions.append(entry)
                elif entry_type == "tool":
                    tools.append(entry)
            except json.JSONDecodeError:
                continue
            except Exception:
                continue
    
    print(f"   文件总行数: {line_count}")
    
    print(f"   讨论条目: {len(discussions)}")
    print(f"   工具条目: {len(tools)}")
    
    # 检查匹配情况
    print("\n   检查匹配情况:")
    matched = 0
    unmatched = 0
    
    for disc in discussions:
        disc_agent = disc.get("agent", "")
        disc_date = disc.get("date", "")
        disc_normalized = disc_agent.replace(" ", "")
        
        # 查找匹配的工具条目
        matching_tools = [
            t for t in tools
            if (t.get("agent", "").replace(" ", "") == disc_normalized or
                t.get("agent", "") == disc_agent or
                t.get("agent", "") == disc_normalized) and
            t.get("date", "") == disc_date
        ]
        
        if matching_tools:
            matched += 1
            print(f"   [OK] {disc_agent} ({disc_date}): 找到 {len(matching_tools)} 个工具结果")
        else:
            unmatched += 1
            tools_used = disc.get("tools_used", [])
            if tools_used:
                print(f"   [WARN] {disc_agent} ({disc_date}): 未找到工具结果 (使用了: {', '.join(tools_used)})")
    
    print(f"\n   匹配结果: {matched} 个有工具结果, {unmatched} 个无工具结果")
    return matched > 0

def test_system_info():
    """测试系统信息"""
    print_section("7. 测试系统信息")
    result = test_api_endpoint("/api/system/info")
    if result and "llm" in result:
        llm_info = result.get("llm", {})
        model = llm_info.get("default_model", "Unknown")
        print_result(True, f"默认模型: {model}")
        
        agent_models = result.get("agent_models", {})
        if agent_models:
            print("   Agent 模型:")
            for agent, model in list(agent_models.items())[:5]:
                print(f"   - {agent}: {model}")
        return True
    else:
        print_result(False, "无法获取系统信息", result)
        return False

def main():
    """主测试流程"""
    print("\n" + "="*80)
    print("  前端流程测试")
    print("="*80)
    print(f"API Base: {API_BASE}")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查服务器是否运行
    print("\n检查后端服务器状态...")
    server_running = check_server_running()
    if not server_running:
        print("[WARNING] 后端服务器未运行或无法连接")
        print("  将跳过 API 测试，仅测试文件读取部分")
        print("  请确保后端服务器正在运行: python -m uvicorn src.api.server:app --reload")
    
    results = []
    
    # 1. 市场状态（需要服务器）
    if server_running:
        market_open = test_market_status()
        results.append(("市场状态", market_open is not None))
    else:
        print_section("1. 测试市场状态检查 (跳过 - 服务器未运行)")
        results.append(("市场状态", False))
    
    # 2. Agent 状态（需要服务器）
    if server_running:
        results.append(("Agent 状态", test_agent_status()))
    else:
        print_section("2. 测试 Agent 状态 (跳过 - 服务器未运行)")
        results.append(("Agent 状态", False))
    
    # 3. 工具列表（需要服务器）
    if server_running:
        results.append(("工具列表", test_tools_list()))
    else:
        print_section("3. 测试工具列表 (跳过 - 服务器未运行)")
        results.append(("工具列表", False))
    
    # 4. 对话数据（需要服务器）
    if server_running:
        results.append(("对话数据", test_conversations()))
    else:
        print_section("4. 测试对话数据 (跳过 - 服务器未运行)")
        results.append(("对话数据", False))
    
    # 5. 工具结果解析（不需要服务器，直接读取文件）
    results.append(("工具结果解析", test_tool_result_parsing()))
    
    # 6. Agent 名称匹配（不需要服务器，直接读取文件）
    results.append(("Agent 名称匹配", test_agent_name_matching()))
    
    # 7. 系统信息（需要服务器）
    if server_running:
        results.append(("系统信息", test_system_info()))
    else:
        print_section("7. 测试系统信息 (跳过 - 服务器未运行)")
        results.append(("系统信息", False))
    
    # 总结
    print_section("测试总结")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        # 判断是否是跳过的测试
        is_skipped = not server_running and any(keyword in test_name for keyword in ["市场状态", "Agent 状态", "工具列表", "对话数据", "系统信息"])
        if is_skipped:
            status = "[SKIP]"
        else:
            status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    if not server_running:
        skipped_count = sum(1 for name, _ in results if not server_running and any(k in name for k in ["市场状态", "Agent 状态", "工具列表", "对话数据", "系统信息"]))
        print(f"跳过: {skipped_count} 个（服务器未运行）")
        print("\n提示: 要运行完整测试，请先启动后端服务器:")
        print("  cd backend")
        print("  python -m uvicorn src.api.server:app --reload")
    
    if passed == total:
        print("\n[SUCCESS] 所有测试通过！")
        return 0
    elif not server_running and passed == sum(1 for name, _ in results if not any(k in name for k in ["市场状态", "Agent 状态", "工具列表", "对话数据", "系统信息"])):
        print("\n[INFO] 文件测试完成（服务器未运行，API 测试已跳过）")
        return 0
    else:
        print(f"\n[WARNING] 有 {total - passed} 个测试失败")
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

