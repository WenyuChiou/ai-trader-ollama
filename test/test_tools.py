#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
综合测试所有工具 - 增强版
用法:
  python test_tools.py                    # 测试所有工具
  python test_tools.py --category news    # 只测试新闻类工具
  python test_tools.py --category fundamental  # 只测试基本面工具
  python test_tools.py --symbol AAPL     # 使用不同的股票代码
  python test_tools.py --save results.json  # 保存结果到文件
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import sys
import argparse
import json
from datetime import datetime
from pathlib import Path

# 自动检测路径：如果在 test 文件夹中运行，使用 ../backend；如果在项目根目录运行，使用 backend
import os
if os.path.basename(os.getcwd()) == 'test':
    sys.path.insert(0, '../backend')
else:
    sys.path.insert(0, 'backend')

from src.agents.toolbox import ToolBox

def test_tool(toolbox, tool_name, tool_args, tool_desc):
    """测试单个工具"""
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
            data_summary = {}
            
            if isinstance(actual_result, dict):
                # 检查是否有非空字段
                for key, value in actual_result.items():
                    if value is not None and value != [] and value != {}:
                        has_data = True
                        # 收集关键信息
                        if isinstance(value, list):
                            data_summary[key] = f"{len(value)} items"
                        elif isinstance(value, dict):
                            data_summary[key] = f"{len(value)} fields"
                        elif isinstance(value, (int, float)):
                            data_summary[key] = value
                        elif isinstance(value, str) and len(value) < 50:
                            data_summary[key] = value
                        else:
                            data_summary[key] = type(value).__name__
            elif isinstance(actual_result, list):
                has_data = len(actual_result) > 0
                data_summary["count"] = len(actual_result)
            else:
                has_data = actual_result is not None
            
            return {
                "status": "✅ PASSED" if has_data else "⚠️ NO DATA",
                "elapsed": elapsed,
                "has_data": has_data,
                "data_summary": data_summary,
                "result": actual_result if has_data else None
            }
        else:
            return {
                "status": f"❌ FAILED: {result.get('error', 'Unknown error')}",
                "elapsed": elapsed,
                "has_data": False,
                "error": result.get("error", "Unknown error")
            }
    except Exception as e:
        return {
            "status": f"❌ EXCEPTION: {str(e)}",
            "elapsed": 0,
            "has_data": False,
            "error": str(e)
        }

