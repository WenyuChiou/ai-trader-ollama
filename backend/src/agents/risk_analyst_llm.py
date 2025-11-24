from __future__ import annotations
from typing import Dict, Any, Optional
from pathlib import Path
import json
from ..utils.json_serializer import make_json_serializable


def run_risk_analyst_llm(
    market_json: Dict[str, Any],
    current_positions: Optional[Dict[str, Any]] = None,
    portfolio_value: Optional[float] = None,
    discussion_risk_signals: Optional[Dict[str, Any]] = None,
    previous_discussion: Optional[str] = None,
    use_tools: bool = True,
) -> Dict[str, Any]:
    """
    LLM-powered Risk Analyst: 使用AI评估市场风险和仓位风险
    
    输入:
    - market_json: 市场数据（包含 stocks）
    - current_positions: 当前持仓 {symbol: {quantity, avg_cost, ...}}
    - portfolio_value: 当前组合净值
    - discussion_risk_signals: 来自 Analyst Discussion 的风险信号
    - previous_discussion: 之前的讨论内容
    - use_tools: 是否允许使用工具
    
    输出:
    - overall_risk_level: 整体风险等级
    - risk_score: 风险评分
    - market_risks: 市场风险列表
    - position_risks: 仓位风险列表
    - position_control_report: 仓位控管报告
    - recommendations: 风险缓解建议
    """
    # CRITICAL FIX: Add entry log to confirm function is called
    import sys
    print(f"[RISK ANALYST] ===== ENTRY: run_risk_analyst_llm called =====", file=sys.stderr)
    print(f"[RISK ANALYST] ===== ENTRY: run_risk_analyst_llm called =====")
    sys.stderr.flush()
    sys.stdout.flush()
    from ..agents.factory import AgentFactory
    from ..agents.base import BaseAgent
    from ..agents.toolbox import ToolBox
    
    # 初始化
    ROOT = Path(__file__).resolve().parents[2]
    fac = AgentFactory(ROOT / "config" / "agents.yaml")
    agent: BaseAgent = fac.create("risk_analyst")
    toolbox = ToolBox()
    
    # 准备prompt变量
    tools_str = ", ".join(toolbox.list()) if use_tools else "No tools available"
    
    # CRITICAL: 格式化当前持仓信息，包含损益和占比（用于prompt）
    # 即使没有持仓，也要传递组合信息（现金、总净值等）
    if current_positions and len(current_positions) > 0:
        positions_formatted = []
        total_position_value = 0.0
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                quantity = pos_info.get("quantity", 0)
                avg_cost = pos_info.get("avg_cost", 0.0)
                current_price = pos_info.get("current_price", avg_cost)
                market_value = pos_info.get("market_value", quantity * current_price)
                unrealized_pnl = pos_info.get("unrealized_pnl", (current_price - avg_cost) * quantity)
                unrealized_pnl_pct = pos_info.get("unrealized_pnl_pct", ((current_price - avg_cost) / avg_cost * 100.0) if avg_cost > 0 else 0.0)
                position_pct = pos_info.get("position_pct", (market_value / portfolio_value * 100.0) if portfolio_value and portfolio_value > 0 else 0.0)
                total_position_value += market_value
                
                positions_formatted.append({
                    "symbol": symbol,
                    "quantity": quantity,
                    "avg_cost": avg_cost,
                    "current_price": current_price,
                    "market_value": market_value,
                    "unrealized_pnl": unrealized_pnl,
                    "unrealized_pnl_pct": unrealized_pnl_pct,
                    "position_pct": position_pct,
                })
        
        # 添加组合摘要
        if portfolio_value and portfolio_value > 0:
            cash = portfolio_value - total_position_value
            cash_pct = (cash / portfolio_value * 100.0) if portfolio_value > 0 else 0.0
            positions_str = f"""**CURRENT PORTFOLIO POSITIONS (with P&L and Position %):**

{json.dumps(positions_formatted, indent=2)}

**Portfolio Summary:**
- Total Portfolio Value: ${portfolio_value:,.2f}
- Cash: ${cash:,.2f} ({cash_pct:.1f}%)
- Positions Value: ${total_position_value:,.2f} ({100.0 - cash_pct:.1f}%)
- Number of Positions: {len(positions_formatted)}

**⚠️ CRITICAL: You MUST analyze each position's P&L (unrealized_pnl, unrealized_pnl_pct) and position percentage (position_pct) when making risk assessments. Consider:**
- Positions with large unrealized losses may need risk reduction
- Positions exceeding position_pct limits (typically >15%) indicate concentration risk
- High position_pct combined with negative unrealized_pnl_pct suggests high risk exposure
"""
        else:
            positions_str = json.dumps(positions_formatted, indent=2)
    else:
        # CRITICAL: 即使没有持仓，也要传递组合信息
        # 这样 Risk Analyst 可以分析"没有持仓"的状态，评估是否应该开始建仓
        if portfolio_value and portfolio_value > 0:
            # 假设全部是现金（因为没有持仓）
            cash = portfolio_value
            cash_pct = 100.0
            positions_str = f"""**CURRENT PORTFOLIO STATUS:**

**No positions currently held.**

**Portfolio Summary:**
- Total Portfolio Value: ${portfolio_value:,.2f}
- Cash: ${cash:,.2f} ({cash_pct:.1f}%)
- Positions Value: $0.00 (0.0%)
- Number of Positions: 0

**⚠️ CRITICAL: Even with no positions, you MUST analyze the portfolio status:**
- Portfolio is 100% cash, indicating no market exposure
- This is a low-risk state but also means no potential returns
- Consider market conditions and risk tolerance when recommending whether to start building positions
- Assess if current market conditions are suitable for initial position entry
- Evaluate if cash should be deployed or kept in reserve based on market risk levels
"""
        else:
            positions_str = "No positions and no portfolio value information available"
    
    # 格式化市场数据（简化）
    # CRITICAL FIX: Extract VIX risk_score from market_json.vix.risk_score (forced by trading_cycle)
    vix_data = market_json.get("vix", {})
    vix_risk_score_from_market = None
    if isinstance(vix_data, dict):
        vix_risk_score_from_market = vix_data.get("risk_score")
        if vix_risk_score_from_market is not None:
            print(f"[RISK ANALYST] ✅ Found VIX risk_score in market_json: {vix_risk_score_from_market:.1f}")
        else:
            print(f"[RISK ANALYST] ⚠️  WARNING: market_json.vix exists but risk_score is None. vix_data keys: {list(vix_data.keys())}")
    else:
        print(f"[RISK ANALYST] ⚠️  WARNING: market_json.vix is not a dict. Type: {type(vix_data)}, Value: {vix_data}")
        print(f"[RISK ANALYST] DEBUG: market_json keys: {list(market_json.keys())}")
    
    market_summary = {
        "stocks_count": len(market_json.get("stocks", {})),
        "vix": vix_data,
        "vix_risk_score": vix_risk_score_from_market,  # CRITICAL: Explicitly include VIX risk score
        "sample_stocks": list(market_json.get("stocks", {}).keys())[:5],
    }
    
    prompt_vars = {
        "market_view": json.dumps(market_summary, indent=2),
        "current_positions": positions_str,
        "portfolio_value": f"{portfolio_value:,.2f}" if portfolio_value else "N/A",
        "discussion_risk_signals": json.dumps(discussion_risk_signals, indent=2) if discussion_risk_signals else "No signals",
        "previous_discussion": previous_discussion[:500] if previous_discussion else "No previous discussion",
        "tools": tools_str,
        "tools_context": "",
    }
    
    # CRITICAL FIX: Track tool calls for RiskAnalyst
    tool_calls_used = []
    tool_results_data = []
    
    # CRITICAL FIX: Force call VIX API before LLM analysis
    # 强制在 LLM 分析之前调用 VIX API 获取最新数据
    # IMPORTANT: Always call VIX API regardless of use_tools, because VIX risk_score is critical
    vix_api_data = None
    vix_risk_score_from_api = None
    print(f"[RISK ANALYST] DEBUG: use_tools={use_tools}, but will force call VIX API anyway (VIX risk_score is critical)")
    # CRITICAL FIX: Always call VIX API, not just when use_tools=True
    # VIX risk_score is critical for risk assessment, so we always need it
    try:
        print("[RISK ANALYST] 🔧 FORCING: Calling vix_term API to get latest VIX data...")
        vix_api_response = toolbox.invoke("vix_term")
        # CRITICAL FIX: toolbox.invoke returns {"ok": True, "result": {...}} structure
        # Extract the actual result data
        if vix_api_response and isinstance(vix_api_response, dict):
            if "result" in vix_api_response:
                vix_api_data = vix_api_response["result"]
            else:
                vix_api_data = vix_api_response
            
            if vix_api_data and isinstance(vix_api_data, dict):
                vix_risk_score_from_api = vix_api_data.get("vix_risk_score")
                vix_level = vix_api_data.get("vix")
                print(f"[RISK ANALYST] ✅ Got VIX data from API: VIX={vix_level}, risk_score={vix_risk_score_from_api}")
                # Add VIX data to tool_results_data for reference (even if use_tools=False)
                tool_results_data.append({
                    "tool": "vix_term",
                    "result": vix_api_data
                })
                tool_calls_used.append("vix_term")
            else:
                print(f"[RISK ANALYST] ⚠️  WARNING: vix_term API returned invalid result data: {vix_api_data}")
                print(f"[RISK ANALYST] DEBUG: vix_api_data type={type(vix_api_data)}, value={vix_api_data}")
                # CRITICAL FIX: Even if data is invalid, add to tool_results_data to track the failure
                tool_results_data.append({
                    "tool": "vix_term",
                    "result": {"error": "Invalid data", "raw": str(vix_api_data)}
                })
        else:
            print(f"[RISK ANALYST] ⚠️  WARNING: vix_term API returned invalid response: {vix_api_response}")
            print(f"[RISK ANALYST] DEBUG: vix_api_response type={type(vix_api_response)}, value={vix_api_response}")
            vix_api_data = None
            # CRITICAL FIX: Even if response is invalid, add to tool_results_data to track the failure
            tool_results_data.append({
                "tool": "vix_term",
                "result": {"error": "Invalid response", "raw": str(vix_api_response)}
            })
    except Exception as e:
        print(f"[RISK ANALYST] ❌ ERROR: Failed to call vix_term API: {e}")
        import traceback
        traceback.print_exc()
        # CRITICAL FIX: Even if exception occurs, add to tool_results_data to track the failure
        tool_results_data.append({
            "tool": "vix_term",
            "result": {"error": str(e), "exception": True}
        })
    
    try:
        # 调用LLM
        response = agent.run(prompt_vars, expect_json=True)
        
        # CRITICAL FIX: Extract tool calls from response if available
        if isinstance(response, dict):
            tool_calls_list = response.get("tool_calls", [])
            if tool_calls_list:
                print(f"[RISK ANALYST] Found {len(tool_calls_list)} tool calls in response")
                # Execute tools if use_tools is True
                if use_tools:
                    # CRITICAL FIX: Filter out news tools (Risk Analyst should not use news tools)
                    # News tools are restricted to Sentiment Analyst only
                    news_tools = ["news_scan", "plan_and_scan_news", "web_search", "fetch_url"]
                    filtered_tool_calls = []
                    for tool_call in tool_calls_list:
                        tool_name = tool_call.get("name", "")
                        if tool_name in news_tools:
                            print(f"[RISK ANALYST] Removing news tool '{tool_name}' (news analysis is handled by Sentiment Analyst)")
                        else:
                            filtered_tool_calls.append(tool_call)
                    tool_calls_list = filtered_tool_calls
                    
                    for tool_call in tool_calls_list:
                        tool_name = tool_call.get("name", "")
                        tool_args = tool_call.get("args", {})
                        
                        if tool_name:
                            try:
                                tool_result = toolbox.invoke(tool_name, **tool_args)
                                tool_calls_used.append(tool_name)
                                tool_results_data.append({
                                    "tool": tool_name,
                                    "result": tool_result
                                })
                                print(f"[RISK ANALYST] Executed tool: {tool_name}")
                            except Exception as e:
                                print(f"[RISK ANALYST] Failed to execute tool {tool_name}: {e}")
        
        # 尝试解析JSON响应
        try:
            # 如果已经是dict，直接使用
            if isinstance(response, dict):
                risk_report = response
            else:
                # 否则是string，需要解析
                # 提取JSON部分（如果有markdown代码块）
                if "```json" in response:
                    json_start = response.find("```json") + 7
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                elif "```" in response:
                    json_start = response.find("```") + 3
                    json_end = response.find("```", json_start)
                    json_str = response[json_start:json_end].strip()
                elif "{" in response and "}" in response:
                    # 找到第一个{和最后一个}
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    json_str = response[json_start:json_end]
                else:
                    json_str = response
                
                risk_report = json.loads(json_str)
            
            # 确保必要字段存在
            if "overall_risk_level" not in risk_report:
                risk_report["overall_risk_level"] = "medium"
            if "risk_score" not in risk_report:
                risk_report["risk_score"] = 5.0
            
            # CRITICAL FIX: Force VIX risk_score into overall risk_score
            # Priority: 1) API data (most reliable), 2) market_json data, 3) discussion_risk_signals
            vix_risk_to_use = None
            vix_source = None
            
            # Priority 1: Use VIX data from API (most reliable, always fresh)
            if vix_risk_score_from_api is not None:
                vix_risk_to_use = vix_risk_score_from_api
                vix_source = "API (vix_term)"
            else:
                # Priority 2: Try market_json
                if isinstance(market_json, dict):
                    vix_data = market_json.get("vix", {})
                    if isinstance(vix_data, dict):
                        vix_risk_from_market = vix_data.get("risk_score")
                        if vix_risk_from_market is not None:
                            vix_risk_to_use = vix_risk_from_market
                            vix_source = "market_json"
                
                # Priority 3: Try discussion_risk_signals
                if vix_risk_to_use is None and discussion_risk_signals:
                    vix_risk_from_signals = discussion_risk_signals.get("vix_risk_score")
                    if vix_risk_from_signals is not None:
                        vix_risk_to_use = vix_risk_from_signals
                        vix_source = "discussion_risk_signals"
            
            if vix_risk_to_use is not None:
                print(f"[RISK ANALYST] Using VIX risk_score={vix_risk_to_use:.1f} from {vix_source}")
                current_risk_score = risk_report.get("risk_score", 5.0)
                # CRITICAL: VIX risk_score should be the minimum for overall risk_score
                # If VIX risk_score >= 6.0, overall risk_score must be at least 5.0
                if vix_risk_to_use >= 6.0:
                    # Force minimum risk_score based on VIX
                    min_risk_score = max(5.0, vix_risk_to_use - 1.0)  # At least 5.0 if VIX=6.0
                    if current_risk_score < min_risk_score:
                        print(f"[RISK ANALYST] 🔧 FORCING: VIX risk_score={vix_risk_to_use:.1f} (from {vix_source}) requires min overall risk_score={min_risk_score:.1f}, but LLM returned {current_risk_score:.1f}. Adjusting...")
                        risk_report["risk_score"] = min_risk_score
                        # Also adjust risk_level if needed
                        if risk_report.get("overall_risk_level", "").lower() == "low":
                            risk_report["overall_risk_level"] = "medium"
                            print(f"[RISK ANALYST] 🔧 FORCING: Changed risk_level from 'low' to 'medium' due to high VIX risk")
                elif vix_risk_to_use >= 4.0:
                    # VIX risk_score 4.0-5.9: ensure risk_score is at least 3.5
                    min_risk_score = max(3.5, vix_risk_to_use - 0.5)
                    if current_risk_score < min_risk_score:
                        print(f"[RISK ANALYST] 🔧 ADJUSTING: VIX risk_score={vix_risk_to_use:.1f} (from {vix_source}) requires min overall risk_score={min_risk_score:.1f}, but LLM returned {current_risk_score:.1f}. Adjusting...")
                        risk_report["risk_score"] = min_risk_score
                
                # Store VIX risk_score and source in risk_report for reference
                risk_report["vix_risk_score"] = vix_risk_to_use
                risk_report["vix_risk_source"] = vix_source
                if vix_api_data:
                    risk_report["vix_level"] = vix_api_data.get("vix")
                print(f"[RISK ANALYST] ✅ Final: VIX risk_score={vix_risk_to_use:.1f} (from {vix_source}), overall risk_score={risk_report['risk_score']:.1f}, risk_level={risk_report.get('overall_risk_level')}")
            else:
                print(f"[RISK ANALYST] ⚠️  WARNING: No VIX risk_score available from API, market_json, or discussion_risk_signals")
                # CRITICAL FIX: Try to get VIX risk_score from market_json one more time
                vix_risk_from_market = None
                if isinstance(market_json, dict):
                    vix_data = market_json.get("vix", {})
                    if isinstance(vix_data, dict):
                        vix_risk_from_market = vix_data.get("risk_score")
                if vix_risk_from_market is not None:
                    print(f"[RISK ANALYST] Found VIX risk_score={vix_risk_from_market:.1f} from market_json, applying...")
                    # Apply same logic as above
                    current_risk_score = risk_report.get("risk_score", 5.0)
                    if vix_risk_from_market >= 6.0:
                        min_risk_score = max(5.0, vix_risk_from_market - 1.0)
                        if current_risk_score < min_risk_score:
                            print(f"[RISK ANALYST] 🔧 FORCING: VIX risk_score={vix_risk_from_market:.1f} requires min overall risk_score={min_risk_score:.1f}, but LLM returned {current_risk_score:.1f}. Adjusting...")
                            risk_report["risk_score"] = min_risk_score
                            if risk_report.get("overall_risk_level", "").lower() == "low":
                                risk_report["overall_risk_level"] = "medium"
                                print(f"[RISK ANALYST] 🔧 FORCING: Changed risk_level from 'low' to 'medium' due to high VIX risk")
                    elif vix_risk_from_market >= 4.0:
                        min_risk_score = max(3.5, vix_risk_from_market - 0.5)
                        if current_risk_score < min_risk_score:
                            print(f"[RISK ANALYST] 🔧 ADJUSTING: VIX risk_score={vix_risk_from_market:.1f} requires min overall risk_score={min_risk_score:.1f}, but LLM returned {current_risk_score:.1f}. Adjusting...")
                            risk_report["risk_score"] = min_risk_score
                    risk_report["vix_risk_score"] = vix_risk_from_market
                    risk_report["vix_risk_source"] = "market_json (fallback)"
                    print(f"[RISK ANALYST] ✅ Final: VIX risk_score={vix_risk_from_market:.1f} (from market_json fallback), overall risk_score={risk_report['risk_score']:.1f}, risk_level={risk_report.get('overall_risk_level')}")
                else:
                    print(f"[RISK ANALYST] ❌ ERROR: No VIX risk_score found anywhere - API call may have failed or use_tools=False")
            
            if "position_control_report" not in risk_report:
                risk_report["position_control_report"] = _default_position_control(current_positions, portfolio_value, market_json)
            
            # 修复：确保 position_control_report.recommended_position_sizes 的值是字典类型
            position_control = risk_report.get("position_control_report", {})
            recommended_sizes = position_control.get("recommended_position_sizes", {})
            if isinstance(recommended_sizes, dict):
                # 检查并修复每个值，确保是字典类型
                for symbol, size_info in list(recommended_sizes.items()):
                    if not isinstance(size_info, dict):
                        # 如果是字符串或其他类型，尝试解析或使用默认值
                        if isinstance(size_info, (int, float)):
                            # 如果是数字，转换为字典格式
                            recommended_sizes[symbol] = {
                                "max_pct": float(size_info),
                                "current_pct": 0.0,
                                "adjustment": "HOLD"
                            }
                        elif isinstance(size_info, str):
                            # 如果是字符串，尝试解析 JSON 或使用默认值
                            try:
                                parsed = json.loads(size_info)
                                if isinstance(parsed, dict):
                                    recommended_sizes[symbol] = parsed
                                else:
                                    # 解析后不是字典，使用默认值
                                    recommended_sizes[symbol] = {
                                        "max_pct": 0.15,
                                        "current_pct": 0.0,
                                        "adjustment": "HOLD"
                                    }
                            except (json.JSONDecodeError, TypeError):
                                # 解析失败，使用默认值
                                recommended_sizes[symbol] = {
                                    "max_pct": 0.15,
                                    "current_pct": 0.0,
                                    "adjustment": "HOLD"
                                }
                        else:
                            # 其他类型，使用默认值
                            recommended_sizes[symbol] = {
                                "max_pct": 0.15,
                                "current_pct": 0.0,
                                "adjustment": "HOLD"
                            }
                position_control["recommended_position_sizes"] = recommended_sizes
                risk_report["position_control_report"] = position_control
            
            # CRITICAL FIX: Add tool calls information to risk_report
            # IMPORTANT: Always add tool_results_data, even if tool_calls_used is empty (forced VIX API call)
            print(f"[RISK ANALYST] DEBUG: Before adding tool calls - tool_calls_used={tool_calls_used}, tool_results_data count={len(tool_results_data)}")
            
            if tool_calls_used:
                risk_report["tools_used"] = tool_calls_used
            # CRITICAL FIX: Always add tool_results_data to risk_report, even if empty
            # This ensures forced VIX API call is always included
            if tool_results_data:
                # CRITICAL FIX: Make tool_results_data JSON serializable (handle pandas Series)
                risk_report["tool_calls"] = make_json_serializable(tool_results_data)
                print(f"[RISK ANALYST] ✅ Added {len(tool_results_data)} tool calls to risk_report (including forced VIX API call)")
                # Debug: Print first tool call details
                if tool_results_data:
                    first_tool = tool_results_data[0]
                    print(f"[RISK ANALYST] DEBUG: First tool call: {first_tool.get('tool')}, result keys: {list(first_tool.get('result', {}).keys()) if isinstance(first_tool.get('result'), dict) else 'N/A'}")
            else:
                # CRITICAL FIX: Even if tool_results_data is empty, add empty list to ensure structure exists
                risk_report["tool_calls"] = []
                print(f"[RISK ANALYST] ⚠️  WARNING: tool_results_data is empty - VIX API call may have failed or returned invalid data")
                print(f"[RISK ANALYST] DEBUG: tool_calls_used={tool_calls_used}, vix_api_data={vix_api_data is not None if 'vix_api_data' in locals() else 'N/A'}")
            
            # CRITICAL FIX: Ensure entire risk_report is JSON serializable
            return make_json_serializable(risk_report)
            
        except json.JSONDecodeError as je:
            print(f"[RISK ANALYST LLM] Failed to parse JSON, using fallback: {je}")
            import traceback
            traceback.print_exc()
            # CRITICAL FIX: Even in fallback, preserve tool_results_data if available
            fallback_report = _fallback_risk_analysis(market_json, current_positions, portfolio_value)
            if tool_results_data:
                fallback_report["tool_calls"] = make_json_serializable(tool_results_data)
                print(f"[RISK ANALYST LLM] Added {len(tool_results_data)} tool calls to fallback report")
            return fallback_report
    
    except Exception as e:
        print(f"[RISK ANALYST LLM] Error: {e}")
        import traceback
        traceback.print_exc()
        # CRITICAL FIX: Even in fallback, preserve tool_results_data if available
        fallback_report = _fallback_risk_analysis(market_json, current_positions, portfolio_value)
        if tool_results_data:
            fallback_report["tool_calls"] = make_json_serializable(tool_results_data)
            print(f"[RISK ANALYST LLM] Added {len(tool_results_data)} tool calls to fallback report")
        return fallback_report


