#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日自动交易脚本
- 自动使用昨天的收盘数据作为分析依据
- 自动判断是否为交易日（工作日）
- 自动加载和保存 Portfolio 状态
- 记录运行日志
"""
from __future__ import annotations
import sys
import json
import os
from pathlib import Path
from datetime import date, timedelta, datetime
from typing import Optional

# 添加 backend 目录到路径
ROOT = Path(__file__).resolve().parents[1]  # scripts/ -> backend/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from dotenv import load_dotenv
from src.orchestrator.trading_cycle import execute_daily_trade
from src.data.portfolio import Portfolio
from src.data.trade_log import TradeLogger
from src.data.memory_manager import MemoryManager


def is_trading_day(check_date: date) -> bool:
    """
    判断是否为交易日（简单判断：排除周末）
    
    注意：这里只排除周末，实际的交易日判断需要排除节假日
    可以考虑使用第三方库如 pandas_market_calendars 或 yfinance 的交易日历
    """
    # 排除周末
    if check_date.weekday() >= 5:  # 周六(5) 或 周日(6)
        return False
    return True


def load_portfolio_state(state_file: Path) -> Optional[Portfolio]:
    """加载 Portfolio 状态"""
    if not state_file.exists():
        return None
    
    try:
        with state_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        portfolio = Portfolio(
            cash=float(state.get("cash", 10000.0)),
            initial_value=float(state.get("initial_value", 10000.0)),
        )
        
        # 恢复持仓
        from src.data.portfolio import Position
        positions = state.get("positions", {})
        for symbol, pos_info in positions.items():
            if isinstance(pos_info, dict):
                portfolio._positions[symbol] = Position(
                    symbol=symbol,
                    quantity=int(pos_info.get("quantity", 0)),
                    avg_cost=float(pos_info.get("avg_cost", 0.0)),
                    total_cost=float(pos_info.get("total_cost", 0.0)),
                )
        
        return portfolio
    except Exception as e:
        print(f"[WARN] Failed to load portfolio state: {e}")
        return None


def save_portfolio_state(portfolio: Portfolio, state_file: Path) -> None:
    """保存 Portfolio 状态"""
    try:
        state = {
            "cash": portfolio.cash,
            "initial_value": portfolio.initial_value,
            "positions": {
                symbol: {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": pos.total_cost,
                }
                for symbol, pos in portfolio._positions.items()
            },
            "last_updated": datetime.now().isoformat(),
        }
        
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with state_file.open("w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        print(f"[PORTFOLIO] Saved state to {state_file}")
    except Exception as e:
        print(f"[WARN] Failed to save portfolio state: {e}")


def load_config() -> dict:
    """加载配置文件"""
    config_path = ROOT / "config" / "config.json"
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with config_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_trading_dates(analysis_date: date, history_days: int = 180) -> tuple[str, str]:
    """
    获取交易日期范围
    
    参数:
    - analysis_date: 分析日期（通常是昨天）
    - history_days: 历史数据天数（用于计算技术指标）
    
    返回:
    - (start_date, end_date) 字符串格式 YYYY-MM-DD
    """
    end_date = analysis_date
    start_date = end_date - timedelta(days=history_days)
    
    return (start_date.isoformat(), end_date.isoformat())


def run_daily_trading(
    *,
    analysis_date: Optional[str] = None,
    skip_weekend: bool = True,
    state_file: Optional[Path] = None,
) -> dict:
    """
    运行每日交易
    
    参数:
    - analysis_date: 分析日期 (YYYY-MM-DD)，如果为 None 则使用昨天
    - skip_weekend: 是否跳过周末
    - state_file: Portfolio 状态文件路径
    
    返回:
    - 交易结果字典
    """
    # 加载环境变量
    load_dotenv()
    
    # 确定分析日期
    if analysis_date:
        today = datetime.strptime(analysis_date, "%Y-%m-%d").date()
    else:
        # 默认使用昨天（因为需要昨天的收盘数据）
        today = date.today() - timedelta(days=1)
    
    # 检查是否为交易日
    if skip_weekend and not is_trading_day(today):
        print(f"[SKIP] {today} is not a trading day (weekend)")
        return {"status": "skipped", "reason": "weekend", "date": today.isoformat()}
    
    print(f"[INFO] Running daily trading for {today}")
    
    # 加载配置
    try:
        config = load_config()
    except Exception as e:
        print(f"[ERROR] Failed to load config: {e}")
        return {"status": "error", "error": str(e)}
    
    # 设置文件路径
    if state_file is None:
        state_file = ROOT / "data" / "portfolio_state.json"
    
    log_dir = ROOT / "data" / "logs"
    
    # 加载或创建 Portfolio
    portfolio = load_portfolio_state(state_file)
    if portfolio is None:
        initial_cash = float(config.get("initial_cash", 10000.0))
        portfolio = Portfolio(cash=initial_cash, initial_value=initial_cash)
        print(f"[PORTFOLIO] Created new portfolio with ${initial_cash:.2f}")
    else:
        print(f"[PORTFOLIO] Loaded portfolio: cash=${portfolio.cash:.2f}, positions={len(portfolio._positions)}")
    
    # 创建 Trade Logger
    trade_logger = TradeLogger(root=str(log_dir))
    
    # 获取交易日期范围
    start_date, end_date = get_trading_dates(today, history_days=180)
    
    # 获取 universe
    universe = config.get("universe", [])
    if not universe:
        raise ValueError("No universe defined in config.json")
    
    # 执行交易循环
    try:
        print(f"[INFO] Executing trading cycle for {today}...")
        result = execute_daily_trade(
            universe=universe,
            start=start_date,
            end=end_date,
            rounds=config.get("discussion_rounds", 3),
            auto_tools=config.get("discussion_auto_tools", True),
            tool_budget=config.get("discussion_tool_budget", 2),
            preferred_domains=config.get("preferred_domains"),
            portfolio=portfolio,
            trade_logger=trade_logger,
        )
        
        # === 收盘后检查挂单是否成交（完整闭环） ===
        # 注意：这里假设脚本在收盘后运行（16:30之后）
        # 如果是开盘前运行（09:00），则应该设置另一个定时任务在收盘后运行 check_pending_orders
        from src.data.order_manager import OrderManager
        from scripts.check_pending_orders import check_and_execute_pending_orders
        
        order_manager = OrderManager(root=str(log_dir))
        pending_orders = order_manager.load_pending_orders(order_date=today.isoformat())
        
        if pending_orders:
            print(f"\n[POST-MARKET] Checking {len(pending_orders)} pending orders...")
            fill_result = check_and_execute_pending_orders(
                check_date=today.isoformat(),
                portfolio_state_file=state_file,
                portfolio=portfolio,  # 使用当前 portfolio 实例
            )
            print(f"[POST-MARKET] Fill result: {fill_result['filled_count']} filled, {fill_result['rejected_count']} rejected")
            
            # 更新 result 以包含成交明细
            if fill_result.get("executed_trades"):
                result["executed_trades"] = fill_result["executed_trades"]
                result["fill_result"] = fill_result
        else:
            print(f"\n[POST-MARKET] No pending orders to check")
        
        # 保存 Portfolio 状态（成交后）
        save_portfolio_state(portfolio, state_file)
        
        # 打印结果摘要
        print(f"\n{'='*80}")
        print(f"Daily Trading Result - {today}")
        print(f"{'='*80}")
        print(f"Stance: {result.get('stance', 'N/A')}")
        print(f"Decision: {result.get('decision', {}).get('action', 'N/A')}")
        executed_trades_count = len(result.get('executed_trades', []))
        print(f"Executed Trades: {executed_trades_count}")
        print(f"Portfolio Value: ${result.get('portfolio', {}).get('total_value', 0):.2f}")
        print(f"Cash: ${result.get('portfolio', {}).get('cash', 0):.2f}")
        print(f"Total P&L: ${result.get('portfolio', {}).get('total_pnl', 0):.2f} ({result.get('portfolio', {}).get('total_pnl_pct', 0)*100:.2f}%)")
        print(f"{'='*80}\n")
        
        return {
            "status": "success",
            "date": today.isoformat(),
            "result": result,
        }
        
    except Exception as e:
        print(f"[ERROR] Trading cycle failed: {e}")
        import traceback
        traceback.print_exc()
        
        # 即使失败也保存 Portfolio 状态（防止丢失）
        save_portfolio_state(portfolio, state_file)
        
        return {
            "status": "error",
            "date": today.isoformat(),
            "error": str(e),
        }


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run daily trading cycle")
    parser.add_argument(
        "--date",
        type=str,
        help="Analysis date (YYYY-MM-DD), default: yesterday",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force run even on weekends",
    )
    parser.add_argument(
        "--state-file",
        type=str,
        help="Portfolio state file path (default: data/portfolio_state.json)",
    )
    
    args = parser.parse_args()
    
    state_file_path = None
    if args.state_file:
        state_file_path = Path(args.state_file)
    
    result = run_daily_trading(
        analysis_date=args.date,
        skip_weekend=not args.force,
        state_file=state_file_path,
    )
    
    if result.get("status") == "error":
        sys.exit(1)

