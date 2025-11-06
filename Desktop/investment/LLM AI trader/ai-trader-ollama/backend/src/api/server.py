# src/api/server.py
"""
FastAPI backend for real-time agent monitoring and frontend integration.
Provides WebSocket for real-time updates and REST API for historical data.
"""
from __future__ import annotations

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
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

# Custom CORS middleware to handle file:// protocol (null origin)
class CORSNullOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        # Always add CORS headers to allow file:// access
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Expose-Headers"] = "*"
        return response

# Apply custom CORS middleware first
app.add_middleware(CORSNullOriginMiddleware)

# Then apply standard CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins including file://
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
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
    
    # 从 config.json 读取股票清单
    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    universe = None  # None 会使用 execute_daily_trade 的默认值
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    universe = config_data["universe"]
                    print(f"[Trading Cycle] 使用 config.json 中的股票清单: {len(universe)} 只股票")
        except Exception as e:
            print(f"[Trading Cycle] 读取 config.json 失败，使用默认清单: {e}")
    
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
            tool_budget=3,
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
        event_bus.emit(AgentEvent(
            timestamp=datetime.now().isoformat(),
            agent_name="Orchestrator",
            event_type="session_error",
            status="error",
            payload={"error": str(e)},
            session_id=session_id
        ))
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "session_id": session_id}
        )


