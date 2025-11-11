# risk_on 和 risk_off 说明

## 什么是 risk_on / risk_off？

`risk_on` 和 `risk_off` 是 Market Analyst 使用的市场情绪/风险偏好指标，用于描述投资者的风险承受意愿。

### risk_on（风险偏好开启）
- **含义**：投资者愿意承担更多风险，追求更高回报
- **市场特征**：
  - 通常对应**牛市**或**看涨**市场
  - 投资者情绪乐观
  - 资金流向高风险资产（股票、成长股、科技股等）
  - VIX 通常较低
  - 市场波动性较小
- **交易建议**：
  - 适合买入股票
  - 适合持有成长股
  - 适合增加仓位

### risk_off（风险偏好关闭）
- **含义**：投资者规避风险，寻求安全资产
- **市场特征**：
  - 通常对应**熊市**或**看跌**市场
  - 投资者情绪悲观或谨慎
  - 资金流向安全资产（债券、黄金、现金等）
  - VIX 通常较高
  - 市场波动性较大
- **交易建议**：
  - 适合卖出股票或减仓
  - 适合持有现金或债券
  - 适合使用对冲工具（如反向ETF）

### neutral（中性）
- **含义**：市场情绪平衡，无明显风险偏好
- **市场特征**：
  - 市场横盘整理
  - 投资者观望
  - 无明显趋势
- **交易建议**：
  - 保持当前仓位
  - 等待更明确的信号

## 在系统中的使用

### Market Analyst 输出
Market Analyst 的 `stance` 字段可以是：
- `risk_on` - 风险偏好开启（看涨）
- `risk_off` - 风险偏好关闭（看跌）
- `neutral` - 中性

### 代码中的处理
在 `backend/src/agents/multi_analyst_system.py` 中：
```python
bullish_count = sum(1 for s in stances if "bullish" in s.lower() or "risk_on" in s.lower())
```
这表明 `risk_on` 被视为与 `bullish` 相同的看涨信号。

### 与传统的 bullish/bearish 的关系
- `risk_on` ≈ `bullish`（看涨）
- `risk_off` ≈ `bearish`（看跌）
- `neutral` = `neutral`（中性）

## 为什么使用 risk_on/risk_off？

1. **更精确的描述**：不仅描述市场方向，还描述投资者的风险承受意愿
2. **资产轮动**：可以更好地描述资金在不同资产类别之间的流动
3. **风险管理**：帮助Trader Agent更好地理解市场情绪，做出更合适的交易决策

