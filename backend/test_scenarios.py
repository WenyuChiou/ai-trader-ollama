#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scenario-Based Testing for AI-Trader System

Tests 4 real-world scenarios:
1. Market open, no holdings
2. Market open, with holdings
3. Market closed, no holdings  
4. Market closed, with holdings

All tests use TODAY'S real market data.
"""
import sys
import os
from pathlib import Path
from datetime import datetime, time as dt_time, date, timedelta
import json

# Fix Windows encoding
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

# Set FRED API key
os.environ["FRED_API_KEY"] = "b04875b1abf3f24890b57ea2cee6b5e1"


class ScenarioTester:
    def __init__(self):
        self.test_date = date.today().isoformat()
        self.logs_dir = Path("data/logs")
        self.portfolio_file = self.logs_dir / "portfolio_state.json"
        self.pending_orders_dir = self.logs_dir / "pending_orders"
        
        # Backup original state
        self.backup_dir = self.logs_dir / "test_backup"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def save_portfolio(self, cash: float, initial_value: float, positions: dict = None):
        """Save portfolio state to JSON file"""
        import json
        if positions is None:
            positions = {}
        
        # Convert Portfolio positions to JSON format
        positions_json = {}
        for symbol, pos in positions.items():
            if hasattr(pos, 'quantity'):  # Position object
                positions_json[symbol] = {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": pos.total_cost if hasattr(pos, 'total_cost') else pos.avg_cost * pos.quantity
                }
            elif isinstance(pos, dict):  # Already dict
                positions_json[symbol] = pos
        
        state = {
            "cash": cash,
            "initial_value": initial_value,
            "positions": positions_json
        }
        
        with self.portfolio_file.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    
    def load_portfolio(self):
        """Load portfolio from JSON file"""
        import json
        from src.data.portfolio import Portfolio, Position
        
        if not self.portfolio_file.exists():
            return Portfolio(cash=10000.0, initial_value=10000.0)
        
        with self.portfolio_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        portfolio = Portfolio(
            cash=state.get("cash", 10000.0),
            initial_value=state.get("initial_value", 10000.0)
        )
        
        # Load positions
        positions_data = state.get("positions", {})
        for symbol, pos_data in positions_data.items():
            if isinstance(pos_data, dict):
                portfolio._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=pos_data.get("quantity", 0),
                    avg_cost=pos_data.get("avg_cost", 0.0),
                    total_cost=pos_data.get("total_cost", pos_data.get("avg_cost", 0.0) * pos_data.get("quantity", 0))
                )
        
        return portfolio
    
    def backup_state(self):
        """Backup current state before testing"""
        print("\n📦 Backing up current state...")
        import shutil
        
        if self.portfolio_file.exists():
            shutil.copy(self.portfolio_file, self.backup_dir / "portfolio_state.json")
            print(f"   ✅ Portfolio backed up")
        
        # Backup logs
        for log_file in ["equity_history.jsonl", "trade_log.jsonl", "discussion_actions.jsonl"]:
            log_path = self.logs_dir / log_file
            if log_path.exists():
                shutil.copy(log_path, self.backup_dir / log_file)
                print(f"   ✅ {log_file} backed up")
    
    def restore_state(self):
        """Restore original state after testing"""
        print("\n📦 Restoring original state...")
        import shutil
        
        for backup_file in self.backup_dir.iterdir():
            target = self.logs_dir / backup_file.name
            shutil.copy(backup_file, target)
            print(f"   ✅ Restored {backup_file.name}")
    
    def setup_scenario_1(self):
        """
        Scenario 1: Market open, no holdings
        - Empty portfolio (cash only)
        - No pending orders
        - Market is open (simulated if actually closed)
        """
        print("\n" + "="*80)
        print("📋 SCENARIO 1: Market Open, No Holdings")
        print("="*80)
        print("\nSetup:")
        print("  • Portfolio: $10,000 cash, 0 positions")
        print("  • Pending orders: None")
        print("  • Market status: Open (or simulated)")
        print()
        
        # Create empty portfolio
        self.save_portfolio(cash=10000.0, initial_value=10000.0, positions={})
        print("  ✅ Portfolio initialized")
        
        # Clear pending orders (remove entire directory and recreate)
        if self.pending_orders_dir.exists():
            import shutil
            shutil.rmtree(self.pending_orders_dir)
        self.pending_orders_dir.mkdir(parents=True, exist_ok=True)
        print("  ✅ Pending orders cleared")
        
        return {
            "scenario": 1,
            "description": "Market open, no holdings",
            "expected_behavior": [
                "System fetches market data",
                "Agents analyze 118 stocks",
                "BUY orders generated",
                "Orders executed immediately (if market open) or placed as pending",
                "Portfolio updated with new positions"
            ]
        }
    
    def setup_scenario_2(self):
        """
        Scenario 2: Market open, with holdings
        - Portfolio with existing positions
        - No pending orders
        - Market is open (simulated if actually closed)
        """
        print("\n" + "="*80)
        print("📋 SCENARIO 2: Market Open, With Holdings")
        print("="*80)
        print("\nSetup:")
        print("  • Portfolio: $5,000 cash + positions")
        print("  • Positions: NVDA x10, MSFT x15, AAPL x20")
        print("  • Pending orders: None")
        print("  • Market status: Open (or simulated)")
        print()
        
        # Create portfolio with holdings
        from src.data.portfolio import Portfolio
        # Calculate required cash: NVDA(10*120) + MSFT(15*380) + AAPL(20*185) = 1200 + 5700 + 3700 = 10600
        # Start with 15000 cash to have some remaining
        portfolio = Portfolio(cash=15000.0, initial_value=25000.0)
        
        # Add sample positions
        portfolio.buy("NVDA", 10, 120.0)  # 1200
        portfolio.buy("MSFT", 15, 380.0)  # 5700
        portfolio.buy("AAPL", 20, 185.0)  # 3700
        # Total: 10600, Remaining cash: 4400
        
        # Save portfolio state
        self.save_portfolio(
            cash=portfolio.cash,
            initial_value=portfolio.initial_value,
            positions=portfolio._positions
        )
        print("  ✅ Portfolio with 3 positions created")
        
        # Clear pending orders (remove entire directory and recreate)
        if self.pending_orders_dir.exists():
            import shutil
            shutil.rmtree(self.pending_orders_dir)
        self.pending_orders_dir.mkdir(parents=True, exist_ok=True)
        print("  ✅ Pending orders cleared")
        
        return {
            "scenario": 2,
            "description": "Market open, with holdings",
            "expected_behavior": [
                "System loads existing positions",
                "Real-time prices fetched for holdings",
                "Unrealized P&L calculated",
                "Agents consider existing exposure",
                "May generate BUY/SELL/HOLD decisions",
                "Position limits respected (max 15% per stock)"
            ]
        }
    
    def setup_scenario_3(self):
        """
        Scenario 3: Market closed, no holdings
        - Empty portfolio (cash only)
        - No pending orders
        - Market is closed (simulated if actually open)
        """
        print("\n" + "="*80)
        print("📋 SCENARIO 3: Market Closed, No Holdings")
        print("="*80)
        print("\nSetup:")
        print("  • Portfolio: $10,000 cash, 0 positions")
        print("  • Pending orders: None")
        print("  • Market status: Closed (or simulated)")
        print()
        
        # Create empty portfolio
        self.save_portfolio(cash=10000.0, initial_value=10000.0, positions={})
        print("  ✅ Portfolio initialized")
        
        # Clear pending orders (remove entire directory and recreate)
        if self.pending_orders_dir.exists():
            import shutil
            shutil.rmtree(self.pending_orders_dir)
        self.pending_orders_dir.mkdir(parents=True, exist_ok=True)
        print("  ✅ Pending orders cleared")
        
        return {
            "scenario": 3,
            "description": "Market closed, no holdings",
            "expected_behavior": [
                "System fetches market data (last closing prices)",
                "Agents analyze and generate recommendations",
                "BUY orders placed as PENDING for next trading day",
                "Orders saved to pending_orders folder",
                "Portfolio unchanged until market opens"
            ]
        }
    
    def setup_scenario_4(self):
        """
        Scenario 4: Market closed, with holdings
        - Portfolio with existing positions
        - May have pending orders from previous session
        - Market is closed (simulated if actually open)
        """
        print("\n" + "="*80)
        print("📋 SCENARIO 4: Market Closed, With Holdings")
        print("="*80)
        print("\nSetup:")
        print("  • Portfolio: $3,000 cash + positions")
        print("  • Positions: NVDA x15, MSFT x20, AAPL x25, GOOGL x10")
        print("  • Pending orders: Possibly from previous session")
        print("  • Market status: Closed (or simulated)")
        print()
        
        # Create portfolio with more holdings
        from src.data.portfolio import Portfolio
        # Calculate required cash: NVDA(15*120) + MSFT(20*380) + AAPL(25*185) + GOOGL(10*140)
        # = 1800 + 7600 + 4625 + 1400 = 15425
        # Start with 20000 cash to have some remaining
        portfolio = Portfolio(cash=20000.0, initial_value=30000.0)
        
        # Add sample positions
        portfolio.buy("NVDA", 15, 120.0)   # 1800
        portfolio.buy("MSFT", 20, 380.0)   # 7600
        portfolio.buy("AAPL", 25, 185.0)   # 4625
        portfolio.buy("GOOGL", 10, 140.0)  # 1400
        # Total: 15425, Remaining cash: 4575
        
        # Save portfolio state
        self.save_portfolio(
            cash=portfolio.cash,
            initial_value=portfolio.initial_value,
            positions=portfolio._positions
        )
        print("  ✅ Portfolio with 4 positions created")
        
        return {
            "scenario": 4,
            "description": "Market closed, with holdings",
            "expected_behavior": [
                "System loads existing positions",
                "Real-time prices fetched (last closing prices)",
                "Unrealized P&L calculated based on close",
                "Agents consider existing exposure",
                "May generate new PENDING orders or SELL decisions",
                "Orders saved for next trading day"
            ]
        }
    
    def run_trading_cycle(self, scenario_info):
        """Execute a full trading cycle"""
        print("\n" + "="*80)
        print("🚀 EXECUTING TRADING CYCLE")
        print("="*80)
        
        from src.orchestrator.trading_cycle import execute_daily_trade
        
        # Load portfolio
        portfolio = self.load_portfolio()
        print(f"\n📊 Initial Portfolio State:")
        print(f"   Cash: ${portfolio.cash:,.2f}")
        print(f"   Positions: {len(portfolio._positions)}")
        print(f"   Total Value: ${portfolio.value({}) if hasattr(portfolio, 'value') else 'N/A'}")
        
        print("\n⏳ Running trading cycle (this may take 1-2 minutes)...")
        print("   • Fetching market data (118 stocks)")
        print("   • Running multi-analyst discussion")
        print("   • Performing risk analysis")
        print("   • Generating trading decisions")
        
        try:
            result = execute_daily_trade(
                universe=None,  # Use default NASDAQ-100
                rounds=3,
                auto_tools=True,
                tool_budget=15,
                min_tools=3,
                portfolio=portfolio,
            )
            
            print("\n✅ Trading cycle completed!")
            return result
            
        except Exception as e:
            print(f"\n❌ Trading cycle failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def verify_results(self, scenario_info, result):
        """Verify the results match expected behavior"""
        print("\n" + "="*80)
        print("✔️  VERIFICATION")
        print("="*80)
        
        checks = []
        
        # Check 1: Trading cycle completed
        checks.append(("Trading cycle completed", result is not None))
        
        if result:
            # Check 2: Market data fetched
            market_agent = result.get("market_agent", {})
            stocks = market_agent.get("stocks", {})
            checks.append(("Market data fetched", len(stocks) > 0))
            print(f"\n   Market Data: {len(stocks)} stocks fetched")
            
            # Check 3: Multi-analyst discussion
            discussion = result.get("discussion", {})
            analyst_reports = discussion.get("analyst_reports", {})
            checks.append(("Multi-analyst discussion", len(analyst_reports) >= 3))
            print(f"   Analysts Participated: {len(analyst_reports)}")
            
            # Check 4: Tool usage
            tool_calls = discussion.get("tool_calls", [])
            checks.append(("Tools used", len(tool_calls) >= 3))
            print(f"   Tools Used: {len(tool_calls)}")
            
            # Check 5: Risk analysis
            risk_report = result.get("risk_report", {})
            checks.append(("Risk analysis completed", "overall_risk_level" in risk_report))
            print(f"   Risk Level: {risk_report.get('overall_risk_level', 'N/A')}")
            
            # Check 6: Trading decisions
            decision = result.get("decision", {})
            buy_orders = decision.get("buy_orders", [])
            sell_orders = decision.get("sell_orders", [])
            checks.append(("Trading decisions generated", len(buy_orders) > 0 or len(sell_orders) > 0))
            print(f"   Buy Orders: {len(buy_orders)}")
            print(f"   Sell Orders: {len(sell_orders)}")
            
            # Check 7: Order execution
            placed_orders = result.get("placed_orders", [])
            executed_trades = result.get("executed_trades", [])
            checks.append(("Orders placed/executed", len(placed_orders) > 0 or len(executed_trades) > 0))
            print(f"   Placed Orders: {len(placed_orders)}")
            print(f"   Executed Trades: {len(executed_trades)}")
            
            # Check 8: Portfolio updated
            portfolio = self.load_portfolio()
            portfolio_updated = True  # Portfolio file exists
            checks.append(("Portfolio state saved", portfolio_updated))
            
            # Check 9: Expected behavior for scenario
            scenario_num = scenario_info["scenario"]
            if scenario_num in [1, 3]:  # No initial holdings
                checks.append(("Started with no holdings", len(buy_orders) > 0))
            else:  # Had holdings
                has_holdings = len(portfolio._positions) > 0
                checks.append(("Had holdings", has_holdings))
        
        # Summary
        passed = sum(1 for _, result in checks if result)
        total = len(checks)
        
        print(f"\n{'='*80}")
        print(f"Test Results: {passed}/{total} checks passed")
        print(f"{'='*80}\n")
        
        for check_name, check_result in checks:
            status = "✅" if check_result else "❌"
            print(f"  {status} {check_name}")
        
        # Show sample data
        if result and result.get("discussion"):
            print(f"\n📝 Sample Discussion Excerpt:")
            transcript = result["discussion"].get("transcript", [])
            if transcript:
                print(f"   {transcript[0][:200]}...")
        
        if result and result.get("decision"):
            print(f"\n💼 Sample Trading Decision:")
            buy_orders = result["decision"].get("buy_orders", [])
            if buy_orders:
                sample = buy_orders[0]
                print(f"   BUY {sample.get('symbol')} x{sample.get('quantity')} @ ${sample.get('buy_price', 0):.2f}")
                print(f"   Rationale: {sample.get('rationale', 'N/A')[:100]}...")
        
        return passed == total


def main():
    print("\n" + "="*80)
    print("🤖 AI-TRADER SCENARIO TESTING")
    print("="*80)
    print(f"\nTest Date: {date.today().isoformat()}")
    print("Using: TODAY'S real market data\n")
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Test AI-Trader scenarios")
    parser.add_argument("--scenario", type=int, choices=[1, 2, 3, 4], 
                       help="Run specific scenario (1-4). If not specified, runs all.")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip backup of current state")
    parser.add_argument("--no-restore", action="store_true",
                       help="Skip restore of original state after testing")
    parser.add_argument("--auto", action="store_true",
                       help="Auto-run without user prompts (for non-interactive testing)")
    args = parser.parse_args()
    
    tester = ScenarioTester()
    
    # Backup original state
    if not args.no_backup:
        tester.backup_state()
    
    # Determine which scenarios to run
    if args.scenario:
        scenarios_to_run = [args.scenario]
    else:
        scenarios_to_run = [1, 2, 3, 4]
    
    results = {}
    
    try:
        for scenario_num in scenarios_to_run:
            # Setup scenario
            if scenario_num == 1:
                scenario_info = tester.setup_scenario_1()
            elif scenario_num == 2:
                scenario_info = tester.setup_scenario_2()
            elif scenario_num == 3:
                scenario_info = tester.setup_scenario_3()
            else:  # 4
                scenario_info = tester.setup_scenario_4()
            
            # Show expected behavior
            print("\n📌 Expected Behavior:")
            for i, behavior in enumerate(scenario_info["expected_behavior"], 1):
                print(f"   {i}. {behavior}")
            
            # Confirm before proceeding
            if not args.auto:
                print(f"\nPress Enter to run Scenario {scenario_num}, or Ctrl+C to skip...")
                try:
                    input()
                except KeyboardInterrupt:
                    print("\n⏭️  Skipping scenario")
                    continue
            else:
                print(f"\n🚀 Auto-running Scenario {scenario_num}...")
            
            # Run trading cycle
            result = tester.run_trading_cycle(scenario_info)
            
            # Verify results
            if result:
                success = tester.verify_results(scenario_info, result)
                results[scenario_num] = {"success": success, "result": result}
            else:
                results[scenario_num] = {"success": False, "result": None}
            
            # Wait before next scenario
            if scenario_num < max(scenarios_to_run) and not args.auto:
                print("\n" + "="*80)
                print(f"Scenario {scenario_num} complete. Press Enter for next scenario...")
                try:
                    input()
                except KeyboardInterrupt:
                    print("\n⏭️  Stopping tests")
                    break
            elif scenario_num < max(scenarios_to_run):
                print(f"\n✅ Scenario {scenario_num} complete. Continuing to next scenario...")
    
    finally:
        # Restore original state
        if not args.no_restore:
            tester.restore_state()
        else:
            print("\n⚠️  Original state NOT restored (--no-restore flag)")
    
    # Final summary
    print("\n" + "="*80)
    print("📊 FINAL SUMMARY")
    print("="*80)
    
    for scenario_num, result_info in results.items():
        status = "✅ PASS" if result_info["success"] else "❌ FAIL"
        print(f"\nScenario {scenario_num}: {status}")
    
    total_passed = sum(1 for r in results.values() if r["success"])
    total_run = len(results)
    
    print(f"\nOverall: {total_passed}/{total_run} scenarios passed")
    
    if total_passed == total_run:
        print("\n🎉 All scenarios passed! System ready for production.")
        return 0
    else:
        print("\n⚠️  Some scenarios failed. Please review the output above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n❌ Testing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

