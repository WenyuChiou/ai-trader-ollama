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

    # ---- (1d) Sentiment Analyst：VIX/Fear&Greed 等情緒指標 ----
    try:
        from src.tools.sentiment_tools import fetch_fear_greed, vix_term_structure, vix_risk_score
        fgi = fetch_fear_greed()
        vix_term = vix_term_structure()
        sentiment_summary = {
            "fgi": fgi,
            "vix_term": vix_term,
            "vix_risk_score": vix_risk_score(vix_term)
        }
    except Exception:
        sentiment_summary = {"fgi": {}, "vix_term": {}, "vix_risk_score": 5.0}

    # ---- (1e) Economic Data (Jin10) ----
    econ_summary = {}
    try:
        from src.tools.jin10_tools import fetch_jin10_economic_data
        econ = fetch_jin10_economic_data(max_items=10)
        econ_summary = {"items": econ[:5]} if isinstance(econ, list) else (econ or {})
    except Exception:
        econ_summary = {}

    enriched_market: Dict[str, Any] = {
        "symbols": symbols,
        # 交給 discussion 自動補：vix_term / fear_greed / news
        "vix_term": sentiment_summary.get("vix_term") or market_view.get("vix_term"),
        "fear_greed": sentiment_summary.get("fgi") or market_view.get("fear_greed"),
        "news": None,
        "signal_score_top": signal_top,
        "stocks": stocks,
        "vix": market_view.get("vix"),
        "recommended_stocks": recommended_stocks,  # 添加 Market Analyst 的推薦股票列表
        "market_sentiment": market_analysis.get("market_sentiment", "neutral"),  # 添加市場情緒
        "sentiment_summary": sentiment_summary,
        "economic_data": econ_summary,
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

        # 額外：將情緒工具（FGI / VIX term）也以 ToolSystem 形式各寫一條，方便前端顯示
        try:
            if sentiment_summary:
                fgi = sentiment_summary.get("fgi") or {}
                if fgi:
                    fgi_value = fgi.get("value")
                    fgi_label = fgi.get("label")
                    fgi_asof = fgi.get("asof")
                    fgi_text = (
                        f"fear_greed: value={fgi_value}, label={fgi_label}, asof={fgi_asof}"
                        if (fgi_value is not None or fgi_label)
                        else "fear_greed: unavailable"
                    )
                    with convo_file.open("a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                            "date": trade_date_str,
                            "agent": "ToolSystem",
                            "round": 0,
                            "content": f"Tool used: {fgi_text}",
                            "type": "tool",
                        }, ensure_ascii=False) + "\n")

                vt = sentiment_summary.get("vix_term") or {}
                if vt:
                    vt_v = vt.get("vix")
                    vt_v3 = vt.get("vix3m")
                    vt_ratio = vt.get("ratio")
                    vt_text = (
                        f"vix_term: VIX={vt_v}, VIX3M={vt_v3}, ratio={vt_ratio} (contango if >1)"
                    )
                    with convo_file.open("a", encoding="utf-8") as f:
                        f.write(json.dumps({
                            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                            "date": trade_date_str,
                            "agent": "ToolSystem",
                            "round": 0,
                            "content": f"Tool used: {vt_text}",
                            "type": "tool",
                        }, ensure_ascii=False) + "\n")
            # Economic data as ToolSystem
            if econ_summary:
                econ_text = "jin10_economic: " + (json.dumps(econ_summary.get("items", econ_summary), ensure_ascii=False)[:180])
                with convo_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps({
                        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                        "date": trade_date_str,
                        "agent": "ToolSystem",
                        "round": 0,
                        "content": f"Tool used: {econ_text}",
                        "type": "tool",
                    }, ensure_ascii=False) + "\n")
        except Exception as _e:
            print(f"[WARN] Failed to append sentiment tools as ToolSystem: {_e}")

        # 追加各 Agent 的關鍵輸出，讓前端能看到所有 Agent（不只 DiscussionAgent）
        try:
            # SentimentAnalyst 摘要
            sa_summary = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,
                "agent": "SentimentAnalyst",
                "round": 0,
                "type": "summary",
                "content": json.dumps({
                    "fgi": sentiment_summary.get("fgi"),
                    "vix_term": sentiment_summary.get("vix_term"),
                    "vix_risk_score": sentiment_summary.get("vix_risk_score")
                }, ensure_ascii=False)
            }
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(sa_summary, ensure_ascii=False) + "\n")

            # TechnicalAnalyst 摘要（從技術指標與 top signals 組裝）
            tech_payload = {
                "top_signals": signal_top,
                "indicators": {sym: {
                    "rsi14": (stocks.get(sym, {}) or {}).get("rsi14"),
                    "macd": (stocks.get(sym, {}) or {}).get("macd"),
                    "bb_pos": (stocks.get(sym, {}) or {}).get("bb_pos"),
                } for sym, _ in signal_top[:5]}
            }
            ta_tech = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,
                "agent": "TechnicalAnalyst",
                "round": 0,
                "type": "summary",
                "content": json.dumps(tech_payload, ensure_ascii=False)
            }
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(ta_tech, ensure_ascii=False) + "\n")

            # FundamentalAnalyst 摘要（以推薦清單與市場情緒為主）
            fa_payload = {
                "market_sentiment": market_analysis.get("market_sentiment"),
                "recommended_stocks": recommended_stocks[:10],
                "key_observations": (market_analysis.get("key_observations") or [])[:10],
            }
            fa_summary = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,
                "agent": "FundamentalAnalyst",
                "round": 0,
                "type": "summary",
                "content": json.dumps(fa_payload, ensure_ascii=False)
            }
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(fa_summary, ensure_ascii=False) + "\n")

            # MarketAnalyst 摘要
            ma_summary = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,
                "agent": "MarketAnalyst",
                "round": 0,
                "type": "summary",
                "content": json.dumps({
                    "market_sentiment": market_analysis.get("market_sentiment"),
                    "recommended_stocks": market_analysis.get("recommended_stocks", [])[:10]
                }, ensure_ascii=False)
            }
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(ma_summary, ensure_ascii=False) + "\n")

            # RiskAnalyst / TraderAgent 摘要放在稍後（風險分析與決策完成之後）
        except Exception as _e:
            print(f"[WARN] Failed to append agent summaries: {_e}")
        
    except Exception as e:
        print(f"[WARN] Failed to write conversations to discussion_actions.jsonl: {e}")
    
    # 提取 Discussion 的风险信号（用于 Risk Analyst）
    discussion_risk_signals = {
        "risk_level": "medium",
        "risk_signals": convo.get("risk_signals", []),
    }

    # ---- (3) Risk Analyst：評估倉位風險 ----
    # 准备当前持仓信息（用于 Risk Analyst，包含完整信息用于P&L分析）
    current_positions_info = {}
    if portfolio:
        portfolio_value = portfolio.value(last_prices)
        for symbol, pos in portfolio._positions.items():
            current_price = last_prices.get(symbol, pos.avg_cost)
            market_value = pos.quantity * current_price
            total_cost = getattr(pos, 'total_cost', pos.avg_cost * pos.quantity)
            
            current_positions_info[symbol] = {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "total_cost": total_cost,  # 添加total_cost用于P&L计算
                "current_price": current_price,
                "market_value": market_value,
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

    # ---- 在風險分析與決策完成後，補寫 RiskAnalyst / TraderAgent 摘要 ----
    try:
        logs_dir = Path("data/logs") if 'logs_dir' not in locals() else logs_dir
        logs_dir.mkdir(parents=True, exist_ok=True)
        convo_file = logs_dir / "discussion_actions.jsonl"

        # Normalize risk level field from risk_report
        _risk_level = (
            risk_report.get("overall_risk_level")
            or risk_report.get("overall_risk")
            or risk_report.get("risk_level")
        )
        ra_summary = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "date": (end if end else date.today().isoformat()),
            "agent": "RiskAnalyst",
            "round": 0,
            "type": "summary",
            "content": json.dumps({
                "overall_risk": _risk_level,
                "warnings": (risk_report.get("warnings") or [])[:5]
            }, ensure_ascii=False)
        }
        with convo_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ra_summary, ensure_ascii=False) + "\n")

        ta_summary = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "date": (end if end else date.today().isoformat()),
            "agent": "TraderAgent",
            "round": 0,
            "type": "summary",
            "content": json.dumps({
                "action": decision.get("action"),
                "buy_count": len(decision.get("buy_orders", [])),
                "sell_count": len(decision.get("sell_orders", []))
            }, ensure_ascii=False)
        }
        with convo_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(ta_summary, ensure_ascii=False) + "\n")
    except Exception as _e:
        print(f"[WARN] Failed to append post-decision summaries: {_e}")

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
        
        # 檢查市場是否開盤
        is_market_open_now = order_manager._is_market_open()
        
        # 如果市場開盤，先檢查並處理當天的 pending 限價單
        if is_market_open_now:
            print(f"[PENDING CHECK] Market is open. Checking pending orders for today ({today})...")
            pending_orders = order_manager.load_pending_orders(order_date=today)
            filled_count = 0
            
            for pending_order in pending_orders:
                symbol = pending_order.get("symbol")
                action = pending_order.get("action", "").upper()
                limit_price = pending_order.get("limit_price")
                quantity = pending_order.get("quantity", 0)
                
                if not symbol or not limit_price or quantity <= 0:
                    continue
                
                # 獲取當前價格
                current_price = last_prices.get(symbol)
                if not current_price or current_price <= 0:
                    # 如果沒有價格，跳過
                    continue
                
                # 檢查是否應該成交
                should_fill = False
                if action == "BUY":
                    # 買單：當前價 <= 限價時成交
                    if current_price <= limit_price:
                        should_fill = True
                elif action == "SELL":
                    # 賣單：當前價 >= 限價時成交
                    if current_price >= limit_price:
                        should_fill = True
                
                if should_fill:
                    try:
                        # 執行成交
                        fill_price = current_price  # 使用當前價成交
                        
                        if action == "BUY":
                            # 檢查現金是否足夠
                            cost = fill_price * quantity
                            if cost > portfolio.cash:
                                print(f"[PENDING FILL] BUY {symbol} skipped: insufficient cash (need ${cost:.2f}, have ${portfolio.cash:.2f})")
                                continue
                            
                            portfolio.buy(symbol, quantity, fill_price)
                            print(f"[PENDING FILL] BUY {symbol} x{quantity} @ ${fill_price:.2f} (limit ${limit_price:.2f}, current ${current_price:.2f})")
                            
                        elif action == "SELL":
                            # 檢查持倉是否足夠
                            pos = portfolio.get_position(symbol)
                            if not pos or pos.quantity < quantity:
                                print(f"[PENDING FILL] SELL {symbol} skipped: insufficient position (need {quantity}, have {pos.quantity if pos else 0})")
                                continue
                            
                            portfolio.sell(symbol, quantity, fill_price)
                            print(f"[PENDING FILL] SELL {symbol} x{quantity} @ ${fill_price:.2f} (limit ${limit_price:.2f}, current ${current_price:.2f})")
                        
                        # 標記為已成交
                        order_manager.mark_order_filled(pending_order, {
                            "filled": True,
                            "fill_price": fill_price,
                            "fill_reason": f"Limit order filled at market price ${fill_price:.2f}",
                            "daily_high": current_price,
                            "daily_low": current_price,
                        })
                        
                        # 記錄交易
                        trade_logger.log(
                            symbol=symbol,
                            action=action,
                            price=fill_price,
                            quantity=quantity,
                            amount=fill_price * quantity,
                            status="FILLED",
                            reason=f"Pending limit order filled",
                            rationale="Pending order execution",
                        )
                        
                        executed_trades.append({
                            "symbol": symbol,
                            "action": action,
                            "quantity": quantity,
                            "price": fill_price,
                            "amount": fill_price * quantity,
                            "status": "FILLED",
                            "date": today,
                        })
                        
                        filled_count += 1
                        
                    except Exception as fill_err:
                        execution_errors.append(f"Pending order fill failed for {action} {symbol}: {fill_err}")
                        print(f"[PENDING FILL ERROR] {action} {symbol}: {fill_err}")
            
            if filled_count > 0:
                print(f"[PENDING CHECK] Filled {filled_count} pending orders")
            else:
                print(f"[PENDING CHECK] No pending orders to fill (checked {len(pending_orders)} orders)")
        
        # 交易策略：市場開盤時直接市價執行，不開盤時創建限價單
        for order in buy_orders_sorted:
            symbol = order.get("symbol")
            buy_price = order.get("buy_price")  # 基准价格（用于计算）
            buy_price_min = order.get("buy_price_min", buy_price)  # 价格范围下限（低买）
            buy_price_max = order.get("buy_price_max", buy_price)  # 价格范围上限
            quantity = order.get("quantity")
            total_cost = order.get("total_cost")
            
            if symbol and buy_price and quantity:
                try:
                    # 使用當前基準價計算成本
                    estimated_cost = buy_price * quantity
                    
                    # Check 3: Cash reserve (use available_for_trading instead of full cash)
                    if estimated_cost > available_for_trading:
                        # 現金不足（考慮保留比例），減少數量
                        max_affordable_qty = floor(available_for_trading / buy_price)
                        if max_affordable_qty > 0:
                            quantity = max_affordable_qty
                            total_cost = buy_price * quantity
                            print(f"[OPTIMIZATION] Reduced {symbol} quantity to {quantity} due to cash reserve limit")
                        else:
                            execution_errors.append(f"BUY {symbol} skipped: insufficient cash after reserve (need ${estimated_cost:.2f}, available ${available_for_trading:.2f})")
                            continue
                    
                    if is_market_open_now:
                        # 市場開盤：直接市價執行
                        try:
                            # 獲取當前價格
                            current_price = last_prices.get(symbol, buy_price)
                            if current_price <= 0:
                                current_price = buy_price
                            
                            # 直接執行買入
                            portfolio.buy(symbol, quantity, current_price)
                            
                            # 記錄交易
                            trade_logger.log(
                                symbol=symbol,
                                action="BUY",
                                price=current_price,
                                quantity=quantity,
                                amount=current_price * quantity,
                                status="FILLED",
                                reason="Market order executed immediately",
                                rationale=decision.get("rationale"),
                            )
                            
                            # 創建已成交訂單記錄（用於前端顯示）
                            filled_order = {
                                "order_id": f"{symbol}_BUY_{today}_{datetime.now().timestamp()}",
                                "symbol": symbol,
                                "action": "BUY",
                                "quantity": quantity,
                                "limit_price": current_price,
                                "fill_price": current_price,
                                "order_date": today,
                                "filled_at": datetime.now().isoformat(),
                                "status": "FILLED",
                                "fill_reason": "Market order executed",
                            }
                            order_manager.mark_order_filled(filled_order, {
                                "filled": True,
                                "fill_price": current_price,
                                "fill_reason": "Market order executed",
                                "daily_high": current_price,
                                "daily_low": current_price,
                            })
                            
                            executed_trades.append({
                                "symbol": symbol,
                                "action": "BUY",
                                "quantity": quantity,
                                "price": current_price,
                                "amount": current_price * quantity,
                                "status": "FILLED",
                                "date": today,
                            })
                            
                            print(f"[MARKET ORDER EXECUTED] BUY {symbol} x{quantity} @ ${current_price:.2f} (market price)")
                            
                        except Exception as exec_err:
                            execution_errors.append(f"BUY {symbol} market execution failed: {exec_err}")
                    else:
                        # 市場未開盤：創建限價單
                        limit_price = round(buy_price * 0.998, 2)
                        placed_order = order_manager.place_order(
                            symbol=symbol,
                            action="BUY",
                            quantity=quantity,
                            limit_price=limit_price,
                            price_range={
                                "min": buy_price_min,
                                "max": buy_price_max,
                            },
                            order_date=today,
                        )
                        placed_orders.append(placed_order)
                        print(f"[ORDER PLACED] BUY {symbol} x{quantity} @ limit ${limit_price:.2f} (market closed, will execute when market opens)")
                    
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
                    
                    # 使用當前基準價的 +0.2% 作為賣出限價，提高盤中成交率
                    limit_price = round(sell_price * 1.002, 2)
                    
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
        from src.data.daily_portfolio_logger import DailyPortfolioLogger
        from src.data.order_manager import OrderManager
        
        memory_manager = MemoryManager(root="data/logs")
        equity_tracker = EquityTracker(root="data/logs")
        portfolio_logger = DailyPortfolioLogger(root="data/logs")
        
        # 使用 end 日期作为今天的日期（如果 end 是 None，使用当前日期）
        today = end if end else date.today().isoformat()
        
        # Portfolio 快照
        portfolio_snapshot = {
            "cash": portfolio.cash if portfolio else 0.0,
            "initial_value": portfolio.initial_value if portfolio else 10000.0,
            "positions": updated_positions_info,
            "positions_detail": updated_positions_info,  # 确保有positions_detail字段
            "total_value": portfolio_value,
            "equity_value": equity_value,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "positions_pnl": portfolio_pnl,
        }
        
        # 获取当日交易记录（buy/sell/filled/pending）
        trades_today = {
            "buy": [],
            "sell": [],
            "filled": [],
            "pending": [],
        }
        try:
            order_manager = OrderManager(root="data/logs")
            # 获取所有订单
            all_orders = order_manager.get_all_orders()
            for order in all_orders:
                order_date = order.get("order_date", "")
                if order_date == today or order_date == today.isoformat() if isinstance(today, date) else today:
                    action = order.get("action", "").upper()
                    status = order.get("status", "").upper()
                    
                    if action == "BUY":
                        trades_today["buy"].append(order)
                    elif action == "SELL":
                        trades_today["sell"].append(order)
                    
                    if status == "FILLED":
                        trades_today["filled"].append(order)
                    elif status == "PENDING":
                        trades_today["pending"].append(order)
        except Exception as e:
            print(f"[PORTFOLIO LOG WARN] Failed to load trades for today: {e}")
        
        # 保存每日组合数据（JSON格式，用于RiskAnalyst输入）
        portfolio_logger.record_daily_portfolio(
            date_str=today,
            portfolio_snapshot=portfolio_snapshot,
            trades_today=trades_today,
        )
        
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

        # 额外：写入最新组合状态（方便测试与前端直接读取）
        try:
            portfolio_state_fp = logs_dir / "portfolio_state.json"
            import json as _json
            with portfolio_state_fp.open("w", encoding="utf-8") as f:
                f.write(_json.dumps({
                    "date": today,
                    "snapshot": portfolio_snapshot,
                }, ensure_ascii=False))
        except Exception as _e:
            print(f"[MEMORY WARN] Failed to write portfolio_state.json: {_e}")

        # 额外：写入一条簡單的實時快照（若真正的實時模組未產生時，提供占位）
        try:
            rt_snapshots_fp = logs_dir / "real_time_snapshots.jsonl"
            import json as _json
            with rt_snapshots_fp.open("a", encoding="utf-8") as f:
                f.write(_json.dumps({
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "date": today,
                    "portfolio": portfolio_snapshot,
                }, ensure_ascii=False) + "\n")
        except Exception as _e:
            print(f"[MEMORY WARN] Failed to append real_time_snapshots.jsonl: {_e}")
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
