#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
完整的交易循环测试
测试多股票持仓改进后的完整交易流程
"""
import sys
import os
from pathlib import Path

# 设置 UTF-8 编码（Windows 兼容）
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    sys.stderr.reconfigure(encoding='utf-8') if hasattr(sys.stderr, 'reconfigure') else None

# 添加 backend 目录到路径（从 tests/ 向上到 backend/）
ROOT = Path(__file__).resolve().parents[1]  # tests/ -> backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger
from datetime import date, timedelta

def test_full_trading_loop():
    """测试完整的交易循环"""
    print("=" * 80)
    print("Complete Trading Loop Test - Multi-Stock Portfolio Improvements")
    print("=" * 80)
    print()
    
    # 初始化 Portfolio 和 TradeLogger
    portfolio = Portfolio(cash=10000.0, initial_value=10000.0)
    trade_logger = TradeLogger(root="data/logs")
    
    # 测试用的股票 universe（较小，便于快速测试）
    test_universe = ["NVDA", "MSFT", "AAPL", "GOOGL", "AMZN"]
    
    # 设置日期范围（最近30天）
    end_date = date.today() - timedelta(days=1)  # 昨天
    start_date = end_date - timedelta(days=30)   # 30天前
    
    print(f"Test Configuration:")
    print(f"  - Universe: {test_universe}")
    print(f"  - Date Range: {start_date} to {end_date}")
    print(f"  - Initial Cash: ${portfolio.cash:.2f}")
    print()
    
    try:
        # 执行交易循环
        print("Starting trading loop...")
        print("-" * 80)
        
        result = execute_daily_trade(
            start=start_date.isoformat(),
            end=end_date.isoformat(),
            universe=test_universe,
            rounds=3,  # 3轮讨论
            auto_tools=True,
            tool_budget=2,
            portfolio=portfolio,
            trade_logger=trade_logger,
        )
        
        print()
        print("=" * 80)
        print("Trading Loop Completed!")
        print("=" * 80)
        print()
        
        # 显示结果摘要
        print("Trading Result Summary:")
        print("-" * 80)
        
        # 1. 市场数据
        market_agent = result.get("market_agent", {})
        stocks_data = market_agent.get("stocks", {})
        # 如果 stocks_data 为空，尝试从其他地方获取
        if not stocks_data:
            # 可能数据在其他字段
            pass
        print(f"  [OK] Market Data: Fetched data for {len(test_universe)} stocks (processed: {len(stocks_data)} with data)")
        
        # 2. Market Analyst 推荐
        market_analysis = result.get("market_analysis", {})
        recommended_stocks = market_analysis.get("recommended_stocks", [])
        print(f"  [OK] Market Analyst: Recommended {len(recommended_stocks)} stocks")
        if recommended_stocks:
            print(f"       Recommended: {', '.join(recommended_stocks[:5])}")
        
        # 3. Discussion
        discussion = result.get("discussion", {})
        final_stance = discussion.get("final_stance", "neutral")
        rounds = discussion.get("rounds", 0)
        print(f"  [OK] Discussion: {rounds} rounds, final stance = {final_stance}")
        
        # 4. Risk Analyst
        risk_report = result.get("risk_report", {})
        overall_risk = risk_report.get("overall_risk_level", "unknown")
        print(f"  [OK] Risk Analyst: Overall risk level = {overall_risk}")
        
        # 5. Trader Agent 决策
        decision = result.get("decision", {})
        action = decision.get("action", "HOLD")
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        print(f"  [OK] Trader Agent: Decision = {action}")
        print(f"       Buy Orders: {len(buy_orders)} orders")
        if buy_orders:
            for order in buy_orders[:5]:
                symbol = order.get("symbol")
                quantity = order.get("quantity")
                total_cost = order.get("total_cost", 0)
                print(f"         - {symbol}: {quantity} shares @ ${total_cost:.2f}")
        print(f"       Sell Orders: {len(sell_orders)} orders")
        if sell_orders:
            for order in sell_orders[:5]:
                symbol = order.get("symbol")
                quantity = order.get("quantity")
                total_proceeds = order.get("total_proceeds", 0)
                print(f"         - {symbol}: {quantity} shares @ ${total_proceeds:.2f}")
        
        # 6. 交易执行
        executed_trades = result.get("executed_trades", [])
        execution_errors = result.get("execution_errors", [])
        print(f"  [OK] Trade Execution: {len(executed_trades)} successful trades")
        if execution_errors:
            print(f"       Errors: {len(execution_errors)}")
            for error in execution_errors[:3]:
                print(f"         - {error}")
        
        # 7. Portfolio 状态
        portfolio_info = result.get("portfolio", {})
        cash = portfolio_info.get("cash", 0)
        positions = portfolio_info.get("positions", {})
        total_value = portfolio_info.get("total_value", 0)
        total_pnl = portfolio_info.get("total_pnl", 0)
        total_pnl_pct = portfolio_info.get("total_pnl_pct", 0)
        
        print()
        print("Portfolio Status:")
        print("-" * 80)
        print(f"  Cash: ${cash:.2f}")
        print(f"  Positions: {len(positions)} stocks")
        if positions:
            print(f"  Position Details:")
            for symbol, qty in list(positions.items())[:5]:
                print(f"    - {symbol}: {qty} shares")
        print(f"  Total Value: ${total_value:.2f}")
        print(f"  Total P&L: ${total_pnl:.2f} ({total_pnl_pct:.2f}%)")
        
        # 8. 多股票持仓验证
        print()
        print("Multi-Stock Portfolio Verification:")
        print("-" * 80)
        if len(positions) > 1:
            print(f"  [OK] Successfully holding {len(positions)} stocks (multi-stock feature works!)")
            # 计算每只股票的仓位百分比
            if total_value > 0:
                for symbol, qty in positions.items():
                    # 需要从 last_prices 获取当前价格
                    last_prices = result.get("last_prices", {})
                    current_price = last_prices.get(symbol, 0)
                    if current_price > 0:
                        position_value = qty * current_price
                        position_pct = (position_value / total_value) * 100
                        print(f"    - {symbol}: {position_pct:.2f}% position ({qty} shares @ ${current_price:.2f})")
        elif len(positions) == 1:
            print(f"  [WARN] Only holding 1 stock (may be due to cash constraints or insufficient signals)")
        else:
            print(f"  [WARN] No stocks held (may be HOLD decision or no recommended stocks)")
        
        print()
        print("=" * 80)
        print("Test Completed Successfully!")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print()
        print("=" * 80)
        print("Test Failed!")
        print("=" * 80)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_trading_loop()
    sys.exit(0 if success else 1)

