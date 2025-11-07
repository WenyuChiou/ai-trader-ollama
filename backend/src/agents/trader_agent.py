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
    *,
    max_position_per_stock: float = 0.15,  # 单股最大仓位（可配置）
    max_total_position: float = 0.80,  # 总仓位上限（可配置）
    min_position_per_stock: float = 0.03,  # 单股最小仓位（新增：允许更小的仓位）
) -> int:
    """
    计算买入数量（改进版：支持多股票分散投资，更灵活的仓位分配）
    
    改进点：
    - 支持同时持有多只股票
    - 单股仓位可以更小（最小3%），允许更多股票同时持有
    - 考虑总仓位限制，避免过度杠杆
    - 根据推荐股票数量动态调整单股仓位
    
    参数:
    - max_position_per_stock: 单股最大仓位（默认15%，但可以根据推荐股票数量调整）
    - max_total_position: 总仓位上限（默认80%，保留20%现金）
    - min_position_per_stock: 单股最小仓位（默认3%，允许更小的仓位分散投资）
    """
    if portfolio_value <= 0 or last_price <= 0:
        return 0
    
    # 从风险报告获取推荐仓位大小
    if risk_report:
        control_report = risk_report.get("position_control_report", {})
        recommended_sizes = control_report.get("recommended_position_sizes", {})
        if symbol in recommended_sizes:
            suggested_max = recommended_sizes[symbol].get("max_pct", max_position_per_stock)
            max_position_per_stock = min(max_position_per_stock, suggested_max)
    
    # 计算当前总仓位（已持有的股票总价值占比）
    current_total_position = 0.0
    if current_positions:
        for sym, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                qty = pos_info.get("quantity", 0)
                current_price = pos_info.get("current_price", 0.0)
            else:
                qty = pos_info if isinstance(pos_info, (int, float)) else 0
                current_price = 0.0
            
            if qty > 0 and current_price > 0:
                position_value = qty * current_price
                current_total_position += position_value / portfolio_value
    
    # 动态调整单股仓位：根据推荐股票数量调整
    # 如果有更多推荐股票，单股仓位可以更小，允许分散投资
    num_recommended = len(recommended_stocks) if recommended_stocks else 1
    
    # 计算可用仓位空间
    available_position_space = max_total_position - current_total_position
    
    if available_position_space <= 0:
        # 已达到总仓位上限
        return 0
    
    # 动态调整：如果有多个推荐股票，单股仓位可以更小
    # 例如：3只股票时，每只10%；5只股票时，每只6%；10只股票时，每只5%
    if num_recommended > 1:
        # 根据推荐股票数量动态调整单股最大仓位
        # 但不超过 max_position_per_stock，也不小于 min_position_per_stock
        dynamic_max_pct = min(max_position_per_stock, available_position_space / num_recommended)
        dynamic_max_pct = max(min_position_per_stock, dynamic_max_pct)
        
        # 确保不超过可用仓位空间
        dynamic_max_pct = min(dynamic_max_pct, available_position_space)
    else:
        # 只有1只推荐股票时，可以使用更大的仓位
        dynamic_max_pct = min(max_position_per_stock, available_position_space)
    
    # 检查当前持仓
    current_symbol_position = 0.0
    if current_positions:
        pos_info = current_positions.get(symbol)
        if pos_info:
            if isinstance(pos_info, dict):
                current_qty = pos_info.get("quantity", 0)
                current_price = pos_info.get("current_price", last_price)
            else:
                current_qty = pos_info if isinstance(pos_info, (int, float)) else 0
                current_price = last_price
            
            if current_qty > 0 and current_price > 0:
                current_value = current_qty * current_price
                current_symbol_position = current_value / portfolio_value
    
    # 计算目标仓位（考虑已有持仓）
    target_position_pct = dynamic_max_pct
    if current_symbol_position >= target_position_pct:
        # 已达到目标仓位
        return 0
    
    # 计算还需要买入的仓位百分比
    remaining_position_pct = target_position_pct - current_symbol_position
    
    # 计算目标市值（但不能超过可用现金）
    target_value = portfolio_value * remaining_position_pct
    
    # 计算数量（向下取整）
    quantity = floor(target_value / last_price)
    
    # 确保不超过可用现金（如果有现金限制，这里可以进一步检查）
    # 但通常 portfolio_value 已经考虑了现金，所以这里不做额外检查
    
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
    position_config: Optional[Dict[str, float]] = None,  # 新增：仓位配置参数
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
                        current_price = last_prices[symbol]
                        # 卖出价格范围（高卖）：期望比当前价格高 0.5%-2%
                        sell_price_min = current_price * 1.005  # 至少高0.5%
                        sell_price_max = current_price * 1.02   # 最高高2%
                        sell_price = sell_price_min  # 用于计算的基准价格（保守估算）
                        sell_orders.append({
                            "symbol": symbol,
                            "sell_price": sell_price,  # 用于计算的基准价格
                            "sell_price_min": sell_price_min,  # 最低卖出价（范围下限）
                            "sell_price_max": sell_price_max,  # 最高卖出价（范围上限，高卖）
                            "quantity": sell_qty,
                            "total_proceeds": sell_price * sell_qty,  # 基于基准价格估算
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

    # 生成买入订单（改进：支持同时买入多只股票，每只股票仓位更灵活）
    if recs and portfolio_value > 0:
        # 从配置中读取仓位限制参数
        if position_config:
            max_position_per_stock = position_config.get("max_position_per_stock", 0.15)
            max_total_position = position_config.get("max_total_position", 0.80)
            min_position_per_stock = position_config.get("min_position_per_stock", 0.03)
        else:
            # 默认值
            max_position_per_stock = 0.15  # 默认单股最大15%
            max_total_position = 0.80  # 默认总仓位80%
            min_position_per_stock = 0.03  # 默认单股最小3%（允许更小的仓位）
        
        # 计算当前总仓位（用于限制买入）
        current_total_value = 0.0
        if current_positions:
            for sym, pos_info in current_positions.items():
                if isinstance(pos_info, dict):
                    qty = pos_info.get("quantity", 0)
                    current_price = pos_info.get("current_price", last_prices.get(sym, 0.0))
                else:
                    qty = pos_info if isinstance(pos_info, (int, float)) else 0
                    current_price = last_prices.get(sym, 0.0)
                
                if qty > 0 and current_price > 0:
                    current_total_value += qty * current_price
        
        # 计算可用资金（考虑总仓位限制）
        current_total_position_pct = current_total_value / portfolio_value if portfolio_value > 0 else 0.0
        available_position_pct = max_total_position - current_total_position_pct
        
        if available_position_pct <= 0:
            # 已达到总仓位上限，不买入新股票
            pass
        else:
            # 遍历所有推荐股票，计算每只股票的买入数量
            for symbol in recs:
                if symbol not in last_prices:
                    continue
                
                last_price = last_prices[symbol]
                if last_price <= 0:
                    continue
                
                # 计算买入数量（使用改进后的函数）
                quantity = _calculate_position_size(
                    symbol, 
                    recs, 
                    portfolio_value, 
                    last_price, 
                    rview, 
                    current_positions,
                    max_position_per_stock=max_position_per_stock,
                    max_total_position=max_total_position,
                    min_position_per_stock=min_position_per_stock,
                )
                
                if quantity > 0:
                    # 买入价格范围（更激进的限价策略，提高成交率）
                    # 使用当前价格的 99%-100% 作为范围，限价设为 99.5%（提高成交率至50%以上）
                    buy_price_max = last_price  # 最高买入价（不超过当前价格）
                    buy_price_min = last_price * 0.995  # 最低买入价（仅比当前价格低0.5%，提高成交率）
                    buy_price = buy_price_max  # 默认使用最高价（保守，确保能买到）
                    total_cost = buy_price * quantity
                    
                    # 检查可用资金（这里检查现金是否足够）
                    # 注意：portfolio_value 是总净值，需要检查现金部分
                    # 但由于我们在 _calculate_position_size 中已经考虑了总仓位限制，
                    # 这里主要检查单笔交易是否可行
                    
                    buy_orders.append({
                        "symbol": symbol,
                        "buy_price": buy_price,  # 用于计算的基准价格
                        "buy_price_min": buy_price_min,  # 最低买入价（范围下限，低买）
                        "buy_price_max": buy_price_max,  # 最高买入价（范围上限，不超过当前价格）
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
                    current_price = last_prices[symbol]
                    # 卖出价格范围（高卖）：期望比当前价格高 0.5%-2%
                    sell_price_min = current_price * 1.005  # 至少高0.5%
                    sell_price_max = current_price * 1.02   # 最高高2%
                    sell_price = sell_price_min  # 用于计算的基准价格（保守估算）
                    sell_orders.append({
                        "symbol": symbol,
                        "sell_price": sell_price,  # 用于计算的基准价格
                        "sell_price_min": sell_price_min,  # 最低卖出价（范围下限）
                        "sell_price_max": sell_price_max,  # 最高卖出价（范围上限，高卖）
                        "quantity": sell_qty,
                        "total_proceeds": sell_price * sell_qty,  # 基于基准价格估算
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
    
    # 生成决策理由（包含coordinator summary）
    # 从convo中提取coordinator summary
    coordinator_summary = ""
    if convo and isinstance(convo, dict):
        # 尝试从convo中直接获取coordinator_summary
        coordinator = convo.get("coordinator_summary", {})
        if isinstance(coordinator, dict):
            summary_text = coordinator.get("summary", "")
            if summary_text and len(summary_text.strip()) > 20:  # 确保summary有意义
                coordinator_summary = summary_text[:200]  # 限制长度
                print(f"[TRADER] Found coordinator summary from convo.coordinator_summary ({len(coordinator_summary)} chars)")
        # 如果直接获取失败，尝试从discussion中获取
        if not coordinator_summary:
            discussion = convo.get("discussion", {})
            if isinstance(discussion, dict):
                coordinator = discussion.get("coordinator_summary", {})
                if isinstance(coordinator, dict):
                    summary_text = coordinator.get("summary", "")
                    if summary_text and len(summary_text.strip()) > 20:
                        coordinator_summary = summary_text[:200]
                        print(f"[TRADER] Found coordinator summary from convo.discussion.coordinator_summary")
        # 如果还是没有，尝试从discussion_history中提取
        if not coordinator_summary:
            discussion_history = convo.get("discussion_history", [])
            for entry in discussion_history:
                if entry.get("analyst") == "Discussion Coordinator":
                    analysis = entry.get("analysis", "")
                    if analysis and len(analysis.strip()) > 20:
                        coordinator_summary = analysis[:200]
                        print(f"[TRADER] Found coordinator summary from discussion_history")
                        break
        if not coordinator_summary:
            print(f"[TRADER] WARNING: Could not find coordinator summary in convo")
            print(f"[TRADER] convo keys: {list(convo.keys())[:10]}")
            if "coordinator_summary" in convo:
                print(f"[TRADER] coordinator_summary type: {type(convo.get('coordinator_summary'))}")
                print(f"[TRADER] coordinator_summary content: {str(convo.get('coordinator_summary'))[:200]}")
    
    # 构建rationale
    base_rationale = ""
    if buy_orders:
        buy_symbols = [o["symbol"] for o in buy_orders]
        base_rationale = f"Buying {len(buy_orders)} stocks ({', '.join(buy_symbols[:5])}{'...' if len(buy_symbols) > 5 else ''}); stance={final_stance}, VIX risk={vix_risk:.1f}"
    elif sell_orders:
        sell_symbols = [o["symbol"] for o in sell_orders]
        base_rationale = f"Selling {len(sell_orders)} stocks ({', '.join(sell_symbols[:5])}{'...' if len(sell_symbols) > 5 else ''}); stance={final_stance}, VIX risk={vix_risk:.1f}"
    else:
        base_rationale = f"No strong consensus; stance={final_stance}, VIX risk={vix_risk:.1f}"
    
    # 如果有coordinator summary，添加到rationale
    if coordinator_summary:
        rationale = f"{base_rationale}. Analysis: {coordinator_summary}"
    else:
        rationale = base_rationale

    # 严格JSON格式输出（交易决策必须严格遵守JSON格式，因为交易系统根据这个判断）
    # 确保所有字段都是JSON可序列化的类型
    decision = {
        "action": str(action),  # 确保是字符串
        "targets": list(targets) if targets else [],  # 确保是列表
        "buy_orders": [
            {
                "symbol": str(order.get("symbol", "")),
                "buy_price": float(order.get("buy_price", 0.0)),
                "buy_price_min": float(order.get("buy_price_min", 0.0)),
                "buy_price_max": float(order.get("buy_price_max", 0.0)),
                "quantity": int(order.get("quantity", 0)),
                "total_cost": float(order.get("total_cost", 0.0)),
            }
            for order in buy_orders
        ],
        "sell_orders": [
            {
                "symbol": str(order.get("symbol", "")),
                "sell_price": float(order.get("sell_price", 0.0)),
                "sell_price_min": float(order.get("sell_price_min", 0.0)),
                "sell_price_max": float(order.get("sell_price_max", 0.0)),
                "quantity": int(order.get("quantity", 0)),
                "total_proceeds": float(order.get("total_proceeds", 0.0)),
            }
            for order in sell_orders
        ],
        "rationale": str(rationale),  # 确保是字符串
        "stance": str(final_stance),  # 确保是字符串
        "vix_risk": float(vix_risk),  # 确保是数字
        "risk_compliance": {
            "position_limits_ok": bool(risk_compliance.get("position_limits_ok", True)),
            "diversification_ok": bool(risk_compliance.get("diversification_ok", True)),
            "warnings": [str(w) for w in risk_compliance.get("warnings", [])],  # 确保是字符串列表
        },
    }
    
    # 验证JSON可序列化
    import json
    try:
        json.dumps(decision)
    except (TypeError, ValueError) as e:
        print(f"[TRADER] WARNING: Decision contains non-JSON-serializable data: {e}")
        # 如果序列化失败，返回最小化版本
        decision = {
            "action": "HOLD",
            "targets": [],
            "buy_orders": [],
            "sell_orders": [],
            "rationale": f"Error: {str(e)}",
            "stance": "neutral",
            "vix_risk": 0.0,
            "risk_compliance": {"position_limits_ok": False, "diversification_ok": False, "warnings": [str(e)]},
        }
    
    return decision
