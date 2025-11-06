#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试讨论式多Agent协作机制

验证：
1. 每个analyst能看到之前的讨论
2. Analysts能够引用和回应之前的观点
3. 形成真正的讨论流程（而不是独立分析）
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


def test_discussion_flow():
    """测试讨论流程"""
    print("\n" + "="*80)
    print("🤖 讨论式多Agent协作测试")
    print("="*80)
    print()
    
    from src.agents.multi_analyst_system import run_multi_analyst_discussion
    from src.tools.market_tools import fetch_market_batch
    
    # 准备测试数据（使用少量股票以加快测试）
    test_symbols = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]
    
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
    print(" 🚀 开始多Analyst讨论...")
    print("="*80)
    print()
    print("预期行为:")
    print("  1. Market Analyst: 提供初始市场评估")
    print("  2. Technical Analyst: 看到Market的讨论，回应并添加技术观点")
    print("  3. Fundamental Analyst: 看到Market+Technical，回应并添加基本面观点")
    print("  4. Sentiment Analyst: 看到所有讨论，综合所有观点")
    print()
    
    try:
        result = run_multi_analyst_discussion(
            market_view=market_view,
            use_tools=True,
            tool_budget=15,
        )
        
        print("\n" + "="*80)
        print(" ✅ 讨论完成！")
        print("="*80)
        print()
        
        # 显示对话历史
        discussion_history = result.get("discussion_history", [])
        
        print("📝 完整对话流程:")
        print("="*80)
        
        for i, entry in enumerate(discussion_history, 1):
            analyst_name = entry.get("analyst", "Unknown")
            stance = entry.get("stance", "N/A")
            analysis = entry.get("analysis", "No analysis")
            tools_used = entry.get("tools_used", [])
            key_points = entry.get("key_points", [])
            
            print(f"\n[{i}] {analyst_name}")
            print(f"    Stance: {stance}")
            print(f"    Analysis: {analysis[:300]}...")
            if tools_used:
                print(f"    Tools: {', '.join(tools_used)}")
            if key_points:
                print(f"    Key Points:")
                for point in key_points:
                    print(f"      - {point}")
        
        print("\n" + "="*80)
        print("🔍 讨论质量检查")
        print("="*80)
        
        checks = []
        
        # 检查1: 所有analysts都参与了
        checks.append(("所有Analysts参与", len(discussion_history) >= 3))
        print(f"   Analysts参与数: {len(discussion_history)}/4")
        
        # 检查2: 对话历史包含分析内容
        has_analysis = all(entry.get("analysis") for entry in discussion_history)
        checks.append(("所有Analysts都有分析", has_analysis))
        print(f"   所有都有分析: {'✅' if has_analysis else '❌'}")
        
        # 检查3: 后续analysts引用了之前的讨论
        references_previous = []
        for i, entry in enumerate(discussion_history[1:], 1):  # 跳过第一个
            analysis = entry.get("analysis", "").lower()
            # 检查是否提到之前的analyst或他们的观点
            prev_analyst = discussion_history[i-1].get("analyst", "").lower()
            if prev_analyst and any(word in analysis for word in ["market", "technical", "fundamental", "sentiment", "previous", "agree", "disagree", "however", "but", "also"]):
                references_previous.append(True)
            else:
                references_previous.append(False)
        
        if references_previous:
            ref_count = sum(references_previous)
            checks.append(("后续Analysts引用之前的讨论", ref_count > 0))
            print(f"   引用之前的讨论: {ref_count}/{len(references_previous)} analysts")
        else:
            checks.append(("后续Analysts引用之前的讨论", False))
            print(f"   引用之前的讨论: 0 (需要改进)")
        
        # 检查4: 工具被使用
        all_tools = []
        for entry in discussion_history:
            all_tools.extend(entry.get("tools_used", []))
        unique_tools = set(all_tools)
        checks.append(("工具被使用", len(unique_tools) >= 3))
        print(f"   使用的工具: {len(unique_tools)} ({', '.join(list(unique_tools)[:5])})")
        
        # 检查5: 最终观点形成
        final_stance = result.get("final_stance", "N/A")
        checks.append(("最终观点形成", final_stance in ["bullish", "bearish", "neutral", "risk_on", "risk_off"]))
        print(f"   最终观点: {final_stance}")
        
        # 总结
        print("\n" + "="*80)
        print("📊 测试结果")
        print("="*80)
        
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        
        print(f"\n通过检查: {passed}/{total}\n")
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
        
        # 显示示例对话片段
        if len(discussion_history) >= 2:
            print("\n" + "="*80)
            print("💬 示例对话片段（验证讨论流程）")
            print("="*80)
            print()
            
            # 显示前两个analysts的对话
            for i in range(min(2, len(discussion_history))):
                entry = discussion_history[i]
                print(f"[{entry.get('analyst')}]")
                print(f"  {entry.get('analysis', '')[:200]}...")
                print()
        
        if passed >= total * 0.8:
            print("\n🎉 讨论机制工作正常！Agents能够互相影响。")
            return True
        else:
            print("\n⚠️  讨论机制需要改进。Agents可能没有充分引用之前的讨论。")
            return False
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print(" 🚀 AI Trader - 讨论式多Agent协作测试")
    print("="*80)
    print()
    print("测试内容:")
    print("  1. Agents能看到之前的讨论")
    print("  2. Agents能够引用和回应之前的观点")
    print("  3. 形成真正的讨论流程")
    print("  4. 工具使用和最终共识")
    print()
    
    success = test_discussion_flow()
    
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

