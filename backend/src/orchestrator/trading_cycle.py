# src/orchestrator/trading_cycle.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, timedelta, datetime, timezone, time as dt_time
from pathlib import Path  # Import at file top to avoid scope issues from repeated imports in functions
import json  # For loading portfolio_state.json

# CRITICAL: Helper function to get project root data/logs directory
# This ensures all trading cycle operations use the same path regardless of working directory
def _get_project_logs_dir() -> Path:
    """Get the project root data/logs directory path."""
    _backend_dir = Path(__file__).resolve().parent.parent.parent  # backend/
    _project_root = _backend_dir.parent  # project root
    logs_dir = _project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

# --- Market: Batch price fetching + indicators ---
from src.tools.market_tools import fetch_market_batch

# --- Analyst Discussion: Use optimized parallel version (default) ---
# Note: multi_analyst_system_parallel internally uses functions from multi_analyst_system,
# so we don't import run_multi_analyst_discussion directly here
from src.agents.multi_analyst_system_parallel import run_multi_analyst_discussion_parallel

# --- Risk Analyst: Assess position risk (LLM-powered) ---
from src.agents.risk_analyst_llm import run_risk_analyst_llm

# --- Trader Agent: Trading decisions ---
from src.agents.trader_agent import run_trader

# --- Portfolio: Position management ---
from src.data.portfolio import Portfolio

# --- Trade Logger: Trade logging ---
from src.data.trade_log import TradeLogger

# --- Timestamp utilities ---
from src.utils.timestamp_utils import get_utc_timestamp


def _default_universe() -> List[str]:
    """
    Load complete stock universe (default: load from config.json)
    If universe field exists in config.json, use it; otherwise use minimal preset
    """
    try:
        # Try to load complete universe from config.json
        config_file = Path(__file__).parent.parent.parent / "config" / "config.json"
        if config_file.exists():
            with config_file.open("r", encoding="utf-8") as f:
                config_data = json.load(f)
                # universe field in config.json
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    symbols = config_data["universe"]
                    if symbols and len(symbols) > 0:
                        return symbols
        
        # Also try to load from universe.json (if exists)
        universe_file = Path(__file__).parent.parent.parent / "config" / "universe.json"
        if universe_file.exists():
            with universe_file.open("r", encoding="utf-8") as f:
                universe_data = json.load(f)
                # universe.json format may be {"nasdaq100": [...]} or directly a list
                if isinstance(universe_data, dict):
                    # Try different keys
                    for key in ["nasdaq100", "symbols", "universe", "stocks"]:
                        if key in universe_data and isinstance(universe_data[key], list):
                            symbols = universe_data[key]
                            if symbols and len(symbols) > 0:
                                return symbols
                elif isinstance(universe_data, list):
                    if len(universe_data) > 0:
                        return universe_data
    except Exception as e:
        print(f"[UNIVERSE WARN] Failed to load universe from config: {e}")
    
    # Fallback: Minimal preset (for testing only)
    print("[UNIVERSE WARN] Using minimal default universe (5 stocks)")
    return ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]


def _default_window() -> Tuple[str, str]:
    # Default: last 180 days
    end = date.today()
    start = end - timedelta(days=180)
    return (start.isoformat(), end.isoformat())


def _get_order_date(order: Dict[str, Any]) -> Optional[str]:
    """
    Extract date from order (prefer placed_at, compatible with old order_date field)
    
    Returns:
    - Order date (YYYY-MM-DD) or None
    """
    placed_at = order.get("placed_at", "")
    if placed_at:
        try:
            return datetime.fromisoformat(placed_at.replace('Z', '+00:00').replace('+00:00', '')).date().isoformat()
        except:
            pass
    # Compatible with old order_date field
    return order.get("order_date")


