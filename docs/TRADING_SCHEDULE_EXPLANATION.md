# 交易系统运行时间说明

**更新时间**: 2025-11-14

---

## ⏰ 市场开放时间

### 美股交易时间（EST/EDT）

**交易时段**: 
- **开盘**: 9:30 AM EST（美东时间上午9:30）
- **收盘**: 4:00 PM EST（美东时间下午4:00）

**交易日**: 
- 周一至周五（排除节假日）
- 排除周末（周六、周日）
- 排除美国股市节假日（元旦、独立日、感恩节、圣诞节等）

**代码位置**: `backend/src/utils/trading_days.py` 第 117-141 行

```python
market_open = dt_time(9, 30)  # 9:30 AM
market_close = dt_time(16, 0)  # 4:00 PM
return market_open <= current_time <= market_close
```

---

## 🔄 系统运行时间表

### 市场开放时（9:30 AM - 4:00 PM EST）

#### 1. **自动交易** ✅

**启动时间**: 市场开盘后（9:30 AM EST）

**执行频率**: 
- **每30分钟自动执行一次**
- 首次执行：页面加载时如果市场已开放，立即执行一次
- 后续执行：每30分钟自动执行

**执行内容**:
1. ✅ 运行对话（AI分析）
2. ✅ 执行交易（创建市场订单并立即成交）
3. ✅ 更新投资组合
4. ✅ 记录净值历史

**代码位置**: `frontend/monitor.html` 第 3014-3020 行

```javascript
const TRADING_INTERVAL = 30 * 60 * 1000;  // 30 minutes
tradeCheckTimer = setInterval(smartAutoTrade, TRADING_INTERVAL);
// Execute immediately once
smartAutoTrade();
```

**执行时间点示例**:
- 9:30 AM - 首次执行（市场开盘时）
- 10:00 AM - 第二次执行
- 10:30 AM - 第三次执行
- 11:00 AM - 第四次执行
- ... 依此类推，每30分钟一次
- 3:30 PM - 最后一次执行（收盘前30分钟）

#### 2. **手动交易** ✅

**可用时间**: 市场开放时（9:30 AM - 4:00 PM EST）

**操作**: 点击 "Start Trading" 按钮

**执行内容**: 与自动交易相同

---

### 市场关闭时（其他时间）

#### 1. **自动交易** ❌

**状态**: 自动停止，不执行

**显示**: "Market Closed - Manual Only"

**代码位置**: `frontend/monitor.html` 第 3022-3024 行

```javascript
// Market is closed: do not start auto-trade
console.log('[Auto Trade] Market is closed, auto-trade disabled (manual only)');
updateAutoTradeStatus('Market Closed - Manual Only');
```

#### 2. **手动分析** ✅

**可用时间**: 任何时间（包括市场关闭时）

**操作**: 点击 "Run Analysis" 按钮

**执行内容**:
1. ✅ 运行对话（AI分析）
2. ✅ 生成讨论记录
3. ❌ **不执行交易**（不创建订单）

**代码位置**: `backend/src/api/server.py` 第 525-527 行

```python
if not is_market_open:
    # 市场关闭：只运行对话和分析，不执行交易
    log_print(f"[TRADING CYCLE] Market is closed. Running analysis only (no trading)...")
```

---

## 📋 详细时间表

### 周一至周五（交易日）

| 时间 | 市场状态 | 自动交易 | 手动操作 | 执行内容 |
|------|---------|---------|---------|---------|
| **00:00 - 9:29 AM** | ❌ 关闭 | ❌ 停止 | ✅ 可运行分析 | 对话、分析（不交易） |
| **9:30 AM** | ✅ **开盘** | ✅ **启动** | ✅ 可交易 | **对话 + 交易** |
| **9:30 AM - 4:00 PM** | ✅ 开放 | ✅ 每30分钟执行 | ✅ 可交易 | **对话 + 交易** |
| **4:00 PM** | ❌ **收盘** | ❌ **停止** | ✅ 可运行分析 | 对话、分析（不交易） |
| **4:01 PM - 23:59 PM** | ❌ 关闭 | ❌ 停止 | ✅ 可运行分析 | 对话、分析（不交易） |

### 周末和节假日

| 时间 | 市场状态 | 自动交易 | 手动操作 | 执行内容 |
|------|---------|---------|---------|---------|
| **全天** | ❌ 关闭 | ❌ 停止 | ✅ 可运行分析 | 对话、分析（不交易） |

