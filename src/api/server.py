# src/api/server.py
"""
FastAPI backend for real-time agent monitoring and frontend integration.
Provides WebSocket for real-time updates and REST API for historical data.
"""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Dict, Any
import random
from pathlib import Path
import json
import asyncio
from datetime import datetime, timezone, date, timedelta
from datetime import time as dt_time
import uuid
import sys
import os

from src.core.event_bus import EventBus, AgentEvent

app = FastAPI(
    title="AI Trader API",
    description="Real-time agent monitoring and trading cycle API",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global event bus
event_bus = EventBus.get_instance()

# Active WebSocket connections
active_connections: List[WebSocket] = []


def broadcast_event(event: AgentEvent):
    """Broadcast event to all connected WebSocket clients"""
    if not active_connections:
        return
    
    message = json.dumps({
        "type": "agent_event",
        "data": {
            "timestamp": event.timestamp,
            "agent_name": event.agent_name,
            "event_type": event.event_type,
            "status": event.status,
            "payload": event.payload,
            "round_number": event.round_number,
            "session_id": event.session_id,
        }
    })
    
    # Broadcast to all connections (async-safe)
    disconnected = []
    for connection in active_connections:
        try:
            asyncio.create_task(connection.send_text(message))
        except Exception:
            disconnected.append(connection)
    
    # Remove disconnected clients
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


# Subscribe event bus to WebSocket broadcaster
event_bus.subscribe(broadcast_event)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time agent updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        # Send current status on connection
        status = event_bus.get_all_agents_status()
        await websocket.send_json({
            "type": "initial_status",
            "data": status
        })
        
        # Keep connection alive
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.get("/api/agents/status")
async def get_agents_status():
    """Get current status of all agents"""
    return event_bus.get_all_agents_status()


@app.get("/api/agents/{agent_name}/status")
async def get_agent_status(agent_name: str):
    """Get status of a specific agent"""
    return event_bus.get_agent_status(agent_name)


@app.get("/api/history")
async def get_history(
    agent_name: str | None = None,
    event_type: str | None = None,
    limit: int = 100,
    session_id: str | None = None
):
    """Get event history"""
    events = event_bus.get_history(
        agent_name=agent_name,
        event_type=event_type,
        limit=limit,
        session_id=session_id
    )
    return {"events": events, "count": len(events)}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """Get full history of a trading session"""
    events = event_bus.get_history(session_id=session_id, limit=1000)
    return {
        "session_id": session_id,
        "events": events,
        "count": len(events)
    }


@app.post("/api/trading/execute")
async def execute_trading_cycle():
    """Trigger a new trading cycle"""
    from src.orchestrator.trading_cycle import execute_daily_trade
    
    # 完全避免使用 print，使用日志文件记录（可选）
    def log_to_file(msg):
        """将日志写入文件，完全不依赖 stdout/stderr"""
        try:
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / "api_execution.log"
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} {msg}\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass  # 完全静默，不抛出任何异常
    
    # 从 config.json 读取股票清单
    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    universe = None  # None 会使用 execute_daily_trade 的默认值
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    universe = config_data["universe"]
                    log_to_file(f"[Trading Cycle] 使用 config.json 中的股票清单: {len(universe)} 只股票")
        except Exception as e:
            log_to_file(f"[Trading Cycle] 读取 config.json 失败，使用默认清单: {e}")
    
    session_id = str(uuid.uuid4())
    
    # Emit session start event
    event_bus.emit(AgentEvent(
        timestamp=datetime.now().isoformat(),
        agent_name="Orchestrator",
        event_type="session_start",
        status="running",
        payload={"session_id": session_id},
        session_id=session_id
    ))
    
    try:
        # Execute trading cycle
        result = execute_daily_trade(
            rounds=3,
            auto_tools=True,
            tool_budget=20,  # 增加到20，允许LLM使用所有工具
            universe=universe  # 使用从 config.json 读取的股票清单（如果存在）
        )
        
        # Emit session end event
        event_bus.emit(AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name="Orchestrator",
            event_type="session_end",
            status="success",
            payload={"result": result},
            session_id=session_id
        ))
        
        return {
            "session_id": session_id,
            "result": result,
            "status": "success"
        }
    except Exception as e:
        # 完全避免使用 print，使用日志文件记录
        def log_to_file(msg):
            """将日志写入文件，完全不依赖 stdout/stderr"""
            try:
                logs_dir = Path("data/logs")
                logs_dir.mkdir(parents=True, exist_ok=True)
                log_file = logs_dir / "api_execution.log"
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} {msg}\n")
                    f.flush()
                    os.fsync(f.fileno())
            except Exception:
                pass  # 完全静默，不抛出任何异常
        
        error_msg = str(e)
        log_to_file(f"[Trading Cycle ERROR] {error_msg}")
        
        # 尝试获取完整 traceback（也写入文件）
        import traceback
        try:
            error_trace = traceback.format_exc()
            log_to_file(f"[Trading Cycle ERROR] Traceback:\n{error_trace}")
        except Exception:
            pass
        
        event_bus.emit(AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name="Orchestrator",
            event_type="session_error",
            status="error",
            payload={"error": error_msg},
            session_id=session_id
        ))
        return JSONResponse(
            status_code=500,
            content={"error": error_msg, "session_id": session_id}
        )


