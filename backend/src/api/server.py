"""
FastAPI server for AI Trader backend
"""
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone, date

# Initialize FastAPI app
app = FastAPI(title="AI Trader API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper function to get project logs directory
def _get_project_logs_dir() -> Path:
    backend_dir = Path(__file__).parent.parent.parent
    project_root = backend_dir.parent
    logs_dir = project_root / "data" / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    return logs_dir

# Helper function to load trading config
def load_trading_config():
    """从 config.json 读取交易配置"""
    config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
    universe = None
    tool_budget = 15  # 默认值
    rounds = 3
    min_tools = 3  # 默认值
    
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                if "universe" in config_data and isinstance(config_data["universe"], list):
                    universe = config_data["universe"]
                # 读取工具预算（优先使用 discussion_tool_budget）
                tool_budget = config_data.get("discussion_tool_budget", config_data.get("tool_budget", 15))
                # 确保至少为8，否则工具调用太少
                if tool_budget < 8:
                    tool_budget = 15
                rounds = config_data.get("discussion_rounds", 3)
                min_tools = config_data.get("discussion_min_tools", 3)
        except Exception as e:
            print(f"[Config] Failed to read config.json, using defaults: {e}")
    
    return {
        "universe": universe,
        "tool_budget": tool_budget,
        "rounds": rounds,
        "min_tools": min_tools
    }

# Root endpoint
@app.get("/")
async def root():
    """根端点，返回 API 信息和端点列表"""
    return {
        "message": "AI Trader API",
        "version": "1.0.0",
        "endpoints": {
            "health": "/api/health",
            "conversations": "/api/agents/conversations",
            "portfolio_realtime": "/api/portfolio/real-time",
            "portfolio_history": "/api/portfolio/equity-history",
            "trades": "/api/trades/recent",
            "execute_trade": "/api/trading/execute-trade",
            "check_orders": "/api/trading/check-pending-orders",
            "market_open": "/api/market/is-open",
            "vix": "/api/vix/term",
            "fear_greed": "/api/fear-greed",
            "system_init": "/api/system/init",
            "system_info": "/api/system/info",
            "agents_status": "/api/agents/status",
            "tools_list": "/api/tools/list",
            "verify_updates": "/api/verify/updates",
        }
    }

# Health check
@app.get("/api/health")
async def health():
    return {"status": "ok"}

# Verify updates endpoint
@app.get("/api/verify/updates")
async def verify_updates():
    """验证 Trading Cycle 更新是否生效"""
    logs_dir = _get_project_logs_dir()
    jsonl_file = logs_dir / "discussion_actions.jsonl"
    
    result = {
        "ok": True,
        "file_exists": jsonl_file.exists(),
        "stats": {
            "RiskAnalyst": 0,
            "DiscussionRound": 0,
            "TraderAgent": 0,
            "DiscussionCoordinator_round0": 0,
        },
        "recent_entries": [],
        "diagnosis": []
    }
    
    if jsonl_file.exists():
        with jsonl_file.open('r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # 分析最后50条
        for line in lines[-50:]:
            try:
                entry = json.loads(line.strip())
                agent = entry.get("agent", "Unknown")
                round_num = entry.get("round", 0)
                
                if agent == "RiskAnalyst":
                    result["stats"]["RiskAnalyst"] += 1
                    if "risk_report" in entry:
                        result["recent_entries"].append({
                            "agent": agent,
                            "round": round_num,
                            "date": entry.get("date"),
                            "has_risk_report": True
                        })
                elif agent == "DiscussionCoordinator":
                    if round_num > 0:
                        result["stats"]["DiscussionRound"] += 1
                        result["recent_entries"].append({
                            "agent": agent,
                            "round": round_num,
                            "date": entry.get("date")
                        })
                    else:
                        result["stats"]["DiscussionCoordinator_round0"] += 1
                elif agent == "TraderAgent":
                    result["stats"]["TraderAgent"] += 1
                    if "decision" in entry:
                        result["recent_entries"].append({
                            "agent": agent,
                            "round": round_num,
                            "date": entry.get("date"),
                            "has_decision": True,
                            "buy_orders_count": entry.get("buy_orders_count", 0)
                        })
            except:
                pass
        
        # 诊断
        if result["stats"]["RiskAnalyst"] > 0:
            result["diagnosis"].append("✅ RiskAnalyst 条目存在")
        else:
            result["diagnosis"].append("❌ 没有 RiskAnalyst 条目 - 后端可能未重启")
        
        if result["stats"]["DiscussionRound"] > 0:
            result["diagnosis"].append("✅ Discussion Round 1/2/3 条目存在")
        else:
            result["diagnosis"].append("❌ 没有 Discussion Round 1/2/3 条目 - 后端可能未重启")
        
        if result["stats"]["TraderAgent"] > 0:
            trader_with_decision = [e for e in result["recent_entries"] if e.get("agent") == "TraderAgent" and e.get("has_decision")]
            if trader_with_decision:
                result["diagnosis"].append("✅ TraderAgent 包含 decision 对象")
            else:
                result["diagnosis"].append("⚠️  TraderAgent 条目存在但缺少 decision 对象")
        else:
            result["diagnosis"].append("❌ 没有 TraderAgent 条目")
    
    return result

# CRITICAL: Execute trading cycle endpoint
@app.post("/api/trading/execute-trade")
@app.get("/api/trading/execute-trade")  # 兼容 GET 方法（不推荐，但前端可能误用）
async def execute_trade_direct():
    """执行交易循环（直接调用）"""
    try:
        from src.orchestrator.trading_cycle import execute_daily_trade
        from src.utils.trading_days import is_market_open
        
        # 加载配置
        config = load_trading_config()
        universe = config["universe"]
        tool_budget = config["tool_budget"]
        rounds = config["rounds"]
        min_tools = config["min_tools"]
        
        # 检查市场状态
        is_market_open_now = is_market_open(datetime.now())
        
        # 执行交易循环
        result = execute_daily_trade(
            rounds=rounds,
            auto_tools=True,
            tool_budget=tool_budget,
            min_tools=min_tools,
            universe=universe
        )
        
        # 根据市场状态返回不同的消息
        if not is_market_open_now:
            message = "Analysis completed (market closed, no trades executed)"
            is_planning = True
        else:
            message = "Trading cycle completed"
            is_planning = False
        
        # 提取订单和对话数量
        placed_orders = result.get("placed_orders", [])
        conversations_count = result.get("conversations_count", 0)
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "message": message,
                "result": {
                    "placed_orders": placed_orders,
                    "conversations_count": conversations_count,
                    "is_planning": is_planning,
                    **result
                }
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": error_msg,
                "traceback": traceback.format_exc()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    
# CRITICAL: Fetch conversations endpoint
@app.get("/api/agents/conversations")
async def fetch_conversations_api(
    limit: int = Query(100, ge=1, le=1000),
    date: Optional[str] = Query(None),
    include_demo: bool = Query(False)
):
    """获取对话记录"""
    try:
        logs_dir = _get_project_logs_dir()
        log_file = logs_dir / "discussion_actions.jsonl"
        
        if not log_file.exists():
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "conversations": [],
                    "count": 0,
                    "total": 0,
                    "has_more": False
                },
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        # 读取对话记录
        conversations = []
        with log_file.open("r", encoding="utf-8") as f:
            # 优化：从文件末尾读取（避免加载整个文件）
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            # 读取最后 ~80KB
            position = max(0, file_size - 8192 * 10)
            f.seek(position)
            lines = f.readlines()
            
            # 处理行（从新到旧）
            for line in reversed(lines[-limit * 3:]):
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    
                    # 过滤 demo 条目
                    if not include_demo and entry.get("type") == "demo":
                        continue
                    
                    # 过滤日期
                    if date and entry.get("date") != date:
                        continue
                    
                    conversations.append(entry)
                except json.JSONDecodeError:
                    continue
        
        # 排序（最新的在前）
        conversations.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # 限制结果
        limited_conversations = conversations[:limit]
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "conversations": limited_conversations,
                "count": len(limited_conversations),
                "total": len(conversations),
                "has_more": len(conversations) > limit
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
                headers={
                    "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )

# ============================================================================
# Portfolio Endpoints
# ============================================================================

@app.get("/api/portfolio/real-time")
async def get_portfolio_real_time():
    """获取投资组合实时数据"""
    try:
        from src.data.portfolio import Portfolio
        from src.tools.market_tools import fetch_market_batch
        
        logs_dir = _get_project_logs_dir()
        portfolio_file = logs_dir / "portfolio_state.json"
        
        # 加载投资组合
        portfolio = Portfolio()
        if portfolio_file.exists():
            try:
                with portfolio_file.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                portfolio.cash = float(state.get("cash", 10000.0))
                portfolio.initial_value = float(state.get("initial_value", 10000.0))
                
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
            except Exception as e:
                print(f"[API] Failed to load portfolio: {e}")
        
        # 获取持仓股票的最新价格
        positions = list(portfolio._positions.keys())
        last_prices = {}
        positions_detail = {}
        positions_pnl = {}
        
        if positions:
            # 先填充所有持仓的基本信息（即使没有价格数据）
            for symbol in positions:
                pos = portfolio._positions[symbol]
                total_cost = getattr(pos, "total_cost", pos.avg_cost * pos.quantity)
                
                # 默认使用 avg_cost 作为价格（如果没有市场数据）
                price = pos.avg_cost
                last_prices[symbol] = price
                
                # 填充基本信息
                positions_detail[symbol] = {
                    "quantity": pos.quantity,
                    "avg_cost": pos.avg_cost,
                    "total_cost": total_cost,
                    "cost_basis": total_cost,
                    "current_price": price,
                    "market_value": pos.quantity * price,
                    "unrealized_pnl": 0.0,  # 默认0，等有真实价格再计算
                    "unrealized_pnl_pct": 0.0,
                }
            
            # 尝试获取实时价格（如果市场开放）
            try:
                market_data = fetch_market_batch(positions)
                for symbol in positions:
                    if symbol in market_data and "price" in market_data[symbol]:
                        price = float(market_data[symbol]["price"])
                        last_prices[symbol] = price
                        
                        # 更新持仓详情（使用真实价格）
                        pos = portfolio._positions[symbol]
                        total_cost = getattr(pos, "total_cost", pos.avg_cost * pos.quantity)
                        positions_detail[symbol] = {
                            "quantity": pos.quantity,
                            "avg_cost": pos.avg_cost,
                            "total_cost": total_cost,
                            "cost_basis": total_cost,
                            "current_price": price,
                            "market_value": pos.quantity * price,
                            "unrealized_pnl": (price - pos.avg_cost) * pos.quantity,
                            "unrealized_pnl_pct": ((price - pos.avg_cost) / pos.avg_cost * 100.0) if pos.avg_cost > 0 else 0.0,
                        }
                        
                        # 计算盈亏
                        positions_pnl[symbol] = portfolio.get_position_pnl(symbol, price)
            except Exception as e:
                print(f"[API] Failed to fetch market data: {e}")
                # 即使失败，positions_detail 也已经填充了基本信息
        
        # 计算总值
        equity_value = portfolio.equity_value(last_prices)
        total_value = portfolio.cash + equity_value
        total_pnl = portfolio.total_pnl(last_prices)
        total_pnl_pct = portfolio.total_pnl_pct(last_prices)
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "cash": portfolio.cash,
                    "total_value": total_value,
                "equity_value": equity_value,
                    "total_pnl": total_pnl,
                    "total_pnl_pct": total_pnl_pct,
                "positions": {sym: pos.quantity for sym, pos in portfolio._positions.items()},
                    "positions_detail": positions_detail,
                "positions_pnl": positions_pnl,
                "positions_count": len(portfolio._positions),
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

@app.get("/api/portfolio/equity-history")
async def get_equity_history(limit: int = Query(60, ge=1, le=1000)):
    """获取权益历史"""
    try:
        logs_dir = _get_project_logs_dir()
        equity_file = logs_dir / "equity_history.jsonl"
        
        if not equity_file.exists():
            return JSONResponse(
                status_code=200,
                content={
                "ok": True,
                    "records": []
                },
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        # 读取最后 N 条记录
        records = []
        with equity_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines[-limit:]):
                if line.strip():
                    try:
                        record = json.loads(line.strip())
                        records.append(record)
                    except json.JSONDecodeError:
                        continue
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "records": records
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

# ============================================================================
# Trading Endpoints
# ============================================================================

@app.get("/api/trades/recent")
async def get_recent_trades(limit: int = Query(10, ge=1, le=1000)):
    """获取最近交易"""
    try:
        logs_dir = _get_project_logs_dir()
        filled_file = logs_dir / "filled_orders.jsonl"
        
        if not filled_file.exists():
            return JSONResponse(
                status_code=200,
                content={
                    "ok": True,
                    "trades": []
                },
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )
        
        # 读取最后 N 条记录
        trades = []
        with filled_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in reversed(lines[-limit:]):
                if line.strip():
                    try:
                        trade = json.loads(line.strip())
                        trades.append(trade)
                    except json.JSONDecodeError:
                        continue
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "trades": trades
            },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
        )

