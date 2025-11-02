from __future__ import annotations
from typing import Dict, Any, Optional, List, Tuple
from math import floor
from ..tools.analysis_tools import assess_trend, risk_score


def _calculate_position_size(
    symbol: str,
    recommended_stocks: List[str],
    portfolio_value: float,
    last_price: float,
    risk_report: Optional[Dict[str, Any]] = None,
    current_positions: Optional[Dict[str, Any]] = None,
) -> int:
    """
    计算买入数量（基于风险控管建议）
    - 单股最大15%仓位
    - 考虑风险报告的建议
    - 考虑当前持仓
    """
    if portfolio_value <= 0 or last_price <= 0:
        return 0
    
    # 基础：单股最大15%
    max_pct = 0.15
    
    # 从风险报告获取推荐仓位大小
    if risk_report:
        control_report = risk_report.get("position_control_report", {})
        recommended_sizes = control_report.get("recommended_position_sizes", {})
        if symbol in recommended_sizes:
            max_pct = recommended_sizes[symbol].get("max_pct", 0.15)
    
    # 计算目标市值
    target_value = portfolio_value * max_pct
    
    # 计算数量（向下取整）
    quantity = floor(target_value / last_price)
    
    # 考虑当前持仓（避免过度集中）
    if current_positions:
        pos_info = current_positions.get(symbol)
        if pos_info:
            if isinstance(pos_info, dict):
                current_qty = pos_info.get("quantity", 0)
                current_price = pos_info.get("current_price", last_price)
            else:
                current_qty = pos_info if isinstance(pos_info, (int, float)) else 0
                current_price = last_price
            
            current_value = current_qty * current_price
            if current_value >= target_value:
                # 已达到目标仓位
                return 0
            # 计算还需要买入的数量
            remaining_value = target_value - current_value
            additional_qty = floor(remaining_value / last_price)
            return additional_qty
    
    return max(0, quantity)


def _calculate_sell_size(
    symbol: str,
    current_qty: int,
    portfolio_value: float,
    last_price: float,
    risk_report: Optional[Dict[str, Any]] = None,
    sell_reason: Optional[str] = None,
) -> Tuple[int, str]:
    """
    计算卖出数量（基于风险控管建议或卖出理由）
    - 如果超过限制，减少到目标仓位（部分卖出）
    - 如果趋势转弱，全部卖出
    - sell_reason: "over_limit" (部分减仓), "downtrend" (全部卖出), "stop_loss" (止损)
    
    返回: (卖出数量, 卖出理由)
    """
    if current_qty <= 0 or last_price <= 0:
        return (0, "")
    
    # 如果趋势转弱，全部卖出
    if sell_reason == "downtrend":
        return (current_qty, "downtrend")
    
    # 如果止损，全部卖出
    if sell_reason == "stop_loss":
        return (current_qty, "stop_loss")
    
    # 检查是否需要减仓（超限）
    if risk_report:
        control_report = risk_report.get("position_control_report", {})
        limit_checks = control_report.get("position_limit_checks", [])
        
        for check in limit_checks:
            if check.get("symbol") == symbol and check.get("status") == "over_limit":
                # 需要减仓
                target_exposure = check.get("limit", 0.15)
                target_value = portfolio_value * target_exposure
                current_value = current_qty * last_price
                
                if current_value > target_value:
                    excess_value = current_value - target_value
                    sell_qty = floor(excess_value / last_price)
                    return (min(sell_qty, current_qty), "over_limit")
    
    return (0, "")


def _evaluate_stock(
    symbol: str,
    stock_data: Dict[str, Any],
    vix_risk: float,
    trend: Optional[str] = None,
    risk_score_val: Optional[float] = None,
) -> Dict[str, Any]:
    """
    评估股票：计算综合评分
    
    返回:
    - score: 综合评分 (0-10)
    - recommendation: "BUY", "HOLD", "SELL"
    - reasons: 理由列表
    """
    signal_score = stock_data.get("signal_score", 0.0)
    if not isinstance(signal_score, (int, float)):
        signal_score = 0.0
    
    # 评估趋势
    if trend is None:
        try:
            trend = assess_trend.invoke({"symbol_data": stock_data})
        except Exception:
            trend = "sideways"
    
    # 评估风险
    if risk_score_val is None:
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


