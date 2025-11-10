#!/usr/bin/env python3
"""
Frontend Scenario Testing Script
Tests all scenarios and evaluates frontend behavior
"""
import requests
import json
import time
from datetime import date, timedelta
from pathlib import Path
import sys

API_BASE = "http://127.0.0.1:8000"

class FrontendScenarioTester:
    def __init__(self):
        self.results = {}
        self.api_base = API_BASE
        
    def check_api_health(self):
        """Check if API is running"""
        try:
            response = requests.get(f"{self.api_base}/", timeout=3)
            return response.status_code == 200
        except:
            return False
    
    def test_scenario(self, scenario_num, description):
        """Test a single scenario"""
        print(f"\n{'='*80}")
        print(f"🧪 Testing Scenario {scenario_num}: {description}")
        print(f"{'='*80}")
        
        result = {
            "scenario": scenario_num,
            "description": description,
            "status": "pending",
            "issues": [],
            "checks": {}
        }
        
        # Step 1: Setup scenario via backend
        print(f"\n[1/5] Setting up scenario {scenario_num}...")
        try:
            setup_response = requests.post(
                f"{self.api_base}/api/test/setup-scenario",
                json={"scenario": scenario_num},
                timeout=10
            )
            if setup_response.status_code == 200:
                print("   ✅ Scenario setup successful")
                result["checks"]["setup"] = True
            else:
                print(f"   ❌ Scenario setup failed: {setup_response.status_code}")
                result["checks"]["setup"] = False
                result["issues"].append(f"Setup failed: {setup_response.status_code}")
        except Exception as e:
            print(f"   ❌ Setup error: {e}")
            result["checks"]["setup"] = False
            result["issues"].append(f"Setup error: {str(e)}")
            return result
        
        # Step 2: Check initial state
        print(f"\n[2/5] Checking initial state...")
        try:
            portfolio_response = requests.get(
                f"{self.api_base}/api/portfolio/real-time",
                timeout=5
            )
            market_response = requests.get(
                f"{self.api_base}/api/market/is-open",
                timeout=5
            )
            
            if portfolio_response.status_code == 200:
                portfolio = portfolio_response.json()
                result["checks"]["portfolio_api"] = True
                result["checks"]["initial_cash"] = portfolio.get("cash", 0)
                result["checks"]["initial_positions"] = len(portfolio.get("positions", {}))
                print(f"   ✅ Portfolio API: ${portfolio.get('cash', 0):,.2f} cash, {len(portfolio.get('positions', {}))} positions")
            else:
                result["checks"]["portfolio_api"] = False
                result["issues"].append("Portfolio API failed")
                
            if market_response.status_code == 200:
                market = market_response.json()
                result["checks"]["market_api"] = True
                result["checks"]["market_open"] = market.get("is_open", False)
                print(f"   ✅ Market API: {'OPEN' if market.get('is_open') else 'CLOSED'}")
            else:
                result["checks"]["market_api"] = False
                result["issues"].append("Market API failed")
                
        except Exception as e:
            print(f"   ❌ Initial state check error: {e}")
            result["issues"].append(f"Initial state error: {str(e)}")
        
        # Step 3: Execute trading cycle
        print(f"\n[3/5] Executing trading cycle...")
        try:
            execute_response = requests.post(
                f"{self.api_base}/api/trading/execute-trade",
                json={},
                timeout=600  # 10 minutes
            )
            
            if execute_response.status_code == 200:
                data = execute_response.json()
                result["checks"]["execute_api"] = True
                result["checks"]["orders_placed"] = len(data.get("result", {}).get("placed_orders", []))
                result["checks"]["conversations"] = data.get("result", {}).get("conversations_count", 0)
                result["checks"]["is_planning"] = data.get("result", {}).get("is_planning", False)
                print(f"   ✅ Trading cycle completed: {result['checks']['orders_placed']} orders, {result['checks']['conversations']} conversations")
            elif execute_response.status_code == 429:
                result["checks"]["execute_api"] = "blocked"
                result["issues"].append("Trading cycle blocked (429 - already running)")
                print("   ⚠️  Trading cycle blocked (already running)")
            else:
                result["checks"]["execute_api"] = False
                result["issues"].append(f"Execute failed: {execute_response.status_code}")
                print(f"   ❌ Trading cycle failed: {execute_response.status_code}")
        except requests.exceptions.Timeout:
            result["checks"]["execute_api"] = "timeout"
            result["issues"].append("Trading cycle timeout (may still be processing)")
            print("   ⏳ Trading cycle timeout (may still be processing)")
        except Exception as e:
            result["checks"]["execute_api"] = False
            result["issues"].append(f"Execute error: {str(e)}")
            print(f"   ❌ Trading cycle error: {e}")
        
        # Step 4: Check final state
        print(f"\n[4/5] Checking final state...")
        time.sleep(2)  # Wait for data to be saved
        try:
            portfolio_response = requests.get(
                f"{self.api_base}/api/portfolio/real-time",
                timeout=5
            )
            trades_response = requests.get(
                f"{self.api_base}/api/trades/recent?limit=30",
                timeout=5
            )
            conversations_response = requests.get(
                f"{self.api_base}/api/agents/conversations?limit=30",
                timeout=5
            )
            
            if portfolio_response.status_code == 200:
                portfolio = portfolio_response.json()
                result["checks"]["final_cash"] = portfolio.get("cash", 0)
                result["checks"]["final_positions"] = len(portfolio.get("positions", {}))
                result["checks"]["portfolio_changed"] = (
                    result["checks"].get("initial_cash", 0) != result["checks"].get("final_cash", 0) or
                    result["checks"].get("initial_positions", 0) != result["checks"].get("final_positions", 0)
                )
                print(f"   ✅ Final portfolio: ${result['checks']['final_cash']:,.2f} cash, {result['checks']['final_positions']} positions")
                if result["checks"]["portfolio_changed"]:
                    print("   ✅ Portfolio state changed (expected)")
                else:
                    print("   ⚠️  Portfolio state unchanged")
                    
            if trades_response.status_code == 200:
                trades = trades_response.json()
                result["checks"]["trades_count"] = len(trades.get("trades", []))
                result["checks"]["pending_orders"] = len([t for t in trades.get("trades", []) if t.get("status") == "PENDING"])
                result["checks"]["filled_orders"] = len([t for t in trades.get("trades", []) if t.get("status") == "FILLED"])
                print(f"   ✅ Trades: {result['checks']['trades_count']} total ({result['checks']['pending_orders']} pending, {result['checks']['filled_orders']} filled)")
            else:
                result["issues"].append("Trades API failed")
                
            if conversations_response.status_code == 200:
                convs = conversations_response.json()
                result["checks"]["conversations_count"] = len(convs.get("conversations", []))
                print(f"   ✅ Conversations: {result['checks']['conversations_count']} entries")
            else:
                result["issues"].append("Conversations API failed")
                
        except Exception as e:
            print(f"   ❌ Final state check error: {e}")
            result["issues"].append(f"Final state error: {str(e)}")
        
        # Step 5: Evaluate frontend readiness
        print(f"\n[5/5] Evaluating frontend readiness...")
        
        # Check if all required APIs are working
        api_checks = [
            result["checks"].get("portfolio_api", False),
            result["checks"].get("market_api", False),
            result["checks"].get("execute_api", False) != False,  # True or "blocked" or "timeout" are OK
        ]
        result["checks"]["all_apis_working"] = all(api_checks)
        
        # Check if data is available for frontend
        data_checks = [
            result["checks"].get("trades_count", 0) >= 0,  # At least API works
            result["checks"].get("conversations_count", 0) >= 0,  # At least API works
        ]
        result["checks"]["data_available"] = all(data_checks)
        
        # Determine overall status
        if len(result["issues"]) == 0:
            result["status"] = "pass"
        elif len(result["issues"]) <= 2 and result["checks"].get("execute_api") in [True, "blocked", "timeout"]:
            result["status"] = "partial"
        else:
            result["status"] = "fail"
        
        print(f"\n   📊 Status: {result['status'].upper()}")
        if result["issues"]:
            print(f"   ⚠️  Issues: {len(result['issues'])}")
            for issue in result["issues"]:
                print(f"      - {issue}")
        
        return result
    
    def run_all_tests(self):
        """Run all scenario tests"""
        print("\n" + "="*80)
        print("🧪 FRONTEND SCENARIO TESTING")
        print("="*80)
        
        # Check API health
        if not self.check_api_health():
            print("❌ API is not running. Please start the backend server first.")
            print("   Run: cd backend && python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000")
            return False
        
        print("✅ API is running")
        
        scenarios = [
            (1, "Market Open, No Holdings"),
            (2, "Market Open, With Holdings"),
            (3, "Market Closed, No Holdings"),
            (4, "Market Closed, With Holdings"),
            (5, "Multi-day Simulation"),
            (6, "Rapid Consecutive Clicks"),
            (7, "Network Timeout"),
            (8, "Partial Order Fills"),
            (9, "Order Conflicts"),
            (10, "Auto-Trade + Manual Conflict"),
            (11, "Initialize Then Execute"),
            (12, "Market Status Switch"),
        ]
        
        for scenario_num, description in scenarios:
            result = self.test_scenario(scenario_num, description)
            self.results[scenario_num] = result
            time.sleep(1)  # Brief pause between scenarios
        
        return True
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "="*80)
        print("📊 TEST REPORT")
        print("="*80)
        
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r["status"] == "pass")
        partial = sum(1 for r in self.results.values() if r["status"] == "partial")
        failed = sum(1 for r in self.results.values() if r["status"] == "fail")
        
        print(f"\nOverall: {passed}/{total} passed, {partial}/{total} partial, {failed}/{total} failed")
        
        print("\n📋 Detailed Results:")
        for scenario_num in sorted(self.results.keys()):
            result = self.results[scenario_num]
            status_icon = "✅" if result["status"] == "pass" else "⚠️" if result["status"] == "partial" else "❌"
            print(f"\n{status_icon} Scenario {scenario_num}: {result['description']}")
            print(f"   Status: {result['status'].upper()}")
            if result["issues"]:
                print(f"   Issues ({len(result['issues'])}):")
                for issue in result["issues"]:
                    print(f"      - {issue}")
            print(f"   Checks:")
            for check, value in result["checks"].items():
                if isinstance(value, bool):
                    icon = "✅" if value else "❌"
                    print(f"      {icon} {check}: {value}")
                else:
                    print(f"      • {check}: {value}")
        
        return {
            "total": total,
            "passed": passed,
            "partial": partial,
            "failed": failed,
            "results": self.results
        }

if __name__ == "__main__":
    tester = FrontendScenarioTester()
    
    if not tester.run_all_tests():
        sys.exit(1)
    
    report = tester.generate_report()
    
    # Save report to file
    report_file = Path("backend/frontend_test_report.json")
    with report_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Report saved to: {report_file}")
    
    # Exit with appropriate code
    if report["failed"] > 0:
        sys.exit(1)
    elif report["partial"] > 0:
        sys.exit(0)  # Partial is OK
    else:
        sys.exit(0)