@app.get("/api/trading/check-pending-orders")
@app.post("/api/trading/check-pending-orders")  # 前端使用 POST
async def check_pending_orders():
    """检查并结算待处理订单"""
    try:
        from src.data.order_manager import OrderManager
        
        logs_dir = _get_project_logs_dir()
        order_manager = OrderManager(root=str(logs_dir))
        
        # 加载待处理订单
        pending_orders = order_manager.load_pending_orders()
        
        # 这里可以添加结算逻辑（如果需要）
        # 目前只返回订单状态
        
        return JSONResponse(
            status_code=200,
            content={
            "ok": True,
                "message": f"Checked {len(pending_orders)} pending orders, 0 filled, 0 rejected",
                "settled_count": 0,
                "rejected_count": 0,
                "pending_count": len(pending_orders),
                "pending_orders": pending_orders
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

# ============================================================================
# Market Endpoints
# ============================================================================

@app.get("/api/market/is-open")
async def check_market_open():
    """检查市场是否开放"""
    try:
        from src.utils.trading_days import is_market_open
        
        now = datetime.now()
        market_open = is_market_open(now)
        
        return JSONResponse(
            status_code=200,
            content={
            "ok": True,
                "is_open": market_open,
                "timestamp": now.isoformat()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

@app.get("/api/vix/term")
async def get_vix_term():
    """获取 VIX 期限结构"""
    try:
        from src.tools.market_tools import get_vix_term_structure
        
        vix_data = get_vix_term_structure()
        
        # 如果返回 None 或空数据，返回默认值
        if vix_data is None:
            vix_data = {"level": None, "regime": "unknown"}
        
        return JSONResponse(
            status_code=200,
            content={
            "ok": True,
                "vix": vix_data
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        # 返回默认值而不是错误，避免前端显示错误
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "vix": {"level": None, "regime": "unknown", "error": str(e)}
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

@app.get("/api/fear-greed")
async def get_fear_greed():
    """获取恐惧贪婪指数"""
    try:
        from src.tools.market_tools import get_fear_greed_index
        
        fg_data = get_fear_greed_index()
        
        # 如果返回 None 或空数据，返回默认值
        if fg_data is None:
            fg_data = {"value": 0, "label": "Unknown"}
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True, 
                "fear_greed": fg_data
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        # 返回默认值而不是错误，避免前端显示错误
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "fear_greed": {"value": 0, "label": "Unknown", "error": str(e)}
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

# ============================================================================
# System Endpoints
# ============================================================================

@app.post("/api/system/init")
async def system_init(force: bool = Query(False)):
    """系统初始化（删除所有数据）"""
    try:
        if not force:
            return JSONResponse(
                status_code=400,
                content={
                    "ok": False,
                    "error": "force parameter required"
                },
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "POST, OPTIONS",
                    "Access-Control-Allow-Headers": "*",
                }
            )

        logs_dir = _get_project_logs_dir()
        
        # 备份 portfolio_state.json（如果存在）
        portfolio_file = logs_dir / "portfolio_state.json"
        if portfolio_file.exists():
            backup_file = logs_dir / f"portfolio_state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            import shutil
            shutil.copy2(portfolio_file, backup_file)
        
        # 删除所有数据文件
        files_to_delete = [
            "portfolio_state.json",
            "pending_orders.jsonl",
            "filled_orders.jsonl",
            "equity_history.jsonl",
            "discussion_actions.jsonl",
        ]
        
        deleted = []
        for filename in files_to_delete:
            file_path = logs_dir / filename
            if file_path.exists():
                file_path.unlink()
                deleted.append(filename)
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "message": f"System initialized. Deleted {len(deleted)} files.",
                "deleted_files": deleted
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.get("/api/system/info")
async def get_system_info():
    """获取系统信息"""
    try:
        config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
        config_data = {}
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except:
                pass
        
        return JSONResponse(
            status_code=200,
            content={
            "ok": True,
                "llm_model": config_data.get("llm_model", "Unknown"),
                "llm_base_url": config_data.get("llm_base_url", "Unknown"),
                "version": "1.0.0"
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

# ============================================================================
# Agent & Tools Endpoints
# ============================================================================

@app.get("/api/agents/status")
async def get_agents_status():
    """获取代理状态"""
    try:
        # 返回代理状态（简化版本）
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "agents": {
                    "MarketAnalyst": "active",
                    "TechnicalAnalyst": "active",
                    "FundamentalAnalyst": "active",
                    "SentimentAnalyst": "active",
                    "RiskAnalyst": "active",
                    "TraderAgent": "active",
                }
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )

@app.get("/api/tools/list")
async def get_tools_list():
    """获取工具列表"""
    try:
        from src.agents.toolbox import ToolBox
        
        toolbox = ToolBox()
        tools = []
        
        # 获取所有工具
        for tool_name in toolbox.tools.keys():
            tool_info = toolbox.tools[tool_name]
            tools.append({
                "name": tool_name,
                "description": getattr(tool_info, "__doc__", "") or "",
            })
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "tools": tools
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
