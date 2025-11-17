"""
检查所有 Agent 的 Summary 是否正常
"""
import sys
import json
from pathlib import Path

# Add project paths
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(project_root))

def check_summaries(result_file: str = None):
    """检查交易结果中所有 agent 的 summary"""
    
    if result_file:
        # 从文件读取结果
        with open(result_file, 'r', encoding='utf-8') as f:
            result = json.load(f)
    else:
        # 从最近的 memory 文件读取
        memory_dir = project_root / "data" / "logs"
        memory_files = sorted(memory_dir.glob("daily_memory_*.json"), reverse=True)
        if not memory_files:
            print("[ERROR] No memory files found")
            return
        
        latest_memory = memory_files[0]
        print(f"[INFO] Reading from: {latest_memory}")
        with open(latest_memory, 'r', encoding='utf-8') as f:
            result = json.load(f)
    
    print("\n" + "="*70)
    print("AGENT SUMMARY CHECK")
    print("="*70 + "\n")
    
    # 1. Check Trader Agent Summary
    print("[1] Trader Agent Summary")
    print("-" * 70)
    decision = result.get("decision", {})
    trader_summary = decision.get("summary", "")
    trader_rationale = decision.get("rationale", "")
    
    if trader_summary:
        print(f"  ✅ Summary found: {len(trader_summary)} chars")
        print(f"     Preview: {trader_summary[:150]}...")
        if "no_op" in trader_summary.lower() or "uncertainty_reason" in trader_summary.lower():
            print(f"  ❌ ERROR: Summary contains error!")
        elif len(trader_summary.strip()) < 50:
            print(f"  ⚠️  WARNING: Summary too short ({len(trader_summary)} chars)")
        else:
            print(f"  ✅ Summary is valid")
    else:
        print(f"  ❌ ERROR: No summary found")
    
    if trader_rationale:
        print(f"  ✅ Rationale found: {len(trader_rationale)} chars")
    
    # 2. Check Risk Analyst Summary
    print("\n[2] Risk Analyst Summary")
    print("-" * 70)
    risk_report = result.get("risk_report", {})
    risk_analysis = risk_report.get("analysis", "")
    
    if risk_analysis:
        print(f"  ✅ Analysis found: {len(risk_analysis)} chars")
        print(f"     Preview: {risk_analysis[:150]}...")
        if len(risk_analysis.strip()) < 50:
            print(f"  ⚠️  WARNING: Analysis too short ({len(risk_analysis)} chars)")
        else:
            print(f"  ✅ Analysis is valid")
    else:
        print(f"  ❌ ERROR: No analysis found")
    
    # 3. Check Market Analyst Summary
    print("\n[3] Market Analyst Summary")
    print("-" * 70)
    market_analysis = result.get("market_analysis", {})
    market_sentiment = market_analysis.get("market_sentiment", "")
    recommended_stocks = market_analysis.get("recommended_stocks", [])
    
    if market_sentiment:
        print(f"  ✅ Market sentiment: {market_sentiment}")
    else:
        print(f"  ⚠️  WARNING: No market sentiment")
    
    if recommended_stocks:
        print(f"  ✅ Recommended stocks: {len(recommended_stocks)} stocks")
    else:
        print(f"  ⚠️  WARNING: No recommended stocks")
    
    # 4. Check Discussion Coordinator Summary
    print("\n[4] Discussion Coordinator Summary")
    print("-" * 70)
    discussion = result.get("discussion", {})
    coordinator_summary = discussion.get("coordinator_summary", {})
    
    if coordinator_summary:
        if isinstance(coordinator_summary, dict):
            coord_summary_text = coordinator_summary.get("summary", "")
            coord_stance = coordinator_summary.get("stance", "")
            
            if coord_summary_text:
                print(f"  ✅ Summary found: {len(coord_summary_text)} chars")
                print(f"     Stance: {coord_stance}")
                print(f"     Preview: {coord_summary_text[:150]}...")
                if len(coord_summary_text.strip()) < 100:
                    print(f"  ⚠️  WARNING: Summary too short ({len(coord_summary_text)} chars)")
                else:
                    print(f"  ✅ Summary is valid")
            else:
                print(f"  ❌ ERROR: Summary text is empty")
        else:
            print(f"  ⚠️  WARNING: coordinator_summary is not a dict: {type(coordinator_summary)}")
    else:
        print(f"  ❌ ERROR: No coordinator_summary found in discussion")
        print(f"     Available keys: {list(discussion.keys())}")
    
    # 5. Check Discussion Transcript (Rounds)
    print("\n[5] Discussion Transcript (Rounds)")
    print("-" * 70)
    transcript = discussion.get("transcript", [])
    rounds = discussion.get("rounds", 0)
    
    if transcript:
        print(f"  ✅ Transcript found: {len(transcript)} rounds")
        for i, round_text in enumerate(transcript, 1):
            print(f"     Round {i}: {len(round_text)} chars")
            # 尝试提取 stance
            if "stance" in round_text.lower():
                if '"stance"' in round_text:
                    try:
                        import re
                        stance_match = re.search(r'"stance"\s*:\s*"([^"]+)"', round_text)
                        if stance_match:
                            print(f"              Stance: {stance_match.group(1)}")
                    except:
                        pass
    else:
        print(f"  ❌ ERROR: No transcript found")
    
    if rounds:
        print(f"  ✅ Total rounds: {rounds}")
    else:
        print(f"  ⚠️  WARNING: No rounds count")
    
    # 6. Check Tool Context
    print("\n[6] Tool Context")
    print("-" * 70)
    tool_context = discussion.get("tool_context", [])
    
    if tool_context:
        print(f"  ✅ Tool context found: {len(tool_context)} tools")
        for tool in tool_context[:5]:
            print(f"     - {tool}")
    else:
        print(f"  ⚠️  WARNING: No tool context")
    
    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    all_ok = True
    if not trader_summary or len(trader_summary.strip()) < 50:
        print("  ❌ Trader Agent summary: FAILED")
        all_ok = False
    else:
        print("  ✅ Trader Agent summary: OK")
    
    if not risk_analysis or len(risk_analysis.strip()) < 50:
        print("  ❌ Risk Analyst summary: FAILED")
        all_ok = False
    else:
        print("  ✅ Risk Analyst summary: OK")
    
    if not market_sentiment or not recommended_stocks:
        print("  ⚠️  Market Analyst: WARNING (missing some fields)")
    else:
        print("  ✅ Market Analyst: OK")
    
    if not coordinator_summary or not isinstance(coordinator_summary, dict) or not coordinator_summary.get("summary"):
        print("  ❌ Coordinator summary: FAILED")
        all_ok = False
    else:
        coord_text = coordinator_summary.get("summary", "")
        if len(coord_text.strip()) < 100:
            print("  ⚠️  Coordinator summary: WARNING (too short)")
        else:
            print("  ✅ Coordinator summary: OK")
    
    if not transcript:
        print("  ❌ Discussion transcript: FAILED")
        all_ok = False
    else:
        print(f"  ✅ Discussion transcript: OK ({len(transcript)} rounds)")
    
    return all_ok

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="Path to result JSON file")
    args = parser.parse_args()
    
    check_summaries(args.file)

