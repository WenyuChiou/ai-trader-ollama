#!/usr/bin/env python3
"""Analyze old vs new tool call records"""
import json
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def analyze_records():
    """Analyze old vs new tool call records"""
    print("=" * 80)
    print("Analyzing Old vs New Tool Call Records")
    print("=" * 80)
    
    log_file = Path("data/logs/discussion_actions.jsonl")
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        return
    
    print(f"\n[1] Reading log file: {log_file}")
    
    all_entries = []
    with open(log_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                entry = json.loads(line.strip())
                entry['_line_num'] = line_num
                all_entries.append(entry)
            except json.JSONDecodeError:
                continue
    
    print(f"   Total entries: {len(all_entries)}")
    
    # Separate by type
    tool_entries = [e for e in all_entries if e.get('type') == 'tool' and e.get('tool_name')]
    discussion_entries = [e for e in all_entries if e.get('type') == 'discussion']
    
    print(f"   Tool entries: {len(tool_entries)}")
    print(f"   Discussion entries: {len(discussion_entries)}")
    
    print("\n[2] Analyzing tool entries by round...")
    
    # Group by round
    by_round = defaultdict(list)
    by_agent = defaultdict(list)
    by_tool = defaultdict(list)
    
    for entry in tool_entries:
        round_val = entry.get('round', 'MISSING')
        agent = entry.get('agent', 'Unknown')
        tool_name = entry.get('tool_name', 'Unknown')
        
        by_round[round_val].append(entry)
        by_agent[agent].append(entry)
        by_tool[tool_name].append(entry)
    
    print(f"\n   Round distribution:")
    for round_val in sorted(by_round.keys(), key=lambda x: (x == 'MISSING', x if isinstance(x, int) else 999)):
        count = len(by_round[round_val])
        percentage = (count / len(tool_entries)) * 100 if tool_entries else 0
        status = "✅" if round_val in [1, 2, 3] else "❌" if round_val == 0 else "⚠️"
        print(f"      {status} Round {round_val}: {count} tools ({percentage:.1f}%)")
    
    print(f"\n   Agent distribution:")
    for agent in sorted(by_agent.keys()):
        entries = by_agent[agent]
        round_0_count = len([e for e in entries if e.get('round') == 0])
        round_1_3_count = len([e for e in entries if e.get('round') in [1, 2, 3]])
        total = len(entries)
        print(f"      {agent}:")
        print(f"         Total: {total}")
        print(f"         Round 0 (old): {round_0_count}")
        print(f"         Round 1-3 (new): {round_1_3_count}")
    
    print(f"\n   Tool distribution (top 10):")
    sorted_tools = sorted(by_tool.items(), key=lambda x: len(x[1]), reverse=True)
    for tool_name, entries in sorted_tools[:10]:
        round_0_count = len([e for e in entries if e.get('round') == 0])
        round_1_3_count = len([e for e in entries if e.get('round') in [1, 2, 3]])
        total = len(entries)
        print(f"      {tool_name}:")
        print(f"         Total: {total} (Round 0: {round_0_count}, Round 1-3: {round_1_3_count})")
    
    print("\n[3] Finding the transition point (where round changed from 0 to 1-3)...")
    
    # Find transition point
    transition_found = False
    for i, entry in enumerate(tool_entries):
        round_val = entry.get('round')
        if round_val == 0 and i < len(tool_entries) - 1:
            next_round = tool_entries[i + 1].get('round')
            if next_round in [1, 2, 3]:
                print(f"   Transition found:")
                print(f"      Line {entry['_line_num']}: {entry.get('agent')}:{entry.get('tool_name')}, round={round_val} (LAST round=0)")
                print(f"      Line {tool_entries[i + 1]['_line_num']}: {tool_entries[i + 1].get('agent')}:{tool_entries[i + 1].get('tool_name')}, round={next_round} (FIRST round=1-3)")
                transition_found = True
                break
    
    if not transition_found:
        print("   ⚠️  No clear transition point found")
    
    print("\n[4] Recent entries (last 20 tools)...")
    for entry in tool_entries[-20:]:
        round_val = entry.get('round', 'MISSING')
        agent = entry.get('agent', 'Unknown')
        tool_name = entry.get('tool_name', 'Unknown')
        timestamp = entry.get('timestamp', 'N/A')
        status = "✅" if round_val in [1, 2, 3] else "❌" if round_val == 0 else "⚠️"
        print(f"   {status} Line {entry['_line_num']}: {agent}:{tool_name}, round={round_val}, time={timestamp[:19] if len(timestamp) > 19 else timestamp}")
    
    print("\n[5] Old records (round=0) details...")
    old_records = [e for e in tool_entries if e.get('round') == 0]
    if old_records:
        print(f"   Found {len(old_records)} old records (round=0):")
        # Group by agent
        old_by_agent = defaultdict(list)
        for entry in old_records:
            old_by_agent[entry.get('agent', 'Unknown')].append(entry)
        
        for agent, entries in sorted(old_by_agent.items()):
            print(f"\n      {agent}: {len(entries)} tools")
            for entry in entries[:5]:  # Show first 5
                print(f"         Line {entry['_line_num']}: {entry.get('tool_name')}, time={entry.get('timestamp', 'N/A')[:19] if len(entry.get('timestamp', 'N/A')) > 19 else entry.get('timestamp', 'N/A')}")
            if len(entries) > 5:
                print(f"         ... and {len(entries) - 5} more")
    else:
        print("   ✅ No old records found (all have round 1-3)")
    
    print("\n[6] Summary...")
    total_tools = len(tool_entries)
    old_tools = len([e for e in tool_entries if e.get('round') == 0])
    new_tools = len([e for e in tool_entries if e.get('round') in [1, 2, 3]])
    missing_round = len([e for e in tool_entries if e.get('round') not in [0, 1, 2, 3]])
    
    print(f"   Total tool entries: {total_tools}")
    print(f"   Old records (round=0): {old_tools} ({(old_tools/total_tools*100) if total_tools else 0:.1f}%)")
    print(f"   New records (round=1-3): {new_tools} ({(new_tools/total_tools*100) if total_tools else 0:.1f}%)")
    print(f"   Missing/invalid round: {missing_round}")
    
    print("\n" + "=" * 80)
    if old_tools > 0:
        print(f"⚠️  Found {old_tools} old records (round=0) that won't be displayed in frontend")
        print(f"✅ Found {new_tools} new records (round=1-3) that should be displayed")
        print(f"\nRecommendation:")
        print(f"   - Old records are from before the fix and won't affect new tools")
        print(f"   - New records should be visible in frontend")
        print(f"   - If tools still don't show, check frontend console logs")
    else:
        print("✅ All records have valid round fields (1-3)")
    print("=" * 80)

if __name__ == "__main__":
    analyze_records()