@app.get("/api/portfolio/equity-history")
async def get_equity_history(
    start_date: str | None = None,
    end_date: str | None = None,
    limit: int | None = None,
):
    """
    Get portfolio equity history for chart visualization
    
    Parameters:
    - start_date: Start date (YYYY-MM-DD)
    - end_date: End date (YYYY-MM-DD)
    - limit: Maximum number of records to return
    """
    try:
        from src.data.equity_tracker import EquityTracker
        
        equity_tracker = EquityTracker(root="data/logs")
        records = equity_tracker.load_equity_history(
            start_date=start_date,
            end_date=end_date,
            limit=limit,
        )
        
        return {
            "ok": True,
            "records": records,
            "count": len(records),
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/portfolio/current")
async def get_current_portfolio():
    """Get current portfolio status (from equity history)"""
    try:
        from src.data.equity_tracker import EquityTracker
        
        equity_tracker = EquityTracker(root="data/logs")
        latest = equity_tracker.get_latest_equity()
        
        if latest:
            return {
                "ok": True,
                "portfolio": latest,
            }
        else:
            return {
                "ok": True,
                "portfolio": None,
                "message": "No portfolio data available",
            }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/portfolio/real-time")
async def get_real_time_portfolio():
    """Get real-time portfolio with current market prices"""
    try:
        import json
        from pathlib import Path
        
        # Load portfolio state (尝试多个可能的路径)
        state_file = Path("data/logs/portfolio_state.json")
        if not state_file.exists():
            # 尝试相对于 backend 目录
            backend_root = Path(__file__).parent.parent.parent
            state_file = backend_root / "data" / "logs" / "portfolio_state.json"
            if not state_file.exists():
                # 尝试相对于项目根目录
                project_root = backend_root.parent if backend_root.name == "backend" else backend_root
                state_file = project_root / "backend" / "data" / "logs" / "portfolio_state.json"
        
        if not state_file.exists():
            # Fallback to demo snapshot so the frontend can render
            print(f"[WARN] portfolio_state.json not found at any location, using demo data")
            from fastapi import Request
            demo = await demo_real_time_portfolio()  # type: ignore
            return demo
        
        print(f"[INFO] Loading portfolio state from: {state_file}")
        
        with state_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        print(f"[INFO] Portfolio state loaded: cash=${state.get('cash', 0):.2f}, positions={len(state.get('positions', {}))}")
        
        from src.data.portfolio import Portfolio, Position
        portfolio = Portfolio(
            cash=float(state.get("cash", 10000.0)),
            initial_value=float(state.get("initial_value", 10000.0)),
        )
        
        # Restore positions
        positions = state.get("positions", {})
        for symbol, pos_info in positions.items():
            if isinstance(pos_info, dict):
                quantity = int(pos_info.get("quantity", 0))
                avg_cost = float(pos_info.get("avg_cost", 0.0))
                total_cost = float(pos_info.get("total_cost", 0.0))
                # 如果total_cost没有保存或为0，从avg_cost和quantity计算
                if total_cost <= 0:
                    total_cost = avg_cost * quantity
                
                if quantity > 0:  # 只恢复有效持仓
                    portfolio._positions[symbol] = Position(
                        symbol=symbol,
                        quantity=quantity,
                        avg_cost=avg_cost,
                        total_cost=total_cost,
                    )
                    print(f"[INFO] Restored position: {symbol} x{quantity} @ ${avg_cost:.2f}, total_cost=${total_cost:.2f}")
        
        print(f"[INFO] Portfolio restored: {len(portfolio._positions)} positions, cash=${portfolio.cash:.2f}")
        
        # If there are no positions, avoid external data calls and return simple snapshot
        if len(portfolio._positions) == 0:
            total_value = portfolio.cash
            snapshot = {
                "ok": True,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "initial_value": portfolio.initial_value,
                "total_value": round(total_value, 2),
                "total_pnl": round(total_value - portfolio.initial_value, 2),
                "total_pnl_pct": 0.0,
                "cash": round(portfolio.cash, 2),
                "equity_value": 0.0,
                "positions": {},
                "positions_pnl": {},
                "source": "simple",
            }
        else:
            # Get real-time snapshot via tracker (with fallback if yfinance missing)
            try:
                from src.data.real_time_tracker import RealTimeTracker
                tracker = RealTimeTracker(root="data/logs")
                snapshot = tracker.update_and_record(portfolio)
            except (ImportError, ModuleNotFoundError) as e:
                # Fallback if yfinance or other deps missing
                # 即使没有实时价格，也要正确计算P&L（使用成本价作为当前价，所以P&L=0是合理的）
                equity = sum((pos_info.get("avg_cost", 0) * pos_info.get("quantity", 0)) for pos_info in positions.values() if isinstance(pos_info, dict))
                total_value = portfolio.cash + equity
                positions_detail = {}
                positions_pnl = {}
                for sym, pos_info in positions.items():
                    if isinstance(pos_info, dict):
                        qty = int(pos_info.get("quantity", 0))
                        avg = float(pos_info.get("avg_cost", 0))
                        total_cost = float(pos_info.get("total_cost", 0))
                        # 如果total_cost没有保存或为0，从avg_cost和quantity计算
                        if total_cost <= 0:
                            total_cost = avg * qty
                        
                        # 尝试从yfinance获取实时价格（如果可用）
                        current_price = avg  # 默认使用平均成本
                        try:
                            import yfinance as yf
                            ticker = yf.Ticker(sym)
                            info = ticker.info
                            current_price = float(info.get("regularMarketPrice") or info.get("currentPrice") or info.get("previousClose") or avg)
                        except Exception:
                            # 如果获取失败，使用平均成本
                            current_price = avg
                        
                        market_value = current_price * qty  # 市场价值
                        # 计算未实现损益（市场价值 - 成本价格）
                        unrealized_pnl = market_value - total_cost
                        unrealized_pnl_pct = (unrealized_pnl / total_cost * 100) if total_cost > 0 else 0.0
                        
                        positions_detail[sym] = {
                            "quantity": qty,
                            "avg_cost": round(avg, 2),
                            "current_price": round(current_price, 2),
                            "market_value": round(market_value, 2),
                            "cost_basis": round(total_cost, 2),
                        }
                        positions_pnl[sym] = {
                            "unrealized_pnl": round(unrealized_pnl, 2),
                            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                        }
                snapshot = {
                    "ok": True,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "initial_value": float(portfolio.initial_value),
                    "total_value": round(float(total_value), 2),
                    "total_pnl": round(float(total_value - portfolio.initial_value), 2),
                    "total_pnl_pct": round(((float(total_value) - float(portfolio.initial_value)) / float(portfolio.initial_value) * 100) if portfolio.initial_value > 0 else 0, 2),
                    "cash": round(float(portfolio.cash), 2),
                    "equity_value": round(float(equity), 2),
                    "positions": positions_detail,
                    "positions_pnl": positions_pnl,
                    "source": "simple",
                }
        
        return {"ok": True, **snapshot}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[ERROR] /api/portfolio/real-time failed: {e}")
        print(f"[ERROR] Traceback:\n{error_trace}")
        
        # 如果出错，返回一个基本的空投资组合状态，避免前端崩溃
        try:
            fallback_snapshot = {
                "ok": True,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "initial_value": 10000.0,
                "total_value": 10000.0,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "cash": 10000.0,
                "equity_value": 0.0,
                "positions": {},
                "positions_pnl": {},
                "source": "fallback",
                "error": str(e),
            }
            return {"ok": True, **fallback_snapshot}
        except Exception as fallback_error:
            # 如果连fallback都失败，返回最简单的响应
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False, 
                    "error": str(e),
                    "fallback_error": str(fallback_error),
                    "message": "Failed to load portfolio state. Please try initializing the system."
                }
            )


@app.get("/api/portfolio/recent-snapshots")
async def get_recent_snapshots(hours: int = 24):
    """Get recent real-time snapshots"""
    try:
        from src.data.real_time_tracker import RealTimeTracker
        tracker = RealTimeTracker(root="data/logs")
        snapshots = tracker.get_recent_snapshots(hours=hours)
        return {"ok": True, "snapshots": snapshots, "count": len(snapshots)}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/tools/list")
async def list_tools():
    """Return an empty tool list in minimal demo mode to avoid optional deps."""
    return {"ok": True, "tools": []}


