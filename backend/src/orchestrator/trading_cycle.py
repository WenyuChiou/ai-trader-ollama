# src/orchestrator/trading_cycle.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, timedelta, datetime, timezone, time as dt_time
from pathlib import Path  # 统一在文件顶部导入，避免函数内部重复导入导致的作用域问题

# --- Market: 批次抓價 + 指標 ---
from src.tools.market_tools import fetch_market_batch

# --- Multi-Analyst Discussion: 多个专门的分析师协同工作 ---
from src.agents.multi_analyst_system import run_multi_analyst_discussion

# --- Risk Analyst: 評估倉位風險 (LLM-powered) ---
from src.agents.risk_analyst_llm import run_risk_analyst_llm

# --- Trader Agent: 交易決策 ---
from src.agents.trader_agent import run_trader

# --- Portfolio: 持倉管理 ---
from src.data.portfolio import Portfolio

# --- Trade Logger: 交易記錄 ---
from src.data.trade_log import TradeLogger


def _default_universe() -> List[str]:
    """
    加载完整的股票universe（默认从config.json加载）
    如果config.json中有universe字段，使用它；否则使用最小预设
    """
    try:
        # 尝试从config.json加载完整的universe
        config_file = Path(__file__).parent.parent.parent / "config" / "config.json"
        if config_file.exists():
            import json
            with config_file.open("r", encoding="utf-8") as f:
                config_data = json.load(f)
                # config.json中universe字段
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    symbols = config_data["universe"]
                    if symbols and len(symbols) > 0:
                        print(f"[UNIVERSE] Loaded {len(symbols)} symbols from config.json")
                        return symbols
        
        # 也尝试从universe.json加载（如果存在）
        universe_file = Path(__file__).parent.parent.parent / "config" / "universe.json"
        if universe_file.exists():
            import json
            with universe_file.open("r", encoding="utf-8") as f:
                universe_data = json.load(f)
                # universe.json格式可能是 {"nasdaq100": [...]} 或直接是列表
                if isinstance(universe_data, dict):
                    # 尝试不同的key
                    for key in ["nasdaq100", "symbols", "universe", "stocks"]:
                        if key in universe_data and isinstance(universe_data[key], list):
                            symbols = universe_data[key]
                            if symbols and len(symbols) > 0:
                                print(f"[UNIVERSE] Loaded {len(symbols)} symbols from {universe_file.name}")
                                return symbols
                elif isinstance(universe_data, list):
                    if len(universe_data) > 0:
                        print(f"[UNIVERSE] Loaded {len(universe_data)} symbols from {universe_file.name}")
                        return universe_data
    except Exception as e:
        print(f"[UNIVERSE WARN] Failed to load universe from config: {e}")
    
    # Fallback: 最小预设（仅用于测试）
    print("[UNIVERSE WARN] Using minimal default universe (5 stocks)")
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
    tool_budget: int = 8,
    min_tools: int = 3,
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
    # Only set default window if both start and end are None
    # If end is provided (for testing/planning), preserve it
    if start is None and end is None:
        start, end = _default_window()
    elif start is None:
        # If only end is provided, calculate start (7 days before end)
        from datetime import datetime as dt, timedelta
        end_date = dt.fromisoformat(end) if isinstance(end, str) else end
        start_date = end_date - timedelta(days=7)
        start = start_date.isoformat().split('T')[0] if isinstance(start_date, dt) else str(start_date)
    elif end is None:
        # If only start is provided, use today as end
        end = date.today().isoformat()
    if preferred_domains is None:
        preferred_domains = []

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
    # 传递所有股票的信号分数（按降序排列），不限制数量
    signal_top = _top_by_signal(stocks, k=len(stocks))  # 使用全部股票
    
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

    # ---- (2) 检查当前订单状态（传递给agent）----
    from src.data.order_manager import OrderManager
    order_manager = OrderManager(root="data/logs")
    
    # 检查市场是否开盘（用于确定订单日期，排除周末和节假日）
    from src.utils.trading_days import is_market_open as check_market_open
    now = datetime.now()
    is_market_open = check_market_open(now)
    
    # 确定要检查的订单日期
    if end:
        order_date = end
    elif is_market_open:
        order_date = date.today().isoformat()
    else:
        # 收盘后：检查明天的订单
        tomorrow = date.today() + timedelta(days=1)
        while tomorrow.weekday() >= 5:
            tomorrow += timedelta(days=1)
        order_date = tomorrow.isoformat()
    
    # 获取pending和filled订单
    pending_orders = order_manager.load_pending_orders(order_date=order_date)
    
    # 获取filled订单
    filled_orders = []
    filled_file = Path("data/logs/filled_orders.jsonl")
    if filled_file.exists():
        try:
            with filled_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        order = json.loads(line)
                        if order.get("order_date") == order_date:
                            filled_orders.append(order)
        except Exception:
            pass
    
    # 准备订单状态信息
    order_status = {
        "pending_count": len(pending_orders),
        "filled_count": len(filled_orders),
        "pending_orders": pending_orders,
        "filled_orders": filled_orders,
        "order_date": order_date,
    }
    
    if pending_orders or filled_orders:
        print(f"[TRADING CYCLE] Order status for {order_date}: {len(pending_orders)} pending, {len(filled_orders)} filled")
    
    # ---- (3) 多Analyst討論層 ----
    # 运行多个专门的分析师：Market, Technical, Fundamental, Sentiment
    convo = run_multi_analyst_discussion(
        market_view=market_view,  # 传入完整的market_view
        use_tools=auto_tools,
        tool_budget=tool_budget,
        order_status=order_status,  # 传入订单状态
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
        
        # 寫入每個analyst的分析結果（從discussion_history中提取）
        discussion_history = convo.get("discussion_history", [])
        for entry_data in discussion_history:
            analyst_name = entry_data.get("analyst", "Unknown")
            stance = entry_data.get("stance", "neutral")
            analysis = entry_data.get("analysis", "No analysis provided")
            tools_used = entry_data.get("tools_used", [])
            
            # 標準化agent名稱（處理有空格和無空格的情況）
            agent_name_map = {
                "market": "MarketAnalyst",
                "market analyst": "MarketAnalyst",
                "technical": "TechnicalAnalyst",
                "technical analyst": "TechnicalAnalyst",
                "fundamental": "FundamentalAnalyst",
                "fundamental analyst": "FundamentalAnalyst",
                "sentiment": "SentimentAnalyst",
                "sentiment analyst": "SentimentAnalyst",
            }
            # 先嘗試完整匹配，再嘗試小寫匹配
            agent_name = agent_name_map.get(analyst_name, agent_name_map.get(analyst_name.lower(), analyst_name))
            
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,
                "agent": agent_name,
                "round": 0,
                "content": f"Stance: {stance}\n\nAnalysis: {analysis}",
                "type": "discussion",
                "stance": stance,
                "tools_used": tools_used,
            }
            
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # 寫入Coordinator統整結果
        coordinator_summary = convo.get("coordinator_summary")
        if coordinator_summary:
            if isinstance(coordinator_summary, dict):
                stance = coordinator_summary.get("stance", "neutral")
                summary = coordinator_summary.get("summary", "No summary provided")
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "date": trade_date_str,
                    "agent": "DiscussionCoordinator",
                    "round": 0,
                    "content": f"Stance: {stance}\n\nSummary: {summary}",
                    "type": "discussion",
                    "stance": stance,
                }
                with convo_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # 寫入工具使用記錄（從tool_calls中提取）
        tool_calls = convo.get("tool_calls", [])
        for tool_call in tool_calls:
            analyst_name = tool_call.get("analyst", "Unknown")
            tool_name = tool_call.get("tool", "")
            tool_result = tool_call.get("result", {})
            
            # 標準化agent名稱
            agent_name_map = {
                "market": "MarketAnalyst",
                "technical": "TechnicalAnalyst",
                "fundamental": "FundamentalAnalyst",
                "sentiment": "SentimentAnalyst",
            }
            agent_name = agent_name_map.get(analyst_name.lower(), analyst_name)
            
            # 格式化工具結果
            if isinstance(tool_result, dict):
                if "error" in tool_result:
                    result_text = f"Error: {tool_result.get('error', 'Unknown error')}"
                else:
                    # 提取關鍵信息
                    result_text = json.dumps(tool_result, ensure_ascii=False, indent=2)[:500]
            else:
                result_text = str(tool_result)[:500]
            
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,
                "agent": agent_name,
                "round": 0,
                "content": f"Tool used: {tool_name}: {result_text}",
                "type": "tool",
                "tool_name": tool_name,
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

    # NOTE: Risk Analyst 和 Trader Agent 的调用会移到订单结算之后，确保使用最新的仓位状态

    # ---- (5) 掛單策略：開盤前掛限價單，收盤後檢查成交 ----
    from src.data.order_manager import OrderManager
    
    order_manager = OrderManager(root="data/logs")
    
    # 检查市场是否开盘，决定订单日期（排除周末和节假日）
    from src.utils.trading_days import is_market_open as check_market_open
    now = datetime.now()
    is_market_open = check_market_open(now)
    
    # 如果市场收盘后，订单日期应该是明天的日期
    # 注意：如果end参数被传递（用于测试或规划），优先使用end日期
    existing_pending_orders = []
    if end:
        # end参数优先：用于测试或规划特定日期的交易
        # 在多日模拟中，订单日期应该使用end日期（当天），而不是"明天"
        today = end
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        print(f"[TRADING CYCLE] Using end date: {today} (forced date for testing/planning)")
        # 在多日模拟中，假设市场是开放的，这样订单日期就是当天
        is_market_open_for_simulation = True
    elif is_market_open:
        today = date.today().isoformat()
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        is_market_open_for_simulation = True
    else:
        # 收盘后：订单日期是下一个交易日的日期（规划下一个交易日的交易）
        # 使用交易日检查工具，排除周末和节假日
        from src.utils.trading_days import get_next_trading_day
        next_trading_day = get_next_trading_day(date.today(), days_ahead=1)
        today = next_trading_day.isoformat()
        
        # 检查是否已经有明天的订单计划
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        if existing_pending_orders:
            print(f"[TRADING CYCLE] Market closed. Already have {len(existing_pending_orders)} pending orders for {today}, skipping new order creation.")
        is_market_open_for_simulation = False
    
    executed_trades = []
    execution_errors = []
    placed_orders = []  # 記錄掛單
    
    # 处理pending订单的逻辑：
    # 1. 如果市场开盘且有pending订单：先尝试结算这些订单，然后决定是否创建新订单
    # 2. 如果市场收盘且有pending订单（明天的订单）：不创建新订单，只返回现有订单
    if existing_pending_orders:
        # 在多日模拟中（end参数提供），也执行订单
        # 条件：1) 市场开盘且是今天，或 2) 提供了end参数（多日模拟）
        should_settle_orders = (is_market_open and today == date.today().isoformat()) or (end is not None)
        if should_settle_orders:
            # 市场开盘时，先尝试结算今天的pending订单
            print(f"[TRADING CYCLE] Market is open (or simulation mode). Found {len(existing_pending_orders)} pending orders for {today}. Checking if they can be filled...")
            
            # 加载当前portfolio状态
            try:
                portfolio_file = Path("data/logs/portfolio_state.json")
                if portfolio_file.exists():
                    with portfolio_file.open("r", encoding="utf-8") as f:
                        state = json.load(f)
                    
                    # 创建Portfolio对象
                    default_cash = portfolio.cash if portfolio else 10000.0
                    default_initial = portfolio.initial_value if portfolio else 10000.0
                    current_portfolio = Portfolio(
                        cash=float(state.get("cash", default_cash)),
                        initial_value=float(state.get("initial_value", default_initial)),
                    )
                    
                    # 恢复持仓
                    from src.data.portfolio import Position
                    for symbol, pos_info in state.get("positions", {}).items():
                        if isinstance(pos_info, dict):
                            qty = int(pos_info.get("quantity", 0))
                            avg_cost = float(pos_info.get("avg_cost", 0))
                            total_cost = pos_info.get("total_cost", avg_cost * qty)
                            if qty > 0:
                                current_portfolio._positions[symbol] = Position(
                                    symbol=symbol,
                                    quantity=qty,
                                    avg_cost=avg_cost,
                                    total_cost=total_cost
                                )
                    
                    # 检查pending订单是否可以成交
                    settled_count = 0
                    for order in existing_pending_orders:
                        symbol = order.get("symbol")
                        action = order.get("action", "").upper()
                        quantity = order.get("quantity", 0)
                        limit_price = order.get("limit_price", 0)
                        order_id = order.get("order_id", "unknown")
                        
                        try:
                            # 在多日模拟中（end is not None），使用历史数据检查订单
                            # 在实时交易中（end is None），使用实时价格
                            use_realtime_for_check = (end is None) and (today == date.today().isoformat())
                            # 如果无法获取历史数据，使用当前价格作为 fallback（从 last_prices 或 market_view 获取）
                            fallback_price = last_prices.get(symbol)
                            if fallback_price is None:
                                # 如果 last_prices 中没有，尝试从 market_view 获取
                                stock_data = stocks.get(symbol, {})
                                fallback_price = stock_data.get("price")
                            if fallback_price is None and end is not None:
                                # 在模拟模式下，如果无法获取价格，使用限价作为成交价（假设订单可以成交）
                                fallback_price = limit_price
                                print(f"[TRADING CYCLE] ⚠️ No price data for {symbol}, using limit price ${limit_price:.2f} as fallback in simulation")
                            fill_result = order_manager.check_order_fill(
                                order, 
                                today, 
                                use_realtime=use_realtime_for_check,
                                fallback_price=fallback_price
                            )
                            
                            # 如果订单已成交，执行交易
                            if fill_result.get("filled", False):
                                fill_price = fill_result.get("fill_price")
                                if fill_price:
                                    print(f"[TRADING CYCLE] Executing {action} {quantity} {symbol} @ ${fill_price:.2f}...")
                                    if action == "BUY":
                                        current_portfolio.buy(symbol, quantity, fill_price)
                                    elif action == "SELL":
                                        current_portfolio.sell(symbol, quantity, fill_price)
                                    
                                    # 标记订单为已成交
                                    order_manager.mark_order_filled(order, fill_result)
                                    settled_count += 1
                                    print(f"[TRADING CYCLE] ✅ Order {order_id} executed successfully")
                        except Exception as e:
                            print(f"[TRADING CYCLE] ❌ Error processing order {order_id}: {e}")
                            pass
                    
                    if settled_count > 0:
                        # 保存更新后的portfolio状态
                        # 计算 total_value（现金 + 持仓市值）
                        equity_value = current_portfolio.equity_value(last_prices) if last_prices else 0.0
                        total_value = current_portfolio.cash + equity_value
                        
                        portfolio_state = {
                            "cash": current_portfolio.cash,
                            "initial_value": current_portfolio.initial_value,
                            "total_value": total_value,  # Add total_value for consistency
                            "positions": {},
                            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                        }
                        
                        for symbol, pos in current_portfolio._positions.items():
                            # pos is a Position object
                            portfolio_state["positions"][symbol] = {
                                "quantity": pos.quantity,
                                "avg_cost": pos.avg_cost,
                                "total_cost": pos.total_cost if hasattr(pos, 'total_cost') and pos.total_cost > 0 else pos.avg_cost * pos.quantity,
                            }
                        
                        portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
                        print(f"[TRADING CYCLE] ✅ Settled {settled_count} orders, portfolio updated")
                        
                        # CRITICAL: 更新传入的 portfolio 参数，确保后续计算使用最新状态
                        # 这样在多日模拟中，净值计算会使用更新后的 portfolio
                        if portfolio:
                            portfolio.cash = current_portfolio.cash
                            portfolio.initial_value = current_portfolio.initial_value
                            portfolio._positions = current_portfolio._positions.copy()
                            print(f"[TRADING CYCLE] ✅ Updated portfolio parameter with executed orders (first settlement)")
                        else:
                            # 如果 portfolio 是 None，直接赋值
                            portfolio = current_portfolio
                    
                    # 重新加载pending订单（可能有些已经成交了）
                    existing_pending_orders = order_manager.load_pending_orders(order_date=today)
                    
                    if existing_pending_orders:
                        print(f"[TRADING CYCLE] Still have {len(existing_pending_orders)} pending orders after settlement.")
                        # 在多日模拟中（end is not None），允许继续创建新订单，即使有 pending 订单
                        # 这样可以确保每天都有交易决策和净值变化
                        if end is not None:
                            print(f"[TRADING CYCLE] Multi-day simulation mode: will create new orders even with {len(existing_pending_orders)} pending orders.")
                        else:
                            # 实时模式下，如果有 pending 订单，跳过创建新订单以避免冲突
                            print(f"[TRADING CYCLE] Real-time mode: will skip creating new orders to avoid conflicts.")
                            return {
                                "placed_orders": existing_pending_orders,
                                "executed_trades": [],
                                "execution_errors": [],
                                "conversations_count": len(convo.get("entries", [])),
                                "is_planning": False,
                                "order_date": today,
                                "message": f"Still have {len(existing_pending_orders)} pending orders for {today} after settlement. No new orders created to avoid conflicts."
                            }
                    else:
                        print(f"[TRADING CYCLE] All pending orders settled. Proceeding to create new orders if needed.")
            except Exception as e:
                print(f"[TRADING CYCLE] Warning: Failed to check pending orders: {e}")
                import traceback
                traceback.print_exc()
                # 如果检查失败，为了安全起见，不创建新订单
                return {
                    "placed_orders": existing_pending_orders,
                    "executed_trades": [],
                    "execution_errors": [f"Failed to check pending orders: {e}"],
                    "conversations_count": len(convo.get("entries", [])),
                    "is_planning": False,
                    "order_date": today,
                    "message": f"Error checking pending orders. No new orders created for safety."
                }
        else:
            # 市场收盘后，如果有pending订单（明天的订单），不创建新订单
            # 但仍然返回完整的结果，包括讨论和分析
            print(f"[TRADING CYCLE] Skipping order creation - {len(existing_pending_orders)} pending orders already exist for {today}")
            # 将现有pending订单设置为placed_orders，这样验证函数可以检查
            placed_orders = existing_pending_orders
            # 继续执行，返回完整结果（包括讨论、分析等）
            # 不要提前返回，让代码继续执行到最后的return语句
    
    # ---- (3) Risk Analyst：評估倉位風險 ----
    # CRITICAL: 在订单结算之后准备仓位信息，确保 Risk Analyst 使用最新的仓位状态
    # 这样在多日模拟中，Risk Analyst 能够正确分析前一天的仓位状态（包括当天已结算的订单）
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
    
    # 调用 Risk Analyst (LLM版本)
    # 传递discussion内容让Risk Analyst理解讨论中的风险信号
    previous_discussion_text = "\n".join(convo.get("transcript", []))[:1000]  # 限制长度
    
    risk_report = run_risk_analyst_llm(
        market_json=market_view,
        current_positions=current_positions_info if current_positions_info else None,
        portfolio_value=portfolio_value,
        discussion_risk_signals=discussion_risk_signals,
        previous_discussion=previous_discussion_text,
        use_tools=auto_tools,  # 与discussion使用相同的tool设置
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
            with open(config_path, 'r', encoding="utf-8") as f:
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
    
    # Debug: Log decision content
    buy_orders_count = len(decision.get("buy_orders", []))
    sell_orders_count = len(decision.get("sell_orders", []))
    print(f"[TRADING CYCLE] Trader decision: {buy_orders_count} buy orders, {sell_orders_count} sell orders")
    if buy_orders_count == 0 and sell_orders_count == 0:
        print(f"[TRADING CYCLE] ⚠️  Warning: No trading decisions generated. Decision keys: {list(decision.keys())}")
        if "rationale" in decision:
            rationale = str(decision.get('rationale', ''))[:300]
            print(f"[TRADING CYCLE] Decision rationale: {rationale}")
        # Debug: Check why no orders were generated
        recs_count = len(enriched_market.get("recommended_stocks", []))
        stocks_count = len(enriched_market.get("stocks", {}))
        print(f"[TRADING CYCLE] Debug: enriched_market has {recs_count} recommended_stocks, {stocks_count} stocks")
        if stocks_count > 0:
            # Check signal scores (lowered threshold to 0.5 to match trader_agent changes)
            stocks = enriched_market.get("stocks", {})
            high_signal_stocks = [s for s, d in stocks.items() if isinstance(d, dict) and float(d.get("signal_score", 0)) > 0.5]
            print(f"[TRADING CYCLE] Debug: {len(high_signal_stocks)} stocks with signal_score > 0.5: {high_signal_stocks[:5]}")
            # Also check top 10 by signal_score
            sorted_stocks = sorted(
                [(s, d) for s, d in stocks.items() if isinstance(d, dict)],
                key=lambda x: float(x[1].get("signal_score", 0)),
                reverse=True
            )
            top_10 = sorted_stocks[:10]
            print(f"[TRADING CYCLE] Debug: Top 10 stocks by signal_score: {[(s, d.get('signal_score', 0)) for s, d in top_10]}")
    
    # Process trading decisions (only if no existing pending orders, or in multi-day simulation)
    if not existing_pending_orders or (end is not None):
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
                    # Debug: Log the order_date being used
                    print(f"[DEBUG] Creating order for {symbol} with order_date={today}")
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
                    market_status = "tomorrow" if not is_market_open and today != date.today().isoformat() else "today"
                    print(f"[ORDER PLACED] BUY {symbol} x{quantity} @ limit ${limit_price:.2f} (order_date: {today}, will check fill after market close)")
                    
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
    
    # ---- (5b) 檢查並結算今天的 PENDING 訂單（如果市場開盤，或在多日模擬中）----
    # 在多日模拟中（end参数提供），也执行订单
    # 条件：1) 市场开盘且是今天，或 2) 提供了end参数（多日模拟）
    should_settle_orders = (is_market_open and today == date.today().isoformat()) or (end is not None)
    if should_settle_orders:
        try:
            # Path 已经在文件顶部导入，不需要重新导入
            import json
            
            # 加载当前 portfolio 状态
            portfolio_file = Path("data/logs/portfolio_state.json")
            if portfolio_file.exists():
                with portfolio_file.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                
                # 创建 Portfolio 对象（使用已导入的 Portfolio 类）
                # 如果函数参数 portfolio 存在，使用它的值；否则使用默认值
                default_cash = portfolio.cash if portfolio else 10000.0
                default_initial = portfolio.initial_value if portfolio else 10000.0
                current_portfolio = Portfolio(
                    cash=float(state.get("cash", default_cash)),
                    initial_value=float(state.get("initial_value", default_initial)),
                )
                
                # 恢复持仓
                from src.data.portfolio import Position
                for symbol, pos_info in state.get("positions", {}).items():
                    if isinstance(pos_info, dict):
                        qty = int(pos_info.get("quantity", 0))
                        avg_cost = float(pos_info.get("avg_cost", 0))
                        total_cost = pos_info.get("total_cost", avg_cost * qty)
                        if qty > 0:
                            current_portfolio._positions[symbol] = Position(
                                symbol=symbol,
                                quantity=qty,
                                avg_cost=avg_cost,
                                total_cost=total_cost
                            )
                
                # 检查今天的 pending 订单
                today_pending = order_manager.load_pending_orders(order_date=today)
                if today_pending:
                    print(f"\n[TRADING CYCLE] Checking {len(today_pending)} pending orders for today ({today})...")
                    settled_count = 0
                    for order in today_pending:
                        symbol = order.get("symbol")
                        action = order.get("action", "").upper()
                        quantity = order.get("quantity", 0)
                        limit_price = order.get("limit_price", 0)
                        order_id = order.get("order_id", "unknown")
                        
                        try:
                            # 在多日模拟中（end is not None），使用历史数据检查订单
                            # 在实时交易中（end is None），使用实时价格
                            use_realtime_for_check = (end is None) and (today == date.today().isoformat())
                            # 如果无法获取历史数据，使用当前价格作为 fallback（从 last_prices 或 market_view 获取）
                            fallback_price = last_prices.get(symbol)
                            if fallback_price is None:
                                # 如果 last_prices 中没有，尝试从 market_view 获取
                                stock_data = stocks.get(symbol, {})
                                fallback_price = stock_data.get("price")
                            if fallback_price is None and end is not None:
                                # 在模拟模式下，如果无法获取价格，使用限价作为成交价（假设订单可以成交）
                                fallback_price = limit_price
                                print(f"[TRADING CYCLE] ⚠️ No price data for {symbol}, using limit price ${limit_price:.2f} as fallback in simulation")
                            fill_result = order_manager.check_order_fill(
                                order, 
                                today, 
                                use_realtime=use_realtime_for_check,
                                fallback_price=fallback_price
                            )
                            
                            # 如果订单已成交，执行交易
                            if fill_result.get("filled", False):
                                fill_price = fill_result.get("fill_price")
                                if fill_price:
                                    print(f"[TRADING CYCLE] Executing {action} {quantity} {symbol} @ ${fill_price:.2f}...")
                                    if action == "BUY":
                                        current_portfolio.buy(symbol, quantity, fill_price)
                                    elif action == "SELL":
                                        current_portfolio.sell(symbol, quantity, fill_price)
                                    
                                    # 标记订单为已成交
                                    order_manager.mark_order_filled(order, fill_result)
                                    settled_count += 1
                                    print(f"[TRADING CYCLE] ✅ Order {order_id} executed successfully")
                        except Exception as e:
                            print(f"[TRADING CYCLE] ❌ Error processing order {order_id}: {e}")
                            pass
                    
                    if settled_count > 0:
                        # 保存更新后的 portfolio 状态
                        # 计算 total_value（现金 + 持仓市值）
                        equity_value = current_portfolio.equity_value(last_prices) if last_prices else 0.0
                        total_value = current_portfolio.cash + equity_value
                        
                        portfolio_state = {
                            "cash": current_portfolio.cash,
                            "initial_value": current_portfolio.initial_value,
                            "total_value": total_value,  # Add total_value for consistency
                            "positions": {},
                            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                        }
                        
                        for symbol, pos in current_portfolio._positions.items():
                            # pos is a Position object
                            portfolio_state["positions"][symbol] = {
                                "quantity": pos.quantity,
                                "avg_cost": pos.avg_cost,
                                "total_cost": pos.total_cost if hasattr(pos, 'total_cost') and pos.total_cost > 0 else pos.avg_cost * pos.quantity,
                            }
                        
                        portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
                        print(f"[TRADING CYCLE] ✅ Settled {settled_count} orders, portfolio updated")
                        
                        # CRITICAL: 更新传入的 portfolio 参数，确保后续计算使用最新状态
                        # 这样在多日模拟中，Day 2+ 能正确加载更新后的持仓
                        if portfolio:
                            portfolio.cash = current_portfolio.cash
                            portfolio.initial_value = current_portfolio.initial_value
                            portfolio._positions = current_portfolio._positions.copy()
                            print(f"[TRADING CYCLE] ✅ Updated portfolio parameter with executed orders")
        except Exception as e:
            print(f"[TRADING CYCLE] Warning: Failed to check pending orders: {e}")
            import traceback
            traceback.print_exc()
    
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
        # 在多日模拟中，end 就是当天的日期，应该使用 end 来记录净值
        # 这样可以确保每天使用不同的日期记录净值
        equity_date = end if end else date.today().isoformat()
        
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
            date=equity_date,
            market_view=market_view,
            market_analysis=market_analysis,
            discussion=convo,
            risk_report=risk_report,
            decision=decision,
            portfolio_snapshot=portfolio_snapshot,
            executed_trades=executed_trades,  # 掛單信息（status: PENDING），成交後會更新
        )
        
        # 记录每日净值（用于前端图表）
        # CRITICAL: 使用更新后的 portfolio 状态记录净值
        equity_tracker.record_daily_equity(
            date_str=equity_date,
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
