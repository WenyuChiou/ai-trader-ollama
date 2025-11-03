#!/usr/bin/env python3
"""
Demo test script to generate realistic trading data for frontend display.

This script:
1. Creates a demo portfolio with positions
2. Generates agent conversations
3. Records equity history
4. Updates portfolio state

Run this once to populate data, then frontend can display it.
"""
import sys
from pathlib import Path
import json
from datetime import datetime, date, timedelta

# Add backend to path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

def init_demo_portfolio():
    """Initialize a demo portfolio state"""
    logs_dir = ROOT / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    state_file = logs_dir / "portfolio_state.json"
    
    # Create demo portfolio with 3 positions
    state = {
        "cash": 2500.0,
        "initial_value": 10000.0,
        "positions": {
            "NVDA": {
                "quantity": 5,
                "avg_cost": 900.0,
                "total_cost": 4500.0
            },
            "MSFT": {
                "quantity": 7,
                "avg_cost": 420.0,
                "total_cost": 2940.0
            },
            "AAPL": {
                "quantity": 10,
                "avg_cost": 190.0,
                "total_cost": 1900.0
            }
        }
    }
    
    with state_file.open("w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
    
    print(f"[OK] Portfolio state initialized: {len(state['positions'])} positions")
    return state

def generate_demo_conversations():
    """Generate demo agent conversations"""
    logs_dir = ROOT / "data" / "logs"
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    conversations = [
        {
            "timestamp": (datetime.now() - timedelta(minutes=5)).isoformat() + "Z",
            "agent": "MarketAgent",
            "round": 1,
            "content": "Market scan complete. VIX at 18.5 (moderate risk). Tech sector showing strong momentum. NVDA, MSFT, AAPL leading.",
            "type": "demo"
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=4)).isoformat() + "Z",
            "agent": "MarketAnalyst",
            "round": 1,
            "content": "Recommended stocks: NVDA (signal_score: 0.85), MSFT (0.72), AAPL (0.68). All above threshold.",
            "type": "demo"
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=3)).isoformat() + "Z",
            "agent": "DiscussionAgent",
            "round": 2,
            "content": "Consensus reached: Mild bullish stance. Focus on tech leaders with strong fundamentals. Risk levels acceptable.",
            "type": "demo"
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=2)).isoformat() + "Z",
            "agent": "RiskAnalyst",
            "round": 2,
            "content": "Portfolio risk check: Position sizes within limits. Max single position: 45% (NVDA). Total exposure: 75%. Hedging not required.",
            "type": "demo"
        },
        {
            "timestamp": (datetime.now() - timedelta(minutes=1)).isoformat() + "Z",
            "agent": "TraderAgent",
            "round": 3,
            "content": "Trade decision: HOLD current positions. All positions performing well. Monitoring for entry/exit signals.",
            "type": "demo"
        }
    ]
    
    # Append to file
    with convo_file.open("a", encoding="utf-8") as f:
        for conv in conversations:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")
    
    print(f"[OK] Generated {len(conversations)} demo conversations")
    return conversations

def generate_equity_history():
    """Generate equity history for chart"""
    logs_dir = ROOT / "data" / "logs"
    equity_file = logs_dir / "equity_history.jsonl"
    
    # Generate last 30 days of data
    today = date.today()
    records = []
    
    base_value = 10000.0
    for i in range(30):
        d = today - timedelta(days=30-i)
        # Simulate gradual growth with some volatility
        value = base_value * (1.0 + (30-i) * 0.001 + (i % 5) * 0.002 - (i % 7) * 0.001)
        pnl = value - base_value
        pnl_pct = (pnl / base_value) * 100.0
        
        record = {
            "date": d.isoformat(),
            "timestamp": datetime.combine(d, datetime.min.time()).isoformat() + "Z",
            "total_value": round(value, 2),
            "total_pnl": round(pnl, 2),
            "total_pnl_pct": round(pnl_pct, 3),
            "cash": 2500.0,
            "equity_value": round(value - 2500.0, 2)
        }
        records.append(record)
    
    # Append to file
    with equity_file.open("a", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    
    print(f"[OK] Generated {len(records)} equity history records")
    return records

def generate_real_time_snapshot():
    """Generate a current real-time snapshot"""
    logs_dir = ROOT / "data" / "logs"
    snapshot_file = logs_dir / "real_time_snapshots.jsonl"
    
    # Load portfolio state
    state_file = logs_dir / "portfolio_state.json"
    if not state_file.exists():
        init_demo_portfolio()
    
    with state_file.open("r", encoding="utf-8") as f:
        state = json.load(f)
    
    # Simulate current prices (slightly above avg_cost for profit)
    positions_detail = {}
    positions_pnl = {}
    equity_value = 0.0
    total_unrealized = 0.0
    
    for sym, info in state["positions"].items():
        qty = info["quantity"]
        avg_cost = info["avg_cost"]
        # Price 2-5% above cost
        current_price = avg_cost * (1.0 + 0.02 + hash(sym) % 3 * 0.01)
        market_value = qty * current_price
        equity_value += market_value
        unrealized_pnl = (current_price - avg_cost) * qty
        total_unrealized += unrealized_pnl
        pnl_pct = ((current_price - avg_cost) / avg_cost * 100.0) if avg_cost > 0 else 0.0
        
        positions_detail[sym] = {
            "quantity": qty,
            "avg_cost": round(avg_cost, 4),
            "current_price": round(current_price, 4),
            "market_value": round(market_value, 2)
        }
        positions_pnl[sym] = {
            "unrealized_pnl": round(unrealized_pnl, 2),
            "unrealized_pnl_pct": round(pnl_pct, 3)
        }
    
    total_value = state["cash"] + equity_value
    total_pnl = total_value - state["initial_value"]
    total_pnl_pct = (total_pnl / state["initial_value"] * 100.0) if state["initial_value"] > 0 else 0.0
    
    snapshot = {
        "ok": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "initial_value": round(state["initial_value"], 2),
        "total_value": round(total_value, 2),
        "total_pnl": round(total_pnl, 2),
        "total_pnl_pct": round(total_pnl_pct, 3),
        "cash": round(state["cash"], 2),
        "equity_value": round(equity_value, 2),
        "positions": positions_detail,
        "positions_pnl": positions_pnl,
        "source": "demo_test"
    }
    
    # Append snapshot
    with snapshot_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    
    print(f"[OK] Generated real-time snapshot: Total Value=${total_value:.2f}, P&L=${total_pnl:.2f} ({total_pnl_pct:.2f}%)")
    return snapshot

def main():
    """Run the demo test"""
    print("=" * 60)
    print("Running Demo Test - Generating Trading Data")
    print("=" * 60)
    
    try:
        # 1. Initialize portfolio
        init_demo_portfolio()
        
        # 2. Generate conversations
        generate_demo_conversations()
        
        # 3. Generate equity history
        generate_equity_history()
        
        # 4. Generate current snapshot
        generate_real_time_snapshot()
        
        print("=" * 60)
        print("[SUCCESS] Demo test completed!")
        print("=" * 60)
        print("\nFrontend should now display:")
        print("  - Portfolio with 3 positions (NVDA, MSFT, AAPL)")
        print("  - Agent conversations (5 messages)")
        print("  - Equity history chart (30 days)")
        print("  - Current P&L and NAV")
        print("\nOpen frontend/monitor.html to view!")
        
    except Exception as e:
        print(f"\n[ERROR] Demo test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

