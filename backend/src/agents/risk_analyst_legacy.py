"""
DEPRECATED: This is a legacy version of Risk Analyst.
The main trading system now uses risk_analyst_llm.py (LLM-powered Risk Analyst).
This file may be removed in a future version.
"""
from __future__ import annotations
from typing import Dict, Any, Optional
from ..tools.analysis_tools import risk_score
from ..data.portfolio import Portfolio


def run_risk_analyst(
    market_json: Dict[str, Any],
    current_positions: Optional[Dict[str, Any]] = None,
    portfolio_value: Optional[float] = None,
    discussion_risk_signals: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Risk Analyst: 评估当前仓位风险，并基于 Market Analyst 和 Analyst Discussion 的结果提出仓位控管报告
    
    输入:
    - market_json: 市场数据（包含 stocks）
    - current_positions: 当前持仓 {symbol: {quantity, avg_cost, ...}}
    - portfolio_value: 当前组合净值
    - discussion_risk_signals: 来自 Analyst Discussion 的风险信号
    
    输出:
    - overall_risk_level: 整体风险等级
    - risk_score: 风险评分
    - current_position_risk: 当前仓位风险评估
    - Position Control Report: 仓位控管报告
    """
    # 1. 评估市场风险（原有逻辑）
    stocks = market_json.get("stocks", {})
    scores = {}
    for sym, stock_data in stocks.items():
        try:
            scores[sym] = float(risk_score.invoke({"symbol_data": stock_data}))
        except Exception:
            scores[sym] = 5.0  # 默认中等风险
    
    high = [s for s, v in scores.items() if v > 7]
    safe = [s for s, v in scores.items() if v <= 5]
    
    # 2. 评估当前仓位风险
    current_position_risk = {
        "position_concentration": 0.0,
        "single_stock_exposure": {},
        "overall_exposure": 0.0,
        "recommended_adjustments": [],
    }
    
    position_limit_checks = []
    recommended_position_sizes = {}
    
    if current_positions and portfolio_value and portfolio_value > 0:
        # 计算仓位集中度
        position_values = {}
        total_position_value = 0.0
        
        for sym, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                qty = pos_info.get("quantity", 0)
                avg_cost = pos_info.get("avg_cost", 0.0)
                current_price = pos_info.get("current_price", avg_cost)
            else:
                # 兼容旧格式：只有数量
                qty = pos_info if isinstance(pos_info, (int, float)) else 0
                avg_cost = stocks.get(sym, {}).get("price", 0.0)
                current_price = avg_cost
            
            position_value = qty * current_price
            position_values[sym] = position_value
            total_position_value += position_value
            
            # 单股暴露度
            exposure = (position_value / portfolio_value) if portfolio_value > 0 else 0.0
            current_position_risk["single_stock_exposure"][sym] = exposure
            
            # 检查仓位限制（可以从配置读取，暂时使用默认值）
            max_per_stock = 0.15  # 单股最大15%（可以从 config.json 读取）
            if exposure > max_per_stock:
                position_limit_checks.append({
                    "symbol": sym,
                    "exposure": exposure,
                    "limit": max_per_stock,
                    "status": "over_limit",
                    "recommendation": f"Reduce {sym} position to <= {max_per_stock*100:.1f}%"
                })
                current_position_risk["recommended_adjustments"].append({
                    "symbol": sym,
                    "action": "reduce",
                    "current_exposure": exposure,
                    "target_exposure": max_per_stock,
                })
        
        # 仓位集中度（使用 Herfindahl-Hirschman Index）
        if total_position_value > 0:
            hhi = sum((v / total_position_value) ** 2 for v in position_values.values())
            current_position_risk["position_concentration"] = hhi
        
        # 总仓位暴露度
        current_position_risk["overall_exposure"] = (total_position_value / portfolio_value) if portfolio_value > 0 else 0.0
        
        # 生成推荐仓位大小（基于风险评分）
        for sym, risk in scores.items():
            if risk > 7:
                recommended_position_sizes[sym] = {
                    "max_pct": 0.05,  # 高风险股票限制5%
                    "recommendation": "high_risk",
                }
            elif risk <= 5:
                recommended_position_sizes[sym] = {
                    "max_pct": 0.15,  # 安全股票可到15%
                    "recommendation": "safe",
                }
            else:
                recommended_position_sizes[sym] = {
                    "max_pct": 0.10,  # 中等风险10%
                    "recommendation": "medium_risk",
                }
    
    # 3. 整合 Discussion 的风险信号
    discussion_risk_level = "medium"
    if discussion_risk_signals:
        discussion_risk_level = discussion_risk_signals.get("risk_level", "medium")
    
    # 4. 生成最终风险报告
    overall_risk_level = "high"
    if len(high) < max(1, len(scores) // 3):
        if current_position_risk["position_concentration"] < 0.3:
            overall_risk_level = "medium"
        else:
            overall_risk_level = "high"
    else:
        overall_risk_level = "high"
    
    # 综合 Discussion 的风险信号
    if discussion_risk_level in ("high", "critical"):
        overall_risk_level = "high"
    
    avg_risk_score = sum(scores.values()) / max(1, len(scores))
    
    # 5. 生成仓位控管报告
    position_control_report = {
        "recommended_position_sizes": recommended_position_sizes,
        "position_limit_checks": position_limit_checks,
        "rebalancing_suggestions": current_position_risk["recommended_adjustments"],
    }
    
    return {
        "overall_risk_level": overall_risk_level,
        "risk_score": avg_risk_score,
        "max_position_size": {"per_stock": 0.15, "total_equity": 0.60},
        "risk_warnings": [f"{s} risk={scores[s]:.1f}" for s in high],
        "safe_stocks": safe,
        "high_risk_stocks": high,
        "diversification_advice": "Keep single-name exposure <=15%.",
        "current_position_risk": current_position_risk,
        "position_control_report": position_control_report,
    }
