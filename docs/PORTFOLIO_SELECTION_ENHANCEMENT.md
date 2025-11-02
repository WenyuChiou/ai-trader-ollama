# 📊 多股票组合选择增强

## 🎯 功能概述

Trader Agent 现在能够从 `config.json` 中的所有候选股票中挑选组合，并能智能地决定买入、卖出和持仓调整。

## ✨ 新增功能

### 1. **评估所有候选股票**

Trader Agent 现在可以评估 `config.json` 中的所有候选股票，而不仅仅是 Market Analyst 推荐的股票。

**功能**:
- 评估所有候选股票的综合评分
- 基于 `signal_score`、`trend`、`risk_score` 计算综合评分
- 筛选出潜在购买公司（评分 >= 3.0，推荐 BUY）

**评分因素**:
- Signal Score (0-3): 技术指标信号
- Trend: uptrend (+2), downtrend (-2), sideways (0)
- Risk Score: 低风险 (+1), 高风险 (-1)
- VIX 风险: 高 VIX (-1)

### 2. **持仓调整逻辑**

Trader Agent 现在能够智能地决定持仓调整：

**卖出决策**:
- **部分卖出** (`over_limit`): 如果持仓超过限制，减少到目标仓位
- **全部卖出** (`downtrend`): 如果趋势转弱，全部卖出
- **全部卖出** (`stop_loss`): 如果风险过高（>= 8.0），止损卖出

**持有决策**:
- 如果趋势良好且风险可控，继续持有

**买入决策**:
- **新持仓** (`NEW`): 买入新股票
- **增持** (`INCREASE`): 对现有持仓增持（如果评分仍高）

### 3. **潜在购买公司列表**

Trader Agent 返回 `potential_buys` 列表，包含所有潜在购买公司的评估信息：

```python
potential_buys = [
    {
        "symbol": "NVDA",
        "score": 5.0,
        "signal_score": 2.0,
        "trend": "uptrend",
        "risk_score": 4.0,
        "recommendation": "BUY",
        "reasons": ["uptrend", "low_risk"],
        "price": 120.0,
    },
    # ...
]
```

### 4. **持仓调整建议**

Trader Agent 返回 `position_adjustments` 列表，包含所有持仓调整建议：

```python
position_adjustments = [
    {
        "symbol": "NVDA",
        "action": "NEW",  # NEW / INCREASE / HOLD / SELL
        "quantity": 10,
        "reason": "score=5.0, trend=uptrend",
    },
    {
        "symbol": "MSFT",
        "action": "HOLD",
        "current_qty": 50,
        "reason": "trend=uptrend, risk=4.5",
    },
    # ...
]
```

## 🔄 工作流程

### 完整决策流程

```
1. 评估所有候选股票
   ↓
2. 筛选潜在购买公司（评分 >= 3.0，推荐 BUY）
   ↓
3. 评估当前持仓
   - 趋势转弱 → 全部卖出
   - 风险过高 → 止损卖出
   - 超过限制 → 部分减仓
   - 趋势良好 → 继续持有
   ↓
4. 选择买入候选
   - 最多买入5只新股票
   - 优先选择高分股票
   - 考虑现有持仓，可增持
   - 限制总买入金额（不超过80%）
   ↓
5. 生成订单
   - buy_orders: 买入订单列表
   - sell_orders: 卖出订单列表
   - potential_buys: 潜在购买公司列表
   - position_adjustments: 持仓调整建议
```

## 📊 输出结构

### Trader Agent 输出

```python
{
    "action": "BUY",  # BUY / SELL / HOLD
    "buy_orders": [
        {
            "symbol": "NVDA",
            "buy_price": 120.0,
            "quantity": 10,
            "total_cost": 1200.0,
            "action": "NEW",  # NEW / INCREASE
        },
        # ...
    ],
    "sell_orders": [
        {
            "symbol": "AAPL",
            "sell_price": 180.0,
            "quantity": 5,
            "total_proceeds": 900.0,
            "sell_reason": "downtrend",  # over_limit / downtrend / stop_loss
            "trend": "downtrend",
            "risk_score": 7.5,
        },
        # ...
    ],
    "potential_buys": [
        {
            "symbol": "NVDA",
            "score": 5.0,
            "signal_score": 2.0,
            "trend": "uptrend",
            "risk_score": 4.0,
            "recommendation": "BUY",
            "reasons": ["uptrend", "low_risk"],
            "price": 120.0,
        },
        # ...
    ],
    "position_adjustments": [
        {
            "symbol": "NVDA",
            "action": "NEW",
            "quantity": 10,
            "reason": "score=5.0, trend=uptrend",
        },
        {
            "symbol": "MSFT",
            "action": "HOLD",
            "current_qty": 50,
            "reason": "trend=uptrend, risk=4.5",
        },
        # ...
    ],
    "rationale": "Rebalancing: Buying 3 stocks, Selling 2 positions; stance=constructive, VIX risk=4.0",
    "stance": "constructive",
    "vix_risk": 4.0,
    "risk_compliance": {
        "position_limits_ok": True,
        "diversification_ok": True,
        "warnings": [],
    },
}
```

## 🔧 配置

### config.json

```json
{
  "universe": [
    "NVDA", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "META", "AVGO", "TSLA",
    // ... 更多候选股票
  ],
  "initial_cash": 10000,
  "position_limit_per_stock": 0.2,
  "position_limit_total": 0.8,
}
```

### 限制参数

- `max_new_positions`: 最多买入5只新股票（避免过度集中）
- `available_cash`: 限制总买入金额（不超过组合净值的80%）
- `position_limit_per_stock`: 单股最大仓位（默认15%，可配置）
- `position_limit_total`: 总仓位限制（默认60%，可配置）

## 📝 使用示例

### Trading Cycle 集成

```python
result = execute_daily_trade(
    universe=["NVDA", "MSFT", "AAPL", "GOOG", "AMZN"],  # 所有候选股票
    portfolio=portfolio,
    trade_logger=trade_logger,
)

# 获取决策结果
decision = result["decision"]
buy_orders = decision["buy_orders"]
sell_orders = decision["sell_orders"]
potential_buys = decision["potential_buys"]
position_adjustments = decision["position_adjustments"]

# 显示潜在购买公司
for stock in potential_buys:
    print(f"{stock['symbol']}: score={stock['score']:.1f}, trend={stock['trend']}, recommendation={stock['recommendation']}")

# 显示持仓调整建议
for adjustment in position_adjustments:
    print(f"{adjustment['symbol']}: {adjustment['action']} - {adjustment['reason']}")
```

## ✅ 完成状态

- ✅ 评估所有候选股票
- ✅ 持仓调整逻辑（部分卖出、全部卖出、持有、增持）
- ✅ 潜在购买公司筛选
- ✅ Trading Cycle 集成（传入所有候选股票）

---

**更新日期**: 2025-11-02

