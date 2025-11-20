#!/usr/bin/env python3
"""Check tool agents in API response"""
import sys
import io
import requests
import json
from collections import Counter

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_api_tool_agents():
    """Check tool agents in API response"""
    try:
        r = requests.get('http://127.0.0.1:8000/api/agents/conversations?limit=100')
        if r.status_code != 200:
            print(f"[ERROR] API returned {r.status_code}")
            return
        
        data = r.json()
        tool_results = data.get('tool_results_by_category', {})
        
        print("=" * 60)
        print("API TOOL RESULTS BY CATEGORY")
        print("=" * 60)
        
        for category, tools in sorted(tool_results.items()):
            if not tools:
                continue
            
            print(f"\n{category.upper()} ({len(tools)} tools):")
            
            # Count by agent
            agents = Counter(t.get('agent', 'Unknown') for t in tools)
            for agent, count in sorted(agents.items(), key=lambda x: x[1], reverse=True):
                print(f"  - {agent}: {count}")
            
            # Show sample for market category
            if category == 'market':
                print(f"\n  Sample market tools:")
                for tool in tools[:5]:
                    agent = tool.get('agent', 'Unknown')
                    tool_name = tool.get('tool_name', 'Unknown')
                    print(f"    - Agent: {agent}, Tool: {tool_name}")
                
                # Check TechnicalAnalyst vs MarketAnalyst
                technical_tools = [t for t in tools if t.get('agent', '').lower() == 'technicalanalyst']
                market_analyst_tools = [t for t in tools if t.get('agent', '').lower() == 'marketanalyst']
                
                print(f"\n  Market category breakdown:")
                print(f"    - TechnicalAnalyst tools: {len(technical_tools)}")
                print(f"    - MarketAnalyst tools: {len(market_analyst_tools)}")
                
                if technical_tools:
                    print(f"\n    TechnicalAnalyst tools:")
                    for tool in technical_tools[:3]:
                        print(f"      - {tool.get('tool_name')} (agent: {tool.get('agent')})")
                
                if market_analyst_tools:
                    print(f"\n    MarketAnalyst tools:")
                    for tool in market_analyst_tools[:3]:
                        print(f"      - {tool.get('tool_name')} (agent: {tool.get('agent')})")
        
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_api_tool_agents()

