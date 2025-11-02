from __future__ import annotations
from typing import Dict, Any, Optional, List
from math import floor


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
    
    # 更激进：单股最大20%（从15%提高到20%）
    max_pct = 0.20
    
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
) -> int:
    """
    计算卖出数量（基于风险控管建议）
    - 如果超过限制，减少到目标仓位
    """
    if current_qty <= 0 or last_price <= 0:
        return 0
    
    # 检查是否需要减仓
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
                    return min(sell_qty, current_qty)
    
    return 0


def run_trader(
    market: Dict[str, Any],
    mview: Dict[str, Any],
    rview: Dict[str, Any] | None,
    convo: Dict[str, Any],
    last_prices: Dict[str, float],
    current_positions: Optional[Dict[str, Any]] = None,
    portfolio_value: Optional[float] = None,
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
    
    输出:
    - action: BUY / SELL / HOLD
    - buy_orders: 买进订单列表（包含 symbol, buy_price, quantity, total_cost）
    - sell_orders: 卖出订单列表（包含 symbol, sell_price, quantity, total_proceeds）
    - rationale: 决策理由
    - risk_compliance: 风险合规检查
    """
    vix = (mview.get("vix") or {}) if isinstance(mview, dict) else {}
    vix_risk = float(vix.get("risk_score", 4.0))
    # 更激进的阈值：降低 VIX 风险阈值，提高交易频率
    stance = "cautious" if vix_risk > 7.5 else mview.get("market_sentiment", "neutral")  # 从6.0提高到7.5

    recs = mview.get("recommended_stocks", []) if isinstance(mview, dict) else []
    final_stance = (convo or {}).get("final_stance", "neutral")
    
    # 更激进：除了 Market Analyst 推荐的股票，还考虑所有 signal_score > 0 的股票
    stocks = mview.get("stocks", {}) if isinstance(mview, dict) else {}
    all_symbols = list(stocks.keys())
    
    # 从所有股票中筛选出信号良好的股票（不依赖 Market Analyst 的推荐）
    additional_buys = []
    for symbol, stock_data in stocks.items():
        if isinstance(stock_data, dict):
            try:
                signal_score = float(stock_data.get("signal_score", 0))
                # 更激进：signal_score > 2.0 就考虑买入（原来可能需要 uptrend + vix_risk <= 6.0）
                if signal_score > 2.0 and symbol not in recs:
                    additional_buys.append(symbol)
            except Exception:
                pass
    
    # 合并推荐列表
    if additional_buys:
        recs = list(set(recs + additional_buys))  # 去重
    
    # 默认组合净值（如果没有提供）
    if portfolio_value is None:
        portfolio_value = 10000.0  # 默认初始净值
    
    # 默认当前持仓（如果没有提供）
    if current_positions is None:
        current_positions = {}
    
    buy_orders: List[Dict[str, Any]] = []
    sell_orders: List[Dict[str, Any]] = []
    
    # 风险合规检查
    risk_compliance = {
        "position_limits_ok": True,
        "diversification_ok": True,
        "warnings": [],
    }

    # 更激进的阈值：只有在 VIX 非常高时才保守处理
    # 从 6.0 提高到 8.0，允许在中等风险时也交易
    if vix_risk > 8.0 or final_stance == "bearish":  # 移除 "cautious"，允许 cautious 时也能买入
        # 检查是否需要减仓
        if current_positions and rview:
            for symbol, pos_info in current_positions.items():
                if isinstance(pos_info, dict):
                    qty = pos_info.get("quantity", 0)
                else:
                    qty = pos_info if isinstance(pos_info, (int, float)) else 0
                
                if qty > 0 and symbol in last_prices:
                    sell_qty = _calculate_sell_size(
                        symbol, qty, portfolio_value, last_prices[symbol], rview
                    )
                    if sell_qty > 0:
                        sell_price = last_prices[symbol]
                        sell_orders.append({
                            "symbol": symbol,
                            "sell_price": sell_price,
                            "quantity": sell_qty,
                            "total_proceeds": sell_price * sell_qty,
                        })
        
        action = "SELL" if sell_orders else "HOLD"
        return {
            "action": action,
            "targets": [],
            "buy_orders": buy_orders,
            "sell_orders": sell_orders,
            "rationale": f"Hold/Sell due to VIX risk={vix_risk:.1f} / news stance={final_stance}",
            "stance": final_stance,
            "vix_risk": vix_risk,
            "risk_compliance": risk_compliance,
        }

    # 生成买入订单
    if recs and portfolio_value > 0:
        for symbol in recs:
            if symbol not in last_prices:
                continue
            
            last_price = last_prices[symbol]
            if last_price <= 0:
                continue
            
            # 计算买入数量
            quantity = _calculate_position_size(
                symbol, recs, portfolio_value, last_price, rview, current_positions
            )
            
            if quantity > 0:
                buy_price = last_price
                total_cost = buy_price * quantity
                
                buy_orders.append({
                    "symbol": symbol,
                    "buy_price": buy_price,
                    "quantity": quantity,
                    "total_cost": total_cost,
                })
    
    # 检查是否有超限持仓需要卖出
    if current_positions and rview:
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                qty = pos_info.get("quantity", 0)
            else:
                qty = pos_info if isinstance(pos_info, (int, float)) else 0
            
            if qty > 0 and symbol in last_prices:
                sell_qty = _calculate_sell_size(
                    symbol, qty, portfolio_value, last_prices[symbol], rview
                )
                if sell_qty > 0:
                    sell_price = last_prices[symbol]
                    sell_orders.append({
                        "symbol": symbol,
                        "sell_price": sell_price,
                        "quantity": sell_qty,
                        "total_proceeds": sell_price * sell_qty,
                    })
                    risk_compliance["warnings"].append(
                        f"{symbol} position exceeds limit, recommend selling {sell_qty} shares"
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
    
    rationale = f"TA + news consensus supports entry; stance={final_stance}, VIX risk={vix_risk:.1f}"
    if not buy_orders and not sell_orders:
        rationale = f"No strong consensus; stance={final_stance}, VIX risk={vix_risk:.1f}"

    return {
        "action": action,
        "targets": targets,
        "buy_orders": buy_orders,
        "sell_orders": sell_orders,
        "rationale": rationale,
        "stance": final_stance,
        "vix_risk": vix_risk,
        "risk_compliance": risk_compliance,
    }