def main():
    parser = argparse.ArgumentParser(description='测试所有工具')
    parser.add_argument('--category', choices=['all', 'fundamental', 'technical', 'market', 'sentiment', 'news'], 
                       default='all', help='测试类别')
    parser.add_argument('--symbol', default='NVDA', help='测试用的股票代码')
    parser.add_argument('--save', help='保存结果到 JSON 文件')
    args = parser.parse_args()
    
    toolbox = ToolBox()
    
    # 定义所有工具
    all_tools = {
        'fundamental': [
            {
                "name": "get_company_fundamentals",
                "args": {"symbol": args.symbol},
                "description": "获取公司基本面数据（估值、盈利能力、增长、财务健康）"
            },
            {
                "name": "get_earnings_history",
                "args": {"symbol": args.symbol},
                "description": "获取收益历史（季度/年度收益、收益日期）"
            },
            {
                "name": "get_financial_statements",
                "args": {"symbol": args.symbol},
                "description": "获取财务报表（资产负债表、现金流量表）"
            },
        ],
        'technical': [
            {
                "name": "get_advanced_indicators",
                "args": {"symbol": args.symbol, "period": "3mo"},
                "description": "获取高级技术指标（RSI, MACD, Bollinger Bands, ADX, Stochastic, ATR, OBV）"
            },
            {
                "name": "get_support_resistance",
                "args": {"symbol": args.symbol, "period": "6mo"},
                "description": "获取支撑阻力位"
            },
        ],
        'market': [
            {
                "name": "get_market_indices",
                "args": {},
                "description": "获取市场指数（S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX）"
            },
            {
                "name": "get_sector_rotation",
                "args": {"period": "1mo"},
                "description": "获取板块轮动（各板块表现）"
            },
            {
                "name": "get_market_breadth",
                "args": {},
                "description": "获取市场广度（涨跌股票数量、市场情绪）"
            },
        ],
        'sentiment': [
            {
                "name": "vix_term",
                "args": {},
                "description": "获取 VIX 期限结构（VIX, VIX3M, 比率）"
            },
            {
                "name": "fear_greed",
                "args": {},
                "description": "获取恐惧贪婪指数"
            },
        ],
        'news': [
            {
                "name": "news_scan",
                "args": {"keywords": [args.symbol, "AAPL"], "max_articles": 5},
                "description": "扫描新闻（根据关键词搜索新闻）"
            },
        ],
    }
    
    # 选择要测试的工具
    if args.category == 'all':
        tools_to_test = []
        for category_tools in all_tools.values():
            tools_to_test.extend(category_tools)
    else:
        tools_to_test = all_tools.get(args.category, [])
    
    if not tools_to_test:
        print(f"❌ 没有找到类别 '{args.category}' 的工具")
        return
    
    print("=" * 80)
    print("综合测试工具")
    print("=" * 80)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试类别: {args.category}")
    print(f"测试股票: {args.symbol}")
    print(f"工具数量: {len(tools_to_test)}")
    print()
    
    results = []
    passed = 0
    failed = 0
    no_data = 0
    
    for i, tool_config in enumerate(tools_to_test, 1):
        tool_name = tool_config["name"]
        tool_args = tool_config["args"]
        tool_desc = tool_config["description"]
        
        print(f"[{i}/{len(tools_to_test)}] {tool_name}")
        print(f"  {tool_desc}")
        
        test_result = test_tool(toolbox, tool_name, tool_args, tool_desc)
        
        print(f"  状态: {test_result['status']}")
        print(f"  耗时: {test_result['elapsed']:.2f}s")
        
        if test_result.get('data_summary'):
            summary_str = ', '.join([f"{k}: {v}" for k, v in list(test_result['data_summary'].items())[:5]])
            print(f"  数据: {summary_str}")
        
        if test_result['has_data']:
            passed += 1
        elif 'error' in test_result:
            failed += 1
        else:
            no_data += 1
        
        results.append({
            "tool": tool_name,
            "description": tool_desc,
            "args": tool_args,
            **test_result
        })
        print()
    
    # 打印总结
    print("=" * 80)
    print("测试总结")
    print("=" * 80)
    print(f"总工具数: {len(tools_to_test)}")
    print(f"✅ 通过: {passed}")
    print(f"⚠️ 无数据: {no_data}")
    print(f"❌ 失败: {failed}")
    print()
    
    # 详细结果表格
    print("详细结果:")
    print("-" * 80)
    print(f"{'工具名称':<30} {'状态':<30} {'耗时':<10}")
    print("-" * 80)
    for r in results:
        status_display = r["status"][:30] if len(r["status"]) <= 30 else r["status"][:27] + "..."
        elapsed_display = f"{r['elapsed']:.2f}s" if r['elapsed'] > 0 else "N/A"
        print(f"{r['tool']:<30} {status_display:<30} {elapsed_display:<10}")
    
    # 保存结果
    if args.save:
        output = {
            "test_time": datetime.now().isoformat(),
            "category": args.category,
            "symbol": args.symbol,
            "summary": {
                "total": len(tools_to_test),
                "passed": passed,
                "no_data": no_data,
                "failed": failed
            },
            "results": results
        }
        with open(args.save, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n结果已保存到: {args.save}")
    
    print()
    print("=" * 80)
    print("测试完成")
    print("=" * 80)
    
    # 使用建议
    print("\n使用建议:")
    print("  python test_tools.py --category fundamental  # 只测试基本面工具")
    print("  python test_tools.py --category news         # 只测试新闻工具")
    print("  python test_tools.py --symbol AAPL           # 使用不同股票代码")
    print("  python test_tools.py --save results.json     # 保存结果到文件")

if __name__ == '__main__':
    main()