@app.get("/api/demo/real-time")
async def demo_real_time_portfolio(volatility_bps: int = 15):
    """Generate a simulated real-time portfolio snapshot (demo mode).

    - Updates every call with a small random walk on prices
    - Persists last demo prices to data/logs/demo_prices.json
    - Appends snapshot to data/logs/real_time_snapshots.jsonl
    - Returns the same schema as /api/portfolio/real-time

    volatility_bps: per-tick volatility in basis points (default 15bps = 0.15%)
    """
    try:
        import json
        from datetime import datetime

        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)

        # Load portfolio state; create a demo one if not exists
        state_file = logs_dir / "portfolio_state.json"
        if state_file.exists():
            with state_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
        else:
            # Seed a simple demo portfolio
            state = {
                "cash": 2500.0,
                "initial_value": 10000.0,
                "positions": {
                    "NVDA": {"quantity": 5, "avg_cost": 900.0, "total_cost": 4500.0},
                    "MSFT": {"quantity": 7, "avg_cost": 420.0, "total_cost": 2940.0},
                    "AAPL": {"quantity": 10, "avg_cost": 190.0, "total_cost": 1900.0},
                },
            }

        positions: Dict[str, Any] = state.get("positions", {})

        # Load or initialize last demo prices
        demo_prices_file = logs_dir / "demo_prices.json"
        if demo_prices_file.exists():
            with demo_prices_file.open("r", encoding="utf-8") as f:
                last_prices: Dict[str, float] = json.load(f)
        else:
            last_prices = {sym: float(info.get("avg_cost", 0.0)) for sym, info in positions.items()}

        # Simulate price changes with random walk
        sigma = max(1, int(volatility_bps)) / 10000.0  # convert bps to fraction
        new_prices: Dict[str, float] = {}
        for sym, info in positions.items():
            base = float(last_prices.get(sym, info.get("avg_cost", 0.0)) or info.get("avg_cost", 0.0))
            # random change in +/- ~3 sigma cap
            drift = random.uniform(-3*sigma, 3*sigma)
            price = max(0.01, base * (1.0 + drift))
            new_prices[sym] = round(price, 4)

        # Build portfolio snapshot
        cash = float(state.get("cash", 0.0))
        initial_value = float(state.get("initial_value", 10000.0))
        positions_detail: Dict[str, Any] = {}
        positions_pnl: Dict[str, Any] = {}
        equity_value = 0.0
        total_unrealized = 0.0

        for sym, info in positions.items():
            qty = int(info.get("quantity", 0))
            avg = float(info.get("avg_cost", 0.0))
            px = float(new_prices.get(sym, avg))
            mv = qty * px
            equity_value += mv
            unreal = (px - avg) * qty
            total_unrealized += unreal
            pnl_pct = ((px - avg) / avg * 100.0) if avg > 0 else 0.0

            positions_detail[sym] = {
                "quantity": qty,
                "avg_cost": round(avg, 4),
                "current_price": round(px, 4),
                "market_value": round(mv, 2),
            }
            positions_pnl[sym] = {
                "unrealized_pnl": round(unreal, 2),
                "unrealized_pnl_pct": round(pnl_pct, 3),
            }

        total_value = cash + equity_value
        total_pnl = total_value - initial_value
        total_pnl_pct = (total_pnl / initial_value * 100.0) if initial_value > 0 else 0.0

        snapshot = {
            "ok": True,
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "initial_value": round(initial_value, 2),
            "total_value": round(total_value, 2),
            "total_pnl": round(total_pnl, 2),
            "total_pnl_pct": round(total_pnl_pct, 3),
            "cash": round(cash, 2),
            "equity_value": round(equity_value, 2),
            "positions": positions_detail,
            "positions_pnl": positions_pnl,
            "source": "demo",
        }

        # Persist latest prices
        with demo_prices_file.open("w", encoding="utf-8") as f:
            json.dump(new_prices, f, ensure_ascii=False, indent=2)

        # Append to real-time snapshots jsonl
        rts_file = logs_dir / "real_time_snapshots.jsonl"
        with rts_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")

        return snapshot
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.post("/api/demo/conversation-tick")
async def demo_conversation_tick():
    """Append a synthetic agent conversation entry for demo display.

    This helps the frontend Conversations modal show activity in demo mode.
    """
    try:
        import json
        from datetime import datetime

        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        convo_file = logs_dir / "discussion_actions.jsonl"

        agents = [
            "MarketAgent",
            "MarketAnalyst",
            "DiscussionAgent",
            "RiskAnalyst",
            "TraderAgent",
        ]
        messages = [
            "Scanning market breadth & volatility regime...",
            "Top signals: momentum up, looking at NVDA/MSFT/AAPL weighting...",
            "Consensus forming: mild bullish with hedged exposure.",
            "Risk limits OK. Position size within constraints.",
            "Placing demo limit orders within price bands.",
        ]

        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            "agent": random.choice(agents),
            "round": random.randint(1, 3),
            "content": random.choice(messages),
            "type": "demo",
        }

        with convo_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        return {"ok": True, "written": True, "entry": entry}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})


@app.get("/api/trades/recent")
async def get_recent_trades(limit: int = 100):
    """Return recent trade records from logs (filled and general)."""
    try:
        import json
        from datetime import datetime

        logs_dir = Path("data/logs")
        trades_file = logs_dir / "trades.jsonl"
        filled_file = logs_dir / "filled_orders.jsonl"

        def read_jsonl(path: Path) -> list[dict]:
            if not path.exists():
                return []
            items: list[dict] = []
            with path.open("r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        items.append(json.loads(line.strip()))
                    except Exception:
                        continue
            return items

        trades = read_jsonl(trades_file)
        filled = read_jsonl(filled_file)

        # normalize and merge
        records: list[dict] = []
        seen_keys = set()  # 用于去重
        
        def norm(x: dict, source: str) -> dict:
            return {
                "timestamp": x.get("timestamp") or x.get("time") or x.get("date"),
                "symbol": x.get("symbol") or x.get("ticker"),
                "side": x.get("side") or x.get("action"),
                "quantity": x.get("quantity") or x.get("qty"),
                "price": x.get("price") or x.get("fill_price") or x.get("avg_price") or 0,
                "status": x.get("status") or ("FILLED" if source == "filled" else x.get("state")) or "FILLED",
                "order_id": x.get("order_id") or x.get("id"),
                "source": source,
                "details": x,
            }
        
        def get_unique_key(record: dict) -> str:
            """生成唯一键用于去重：symbol + side + quantity + price（不依赖timestamp，因为可能为空）"""
            sym = record.get("symbol", "")
            side = record.get("side", "")
            qty = record.get("quantity", 0)
            price = record.get("price", 0)
            # 价格归一化（保留2位小数）以避免浮点数精度问题
            price_normalized = round(float(price), 2) if price else 0
            return f"{sym}|{side}|{int(qty)}|{price_normalized}"
        
        def get_order_id(record: dict) -> str:
            """获取订单ID用于去重（如果存在）"""
            return record.get("order_id") or record.get("id") or ""

        # 分开处理 PENDING 和 FILLED 订单
        filled_records = []  # 已成交订单
        pending_records = []  # 待处理订单
        
        # 先处理 filled_orders（已成交订单）
        seen_order_ids = set()  # 用于基于 order_id 去重
        for x in filled[-limit * 2:]:  # 读取更多以便去重
            record = norm(x, "filled")
            key = get_unique_key(record)
            order_id = get_order_id(record)
            
            # 双重去重：既检查 unique_key，也检查 order_id
            if key not in seen_keys and (not order_id or order_id not in seen_order_ids):
                seen_keys.add(key)
                if order_id:
                    seen_order_ids.add(order_id)
                record["status"] = "FILLED"  # 确保状态为FILLED
                filled_records.append(record)
        
        # 然后处理 pending_orders（待处理订单）
        pending_file = logs_dir / "pending_orders.jsonl"
        if pending_file.exists():
            try:
                with pending_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        if not line.strip():
                            continue
                        try:
                            x = json.loads(line.strip())
                            record = norm(x, "pending")
                            key = get_unique_key(record)
                            order_id = get_order_id(record)
                            
                            # 只添加未在filled中出现的订单
                            if key not in seen_keys and (not order_id or order_id not in seen_order_ids):
                                record["status"] = "PENDING"  # 确保状态为PENDING
                                pending_records.append(record)
                        except Exception:
                            continue
            except Exception:
                pass
        
        # 最后处理 trades（只添加未重复的，且不在pending中）
        for x in trades[-limit * 2:]:  # 读取更多以便去重
            record = norm(x, "trades")
            key = get_unique_key(record)
            order_id = get_order_id(record)
            
            # 只添加未重复的，且状态为FILLED的（避免与pending重复）
            if key not in seen_keys and (not order_id or order_id not in seen_order_ids):
                seen_keys.add(key)
                if order_id:
                    seen_order_ids.add(order_id)
                # 如果状态不明确，默认为FILLED（因为来自trades.jsonl）
                if not record.get("status") or record.get("status") == "SUCCESS":
                    record["status"] = "FILLED"
                filled_records.append(record)
        
        # 合并：先显示FILLED，再显示PENDING
        records = filled_records + pending_records

        # sort by timestamp desc
        def ts_key(r: dict):
            t = r.get("timestamp") or ""
            try:
                return datetime.fromisoformat(t.replace("Z", "+00:00"))
            except Exception:
                return datetime.min
        records.sort(key=ts_key, reverse=True)

        return {"ok": True, "trades": records[:limit], "count": len(records[:limit])}
    except Exception as e:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(e)})

