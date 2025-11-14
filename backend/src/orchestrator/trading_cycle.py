# src/orchestrator/trading_cycle.py
from __future__ import annotations
from typing import Dict, Any, List, Tuple, Optional
from datetime import date, timedelta, datetime, timezone, time as dt_time
from pathlib import Path  # 统一在文件顶部导入，避免函数内部重复导入导致的作用域问题
import json  # 用于加载 portfolio_state.json

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
    # CRITICAL: 确保 end 参数正确设置（用于获取市场数据）
    # 如果 end 是 None（实时模式），使用昨天的日期（因为今天的数据可能还不完整）
    # 如果 end 是特定日期（规划模式），使用该日期
    market_data_end = end if end else (date.today() - timedelta(days=1)).isoformat()
    print(f"[TRADING CYCLE] Fetching market data: start={start}, end={market_data_end}")
    
    try:
        market_view: Dict[str, Any] = fetch_market_batch.invoke({
            "symbols": universe,
            "start": start,
            "end": market_data_end,
        })
        print(f"[TRADING CYCLE] Market data fetched successfully: {len(market_view.get('stocks', {}))} stocks")
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
        # CRITICAL: 尝试从 portfolio_state.json 加载现有状态，而不是创建新的空 Portfolio
        portfolio_file = Path("data/logs/portfolio_state.json")
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
    
    # 计算初步可用现金
    from src.utils.config_loader import load_config
    config = load_config()
    MIN_CASH_RESERVE_RATIO = config.get("min_cash_reserve_ratio", 0.20)
    required_cash_reserve = preliminary_portfolio_value * MIN_CASH_RESERVE_RATIO
    preliminary_available_cash = max(0, portfolio.cash - required_cash_reserve) if portfolio else 0.0
    
    convo = run_multi_analyst_discussion(
        market_view=market_view,  # 传入完整的market_view
        use_tools=auto_tools,
        tool_budget=tool_budget,
        order_status=order_status,  # 传入订单状态
        current_positions=preliminary_positions_info if preliminary_positions_info else None,  # 传入仓位信息
        portfolio_value=preliminary_portfolio_value,  # 传入组合净值
        available_cash=preliminary_available_cash,  # 传入可用现金
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
                        "tools_used": entry_data.get("tools_used", []),
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
                "tools_used": tools_used,
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
                    "tools_used": [],  # Coordinator 不使用工具
                }
                with convo_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                print(f"[TRADING CYCLE] Wrote Coordinator from coordinator_summary (stance: {stance})")
        elif coordinator_summary and coordinator_found_in_history:
            print(f"[TRADING CYCLE] Skipped writing coordinator_summary (Coordinator already exists in discussion_history)")
        
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
            # 处理双重嵌套：{"ok": true, "result": {"ok": true, "result": {...}}}
            # 递归提取实际的 result 数据
            actual_result = tool_result
            if isinstance(tool_result, dict):
                while isinstance(actual_result, dict) and "ok" in actual_result and "result" in actual_result:
                    actual_result = actual_result["result"]
            
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
                        # 对于新闻工具，尝试保留完整的 hits 数组（即使截断，也要确保 hits 数组是完整的）
                        if tool_name in ["news_scan", "plan_and_scan_news"] and "hits" in actual_result:
                            # 保留完整的 hits 数组，只截断其他部分
                            hits_json = json.dumps(actual_result.get("hits", []), ensure_ascii=False, indent=2)
                            queries_json = json.dumps(actual_result.get("queries", []), ensure_ascii=False)
                            # 构建一个简化的结果，但保留完整的 hits
                            simplified = {
                                "hits": actual_result.get("hits", []),
                                "queries": actual_result.get("queries", [])
                            }
                            result_text = json.dumps(simplified, ensure_ascii=False, indent=2)
                            # 如果还是太长，至少保留前几个 hits
                            if len(result_text) > max_length:
                                # 保留前 N 个 hits，确保 JSON 完整
                                hits = actual_result.get("hits", [])
                                max_hits = min(len(hits), 10)  # 最多保留10个新闻
                                simplified["hits"] = hits[:max_hits]
                                result_text = json.dumps(simplified, ensure_ascii=False, indent=2)
                                if len(result_text) > max_length:
                                    result_text = result_text[:max_length] + "\n... (truncated, showing first " + str(max_hits) + " hits)"
                        else:
                            result_text = result_text[:max_length] + "\n... (truncated)"
            else:
                result_text = str(actual_result)
                if len(result_text) > 2000:
                    result_text = result_text[:2000] + "... (truncated)"
            
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
        # CRITICAL FIX: 市场收盘后，允许运行对话（AI分析），但不执行交易
        # 继续执行对话和分析，但跳过订单创建和执行
        print(f"[TRADING CYCLE] Market closed. Running conversation/analysis only (no trading).")
        # 设置标志，后续跳过订单执行
        is_market_open_for_simulation = False
        today = date.today().isoformat()
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
            o.get("order_date")
            for o in all_pending_orders
            if o.get("order_date") and o.get("order_date") < today_str
        })
        for stale_date in stale_dates:
            cancelled = order_manager.cancel_orders(order_date=stale_date)
            if cancelled > 0:
                print(f"[TRADING CYCLE] Removed {cancelled} stale pending orders from {stale_date}")

        # 重新加载（排除已清理的旧订单）
        all_pending_orders = order_manager.load_pending_orders()
        
        from src.utils.trading_days import get_next_trading_day
        tomorrow_str = get_next_trading_day(date.today(), days_ahead=1).isoformat()
        
        today_orders = [o for o in all_pending_orders if o.get("order_date") == today_str]
        tomorrow_orders = [o for o in all_pending_orders if o.get("order_date") == tomorrow_str]
        
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
            print(f"[TRADING CYCLE] ⚠️ Found {len(all_pending_orders)} total pending orders ({len(today_orders)} for today, {len(tomorrow_orders)} for tomorrow)")
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
                        filled_file = Path("data/logs/filled_orders.jsonl")
                        today_has_filled_orders = False
                        if filled_file.exists() and not end:  # 只在实时模式下检查
                            try:
                                with filled_file.open("r", encoding="utf-8") as f:
                                    for line in f:
                                        if line.strip():
                                            filled_order = json.loads(line)
                                            if filled_order.get("order_date") == today and filled_order.get("status") == "FILLED":
                                                today_has_filled_orders = True
                                                break
                            except Exception:
                                pass
                        
                        if today_has_filled_orders and not end:
                            print(f"[TRADING CYCLE] ⚠️ Today already has filled orders. Skipping new order creation to prevent hourly duplicates.")
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
            # 市场收盘后，如果有pending订单（明天的订单），不创建新订单
            # 但仍然返回完整的结果，包括讨论和分析
            print(f"[TRADING CYCLE] Skipping order creation - {len(existing_pending_orders)} pending orders already exist for {today}")
            # 将现有pending订单设置为placed_orders，这样验证函数可以检查
            placed_orders = existing_pending_orders
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
                print(f"[TRADING CYCLE] Loaded position limits from config.json:")
                print(f"  - max_position_per_stock: {position_config['max_position_per_stock']:.1%}")
                print(f"  - max_total_position: {position_config['max_total_position']:.1%}")
                print(f"  - min_position_per_stock: {position_config['min_position_per_stock']:.1%}")
        else:
            print(f"[TRADING CYCLE] ⚠️ Config file not found at {config_path}, using default position limits")
    except Exception as e:
        # 如果读取失败，使用默认值
        print(f"[TRADING CYCLE] ⚠️ Failed to load position limits from config: {e}, using defaults")

    # 计算可用现金（考虑现金储备要求）
    # 先计算，以便传递给 trader agent
    from src.utils.config_loader import load_config
    config = load_config()
    MIN_CASH_RESERVE_RATIO = config.get("min_cash_reserve_ratio", 0.20)  # Keep 20% cash
    required_cash_reserve = portfolio_value * MIN_CASH_RESERVE_RATIO
    available_cash_for_trading = max(0, portfolio.cash - required_cash_reserve)
    
    print(f"[TRADING CYCLE] Portfolio cash: ${portfolio.cash:.2f}, required reserve: ${required_cash_reserve:.2f}, available for trading: ${available_cash_for_trading:.2f}")
    
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
    )
    
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
            # Check signal scores (signal_score range is now 0-10, threshold is 3.0)
            stocks = enriched_market.get("stocks", {})
            high_signal_stocks = [s for s, d in stocks.items() if isinstance(d, dict) and float(d.get("signal_score", 0)) > 3.0]
            print(f"[TRADING CYCLE] Debug: {len(high_signal_stocks)} stocks with signal_score > 3.0: {high_signal_stocks[:5]}")
            # Also check top 10 by signal_score
            sorted_stocks = sorted(
                [(s, d) for s, d in stocks.items() if isinstance(d, dict)],
                key=lambda x: float(x[1].get("signal_score", 0)),
                reverse=True
            )
            top_10 = sorted_stocks[:10]
            print(f"[TRADING CYCLE] Debug: Top 10 stocks by signal_score: {[(s, d.get('signal_score', 0)) for s, d in top_10]}")
    
    # Process trading decisions (only if no existing pending orders, or in multi-day simulation)
    # CRITICAL FIX: 在实时模式下，额外检查今天是否已经有pending或filled订单
    # 如果有，就不应该再创建新订单，避免每小时重复创建
    # CRITICAL FIX: 市场关闭时，不允许创建订单
    should_create_orders = False
    if end is not None:
        # 多日模拟模式：允许创建订单（假设市场开放）
        should_create_orders = True
    elif is_market_open_for_simulation:
        # 实时模式：只有在市场开放时才检查是否可以创建订单
        if not existing_pending_orders:
            # 检查今天是否已经有filled订单
            filled_file = Path("data/logs/filled_orders.jsonl")
            today_has_any_orders = False
            if filled_file.exists():
                try:
                    with filled_file.open("r", encoding="utf-8") as f:
                        for line in f:
                            if line.strip():
                                filled_order = json.loads(line)
                                if filled_order.get("order_date") == today:
                                    today_has_any_orders = True
                                    break
                except Exception:
                    pass
            
            # 如果今天没有任何订单（pending或filled），才允许创建新订单
            should_create_orders = not today_has_any_orders
            if today_has_any_orders:
                print(f"[TRADING CYCLE] ⚠️ Today already has orders (filled or pending). Skipping new order creation to prevent hourly duplicates.")
        else:
            # 有pending订单，不创建新订单
            should_create_orders = False
    else:
        # 市场关闭：不允许创建订单
        should_create_orders = False
        print(f"[TRADING CYCLE] Market is closed. Skipping order creation (should_create_orders=False).")
    
    if should_create_orders:
        # === OPTIMIZATION: Position limits (移除 cooldown 检查) ===
        from src.utils.config_loader import load_config
        
        # Load configuration for limits
        config = load_config()
        MAX_POSITIONS = config.get("max_positions", 10)  # Maximum number of different stocks
        # 移除 TRADE_COOLDOWN_HOURS（不再使用冷却期限制）
        # TRADE_COOLDOWN_HOURS = config.get("trade_cooldown_hours", 24.0)  # 已移除
        MIN_CASH_RESERVE_RATIO = config.get("min_cash_reserve_ratio", 0.20)  # Keep 20% cash
        
        # 移除 trade history tracker（不再需要冷却期检查）
        # trade_history = TradeHistoryTracker(root="data/logs")  # 已移除
        
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
                    
                    # 获取当前市价
                    import yfinance as yf
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.fast_info
                        current_price = info.get("lastPrice") or info.get("regularMarketPrice")
                        if not current_price:
                            # 如果获取不到实时价格，使用buy_price作为后备
                            current_price = buy_price
                            print(f"[MARKET ORDER] Warning: Could not get real-time price for {symbol}, using buy_price ${current_price:.2f}")
                        else:
                            current_price = float(current_price)
                    except Exception as e:
                        # 如果获取价格失败，使用buy_price作为后备
                        current_price = buy_price
                        print(f"[MARKET ORDER] Warning: Failed to get real-time price for {symbol}: {e}, using buy_price ${current_price:.2f}")
                    
                    # 使用当前市价重新计算成本和数量
                    estimated_cost = current_price * quantity
                    
                    # 检查现金是否足够（使用市价）
                    if estimated_cost > remaining_cash:
                        max_affordable_qty = floor(remaining_cash / current_price)
                        if max_affordable_qty > 0:
                            quantity = max_affordable_qty
                            estimated_cost = current_price * quantity
                            print(f"[MARKET ORDER] Reduced {symbol} quantity to {quantity} due to cash limit (remaining cash: ${remaining_cash:.2f})")
                        else:
                            execution_errors.append(f"BUY {symbol} skipped: insufficient cash (need ${estimated_cost:.2f}, remaining ${remaining_cash:.2f})")
                            continue
                    
                    # CRITICAL: 扣除已使用的现金（在创建订单前）
                    remaining_cash -= estimated_cost
                    print(f"[CASH TRACKING] Order for {symbol}: cost=${estimated_cost:.2f}, remaining cash=${remaining_cash:.2f}")
                    
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
                        order_date=today,
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
                    order_manager.mark_order_filled(placed_order, fill_result)
                    
                    # 更新投资组合（立即执行交易）
                    portfolio.buy(symbol, quantity, current_price)
                    
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
                    
                    # 获取当前市价
                    import yfinance as yf
                    try:
                        ticker = yf.Ticker(symbol)
                        info = ticker.fast_info
                        current_price = info.get("lastPrice") or info.get("regularMarketPrice")
                        if not current_price:
                            # 如果获取不到实时价格，使用sell_price作为后备
                            current_price = sell_price
                            print(f"[MARKET ORDER] Warning: Could not get real-time price for {symbol}, using sell_price ${current_price:.2f}")
                        else:
                            current_price = float(current_price)
                    except Exception as e:
                        # 如果获取价格失败，使用sell_price作为后备
                        current_price = sell_price
                        print(f"[MARKET ORDER] Warning: Failed to get real-time price for {symbol}: {e}, using sell_price ${current_price:.2f}")
                    
                    # 市价单：使用当前价格
                    limit_price = current_price
                    total_proceeds = current_price * quantity
                    
                    # 市价单：立即成交，不挂单
                    # 创建订单记录（标记为已成交）
                    placed_order = order_manager.place_order(
                        symbol=symbol,
                        action="SELL",
                        quantity=quantity,
                        limit_price=current_price,  # 市价单：使用当前价格
                        price_range={
                            "min": current_price,
                            "max": current_price,
                        },
                        order_date=today,
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
                    order_manager.mark_order_filled(placed_order, fill_result)
                    
                    # 更新投资组合（立即执行交易）
                    portfolio.sell(symbol, quantity, current_price)
                    
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
    
    # 写入Trader Agent的conversation entry（在订单创建后，以便反映实际创建的订单数量）
    try:
        # 更新 summary 以反映实际创建的订单数量
        trader_summary = trader_summary_original
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
        
        trader_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "date": trade_date_str,
            "agent": "TraderAgent",
            "round": 0,
            "content": f"Stance: {trader_stance}\n\nAnalysis: {trader_summary}",
            "type": "discussion",
            "stance": trader_stance,
            "tools_used": [],  # Trader Agent不使用工具，它是基于其他agent的分析做决策
        }
        
        with convo_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(trader_entry, ensure_ascii=False) + "\n")
        
        print(f"[TRADING CYCLE] Wrote Trader Agent conversation entry with summary (actual orders: {actual_buy_orders_count} buy, {actual_sell_orders_count} sell)")
    except Exception as e:
        print(f"[TRADING CYCLE] ⚠️  Failed to write Trader Agent conversation entry: {e}")
    
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
    # 注意：discussion_history 已经在 multi_analyst_system 中自动限制长度
    # 这里可以添加其他内存清理逻辑（如果需要）
    import gc
    gc.collect()  # 强制垃圾回收，释放未使用的内存
    print("[MEMORY] Trading cycle completed, memory cleaned")

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
