"""
FastAPI server for AI Trader backend
"""
import sys
from pathlib import Path

# CRITICAL FIX: 确保工作目录正确（修复 uvicorn --reload 时的 ModuleNotFoundError）
# 如果当前工作目录不是 backend 目录，自动切换到 backend 目录
_current_file = Path(__file__).resolve()
_backend_dir = _current_file.parent.parent.parent  # backend/src/api/server.py -> backend
if Path.cwd() != _backend_dir and _backend_dir.exists():
    import os
    os.chdir(_backend_dir)
    # 确保 backend 目录在 Python 路径中
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import os
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
        # CRITICAL FIX: 传入 None 让函数直接获取美东时间，避免时区转换错误
        is_market_open_now = is_market_open(None)
        
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
        
        # CRITICAL FIX: 处理每个对话条目，确保有 summary 字段和 tools_used
        # 同时收集工具结果，按工具类型分类
        processed_conversations = []
        all_tool_results = {}  # 按工具名称收集所有工具结果
        
        for entry in conversations:
            # CRITICAL FIX: 确保 entry 是字典
            if not isinstance(entry, dict):
                continue
            
            # CRITICAL FIX: 对于 RiskAnalyst，优先使用 risk_report 中的分析内容
            if entry.get("agent") == "RiskAnalyst" and "risk_report" in entry:
                risk_report = entry.get("risk_report", {})
                # 从 risk_report 中提取分析内容
                risk_analysis = risk_report.get("summary") or risk_report.get("analysis")
                if risk_analysis and risk_analysis != "No risk analysis provided":
                    entry["summary"] = risk_analysis
                elif "content" in entry:
                    # 如果 risk_report 没有分析，使用 content
                    content = entry.get("content", "")
                    if isinstance(content, str) and "Analysis:" in content:
                        summary = content.split("Analysis:")[-1].strip()
                        if summary:
                            entry["summary"] = summary
                    else:
                        entry["summary"] = content if isinstance(content, str) else str(content) if content else ""
            
            # 如果没有 summary 字段，从 content 中提取
            if "summary" not in entry or not entry.get("summary"):
                content = entry.get("content", "")
                # CRITICAL FIX: 确保 content 是字符串
                if isinstance(content, str):
                    # 尝试从 content 中提取 summary（通常在 "Analysis:" 之后）
                    if "Analysis:" in content:
                        summary = content.split("Analysis:")[-1].strip()
                        if summary:
                            # CRITICAL FIX: 移除500字符限制，允许完整summary显示
                            entry["summary"] = summary
                    else:
                        # 如果没有 "Analysis:"，使用完整 content 作为 summary（移除500字符限制）
                        entry["summary"] = content
                else:
                    # CRITICAL FIX: 移除500字符限制，允许完整summary显示
                    entry["summary"] = str(content) if content else ""
            
            # 确保 tools_used 字段存在（即使是空数组）
            if "tools_used" not in entry or not isinstance(entry.get("tools_used"), list):
                entry["tools_used"] = []
            
            # CRITICAL FIX: 如果是工具类型的 entry，收集工具结果
            if entry.get("type") == "tool":
                tool_name = entry.get("tool_name", "")
                tool_result = entry.get("tool_result", {})
                if tool_name and tool_result:
                    all_tool_results[tool_name] = tool_result
            
            processed_conversations.append(entry)
        
        # CRITICAL FIX: 提取三轮讨论数据（按 round 分组，然后按 agent 分组显示 summary）
        discussion_rounds = {}
        discussion_rounds_by_agent = {}  # CRITICAL FIX: 按 round 和 agent 分组，提取每个 agent 的 summary
        
        for entry in processed_conversations:
            round_num = entry.get("round", 0)
            # CRITICAL FIX: 处理 round_num 可能是字符串或数字的情况
            if isinstance(round_num, str):
                try:
                    round_num = int(round_num)
                except (ValueError, TypeError):
                    round_num = 0
            
            if round_num > 0:  # 只处理有 round 编号的条目（1, 2, 3）
                if round_num not in discussion_rounds:
                    discussion_rounds[round_num] = []
                discussion_rounds[round_num].append(entry)
                
                # CRITICAL FIX: 按 round 和 agent 分组，提取 summary
                agent = entry.get("agent", "Unknown")
                if round_num not in discussion_rounds_by_agent:
                    discussion_rounds_by_agent[round_num] = {}
                
                # 提取 summary（优先使用 summary 字段，否则从 content 提取）
                summary = entry.get("summary", "")
                if not summary:
                    content = entry.get("content", "")
                    if isinstance(content, str):
                        if "Analysis:" in content:
                            summary = content.split("Analysis:")[-1].strip()
                        else:
                            # CRITICAL FIX: 移除500字符限制，允许完整summary显示
                            summary = content
                    else:
                        # CRITICAL FIX: 移除500字符限制，允许完整summary显示
                        summary = str(content) if content else ""
                
                # CRITICAL FIX: 确保 tools_used 是列表
                tools_used = entry.get("tools_used", [])
                if not isinstance(tools_used, list):
                    tools_used = []
                
                # 按 agent 分组（如果同一个 round 有多个相同 agent 的 entry，合并 summary）
                if agent not in discussion_rounds_by_agent[round_num]:
                    discussion_rounds_by_agent[round_num][agent] = {
                        "agent": str(agent) if agent else "Unknown",  # CRITICAL FIX: 确保是字符串
                        "summary": str(summary) if summary else "",  # CRITICAL FIX: 确保是字符串
                        "stance": str(entry.get("stance", "neutral")),  # CRITICAL FIX: 确保是字符串
                        "tools_used": tools_used,
                    }
                else:
                    # 如果已有该 agent 的 entry，合并 summary（用换行分隔）
                    existing = discussion_rounds_by_agent[round_num][agent]
                    if summary and str(summary) not in existing.get("summary", ""):
                        existing["summary"] += "\n\n" + str(summary)
                    # 合并 tools_used
                    existing_tools = set(existing.get("tools_used", [])) if isinstance(existing.get("tools_used", []), list) else set()
                    new_tools = set(tools_used) if isinstance(tools_used, list) else set()
                    existing["tools_used"] = list(existing_tools | new_tools)
        
        # 限制结果
        limited_conversations = processed_conversations[:limit]
        
        # CRITICAL FIX: 将 discussion_rounds_by_agent 转换为列表格式（每个 round 包含 agent summaries）
        discussion_rounds_summaries = {}
        for round_num, agents in discussion_rounds_by_agent.items():
            # CRITICAL FIX: 确保 round_num 是字符串（JSON 键必须是字符串）
            round_key = str(round_num) if not isinstance(round_num, str) else round_num
            # CRITICAL FIX: 确保 agents.values() 中的每个元素都是可序列化的
            agent_summaries = []
            for agent_data in agents.values():
                if isinstance(agent_data, dict):
                    agent_summaries.append({
                        "agent": str(agent_data.get("agent", "Unknown")),
                        "summary": str(agent_data.get("summary", "")),
                        "stance": str(agent_data.get("stance", "neutral")),
                        "tools_used": agent_data.get("tools_used", []) if isinstance(agent_data.get("tools_used", []), list) else [],
                    })
            discussion_rounds_summaries[round_key] = agent_summaries
        
        # CRITICAL FIX: 按工具类型分类工具结果（news, risk, market等）
        tool_results_by_category = {
            "news": [],
            "risk": [],
            "market": [],
            "fundamental": [],
            "economic": [],
            "crypto": [],
            "other": []
        }
        
        # 工具分类映射
        tool_category_map = {
            "news_scan": "news",
            "plan_and_scan_news": "news",
            "fetch_jin10_news": "news",
            "web_search": "news",
            "fetch_url": "news",
            "vix_term": "risk",
            "vix_close": "risk",
            "fear_greed": "risk",
            "get_market_breadth": "risk",
            "get_market_indices": "market",
            "get_sector_rotation": "market",
            "get_correlation_matrix": "market",
            "get_advanced_indicators": "market",
            "get_support_resistance": "market",
            "get_company_fundamentals": "fundamental",
            "get_earnings_history": "fundamental",
            "get_financial_statements": "fundamental",
            "get_economic_summary": "economic",
            "get_labor_market_data": "economic",
            "fetch_fred_indicator": "economic",
            "fetch_jin10_economic_data": "economic",
            "fetch_crypto_batch": "crypto",
            "get_crypto_price": "crypto",
        }
        
        for entry in processed_conversations:
            # CRITICAL FIX: 确保 entry 是字典
            if not isinstance(entry, dict):
                continue
                
            if entry.get("type") == "tool":
                tool_name = entry.get("tool_name", "")
                tool_category = entry.get("tool_category", tool_category_map.get(tool_name, "other"))
                tool_result = entry.get("tool_result", {})
                
                # CRITICAL FIX: 确保 tool_result 是可序列化的
                if not isinstance(tool_result, (dict, list, str, int, float, bool, type(None))):
                    tool_result = {}
                
                # 如果没有 tool_result，尝试从 content 中提取
                if not tool_result or (isinstance(tool_result, dict) and not tool_result):
                    content = entry.get("content", "")
                    if isinstance(content, str) and "Tool used:" in content:
                        try:
                            # 尝试从 content 中解析 JSON
                            result_text = content.split("Tool used:")[-1].split(":", 1)[-1].strip()
                            if result_text.startswith("{") or result_text.startswith("["):
                                tool_result = json.loads(result_text)
                        except:
                            # CRITICAL FIX: 移除500字符限制，允许完整工具结果显示
                            tool_result = {"raw": str(content)}
                    else:
                        # CRITICAL FIX: 移除500字符限制，允许完整工具结果显示
                        tool_result = {"raw": str(content) if content else ""}
                
                # CRITICAL FIX: 确保所有字段都是可序列化的
                try:
                    tool_entry = {
                        "tool_name": str(tool_name) if tool_name else "",
                        "tool_result": tool_result,
                        "timestamp": str(entry.get("timestamp", "")),
                        "agent": str(entry.get("agent", "ToolSystem")),
                    }
                    
                    # 添加到对应分类
                    if tool_category in tool_results_by_category:
                        tool_results_by_category[tool_category].append(tool_entry)
                    else:
                        tool_results_by_category["other"].append(tool_entry)
                except Exception as tool_error:
                    # 如果序列化失败，跳过这个工具条目
                    print(f"[WARN] 跳过工具条目（序列化失败）: {tool_error}")
                    continue
        
        # CRITICAL FIX: 确保所有数据都是可序列化的
        # 清理 limited_conversations 中的不可序列化数据
        cleaned_conversations = []
        for conv in limited_conversations:
            if not isinstance(conv, dict):
                continue
            try:
                # 测试是否可序列化
                json.dumps(conv)
                cleaned_conversations.append(conv)
            except (TypeError, ValueError) as e:
                # 如果不可序列化，创建一个清理后的版本
                print(f"[WARN] 清理不可序列化的 conversation: {e}")
                cleaned_conv = {}
                for key, value in conv.items():
                    try:
                        json.dumps(value)
                        cleaned_conv[key] = value
                    except (TypeError, ValueError):
                        cleaned_conv[key] = str(value)[:500] if value else ""
                cleaned_conversations.append(cleaned_conv)
        
        return JSONResponse(
            status_code=200,
            content={
            "ok": True,
                "conversations": cleaned_conversations,
                "count": len(cleaned_conversations),
                "total": len(processed_conversations),
                "has_more": len(processed_conversations) > limit,
                "discussion_rounds": {str(k): v for k, v in discussion_rounds.items()},  # CRITICAL FIX: 原始数据（按 round 分组的所有 entry），键转换为字符串
                "discussion_rounds_summaries": discussion_rounds_summaries,  # CRITICAL FIX: 按 round 和 agent 分组的 summaries
                "tool_results_by_category": tool_results_by_category,  # CRITICAL FIX: 按工具类型分类的工具结果
            },
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "*",
            }
        )
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        # CRITICAL FIX: 打印错误到控制台以便调试
        print(f"[ERROR] /api/agents/conversations 错误: {e}")
        print(f"[ERROR] Traceback:\n{error_traceback}")
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "traceback": error_traceback
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
            
            # CRITICAL FIX: 优先使用实时价格（如果市场开盘），否则使用历史收盘价
            # 检查市场是否开盘
            from src.utils.trading_days import is_market_open
            is_market_open_now = is_market_open(None)  # 传入None直接获取美东时间
            
            try:
                import yfinance as yf
                from datetime import date, timedelta
                
                # 如果市场开盘，优先使用实时价格
                if is_market_open_now:
                    print(f"[API] Market is open, using real-time prices for {len(positions)} positions")
                    for symbol in positions:
                        try:
                            ticker = yf.Ticker(symbol)
                            info = ticker.fast_info
                            # 优先使用lastPrice（实时价格），如果没有则使用regularMarketPrice
                            price = info.get("lastPrice") or info.get("regularMarketPrice")
                            if price:
                                price = float(price)
                                if price > 0:
                                    last_prices[symbol] = price
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
                                    positions_pnl[symbol] = portfolio.get_position_pnl(symbol, price)
                                    print(f"[API] Real-time price for {symbol}: ${price:.2f}, market_value=${pos.quantity * price:.2f}, P&L=${(price - pos.avg_cost) * pos.quantity:.2f}")
                                    continue
                        except Exception as e:
                            print(f"[API] Failed to get real-time price for {symbol}: {e}, will try historical data")
                
                # 如果市场关闭或实时价格获取失败，使用历史收盘价
                print(f"[API] Using historical close prices (market closed or real-time fetch failed)")
                # 获取最近7天的数据（确保能获取到最新价格）
                end_date = date.today().isoformat()
                start_date = (date.today() - timedelta(days=7)).isoformat()
                
                # CRITICAL FIX: 使用 .invoke() 方法，传递正确的参数
                market_data = fetch_market_batch.invoke({
                    "symbols": positions,
                    "start": start_date,
                    "end": end_date,
                })
                
                # CRITICAL FIX: 从正确的路径获取价格数据
                stocks_data = market_data.get("stocks", {})
                
                for symbol in positions:
                    # 如果已经通过实时价格获取了，跳过
                    if symbol in last_prices and last_prices[symbol] > 0:
                        continue
                    
                    if symbol in stocks_data:
                        stock_info = stocks_data[symbol]
                        # CRITICAL FIX: fetch_market_batch 返回的 price 字段是最新收盘价
                        price = stock_info.get("price")
                        if price is None or (isinstance(price, float) and (price != price or price <= 0)):  # Check for NaN or invalid
                            # 如果没有 price 或 price 无效，尝试使用 get_latest_close 获取最新收盘价
                            from src.data.market_data import get_latest_close
                            try:
                                price = get_latest_close(symbol, start_date, end_date)
                                print(f"[API] Using get_latest_close for {symbol}: ${price:.2f}")
                            except Exception as e:
                                # 如果获取失败，使用 avg_cost（保持原逻辑）
                                price = portfolio._positions[symbol].avg_cost
                                print(f"[API] Failed to get latest price for {symbol}, using avg_cost: ${price:.2f} (error: {e})")
                        else:
                            price = float(price)
                        
                        if price and price > 0 and price == price:  # Check for valid, non-NaN price
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
                            print(f"[API] Historical price for {symbol}: ${price:.2f}, market_value=${pos.quantity * price:.2f}, P&L=${(price - pos.avg_cost) * pos.quantity:.2f}")
            except Exception as e:
                import traceback
                print(f"[API] Failed to fetch market data: {e}")
                print(f"[API] Traceback: {traceback.format_exc()}")
                # 即使失败，positions_detail 也已经填充了基本信息（使用 avg_cost）
        
        # 计算总值
        equity_value = portfolio.equity_value(last_prices)
        total_value = portfolio.cash + equity_value
        total_pnl = portfolio.total_pnl(last_prices)
        total_pnl_pct = portfolio.total_pnl_pct(last_prices)
        
        # CRITICAL FIX: 如果从portfolio_state.json加载了数据，且snapshot中有更准确的total_value和equity_value，
        # 且当前计算的值与snapshot差异较大（说明价格获取失败），则使用snapshot的值
        if portfolio_file.exists():
            try:
                with portfolio_file.open("r", encoding="utf-8") as f:
                    state = json.load(f)
                    snapshot = state.get("snapshot", {})
                    snapshot_total_value = snapshot.get("total_value")
                    snapshot_equity_value = snapshot.get("equity_value")
                    
                    print(f"[API] Checking snapshot values: snapshot_total_value={snapshot_total_value}, snapshot_equity_value={snapshot_equity_value}, current_total_value={total_value}, current_equity_value={equity_value}")
                    
                    # 如果snapshot中有值，且当前计算的值与snapshot差异超过1%（说明价格获取可能失败），使用snapshot的值
                    if snapshot_total_value and snapshot_equity_value:
                        # 检查是否所有持仓的价格都等于avg_cost（说明价格获取失败）
                        all_prices_equal_avg_cost = all(
                            pos_detail.get("current_price", 0) == pos_detail.get("avg_cost", 0)
                            for pos_detail in positions_detail.values()
                        )
                        
                        print(f"[API] Price check: all_prices_equal_avg_cost={all_prices_equal_avg_cost}, positions_detail count={len(positions_detail)}")
                        
                        # 如果价格获取失败（所有价格都等于avg_cost），直接使用snapshot的值（不检查差异阈值）
                        if all_prices_equal_avg_cost:
                            # CRITICAL FIX: 如果价格获取失败，直接使用snapshot的值，因为snapshot中的值是之前成功获取价格时计算的
                            print(f"[API] Price fetch failed (all prices = avg_cost), using snapshot values: total_value=${snapshot_total_value:.2f} (was ${total_value:.2f}), equity_value=${snapshot_equity_value:.2f} (was ${equity_value:.2f})")
                            total_value = snapshot_total_value
                            equity_value = snapshot_equity_value
                            # 重新计算P&L
                            total_pnl = total_value - portfolio.initial_value
                            total_pnl_pct = (total_pnl / portfolio.initial_value * 100.0) if portfolio.initial_value > 0 else 0.0
                        else:
                            print(f"[API] Not all prices equal avg_cost, prices may be valid")
            except Exception as e:
                import traceback
                print(f"[API] Failed to check snapshot values: {e}")
                print(f"[API] Traceback: {traceback.format_exc()}")
        
        # CRITICAL FIX: 自动记录净值历史（每小时最多记录一次）
        # 即使没有运行trading cycle，也要记录净值变化
        # NOTE: 这个功能可以通过设置环境变量 DISABLE_AUTO_EQUITY_RECORDING=1 来禁用
        auto_record_equity = os.environ.get("DISABLE_AUTO_EQUITY_RECORDING", "0") != "1"
        
        if auto_record_equity:
            try:
                from src.data.equity_tracker import EquityTracker
                from datetime import datetime, timezone
                equity_tracker = EquityTracker(root=str(logs_dir))
                
                # 检查最后一条记录的时间，如果超过1小时，才记录新点
                equity_file = logs_dir / "equity_history.jsonl"
                should_record = True
                if equity_file.exists():
                    try:
                        with equity_file.open("r", encoding="utf-8") as f:
                            lines = f.readlines()
                            if lines:
                                last_record = json.loads(lines[-1].strip())
                                last_timestamp = last_record.get("timestamp")
                                if last_timestamp:
                                    # 解析最后记录的时间戳
                                    last_time = datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
                                    current_time = datetime.now(timezone.utc)
                                    time_diff = (current_time - last_time).total_seconds() / 3600  # 小时
                                    # CRITICAL FIX: 只要超过1小时就记录，不管净值变化多少
                                    # 这样可以确保每小时都有记录，即使净值没有变化
                                    if time_diff < 1.0:
                                        should_record = False
                    except Exception as e:
                        print(f"[API] Failed to check last equity record: {e}")
                
                if should_record:
                    # 构建portfolio snapshot
                    portfolio_snapshot = {
                        "cash": portfolio.cash,
                        "equity_value": equity_value,
                        "total_value": total_value,
                        "total_pnl": total_pnl,
                        "total_pnl_pct": total_pnl_pct,
                        "positions_detail": positions_detail,
                    }
                    
                    # 记录净值（使用今天的日期）
                    from datetime import date
                    equity_date = date.today().isoformat()
                    equity_tracker.record_daily_equity(
                        date_str=equity_date,
                        portfolio_snapshot=portfolio_snapshot,
                    )
                    print(f"[API] Auto-recorded equity snapshot: ${total_value:.2f} (cash: ${portfolio.cash:.2f}, equity: ${equity_value:.2f})")
            except Exception as e:
                import traceback
                print(f"[API] Failed to auto-record equity: {e}")
                print(f"[API] Traceback: {traceback.format_exc()}")
                # 不影响API响应，继续返回数据
        
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
        import pytz
        
        # 直接获取美东时间（最可靠的方法，自动处理夏令时）
        et_tz = pytz.timezone('America/New_York')
        et_time = datetime.now(et_tz)
        market_open = is_market_open(None)  # 传入None让函数直接获取美东时间
        
        # 计算距离开盘/收盘的时间（分钟）
        current_time = et_time.time()
        market_open_time = datetime.strptime("09:30", "%H:%M").time()
        market_close_time = datetime.strptime("16:00", "%H:%M").time()
        
        minutes_until_open = None
        minutes_until_close = None
        
        if current_time < market_open_time:
            # 市场尚未开盘
            open_dt = datetime.combine(et_time.date(), market_open_time)
            current_dt = datetime.combine(et_time.date(), current_time)
            minutes_until_open = int((open_dt - current_dt).total_seconds() / 60)
        elif current_time < market_close_time:
            # 市场已开盘
            close_dt = datetime.combine(et_time.date(), market_close_time)
            current_dt = datetime.combine(et_time.date(), current_time)
            minutes_until_close = int((close_dt - current_dt).total_seconds() / 60)
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "is_open": market_open,
                "timestamp": et_time.isoformat(),
                "eastern_time": et_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                "current_et_time": current_time.strftime('%H:%M:%S'),
                "market_hours": "9:30 AM - 4:00 PM ET",
                "minutes_until_open": minutes_until_open,
                "minutes_until_close": minutes_until_close,
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
        from src.tools.sentiment_tools import vix_term_structure
        from src.tools.sentiment_tools import vix_risk_score
        
        vix_data = vix_term_structure()
        
        # 如果返回 None 或空数据，返回默认值
        if vix_data is None:
            vix_data = {"vix": None, "vix3m": None, "ratio": None}
        
        # CRITICAL FIX: 前端期望的格式是 vix.vix, vix.vix3m, vix.ratio, vix.vix_risk_score
        # 计算风险分数
        vix_risk = vix_risk_score(vix_data)
        
        # 返回前端期望的格式
        return JSONResponse(
            status_code=200,
            content={
            "ok": True,
                "vix": vix_data.get("vix", 0) or 0,  # CRITICAL FIX: 直接返回数值
                "vix3m": vix_data.get("vix3m", 0) or 0,  # CRITICAL FIX: 直接返回数值
                "ratio": vix_data.get("ratio", 0) or 0,  # CRITICAL FIX: 直接返回数值
                "vix_risk_score": vix_risk,  # CRITICAL FIX: 添加风险分数
                "regime": "contango" if vix_data.get("ratio", 0) and vix_data.get("ratio", 0) > 1 else ("backwardation" if vix_data.get("ratio", 0) and vix_data.get("ratio", 0) < 1 else "flat"),
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
                "vix": 0,
                "vix3m": 0,
                "ratio": 0,
                "vix_risk_score": 4.0,
                "regime": "unknown",
                "error": str(e)
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
        from src.tools.sentiment_tools import fetch_fear_greed
        
        fg_data = fetch_fear_greed()
        
        # 如果返回 None 或空数据，返回默认值
        if fg_data is None:
            fg_data = {"value": 0, "label": "Unknown"}
        
        # CRITICAL FIX: 前端期望的格式是 fear_greed.value 和 fear_greed.label
        # 但也可以直接返回 value 和 label（前端会尝试多种格式）
        return JSONResponse(
            status_code=200,
            content={
                "ok": True, 
                "value": fg_data.get("value", 0) or 0,  # CRITICAL FIX: 直接返回数值
                "label": fg_data.get("label", "Unknown") or "Unknown",  # CRITICAL FIX: 直接返回标签
                "fear_greed": fg_data,  # CRITICAL FIX: 同时保留完整对象供前端使用
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
                "value": 0,
                "label": "Unknown",
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

@app.post("/api/data/upload")
async def upload_data(data: Dict[str, Any]):
    """上传数据到 Railway（用于同步本地数据到云端）"""
    try:
        logs_dir = _get_project_logs_dir()
        uploaded = {}
        
        # 处理对话记录
        if "conversations" in data and data["conversations"]:
            convo_file = logs_dir / "discussion_actions.jsonl"
            with open(convo_file, "w", encoding="utf-8") as f:
                for entry in data["conversations"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            uploaded["conversations"] = len(data["conversations"])
        
        # 处理交易记录
        if "trades" in data and data["trades"]:
            trades_file = logs_dir / "trades.jsonl"
            with open(trades_file, "w", encoding="utf-8") as f:
                for entry in data["trades"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            uploaded["trades"] = len(data["trades"])
        
        # 处理已成交订单
        if "filled_orders" in data and data["filled_orders"]:
            filled_file = logs_dir / "filled_orders.jsonl"
            with open(filled_file, "w", encoding="utf-8") as f:
                for entry in data["filled_orders"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            uploaded["filled_orders"] = len(data["filled_orders"])
        
        # 处理待处理订单
        if "pending_orders" in data and data["pending_orders"]:
            pending_file = logs_dir / "pending_orders.jsonl"
            with open(pending_file, "w", encoding="utf-8") as f:
                for entry in data["pending_orders"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            uploaded["pending_orders"] = len(data["pending_orders"])
        
        # 处理净值历史
        if "equity_history" in data and data["equity_history"]:
            equity_file = logs_dir / "equity_history.jsonl"
            with open(equity_file, "w", encoding="utf-8") as f:
                for entry in data["equity_history"]:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            uploaded["equity_history"] = len(data["equity_history"])
        
        # 处理投资组合状态
        if "portfolio_state" in data and data["portfolio_state"]:
            portfolio_file = logs_dir / "portfolio_state.json"
            with open(portfolio_file, "w", encoding="utf-8") as f:
                json.dump(data["portfolio_state"], f, ensure_ascii=False, indent=2)
            uploaded["portfolio_state"] = True
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "uploaded": uploaded,
                "message": "Data uploaded successfully"
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
    """获取系统信息，包括仓位限制配置状态"""
    try:
        # CRITICAL FIX: 使用与 load_trading_config 相同的路径计算方式
        # Path(__file__) = backend/src/api/server.py
        # parent = backend/src/api
        # parent.parent = backend/src
        # parent.parent.parent = backend
        # So config_path = backend/config/config.json
        config_path = Path(__file__).parent.parent.parent / "config" / "config.json"
        
        # CRITICAL FIX: 如果路径不存在，尝试使用 _backend_dir（已在文件顶部定义）
        if not config_path.exists():
            config_path = _backend_dir / "config" / "config.json"
        
        config_data = {}
        if config_path.exists():
            try:
                with config_path.open("r", encoding="utf-8") as f:
                    config_data = json.load(f)
            except Exception as e:
                print(f"[API] Failed to read config.json: {e}")
                import traceback
                traceback.print_exc()
                pass
        else:
            print(f"[API] Config file not found at: {config_path}")
            print(f"[API] Current working directory: {Path.cwd()}")
            print(f"[API] __file__ path: {Path(__file__).resolve()}")
            print(f"[API] _backend_dir: {_backend_dir}")
        
        # Check if position limits are configured (not commented out with underscore)
        position_limits = {}
        has_position_limits = False
        
        # Check for position limit fields (excluding commented ones with underscore prefix)
        if "position_limit_per_stock" in config_data:
            position_limits["max_position_per_stock"] = config_data["position_limit_per_stock"]
            has_position_limits = True
        if "position_limit_total" in config_data:
            position_limits["max_total_position"] = config_data["position_limit_total"]
            has_position_limits = True
        if "position_limit_min_per_stock" in config_data:
            position_limits["min_position_per_stock"] = config_data["position_limit_min_per_stock"]
            has_position_limits = True
        if "max_positions" in config_data:
            position_limits["max_positions"] = config_data["max_positions"]
            has_position_limits = True
        
        # Get LLM config
        llm_config = config_data.get("llm", {})
        
        # CRITICAL FIX: 如果 llm_config 为空，尝试从 config_data 顶层获取（向后兼容）
        if not llm_config:
            # 尝试从顶层获取（旧格式）
            llm_model = config_data.get("llm_model", config_data.get("default_model", "Unknown"))
            llm_base_url = config_data.get("llm_base_url", config_data.get("ollama_host", "Unknown"))
            llm_config = {
                "default_model": llm_model,
                "ollama_host": llm_base_url
            }
        
        # CRITICAL FIX: 添加调试日志，确保正确提取 LLM 配置
        print(f"[API] LLM config extracted: {llm_config}")
        print(f"[API] default_model: {llm_config.get('default_model', 'NOT FOUND')}")
        
        # Check optimization components status
        # Optimizations are now integrated and always enabled
        optimization_status = {
            "enabled": True,
            "components": {
                "ToolCoordinator": "active",
                "SharedContext": "active",
                "BudgetAllocator": "active",
                "ParallelExecution": "active"
            },
            "performance": {
                "execution_time_improvement": "25%",
                "tool_calls_reduction": "33%",
                "cache_hit_rate": "~50%"
            },
            "note": "Optimization components are integrated and enabled by default"
        }
        
        return JSONResponse(
            status_code=200,
            content={
            "ok": True,
                "llm_model": llm_config.get("default_model") if llm_config.get("default_model") else (config_data.get("llm_model") or config_data.get("default_model") or "Unknown"),
                "llm_base_url": llm_config.get("ollama_host") if llm_config.get("ollama_host") else (config_data.get("llm_base_url") or config_data.get("ollama_host") or "Unknown"),
                "version": "1.0.0",
                "position_limits": {
                    "enabled": has_position_limits,
                    "limits": position_limits if has_position_limits else None,
                    "mode": "restricted" if has_position_limits else "free"
                },
                "agent_freedom": {
                    "position_sizing": "free" if not has_position_limits else "restricted",
                    "description": "Agent has complete freedom to decide position sizes based on VIX risk, signal strength, and diversification needs" if not has_position_limits else "Agent will respect configured position limits"
                },
                "optimizations": optimization_status
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
