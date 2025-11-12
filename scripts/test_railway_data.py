#!/usr/bin/env python3
"""Quick test to verify Railway data"""
import requests
import json
import sys
import os

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

RAILWAY_URL = "https://web-production-b42d6.up.railway.app"

print("Testing Railway data...")
print("=" * 60)

# Test conversations
try:
    r = requests.get(f"{RAILWAY_URL}/api/agents/conversations?limit=5", timeout=10)
    if r.status_code == 200:
        data = r.json()
        convos = data.get("conversations", [])
        print(f"[SUCCESS] Conversations: {len(convos)} found")
        if convos:
            print(f"   Latest: {convos[0].get('agent', 'Unknown')} - {convos[0].get('content', '')[:50]}...")
    else:
        print(f"[ERROR] Conversations API returned: {r.status_code}")
except Exception as e:
    print(f"[ERROR] Conversations API error: {e}")

# Test trades
try:
    r = requests.get(f"{RAILWAY_URL}/api/trades/recent?limit=5", timeout=10)
    if r.status_code == 200:
        data = r.json()
        trades = data.get("trades", [])
        print(f"[SUCCESS] Trades: {len(trades)} found")
        if trades:
            print(f"   Latest: {trades[0].get('symbol', 'Unknown')} - {trades[0].get('status', 'Unknown')}")
    else:
        print(f"[ERROR] Trades API returned: {r.status_code}")
except Exception as e:
    print(f"[ERROR] Trades API error: {e}")

print("=" * 60)
print("[INFO] Test complete! Check GitHub Pages in 1-2 minutes.")
print(f"[INFO] GitHub Pages: https://wenyuchiou.github.io/ai-trader-ollama/monitor.html")