@app.post("/api/trading/execute-trade")
async def execute_trade_direct():
    """直接执行交易循环，支持非交易时段规划明日交易"""
    from src.orchestrator.trading_cycle import execute_daily_trade
    from src.data.order_manager import OrderManager
    from datetime import time as dt_time, timedelta
    
    # 检查市场是否开盘
    now = datetime.now()
    is_weekday = now.weekday() < 5
    market_open_time = dt_time(9, 30)  # 9:30 AM
    market_close_time = dt_time(16, 0)  # 4:00 PM
    is_market_open = is_weekday and (market_open_time <= now.time() <= market_close_time)
    
    # 从 config.json 读取股票清单
    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    universe = None
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    universe = config_data["universe"]
        except Exception:
            pass
    
    # 非交易时段：检查是否已有明日订单计划
    if not is_market_open:
        # 计算明天的日期（下一个交易日）
        tomorrow = date.today() + timedelta(days=1)
        while tomorrow.weekday() >= 5:
            tomorrow += timedelta(days=1)
        tomorrow_str = tomorrow.isoformat()
        
        order_manager = OrderManager(root="data/logs")
        existing_orders = order_manager.load_pending_orders(order_date=tomorrow_str)
        
        if existing_orders:
            return {
                "ok": True,
                "message": f"Market closed. Already have {len(existing_orders)} pending orders for tomorrow ({tomorrow_str}). No new planning needed.",
                "result": {
                    "placed_orders": [],
                    "conversations_count": 0,
                    "is_planning": True,
                    "order_date": tomorrow_str
                }
            }
        
        # 非交易时段：规划明日交易
        print(f"[TRADING CYCLE] Market closed. Planning trades for tomorrow ({tomorrow_str})")
        try:
            result = execute_daily_trade(
                rounds=3,
                auto_tools=True,
                tool_budget=3,
                universe=universe
            )
            
            return {
                "ok": True,
                "message": f"Planning completed for tomorrow ({tomorrow_str})",
                "result": result
            }
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            error_msg = str(e)
            error_type = type(e).__name__
            print(f"[API ERROR] execute_trade_direct (planning) failed: {error_msg}")
            print(f"[API ERROR] Error type: {error_type}")
            print(f"[API ERROR] Traceback:\n{error_trace}")
            return JSONResponse(
                status_code=500,
                content={
                    "ok": False, 
                    "error": error_msg,
                    "error_type": error_type,
                    "message": f"Failed to execute trade planning: {error_msg}"
                },
                headers={"Access-Control-Allow-Origin": "*"}
            )
    
    # 交易时段：正常执行交易
    try:
        result = execute_daily_trade(
            rounds=3,
            auto_tools=True,
            tool_budget=3,
            universe=universe
        )
        
        return {
            "ok": True,
            "result": result
        }
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"[API ERROR] execute_trade_direct failed: {error_msg}")
        print(f"[API ERROR] Error type: {error_type}")
        print(f"[API ERROR] Traceback:\n{error_trace}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False, 
                "error": error_msg,
                "error_type": error_type,
                "message": f"Failed to execute trade: {error_msg}"
            },
            headers={"Access-Control-Allow-Origin": "*"}
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
        from datetime import time as dt_time
        # Path 已经在文件顶部导入，不需要重新导入
        
        # 检查市场是否开盘 - 非交易时段不更新数据
        now = datetime.now()
        is_weekday = now.weekday() < 5
        market_open_time = dt_time(9, 30)  # 9:30 AM
        market_close_time = dt_time(16, 0)  # 4:00 PM
        is_market_open = is_weekday and (market_open_time <= now.time() <= market_close_time)
        
        # Load portfolio state
        state_file = Path("data/logs/portfolio_state.json")
        if not state_file.exists():
            # Fallback: return simple default portfolio when no state file exists
            return {
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
                "source": "default",
            }
        
        with state_file.open("r", encoding="utf-8") as f:
            state = json.load(f)
        
        # Handle nested snapshot structure: {date, snapshot: {...}}
        snapshot = state.get("snapshot", state)  # Support both formats
        
        from src.data.portfolio import Portfolio, Position
        portfolio = Portfolio(
            cash=float(snapshot.get("cash", 10000.0)),
            initial_value=float(snapshot.get("initial_value", state.get("initial_value", 10000.0))),
        )
        
        # Restore positions
        positions = snapshot.get("positions", {})
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
            # 非交易时段：不更新数据，只返回已保存的快照
            if not is_market_open:
                # 优先使用snapshot中的positions_pnl（如果有）
                snapshot_positions_pnl = snapshot.get("positions_pnl", {})
                
                # 获取最新快照（不更新）
                try:
                    from src.data.real_time_tracker import RealTimeTracker
                    tracker = RealTimeTracker(root="data/logs")
                    cached_snapshot = tracker.get_latest_snapshot()
                    if cached_snapshot:
                        cached_snapshot["ok"] = True
                        cached_snapshot["source"] = "cached"
                        return {"ok": True, **cached_snapshot}
                except Exception:
                    pass
                
                # 如果没有快照，使用snapshot中的positions_pnl（如果存在）
                # 使用snapshot中保存的positions_pnl（如果有），否则计算
                positions_pnl_from_snapshot = snapshot.get("positions_pnl", {})
                equity = sum((pos_info.get("market_value", pos_info.get("avg_cost", 0) * pos_info.get("quantity", 0))) for pos_info in positions.values() if isinstance(pos_info, dict))
                total_value = portfolio.cash + equity
                positions_detail = {}
                positions_pnl = {}
                for sym, pos_info in positions.items():
                    if isinstance(pos_info, dict):
                        qty = int(pos_info.get("quantity", 0))
                        avg = float(pos_info.get("avg_cost", 0))
                        total_cost = float(pos_info.get("total_cost", 0.0))
                        if total_cost <= 0:
                            total_cost = avg * qty
                        
                        # 使用snapshot中的current_price（如果有），否则使用avg_cost
                        current_price = float(pos_info.get("current_price", avg))
                        mv = current_price * qty
                        cost_basis = total_cost
                        
                        positions_detail[sym] = {
                            "quantity": qty,
                            "avg_cost": round(avg, 2),
                            "total_cost": round(total_cost, 2),
                            "cost_basis": round(cost_basis, 2),
                            "current_price": round(current_price, 2),
                            "market_value": round(mv, 2),
                        }
                        
                        # 优先使用snapshot中的positions_pnl，否则计算
                        if sym in positions_pnl_from_snapshot:
                            positions_pnl[sym] = positions_pnl_from_snapshot[sym]
                        else:
                            unrealized_pnl = mv - cost_basis
                            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
                            positions_pnl[sym] = {
                                "unrealized_pnl": round(unrealized_pnl, 2),
                                "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                            }
                snapshot = {
                    "ok": True,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "initial_value": portfolio.initial_value,
                    "total_value": round(total_value, 2),
                    "total_pnl": round(total_value - portfolio.initial_value, 2),
                    "total_pnl_pct": round(((total_value - portfolio.initial_value) / portfolio.initial_value * 100) if portfolio.initial_value > 0 else 0, 2),
                    "cash": round(portfolio.cash, 2),
                    "equity_value": round(equity, 2),
                    "positions": positions_detail,
                    "positions_pnl": positions_pnl,
                    "source": "static_after_hours",
                }
            else:
                # 交易时段：更新实时数据
                snapshot = None
                try:
                    from src.data.real_time_tracker import RealTimeTracker
                    tracker = RealTimeTracker(root="data/logs")
                    snapshot = tracker.update_and_record(portfolio)
                    if snapshot and snapshot.get("ok"):
                        # Use snapshot from tracker (includes real-time prices and P&L)
                        return {"ok": True, **snapshot}
                except Exception as e:
                    # Fallback: fetch current prices manually
                    print(f"[Portfolio API] RealTimeTracker failed, using fallback: {e}")
                    pass
                
                # Fallback: 在交易时段，强制获取实时价格（不依赖snapshot中的旧价格）
                # 获取所有symbol的实时价格
                all_symbols = [sym for sym, pos_info in positions.items() if isinstance(pos_info, dict)]
                last_prices = {}
                
                # 在交易时段，总是尝试获取实时价格
                if all_symbols:
                    try:
                        from src.tools.market_tools import fetch_market_batch
                        # 分批获取实时价格（减少耗时）
                        batch_size = 10
                        for i in range(0, len(all_symbols), batch_size):
                            batch = all_symbols[i:i+batch_size]
                            try:
                                market_data = fetch_market_batch.invoke({"symbols": batch, "start": date.today().isoformat(), "end": date.today().isoformat()})
                                stocks = market_data.get("stocks", {})
                                for sym in batch:
                                    if sym in stocks and "price" in stocks[sym] and stocks[sym]["price"]:
                                        last_prices[sym] = float(stocks[sym]["price"])
                                    elif sym in positions and isinstance(positions[sym], dict):
                                        # 如果获取失败，暂时使用avg_cost，但会继续尝试
                                        last_prices[sym] = float(positions[sym].get("avg_cost", 0))
                            except Exception as batch_err:
                                # If batch fails, use avg_cost as fallback for this batch
                                for sym in batch:
                                    if sym in positions and isinstance(positions[sym], dict):
                                        last_prices[sym] = float(positions[sym].get("avg_cost", 0))
                    except Exception as e:
                        print(f"[Portfolio API] Failed to fetch batch prices: {e}")
                        # If all price fetch fails, use avg_cost as fallback for all
                        for sym in all_symbols:
                            if sym in positions and isinstance(positions[sym], dict):
                                last_prices[sym] = float(positions[sym].get("avg_cost", 0))
                
                # 确保所有symbol都有价格（final fallback）
                for sym, pos_info in positions.items():
                    if isinstance(pos_info, dict) and sym not in last_prices:
                        last_prices[sym] = float(pos_info.get("avg_cost", 0))
                
                # Calculate positions detail and P&L with real-time prices
                total_value = portfolio.cash
                positions_detail = {}
                positions_pnl = {}
                for sym, pos_info in positions.items():
                    if isinstance(pos_info, dict):
                        qty = int(pos_info.get("quantity", 0))
                        avg = float(pos_info.get("avg_cost", 0))
                        total_cost = float(pos_info.get("total_cost", 0.0))
                        if total_cost <= 0:
                            total_cost = avg * qty
                        
                        current_price = float(last_prices.get(sym, avg))
                        mv = current_price * qty
                        cost_basis = total_cost
                        total_value += mv
                        
                        positions_detail[sym] = {
                            "quantity": qty,
                            "avg_cost": round(avg, 2),
                            "total_cost": round(total_cost, 2),
                            "cost_basis": round(cost_basis, 2),
                            "current_price": round(current_price, 2),
                            "market_value": round(mv, 2),
                        }
                        # 计算P&L (使用实时价格)
                        unrealized_pnl = mv - cost_basis
                        unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
                        positions_pnl[sym] = {
                            "unrealized_pnl": round(unrealized_pnl, 2),
                            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                        }
                
                snapshot = {
                    "ok": True,
                    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    "initial_value": portfolio.initial_value,
                    "total_value": round(total_value, 2),
                    "total_pnl": round(total_value - portfolio.initial_value, 2),
                    "total_pnl_pct": round(((total_value - portfolio.initial_value) / portfolio.initial_value * 100) if portfolio.initial_value > 0 else 0, 2),
                    "cash": round(portfolio.cash, 2),
                    "equity_value": round(total_value - portfolio.cash, 2),
                    "positions": positions_detail,
                    "positions_pnl": positions_pnl,
                    "source": "fallback_realtime",
                }
        
        # 定期记录净值（每30秒或净值变化超过0.5%时）
        try:
            from src.data.equity_tracker import EquityTracker
            today_str = date.today().isoformat()
            equity_tracker = EquityTracker(root="data/logs")
            
            # 检查今天是否已有记录
            existing_records = equity_tracker.load_equity_history(start_date=today_str, end_date=today_str)
            current_time = datetime.now()
            should_record = False
            
            if not existing_records:
                # 如果今天还没有记录，立即记录
                should_record = True
                print(f"[Portfolio API] No records today, recording first snapshot")
            else:
                # 检查最后一条记录的时间
                last_record = existing_records[-1]
                last_timestamp_str = last_record.get("timestamp", "")
                
                if last_timestamp_str:
                    try:
                        # 尝试解析时间戳（支持多种格式）
                        last_timestamp_str_clean = last_timestamp_str.replace('Z', '+00:00').replace('+00:00', '')
                        try:
                            last_timestamp = datetime.fromisoformat(last_timestamp_str_clean)
                        except:
                            # 如果ISO格式失败，尝试其他格式
                            last_timestamp = datetime.strptime(last_timestamp_str_clean.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                        
                        # 如果时区信息存在，转换为本地时间
                        if last_timestamp.tzinfo:
                            last_timestamp = last_timestamp.astimezone().replace(tzinfo=None)
                        
                        time_diff = (current_time - last_timestamp).total_seconds()
                        
                        # 如果距离上次记录超过30秒，或者净值变化超过0.5%
                        last_value = last_record.get("total_value", 0.0)
                        current_value = snapshot.get("total_value", 0.0)
                        value_change_pct = abs((current_value - last_value) / last_value * 100) if last_value > 0 else 0
                        
                        if time_diff >= 30:
                            should_record = True
                            print(f"[Portfolio API] Time diff: {time_diff:.1f}s, recording snapshot")
                        elif value_change_pct >= 0.5:
                            should_record = True
                            print(f"[Portfolio API] Value changed {value_change_pct:.2f}%, recording snapshot")
                    except Exception as e:
                        # 如果时间解析失败，每30秒记录一次（简化逻辑）
                        print(f"[Portfolio API] Timestamp parse error: {e}, will record anyway")
                        # 如果无法解析时间，但记录数少于10，也记录（避免无限记录）
                        if len(existing_records) < 10:
                            should_record = True
                else:
                    # 没有时间戳，每30秒记录一次
                    if len(existing_records) < 10:
                        should_record = True
            
            if should_record:
                portfolio_snapshot_for_record = {
                    "cash": snapshot.get("cash", 0.0),
                    "equity_value": snapshot.get("equity_value", 0.0),
                    "total_value": snapshot.get("total_value", 0.0),
                    "total_pnl": snapshot.get("total_pnl", 0.0),
                    "total_pnl_pct": snapshot.get("total_pnl_pct", 0.0),
                    "initial_value": snapshot.get("initial_value", 10000.0),
                    "positions_detail": snapshot.get("positions", {}),
                }
                # 使用update_existing=False来追加记录，而不是覆盖
                equity_tracker.record_daily_equity(
                    date_str=today_str,
                    portfolio_snapshot=portfolio_snapshot_for_record,
                    update_existing=False,  # 追加记录，允许同一天多条记录
                )
                print(f"[Portfolio API] ✓ Recorded intraday equity snapshot for {today_str}: ${snapshot.get('total_value', 0):.2f}")
        except Exception as e:
            import traceback
            print(f"[Portfolio API] Failed to record intraday equity: {e}")
            print(f"[Portfolio API] Traceback: {traceback.format_exc()}")
            # 不影响主流程
        
        return {"ok": True, **snapshot}
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        error_msg = str(e)
        print(f"[Portfolio API ERROR] get_real_time_portfolio failed: {error_msg}")
        print(f"[Portfolio API ERROR] Traceback:\n{error_trace}")
        # Return a safe fallback response instead of 500 error
        return JSONResponse(
            status_code=500,
            content={
                "ok": False, 
                "error": error_msg,
                "error_type": type(e).__name__,
                "message": "Failed to get portfolio data. Using default values.",
                # Fallback data so frontend can still render
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "initial_value": 10000.0,
                "total_value": 10000.0,
                "total_pnl": 0.0,
                "total_pnl_pct": 0.0,
                "cash": 10000.0,
                "equity_value": 0.0,
                "positions": {},
                "positions_pnl": {},
                "source": "error_fallback",
            },
            headers={"Access-Control-Allow-Origin": "*"}
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
    """Return recent trade records from logs (filled, pending, and general)."""
    try:
        import json
        from datetime import datetime

        logs_dir = Path("data/logs")
        trades_file = logs_dir / "trades.jsonl"
        filled_file = logs_dir / "filled_orders.jsonl"
        pending_file = logs_dir / "pending_orders.jsonl"

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
        pending = read_jsonl(pending_file)

        # normalize and merge
        records: list[dict] = []
        def norm(x: dict, source: str) -> dict:
            # 对于pending订单，确保状态是PENDING而不是FILLED
            status = x.get("status", "")
            if source == "pending" or status.upper() == "PENDING":
                final_status = "PENDING"
            elif source == "filled" or status.upper() == "FILLED":
                final_status = "FILLED"
            else:
                final_status = status or ("FILLED" if source == "filled" else x.get("state", "PENDING"))
            
            # 對於pending訂單，優先使用limit_price作為price
            limit_price = x.get("limit_price")
            if source == "pending" and limit_price:
                display_price = limit_price
            else:
                display_price = x.get("price") or x.get("fill_price") or limit_price or x.get("avg_price")
            
            return {
                "timestamp": x.get("timestamp") or x.get("time") or x.get("date") or x.get("placed_at") or x.get("filled_at"),
                "symbol": x.get("symbol") or x.get("ticker"),
                "side": x.get("side") or x.get("action"),
                "quantity": x.get("quantity") or x.get("qty"),
                "price": display_price,
                "limit_price": limit_price,  # 明確返回limit_price字段
                "fill_price": x.get("fill_price"),  # 添加fill_price字段
                "status": final_status,
                "order_id": x.get("order_id") or x.get("id"),
                "source": source,
                "placed_at": x.get("placed_at"),  # 添加placed_at字段
                "filled_at": x.get("filled_at"),  # 添加filled_at字段
                "order_date": x.get("order_date"),  # 添加order_date字段
                "details": x,
            }

        for x in trades[-limit:]:
            records.append(norm(x, "trades"))
        for x in filled[-limit:]:
            records.append(norm(x, "filled"))
        for x in pending[-limit:]:
            records.append(norm(x, "pending"))

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
        # Path 已经在文件顶部导入，不需要重复导入
        
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
            # Path 已经在文件顶部导入，不需要重复导入
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
        log_file = Path("data/logs/discussion_actions.jsonl")
        conversations = []
        
        if log_file.exists():
            with log_file.open("r", encoding="utf-8") as f:
                lines = f.readlines()
                # Read last N lines
                for line in lines[-limit * 2:]:  # Get more lines, then filter
                    try:
                        entry = json.loads(line.strip())
                        # Ensure timestamp field exists for frontend rendering
                        if not entry.get("timestamp"):
                            # fallback to date or now
                            ts_fallback = entry.get("date")
                            if ts_fallback:
                                entry["timestamp"] = f"{ts_fallback}T00:00:00Z"
                            else:
                                entry["timestamp"] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
                        if date:
                            entry_date = entry.get("date", entry.get("timestamp", ""))
                            if entry_date and not entry_date.startswith(date):
                                continue
                        # Exclude demo entries unless explicitly requested
                        if not include_demo and entry.get("type") == "demo":
                            continue
                        conversations.append(entry)
                    except json.JSONDecodeError:
                        continue
        
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
                                # Ensure timestamp is present; if only date available, synthesize a timestamp at midnight UTC
                                memory_date = memory.get("date", "")
                                ts = msg.get("timestamp") or (f"{memory_date}T00:00:00Z" if memory_date else datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'))
                                conversations.append({
                                    "date": memory.get("date", ""),
                                    "type": "memory",
                                    "agent": msg.get("agent", "Unknown"),
                                    "content": msg.get("content", msg.get("message", "")),
                                    "round": msg.get("round"),
                                    "timestamp": ts,
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
    """Reset logs and initialize portfolio to defaults, then seed minimal data.
    
    This will DELETE ALL:
    - Trading history
    - Conversation logs
    - Pending orders
    - Portfolio records
    - Memory files
    """
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Clear ALL log files including memory files
    files_to_clear = [
        "equity_history.jsonl", "filled_orders.jsonl", "pending_orders.jsonl",
        "trades.jsonl", "real_time_snapshots.jsonl", "monitoring.jsonl",
        "discussion_actions.jsonl", "last_trade_date.txt"
    ]
    
    # Clear memory files (daily and weekly)
    try:
        from src.data.memory_manager import MemoryManager
        memory_manager = MemoryManager(root="data/logs")
        # Clear all memory files
        memory_dir = Path("data/logs")
        for memory_file in memory_dir.glob("memory_*.jsonl"):
            try:
                memory_file.unlink()
            except Exception:
                pass
        for memory_file in memory_dir.glob("memory_weekly_*.jsonl"):
            try:
                memory_file.unlink()
            except Exception:
                pass
    except Exception:
        pass
    
    # Clear key log files
    for name in files_to_clear:
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
        "cash": 10000.0,
        "initial_value": 10000.0,
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
    """Kick one trading cycle, but block if already executed today or market is closed."""
    # Check if market is open first
    now = datetime.now()
    is_weekday = now.weekday() < 5
    start = dt_time(9, 30)  # Market opens at 9:30 AM
    end = dt_time(16, 0)     # Market closes at 4:00 PM
    is_open = is_weekday and (start <= now.time() <= end)
    
    if not is_open:
        return {
            "ok": False, 
            "blocked": True, 
            "reason": "market_closed", 
            "message": "Market is closed. Trading only available Mon-Fri, 9:30 AM - 4:00 PM EST"
        }
    
    logs_dir = Path("data/logs")
    logs_dir.mkdir(parents=True, exist_ok=True)
    flag = logs_dir / "last_trade_date.txt"
    today = datetime.now().strftime("%Y-%m-%d")
    if flag.exists():
        last = flag.read_text(encoding="utf-8").strip()
        if last == today:
            return {"ok": False, "blocked": True, "reason": "already_executed_today", "date": today}
    
    # run once
    try:
        res = await execute_trading_cycle()
        
        # If execute_trading_cycle returned a JSONResponse (error), extract error
        if isinstance(res, JSONResponse):
            error_body = res.body.decode('utf-8') if hasattr(res.body, 'decode') else str(res.body)
            try:
                error_data = json.loads(error_body)
                return JSONResponse(
                    status_code=500,
                    content={"ok": False, "error": error_data.get("error", "Unknown error"), "date": today}
                )
            except:
                return JSONResponse(
                    status_code=500,
                    content={"ok": False, "error": "Trading cycle failed", "date": today}
                )
        
        # Success - write flag
        try:
            flag.write_text(today, encoding="utf-8")
        except Exception as e:
            print(f"[WARN] Failed to write last_trade_date.txt: {e}")
        
        return {"ok": True, "result": res, "date": today}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": str(e), "traceback": traceback.format_exc(), "date": today}
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

def run_october_simulation_background():
    """后台运行10月模拟（在单独的线程中）"""
    import sys
    import io
    import time
    # Path 已经在文件顶部导入，不需要重新导入
    
    # Fix encoding
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    try:
        # 确保在backend目录
        backend_dir = Path(__file__).parent.parent.parent
        os.chdir(str(backend_dir))
        sys.path.insert(0, str(backend_dir))
        
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.data.order_manager import OrderManager
        from src.data.portfolio import Portfolio
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
                        print(f"[Simulation] 使用 config.json 中的股票清单: {len(universe)} 只股票")
                    else:
                        print(f"[Simulation] config.json 中没有 universe，使用默认清单: {len(universe)} 只股票")
            except Exception as e:
                print(f"[Simulation] 读取 config.json 失败，使用默认清单: {e}")
        else:
            print(f"[Simulation] config.json 不存在，使用默认清单: {len(universe)} 只股票")
        
        _simulation_status["running"] = True
        _simulation_status["started_at"] = datetime.now(timezone.utc).isoformat()
        _simulation_status["error"] = None
        
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
                        portfolio.positions[symbol] = {"quantity": qty, "avg_cost": avg_cost}
            
            settled_count = 0
            for order in pending_orders:
                symbol = order.get("symbol")
                action = order.get("action", "").upper()
                quantity = order.get("quantity", 0)
                
                try:
                    # 检查订单是否成交（这会检查市场是否开盘）
                    fill_result = order_manager.check_order_fill(order, settle_date)
                    
                    # 如果市场未开盘或订单未成交，跳过
                    if not fill_result.get("filled", False):
                        continue
                    
                    # 订单已成交，执行交易
                    fill_price = fill_result.get("fill_price")
                    if fill_price is None:
                        continue
                    
                    if action == "BUY":
                        portfolio.buy(symbol, quantity, fill_price)
                    elif action == "SELL":
                        portfolio.sell(symbol, quantity, fill_price)
                    
                    # 标记订单为已成交
                    order_manager.mark_order_filled(order, fill_result)
                    settled_count += 1
                except Exception as e:
                    print(f"[Settle Orders] Error processing order {order.get('order_id')}: {e}")
                    pass
            
            portfolio_state = {
                "cash": portfolio.cash,
                "initial_value": portfolio.initial_value,
                "positions": {},
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
            }
            
            for symbol, pos in portfolio.positions.items():
                if isinstance(pos, dict):
                    quantity = pos.get("quantity", 0)
                    avg_cost = pos.get("avg_cost", 0)
                    total_cost = pos.get("total_cost", 0)
                    # 如果total_cost没有保存或为0，从avg_cost和quantity计算
                    if total_cost <= 0:
                        total_cost = avg_cost * quantity
                    portfolio_state["positions"][symbol] = {
                        "quantity": quantity,
                        "avg_cost": avg_cost,
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
            
            # 結算前一天的訂單
            if day_num > 1:
                prev_date = trading_days[day_num - 2].isoformat()
                settle_orders(prev_date, logs_dir)
            
            # 執行當天交易循環
            try:
                window_start = (trade_date - timedelta(days=10)).isoformat()
                window_end = (trade_date + timedelta(days=1)).isoformat()
                
                result = execute_daily_trade(
                    start=window_start,
                    end=window_end,
                    universe=universe  # 使用从 config.json 读取的股票清单
                )
                
                _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
                
            except Exception as e:
                print(f"[Simulation] Error on {trade_date_str}: {e}")
                if "No data" not in str(e) and "YFPricesMissingError" not in str(e):
                    _simulation_status["error"] = str(e)
                    break
            
            # 等待5分钟（如果不是最后一天）
            if day_num < len(trading_days) and _simulation_status["running"]:
                # 等待5分钟 = 300秒
                for _ in range(300):
                    if not _simulation_status["running"]:
                        break
                    time.sleep(1)
        
        # 結算最後一天的訂單
        if trading_days and _simulation_status["running"]:
            last_date = trading_days[-1].isoformat()
            settle_orders(last_date, logs_dir)
        
        _simulation_status["running"] = False
        _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
        
    except Exception as e:
        _simulation_status["running"] = False
        _simulation_status["error"] = str(e)
        _simulation_status["last_update"] = datetime.now(timezone.utc).isoformat()
        import traceback
        traceback.print_exc()


@app.post("/api/trading/simulate-october")
async def simulate_october(background_tasks: BackgroundTasks):
    """启动10月历史数据模拟（后台运行）"""
    if _simulation_status["running"]:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "模拟已在运行中"}
        )
    
    # 重置状态
    _simulation_status["running"] = False
    _simulation_status["current_day"] = 0
    _simulation_status["total_days"] = 22
    _simulation_status["started_at"] = None
    _simulation_status["last_update"] = None
    _simulation_status["error"] = None
    
    # 在后台线程中运行
    import threading
    thread = threading.Thread(target=run_october_simulation_background, daemon=True)
    thread.start()
    
    return {
        "ok": True,
        "message": "10月模拟已启动（后台运行）",
        "status": "started"
    }


@app.get("/api/trading/simulate-status")
async def get_simulation_status():
    """获取10月模拟的状态"""
    return {
        "ok": True,
        "status": _simulation_status.copy()
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
            "seed_conversations": "/api/demo/seed-conversations"
        }
    }

