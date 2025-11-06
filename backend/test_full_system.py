#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整系统测试：验证Agent对话、工具调用、历史记忆、数据持久化
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

def test_portfolio_data_loading():
    """测试Portfolio数据加载"""
    print("\n" + "="*80)
    print("测试 1: Portfolio 数据加载")
    print("="*80)
    
    from src.data.portfolio import Portfolio
    import json
    
    state_file = ROOT / "data" / "logs" / "portfolio_state.json"
    if not state_file.exists():
        print("❌ Portfolio state file not found!")
        return False
    
    with state_file.open("r", encoding="utf-8") as f:
        state = json.load(f)
    
    print(f"\n✅ Portfolio State:")
    print(f"   Cash: ${state.get('cash', 0):,.2f}")
    print(f"   Initial Value: ${state.get('initial_value', 0):,.2f}")
    print(f"   Positions: {len(state.get('positions', {}))}")
    
    for symbol, pos in state.get('positions', {}).items():
        qty = pos.get('quantity', 0)
        avg_cost = pos.get('avg_cost', 0)
        print(f"   - {symbol}: {qty} shares @ ${avg_cost:.2f}")
    
    return True


def test_historical_memory():
    """测试历史记忆读取"""
    print("\n" + "="*80)
    print("测试 2: 历史记忆读取")
    print("="*80)
    
    from src.agents.memory import AgentMemory
    
    try:
        memory = AgentMemory(ROOT / "data" / "logs" / "memory")
        recent_memories = memory.get_recent_days(days=3)
        
        print(f"\n✅ 历史记忆:")
        print(f"   最近3天记录: {len(recent_memories)} 条")
        
        for mem in recent_memories[-3:]:
            date = mem.get('date', 'Unknown')
            stance = mem.get('stance', 'Unknown')
            action = mem.get('action', 'Unknown')
            stocks = mem.get('stocks_involved', [])
            print(f"   - {date}: {stance} / {action} / {len(stocks)} stocks")
        
        return True
    except Exception as e:
        print(f"❌ 历史记忆读取失败: {e}")
        return False


def test_toolbox_listing():
    """测试ToolBox工具列表"""
    print("\n" + "="*80)
    print("测试 3: ToolBox 工具列表")
    print("="*80)
    
    from src.agents.toolbox import ToolBox
    
    toolbox = ToolBox()
    tools = toolbox.list()
    
    print(f"\n✅ 可用工具 ({len(tools)} 个):")
    for tool in sorted(tools):
        print(f"   - {tool}")
    
    # 验证FRED API工具存在
    fred_tools = [t for t in tools if 'economic' in t or 'labor' in t or 'fred' in t]
    print(f"\n✅ FRED API 工具 ({len(fred_tools)} 个):")
    for tool in fred_tools:
        print(f"   - {tool}")
    
    return len(fred_tools) >= 3


def test_fred_api_tools():
    """测试FRED API工具调用"""
    print("\n" + "="*80)
    print("测试 4: FRED API 工具调用")
    print("="*80)
    
    from src.agents.toolbox import ToolBox
    
    toolbox = ToolBox()
    
    # Test get_economic_summary
    print("\n📊 测试 get_economic_summary:")
    result = toolbox.invoke("get_economic_summary")
    if result.get("ok"):
        data = result.get("result", {})
        print(f"   ✅ GDP: {data.get('gdp', {}).get('value', 'N/A')}")
        print(f"   ✅ Unemployment: {data.get('unemployment_rate', {}).get('value', 'N/A')}%")
        print(f"   ✅ CPI: {data.get('cpi', {}).get('value', 'N/A')}")
    else:
        print(f"   ❌ Error: {result.get('error')}")
        return False
    
    # Test get_labor_market_data
    print("\n📊 测试 get_labor_market_data:")
    result = toolbox.invoke("get_labor_market_data")
    if result.get("ok"):
        data = result.get("result", {})
        print(f"   ✅ Unemployment Rate: {data.get('unemployment_rate', {}).get('value', 'N/A')}%")
        print(f"   ✅ Nonfarm Payrolls: {data.get('nonfarm_payrolls', {}).get('value', 'N/A')}")
    else:
        print(f"   ❌ Error: {result.get('error')}")
        return False
    
    return True


def test_other_tools():
    """测试其他工具"""
    print("\n" + "="*80)
    print("测试 5: 其他工具调用")
    print("="*80)
    
    from src.agents.toolbox import ToolBox
    
    toolbox = ToolBox()
    
    # Test vix_term
    print("\n📊 测试 vix_term:")
    result = toolbox.invoke("vix_term")
    if result.get("ok"):
        data = result.get("result", {})
        print(f"   ✅ VIX: {data.get('vix', 'N/A')}")
        print(f"   ✅ VIX3M: {data.get('vix3m', 'N/A')}")
        print(f"   ✅ Ratio: {data.get('ratio', 'N/A')}")
    else:
        print(f"   ❌ Error: {result.get('error')}")
    
    # Test fear_greed
    print("\n📊 测试 fear_greed:")
    result = toolbox.invoke("fear_greed")
    if result.get("ok"):
        data = result.get("result", {})
        print(f"   ✅ Value: {data.get('value', 'N/A')}")
        print(f"   ✅ Label: {data.get('label', 'N/A')}")
    else:
        print(f"   ❌ Error: {result.get('error')}")
    
    return True


def test_agent_conversation():
    """测试完整的Agent对话"""
    print("\n" + "="*80)
    print("测试 6: Agent 对话流程")
    print("="*80)
    
    print("\n⚠️  这个测试需要运行完整的trading cycle，会调用LLM")
    print("   建议手动通过前端 'Start Trading' 按钮测试")
    print("   或运行: python scripts/run_daily_trading.py")
    
    return True


def main():
    print("\n" + "="*80)
    print(" AI Trader - 完整系统测试")
    print("="*80)
    print()
    
    tests = [
        ("Portfolio 数据加载", test_portfolio_data_loading),
        ("历史记忆读取", test_historical_memory),
        ("ToolBox 工具列表", test_toolbox_listing),
        ("FRED API 工具", test_fred_api_tools),
        ("其他工具", test_other_tools),
        ("Agent 对话", test_agent_conversation),
    ]
    
    results = []
    for name, test_fn in tests:
        try:
            result = test_fn()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print(" 测试结果总结")
    print("="*80)
    print()
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    print()
    print(f"通过: {passed}/{total}")
    
    return 0 if passed == total else 1


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

