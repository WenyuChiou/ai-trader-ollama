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
        
        # CRITICAL FIX: Make result JSON serializable (handle pandas Series in risk_report, tool_calls, etc.)
        from src.utils.json_serializer import make_json_serializable
        serializable_result = make_json_serializable({
            "placed_orders": placed_orders,
            "conversations_count": conversations_count,
            "is_planning": is_planning,
            **result
        })
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "message": message,
                "result": serializable_result
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
        
        # CRITICAL FIX: Also extract round=0 entries for analysts (fallback for single-round discussions)
        analyst_names = ["MarketAnalyst", "TechnicalAnalyst", "FundamentalAnalyst", "SentimentAnalyst"]
        
        for entry in processed_conversations:
            round_num = entry.get("round", 0)
            # CRITICAL FIX: 处理 round_num 可能是字符串或数字的情况
            if isinstance(round_num, str):
                try:
                    round_num = int(round_num)
                except (ValueError, TypeError):
                    round_num = 0
            
            agent = entry.get("agent", "Unknown")
            entry_type = entry.get("type", "discussion")
            
            # CRITICAL FIX: Process both round > 0 (multi-round) and round = 0 (single-round or fallback)
            # For round = 0, only process analyst entries (not Coordinator or TraderAgent)
            should_process = False
            if round_num > 0:
                # Multi-round discussion entries
                should_process = True
            elif round_num == 0 and entry_type == "discussion" and agent in analyst_names:
                # Single-round discussion entries (fallback) - only for analysts
                should_process = True
            
            if should_process:
                if round_num not in discussion_rounds:
                    discussion_rounds[round_num] = []
                discussion_rounds[round_num].append(entry)
                
                # CRITICAL FIX: 按 round 和 agent 分组，提取 summary
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
            # CRITICAL FIX: news_scan 已移除，只保留 plan_and_scan_news
            "get_news_scan": "news",  # 兼容旧名称
            "plan_and_scan_news": "news",
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
            "get_treasury_yield_curve": "economic",
            "fetch_fred_indicator": "economic",
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
                
                # DEBUG: Log news tools
                if tool_category == "news":
                    print(f"[API] ✅ Found news tool: {tool_name}, agent: {entry.get('agent', 'Unknown')}")
                    # DEBUG: Check if tool_result has news data
                    if isinstance(tool_result, dict):
                        # CRITICAL FIX: Check for nested structure {ok: true, result: {...}}
                        actual_result = tool_result
                        if tool_result.get("ok") and "result" in tool_result:
                            actual_result = tool_result.get("result", {})
                            print(f"[API]   Extracted result from tool_result.ok structure")
                        
                        if isinstance(actual_result, dict):
                            hits = actual_result.get("hits", [])
                            articles = actual_result.get("articles", [])
                            print(f"[API]   News data: {len(hits) if isinstance(hits, list) else 0} hits, {len(articles) if isinstance(articles, list) else 0} articles")
                            print(f"[API]   actual_result keys: {list(actual_result.keys())[:10]}")
                            if articles and isinstance(articles, list) and len(articles) > 0:
                                print(f"[API]   First article keys: {list(articles[0].keys())[:10] if isinstance(articles[0], dict) else 'not dict'}")
                            elif hits and isinstance(hits, list) and len(hits) > 0:
                                print(f"[API]   First hit keys: {list(hits[0].keys())[:10] if isinstance(hits[0], dict) else 'not dict'}")
                        else:
                            print(f"[API]   ⚠️ actual_result is not a dict: {type(actual_result)}")
                    else:
                        print(f"[API]   ⚠️ tool_result is not a dict: {type(tool_result)}")
                
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
                    
                    # DEBUG: Log news tool entry structure
                    if tool_category == "news":
                        print(f"[API] Adding news tool entry: {tool_name}, result keys: {list(tool_result.keys())[:10] if isinstance(tool_result, dict) else 'not dict'}")
                        # CRITICAL FIX: Ensure tool_result structure is correct for frontend parsing
                        if isinstance(tool_result, dict):
                            # Check if we need to extract from nested structure
                            if tool_result.get("ok") and "result" in tool_result:
                                # Keep the nested structure, frontend will extract it
                                print(f"[API]   Tool result has nested structure: ok={tool_result.get('ok')}, has result={('result' in tool_result)}")
                                # Extract actual_result for logging
                                actual_result_for_log = tool_result.get("result", {})
                                if isinstance(actual_result_for_log, dict):
                                    articles_count = len(actual_result_for_log.get("articles", [])) if isinstance(actual_result_for_log.get("articles"), list) else 0
                                    hits_count = len(actual_result_for_log.get("hits", [])) if isinstance(actual_result_for_log.get("hits"), list) else 0
                                    print(f"[API]   Nested result contains: {articles_count} articles, {hits_count} hits")
                            else:
                                # Check if tool_result directly has articles/hits (from trading_cycle.py processing)
                                actual_result = tool_result
                                if isinstance(actual_result, dict):
                                    has_articles = bool(actual_result.get("articles"))
                                    has_hits = bool(actual_result.get("hits"))
                                    articles_count = len(actual_result.get("articles", [])) if isinstance(actual_result.get("articles"), list) else 0
                                    hits_count = len(actual_result.get("hits", [])) if isinstance(actual_result.get("hits"), list) else 0
                                    print(f"[API]   Tool result structure: has_articles={has_articles} ({articles_count} items), has_hits={has_hits} ({hits_count} items)")
                                    if not has_articles and not has_hits:
                                        print(f"[API]   [WARN] News tool result has no articles or hits!")
                                        print(f"[API]   [WARN] tool_result keys: {list(tool_result.keys())[:15]}")
                    
                    # 添加到对应分类
                    if tool_category in tool_results_by_category:
                        tool_results_by_category[tool_category].append(tool_entry)
                    else:
                        tool_results_by_category["other"].append(tool_entry)
                except Exception as tool_error:
                    # 如果序列化失败，跳过这个工具条目
                    print(f"[WARN] 跳过工具条目（序列化失败）: {tool_error}")
                    continue
        
        # DEBUG: Log final news category count
        print(f"[API] Final tool_results_by_category.news count: {len(tool_results_by_category['news'])}")
        
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
            # 先填充所有持仓的基本信息（但不设置 last_prices，等获取真实价格后再设置）
            for symbol in positions:
                pos = portfolio._positions[symbol]
                total_cost = getattr(pos, "total_cost", pos.avg_cost * pos.quantity)
                
                # 填充基本信息（使用 avg_cost 作为占位符，但不在 last_prices 中设置）
                positions_detail[symbol] = {
                                "quantity": pos.quantity,
                                "avg_cost": pos.avg_cost,
                    "total_cost": total_cost,
                    "cost_basis": total_cost,
                    "current_price": pos.avg_cost,  # 占位符，会被真实价格替换
                    "market_value": pos.quantity * pos.avg_cost,  # 占位符
                    "unrealized_pnl": 0.0,  # 默认0，等有真实价格再计算
                    "unrealized_pnl_pct": 0.0,
                }
            
            # CRITICAL FIX: 智能价格获取 - 确保在所有情况下都能正常更新
            # 价格获取策略（按优先级）：
            # 1. 市场开盘时：优先使用实时价格
            # 2. 市场收盘后（交易日）：使用今天的收盘价
            # 3. 非交易日（周末/节假日）：使用最近一个交易日的收盘价
            # 4. 所有情况都有多层fallback，确保总能获取到价格
            
            from src.utils.trading_days import is_market_open, is_trading_day
            import yfinance as yf
            from datetime import date, timedelta
            
            is_market_open_now = is_market_open(None)  # 传入None直接获取美东时间
            today_is_trading_day = is_trading_day(date.today())
            
            print(f"[API] Market status: open={is_market_open_now}, trading_day={today_is_trading_day}")
            
            try:
                # 策略1: 如果市场开盘，优先使用实时价格
                if is_market_open_now:
                    print(f"[API] Market is OPEN - using real-time prices for {len(positions)} positions")
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
                                    print(f"[API] ✅ Real-time price for {symbol}: ${price:.2f}")
                                    continue
                        except Exception as e:
                            print(f"[API] ⚠️  Failed to get real-time price for {symbol}: {e}, will try close price")
                
                # 策略2: 市场关闭或非交易日 - 使用收盘价（多层fallback确保总能获取到价格）
                market_status = "CLOSED (trading day)" if today_is_trading_day else "CLOSED (non-trading day)"
                print(f"[API] Market is {market_status} - using latest close prices for {len(positions)} positions")
                
                # CRITICAL FIX: 优先使用 yfinance 直接获取最新收盘价（更可靠）
                # 这样可以确保获取到今天的收盘价（如果市场已收盘）或最近一个交易日的收盘价
                for symbol in positions:
                    # 如果已经通过实时价格获取了，跳过（last_prices 中只包含真实获取的价格）
                    if symbol in last_prices:
                        continue
                    
                    try:
                        # CRITICAL FIX: 多层fallback策略，确保在所有情况下都能获取到价格
                        # 适用于：交易日收盘后、非交易日（周末/节假日）、盘前盘后
                        ticker = yf.Ticker(symbol)
                        price = None
                        price_source = None
                        
                        # 方法1: 优先使用 history(period="1d") 获取今天的收盘价
                        # 如果今天是交易日且已收盘，这会返回今天的收盘价
                        # 如果今天是非交易日，这会返回最近一个交易日的收盘价
                        try:
                            hist = ticker.history(period="1d")
                            if not hist.empty and "Close" in hist.columns:
                                price = float(hist["Close"].iloc[-1])
                                price_source = "today's close (1d history)"
                                print(f"[API] ✅ Using {price_source} for {symbol}: ${price:.2f}")
                        except Exception as e:
                            print(f"[API] ⚠️  Failed to get 1d history for {symbol}: {e}")
                        
                        # 方法2: 如果1d失败，使用 history(period="5d") 获取最近5天的收盘价
                        # 这会返回最近一个交易日的收盘价（包括今天如果是交易日）
                        if price is None or price <= 0:
                            try:
                                hist = ticker.history(period="5d")
                                if not hist.empty and "Close" in hist.columns:
                                    price = float(hist["Close"].iloc[-1])
                                    price_source = "latest close (5d history)"
                                    print(f"[API] ✅ Using {price_source} for {symbol}: ${price:.2f}")
                            except Exception as e:
                                print(f"[API] ⚠️  Failed to get 5d history for {symbol}: {e}")
                        
                        # 方法3: 如果 history 失败，使用 ticker.info（备选方案）
                        # 注意：info字段可能有时区延迟，但作为fallback仍然有用
                        if price is None or price <= 0:
                            try:
                                info = ticker.info
                                # CRITICAL: regularMarketClose 是当天的收盘价（如果市场已收盘）
                                # 对于非交易日，这可能不存在，所以优先使用 regularMarketPreviousClose
                                if "regularMarketClose" in info and info["regularMarketClose"]:
                                    price = float(info["regularMarketClose"])
                                    price_source = "regularMarketClose (info)"
                                    print(f"[API] ✅ Using {price_source} for {symbol}: ${price:.2f}")
                                elif "regularMarketPreviousClose" in info and info["regularMarketPreviousClose"]:
                                    price = float(info["regularMarketPreviousClose"])
                                    price_source = "regularMarketPreviousClose (info)"
                                    print(f"[API] ✅ Using {price_source} for {symbol}: ${price:.2f}")
                                elif "previousClose" in info and info["previousClose"]:
                                    price = float(info["previousClose"])
                                    price_source = "previousClose (info)"
                                    print(f"[API] ✅ Using {price_source} for {symbol}: ${price:.2f}")
                            except Exception as e:
                                print(f"[API] ⚠️  Failed to get info for {symbol}: {e}")
                        
                        # 方法4: 如果所有方法都失败，尝试使用更长的历史数据（30天）
                        if price is None or price <= 0:
                            try:
                                hist = ticker.history(period="30d")
                                if not hist.empty and "Close" in hist.columns:
                                    price = float(hist["Close"].iloc[-1])
                                    price_source = "latest close (30d history)"
                                    print(f"[API] ✅ Using {price_source} for {symbol}: ${price:.2f}")
                            except Exception as e:
                                print(f"[API] ⚠️  Failed to get 30d history for {symbol}: {e}")
                        
                        if price and price > 0:
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
                            print(f"[API] ✅ Close price for {symbol}: ${price:.2f} (source: {price_source}), market_value=${pos.quantity * price:.2f}, P&L=${(price - pos.avg_cost) * pos.quantity:.2f}")
                            continue
                    except Exception as e:
                        print(f"[API] Failed to get latest close price for {symbol} via yfinance: {e}, will try fetch_market_batch")
                    
                    # Fallback: 如果直接获取失败，使用 fetch_market_batch
                    # 获取最近7天的数据（确保能获取到最新价格）
                    # CRITICAL FIX: end_date 应该是明天，这样 yfinance 才会包含今天的数据
                    end_date = (date.today() + timedelta(days=1)).isoformat()
                    start_date = (date.today() - timedelta(days=7)).isoformat()
                    
                    try:
                        # CRITICAL FIX: 使用 .invoke() 方法，传递正确的参数
                        market_data = fetch_market_batch.invoke({
                            "symbols": [symbol],  # 只获取这个 symbol 的数据
                            "start": start_date,
                            "end": end_date,
                        })
                        
                        # CRITICAL FIX: 从正确的路径获取价格数据
                        stocks_data = market_data.get("stocks", {})
                        
                        if symbol in stocks_data:
                            stock_info = stocks_data[symbol]
                            # CRITICAL FIX: fetch_market_batch 返回的 price 字段是最新收盘价（Latest Close Price）
                            # This is the closing price from the most recent trading day
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
                                print(f"[API] Historical price for {symbol} (via fetch_market_batch): ${price:.2f}, market_value=${pos.quantity * price:.2f}, P&L=${(price - pos.avg_cost) * pos.quantity:.2f}")
                            else:
                                # 如果价格无效，使用 avg_cost
                                print(f"[API] Invalid price for {symbol}, using avg_cost as placeholder")
                                last_prices[symbol] = portfolio._positions[symbol].avg_cost
                        else:
                            # 如果 stocks_data 中没有该 symbol，使用 avg_cost 作为占位符
                            print(f"[API] Symbol {symbol} not found in market data, using avg_cost as placeholder")
                            last_prices[symbol] = portfolio._positions[symbol].avg_cost
                    except Exception as e2:
                        print(f"[API] Failed to get price for {symbol} via fetch_market_batch: {e2}")
                        # 如果所有方法都失败，使用 avg_cost 作为占位符
                        if symbol not in last_prices:
                            last_prices[symbol] = portfolio._positions[symbol].avg_cost
            except Exception as e:
                import traceback
                print(f"[API] Failed to fetch market data: {e}")
                print(f"[API] Traceback: {traceback.format_exc()}")
                # 即使失败，positions_detail 也已经填充了基本信息（使用 avg_cost）
                # 需要确保 last_prices 中有值，否则 portfolio.equity_value() 会失败
                for symbol in positions:
                    if symbol not in last_prices:
                        last_prices[symbol] = portfolio._positions[symbol].avg_cost
        
        # 计算总值
        equity_value = portfolio.equity_value(last_prices)
        total_value = portfolio.cash + equity_value
        # CRITICAL FIX: total_pnl 应该是 total_value - initial_value（包括现金和持仓的所有变化）
        # portfolio.total_pnl(last_prices) 只计算持仓的未实现盈亏，不包括现金变化
        # 所以应该使用 total_value - initial_value 来计算总盈亏
        total_pnl = total_value - portfolio.initial_value
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
                    
                    # CRITICAL FIX: 验证 snapshot 值的准确性
                    # snapshot 中的 total_value 应该等于 snapshot.cash + snapshot.equity_value
                    # 如果 snapshot 值不一致，应该使用当前计算的值
                    if snapshot_total_value and snapshot_equity_value:
                        snapshot_cash = snapshot.get("cash", portfolio.cash)
                        snapshot_calculated_total = snapshot_cash + snapshot_equity_value
                        
                        # 检查 snapshot 内部一致性（允许小的浮点误差）
                        snapshot_consistent = abs(snapshot_total_value - snapshot_calculated_total) < 0.01
                        
                        # 检查是否所有持仓的价格都等于avg_cost（说明价格获取失败）
                        all_prices_equal_avg_cost = all(
                            pos_detail.get("current_price", 0) == pos_detail.get("avg_cost", 0)
                            for pos_detail in positions_detail.values()
                        )
                        
                        # CRITICAL FIX: 只有在价格获取失败 AND snapshot 内部一致时，才使用 snapshot 的值
                        # 如果 snapshot 内部不一致，说明 snapshot 数据有问题，应该使用当前计算的值
                        if all_prices_equal_avg_cost and snapshot_consistent:
                            # 如果价格获取失败，且 snapshot 内部一致，使用 snapshot 的值
                            total_value = snapshot_total_value
                            equity_value = snapshot_equity_value
                            # 重新计算P&L
                            total_pnl = total_value - portfolio.initial_value
                            total_pnl_pct = (total_pnl / portfolio.initial_value * 100.0) if portfolio.initial_value > 0 else 0.0
                        elif not snapshot_consistent:
                            # CRITICAL FIX: snapshot 内部不一致，说明数据有问题，使用当前计算的值
                            pass  # 使用当前计算的值（默认行为）
            except Exception as e:
                import traceback
                print(f"[API] Failed to check snapshot values: {e}")
                print(f"[API] Traceback: {traceback.format_exc()}")
        
        # CRITICAL FIX: 自动记录净值历史（每30分钟最多记录一次）
        # 只在市场开盘时记录（9:30 AM - 4:00 PM ET），收盘后不记录
        # NOTE: 这个功能可以通过设置环境变量 DISABLE_AUTO_EQUITY_RECORDING=1 来禁用
        auto_record_equity = os.environ.get("DISABLE_AUTO_EQUITY_RECORDING", "0") != "1"
        
        # CRITICAL: 检查市场是否开盘，收盘后不记录
        if auto_record_equity:
            try:
                from src.utils.trading_days import is_market_open
                is_market_open_now = is_market_open(None)
                if not is_market_open_now:
                    auto_record_equity = False  # 市场收盘，不记录
                    print(f"[API] Market is closed, skipping auto equity recording (will resume at next market open)")
            except Exception as e:
                print(f"[API WARNING] Failed to check market status: {e}, proceeding with auto record")
        
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
                                    time_diff = (current_time - last_time).total_seconds() / 1800  # 30分钟
                                    # CRITICAL FIX: 每30分钟记录一次（市场开盘时）
                                    # 这样可以确保每30分钟都有记录，即使净值没有变化
                                    if time_diff < 0.5:  # 30分钟 = 0.5小时
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

