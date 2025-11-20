#!/usr/bin/env python3
"""Check tool calls in discussion_actions.jsonl for round field"""
import json
import sys
from pathlib import Path

# Fix encoding for Windows
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

log_file = Path("data/logs/discussion_actions.jsonl")
if not log_file.exists():
    print(f"File not found: {log_file}")
    sys.exit(1)

tool_entries = []
with open(log_file, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            entry = json.loads(line.strip())
            if entry.get('type') == 'tool' and entry.get('tool_name'):
                tool_entries.append(entry)
        except:
            continue

print(f"Found {len(tool_entries)} tool entries")
print("\nLast 10 tool entries:")
for entry in tool_entries[-10:]:
    print(f"  Agent: {entry.get('agent', 'N/A')}, Tool: {entry.get('tool_name', 'N/A')}, Round: {entry.get('round', 'MISSING')}")

# Check round distribution
rounds = {}
for entry in tool_entries:
    round_val = entry.get('round', 'MISSING')
    rounds[round_val] = rounds.get(round_val, 0) + 1

print(f"\nRound distribution:")
for round_val, count in sorted(rounds.items()):
    print(f"  Round {round_val}: {count} tools")

