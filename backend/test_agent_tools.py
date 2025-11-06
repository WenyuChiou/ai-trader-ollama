#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Agent工具调用：确保agent能成功调用工具并输出正确信息
"""
import sys
import os
from pathlib import Path
import json

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

# Set FRED API key
os.environ["FRED_API_KEY"] = "b04875b1abf3f24890b57ea2cee6b5e1"


def test_toolbox_direct():
    """直接测试ToolBox工具调用"""
    print("\n" + "="*80)
    print("测试 1: 直接调用ToolBox工具")
    print("="*80)
    
    from src.agents.toolbox import ToolBox
    
    toolbox = ToolBox()
    
    # Test 1: vix_term
    print("\n📊 测试 vix_term:")
    result = toolbox.invoke("vix_term")
    if result.get("ok"):
        data = result.get("result", {})
        vix = data.get('vix')
        vix3m = data.get('vix3m')
        ratio = data.get('ratio')
        print(f"   ✅ VIX: {vix:.2f}")
        print(f"   ✅ VIX3M: {vix3m:.2f}")
        print(f"   ✅ Ratio: {ratio:.4f}")
        assert vix is not None and vix > 0, "VIX should be positive"
        assert vix3m is not None and vix3m > 0, "VIX3M should be positive"
    else:
        print(f"   ❌ Error: {result.get('error')}")
        return False
    
    # Test 2: fear_greed
    print("\n📊 测试 fear_greed:")
    result = toolbox.invoke("fear_greed")
    if result.get("ok"):
        data = result.get("result", {})
        value = data.get('value')
        label = data.get('label')
        print(f"   ✅ Value: {value}")
        print(f"   ✅ Label: {label}")
        assert value is not None and 0 <= value <= 100, "Fear & Greed should be 0-100"
        assert label in ['Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'], f"Invalid label: {label}"
    else:
        print(f"   ❌ Error: {result.get('error')}")
        return False
    
    # Test 3: get_economic_summary (FRED API)
    print("\n📊 测试 get_economic_summary (FRED API):")
    result = toolbox.invoke("get_economic_summary")
    if result.get("ok"):
        # toolbox返回{"ok": True, "result": string_data}
        data = result.get("result", "")
        # 如果result是嵌套的dict，提取内部的result
        if isinstance(data, dict) and "result" in data:
            data = data.get("result", "")
        print(f"   ✅ Result length: {len(str(data))} characters")
        data_str = str(data)
        print(f"   Preview:\n{data_str[:300]}...")
        assert "GDP" in data_str or "Unemployment" in data_str or "CPI" in data_str, "Should contain economic data"
        assert "FRED" in data_str, "Should mention FRED"
    else:
        print(f"   ❌ Error: {result.get('error')}")
        return False
    
    # Test 4: get_labor_market_data (FRED API)
    print("\n📊 测试 get_labor_market_data (FRED API):")
    result = toolbox.invoke("get_labor_market_data")
    if result.get("ok"):
        data = result.get("result", "")
        if isinstance(data, dict) and "result" in data:
            data = data.get("result", "")
        data_str = str(data)
        print(f"   ✅ Result length: {len(data_str)} characters")
        print(f"   Preview:\n{data_str[:300]}...")
        assert "Unemployment" in data_str or "Payrolls" in data_str or "Labor" in data_str, "Should contain labor market data"
    else:
        print(f"   ❌ Error: {result.get('error')}")
        return False
    
    # Test 5: news_scan
    print("\n📊 测试 news_scan:")
    result = toolbox.invoke("news_scan", keywords=["market", "AI"], max_articles=5, recency_days=7)
    if result.get("ok"):
        data = result.get("result", {})
        hits = data.get('hits', [])
        # hits可能是列表也可能是数字
        if isinstance(hits, list):
            hits_count = len(hits)
            articles = hits  # hits就是articles列表
        else:
            hits_count = int(hits)
            articles = data.get('articles', [])
        print(f"   ✅ Hits: {hits_count}")
        print(f"   ✅ Articles returned: {len(articles)}")
        if articles:
            sample = articles[0]
            if isinstance(sample, dict):
                print(f"   Sample article: {sample.get('title', 'N/A')[:80]}...")
        assert hits_count >= 0, "Hits should be non-negative"
    else:
        print(f"   ❌ Error: {result.get('error')}")
        return False
    
    print("\n✅ 所有工具测试通过!")
    return True


def test_risk_analyst():
    """测试Risk Analyst风险评估"""
    print("\n" + "="*80)
    print("测试 2: Risk Analyst 风险评估")
    print("="*80)
    
    from src.agents.risk_analyst import run_risk_analyst
    
    # 准备测试数据
    market_json = {
        "stocks": {
            "NVDA": {
                "symbol": "NVDA",
                "last_price": 900.0,
                "change_pct": 2.5,
                "volume": 50000000,
                "signal_score": 0.7
            },
            "MSFT": {
                "symbol": "MSFT",
                "last_price": 420.0,
                "change_pct": 1.2,
                "volume": 30000000,
                "signal_score": 0.5
            },
            "AAPL": {
                "symbol": "AAPL",
                "last_price": 190.0,
                "change_pct": -0.5,
                "volume": 40000000,
                "signal_score": 0.3
            }
        }
    }
    
    current_positions = {
        "NVDA": {"quantity": 5, "avg_cost": 900.0},
        "MSFT": {"quantity": 7, "avg_cost": 420.0},
        "AAPL": {"quantity": 10, "avg_cost": 190.0}
    }
    
    portfolio_value = 10000.0
    
    print("\n📊 运行Risk Analyst...")
    print(f"   Portfolio Value: ${portfolio_value:,.2f}")
    print(f"   Positions: {len(current_positions)}")
    
    try:
        risk_report = run_risk_analyst(
            market_json=market_json,
            current_positions=current_positions,
            portfolio_value=portfolio_value
        )
        
        print(f"\n✅ Risk Report生成成功！")
        print(f"   Overall Risk Level: {risk_report.get('overall_risk_level', 'N/A')}")
        print(f"   Risk Score: {risk_report.get('risk_score', 'N/A')}")
        print(f"   High Risk Stocks: {len(risk_report.get('high_risk_stocks', []))}")
        print(f"   Safe Stocks: {len(risk_report.get('safe_stocks', []))}")
        
        # 检查Position Control Report
        if 'position_control_report' in risk_report:
            pcr = risk_report['position_control_report']
            print(f"   Position Control Report:")
            print(f"     - Position Limit Checks: {len(pcr.get('position_limit_checks', []))}")
            print(f"     - Recommended Sizes: {len(pcr.get('recommended_position_sizes', {}))}")
        
        assert 'overall_risk_level' in risk_report, "Should contain overall_risk_level"
        assert 'risk_score' in risk_report, "Should contain risk_score"
        assert 'position_control_report' in risk_report, "Should contain position_control_report"
        
        return True
        
    except Exception as e:
        print(f"\n❌ Risk Analyst失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "="*80)
    print(" AI Trader - Agent工具调用测试")
    print("="*80)
    print()
    
    tests = [
        ("直接调用ToolBox工具", test_toolbox_direct),
        ("Risk Analyst风险评估", test_risk_analyst),
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
    
    if passed == total:
        print("\n🎉 所有测试通过！Agent工具调用正常！")
    
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

