#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多Analyst系统
验证所有analysts能够被单独调用并使用工具
"""
import sys
import os
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

# Set FRED API key
os.environ["FRED_API_KEY"] = "b04875b1abf3f24890b57ea2cee6b5e1"


def test_multi_analyst_system():
    """测试多Analyst系统"""
    print("\n" + "="*80)
    print(" 🤖 多Analyst系统测试")
    print("="*80)
    print()
    
    from src.agents.multi_analyst_system import run_multi_analyst_discussion
    from src.tools.market_tools import fetch_market_batch
    
    # 准备测试数据
    test_symbols = ["NVDA", "MSFT", "AAPL"]
    
    print(f"📊 测试参数:")
    print(f"   Symbols: {', '.join(test_symbols)}")
    print(f"   Tool Budget: 15")
    print()
    
    # 获取市场数据
    print("📈 获取市场数据...")
    market_view = fetch_market_batch.invoke({
        "symbols": test_symbols,
        "start": "2024-10-01",
        "end": "2025-01-01",
    })
    print(f"   ✅ 获取了 {len(market_view.get('stocks', {}))} 只股票数据")
    print()
    
    print("="*80)
    print(" 🚀 开始多Analyst分析...")
    print("="*80)
    
    try:
        result = run_multi_analyst_discussion(
            market_view=market_view,
            use_tools=True,
            tool_budget=15,
        )
        
        print("\n" + "="*80)
        print(" ✅ 多Analyst分析完成！")
        print("="*80)
        print()
        
        # 验证结果
        analyst_reports = result.get("analyst_reports", {})
        tool_calls = result.get("tool_calls", [])
        final_stance = result.get("final_stance", "N/A")
        
        print(f"📊 分析结果:")
        print(f"   Final Stance: {final_stance}")
        print(f"   Analysts Participated: {len(analyst_reports)}")
        print(f"   Total Tool Calls: {len(tool_calls)}")
        print()
        
        # 检查每个analyst
        for analyst_type, report in analyst_reports.items():
            print(f"\n{analyst_type.upper()} Analyst:")
            if "error" in report:
                print(f"   ❌ Error: {report['error']}")
            else:
                stance = report.get("stance", "N/A")
                score_key = f"{analyst_type}_score"
                if score_key in report:
                    score = report[score_key]
                else:
                    score = report.get("market_score", report.get("sentiment_score", "N/A"))
                print(f"   Stance: {stance}")
                print(f"   Score: {score}")
                
                # 检查工具调用
                tool_calls_for_analyst = [tc for tc in tool_calls if tc.get("analyst", "").startswith(analyst_type.capitalize())]
                if tool_calls_for_analyst:
                    print(f"   Tools Used:")
                    for tc in tool_calls_for_analyst:
                        print(f"      - {tc.get('tool', 'unknown')}")
        
        # 工具多样性检查
        tools_used = set(tc.get("tool", "") for tc in tool_calls)
        print(f"\n📋 工具多样性:")
        print(f"   Unique Tools Used: {len(tools_used)}")
        print(f"   Tools: {', '.join(sorted(tools_used))}")
        
        # 验证检查
        print("\n" + "="*80)
        print(" 📊 验证检查")
        print("="*80)
        
        checks = []
        checks.append(("Market Analyst运行", "market" in analyst_reports and "error" not in analyst_reports["market"]))
        checks.append(("Technical Analyst运行", "technical" in analyst_reports and "error" not in analyst_reports["technical"]))
        checks.append(("Fundamental Analyst运行", "fundamental" in analyst_reports and "error" not in analyst_reports["fundamental"]))
        checks.append(("Sentiment Analyst运行", "sentiment" in analyst_reports and "error" not in analyst_reports["sentiment"]))
        checks.append(("工具被使用", len(tool_calls) >= 3))
        checks.append(("工具多样性", len(tools_used) >= 3))
        checks.append(("生成最终观点", final_stance in ["bullish", "bearish", "neutral"]))
        
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        
        print(f"\n通过检查: {passed}/{total}\n")
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
        
        if passed == total:
            print(f"\n🎉 所有检查通过！多Analyst系统运行正常！")
            return True
        elif passed >= total * 0.7:
            print(f"\n⚠️  大部分检查通过，但有些地方需要改进")
            return True
        else:
            print(f"\n❌ 多个检查失败，需要调试")
            return False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print(" 🚀 AI Trader - 多Analyst系统测试")
    print("="*80)
    print()
    print("测试内容:")
    print("  1. Market Analyst - 市场整体分析")
    print("  2. Technical Analyst - 技术指标分析")
    print("  3. Fundamental Analyst - 基本面分析")
    print("  4. Sentiment Analyst - 情绪分析")
    print("  5. 工具多样性验证")
    print("  6. Analysts间协同验证")
    print()
    
    success = test_multi_analyst_system()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ 用户取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