def _default_position_control(
    current_positions: Optional[Dict[str, Any]],
    portfolio_value: Optional[float],
    market_json: Dict[str, Any],
) -> Dict[str, Any]:
    """生成默认的仓位控管报告"""
    stocks = market_json.get("stocks", {})
    
    # Load max_positions from config
    from src.utils.config_loader import load_config
    config = load_config()
    MAX_POSITIONS = config.get("max_positions", 10)
    
    position_control = {
        "max_position_per_stock": 0.15,
        "max_total_position": 0.85,
        "max_positions": MAX_POSITIONS,  # Add max_positions to control report
        "recommended_position_sizes": {},
        "position_limit_checks": [],
    }
    
    if current_positions and portfolio_value and portfolio_value > 0:
        current_position_count = len(current_positions)
        
        # Check if total position count exceeds limit
        if current_position_count > MAX_POSITIONS:
            # Mark all positions as over_limit to trigger selling
            for symbol, pos_info in current_positions.items():
                if isinstance(pos_info, dict):
                    qty = pos_info.get("quantity", 0)
                    current_price = pos_info.get("current_price", pos_info.get("avg_cost", 0.0))
                else:
                    qty = pos_info if isinstance(pos_info, (int, float)) else 0
                    current_price = stocks.get(symbol, {}).get("price", 0.0)
                
                position_value = qty * current_price
                exposure = (position_value / portfolio_value) if portfolio_value > 0 else 0.0
                
                # Add recommended position size
                position_control["recommended_position_sizes"][symbol] = {
                    "current_pct": round(exposure, 4),
                    "max_pct": 0.15,
                    "adjustment": "REDUCE",  # Force reduce when over max_positions
                }
                
                # Mark as over_limit to trigger selling
                position_control["position_limit_checks"].append({
                    "symbol": symbol,
                    "status": "over_limit",
                    "limit": 0.15,
                    "message": f"Position count exceeds max ({current_position_count}/{MAX_POSITIONS}), recommend reducing {symbol}",
                })
        else:
            # Normal position limit checks (per-stock exposure)
            for symbol, pos_info in current_positions.items():
                if isinstance(pos_info, dict):
                    qty = pos_info.get("quantity", 0)
                    current_price = pos_info.get("current_price", pos_info.get("avg_cost", 0.0))
                else:
                    qty = pos_info if isinstance(pos_info, (int, float)) else 0
                    current_price = stocks.get(symbol, {}).get("price", 0.0)
                
                position_value = qty * current_price
                exposure = (position_value / portfolio_value) if portfolio_value > 0 else 0.0
                
                # Add recommended position size
                position_control["recommended_position_sizes"][symbol] = {
                    "current_pct": round(exposure, 4),
                    "max_pct": 0.15,
                    "adjustment": "HOLD" if exposure <= 0.15 else "REDUCE",
                }
                
                # Add position limit check
                if exposure > 0.15:
                    position_control["position_limit_checks"].append({
                        "symbol": symbol,
                        "status": "over_limit",
                        "limit": 0.15,
                        "message": f"Position exceeds 15% limit ({exposure*100:.1f}%)",
                    })
                else:
                    position_control["position_limit_checks"].append({
                        "symbol": symbol,
                        "status": "OK",
                        "message": f"Within limits ({exposure*100:.1f}%)",
                    })
    
    return position_control


