#!/usr/bin/env python3
"""
运行一次完整的 Agent Loop 演示
展示工具调用、Agent讨论等详细执行过程
"""
from __future__ import annotations
import sys
import os
from pathlib import Path
from datetime import date, timedelta
import json

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

def print_section(title: str, char: str = "="):
    """打印分隔线"""
    print("\n" + char * 80)
    print(f"  {title}")
    print(char * 80)

def print_subsection(title: str, char: str = "-"):
    """打印子标题"""
    print(f"\n{char * 60}")
    print(f"  {title}")
    print(char * 60)

def run_agent_loop_demo():
    """运行一次完整的 Agent Loop 演示"""
    print_section("🚀 Agent Loop 执行演示", "=")
    print("\n本脚本将运行一次完整的 Agent Loop，展示：")
    print("  1. 市场数据获取")
    print("  2. Multi-Analyst Discussion (4个分析师 + Coordinator)")
    print("  3. 工具调用详情")
    print("  4. Agent讨论历史")
    print("  5. Risk Analyst 评估")
    print("  6. Trader Agent 决策")
    print("\n预计执行时间: 1-3分钟\n")
    
    try:
        # 1. 加载配置
        print_section("📋 Step 1: 加载配置", "=")
        from src.utils.config_loader import load_config
        config = load_config()
        universe = config.get("universe", [])[:10]  # 只使用前10个股票以加快速度
        tool_budget = config.get("discussion_tool_budget", 15)
        rounds = config.get("discussion_rounds", 3)
        
        print(f"  ✅ 配置加载成功")
        print(f"  - Universe: {len(universe)} 个股票 (演示使用前10个)")
        print(f"  - Tool Budget: {tool_budget}")
        print(f"  - Discussion Rounds: {rounds}")
        print(f"  - Universe symbols: {', '.join(universe[:10])}")
        
        # 2. 获取市场数据
        print_section("📊 Step 2: 获取市场数据", "=")
        from src.tools.market_tools import fetch_market_batch
        
        end_date = date.today().isoformat()
        start_date = (date.today() - timedelta(days=30)).isoformat()
        
        print(f"  📅 日期范围: {start_date} 到 {end_date}")
        print(f"  🔄 正在获取市场数据...")
        
        market_data = fetch_market_batch.invoke({
            "symbols": universe[:10],
            "start": start_date,
            "end": end_date,
        })
        
        stocks_data = market_data.get("stocks", {})
        print(f"  ✅ 市场数据获取成功")
        print(f"  - 获取到 {len(stocks_data)} 个股票的数据")
        print(f"  - 数据包含: price, signal_score, indicators 等")
        
        # 显示部分数据示例
        if stocks_data:
            sample_symbol = list(stocks_data.keys())[0]
            sample_data = stocks_data[sample_symbol]
            print(f"\n  📈 示例数据 ({sample_symbol}):")
            print(f"    - Price: ${sample_data.get('price', 'N/A')}")
            print(f"    - Signal Score: {sample_data.get('signal_score', 'N/A')}")
            if 'indicators' in sample_data:
                indicators = sample_data['indicators']
                print(f"    - RSI: {indicators.get('rsi', 'N/A')}")
                print(f"    - MACD: {indicators.get('macd', 'N/A')}")
        
        # 3. 运行 Multi-Analyst Discussion
        print_section("🤖 Step 3: Multi-Analyst Discussion", "=")
        print(f"  🔄 开始运行 Agent Loop...")
        print(f"  - 将运行 {rounds} 轮讨论")
        print(f"  - 工具预算: {tool_budget}")
        print(f"\n  ⏳ 这可能需要 30-60 秒...\n")
        
        from src.agents.multi_analyst_system import run_multi_analyst_discussion
        
        # 准备market_view
        market_view = {
            "stocks": stocks_data,
            "date": end_date,
            "market_status": "open"  # 假设市场开盘
        }
        
        # 运行讨论
        discussion_result = run_multi_analyst_discussion(
            market_view=market_view,
            use_tools=True,
            tool_budget=tool_budget,
            current_positions=None,  # 演示时不使用持仓
            portfolio_value=None,
            available_cash=None,
        )
        
        # 4. 显示讨论结果
        print_section("💬 Step 4: Agent 讨论结果", "=")
        
        analyst_reports = discussion_result.get("analyst_reports", {})
        discussion_history = discussion_result.get("discussion_history", [])
        
        print(f"\n  📊 Analyst Reports:")
        for analyst_name, report in analyst_reports.items():
            stance = report.get("stance", "N/A")
            print(f"    - {analyst_name.capitalize()}: {stance}")
        
        # 显示讨论历史
        print(f"\n  📝 Discussion History ({len(discussion_history)} 条记录):")
        for i, entry in enumerate(discussion_history[:10], 1):  # 只显示前10条
            analyst = entry.get("analyst", "Unknown")
            stance = entry.get("stance", "neutral")
            tools_used = entry.get("tools_used", [])
            print(f"\n    [{i}] {analyst} (Stance: {stance})")
            if tools_used:
                print(f"        Tools: {', '.join(tools_used)}")
            analysis = entry.get("analysis", "")
            if analysis:
                preview = analysis[:100] + "..." if len(analysis) > 100 else analysis
                print(f"        Analysis: {preview}")
        
        # 5. 显示工具调用统计
        print_section("🔧 Step 5: 工具调用统计", "=")
        
        all_tool_calls = []
        for entry in discussion_history:
            tools_used = entry.get("tools_used", [])
            if tools_used:
                all_tool_calls.extend(tools_used)
        
        # 统计工具使用
        tool_counts = {}
        for tool in all_tool_calls:
            tool_counts[tool] = tool_counts.get(tool, 0) + 1
        
        print(f"\n  📊 工具调用统计:")
        print(f"    - 总调用次数: {len(all_tool_calls)}")
        print(f"    - 不同工具数: {len(tool_counts)}")
        print(f"\n  🔧 工具使用详情:")
        for tool, count in sorted(tool_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {tool}: {count} 次")
        
        # 6. 显示最终共识
        print_section("🎯 Step 6: 最终共识", "=")
        
        final_stance = discussion_result.get("final_stance", "N/A")
        recommended_stocks = discussion_result.get("recommended_stocks", [])
        
        print(f"\n  📊 Final Stance: {final_stance}")
        print(f"\n  💡 Recommended Stocks: {len(recommended_stocks)} 个")
        if recommended_stocks:
            print(f"    {', '.join(recommended_stocks[:10])}")
            if len(recommended_stocks) > 10:
                print(f"    ... 还有 {len(recommended_stocks) - 10} 个")
        
        # 7. 显示完整结果摘要
        print_section("📋 Step 7: 完整结果摘要", "=")
        
        print(f"\n  ✅ Agent Loop 执行完成!")
        print(f"\n  📊 执行摘要:")
        print(f"    - Analyst Reports: {len(analyst_reports)} 个")
        print(f"    - Discussion Entries: {len(discussion_history)} 条")
        print(f"    - Tool Calls: {len(all_tool_calls)} 次")
        print(f"    - Final Stance: {final_stance}")
        print(f"    - Recommended Stocks: {len(recommended_stocks)} 个")
        
        # 保存结果到文件
        output_file = ROOT / "data" / "logs" / "agent_loop_demo_result.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        result_summary = {
            "timestamp": date.today().isoformat(),
            "universe_size": len(universe[:10]),
            "tool_budget": tool_budget,
            "rounds": rounds,
            "analyst_reports": {k: {"stance": v.get("stance")} for k, v in analyst_reports.items()},
            "tool_calls": {
                "total": len(all_tool_calls),
                "unique_tools": len(tool_counts),
                "tool_counts": tool_counts
            },
            "final_stance": final_stance,
            "recommended_stocks": recommended_stocks[:20],  # 只保存前20个
            "discussion_history_count": len(discussion_history)
        }
        
        with output_file.open("w", encoding="utf-8") as f:
            json.dump(result_summary, f, indent=2, ensure_ascii=False)
        
        print(f"\n  💾 结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"\n  ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_agent_loop_demo()
    sys.exit(0 if success else 1)

