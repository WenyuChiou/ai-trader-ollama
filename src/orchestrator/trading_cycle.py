# src/orchestrator/trading_cycle.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, timedelta

# --- Market Agent: 市場數據抓取（支持多資產類別）---
from src.agents.market_agent import run_market_agent

# --- Market Analyst: 市場分析 ---
from src.agents.market_analyst import run_market_analyst

# --- Discussion: 帶經驗調整機制（auto-tools，主導新聞和工具使用）---
from src.agents.analyst_discussion import run_analyst_discussion

# --- Stock Selection Agent: 股票篩選 ---
from src.agents.stock_selection_agent import run_stock_selection_agent

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
    asset_classes: Dict[str, List[str]] | None = None,
    rounds: int = 3,
    auto_tools: bool = True,
    tool_budget: int = 2,
    preferred_domains: List[str] | None = None,
    portfolio: Optional[Portfolio] = None,
    trade_logger: Optional[TradeLogger] = None,
) -> Dict[str, Any]:
    """
    每日交易前分析流程（基于昨天收盘数据 + 昨天/今日新闻 → 今天交易决策）：
    
    流程：
      1) Market Agent：抓取多资产类别市场数据（股票、债券、商品、指数、波动率）
         - 昨天收盘数据 + 历史数据用于技术指标计算
      2) Market Analyst：分析市场数据，评估市场情绪和趋势
      3) Stock Selection Agent：评估所有候选股票，生成 potential_buys 列表
      4) Discussion Agent：多轮讨论形成共识（主导新闻扫描和工具使用）
         - 扫描昨天/今日新闻（news_scan, plan_and_scan_news）
         - 获取 VIX 期限结构（vix_term）
         - 获取恐慌贪婪指数（fear_greed）
         - 讨论股票选择（potential_buys）
      5) Risk Analyst：评估当前仓位风险，提出仓位控管报告
      6) Trader Agent：综合所有信息做出最终交易决策（买入、卖出、持有、调整）
      7) 执行交易：更新 Portfolio 并记录 Trade Logger
    
    注意：
      - Discussion Agent 主导所有新闻和工具的使用（news_scan, vix_term, fear_greed, etc.）
      - 这是日度交易前的分析流程：基于昨天收盘 + 昨天/今日新闻 → 决定今天交易
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

    # ---- (1) Market Agent：市場數據抓取（支持多資產類別）----
    market_agent_result = run_market_agent(
        symbols=universe,
        start=start,
        end=end,
        asset_classes=asset_classes,
    )
    market_view = market_agent_result.get("market_data", {})
    
    # market_view 典型結構：
    # {
    #   "stocks": {SYM: {price, change_pct, rsi14, macd, bb_pos, signal_score, ...}, ...},
    #   "bonds": {"^TNX": {...}, "LQD": {...}, ...},
    #   "commodities": {"GC=F": {...}, "CL=F": {...}, ...},
    #   "indices": {"^GSPC": {...}, "^N225": {...}, ...},
    #   "volatility": {"^VIX": {...}, "^VIX3M": {...}},
    #   "VIX": {"level": ..., "chg_1d": ..., "zscore": ...}
    # }

    # ---- (2) Market Analyst：市場分析 ----
    market_analysis = run_market_analyst(market_view)
    
    # market_analysis 包含：
    # {
    #   "raw": LLM 生成的文本分析,
    #   "market_sentiment": "bullish" / "neutral" / "cautious",
    #   "key_observations": [...],
    #   "recommended_stocks": [...],
    #   "concerns": [...],
    #   "vix": {...}
    # }

    # ---- (2b) 準備基礎數據 ----
    stocks = market_view.get("stocks") or {}
    symbols = list(stocks.keys())
    signal_top = _top_by_signal(stocks, k=5)

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

    # ---- (3) Stock Selection Agent：評估所有候選股票 ----
    vix_info = market_view.get("VIX", {}) or {}
    vix_risk = float(vix_info.get("risk_score", 4.0))
    
    # 调用 Stock Selection Agent 评估所有候选股票
    stock_selection = run_stock_selection_agent(
        market_data=market_view,
        universe=universe,
        last_prices=last_prices,
        vix_risk=vix_risk,
        min_score=3.0,  # 最小评分阈值
        top_n=20,  # 返回前 20 名
    )
    
    potential_buys = stock_selection.get("potential_buys", [])
    stock_rankings = stock_selection.get("stock_rankings", [])
    
    enriched_market: Dict[str, Any] = {
        "symbols": symbols,
        # Market Analyst 的分析结果
        "market_analysis": market_analysis,
        # 交给 Discussion Agent 自动补：vix_term / fear_greed / news
        # Discussion Agent 主导所有工具使用（news_scan, vix_term, fear_greed, plan_and_scan_news）
        "vix_term": market_view.get("vix_term"),      # 如果你稍后在 market 层就算好也可带入
        "fear_greed": market_view.get("fear_greed"),
        "news": None,  # 由 Discussion Agent 主导填充
        "signal_score_top": signal_top,
        "stocks": stocks,
        "bonds": market_view.get("bonds", {}),
        "commodities": market_view.get("commodities", {}),
        "indices": market_view.get("indices", {}),
        "volatility": market_view.get("volatility", {}),
        "vix": market_view.get("VIX"),  # 修正：使用 VIX 而不是 vix
        # 新增：股票选择结果
        "potential_buys": potential_buys,
        "stock_rankings": stock_rankings[:10],  # 只包含前 10 名用于讨论
    }

    # ---- (4) Discussion Agent：多輪討論（主導新聞和工具使用 + 股票選擇討論）----
    # Discussion Agent 主导：
    # - 新闻扫描（news_scan, plan_and_scan_news）：扫描昨天/今日新闻
    # - VIX 期限结构（vix_term）
    # - 恐慌贪婪指数（fear_greed）
    # - 股票选择讨论（potential_buys）
    convo = run_analyst_discussion(
        enriched_market,
        None,  # _unused parameter
        rounds=rounds,
        auto_tools=auto_tools,
        tool_budget=tool_budget,
        preferred_domains=preferred_domains,
        potential_buys=potential_buys,  # 传入潜在购买公司列表供讨论
    )
    final_stance = convo.get("final_stance", "neutral")
    
    # 提取 Discussion 的风险信号（用于 Risk Analyst）
    discussion_risk_signals = {
        "risk_level": "medium",
        "risk_signals": convo.get("risk_signals", []),
    }

    # ---- (5) Risk Analyst：評估倉位風險 ----
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

    # ---- (6) Trader Agent：交易決策 ----
    # 传入所有候选股票（universe）给 Trader Agent
    decision = run_trader(
        market=market_view,
        mview=enriched_market,
        rview=risk_report,  # 传入 Risk Report
        convo=convo,
        last_prices=last_prices,
        current_positions=current_positions_info if current_positions_info else None,
        portfolio_value=portfolio_value,
        all_candidates=universe,  # 传入所有候选股票
    )

    # ---- (5) 執行交易並更新 Portfolio ----
    executed_trades = []
    execution_errors = []
    
    # 执行买入订单
    buy_orders = decision.get("buy_orders", [])
    for order in buy_orders:
        symbol = order.get("symbol")
        buy_price = order.get("buy_price")
        quantity = order.get("quantity")
        total_cost = order.get("total_cost")
        
        if symbol and buy_price and quantity:
            try:
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
        "stock_selection": stock_selection,  # 股票选择结果
        "market_agent": market_agent_result,  # Market Agent 结果（多资产类别）
        "market_analysis": market_analysis,  # Market Analyst 结果
        "discussion": convo,  # Discussion Agent 结果（主导新闻和工具使用）
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
