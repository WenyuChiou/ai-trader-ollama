"""
Test script to run a single agent discussion cycle
This script will:
1. Start the backend server (if not running)
2. Run a single agent discussion cycle
3. Display the results
"""
import sys
import os
import time
import requests
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

def check_backend_running(port=8000, timeout=5):
    """Check if backend is running"""
    try:
        response = requests.get(f"http://localhost:{port}/api/health", timeout=timeout)
        return response.status_code == 200
    except:
        return False

def wait_for_backend(port=8000, max_wait=30):
    """Wait for backend to be ready"""
    print(f"Waiting for backend on port {port}...")
    for i in range(max_wait):
        if check_backend_running(port):
            print(f"✅ Backend is running on port {port}")
            return True
        time.sleep(1)
        if i % 5 == 0:
            print(f"  Still waiting... ({i}/{max_wait}s)")
    return False

def run_agent_discussion_test():
    """Run a single agent discussion cycle"""
    print("=" * 60)
    print("Agent Discussion Test Run")
    print("=" * 60)
    print()
    
    # Check if backend is running (optional - not required for direct execution)
    print("[1/4] Checking backend status...")
    backend_running = check_backend_running()
    if backend_running:
        print("✅ Backend is running (API endpoints available)")
    else:
        print("⚠️  Backend API not running - running agent discussion directly")
        print("   (This is fine - agent discussion runs independently)")
    
    print()
    
    # Import trading cycle
    print("[2/4] Importing trading cycle module...")
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        print("✅ Trading cycle module imported")
    except Exception as e:
        print(f"❌ Failed to import trading cycle: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print()
    
    # Run discussion with minimal universe for quick test
    print("[3/4] Running agent discussion...")
    print("   Using minimal universe: NVDA, MSFT, AAPL (for quick test)")
    print("   This will run:")
    print("   - Market data fetching")
    print("   - 4 Analysts (Market, Technical, Fundamental, Sentiment)")
    print("   - Discussion Coordinator")
    print("   - Risk Analyst")
    print("   - Trader Agent")
    print()
    
    try:
        result = execute_daily_trade(
            universe=["NVDA", "MSFT", "AAPL"],  # Small universe for quick test
            rounds=2,  # Reduced rounds for faster test
            auto_tools=True,
            tool_budget=10,  # Reduced budget for faster test
            min_tools=2
        )
        
        print()
        print("=" * 60)
        print("Discussion Results")
        print("=" * 60)
        print()
        
        # Display key results
        if "conversations_count" in result:
            print(f"✅ Conversations: {result['conversations_count']}")
        
        if "final_stance" in result:
            print(f"✅ Final Stance: {result['final_stance']}")
        
        if "risk_report" in result:
            risk_report = result["risk_report"]
            print(f"\n📊 Risk Report:")
            if "risk_score" in risk_report:
                print(f"   Risk Score: {risk_report['risk_score']}")
            if "overall_risk_level" in risk_report:
                print(f"   Risk Level: {risk_report['overall_risk_level']}")
            if "vix_risk_score" in risk_report:
                print(f"   VIX Risk Score: {risk_report['vix_risk_score']}")
        
        if "trader_decision" in result:
            trader_decision = result["trader_decision"]
            print(f"\n💼 Trader Decision:")
            if isinstance(trader_decision, dict):
                if "action" in trader_decision:
                    print(f"   Action: {trader_decision['action']}")
                if "reasoning" in trader_decision:
                    reasoning = trader_decision["reasoning"]
                    if len(reasoning) > 200:
                        reasoning = reasoning[:200] + "..."
                    print(f"   Reasoning: {reasoning}")
        
        if "placed_orders" in result:
            orders = result["placed_orders"]
            print(f"\n📝 Orders Placed: {len(orders)}")
            if orders:
                for i, order in enumerate(orders[:3], 1):  # Show first 3 orders
                    symbol = order.get("symbol", "N/A")
                    action = order.get("action", "N/A")
                    quantity = order.get("quantity", "N/A")
                    print(f"   {i}. {symbol}: {action} {quantity} shares")
        
        print()
        print("=" * 60)
        print("✅ Agent Discussion Test Completed Successfully!")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Agent discussion failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_agent_discussion_test()
    exit(0 if success else 1)

