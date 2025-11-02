# backend/tests/test_multi_agent_loop_quick.py
"""
快速测试多 Agent 讨论系统（最小配置）
用于快速验证系统是否正常工作
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
    """快速测试"""
    print("\n" + "="*80)
    print("Quick Multi-Agent Discussion Loop Test")
    print("="*80)
    
    # 最小配置
    test_universe = ["NVDA", "MSFT"]
    
    print(f"\n[CONFIG]")
    print(f"  Universe: {test_universe}")
    print(f"  Rounds: 1 (quick test)")
    print(f"  Tool budget: 4")
    
    try:
        result = execute_daily_trade(
            universe=test_universe,
            rounds=1,  # 只跑 1 轮以加快测试
            auto_tools=True,
            tool_budget=4,
            preferred_domains=["www.reuters.com"],
        )
        
        print("\n[RESULTS]")
        print(f"  Stance: {result.get('stance', 'N/A')}")
        print(f"  Rounds: {result.get('rounds', 0)}")
        
        # 检查多 Agent 讨论
        discussion = result.get("discussion", {})
        if discussion:
            consensus = discussion.get("consensus", {})
            agent_views = discussion.get("agent_views", {})
            
            print(f"\n[MULTI-AGENT]")
            print(f"  Final stance: {consensus.get('final_stance', 'N/A')}")
            print(f"  Agents: {len(agent_views)}")
            
            for agent_name in ["technical", "fundamental", "risk", "sentiment"]:
                if agent_name in agent_views:
                    viewpoint = agent_views[agent_name].get("viewpoint", "N/A")
                    print(f"    - {agent_name}: {viewpoint}")
        
        print("\n[STATUS] OK")
        return 0
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

