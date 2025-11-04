# 对冲策略说明

## 概述

系统已支持使用反向ETF进行对冲，允许Agent在市场风险较高时使用反向ETF保护投资组合。

## 反向ETF列表

在 `backend/config/config.json` 中配置了以下反向ETF：

```json
{
  "inverse_etfs": [
    "SQQQ",  // 3x Inverse NASDAQ (3倍反向纳斯达克)
    "SPXU",  // 3x Inverse S&P 500 (3倍反向标普500)
    "SH",    // 1x Inverse S&P 500 (1倍反向标普500)
    "PSQ",   // 1x Inverse QQQ (1倍反向QQQ)
    "SDS",   // 2x Inverse S&P 500 (2倍反向标普500)
    "DOG",   // 1x Inverse Dow Jones (1倍反向道琼斯)
    "SOXS"   // 3x Inverse Semiconductor ETF (3倍反向半导体)
  ]
}
```

这些ETF已添加到 `universe` 中，可以正常交易。

## 杠杆ETF列表

在 `backend/config/config.json` 中配置了以下杠杆ETF（适度使用）：

```json
{
  "leveraged_etfs": [
    "TQQQ",  // 3x Leveraged NASDAQ (3倍杠杆纳斯达克)
    "SOXL",  // 3x Leveraged Semiconductor ETF (3倍杠杆半导体)
    "UPRO",  // 3x Leveraged S&P 500 (3倍杠杆标普500)
    "TNA",   // 3x Leveraged Small Cap (3倍杠杆小盘股)
    "FAS",   // 3x Leveraged Financials (3倍杠杆金融)
    "CURE",  // 3x Leveraged Healthcare (3倍杠杆医疗)
    "LABU",  // 3x Leveraged Biotech (3倍杠杆生物科技)
    "TECL",  // 3x Leveraged Technology (3倍杠杆科技)
    "TMF",   // 3x Leveraged 20+ Year Treasury (3倍杠杆长期国债)
    "EDC"    // 3x Leveraged Emerging Markets (3倍杠杆新兴市场)
  ]
}
```

这些ETF已添加到 `universe` 中，可以正常交易，但需要谨慎使用。

## 反向ETF说明

### 杠杆倍数

- **1x (SH, PSQ, DOG)**: 反向比例为1:1，波动较小，适合温和对冲
- **2x (SDS)**: 反向比例为2:1，中等杠杆，适合中等风险对冲
- **3x (SQQQ, SPXU)**: 反向比例为3:1，高杠杆，适合激进对冲

### 使用场景

1. **市场下跌保护**: 当市场预期下跌时，买入反向ETF可以保护投资组合
2. **波动率对冲**: 当VIX > 20时，使用反向ETF降低组合风险
3. **仓位保护**: 不想卖出现有持仓，但想降低净风险敞口
4. **技术面反转信号**: 技术指标显示市场可能反转时

## Agent提示

### Discussion Agent

在 `backend/prompts/discussion_agent.yml` 中添加了对冲策略提示：

- 当市场情绪看跌时，考虑使用反向ETF
- 当VIX > 20时，建议使用反向ETF对冲
- 保护收益时可以使用反向ETF

### Trader Agent

在 `backend/prompts/trader_agent.yml` 中添加了详细的对冲指导：

- 反向ETF列表和使用场景
- 对冲比例建议（10-20%组合价值）
- 杠杆倍数选择指南
- 何时调整对冲仓位

## 使用示例

### 场景1: 高波动率对冲

```
市场条件:
- VIX = 25 (高波动率)
- 市场情绪: bearish
- 持仓: 多只科技股

Agent决策:
- 买入 SQQQ (3x Inverse NASDAQ) 作为对冲
- 对冲比例: 15% 组合价值
- 理由: 保护科技股持仓，应对市场下跌风险
```

### 场景2: 技术面反转

```
市场条件:
- S&P 500 RSI > 70 (超买)
- MACD 显示看跌信号
- 持仓: 多只股票

Agent决策:
- 买入 SPXU (3x Inverse S&P 500) 作为对冲
- 对冲比例: 10% 组合价值
- 理由: 技术指标显示市场可能反转
```

### 场景3: 温和对冲

```
市场条件:
- VIX = 18 (中等波动率)
- 市场情绪: neutral
- 持仓: 平衡配置

Agent决策:
- 买入 SH (1x Inverse S&P 500) 作为温和对冲
- 对冲比例: 10% 组合价值
- 理由: 温和保护，降低波动率
```

## 对冲策略原则

1. **对冲比例**: 通常为组合价值的 10-20%
2. **杠杆选择**: 
   - 高风险环境: 使用3x杠杆 (SQQQ, SPXU)
   - 中等风险: 使用2x杠杆 (SDS)
   - 低风险: 使用1x杠杆 (SH, PSQ, DOG)
3. **动态调整**: 根据市场条件调整对冲仓位
4. **成本考虑**: 反向ETF有管理费和交易成本

## 杠杆ETF使用指南

### 使用场景

1. **强烈看涨趋势**: 市场明确上涨趋势，技术指标强劲
2. **低波动率环境**: VIX < 15，市场稳定
3. **动量强劲**: RSI < 70，MACD看涨，趋势明确
4. **短期持有**: 适合短期交易，不适合长期持有

### 仓位限制

- **单只杠杆ETF**: 最大 5-10% 组合价值（vs 普通股票15%）
- **总杠杆ETF仓位**: 最大 20-30% 组合价值
- **原因**: 杠杆ETF波动极大，需要严格控制风险

### 风险警告

1. **波动率拖累 (Volatility Drag)**: 杠杆ETF在震荡市场中会衰减
2. **复利效应**: 每日重新平衡导致长期持有成本
3. **极端波动**: 市场暴跌时可能快速亏损
4. **不适合长期持有**: 仅适合短期趋势交易

## 注意事项

### 反向ETF

1. **杠杆风险**: 3x杠杆ETF波动极大，可能快速亏损
2. **时间衰减**: 反向ETF不适合长期持有，适合短期对冲
3. **追踪误差**: 反向ETF可能不完全追踪指数反向走势
4. **流动性**: 确保反向ETF有足够的交易量

### 杠杆ETF

1. **波动率拖累**: 在震荡市场中会持续衰减
2. **仓位限制**: 必须严格控制仓位（5-10%单只，20-30%总仓位）
3. **趋势依赖**: 只在明确趋势中使用，避免震荡市场
4. **止损建议**: 考虑设置止损或定期调整仓位

## 验证

Agent在生成订单时会考虑：
- 市场情绪（bearish时更可能使用对冲）
- VIX水平（高VIX时更可能使用对冲）
- 技术指标（反转信号时更可能使用对冲）
- 风险报告（高风险时建议使用对冲）

## 配置

在 `backend/config/config.json` 中：
- `universe`: 包含所有反向ETF（已添加）
- `inverse_etfs`: 反向ETF列表（用于参考）

## 监控

前端会显示反向ETF的持仓和P&L，与普通股票一样处理。

