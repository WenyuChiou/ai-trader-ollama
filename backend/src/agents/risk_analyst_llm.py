from __future__ import annotations
from typing import Dict, Any, Optional
from pathlib import Path
import json


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
    market_summary = {
        "stocks_count": len(market_json.get("stocks", {})),
        "vix": market_json.get("vix"),
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
                    for tool_call in tool_calls_list:
                        tool_name = tool_call.get("name", "")
                        tool_args = tool_call.get("args", {})
                        
                        # CRITICAL FIX: Map deprecated news_scan to plan_and_scan_news
                        if tool_name == "news_scan":
                            print(f"[RISK ANALYST] Mapping news_scan to plan_and_scan_news (news_scan is deprecated)")
                            tool_name = "plan_and_scan_news"
                            # Update tool_args if needed
                            if "keywords" in tool_args and "tickers" not in tool_args:
                                tool_args["tickers"] = tool_args.pop("keywords", [])
                        
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
            if tool_calls_used:
                risk_report["tools_used"] = tool_calls_used
                # CRITICAL FIX: Make tool_results_data JSON serializable (handle pandas Series)
                risk_report["tool_calls"] = make_json_serializable(tool_results_data)
            
            # CRITICAL FIX: Ensure entire risk_report is JSON serializable
            return make_json_serializable(risk_report)
            
        except json.JSONDecodeError:
            print(f"[RISK ANALYST LLM] Failed to parse JSON, using fallback")
            # Fallback: 使用基础规则
            return _fallback_risk_analysis(market_json, current_positions, portfolio_value)
    
    except Exception as e:
        print(f"[RISK ANALYST LLM] Error: {e}")
        # Fallback: 使用基础规则
        return _fallback_risk_analysis(market_json, current_positions, portfolio_value)


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

