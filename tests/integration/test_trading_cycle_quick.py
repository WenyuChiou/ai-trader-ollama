#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick Trading Cycle Test - Single Round Discussion, Verify Order Recording

This test script verifies that orders are correctly recorded during a trading cycle.
It forces the market status to OPEN for testing purposes and runs a single round
of discussion to ensure order recording functionality works correctly.

Key Features:
- Forces market status to OPEN using unittest.mock.patch
- Runs a single round of discussion (rounds=1) for quick testing
- Verifies order recording before and after execution
- Checks order completeness (required fields, P&L fields for SELL orders)
- Provides detailed output for debugging

Usage:
    python tests/integration/test_trading_cycle_quick.py
    # Or from project root:
    python -m pytest tests/integration/test_trading_cycle_quick.py -v
"""
import sys
import os
from pathlib import Path
from datetime import datetime, timezone
import json

# Configure UTF-8 encoding (Windows compatibility)
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Add backend and backend/src to path
# From tests/integration/, go up 2 levels to project root, then to backend
backend_dir = Path(__file__).resolve().parents[2] / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))
if str(backend_dir / "src") not in sys.path:
    sys.path.insert(0, str(backend_dir / "src"))

# Set working directory to backend
os.chdir(backend_dir)

# CRITICAL: Force market status to OPEN (for testing)
# Use unittest.mock.patch to ensure all imports and calls use the mock
from unittest.mock import patch

# Mock function: Force return market OPEN status
def mock_is_market_open(check_datetime=None):
    """Mock function: Force return market OPEN status (for testing)"""
    print("[TEST] Mock is_market_open called - returning True (market forced OPEN)")
    return True

# Patch before imports to ensure all subsequent imports use the mock
# Use patch's start() method to activate the patch, which remains active
# throughout the program execution
_patchers = []

# Patch 1: src.utils.trading_days.is_market_open
_patcher1 = patch('src.utils.trading_days.is_market_open', side_effect=mock_is_market_open)
_patcher1.start()
_patchers.append(_patcher1)

# Now import trading_cycle (it will use the mocked is_market_open)
from src.orchestrator.trading_cycle import execute_daily_trade, _get_project_logs_dir
from src.data.order_manager import OrderManager

# Patch 2: OrderManager._is_market_open
_patcher2 = patch.object(OrderManager, '_is_market_open', return_value=True)
_patcher2.start()
_patchers.append(_patcher2)

# Patch 3: Ensure trading_cycle module's internal imports also use mock
# Since trading_cycle imports internally in functions, we need to patch
# module-level references. However, since we've already patched
# src.utils.trading_days.is_market_open, all functions imported from that
# module will use the mock version

print("[TEST] Market status forced to OPEN for testing")

def print_unicode(message):
    """Print Unicode characters (Windows compatibility)"""
    try:
        print(message)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((message + "\n").encode('utf-8'))

def check_orders_before():
    """Check order count before execution"""
    logs_dir = _get_project_logs_dir()
    order_manager = OrderManager(root=str(logs_dir))
    
    pending_before = len(order_manager.load_pending_orders())
    
    filled_file = order_manager.filled_orders_file
    filled_before = 0
    if filled_file.exists():
        with filled_file.open("r", encoding="utf-8") as f:
            filled_before = len([line for line in f if line.strip()])
    
    return pending_before, filled_before

def check_orders_after():
    """Check order count after execution"""
    logs_dir = _get_project_logs_dir()
    order_manager = OrderManager(root=str(logs_dir))
    
    pending_after = len(order_manager.load_pending_orders())
    
    filled_file = order_manager.filled_orders_file
    filled_after = 0
    filled_orders = []
    if filled_file.exists():
        with filled_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        order = json.loads(line)
                        filled_orders.append(order)
                    except:
                        pass
        filled_after = len(filled_orders)
    
    return pending_after, filled_after, filled_orders

def main():
    print_unicode("=" * 80)
    print_unicode("Quick Trading Cycle Test - Single Round Discussion")
    print_unicode("=" * 80)
    print_unicode("")
    print_unicode("[IMPORTANT] Market status forced to OPEN (for testing)")
    print_unicode("")
    
    # Check order status before execution
    print_unicode("[Step 1] Check order status before execution")
    print_unicode("-" * 80)
    pending_before, filled_before = check_orders_before()
    print_unicode(f"Before execution - Pending orders: {pending_before}, Filled orders: {filled_before}")
    print_unicode("")
    
    # Execute trading cycle (1 round)
    print_unicode("[Step 2] Execute trading cycle (rounds=1)")
    print_unicode("-" * 80)
    print_unicode("Configuration:")
    print_unicode("  - rounds: 1 (quick test)")
    print_unicode("  - auto_tools: True")
    print_unicode("  - tool_budget: 8")
    print_unicode("  - universe: Use config.json configuration")
    print_unicode("  - Market status: Forced OPEN (test mode)")
    print_unicode("")
    
    # Verify mock is active
    print_unicode("[TEST] Verify market status mock...")
    from src.utils.trading_days import is_market_open
    test_result = is_market_open(None)
    print_unicode(f"[TEST] is_market_open(None) = {test_result} (should be True)")
    if not test_result:
        print_unicode("[ERROR] Mock not working correctly! Market status is still CLOSED!")
        print_unicode("[ERROR] This will cause Trader Agent to not generate orders")
        return False
    print_unicode("[TEST] ✅ Mock is active, market status forced to OPEN")
    print_unicode("")
    
    # CRITICAL: Use context manager to ensure patch remains active throughout execution
    # This ensures that even if trading_cycle.py re-imports internally,
    # it will use the patched version
    with patch('src.utils.trading_days.is_market_open', side_effect=mock_is_market_open), \
         patch.object(OrderManager, '_is_market_open', return_value=True):
        try:
            result = execute_daily_trade(
                rounds=1,  # Run only 1 round of discussion
                auto_tools=True,
                tool_budget=8,
                min_tools=2,
                universe=None  # Use universe from config.json
            )
            
            print_unicode("")
            print_unicode("[OK] Trading cycle execution completed")
            print_unicode("")
            
            # Display result summary
            placed_orders = result.get("placed_orders", [])
            conversations_count = result.get("conversations_count", 0)
            final_stance = result.get("final_stance", "unknown")
            
            print_unicode("Execution Result Summary:")
            print_unicode(f"  - Final stance: {final_stance}")
            print_unicode(f"  - Conversation rounds: {conversations_count}")
            print_unicode(f"  - Orders placed: {len(placed_orders)}")
            
            if placed_orders:
                print_unicode("")
                print_unicode("Order Details:")
                for i, order in enumerate(placed_orders[:10], 1):  # Show only first 10
                    symbol = order.get("symbol", "N/A")
                    action = order.get("action", "N/A")
                    quantity = order.get("quantity", 0)
                    price = order.get("limit_price", 0.0)
                    status = order.get("status", "N/A")
                    print_unicode(f"  {i}. {symbol} {action} x{quantity} @ ${price:.2f} [Status: {status}]")
                
                print_unicode("")
            
            print_unicode("")
        
        except Exception as e:
            print_unicode(f"[ERROR] Trading cycle execution failed: {e}")
            import traceback
            traceback.print_exc()
            print_unicode("")
            return False
    
    # Check order status after execution
    print_unicode("[Step 3] Check order records after execution")
    print_unicode("-" * 80)
    pending_after, filled_after, filled_orders = check_orders_after()
    print_unicode(f"After execution - Pending orders: {pending_after}, Filled orders: {filled_after}")
    print_unicode("")
    
    # Calculate new orders
    new_filled = filled_after - filled_before
    new_pending = pending_after - pending_before
    
    print_unicode("Order Record Changes:")
    print_unicode(f"  - New filled orders: {new_filled}")
    print_unicode(f"  - New pending orders: {new_pending}")
    print_unicode("")
    
    # Display details of new filled orders
    if new_filled > 0 and filled_orders:
        print_unicode("New Filled Order Details:")
        # Show only the last new_filled orders (assuming appended chronologically)
        recent_orders = filled_orders[-new_filled:] if new_filled <= len(filled_orders) else filled_orders
        for i, order in enumerate(recent_orders, 1):
            symbol = order.get("symbol", "N/A")
            action = order.get("action", "N/A")
            quantity = order.get("quantity", 0)
            fill_price = order.get("fill_price", 0.0)
            status = order.get("status", "N/A")
            order_id = order.get("order_id", "N/A")
            placed_at = order.get("placed_at", "N/A")
            filled_at = order.get("filled_at", "N/A")
            
            print_unicode(f"\n  {i}. {symbol} {action} x{quantity} @ ${fill_price:.2f}")
            print_unicode(f"     Order ID: {order_id}")
            print_unicode(f"     Status: {status}")
            print_unicode(f"     Placed At: {placed_at}")
            print_unicode(f"     Filled At: {filled_at}")
            
            # If SELL order, display P&L
            if action == "SELL" and "realized_pnl" in order:
                pnl = order.get("realized_pnl", 0.0)
                pnl_pct = order.get("realized_pnl_pct", 0.0)
                cost_basis = order.get("cost_basis", 0.0)
                proceeds = order.get("proceeds", 0.0)
                print_unicode(f"     Realized P&L: ${pnl:.2f} ({pnl_pct*100:.2f}%)")
                print_unicode(f"     Cost Basis: ${cost_basis:.2f}")
                print_unicode(f"     Proceeds: ${proceeds:.2f}")
        
        print_unicode("")
    
    # Verify results
    print_unicode("=" * 80)
    print_unicode("Test Result Verification")
    print_unicode("=" * 80)
    
    success = True
    issues = []
    
    # Check 1: Are orders recorded?
    if len(placed_orders) > 0:
        if new_filled == 0 and new_pending == 0:
            issues.append("⚠️ Orders placed but not recorded to file (may be market orders immediately filled but recording failed)")
            success = False
        elif new_filled > 0 or new_pending > 0:
            print_unicode("✅ Orders successfully recorded to file")
    else:
        print_unicode("ℹ️ No orders placed this round (this is normal, depends on analysis results)")
    
    # Check 2: Filled order completeness
    if new_filled > 0:
        for order in recent_orders if 'recent_orders' in locals() else []:
            required_fields = ["order_id", "symbol", "action", "quantity", "status", "placed_at", "fill_price", "filled_at"]
            missing_fields = [f for f in required_fields if f not in order]
            if missing_fields:
                issues.append(f"⚠️ Order {order.get('order_id')} missing fields: {', '.join(missing_fields)}")
                success = False
            else:
                print_unicode(f"✅ Order {order.get('order_id')} fields complete")
        
        # Check SELL order P&L fields
        sell_orders = [o for o in (recent_orders if 'recent_orders' in locals() else []) if o.get('action') == 'SELL']
        for order in sell_orders:
            pnl_fields = ["realized_pnl", "realized_pnl_pct", "cost_basis", "proceeds"]
            missing_pnl = [f for f in pnl_fields if f not in order]
            if missing_pnl:
                issues.append(f"⚠️ SELL order {order.get('order_id')} missing P&L fields: {', '.join(missing_pnl)}")
                success = False
            else:
                print_unicode(f"✅ SELL order {order.get('order_id')} P&L fields complete")
    
    if issues:
        print_unicode("")
        print_unicode("Issues Found:")
        for issue in issues:
            print_unicode(f"  {issue}")
    
    print_unicode("")
    print_unicode("=" * 80)
    if success and (new_filled > 0 or new_pending > 0 or len(placed_orders) == 0):
        print_unicode("[SUCCESS] Test passed! Order recording functionality is working correctly")
        return True
    elif len(placed_orders) == 0:
        print_unicode("[INFO] No orders placed this round, cannot verify order recording functionality")
        return True  # No orders is also a normal situation
    else:
        print_unicode("[FAILED] Test failed! Order recording has issues")
        return False

def test_order_status_transition():
    """Test order status transition from PENDING to FILLED"""
    print_unicode("")
    print_unicode("=" * 80)
    print_unicode("Test: Order Status Transition (PENDING → FILLED)")
    print_unicode("=" * 80)
    
    logs_dir = _get_project_logs_dir()
    order_manager = OrderManager(root=str(logs_dir))
    
    # Load pending orders
    pending_orders = order_manager.load_pending_orders()
    
    if not pending_orders:
        print_unicode("ℹ️ No pending orders found - skipping status transition test")
        return True
    
    print_unicode(f"Found {len(pending_orders)} pending orders")
    
    # Check order status fields
    success = True
    for order in pending_orders:
        order_id = order.get("order_id", "N/A")
        status = order.get("status", "N/A")
        
        if status != "PENDING":
            print_unicode(f"⚠️ Order {order_id} has status '{status}' instead of 'PENDING'")
            success = False
        else:
            print_unicode(f"✅ Order {order_id} has correct PENDING status")
        
        # Check that PENDING orders don't have filled_at
        if "filled_at" in order and order.get("filled_at"):
            print_unicode(f"⚠️ Order {order_id} is PENDING but has filled_at timestamp")
            success = False
    
    # Check filled orders for proper status
    filled_file = order_manager.filled_orders_file
    if filled_file.exists():
        filled_orders = []
        with filled_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        order = json.loads(line)
                        filled_orders.append(order)
                    except:
                        pass
        
        for order in filled_orders[-10:]:  # Check last 10 filled orders
            order_id = order.get("order_id", "N/A")
            status = order.get("status", "N/A")
            
            if status != "FILLED":
                print_unicode(f"⚠️ Order {order_id} in filled_orders.jsonl has status '{status}' instead of 'FILLED'")
                success = False
            else:
                print_unicode(f"✅ Order {order_id} has correct FILLED status")
            
            # Check that FILLED orders have filled_at
            if "filled_at" not in order or not order.get("filled_at"):
                print_unicode(f"⚠️ Order {order_id} is FILLED but missing filled_at timestamp")
                success = False
    
    if success:
        print_unicode("✅ Order status transition test passed")
    else:
        print_unicode("⚠️ Order status transition test found issues")
    
    return success

def test_order_deduplication():
    """Test that orders are not duplicated"""
    print_unicode("")
    print_unicode("=" * 80)
    print_unicode("Test: Order Deduplication")
    print_unicode("=" * 80)
    
    logs_dir = _get_project_logs_dir()
    order_manager = OrderManager(root=str(logs_dir))
    
    # Load all orders
    pending_orders = order_manager.load_pending_orders()
    
    filled_file = order_manager.filled_orders_file
    filled_orders = []
    if filled_file.exists():
        with filled_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        order = json.loads(line)
                        filled_orders.append(order)
                    except:
                        pass
    
    # Check for duplicate order_ids
    all_order_ids = []
    duplicates = []
    
    for order in pending_orders:
        order_id = order.get("order_id")
        if order_id:
            if order_id in all_order_ids:
                duplicates.append(order_id)
            all_order_ids.append(order_id)
    
    for order in filled_orders:
        order_id = order.get("order_id")
        if order_id:
            if order_id in all_order_ids:
                duplicates.append(order_id)
            all_order_ids.append(order_id)
    
    if duplicates:
        print_unicode(f"⚠️ Found {len(set(duplicates))} duplicate order IDs: {', '.join(set(duplicates)[:5])}")
        return False
    else:
        print_unicode(f"✅ No duplicate order IDs found (checked {len(all_order_ids)} orders)")
        return True

def test_order_completeness():
    """Test that all orders have required fields"""
    print_unicode("")
    print_unicode("=" * 80)
    print_unicode("Test: Order Completeness (All Required Fields)")
    print_unicode("=" * 80)
    
    logs_dir = _get_project_logs_dir()
    order_manager = OrderManager(root=str(logs_dir))
    
    # Required fields for all orders
    required_fields = ["order_id", "symbol", "action", "quantity", "status", "placed_at"]
    
    success = True
    
    # Check pending orders
    pending_orders = order_manager.load_pending_orders()
    for order in pending_orders:
        order_id = order.get("order_id", "N/A")
        missing_fields = [f for f in required_fields if f not in order or not order.get(f)]
        if missing_fields:
            print_unicode(f"⚠️ Pending order {order_id} missing fields: {', '.join(missing_fields)}")
            success = False
    
    # Check filled orders
    filled_file = order_manager.filled_orders_file
    if filled_file.exists():
        with filled_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        order = json.loads(line)
                        order_id = order.get("order_id", "N/A")
                        missing_fields = [f for f in required_fields if f not in order or not order.get(f)]
                        filled_fields = ["fill_price", "filled_at"]
                        missing_filled = [f for f in filled_fields if f not in order or not order.get(f)]
                        
                        if missing_fields:
                            print_unicode(f"⚠️ Filled order {order_id} missing required fields: {', '.join(missing_fields)}")
                            success = False
                        if missing_filled:
                            print_unicode(f"⚠️ Filled order {order_id} missing filled fields: {', '.join(missing_filled)}")
                            success = False
                    except:
                        pass
    
    if success:
        print_unicode("✅ All orders have required fields")
    else:
        print_unicode("⚠️ Some orders are missing required fields")
    
    return success

if __name__ == "__main__":
    success = main()
    
    # Run additional tests
    if success:
        success = test_order_status_transition() and success
        success = test_order_deduplication() and success
        success = test_order_completeness() and success
    
    sys.exit(0 if success else 1)

