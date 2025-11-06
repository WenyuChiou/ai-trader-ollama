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
    
    # 格式化当前持仓信息
    positions_str = json.dumps(current_positions, indent=2) if current_positions else "No positions"
    
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
    
    try:
        # 调用LLM
        response = agent.chat(prompt_vars)
        
        # 尝试解析JSON响应
        try:
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
            
            return risk_report
            
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
    
    position_control = {
        "max_position_per_stock": 0.15,
        "max_total_position": 0.85,
        "recommended_position_sizes": {},
        "position_limit_checks": [],
    }
    
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
            
            # 添加推荐仓位大小
            position_control["recommended_position_sizes"][symbol] = {
                "current_pct": round(exposure, 4),
                "max_pct": 0.15,
                "adjustment": "HOLD" if exposure <= 0.15 else "REDUCE",
            }
            
            # 添加仓位限制检查
            if exposure > 0.15:
                position_control["position_limit_checks"].append({
                    "symbol": symbol,
                    "status": "WARNING",
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

