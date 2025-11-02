# src/orchestrator/trading_cycle.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, timedelta

# --- Market: 批次抓價 + 指標 ---
from src.tools.market_tools import fetch_market_batch

# --- Discussion: 帶經驗調整機制（auto-tools）---
from src.agents.analyst_discussion import run_analyst_discussion

# --- Risk Analyst: 評估倉位風險 ---
from src.agents.risk_analyst import run_risk_analyst

# --- Trader Agent: 交易決策 ---
from src.agents.trader_agent import run_trader

# --- Portfolio: 持倉管理 ---
from src.data.portfolio import Portfolio

# --- Trade Logger: 交易記錄 ---
from src.data.trade_log import TradeLogger


def _default_universe() -> List[str]:
    # 最小預設，不依賴 config，直接可跑
    return ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]


def _default_window() -> Tuple[str, str]:
    # 預設近 180 天
    end = date.today()
    start = end - timedelta(days=180)
    return (start.isoformat(), end.isoformat())


def _top_by_signal(stocks: Dict[str, Dict[str, float]], k: int = 5) -> List[Tuple[str, float]]:
    items: List[Tuple[str, float]] = []
    for s, d in (stocks or {}).items():
        try:
            sc = float(d.get("signal_score"))
        except Exception:
            sc = float("nan")
        items.append((s, sc))
    # NaN 排後
    items.sort(key=lambda x: (float("-inf") if x[1] != x[1] else x[1]), reverse=True)
    return [(s, sc) for s, sc in items[:k] if sc == sc]


