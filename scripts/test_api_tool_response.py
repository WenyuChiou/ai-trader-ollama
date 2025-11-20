#!/usr/bin/env python3
"""Test script to check API response for tool calls"""
import json
import sys
import requests
from pathlib import Path

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_api_response():
    """Test API response for tool calls"""
    print("=" * 80)
    print("Testing API Response for Tool Calls")
    print("=" * 80)
    
    api_base = "http://127.0.0.1:8000"
    url = f"{api_base}/api/agents/conversations?limit=200&include_demo=false"
    
    print(f"\n[1] Fetching from API: {url}")
    
    try:
        response = requests.get(url, timeout=30)
        if not response.ok:
            print(f"   ❌ API request failed: {response.status_code} {response.reason}")
            return False
        
        data = response.json()
        print(f"   ✅ API response received")
        
        conversations = data.get("conversations", [])
        print(f"   Total conversations: {len(conversations)}")
        
        # Check tool entries
        tool_entries = [c for c in conversations if c.get("type") == "tool"]
        print(f"   Tool entries: {len(tool_entries)}")
        
        if not tool_entries:
            print("\n   ⚠️  No tool entries found in API response")
            return False
        
        print("\n[2] Analyzing tool entries...")
        
        # Check round fields
        rounds_distribution = {}
        missing_rounds = []
        invalid_rounds = []
        memory_tools = []
        
        for entry in tool_entries:
            agent = entry.get("agent", "Unknown")
            tool_name = entry.get("tool_name", "Unknown")
            round_val = entry.get("round")
            
            if round_val is None:
                missing_rounds.append(f"{agent}:{tool_name}")
            elif round_val not in [1, 2, 3]:
                invalid_rounds.append((agent, tool_name, round_val))
            else:
                rounds_distribution[round_val] = rounds_distribution.get(round_val, 0) + 1
            
            if tool_name == "get_recent_memories":
                memory_tools.append({
                    "agent": agent,
                    "round": round_val,
                    "timestamp": entry.get("timestamp", "N/A")
                })
        
        print(f"\n   Round distribution:")
        for round_val in sorted(rounds_distribution.keys()):
            count = rounds_distribution[round_val]
            print(f"      Round {round_val}: {count} tools")
        
        print(f"\n   Memory tools (get_recent_memories): {len(memory_tools)}")
        if memory_tools:
            for mt in memory_tools[:5]:  # Show first 5
                round_status = f"Round {mt['round']}" if mt['round'] is not None else "MISSING"
                print(f"      - {mt['agent']}, {round_status}")
        
        if missing_rounds:
            print(f"\n   ⚠️  Tools missing round field: {len(missing_rounds)}")
            for missing in missing_rounds[:10]:  # Show first 10
                print(f"      - {missing}")
        
        if invalid_rounds:
            print(f"\n   ⚠️  Tools with invalid round values: {len(invalid_rounds)}")
            for agent, tool_name, round_val in invalid_rounds[:10]:  # Show first 10
                print(f"      - {agent}:{tool_name}, round={round_val} (should be 1-3)")
        
        # Check recent entries
        print("\n[3] Recent tool entries (last 10):")
        for entry in tool_entries[-10:]:
            agent = entry.get("agent", "Unknown")
            tool_name = entry.get("tool_name", "Unknown")
            round_val = entry.get("round", "MISSING")
            round_status = "✅" if round_val in [1, 2, 3] else "❌"
            print(f"   {round_status} {agent}:{tool_name}, round={round_val}")
        
        # Check sample entry structure
        if tool_entries:
            print("\n[4] Sample tool entry structure:")
            sample = tool_entries[0]
            print(f"   Keys: {list(sample.keys())}")
            print(f"   Agent: {sample.get('agent')}")
            print(f"   Tool name: {sample.get('tool_name')}")
            print(f"   Round: {sample.get('round')}")
            print(f"   Type: {sample.get('type')}")
            print(f"   Has tool_result: {bool(sample.get('tool_result'))}")
        
        # Summary
        print("\n[5] Summary:")
        all_good = True
        
        if missing_rounds:
            print(f"   ❌ {len(missing_rounds)} tools missing round field in API response")
            all_good = False
        else:
            print(f"   ✅ All tools have round field in API response")
        
        if invalid_rounds:
            print(f"   ❌ {len(invalid_rounds)} tools have invalid round values")
            all_good = False
        else:
            print(f"   ✅ All round values are valid (1-3)")
        
        if memory_tools:
            memory_valid = all(mt['round'] in [1, 2, 3] for mt in memory_tools)
            if memory_valid:
                print(f"   ✅ Memory tools have valid round fields")
            else:
                print(f"   ❌ Some memory tools have invalid round fields")
                all_good = False
        
        print("\n" + "=" * 80)
        if all_good:
            print("✅ API TEST PASSED: All tool calls have correct round fields")
            print("   Frontend should be able to display these tools")
        else:
            print("❌ API TEST FAILED: Some tool calls are missing or have invalid round fields")
            print("   Frontend may not display these tools correctly")
        print("=" * 80)
        
        return all_good
        
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Cannot connect to API at {api_base}")
        print(f"   Please make sure the API server is running")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_api_response()
    sys.exit(0 if success else 1)

