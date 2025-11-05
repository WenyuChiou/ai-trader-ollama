# src/orchestrator/trading_cycle.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, timedelta, datetime, timezone, time as dt_time
from pathlib import Path  # 统一在文件顶部导入，避免函数内部重复导入导致的作用域问题

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

    # ---- (1.5) 加載歷史記憶（長短記憶）----
    historical_memories = []
    try:
        from src.data.memory_manager import MemoryManager
        memory_manager = MemoryManager(root="data/logs")
        # 加載最近5天的記憶摘要（短期記憶）
        historical_memories = memory_manager.load_recent_memories(
            days=5,
            end_date=end if end else None,
            summary_only=True,  # 只加載摘要，減少 prompt 長度
        )
        if historical_memories:
            print(f"[MEMORY] Loaded {len(historical_memories)} historical memories for context")
    except Exception as e:
        print(f"[MEMORY WARN] Failed to load historical memories: {e}")
        # 不影響主流程，繼續執行

    # ---- (2) 討論層（自動補工具 + 歷史記憶注入）----
    convo = run_analyst_discussion(
        enriched_market,
        _unused=None,                   # 第二个参数是 _unused（用于向后兼容）
        rounds=rounds,
        auto_tools=auto_tools,
        tool_budget=tool_budget,
        preferred_domains=preferred_domains,
        historical_memories=historical_memories,  # 注入歷史記憶
    )
    final_stance = convo.get("final_stance", "neutral")
    
    # 將對話寫入 discussion_actions.jsonl（供前端顯示）
    try:
        # Path 已经在文件顶部导入，不需要重复导入
        import os
        
        # 選項1: 相對於當前工作目錄
        logs_dir = Path("data/logs")
        if not logs_dir.exists():
            # 選項2: 相對於 backend 目錄
            backend_root = Path(__file__).parent.parent.parent
            logs_dir = backend_root / "data" / "logs"
            if not logs_dir.exists():
                # 選項3: 相對於項目根目錄
                project_root = backend_root.parent if backend_root.name == "backend" else backend_root
                logs_dir = project_root / "backend" / "data" / "logs"
        
        logs_dir.mkdir(parents=True, exist_ok=True)
        convo_file = logs_dir / "discussion_actions.jsonl"
        
        transcript = convo.get("transcript", [])
        tool_context = convo.get("tool_context", [])
        actions = convo.get("actions", [])
        
        # 獲取交易日期（使用 end 參數，如果沒有則使用今天）
        trade_date = end if end else date.today().isoformat()
        if isinstance(trade_date, str):
            # 確保是 YYYY-MM-DD 格式
            try:
                from datetime import datetime as dt
                trade_date_obj = dt.strptime(trade_date, "%Y-%m-%d").date()
                trade_date_str = trade_date_obj.isoformat()
            except:
                trade_date_str = date.today().isoformat()
        else:
            trade_date_str = date.today().isoformat()
        
        # 寫入每一輪對話
        import json
        
        for round_num, round_text in enumerate(transcript, 1):
            # 提取 agent 名稱（從 transcript 文本中或使用默認）
            agent_name = "DiscussionAgent"  # 默認
            if "--- Round" in round_text:
                # 嘗試從文本中提取 agent 信息
                lines = round_text.split("\n")
                for line in lines[:5]:  # 檢查前幾行
                    if "agent" in line.lower() or "analyst" in line.lower():
                        if "technical" in line.lower():
                            agent_name = "TechnicalAnalyst"
                        elif "fundamental" in line.lower():
                            agent_name = "FundamentalAnalyst"
                        elif "risk" in line.lower():
                            agent_name = "RiskAnalyst"
                        elif "sentiment" in line.lower():
                            agent_name = "SentimentAnalyst"
                        break
            
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,  # 使用交易日期，不是當前日期
                "agent": agent_name,
                "round": round_num,
                "content": round_text[:500] if len(round_text) > 500 else round_text,  # 限制長度
                "type": "discussion",  # 標記為真實討論，非 demo
            }
            
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # 寫入工具使用記錄
        for tool_info in tool_context:
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,  # 使用交易日期，不是當前日期
                "agent": "ToolSystem",
                "round": 0,
                "content": f"Tool used: {tool_info}",
                "type": "tool",
            }
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
    except Exception as e:
        print(f"[WARN] Failed to write conversations to discussion_actions.jsonl: {e}")
    
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
    # Path 已经在文件顶部导入，不需要重复导入
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

    # ---- (5) 掛單策略：開盤前掛限價單，收盤後檢查成交 ----
    from src.data.order_manager import OrderManager
    
    order_manager = OrderManager(root="data/logs")
    
    # 检查市场是否开盘，决定订单日期
    now = datetime.now()
    is_weekday = now.weekday() < 5
    market_open_time = dt_time(9, 30)  # 9:30 AM
    market_close_time = dt_time(16, 0)  # 4:00 PM
    is_market_open = is_weekday and (market_open_time <= now.time() <= market_close_time)
    
    # 如果市场收盘后，订单日期应该是明天的日期
    existing_pending_orders = []
    if end:
        today = end
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
    elif is_market_open:
        today = date.today().isoformat()
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
    else:
        # 收盘后：订单日期是明天的日期（规划明天的交易）
        tomorrow = date.today() + timedelta(days=1)
        # 如果明天是周末，找到下一个交易日
        while tomorrow.weekday() >= 5:
            tomorrow += timedelta(days=1)
        today = tomorrow.isoformat()
        
        # 检查是否已经有明天的订单计划
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        if existing_pending_orders:
            print(f"[TRADING CYCLE] Market closed. Already have {len(existing_pending_orders)} pending orders for {today}, skipping new order creation.")
    
    executed_trades = []
    execution_errors = []
    placed_orders = []  # 記錄掛單
    
    # 如果已经有待处理订单（收盘后已规划），不创建新订单
    if existing_pending_orders:
        print(f"[TRADING CYCLE] Skipping order creation - {len(existing_pending_orders)} pending orders already exist for {today}")
    else:
        # === OPTIMIZATION: Position limits and cooldown checks ===
        from src.data.trade_history_tracker import TradeHistoryTracker
        from src.utils.config_loader import load_config
        
        # Load configuration for limits
        config = load_config()
        MAX_POSITIONS = config.get("max_positions", 10)  # Maximum number of different stocks
        TRADE_COOLDOWN_HOURS = config.get("trade_cooldown_hours", 24.0)  # 24-hour cooldown
        MIN_CASH_RESERVE_RATIO = config.get("min_cash_reserve_ratio", 0.20)  # Keep 20% cash
        
        # Initialize trade history tracker
        trade_history = TradeHistoryTracker(root="data/logs")
        
        # Check current position count
        current_position_count = len(portfolio._positions)
        portfolio_value = portfolio.value(last_prices)
        
        # Calculate available cash (after reserve)
        required_cash_reserve = portfolio_value * MIN_CASH_RESERVE_RATIO
        available_for_trading = max(0, portfolio.cash - required_cash_reserve)
        
        print(f"[OPTIMIZATION] Position limits: {current_position_count}/{MAX_POSITIONS} positions, "
              f"Available cash: ${available_for_trading:.2f} (reserve: ${required_cash_reserve:.2f})")
        
        # 掛單策略：將所有訂單先掛單，收盤後再檢查成交
        buy_orders = decision.get("buy_orders", [])
        
        # Filter buy orders based on optimization rules
        filtered_buy_orders = []
        for order in buy_orders:
            symbol = order.get("symbol")
            
            # Check 1: Position limit
            if current_position_count >= MAX_POSITIONS:
                # Check if we already have this position
                if symbol not in portfolio._positions:
                    execution_errors.append(f"BUY {symbol} skipped: max positions reached ({current_position_count}/{MAX_POSITIONS})")
                    continue
            
            # Check 2: Cooldown period
            can_trade, hours_remaining = trade_history.can_trade(symbol, TRADE_COOLDOWN_HOURS)
            if not can_trade:
                execution_errors.append(f"BUY {symbol} skipped: cooldown period active ({hours_remaining:.1f} hours remaining)")
                continue
            
            filtered_buy_orders.append(order)
        
        # 按优先级排序（可以根据 signal_score 或其他指标排序）
        # 这里先按照 buy_price * quantity（金额）排序，确保资金充足时优先买入
        from math import floor
        buy_orders_sorted = sorted(filtered_buy_orders, key=lambda x: x.get("total_cost", 0.0), reverse=True)
        
        # 掛單策略：開盤前掛限價單（使用價格範圍最低價作為限價）
        for order in buy_orders_sorted:
            symbol = order.get("symbol")
            buy_price = order.get("buy_price")  # 基准价格（用于计算）
            buy_price_min = order.get("buy_price_min", buy_price)  # 价格范围下限（低买）
            buy_price_max = order.get("buy_price_max", buy_price)  # 价格范围上限
            quantity = order.get("quantity")
            total_cost = order.get("total_cost")
            
            if symbol and buy_price and quantity:
                try:
                    # 檢查現金是否足夠
                    # 使用 buy_price_min 作為限價（但更激進，提高成交率）
                    # buy_price_min 現在是 99.5% 當前價格，而不是 98%
                    limit_price = buy_price_min  # 使用價格範圍最低價作為限價（99.5%當前價格）
                    estimated_cost = limit_price * quantity
                    
                    # Check 3: Cash reserve (use available_for_trading instead of full cash)
                    if estimated_cost > available_for_trading:
                        # 現金不足（考慮保留比例），減少數量
                        max_affordable_qty = floor(available_for_trading / limit_price)
                        if max_affordable_qty > 0:
                            quantity = max_affordable_qty
                            total_cost = limit_price * quantity
                            print(f"[OPTIMIZATION] Reduced {symbol} quantity to {quantity} due to cash reserve limit")
                        else:
                            execution_errors.append(f"BUY {symbol} skipped: insufficient cash after reserve (need ${estimated_cost:.2f}, available ${available_for_trading:.2f})")
                            continue
                    
                    # 掛單：創建限價買單（使用 buy_price_min 作為限價）
                    placed_order = order_manager.place_order(
                        symbol=symbol,
                        action="BUY",
                        quantity=quantity,
                        limit_price=limit_price,  # 限價：使用價格範圍最低價
                        price_range={
                            "min": buy_price_min,
                            "max": buy_price_max,
                        },
                        order_date=today,
                    )
                    placed_orders.append(placed_order)
                    
                    # 注意：訂單已掛單，但尚未執行
                    # 實際執行會在收盤後通過 check_order_fills() 檢查
                    print(f"[ORDER PLACED] BUY {symbol} x{quantity} @ limit ${limit_price:.2f} (will check fill after market close)")
                    
                except Exception as e:
                    execution_errors.append(f"BUY {symbol} order placement failed: {e}")
                    trade_logger.log(
                        symbol=symbol,
                        action="BUY",
                        price=buy_price,
                        quantity=quantity,
                        amount=total_cost,
                        status="FAILED",
                        reason=f"Order placement failed: {e}",
                        rationale=decision.get("rationale"),
                    )
        
        # 执行卖出订单
        sell_orders = decision.get("sell_orders", [])
        for order in sell_orders:
            symbol = order.get("symbol")
            sell_price = order.get("sell_price")  # 基准价格（用于计算）
            sell_price_min = order.get("sell_price_min", sell_price)  # 价格范围下限
            sell_price_max = order.get("sell_price_max", sell_price)  # 价格范围上限（高卖）
            quantity = order.get("quantity")
            total_proceeds = order.get("total_proceeds")
            
            if symbol and sell_price and quantity:
                try:
                    # 檢查持倉是否足夠
                    pos = portfolio.get_position(symbol)
                    if not pos or pos.quantity < quantity:
                        execution_errors.append(f"SELL {symbol}: insufficient position (need {quantity}, have {pos.quantity if pos else 0})")
                        continue
                    
                    # 掛單：創建限價賣單（使用 sell_price_max 作為限價，高賣策略）
                    limit_price = sell_price_max  # 使用價格範圍最高價作為限價
                    
                    placed_order = order_manager.place_order(
                        symbol=symbol,
                        action="SELL",
                        quantity=quantity,
                        limit_price=limit_price,  # 限價：使用價格範圍最高價
                        price_range={
                            "min": sell_price_min,
                            "max": sell_price_max,
                        },
                        order_date=today,
                    )
                    placed_orders.append(placed_order)
                    
                    # 注意：訂單已掛單，但尚未執行
                    # 實際執行會在收盤後通過 check_order_fills() 檢查
                    print(f"[ORDER PLACED] SELL {symbol} x{quantity} @ limit ${limit_price:.2f} (will check fill after market close)")
                    
                except Exception as e:
                    execution_errors.append(f"SELL {symbol} order placement failed: {e}")
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
    # 交易执行后，重新计算持仓信息（包含新买入的股票）
    updated_positions_info = {}
    portfolio_pnl = {}
    if portfolio:
        # 重新计算持仓信息（包含交易后的最新状态）
        portfolio_value = portfolio.value(last_prices)
        for symbol, pos in portfolio._positions.items():
            current_price = last_prices.get(symbol, pos.avg_cost)
            # 确保total_cost正确计算（用于P&L计算）
            total_cost = pos.total_cost if hasattr(pos, 'total_cost') and pos.total_cost > 0 else pos.avg_cost * pos.quantity
            updated_positions_info[symbol] = {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "total_cost": total_cost,
                "cost_basis": total_cost,  # 添加cost_basis字段，便于前端使用
                "current_price": current_price,
                "market_value": pos.quantity * current_price,
            }
        
        portfolio_pnl = portfolio.get_all_positions_pnl(last_prices)
        total_pnl = portfolio.total_pnl(last_prices)
        total_pnl_pct = portfolio.total_pnl_pct(last_prices)
        equity_value = portfolio.equity_value(last_prices)
    else:
        total_pnl = 0.0
        total_pnl_pct = 0.0
        portfolio_value = 10000.0
        equity_value = 0.0

    # ---- 保存每日记忆和净值记录（Memory Management + Equity Tracking）----
    try:
        from src.data.memory_manager import MemoryManager
        from src.data.equity_tracker import EquityTracker
        
        memory_manager = MemoryManager(root="data/logs")
        equity_tracker = EquityTracker(root="data/logs")
        
        # 使用 end 日期作为今天的日期（如果 end 是 None，使用当前日期）
        today = end if end else date.today().isoformat()
        
        # Portfolio 快照
        portfolio_snapshot = {
            "cash": portfolio.cash if portfolio else 0.0,
            "positions": updated_positions_info,
            "total_value": portfolio_value,
            "equity_value": equity_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions_pnl": portfolio_pnl,
        }
        
        # 保存完整的每日记忆（注意：此時 executed_trades 只包含掛單信息，成交明細會在收盤後補充）
        # 實際成交明細會在 check_pending_orders.py 中補充到每日記憶
        memory_manager.save_daily_memory(
            date=today,
            market_view=market_view,
            market_analysis=market_analysis,
            discussion=convo,
            risk_report=risk_report,
            decision=decision,
            portfolio_snapshot=portfolio_snapshot,
            executed_trades=executed_trades,  # 掛單信息（status: PENDING），成交後會更新
        )
        
        # 记录每日净值（用于前端图表）
        equity_tracker.record_daily_equity(
            date_str=today,
            portfolio_snapshot=portfolio_snapshot,
        )
    except Exception as e:
        print(f"[MEMORY WARN] Failed to save memory/equity: {e}")
        # 不影响主流程，继续执行

    return {
        "stance": final_stance,
        "decision": decision,
        "risk_report": risk_report,
        "discussion": convo,  # 添加完整的讨论信息（包含 transcript, actions 等）
        "rounds": convo.get("rounds"),
        "symbols": symbols,
        "top_signals": signal_top,
        "market_agent": market_view,  # 添加市场数据
        "market_analysis": market_analysis,  # 添加 Market Analyst 结果
        "last_prices": last_prices,  # 添加最新价格（用于计算仓位百分比）
        # 执行结果
        "executed_trades": executed_trades,  # 包含掛單信息（status: PENDING）
        "execution_errors": execution_errors,
        "placed_orders": placed_orders,  # 掛單列表
        # Portfolio 信息（用于后端展示，包含交易后的最新状态）
        "portfolio": {
            "cash": portfolio.cash if portfolio else 0.0,
            "positions": {sym: info["quantity"] for sym, info in updated_positions_info.items()},  # 只返回数量（兼容旧接口）
            "positions_detail": updated_positions_info,  # 详细持仓信息
            "total_value": portfolio_value,
            "equity_value": equity_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions_pnl": portfolio_pnl,
        },
    }
