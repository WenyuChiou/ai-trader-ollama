# src/agents/stock_selection_agent.py
"""
Stock Selection Agent: 评估所有候选股票，生成潜在购买公司列表

这个 Agent 专门负责：
1. 评估所有候选股票（从 config.json 的 universe）
2. 生成 potential_buys 列表（带评分和理由）
3. 为 Discussion Agent 提供股票选择讨论的基础
"""
from __future__ import annotations
from typing import Dict, Any, List, Optional
from ..tools.analysis_tools import assess_trend, risk_score


def _evaluate_stock(
    symbol: str,
    stock_data: Dict[str, Any],
    vix_risk: float,
) -> Dict[str, Any]:
    """
    评估单个股票：计算综合评分
    
    返回:
    - score: 综合评分 (0-10)
    - recommendation: "BUY", "HOLD", "SELL"
    - reasons: 理由列表
    """
    signal_score = stock_data.get("signal_score", 0.0)
    if not isinstance(signal_score, (int, float)):
        signal_score = 0.0
    
    # 评估趋势
    try:
        trend = assess_trend.invoke({"symbol_data": stock_data})
    except Exception:
        trend = "sideways"
    
    # 评估风险
    try:
        risk_score_val = float(risk_score.invoke({"symbol_data": stock_data}))
    except Exception:
        risk_score_val = 5.0
    
    # 计算综合评分
    score = 0.0
    reasons = []
    
    # Signal Score (0-3)
    score += signal_score
    
    # Trend (uptrend: +2, downtrend: -2, sideways: 0)
    if trend == "uptrend":
        score += 2.0
        reasons.append("uptrend")
    elif trend == "downtrend":
        score -= 2.0
        reasons.append("downtrend")
    
    # Risk Score (低风险 +1, 高风险 -1)
    if risk_score_val <= 4.0:
        score += 1.0
        reasons.append("low_risk")
    elif risk_score_val >= 7.0:
        score -= 1.0
        reasons.append("high_risk")
    
    # VIX 风险影响（高 VIX 降低评分）
    if vix_risk > 6.0:
        score -= 1.0
        reasons.append("high_vix")
    
    # 确定推荐
    if trend == "downtrend" or risk_score_val >= 8.0:
        recommendation = "SELL"
    elif score >= 4.0 and trend == "uptrend" and vix_risk <= 6.0:
        recommendation = "BUY"
    elif score >= 2.0:
        recommendation = "HOLD"
    else:
        recommendation = "HOLD"
    
    return {
        "symbol": symbol,
        "score": score,
        "signal_score": signal_score,
        "trend": trend,
        "risk_score": risk_score_val,
        "recommendation": recommendation,
        "reasons": reasons,
    }


def run_stock_selection_agent(
    market_data: Dict[str, Any],
    universe: List[str],
    last_prices: Dict[str, float],
    vix_risk: float = 4.0,
    min_score: float = 3.0,
    top_n: int = 20,
) -> Dict[str, Any]:
    """
    Stock Selection Agent: 评估所有候选股票，生成潜在购买公司列表
    
    输入:
    - market_data: 市场数据（包含 stocks）
    - universe: 所有候选股票列表
    - last_prices: 最新价格
    - vix_risk: VIX 风险评分
    - min_score: 最小评分阈值（只返回 >= min_score 的股票）
    - top_n: 返回前 N 名股票
    
    输出:
    - recommended_stocks: 推荐的股票列表（带评分）
    - stock_rankings: 所有候选股票的排名（按评分降序）
    - potential_buys: 潜在购买公司列表（评分 >= min_score，推荐 BUY）
    - selection_summary: 选择摘要
    """
    stocks = market_data.get("stocks", {})
    evaluations: List[Dict[str, Any]] = []
    
    # 评估所有候选股票
    for symbol in universe:
        if symbol not in stocks:
            continue
        
        if symbol not in last_prices:
            continue
        
        stock_data = stocks[symbol]
        evaluation = _evaluate_stock(symbol, stock_data, vix_risk)
        evaluation["price"] = last_prices.get(symbol, 0.0)
        evaluations.append(evaluation)
    
    # 按评分排序（降序）
    evaluations.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    
    # 筛选潜在购买公司（评分 >= min_score，推荐 BUY）
    potential_buys = [
        e for e in evaluations
        if e.get("score", 0) >= min_score and e.get("recommendation") == "BUY"
    ]
    
    # 限制数量
    if len(potential_buys) > top_n:
        potential_buys = potential_buys[:top_n]
    
    # 推荐股票（前 N 名）
    recommended_stocks = [e["symbol"] for e in evaluations[:top_n]]
    
    # 生成选择摘要
    buy_count = len(potential_buys)
    hold_count = sum(1 for e in evaluations if e.get("recommendation") == "HOLD")
    sell_count = sum(1 for e in evaluations if e.get("recommendation") == "SELL")
    
    selection_summary = {
        "total_evaluated": len(evaluations),
        "buy_candidates": buy_count,
        "hold_candidates": hold_count,
        "sell_candidates": sell_count,
        "top_score": evaluations[0].get("score", 0.0) if evaluations else 0.0,
        "avg_score": sum(e.get("score", 0.0) for e in evaluations) / len(evaluations) if evaluations else 0.0,
    }
    
    return {
        "recommended_stocks": recommended_stocks,
        "stock_rankings": evaluations,  # 所有股票的排名（按评分降序）
        "potential_buys": potential_buys,  # 潜在购买公司列表
        "selection_summary": selection_summary,
    }