def execute_daily_trade(
    *,
    start: str | None = None,
    end: str | None = None,
    universe: List[str] | None = None,
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget: int = 2,
    preferred_domains: List[str] | None = None,
    portfolio: Optional[Portfolio] = None,
    trade_logger: Optional[TradeLogger] = None,
) -> Dict[str, Any]:
    """
    單日交易流程（集成 Portfolio 和 Risk Analyst）：
      1) Market：抓取 universe 的 OHLCV + 指標（fetch_market_batch）
      2) Analyst Discussion：若資訊不足自動用工具補齊（news_scan / vix_term / fear_greed）
      3) Risk Analyst：評估當前倉位風險，提出倉位控管報告
      4) Trader：依最終 stance + VIX 風險 + Risk Report 做 BUY/HOLD/SELL 建議（包含價格和數量）
      5) 執行交易：更新 Portfolio 並記錄 Trade Logger
    """

    # ---- 參數預設 ----
    if universe is None:
        universe = _default_universe()
    if start is None or end is None:
        start, end = _default_window()
    if preferred_domains is None:
        preferred_domains = [
            "www.cboe.com", "www.wsj.com", "www.reuters.com", "www.ft.com",
            "www.cmegroup.com", "fred.stlouisfed.org", "home.treasury.gov"
        ]

    # ---- (1) 市場層 ----
    # fetch_market_batch 是 LangChain StructuredTool，需要使用 .invoke() 调用
    # 注意：fetch_market_batch 只接受 symbols, start, end 三个参数
    market_view: Dict[str, Any] = fetch_market_batch.invoke({
        "symbols": universe,
        "start": start,
        "end": end,
    })
    # market_view 典型：
    # {
    #   "stocks": {SYM: {price, change_pct, rsi14, macd, bb_pos, signal_score, ...}, ...},
    #   "vix": {"level": ..., "chg_1d": ..., "zscore": ...}
    # }

    # ---- (1b) 輕量 enriched 給討論層 ----
    stocks = market_view.get("stocks") or {}
    symbols = list(stocks.keys())
    signal_top = _top_by_signal(stocks, k=5)
    
    # ---- (1c) Market Analyst：評估所有 universe 股票，生成推薦列表 ----
    from src.tools.market_analyst import run_market_analyst
    market_analysis = run_market_analyst(market_view)
    recommended_stocks = market_analysis.get("recommended_stocks", [])

    enriched_market: Dict[str, Any] = {
        "symbols": symbols,
        # 交給 discussion 自動補：vix_term / fear_greed / news
        "vix_term": market_view.get("vix_term"),      # 如果你稍後在 market 層就算好也可帶入
        "fear_greed": market_view.get("fear_greed"),
        "news": None,
        "signal_score_top": signal_top,
        "stocks": stocks,
        "vix": market_view.get("vix"),
        "recommended_stocks": recommended_stocks,  # 添加 Market Analyst 的推薦股票列表
        "market_sentiment": market_analysis.get("market_sentiment", "neutral"),  # 添加市場情緒
    }

    # ---- 初始化 Portfolio 和 Trade Logger（如果未提供）----
    if portfolio is None:
        portfolio = Portfolio()
    if trade_logger is None:
        trade_logger = TradeLogger()

    # ---- 最新收盤價（用於多處）----
    last_prices = {}
    for s, d in stocks.items():
        try:
            last_prices[s] = float(d.get("price"))
        except Exception:
            pass

    # ---- (2) 討論層（自動補工具）----
    convo = run_analyst_discussion(
        enriched_market,
        _unused=None,                   # 第二个参数是 _unused（用于向后兼容）
        rounds=rounds,
        auto_tools=auto_tools,
        tool_budget=tool_budget,
        preferred_domains=preferred_domains,
    )
    final_stance = convo.get("final_stance", "neutral")
    
    # 提取 Discussion 的风险信号（用于 Risk Analyst）
    discussion_risk_signals = {
        "risk_level": "medium",
        "risk_signals": convo.get("risk_signals", []),
    }

    # ---- (3) Risk Analyst：評估倉位風險 ----
    # 准备当前持仓信息（用于 Risk Analyst）
    current_positions_info = {}
    if portfolio:
        portfolio_value = portfolio.value(last_prices)
        for symbol, pos in portfolio._positions.items():
            current_price = last_prices.get(symbol, pos.avg_cost)
            current_positions_info[symbol] = {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "current_price": current_price,
                "market_value": pos.quantity * current_price,
            }
    else:
        portfolio_value = 10000.0  # 默认初始净值
    
    # 调用 Risk Analyst
    risk_report = run_risk_analyst(
        market_json=market_view,
        current_positions=current_positions_info if current_positions_info else None,
        portfolio_value=portfolio_value,
        discussion_risk_signals=discussion_risk_signals,
    )

    # ---- (4) Trader Agent：交易決策 ----
    # 从配置文件中读取仓位限制参数（如果可用）
    from pathlib import Path
    import json
    
    position_config = {
        "max_position_per_stock": 0.15,  # 默认单股最大15%
        "max_total_position": 0.85,  # 默认总仓位85%（保留15%现金）
        "min_position_per_stock": 0.03,  # 默认单股最小3%（允许更小的仓位分散投资）
    }
    
    # 尝试从 config.json 读取仓位限制
    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                position_config["max_position_per_stock"] = float(config_data.get("position_limit_per_stock", 0.15))
                position_config["max_total_position"] = float(config_data.get("position_limit_total", 0.85))
                # min_position_per_stock 如果配置中没有，使用默认值
                position_config["min_position_per_stock"] = float(config_data.get("position_limit_min_per_stock", 0.03))
    except Exception:
        # 如果读取失败，使用默认值
        pass
    
    decision = run_trader(
        market=market_view,
        mview=enriched_market,
        rview=risk_report,  # 传入 Risk Report
        convo=convo,
        last_prices=last_prices,
        current_positions=current_positions_info if current_positions_info else None,
        portfolio_value=portfolio_value,
        position_config=position_config,  # 传入仓位配置
    )

    # ---- (5) 執行交易並更新 Portfolio ----
    executed_trades = []
    execution_errors = []
    
    # 执行买入订单（改进：支持同时买入多只股票）
    buy_orders = decision.get("buy_orders", [])
    
    # 按优先级排序（可以根据 signal_score 或其他指标排序）
    # 这里先按照 buy_price * quantity（金额）排序，确保资金充足时优先买入
    from math import floor
    buy_orders_sorted = sorted(buy_orders, key=lambda x: x.get("total_cost", 0.0), reverse=True)
    
    for order in buy_orders_sorted:
        symbol = order.get("symbol")
        buy_price = order.get("buy_price")
        quantity = order.get("quantity")
        total_cost = order.get("total_cost")
        
        if symbol and buy_price and quantity:
            try:
                # 检查现金是否足够（在买入前再次检查）
                if total_cost > portfolio.cash:
                    # 现金不足，尝试减少数量
                    max_affordable_qty = floor(portfolio.cash / buy_price)
                    if max_affordable_qty > 0:
                        quantity = max_affordable_qty
                        total_cost = buy_price * quantity
                        order["quantity"] = quantity
                        order["total_cost"] = total_cost
                    else:
                        # 现金完全不足，跳过这笔订单
                        execution_errors.append(f"BUY {symbol} skipped: insufficient cash (need ${total_cost:.2f}, have ${portfolio.cash:.2f})")
                        continue
                
                portfolio.buy(symbol, quantity, buy_price)
                # 记录交易
                trade_logger.log(
                    symbol=symbol,
                    action="BUY",
                    price=buy_price,
                    quantity=quantity,
                    amount=total_cost,
                    status="SUCCESS",
                    reason=decision.get("rationale"),
                    rationale=decision.get("rationale"),
                    stance=decision.get("stance"),
                    vix_risk=decision.get("vix_risk"),
                )
                executed_trades.append({
                    "symbol": symbol,
                    "action": "BUY",
                    "price": buy_price,
                    "quantity": quantity,
                    "amount": total_cost,
                    "status": "SUCCESS",
                })
            except Exception as e:
                execution_errors.append(f"BUY {symbol} failed: {e}")
                trade_logger.log(
                    symbol=symbol,
                    action="BUY",
                    price=buy_price,
                    quantity=quantity,
                    amount=total_cost,
                    status="FAILED",
                    reason=f"Execution failed: {e}",
                    rationale=decision.get("rationale"),
                )
    
    # 执行卖出订单
    sell_orders = decision.get("sell_orders", [])
    for order in sell_orders:
        symbol = order.get("symbol")
        sell_price = order.get("sell_price")
        quantity = order.get("quantity")
        total_proceeds = order.get("total_proceeds")
        
        if symbol and sell_price and quantity:
            try:
                portfolio.sell(symbol, quantity, sell_price)
                # 记录交易
                trade_logger.log(
                    symbol=symbol,
                    action="SELL",
                    price=sell_price,
                    quantity=quantity,
                    amount=total_proceeds,
                    status="SUCCESS",
                    reason=decision.get("rationale"),
                    rationale=decision.get("rationale"),
                    stance=decision.get("stance"),
                    vix_risk=decision.get("vix_risk"),
                )
                executed_trades.append({
                    "symbol": symbol,
                    "action": "SELL",
                    "price": sell_price,
                    "quantity": quantity,
                    "amount": total_proceeds,
                    "status": "SUCCESS",
                })
            except Exception as e:
                execution_errors.append(f"SELL {symbol} failed: {e}")
                trade_logger.log(
                    symbol=symbol,
                    action="SELL",
                    price=sell_price,
                    quantity=quantity,
                    amount=total_proceeds,
                    status="FAILED",
                    reason=f"Execution failed: {e}",
                    rationale=decision.get("rationale"),
                )
    
    # ---- 計算當前持倉 P&L（用於後端展示）----
    portfolio_pnl = {}
    if portfolio:
        portfolio_pnl = portfolio.get_all_positions_pnl(last_prices)
        total_pnl = portfolio.total_pnl(last_prices)
        total_pnl_pct = portfolio.total_pnl_pct(last_prices)
        portfolio_value = portfolio.value(last_prices)
        equity_value = portfolio.equity_value(last_prices)
    else:
        total_pnl = 0.0
        total_pnl_pct = 0.0
        portfolio_value = 10000.0
        equity_value = 0.0

    return {
        "stance": final_stance,
        "decision": decision,
        "risk_report": risk_report,
        "discussion": convo,  # 添加完整的讨论信息（包含 transcript, actions 等）
        "rounds": convo.get("rounds"),
        "symbols": symbols,
        "top_signals": signal_top,
        # 执行结果
        "executed_trades": executed_trades,
        "execution_errors": execution_errors,
        # Portfolio 信息（用于后端展示）
        "portfolio": {
            "cash": portfolio.cash if portfolio else 0.0,
            "positions": current_positions_info,
            "total_value": portfolio_value,
            "equity_value": equity_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions_pnl": portfolio_pnl,
        },
    }
