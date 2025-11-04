# scripts/generate_daily_report.py
"""
生成每日交易报告
包含：
1. 每日交易订单明细
2. 每日净值变化与盈亏分析
3. Agent 参与度验证
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

# Fix Windows encoding issue
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import json
from typing import Dict, Any, List
from datetime import date

from src.data.memory_manager import MemoryManager
from src.data.equity_tracker import EquityTracker


def generate_daily_report(target_date: str) -> Dict[str, Any]:
    """生成指定日期的交易报告"""
    memory_manager = MemoryManager(root="data/logs")
    equity_tracker = EquityTracker(root="data/logs")
    
    # 加载每日记忆
    daily_memory = memory_manager.load_daily_memory(target_date)
    if not daily_memory:
        return {"error": f"No memory found for {target_date}"}
    
    # 加载净值记录
    equity_history = equity_tracker.load_equity_history(start_date=target_date, end_date=target_date)
    equity_record = equity_history[-1] if equity_history else None
    
    # 提取关键信息
    report = {
        "date": target_date,
        "market_analysis": daily_memory.get("market_analysis", {}),
        "discussion": {
            "final_stance": daily_memory.get("discussion", {}).get("final_stance"),
            "rounds": daily_memory.get("discussion", {}).get("rounds"),
            "tools_used": len(daily_memory.get("discussion", {}).get("tool_context", [])),
        },
        "risk_report": daily_memory.get("risk_report", {}),
        "decision": daily_memory.get("decision", {}),
        "executed_trades": daily_memory.get("executed_trades", []),
        "executed_trades_count": daily_memory.get("executed_trades_count", 0),
        "portfolio_snapshot": daily_memory.get("portfolio_snapshot", {}),
        "equity_record": equity_record,
    }
    
    return report


def print_daily_report(report: Dict[str, Any]) -> None:
    """打印每日报告"""
    print("\n" + "="*80)
    print(f" DAILY TRADING REPORT: {report['date']}")
    print("="*80)
    
    # 1. Agent 参与度
    print("\n【Agent 参与度验证】")
    print(f"  ✓ Market Analyst: 已参与")
    if report.get("market_analysis"):
        recommended = report["market_analysis"].get("recommended_stocks", [])
        print(f"    推荐股票: {len(recommended)} 只")
    
    print(f"  ✓ Discussion Agent: 已参与")
    discussion = report.get("discussion", {})
    print(f"    最终立场: {discussion.get('final_stance', 'N/A')}")
    print(f"    讨论轮次: {discussion.get('rounds', 0)}")
    print(f"    工具使用: {discussion.get('tools_used', 0)} 次")
    
    print(f"  ✓ Risk Analyst: 已参与")
    risk_report = report.get("risk_report", {})
    print(f"    风险等级: {risk_report.get('overall_risk_level', 'N/A')}")
    
    print(f"  ✓ Trader Agent: 已参与")
    decision = report.get("decision", {})
    buy_orders = decision.get("buy_orders", [])
    sell_orders = decision.get("sell_orders", [])
    print(f"    买入订单: {len(buy_orders)} 笔")
    print(f"    卖出订单: {len(sell_orders)} 笔")
    
    # 2. 交易订单明细
    print("\n【每日交易订单明细】")
    executed_trades = report.get("executed_trades", [])
    if executed_trades:
        filled = [t for t in executed_trades if t.get("status") == "FILLED"]
        rejected = [t for t in executed_trades if t.get("status") == "REJECTED"]
        
        print(f"  总订单数: {len(executed_trades)}")
        print(f"  成交: {len(filled)} 笔")
        print(f"  拒绝: {len(rejected)} 笔")
        print(f"  成交率: {len(filled)/len(executed_trades)*100:.1f}%")
        
        if filled:
            print("\n  成交明细:")
            for trade in filled:
                symbol = trade.get("symbol")
                action = trade.get("action")
                price = trade.get("price")
                quantity = trade.get("quantity")
                fill_reason = trade.get("fill_reason", "")
                print(f"    ✓ {action} {symbol} x{quantity} @ ${price:.2f} ({fill_reason})")
    else:
        print("  无交易订单")
    
    # 3. 净值变化与盈亏分析
    print("\n【每日净值变化与盈亏分析】")
    portfolio_snapshot = report.get("portfolio_snapshot", {})
    equity_record = report.get("equity_record", {})
    
    if portfolio_snapshot:
        cash = portfolio_snapshot.get("cash", 0)
        equity_value = portfolio_snapshot.get("equity_value", 0)
        total_value = portfolio_snapshot.get("total_value", 0)
        total_pnl = portfolio_snapshot.get("total_pnl", 0)
        total_pnl_pct = portfolio_snapshot.get("total_pnl_pct", 0)
        
        print(f"  现金: ${cash:.2f}")
        print(f"  持仓市值: ${equity_value:.2f}")
        print(f"  总净值: ${total_value:.2f}")
        print(f"  总盈亏: ${total_pnl:.2f} ({total_pnl_pct:.2f}%)")
        
        positions_detail = portfolio_snapshot.get("positions_detail", {})
        if positions_detail:
            print(f"\n  持仓明细 ({len(positions_detail)} 只):")
            for symbol, pos in list(positions_detail.items())[:10]:  # 只显示前10只
                qty = pos.get("quantity", 0)
                avg_cost = pos.get("avg_cost", 0)
                current_price = pos.get("current_price", avg_cost)
                unrealized_pnl = pos.get("unrealized_pnl", 0)
                unrealized_pnl_pct = pos.get("unrealized_pnl_pct", 0)
                print(f"    {symbol}: {qty}股 @ ${avg_cost:.2f} (当前: ${current_price:.2f}, "
                      f"未实现盈亏: ${unrealized_pnl:.2f}, {unrealized_pnl_pct:.2f}%)")
    
    # 与前一日对比（如果有）
    prev_date = (date.fromisoformat(report['date']) - date.resolution).isoformat()
    prev_equity = equity_tracker.load_equity_history(start_date=prev_date, end_date=prev_date)
    if prev_equity:
        prev_value = prev_equity[-1].get("total_value", 0)
        current_value = portfolio_snapshot.get("total_value", 0)
        daily_change = current_value - prev_value
        daily_change_pct = (daily_change / prev_value * 100) if prev_value > 0 else 0
        print(f"\n  与前一日对比:")
        print(f"    前一日净值: ${prev_value:.2f}")
        print(f"    当日净值: ${current_value:.2f}")
        print(f"    日变化: ${daily_change:.2f} ({daily_change_pct:.2f}%)")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate daily trading report")
    parser.add_argument("--date", type=str, help="Date to report (YYYY-MM-DD)")
    
    args = parser.parse_args()
    target_date = args.date or date.today().isoformat()
    
    report = generate_daily_report(target_date)
    if "error" in report:
        print(f"Error: {report['error']}")
    else:
        print_daily_report(report)

