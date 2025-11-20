#!/usr/bin/env python3
"""Check tool entries agent field"""
import sys
import io
import json
from pathlib import Path
from collections import Counter

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_tool_agents():
    """Check tool entries and their agent fields"""
    log_file = Path('data/logs/discussion_actions.jsonl')
    
    if not log_file.exists():
        print("[ERROR] File does not exist!")
        return
    
    with log_file.open('r', encoding='utf-8') as f:
        lines = f.readlines()
    
    tools = []
    for line in lines:
        if line.strip():
            try:
                entry = json.loads(line.strip())
                if entry.get('type') == 'tool':
                    tools.append(entry)
            except:
                pass
    
    print("=" * 60)
    print("TOOL AGENT FIELD CHECK")
    print("=" * 60)
    
    # Group by category
    by_category = {}
    for tool in tools:
        category = tool.get('tool_category', 'other')
        if category not in by_category:
            by_category[category] = []
        by_category[category].append(tool)
    
    print(f"\nTotal tools: {len(tools)}")
    print(f"\nTools by category:")
    for category, category_tools in sorted(by_category.items()):
        print(f"\n  {category.upper()} ({len(category_tools)} tools):")
        
        # Count by agent
        agents = Counter(t.get('agent', 'Unknown') for t in category_tools)
        for agent, count in sorted(agents.items(), key=lambda x: x[1], reverse=True):
            print(f"    - {agent}: {count}")
        
        # Show sample tools for market category
        if category == 'market':
            print(f"\n    Sample market tools:")
            for tool in category_tools[:5]:
                agent = tool.get('agent', 'Unknown')
                tool_name = tool.get('tool_name', 'Unknown')
                print(f"      - Agent: {agent}, Tool: {tool_name}")
    
    # Check for potential mismatches
    print(f"\n\nPOTENTIAL ISSUES:")
    
    # Check market category
    market_tools = by_category.get('market', [])
    if market_tools:
        market_agents = set(t.get('agent', 'Unknown') for t in market_tools)
        print(f"\n  Market category tools have agents: {sorted(market_agents)}")
        
        # Check if TechnicalAnalyst tools are in market category
        technical_tools = [t for t in market_tools if t.get('agent', '').lower() == 'technicalanalyst']
        market_analyst_tools = [t for t in market_tools if t.get('agent', '').lower() == 'marketanalyst']
        
        print(f"    - TechnicalAnalyst tools in market: {len(technical_tools)}")
        print(f"    - MarketAnalyst tools in market: {len(market_analyst_tools)}")
        
        if technical_tools:
            print(f"\n    TechnicalAnalyst market tools:")
            for tool in technical_tools[:3]:
                print(f"      - {tool.get('tool_name')} (round: {tool.get('round', 'N/A')})")
        
        if market_analyst_tools and not technical_tools:
            print(f"\n    [WARN] Market category has MarketAnalyst tools but no TechnicalAnalyst tools!")
            print(f"    [WARN] This may cause filtering issues for TechnicalAnalyst")

if __name__ == "__main__":
    check_tool_agents()

