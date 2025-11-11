# 持仓信息传递增强总结

## 问题
需要确保持仓信息（损益、占比等）完整传递给所有 agent（Risk Analyst 和 Trader），并在 prompt 中明确要求使用这些信息。

## 修复内容

### 1. 完善持仓信息数据结构 ✅

**文件**: `backend/src/orchestrator/trading_cycle.py`

**修改前**:
```python
current_positions_info[symbol] = {
    "quantity": pos.quantity,
    "avg_cost": pos.avg_cost,
    "current_price": current_price,
    "market_value": pos.quantity * current_price,
}
```

**修改后**:
```python
current_positions_info[symbol] = {
    "quantity": pos.quantity,
    "avg_cost": pos.avg_cost,
    "current_price": current_price,
    "market_value": market_value,
    "unrealized_pnl": unrealized_pnl,  # 未实现损益（金额）
    "unrealized_pnl_pct": unrealized_pnl_pct,  # 未实现损益（百分比）
    "position_pct": position_pct,  # 持仓占比（占组合净值的百分比）
}
```

**效果**: 持仓信息现在包含完整的损益和占比数据

### 2. 增强 Risk Analyst 的持仓信息格式化 ✅

**文件**: `backend/src/agents/risk_analyst_llm.py`

**修改**:
- 格式化持仓信息时，明确包含所有字段（包括 P&L 和占比）
- 在 prompt 中添加明确的警告和要求

**新增内容**:
```python
positions_str = f"""**CURRENT PORTFOLIO POSITIONS (with P&L and Position %):**

{json.dumps(positions_formatted, indent=2)}

**⚠️ CRITICAL: You MUST analyze each position's P&L (unrealized_pnl, unrealized_pnl_pct) and position percentage (position_pct) when making risk assessments.**
"""
```

### 3. 强化 Risk Analyst Prompt ✅

**文件**: `backend/prompts/risk_analyst.yml`

**新增内容**:
```yaml
**⚠️ CRITICAL: Current Positions Information**
The {current_positions} field contains detailed position information including:
- **unrealized_pnl**: Unrealized profit/loss in dollars
- **unrealized_pnl_pct**: Unrealized profit/loss percentage
- **position_pct**: Position size as percentage of total portfolio value

**YOU MUST USE THIS INFORMATION IN YOUR RISK ANALYSIS:**
1. **Analyze P&L for each position**: Check unrealized_pnl and unrealized_pnl_pct
2. **Check position concentration**: Review position_pct for each holding
3. **Assess overall portfolio health**: Calculate total unrealized P&L
4. **Make specific recommendations** based on P&L and position size
```

### 4. 增强 Trader Agent 的持仓信息使用 ✅

**文件**: `backend/src/agents/trader_agent.py`

**修改**:
- 添加注释说明持仓信息包含的完整字段
- 添加调试日志，打印每个持仓的损益和占比
- 优先使用 `market_value`（如果存在）

**新增内容**:
```python
# CRITICAL: 计算当前总仓位（用于限制买入）
# current_positions 包含完整信息：quantity, avg_cost, current_price, market_value, unrealized_pnl, unrealized_pnl_pct, position_pct

# DEBUG: 打印持仓信息（包括损益和占比）
unrealized_pnl = pos_info.get("unrealized_pnl", 0.0)
unrealized_pnl_pct = pos_info.get("unrealized_pnl_pct", 0.0)
position_pct = pos_info.get("position_pct", 0.0)
if market_value > 0:
    print(f"[TRADER] Position {sym}: value=${market_value:.2f} ({position_pct:.1f}%), P&L=${unrealized_pnl:.2f} ({unrealized_pnl_pct:+.1f}%)")
```

### 5. 增强 Multi-Analyst System 的提示 ✅

**文件**: `backend/src/agents/multi_analyst_system.py`

**修改**:
- 更新提示文本，明确要求使用持仓信息（P&L 和占比）
- 添加具体的检查要求

**新增内容**:
```python
positions_text += "\n**⚠️ CRITICAL: You MUST use position information (P&L and position %) when making recommendations:**\n"
positions_text += "- Check position_pct for each holding (avoid over-concentration >15%)\n"
positions_text += "- Consider unrealized_pnl_pct (large losses may need position reduction)\n"
positions_text += "- Respect position limits and diversification requirements\n"
positions_text += "- Use available_cash information to avoid creating orders exceeding cash limits\n"
```

## 持仓信息字段说明

每个持仓现在包含以下完整信息：

1. **quantity**: 持仓数量（股数）
2. **avg_cost**: 平均成本价格
3. **current_price**: 当前市场价格
4. **market_value**: 当前市值（quantity × current_price）
5. **unrealized_pnl**: 未实现损益（金额，正数=盈利，负数=亏损）
6. **unrealized_pnl_pct**: 未实现损益（百分比，正数=盈利%，负数=亏损%）
7. **position_pct**: 持仓占比（占组合净值的百分比）

## Agent 使用要求

### Risk Analyst
- **必须**分析每个持仓的 P&L（unrealized_pnl, unrealized_pnl_pct）
- **必须**检查持仓集中度（position_pct）
- **必须**基于 P&L 和占比做出具体的风险建议
- **必须**识别超过限制的持仓（position_pct > 15%）
- **必须**识别大额亏损的持仓（unrealized_pnl_pct < -10%）

### Trader Agent
- **必须**使用持仓信息计算总仓位
- **必须**考虑可用现金限制
- **必须**避免创建超过现金限制的订单
- **必须**考虑持仓集中度限制

### Multi-Analyst System (所有分析师)
- **必须**在推荐时考虑现有持仓
- **必须**避免过度集中（position_pct > 15%）
- **必须**考虑持仓的损益情况
- **必须**尊重持仓限制和分散投资要求

## 预期效果

1. **Risk Analyst** 能够基于 P&L 和占比做出更准确的风险评估
2. **Trader Agent** 能够基于持仓信息做出更合理的交易决策
3. **所有分析师** 都能看到完整的持仓信息，避免重复买入或过度集中
4. **订单创建** 会严格考虑现金限制和持仓限制

## 测试建议

1. 运行一次交易周期，检查日志中是否有 `[TRADER] Position ... P&L=...` 的输出
2. 检查 Risk Analyst 的报告是否包含基于 P&L 和占比的建议
3. 验证订单总金额不超过可用现金
4. 验证持仓集中度是否在合理范围内

