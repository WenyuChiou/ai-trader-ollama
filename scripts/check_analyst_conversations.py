#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check analyst conversations in discussion_actions.jsonl
"""
import json
from pathlib import Path
from collections import defaultdict

def check_analyst_conversations():
    log_file = Path(__file__).parent.parent / "data" / "logs" / "discussion_actions.jsonl"
    
    if not log_file.exists():
        print(f"Error: File not found at {log_file}")
        return
    
    entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    
    # Filter discussion entries
    discussions = [e for e in entries if e.get('type') == 'discussion']
    
    # Group by agent
    agents = defaultdict(list)
    for e in discussions:
        agent = e.get('agent', 'Unknown')
        agents[agent].append(e)
    
    print("=" * 80)
    print("Analyst Conversations Summary")
    print("=" * 80)
    print(f"\nTotal discussion entries: {len(discussions)}")
    print(f"\nAgents found:")
    for agent in sorted(agents.keys()):
        count = len(agents[agent])
        rounds = set(e.get('round', 0) for e in agents[agent])
        print(f"  {agent}: {count} entries, rounds: {sorted(rounds)}")
    
    # Check for required analysts
    required_analysts = ['MarketAnalyst', 'TechnicalAnalyst', 'FundamentalAnalyst', 'SentimentAnalyst']
    print(f"\nRequired analysts check:")
    for agent in required_analysts:
        if agent in agents:
            latest = max(agents[agent], key=lambda x: x.get('timestamp', ''))
            round_num = latest.get('round', 0)
            summary = latest.get('summary', latest.get('content', ''))[:60]
            print(f"  ✓ {agent}: Found (round={round_num}, latest: {summary}...)")
        else:
            print(f"  ✗ {agent}: NOT FOUND")
    
    # Show last 20 discussion entries
    print(f"\nLast 20 discussion entries:")
    for i, e in enumerate(discussions[-20:], 1):
        agent = e.get('agent', 'Unknown')
        round_num = e.get('round', 0)
        summary = e.get('summary', e.get('content', ''))
        if isinstance(summary, str):
            summary_preview = summary[:60] + '...' if len(summary) > 60 else summary
        else:
            summary_preview = str(summary)[:60] + '...'
        print(f"  {i}. {agent} (round={round_num}): {summary_preview}")

if __name__ == "__main__":
    check_analyst_conversations()

