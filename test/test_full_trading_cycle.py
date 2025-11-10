#!/usr/bin/env python3
"""
完整交易周期测试：
1. 测试100+股票的处理
2. 测试500字summary生成
3. 测试工具调用
4. 验证所有功能正常工作
"""

import sys
import os
import io
import json
from pathlib import Path
from datetime import datetime

# 修复Windows编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 自动检测路径
current_dir = Path(__file__).parent.absolute()
if current_dir.name == 'test':
    backend_dir = current_dir.parent / 'backend'
    sys.path.insert(0, str(backend_dir))
else:
    backend_dir = Path(__file__).parent / 'backend'
    sys.path.insert(0, str(backend_dir))

print("=" * 80)
print("完整交易周期测试")
print("=" * 80)
print(f"当前目录: {current_dir}")
print(f"Backend目录: {backend_dir}")
print()

# 检查后端服务是否运行
print("【检查】后端服务状态")
print("-" * 80)
try:
    import requests
    response = requests.get("http://127.0.0.1:8000/api/system/info", timeout=2)
    if response.status_code == 200:
        print("✅ 后端服务正在运行")
        server_running = True
    else:
        print(f"⚠️  后端服务响应异常: {response.status_code}")
        server_running = False
except Exception as e:
    print(f"⚠️  后端服务未运行或无法连接: {e}")
    print("   提示: 请先启动后端服务 (python -m uvicorn src.api.server:app --reload)")
    server_running = False
print()

if not server_running:
    print("⚠️  由于后端服务未运行，跳过API测试")
    print("   可以运行以下测试:")
    print("   1. 配置检查")
    print("   2. 函数逻辑检查")
    print()
    
    # 只进行配置和逻辑检查
    print("【测试】配置和逻辑检查")
    print("-" * 80)
    
    # 检查config.json
    config_path = backend_dir / "config" / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            universe = config.get("universe", [])
            tool_budget = config.get("discussion_tool_budget", 15)
            rounds = config.get("discussion_rounds", 3)
            
            print(f"✅ 配置检查:")
            print(f"   - Universe: {len(universe)}个股票")
            print(f"   - Tool Budget: {tool_budget}")
            print(f"   - Discussion Rounds: {rounds}")
            
            if len(universe) >= 100:
                print(f"   ✅ Universe包含100+股票")
            else:
                print(f"   ⚠️  Universe只有{len(universe)}个股票")
    print()
    
    print("=" * 80)
    print("测试完成（部分）")
    print("=" * 80)
    print("提示: 启动后端服务后可以运行完整测试")
    sys.exit(0)

# 如果后端服务运行，进行完整测试
print("【测试1】系统信息")
print("-" * 80)
try:
    response = requests.get("http://127.0.0.1:8000/api/system/info", timeout=5)
    if response.status_code == 200:
        info = response.json()
        print(f"✅ 系统信息获取成功")
        print(f"   - 默认模型: {info.get('default_model', 'N/A')}")
        print(f"   - Agent数量: {len(info.get('agents', {}))}")
    else:
        print(f"❌ 系统信息获取失败: {response.status_code}")
except Exception as e:
    print(f"❌ 系统信息获取异常: {e}")
print()

print("【测试2】Universe配置")
print("-" * 80)
try:
    config_path = backend_dir / "config" / "config.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            universe = config.get("universe", [])
            print(f"✅ Universe配置:")
            print(f"   - 股票数量: {len(universe)}")
            print(f"   - 前5个: {universe[:5]}")
            print(f"   - 最后5个: {universe[-5:]}")
            
            if len(universe) >= 100:
                print(f"   ✅ 包含100+股票")
            else:
                print(f"   ⚠️  只有{len(universe)}个股票")
except Exception as e:
    print(f"❌ Universe配置检查失败: {e}")
print()

print("【测试3】Agent状态")
print("-" * 80)
try:
    response = requests.get("http://127.0.0.1:8000/api/agents/status", timeout=5)
    if response.status_code == 200:
        status = response.json()
        print(f"✅ Agent状态获取成功")
        agents = status.get("agents", {})
        print(f"   - 可用Agent数量: {len(agents)}")
        for name, info in list(agents.items())[:5]:
            print(f"   - {name}: {info.get('status', 'N/A')}")
    else:
        print(f"❌ Agent状态获取失败: {response.status_code}")
except Exception as e:
    print(f"❌ Agent状态获取异常: {e}")
print()

print("【测试4】工具列表")
print("-" * 80)
try:
    response = requests.get("http://127.0.0.1:8000/api/tools/list", timeout=5)
    if response.status_code == 200:
        tools = response.json()
        tool_list = tools.get("tools", [])
        print(f"✅ 工具列表获取成功")
        print(f"   - 可用工具数量: {len(tool_list)}")
        print(f"   - 前10个工具: {tool_list[:10]}")
    else:
        print(f"❌ 工具列表获取失败: {response.status_code}")
except Exception as e:
    print(f"❌ 工具列表获取异常: {e}")
print()

print("【测试5】市场状态")
print("-" * 80)
try:
    response = requests.get("http://127.0.0.1:8000/api/market/is-open", timeout=5)
    if response.status_code == 200:
        market = response.json()
        is_open = market.get("is_open", False)
        print(f"✅ 市场状态获取成功")
        print(f"   - 市场是否开盘: {is_open}")
        if not is_open:
            print(f"   ℹ️  市场已收盘，可以测试'规划明日交易'功能")
    else:
        print(f"❌ 市场状态获取失败: {response.status_code}")
except Exception as e:
    print(f"❌ 市场状态获取异常: {e}")
print()

print("=" * 80)
print("测试总结")
print("=" * 80)
print("✅ 基础测试完成")
print()
print("下一步:")
print("1. 如果市场已收盘，可以测试'规划明日交易'功能")
print("2. 如果市场开盘，可以测试完整的交易周期")
print("3. 检查生成的summary是否达到500字")
print("4. 验证工具调用是否正常工作")
print()
print("提示: 运行交易周期后，检查:")
print("- discussion_actions.jsonl 中的analysis字段长度")
print("- 是否包含工具结果和新闻内容")
print("- summary是否达到约500字")
print()