def _evaluate_all_stocks(
    market: Dict[str, Any],
    mview: Dict[str, Any],
    last_prices: Dict[str, float],
    vix_risk: float,
) -> List[Dict[str, Any]]:
    """
    评估所有候选股票
    
    返回: 排序后的股票评估列表（按评分降序）
    """
    stocks = market.get("stocks", {})
    evaluations = []
    
    for symbol, stock_data in stocks.items():
        if symbol not in last_prices:
            continue
        
        evaluation = _evaluate_stock(symbol, stock_data, vix_risk)
        evaluation["price"] = last_prices.get(symbol, 0.0)
        evaluations.append(evaluation)
    
    # 按评分排序（降序）
    evaluations.sort(key=lambda x: x.get("score", 0.0), reverse=True)
    
    return evaluations


def run_trader(
    market: Dict[str, Any],
    mview: Dict[str, Any],
    rview: Dict[str, Any] | None,
    convo: Dict[str, Any],
    last_prices: Dict[str, float],
    current_positions: Optional[Dict[str, Any]] = None,
    portfolio_value: Optional[float] = None,
    all_candidates: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Trader Agent: 决定是否买卖（包含买卖那些公司、部位、买进价格、卖出价格等）
    
    输入:
    - market: 市场数据
    - mview: enriched market view
    - rview: risk view (来自 Risk Analyst，包含仓位控管报告)
    - convo: discussion consensus
    - last_prices: 最新价格
    - current_positions: 当前持仓（可选）
    - portfolio_value: 当前组合净值（可选）
    - all_candidates: 所有候选股票列表（可选，如果提供则评估所有候选股票）
    
    输出:
    - action: BUY / SELL / HOLD
    - buy_orders: 买进订单列表（包含 symbol, buy_price, quantity, total_cost）
    - sell_orders: 卖出订单列表（包含 symbol, sell_price, quantity, total_proceeds, sell_reason）
    - rationale: 决策理由
    - risk_compliance: 风险合规检查
    - potential_buys: 潜在购买公司列表（包含评估信息）
    - position_adjustments: 持仓调整建议
    """
    vix = (mview.get("vix") or {}) if isinstance(mview, dict) else {}
    vix_risk = float(vix.get("risk_score", 4.0))
    stance = "cautious" if vix_risk > 6.0 else mview.get("market_sentiment", "neutral")

    recs = mview.get("recommended_stocks", []) if isinstance(mview, dict) else []
    final_stance = (convo or {}).get("final_stance", "neutral")
    
    # 默认组合净值（如果没有提供）
    if portfolio_value is None:
        portfolio_value = 10000.0  # 默认初始净值
    
    # 默认当前持仓（如果没有提供）
    if current_positions is None:
        current_positions = {}
    
    buy_orders: List[Dict[str, Any]] = []
    sell_orders: List[Dict[str, Any]] = []
    potential_buys: List[Dict[str, Any]] = []
    position_adjustments: List[Dict[str, Any]] = []
    
    # 风险合规检查
    risk_compliance = {
        "position_limits_ok": True,
        "diversification_ok": True,
        "warnings": [],
    }
    
    # === 评估所有候选股票 ===
    if all_candidates:
        # 如果有提供候选列表，评估所有候选股票
        stock_evaluations = _evaluate_all_stocks(market, mview, last_prices, vix_risk)
        
        # 过滤出有价格的股票
        stock_evaluations = [e for e in stock_evaluations if e.get("price", 0) > 0]
        
        # 潜在购买公司（评分 >= 3.0，且推荐 BUY）
        potential_buys = [
            e for e in stock_evaluations
            if e.get("score", 0) >= 3.0 and e.get("recommendation") == "BUY"
        ]
    else:
        # 否则只评估推荐的股票
        stock_evaluations = []
        for symbol in recs:
            if symbol in market.get("stocks", {}) and symbol in last_prices:
                stock_data = market["stocks"][symbol]
                evaluation = _evaluate_stock(symbol, stock_data, vix_risk)
                evaluation["price"] = last_prices[symbol]
                stock_evaluations.append(evaluation)
        
        potential_buys = stock_evaluations

    # === 评估当前持仓：决定是否卖出 ===
    holdings_to_sell: List[Dict[str, Any]] = []
    holdings_to_hold: List[str] = []
    
    for symbol, pos_info in current_positions.items():
        if isinstance(pos_info, dict):
            qty = pos_info.get("quantity", 0)
            avg_cost = pos_info.get("avg_cost", 0.0)
            current_price = pos_info.get("current_price", last_prices.get(symbol, 0.0))
        else:
            qty = pos_info if isinstance(pos_info, (int, float)) else 0
            avg_cost = 0.0
            current_price = last_prices.get(symbol, 0.0)
        
        if qty <= 0 or symbol not in last_prices:
            continue
        
        # 评估当前持仓股票
        stock_data = market.get("stocks", {}).get(symbol, {})
        if not stock_data:
            continue
        
        evaluation = _evaluate_stock(symbol, stock_data, vix_risk)
        trend = evaluation.get("trend")
        risk_score_val = evaluation.get("risk_score", 5.0)
        recommendation = evaluation.get("recommendation")
        
        # 决定卖出理由
        sell_reason = None
        
        # 如果趋势转弱，全部卖出
        if trend == "downtrend":
            sell_reason = "downtrend"
        # 如果风险过高，全部卖出
        elif risk_score_val >= 8.0:
            sell_reason = "stop_loss"
        # 如果超过仓位限制，部分减仓
        elif rview:
            control_report = rview.get("position_control_report", {})
            limit_checks = control_report.get("position_limit_checks", [])
            for check in limit_checks:
                if check.get("symbol") == symbol and check.get("status") == "over_limit":
                    sell_reason = "over_limit"
                    break
        
        # 计算卖出数量
        if sell_reason:
            sell_qty, reason = _calculate_sell_size(
                symbol, qty, portfolio_value, last_prices[symbol], rview, sell_reason
            )
            if sell_qty > 0:
                sell_price = last_prices[symbol]
                holdings_to_sell.append({
                    "symbol": symbol,
                    "sell_price": sell_price,
                    "quantity": sell_qty,
                    "total_proceeds": sell_price * sell_qty,
                    "sell_reason": reason,
                    "trend": trend,
                    "risk_score": risk_score_val,
                })
                
                # 如果是部分卖出，剩余持仓继续持有
                if sell_qty < qty:
                    holdings_to_hold.append(symbol)
        else:
            # 继续持有
            holdings_to_hold.append(symbol)
            position_adjustments.append({
                "symbol": symbol,
                "action": "HOLD",
                "current_qty": qty,
                "reason": f"trend={trend}, risk={risk_score_val:.1f}",
            })
    
    sell_orders.extend(holdings_to_sell)
    
    # 若新聞/情緒最終 stance 偏空或 VIX 高風險，保守處理（只卖出，不买入）
    if vix_risk > 6.0 or final_stance in ("bearish", "cautious"):
        action = "SELL" if sell_orders else "HOLD"
        return {
            "action": action,
            "targets": [],
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "potential_buys": potential_buys[:10],  # 限制数量
            "position_adjustments": position_adjustments,
            "rationale": f"Hold/Sell due to VIX risk={vix_risk:.1f} / news stance={final_stance}",
            "stance": final_stance,
            "vix_risk": vix_risk,
            "risk_compliance": risk_compliance,
        }

    # === 生成买入订单：从潜在购买公司中选择 ===
    if potential_buys and portfolio_value > 0:
        # 按评分排序，优先买入高分股票
        # 限制买入数量（避免过度集中）
        max_new_positions = 5  # 最多买入5只新股票
        
        buy_candidates = []
        for eval_info in potential_buys:
            symbol = eval_info.get("symbol")
            if symbol not in last_prices:
                continue
            
            last_price = eval_info.get("price", 0.0)
            if last_price <= 0:
                continue
            
            # 如果已有持仓且评分仍高，可以考虑增持
            has_position = symbol in current_positions
            
            # 如果是新持仓，限制数量
            if not has_position and len([o for o in buy_orders if o.get("symbol") not in current_positions]) >= max_new_positions:
                continue
            
            # 计算买入数量
            quantity = _calculate_position_size(
                symbol, [e.get("symbol") for e in potential_buys], portfolio_value, last_price, rview, current_positions
            )
            
            if quantity > 0:
                buy_candidates.append({
                    "symbol": symbol,
                    "buy_price": last_price,
                    "quantity": quantity,
                    "total_cost": last_price * quantity,
                    "evaluation": eval_info,
                    "action": "INCREASE" if has_position else "NEW",
                })
        
        # 按评分排序并选择最佳候选
        buy_candidates.sort(key=lambda x: x.get("evaluation", {}).get("score", 0), reverse=True)
        
        # 限制总买入金额（不超过可用现金的80%）
        available_cash = portfolio_value * 0.8
        total_cost = 0.0
        
        for candidate in buy_candidates:
            if total_cost + candidate["total_cost"] <= available_cash:
                buy_orders.append({
                    "symbol": candidate["symbol"],
                    "buy_price": candidate["buy_price"],
                    "quantity": candidate["quantity"],
                    "total_cost": candidate["total_cost"],
                    "action": candidate["action"],
                })
                total_cost += candidate["total_cost"]
                
                position_adjustments.append({
                    "symbol": candidate["symbol"],
                    "action": candidate["action"],
                    "quantity": candidate["quantity"],
                    "reason": f"score={candidate['evaluation'].get('score', 0):.1f}, trend={candidate['evaluation'].get('trend')}",
                })
    
    # 检查是否有超限持仓需要卖出（已在上面处理）
    # 这里只是补充警告信息
    for order in sell_orders:
        if order.get("sell_reason") == "over_limit":
            risk_compliance["warnings"].append(
                f"{order['symbol']} position exceeds limit, selling {order['quantity']} shares"
            )
    
    # 确定最终动作
    if buy_orders:
        action = "BUY"
    elif sell_orders:
        action = "SELL"
    else:
        action = "HOLD"
    
    # 生成 targets（兼容旧接口）
    targets = []
    for order in buy_orders:
        targets.append({
            "symbol": order["symbol"],
            "action": "BUY",
            "price": order["buy_price"],
            "quantity": order["quantity"],
            "value": order["total_cost"],
        })
    for order in sell_orders:
        targets.append({
            "symbol": order["symbol"],
            "action": "SELL",
            "price": order["sell_price"],
            "quantity": order["quantity"],
            "value": order["total_proceeds"],
        })
    
    # 风险合规检查
    if rview:
        control_report = rview.get("position_control_report", {})
        limit_checks = control_report.get("position_limit_checks", [])
        if limit_checks:
            risk_compliance["position_limits_ok"] = False
    
    # 生成决策理由
    buy_count = len(buy_orders)
    sell_count = len(sell_orders)
    
    if buy_count > 0 and sell_count > 0:
        rationale = f"Rebalancing: Buying {buy_count} stocks, Selling {sell_count} positions; stance={final_stance}, VIX risk={vix_risk:.1f}"
    elif buy_count > 0:
        rationale = f"Adding {buy_count} new positions; stance={final_stance}, VIX risk={vix_risk:.1f}"
    elif sell_count > 0:
        rationale = f"Reducing {sell_count} positions; stance={final_stance}, VIX risk={vix_risk:.1f}"
    else:
        rationale = f"Maintaining positions; stance={final_stance}, VIX risk={vix_risk:.1f}"
    
    # 限制 potential_buys 数量（用于展示）
    if len(potential_buys) > 20:
        potential_buys = potential_buys[:20]

    return {
        "action": action,
        "targets": targets,
        "buy_orders": buy_orders,
        "sell_orders": sell_orders,
        "potential_buys": potential_buys,  # 潜在购买公司
        "position_adjustments": position_adjustments,  # 持仓调整建议
        "rationale": rationale,
        "stance": final_stance,
        "vix_risk": vix_risk,
        "risk_compliance": risk_compliance,
    }