---

## 🔍 关键逻辑说明

### 1. 市场状态检测

**位置**: `backend/src/utils/trading_days.py` 第 117-141 行

**逻辑**:
```python
def is_market_open(check_datetime: Optional[datetime] = None) -> bool:
    # 检查是否是交易日（排除周末和节假日）
    if not is_trading_day(check_date):
        return False
    
    # 检查时间（9:30 AM - 4:00 PM）
    market_open = dt_time(9, 30)  # 9:30 AM
    market_close = dt_time(16, 0)  # 4:00 PM
    return market_open <= current_time <= market_close
```

### 2. 自动交易启动

**位置**: `frontend/monitor.html` 第 3008-3030 行

**逻辑**:
```javascript
// 检查市场状态
const isOpen = await isMarketOpen();
if (isOpen) {
    // 市场开放：启动30分钟定时器
    const TRADING_INTERVAL = 30 * 60 * 1000;  // 30分钟
    tradeCheckTimer = setInterval(smartAutoTrade, TRADING_INTERVAL);
    // 立即执行一次
    smartAutoTrade();
} else {
    // 市场关闭：不启动定时器
    updateAutoTradeStatus('Market Closed - Manual Only');
}
```

### 3. 市场状态监控

**位置**: `frontend/monitor.html` 第 7775-7820 行

**逻辑**:
- 每5分钟检查一次市场状态
- 市场从关闭→开放：自动启动自动交易
- 市场从开放→关闭：自动停止自动交易

---

## 📊 执行时间点示例

### 示例：2025-11-14（周五）

| 时间 | 事件 | 说明 |
|------|------|------|
| **9:30 AM** | 🟢 市场开盘 | 自动交易启动，立即执行第一次 |
| **10:00 AM** | ✅ 自动执行 | 第二次自动交易 |
| **10:30 AM** | ✅ 自动执行 | 第三次自动交易 |
| **11:00 AM** | ✅ 自动执行 | 第四次自动交易 |
| **11:30 AM** | ✅ 自动执行 | 第五次自动交易 |
| **12:00 PM** | ✅ 自动执行 | 第六次自动交易 |
| **12:30 PM** | ✅ 自动执行 | 第七次自动交易 |
| **1:00 PM** | ✅ 自动执行 | 第八次自动交易 |
| **1:30 PM** | ✅ 自动执行 | 第九次自动交易 |
| **2:00 PM** | ✅ 自动执行 | 第十次自动交易 |
| **2:30 PM** | ✅ 自动执行 | 第十一次自动交易 |
| **3:00 PM** | ✅ 自动执行 | 第十二次自动交易 |
| **3:30 PM** | ✅ 自动执行 | 第十三次自动交易（最后一次） |
| **4:00 PM** | 🔴 市场收盘 | 自动交易停止 |

**总计**: 13次自动交易（9:30 AM, 10:00 AM, ..., 3:30 PM）

---

## ⚠️ 重要说明

### 时区问题

**当前设置**: 使用服务器本地时间

**注意**: 
- 如果服务器不在EST时区，需要调整时区设置
- 建议服务器时区设置为EST/EDT（美东时间）

**代码位置**: `backend/src/utils/trading_days.py` 第 135-139 行

```python
# 检查时间（使用本地时间，假设服务器在EST时区或用户配置的时区）
market_open = dt_time(9, 30)  # 9:30 AM
market_close = dt_time(16, 0)  # 4:00 PM
current_time = check_datetime.time()
```

### 对话和分析

**运行时间**: 
- ✅ **任何时间**都可以运行对话和分析
- ✅ 市场关闭时也可以运行（只运行分析，不交易）

### 交易执行

**运行时间**: 
- ✅ **仅市场开放时**（9:30 AM - 4:00 PM EST）
- ❌ 市场关闭时不执行交易

---

## ✅ 总结

### 对话和分析
- **运行时间**: 任何时间（24/7）
- **市场开放时**: 自动每30分钟执行 + 可手动
- **市场关闭时**: 只能手动，不执行交易

### 交易执行
- **运行时间**: 仅市场开放时（9:30 AM - 4:00 PM EST）
- **执行频率**: 每30分钟自动执行一次
- **市场关闭时**: 不执行交易

### 关键时间点
- **9:30 AM EST**: 市场开盘，自动交易启动
- **4:00 PM EST**: 市场收盘，自动交易停止
- **每30分钟**: 市场开放时自动执行一次交易

