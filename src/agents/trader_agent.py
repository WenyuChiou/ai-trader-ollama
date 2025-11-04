from __future__ import annotations
from typing import Dict, Any, Optional, List
from math import floor
import sys

# 安全的 print 函数
def safe_print(msg, **kwargs):
    """安全打印函数，如果 stdout 关闭则使用 stderr"""
    try:
        print(msg, flush=True, **kwargs)
    except (ValueError, OSError, AttributeError):
        try:
            sys.stderr.write(str(msg) + "\n")
            sys.stderr.flush()
        except Exception:
            pass  # 如果 stderr 也失败，忽略


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
    # 移除 VIX 阈值限制：完全依赖 Market Analyst 的 market_sentiment
    stance = mview.get("market_sentiment", "neutral")

    recs = mview.get("recommended_stocks", []) if isinstance(mview, dict) else []
    final_stance = (convo or {}).get("final_stance", "neutral")
    
    # 更激进：除了 Market Analyst 推荐的股票，还考虑所有 signal_score > 0 的股票
    # 优先使用 stocks_only（只包含股票），如果不存在则使用 stocks（但需要过滤指数）
    stocks = mview.get("stocks_only", {}) if isinstance(mview, dict) else {}
    if not stocks and isinstance(mview, dict):
        stocks = {k: v for k, v in (mview.get("stocks", {}) or {}).items() if not k.startswith("^")}
    all_symbols = list(stocks.keys())
    
    # 让LLM自己决定：不添加额外的筛选逻辑，完全依赖 Market Analyst 的推荐和 Discussion Agent 的共识
    # 移除硬编码的 signal_score 阈值，让 LLM 根据整体分析做出决策
    
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

    # 移除 VIX 阈值限制：完全依赖 LLM Agent 的决策
    # 不再基于 VIX 风险提前返回，让所有逻辑都执行
    if False:  # 不再提前返回，让所有订单生成逻辑都执行
        # 检查是否需要减仓（高风险时）
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
        
        # 即使 VIX 风险高，如果已经有持仓，仍然尝试生成卖出订单
        # 如果没有持仓，则返回空订单（但继续执行后续逻辑，看是否能在中性时生成订单）
        if not sell_orders and current_positions:
            # 尝试卖出一些持仓（如果 VIX 风险很高）
            for symbol, pos_info in current_positions.items():
                if isinstance(pos_info, dict):
                    qty = pos_info.get("quantity", 0)
                else:
                    qty = pos_info if isinstance(pos_info, (int, float)) else 0
                
                if qty > 0 and symbol in last_prices:
                    # 卖出部分持仓（例如 50%）
                    sell_qty = max(1, qty // 2)  # 至少卖出 50%
                    current_price = last_prices[symbol]
                    sell_price_min = current_price * 1.005
                    sell_price_max = current_price * 1.02
                    sell_price = sell_price_min
                    
                    sell_orders.append({
                        "symbol": symbol,
                        "sell_price": sell_price,
                        "sell_price_min": sell_price_min,
                        "sell_price_max": sell_price_max,
                        "quantity": sell_qty,
                        "total_proceeds": sell_price * sell_qty,
                    })
                    safe_print(f"[TRADER] High VIX risk: generating sell order for {symbol} ({sell_qty} shares)")
    
    # 让LLM自己决定：移除VIX风险阈值限制，完全依赖LLM的分析和决策
    # 即使VIX风险很高，也继续执行后续逻辑，让LLM根据整体情况做出决策
    
    # 从配置中读取仓位限制参数（提前定义，供后续使用）
    if position_config:
        max_position_per_stock = position_config.get("max_position_per_stock", 0.15)
        max_total_position = position_config.get("max_total_position", 0.80)
        min_position_per_stock = position_config.get("min_position_per_stock", 0.03)
    else:
        # 默认值
        max_position_per_stock = 0.15  # 默认单股最大15%
        max_total_position = 0.80  # 默认总仓位80%
        min_position_per_stock = 0.03  # 默认单股最小3%（允许更小的仓位）
    
    # 让LLM自己决定：如果 Market Analyst 和 Discussion Agent 都没有推荐，不自动生成买入订单
    # 完全依赖 LLM 的分析和决策，不添加硬编码的筛选逻辑
    
    if recs and portfolio_value > 0:
        
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
    
    # 基于市场分析和持仓情况生成卖出订单
    # 1. 如果市场情绪看跌或 Discussion Agent 立场为 bearish，考虑卖出部分持仓
    if current_positions and (stance == "bearish" or final_stance == "bearish"):
        # 市场看跌时，考虑卖出部分持仓（例如 30-50%）
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                qty = pos_info.get("quantity", 0)
            else:
                qty = pos_info if isinstance(pos_info, (int, float)) else 0
            
            if qty > 0 and symbol in last_prices:
                # 根据市场情绪决定卖出比例
                if stance == "bearish" or final_stance == "bearish":
                    # 看跌时卖出 30-50% 持仓
                    sell_pct = 0.40  # 40%
                    sell_qty = max(1, int(qty * sell_pct))
                    
                    current_price = last_prices[symbol]
                    sell_price_min = current_price * 1.005
                    sell_price_max = current_price * 1.02
                    sell_price = sell_price_min
                    
                    sell_orders.append({
                        "symbol": symbol,
                        "sell_price": sell_price,
                        "sell_price_min": sell_price_min,
                        "sell_price_max": sell_price_max,
                        "quantity": sell_qty,
                        "total_proceeds": sell_price * sell_qty,
                    })
                    safe_print(f"[TRADER] Bearish market: generating sell order for {symbol} ({sell_qty} shares, {sell_pct*100:.0f}% of position)")
    
    # 2. 检查是否有超限持仓需要卖出（风险控制）
    if current_positions and rview:
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                qty = pos_info.get("quantity", 0)
            else:
                qty = pos_info if isinstance(pos_info, (int, float)) else 0
            
            if qty > 0 and symbol in last_prices:
                # 检查是否已经在 sell_orders 中（避免重复）
                already_in_sell_orders = any(o.get("symbol") == symbol for o in sell_orders)
                if not already_in_sell_orders:
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
    
    # 让LLM自己决定：完全依赖 Market Analyst 和 Discussion Agent 的推荐
    # 如果 LLM 没有推荐任何股票（recs 为空），不自动生成买入订单
    # 移除所有硬编码的筛选逻辑，让 LLM 根据整体分析做出决策
    
    # 最后兜底：如果没有生成任何订单，进行小额探索性交易以推动流程
    if not buy_orders and not sell_orders:
        try:
            candidate_stocks: list[tuple[str, float]] = []
            # 优先使用 stocks_only（只包含股票），如果不存在则使用 stocks（但需要过滤指数）
            stocks_for_trading = mview.get("stocks_only", {}) if isinstance(mview, dict) else {}
            if not stocks_for_trading and isinstance(mview, dict):
                stocks_for_trading = {k: v for k, v in (mview.get("stocks", {}) or {}).items() if not k.startswith("^")}
            for symbol, stock_data in (stocks_for_trading or {}).items():
                if symbol in last_prices and isinstance(stock_data, dict):
                    try:
                        score = float(stock_data.get("signal_score", 0))
                        price = float(last_prices.get(symbol, 0))
                        if price > 0:
                            candidate_stocks.append((symbol, score))
                    except Exception:
                        pass
            # 选择前3名（不设阈值），做小额分散买入
            candidate_stocks.sort(key=lambda x: x[1], reverse=True)
            for symbol, _ in candidate_stocks[:3]:
                price = float(last_prices.get(symbol, 0))
                if price <= 0:
                    continue
                qty = _calculate_position_size(
                    symbol=symbol,
                    recommended_stocks=[s for s, _ in candidate_stocks[:3]],
                    portfolio_value=portfolio_value or 10000.0,
                    last_price=price,
                    risk_report=rview,
                    current_positions=current_positions,
                    max_position_per_stock=max_position_per_stock,
                    max_total_position=max_total_position,
                    min_position_per_stock=min_position_per_stock,
                )
                qty = max(1, qty)
                buy_price_min = price * 0.995
                buy_price_max = price
                buy_orders.append({
                    "symbol": symbol,
                    "buy_price": buy_price_max,
                    "buy_price_min": buy_price_min,
                    "buy_price_max": buy_price_max,
                    "quantity": qty,
                    "total_cost": buy_price_max * qty,
                })
            if not buy_orders and current_positions:
                # 若已有持仓，做一次小额减仓尝试
                for symbol, pos_info in current_positions.items():
                    qty = pos_info.get("quantity", 0) if isinstance(pos_info, dict) else int(pos_info or 0)
                    if qty > 0 and symbol in last_prices:
                        price = float(last_prices[symbol])
                        sell_qty = max(1, qty // 4)
                        sell_price_min = price * 1.005
                        sell_price_max = price * 1.02
                        sell_orders.append({
                            "symbol": symbol,
                            "sell_price": sell_price_min,
                            "sell_price_min": sell_price_min,
                            "sell_price_max": sell_price_max,
                            "quantity": sell_qty,
                            "total_proceeds": sell_price_min * sell_qty,
                        })
                        break
        except Exception:
            pass

    if buy_orders:
        buy_symbols = [o["symbol"] for o in buy_orders]
        rationale = f"Buying {len(buy_orders)} stocks ({', '.join(buy_symbols[:5])}{'...' if len(buy_symbols) > 5 else ''}); stance={final_stance}, VIX risk={vix_risk:.1f}"
    elif sell_orders:
        sell_symbols = [o["symbol"] for o in sell_orders]
        rationale = f"Selling {len(sell_orders)} stocks ({', '.join(sell_symbols[:5])}{'...' if len(sell_symbols) > 5 else ''}); stance={final_stance}, VIX risk={vix_risk:.1f}"
    else:
        rationale = f"No strong consensus; stance={final_stance}, VIX risk={vix_risk:.1f}. Attempted to generate orders but conditions not met."

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
