#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试所有工具
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sys
# 自动检测路径：如果在 test 文件夹中运行，使用 ../backend；如果在项目根目录运行，使用 backend
import os
if os.path.basename(os.getcwd()) == 'test':
    sys.path.insert(0, '../backend')
else:
    sys.path.insert(0, 'backend')

from src.agents.toolbox import ToolBox
import json
from datetime import datetime

print("=" * 80)
print("综合测试所有工具")
print("=" * 80)
print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

toolbox = ToolBox()
test_symbol = "NVDA"  # 测试用的股票代码

# 定义要测试的工具列表
tools_to_test = [
    # 基本面分析工具
    {
        "name": "get_company_fundamentals",
        "args": {"symbol": test_symbol},
        "description": "获取公司基本面数据"
    },
    {
        "name": "get_earnings_history",
        "args": {"symbol": test_symbol},
        "description": "获取收益历史"
    },
    {
        "name": "get_financial_statements",
        "args": {"symbol": test_symbol},
        "description": "获取财务报表"
    },
    
    # 技术分析工具
    {
        "name": "get_advanced_indicators",
        "args": {"symbol": test_symbol, "period": "3mo"},
        "description": "获取高级技术指标"
    },
    {
        "name": "get_support_resistance",
        "args": {"symbol": test_symbol, "period": "6mo"},
        "description": "获取支撑阻力位"
    },
    
    # 市场工具
    {
        "name": "get_market_indices",
        "args": {},
        "description": "获取市场指数"
    },
    {
        "name": "get_sector_rotation",
        "args": {"period": "1mo"},
        "description": "获取板块轮动"
    },
    {
        "name": "get_market_breadth",
        "args": {},
        "description": "获取市场广度"
    },
    
    # 情绪工具
    {
        "name": "vix_term",
        "args": {},
        "description": "获取 VIX 期限结构"
    },
    {
        "name": "fear_greed",
        "args": {},
        "description": "获取恐惧贪婪指数"
    },
    
    # 新闻工具
    {
        "name": "news_scan",
        "args": {"keywords": [test_symbol, "AAPL"], "max_articles": 5},
        "description": "扫描新闻"
    },
]

# 统计
total_tools = len(tools_to_test)
passed_tools = 0
failed_tools = 0
skipped_tools = 0

results = []

print(f"准备测试 {total_tools} 个工具...\n")

for i, tool_config in enumerate(tools_to_test, 1):
    tool_name = tool_config["name"]
    tool_args = tool_config["args"]
    tool_desc = tool_config["description"]
    
    print(f"[{i}/{total_tools}] 测试: {tool_name}")
    print(f"  描述: {tool_desc}")
    print(f"  参数: {tool_args}")
    
    try:
        start_time = datetime.now()
        result = toolbox.invoke(tool_name, **tool_args)
        elapsed = (datetime.now() - start_time).total_seconds()
        
        if result.get("ok"):
            # 处理双重嵌套
            inner_result = result.get("result", {})
            if isinstance(inner_result, dict) and 'ok' in inner_result and 'result' in inner_result:
                actual_result = inner_result['result']
            else:
                actual_result = inner_result
            
            # 检查结果是否有数据
            has_data = False
            if isinstance(actual_result, dict):
                # 检查是否有非空字段
                for key, value in actual_result.items():
                    if value is not None and value != [] and value != {}:
                        has_data = True
                        break
            elif isinstance(actual_result, list):
                has_data = len(actual_result) > 0
            else:
                has_data = actual_result is not None
            
            if has_data:
                print(f"  ✅ 成功 (耗时: {elapsed:.2f}s)")
                # 显示关键信息
                if isinstance(actual_result, dict):
                    keys = list(actual_result.keys())[:5]
                    print(f"  关键字段: {', '.join(keys)}{'...' if len(actual_result) > 5 else ''}")
                    # 显示一些具体值
                    if 'symbol' in actual_result:
                        print(f"  Symbol: {actual_result['symbol']}")
                    if 'hits' in actual_result:
                        print(f"  新闻数量: {len(actual_result.get('hits', []))}")
                    if 'vix' in actual_result:
                        print(f"  VIX: {actual_result.get('vix')}")
                    if 'value' in actual_result:
                        print(f"  FGI Value: {actual_result.get('value')}")
                passed_tools += 1
                status = "✅ PASSED"
            else:
                print(f"  ⚠️ 成功但无数据 (耗时: {elapsed:.2f}s)")
                skipped_tools += 1
                status = "⚠️ NO DATA"
        else:
            error_msg = result.get("error", "Unknown error")
            print(f"  ❌ 失败: {error_msg}")
            failed_tools += 1
            status = f"❌ FAILED: {error_msg}"
        
        results.append({
            "tool": tool_name,
            "status": status,
            "elapsed": elapsed,
            "description": tool_desc
        })
        
    except Exception as e:
        print(f"  ❌ 异常: {str(e)}")
        failed_tools += 1
        results.append({
            "tool": tool_name,
            "status": f"❌ EXCEPTION: {str(e)}",
            "elapsed": 0,
            "description": tool_desc
        })
    
    print()

# 打印总结
print("=" * 80)
print("测试总结")
print("=" * 80)
print(f"总工具数: {total_tools}")
print(f"✅ 通过: {passed_tools}")
print(f"⚠️ 无数据: {skipped_tools}")
print(f"❌ 失败: {failed_tools}")
print()

# 详细结果表格
print("详细结果:")
print("-" * 80)
print(f"{'工具名称':<30} {'状态':<40} {'耗时':<10}")
print("-" * 80)
for r in results:
    status_display = r["status"][:40] if len(r["status"]) <= 40 else r["status"][:37] + "..."
    elapsed_display = f"{r['elapsed']:.2f}s" if r['elapsed'] > 0 else "N/A"
    print(f"{r['tool']:<30} {status_display:<40} {elapsed_display:<10}")

print()
print("=" * 80)
print("测试完成")
print("=" * 80)

# 如果有失败的，提供建议
if failed_tools > 0:
    print("\n建议:")
    print("1. 检查后端服务是否运行")
    print("2. 检查网络连接（某些工具需要访问外部 API）")
    print("3. 检查依赖库是否安装完整（如 scipy 用于 get_support_resistance）")
    print("4. 查看上面的错误信息以获取更多详情")

