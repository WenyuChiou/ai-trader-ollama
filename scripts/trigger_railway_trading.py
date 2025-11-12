#!/usr/bin/env python3
"""
Trigger trading cycle on Railway backend
Usage: python scripts/trigger_railway_trading.py
"""
import requests
import json
import sys

# Railway backend URL
RAILWAY_URL = "https://web-production-b42d6.up.railway.app"

def trigger_trading_cycle():
    """Trigger trading cycle on Railway"""
    print("=" * 60)
    print("Triggering Trading Cycle on Railway")
    print("=" * 60)
    print(f"\n📡 Railway URL: {RAILWAY_URL}")
    print(f"📡 Endpoint: /api/trading/execute-trade")
    print(f"\n⏳ Sending request...")
    print(f"   This may take 2-5 minutes...\n")
    
    try:
        response = requests.post(
            f"{RAILWAY_URL}/api/trading/execute-trade",
            json={},
            timeout=600,  # 10 minutes timeout
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                print("\n✅ Trading cycle completed successfully!")
                print(f"\n📊 Result:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return True
            else:
                print(f"\n❌ Trading cycle failed: {data.get('error', 'Unknown error')}")
                print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
                return False
        elif response.status_code == 429:
            print("\n⚠️  Trading cycle is already running. Please wait...")
            print(f"Response: {response.text}")
            return False
        else:
            print(f"\n❌ API returned status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("\n❌ Request timeout (trading cycle took too long)")
        print("   The cycle may still be running on Railway.")
        print("   Check Railway logs or wait a few minutes and check the dashboard.")
        return False
    except requests.exceptions.ConnectionError:
        print("\n❌ Cannot connect to Railway backend.")
        print(f"   URL: {RAILWAY_URL}")
        print("   Please check:")
        print("   1. Railway service is running")
        print("   2. URL is correct")
        print("   3. Network connection is working")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = trigger_trading_cycle()
    sys.exit(0 if success else 1)

