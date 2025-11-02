# tests/test_05_backend_integration.py
"""
测试后端逻辑优化：Portfolio、Risk Analyst、Trader Agent 集成
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger
from src.agents.risk_analyst import run_risk_analyst
from src.agents.trader_agent import run_trader
from src.orchestrator.trading_cycle import execute_daily_trade


def test_portfolio_pnl():
    """测试 Portfolio P&L 计算"""
    print("\n" + "="*80)
    print("Test 1: Portfolio P&L Calculation")
    print("="*80)
    
    portfolio = Portfolio(cash=10000.0, initial_value=10000.0)
    
    # 买入股票
    portfolio.buy("NVDA", 10, 100.0)  # 成本 $1000
    portfolio.buy("MSFT", 5, 200.0)    # 成本 $1000
    portfolio.buy("NVDA", 5, 110.0)    # 加权平均成本 = (10*100 + 5*110) / 15 = 103.33
    
    # 检查平均成本
    nvda_pos = portfolio.get_position("NVDA")
    assert nvda_pos is not None, "NVDA position should exist"
    assert abs(nvda_pos.avg_cost - 103.33) < 1.0, f"Expected avg_cost ~103.33, got {nvda_pos.avg_cost}"
    assert nvda_pos.quantity == 15, f"Expected quantity 15, got {nvda_pos.quantity}"
    
    # 计算 P&L
    last_prices = {"NVDA": 120.0, "MSFT": 210.0}
    
    # 总净值
    total_value = portfolio.value(last_prices)
    print(f"Total Value: ${total_value:.2f}")
    assert total_value > 0, "Total value should be positive"
    
    # 总盈亏
    total_pnl = portfolio.total_pnl(last_prices)
    print(f"Total P&L: ${total_pnl:.2f}")
    
    # 总盈亏百分比
    total_pnl_pct = portfolio.total_pnl_pct(last_prices)
    print(f"Total P&L %: {total_pnl_pct:.2f}%")
    
    # 单股 P&L
    nvda_pnl = portfolio.get_position_pnl("NVDA", 120.0)
    print(f"NVDA P&L: {nvda_pnl}")
    assert nvda_pnl["unrealized_pnl"] > 0, "NVDA should have profit"
    assert nvda_pnl["unrealized_pnl_pct"] > 0, "NVDA should have positive P&L %"
    
    # 所有持仓 P&L
    all_pnl = portfolio.get_all_positions_pnl(last_prices)
    print(f"All Positions P&L keys: {list(all_pnl.keys())}")
    assert "NVDA" in all_pnl, "NVDA should be in all_pnl"
    assert "MSFT" in all_pnl, "MSFT should be in all_pnl"
    
    print("[TEST 1] PASS: Portfolio P&L Calculation OK")


def test_risk_analyst_with_positions():
    """测试 Risk Analyst 评估当前仓位风险"""
    print("\n" + "="*80)
    print("Test 2: Risk Analyst with Current Positions")
    print("="*80)
    
    # 模拟市场数据
    market_json = {
        "stocks": {
            "NVDA": {"price": 120.0, "signal_score": 1.2},
            "MSFT": {"price": 210.0, "signal_score": 0.8},
            "AAPL": {"price": 180.0, "signal_score": 0.5},
        }
    }
    
    # 模拟当前持仓（NVDA 持仓过重）
    current_positions = {
        "NVDA": {
            "quantity": 50,
            "avg_cost": 100.0,
            "current_price": 120.0,
            "market_value": 6000.0,
        },
        "MSFT": {
            "quantity": 10,
            "avg_cost": 200.0,
            "current_price": 210.0,
            "market_value": 2100.0,
        },
    }
    
    portfolio_value = 10000.0  # 总净值
    
    # 调用 Risk Analyst
    risk_report = run_risk_analyst(
        market_json=market_json,
        current_positions=current_positions,
        portfolio_value=portfolio_value,
        discussion_risk_signals=None,
    )
    
    print(f"Overall Risk Level: {risk_report.get('overall_risk_level')}")
    print(f"Risk Score: {risk_report.get('risk_score'):.2f}")
    
    # 检查当前仓位风险
    position_risk = risk_report.get("current_position_risk", {})
    print(f"Position Concentration: {position_risk.get('position_concentration'):.4f}")
    print(f"Overall Exposure: {position_risk.get('overall_exposure'):.4f}")
    print(f"Single Stock Exposure: {position_risk.get('single_stock_exposure')}")
    
    # 检查仓位控管报告
    control_report = risk_report.get("position_control_report", {})
    limit_checks = control_report.get("position_limit_checks", [])
    print(f"Position Limit Checks: {len(limit_checks)}")
    
    # NVDA 应该超过限制（6000/10000 = 60% > 15%）
    if limit_checks:
        nvda_check = next((c for c in limit_checks if c.get("symbol") == "NVDA"), None)
        if nvda_check:
            print(f"NVDA Exposure: {nvda_check.get('exposure'):.2%}, Limit: {nvda_check.get('limit'):.2%}")
            assert nvda_check.get("status") == "over_limit", "NVDA should be over limit"
    
    print("[TEST 2] PASS: Risk Analyst with Positions OK")


def test_trader_agent_output():
    """测试 Trader Agent 输出完整买卖订单"""
    print("\n" + "="*80)
    print("Test 3: Trader Agent Complete Output")
    print("="*80)
    
    # 模拟输入
    market = {"stocks": {"NVDA": {"price": 120.0}, "MSFT": {"price": 210.0}}}
    mview = {
        "recommended_stocks": ["NVDA", "MSFT"],
        "market_sentiment": "constructive",
        "vix": {"risk_score": 4.0},
    }
    convo = {"final_stance": "constructive"}
    last_prices = {"NVDA": 120.0, "MSFT": 210.0}
    
    # 模拟风险报告
    risk_report = {
        "overall_risk_level": "medium",
        "risk_score": 5.0,
        "position_control_report": {
            "recommended_position_sizes": {
                "NVDA": {"max_pct": 0.15},
                "MSFT": {"max_pct": 0.15},
            },
        },
    }
    
    portfolio_value = 10000.0
    current_positions = {}
    
    # 调用 Trader Agent
    decision = run_trader(
        market=market,
        mview=mview,
        rview=risk_report,
        convo=convo,
        last_prices=last_prices,
        current_positions=current_positions,
        portfolio_value=portfolio_value,
    )
    
    print(f"Action: {decision.get('action')}")
    print(f"Buy Orders: {len(decision.get('buy_orders', []))}")
    print(f"Sell Orders: {len(decision.get('sell_orders', []))}")
    
    # 检查输出结构
    assert "action" in decision, "Should have action"
    assert "buy_orders" in decision, "Should have buy_orders"
    assert "sell_orders" in decision, "Should have sell_orders"
    assert "targets" in decision, "Should have targets (backward compatibility)"
    assert "risk_compliance" in decision, "Should have risk_compliance"
    
    # 检查 buy_orders 结构
    buy_orders = decision.get("buy_orders", [])
    if buy_orders:
        order = buy_orders[0]
        assert "symbol" in order, "Buy order should have symbol"
        assert "buy_price" in order, "Buy order should have buy_price"
        assert "quantity" in order, "Buy order should have quantity"
        assert "total_cost" in order, "Buy order should have total_cost"
        print(f"Sample Buy Order: {order}")
    
    print("[TEST 3] PASS: Trader Agent Output OK")


def test_trade_logger():
    """测试 Trade Logger"""
    print("\n" + "="*80)
    print("Test 4: Trade Logger")
    print("="*80)
    
    # 使用临时目录
    import tempfile
    import os
    temp_dir = tempfile.mkdtemp()
    
    try:
        logger = TradeLogger(root=temp_dir)
        
        # 记录交易
        logger.log(
            symbol="NVDA",
            action="BUY",
            price=120.0,
            quantity=10,
            amount=1200.0,
            status="SUCCESS",
            reason="Test buy order",
            rationale="Test rationale",
            stance="constructive",
            vix_risk=4.0,
        )
        
        logger.log(
            symbol="MSFT",
            action="SELL",
            price=210.0,
            quantity=5,
            amount=1050.0,
            status="SUCCESS",
            reason="Test sell order",
        )
        
        # 获取交易记录
        trades = logger.get_trades()
        print(f"Total Trades: {len(trades)}")
        assert len(trades) == 2, f"Expected 2 trades, got {len(trades)}"
        
        # 过滤测试
        buy_trades = logger.get_trades(action="BUY")
        print(f"Buy Trades: {len(buy_trades)}")
        assert len(buy_trades) == 1, "Should have 1 buy trade"
        
        sell_trades = logger.get_trades(action="SELL")
        print(f"Sell Trades: {len(sell_trades)}")
        assert len(sell_trades) == 1, "Should have 1 sell trade"
        
        # 获取统计
        stats = logger.get_statistics()
        print(f"Statistics: {stats}")
        assert stats["total_trades"] == 2, "Should have 2 total trades"
        assert stats["buy_count"] == 1, "Should have 1 buy"
        assert stats["sell_count"] == 1, "Should have 1 sell"
        
        print("[TEST 4] PASS: Trade Logger OK")
    
    finally:
        # 清理临时文件
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)


def test_trading_cycle_integration():
    """测试完整的 Trading Cycle 集成"""
    print("\n" + "="*80)
    print("Test 5: Trading Cycle Integration")
    print("="*80)
    
    # 创建 Portfolio 和 TradeLogger
    portfolio = Portfolio(cash=10000.0, initial_value=10000.0)
    
    import tempfile
    import os
    temp_dir = tempfile.mkdtemp()
    
    try:
        trade_logger = TradeLogger(root=temp_dir)
        
        # 执行交易周期（使用小数据集）
        result = execute_daily_trade(
            universe=["NVDA", "MSFT", "AAPL"],
            rounds=2,
            auto_tools=True,
            tool_budget=2,
            portfolio=portfolio,
            trade_logger=trade_logger,
        )
        
        print(f"Stance: {result.get('stance')}")
        print(f"Decision Action: {result.get('decision', {}).get('action')}")
        print(f"Risk Report: {result.get('risk_report', {}).get('overall_risk_level')}")
        print(f"Executed Trades: {len(result.get('executed_trades', []))}")
        print(f"Execution Errors: {len(result.get('execution_errors', []))}")
        
        # 检查返回结构
        assert "stance" in result, "Should have stance"
        assert "decision" in result, "Should have decision"
        assert "risk_report" in result, "Should have risk_report"
        assert "executed_trades" in result, "Should have executed_trades"
        assert "portfolio" in result, "Should have portfolio"
        
        # 检查 Portfolio 信息
        portfolio_info = result.get("portfolio", {})
        print(f"Portfolio Cash: ${portfolio_info.get('cash', 0):.2f}")
        print(f"Portfolio Total Value: ${portfolio_info.get('total_value', 0):.2f}")
        print(f"Portfolio Total P&L: ${portfolio_info.get('total_pnl', 0):.2f}")
        print(f"Portfolio Total P&L %: {portfolio_info.get('total_pnl_pct', 0):.2f}%")
        
        assert "total_value" in portfolio_info, "Portfolio info should have total_value"
        assert "total_pnl" in portfolio_info, "Portfolio info should have total_pnl"
        assert "positions_pnl" in portfolio_info, "Portfolio info should have positions_pnl"
        
        print("[TEST 5] PASS: Trading Cycle Integration OK")
    
    finally:
        # 清理临时文件
        if os.path.exists(temp_dir):
            import shutil
            shutil.rmtree(temp_dir)


def main():
    """运行所有测试"""
    print("\n" + "="*80)
    print("Backend Integration Tests")
    print("="*80)
    
    try:
        test_portfolio_pnl()
        test_risk_analyst_with_positions()
        test_trader_agent_output()
        test_trade_logger()
        test_trading_cycle_integration()
        
        print("\n" + "="*80)
        print("PASS: All Backend Integration Tests Passed!")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n[FAIL] Assertion Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

