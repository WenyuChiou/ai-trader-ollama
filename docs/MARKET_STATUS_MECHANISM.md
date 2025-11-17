# 市场状态判断机制确认文档

## 概述

本文档确认整个系统中市场状态判断的机制，确保所有组件使用一致的逻辑。

## 核心判断函数

### 位置
`backend/src/utils/trading_days.py` → `is_market_open()`

### 判断逻辑

```python
def is_market_open(check_datetime: Optional[datetime] = None) -> bool:
    """
    检查市场是否开盘（美股：周一至周五 9:30 AM - 4:00 PM EST/EDT，排除节假日）
    
    判断标准：
    1. 必须是交易日（排除周末和节假日）
    2. 时间必须在 9:30 AM - 4:00 PM ET 之间（不包括 4:00 PM）
    """
```

### 关键特性

1. **时区处理**
   - 使用 `pytz.timezone('America/New_York')` 获取美东时区
   - 自动处理 EST/EDT 转换（夏令时）
   - 如果 `check_datetime` 为 `None`，直接获取当前美东时间（最可靠）

2. **交易日检查**
   - 排除周末（周六、周日）
   - 排除固定日期节假日（元旦、独立日、圣诞节）
   - 排除可变日期节假日（感恩节、劳动节、阵亡将士纪念日、马丁路德金日、总统日、哥伦布日）

3. **交易时间检查**
   - 开盘时间：9:30 AM ET
   - 收盘时间：4:00 PM ET（不包括 4:00 PM，即 `current_time < 16:00`）
   - 判断条件：`9:30 <= current_time < 16:00`

## 系统各组件使用情况

### 1. Trading Cycle (`backend/src/orchestrator/trading_cycle.py`)

#### 调用位置
- **位置1**（第313-315行）：确定订单日期
  ```python
  from src.utils.trading_days import is_market_open as check_market_open
  is_market_open = check_market_open(None)  # 传入 None 直接获取美东时间
  ```

- **位置2**（第744-746行）：确定是否允许交易
  ```python
  from src.utils.trading_days import is_market_open as check_market_open
  is_market_open = check_market_open(None)  # 传入 None 直接获取美东时间
  ```

- **位置3**（第1288-1289行）：双重检查（订单创建前）
  ```python
  from src.utils.trading_days import is_market_open as double_check_market
  market_open_double_check = double_check_market(None)
  ```

#### 使用逻辑

1. **`is_market_open`**：实际市场状态（从 `is_market_open()` 函数获取）
2. **`is_market_open_for_simulation`**：用于控制是否允许交易的标志
   - 如果 `end` 参数存在（多日模拟）：`is_market_open_for_simulation = is_market_open`
   - 如果市场开放：`is_market_open_for_simulation = True`
   - 如果市场关闭：`is_market_open_for_simulation = False`

3. **订单创建逻辑**：
   ```python
   if should_create_orders:
       # 只有在 should_create_orders=True 时才创建订单
       # should_create_orders 的确定逻辑：
       # - 如果 is_market_open_for_simulation=False → should_create_orders=False
       # - 如果今天已有订单 → should_create_orders=False（避免重复）
       # - 如果市场开放且无现有订单 → should_create_orders=True
   ```

4. **双重检查机制**：
   - 在创建订单前，再次调用 `is_market_open(None)` 确认市场状态
   - 如果双重检查显示市场关闭，即使 `is_market_open_for_simulation=True`，也不创建订单

### 2. API 端点 (`backend/src/api/server.py`)

#### 端点
`GET /api/market/is-open`

#### 实现
```python
@app.get("/api/market/is-open")
async def check_market_open():
    from src.utils.trading_days import is_market_open
    import pytz
    
    et_tz = pytz.timezone('America/New_York')
    et_time = datetime.now(et_tz)
    market_open = is_market_open(None)  # 传入None让函数直接获取美东时间
    
    return {
        "ok": True,
        "is_open": market_open,
        "timestamp": et_time.isoformat(),
        "eastern_time": et_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
        "current_et_time": current_time.strftime('%H:%M:%S'),
        "market_hours": "9:30 AM - 4:00 PM ET",
        "minutes_until_open": minutes_until_open,
        "minutes_until_close": minutes_until_close,
    }
```

#### 特点
- 使用相同的 `is_market_open(None)` 函数
- 返回详细的时间信息（ET时间、距离开盘/收盘时间等）
- 提供 CORS 支持

### 3. Trader Agent (`backend/src/agents/trader_agent.py`)

#### 参数
```python
def run_trader(
    ...,
    is_market_open: bool = True,  # CRITICAL: 市场状态
) -> Dict[str, Any]:
```

#### 使用逻辑
- 如果 `is_market_open=False`，Trader Agent **不会生成任何订单**
- 这是第一道防线，在任何订单生成逻辑之前检查
- 即使后续代码有bug，也不会在市场关闭时生成订单

### 4. 前端 (`frontend/monitor.html`)

#### 调用方式
```javascript
async function isMarketOpen(useCache = true, silent = false) {
    const r = await fetch(`${getApiBase()}/api/market/is-open`);
    const j = await r.json();
    const isOpen = j.is_open !== undefined ? j.is_open : false;
    return !!isOpen;
}
```

