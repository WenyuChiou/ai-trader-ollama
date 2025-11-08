#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Integration Testing
Tests backend scenarios and evaluates what frontend should display
"""
import subprocess
import json
import time
import sys
import io
from pathlib import Path
from datetime import date

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

class FrontendIntegrationTester:
    def __init__(self):
        self.results = {}
        self.backend_dir = Path(__file__).parent
        
    def run_backend_scenario(self, scenario_num, auto=True):
        """Run backend scenario test"""
        cmd = [sys.executable, "test_scenarios.py", "--scenario", str(scenario_num)]
        if auto:
            cmd.append("--auto")
        cmd.append("--no-restore")  # Don't restore to keep state for frontend testing
        
        try:
            result = subprocess.run(
                cmd,
                cwd=self.backend_dir,
                capture_output=True,
                text=True,
                timeout=600,  # 10 minutes
                encoding='utf-8',
                errors='replace'
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Timeout after 10 minutes",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
    
    def evaluate_frontend_state(self, scenario_num, backend_result):
        """Evaluate what frontend should display"""
        evaluation = {
            "scenario": scenario_num,
            "backend_status": "pass" if backend_result["success"] else "fail",
            "frontend_checks": {},
            "issues": [],
            "recommendations": []
        }
        
        stdout = backend_result.get("stdout", "")
        stderr = backend_result.get("stderr", "")
        combined = stdout + "\n" + stderr
        
        # Check 1: Portfolio state
        if "Portfolio state saved" in combined or "Portfolio updated" in combined:
            evaluation["frontend_checks"]["portfolio_updated"] = True
        else:
            evaluation["frontend_checks"]["portfolio_updated"] = False
            evaluation["issues"].append("Portfolio may not be updated")
        
        # Check 2: Orders generated
        if "buy orders" in combined.lower() or "sell orders" in combined.lower():
            # Extract order counts
            import re
            buy_match = re.search(r'(\d+)\s+buy\s+orders?', combined, re.IGNORECASE)
            sell_match = re.search(r'(\d+)\s+sell\s+orders?', combined, re.IGNORECASE)
            if buy_match:
                evaluation["frontend_checks"]["buy_orders"] = int(buy_match.group(1))
            if sell_match:
                evaluation["frontend_checks"]["sell_orders"] = int(sell_match.group(1))
            
            if buy_match or sell_match:
                evaluation["frontend_checks"]["orders_generated"] = True
            else:
                evaluation["frontend_checks"]["orders_generated"] = False
                evaluation["issues"].append("No orders generated")
        else:
            evaluation["frontend_checks"]["orders_generated"] = False
            evaluation["issues"].append("No order information found")
        
        # Check 3: Conversations generated
        if "conversations" in combined.lower() and ("entries" in combined.lower() or "conversations_count" in combined.lower()):
            evaluation["frontend_checks"]["conversations_generated"] = True
        else:
            evaluation["frontend_checks"]["conversations_generated"] = False
            evaluation["issues"].append("Conversations may not be generated")
        
        # Check 4: Market status
        if "Market is open" in combined or "Market is closed" in combined:
            evaluation["frontend_checks"]["market_status_determined"] = True
        else:
            evaluation["frontend_checks"]["market_status_determined"] = False
        
        # Check 5: Errors
        if "Error" in combined or "error" in stderr.lower():
            evaluation["frontend_checks"]["has_errors"] = True
            # Extract error messages
            import re
            errors = re.findall(r'Error[:\s]+([^\n]+)', combined, re.IGNORECASE)
            if errors:
                evaluation["issues"].extend([f"Error: {e[:100]}" for e in errors[:3]])
        else:
            evaluation["frontend_checks"]["has_errors"] = False
        
        # Check 6: Warnings
        if "Warning" in combined or "⚠️" in combined:
            evaluation["frontend_checks"]["has_warnings"] = True
            warnings = []
            if "No trading decisions generated" in combined:
                warnings.append("No trading decisions - frontend should show appropriate message")
            if "pending orders" in combined.lower():
                warnings.append("Pending orders exist - frontend should display them")
            evaluation["recommendations"].extend(warnings)
        else:
            evaluation["frontend_checks"]["has_warnings"] = False
        
        # Frontend display recommendations
        if evaluation["frontend_checks"].get("orders_generated"):
            evaluation["recommendations"].append("Frontend should display orders in Execution Details")
        if evaluation["frontend_checks"].get("conversations_generated"):
            evaluation["recommendations"].append("Frontend should display conversations in Conversations section")
        if evaluation["frontend_checks"].get("portfolio_updated"):
            evaluation["recommendations"].append("Frontend should refresh portfolio data after trading cycle")
        
        return evaluation
    
    def test_scenario(self, scenario_num, description):
        """Test a single scenario"""
        print(f"\n{'='*80}")
        print(f"[TEST] Testing Scenario {scenario_num}: {description}")
        print(f"{'='*80}")
        
        # Run backend test
        print(f"\n[1/2] Running backend scenario test...")
        backend_result = self.run_backend_scenario(scenario_num, auto=True)
        
        if backend_result["success"]:
            print("   ✅ Backend test completed")
        else:
            print(f"   ⚠️  Backend test had issues (returncode: {backend_result['returncode']})")
            if backend_result["stderr"]:
                print(f"   Error: {backend_result['stderr'][:200]}")
        
        # Evaluate frontend state
        print(f"\n[2/2] Evaluating frontend state...")
        evaluation = self.evaluate_frontend_state(scenario_num, backend_result)
        
        # Print evaluation
        print(f"\n   [CHECK] Frontend Checks:")
        for check, value in evaluation["frontend_checks"].items():
            icon = "[OK]" if value else "[FAIL]" if isinstance(value, bool) else "[INFO]"
            print(f"      {icon} {check}: {value}")
        
        if evaluation["issues"]:
            print(f"\n   [WARN] Issues ({len(evaluation['issues'])}):")
            for issue in evaluation["issues"][:5]:  # Show first 5
                print(f"      - {issue}")
        
        if evaluation["recommendations"]:
            print(f"\n   [REC] Recommendations ({len(evaluation['recommendations'])}):")
            for rec in evaluation["recommendations"][:5]:  # Show first 5
                print(f"      - {rec}")
        
        evaluation["backend_output"] = backend_result.get("stdout", "")[:1000]  # Store first 1000 chars
        return evaluation
    
    def run_all_tests(self):
        """Run all scenario tests"""
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
            evaluation = self.test_scenario(scenario_num, description)
            self.results[scenario_num] = evaluation
            time.sleep(2)  # Brief pause between scenarios
        
        return True
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("[REPORT] FRONTEND INTEGRATION TEST REPORT")
        print("="*80)
        
        total = len(self.results)
        backend_passed = sum(1 for r in self.results.values() if r["backend_status"] == "pass")
        
        # Count frontend readiness
        frontend_ready = 0
        for result in self.results.values():
            checks = result.get("frontend_checks", {})
            critical_checks = [
                checks.get("portfolio_updated", False),
                checks.get("orders_generated", False) or checks.get("conversations_generated", False),
                not checks.get("has_errors", False),
            ]
            if all(critical_checks):
                frontend_ready += 1
        
        print(f"\n[SUMMARY]")
        print(f"   Total Scenarios: {total}")
        print(f"   Backend Passed: {backend_passed}/{total}")
        print(f"   Frontend Ready: {frontend_ready}/{total}")
        
        print(f"\n[DETAILS] Detailed Results:")
        for scenario_num in sorted(self.results.keys()):
            result = self.results[scenario_num]
            status_icon = "[PASS]" if result["backend_status"] == "pass" else "[FAIL]"
            print(f"\n{status_icon} Scenario {scenario_num}: {result.get('scenario', 'N/A')}")
            print(f"   Backend: {result['backend_status'].upper()}")
            print(f"   Frontend Checks: {len([k for k, v in result.get('frontend_checks', {}).items() if v])}/{len(result.get('frontend_checks', {}))}")
            if result.get("issues"):
                print(f"   Issues: {len(result['issues'])}")
            if result.get("recommendations"):
                print(f"   Recommendations: {len(result['recommendations'])}")
        
        # Generate recommendations
        print(f"\n[RECOMMENDATIONS] Overall Recommendations:")
        all_issues = []
        all_recommendations = []
        for result in self.results.values():
            all_issues.extend(result.get("issues", []))
            all_recommendations.extend(result.get("recommendations", []))
        
        # Count unique issues
        from collections import Counter
        issue_counts = Counter(all_issues)
        if issue_counts:
            print(f"\n   Common Issues:")
            for issue, count in issue_counts.most_common(5):
                print(f"      - {issue} ({count} scenarios)")
        
        # Count unique recommendations
        rec_counts = Counter(all_recommendations)
        if rec_counts:
            print(f"\n   Common Recommendations:")
            for rec, count in rec_counts.most_common(5):
                print(f"      - {rec} ({count} scenarios)")
        
        return {
            "total": total,
            "backend_passed": backend_passed,
            "frontend_ready": frontend_ready,
            "results": self.results
        }

if __name__ == "__main__":
    tester = FrontendIntegrationTester()
    
    print("\n" + "="*80)
    print("[TEST] FRONTEND INTEGRATION TESTING")
    print("="*80)
    print("\nThis will test all backend scenarios and evaluate frontend readiness.")
    print("Each scenario will be run with --auto flag.")
    print("\nStarting tests...")
    
    tester.run_all_tests()
    report = tester.generate_report()
    
    # Save report
    report_file = Path("backend/frontend_integration_report.json")
    with report_file.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[SAVE] Report saved to: {report_file}")
    
    # Exit code
    if report["frontend_ready"] == report["total"]:
        sys.exit(0)
    else:
        sys.exit(1)

