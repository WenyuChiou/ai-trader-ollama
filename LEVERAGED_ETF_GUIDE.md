# 杠杆ETF使用指南

## 概述

系统已支持使用杠杆ETF进行适度交易，允许Agent在市场条件有利时使用杠杆ETF获取增强收益。

## 杠杆ETF列表

在 `backend/config/config.json` 中配置了以下杠杆ETF：

```json
{
  "leveraged_etfs": [
    "TQQQ",  // 3x Leveraged NASDAQ
    "SOXL",  // 3x Leveraged Semiconductor ETF
    "UPRO",  // 3x Leveraged S&P 500
    "TNA",   // 3x Leveraged Small Cap
    "FAS",   // 3x Leveraged Financials
    "CURE",  // 3x Leveraged Healthcare
    "LABU",  // 3x Leveraged Biotech
    "TECL",  // 3x Leveraged Technology
    "TMF",   // 3x Leveraged 20+ Year Treasury
    "EDC"    // 3x Leveraged Emerging Markets
  ]
}
```

## 杠杆ETF说明

### 杠杆倍数

所有配置的杠杆ETF都是 **3x杠杆**，意味着：
- 如果指数上涨 1%，ETF 上涨约 3%
- 如果指数下跌 1%，ETF 下跌约 3%

### 使用场景

1. **强烈看涨趋势**: 市场明确上涨，技术指标强劲
2. **低波动率环境**: VIX < 15，市场稳定
3. **动量交易**: RSI < 70，MACD看涨，趋势明确
4. **短期持有**: 适合短期交易（数天到数周）

## 仓位限制（重要）

### 单只杠杆ETF
- **最大仓位**: 5-10% 组合价值（vs 普通股票15%）
- **原因**: 杠杆ETF波动极大，需要严格控制风险

### 总杠杆ETF仓位
- **最大仓位**: 20-30% 组合价值
- **原因**: 避免过度杠杆化，保持组合平衡

## 风险警告

### 1. 波动率拖累 (Volatility Drag)

杠杆ETF在震荡市场中会持续衰减：

```
示例：
Day 1: 指数 +10%, ETF +30% (100 → 130)
Day 2: 指数 -10%, ETF -30% (130 → 91)
Day 3: 指数 +10%, ETF +30% (91 → 118.3)

结果：指数回到原点，但ETF下跌了！
```

### 2. 复利效应

每日重新平衡导致长期持有成本累积。

### 3. 极端波动

市场暴跌时可能快速亏损：
- 指数下跌 33% → ETF 可能接近归零
- 需要设置止损或严格控制仓位

## Agent提示

### Discussion Agent

在 `backend/prompts/discussion_agent.yml` 中添加了杠杆ETF提示：

- 仅在强烈看涨趋势中使用
- 技术指标必须强劲（RSI < 70, MACD看涨）
- VIX < 15（低波动率环境）
- 使用较小仓位（5-10%单只，20-30%总仓位）

### Trader Agent

在 `backend/prompts/trader_agent.yml` 中添加了详细指导：

- 仓位限制：5-10%单只，20-30%总仓位
- 使用条件：强烈看涨趋势、低波动率、技术指标强劲
- 风险警告：波动率拖累、不适合长期持有

## 使用示例

### 场景1: 强烈看涨趋势

```
市场条件:
- NASDAQ 强劲上涨趋势
- RSI = 55 (未超买)
- MACD 看涨
- VIX = 12 (低波动率)

Agent决策:
- 买入 TQQQ (3x Leveraged NASDAQ)
- 仓位: 8% 组合价值
- 理由: 强烈看涨趋势，低波动率，适合使用杠杆ETF
```

### 场景2: 半导体板块强势

```
市场条件:
- 半导体板块强势上涨
- SOXL 技术指标强劲
- 市场情绪: bullish
- VIX = 13

Agent决策:
- 买入 SOXL (3x Leveraged Semiconductor)
- 仓位: 6% 组合价值
- 理由: 板块强势，技术指标强劲，适合杠杆ETF
```

### 场景3: 市场震荡（不应使用）

```
市场条件:
- 市场横盘震荡
- RSI 在 40-60 之间波动
- VIX = 18 (中等波动率)

Agent决策:
- 不买入杠杆ETF
- 理由: 震荡市场不适合杠杆ETF（波动率拖累）
```

## 最佳实践

1. **仅在明确趋势中使用**: 避免震荡市场
2. **严格控制仓位**: 单只5-10%，总计20-30%
3. **设置止损**: 考虑设置止损点（例如 -15%）
4. **短期持有**: 数天到数周，避免长期持有
5. **监控波动率**: VIX > 15 时减少或退出
6. **定期调整**: 根据市场条件调整仓位

## 与反向ETF的配合

可以同时使用：
- **杠杆ETF**: 在上涨趋势中增强收益
- **反向ETF**: 在市场下跌时对冲风险

但需要注意总仓位限制，避免过度杠杆化。

## 配置

在 `backend/config/config.json` 中：
- `universe`: 包含所有杠杆ETF（已添加）
- `leveraged_etfs`: 杠杆ETF列表（用于参考）

## 监控

前端会显示杠杆ETF的持仓和P&L，与普通股票一样处理。但需要注意：
- 杠杆ETF的P&L波动会更大
- 需要更频繁地监控仓位
- 考虑设置止损或定期调整