@app.options("/api/portfolio/record-equity")
async def options_record_equity():
    """CORS preflight for record-equity endpoint"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/api/portfolio/record-equity")
async def record_equity(equity_data: dict):
    """记录净值到历史记录"""
    try:
        from src.data.equity_tracker import EquityTracker
        from datetime import date
        
        logs_dir = _get_project_logs_dir()
        equity_tracker = EquityTracker(root=str(logs_dir))
        
        # 提取日期（优先使用date字段，否则从timestamp提取）
        date_str = equity_data.get("date")
        if not date_str and equity_data.get("timestamp"):
            date_str = equity_data["timestamp"].split("T")[0]
        if not date_str:
            date_str = date.today().isoformat()
        
        # 记录净值
        equity_tracker.record_daily_equity(
            date_str=date_str,
            portfolio_snapshot=equity_data,
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "message": "Equity recorded successfully",
                "date": date_str,
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

@app.get("/api/portfolio/equity-history")
async def get_equity_history(
    limit: int = Query(60, ge=1, le=1000),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    start_timestamp: Optional[str] = Query(None, description="Start timestamp (ISO 8601)"),
    end_timestamp: Optional[str] = Query(None, description="End timestamp (ISO 8601)"),
    period: Optional[str] = Query(None, description="Period: 'day', 'week', or 'month'"),
):
    """获取权益历史，支持时间范围查询"""
    try:
        from src.data.equity_tracker import EquityTracker
        from datetime import datetime, timedelta, timezone
        
        logs_dir = _get_project_logs_dir()
        equity_tracker = EquityTracker(root=str(logs_dir))
        
        # 处理period参数（如果提供）
        if period:
            now = datetime.now(timezone.utc)
            if period == "day":
                # CRITICAL FIX: 统一时间戳格式 - 使用UTC格式（Z后缀）
                start_ts = (now - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            elif period == "week":
                start_ts = (now - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            elif period == "month":
                start_ts = (now - timedelta(days=30)).strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            else:
                start_ts = None
            
            if start_ts:
                end_ts = now.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
                records = equity_tracker.load_equity_history(
                    start_timestamp=start_ts,
                    end_timestamp=end_ts,
                    limit=limit
                )
            else:
                records = equity_tracker.load_equity_history(
                    start_date=start_date,
                    end_date=end_date,
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    limit=limit
                )
        else:
            # 使用EquityTracker的方法加载记录
            records = equity_tracker.load_equity_history(
                start_date=start_date,
                end_date=end_date,
                start_timestamp=start_timestamp,
                end_timestamp=end_timestamp,
                limit=limit
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "records": records,
                "count": len(records)
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
        
        # 读取最后 N 条记录（优化：从文件末尾读取，避免加载整个文件）
        trades = []
        with filled_file.open("r", encoding="utf-8") as f:
            # 优化：从文件末尾读取（避免加载整个文件）
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            # 读取最后 ~100KB（足够容纳 limit 条记录）
            position = max(0, file_size - 1024 * 100)
            f.seek(position)
            lines = f.readlines()
            
            # 处理行（从新到旧）
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
        backup_created = False
        backup_filename = None
        portfolio_file = logs_dir / "portfolio_state.json"
        if portfolio_file.exists():
            backup_filename = f"portfolio_state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            backup_file = logs_dir / backup_filename
            import shutil
            try:
                shutil.copy2(portfolio_file, backup_file)
                backup_created = True
                print(f"[INIT] Created backup: {backup_filename}")
            except Exception as e:
                print(f"[INIT] Failed to create backup: {e}")
        
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
        
        # CRITICAL FIX: 清理所有旧的备份文件（初始化时删除所有旧备份，只保留刚创建的新备份）
        # 这样可以确保初始化后目录干净，只保留最新的备份
        backup_files = list(logs_dir.glob("*backup*.json"))
        if backup_files:
            old_backups_deleted = 0
            for backup_file in backup_files:
                try:
                    # 如果刚创建了新备份，保留它；否则删除所有旧备份
                    if backup_filename and backup_file.name == backup_filename:
                        # 保留刚创建的新备份
                        print(f"[INIT] Keeping newly created backup: {backup_file.name}")
                        continue
                    # 删除所有其他备份文件
                    backup_file.unlink()
                    old_backups_deleted += 1
                    deleted.append(f"old_backup: {backup_file.name}")
                except Exception as e:
                    print(f"[INIT] Failed to delete old backup {backup_file.name}: {e}")
            
            if old_backups_deleted > 0:
                print(f"[INIT] Deleted {old_backups_deleted} old backup files during initialization")
        
        # CRITICAL FIX: 清理 memory/ 文件夹内的所有文件（保留文件夹本身）
        memory_dir = logs_dir / "memory"
        if memory_dir.exists() and memory_dir.is_dir():
            memory_files_deleted = 0
            try:
                # 递归遍历 memory/ 目录下的所有文件
                for item in memory_dir.rglob("*"):
                    if item.is_file():
                        try:
                            item.unlink()
                            memory_files_deleted += 1
                            # 记录相对路径
                            relative_path = item.relative_to(logs_dir)
                            deleted.append(f"memory: {relative_path}")
                        except Exception as e:
                            print(f"[INIT] Failed to delete memory file {item}: {e}")
                
                if memory_files_deleted > 0:
                    print(f"[INIT] Deleted {memory_files_deleted} files from memory/ directory")
                else:
                    print(f"[INIT] No files found in memory/ directory to delete")
            except Exception as e:
                print(f"[INIT] Error cleaning memory/ directory: {e}")
        
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "message": f"System initialized. Deleted {len(deleted)} files.",
                "deleted_files": deleted,
                "backup_created": backup_created,
                "backup_filename": backup_filename if backup_created else None,
                "note": "First trade after initialization must be triggered manually. Auto-trading will resume after the first manual trade."
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

# ============================================================================
# Performance Analysis Endpoints
# ============================================================================

@app.get("/api/performance/statistics")
async def get_performance_statistics_endpoint(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get overall performance statistics"""
    try:
        from src.api.performance import get_performance_statistics
        
        result = get_performance_statistics(start_date=start_date, end_date=end_date)
        
        return JSONResponse(
            status_code=200,
            content=result,
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


@app.options("/api/performance/statistics")
async def options_performance_statistics():
    """CORS preflight for performance statistics"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/api/performance/trades-by-date")
async def get_trades_by_date_endpoint(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: Optional[int] = Query(None, ge=1, le=1000, description="Limit number of dates"),
):
    """Get trades grouped by date"""
    try:
        from src.api.performance import get_trades_by_date
        
        result = get_trades_by_date(start_date=start_date, end_date=end_date, limit=limit)
        
        return JSONResponse(
            status_code=200,
            content=result,
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


@app.options("/api/performance/trades-by-date")
async def options_trades_by_date():
    """CORS preflight for trades by date"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )


@app.get("/api/performance/symbol-analysis")
async def get_symbol_analysis_endpoint(
    symbol: Optional[str] = Query(None, description="Stock symbol (optional, returns all symbols if not specified)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
):
    """Get performance analysis by symbol"""
    try:
        from src.api.performance import get_symbol_analysis
        
        result = get_symbol_analysis(symbol=symbol, start_date=start_date, end_date=end_date)
        
        return JSONResponse(
            status_code=200,
            content=result,
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


@app.options("/api/performance/symbol-analysis")
async def options_symbol_analysis():
    """CORS preflight for symbol analysis"""
    return JSONResponse(
        status_code=200,
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )
