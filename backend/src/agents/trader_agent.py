from __future__ import annotations
from typing import Dict, Any, Optional, List
from math import floor
import json
from ..utils.json_serializer import make_json_serializable, safe_json_dumps


def _calculate_position_size(
    symbol: str,
    recommended_stocks: List[str],
    portfolio_value: float,
    last_price: float,
    risk_report: Optional[Dict[str, Any]] = None,
    current_positions: Optional[Dict[str, Any]] = None,
    *,
    max_position_per_stock: Optional[float] = None,  # 单股最大仓位（可选，None=无限制）
    max_total_position: Optional[float] = None,  # 总仓位上限（可选，None=无限制）
    min_position_per_stock: Optional[float] = None,  # 单股最小仓位（可选，None=无限制）
    available_cash: Optional[float] = None,  # 可用现金（如果提供，用于限制买入数量）
) -> int:
    """
    计算买入数量（改进版：支持多股票分散投资，更灵活的仓位分配）
    
    改进点：
    - 支持同时持有多只股票
    - 仓位限制为可选（如果未设置，agent 完全自由决定）
    - 根据推荐股票数量、VIX 风险、信号强度等因素动态调整单股仓位
    - 如果设置了限制，则遵守限制；否则 agent 自由决定
    
    参数:
    - max_position_per_stock: 单股最大仓位（可选，None=无限制，agent 自由决定）
    - max_total_position: 总仓位上限（可选，None=无限制，agent 自由决定）
    - min_position_per_stock: 单股最小仓位（可选，None=无限制，agent 自由决定）
    """
    if portfolio_value <= 0 or last_price <= 0:
        return 0
    
    # NEW: If no limits are set, agent has complete freedom
    # Agent will decide based on VIX risk, signal strength, diversification needs, etc.
    
    # 从风险报告获取推荐仓位大小（如果有限制，则考虑风险报告的建议）
    if risk_report and max_position_per_stock is not None:
        control_report = risk_report.get("position_control_report", {})
        recommended_sizes = control_report.get("recommended_position_sizes", {})
        if symbol in recommended_sizes:
            size_info = recommended_sizes[symbol]
            if isinstance(size_info, dict):
                suggested_max = size_info.get("max_pct", max_position_per_stock)
                max_position_per_stock = min(max_position_per_stock, suggested_max)
            elif isinstance(size_info, (int, float)):
                suggested_max = float(size_info)
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
    
    # NEW: Agent decision logic - if no limits, agent decides freely
    num_recommended = len(recommended_stocks) if recommended_stocks else 1
    
    # If max_total_position is set, check if we've reached it
    if max_total_position is not None:
        available_position_space = max_total_position - current_total_position
        if available_position_space <= 0:
            # 已达到总仓位上限（硬限制）
            return 0
    else:
        # No total position limit - agent can use all available cash
        available_position_space = 1.0  # 100% of portfolio (limited only by cash)
    
    # Agent 决策逻辑：根据推荐股票数量、VIX 风险等因素动态调整单股仓位
    # If no limits are set, agent has complete freedom to decide
    if max_position_per_stock is None:
        # No per-stock limit - agent decides based on:
        # - VIX risk (high VIX = smaller positions, low VIX = larger positions)
        # - Number of recommended stocks (more stocks = smaller per-stock positions)
        # - Signal strength (strong signals = larger positions)
        # - Diversification needs
        
        # Default behavior: distribute based on number of stocks
        # High VIX (7-10): 5-8% per stock
        # Medium VIX (4-6): 8-12% per stock
        # Low VIX (0-3): 10-15% per stock
        # Many stocks (>10): smaller positions (5-8%)
        # Few stocks (<5): larger positions (12-15%)
        
        # Get VIX risk score if available
        # CRITICAL FIX: risk_report contains vix_risk_score directly, not nested in vix.risk_score
        vix_risk_score = None
        if risk_report:
            # Priority 1: Direct vix_risk_score field (from Risk Analyst)
            vix_risk_score = risk_report.get("vix_risk_score")
            # Priority 2: Fallback to nested vix.risk_score (for backward compatibility)
            if vix_risk_score is None:
                vix_info = risk_report.get("vix", {})
                if isinstance(vix_info, dict):
                    vix_risk_score = vix_info.get("risk_score")
        
        # Determine base position size based on VIX and number of stocks
        if vix_risk_score is not None:
            if vix_risk_score >= 7:  # High risk
                base_pct = 0.06  # 6% base (5-8% range)
            elif vix_risk_score >= 4:  # Medium risk
                base_pct = 0.10  # 10% base (8-12% range)
            else:  # Low risk
                base_pct = 0.12  # 12% base (10-15% range)
        else:
            base_pct = 0.10  # Default 10%
        
        # Adjust based on number of recommended stocks
        if num_recommended > 10:
            dynamic_max_pct = max(0.05, base_pct * 0.7)  # Smaller positions for many stocks
        elif num_recommended > 5:
            dynamic_max_pct = base_pct  # Use base
        else:
            dynamic_max_pct = min(0.15, base_pct * 1.2)  # Larger positions for few stocks
        
        # Ensure we don't exceed available space
        dynamic_max_pct = min(dynamic_max_pct, available_position_space)
    else:
        # Limits are set - respect them
        if num_recommended > 1:
            dynamic_max_pct = min(max_position_per_stock, available_position_space / num_recommended)
            if min_position_per_stock is not None:
                dynamic_max_pct = max(min_position_per_stock, dynamic_max_pct)
            dynamic_max_pct = min(dynamic_max_pct, available_position_space)
        else:
            dynamic_max_pct = min(max_position_per_stock, available_position_space)
    
    # 检查当前持仓
    current_symbol_position = 0.0
    current_qty = 0
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
                print(f"[TRADER] {symbol}: Already has {current_qty} shares @ ${current_price:.2f}, position_pct={current_symbol_position:.2%}")
    
    # 计算目标仓位（考虑已有持仓）
    # If max_position_per_stock is set, respect it; otherwise agent decides freely
    if max_position_per_stock is not None:
        target_position_pct = min(dynamic_max_pct, max_position_per_stock)
        if current_symbol_position >= target_position_pct:
            print(f"[TRADER] {symbol}: Skipping - already at target position (current={current_symbol_position:.2%}, target={target_position_pct:.2%})")
            return 0
        
        remaining_position_pct = target_position_pct - current_symbol_position
        # Ensure we don't exceed the limit
        if current_symbol_position + remaining_position_pct > max_position_per_stock:
            remaining_position_pct = max(0, max_position_per_stock - current_symbol_position)
            print(f"[TRADER] {symbol}: Capped position to {max_position_per_stock:.1%} (limit, current={current_symbol_position:.2%})")
    else:
        # No limit - agent decides freely
        target_position_pct = dynamic_max_pct
        if current_symbol_position >= target_position_pct:
            print(f"[TRADER] {symbol}: Skipping - already at target position (current={current_symbol_position:.2%}, target={target_position_pct:.2%})")
            return 0
        
        remaining_position_pct = target_position_pct - current_symbol_position
    
    if current_qty > 0:
        print(f"[TRADER] {symbol}: Current position={current_symbol_position:.2%}, target={target_position_pct:.2%}, remaining={remaining_position_pct:.2%}")
    
    # 计算目标市值（但不能超过可用现金）
    target_value = portfolio_value * remaining_position_pct
    
    # CRITICAL: 如果提供了可用现金，确保不超过可用现金
    # CRITICAL FIX: 如果可用现金为0或负数，直接返回0，不生成订单
    if available_cash is not None:
        if available_cash <= 0:
            print(f"[TRADER] Skipping {symbol}: no available cash (available_cash=${available_cash:.2f})")
            return 0
        # 限制目标市值不超过可用现金
        target_value = min(target_value, available_cash)
        if target_value <= 0:
            print(f"[TRADER] Skipping {symbol}: target value <= 0 after cash limit (available_cash=${available_cash:.2f})")
            return 0
    
    # 计算数量（向下取整）
    quantity = floor(target_value / last_price)
    
    # CRITICAL FIX: 确保至少能买1股（如果价格合理且仓位百分比足够）
    # 但必须确保有足够的可用现金
    if quantity == 0 and remaining_position_pct > 0:
        # 检查1股的价值是否在合理范围内（不超过目标仓位的150%）
        one_share_value = last_price / portfolio_value if portfolio_value > 0 else 0
        if one_share_value <= remaining_position_pct * 1.5:
            # CRITICAL FIX: 如果提供了可用现金，必须确保1股的价格不超过可用现金
            if available_cash is None:
                quantity = 1
                print(f"[TRADER] Ensuring minimum 1 share for {symbol} (position_pct={remaining_position_pct:.2%}, one_share_pct={one_share_value:.2%}, no cash limit)")
            elif last_price <= available_cash and available_cash > 0:
                quantity = 1
                print(f"[TRADER] Ensuring minimum 1 share for {symbol} (position_pct={remaining_position_pct:.2%}, one_share_pct={one_share_value:.2%}, available_cash=${available_cash:.2f})")
            else:
                print(f"[TRADER] Cannot buy 1 share of {symbol}: price=${last_price:.2f} > available_cash=${available_cash:.2f}")
    
    # 最终检查：如果提供了可用现金，确保总成本不超过可用现金
    if available_cash is not None and quantity > 0:
        total_cost = quantity * last_price
        if total_cost > available_cash:
            # 减少数量以匹配可用现金
            quantity = floor(available_cash / last_price)
            if quantity <= 0:
                print(f"[TRADER] Skipping {symbol}: insufficient cash (need ${total_cost:.2f}, available ${available_cash:.2f})")
                return 0
            print(f"[TRADER] Reduced {symbol} quantity to {quantity} due to cash limit (available ${available_cash:.2f})")
    
    return max(0, quantity)


def _calculate_sell_size(
    symbol: str,
    current_qty: int,
    portfolio_value: float,
    last_price: float,
    risk_report: Optional[Dict[str, Any]] = None,
    current_positions: Optional[Dict[str, Any]] = None,
) -> int:
    """
    计算卖出数量（基于风险控管建议）
    - 如果超过限制，减少到目标仓位
    - 如果仓位数量超过max_positions，卖出部分仓位
    """
    if current_qty <= 0 or last_price <= 0:
        return 0
    
    # 检查是否需要减仓
    if risk_report:
        control_report = risk_report.get("position_control_report", {})
        limit_checks = control_report.get("position_limit_checks", [])
        max_positions = control_report.get("max_positions", 10)
        
        # Check if position count exceeds limit
        if current_positions and len(current_positions) > max_positions:
            # Calculate how many positions to sell to get back to limit
            excess_positions = len(current_positions) - max_positions
            # Sell a portion of this position (at least 1 share, but proportional to excess)
            # If we have 11 positions and limit is 10, we need to reduce by 1 position
            # So we should sell this entire position (or a significant portion)
            sell_qty = max(1, floor(current_qty * (excess_positions / len(current_positions))))
            return min(sell_qty, current_qty)
        
        # Check per-stock exposure limits
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
    available_cash: Optional[float] = None,  # 新增：可用现金（如果提供，用于限制买入）
    is_market_open: bool = True,  # CRITICAL: 市场状态（True=市场开放可以交易，False=市场关闭只能评估）
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
    - is_market_open: 市场状态（True=市场开放可以交易，False=市场关闭只能评估）
    
    输出:
    - action: BUY / SELL / HOLD
    - buy_orders: 买进订单列表（包含 symbol, buy_price, quantity, total_cost）
    - sell_orders: 卖出订单列表（包含 symbol, sell_price, quantity, total_proceeds）
    - rationale: 决策理由
    - risk_compliance: 风险合规检查
    
    重要说明：
    - 市场开放时（is_market_open=True）：可以生成买卖订单并执行交易
    - 市场关闭时（is_market_open=False）：只能进行评估和分析，不能生成任何订单（buy_orders和sell_orders都应该是空的）
    - 系统采用市价交易，所有订单应该立即成交，不应该有PENDING状态
    """
    # CRITICAL: 首先提取基本变量（用于市场关闭时的分析说明）
    # 这些变量需要在市场状态检查之前定义，以便在市场关闭时也能使用
    final_stance = "NEUTRAL"
    vix_risk = 4.0
    if convo and isinstance(convo, dict):
        stance = convo.get("stance", "")
        if stance and isinstance(stance, str):
            final_stance = stance.upper()
        vix_risk_val = convo.get("vix_risk")
        if vix_risk_val is not None:
            try:
                vix_risk = float(vix_risk_val)
            except (ValueError, TypeError):
                pass
    
    # CRITICAL: 市场关闭时，不生成任何订单（只能评估和分析）
    # 系统采用市价交易，市场关闭时不应该有订单
    # CRITICAL FIX: 将市场状态检查移到最前面，在任何订单生成逻辑之前
    # 确保即使后续代码有bug，也不会在市场关闭时生成订单
    # 这是第一道防线，必须最先执行
    print(f"[TRADER] ===== MARKET STATUS CHECK (FIRST LINE OF DEFENSE) =====")
    print(f"[TRADER] is_market_open parameter: {is_market_open} (type: {type(is_market_open)})")
    print(f"[TRADER] is_market_open == False: {is_market_open == False}")
    print(f"[TRADER] not is_market_open: {not is_market_open}")
    if not is_market_open:
        print(f"[TRADER] Market is CLOSED. Running analysis only - no trading orders will be generated.")
        print(f"[TRADER] This is expected behavior: market orders can only execute during trading hours (9:30 AM - 4:00 PM ET).")
        # 继续执行分析逻辑，但不生成订单
        # 仍然可以生成rationale和summary，说明分析结果
        
        # 提取coordinator summary（用于分析说明）
        coordinator_summary = ""
        if convo and isinstance(convo, dict):
            coordinator = convo.get("coordinator_summary", {})
            if isinstance(coordinator, dict):
                summary_text = coordinator.get("summary", "")
                if summary_text and len(summary_text.strip()) > 20:
                    coordinator_summary = summary_text
            if not coordinator_summary:
                discussion = convo.get("discussion", {})
                if isinstance(discussion, dict):
                    coordinator = discussion.get("coordinator_summary", {})
                    if isinstance(coordinator, dict):
                        summary_text = coordinator.get("summary", "")
                        if summary_text and len(summary_text.strip()) > 20:
                            coordinator_summary = summary_text
        
        # 生成分析rationale（不包含交易订单）
        rationale = f"Market is closed. Analysis completed but no trading orders generated (market orders only execute during trading hours: 9:30 AM - 4:00 PM ET). Market stance: {final_stance}, VIX risk: {vix_risk:.1f}"
        if coordinator_summary:
            # CRITICAL FIX: 移除5000字符限制，允许完整summary显示
            rationale += f" Analysis: {coordinator_summary}"
        
        # CRITICAL: 使用 LLM 来生成市场关闭时的分析 summary
        print(f"[TRADER] ===== CALLING LLM FOR MARKET CLOSED SUMMARY =====")
        trader_summary = None
        
        try:
            # 创建 AgentFactory 和 trader_agent
            from pathlib import Path
            from src.agents.factory import AgentFactory
            from src.agents.base import BaseAgent
            import json
            
            ROOT = Path(__file__).resolve().parents[2]
            fac = AgentFactory(ROOT / "config" / "agents.yaml")
            trader_agent: BaseAgent = fac.create("trader_agent")
            
            # 准备完整的 prompt 信息（包括持仓信息）
            positions_summary = ""
            if current_positions:
                positions_list = []
                for sym, pos_info in list(current_positions.items())[:10]:  # 最多显示10个持仓
                    if isinstance(pos_info, dict):
                        qty = pos_info.get("quantity", 0)
                        market_value = pos_info.get("market_value", 0.0)
                        unrealized_pnl = pos_info.get("unrealized_pnl", 0.0)
                        unrealized_pnl_pct = pos_info.get("unrealized_pnl_pct", 0.0)
                        positions_list.append(f"{sym}: {qty} shares, value=${market_value:.2f}, P&L=${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%)")
                if positions_list:
                    positions_summary = "\n".join(positions_list)
                else:
                    positions_summary = "No current positions"
            else:
                positions_summary = "No current positions"
            
            # 准备 prompt 变量（市场关闭时也需要传入基本数据）
            # CRITICAL FIX: Use safe_json_dumps to handle pandas Series/DataFrame
            market_closed_prompt_vars = {
                "market_status": "CLOSED",
                "quotes_snapshot": safe_json_dumps(market, indent=2, ensure_ascii=False) if market else "{}",
                "risk_result_json": safe_json_dumps(rview, indent=2, ensure_ascii=False) if rview else "{}",
                "tech_result_json": safe_json_dumps(mview, indent=2, ensure_ascii=False) if mview else "{}",
                "psych_result_json": safe_json_dumps(convo, indent=2, ensure_ascii=False) if convo else "{}",
                "consensus_json": safe_json_dumps(convo, indent=2, ensure_ascii=False) if convo else "{}",
                "positions_summary": positions_summary,
                "final_stance": final_stance,
                "vix_risk": vix_risk,
                "coordinator_summary": coordinator_summary if coordinator_summary else "No coordinator summary available",
                "portfolio_value": portfolio_value or 10000.0,
                "available_cash": available_cash or 0.0,
            }
            
            # 准备 prompt
            # CRITICAL FIX: available_cash 现在总是有值（限制在实际现金范围内），即使是在 LLM 自主模式下
            available_cash_str = f"${available_cash:,.2f}" if available_cash is not None else "$0.00"
            summary_prompt = f"""The market is currently CLOSED. Based on the following analysis, generate a concise summary (100-150 words) explaining the market assessment:

Market Status: CLOSED (no trading allowed)
Market Stance: {final_stance}
VIX Risk: {vix_risk:.1f}
Portfolio Value: ${portfolio_value:,.2f}
Available Cash: {available_cash_str}

Current Positions:
{positions_summary}

Coordinator Analysis Summary:
{coordinator_summary if coordinator_summary else "No coordinator summary available"}

Please provide a clear, professional summary that:
1. States that the market is currently CLOSED
2. Explains the completed market analysis and risk assessment
3. Mentions key factors (stance, VIX, coordinator insights)
4. If there are current positions, briefly mention their status
5. Clarifies that no trading orders can be generated when the market is closed
6. Notes that analysis continues 24/7, but trading only occurs during market hours (9:30 AM - 4:00 PM ET)

Write in natural language, approximately 100-150 words."""
            
            # CRITICAL FIX: 传入完整的 prompt_vars 让模板正常渲染，然后使用 user_append 附加 summary prompt
            llm_response = trader_agent.run(market_closed_prompt_vars, expect_json=False, user_append=summary_prompt)
            
            if llm_response and isinstance(llm_response, str) and len(llm_response.strip()) > 50:
                trader_summary = llm_response.strip()
                print(f"[TRADER] LLM generated market-closed summary ({len(trader_summary)} chars)")
            else:
                print(f"[TRADER] WARNING: LLM response invalid, using fallback")
                raise Exception("Invalid LLM response")
                
        except Exception as e:
            print(f"[TRADER] LLM summary generation failed: {e}, using fallback")
            import traceback
            traceback.print_exc()
            # Fallback: 使用基于规则的 summary
            trader_summary = f"Market is currently closed. I've completed market analysis and risk assessment. "
            trader_summary += f"Market stance is {final_stance} with VIX risk at {vix_risk:.1f}. "
            trader_summary += "No trading orders can be generated when the market is closed, as we use market orders that execute immediately during trading hours only. "
            trader_summary += "Analysis and evaluation can continue 24/7, but actual trading only occurs during market hours (9:30 AM - 4:00 PM ET, Monday-Friday, excluding holidays)."
            if coordinator_summary:
                # CRITICAL FIX: 移除5000字符限制，允许完整summary显示
                trader_summary += f" Key insights: {coordinator_summary}"
        
        # 返回分析结果（不包含任何订单）
        return {
            "action": "HOLD",
            "targets": [],
            "buy_orders": [],  # 市场关闭时，不生成任何买入订单
            "sell_orders": [],  # 市场关闭时，不生成任何卖出订单
            "rationale": rationale,
            "summary": trader_summary,
            "stance": final_stance,
            "vix_risk": vix_risk,
            "risk_compliance": {
                "position_limits_ok": True,
                "diversification_ok": True,
                "warnings": [],
            },
        }
    
    # CRITICAL: 如果执行到这里，说明 is_market_open=True（市场开放）
    # 打印接收到的仓位和现金信息（用于调试）
    print(f"[TRADER] Received parameters:")
    print(f"  - is_market_open: {is_market_open} (Market OPEN - can trade)")
    print(f"  - portfolio_value: ${portfolio_value:,.2f}")
    # CRITICAL FIX: available_cash 现在总是有值（限制在实际现金范围内），即使是在 LLM 自主模式下
    print(f"  - available_cash: ${available_cash:,.2f}" if available_cash is not None else "  - available_cash: $0.00")
    print(f"  - current_positions count: {len(current_positions) if current_positions else 0}")
    if current_positions:
        total_position_value = sum(
            pos_info.get("market_value", 0.0) if isinstance(pos_info, dict) else 0.0
            for pos_info in current_positions.values()
        )
        print(f"  - Total position value: ${total_position_value:,.2f}")
        for sym, pos_info in list(current_positions.items())[:5]:  # 只显示前5个
            if isinstance(pos_info, dict):
                qty = pos_info.get("quantity", 0)
                market_value = pos_info.get("market_value", 0.0)
                position_pct = pos_info.get("position_pct", 0.0)
                print(f"    {sym}: {qty} shares, value=${market_value:.2f} ({position_pct:.1f}%)")
    else:
        print(f"  - No current positions")
    
    buy_orders: List[Dict[str, Any]] = []
    sell_orders: List[Dict[str, Any]] = []
    
    # 风险合规检查
    risk_compliance = {
        "position_limits_ok": True,
        "diversification_ok": True,
        "warnings": [],
    }

    # 提取推荐股票列表（recs）
    # CRITICAL: 优先使用分析师推荐的股票，如果没有推荐则从 universe 的所有股票中选择
    recs = []
    if mview and isinstance(mview, dict):
        recs = mview.get("recommended_stocks", [])
        if not recs:
            recs = mview.get("recs", [])
    if not recs and convo and isinstance(convo, dict):
        recs = convo.get("recommended_stocks", [])
        if not recs:
            recs = convo.get("recs", [])
    
    # DEBUG: 打印推荐股票来源
    if recs:
        print(f"[TRADER] Using {len(recs)} recommended stocks from analysts: {recs[:10]}...")
    else:
        print(f"[TRADER] No recommended stocks from analysts, will use fallback from universe")
    
    # 反向ETF列表（用于做空市场）
    INVERSE_ETFS = ["SQQQ", "SPXU", "SH", "PSQ", "SDS", "DOG", "SOXS"]
    LEVERAGED_ETFS = ["TQQQ", "SPXL", "UPRO"]
    
    # 更激进的阈值：只有在 VIX 非常高时才保守处理
    # 从 6.0 提高到 8.0，允许在中等风险时也交易
    if vix_risk > 8.0 or final_stance == "bearish":
        # 检查推荐列表中是否有反向ETF（用于做空）
        inverse_etf_recommendations = [sym for sym in recs if sym in INVERSE_ETFS]
        
        # 如果有反向ETF推荐，允许买入（做空策略）
        if inverse_etf_recommendations:
            # 继续处理买入逻辑（包括反向ETF），见下面的买入订单生成
            pass
        else:
            # 如果没有反向ETF推荐，检查是否需要减仓
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
            
            # 如果没有反向ETF推荐且没有卖出订单，返回HOLD
            if not inverse_etf_recommendations and not sell_orders:
                action = "HOLD"
                return {
                    "action": action,
                    "targets": [],
                    "buy_orders": buy_orders,
                    "sell_orders": sell_orders,
                    "rationale": f"Hold due to VIX risk={vix_risk:.1f} / stance={final_stance} (no inverse ETF recommendations)",
                    "stance": final_stance,
                    "vix_risk": vix_risk,
                    "risk_compliance": risk_compliance,
                }

    # 生成买入订单（改进：支持同时买入多只股票，每只股票仓位更灵活）
    # 包括：普通股票、杠杆ETF（做多）、反向ETF（做空）
    # CRITICAL: 即使 recs 为空或很少，在 neutral stance 时也应该生成一些订单
    # 确保至少有一些交易决策，避免完全 HOLD
    
    # 提取 stocks 数据（用于 fallback）
    stocks = {}
    if mview and isinstance(mview, dict):
        stocks = mview.get("stocks", {})
    if not stocks and market and isinstance(market, dict):
        stocks = market.get("stocks", {})
    
    if not recs and stocks and portfolio_value > 0:
        # Fallback: 如果仍然没有推荐股票，使用所有有价格的股票（从 universe 中选择）
        # CRITICAL: 从 universe 的所有股票中选择，按 signal_score 排序
        available_stocks = [
            (s, d) for s, d in stocks.items() 
            if isinstance(d, dict) and s in last_prices and last_prices.get(s, 0) > 0
        ]
        if available_stocks:
            # 按 signal_score 排序，选择前20只（增加选择范围，让 agent 有更多选择）
            sorted_available = sorted(
                available_stocks,
                key=lambda x: float(x[1].get("signal_score", 0)) if isinstance(x[1], dict) else 0,
                reverse=True
            )
            # CRITICAL: 使用所有 universe 股票，不限制数量（让 agent 自由选择）
            # 但为了性能，限制在 top 50（如果 universe 很大）
            max_candidates = min(50, len(sorted_available))
            recs = [symbol for symbol, _ in sorted_available[:max_candidates]]
            print(f"[TRADER] Fallback: Using top {len(recs)} stocks from universe (total available: {len(available_stocks)}): {recs[:10]}...")
    
    if recs and portfolio_value > 0:
        # NEW: Position limits are OPTIONAL - only use if explicitly set in config.json
        # If not set, agent has complete freedom (no restrictions)
        max_position_per_stock = position_config.get("max_position_per_stock") if position_config else None
        max_total_position = position_config.get("max_total_position") if position_config else None
        min_position_per_stock = position_config.get("min_position_per_stock") if position_config else None
        max_positions = position_config.get("max_positions") if position_config else None
        
        # Print position limit status
        if max_position_per_stock is not None or max_total_position is not None:
            print(f"[TRADER] Position limits configured (agent will respect these):")
            if max_position_per_stock is not None:
                print(f"  - Max per stock: {max_position_per_stock:.1%}")
            if max_total_position is not None:
                print(f"  - Max total position: {max_total_position:.1%}")
            if min_position_per_stock is not None:
                print(f"  - Min per stock: {min_position_per_stock:.1%}")
            if max_positions is not None:
                print(f"  - Max positions: {max_positions}")
        else:
            print(f"[TRADER] No position limits configured - agent has complete freedom")
            print(f"  - Agent will decide position sizes based on VIX risk, signal strength, diversification needs, etc.")
        
        # CRITICAL FIX: available_cash 现在总是有值（限制在实际现金范围内），即使是在 LLM 自主模式下
        # LLM 可以自主决定如何使用现金，但不能超过实际可用的现金
        if available_cash is not None:
            print(f"  - Available cash: ${available_cash:,.2f} (hard limit, cannot exceed - LLM can decide how to use within this limit)")
        else:
            print(f"  - Available cash: $0.00 (no cash available)")
        
        # Note: We no longer limit stock count based on stance - agent decides freely
        # Agent can consider stance when making decisions, but we don't enforce limits
        
        # CRITICAL: 计算当前总仓位（用于限制买入）
        # current_positions 包含完整信息：quantity, avg_cost, current_price, market_value, unrealized_pnl, unrealized_pnl_pct, position_pct
        current_total_value = 0.0
        if current_positions:
            for sym, pos_info in current_positions.items():
                if isinstance(pos_info, dict):
                    # 优先使用 market_value（如果存在），否则计算
                    market_value = pos_info.get("market_value")
                    if market_value is None or market_value == 0:
                        qty = pos_info.get("quantity", 0)
                        current_price = pos_info.get("current_price", last_prices.get(sym, 0.0))
                        market_value = qty * current_price
                    current_total_value += market_value
                    
                    # DEBUG: 打印持仓信息（包括损益和占比）
                    unrealized_pnl = pos_info.get("unrealized_pnl", 0.0)
                    unrealized_pnl_pct = pos_info.get("unrealized_pnl_pct", 0.0)
                    position_pct = pos_info.get("position_pct", 0.0)
                    if market_value > 0:
                        print(f"[TRADER] Position {sym}: value=${market_value:.2f} ({position_pct:.1f}%), P&L=${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%)")
                else:
                    # 旧格式兼容
                    qty = pos_info if isinstance(pos_info, (int, float)) else 0
                    current_price = last_prices.get(sym, 0.0)
                    if qty > 0 and current_price > 0:
                        current_total_value += qty * current_price
        
        # 计算可用资金（考虑总仓位限制）
        current_total_position_pct = current_total_value / portfolio_value if portfolio_value > 0 else 0.0
        # CRITICAL FIX: 如果 max_total_position 是 None（没有限制），使用 1.0 (100%) 作为可用仓位空间
        if max_total_position is not None:
            available_position_pct = max_total_position - current_total_position_pct
        else:
            # 没有总仓位限制，agent 可以使用所有可用现金（100% 仓位空间）
            available_position_pct = 1.0  # 100% of portfolio (limited only by cash)
        
        # CRITICAL: 跟踪累计使用的现金，确保总订单金额不超过可用现金
        # CRITICAL FIX: available_cash 现在总是有值（限制在实际现金范围内），即使是在 LLM 自主模式下
        # LLM 可以自主决定如何使用现金，但不能超过实际可用的现金
        remaining_cash = available_cash if available_cash is not None else 0.0
        
        # CRITICAL: 打印开始生成买入订单时的状态（用于调试）
        print(f"[TRADER] Starting buy order generation:")
        print(f"  - Available cash: ${remaining_cash:,.2f} (LLM can decide how to use, but cannot exceed this amount)")
        print(f"  - Current total position value: ${current_total_value:,.2f} ({current_total_position_pct:.1f}%)")
        # CRITICAL FIX: 修复显示格式，1.0 应该显示为 100.0%（而不是 1.0%）
        available_position_pct_display = available_position_pct * 100 if available_position_pct <= 1.0 else available_position_pct
        print(f"  - Available position space: {available_position_pct_display:.1f}%")
        
        if available_position_pct <= 0:
            # 已达到总仓位上限，不买入新股票
            print(f"[TRADER] Skipping all buy orders: available position space <= 0%")
            pass
        else:
            # 遍历所有推荐股票，计算每只股票的买入数量
            # 包括普通股票、杠杆ETF（做多）、反向ETF（做空）
            # CRITICAL: 打印推荐股票列表和现有持仓的对比
            if current_positions:
                existing_symbols = set(current_positions.keys())
                recommended_symbols = set(recs)
                overlap = existing_symbols & recommended_symbols
                new_symbols = recommended_symbols - existing_symbols
                print(f"[TRADER] Recommended stocks: {len(recs)} total")
                print(f"  - Already held: {len(overlap)} symbols ({', '.join(list(overlap)[:5])}{'...' if len(overlap) > 5 else ''})")
                print(f"  - New symbols: {len(new_symbols)} symbols ({', '.join(list(new_symbols)[:5])}{'...' if len(new_symbols) > 5 else ''})")
            else:
                print(f"[TRADER] Recommended stocks: {len(recs)} total (no existing positions)")
            
            for symbol in recs:
                if symbol not in last_prices:
                    print(f"[TRADER] Skipping {symbol}: no price data")
                    continue
                
                last_price = last_prices[symbol]
                if last_price <= 0:
                    print(f"[TRADER] Skipping {symbol}: invalid price (${last_price:.2f})")
                    continue
                
                # CRITICAL: 检查是否已有持仓（用于日志和验证）
                has_existing_position = False
                existing_qty = 0
                if current_positions and symbol in current_positions:
                    pos_info = current_positions[symbol]
                    if isinstance(pos_info, dict):
                        existing_qty = pos_info.get("quantity", 0)
                    else:
                        existing_qty = pos_info if isinstance(pos_info, (int, float)) else 0
                    if existing_qty > 0:
                        has_existing_position = True
                        print(f"[TRADER] {symbol}: Already has {existing_qty} shares, will calculate additional buy quantity")
                
                # 检查是否是反向ETF（用于做空）
                is_inverse_etf = symbol in INVERSE_ETFS
                is_leveraged_etf = symbol in LEVERAGED_ETFS
                
                # 计算买入数量（使用改进后的函数）
                # NOTE: 仓位限制是指导原则，agent 可以根据信号强度、市场条件等因素灵活调整
                # 函数内部会根据信号强度、推荐股票数量等因素动态调整仓位大小
                # CRITICAL: _calculate_position_size 会检查已有持仓，如果已达到目标仓位则返回0
                quantity = _calculate_position_size(
                    symbol, 
                    recs, 
                    portfolio_value, 
                    last_price, 
                    rview, 
                    current_positions,  # CRITICAL: 传入持仓信息，函数会检查并避免超过仓位限制
                    max_position_per_stock=max_position_per_stock,  # 指导原则：最大单股仓位
                    max_total_position=max_total_position,  # 指导原则：最大总仓位
                    min_position_per_stock=min_position_per_stock,  # 指导原则：最小单股仓位（用于分散投资）
                    available_cash=remaining_cash,  # 硬限制：可用现金（不能超过）
                )
                
                # CRITICAL: 验证买入数量（确保逻辑正确）
                if quantity > 0 and has_existing_position:
                    print(f"[TRADER] {symbol}: Will add {quantity} shares to existing {existing_qty} shares (total will be {existing_qty + quantity})")
                elif quantity == 0 and has_existing_position:
                    print(f"[TRADER] {symbol}: Skipping buy - already at target position ({existing_qty} shares)")
                elif quantity == 0:
                    print(f"[TRADER] {symbol}: Skipping buy - no quantity calculated (may be due to cash limit, position limit, or other constraints)")
                
                if quantity > 0:
                    # 买入价格范围（优化限价策略，提高成交率）
                    # 使用当前价格的 99.5%-100.5% 作为范围，限价设为 100%（允许小幅溢价，提高成交率）
                    buy_price_max = last_price * 1.005  # 最高买入价（允许0.5%溢价，提高成交率）
                    buy_price_min = last_price * 0.995  # 最低买入价（比当前价格低0.5%）
                    buy_price = last_price * 1.002  # 默认使用当前价格+0.2%（平衡成交率和成本）
                    total_cost = buy_price * quantity
                    
                    # CRITICAL: 再次检查剩余现金（双重保险）
                    # CRITICAL FIX: 如果剩余现金为0或负数，直接跳过
                    if available_cash is not None:
                        if remaining_cash <= 0:
                            print(f"[TRADER] Skipping {symbol}: no remaining cash (remaining: ${remaining_cash:.2f})")
                            continue
                        if total_cost > remaining_cash:
                            # 如果总成本超过剩余现金，减少数量
                            max_affordable_qty = floor(remaining_cash / buy_price)
                            if max_affordable_qty > 0:
                                quantity = max_affordable_qty
                                total_cost = buy_price * quantity
                                print(f"[TRADER] Reduced {symbol} quantity to {quantity} due to remaining cash limit (remaining: ${remaining_cash:.2f})")
                            else:
                                print(f"[TRADER] Skipping {symbol}: insufficient remaining cash (need ${total_cost:.2f}, remaining ${remaining_cash:.2f})")
                                continue
                    
                    # CRITICAL: 扣除已使用的现金（在添加到订单列表前）
                    if available_cash is not None:
                        remaining_cash -= total_cost
                        print(f"[TRADER] Order for {symbol}: cost=${total_cost:.2f}, remaining cash=${remaining_cash:.2f}")
                    
                    # 构建订单信息
                    order_info = {
                        "symbol": symbol,
                        "buy_price": buy_price,  # 用于计算的基准价格
                        "buy_price_min": buy_price_min,  # 最低买入价（范围下限，低买）
                        "buy_price_max": buy_price_max,  # 最高买入价（范围上限，不超过当前价格）
                        "quantity": quantity,
                        "total_cost": total_cost,
                    }
                    
                    # 标记ETF类型（用于后续处理和日志）
                    if is_inverse_etf:
                        order_info["etf_type"] = "inverse"  # 反向ETF（做空市场）
                    elif is_leveraged_etf:
                        order_info["etf_type"] = "leveraged"  # 杠杆ETF（放大做多）
                    
                    buy_orders.append(order_info)
    
    # CRITICAL: 检查所有当前持仓，决定是否需要卖出
    # 确保agent知道所有可卖出的持仓及其数量
    if current_positions:
        print(f"[TRADER] Checking {len(current_positions)} current positions for sell opportunities...")
        
        for symbol, pos_info in current_positions.items():
            if isinstance(pos_info, dict):
                qty = pos_info.get("quantity", 0)
                avg_cost = pos_info.get("avg_cost", 0.0)
                current_price = pos_info.get("current_price", last_prices.get(symbol, 0.0))
                unrealized_pnl = pos_info.get("unrealized_pnl", 0.0)
                unrealized_pnl_pct = pos_info.get("unrealized_pnl_pct", 0.0)
                position_pct = pos_info.get("position_pct", 0.0)
            else:
                qty = pos_info if isinstance(pos_info, (int, float)) else 0
                avg_cost = 0.0
                current_price = last_prices.get(symbol, 0.0)
                unrealized_pnl = 0.0
                unrealized_pnl_pct = 0.0
                position_pct = 0.0
            
            # 确保有持仓且价格有效
            if qty <= 0 or symbol not in last_prices or last_prices[symbol] <= 0:
                continue
            
            # 使用当前价格（如果持仓信息中没有）
            if current_price <= 0:
                current_price = last_prices[symbol]
            
            print(f"[TRADER] Position {symbol}: {qty} shares @ ${avg_cost:.2f} avg, current ${current_price:.2f}, P&L=${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%), position_pct={position_pct:.1f}%")
            
            # 决定卖出数量的逻辑：
            # 1. 基于风险报告的仓位限制检查
            sell_qty_from_risk = 0
            if rview:
                sell_qty_from_risk = _calculate_sell_size(
                    symbol, qty, portfolio_value, current_price, rview, current_positions
                )
            
            # 2. 基于持仓表现的卖出决策（可以考虑亏损持仓、盈利持仓等）
            # 这里可以根据市场分析、持仓表现等因素决定是否卖出
            # 例如：如果持仓亏损超过阈值，可以考虑卖出止损
            # 或者：如果持仓盈利达到目标，可以考虑获利了结
            
            # 3. 基于市场分析的卖出决策
            # 如果市场分析建议卖出某些股票（例如：技术分析显示趋势反转）
            # 可以从mview或convo中提取卖出建议
            
            # 综合决定：优先考虑风险报告的建议，但也可以考虑其他因素
            sell_qty = sell_qty_from_risk
            
            # CRITICAL: 如果风险报告建议卖出，或者有其他卖出信号，生成卖出订单
            if sell_qty > 0:
                # CRITICAL FIX: 确保卖出数量不超过持仓数量（硬性限制）
                original_sell_qty = sell_qty
                sell_qty = min(sell_qty, qty)
                if sell_qty < original_sell_qty:
                    print(f"[TRADER] WARNING: {symbol} sell quantity capped from {original_sell_qty} to {sell_qty} (current position: {qty} shares)")
                
                # CRITICAL: 再次验证卖出数量（确保不会卖出超过持有的数量）
                if sell_qty > qty:
                    print(f"[TRADER] ERROR: {symbol} sell quantity ({sell_qty}) exceeds current position ({qty}), forcing to {qty}")
                    sell_qty = qty
                
                if sell_qty <= 0:
                    print(f"[TRADER] Skipping {symbol}: sell quantity is 0 or negative after validation")
                    continue
                
                # 卖出价格范围（市价单：使用当前价格）
                sell_price = current_price  # 市价单：使用当前价格
                sell_price_min = current_price  # 市价单：价格范围就是当前价格
                sell_price_max = current_price
                
                sell_orders.append({
                    "symbol": symbol,
                    "sell_price": sell_price,  # 用于计算的基准价格
                    "sell_price_min": sell_price_min,  # 最低卖出价（范围下限）
                    "sell_price_max": sell_price_max,  # 最高卖出价（范围上限）
                    "quantity": sell_qty,
                    "total_proceeds": sell_price * sell_qty,  # 基于基准价格估算
                    "current_position": qty,  # 记录当前持仓数量（用于验证）
                    "avg_cost": avg_cost,  # 记录平均成本（用于计算realized_pnl）
                    "unrealized_pnl": unrealized_pnl,  # 记录未实现损益（用于参考）
                })
                
                if sell_qty_from_risk > 0:
                    risk_compliance["warnings"].append(
                        f"{symbol} position exceeds limit, recommend selling {sell_qty} shares (current: {qty} shares)"
                    )
                else:
                    risk_compliance["warnings"].append(
                        f"{symbol} sell order generated based on market analysis (selling {sell_qty} of {qty} shares)"
                    )
                
                print(f"[TRADER] Generated SELL order for {symbol}: {sell_qty} shares @ ${sell_price:.2f} (current position: {qty} shares, P&L: ${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%))")
            else:
                print(f"[TRADER] No sell order for {symbol}: position within limits, qty={qty}")
    
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
                # CRITICAL FIX: 移除200字符限制，允许完整提取coordinator_summary
                coordinator_summary = summary_text
                print(f"[TRADER] Found coordinator summary from convo.coordinator_summary ({len(coordinator_summary)} chars)")
        # 如果直接获取失败，尝试从discussion中获取
        if not coordinator_summary:
            discussion = convo.get("discussion", {})
            if isinstance(discussion, dict):
                coordinator = discussion.get("coordinator_summary", {})
                if isinstance(coordinator, dict):
                    summary_text = coordinator.get("summary", "")
                    if summary_text and len(summary_text.strip()) > 20:
                        # CRITICAL FIX: 移除200字符限制，允许完整提取coordinator_summary
                        coordinator_summary = summary_text
                        print(f"[TRADER] Found coordinator summary from convo.discussion.coordinator_summary ({len(coordinator_summary)} chars)")
        # 如果还是没有，尝试从discussion_history中提取
        if not coordinator_summary:
            discussion_history = convo.get("discussion_history", [])
            for entry in discussion_history:
                if entry.get("analyst") == "Discussion Coordinator":
                    analysis = entry.get("analysis", "")
                    if analysis and len(analysis.strip()) > 20:
                        # CRITICAL FIX: 移除200字符限制，允许完整提取coordinator_summary
                        coordinator_summary = analysis
                        print(f"[TRADER] Found coordinator summary from discussion_history ({len(coordinator_summary)} chars)")
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

    # CRITICAL: 使用 LLM 来生成交易决策的 summary
    # LLM 会考虑市场状态、订单信息、分析结果，并生成有意义的说明
    print(f"[TRADER] ===== CALLING LLM FOR SUMMARY GENERATION =====")
    trader_summary = None
    
    try:
        # 创建 AgentFactory 和 trader_agent
        from pathlib import Path
        from src.agents.factory import AgentFactory
        from src.agents.base import BaseAgent
        import json
        
        ROOT = Path(__file__).resolve().parents[2]
        fac = AgentFactory(ROOT / "config" / "agents.yaml")
        trader_agent: BaseAgent = fac.create("trader_agent")
        
        # 准备订单信息摘要
        orders_summary = []
        if buy_orders:
            buy_symbols = [o["symbol"] for o in buy_orders[:10]]
            buy_count = len(buy_orders)
            total_buy_cost = sum(o.get("total_cost", 0.0) for o in buy_orders)
            orders_summary.append(f"Generating {buy_count} BUY orders: {', '.join(buy_symbols)}{'...' if buy_count > 10 else ''} (Total: ${total_buy_cost:,.2f})")
        if sell_orders:
            sell_symbols = [o["symbol"] for o in sell_orders[:10]]
            sell_count = len(sell_orders)
            total_sell_proceeds = sum(o.get("total_proceeds", 0.0) for o in sell_orders)
            orders_summary.append(f"Generating {sell_count} SELL orders: {', '.join(sell_symbols)}{'...' if sell_count > 10 else ''} (Total: ${total_sell_proceeds:,.2f})")
        if not orders_summary:
            orders_summary.append("No trading orders generated (HOLD position)")
        
        # 准备持仓信息摘要
        positions_summary = ""
        if current_positions:
            positions_list = []
            for sym, pos_info in list(current_positions.items())[:10]:  # 最多显示10个持仓
                if isinstance(pos_info, dict):
                    qty = pos_info.get("quantity", 0)
                    market_value = pos_info.get("market_value", 0.0)
                    unrealized_pnl = pos_info.get("unrealized_pnl", 0.0)
                    unrealized_pnl_pct = pos_info.get("unrealized_pnl_pct", 0.0)
                    positions_list.append(f"{sym}: {qty} shares, value=${market_value:.2f}, P&L=${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%)")
            if positions_list:
                positions_summary = "\n".join(positions_list)
            else:
                positions_summary = "No current positions"
        else:
            positions_summary = "No current positions"
        
        # 准备 prompt 变量（用于完整信息传递）
        # CRITICAL FIX: Use safe_json_dumps to handle pandas Series/DataFrame
        # CRITICAL FIX: Calculate current position count and max_positions
        current_position_count = len(current_positions) if current_positions else 0
        max_positions_value = position_config.get("max_positions") if position_config else None
        
        prompt_vars = {
            "market_status": "OPEN" if is_market_open else "CLOSED",  # ⭐ 关键：传入市场状态
            "quotes_snapshot": safe_json_dumps(market, indent=2, ensure_ascii=False) if market else "{}",
            "risk_result_json": safe_json_dumps(rview, indent=2, ensure_ascii=False) if rview else "{}",
            "tech_result_json": safe_json_dumps(mview, indent=2, ensure_ascii=False) if mview else "{}",
            "psych_result_json": safe_json_dumps(convo, indent=2, ensure_ascii=False) if convo else "{}",
            "consensus_json": safe_json_dumps(convo, indent=2, ensure_ascii=False) if convo else "{}",
            "orders_summary": "\n".join(orders_summary),
            "positions_summary": positions_summary,
            "final_stance": final_stance,
            "vix_risk": vix_risk,
            "coordinator_summary": coordinator_summary if coordinator_summary else "No coordinator summary available",
            "portfolio_value": portfolio_value or 10000.0,
            "available_cash": available_cash or 0.0,
            "max_position_per_stock": position_config.get("max_position_per_stock", 0.15) * 100 if position_config else 15.0,
            "max_total_position": position_config.get("max_total_position", 0.85) * 100 if position_config else 85.0,
            "min_position_per_stock": position_config.get("min_position_per_stock", 0.03) * 100 if position_config else 3.0,
            "current_position_count": current_position_count,  # CRITICAL: 当前持仓数量
            "max_positions": max_positions_value if max_positions_value is not None else "unlimited",  # CRITICAL: 最大持仓数限制
        }
        
        # 调用 LLM 生成 summary（传入完整信息）
        # CRITICAL FIX: 使用 user_append 附加 summary prompt，而不是替换整个 user prompt
        # 这样模板变量可以正常渲染，同时附加我们的 summary 请求
        summary_prompt = f"""Based on the following trading decision information, generate a concise summary (100-150 words) explaining the trading rationale:

Market Status: {prompt_vars['market_status']} (trading allowed only when OPEN)
Market Stance: {final_stance}
VIX Risk: {vix_risk:.1f}
Portfolio Value: ${prompt_vars['portfolio_value']:,.2f}
Available Cash: ${prompt_vars['available_cash']:,.2f}

Current Positions:
{prompt_vars['positions_summary']}

Orders Generated:
{prompt_vars['orders_summary']}

Coordinator Analysis Summary:
{prompt_vars['coordinator_summary']}

Please provide a clear, professional summary that:
1. States the market status (OPEN/CLOSED) and its implications
2. Explains the trading decision rationale based on all available information
3. Mentions key factors (stance, VIX, coordinator insights, current positions)
4. If orders were generated, briefly explain why and what they are
5. If no orders, explain the reasoning (e.g., market closed, risk concerns, waiting for better entry)
6. If there are current positions, mention their status briefly

Write in natural language, approximately 100-150 words."""
        
        # CRITICAL FIX: 传入完整的 prompt_vars 让模板正常渲染，然后使用 user_append 附加 summary prompt
        # 这样 LLM 可以访问所有输入数据（quotes_snapshot, risk_result_json 等），同时收到 summary 请求
        llm_response = trader_agent.run(prompt_vars, expect_json=False, user_append=summary_prompt)
        
        if llm_response and isinstance(llm_response, str) and len(llm_response.strip()) > 50:
            trader_summary = llm_response.strip()
            print(f"[TRADER] LLM generated summary ({len(trader_summary)} chars)")
        else:
            print(f"[TRADER] WARNING: LLM response invalid, using fallback")
            raise Exception("Invalid LLM response")
            
    except Exception as e:
        print(f"[TRADER] LLM summary generation failed: {e}, using fallback")
        import traceback
        traceback.print_exc()
        # Fallback: 使用基于规则的 summary
        if buy_orders and len(buy_orders) > 0:
            buy_symbols = [o["symbol"] for o in buy_orders[:5]]
            buy_count = len(buy_orders)
            total_buy_cost = sum(o.get("total_cost", 0.0) for o in buy_orders)
            trader_summary = f"Market is currently OPEN. Based on market analysis and risk assessment, I'm generating {buy_count} buy orders for {', '.join(buy_symbols)}{'...' if buy_count > 5 else ''} with a total cost of ${total_buy_cost:,.2f}. Market stance is {final_stance} with VIX risk at {vix_risk:.1f}."
            if coordinator_summary:
                # CRITICAL FIX: 移除500字符限制，允许完整summary显示
                trader_summary += f" Key insights: {coordinator_summary}"
        elif sell_orders and len(sell_orders) > 0:
            sell_symbols = [o["symbol"] for o in sell_orders[:5]]
            sell_count = len(sell_orders)
            total_sell_proceeds = sum(o.get("total_proceeds", 0.0) for o in sell_orders)
            trader_summary = f"Market is currently OPEN. Based on risk management and market conditions, I'm generating {sell_count} sell orders for {', '.join(sell_symbols)}{'...' if sell_count > 5 else ''} with expected proceeds of ${total_sell_proceeds:,.2f}. Market stance is {final_stance} with VIX risk at {vix_risk:.1f}."
            if coordinator_summary:
                # CRITICAL FIX: 移除500字符限制，允许完整summary显示
                trader_summary += f" Key insights: {coordinator_summary}"
        else:
            trader_summary = f"Market is currently OPEN. No trading orders generated. Market stance is {final_stance} with VIX risk at {vix_risk:.1f}. Current market conditions and risk assessment suggest maintaining current positions or waiting for better entry points."
            if coordinator_summary:
                # CRITICAL FIX: 移除500字符限制，允许完整summary显示
                trader_summary += f" Analysis: {coordinator_summary}"
    
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
                # CRITICAL: Include position info for validation and P&L calculation
                "current_position": int(order.get("current_position", 0)) if order.get("current_position") is not None else None,
                "avg_cost": float(order.get("avg_cost", 0.0)) if order.get("avg_cost") is not None else None,
                "unrealized_pnl": float(order.get("unrealized_pnl", 0.0)) if order.get("unrealized_pnl") is not None else None,
            }
            for order in sell_orders
        ],
        "rationale": str(rationale),  # 确保是字符串
        "summary": str(trader_summary),  # 新增：Trader Agent的summary
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
        # 如果序列化失败，返回最小化版本（确保包含summary字段）
        decision = {
            "action": "HOLD",
            "targets": [],
            "buy_orders": [],
            "sell_orders": [],
            "rationale": f"Error: {str(e)}",
            "summary": f"Error occurred during decision generation: {str(e)}. No trading orders generated.",
            "stance": "neutral",
            "vix_risk": 0.0,
            "risk_compliance": {"position_limits_ok": False, "diversification_ok": False, "warnings": [str(e)]},
        }
    
    return decision