#### Fallback 机制
如果 API 调用失败或超时（5秒），使用客户端时间估算：
```javascript
function estimateMarketStatusFromTime() {
    const now = new Date();
    const day = now.getDay();  // 0 = Sunday, 6 = Saturday
    
    // Convert to Eastern Time (handles DST automatically)
    const etFormatter = new Intl.DateTimeFormat('en-US', {
        timeZone: 'America/New_York',
        hour: 'numeric',
        minute: 'numeric',
        hour12: false
    });
    const etParts = etFormatter.formatToParts(now);
    const etHour = parseInt(etParts.find(p => p.type === 'hour').value);
    const etMinute = parseInt(etParts.find(p => p.type === 'minute').value);
    
    // Check if weekday (Monday=1 to Friday=5)
    const isWeekday = day >= 1 && day <= 5;
    // Check if trading hours (9:30 AM - 4:00 PM ET)
    const isTradingHours = (etHour > 9 || (etHour === 9 && etMinute >= 30)) && etHour < 16;
    
    return isWeekday && isTradingHours;
}
```

#### 特点
- 使用缓存机制（30秒 TTL）减少 API 调用
- 5秒超时，快速 fallback
- Fallback 使用 `Intl.DateTimeFormat` 自动处理 DST

## 市场状态判断流程图

```
┌─────────────────────────────────────────────────────────────┐
│                    is_market_open(None)                      │
│                  (backend/src/utils/trading_days.py)         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  1. 获取当前美东时间 (ET)              │
        │     datetime.now(pytz.timezone(       │
        │       'America/New_York'))            │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  2. 检查是否是交易日                  │
        │     - 排除周末 (周六、周日)           │
        │     - 排除节假日                      │
        └───────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │  3. 检查交易时间                      │
        │     9:30 AM <= current_time < 4:00 PM │
        └───────────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ 返回 True/False│
                    └───────────────┘
```

## 关键检查点

### 1. 时区处理
- ✅ 使用 `pytz.timezone('America/New_York')` 自动处理 EST/EDT
- ✅ 所有调用都传入 `None`，让函数直接获取美东时间
- ✅ 避免本地时区转换错误

### 2. 交易日检查
- ✅ 排除周末
- ✅ 排除固定日期节假日
- ✅ 排除可变日期节假日

### 3. 交易时间检查
- ✅ 开盘：9:30 AM ET（包括）
- ✅ 收盘：4:00 PM ET（不包括，即 `current_time < 16:00`）

### 4. 双重检查机制
- ✅ Trading Cycle 在创建订单前进行双重检查
- ✅ Trader Agent 在生成订单前检查市场状态

### 5. 错误处理
- ✅ 如果 `pytz` 未安装，使用 fallback
- ✅ 前端有 fallback 机制（客户端时间估算）
- ✅ API 调用有超时机制（5秒）

## 测试建议

### 1. 测试市场开放时间
- 9:30 AM ET：应该返回 `True`
- 10:00 AM ET：应该返回 `True`
- 3:59 PM ET：应该返回 `True`
- 4:00 PM ET：应该返回 `False`
- 4:01 PM ET：应该返回 `False`

### 2. 测试周末
- 周六：应该返回 `False`
- 周日：应该返回 `False`

### 3. 测试节假日
- 元旦（1月1日）：应该返回 `False`
- 独立日（7月4日）：应该返回 `False`
- 圣诞节（12月25日）：应该返回 `False`
- 感恩节（11月第4个周四）：应该返回 `False`

### 4. 测试时区转换
- 在不同时区运行系统，确保都使用美东时间
- 测试 EST/EDT 转换（3月第2个周日和11月第1个周日）

## 已知问题和限制

### 1. 节假日列表可能不完整
- 当前只包含主要节假日
- 可能遗漏一些特殊交易日（如提前收盘日）

### 2. Fallback 机制
- 如果 `pytz` 未安装，使用本地时间（可能不准确）
- 前端 fallback 不检查节假日，只检查周末和交易时间

### 3. 时区依赖
- 系统依赖 `pytz` 库正确处理时区
- 如果系统时区设置错误，可能影响判断

## 改进建议

1. **扩展节假日列表**
   - 添加更多美国股市节假日
   - 考虑提前收盘日（如感恩节前一天）

2. **增强日志**
   - 记录每次市场状态检查的详细信息
   - 记录时区转换过程

3. **添加单元测试**
   - 测试各种时间场景
   - 测试节假日判断
   - 测试时区转换

4. **监控和告警**
   - 监控市场状态判断的准确性
   - 如果判断错误，发送告警

## 总结

市场状态判断机制的核心是 `is_market_open()` 函数，它：
1. 使用美东时区（自动处理 EST/EDT）
2. 检查交易日（排除周末和节假日）
3. 检查交易时间（9:30 AM - 4:00 PM ET）

所有系统组件都使用这个函数，确保一致性。Trading Cycle 有双重检查机制，Trader Agent 有第一道防线，前端有 fallback 机制，确保系统在各种情况下都能正确判断市场状态。