@app.get("/api/system/info")
async def get_system_info():
    """Get system information including LLM model and configuration"""
    try:
        import json
        from pathlib import Path
        
        # Load config.json
        config_file = Path("config/config.json")
        llm_config = {}
        config = {}
        if config_file.exists():
            with config_file.open("r", encoding="utf-8") as f:
                config = json.load(f)
                llm_config = config.get("llm", {})
        
        # Load agents.yaml to get agent-specific models
        agent_models = {}
        try:
            from pathlib import Path
            import yaml
            
            agents_file = Path("config/agents.yaml")
            if agents_file.exists():
                with agents_file.open("r", encoding="utf-8") as f:
                    agents_conf = yaml.safe_load(f)
                    if agents_conf:
                        for agent_key, agent_conf in agents_conf.items():
                            if isinstance(agent_conf, dict):
                                agent_models[agent_key] = agent_conf.get("model", llm_config.get("default_model", "llama3.1"))
        except Exception:
            pass
        
        return {
            "ok": True,
            "llm": {
                "default_model": llm_config.get("default_model", "llama3.1"),
                "ollama_host": llm_config.get("ollama_host", "http://localhost:11434"),
                "auto_pull": llm_config.get("auto_pull", True),
            },
            "agent_models": agent_models,
            "config": {
                "discussion_rounds": config.get("discussion_rounds", 3),
                "discussion_tool_budget": config.get("discussion_tool_budget", 2),
            }
        }
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/agents/conversations")
async def get_agent_conversations(
    limit: int = 50,
    date: str | None = None,
    include_demo: bool = False,
):
    """Get recent agent conversations/discussions"""
    try:
        import json
        from pathlib import Path
        
        # Load from discussion_actions.jsonl
        # 尝试多个可能的路径
        possible_paths = [
            Path("data/logs/discussion_actions.jsonl"),
            Path(__file__).parent.parent.parent / "data" / "logs" / "discussion_actions.jsonl",
        ]
        
        log_file = None
        for path in possible_paths:
            if path.exists():
                log_file = path
                break
        
        conversations = []
        
        if log_file and log_file.exists():
            try:
                with log_file.open("r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Read last N lines
                    for line in lines[-limit * 2:]:  # Get more lines, then filter
                        if not line.strip():
                            continue
                        try:
                            entry = json.loads(line.strip())
                            if date:
                                entry_date = entry.get("date", entry.get("timestamp", ""))
                                if entry_date and not entry_date.startswith(date):
                                    continue
                            # Exclude demo entries unless explicitly requested
                            if not include_demo and entry.get("type") == "demo":
                                continue
                            conversations.append(entry)
                        except json.JSONDecodeError as e:
                            # 静默跳过无效的 JSON 行
                            continue
            except Exception as e:
                # 如果读取失败，记录错误但继续尝试从 memory 加载
                print(f"[WARN] Failed to read discussion_actions.jsonl: {e}")
        
        # Also try to load from memory if available
        try:
            from src.data.memory_manager import MemoryManager
            memory_manager = MemoryManager(root="data/logs")
            
            # Get recent memories (load more days to ensure we have enough data)
            recent_memories = memory_manager.load_recent_memories(days=30)  # Load 30 days, then filter
            memory_count = 0
            for memory in recent_memories:
                if memory_count >= limit:  # Stop if we've reached the limit
                    break
                discussion = memory.get("discussion", {})
                if discussion:
                    transcript = discussion.get("transcript", [])
                    if transcript:
                        # Extract individual messages from transcript
                        for msg in transcript:
                            if isinstance(msg, dict) and memory_count < limit:
                                conversations.append({
                                    "date": memory.get("date", ""),
                                    "type": "memory",
                                    "agent": msg.get("agent", "Unknown"),
                                    "content": msg.get("content", msg.get("message", "")),
                                    "round": msg.get("round"),
                                })
                                memory_count += 1
        except Exception as e:
            print(f"[WARN] Failed to load from memory: {e}")

        # Sort by date (newest first)
        conversations.sort(
            key=lambda x: x.get("timestamp", x.get("date", "")), 
            reverse=True
        )
        
        # Limit results (避免前端性能問題)
        limited_conversations = conversations[:limit]
        total_count = len(conversations)
        
        return {
            "ok": True,
            "conversations": limited_conversations,
            "count": len(limited_conversations),
            "total": total_count,  # 總數（用於前端顯示"還有更多"）
            "has_more": total_count > limit
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e)}
        )


@app.get("/api/trading/execution-status")
async def get_execution_status():
    """获取当前交易循环执行状态"""
    return {
        "ok": True,
        "status": _execution_status.copy()
    }


@app.get("/api/market/is-open")
async def is_market_open():
    """Simple market hour check: Mon-Fri, 09:00-16:00 local time."""
    now = datetime.now()
    is_weekday = now.weekday() < 5
    start = dt_time(9, 0)
    end = dt_time(16, 0)
    open_now = is_weekday and (start <= now.time() <= end)
    return {"ok": True, "open": open_now, "now": now.isoformat()}


