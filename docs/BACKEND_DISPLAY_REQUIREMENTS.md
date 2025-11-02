# 📊 后端展示需求

## 🎯 后端功能定义

**后端职责**: 根据持仓部位净值与当前市场价格，进行损益展示、交易纪录展示等相关展示

## 📋 展示功能清单

### 1. **损益展示** (P&L Display)

#### 1.1 实时盈亏计算
- **输入**: 
  - 持仓部位 (Portfolio.positions)
  - 当前市场价格 (last_prices)
  - 持仓成本 (需要记录)
- **计算**:
  - 单股盈亏 = (当前价格 - 成本价格) × 持有数量
  - 总盈亏 = Σ 单股盈亏
  - 盈亏百分比 = (当前净值 - 初始净值) / 初始净值 × 100%
- **展示**:
  - 总盈亏金额
  - 总盈亏百分比
  - 单股盈亏明细
  - 盈亏分布图表

#### 1.2 持仓净值
- **计算**:
  - 持仓市值 = Σ (股票价格 × 持有数量)
  - 总净值 = 现金 + 持仓市值
- **展示**:
  - 现金余额
  - 持仓市值
  - 总净值
  - 净值变化曲线

#### 1.3 持仓明细
- **展示**:
  - 股票代码
  - 持有数量
  - 成本价格（平均成本）
  - 当前价格
  - 市值
  - 盈亏金额
  - 盈亏百分比
  - 持仓占比

### 2. **交易纪录展示** (Trade History Display)

#### 2.1 交易历史列表
- **展示**:
  - 交易时间
  - 股票代码
  - 交易类型 (BUY/SELL)
  - 交易价格
  - 交易数量
  - 交易金额
  - 交易状态 (成功/失败/部分成交)
  - 交易原因/备注

#### 2.2 交易统计
- **展示**:
  - 总交易次数
  - 买入次数 / 卖出次数
  - 总交易金额
  - 平均交易价格
  - 交易日期分布

#### 2.3 交易执行状态
- **展示**:
  - 待执行订单
  - 已执行订单
  - 失败订单
  - 部分成交订单

### 3. **仓位展示** (Position Display)

#### 3.1 仓位分布
- **展示**:
  - 单股仓位占比
  - 仓位集中度
  - 仓位分布饼图/柱状图

#### 3.2 仓位状态
- **展示**:
  - 持仓股票列表
  - 空仓股票列表
  - 仓位调整建议（来自 Risk Analyst）

### 4. **风险指标展示** (Risk Metrics Display)

#### 4.1 风险指标
- **展示**:
  - 整体风险等级（来自 Risk Analyst）
  - 风险评分
  - 仓位集中度
  - 单股暴露度
  - 总仓位暴露度

#### 4.2 风险警告
- **展示**:
  - 风险警告列表（来自 Risk Analyst）
  - 高风险股票列表
  - 安全股票列表

### 5. **绩效统计展示** (Performance Display)

#### 5.1 绩效指标
- **计算**:
  - 总收益率
  - 年化收益率
  - 夏普比率（如果有基准）
  - 最大回撤
- **展示**:
  - 绩效指标数值
  - 绩效趋势图

#### 5.2 绩效对比
- **展示**:
  - 与基准对比（如果有）
  - 历史绩效对比

## 🗂️ 数据模型

### Portfolio 扩展需求

```python
@dataclass
class Position:
    symbol: str
    quantity: int
    avg_cost: float  # 平均成本价格
    last_price: float  # 当前价格
    market_value: float  # 市值 = quantity * last_price
    unrealized_pnl: float  # 未实现盈亏
    unrealized_pnl_pct: float  # 未实现盈亏百分比

@dataclass
class TradeRecord:
    timestamp: str
    symbol: str
    action: str  # BUY/SELL
    price: float
    quantity: int
    amount: float  # price * quantity
    status: str  # SUCCESS/FAILED/PARTIAL
    reason: str  # 交易原因

@dataclass
class PortfolioSnapshot:
    timestamp: str
    cash: float
    positions: Dict[str, Position]
    total_value: float
    total_pnl: float
    total_pnl_pct: float
```

### Trade Logger 扩展需求

```python
class TradeLogger:
    def log(self, record: TradeRecord):
        # 记录交易
        pass
    
    def get_trades(self, symbol: str = None, start: str = None, end: str = None):
        # 获取交易记录
        pass
    
    def get_statistics(self):
        # 获取交易统计
        pass
```

## 🔄 数据流

### 后端展示数据流

```
Portfolio (持仓数据)
    ↓
当前市场价格 (last_prices)
    ↓
损益计算模块
    ↓
损益展示数据
    ↓
前端展示

Trade Logger (交易记录)
    ↓
交易记录查询模块
    ↓
交易记录展示数据
    ↓
前端展示

Risk Analyst (风险评估)
    ↓
风险指标计算模块
    ↓
风险指标展示数据
    ↓
前端展示
```

## 📝 实现优先级

### 优先级 1: 基础展示（高优先级）

1. **损益展示**
   - 持仓净值计算
   - 盈亏计算
   - 持仓明细

2. **交易记录展示**
   - 交易历史列表
   - 交易统计

### 优先级 2: 增强展示（中优先级）

3. **仓位展示**
   - 仓位分布
   - 仓位状态

4. **风险指标展示**
   - 风险指标
   - 风险警告

### 优先级 3: 高级展示（低优先级）

5. **绩效统计展示**
   - 绩效指标
   - 绩效对比

## 🔧 技术实现建议

### API 端点建议

```
GET /api/portfolio
  - 返回当前持仓和净值

GET /api/portfolio/pnl
  - 返回损益明细

GET /api/trades
  - 返回交易记录列表

GET /api/trades/statistics
  - 返回交易统计

GET /api/positions
  - 返回仓位明细

GET /api/risk
  - 返回风险指标

GET /api/performance
  - 返回绩效统计
```

### WebSocket 实时更新

```
WS /ws/portfolio
  - 实时推送持仓变化

WS /ws/prices
  - 实时推送价格更新
  - 触发损益重新计算

WS /ws/trades
  - 实时推送新交易
```

---

**文档状态**: ✅ 需求已记录  
**更新日期**: 2025-11-02

