# backend/tests/test_multi_agent_loop_simple.py
"""
简化版的多 Agent 讨论系统测试
快速验证多 Agent 讨论系统是否正常工作
"""
from __future__ import annotations
import sys
from pathlib import Path

# 添加路径
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.orchestrator.trading_cycle import execute_daily_trade


def main():
    """快速测试多 Agent 讨论系统"""
    print("\n" + "="*80)
    print("Simple Multi-Agent Discussion Loop Test")
    print("="*80)
    
    # 使用少量股票进行快速测试
    test_universe = ["NVDA", "MSFT", "AAPL"]
    
    print(f"\n[TEST] Universe: {test_universe}")
    print(f"[TEST] Rounds: 2")
    print(f"[TEST] Tool budget: 4 (1 per agent)")
    
    try:
        # 执行交易循环
        print("\n[EXECUTING] Starting trading cycle...")
        result = execute_daily_trade(
            universe=test_universe,
            rounds=2,  # 减少轮数以加快测试
            auto_tools=True,
            tool_budget=4,  # 总工具预算（每个 Agent = 4 // 4 = 1）
            preferred_domains=[
                "www.reuters.com", "www.cboe.com", "www.cmegroup.com"
            ],
        )
        
        # 基本验证
        print("\n" + "="*80)
        print("RESULTS")
        print("="*80)
        
        print(f"\n[STANCE] {result.get('stance', 'N/A')}")
        print(f"[ROUNDS] {result.get('rounds', 0)}")
        
        # 多 Agent 讨论结果
        discussion = result.get("discussion", {})
        if discussion:
            consensus = discussion.get("consensus", {})
            agent_views = discussion.get("agent_views", {})
            
            print(f"\n[MULTI-AGENT DISCUSSION]")
            print(f"  Final stance: {consensus.get('final_stance', 'N/A')}")
            
            if agent_views:
                print("  Agent viewpoints:")
                for agent_name, view in agent_views.items():
                    viewpoint = view.get("viewpoint", "N/A")
                    print(f"    - {agent_name}: {viewpoint}")
            
            discussion_rounds = discussion.get("discussion_rounds", [])
            print(f"  Discussion rounds: {len(discussion_rounds)}")
        
        # 验证关键字段
        required_fields = [
            "stance", "decision", "discussion", "risk_report",
            "stock_selection", "market_analysis"
        ]
        
        print("\n[VALIDATION]")
        all_ok = True
        for field in required_fields:
            has_field = field in result
            status = "[OK]" if has_field else "[FAIL]"
            print(f"  {status} {field}: {has_field}")
            if not has_field:
                all_ok = False
        
        # 验证多 Agent 讨论结构
        if discussion:
            consensus = discussion.get("consensus", {})
            agent_views = discussion.get("agent_views", {})
            
            print("\n[MULTI-AGENT VALIDATION]")
            print(f"  [OK] Has consensus: {consensus is not None}")
            print(f"  [OK] Has agent_views: {len(agent_views) > 0}")
            
            expected_agents = ["technical", "fundamental", "risk", "sentiment"]
            for agent_name in expected_agents:
                has_view = agent_name in agent_views
                status = "[OK]" if has_view else "[FAIL]"
                print(f"  {status} {agent_name} in agent_views")
                if not has_view:
                    all_ok = False
        
        print("\n" + "="*80)
        if all_ok:
            print("PASS: All checks passed!")
        else:
            print("FAIL: Some checks failed!")
        print("="*80)
        
        return 0 if all_ok else 1
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