def _fallback_risk_analysis(
    market_json: Dict[str, Any],
    current_positions: Optional[Dict[str, Any]],
    portfolio_value: Optional[float],
) -> Dict[str, Any]:
    """Fallback: 使用基础规则进行风险评估"""
    from ..tools.analysis_tools import risk_score
    
    stocks = market_json.get("stocks", {})
    
    # 计算每只股票的风险分数
    scores = {}
    for sym, stock_data in stocks.items():
        try:
            scores[sym] = float(risk_score.invoke({"symbol_data": stock_data}))
        except Exception:
            scores[sym] = 5.0
    
    high_risk = [s for s, v in scores.items() if v > 7]
    safe_stocks = [s for s, v in scores.items() if v <= 5]
    
    avg_risk = sum(scores.values()) / len(scores) if scores else 5.0
    
    # 判断整体风险等级
    if avg_risk > 7:
        overall_risk_level = "high"
    elif avg_risk > 5:
        overall_risk_level = "medium"
    else:
        overall_risk_level = "low"
    
    # 生成市场风险列表
    market_risks = []
    if len(high_risk) > 0:
        market_risks.append({
            "type": "high_volatility_stocks",
            "severity": "high",
            "description": f"{len(high_risk)} stocks with high risk scores: {', '.join(high_risk[:3])}",
        })
    
    # 生成仓位风险列表
    position_risks = []
    if current_positions and portfolio_value and portfolio_value > 0:
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                qty = pos_info.get("quantity", 0)
                current_price = pos_info.get("current_price", pos_info.get("avg_cost", 0.0))
            else:
                qty = pos_info if isinstance(pos_info, (int, float)) else 0
                current_price = stocks.get(symbol, {}).get("price", 0.0)
            
            position_value = qty * current_price
            exposure = (position_value / portfolio_value) if portfolio_value > 0 else 0.0
            
            if exposure > 0.15:
                position_risks.append({
                    "symbol": symbol,
                    "risk": "concentration",
                    "exposure": f"{exposure*100:.1f}%",
                    "recommendation": "Consider reducing position",
                })
    
    return {
        "overall_risk_level": overall_risk_level,
        "risk_score": round(avg_risk, 2),
        "analysis": f"Market analysis shows {len(high_risk)} high-risk stocks and {len(safe_stocks)} safe stocks. Overall risk score: {avg_risk:.2f}/10.",
        "market_risks": market_risks,
        "position_risks": position_risks,
        "high_risk_stocks": high_risk,
        "safe_stocks": safe_stocks,
        "position_control_report": _default_position_control(current_positions, portfolio_value, market_json),
        "recommendations": [
            "Monitor high-risk stocks closely",
            "Maintain diversification",
            "Keep cash reserves for opportunities",
        ],
    }

