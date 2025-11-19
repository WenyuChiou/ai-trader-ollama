# src/orchestrator/trading_cycle.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, timedelta, datetime, timezone, time as dt_time
from pathlib import Path  # 统一在文件顶部导入，避免函数内部重复导入导致的作用域问题
import json  # 用于加载 portfolio_state.json

# CRITICAL: Helper function to get project root data/logs directory
# This ensures all trading cycle operations use the same path regardless of working directory
def _get_project_logs_dir() -> Path:
    """Get the project root data/logs directory path."""
    _backend_dir = Path(__file__).resolve().parent.parent.parent  # backend/
    _project_root = _backend_dir.parent  # project root
    logs_dir = _project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

# --- Market: 批次抓價 + 指標 ---
from src.tools.market_tools import fetch_market_batch

# --- Analyst Discussion: 使用优化的并行版本（默认） ---
# Note: multi_analyst_system_parallel internally uses functions from multi_analyst_system,
# so we don't import run_multi_analyst_discussion directly here
from src.agents.multi_analyst_system_parallel import run_multi_analyst_discussion_parallel

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


def _get_order_date(order: Dict[str, Any]) -> Optional[str]:
    """
    从订单中提取日期（优先从placed_at提取，兼容旧的order_date字段）
    
    返回:
    - 订单日期 (YYYY-MM-DD) 或 None
    """
    placed_at = order.get("placed_at", "")
    if placed_at:
        try:
            return datetime.fromisoformat(placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
        except:
            pass
    # 兼容旧的order_date字段
    return order.get("order_date")


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
        end_date = datetime.fromisoformat(end) if isinstance(end, str) else end
        start_date = end_date - timedelta(days=7)
        start = start_date.isoformat().split('T')[0] if isinstance(start_date, datetime) else str(start_date)
    elif end is None:
        # If only start is provided, use today as end
        end = date.today().isoformat()
    if preferred_domains is None:
        preferred_domains = []

    # ---- (1) 市場層 ----
    # fetch_market_batch 是 LangChain StructuredTool，需要使用 .invoke() 调用
    # 注意：fetch_market_batch 只接受 symbols, start, end 三个参数
    # CRITICAL: 确保 end 参数正确设置（用于获取市场数据）
    # 如果 end 是 None（实时模式），使用昨天的日期（因为今天的数据可能还不完整）
    # 如果 end 是特定日期（规划模式），使用该日期
    market_data_end = end if end else (date.today() - timedelta(days=1)).isoformat()
    
    # CRITICAL FIX: 如果 start == end（单天查询），自动扩展 start 到 7 天前
    # 这样可以确保 yfinance 能正确获取数据（单天查询经常失败）
    if start == market_data_end:
        end_dt = datetime.fromisoformat(market_data_end.split('T')[0]) if isinstance(market_data_end, str) else market_data_end
        start_dt = end_dt - timedelta(days=7)
        start = start_dt.isoformat().split('T')[0] if isinstance(start_dt, datetime) else str(start_dt)
        print(f"[TRADING CYCLE] Single-day query detected, extended start to 7 days before: {start} -> {market_data_end}")
    
    print(f"[TRADING CYCLE] Fetching market data: start={start}, end={market_data_end}")
    print(f"[TRADING CYCLE] Universe size: {len(universe)} symbols (processing ALL symbols)")
    if len(universe) <= 20:
        print(f"[TRADING CYCLE] Universe symbols: {universe}")
    else:
        print(f"[TRADING CYCLE] Universe symbols (first 10): {universe[:10]} ... (and {len(universe) - 10} more)")
    
    try:
        market_view: Dict[str, Any] = fetch_market_batch.invoke({
            "symbols": universe,
            "start": start,
            "end": market_data_end,
        })
        stocks_count = len(market_view.get('stocks', {}))
        print(f"[TRADING CYCLE] Market data fetched successfully: {stocks_count} stocks")
        if stocks_count < len(universe):
            print(f"[TRADING CYCLE] ⚠️  WARNING: Fetched {stocks_count} stocks but universe has {len(universe)} symbols")
            # 显示哪些股票没有被获取
            fetched_symbols = set(market_view.get('stocks', {}).keys())
            missing_symbols = [s for s in universe if s not in fetched_symbols]
            if missing_symbols:
                print(f"[TRADING CYCLE] ⚠️  Missing symbols (first 10): {missing_symbols[:10]}")
    except Exception as e:
        print(f"[TRADING CYCLE] Failed to fetch market data: {e}")
        # 如果获取失败，返回错误信息
        raise Exception(f"Failed to fetch market data: {e}")
    # market_view 典型：
    # {
    #   "stocks": {SYM: {price, change_pct, rsi14, macd, bb_pos, signal_score, ...}, ...},
    #   "vix": {"level": ..., "chg_1d": ..., "zscore": ...}
    # }

    # ---- (1b) 輕量 enriched 給討論層 ----
    stocks = market_view.get("stocks") or {}
    symbols = list(stocks.keys())
    print(f"[TRADING CYCLE] Stocks available for analysis: {len(symbols)} symbols (ALL symbols will be analyzed)")
    if len(symbols) <= 20:
        print(f"[TRADING CYCLE] Stock symbols: {symbols}")
    else:
        print(f"[TRADING CYCLE] Stock symbols (first 10): {symbols[:10]} ... (and {len(symbols) - 10} more)")
    # CRITICAL FIX: 移除 signal_score 自动排序
    # signal_score 现在由 agent 自行判断，不再自动计算和排序
    # 仍然保留 signal_score 字段（在 market_tools.py 中计算），但不再用于自动筛选
    signal_top = []  # 不再使用 signal_score 排序
    print(f"[TRADING CYCLE] {len(stocks)} stocks available (signal_score judgment by agents, not auto-sorted)")
    
    # ---- (1c) Market Analyst：評估所有 universe 股票，生成推薦列表 ----
    # CRITICAL FIX: 使用 fallback 推荐（实际推荐会在 multi_analyst_system 中由 LLM 生成）
    from src.tools.market_analyst import run_market_analyst
    market_analysis = run_market_analyst(market_view)
    recommended_stocks_fallback = market_analysis.get("recommended_stocks", [])

    enriched_market: Dict[str, Any] = {
        "symbols": symbols,
        # 交給 discussion 自動補：vix_term / fear_greed / news
        "vix_term": market_view.get("vix_term"),      # 如果你稍後在 market 層就算好也可帶入
        "fear_greed": market_view.get("fear_greed"),
        "news": None,
        # CRITICAL FIX: signal_score_top 已移除，signal_score 由 agent 自行判断
        # "signal_score_top": signal_top,  # 不再使用
        "stocks": stocks,
        "vix": market_view.get("vix"),
        "recommended_stocks": recommended_stocks_fallback,  # Fallback推荐（实际推荐会在 multi_analyst_system 中更新）
        "market_sentiment": market_analysis.get("market_sentiment", "neutral"),  # 添加市場情緒
    }

    # ---- 初始化 Portfolio 和 Trade Logger（如果未提供）----
    if portfolio is None:
        # CRITICAL: 尝试从 portfolio_state.json 加载现有状态，而不是创建新的空 Portfolio
        # CRITICAL: Use project root data/logs directory explicitly
        portfolio_file = _get_project_logs_dir() / "portfolio_state.json"
        if portfolio_file.exists():
            try:
                with portfolio_file.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                portfolio = Portfolio(
                    cash=float(state.get("cash", 10000.0)),
                    initial_value=float(state.get("initial_value", 10000.0)),
                )
                # 恢复持仓
                from src.data.portfolio import Position
                for symbol, pos_info in state.get("positions", {}).items():
                    if isinstance(pos_info, dict):
                        qty = int(pos_info.get("quantity", 0))
                        avg_cost = float(pos_info.get("avg_cost", 0))
                        total_cost = float(pos_info.get("total_cost", 0))
                        if total_cost <= 0:
                            total_cost = avg_cost * qty
                        if qty > 0:
                            portfolio._positions[symbol] = Position(
                                symbol=symbol,
                                quantity=qty,
                                avg_cost=avg_cost,
                                total_cost=total_cost,
                            )
                print(f"[TRADING CYCLE] Loaded portfolio from state: cash=${portfolio.cash:.2f}, positions={len(portfolio._positions)}")
            except Exception as e:
                print(f"[TRADING CYCLE] Warning: Failed to load portfolio state: {e}, using default Portfolio()")
                portfolio = Portfolio()
        else:
            print(f"[TRADING CYCLE] Portfolio state file not found, using default Portfolio()")
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

    # Ensure we have price coverage for all held positions (fallback to available data)
    if portfolio:
        for symbol, pos in portfolio._positions.items():
            price = last_prices.get(symbol)
            if price is None or price <= 0:
                fallback_price = None
                stock_data = stocks.get(symbol)
                if isinstance(stock_data, dict):
                    fallback_price = (
                        stock_data.get("price")
                        or stock_data.get("last_price")
                        or stock_data.get("close")
                    )
                if fallback_price is None:
                    mv_prices = market_view.get("last_prices") if isinstance(market_view, dict) else None
                    fallback_price = mv_prices.get(symbol) if isinstance(mv_prices, dict) else None
                if fallback_price is None:
                    fallback_price = pos.avg_cost
                try:
                    last_prices[symbol] = float(fallback_price)
                except (TypeError, ValueError):
                    last_prices[symbol] = float(pos.avg_cost)

    # ---- (1.5) 加載歷史記憶（長短記憶）----
    historical_memories = []
    try:
        from src.data.memory_manager import MemoryManager
        # CRITICAL: Use project root data/logs directory explicitly
        memory_manager = MemoryManager(root=str(_get_project_logs_dir()))
        # 加載最近5天的記憶摘要（短期記憶）
        historical_memories = memory_manager.load_recent_memories(
            days=5,
            end_date=end if end else None,
            summary_only=True,  # 只加載摘要，減少 prompt 長度
        )
        if historical_memories:
            print(f"[MEMORY] ✅ Loaded {len(historical_memories)} historical memories for context")
            # 显示记忆日期范围
            if len(historical_memories) > 0:
                dates = [m.get("date", "N/A") for m in historical_memories]
                print(f"[MEMORY] 📅 Memory dates: {', '.join(dates)}")
        else:
            print(f"[MEMORY] ⚠️ No historical memories found (agents should use memory tools to retrieve past decisions)")
    except Exception as e:
        print(f"[MEMORY WARN] Failed to load historical memories: {e}")
        # 不影響主流程，繼續執行

    # ---- (2) 检查当前订单状态（传递给agent）----
    from src.data.order_manager import OrderManager
    # CRITICAL: Use project root data/logs directory explicitly
    order_manager = OrderManager(root=str(_get_project_logs_dir()))
    
    # 检查市场是否开盘（用于确定订单日期，排除周末和节假日）
    # CRITICAL FIX: 传入 None 让函数直接获取美东时间，避免时区转换错误
    from src.utils.trading_days import is_market_open as check_market_open
    now = datetime.now()
    is_market_open = check_market_open(None)  # 传入 None 直接获取美东时间
    
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
    # CRITICAL: Use project root data/logs directory explicitly
    filled_file = _get_project_logs_dir() / "filled_orders.jsonl"
    if filled_file.exists():
        try:
            with filled_file.open("r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        order = json.loads(line)
                        if _get_order_date(order) == order_date:
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
    # 注意：这里先准备仓位信息（在订单结算之前），但会在订单结算后更新
    # 为了确保讨论系统也能看到当前仓位，我们先准备一个初步的仓位信息
    preliminary_positions_info = {}
    preliminary_portfolio_value = 10000.0
    if portfolio:
        preliminary_portfolio_value = portfolio.value(last_prices)
        for symbol, pos in portfolio._positions.items():
            current_price = last_prices.get(symbol, pos.avg_cost)
            preliminary_positions_info[symbol] = {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "current_price": current_price,
                "market_value": pos.quantity * current_price,
            }
    
    # CRITICAL FIX: 计算初步可用现金（根据模式决定是否应用现金储备）
    from src.utils.config_loader import load_config
    config = load_config()
    position_limit_mode = config.get("position_limit_mode", "auto")
    min_cash_reserve_ratio = config.get("min_cash_reserve_ratio")
    
    # CRITICAL FIX: 即使是在 auto 模式下，可用现金也必须限制在实际现金范围内
    # LLM 可以自主决定如何使用现金，但不能超过实际可用的现金
    if position_limit_mode == "auto" or min_cash_reserve_ratio is None:
        preliminary_available_cash = portfolio.cash if portfolio else 0.0
        print(f"[TRADING CYCLE] Cash reserve DISABLED (auto mode) - all cash available: ${preliminary_available_cash:.2f} (LLM autonomous, but limited to actual cash)")
    else:
        MIN_CASH_RESERVE_RATIO = float(min_cash_reserve_ratio)
        required_cash_reserve = preliminary_portfolio_value * MIN_CASH_RESERVE_RATIO
        preliminary_available_cash = max(0, portfolio.cash - required_cash_reserve) if portfolio else 0.0
        print(f"[TRADING CYCLE] Cash reserve ENABLED (configured mode): reserve={MIN_CASH_RESERVE_RATIO:.1%}, available=${preliminary_available_cash:.2f}")
    
    # CRITICAL FIX: 使用四个独立 Analyst 的版本，确保每个 analyst 都有工具调用和 summary
    # 获取当前仓位信息（用于 analyst 分析）
    current_positions = {}
    if portfolio:
        # FIX: Use _positions instead of positions property (positions returns Dict[str, int], _positions returns Dict[str, Position])
        for symbol, pos in portfolio._positions.items():
            current_positions[symbol] = {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "total_cost": pos.total_cost,
            }
    
    # 获取订单状态（用于 analyst 分析）
    order_status = None
    if trade_logger:
        try:
            pending_orders = trade_logger.get_pending_orders()
            filled_orders = trade_logger.get_filled_orders(limit=10)
            order_status = {
                "pending": len(pending_orders),
                "filled_recent": len(filled_orders),
            }
        except:
            order_status = None
    
    # CRITICAL FIX: 计算 portfolio_value（使用 market_view 中的价格）
    portfolio_value = None
    if portfolio:
        # 从 market_view 中提取价格
        last_prices = {}
        if market_view and "stocks" in market_view:
            for symbol, stock_data in market_view["stocks"].items():
                if isinstance(stock_data, dict) and "price" in stock_data:
                    last_prices[symbol] = stock_data["price"]
        
        # 如果有价格数据，使用 portfolio.value() 计算总净值
        if last_prices:
            portfolio_value = portfolio.value(last_prices)
        else:
            # 如果没有价格数据，使用现金 + 初始净值作为近似值
            portfolio_value = portfolio.cash + portfolio.initial_value
    
    # CRITICAL: Use optimized parallel version as default (direct integration)
    print("[TRADING CYCLE] ✅ Using OPTIMIZED agent discussion system (ToolCoordinator + SharedContext + BudgetAllocator)")
    # CRITICAL FIX: 传递 historical_memories 给 discussion system
    convo = run_multi_analyst_discussion_parallel(
        market_view=market_view,  # 传入完整的market_view
        use_tools=auto_tools,
        tool_budget=tool_budget,
        order_status=order_status,
        current_positions=current_positions if current_positions else None,
        portfolio_value=portfolio_value,
        available_cash=portfolio.cash if portfolio else None,
        enable_parallel=True,
        historical_memories=historical_memories,  # 传递历史记忆
    )
    final_stance = convo.get("final_stance", "neutral")
    
    # CRITICAL FIX: 从 multi_analyst_system 的 Market Analyst LLM 输出中提取推荐股票
    # 优先使用 LLM 的推荐，如果没有则使用 fallback
    # CRITICAL FIX: Filter out ETFs and invalid symbols from recommended stocks
    from src.utils.etf_checker import is_etf
    
    recommended_stocks_from_llm = []
    analyst_reports = convo.get("analyst_reports", {})
    market_analyst_report = analyst_reports.get("market", {})
    if market_analyst_report:
        # 尝试从 Market Analyst 的响应中提取 recommended_stocks
        raw_recommended = market_analyst_report.get("recommended_stocks", [])
        if raw_recommended:
            # CRITICAL FIX: Filter out ETFs and invalid symbols
            if isinstance(raw_recommended, str):
                raw_recommended = [s.strip() for s in raw_recommended.split(",") if s.strip()]
            elif not isinstance(raw_recommended, list):
                raw_recommended = []
            
            filtered_recommended = []
            for sym in raw_recommended:
                sym_upper = str(sym).upper().strip()
                # Skip empty or invalid format
                if not sym_upper or len(sym_upper) > 10 or not sym_upper.replace(".", "").replace("-", "").isalnum():
                    print(f"[TRADING CYCLE] ⚠️ Skipping invalid symbol format in recommended stocks: {sym}")
                    continue
                # Skip ETFs
                if is_etf(sym_upper):
                    print(f"[TRADING CYCLE] ⚠️ Skipping ETF in recommended stocks: {sym_upper}")
                    continue
                filtered_recommended.append(sym_upper)
            
            recommended_stocks_from_llm = filtered_recommended
            if recommended_stocks_from_llm:
                print(f"[TRADING CYCLE] ✅ Using LLM recommended stocks from Market Analyst: {len(recommended_stocks_from_llm)} stocks (filtered from {len(raw_recommended)} raw recommendations)")
                print(f"[TRADING CYCLE]   Recommended stocks: {recommended_stocks_from_llm[:10]}...")
                # 更新 enriched_market 中的推荐股票
                enriched_market["recommended_stocks"] = recommended_stocks_from_llm
            else:
                print(f"[TRADING CYCLE] ⚠️ All recommended stocks were filtered out (ETFs/invalid), using fallback")
        else:
            print(f"[TRADING CYCLE] ⚠️  Market Analyst LLM did not provide recommended_stocks, using fallback")
    else:
        print(f"[TRADING CYCLE] ⚠️  Market Analyst report not found in analyst_reports, using fallback")

    # 將對話寫入 discussion_actions.jsonl（供前端顯示）
    # CRITICAL FIX: 将 convo_file 和 trade_date_str 定义移到 try 块外，确保 RiskAnalyst 和 TraderAgent 写入可以访问
    # CRITICAL: Use project root data/logs directory explicitly
    logs_dir = _get_project_logs_dir()
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    # 獲取交易日期（使用 end 參數，如果沒有則使用今天）
    trade_date = end if end else date.today().isoformat()
    if isinstance(trade_date, str):
        # 確保是 YYYY-MM-DD 格式
        # CRITICAL FIX: datetime 已在文件顶部导入，直接使用
        try:
            trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
            trade_date_str = trade_date_obj.isoformat()
        except:
            trade_date_str = date.today().isoformat()
    else:
        trade_date_str = date.today().isoformat()
    
    try:
        # Path 已经在文件顶部导入，不需要重复导入
        import os
        
        transcript = convo.get("transcript", [])
        tool_context = convo.get("tool_context", [])
        actions = convo.get("actions", [])
        
        # 寫入每一輪對話
        # CRITICAL FIX: json 已在文件顶部导入，确保在 try 块外可以访问
        
        # CRITICAL FIX: 写入三轮 Discussion 信息（从 transcript 中提取，设置正确的 round 字段）
        transcript = convo.get("transcript", [])
        if transcript and isinstance(transcript, list):
            for round_num, round_text in enumerate(transcript, 1):
                if not round_text or not isinstance(round_text, str):
                    continue
                
                # 解析 transcript 格式: "--- Round {r} ---\n{out_text}"
                # 提取轮次和内容
                round_content = round_text
                if "--- Round" in round_text:
                    # 提取轮次编号和内容
                    parts = round_text.split("--- Round", 1)
                    if len(parts) == 2:
                        round_info = parts[1].split("---", 1)
                        if len(round_info) > 1:
                            round_content = round_info[1].strip()
                
                # 写入每轮讨论
                round_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "date": trade_date_str,
                    "agent": "DiscussionCoordinator",
                    "round": round_num,  # CRITICAL: 使用实际轮次编号（1, 2, 3）
                    "content": f"Round {round_num} Discussion:\n\n{round_content}",
                    "type": "discussion",
                    "stance": final_stance,  # 使用最终 stance
                    "summary": round_content,  # CRITICAL FIX: 添加单独的 summary 字段供前端使用
                    "tools_used": [],  # CRITICAL FIX: 确保 tools_used 被正确存储（讨论轮次可能没有工具）
                }
                
                with convo_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(round_entry, ensure_ascii=False) + "\n")
                print(f"[TRADING CYCLE] Wrote Discussion Round {round_num} entry")
        
        # CRITICAL FIX: 确保从 discussion_history 中提取四个 analyst 的结果
        # 如果 discussion_history 为空，尝试从 analyst_reports 中构建
        discussion_history = convo.get("discussion_history", [])
        
        # 如果 discussion_history 为空，从 analyst_reports 构建
        if not discussion_history:
            analyst_reports = convo.get("analyst_reports", {})
            all_tool_calls = convo.get("tool_calls", [])
            for analyst_key, report in analyst_reports.items():
                if report and isinstance(report, dict):
                    # 标准化 analyst 名称
                    analyst_name_map = {
                        "market": "Market Analyst",
                        "technical": "Technical Analyst",
                        "fundamental": "Fundamental Analyst",
                        "sentiment": "Sentiment Analyst",
                    }
                    analyst_name = analyst_name_map.get(analyst_key, analyst_key.title() + " Analyst")
                    
                    # 从 tool_calls 中提取该 analyst 使用的工具
                    tools_used = [tc.get("tool", "") for tc in all_tool_calls if tc.get("analyst", "").lower() == analyst_key]
                    
                    # 确保有 analysis（summary）
                    analysis = report.get("analysis", "No analysis provided")
                    if not analysis or len(analysis.strip()) < 50:
                        # 如果 analysis 太短，尝试从工具结果生成
                        if tools_used:
                            analysis = f"Analysis based on {', '.join(tools_used[:3])}. {analysis}"
                    
                    discussion_history.append({
                        "analyst": analyst_name,
                        "stance": report.get("stance", "neutral"),
                        "analysis": analysis,
                        "tools_used": tools_used,
                        "key_points": report.get("recommendations", [])[:3] if report.get("recommendations") else [],
                    })
        
        coordinator_found_in_history = False
        for entry_data in discussion_history:
            analyst_name = entry_data.get("analyst", "Unknown")
            
            # 检查是否是 Discussion Coordinator
            analyst_name_lower = analyst_name.lower().strip()
            is_coordinator = (analyst_name_lower in ["discussion coordinator", "discussioncoordinator", "coordinator"] or
                            "discussion" in analyst_name_lower and "coordinator" in analyst_name_lower or
                            analyst_name_lower.startswith("discussion") and "coordinator" in analyst_name_lower)
            
            if is_coordinator:
                # 如果找到 Coordinator，标记并写入（统一格式为 DiscussionCoordinator）
                # 只写入第一个 Coordinator，避免重复
                if not coordinator_found_in_history:
                    coordinator_found_in_history = True
                    stance = entry_data.get("stance", "neutral")
                    analysis = entry_data.get("analysis", entry_data.get("summary", "No analysis provided"))
                    
                    entry = {
                        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                        "date": trade_date_str,
                        "agent": "DiscussionCoordinator",  # 统一使用 DiscussionCoordinator
                        "round": 0,
                        "content": f"Stance: {stance}\n\nAnalysis: {analysis}",
                        "type": "discussion",
                        "stance": stance,
                        "summary": analysis,  # CRITICAL FIX: 添加单独的 summary 字段供前端使用
                        "tools_used": entry_data.get("tools_used", []),  # CRITICAL FIX: 确保 tools_used 被正确存储
                    }
                    with convo_file.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    print(f"[TRADING CYCLE] Wrote Coordinator from discussion_history (stance: {stance})")
                else:
                    print(f"[TRADING CYCLE] Skipped duplicate Coordinator in discussion_history: {analyst_name}")
                continue  # 跳过，不重复处理
            
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
                "summary": analysis,  # CRITICAL FIX: 添加单独的 summary 字段供前端使用
                "tools_used": tools_used,  # CRITICAL FIX: 确保 tools_used 被正确存储
            }
            
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # 寫入Coordinator統整結果（只寫一次，避免重複）
        # 如果 discussion_history 中已经有 Coordinator，就不再单独写入 coordinator_summary
        coordinator_summary = convo.get("coordinator_summary")
        if coordinator_summary and not coordinator_found_in_history:
            if isinstance(coordinator_summary, dict):
                stance = coordinator_summary.get("stance", "neutral")
                summary = coordinator_summary.get("summary", "No summary provided")
                # 确保 summary 不为空
                if not summary or summary.strip() == "":
                    summary = "Coordinator synthesized all analyst perspectives."
                
                entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "date": trade_date_str,
                    "agent": "DiscussionCoordinator",
                    "round": 0,
                    "content": f"Stance: {stance}\n\nAnalysis: {summary}",  # 使用 Analysis 而不是 Summary，保持一致性
                    "type": "discussion",
                    "stance": stance,
                    "summary": summary,  # CRITICAL FIX: 添加单独的 summary 字段供前端使用
                    "tools_used": [],  # Coordinator 不使用工具
                }
                with convo_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"[TRADING CYCLE] Wrote Coordinator from coordinator_summary (stance: {stance})")
        elif coordinator_summary and coordinator_found_in_history:
            print(f"[TRADING CYCLE] Skipped writing coordinator_summary (Coordinator already exists in discussion_history)")
        
        # 寫入工具使用記錄（從tool_calls中提取）
        tool_calls = convo.get("tool_calls", [])
        print(f"[TRADING CYCLE] Writing {len(tool_calls)} tool calls to discussion_actions.jsonl")
        
        # DEBUG: Log tool_calls structure for news tools
        # CRITICAL FIX: Check both "tool" and "name" fields (some tool_calls may use "name")
        news_tool_calls = []
        for tc in tool_calls:
            tool_name = tc.get("tool", "") or tc.get("name", "")
            if tool_name.lower() in ["plan_and_scan_news", "news_scan", "get_news_scan"]:
                news_tool_calls.append(tc)
        
        if news_tool_calls:
            print(f"[TRADING CYCLE] [NEWS] Found {len(news_tool_calls)} news tool calls in convo.tool_calls")
            for idx, tc in enumerate(news_tool_calls):
                tool_name = tc.get("tool", "") or tc.get("name", "")
                print(f"[TRADING CYCLE] [NEWS]   Tool call {idx}: analyst={tc.get('analyst')}, tool={tool_name}, has_result={bool(tc.get('result'))}")
        else:
            print(f"[TRADING CYCLE] [NEWS] ⚠️ No news tool calls found in {len(tool_calls)} tool calls")
            # DEBUG: List all tool names (check both "tool" and "name" fields)
            all_tool_names = [tc.get("tool", "") or tc.get("name", "") for tc in tool_calls]
            print(f"[TRADING CYCLE] [NEWS]   All tool names: {', '.join(all_tool_names[:10])}{'...' if len(all_tool_names) > 10 else ''}")
        
        for tool_call in tool_calls:
            analyst_name = tool_call.get("analyst", "Unknown")
            # CRITICAL FIX: Check both "tool" and "name" fields (some tool_calls may use "name")
            tool_name = tool_call.get("tool", "") or tool_call.get("name", "")
            
            # CRITICAL FIX: Map deprecated news_scan to plan_and_scan_news (for Risk Analyst and others)
            if tool_name == "news_scan":
                print(f"[TRADING CYCLE] [NEWS] Mapping news_scan to plan_and_scan_news (news_scan is deprecated)")
                tool_name = "plan_and_scan_news"
            
            tool_result = tool_call.get("result", {})
            
            # 標準化agent名稱
            agent_name_map = {
                "market": "MarketAnalyst",
                "marketanalyst": "MarketAnalyst",
                "technical": "TechnicalAnalyst",
                "technicalanalyst": "TechnicalAnalyst",
                "fundamental": "FundamentalAnalyst",
                "fundamentanalyst": "FundamentalAnalyst",
                "sentiment": "SentimentAnalyst",
                "sentimentanalyst": "SentimentAnalyst",  # CRITICAL FIX: 支持完整名称匹配
            }
            # CRITICAL FIX: 先尝试完整匹配，再尝试小写匹配
            agent_name = agent_name_map.get(analyst_name, agent_name_map.get(analyst_name.lower(), analyst_name))
            
            # 格式化工具結果
            # 处理双重嵌套：{"ok": true, "result": {"ok": true, "result": {...}}}
            # 递归提取实际的 result 数据
            actual_result = tool_result
            if isinstance(tool_result, dict):
                while isinstance(actual_result, dict) and "ok" in actual_result and "result" in actual_result:
                    actual_result = actual_result["result"]
            
            # CRITICAL FIX: 对于新闻工具，先保存完整的 articles 和 hits（在截断之前）
            news_articles_backup = None
            news_hits_backup = None
            if tool_name in ["plan_and_scan_news", "news_scan"] and isinstance(actual_result, dict):
                news_articles_backup = actual_result.get("articles", [])
                news_hits_backup = actual_result.get("hits", [])
                print(f"[TRADING CYCLE] [NEWS] Backed up news data before truncation: {len(news_articles_backup)} articles, {len(news_hits_backup)} hits")
            
            if isinstance(actual_result, dict):
                if "error" in actual_result:
                    result_text = f"Error: {actual_result.get('error', 'Unknown error')}"
                else:
                    # 提取關鍵信息
                    result_text = json.dumps(actual_result, ensure_ascii=False, indent=2)
                    # 对于新闻工具，保留更多数据（不截断或只截断到5000字符）
                    # 对于其他工具，限制在2000字符
                    max_length = 5000 if tool_name in ["news_scan", "plan_and_scan_news"] else 2000
                    if len(result_text) > max_length:
                        # 对于新闻工具，尝试保留完整的 articles 和 hits 数组（即使截断，也要确保数组是完整的）
                        if tool_name in ["news_scan", "plan_and_scan_news"]:
                            # CRITICAL FIX: 优先保留 articles（包含内容），如果没有则保留 hits
                            articles = actual_result.get("articles", [])
                            hits = actual_result.get("hits", [])
                            queries = actual_result.get("queries", [])
                            
                            # 构建一个简化的结果，但保留完整的 articles 和 hits
                            simplified = {}
                            if articles:
                                simplified["articles"] = articles
                            if hits:
                                simplified["hits"] = hits
                            if queries:
                                simplified["queries"] = queries
                            
                            result_text = json.dumps(simplified, ensure_ascii=False, indent=2)
                            # 如果还是太长，至少保留前几个 articles/hits
                            if len(result_text) > max_length:
                                # 保留前 N 个 articles（优先）或 hits，确保 JSON 完整
                                if articles:
                                    max_items = min(len(articles), 10)  # 最多保留10篇文章
                                    simplified["articles"] = articles[:max_items]
                                    simplified["total_articles"] = len(articles)
                                elif hits:
                                    max_items = min(len(hits), 10)  # 最多保留10个hits
                                    simplified["hits"] = hits[:max_items]
                                    simplified["total_hits"] = len(hits)
                                
                                result_text = json.dumps(simplified, ensure_ascii=False, indent=2)
                                if len(result_text) > max_length:
                                    result_text = result_text[:max_length] + "\n... (truncated)"
                        else:
                            result_text = result_text[:max_length] + "\n... (truncated)"
            else:
                result_text = str(actual_result)
                if len(result_text) > 2000:
                    result_text = result_text[:2000] + "... (truncated)"
            
            # CRITICAL FIX: 根据工具类型分类（news, risk, market等）
            tool_category = "other"
            if tool_name in ["news_scan", "plan_and_scan_news", "web_search", "fetch_url"]:
                tool_category = "news"
            elif tool_name in ["vix_term", "vix_close", "fear_greed", "get_market_breadth"]:
                tool_category = "risk"
            elif tool_name in ["get_market_indices", "get_sector_rotation", "get_correlation_matrix", "get_advanced_indicators", "get_support_resistance"]:
                tool_category = "market"
            elif tool_name in ["get_company_fundamentals", "get_earnings_history", "get_financial_statements"]:
                tool_category = "fundamental"
            elif tool_name in ["get_economic_summary", "get_labor_market_data", "get_treasury_yield_curve", "fetch_fred_indicator"]:
                tool_category = "economic"
            elif tool_name in ["fetch_crypto_batch", "get_crypto_price"]:
                tool_category = "crypto"
            
            # CRITICAL FIX: 对于 get_company_fundamentals，确保 tool_result 包含 symbol（即使结果被截断）
            # CRITICAL FIX: 对于新闻工具，确保保留完整的 articles 和 hits 数组（使用备份数据）
            tool_result_data = actual_result if isinstance(actual_result, dict) else {"raw": result_text}
            
            # CRITICAL FIX: 对于新闻工具，使用备份的完整数据（即使 result_text 被截断）
            if tool_name in ["plan_and_scan_news", "news_scan"]:
                # CRITICAL FIX: Ensure tool_result_data is a dict (not nested structure)
                # The frontend expects tool_result_data to directly contain articles/hits, not wrapped in {ok: true, result: {...}}
                if not isinstance(tool_result_data, dict):
                    tool_result_data = {}
                
                # 使用备份的完整 articles 和 hits（在截断之前保存的）
                if news_articles_backup is not None:
                    tool_result_data["articles"] = news_articles_backup
                if news_hits_backup is not None:
                    tool_result_data["hits"] = news_hits_backup
                
                # 如果备份不存在，尝试从 actual_result 中提取
                if isinstance(actual_result, dict):
                    if "articles" not in tool_result_data and "articles" in actual_result:
                        articles_list = actual_result.get("articles", [])
                        if isinstance(articles_list, list):
                            tool_result_data["articles"] = articles_list
                    if "hits" not in tool_result_data and "hits" in actual_result:
                        hits_list = actual_result.get("hits", [])
                        if isinstance(hits_list, list):
                            tool_result_data["hits"] = hits_list
                    # 保留其他重要字段
                    for key in ["queries", "summary", "total_hits", "total_articles"]:
                        if key in actual_result:
                            tool_result_data[key] = actual_result.get(key)
                
                # CRITICAL FIX: Remove nested structure - frontend expects direct access to articles/hits
                # Do NOT wrap in {ok: true, result: {...}} - frontend will handle it
                articles_count = len(tool_result_data.get('articles', [])) if isinstance(tool_result_data.get('articles'), list) else 0
                hits_count = len(tool_result_data.get('hits', [])) if isinstance(tool_result_data.get('hits'), list) else 0
                print(f"[TRADING CYCLE] [NEWS] Preserved news data: {articles_count} articles, {hits_count} hits")
                print(f"[TRADING CYCLE] [NEWS] tool_result_data structure: keys={list(tool_result_data.keys())[:10]}")
                if tool_result_data.get("articles"):
                    print(f"[TRADING CYCLE] [NEWS] articles is array: {isinstance(tool_result_data.get('articles'), list)}, length: {articles_count}")
                if tool_result_data.get("hits"):
                    print(f"[TRADING CYCLE] [NEWS] hits is array: {isinstance(tool_result_data.get('hits'), list)}, length: {hits_count}")
            
            if tool_name == "get_company_fundamentals" and isinstance(actual_result, dict):
                # 确保 symbol 字段存在（即使结果被截断，也要保留 symbol）
                if "symbol" not in tool_result_data:
                    # 尝试从 actual_result 中提取 symbol
                    symbol = actual_result.get("symbol") or actual_result.get("Symbol")
                    if symbol:
                        tool_result_data["symbol"] = symbol
                    # 如果 actual_result 被截断了，尝试从 content 中提取
                    elif "symbol" in result_text:
                        try:
                            import re
                            symbol_match = re.search(r'"symbol"\s*:\s*"([^"]+)"', result_text)
                            if symbol_match:
                                tool_result_data["symbol"] = symbol_match.group(1)
                        except:
                            pass
            
            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,
                "agent": agent_name,  # CRITICAL FIX: 使用调用工具的 agent 名称（MarketAnalyst, TechnicalAnalyst等），而不是 ToolSystem
                "round": 0,
                "content": f"Tool used: {tool_name}: {result_text}",
                "type": "tool",
                "tool_name": tool_name,
                "tool_category": tool_category,  # CRITICAL FIX: 添加工具分类
                "tool_result": tool_result_data,  # CRITICAL FIX: 添加工具结果（结构化数据，确保包含 symbol）
            }
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            
            # DEBUG: Log news tool writes
            if tool_category == "news":
                print(f"[TRADING CYCLE] ✅ Wrote news tool entry: {tool_name}, agent: {agent_name}, category: {tool_category}")
                if isinstance(tool_result_data, dict):
                    # CRITICAL FIX: Check for nested structure
                    actual_result = tool_result_data
                    if tool_result_data.get("ok") and "result" in tool_result_data:
                        actual_result = tool_result_data.get("result", {})
                    elif not tool_result_data.get("ok"):
                        actual_result = tool_result_data
                    
                    hits = actual_result.get("hits", []) if isinstance(actual_result, dict) else []
                    articles = actual_result.get("articles", []) if isinstance(actual_result, dict) else []
                    print(f"[TRADING CYCLE]   News data in entry: {len(hits) if isinstance(hits, list) else 0} hits, {len(articles) if isinstance(articles, list) else 0} articles")
                    print(f"[TRADING CYCLE]   tool_result_data keys: {list(tool_result_data.keys())[:10]}")
                    if isinstance(actual_result, dict):
                        print(f"[TRADING CYCLE]   actual_result keys: {list(actual_result.keys())[:10]}")
                        if articles and isinstance(articles, list) and len(articles) > 0:
                            print(f"[TRADING CYCLE]   First article keys: {list(articles[0].keys())[:10] if isinstance(articles[0], dict) else 'not dict'}")
                        elif hits and isinstance(hits, list) and len(hits) > 0:
                            print(f"[TRADING CYCLE]   First hit keys: {list(hits[0].keys())[:10] if isinstance(hits[0], dict) else 'not dict'}")
        
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
    
    # CRITICAL: Use project root data/logs directory explicitly
    order_manager = OrderManager(root=str(_get_project_logs_dir()))
    
    # 检查市场是否开盘，决定订单日期（排除周末和节假日）
    # CRITICAL FIX: 传入 None 让函数直接获取美东时间，避免时区转换错误
    from src.utils.trading_days import is_market_open as check_market_open
    now = datetime.now()
    is_market_open = check_market_open(None)  # 传入 None 直接获取美东时间
    
    # 如果市场收盘后，订单日期应该是明天的日期
    # 注意：如果end参数被传递（用于测试或规划），优先使用end日期
    existing_pending_orders = []
    if end:
        # end参数优先：用于测试或规划特定日期的交易
        # 在多日模拟中，订单日期应该使用end日期（当天），而不是"明天"
        today = end
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        print(f"[TRADING CYCLE] Using end date: {today} (forced date for testing/planning)")
        # CRITICAL FIX: 即使有end参数，也应该检查实际市场状态
        # 只有在实际市场开放时，才允许交易；否则只运行分析
        is_market_open_for_simulation = is_market_open
        if not is_market_open:
            print(f"[TRADING CYCLE] Market is actually closed. Will run analysis only (no trading).")
    elif is_market_open:
        today = date.today().isoformat()
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        is_market_open_for_simulation = True
        print(f"[TRADING CYCLE] ✅ Market is OPEN - trading allowed")
    else:
        # CRITICAL FIX: 市场收盘后，允许运行对话（AI分析），但不执行交易
        # 继续执行对话和分析，但跳过订单创建和执行
        print(f"[TRADING CYCLE] ⚠️  Market closed. Running conversation/analysis only (no trading).")
        # 设置标志，后续跳过订单执行
        is_market_open_for_simulation = False
        # CRITICAL FIX: 打印详细的市场状态信息，帮助调试
        import pytz
        et_tz = pytz.timezone('America/New_York')
        et_time = datetime.now(et_tz)
        from src.utils.trading_days import is_trading_day
        print(f"[TRADING CYCLE] Market status details:")
        print(f"  - Current ET time: {et_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        print(f"  - Market hours: 9:30 AM - 4:00 PM ET")
        print(f"  - Today is trading day: {is_trading_day(et_time.date())}")
        today = date.today().isoformat()
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        
        # CRITICAL FIX: 市场关闭时，立即清理今天的pending订单（因为市场订单不应该有pending状态）
        # 即使没有运行交易周期，也要清理pending订单
        if len(existing_pending_orders) > 0:
            print(f"[TRADING CYCLE] Market is closed. Immediately cancelling {len(existing_pending_orders)} today's pending orders (market orders should not be pending when market is closed).")
            cancelled_count = order_manager.cancel_orders(order_date=today)
            if cancelled_count > 0:
                print(f"[TRADING CYCLE] Cancelled {cancelled_count} today's pending orders")
                # 重新加载pending订单（应该为空）
                existing_pending_orders = order_manager.load_pending_orders(order_date=today)
    
    executed_trades = []
    execution_errors = []
    placed_orders = []  # 記錄掛單
    new_orders_count = 0  # 記錄本次新創建的訂單數量（不包括existing_pending_orders）
    
    # 检查是否有大量pending订单，如果有，取消今日的pending订单，只保留明日的订单
    # 这个机制可以防止pending订单堆积
    # CRITICAL: 无论市场是否开放，都要清理旧的pending订单
    if not end:  # 只在实时模式下执行（不在多日模拟中执行）
        all_pending_orders = order_manager.load_pending_orders()  # 加载所有pending订单
        today_str = date.today().isoformat()

        # 自动清理前几个交易日遗留的订单，防止无限累积
        stale_dates = sorted({
            _get_order_date(o)
            for o in all_pending_orders
            if _get_order_date(o) and _get_order_date(o) < today_str
        })
        for stale_date in stale_dates:
            if stale_date:
                cancelled = order_manager.cancel_orders(order_date=stale_date)
                if cancelled > 0:
                    print(f"[TRADING CYCLE] Removed {cancelled} stale pending orders from {stale_date}")

        # 重新加载（排除已清理的旧订单）
        all_pending_orders = order_manager.load_pending_orders()
        
        from src.utils.trading_days import get_next_trading_day
        tomorrow_str = get_next_trading_day(date.today(), days_ahead=1).isoformat()
        
        today_orders = [o for o in all_pending_orders if _get_order_date(o) == today_str]
        tomorrow_orders = [o for o in all_pending_orders if _get_order_date(o) == tomorrow_str]
        
        # CRITICAL: 如果市场关闭，清理今天的pending订单（因为市场订单不应该有pending状态）
        if not is_market_open_for_simulation and len(today_orders) > 0:
            print(f"[TRADING CYCLE] Market is closed. Cancelling {len(today_orders)} today's pending orders (market orders should not be pending).")
            cancelled_count = order_manager.cancel_orders(order_date=today_str)
            if cancelled_count > 0:
                print(f"[TRADING CYCLE] Cancelled {cancelled_count} today's pending orders")
                # 重新加载pending订单（排除已取消的今日订单）
                existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        # 如果今日有pending订单，且总pending订单数量较多（>= 5），取消今日的订单
        elif len(today_orders) > 0 and len(all_pending_orders) >= 5:
            print(f"[TRADING CYCLE] WARNING: Found {len(all_pending_orders)} total pending orders ({len(today_orders)} for today, {len(tomorrow_orders)} for tomorrow)")
            print(f"[TRADING CYCLE] Cancelling {len(today_orders)} today's pending orders, keeping {len(tomorrow_orders)} tomorrow's orders")
            cancelled_count = order_manager.cancel_orders(order_date=today_str)
            if cancelled_count > 0:
                print(f"[TRADING CYCLE] Cancelled {cancelled_count} today's pending orders")
                # 重新加载pending订单（排除已取消的今日订单）
                existing_pending_orders = order_manager.load_pending_orders(order_date=today)
    
    # 处理pending订单的逻辑：
    # 1. 如果市场开盘且有pending订单：先尝试结算这些订单，然后决定是否创建新订单
    # 2. 如果市场收盘且有pending订单（明天的订单）：不创建新订单，只返回现有订单
    if existing_pending_orders:
        # 在多日模拟中（end参数提供），也执行订单
        # 条件：1) 市场开盘且是今天，或 2) 提供了end参数（多日模拟）
        # CRITICAL FIX: 使用 is_market_open_for_simulation 而不是 is_market_open，确保市场关闭时不执行
        should_settle_orders = (is_market_open_for_simulation and today == date.today().isoformat()) or (end is not None)
        if should_settle_orders:
            # 市场开盘时，先尝试结算今天的pending订单
            print(f"[TRADING CYCLE] Market is open (or simulation mode). Found {len(existing_pending_orders)} pending orders for {today}. Checking if they can be filled...")
            
            # 加载当前portfolio状态
            try:
                # CRITICAL: Use project root data/logs directory explicitly
                portfolio_file = _get_project_logs_dir() / "portfolio_state.json"
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
                            # CRITICAL FIX: 只有在市场开盘时才使用实时价格，市场关闭时不执行订单
                            use_realtime_for_check = (end is None) and (today == date.today().isoformat()) and is_market_open_for_simulation
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
                                    realized_pnl = None
                                    if action == "BUY":
                                        current_portfolio.buy(symbol, quantity, fill_price)
                                    elif action == "SELL":
                                        # 卖出时计算已实现损益
                                        realized_pnl = current_portfolio.sell(symbol, quantity, fill_price)
                                        print(f"[TRADING CYCLE] Realized P&L: ${realized_pnl['realized_pnl']:.2f} ({realized_pnl['realized_pnl_pct']:+.2f}%)")
                                    
                                    # 标记订单为已成交（传递已实现损益，仅SELL订单有值）
                                    order_manager.mark_order_filled(order, fill_result, realized_pnl=realized_pnl)
                                    settled_count += 1
                                    print(f"[TRADING CYCLE] Order {order_id} executed successfully")
                        except Exception as e:
                            print(f"[TRADING CYCLE] Error processing order {order_id}: {e}")
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
                        print(f"[TRADING CYCLE] Settled {settled_count} orders, portfolio updated")
                        
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
                        print(f"[TRADING CYCLE] All pending orders settled.")
                        # CRITICAL FIX: 在实时模式下，如果今天已经创建过订单（即使已全部成交），
                        # 不应该再次创建新订单，避免每小时重复创建
                        # 检查今天是否有已成交的订单（filled_orders）
                        # CRITICAL: Use project root data/logs directory explicitly
                        filled_file = _get_project_logs_dir() / "filled_orders.jsonl"
                        today_has_filled_orders = False
                        if filled_file.exists() and not end:  # 只在实时模式下检查
                            try:
                                with filled_file.open("r", encoding="utf-8") as f:
                                    for line in f:
                                        if line.strip():
                                            filled_order = json.loads(line)
                                            if _get_order_date(filled_order) == today and filled_order.get("status") == "FILLED":
                                                today_has_filled_orders = True
                                                break
                            except Exception:
                                pass
                        
                        if today_has_filled_orders and not end:
                            print(f"[TRADING CYCLE] WARNING: Today already has filled orders. Skipping new order creation to prevent hourly duplicates.")
                            return {
                                "placed_orders": [],
                                "executed_trades": executed_trades,
                                "execution_errors": [],
                                "conversations_count": len(convo.get("entries", [])),
                                "is_planning": False,
                                "order_date": today,
                                "message": f"Today already has filled orders. No new orders created to prevent hourly duplicates."
                            }
                        else:
                            print(f"[TRADING CYCLE] Proceeding to create new orders if needed.")
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
            # 市场收盘后，如果有pending订单，应该清理它们（因为市场订单不应该有pending状态）
            # CRITICAL FIX: 市场关闭时，清理今天的pending订单，不返回它们
            if len(existing_pending_orders) > 0:
                print(f"[TRADING CYCLE] Market is closed. Cancelling {len(existing_pending_orders)} today's pending orders (market orders should not be pending when market is closed).")
                cancelled_count = order_manager.cancel_orders(order_date=today)
                if cancelled_count > 0:
                    print(f"[TRADING CYCLE] Cancelled {cancelled_count} today's pending orders")
                    # 重新加载pending订单（应该为空）
                    existing_pending_orders = order_manager.load_pending_orders(order_date=today)
            
            # 市场关闭时，不返回任何pending订单
            placed_orders = []
            # CRITICAL FIX: 记录这是现有订单，不是新创建的
            new_orders_count = 0  # 没有创建新订单
            # 继续执行，返回完整结果（包括讨论、分析等）
            # 不要提前返回，让代码继续执行到最后的return语句
    
    # ---- (3) Risk Analyst：評估倉位風險 ----
    # CRITICAL: 在订单结算之后准备仓位信息，确保 Risk Analyst 使用最新的仓位状态
    # 这样在多日模拟中，Risk Analyst 能够正确分析前一天的仓位状态（包括当天已结算的订单）
    # CRITICAL: 准备完整的持仓信息，包括损益和占比
    # 即使没有持仓，也要传递组合信息（现金、总净值等）给 Risk Analyst
    current_positions_info = {}
    if portfolio:
        portfolio_value = portfolio.value(last_prices)
        for symbol, pos in portfolio._positions.items():
            current_price = last_prices.get(symbol, pos.avg_cost)
            market_value = pos.quantity * current_price
            unrealized_pnl = (current_price - pos.avg_cost) * pos.quantity
            unrealized_pnl_pct = ((current_price - pos.avg_cost) / pos.avg_cost * 100.0) if pos.avg_cost > 0 else 0.0
            position_pct = (market_value / portfolio_value * 100.0) if portfolio_value > 0 else 0.0
            
            current_positions_info[symbol] = {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "current_price": current_price,
                "market_value": market_value,
                "unrealized_pnl": unrealized_pnl,  # 未实现损益（金额）
                "unrealized_pnl_pct": unrealized_pnl_pct,  # 未实现损益（百分比）
                "position_pct": position_pct,  # 持仓占比（占组合净值的百分比）
            }
    else:
        portfolio_value = 10000.0  # 默认初始净值
    
    # CRITICAL: 即使没有持仓（current_positions_info为空），也要传递组合信息
    # 这样 Risk Analyst 可以分析"没有持仓"的状态，评估是否应该开始建仓
    
    # 调用 Risk Analyst (LLM版本)
    # 传递discussion内容让Risk Analyst理解讨论中的风险信号
    previous_discussion_text = "\n".join(convo.get("transcript", []))[:1000]  # 限制长度
    
    # CRITICAL: 即使没有持仓（current_positions_info为空），也要传递组合信息
    # 传递空字典而不是None，这样 Risk Analyst 可以明确知道"没有持仓"的状态
    risk_report = run_risk_analyst_llm(
        market_json=market_view,
        current_positions=current_positions_info,  # 传递空字典{}而不是None，表示"没有持仓"的状态
        portfolio_value=portfolio_value,  # 即使没有持仓，也要传递组合净值
        discussion_risk_signals=discussion_risk_signals,
        previous_discussion=previous_discussion_text,
        use_tools=auto_tools,  # 与discussion使用相同的tool设置
    )
    
    # CRITICAL FIX: 写入 RiskAnalyst 结果到 discussion_actions.jsonl
    try:
        risk_level = risk_report.get("overall_risk_level", risk_report.get("risk_level", "medium"))
        risk_score = risk_report.get("risk_score", 5.0)
        
        # CRITICAL FIX: 从 risk_report 中提取完整的分析内容
        # 优先使用 summary 或 analysis 字段，如果没有则从其他字段构建
        risk_summary = risk_report.get("summary") or risk_report.get("analysis")
        
        # 如果没有 summary/analysis，从其他字段构建分析内容
        if not risk_summary or risk_summary == "No risk analysis provided":
            analysis_parts = []
            
            # 从 market_risks 提取信息
            market_risks = risk_report.get("market_risks", [])
            if market_risks:
                risk_descriptions = []
                for risk in market_risks:
                    if isinstance(risk, dict):
                        risk_type = risk.get("type", "")
                        severity = risk.get("severity", "")
                        description = risk.get("description", "")
                        if description:
                            risk_descriptions.append(f"{risk_type} ({severity}): {description}")
                    elif isinstance(risk, str):
                        risk_descriptions.append(risk)
                if risk_descriptions:
                    analysis_parts.append("Market Risks: " + "; ".join(risk_descriptions))
            
            # 从 position_risks 提取信息
            position_risks = risk_report.get("position_risks", [])
            if position_risks:
                pos_risk_descriptions = []
                for risk in position_risks:
                    if isinstance(risk, dict):
                        description = risk.get("description", "")
                        if description:
                            pos_risk_descriptions.append(description)
                    elif isinstance(risk, str):
                        pos_risk_descriptions.append(risk)
                if pos_risk_descriptions:
                    analysis_parts.append("Position Risks: " + "; ".join(pos_risk_descriptions))
            
            # 从 position_control_report 提取信息
            position_control = risk_report.get("position_control_report", {})
            if position_control:
                checks = position_control.get("checks", [])
                if checks:
                    check_messages = []
                    for check in checks:
                        if isinstance(check, dict):
                            status = check.get("status", "")
                            msg = check.get("message", check.get("description", ""))
                            if msg:
                                check_messages.append(f"{status}: {msg}")
                    if check_messages:
                        analysis_parts.append("Position Control: " + "; ".join(check_messages))
            
            # 从 recommendations 提取信息
            recommendations = risk_report.get("recommendations", [])
            if recommendations:
                recs_text = ', '.join(recommendations) if isinstance(recommendations, list) else str(recommendations)
                analysis_parts.append(f"Recommendations: {recs_text}")
            
            # 如果还是没有内容，使用默认分析
            if analysis_parts:
                risk_summary = " ".join(analysis_parts)
            else:
                # 构建基础分析
                risk_summary = f"Overall risk level is {risk_level.upper()} with a risk score of {risk_score}/10. "
                if current_positions_info:
                    risk_summary += f"Current portfolio has {len(current_positions_info)} positions. "
                else:
                    risk_summary += "Portfolio is currently 100% cash with no market exposure. "
                risk_summary += "Risk assessment considers market conditions, volatility, and portfolio composition."
        
        risk_signals = risk_report.get("risk_signals", [])
        recommendations = risk_report.get("recommendations", [])
        
        # 构建 RiskAnalyst 内容
        risk_content_parts = [
            f"Risk Level: {risk_level.upper()}",
            f"Risk Score: {risk_score}/10",
            f"\n\nAnalysis: {risk_summary}",
        ]
        
        if risk_signals:
            risk_content_parts.append(f"\n\nRisk Signals: {', '.join(risk_signals) if isinstance(risk_signals, list) else str(risk_signals)}")
        
        if recommendations:
            recs_text = ', '.join(recommendations) if isinstance(recommendations, list) else str(recommendations)
            risk_content_parts.append(f"\n\nRecommendations: {recs_text}")
        
        risk_content = "".join(risk_content_parts)
        # CRITICAL FIX: Extract tool calls from risk_report
        tools_used = risk_report.get("tools_used", [])
        tool_calls = risk_report.get("tool_calls", [])
        
        risk_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "date": trade_date_str,
            "agent": "RiskAnalyst",
            "round": 0,
            "content": risk_content,
            "type": "discussion",
            "stance": risk_level,  # 使用 risk_level 作为 stance
            "summary": risk_content,  # CRITICAL FIX: 移除500字符限制，允许完整summary显示
            "tools_used": tools_used,  # CRITICAL FIX: 从 risk_report 中提取 tools_used
            "risk_report": risk_report,  # CRITICAL: 添加完整的 risk_report 数据供前端使用
        }
        
        # CRITICAL FIX: Write tool calls to discussion_actions.jsonl (similar to other analysts)
        if tool_calls:
            print(f"[TRADING CYCLE] Writing {len(tool_calls)} RiskAnalyst tool calls to discussion_actions.jsonl")
            for tool_call_data in tool_calls:
                tool_name = tool_call_data.get("tool", "")
                tool_result = tool_call_data.get("result", {})
                
                # Extract actual result (handle nested structure)
                actual_result = tool_result
                if isinstance(tool_result, dict):
                    while isinstance(actual_result, dict) and "ok" in actual_result and "result" in actual_result:
                        actual_result = actual_result["result"]
                
                # Format result text
                if isinstance(actual_result, dict):
                    if "error" in actual_result:
                        result_text = f"Error: {actual_result.get('error', 'Unknown error')}"
                    else:
                        result_text = json.dumps(actual_result, ensure_ascii=False, indent=2)
                        if len(result_text) > 2000:
                            result_text = result_text[:2000] + "... (truncated)"
                else:
                    result_text = str(actual_result)
                    if len(result_text) > 2000:
                        result_text = result_text[:2000] + "... (truncated)"
                
                # Determine tool category
                tool_category = "other"
                if tool_name in ["vix_term", "vix_close", "fear_greed", "get_market_breadth"]:
                    tool_category = "risk"
                elif tool_name in ["get_market_indices", "get_sector_rotation", "get_correlation_matrix", "get_advanced_indicators", "get_support_resistance"]:
                    tool_category = "market"
                elif tool_name in ["get_company_fundamentals", "get_earnings_history", "get_financial_statements"]:
                    tool_category = "fundamental"
                
                tool_result_data = actual_result if isinstance(actual_result, dict) else {"raw": result_text}
                
                tool_entry = {
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "date": trade_date_str,
                    "agent": "RiskAnalyst",
                    "round": 0,
                    "content": f"Tool used: {tool_name}: {result_text}",
                    "type": "tool",
                    "tool_name": tool_name,
                    "tool_category": tool_category,
                    "tool_result": tool_result_data,
                }
                
                with convo_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(tool_entry, ensure_ascii=False) + "\n")
                
                print(f"[TRADING CYCLE] ✅ Wrote RiskAnalyst tool entry: {tool_name}, category: {tool_category}")
        
        with convo_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(risk_entry, ensure_ascii=False) + "\n")
        print(f"[TRADING CYCLE] Wrote RiskAnalyst conversation entry (risk_level: {risk_level}, risk_score: {risk_score})")
    except Exception as e:
        print(f"[TRADING CYCLE] ⚠️  Failed to write RiskAnalyst conversation entry: {e}")
    
    # ---- (4) Trader Agent：交易決策 ----
    # 从配置文件中读取仓位限制参数（如果可用）
    # Path 已经在文件顶部导入，不需要重复导入
    # CRITICAL FIX: json 已在文件顶部导入，不需要重复导入
    
    # NEW: Position limits are OPTIONAL - only enforce if explicitly set in config.json
    # If not set, agent has complete freedom to decide position sizes
    position_config = {}  # Empty by default - no restrictions
    
    # 尝试从 config.json 读取仓位限制（可选）
    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    try:
        if config_path.exists():
            with open(config_path, 'r', encoding="utf-8") as f:
                config_data = json.load(f)
                
                # CRITICAL FIX: 检查模式设置：'auto' (LLM自主) 或 'configured' (使用约束)
                position_limit_mode = config_data.get("position_limit_mode", "auto")
                
                if position_limit_mode == "configured":
                    # 配置模式：检查是否有仓位限制（使用不带下划线的字段名）
                    if "position_limit_per_stock" in config_data and config_data.get("position_limit_per_stock") is not None:
                        position_config["max_position_per_stock"] = float(config_data["position_limit_per_stock"])
                        print(f"[TRADING CYCLE] Position limit configured: max_position_per_stock = {position_config['max_position_per_stock']:.1%}")
                    
                    if "position_limit_total" in config_data and config_data.get("position_limit_total") is not None:
                        position_config["max_total_position"] = float(config_data["position_limit_total"])
                        print(f"[TRADING CYCLE] Position limit configured: max_total_position = {position_config['max_total_position']:.1%}")
                    
                    if "position_limit_min_per_stock" in config_data and config_data.get("position_limit_min_per_stock") is not None:
                        position_config["min_position_per_stock"] = float(config_data["position_limit_min_per_stock"])
                        print(f"[TRADING CYCLE] Position limit configured: min_position_per_stock = {position_config['min_position_per_stock']:.1%}")
                    
                    if "max_positions" in config_data and config_data.get("max_positions") is not None:
                        position_config["max_positions"] = int(config_data["max_positions"])
                        print(f"[TRADING CYCLE] Position limit configured: max_positions = {position_config['max_positions']}")
                    
                    if position_config:
                        print(f"[TRADING CYCLE] Position limits ENABLED (configured mode) - agent will respect these constraints")
                    else:
                        print(f"[TRADING CYCLE] Position limits DISABLED (configured mode but no limits set) - agent has complete freedom")
                else:
                    # Auto模式（默认）：LLM完全自主决定，不使用任何硬约束
                    print(f"[TRADING CYCLE] Position limits DISABLED (auto mode) - agent has complete freedom to decide position sizes")
        else:
            print(f"[TRADING CYCLE] Config file not found - agent has complete freedom (no position limits)")
    except Exception as e:
        # 如果读取失败，不设置限制（给 agent 自由）
        print(f"[TRADING CYCLE] Failed to load config: {e} - agent has complete freedom (no position limits)")

    # CRITICAL FIX: 计算可用现金（根据模式决定是否应用现金储备）
    # 先计算，以便传递给 trader agent
    from src.utils.config_loader import load_config
    config = load_config()
    position_limit_mode = config.get("position_limit_mode", "auto")
    min_cash_reserve_ratio = config.get("min_cash_reserve_ratio")
    
    # CRITICAL FIX: 即使是在 auto 模式下，可用现金也必须限制在实际现金范围内
    # LLM 可以自主决定如何使用现金，但不能超过实际可用的现金
    if position_limit_mode == "auto" or min_cash_reserve_ratio is None:
        # Auto模式：不应用现金储备限制，但可用现金仍然限制在实际现金范围内
        available_cash_for_trading = portfolio.cash if portfolio else 0.0
        print(f"[TRADING CYCLE] Cash reserve DISABLED (auto mode) - LLM decides cash usage autonomously")
        print(f"[TRADING CYCLE] Portfolio cash: ${portfolio.cash:.2f}, available for trading: ${available_cash_for_trading:.2f} (LLM autonomous, but limited to actual cash)")
    else:
        # Configured模式：应用现金储备限制
        MIN_CASH_RESERVE_RATIO = float(min_cash_reserve_ratio)
        required_cash_reserve = portfolio_value * MIN_CASH_RESERVE_RATIO
        available_cash_for_trading = max(0, portfolio.cash - required_cash_reserve) if portfolio else 0.0
        print(f"[TRADING CYCLE] Cash reserve ENABLED (configured mode): reserve={MIN_CASH_RESERVE_RATIO:.1%}")
        print(f"[TRADING CYCLE] Portfolio cash: ${portfolio.cash:.2f}, required reserve: ${required_cash_reserve:.2f}, available for trading: ${available_cash_for_trading:.2f}")
    
    # CRITICAL: 传递市场状态给 Trader Agent，让它知道是否可以交易
    # 市场关闭时：可以评估和分析，但不能生成订单
    # 市场开放时：可以评估、分析和交易
    # CRITICAL FIX: 更清晰的日志显示市场状态
    market_status = "OPEN (simulation)" if is_market_open_for_simulation and not is_market_open else ("OPEN" if is_market_open else "CLOSED")
    print(f"[TRADING CYCLE] ===== STEP 4: TRADER AGENT ======")
    print(f"[TRADING CYCLE] Calling Trader Agent with is_market_open={is_market_open_for_simulation} (actual market: {market_status}, is_market_open={is_market_open})")
    print(f"[TRADING CYCLE] Parameters:")
    print(f"  - portfolio_value: ${portfolio_value:,.2f}")
    print(f"  - available_cash: ${available_cash_for_trading:,.2f} (LLM can decide how to use, but cannot exceed this amount)")
    print(f"  - current_positions: {len(current_positions_info) if current_positions_info else 0}")
    print(f"  - enriched_market keys: {list(enriched_market.keys())[:5] if isinstance(enriched_market, dict) else 'N/A'}...")
    print(f"  - convo keys: {list(convo.keys())[:5] if isinstance(convo, dict) else 'N/A'}...")
    
    # CRITICAL FIX: 添加 try-except 来捕获 run_trader 的异常，避免整个流程中断
    try:
        decision = run_trader(
            market=market_view,
            mview=enriched_market,
            rview=risk_report,  # 传入 Risk Report
            convo=convo,
            last_prices=last_prices,
            current_positions=current_positions_info if current_positions_info else None,
            portfolio_value=portfolio_value,
            position_config=position_config,  # 传入仓位配置
            available_cash=available_cash_for_trading,  # 传入可用现金
            is_market_open=is_market_open_for_simulation,  # CRITICAL: 传递市场状态，让agent知道是否可以交易
        )
        print(f"[TRADING CYCLE] ✅ Trader Agent completed successfully")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[TRADING CYCLE] ❌ ERROR: Trader Agent failed with exception: {e}")
        print(f"[TRADING CYCLE] ❌ Traceback:\n{error_trace}")
        # CRITICAL: 即使 Trader Agent 失败，也要创建一个默认的 decision，确保流程继续
        print(f"[TRADING CYCLE] ⚠️  Creating fallback decision due to Trader Agent failure")
        decision = {
            "action": "HOLD",
            "targets": [],
            "buy_orders": [],
            "sell_orders": [],
            "rationale": f"Trader Agent failed: {str(e)}",
            "summary": f"Trader Agent encountered an error and could not generate trading decisions. Error: {str(e)}",
            "stance": "neutral",
            "vix_risk": 0.0,
            "risk_compliance": {
                "position_limits_ok": True,
                "diversification_ok": True,
                "warnings": [f"Trader Agent error: {str(e)}"],
            },
        }
    
    # 注意：Trader Agent 的 conversation entry 将在订单创建后写入，以便反映实际创建的订单数量
    # 先保存 summary 和 stance，稍后更新
    trader_summary_original = decision.get("summary", decision.get("rationale", ""))
    trader_stance = decision.get("stance", "neutral")
    
    # 初始化实际订单计数器
    actual_buy_orders_count = 0
    actual_sell_orders_count = 0
    
    # Debug: Log decision content
    buy_orders_count = len(decision.get("buy_orders", []))
    sell_orders_count = len(decision.get("sell_orders", []))
    print(f"[TRADING CYCLE] Trader decision: {buy_orders_count} buy orders, {sell_orders_count} sell orders")
    print(f"[TRADING CYCLE] Market status check: is_market_open_for_simulation={is_market_open_for_simulation}, is_market_open={is_market_open}")
    if not is_market_open_for_simulation and (buy_orders_count > 0 or sell_orders_count > 0):
        print(f"[TRADING CYCLE] WARNING: Market is closed but Trader Agent generated {buy_orders_count} buy and {sell_orders_count} sell orders!")
        print(f"[TRADING CYCLE] This should not happen - Trader Agent should return empty orders when market is closed.")
        # CRITICAL FIX: 如果市场关闭但Trader Agent仍然生成了订单，强制清空订单列表
        print(f"[TRADING CYCLE] WARNING: FORCING: Clearing orders because market is closed.")
        decision["buy_orders"] = []
        decision["sell_orders"] = []
        decision["targets"] = []
        decision["action"] = "HOLD"
        buy_orders_count = 0
        sell_orders_count = 0
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
            # CRITICAL FIX: 移除 signal_score 自动排序和筛选
            # signal_score 现在由 agent 自行判断，不再自动计算和排序
            stocks = enriched_market.get("stocks", {})
            stocks_count = len([s for s, d in stocks.items() if isinstance(d, dict)])
            print(f"[TRADING CYCLE] Debug: {stocks_count} stocks available for agent analysis (signal_score judgment by agents)")
    
    # Process trading decisions (only if no existing pending orders, or in multi-day simulation)
    # CRITICAL FIX: 在实时模式下，额外检查今天是否已经有pending或filled订单
    # 如果有，就不应该再创建新订单，避免每小时重复创建
    # CRITICAL FIX: 市场关闭时，不允许创建订单
    should_create_orders = False
    if end is not None:
        # 多日模拟模式：允许创建订单（假设市场开放）
        # CRITICAL FIX: 即使有end参数，也要检查市场是否真的开放
        # 只有在多日模拟且市场开放时才允许创建订单
        if is_market_open_for_simulation:
            should_create_orders = True
        else:
            print(f"[TRADING CYCLE] ⚠️ WARNING: end parameter provided but market is closed. Skipping order creation.")
            should_create_orders = False
    elif is_market_open_for_simulation:
        # 实时模式：只有在市场开放时才检查是否可以创建订单
        # CRITICAL FIX: 再次确认市场状态（双重检查，避免误判）
        # NOTE: 双重检查可能导致误判，如果 is_market_open_for_simulation=True 但双重检查显示关闭
        # 这可能是因为时区问题或时间判断的微小差异
        # 为了更可靠，我们优先信任 is_market_open_for_simulation（它已经在前面检查过了）
        from src.utils.trading_days import is_market_open as double_check_market
        market_open_double_check = double_check_market(None)
        
        # CRITICAL FIX: 如果双重检查显示关闭，但 is_market_open_for_simulation=True，记录警告但继续
        # 因为 is_market_open_for_simulation 已经在前面经过检查，更可靠
        if not market_open_double_check:
            print(f"[TRADING CYCLE] ⚠️  WARNING: Double-check shows market is closed, but is_market_open_for_simulation=True")
            print(f"[TRADING CYCLE] ⚠️  This may be a timing issue. Continuing with is_market_open_for_simulation=True")
            # 不设置 should_create_orders = False，继续检查其他条件
        elif not existing_pending_orders:
            # 检查今天是否已经有filled订单
            # CRITICAL: Use project root data/logs directory explicitly
            filled_file = _get_project_logs_dir() / "filled_orders.jsonl"
            today_has_any_orders = False
            if filled_file.exists():
                try:
                    with filled_file.open("r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                filled_order = json.loads(line)
                                if _get_order_date(filled_order) == today:
                                    today_has_any_orders = True
                                    break
                except Exception:
                    pass
            
            # 如果今天没有任何订单（pending或filled），才允许创建新订单
            should_create_orders = not today_has_any_orders
            if today_has_any_orders:
                print(f"[TRADING CYCLE] ⚠️ Today already has orders (filled or pending). Skipping new order creation to prevent hourly duplicates.")
            else:
                print(f"[TRADING CYCLE] ✅ Market is open and no existing orders - will create new orders")
        else:
            # 有pending订单，不创建新订单
            should_create_orders = False
            print(f"[TRADING CYCLE] ⚠️  Existing pending orders found, skipping new order creation")
    else:
        # 市场关闭：不允许创建订单
        should_create_orders = False
        print(f"[TRADING CYCLE] ⚠️  Market is closed. Skipping order creation (should_create_orders=False).")
    
    if should_create_orders:
        # === OPTIMIZATION: Position limits (移除 cooldown 检查) ===
        from src.utils.config_loader import load_config
        
        # Load configuration for limits
        config = load_config()
        MAX_POSITIONS = config.get("max_positions", 10)  # Maximum number of different stocks
        # 移除 TRADE_COOLDOWN_HOURS（不再使用冷却期限制）
        # TRADE_COOLDOWN_HOURS = config.get("trade_cooldown_hours", 24.0)  # 已移除
        
        # CRITICAL FIX: 根据模式决定是否应用现金储备
        position_limit_mode = config.get("position_limit_mode", "auto")
        min_cash_reserve_ratio = config.get("min_cash_reserve_ratio")
        
        # 移除 trade history tracker（不再需要冷却期检查）
        # trade_history = TradeHistoryTracker(root="data/logs")  # 已移除
        
        # Check current position count
        current_position_count = len(portfolio._positions)
        portfolio_value = portfolio.value(last_prices)
        
        # CRITICAL FIX: 计算可用现金（根据模式决定是否应用现金储备）
        if position_limit_mode == "auto" or min_cash_reserve_ratio is None:
            # Auto模式：不应用现金储备限制，但可用现金仍然限制在实际现金范围内
            available_for_trading = portfolio.cash
            print(f"[OPTIMIZATION] Position limits: {current_position_count}/{MAX_POSITIONS} positions, "
                  f"Available cash: ${available_for_trading:.2f} (no reserve, LLM autonomous but limited to actual cash)")
        else:
            # Configured模式：应用现金储备限制
            MIN_CASH_RESERVE_RATIO = float(min_cash_reserve_ratio)
            required_cash_reserve = portfolio_value * MIN_CASH_RESERVE_RATIO
            available_for_trading = max(0, portfolio.cash - required_cash_reserve)
            print(f"[OPTIMIZATION] Position limits: {current_position_count}/{MAX_POSITIONS} positions, "
                  f"Available cash: ${available_for_trading:.2f} (reserve: ${required_cash_reserve:.2f}, ratio: {MIN_CASH_RESERVE_RATIO:.1%})")
        
        # 掛單策略：將所有訂單先掛單，收盤後再檢查成交
        buy_orders = decision.get("buy_orders", [])
        
        # Filter buy orders based on optimization rules
        # 移除硬条件限制：不再检查 cooldown 和 max_orders_per_cycle
        # 只保留现金检查（这是必要的安全措施）
        filtered_buy_orders = []
        for order in buy_orders:
            symbol = order.get("symbol")
            
            # Check 1: Position limit (保留，但只检查是否已有持仓，不限制数量)
            if current_position_count >= MAX_POSITIONS:
                # Check if we already have this position
                if symbol not in portfolio._positions:
                    # 如果已达到最大持仓数且没有该股票持仓，跳过
                    # 但如果已有该股票持仓，允许加仓
                    execution_errors.append(f"BUY {symbol} skipped: max positions reached ({current_position_count}/{MAX_POSITIONS})")
                    continue
            
            # 移除 Check 2: Cooldown period（不再检查冷却期）
            # can_trade, hours_remaining = trade_history.can_trade(symbol, TRADE_COOLDOWN_HOURS)
            # if not can_trade:
            #     execution_errors.append(f"BUY {symbol} skipped: cooldown period active ({hours_remaining:.1f} hours remaining)")
            #     continue
            
            filtered_buy_orders.append(order)
        
        # 按优先级排序（可以根据 signal_score 或其他指标排序）
        # 这里先按照 buy_price * quantity（金额）排序，确保资金充足时优先买入
        from math import floor
        
        # 移除订单数量限制：不再限制 max_orders_per_cycle
        # MAX_ORDERS_PER_CYCLE = config.get("max_orders_per_cycle", 20)
        buy_orders_sorted = sorted(filtered_buy_orders, key=lambda x: x.get("total_cost", 0.0), reverse=True)
        # buy_orders_sorted = buy_orders_sorted[:MAX_ORDERS_PER_CYCLE]  # 移除限制
        
        # if len(filtered_buy_orders) > MAX_ORDERS_PER_CYCLE:
        #     print(f"[OPTIMIZATION] Limited buy orders from {len(filtered_buy_orders)} to {MAX_ORDERS_PER_CYCLE} (max_orders_per_cycle)")
        
        # 掛單策略：開盤前掛限價單（使用更合理的限价策略）
        # CRITICAL: 累计跟踪已使用的现金，确保订单总金额不超过可用现金
        remaining_cash = available_for_trading  # 剩余可用现金（动态更新）
        
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
                    # 使用更合理的限价策略：使用 buy_price（当前价格+0.2%）作为限价，允许小幅溢价提高成交率
                    # 如果 buy_price 不在范围内，使用 buy_price_max（当前价格+0.5%）
                    limit_price = min(buy_price, buy_price_max) if buy_price <= buy_price_max else buy_price_max
                    estimated_cost = limit_price * quantity
                    
                    # Check 3: Cash reserve (use remaining_cash instead of initial available_for_trading)
                    # CRITICAL: 使用剩余现金，而不是初始可用现金
                    if estimated_cost > remaining_cash:
                        # 現金不足（考慮保留比例），減少數量
                        max_affordable_qty = floor(remaining_cash / limit_price)
                        if max_affordable_qty > 0:
                            quantity = max_affordable_qty
                            total_cost = limit_price * quantity
                            estimated_cost = total_cost
                            print(f"[OPTIMIZATION] Reduced {symbol} quantity to {quantity} due to cash reserve limit (remaining cash: ${remaining_cash:.2f})")
                        else:
                            execution_errors.append(f"BUY {symbol} skipped: insufficient cash after reserve (need ${estimated_cost:.2f}, remaining ${remaining_cash:.2f})")
                            continue
                    
                    # CRITICAL FIX: 市价交易 - 获取当前价格并立即成交
                    # 只在市场开盘时执行市价交易（使用is_market_open_for_simulation检查）
                    if not is_market_open_for_simulation:
                        execution_errors.append(f"BUY {symbol} skipped: market is closed (market orders only execute during trading hours)")
                        continue
                    
                    # CRITICAL FIX: 获取当前市价 - 优先使用实时价格，fallback到last_prices中的价格
                    # 不使用buy_price（+0.2%），确保成本价格接近市价
                    import yfinance as yf
                    current_price = None
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.fast_info
                        current_price = info.get("lastPrice") or info.get("regularMarketPrice")
                        if current_price:
                            current_price = float(current_price)
                            print(f"[MARKET ORDER] Got real-time price for {symbol}: ${current_price:.2f}")
                    except Exception as e:
                        print(f"[MARKET ORDER] Warning: Failed to get real-time price for {symbol}: {e}")
                    
                    # CRITICAL FIX: 如果获取实时价格失败，使用last_prices中的价格（而不是buy_price）
                    if current_price is None or current_price <= 0:
                        # 优先使用last_prices中的价格（这是从market_view获取的最新价格）
                        current_price = last_prices.get(symbol)
                        if current_price and current_price > 0:
                            print(f"[MARKET ORDER] Using last_prices for {symbol}: ${current_price:.2f}")
                        else:
                            # 最后fallback到buy_price（但应该很少发生）
                            current_price = buy_price
                            print(f"[MARKET ORDER] Warning: Using buy_price as last resort for {symbol}: ${current_price:.2f}")
                    
                    # 使用当前市价重新计算成本和数量
                    estimated_cost = current_price * quantity
                    
                    # CRITICAL: 使用实际portfolio.cash检查，确保现金同步
                    # 双重检查：确保remaining_cash和portfolio.cash都足够
                    if estimated_cost > portfolio.cash:
                        max_affordable_qty = floor(portfolio.cash / current_price)
                        if max_affordable_qty > 0:
                            quantity = max_affordable_qty
                            estimated_cost = current_price * quantity
                            print(f"[MARKET ORDER] Reduced {symbol} quantity to {quantity} due to cash limit (portfolio cash: ${portfolio.cash:.2f})")
                        else:
                            execution_errors.append(f"BUY {symbol} skipped: insufficient cash (need ${estimated_cost:.2f}, portfolio cash: ${portfolio.cash:.2f})")
                            continue
                    
                    # CRITICAL FIX: 同步remaining_cash和portfolio.cash
                    # 如果remaining_cash和portfolio.cash不同步，使用portfolio.cash（更准确）
                    if remaining_cash > portfolio.cash:
                        remaining_cash = portfolio.cash
                        print(f"[CASH SYNC] Synced remaining_cash to portfolio.cash: ${remaining_cash:.2f}")
                    
                    # 最终检查：确保有足够现金（使用更保守的值）
                    final_check_cash = min(remaining_cash, portfolio.cash)
                    if estimated_cost > final_check_cash:
                        max_affordable_qty = floor(final_check_cash / current_price)
                        if max_affordable_qty > 0:
                            quantity = max_affordable_qty
                            estimated_cost = current_price * quantity
                            print(f"[MARKET ORDER] Final reduction: {symbol} quantity to {quantity} (final check cash: ${final_check_cash:.2f})")
                        else:
                            execution_errors.append(f"BUY {symbol} skipped: insufficient cash after final check (need ${estimated_cost:.2f}, available: ${final_check_cash:.2f})")
                            continue
                    
                    # CRITICAL FIX: 在调用portfolio.buy()之前，再次使用实际计算值检查现金
                    # 使用实际的计算值：quantity * current_price（与portfolio.buy()内部计算一致）
                    actual_cost = quantity * current_price
                    if actual_cost > portfolio.cash:
                        # 如果实际成本超过现金，再次减少数量
                        max_affordable_qty = floor(portfolio.cash / current_price)
                        if max_affordable_qty > 0:
                            quantity = max_affordable_qty
                            actual_cost = current_price * quantity
                            estimated_cost = actual_cost
                            print(f"[MARKET ORDER] Last-minute reduction: {symbol} quantity to {quantity} (actual cost: ${actual_cost:.2f}, portfolio cash: ${portfolio.cash:.2f})")
                        else:
                            execution_errors.append(f"BUY {symbol} skipped: insufficient cash for actual cost (need ${actual_cost:.2f}, portfolio cash: ${portfolio.cash:.2f})")
                            print(f"[MARKET ORDER] ERROR: Cannot afford even 1 share of {symbol} (price: ${current_price:.2f}, cash: ${portfolio.cash:.2f})")
                            continue
                    
                    # CRITICAL: 先执行交易，成功后再创建订单
                    # 如果portfolio.buy()失败（现金不足），不应该创建订单
                    try:
                        # 更新投资组合（立即执行交易）
                        portfolio.buy(symbol, quantity, current_price)
                    except ValueError as e:
                        # 如果portfolio.buy()失败（通常是现金不足），跳过这个订单
                        error_msg = str(e)
                        execution_errors.append(f"BUY {symbol} skipped: portfolio.buy() failed - {error_msg}")
                        print(f"[MARKET ORDER] ERROR: portfolio.buy() failed for {symbol}: {error_msg}")
                        print(f"[MARKET ORDER] DEBUG: quantity={quantity}, current_price=${current_price:.2f}, cost=${actual_cost:.2f}, portfolio.cash=${portfolio.cash:.2f}")
                        continue
                    
                    # 交易成功后，扣除已使用的现金（用于跟踪）
                    # CRITICAL FIX: 使用实际成本（actual_cost）而不是estimated_cost，确保同步
                    remaining_cash -= actual_cost
                    print(f"[CASH TRACKING] Order for {symbol}: actual_cost=${actual_cost:.2f}, remaining cash=${remaining_cash:.2f}, portfolio cash=${portfolio.cash:.2f}")
                    
                    # 市价单：立即成交，不挂单
                    # 创建订单记录（标记为已成交）
                    placed_order = order_manager.place_order(
                        symbol=symbol,
                        action="BUY",
                        quantity=quantity,
                        limit_price=current_price,  # 市价单：使用当前价格
                        price_range={
                            "min": current_price,
                            "max": current_price,
                        },
                    )
                    
                    # 立即标记为已成交（市价单保证成交）
                    fill_result = {
                        "filled": True,
                        "fill_price": current_price,
                        "fill_reason": "Market order executed immediately at current price",
                        "daily_high": current_price,
                        "daily_low": current_price,
                        "current_price": current_price,
                    }
                    # CRITICAL: 确保订单标记为FILLED（市价单必须立即成交）
                    try:
                        order_manager.mark_order_filled(placed_order, fill_result)
                        # 确保订单状态是FILLED（双重保险）
                        placed_order["status"] = "FILLED"
                    except Exception as e:
                        # 如果mark_order_filled失败，手动设置状态为FILLED并移除pending
                        print(f"[MARKET ORDER] WARNING: mark_order_filled failed for {symbol}, manually setting status to FILLED: {e}")
                        placed_order["status"] = "FILLED"
                        placed_order["fill_price"] = current_price
                        placed_order["fill_reason"] = "Market order executed immediately at current price"
                        # CRITICAL: 使用UTC时区，ISO 8601格式，包含Z后缀
                        placed_order["filled_at"] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                        placed_order["fill_result"] = fill_result
                        
                        # CRITICAL: 手动从pending中移除并写入filled
                        try:
                            # 1. 写入filled_orders.jsonl（使用order_manager的路径）
                            filled_file = order_manager.filled_orders_file
                            with filled_file.open("a", encoding="utf-8") as f:
                                f.write(json.dumps(placed_order, ensure_ascii=False) + "\n")
                            
                            # 2. 从pending_orders.jsonl中移除（使用order_manager的路径）
                            pending_file = order_manager.pending_orders_file
                            if pending_file.exists():
                                all_pending = []
                                with pending_file.open("r", encoding="utf-8") as f:
                                    for line in f:
                                        if line.strip():
                                            try:
                                                o = json.loads(line)
                                                if o.get("order_id") != placed_order.get("order_id"):
                                                    all_pending.append(o)
                                            except:
                                                pass
                                
                                with pending_file.open("w", encoding="utf-8") as f:
                                    for o in all_pending:
                                        f.write(json.dumps(o, ensure_ascii=False) + "\n")
                            
                            print(f"[MARKET ORDER] Manually moved {symbol} order to filled_orders.jsonl and removed from pending")
                        except Exception as e2:
                            print(f"[MARKET ORDER] ERROR: Failed to manually process order: {e2}")
                            import traceback
                            traceback.print_exc()
                    
                    placed_orders.append(placed_order)
                    new_orders_count += 1  # 记录新创建的BUY订单
                    
                    # 记录已成交的交易
                    executed_trades.append({
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": quantity,
                        "price": current_price,
                        "amount": estimated_cost,
                        "status": "FILLED",
                        "order_id": placed_order.get("order_id"),
                    })
                    
                    print(f"[MARKET ORDER] BUY {symbol} x{quantity} @ ${current_price:.2f} (FILLED immediately, cost=${estimated_cost:.2f}, remaining_cash=${remaining_cash:.2f})")
                    
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
        
        # 打印现金使用总结
        total_orders_cost = available_for_trading - remaining_cash
        print(f"[CASH SUMMARY] Total orders cost: ${total_orders_cost:.2f}, Remaining cash: ${remaining_cash:.2f} (from ${available_for_trading:.2f} available)")
        
        # 记录实际创建的买入订单数量（用于更新 Trader Agent summary）
        # CRITICAL FIX: 只统计新创建的BUY订单，不包括existing_pending_orders
        # 由于BUY订单在SELL订单之前创建，我们可以通过计算BUY订单数量来得到
        # 只统计在should_create_orders=True时创建的BUY订单
        if should_create_orders:
            actual_buy_orders_count = len([o for o in placed_orders if o.get("action") == "BUY" and o.get("order_id")])  # 新创建的BUY订单都有order_id
        else:
            actual_buy_orders_count = 0  # 没有创建新订单
        
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
                    
                    # CRITICAL FIX: 市价交易 - 获取当前价格并立即成交
                    # 只在市场开盘时执行市价交易（使用is_market_open_for_simulation检查）
                    if not is_market_open_for_simulation:
                        execution_errors.append(f"SELL {symbol} skipped: market is closed (market orders only execute during trading hours)")
                        continue
                    
                    # CRITICAL FIX: 获取当前市价 - 优先使用实时价格，fallback到last_prices中的价格
                    # 不使用sell_price（+0.5%），确保成交价格接近市价
                    import yfinance as yf
                    current_price = None
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.fast_info
                        current_price = info.get("lastPrice") or info.get("regularMarketPrice")
                        if current_price:
                            current_price = float(current_price)
                            print(f"[MARKET ORDER] Got real-time price for {symbol}: ${current_price:.2f}")
                    except Exception as e:
                        print(f"[MARKET ORDER] Warning: Failed to get real-time price for {symbol}: {e}")
                    
                    # CRITICAL FIX: 如果获取实时价格失败，使用last_prices中的价格（而不是sell_price）
                    if current_price is None or current_price <= 0:
                        # 优先使用last_prices中的价格（这是从market_view获取的最新价格）
                        current_price = last_prices.get(symbol)
                        if current_price and current_price > 0:
                            print(f"[MARKET ORDER] Using last_prices for {symbol}: ${current_price:.2f}")
                        else:
                            # 最后fallback到sell_price（但应该很少发生）
                            current_price = sell_price
                            print(f"[MARKET ORDER] Warning: Using sell_price as last resort for {symbol}: ${current_price:.2f}")
                    
                    # 市价单：使用当前价格
                    limit_price = current_price
                    total_proceeds = current_price * quantity
                    
                    # CRITICAL FIX: 先检查持仓，再创建订单和执行交易
                    # 检查持仓是否足够
                    current_position = portfolio.get_position(symbol)
                    if not current_position or current_position.quantity < quantity:
                        available_qty = current_position.quantity if current_position else 0
                        execution_errors.append(f"SELL {symbol} skipped: insufficient shares (need {quantity}, have {available_qty})")
                        continue
                    
                    # 市价单：立即成交，不挂单
                    # 先执行交易以获取realized_pnl（在创建订单前）
                    realized_pnl = portfolio.sell(symbol, quantity, current_price)
                    
                    # 交易成功后，创建订单记录（标记为已成交）
                    placed_order = order_manager.place_order(
                        symbol=symbol,
                        action="SELL",
                        quantity=quantity,
                        limit_price=current_price,  # 市价单：使用当前价格
                        price_range={
                            "min": current_price,
                            "max": current_price,
                        },
                    )
                    
                    # 立即标记为已成交（市价单保证成交）
                    fill_result = {
                        "filled": True,
                        "fill_price": current_price,
                        "fill_reason": "Market order executed immediately at current price",
                        "daily_high": current_price,
                        "daily_low": current_price,
                        "current_price": current_price,
                    }
                    # CRITICAL FIX: 传递realized_pnl给mark_order_filled，确保SELL订单正确记录已实现损益
                    # CRITICAL: 确保订单标记为FILLED（市价单必须立即成交）
                    try:
                        order_manager.mark_order_filled(placed_order, fill_result, realized_pnl=realized_pnl)
                        # 确保订单状态是FILLED（双重保险）
                        placed_order["status"] = "FILLED"
                    except Exception as e:
                        # 如果mark_order_filled失败，手动设置状态为FILLED并移除pending
                        print(f"[MARKET ORDER] WARNING: mark_order_filled failed for {symbol}, manually setting status to FILLED: {e}")
                        placed_order["status"] = "FILLED"
                        placed_order["fill_price"] = current_price
                        placed_order["fill_reason"] = "Market order executed immediately at current price"
                        # CRITICAL: 使用UTC时区，ISO 8601格式，包含Z后缀
                        placed_order["filled_at"] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                        placed_order["fill_result"] = fill_result
                        # 记录realized_pnl
                        if realized_pnl:
                            placed_order["realized_pnl"] = realized_pnl.get("realized_pnl", 0.0)
                            placed_order["realized_pnl_pct"] = realized_pnl.get("realized_pnl_pct", 0.0)
                            placed_order["cost_basis"] = realized_pnl.get("cost_basis", 0.0)
                            placed_order["proceeds"] = realized_pnl.get("proceeds", 0.0)
                        
                        # CRITICAL: 手动从pending中移除并写入filled
                        try:
                            # 1. 写入filled_orders.jsonl（使用order_manager的路径）
                            filled_file = order_manager.filled_orders_file
                            with filled_file.open("a", encoding="utf-8") as f:
                                f.write(json.dumps(placed_order, ensure_ascii=False) + "\n")
                            
                            # 2. 从pending_orders.jsonl中移除（使用order_manager的路径）
                            pending_file = order_manager.pending_orders_file
                            if pending_file.exists():
                                all_pending = []
                                with pending_file.open("r", encoding="utf-8") as f:
                                    for line in f:
                                        if line.strip():
                                            try:
                                                o = json.loads(line)
                                                if o.get("order_id") != placed_order.get("order_id"):
                                                    all_pending.append(o)
                                            except:
                                                pass
                                
                                with pending_file.open("w", encoding="utf-8") as f:
                                    for o in all_pending:
                                        f.write(json.dumps(o, ensure_ascii=False) + "\n")
                            
                            print(f"[MARKET ORDER] Manually moved {symbol} order to filled_orders.jsonl and removed from pending")
                        except Exception as e2:
                            print(f"[MARKET ORDER] ERROR: Failed to manually process order: {e2}")
                            import traceback
                            traceback.print_exc()
                    
                    placed_orders.append(placed_order)
                    new_orders_count += 1  # 记录新创建的SELL订单
                    
                    # 记录已成交的交易
                    executed_trades.append({
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": quantity,
                        "price": current_price,
                        "amount": total_proceeds,
                        "status": "FILLED",
                        "order_id": placed_order.get("order_id"),
                    })
                    
                    print(f"[MARKET ORDER] SELL {symbol} x{quantity} @ ${current_price:.2f} (FILLED immediately, proceeds=${total_proceeds:.2f})")
                    
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
        
        # 记录实际创建的卖出订单数量
        # CRITICAL FIX: 只统计新创建的SELL订单，不包括existing_pending_orders
        # 由于new_orders_count包含了所有新创建的订单（BUY+SELL），我们需要单独统计SELL
        # 但这里我们只统计在should_create_orders=True时创建的SELL订单
        # 如果should_create_orders=False，actual_sell_orders_count应该为0（因为没有创建新订单）
        if should_create_orders:
            actual_sell_orders_count = len([o for o in placed_orders if o.get("action") == "SELL" and o.get("order_id")])  # 新创建的SELL订单都有order_id
        else:
            actual_sell_orders_count = 0  # 没有创建新订单
    else:
        # CRITICAL FIX: 如果should_create_orders=False，确保actual_buy_orders_count和actual_sell_orders_count被正确设置
        # 这些变量已经在1219-1220行被初始化为0，但这里再次确认
        actual_buy_orders_count = 0
        actual_sell_orders_count = 0
        print(f"[TRADING CYCLE] Market closed or orders skipped - actual_buy_orders_count=0, actual_sell_orders_count=0")
    
    # CRITICAL FIX: 写入Trader Agent的conversation entry（无论should_create_orders是True还是False，都要写入）
    # 这确保即使市场关闭或没有创建订单，Trader Agent的决策也会被记录
    try:
        # CRITICAL FIX: 确保decision存在，如果为空则创建默认值
        if not decision:
            print(f"[TRADING CYCLE] ⚠️  WARNING: decision is None or empty, creating default decision")
            decision = {
                "action": "HOLD",
                "summary": "No trading decision generated",
                "rationale": "Trader agent did not generate a decision",
                "stance": "neutral",
                "buy_orders": [],
                "sell_orders": []
            }
        
        # CRITICAL FIX: 确保trader_summary_original和trader_stance有值
        if not trader_summary_original:
            trader_summary_original = decision.get("summary", decision.get("rationale", "No summary available"))
        if not trader_stance:
            trader_stance = decision.get("stance", "neutral")
        
        # 更新 summary 以反映实际创建的订单数量
        trader_summary = trader_summary_original if trader_summary_original else decision.get("summary", decision.get("rationale", "No summary available"))
        
        # 如果summary为空，使用decision中的其他字段
        if not trader_summary or trader_summary.strip() == "":
            trader_summary = decision.get("rationale", decision.get("summary", "No analysis provided"))
        
        # CRITICAL FIX: 如果所有字段都为空，使用默认值
        if not trader_summary or trader_summary.strip() == "":
            trader_summary = "Trader agent analysis completed but no summary provided"
            print(f"[TRADING CYCLE] ⚠️  WARNING: All summary fields are empty, using default message")
        
        if actual_buy_orders_count is not None:
            # 检查 summary 中是否包含订单数量信息
            import re
            # 匹配 "generating X buy orders" 或 "X buy orders" 等模式
            pattern = r'generating\s+(\d+)\s+buy\s+orders|(\d+)\s+buy\s+orders'
            match = re.search(pattern, trader_summary, re.IGNORECASE)
            if match:
                # 找到提到的订单数量
                mentioned_count = int(match.group(1) or match.group(2))
                if mentioned_count != actual_buy_orders_count:
                    # 替换为实际创建的订单数量
                    trader_summary = re.sub(
                        pattern,
                        f'generating {actual_buy_orders_count} buy orders',
                        trader_summary,
                        count=1,
                        flags=re.IGNORECASE
                    )
                    print(f"[TRADING CYCLE] Updated Trader Agent summary: {mentioned_count} -> {actual_buy_orders_count} buy orders")
        
        # CRITICAL FIX: 对话中只显示 summary，订单信息保留在 decision 对象中供系统使用
        buy_orders = decision.get("buy_orders", [])
        sell_orders = decision.get("sell_orders", [])
        
        # 对话内容只包含 summary（简洁显示）
        trader_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "date": trade_date_str,
            "agent": "TraderAgent",
            "round": 0,
            "content": f"Stance: {trader_stance}\n\nAnalysis: {trader_summary}",  # 只显示 summary
            "type": "discussion",
            "stance": trader_stance,
            "summary": trader_summary,  # CRITICAL FIX: 添加单独的 summary 字段供前端使用
            "tools_used": [],  # Trader Agent不使用工具，它是基于其他agent的分析做决策
            "decision": decision,  # CRITICAL: 完整的 decision 对象供系统使用（包含 buy_orders, sell_orders 等）
            "buy_orders_count": len(buy_orders),  # 订单数量统计
            "sell_orders_count": len(sell_orders),  # 订单数量统计
            "actual_buy_orders_created": actual_buy_orders_count,  # 实际创建的订单数量
            "actual_sell_orders_created": actual_sell_orders_count,  # 实际创建的订单数量
        }
        
        # CRITICAL FIX: 确保convo_file存在且可写
        if not convo_file:
            logs_dir = _get_project_logs_dir()
            convo_file = logs_dir / "discussion_actions.jsonl"
            print(f"[TRADING CYCLE] Convo file not defined, using default: {convo_file}")
        
        # 确保目录存在
        convo_file.parent.mkdir(parents=True, exist_ok=True)
        
        with convo_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trader_entry, ensure_ascii=False) + "\n")
        
        print(f"[TRADING CYCLE] ✅ Wrote Trader Agent conversation entry to {convo_file}")
        print(f"[TRADING CYCLE]   - Summary: {trader_summary[:100]}..." if len(trader_summary) > 100 else f"[TRADING CYCLE]   - Summary: {trader_summary}")
        print(f"[TRADING CYCLE]   - Stance: {trader_stance}")
        print(f"[TRADING CYCLE]   - Decision buy_orders: {len(buy_orders)}, sell_orders: {len(sell_orders)}")
        print(f"[TRADING CYCLE]   - Actual orders created: {actual_buy_orders_count} buy, {actual_sell_orders_count} sell")
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[TRADING CYCLE] ⚠️  Failed to write Trader Agent conversation entry: {e}")
        print(f"[TRADING CYCLE] ⚠️  Traceback: {error_trace}")
        # CRITICAL: 即使写入失败，也要继续执行，不要中断整个流程
    
    # CRITICAL FIX: 保存 portfolio 状态（无论是否有订单都要保存）
    # 确保portfolio状态始终是最新的（包括持仓价格变化、现金变化等）
    # 即使没有订单，也要保存portfolio状态（因为持仓价格可能变化）
    if portfolio:
        try:
            # json 已在文件顶部导入
            portfolio_file = _get_project_logs_dir() / "portfolio_state.json"
            
            # 计算 total_value（现金 + 持仓市值）
            equity_value = portfolio.equity_value(last_prices) if last_prices else 0.0
            total_value = portfolio.cash + equity_value
            
            portfolio_state = {
                "cash": portfolio.cash,
                "initial_value": portfolio.initial_value,
                "total_value": total_value,
                "positions": {},
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "snapshot": {
                    "cash": portfolio.cash,
                    "total_value": total_value,
                    "equity_value": equity_value,
                    "positions_count": len(portfolio._positions),
                }
            }
            
            for symbol, pos in portfolio._positions.items():
                portfolio_state["positions"][symbol] = {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": pos.total_cost if hasattr(pos, 'total_cost') and pos.total_cost > 0 else pos.avg_cost * pos.quantity,
                }
            
            portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
            if actual_buy_orders_count > 0 or actual_sell_orders_count > 0:
                print(f"[TRADING CYCLE] Saved portfolio state after order execution ({actual_buy_orders_count} buy, {actual_sell_orders_count} sell orders)")
            else:
                print(f"[TRADING CYCLE] Saved portfolio state (no new orders, {len(portfolio._positions)} positions, total_value=${total_value:.2f})")
        except Exception as e:
            print(f"[TRADING CYCLE] ⚠️  Failed to save portfolio state: {e}")
    
    # ---- (5b) 檢查並結算今天的 PENDING 訂單（如果市場開盤，或在多日模擬中）----
    # 在多日模拟中（end参数提供），也执行订单
    # 条件：1) 市场开盘且是今天，或 2) 提供了end参数（多日模拟）
    # CRITICAL FIX: 使用 is_market_open_for_simulation 而不是 is_market_open，确保市场关闭时不执行
    should_settle_orders = (is_market_open_for_simulation and today == date.today().isoformat()) or (end is not None)
    if should_settle_orders:
        try:
            # Path 已经在文件顶部导入，不需要重新导入
            # CRITICAL FIX: json 已在文件顶部导入，不需要重复导入
            
            # 加载当前 portfolio 状态
            # CRITICAL: Use project root data/logs directory explicitly
            portfolio_file = _get_project_logs_dir() / "portfolio_state.json"
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
                            # CRITICAL FIX: 只有在市场开盘时才使用实时价格，市场关闭时不执行订单
                            use_realtime_for_check = (end is None) and (today == date.today().isoformat()) and is_market_open_for_simulation
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
                                    realized_pnl = None
                                    if action == "BUY":
                                        current_portfolio.buy(symbol, quantity, fill_price)
                                    elif action == "SELL":
                                        # 卖出时计算已实现损益
                                        realized_pnl = current_portfolio.sell(symbol, quantity, fill_price)
                                        print(f"[TRADING CYCLE] Realized P&L: ${realized_pnl['realized_pnl']:.2f} ({realized_pnl['realized_pnl_pct']:+.2f}%)")
                                    
                                    # 标记订单为已成交（传递已实现损益，仅SELL订单有值）
                                    order_manager.mark_order_filled(order, fill_result, realized_pnl=realized_pnl)
                                    settled_count += 1
                                    print(f"[TRADING CYCLE] Order {order_id} executed successfully")
                        except Exception as e:
                            print(f"[TRADING CYCLE] Error processing order {order_id}: {e}")
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
                        print(f"[TRADING CYCLE] Settled {settled_count} orders, portfolio updated")
                        
                        # CRITICAL: 更新传入的 portfolio 参数，确保后续计算使用最新状态
                        # 这样在多日模拟中，Day 2+ 能正确加载更新后的持仓
                        if portfolio:
                            portfolio.cash = current_portfolio.cash
                            portfolio.initial_value = current_portfolio.initial_value
                            portfolio._positions = current_portfolio._positions.copy()
                            print(f"[TRADING CYCLE] Updated portfolio parameter with executed orders")
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
        
        # CRITICAL: Use project root data/logs directory explicitly
        memory_manager = MemoryManager(root=str(_get_project_logs_dir()))
        # CRITICAL: Use project root data/logs directory explicitly
        equity_tracker = EquityTracker(root=str(_get_project_logs_dir()))
        
        # 使用 end 日期作为今天的日期（如果 end 是 None，使用当前日期）
        # 在多日模拟中，end 就是当天的日期，应该使用 end 来记录净值
        # 这样可以确保每天使用不同的日期记录净值
        # CRITICAL FIX: Ensure equity_date is always a string (YYYY-MM-DD format)
        # Handle all possible types: date, str, datetime, or None
        if end:
            if isinstance(end, date):
                equity_date = end.isoformat()
            elif isinstance(end, datetime):
                equity_date = end.date().isoformat()
            elif isinstance(end, str):
                # Ensure it's in YYYY-MM-DD format (remove time part if present)
                equity_date = end.split('T')[0].split(' ')[0]
            else:
                equity_date = date.today().isoformat()
        else:
            equity_date = date.today().isoformat()
        
        # CRITICAL FIX: Double-check that equity_date is a string before passing to functions
        if not isinstance(equity_date, str):
            equity_date = str(equity_date) if hasattr(equity_date, 'isoformat') else date.today().isoformat()
        
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
        # CRITICAL FIX: 确保 positions_detail 字段存在，equity_tracker 需要它
        if "positions_detail" not in portfolio_snapshot:
            portfolio_snapshot["positions_detail"] = updated_positions_info
        
        equity_tracker.record_daily_equity(
            date_str=equity_date,
            portfolio_snapshot=portfolio_snapshot,
        )
        print(f"[EQUITY] Recorded equity for {equity_date}: ${portfolio_value:.2f} (cash: ${portfolio.cash:.2f}, equity: ${equity_value:.2f})")
    except Exception as e:
        print(f"[MEMORY WARN] Failed to save memory/equity: {e}")
        # 不影响主流程，继续执行
    
    # ---- 内存清理：交易循环结束后清理临时数据 ----
    # 这里可以添加其他内存清理逻辑（如果需要）
    import gc
    gc.collect()  # 强制垃圾回收，释放未使用的内存
    print("[MEMORY] Trading cycle completed, memory cleaned")

    # CRITICAL: 确保 coordinator_summary 被包含在返回结果中
    # 即使 convo 中已有，也显式添加到 discussion 中以便前端访问
    discussion_result = dict(convo) if isinstance(convo, dict) else {}
    # CRITICAL FIX: Ensure optimization_stats is included in discussion_result
    if "optimization_stats" in convo:
        discussion_result["optimization_stats"] = convo["optimization_stats"]
    coordinator_summary = discussion_result.get("coordinator_summary")
    if coordinator_summary:
        # 确保 coordinator_summary 存在且有效
        if isinstance(coordinator_summary, dict):
            summary_text = coordinator_summary.get("summary", "")
            if not summary_text or len(summary_text.strip()) < 50:
                print(f"[TRADING CYCLE] ⚠️  Coordinator summary too short ({len(summary_text)} chars), may need improvement")
        print(f"[TRADING CYCLE] Coordinator summary included in result: {len(coordinator_summary.get('summary', '')) if isinstance(coordinator_summary, dict) else 0} chars")
    else:
        print(f"[TRADING CYCLE] ⚠️  WARNING: coordinator_summary not found in convo")
    
    # CRITICAL FIX: 计算实际的对话数量（从文件中读取，包括新写入的条目）
    conversations_count = 0
    try:
        if convo_file.exists():
            with convo_file.open('r', encoding='utf-8') as f:
                # 只计算今天日期的条目
                today_entries = [line for line in f if trade_date_str in line]
                conversations_count = len(today_entries)
                print(f"[TRADING CYCLE] Counted {conversations_count} conversations for {trade_date_str} from file")
    except Exception as e:
        print(f"[TRADING CYCLE] ⚠️  Failed to count conversations from file: {e}")
        # Fallback: 使用 convo 中的条目数（可能不准确）
        conversations_count = len(convo.get("entries", [])) if isinstance(convo, dict) else 0
    
    return {
        "stance": final_stance,  # 主要键名
        "final_stance": final_stance,  # CRITICAL FIX: 同时提供 final_stance 键以保持向后兼容
        "decision": decision,
        "risk_report": risk_report,
        "discussion": discussion_result,  # 添加完整的讨论信息（包含 transcript, actions, coordinator_summary 等）
        "rounds": convo.get("rounds") if isinstance(convo, dict) else 0,
        "conversations_count": conversations_count,  # CRITICAL FIX: 添加对话数量（从文件读取）
        "symbols": symbols,
        # CRITICAL FIX: top_signals 已移除，signal_score 由 agent 自行判断
        # "top_signals": signal_top,  # 不再使用
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
