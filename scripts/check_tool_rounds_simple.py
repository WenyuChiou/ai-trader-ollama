#!/usr/bin/env python3
"""Simple script to check tool calls round fields in discussion_actions.jsonl"""
import json
import sys
from pathlib import Path

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_tool_rounds():
    """Check tool calls in discussion_actions.jsonl for round fields"""
    print("=" * 80)
    print("Checking Tool Calls Round Fields")
    print("=" * 80)
    
    log_file = Path("data/logs/discussion_actions.jsonl")
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return False
    
    print(f"\n[1] Reading log file: {log_file}")
    
    tool_entries = []
    all_entries = []
    
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                all_entries.append(entry)
                if entry.get('type') == 'tool' and entry.get('tool_name'):
                    tool_entries.append((line_num, entry))
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Line {line_num}: JSON decode error: {e}")
                continue
    
    print(f"   Total entries: {len(all_entries)}")
    print(f"   Tool entries: {len(tool_entries)}")
    
    if not tool_entries:
        print("\n   ⚠️  No tool entries found in log file")
        return False
    
    print("\n[2] Analyzing tool entries...")
    
    # Check round fields
    rounds_distribution = {}
    missing_rounds = []
    invalid_rounds = []
    memory_tools = []
    
    for line_num, entry in tool_entries:
        agent = entry.get('agent', 'Unknown')
        tool_name = entry.get('tool_name', 'Unknown')
        round_val = entry.get('round')
        
        if round_val is None:
            missing_rounds.append((line_num, agent, tool_name))
        elif round_val not in [1, 2, 3]:
            invalid_rounds.append((line_num, agent, tool_name, round_val))
        else:
            rounds_distribution[round_val] = rounds_distribution.get(round_val, 0) + 1
        
        if tool_name == "get_recent_memories":
            memory_tools.append({
                "line": line_num,
                "agent": agent,
                "round": round_val,
                "timestamp": entry.get('timestamp', 'N/A')
            })
    
    print(f"\n   Round distribution:")
    for round_val in sorted(rounds_distribution.keys()):
        count = rounds_distribution[round_val]
        print(f"      Round {round_val}: {count} tools")
    
    print(f"\n   Memory tools (get_recent_memories): {len(memory_tools)}")
    if memory_tools:
        for mt in memory_tools[-5:]:  # Show last 5
            round_status = f"Round {mt['round']}" if mt['round'] is not None else "MISSING"
            print(f"      Line {mt['line']}: {mt['agent']}, {round_status}")
    
    if missing_rounds:
        print(f"\n   ⚠️  Tools missing round field: {len(missing_rounds)}")
        for line_num, agent, tool_name in missing_rounds[:10]:  # Show first 10
            print(f"      Line {line_num}: {agent}:{tool_name}")
    
    if invalid_rounds:
        print(f"\n   ⚠️  Tools with invalid round values: {len(invalid_rounds)}")
        for line_num, agent, tool_name, round_val in invalid_rounds[:10]:  # Show first 10
            print(f"      Line {line_num}: {agent}:{tool_name}, round={round_val} (should be 1-3)")
    
    # Check recent entries
    print("\n[3] Recent tool entries (last 10):")
    for line_num, entry in tool_entries[-10:]:
        agent = entry.get('agent', 'Unknown')
        tool_name = entry.get('tool_name', 'Unknown')
        round_val = entry.get('round', 'MISSING')
        round_status = "✅" if round_val in [1, 2, 3] else "❌"
        print(f"   {round_status} Line {line_num}: {agent}:{tool_name}, round={round_val}")
    
    # Summary
    print("\n[4] Summary:")
    all_valid = True
    
    if missing_rounds:
        print(f"   ❌ {len(missing_rounds)} tools missing round field")
        all_valid = False
    else:
        print(f"   ✅ All tools have round field")
    
    if invalid_rounds:
        print(f"   ❌ {len(invalid_rounds)} tools have invalid round values")
        all_valid = False
    else:
        print(f"   ✅ All round values are valid (1-3)")
    
    if memory_tools:
        memory_valid = all(mt['round'] in [1, 2, 3] for mt in memory_tools)
        if memory_valid:
            print(f"   ✅ Memory tools have valid round fields")
        else:
            print(f"   ❌ Some memory tools have invalid round fields")
            all_valid = False
    
    # Check if latest entries are valid (ignore old round=0 entries)
    latest_valid = True
    if tool_entries:
        recent_invalid = [e for _, e in tool_entries[-20:] if e.get('round') not in [1, 2, 3]]
        if recent_invalid:
            latest_valid = False
            print(f"\n   ⚠️  Recent entries with invalid rounds: {len(recent_invalid)}")
        else:
            print(f"\n   ✅ All recent entries (last 20) have valid round fields")
    
    print("\n" + "=" * 80)
    if all_valid:
        print("✅ CHECK PASSED: All tool calls have correct round fields (1-3)")
        print("   Tools should be visible in frontend")
    elif latest_valid:
        print("✅ LATEST ENTRIES VALID: Recent tool calls have correct round fields (1-3)")
        print("   Old round=0 entries are from before the fix and won't affect new tools")
        print("   New tools should be visible in frontend")
    else:
        print("❌ CHECK FAILED: Some tool calls are missing or have invalid round fields")
        print("   These tools may not be visible in frontend")
    print("=" * 80)
    
    return all_valid

if __name__ == "__main__":
    success = check_tool_rounds()
    sys.exit(0 if success else 1)