@app.post("/api/system/init")
async def system_init():
    """Reset logs and initialize portfolio to defaults, then seed minimal data."""
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    # Clear key log files
    for name in [
        "equity_history.jsonl", "filled_orders.jsonl", "pending_orders.jsonl",
        "trades.jsonl", "real_time_snapshots.jsonl", "monitoring.jsonl",
        "discussion_actions.jsonl"
    ]:
        p = logs_dir / name
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass
    # Initialize empty discussion file
    (logs_dir / "discussion_actions.jsonl").touch(exist_ok=True)

    # Create a clean portfolio: all cash, no positions
    state = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "cash": 10000.0,
        "initial_value": 10000.0,
        "total_value": 10000.0,  # 确保所有字段都存在
        "equity_value": 0.0,
        "total_pnl": 0.0,
        "total_pnl_pct": 0.0,
        "positions": {},
    }
    with (logs_dir / "portfolio_state.json").open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    # Seed a couple of conversations so UI is not empty
    # Do not seed demo conversations here to ensure only real conversations are shown
    # Build a minimal snapshot matching current state
    snapshot = {
        "ok": True,
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "initial_value": 10000.0,
        "total_value": 10000.0,
        "total_pnl": 0.0,
        "total_pnl_pct": 0.0,
        "cash": 10000.0,
        "equity_value": 0.0,
        "positions": {},
        "positions_pnl": {},
        "source": "init",
    }
    with (logs_dir / "real_time_snapshots.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(snapshot, ensure_ascii=False) + "\n")
    # If市場開盤且今日尚未交易，自動執行一次交易循環
    try:
        start = dt_time(9, 0)
        end = dt_time(16, 0)
        now = datetime.now()
        is_open = (now.weekday() < 5) and (start <= now.time() <= end)
        flag = logs_dir / "last_trade_date.txt"
        today = now.strftime("%Y-%m-%d")
        traded_today = flag.exists() and flag.read_text(encoding="utf-8").strip() == today
        result = None
        if is_open and not traded_today:
            result = await execute_trading_cycle()
            try:
                flag.write_text(today, encoding="utf-8")
            except Exception:
                pass
        return {"ok": True, "snapshot": snapshot, "auto_ran": bool(result is not None), "result": result}
    except Exception:
        return {"ok": True, "snapshot": snapshot, "auto_ran": False}


@app.post("/api/trading/run-loop")
async def run_trading_loop():
    """DEPRECATED: 已弃用，请使用 /api/trading/execute-trade 替代"""
    return JSONResponse(
        status_code=410,
        content={"ok": False, "error": "此端点已弃用，请使用 /api/trading/execute-trade", "deprecated": True}
    )


@app.post("/api/trading/execute-trade")
async def execute_trade_direct():
    """直接执行交易循环，确保对话输出（不依赖 run-loop）"""
    from src.orchestrator.trading_cycle import execute_daily_trade
    from src.data.portfolio import Portfolio
    from src.data.trade_log import TradeLogger
    
    # 更新执行状态
    _execution_status["running"] = True
    _execution_status["status"] = "analyzing"
    _execution_status["started_at"] = datetime.now(timezone.utc).isoformat()
    _execution_status["completed_at"] = None
    _execution_status["current_step"] = "market_analysis"
    _execution_status["error"] = None
    
    # 完全避免使用 print，使用日志文件记录
    def log_to_file(msg):
        """将日志写入文件，完全不依赖 stdout/stderr"""
        try:
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / "api_execution.log"
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} {msg}\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass  # 完全静默，不抛出任何异常
    
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    
    try:
        log_to_file(f"[Execute Trade] 开始执行交易循环...")
        
        # 更新状态：市场分析
        _execution_status["current_step"] = "market_analysis"
        _execution_status["status"] = "analyzing"
        
        # 从 config.json 读取股票清单
        try:
            config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
            log_to_file(f"[Execute Trade] 尝试读取配置文件: {config_path}")
            log_to_file(f"[Execute Trade] 配置文件存在: {config_path.exists()}")
            universe = None
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config_data = json.load(f)
                        if "universe" in config_data and isinstance(config_data["universe"], list):
                            universe = config_data["universe"]
                            log_to_file(f"[Execute Trade] 使用 config.json 中的股票清单: {len(universe)} 只股票")
                        else:
                            log_to_file(f"[Execute Trade] config.json 中没有有效的 universe 列表")
                except Exception as e:
                    log_to_file(f"[Execute Trade] 读取 config.json 失败: {e}")
                    import traceback
                    log_to_file(f"[Execute Trade] Traceback: {traceback.format_exc()}")
            else:
                log_to_file(f"[Execute Trade] config.json 不存在，将使用默认清单")
        except Exception as e:
            log_to_file(f"[Execute Trade] 配置文件路径处理失败: {e}")
            import traceback
            log_to_file(f"[Execute Trade] Traceback: {traceback.format_exc()}")
            universe = None
        
        # 加载或创建 Portfolio
        portfolio_state_file = logs_dir / "portfolio_state.json"
        portfolio = None
        if portfolio_state_file.exists():
            try:
                with open(portfolio_state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    portfolio = Portfolio(cash=state.get("cash", 10000.0))
                    # 恢复持仓
                    for symbol, pos_data in state.get("positions", {}).items():
                        portfolio.buy(symbol, pos_data.get("quantity", 0), pos_data.get("avg_cost", 0.0))
                log_to_file(f"[Execute Trade] 从 portfolio_state.json 加载投资组合")
            except Exception as e:
                log_to_file(f"[Execute Trade] 加载投资组合失败，创建新组合: {e}")
                portfolio = Portfolio(cash=10000.0)
        else:
            portfolio = Portfolio(cash=10000.0)
            log_to_file(f"[Execute Trade] 创建新投资组合")
        
        # 创建 TradeLogger
        trade_logger = TradeLogger(root=str(logs_dir))
        
        # 执行交易循环（直接调用，不通过 execute_trading_cycle）
        today_date = datetime.now().date()
        start_date = (today_date - timedelta(days=10)).isoformat()
        end_date = (today_date + timedelta(days=1)).isoformat()
        
        log_to_file(f"[Execute Trade] 调用 execute_daily_trade: start={start_date}, end={end_date}, universe={len(universe) if universe else 'None'} 只股票")
        log_to_file(f"[Execute Trade] Portfolio: cash={portfolio.cash}, positions={len(portfolio.positions)}")
        
        # 更新状态：执行中
        _execution_status["current_step"] = "executing"
        _execution_status["status"] = "executing"
        
        try:
            result = execute_daily_trade(
                start=start_date,
                end=end_date,
                universe=universe,
                portfolio=portfolio,
                trade_logger=trade_logger,
                rounds=3,
                auto_tools=True,
                tool_budget=20  # 增加到20，允许LLM使用所有工具
            )
            log_to_file(f"[Execute Trade] execute_daily_trade 调用成功，返回键: {list(result.keys()) if result else 'None'}")
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            log_to_file(f"[Execute Trade] execute_daily_trade 调用异常: {e}")
            log_to_file(f"[Execute Trade] Traceback:\n{error_trace}")
            raise
        
        # 检查 result 是否有错误
        if result and result.get("error"):
            error_msg = result.get("error", "Unknown error")
            log_to_file(f"[Execute Trade] execute_daily_trade 返回错误: {error_msg}")
            raise Exception(f"交易循环执行失败: {error_msg}")
        
        if not result:
            log_to_file(f"[Execute Trade] execute_daily_trade 返回 None")
            raise Exception("交易循环执行失败: execute_daily_trade 返回 None")
        
        log_to_file(f"[Execute Trade] execute_daily_trade 完成，返回键: {list(result.keys())}")
        
        # 更新状态：完成
        _execution_status["current_step"] = "completed"
        _execution_status["status"] = "completed"
        
        # 检查是否有订单生成
        placed_orders = result.get("placed_orders", [])
        buy_orders = result.get("buy_orders", [])
        sell_orders = result.get("sell_orders", [])
        
        # 即使没有订单，对话也已经生成，需要检查对话文件
        # 不再提前返回，确保对话能被读取到
        
        # 检查对话文件（尝试多个路径）
        possible_convo_paths = [
            logs_dir / "discussion_actions.jsonl",
            Path(__file__).parent.parent.parent / "data" / "logs" / "discussion_actions.jsonl",
        ]
        
        convo_file = None
        for path in possible_convo_paths:
            if path.exists():
                convo_file = path
                break
        
        convo_count = 0
        if convo_file and convo_file.exists():
            try:
                with convo_file.open("r", encoding="utf-8") as f:
                    lines = [line for line in f if line.strip()]
                    convo_count = len(lines)
                    log_to_file(f"[Execute Trade] 对话文件当前有 {convo_count} 条记录 (路径: {convo_file})")
            except Exception as e:
                log_to_file(f"[Execute Trade] 读取对话文件失败: {e}")
        else:
            log_to_file(f"[Execute Trade] WARNING: 对话文件不存在！尝试的路径: {possible_convo_paths}")
        
        # 保存投资组合状态
        try:
            # 计算总价值（现金 + 持仓价值）
            total_value = portfolio.cash
            equity_value = 0.0
            positions_dict = {}
            for symbol, pos_obj in portfolio._positions.items():
                if pos_obj.quantity > 0 and pos_obj.avg_cost:
                    position_value = pos_obj.quantity * pos_obj.avg_cost
                    total_value += position_value
                    equity_value += position_value
                    # 确保total_cost正确保存（用于计算P&L）
                    total_cost = pos_obj.total_cost if hasattr(pos_obj, 'total_cost') and pos_obj.total_cost > 0 else pos_obj.avg_cost * pos_obj.quantity
                    positions_dict[symbol] = {
                        "quantity": pos_obj.quantity,
                        "avg_cost": pos_obj.avg_cost,
                        "total_cost": total_cost,
                        "current_value": position_value
                    }
            
            portfolio_snapshot = {
                "cash": portfolio.cash,
                "total_value": total_value,
                "equity_value": equity_value,
                "positions": positions_dict
            }
            with portfolio_state_file.open("w", encoding="utf-8") as f:
                json.dump(portfolio_snapshot, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            log_to_file(f"[Execute Trade] 投资组合状态已保存")
        except Exception as e:
            log_to_file(f"[Execute Trade] 保存投资组合状态失败: {e}")
        
        # 更新状态：完成
        _execution_status["running"] = False
        _execution_status["status"] = "completed"
        _execution_status["completed_at"] = datetime.now(timezone.utc).isoformat()
        _execution_status["current_step"] = None
        
        # 计算投资组合总价值（使用 result 中的 portfolio_state 或直接计算）
        portfolio_total_value = portfolio.cash
        if result and "portfolio_state" in result:
            portfolio_total_value = result["portfolio_state"].get("total_value", portfolio.cash)
        elif result and "portfolio" in result:
            portfolio_total_value = result["portfolio"].get("total_value", portfolio.cash)
        else:
            # 手动计算：现金 + 持仓价值（使用 Portfolio 的 _positions）
            for symbol, pos_obj in portfolio._positions.items():
                if pos_obj.quantity > 0 and pos_obj.avg_cost:
                    portfolio_total_value += pos_obj.quantity * pos_obj.avg_cost
        
        return {
            "ok": True,
            "date": today,
            "result": {
                "placed_orders": len(result.get("placed_orders", [])),
                "conversations_count": convo_count,
                "portfolio_cash": portfolio.cash,
                "portfolio_total_value": portfolio_total_value
            },
            "message": f"交易循环执行成功，生成 {convo_count} 条对话记录"
        }
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        log_to_file(f"[Execute Trade] 异常: {e}")
        log_to_file(f"[Execute Trade] Traceback:\n{error_trace}")
        
        # 更新状态：错误
        _execution_status["running"] = False
        _execution_status["status"] = "error"
        _execution_status["completed_at"] = datetime.now(timezone.utc).isoformat()
        _execution_status["error"] = str(e)
        _execution_status["current_step"] = None
        
        # 确保错误信息被正确返回
        error_response = {
            "ok": False,
            "error": str(e),
            "traceback": error_trace,
            "date": today,
            "message": f"交易循环执行失败: {str(e)}"
        }
        log_to_file(f"[Execute Trade] 返回错误响应: {error_response}")
        return JSONResponse(
            status_code=500,
            content=error_response
        )


@app.post("/api/demo/seed-conversations")
async def seed_conversations(n: int = 10):
    """Generate N demo conversation entries quickly."""
    for _ in range(max(1, n)):
        await demo_conversation_tick()
    return {"ok": True, "written": n}


# 模拟状态跟踪
_simulation_status = {
    "running": False,
    "current_day": 0,
    "total_days": 22,
    "started_at": None,
    "last_update": None,
    "error": None
}

# Global execution status (for trading cycle)
_execution_status = {
    "running": False,
    "status": "idle",  # idle, analyzing, executing, completed, error
    "started_at": None,
    "completed_at": None,
    "current_step": None,  # "market_analysis", "discussion", "risk_analysis", "trading_decision", "order_execution"
    "error": None,
}

def run_october_simulation_background():
    """后台运行10月模拟（在单独的线程中）"""
    import sys
    import io
    import time
    from pathlib import Path
    
    # Fix encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # 确保状态在函数开始时就是True（即使后面出错也能看到）
    # 在try块之前就设置状态，确保即使导入失败也能看到
    _simulation_status["running"] = True
    _simulation_status["started_at"] = datetime.now(timezone.utc).isoformat()
    _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
    _simulation_status["error"] = None
    # 使用 log_to_file 替代 safe_print（在后台线程中）
    def log_to_file(msg):
        try:
            logs_dir = Path("data/logs")
            logs_dir.mkdir(parents=True, exist_ok=True)
            log_file = logs_dir / "api_execution.log"
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"{datetime.now().isoformat()} {msg}\n")
                f.flush()
                os.fsync(f.fileno())
        except Exception:
            pass
    
    log_to_file(f"[Simulation] 后台线程开始，立即设置状态: running={_simulation_status['running']}, started_at={_simulation_status['started_at']}")
    
    # 立即检查并打印当前状态，确保状态被正确设置
    import copy
    status_check = copy.deepcopy(_simulation_status)
    log_to_file(f"[Simulation] 状态检查: {status_check}")
    
    try:
        # 确保在backend目录
        backend_dir = Path(__file__).parent.parent.parent
        os.chdir(str(backend_dir))
        sys.path.insert(0, str(backend_dir))
        
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.data.order_manager import OrderManager
        from src.data.portfolio import Portfolio, Position
        from src.data.order_executor import get_current_or_open_price
        
        # 从 config.json 读取股票清单
        config_path = backend_dir / "config" / "config.json"
        universe = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL"]  # 默认值
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    if "universe" in config_data and isinstance(config_data["universe"], list):
                        universe = config_data["universe"]
                        log_to_file(f"[Simulation] 使用 config.json 中的股票清单: {len(universe)} 只股票")
                    else:
                        log_to_file(f"[Simulation] config.json 中没有 universe，使用默认清单: {len(universe)} 只股票")
            except Exception as e:
                log_to_file(f"[Simulation] 读取 config.json 失败，使用默认清单: {e}")
        else:
            log_to_file(f"[Simulation] config.json 不存在，使用默认清单: {len(universe)} 只股票")
        
        # 确认状态为True（API端点和函数开始都已设置，这里再次确认）
        _simulation_status["running"] = True  # 强制设置为True
        if not _simulation_status["started_at"]:
            _simulation_status["started_at"] = datetime.now(timezone.utc).isoformat()
        _simulation_status["error"] = None
        _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
        log_to_file(f"[Simulation] 模拟线程初始化完成，状态: running={_simulation_status['running']}, started_at={_simulation_status['started_at']}")
        
        # 初始化
        logs_dir = Path("data/logs")
        logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 清空对话日誌
        convo_file = logs_dir / "discussion_actions.jsonl"
        if convo_file.exists():
            convo_file.write_text("", encoding="utf-8")
        
        # 清空掛單記錄
        pending_file = logs_dir / "pending_orders.jsonl"
        if pending_file.exists():
            pending_file.write_text("", encoding="utf-8")
        
        # 重置組合狀態
        portfolio_file = logs_dir / "portfolio_state.json"
        initial_state = {
            "cash": 10000.0,
            "initial_value": 10000.0,
            "positions": {},
            "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
        }
        portfolio_file.write_text(json.dumps(initial_state, indent=2, ensure_ascii=False), encoding="utf-8")
        
        # 清空單日鎖
        last_trade_file = logs_dir / "last_trade_date.txt"
        if last_trade_file.exists():
            last_trade_file.unlink()
        
        # 生成10月份的所有交易日
        start_date = date(2024, 10, 1)
        end_date = date(2024, 10, 31)
        trading_days = []
        current = start_date
        while current <= end_date:
            if current.weekday() < 5:  # 周一到周五
                trading_days.append(current)
            current += timedelta(days=1)
        
        _simulation_status["total_days"] = len(trading_days)
        
        # 結算函數
        def settle_orders(settle_date, logs_dir):
            order_manager = OrderManager(root="data/logs")
            pending_orders = order_manager.load_pending_orders(order_date=settle_date)
            
            if not pending_orders:
                return 0
            
            portfolio_file = logs_dir / "portfolio_state.json"
            if not portfolio_file.exists():
                return 0
            
            with portfolio_file.open("r", encoding="utf-8") as f:
                state = json.load(f)
            
            portfolio = Portfolio(
                cash=float(state.get("cash", 10000.0)),
                initial_value=float(state.get("initial_value", 10000.0)),
            )
            
            for symbol, pos_info in state.get("positions", {}).items():
                if isinstance(pos_info, dict):
                    qty = int(pos_info.get("quantity", 0))
                    avg_cost = float(pos_info.get("avg_cost", 0))
                    if qty > 0:
                        portfolio._positions[symbol] = Position(
                            symbol=symbol,
                            quantity=qty,
                            avg_cost=avg_cost,
                            total_cost=avg_cost * qty,
                        )
            
            settled_count = 0
            for order in pending_orders:
                symbol = order.get("symbol")
                action = order.get("action", "").upper()
                quantity = order.get("quantity", 0)
                limit_price = order.get("limit_price", 0)
                
                try:
                    current_price = get_current_or_open_price(symbol, settle_date)
                    if current_price is None:
                        # 如果无法获取价格（可能是假期或退市），使用限价
                        current_price = limit_price
                        if current_price is None or current_price <= 0:
                            # 如果限价也没有，跳过这个订单
                            log_to_file(f"[Simulation] 跳过订单 {symbol}: 无法获取价格且无限价")
                            continue
                    
                    # 确保 current_price 是 float 类型
                    try:
                        current_price = float(current_price)
                    except (ValueError, TypeError):
                        log_to_file(f"[Simulation] 跳过订单 {symbol}: 价格格式错误 {current_price}")
                        continue
                    
                    # 创建fill_result
                    fill_result = {
                        "filled": True,
                        "fill_price": current_price,
                        "fill_reason": f"Simulated fill at ${current_price:.2f}",
                        "daily_high": current_price,
                        "daily_low": current_price,
                    }
                    
                    if action == "BUY":
                        portfolio.buy(symbol, quantity, current_price)
                    elif action == "SELL":
                        portfolio.sell(symbol, quantity, current_price)
                    
                    # 正确调用mark_order_filled（这会写入 filled_orders.jsonl）
                    order_manager.mark_order_filled(order, fill_result)
                    
                    # 注意：不在这里再次写入 trades.jsonl，因为：
                    # 1. mark_order_filled 已经写入 filled_orders.jsonl
                    # 2. get_recent_trades 会同时读取 filled_orders.jsonl 和 trades.jsonl 并去重
                    # 3. 避免重复记录
                    # 如果前端需要 trades.jsonl 格式，可以在 mark_order_filled 内部统一处理
                    
                    settled_count += 1
                except Exception as e:
                    # 忽略假期或退市股票的错误
                    error_str = str(e)
                    if "YFPricesMissingError" in error_str or "possibly delisted" in error_str or "no price data found" in error_str or "unsupported format string" in error_str:
                        # 静默忽略，这是假期或退市股票的正常情况
                        log_to_file(f"[Simulation] 跳过订单 {symbol}: 假期或退市股票（{error_str[:50]}）")
                        continue
                    log_to_file(f"[Simulation] 结算订单失败: {symbol}, {e}")
                    import traceback
                    try:
                        traceback.print_exc()
                    except (ValueError, OSError):
                        try:
                            sys.stderr.write(traceback.format_exc())
                            sys.stderr.flush()
                        except Exception:
                            pass
            
            portfolio_state = {
                "cash": portfolio.cash,
                "initial_value": portfolio.initial_value,
                "positions": {},
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
            
            for symbol, pos in portfolio._positions.items():
                # 确保total_cost正确保存（用于计算P&L）
                total_cost = pos.total_cost if hasattr(pos, 'total_cost') and pos.total_cost > 0 else pos.avg_cost * pos.quantity
                portfolio_state["positions"][symbol] = {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": total_cost,
                }
            
            portfolio_file.write_text(json.dumps(portfolio_state, indent=2, ensure_ascii=False), encoding="utf-8")
            return settled_count
        
        # 模拟每一天
        for day_num, trade_date in enumerate(trading_days, 1):
            if not _simulation_status["running"]:
                break
                
            trade_date_str = trade_date.isoformat()
            _simulation_status["current_day"] = day_num
            _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
            
            # 結算前一天的訂單（如果有）
            if day_num > 1:
                prev_date = trading_days[day_num - 2].isoformat()
                settled = settle_orders(prev_date, logs_dir)
                if settled > 0:
                    log_to_file(f"[Simulation] 結算 {prev_date} 的訂單: {settled} 筆")
            
            # 執行當天交易循環
            try:
                window_start = (trade_date - timedelta(days=10)).isoformat()
                window_end = (trade_date + timedelta(days=1)).isoformat()
                
                log_to_file(f"[Simulation] 執行 {trade_date_str} 的交易循環...")
                log_to_file(f"[Simulation] 參數: start={window_start}, end={window_end}, universe={len(universe)} stocks")
                
                result = execute_daily_trade(
                    start=window_start,
                    end=window_end,
                    universe=universe,  # 使用从 config.json 读取的股票清单
                    rounds=3,
                    auto_tools=True,
                    tool_budget=20  # 增加到20，允许LLM使用所有工具
                )
                
                log_to_file(f"[Simulation] execute_daily_trade 返回: {list(result.keys())}")
                
                # 檢查是否有訂單生成
                buy_orders = result.get("buy_orders", [])
                placed_orders = result.get("placed_orders", [])
                if placed_orders:
                    log_to_file(f"[Simulation] {trade_date_str} 生成 {len(placed_orders)} 筆訂單")
                elif buy_orders:
                    log_to_file(f"[Simulation] {trade_date_str} Trader 建議 {len(buy_orders)} 筆買單，但未生成訂單")
                else:
                    log_to_file(f"[Simulation] {trade_date_str} 無交易建議")
                
                # 檢查對話是否生成
                convo_file = logs_dir / "discussion_actions.jsonl"
                if convo_file.exists():
                    with convo_file.open("r", encoding="utf-8") as f:
                        lines = [line for line in f if line.strip()]
                    log_to_file(f"[Simulation] {trade_date_str} 對話文件當前有 {len(lines)} 行")
                else:
                    log_to_file(f"[Simulation] {trade_date_str} WARNING: 對話文件不存在！")
                
                _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
                
            except Exception as e:
                log_to_file(f"[Simulation] Error on {trade_date_str}: {e}")
                import traceback
                try:
                    traceback.print_exc()
                except (ValueError, OSError):
                    try:
                        sys.stderr.write(traceback.format_exc())
                        sys.stderr.flush()
                    except Exception:
                        pass
                if "No data" not in str(e) and "YFPricesMissingError" not in str(e):
                    _simulation_status["error"] = str(e)
                    break
            
            # 結算當天的訂單（立即結算，讓前端能立即看到）
            try:
                settled = settle_orders(trade_date_str, logs_dir)
                if settled > 0:
                    log_to_file(f"[Simulation] 立即結算 {trade_date_str} 的訂單: {settled} 筆")
                
                # 結算後，記錄交易完成後的equity狀態（確保圖表顯示正確的最終值）
                try:
                    from src.data.equity_tracker import EquityTracker
                    from src.data.real_time_tracker import RealTimeTracker
                    
                    # 重新加載portfolio狀態（settle_orders已更新）
                    portfolio_file = logs_dir / "portfolio_state.json"
                    if portfolio_file.exists():
                        with portfolio_file.open("r", encoding="utf-8") as f:
                            state = json.load(f)
                        
                        # 創建Portfolio對象
                        portfolio = Portfolio(
                            cash=float(state.get("cash", 10000.0)),
                            initial_value=float(state.get("initial_value", 10000.0)),
                        )
                        
                        # 恢復持倉
                        for symbol, pos_info in state.get("positions", {}).items():
                            if isinstance(pos_info, dict):
                                qty = int(pos_info.get("quantity", 0))
                                avg_cost = float(pos_info.get("avg_cost", 0))
                                if qty > 0:
                                    portfolio._positions[symbol] = Position(
                                        symbol=symbol,
                                        quantity=qty,
                                        avg_cost=avg_cost,
                                        total_cost=avg_cost * qty,
                                    )
                        
                        # 獲取當前價格並計算equity
                        try:
                            tracker = RealTimeTracker(root="data/logs")
                            snapshot = tracker.update_and_record(portfolio)
                            
                            # 記錄到equity_history（使用交易日期）
                            equity_tracker = EquityTracker(root="data/logs")
                            equity_tracker.record_daily_equity(
                                date_str=trade_date_str,
                                portfolio_snapshot=snapshot,
                            )
                            log_to_file(f"[Simulation] 記錄 {trade_date_str} 交易後的equity: ${snapshot.get('total_value', 0):.2f}")
                        except Exception as tracker_err:
                            # 如果RealTimeTracker失敗（例如yfinance不可用），使用簡單計算
                            equity_value = sum(
                                float(pos_info.get("avg_cost", 0)) * int(pos_info.get("quantity", 0))
                                for pos_info in state.get("positions", {}).values()
                                if isinstance(pos_info, dict)
                            )
                            total_value = float(state.get("cash", 0)) + equity_value
                            
                            snapshot = {
                                "cash": float(state.get("cash", 0)),
                                "equity_value": equity_value,
                                "total_value": total_value,
                                "initial_value": float(state.get("initial_value", 10000.0)),
                                "total_pnl": total_value - float(state.get("initial_value", 10000.0)),
                                "total_pnl_pct": ((total_value - float(state.get("initial_value", 10000.0))) / float(state.get("initial_value", 10000.0)) * 100) if state.get("initial_value", 0) > 0 else 0,
                                "positions_detail": {
                                    sym: {
                                        "quantity": int(p.get("quantity", 0)),
                                        "avg_cost": float(p.get("avg_cost", 0)),
                                        "current_price": float(p.get("avg_cost", 0)),
                                        "market_value": float(p.get("avg_cost", 0)) * int(p.get("quantity", 0)),
                                    }
                                    for sym, p in state.get("positions", {}).items()
                                    if isinstance(p, dict)
                                },
                            }
                            
                            equity_tracker = EquityTracker(root="data/logs")
                            equity_tracker.record_daily_equity(
                                date_str=trade_date_str,
                                portfolio_snapshot=snapshot,
                            )
                            log_to_file(f"[Simulation] 記錄 {trade_date_str} 交易後的equity (簡單計算): ${total_value:.2f}")
                except Exception as equity_err:
                    log_to_file(f"[Simulation] 記錄equity時出錯: {equity_err}")
            except Exception as e:
                log_to_file(f"[Simulation] 結算 {trade_date_str} 訂單時出錯: {e}")
            
            # 等待5分钟（如果不是最后一天）
            if day_num < len(trading_days) and _simulation_status["running"]:
                # 等待5分钟 = 300秒
                for _ in range(300):
                    if not _simulation_status["running"]:
                        break
                    time.sleep(1)
        
        _simulation_status["running"] = False
        _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
        
    except Exception as e:
        # 使用 log_to_file 替代 safe_print（在后台线程中）
        def log_to_file(msg):
            try:
                logs_dir = Path("data/logs")
                logs_dir.mkdir(parents=True, exist_ok=True)
                log_file = logs_dir / "api_execution.log"
                with log_file.open("a", encoding="utf-8") as f:
                    f.write(f"{datetime.now().isoformat()} {msg}\n")
                    f.flush()
                    os.fsync(f.fileno())
            except Exception:
                pass
        
        log_to_file(f"[Simulation] 模拟线程出错: {e}")
        import traceback
        try:
            traceback.print_exc()
        except (ValueError, OSError):
            try:
                sys.stderr.write(traceback.format_exc())
                sys.stderr.flush()
            except Exception:
                pass
        # 只有在真正出错时才设置为False，但保留started_at以便前端能看到错误
        _simulation_status["running"] = False
        if not _simulation_status["started_at"]:
            _simulation_status["started_at"] = datetime.now(timezone.utc).isoformat()
        _simulation_status["error"] = str(e)
        _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
        log_to_file(f"[Simulation] 错误后状态: running={_simulation_status['running']}, error={_simulation_status['error']}, started_at={_simulation_status['started_at']}")


@app.post("/api/trading/simulate-october")
async def simulate_october(background_tasks: BackgroundTasks):
    """启动10月历史数据模拟（后台运行）"""
    if _simulation_status["running"]:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "模拟已在运行中"}
        )
    
    # 重置状态并立即设置为启动中（让前端能立即看到）
    _simulation_status["running"] = True  # 立即设置为True，让前端能检测到
    _simulation_status["current_day"] = 0
    _simulation_status["total_days"] = 22
    _simulation_status["started_at"] = datetime.now(timezone.utc).isoformat()
    _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
    _simulation_status["error"] = None
    
    # 在后台线程中运行
    import threading
    
    # 安全的 print 函数（用于主线程）
    def api_safe_print(msg):
        try:
            print(msg, flush=True)
        except (ValueError, OSError):
            try:
                sys.stderr.write(str(msg) + "\n")
                sys.stderr.flush()
            except Exception:
                pass
    
    # 确保状态在启动线程前已经设置
    api_safe_print(f"[API] 启动模拟线程前，状态: running={_simulation_status['running']}, started_at={_simulation_status['started_at']}")
    
    thread = threading.Thread(target=run_october_simulation_background, daemon=True)
    thread.start()
    
    # 等待一小段时间确保线程启动
    import time
    time.sleep(0.1)  # 等待100ms让线程有机会设置状态
    
    # 再次确认状态（线程应该已经设置了）
    api_safe_print(f"[API] 启动模拟线程后，状态: running={_simulation_status['running']}, started_at={_simulation_status['started_at']}")
    
    # 返回深拷贝，确保状态被正确传递
    import copy
    status_copy = copy.deepcopy(_simulation_status)
    api_safe_print(f"[API] 返回状态: running={status_copy['running']}, started_at={status_copy['started_at']}")
    
    return {
        "ok": True,
        "message": "10月模拟已启动（后台运行）",
        "status": "started",
        "simulation_status": status_copy  # 返回当前状态，让前端立即显示
    }


@app.get("/api/trading/simulate-status")
async def get_simulation_status():
    """获取10月模拟的状态"""
    # 返回深拷贝，避免并发修改问题
    import copy
    return {
        "ok": True,
        "status": copy.deepcopy(_simulation_status)
    }


@app.post("/api/trading/stop-simulation")
async def stop_simulation():
    """停止10月模拟"""
    _simulation_status["running"] = False
    return {
        "ok": True,
        "message": "模拟已停止"
    }


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "AI Trader API",
        "version": "1.0.0",
        "endpoints": {
            "websocket": "/ws",
            "agent_status": "/api/agents/status",
            "history": "/api/history",
            "execute": "/api/trading/execute",
            "market_open": "/api/market/is-open",
            "system_init": "/api/system/init",
            "run_loop": "/api/trading/run-loop",
            "execution_status": "/api/trading/execution-status",
            "execute_trade": "/api/trading/execute-trade",
            "seed_conversations": "/api/demo/seed-conversations"
        }
    }