def _top_by_signal(stocks: Dict[str, Dict[str, float]], k: int = 5) -> List[Tuple[str, float]]:
    items: List[Tuple[str, float]] = []
    for s, d in (stocks or {}).items():
        try:
            sc = float(d.get("signal_score"))
        except Exception:
            sc = float("nan")
        items.append((s, sc))
    # NaN sorted last
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
    Daily trading flow (integrated with Portfolio and Risk Analyst):
      1) Market: Fetch universe OHLCV + indicators (fetch_market_batch)
      2) Analyst Discussion: Auto-complete missing info with tools (news_scan / vix_term / fear_greed)
      3) Risk Analyst: Assess current position risk, provide position control report
      4) Trader: Make BUY/HOLD/SELL recommendations based on final stance + VIX risk + Risk Report (including price and quantity)
      5) Execute trades: Update Portfolio and log to Trade Logger
    """

    # ---- Parameter defaults ----
    # CRITICAL FIX: Load config values first, then override with function parameters if provided
    from src.utils.config_loader import load_config
    config = load_config()
    
    # CRITICAL FIX: Load rounds from config.json
    # Always use config value if available, unless explicitly overridden
    # Note: In Python, we can't distinguish between default and explicit default value,
    # so we always check config and use it if different from default
    config_rounds = config.get("discussion_rounds", 3)
    if rounds == 3:  # Using default value, use config value instead
        rounds = config_rounds
    # CRITICAL FIX: Load auto_tools from config.json
    config_auto_tools = config.get("discussion_auto_tools", True)
    if auto_tools == True:  # Using default value, use config value instead
        auto_tools = config_auto_tools
    # CRITICAL FIX: Load tool_budget from config.json
    config_tool_budget = config.get("discussion_tool_budget", config.get("tool_budget", 15))
    if tool_budget == 8:  # Using default value, use config value instead
        tool_budget = config_tool_budget
    
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

    # ---- (1) Market layer ----
    # fetch_market_batch is a LangChain StructuredTool, need to use .invoke() to call
    # Note: fetch_market_batch only accepts symbols, start, end three parameters
    # CRITICAL: Ensure end parameter is set correctly (for fetching market data)
    # If end is None (real-time mode), use yesterday's date (because today's data may be incomplete)
    # If end is a specific date (planning mode), use that date
    market_data_end = end if end else (date.today() - timedelta(days=1)).isoformat()
    
    # CRITICAL FIX: If start == end (single-day query), automatically extend start to 7 days before
    # This ensures yfinance can correctly fetch data (single-day queries often fail)
    if start == market_data_end:
        end_dt = datetime.fromisoformat(market_data_end.split('T')[0]) if isinstance(market_data_end, str) else market_data_end
        start_dt = end_dt - timedelta(days=7)
        start = start_dt.isoformat().split('T')[0] if isinstance(start_dt, datetime) else str(start_dt)
    
    try:
        market_view: Dict[str, Any] = fetch_market_batch.invoke({
            "symbols": universe,
            "start": start,
            "end": market_data_end,
        })
        stocks_count = len(market_view.get('stocks', {}))
        if stocks_count < len(universe):
            # Show which stocks were not fetched
            fetched_symbols = set(market_view.get('stocks', {}).keys())
            missing_symbols = [s for s in universe if s not in fetched_symbols]
    except Exception as e:
        # If fetch fails, return error message
        raise Exception(f"Failed to fetch market data: {e}")
    # market_view typical structure:
    # {
    #   "stocks": {SYM: {price, change_pct, rsi14, macd, bb_pos, signal_score, ...}, ...},
    #   "vix": {"level": ..., "chg_1d": ..., "zscore": ...}
    # }

    # ---- (1b) Lightweight enriched data for discussion layer ----
    stocks = market_view.get("stocks") or {}
    symbols = list(stocks.keys())
    # CRITICAL FIX: Remove signal_score auto-sorting
    # signal_score is now judged by agents themselves, no longer auto-calculated and sorted
    # Still keep signal_score field (calculated in market_tools.py), but no longer used for auto-filtering
    signal_top = []  # No longer using signal_score sorting
    
    # ---- (1c) Market Analyst: Evaluate all universe stocks, generate recommendation list ----
    # CRITICAL FIX: Use fallback recommendations (actual recommendations will be generated by LLM in multi_analyst_system)
    from src.tools.market_analyst import run_market_analyst
    market_analysis = run_market_analyst(market_view)
    recommended_stocks_fallback = market_analysis.get("recommended_stocks", [])

    enriched_market: Dict[str, Any] = {
        "symbols": symbols,
        # Let discussion auto-complete: vix_term / fear_greed / news
        "vix_term": market_view.get("vix_term"),      # If calculated in market layer later, can also be passed in
        "fear_greed": market_view.get("fear_greed"),
        "news": None,
        # CRITICAL FIX: signal_score_top removed, signal_score judged by agent itself
        # "signal_score_top": signal_top,  # No longer used
        "stocks": stocks,
        "vix": market_view.get("vix"),
        "recommended_stocks": recommended_stocks_fallback,  # Fallback recommendations (actual recommendations will be updated in multi_analyst_system)
        "market_sentiment": market_analysis.get("market_sentiment", "neutral"),  # Add market sentiment
    }

    # ---- Initialize Portfolio and Trade Logger (if not provided) ----
    if portfolio is None:
        # CRITICAL: Try to load existing state from portfolio_state.json, instead of creating new empty Portfolio
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
                # Restore positions
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
            except Exception as e:
                portfolio = Portfolio()
        else:
            portfolio = Portfolio()
    if trade_logger is None:
        # CRITICAL FIX: Use project root data/logs directory explicitly (same as OrderManager)
        trade_logger = TradeLogger(root=str(_get_project_logs_dir()))

    # ---- Latest closing price (used in multiple places) ----
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

    # ---- (1.5) Load historical memories (short and long term) ----
    historical_memories = []
    try:
        from src.data.memory_manager import MemoryManager
        # CRITICAL: Use project root data/logs directory explicitly
        memory_manager = MemoryManager(root=str(_get_project_logs_dir()))
        # Load memory summaries from last 5 days (short-term memory)
        historical_memories = memory_manager.load_recent_memories(
            days=5,
            end_date=end if end else None,
            summary_only=True,  # Only load summaries, reduce prompt length
        )
        if historical_memories:
            print(f"[MEMORY] ✅ Loaded {len(historical_memories)} historical memories for context")
        else:
            print(f"[MEMORY] ⚠️ No historical memories found (agents should use memory tools to retrieve past decisions)")
    except Exception as e:
        print(f"[MEMORY WARN] Failed to load historical memories: {e}")
        # Does not affect main flow, continue execution

    # ---- (2) Check current order status (pass to agent) ----
    from src.data.order_manager import OrderManager
    # CRITICAL: Use project root data/logs directory explicitly
    order_manager = OrderManager(root=str(_get_project_logs_dir()))
    
    # Check if market is open (for determining order date, exclude weekends and holidays)
    # CRITICAL FIX: Pass None to let function directly get Eastern time, avoid timezone conversion errors
    from src.utils.trading_days import is_market_open as check_market_open
    now = datetime.now()
    is_market_open = check_market_open(None)  # Pass None to directly get Eastern time
    
    # Determine order date to check
    if end:
        order_date = end
    elif is_market_open:
        order_date = date.today().isoformat()
    else:
        # After market close: check tomorrow's orders
        tomorrow = date.today() + timedelta(days=1)
        while tomorrow.weekday() >= 5:
            tomorrow += timedelta(days=1)
        order_date = tomorrow.isoformat()
    
    # Get pending and filled orders
    pending_orders = order_manager.load_pending_orders(order_date=order_date)
    
    # Get filled orders
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
    
    # Prepare order status information
    order_status = {
        "pending_count": len(pending_orders),
        "filled_count": len(filled_orders),
        "pending_orders": pending_orders,
        "filled_orders": filled_orders,
        "order_date": order_date,
    }
    
    # ---- (3) Multi-Analyst discussion layer ----
    # Run multiple specialized analysts: Market, Technical, Fundamental, Sentiment
    # Note: Prepare position information here first (before order settlement), but will update after order settlement
    # To ensure discussion system can also see current positions, we prepare preliminary position information first
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
    
    # CRITICAL FIX: Calculate preliminary available cash (decide whether to apply cash reserve based on mode)
    # Reuse config loaded earlier (line 145)
    position_limit_mode = config.get("position_limit_mode", "auto")
    min_cash_reserve_ratio = config.get("min_cash_reserve_ratio")
    
    # CRITICAL FIX: 即使是在 auto 模式下，可用现金也必须限制在实际现金范围内
    # LLM 可以自主决定如何使用现金，但不能超过实际可用的现金
    if position_limit_mode == "auto" or min_cash_reserve_ratio is None:
        preliminary_available_cash = portfolio.cash if portfolio else 0.0
    else:
        MIN_CASH_RESERVE_RATIO = float(min_cash_reserve_ratio)
        required_cash_reserve = preliminary_portfolio_value * MIN_CASH_RESERVE_RATIO
        preliminary_available_cash = max(0, portfolio.cash - required_cash_reserve) if portfolio else 0.0
    
    # CRITICAL FIX: Use version with four independent Analysts, ensure each analyst has tool calls and summary
    # Get current position information (for analyst analysis)
    # CRITICAL: Include complete position information (current_price, market_value, unrealized_pnl) for agent analysis
    current_positions = {}
    if portfolio:
        # FIX: Use _positions instead of positions property (positions returns Dict[str, int], _positions returns Dict[str, Position])
        # CRITICAL: Calculate current_price from market_view to provide complete position information
        for symbol, pos in portfolio._positions.items():
            # Get current price from market_view (if available) or use avg_cost as fallback
            current_price = pos.avg_cost  # Default fallback
            if market_view and "stocks" in market_view:
                stock_data = market_view["stocks"].get(symbol, {})
                if isinstance(stock_data, dict) and "price" in stock_data:
                    current_price = stock_data["price"]
            
            market_value = pos.quantity * current_price
            unrealized_pnl = (current_price - pos.avg_cost) * pos.quantity
            unrealized_pnl_pct = ((current_price - pos.avg_cost) / pos.avg_cost * 100.0) if pos.avg_cost > 0 else 0.0
            
            current_positions[symbol] = {
                "quantity": pos.quantity,
                "avg_cost": pos.avg_cost,
                "total_cost": pos.total_cost,
                "current_price": current_price,  # CRITICAL: Include current price
                "market_value": market_value,  # CRITICAL: Include market value
                "unrealized_pnl": unrealized_pnl,  # CRITICAL: Include unrealized P&L
                "unrealized_pnl_pct": unrealized_pnl_pct,  # CRITICAL: Include unrealized P&L percentage
            }
    
    # Get order status (for analyst analysis)
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
    
    # CRITICAL FIX: Calculate portfolio_value (using prices from market_view)
    portfolio_value = None
    if portfolio:
        # Extract prices from market_view
        last_prices = {}
        if market_view and "stocks" in market_view:
            for symbol, stock_data in market_view["stocks"].items():
                if isinstance(stock_data, dict) and "price" in stock_data:
                    last_prices[symbol] = stock_data["price"]
        
        # If price data available, use portfolio.value() to calculate total value
        if last_prices:
            portfolio_value = portfolio.value(last_prices)
        else:
            # If no price data, use cash + initial value as approximation
            portfolio_value = portfolio.cash + portfolio.initial_value
    
    # CRITICAL: Use optimized parallel version as default (direct integration)
    # CRITICAL FIX: Pass historical_memories and rounds to discussion system
    convo = run_multi_analyst_discussion_parallel(
        market_view=market_view,  # Pass complete market_view
        use_tools=auto_tools,
        tool_budget=tool_budget,
        order_status=order_status,
        current_positions=current_positions if current_positions else None,
        portfolio_value=portfolio_value,
        available_cash=portfolio.cash if portfolio else None,
        enable_parallel=True,
        historical_memories=historical_memories,  # Pass historical memories
        rounds=rounds,  # CRITICAL FIX: Pass rounds parameter for multi-round discussion
    )
    final_stance = convo.get("final_stance", "neutral")
    
    # CRITICAL FIX: Calculate VIX risk score and add to convo for trader_agent
    # trader_agent expects vix_risk in convo, but it's not calculated by multi_analyst_system
    # Note: Agents can now use vix_term tool to get vix_risk_score directly, but we still calculate it here for trader_agent
    vix_risk_score_value = 4.0  # Default value
    try:
        from src.tools.sentiment_tools import vix_term_structure, vix_risk_score
        # Try to get VIX data from market_view first
        vix_data_from_market = market_view.get("VIX") or market_view.get("vix")
        if vix_data_from_market and isinstance(vix_data_from_market, dict):
            # Extract VIX level from market_view
            vix_level = vix_data_from_market.get("level")
            if vix_level is not None and not (isinstance(vix_level, float) and (vix_level != vix_level)):  # Check for NaN
                # Create a dict in the format expected by vix_risk_score
                vix_dict = {"vix": vix_level}
                vix_risk_score_value = vix_risk_score(vix_dict)
                print(f"[TRADING CYCLE] Calculated VIX risk score from market_view: VIX={vix_level:.2f} -> risk_score={vix_risk_score_value:.1f}")
        else:
            # Fallback: fetch VIX data directly
            vix_data = vix_term_structure()
            if vix_data and vix_data.get("vix"):
                vix_risk_score_value = vix_risk_score(vix_data)
                print(f"[TRADING CYCLE] Calculated VIX risk score from vix_term_structure: VIX={vix_data.get('vix'):.2f} -> risk_score={vix_risk_score_value:.1f}")
            else:
                print(f"[TRADING CYCLE] ⚠️  VIX data not available, using default risk score: {vix_risk_score_value:.1f}")
    except Exception as e:
        print(f"[TRADING CYCLE] ⚠️  Failed to calculate VIX risk score: {e}, using default: {vix_risk_score_value:.1f}")
    
    # Add vix_risk to convo so trader_agent can access it
    if not isinstance(convo, dict):
        convo = {}
    convo["vix_risk"] = vix_risk_score_value
    print(f"[TRADING CYCLE] Added vix_risk={vix_risk_score_value:.1f} to convo for trader_agent (agents can also use vix_term tool to get this directly)")
    
    # CRITICAL FIX: Extract recommended stocks from Market Analyst LLM output in multi_analyst_system
    # Prefer LLM recommendations, use fallback if not available
    # CRITICAL FIX: Filter out ETFs and invalid symbols from recommended stocks
    from src.utils.etf_checker import is_etf
    
    recommended_stocks_from_llm = []
    analyst_reports = convo.get("analyst_reports", {})
    market_analyst_report = analyst_reports.get("market", {})
    if market_analyst_report:
        # Try to extract recommended_stocks from Market Analyst response
        raw_recommended = market_analyst_report.get("recommended_stocks", [])
        if raw_recommended:
            # CRITICAL FIX: Filter out ETFs and invalid symbols
            if isinstance(raw_recommended, str):
                raw_recommended = [s.strip() for s in raw_recommended.split(",") if s.strip()]
            elif not isinstance(raw_recommended, list):
                raw_recommended = []
            
            filtered_recommended = []
            from src.utils.etf_checker import is_crypto
            # CRITICAL FIX: Validate against universe symbols
            universe_set = set(s.upper() for s in universe)
            for sym in raw_recommended:
                sym_upper = str(sym).upper().strip()
                # Skip empty or invalid format
                if not sym_upper or len(sym_upper) > 10 or not sym_upper.replace(".", "").replace("-", "").isalnum():
                    continue
                # Skip cryptocurrencies (DOGE, BTC, ETH, etc.)
                if is_crypto(sym_upper):
                    continue
                # Skip ETFs
                if is_etf(sym_upper):
                    continue
                # CRITICAL FIX: Validate against universe
                if sym_upper not in universe_set:
                    print(f"[TRADING CYCLE] ⚠️ Skipping invalid symbol not in universe: {sym_upper}")
                    continue
                filtered_recommended.append(sym_upper)
            
            recommended_stocks_from_llm = filtered_recommended
            if recommended_stocks_from_llm:
                # Update recommended stocks in enriched_market
                enriched_market["recommended_stocks"] = recommended_stocks_from_llm
            else:
                print(f"[TRADING CYCLE] ⚠️ All recommended stocks were filtered out (ETFs/invalid), using fallback")
        else:
            print(f"[TRADING CYCLE] ⚠️  Market Analyst LLM did not provide recommended_stocks, using fallback")
    else:
        print(f"[TRADING CYCLE] ⚠️  Market Analyst report not found in analyst_reports, using fallback")

    # Write conversations to discussion_actions.jsonl (for frontend display)
    # CRITICAL FIX: Move convo_file and trade_date_str definitions outside try block, ensure RiskAnalyst and TraderAgent writes can access
    # CRITICAL: Use project root data/logs directory explicitly
    logs_dir = _get_project_logs_dir()
    convo_file = logs_dir / "discussion_actions.jsonl"
    
    # OPTIMIZATION: Check and rotate log file if needed (before writing)
    try:
        from src.utils.log_rotation import check_and_rotate
        archived_file = check_and_rotate(
            logs_dir,
            filename="discussion_actions.jsonl",
            rotation_type="size",  # Rotate when file exceeds 50 MB
            max_size_mb=50.0
        )
        if archived_file:
            print(f"[LOG ROTATION] Rotated log file to archive: {archived_file.name}")
    except Exception as e:
        # Don't fail the trading cycle if rotation fails
        print(f"[LOG ROTATION] Warning: Failed to check/rotate log file: {e}")
    
    # Get trade date (use end parameter, if not available use today)
    trade_date = end if end else date.today().isoformat()
    if isinstance(trade_date, str):
        # Ensure YYYY-MM-DD format
        # CRITICAL FIX: datetime already imported at file top, use directly
        try:
            trade_date_obj = datetime.strptime(trade_date, "%Y-%m-%d").date()
            trade_date_str = trade_date_obj.isoformat()
        except:
            trade_date_str = date.today().isoformat()
    else:
        trade_date_str = date.today().isoformat()
    
    try:
        # Path already imported at file top, no need to re-import
        import os
        
        transcript = convo.get("transcript", [])
        tool_context = convo.get("tool_context", [])
        actions = convo.get("actions", [])
        
        # Write each round's conversation
        # CRITICAL FIX: json already imported at file top, ensure accessible outside try block
        
        # CRITICAL FIX: Parse transcript array to extract individual analyst analyses
        # Transcript format: ["--- Market Analyst ---\nStance: ...\nAnalysis: ...", "--- Technical Analyst ---\n...", ...]
        transcript = convo.get("transcript", [])
        transcript_analysts_written = set()  # Track which analysts were written from transcript to avoid duplicates
        
        if transcript and isinstance(transcript, list):
            for transcript_item in transcript:
                if not transcript_item or not isinstance(transcript_item, str):
                    continue
                
                # Parse transcript format: "--- Analyst Name ---\nStance: X\nAnalysis: Y\nTools Used: ...\nKey Points: ..."
                lines = transcript_item.strip().split('\n')
                if not lines or not lines[0].startswith('---'):
                    continue
                
                # Extract analyst name from first line: "--- Market Analyst ---" -> "Market Analyst"
                analyst_line = lines[0].strip()
                analyst_name_raw = analyst_line.replace('---', '').strip()
                
                # Map to standard agent names
                analyst_name_map = {
                    "Market Analyst": "MarketAnalyst",
                    "Technical Analyst": "TechnicalAnalyst",
                    "Fundamental Analyst": "FundamentalAnalyst",
                    "Sentiment Analyst": "SentimentAnalyst",
                    "Discussion Coordinator": "DiscussionCoordinator",
                }
                agent_name = analyst_name_map.get(analyst_name_raw, analyst_name_raw.replace(' ', ''))
                
                # Extract stance and analysis from remaining lines
                stance = "neutral"
                analysis = ""
                tools_used = []
                
                for i, line in enumerate(lines[1:], 1):
                    line = line.strip()
                    if line.startswith("Stance:"):
                        stance = line.replace("Stance:", "").strip()
                    elif line.startswith("Analysis:"):
                        # Analysis may span multiple lines, collect until next section
                        # CRITICAL FIX: Handle JSON format in analysis (e.g., Technical Analyst)
                        analysis_parts = [line.replace("Analysis:", "").strip()]
                        brace_count = 0
                        if '{' in analysis_parts[0]:
                            brace_count = analysis_parts[0].count('{') - analysis_parts[0].count('}')
                        
                        for j in range(i + 1, len(lines)):
                            next_line = lines[j].strip()
                            # Stop at next section header
                            if next_line.startswith("Tools Used:") or next_line.startswith("Key Points:"):
                                break
                            analysis_parts.append(next_line)
                            # Track braces for JSON content
                            if '{' in next_line or '}' in next_line:
                                brace_count += next_line.count('{') - next_line.count('}')
                                # If braces are balanced and we've collected content, we can stop
                                if brace_count == 0 and len(analysis_parts) > 1:
                                    # Check if next line is a section header
                                    if j + 1 < len(lines):
                                        peek_line = lines[j + 1].strip()
                                        if peek_line.startswith("Tools Used:") or peek_line.startswith("Key Points:"):
                                            break
                        analysis = '\n'.join(analysis_parts).strip()
                    elif line.startswith("Tools Used:"):
                        tools_str = line.replace("Tools Used:", "").strip()
                        if tools_str:
                            # CRITICAL FIX: Deduplicate tools_used, record each tool only once (even for different companies)
                            tools_used = [t.strip() for t in tools_str.split(',') if t.strip()]
                            tools_used = list(dict.fromkeys(tools_used))  # Deduplicate but maintain order
                
                # If no analysis extracted, use the full transcript item (minus header)
                if not analysis:
                    analysis = '\n'.join(lines[1:]).strip()
                
                # Only write if this analyst hasn't been written from discussion_history yet
                if agent_name not in transcript_analysts_written:
                    transcript_analysts_written.add(agent_name)
                    
                    entry = {
                        "timestamp": get_utc_timestamp(),
                        "date": trade_date_str,
                        "agent": agent_name,
                        "round": 0,
                        "content": f"Stance: {stance}\n\nAnalysis: {analysis}",
                        "type": "discussion",
                        "stance": stance,
                        "summary": analysis,  # CRITICAL FIX: Add separate summary field for frontend use
                        "tools_used": tools_used,  # CRITICAL FIX: Ensure tools_used is correctly stored
                    }
                    
                    with convo_file.open("a", encoding="utf-8") as f:
                        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # CRITICAL FIX: Ensure extraction of four analyst results from discussion_history
        # If discussion_history is empty, try to build from analyst_reports
        discussion_history = convo.get("discussion_history", [])
        
        # CRITICAL FIX: Extract recommended_stocks from analyst_reports for MarketAnalyst
        analyst_reports = convo.get("analyst_reports", {})
        market_recommended_stocks = []
        if analyst_reports.get("market"):
            market_recommended_stocks = analyst_reports["market"].get("recommended_stocks", [])
            if isinstance(market_recommended_stocks, str):
                market_recommended_stocks = [s.strip() for s in market_recommended_stocks.split(",") if s.strip()]
            elif not isinstance(market_recommended_stocks, list):
                market_recommended_stocks = []
        
        # CRITICAL FIX: Update MarketAnalyst entry from transcript with recommended_stocks if available
        if market_recommended_stocks:
            # Try to find and update MarketAnalyst entry written from transcript
            # Read the file, find MarketAnalyst entry, add recommended_stocks, rewrite
            try:
                convo_file = _get_project_logs_dir() / "discussion_actions.jsonl"
                if convo_file.exists():
                    lines = convo_file.read_text(encoding="utf-8").strip().split("\n")
                    updated_lines = []
                    market_updated = False
                    for line in lines:
                        if line.strip():
                            try:
                                entry = json.loads(line)
                                # Update the most recent MarketAnalyst entry from transcript
                                if entry.get("agent") == "MarketAnalyst" and "recommended_stocks" not in entry and not market_updated:
                                    entry["recommended_stocks"] = market_recommended_stocks
                                    market_updated = True
                                updated_lines.append(json.dumps(entry, ensure_ascii=False))
                            except:
                                updated_lines.append(line)
                    
                    if market_updated:
                        convo_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")
            except Exception as e:
                pass  # Failed to update MarketAnalyst entry
        
        # If discussion_history is empty, build from analyst_reports
        if not discussion_history:
            all_tool_calls = convo.get("tool_calls", [])
            for analyst_key, report in analyst_reports.items():
                if report and isinstance(report, dict):
                    # Normalize analyst names
                    analyst_name_map = {
                        "market": "Market Analyst",
                        "technical": "Technical Analyst",
                        "fundamental": "Fundamental Analyst",
                        "sentiment": "Sentiment Analyst",
                    }
                    analyst_name = analyst_name_map.get(analyst_key, analyst_key.title() + " Analyst")
                    
                    # CRITICAL FIX: Extract only successfully used tools by this analyst from tool_calls
                    # Only include tools that were actually executed and succeeded
                    # CRITICAL FIX: Deduplicate tools_used, record each tool only once (even for different companies)
                    tools_used = []
                    for tc in all_tool_calls:
                        if tc.get("analyst", "").lower() == analyst_key:
                            tool_result = tc.get("result", {})
                            # Only include successful tools
                            if check_tool_success(tool_result):
                                tool_name = tc.get("tool", "") or tc.get("name", "")
                                if tool_name:
                                    tools_used.append(tool_name)
                    # Deduplicate but maintain order (use dict.fromkeys to maintain first occurrence order)
                    tools_used = list(dict.fromkeys(tools_used))
                    
                    # Ensure there is analysis (summary)
                    analysis = report.get("analysis", "No analysis provided")
                    if not analysis or len(analysis.strip()) < 50:
                        # If analysis is too short, try to generate from tool results
                        if tools_used:
                            analysis = f"Analysis based on {', '.join(tools_used[:3])}. {analysis}"
                    
                    entry_data = {
                        "analyst": analyst_name,
                        "stance": report.get("stance", "neutral"),
                        "analysis": analysis,
                        "tools_used": tools_used,
                        "key_points": report.get("recommendations", [])[:3] if report.get("recommendations") else [],
                    }
                    
                    # CRITICAL FIX: Add recommended_stocks for MarketAnalyst
                    if analyst_key == "market" and market_recommended_stocks:
                        entry_data["recommended_stocks"] = market_recommended_stocks
                    
                    discussion_history.append(entry_data)
        
        # CRITICAL FIX: Group entries by agent and keep only the latest round for each agent
        # This ensures we write the most complete analysis (from the latest round)
        agent_entries = {}  # Map<agent_name, entry_data>
        coordinator_entry = None
        
        for entry_data in discussion_history:
            analyst_name = entry_data.get("analyst", "Unknown")
            analyst_name_normalized = analyst_name.strip().lower()
            
            # Check if this is a coordinator
            is_coordinator = (analyst_name_normalized in ["discussion coordinator", "discussioncoordinator", "coordinator"] or
                            "discussion" in analyst_name_normalized and "coordinator" in analyst_name_normalized or
                            analyst_name_normalized.startswith("discussion") and "coordinator" in analyst_name_normalized)
            
            if is_coordinator:
                # Keep the coordinator entry (prefer round 0, or latest round)
                if coordinator_entry is None:
                    coordinator_entry = entry_data
                else:
                    # Prefer round 0, otherwise keep the latest round
                    current_round = entry_data.get("round", 0)
                    existing_round = coordinator_entry.get("round", 0)
                    if current_round == 0 or (current_round > existing_round and existing_round != 0):
                        coordinator_entry = entry_data
                continue
            
            # Normalize agent name
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
            agent_name = agent_name_map.get(analyst_name_normalized, analyst_name)
            
            # If still not matched, try to extract from the name
            if agent_name == analyst_name and agent_name not in ["MarketAnalyst", "TechnicalAnalyst", "FundamentalAnalyst", "SentimentAnalyst", "DiscussionCoordinator"]:
                if "market" in analyst_name_normalized:
                    agent_name = "MarketAnalyst"
                elif "technical" in analyst_name_normalized:
                    agent_name = "TechnicalAnalyst"
                elif "fundamental" in analyst_name_normalized:
                    agent_name = "FundamentalAnalyst"
                elif "sentiment" in analyst_name_normalized:
                    agent_name = "SentimentAnalyst"
            
            # Skip if not a recognized analyst
            if agent_name not in ["MarketAnalyst", "TechnicalAnalyst", "FundamentalAnalyst", "SentimentAnalyst"]:
                continue
            
            # Keep only the latest round for each agent
            if agent_name not in agent_entries:
                agent_entries[agent_name] = entry_data
            else:
                # Compare rounds - keep the entry with the highest round number
                current_round = entry_data.get("round", 0)
                existing_round = agent_entries[agent_name].get("round", 0)
                if current_round > existing_round:
                    agent_entries[agent_name] = entry_data
        
        # Now process the grouped entries
        coordinator_found_in_history = False
        if coordinator_entry:
            # Write coordinator entry
            coordinator_found_in_history = True
            stance = coordinator_entry.get("stance", "neutral")
            analysis = coordinator_entry.get("analysis", coordinator_entry.get("summary", "No analysis provided"))
            
            entry = {
                "timestamp": get_utc_timestamp(),
                "date": trade_date_str,
                "agent": "DiscussionCoordinator",
                "round": 0,
                "original_round": coordinator_entry.get("round", 0),
                "content": f"Stance: {stance}\n\nAnalysis: {analysis}",
                "type": "discussion",
                "stance": stance,
                "summary": analysis,
                "tools_used": coordinator_entry.get("tools_used", []),
            }
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # Process analyst entries (already grouped and normalized)
        for agent_name, entry_data in agent_entries.items():
            # CRITICAL FIX: Skip if this analyst was already written from transcript
            if agent_name in transcript_analysts_written:
                continue
            
            stance = entry_data.get("stance", "neutral")
            analysis = entry_data.get("analysis", "No analysis provided")
            tools_used = entry_data.get("tools_used", [])
            recommended_stocks = entry_data.get("recommended_stocks", [])  # CRITICAL FIX: Extract recommended_stocks for MarketAnalyst
            
            # CRITICAL FIX: Skip if analysis is too short or placeholder (e.g., "Waiting for tool results")
            if not analysis or len(analysis.strip()) < 50 or "waiting for tool results" in analysis.lower():
                continue
            
            # CRITICAL FIX: If MarketAnalyst and no recommended_stocks in entry_data, try to get from analyst_reports
            if agent_name == "MarketAnalyst" and not recommended_stocks and market_recommended_stocks:
                recommended_stocks = market_recommended_stocks
            
            # CRITICAL FIX: Always use round: 0 for frontend display (frontend filters for round === 0)
            # Round information is preserved in discussion_history if needed for analysis
            round_num = entry_data.get("round", 0)  # Keep original round for reference
            
            entry = {
                "timestamp": get_utc_timestamp(),
                "date": trade_date_str,
                "agent": agent_name,
                "round": 0,  # CRITICAL FIX: Always use 0 for frontend display (frontend filters for round === 0)
                "original_round": round_num,  # CRITICAL FIX: Preserve original round number for reference
                "content": f"Stance: {stance}\n\nAnalysis: {analysis}",
                "type": "discussion",
                "stance": stance,
                "summary": analysis,  # CRITICAL FIX: Add separate summary field for frontend use
                "tools_used": tools_used,  # CRITICAL FIX: Ensure tools_used is correctly stored
            }
            
            # CRITICAL FIX: Add recommended_stocks field for MarketAnalyst (for frontend filtering)
            if agent_name == "MarketAnalyst" and recommended_stocks:
                entry["recommended_stocks"] = recommended_stocks if isinstance(recommended_stocks, list) else []
            
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            transcript_analysts_written.add(agent_name)  # CRITICAL FIX: Mark as written to avoid duplicates
        
        # CRITICAL FIX: Ensure all required analysts are written (final check)
        # This guarantees that even if transcript parsing fails or discussion_history is incomplete,
        # all analysts will still be written from analyst_reports
        required_analysts = {
            "MarketAnalyst": "market",
            "TechnicalAnalyst": "technical",
            "FundamentalAnalyst": "fundamental",
            "SentimentAnalyst": "sentiment"
        }
        
        for agent_name, analyst_key in required_analysts.items():
            if agent_name not in transcript_analysts_written:
                # This analyst was not written, try to write from analyst_reports
                report = analyst_reports.get(analyst_key, {})
                if report and isinstance(report, dict):
                    analysis = report.get("analysis", "")
                    stance = report.get("stance", "neutral")
                    tools_used = report.get("tools_used", [])
                    
                    # Only write if we have meaningful analysis
                    if analysis and len(analysis.strip()) > 10:
                        entry = {
                            "timestamp": get_utc_timestamp(),
                            "date": trade_date_str,
                            "agent": agent_name,
                            "round": 0,
                            "content": f"Stance: {stance}\n\nAnalysis: {analysis}",
                            "type": "discussion",
                            "stance": stance,
                            "summary": analysis,
                            "tools_used": tools_used if isinstance(tools_used, list) else [],
                        }
                        
                        # Add recommended_stocks for MarketAnalyst
                        if agent_name == "MarketAnalyst" and market_recommended_stocks:
                            entry["recommended_stocks"] = market_recommended_stocks if isinstance(market_recommended_stocks, list) else []
                        
                        with convo_file.open("a", encoding="utf-8") as f:
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        transcript_analysts_written.add(agent_name)
        
        # CRITICAL FIX: Final verification - ensure all required analysts were written
        written_analysts = list(transcript_analysts_written)
        missing_analysts = [agent for agent in required_analysts.keys() if agent not in written_analysts]
        if missing_analysts:
            pass  # Missing analysts logged above
        
        # Write Coordinator synthesis result (write only once, avoid duplicates)
        # If Coordinator already exists in discussion_history, don't write coordinator_summary separately
        coordinator_summary = convo.get("coordinator_summary")
        if coordinator_summary and not coordinator_found_in_history:
            if isinstance(coordinator_summary, dict):
                stance = coordinator_summary.get("stance", "neutral")
                summary = coordinator_summary.get("summary", "No summary provided")
                # Ensure summary is not empty
                if not summary or summary.strip() == "":
                    summary = "Coordinator synthesized all analyst perspectives."
                
                entry = {
                    "timestamp": get_utc_timestamp(),
                    "date": trade_date_str,
                    "agent": "DiscussionCoordinator",
                    "round": 0,
                    "content": f"Stance: {stance}\n\nAnalysis: {summary}",  # Use Analysis instead of Summary for consistency
                    "type": "discussion",
                    "stance": stance,
                    "summary": summary,  # CRITICAL FIX: Add separate summary field for frontend use
                    "tools_used": [],  # Coordinator does not use tools
                }
                with convo_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        elif coordinator_summary and coordinator_found_in_history:
            print(f"[TRADING CYCLE] Skipped writing coordinator_summary (Coordinator already exists in discussion_history)")
        
        # Write tool usage records (extracted from tool_calls)
        # CRITICAL FIX: Only record tools that were successfully used in the discussion rounds (1-3)
        tool_calls = convo.get("tool_calls", [])
        
        # CRITICAL FIX: Import check_tool_success to filter successful tools only
        from src.agents.analysts.common import check_tool_success
        
        # CRITICAL FIX: Filter to only successful tools used in discussion rounds
        successful_tool_calls = []
        failed_tool_calls = []
        for tc in tool_calls:
            tool_result = tc.get("result", {})
            if check_tool_success(tool_result):
                successful_tool_calls.append(tc)
            else:
                failed_tool_calls.append(tc)
        
        print(f"[TRADING CYCLE] Writing {len(successful_tool_calls)} successful tool calls to discussion_actions.jsonl (filtered out {len(failed_tool_calls)} failed tools)")
        
        # DEBUG: Log tool_calls structure for news tools
        # CRITICAL FIX: Check both "tool" and "name" fields (some tool_calls may use "name")
        news_tool_calls = []
        for tc in successful_tool_calls:
            tool_name = tc.get("tool", "") or tc.get("name", "")
            if tool_name.lower() in ["plan_and_scan_news", "news_scan", "get_news_scan"]:
                news_tool_calls.append(tc)
        
        if news_tool_calls:
            print(f"[TRADING CYCLE] [NEWS] Found {len(news_tool_calls)} successful news tool calls in convo.tool_calls")
            for idx, tc in enumerate(news_tool_calls):
                tool_name = tc.get("tool", "") or tc.get("name", "")
                print(f"[TRADING CYCLE] [NEWS]   Tool call {idx}: analyst={tc.get('analyst')}, tool={tool_name}, has_result={bool(tc.get('result'))}")
        else:
            print(f"[TRADING CYCLE] [NEWS] ⚠️ No successful news tool calls found in {len(successful_tool_calls)} tool calls")
            # DEBUG: List all tool names (check both "tool" and "name" fields)
            all_tool_names = [tc.get("tool", "") or tc.get("name", "") for tc in successful_tool_calls]
            print(f"[TRADING CYCLE] [NEWS]   All tool names: {', '.join(all_tool_names[:10])}{'...' if len(all_tool_names) > 10 else ''}")
        
        # CRITICAL FIX: Get actual round number from discussion_history or convo
        # Try to extract round from discussion_history entries
        discussion_history = convo.get("discussion_history", [])
        tool_round_map = {}  # Map analyst -> round number (for fallback)
        # Build a map of analyst -> latest round number (for fallback if tool_call doesn't have round)
        for entry in discussion_history:
            analyst = entry.get("analyst", "")
            round_num = entry.get("round", 0)
            if analyst and round_num > 0:
                # Normalize analyst name
                analyst_lower = analyst.lower()
                if "market" in analyst_lower:
                    tool_round_map["MarketAnalyst"] = round_num
                elif "technical" in analyst_lower:
                    tool_round_map["TechnicalAnalyst"] = round_num
                elif "fundamental" in analyst_lower:
                    tool_round_map["FundamentalAnalyst"] = round_num
                elif "sentiment" in analyst_lower:
                    tool_round_map["SentimentAnalyst"] = round_num
        
        # CRITICAL FIX: Only write successful tools that were used in discussion rounds (1-3)
        for tool_call in successful_tool_calls:
            analyst_name = tool_call.get("analyst", "Unknown")
            # CRITICAL FIX: Check both "tool" and "name" fields (some tool_calls may use "name")
            tool_name = tool_call.get("tool", "") or tool_call.get("name", "")
            
            # CRITICAL FIX: Map deprecated news_scan to plan_and_scan_news (for Risk Analyst and others)
            if tool_name == "news_scan":
                print(f"[TRADING CYCLE] [NEWS] Mapping news_scan to plan_and_scan_news (news_scan is deprecated)")
                tool_name = "plan_and_scan_news"
            
            tool_result = tool_call.get("result", {})
            
            # Normalize agent names
            agent_name_map = {
                "market": "MarketAnalyst",
                "marketanalyst": "MarketAnalyst",
                "technical": "TechnicalAnalyst",
                "technicalanalyst": "TechnicalAnalyst",
                "fundamental": "FundamentalAnalyst",
                "fundamentanalyst": "FundamentalAnalyst",
                "sentiment": "SentimentAnalyst",
                "sentimentanalyst": "SentimentAnalyst",  # CRITICAL FIX: Support full name matching
            }
            # CRITICAL FIX: Try full match first, then try lowercase match
            agent_name = agent_name_map.get(analyst_name, agent_name_map.get(analyst_name.lower(), analyst_name))
            
            # Format tool results
            # Handle double nesting: {"ok": true, "result": {"ok": true, "result": {...}}}
            # Recursively extract actual result data
            actual_result = tool_result
            if isinstance(tool_result, dict):
                while isinstance(actual_result, dict) and "ok" in actual_result and "result" in actual_result:
                    actual_result = actual_result["result"]
            
            # CRITICAL FIX: For news tools, save complete articles and hits first (before truncation)
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
                    # Extract key information
                    result_text = json.dumps(actual_result, ensure_ascii=False, indent=2)
                    # For news tools, keep more data (no truncation or truncate to 5000 chars)
                    # For other tools, limit to 2000 chars
                    max_length = 5000 if tool_name in ["news_scan", "plan_and_scan_news"] else 2000
                    if len(result_text) > max_length:
                        # For news tools, try to keep complete articles and hits arrays (even if truncated, ensure arrays are complete)
                        if tool_name in ["news_scan", "plan_and_scan_news"]:
                            # CRITICAL FIX: Prioritize keeping articles (contains content), if not available keep hits
                            articles = actual_result.get("articles", [])
                            hits = actual_result.get("hits", [])
                            queries = actual_result.get("queries", [])
                            
                            # Build a simplified result but keep complete articles and hits
                            simplified = {}
                            if articles:
                                simplified["articles"] = articles
                            if hits:
                                simplified["hits"] = hits
                            if queries:
                                simplified["queries"] = queries
                            
                            result_text = json.dumps(simplified, ensure_ascii=False, indent=2)
                            # If still too long, at least keep first few articles/hits
                            if len(result_text) > max_length:
                                # Keep first N articles (priority) or hits, ensure JSON is complete
                                if articles:
                                    max_items = min(len(articles), 10)  # Keep max 10 articles
                                    simplified["articles"] = articles[:max_items]
                                    simplified["total_articles"] = len(articles)
                                elif hits:
                                    max_items = min(len(hits), 10)  # Keep max 10 hits
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
            
            # CRITICAL FIX: Categorize by tool type (news, risk, market, etc.)
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
            
            # CRITICAL FIX: For get_company_fundamentals, ensure tool_result contains symbol (even if result is truncated)
            # CRITICAL FIX: For news tools, ensure complete articles and hits arrays are preserved (use backup data)
            # CRITICAL FIX: For economic tools (FRED), preserve string format for frontend to display correctly
            if tool_name in ["get_economic_summary", "get_labor_market_data", "get_treasury_yield_curve", "fetch_fred_indicator"]:
                # FRED tools return strings, save directly as string format (frontend will handle)
                if isinstance(actual_result, str):
                    tool_result_data = actual_result
                elif isinstance(actual_result, dict) and "raw" in actual_result:
                    # If already in {"raw": "..."} format, extract string
                    tool_result_data = actual_result.get("raw", result_text)
                else:
                    tool_result_data = result_text if result_text else str(actual_result)
            else:
                tool_result_data = actual_result if isinstance(actual_result, dict) else {"raw": result_text}
            
            # CRITICAL FIX: For news tools, use backup complete data (even if result_text is truncated)
            if tool_name in ["plan_and_scan_news", "news_scan"]:
                # CRITICAL FIX: Ensure tool_result_data is a dict (not nested structure)
                # The frontend expects tool_result_data to directly contain articles/hits, not wrapped in {ok: true, result: {...}}
                if not isinstance(tool_result_data, dict):
                    tool_result_data = {}
                
                # Use backup complete articles and hits (saved before truncation)
                if news_articles_backup is not None:
                    tool_result_data["articles"] = news_articles_backup
                if news_hits_backup is not None:
                    tool_result_data["hits"] = news_hits_backup
                
                # If backup doesn't exist, try to extract from actual_result
                if isinstance(actual_result, dict):
                    if "articles" not in tool_result_data and "articles" in actual_result:
                        articles_list = actual_result.get("articles", [])
                        if isinstance(articles_list, list):
                            tool_result_data["articles"] = articles_list
                    if "hits" not in tool_result_data and "hits" in actual_result:
                        hits_list = actual_result.get("hits", [])
                        if isinstance(hits_list, list):
                            tool_result_data["hits"] = hits_list
                    # Preserve other important fields
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
                # Ensure symbol field exists (even if result is truncated, preserve symbol)
                if "symbol" not in tool_result_data:
                    # Try to extract symbol from actual_result
                    symbol = actual_result.get("symbol") or actual_result.get("Symbol")
                    if symbol:
                        tool_result_data["symbol"] = symbol
                    # If actual_result is truncated, try to extract from content
                    elif "symbol" in result_text:
                        try:
                            import re
                            symbol_match = re.search(r'"symbol"\s*:\s*"([^"]+)"', result_text)
                            if symbol_match:
                                tool_result_data["symbol"] = symbol_match.group(1)
                        except:
                            pass
            
            # CRITICAL FIX: Get round number for this tool call
            # First try to get round from tool_call itself (if it was added when appending to all_tool_calls)
            tool_round = tool_call.get("round", None)
            # If not found in tool_call, use the round from tool_round_map (extracted from discussion_history)
            if tool_round is None:
                tool_round = tool_round_map.get(agent_name, 1)
            # Ensure round is between 1 and 3 (discussion rounds)
            tool_round = max(1, min(3, tool_round))
            
            entry = {
                "timestamp": get_utc_timestamp(),
                "date": trade_date_str,
                "agent": agent_name,  # CRITICAL FIX: Use agent name that called the tool (MarketAnalyst, TechnicalAnalyst, etc.), not ToolSystem
                "round": tool_round,  # CRITICAL FIX: Use actual discussion round (1-3) instead of 0
                "content": f"Tool used: {tool_name}: {result_text}",
                "type": "tool",
                "tool_name": tool_name,
                "tool_category": tool_category,  # CRITICAL FIX: Add tool category
                "tool_result": tool_result_data,  # CRITICAL FIX: Add tool result (structured data, ensure symbol is included)
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
    
    # Extract risk signals from Discussion (for Risk Analyst)
    discussion_risk_signals = {
        "risk_level": "medium",
        "risk_signals": convo.get("risk_signals", []),
    }

    # NOTE: Risk Analyst and Trader Agent calls will be moved after order settlement to ensure using latest position status

    # ---- (5) Order Strategy: Place limit orders before market open, check fills after market close ----
    from src.data.order_manager import OrderManager
    
    # CRITICAL: Use project root data/logs directory explicitly
    order_manager = OrderManager(root=str(_get_project_logs_dir()))
    
    # Check if market is open, determine order date (exclude weekends and holidays)
    # CRITICAL FIX: Pass None to let function directly get ET time, avoid timezone conversion errors
    from src.utils.trading_days import is_market_open as check_market_open
    now = datetime.now()
    is_market_open = check_market_open(None)  # Pass None to directly get ET time
    
    # If market is closed, order date should be tomorrow's date
    # Note: If end parameter is passed (for testing or planning), prioritize using end date
    existing_pending_orders = []
    if end:
        # end parameter priority: for testing or planning trades on specific dates
        # In multi-day simulation, order date should use end date (same day), not "tomorrow"
        today = end
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        print(f"[TRADING CYCLE] Using end date: {today} (forced date for testing/planning)")
        # CRITICAL FIX: Even with end parameter, should check actual market status
        # Only allow trading when market is actually open; otherwise run analysis only
        is_market_open_for_simulation = is_market_open
        if not is_market_open:
            print(f"[TRADING CYCLE] Market is actually closed. Will run analysis only (no trading).")
    elif is_market_open:
        today = date.today().isoformat()
        existing_pending_orders = order_manager.load_pending_orders(order_date=today)
        is_market_open_for_simulation = True
        print(f"[TRADING CYCLE] ✅ Market is OPEN - trading allowed")
    else:
        # CRITICAL FIX: After market close, allow running conversation (AI analysis), but don't execute trades
        # Continue executing conversation and analysis, but skip order creation and execution
        print(f"[TRADING CYCLE] ⚠️  Market closed. Running conversation/analysis only (no trading).")
        # Set flag to skip order execution later
        is_market_open_for_simulation = False
        # CRITICAL FIX: Print detailed market status information for debugging
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
        
        # CRITICAL FIX: When market is closed, immediately clean up today's pending orders (market orders should not have pending status)
        # Even if trading cycle is not run, still clean up pending orders
        if len(existing_pending_orders) > 0:
            print(f"[TRADING CYCLE] Market is closed. Immediately cancelling {len(existing_pending_orders)} today's pending orders (market orders should not be pending when market is closed).")
            cancelled_count = order_manager.cancel_orders(order_date=today)
            if cancelled_count > 0:
                print(f"[TRADING CYCLE] Cancelled {cancelled_count} today's pending orders")
                # Reload pending orders (should be empty)
                existing_pending_orders = order_manager.load_pending_orders(order_date=today)
    
    executed_trades = []
    execution_errors = []
    placed_orders = []  # Record placed orders
    new_orders_count = 0  # Record number of newly created orders this time (excluding existing_pending_orders)
    
    # Check if there are many pending orders, if so, cancel today's pending orders, only keep tomorrow's orders
    # This mechanism prevents pending order accumulation
    # CRITICAL: Regardless of market status, always clean up old pending orders
    if not end:  # Only execute in real-time mode (not in multi-day simulation)
        all_pending_orders = order_manager.load_pending_orders()  # Load all pending orders
        today_str = date.today().isoformat()

        # Automatically clean up orders from previous trading days to prevent infinite accumulation
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
                            "timestamp": get_utc_timestamp()
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
    
    # CRITICAL FIX: Force VIX risk score into market_view for Risk Analyst
    # Risk Analyst MUST use VIX risk score - we force it here to ensure it's always available
    # We already calculated vix_risk_score_value earlier (line 490-518), add it to market_view
    market_view_for_risk = dict(market_view)  # Create a copy to avoid modifying original
    
    # CRITICAL: Force VIX risk score into market_view.vix structure
    if "vix" in market_view_for_risk:
        if isinstance(market_view_for_risk["vix"], dict):
            market_view_for_risk["vix"]["risk_score"] = vix_risk_score_value
            # Also ensure level is present for context
            if "level" not in market_view_for_risk["vix"]:
                # Try to get from VIX data
                vix_data_from_market = market_view.get("VIX") or market_view.get("vix")
                if isinstance(vix_data_from_market, dict):
                    market_view_for_risk["vix"]["level"] = vix_data_from_market.get("level")
        else:
            # If vix is not a dict, create one with both level and risk_score
            vix_level = None
            vix_data_from_market = market_view.get("VIX") or market_view.get("vix")
            if isinstance(vix_data_from_market, dict):
                vix_level = vix_data_from_market.get("level")
            market_view_for_risk["vix"] = {"level": vix_level, "risk_score": vix_risk_score_value}
    else:
        # If vix doesn't exist, create it with risk_score
        vix_level = None
        vix_data_from_market = market_view.get("VIX") or market_view.get("vix")
        if isinstance(vix_data_from_market, dict):
            vix_level = vix_data_from_market.get("level")
        market_view_for_risk["vix"] = {"level": vix_level, "risk_score": vix_risk_score_value}
    
    # Also add VIX risk score to discussion_risk_signals for additional context
    if discussion_risk_signals is None:
        discussion_risk_signals = {}
    discussion_risk_signals["vix_risk_score"] = vix_risk_score_value
    discussion_risk_signals["vix_level"] = market_view_for_risk["vix"].get("level")
    print(f"[TRADING CYCLE] FORCED VIX risk score ({vix_risk_score_value:.1f}) into market_view.vix.risk_score for Risk Analyst")
    
    # CRITICAL: 即使没有持仓（current_positions_info为空），也要传递组合信息
    # 传递空字典而不是None，这样 Risk Analyst 可以明确知道"没有持仓"的状态
    risk_report = run_risk_analyst_llm(
        market_json=market_view_for_risk,  # CRITICAL FIX: Use market_view with VIX risk score
        current_positions=current_positions_info,  # 传递空字典{}而不是None，表示"没有持仓"的状态
        portfolio_value=portfolio_value,  # 即使没有持仓，也要传递组合净值
        discussion_risk_signals=discussion_risk_signals,  # CRITICAL FIX: Includes vix_risk_score
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
                    "timestamp": get_utc_timestamp(),
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
                elif tool_name in ["get_economic_summary", "get_labor_market_data", "get_treasury_yield_curve", "fetch_fred_indicator"]:
                    tool_category = "economic"
                
                tool_result_data = actual_result if isinstance(actual_result, dict) else {"raw": result_text}
                
                tool_entry = {
                    "timestamp": get_utc_timestamp(),
                    "date": trade_date_str,
                    "agent": "RiskAnalyst",
                    "round": 1,  # CRITICAL FIX: RiskAnalyst runs after discussion, use round 1 so tools are visible in frontend
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
        
        # Log error to error logger
        try:
            from src.utils.error_logger import get_error_logger, ErrorLevel
            error_logger = get_error_logger(root=str(_get_project_logs_dir()))
            error_logger.error(
                message="Trader Agent failed during trading cycle",
                component="trading_cycle",
                exception=e,
                context={
                    "function": "execute_daily_trade",
                    "market_open": is_market_open_for_simulation,
                    "portfolio_value": portfolio.value(last_prices) if portfolio and last_prices else None,
                }
            )
        except Exception as log_error:
            print(f"[TRADING CYCLE] ⚠️  Failed to log error: {log_error}")
        
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
                    
                    # CRITICAL: 市价单必须100%记录 - 使用多重保障机制
                    # 市价单：立即成交，不挂单
                    # 创建订单记录（标记为已成交）
                    print(f"[MARKET ORDER] Creating order record for {symbol} (quantity={quantity}, price=${current_price:.2f})")
                    
                    # 准备订单数据（无论place_order是否成功，都需要这个数据）
                    order_data = {
                        "symbol": symbol,
                        "action": "BUY",
                        "quantity": quantity,
                        "limit_price": current_price,
                        "price_range": {
                            "min": current_price,
                            "max": current_price,
                        },
                    }
                    
                    fill_result = {
                        "filled": True,
                        "fill_price": current_price,
                        "fill_reason": "Market order executed immediately at current price",
                        "daily_high": current_price,
                        "daily_low": current_price,
                        "current_price": current_price,
                    }
                    
                    placed_order = None
                    order_recorded = False
                    
                    # 方法1: 尝试使用 OrderManager 的标准流程
                    try:
                        placed_order = order_manager.place_order(
                            symbol=order_data["symbol"],
                            action=order_data["action"],
                            quantity=order_data["quantity"],
                            limit_price=order_data["limit_price"],
                            price_range=order_data["price_range"],
                        )
                        print(f"[MARKET ORDER] ✅ Order created via OrderManager: {placed_order.get('order_id')}")
                        
                        # 立即标记为已成交
                        try:
                            print(f"[MARKET ORDER] Marking {symbol} order as FILLED (fill_price=${current_price:.2f})")
                            order_manager.mark_order_filled(placed_order, fill_result)
                            placed_order["status"] = "FILLED"
                            order_recorded = True
                            print(f"[MARKET ORDER] ✅ Successfully marked {symbol} order as FILLED via OrderManager")
                        except Exception as e:
                            print(f"[MARKET ORDER] ⚠️ WARNING: mark_order_filled failed, will use fallback: {e}")
                            # 继续到备用方法
                    except Exception as e:
                        print(f"[MARKET ORDER] ⚠️ WARNING: place_order() failed, will use fallback: {e}")
                        import traceback
                        traceback.print_exc()
                        # 继续到备用方法
                    
                    # 方法2: 备用机制 - 如果 OrderManager 失败，直接写入 filled_orders.jsonl
                    if not order_recorded:
                        print(f"[MARKET ORDER] Using fallback method to record {symbol} order")
                        try:
                            # 创建订单ID（如果place_order失败，手动创建）
                            if not placed_order:
                                # datetime already imported at top
                                now = datetime.now(timezone.utc)
                                order_id = f"{symbol}_BUY_{now.date().isoformat()}_{now.timestamp()}"
                                placed_at = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                                
                                placed_order = {
                                    "order_id": order_id,
                                    "symbol": symbol,
                                    "action": "BUY",
                                    "quantity": quantity,
                                    "limit_price": current_price,
                                    "price_range": order_data["price_range"],
                                    "placed_at": placed_at,
                                    "status": "FILLED",
                                    "fill_price": current_price,
                                    "filled_at": get_utc_timestamp(),
                                    "fill_reason": "Market order executed immediately at current price",
                                    "daily_high": current_price,
                                    "daily_low": current_price,
                                    "fill_result": fill_result,
                                }
                            
                            # 确保目录存在
                            filled_file = order_manager.filled_orders_file
                            filled_file.parent.mkdir(parents=True, exist_ok=True)
                            
                            # 直接写入 filled_orders.jsonl
                            with filled_file.open("a", encoding="utf-8") as f:
                                f.write(json.dumps(placed_order, ensure_ascii=False) + "\n")
                            
                            order_recorded = True
                            print(f"[MARKET ORDER] ✅ Fallback: Successfully wrote {symbol} order to {filled_file}")
                            
                            # 如果 pending_orders.jsonl 中有这个订单，移除它
                            pending_file = order_manager.pending_orders_file
                            if pending_file.exists() and placed_order.get("order_id"):
                                try:
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
                                    
                                    pending_file.parent.mkdir(parents=True, exist_ok=True)
                                    with pending_file.open("w", encoding="utf-8") as f:
                                        for o in all_pending:
                                            f.write(json.dumps(o, ensure_ascii=False) + "\n")
                                    print(f"[MARKET ORDER] ✅ Removed {symbol} order from pending (remaining: {len(all_pending)})")
                                except Exception as e3:
                                    print(f"[MARKET ORDER] ⚠️ WARNING: Failed to clean pending_orders.jsonl: {e3}")
                        except Exception as e2:
                            print(f"[MARKET ORDER] ❌ ERROR: Fallback method also failed: {e2}")
                            import traceback
                            traceback.print_exc()
                    
                    # 方法3: 最后保障 - 如果所有方法都失败，至少记录到 trades.jsonl
                    if not order_recorded:
                        print(f"[MARKET ORDER] ⚠️ CRITICAL: All order recording methods failed, logging to trades.jsonl as backup")
                        try:
                            trade_logger.log(
                                symbol=symbol,
                                action="BUY",
                                price=current_price,
                                quantity=quantity,
                                amount=actual_cost,
                                status="SUCCESS",  # 交易成功，只是订单记录失败
                                reason=f"Order recorded via fallback (order_id: {placed_order.get('order_id') if placed_order else 'N/A'})",
                            )
                            print(f"[MARKET ORDER] ✅ Backup: Logged {symbol} trade to trades.jsonl")
                        except Exception as e3:
                            print(f"[MARKET ORDER] ❌ CRITICAL ERROR: Even backup logging failed: {e3}")
                            # 最后的最后，至少打印到控制台
                            print(f"[MARKET ORDER] ⚠️⚠️⚠️ CRITICAL: Order may be lost! {symbol} BUY x{quantity} @ ${current_price:.2f}")
                    
                    # 确保 placed_order 存在（用于后续代码）
                    if not placed_order:
                        # 创建最小订单对象
                        # datetime already imported at top
                        now = datetime.now(timezone.utc)
                        placed_order = {
                            "order_id": f"{symbol}_BUY_{now.date().isoformat()}_{now.timestamp()}",
                            "symbol": symbol,
                            "action": "BUY",
                            "quantity": quantity,
                            "limit_price": current_price,
                            "status": "FILLED" if order_recorded else "UNKNOWN",
                        }
                    
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
                    # CRITICAL FIX: Print detailed error information
                    print(f"[MARKET ORDER] ❌ ERROR: Order placement failed for {symbol}: {e}")
                    import traceback
                    traceback.print_exc()
                    
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
                    
                    # CRITICAL: 市价单必须100%记录 - 使用多重保障机制（SELL订单）
                    # 市价单：立即成交，不挂单
                    # 先执行交易以获取realized_pnl（在创建订单前）
                    realized_pnl = portfolio.sell(symbol, quantity, current_price)
                    
                    # 准备订单数据
                    order_data = {
                        "symbol": symbol,
                        "action": "SELL",
                        "quantity": quantity,
                        "limit_price": current_price,
                        "price_range": {
                            "min": current_price,
                            "max": current_price,
                        },
                    }
                    
                    fill_result = {
                        "filled": True,
                        "fill_price": current_price,
                        "fill_reason": "Market order executed immediately at current price",
                        "daily_high": current_price,
                        "daily_low": current_price,
                        "current_price": current_price,
                    }
                    
                    placed_order = None
                    order_recorded = False
                    
                    # 方法1: 尝试使用 OrderManager 的标准流程
                    try:
                        placed_order = order_manager.place_order(
                            symbol=order_data["symbol"],
                            action=order_data["action"],
                            quantity=order_data["quantity"],
                            limit_price=order_data["limit_price"],
                            price_range=order_data["price_range"],
                        )
                        print(f"[MARKET ORDER] ✅ SELL order created via OrderManager: {placed_order.get('order_id')}")
                        
                        # 立即标记为已成交（包含realized_pnl）
                        try:
                            print(f"[MARKET ORDER] Marking {symbol} SELL order as FILLED (fill_price=${current_price:.2f}, realized_pnl=${realized_pnl.get('realized_pnl', 0):.2f})")
                            order_manager.mark_order_filled(placed_order, fill_result, realized_pnl=realized_pnl)
                            placed_order["status"] = "FILLED"
                            order_recorded = True
                            print(f"[MARKET ORDER] ✅ Successfully marked {symbol} SELL order as FILLED via OrderManager")
                        except Exception as e:
                            print(f"[MARKET ORDER] ⚠️ WARNING: mark_order_filled failed for SELL, will use fallback: {e}")
                            # 继续到备用方法
                    except Exception as e:
                        print(f"[MARKET ORDER] ⚠️ WARNING: place_order() failed for SELL, will use fallback: {e}")
                        import traceback
                        traceback.print_exc()
                        # 继续到备用方法
                    
                    # 方法2: 备用机制 - 如果 OrderManager 失败，直接写入 filled_orders.jsonl
                    if not order_recorded:
                        print(f"[MARKET ORDER] Using fallback method to record {symbol} SELL order")
                        try:
                            # 创建订单ID（如果place_order失败，手动创建）
                            if not placed_order:
                                # datetime already imported at top
                                now = datetime.now(timezone.utc)
                                order_id = f"{symbol}_SELL_{now.date().isoformat()}_{now.timestamp()}"
                                placed_at = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                                
                                placed_order = {
                                    "order_id": order_id,
                                    "symbol": symbol,
                                    "action": "SELL",
                                    "quantity": quantity,
                                    "limit_price": current_price,
                                    "price_range": order_data["price_range"],
                                    "placed_at": placed_at,
                                    "status": "FILLED",
                                    "fill_price": current_price,
                                    "filled_at": get_utc_timestamp(),
                                    "fill_reason": "Market order executed immediately at current price",
                                    "daily_high": current_price,
                                    "daily_low": current_price,
                                    "fill_result": fill_result,
                                }
                            
                            # 记录realized_pnl
                            if realized_pnl:
                                placed_order["realized_pnl"] = realized_pnl.get("realized_pnl", 0.0)
                                placed_order["realized_pnl_pct"] = realized_pnl.get("realized_pnl_pct", 0.0)
                                placed_order["cost_basis"] = realized_pnl.get("cost_basis", 0.0)
                                placed_order["proceeds"] = realized_pnl.get("proceeds", 0.0)
                                placed_order["fill_result"]["realized_pnl"] = realized_pnl.get("realized_pnl", 0.0)
                                placed_order["fill_result"]["realized_pnl_pct"] = realized_pnl.get("realized_pnl_pct", 0.0)
                                placed_order["fill_result"]["cost_basis"] = realized_pnl.get("cost_basis", 0.0)
                                placed_order["fill_result"]["proceeds"] = realized_pnl.get("proceeds", 0.0)
                            
                            # 确保目录存在
                            filled_file = order_manager.filled_orders_file
                            filled_file.parent.mkdir(parents=True, exist_ok=True)
                            
                            # 直接写入 filled_orders.jsonl
                            with filled_file.open("a", encoding="utf-8") as f:
                                f.write(json.dumps(placed_order, ensure_ascii=False) + "\n")
                            
                            order_recorded = True
                            print(f"[MARKET ORDER] ✅ Fallback: Successfully wrote {symbol} SELL order to {filled_file}")
                            
                            # 如果 pending_orders.jsonl 中有这个订单，移除它
                            pending_file = order_manager.pending_orders_file
                            if pending_file.exists() and placed_order.get("order_id"):
                                try:
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
                                    
                                    pending_file.parent.mkdir(parents=True, exist_ok=True)
                                    with pending_file.open("w", encoding="utf-8") as f:
                                        for o in all_pending:
                                            f.write(json.dumps(o, ensure_ascii=False) + "\n")
                                    print(f"[MARKET ORDER] ✅ Removed {symbol} SELL order from pending (remaining: {len(all_pending)})")
                                except Exception as e3:
                                    print(f"[MARKET ORDER] ⚠️ WARNING: Failed to clean pending_orders.jsonl: {e3}")
                        except Exception as e2:
                            print(f"[MARKET ORDER] ❌ ERROR: Fallback method also failed for SELL: {e2}")
                            import traceback
                            traceback.print_exc()
                    
                    # 方法3: 最后保障 - 如果所有方法都失败，至少记录到 trades.jsonl
                    if not order_recorded:
                        print(f"[MARKET ORDER] ⚠️ CRITICAL: All order recording methods failed for SELL, logging to trades.jsonl as backup")
                        try:
                            trade_logger.log(
                                symbol=symbol,
                                action="SELL",
                                price=current_price,
                                quantity=quantity,
                                amount=current_price * quantity,
                                status="SUCCESS",
                                reason=f"Order recorded via fallback (order_id: {placed_order.get('order_id') if placed_order else 'N/A'}, realized_pnl: ${realized_pnl.get('realized_pnl', 0):.2f})",
                            )
                            print(f"[MARKET ORDER] ✅ Backup: Logged {symbol} SELL trade to trades.jsonl")
                        except Exception as e3:
                            print(f"[MARKET ORDER] ❌ CRITICAL ERROR: Even backup logging failed for SELL: {e3}")
                            print(f"[MARKET ORDER] ⚠️⚠️⚠️ CRITICAL: SELL order may be lost! {symbol} SELL x{quantity} @ ${current_price:.2f}, realized_pnl=${realized_pnl.get('realized_pnl', 0):.2f}")
                    
                    # 确保 placed_order 存在（用于后续代码）
                    if not placed_order:
                        # datetime already imported at top
                        now = datetime.now(timezone.utc)
                        placed_order = {
                            "order_id": f"{symbol}_SELL_{now.date().isoformat()}_{now.timestamp()}",
                            "symbol": symbol,
                            "action": "SELL",
                            "quantity": quantity,
                            "limit_price": current_price,
                            "status": "FILLED" if order_recorded else "UNKNOWN",
                        }
                        if realized_pnl:
                            placed_order["realized_pnl"] = realized_pnl.get("realized_pnl", 0.0)
                    
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
                    "timestamp": get_utc_timestamp(),
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
                "timestamp": get_utc_timestamp(),
                "snapshot": {
                    "cash": portfolio.cash,
                    "total_value": total_value,
                    "equity_value": equity_value,
                    "positions_count": len(portfolio._positions),
                }
            }
            
            # CRITICAL FIX: Include current_price and market_value in portfolio_state for consistency
            # This ensures portfolio_state.json contains complete position information
            for symbol, pos in portfolio._positions.items():
                # Get current price from last_prices if available
                current_price = last_prices.get(symbol) if last_prices else None
                market_value = (current_price * pos.quantity) if current_price else None
                
                position_data = {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": pos.total_cost if hasattr(pos, 'total_cost') and pos.total_cost > 0 else pos.avg_cost * pos.quantity,
                }
                
                # Add price information if available
                if current_price is not None:
                    position_data["current_price"] = current_price
                if market_value is not None:
                    position_data["market_value"] = market_value
                
                portfolio_state["positions"][symbol] = position_data
            
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
                            "timestamp": get_utc_timestamp()
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
        
        # CRITICAL FIX: Save portfolio_state.json again with updated_positions_info (contains current_price and market_value)
        # This ensures portfolio_state.json always has the latest complete position information
        if portfolio and updated_positions_info:
            try:
                portfolio_file = _get_project_logs_dir() / "portfolio_state.json"
                
                portfolio_state = {
                    "cash": portfolio.cash,
                    "initial_value": portfolio.initial_value,
                    "total_value": total_value,
                    "positions": updated_positions_info,  # Use updated_positions_info with complete price information
                    "timestamp": get_utc_timestamp(),
                    "snapshot": {
                        "cash": portfolio.cash,
                        "total_value": total_value,
                        "equity_value": equity_value,
                        "positions_count": len(portfolio._positions),
                    }
                }
                
                portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
                print(f"[TRADING CYCLE] Updated portfolio_state.json with complete position information (including prices)")
            except Exception as e:
                print(f"[TRADING CYCLE] ⚠️  Failed to update portfolio_state.json with prices: {e}")
    except Exception as e:
        print(f"[MEMORY WARN] Failed to save memory/equity: {e}")
        # Log error to error logger
        try:
            from src.utils.error_logger import get_error_logger, ErrorLevel
            error_logger = get_error_logger(root=str(_get_project_logs_dir()))
            error_logger.error(
                message="Failed to save memory/equity",
                component="trading_cycle",
                exception=e,
                context={"function": "save_memory_equity"}
            )
        except Exception:
            pass  # Ignore logging errors
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
