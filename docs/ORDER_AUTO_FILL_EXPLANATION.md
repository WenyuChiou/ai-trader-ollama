# 📋 订单自动成交机制说明

> **为什么订单会突然成交？净值为什么会上升？**

---

## 🔄 自动成交机制（这是正常功能）

### 1. 前端自动检查机制

**前端每 10 秒自动检查 pending 订单：**

```javascript
// frontend/monitor.html 第 1534 行
const ORDER_CHECK_INTERVAL = 10000; // 10 seconds

// 每 10 秒调用一次
async function checkPendingOrders() {
    // 调用 API: /api/trading/check-pending-orders
    // 如果市场开盘，使用实时价格检查订单是否可以成交
}
```

**触发条件：**
- ✅ 市场开盘时
- ✅ 每 10 秒自动检查一次
- ✅ 使用实时价格判断

---

### 2. 订单成交逻辑

**BUY 订单成交条件：**
```python
# backend/src/data/order_manager.py 第 164 行
if current_price <= limit_price:
    # 订单自动成交
    fill_price = current_price  # 使用实际市价作为成交价
```

**示例：**
- 订单：BUY MU @ $241.11 (限价)
- 当前价格：$241.00
- 结果：✅ 自动成交（因为 $241.00 <= $241.11）
- 成交价：$241.00（实际市价）

---

### 3. 订单执行流程

```
1. 订单创建（PENDING）
   ↓
2. 前端每 10 秒检查（市场开盘时）
   ↓
3. 使用实时价格判断
   ↓
4. 如果价格满足条件 → 自动成交（FILLED）
   ↓
5. 更新 portfolio（现金减少，持仓增加）
   ↓
6. 净值重新计算（使用当前实时价格）
```

---

## 💰 净值上升的原因（正常现象）

### 净值计算公式

```
净值 = 现金 + 持仓市值
持仓市值 = Σ(持仓数量 × 当前实时价格)
```

### 为什么净值会上升？

**示例：**

1. **订单成交时：**
   - BUY MU x1 @ $241.11
   - 现金减少：$241.11
   - 持仓成本：$241.11

2. **净值计算（使用当前实时价格）：**
   - 如果当前价格 = $242.00
   - 持仓市值 = 1 × $242.00 = $242.00
   - 净值 = 现金 + $242.00

3. **净值变化：**
   - 成交时净值 = 现金 + $241.11（成本价）
   - 当前净值 = 现金 + $242.00（实时价）
   - **净值上升 = $0.89**（这是未实现盈亏）

---

## ✅ 这是正常行为

### 为什么这是正常的？

1. **订单成交是自动的**
   - ✅ 系统设计如此
   - ✅ 市场开盘时自动检查
   - ✅ 价格满足条件就成交

2. **净值上升是正常的**
   - ✅ 反映持仓的未实现盈亏
   - ✅ 使用实时价格计算（标准做法）
   - ✅ 如果价格下跌，净值也会下降

3. **这是市场波动**
   - ✅ 不是系统错误
   - ✅ 反映真实的市场价格变化
   - ✅ 持仓盈利时净值上升，亏损时净值下降

---

## 🔍 如何验证是否正常

### 检查订单成交记录

```powershell
# 查看已成交订单
Get-Content data\logs\filled_orders.jsonl | ConvertFrom-Json | Select-Object -Last 5
```

### 检查净值计算

```powershell
# 查看 portfolio 状态
Get-Content data\logs\portfolio_state.json | ConvertFrom-Json
```

### 验证价格数据

```python
# 检查成交价和当前价格
import yfinance as yf
ticker = yf.Ticker("MU")
current_price = ticker.fast_info.get("lastPrice")
print(f"当前价格: ${current_price:.2f}")
```

---

## ⚠️ 如果净值异常上升（可能的问题）

### 问题 1: 价格数据错误

**症状：**
- 净值突然大幅上升
- 持仓市值异常高

**检查：**
```python
# 检查价格是否合理
import yfinance as yf
ticker = yf.Ticker("MU")
info = ticker.fast_info
print(f"当前价格: {info.get('lastPrice')}")
print(f"昨日收盘: {info.get('previousClose')}")
```

### 问题 2: 订单重复执行

**症状：**
- 同一订单被执行多次
- 持仓数量异常

**检查：**
```powershell
# 检查是否有重复订单
Get-Content data\logs\filled_orders.jsonl | ConvertFrom-Json | Group-Object symbol, action | Where-Object {$_.Count -gt 1}
```

### 问题 3: 净值计算错误

**症状：**
- 净值与持仓市值不匹配
- 现金余额异常

**检查：**
```python
# 手动计算净值
portfolio = Portfolio.load("data/logs/portfolio_state.json")
current_prices = get_current_prices(portfolio.positions.keys())
calculated_value = portfolio.cash + sum(qty * current_prices[sym] for sym, qty in portfolio.positions.items())
print(f"计算净值: ${calculated_value:.2f}")
```

---

## 🛠️ 如何控制自动成交

### 方法 1: 停止前端自动检查

**修改前端代码：**
```javascript
// frontend/monitor.html
// 注释掉或删除自动检查
// orderCheckTimer = setInterval(...)
```

### 方法 2: 手动控制订单检查

**只在需要时检查：**
```javascript
// 移除自动检查，只在点击按钮时检查
// 或者增加检查间隔（例如 60 秒）
const ORDER_CHECK_INTERVAL = 60000; // 60 seconds
```

### 方法 3: 使用更严格的成交条件

**修改订单成交逻辑：**
```python
# backend/src/data/order_manager.py
# 可以添加价格差异检查
if current_price <= limit_price:
    price_diff = (limit_price - current_price) / limit_price
    if price_diff > 0.01:  # 价格差异 > 1% 才成交
        # 成交
```

---

## 📊 当前状态分析

从你的截图看：

**已成交订单（FILLED）：**
- MU: 1 股 @ $241.11
- AEP: 2 股 @ $122.73
- SBUX: 3 股 @ $86.42

**待成交订单（PENDING）：**
- AMGN: 1 股 @ $324.31
- AVGO: 1 股 @ $359.11
- CEG: 1 股 @ $361.65
- TSLA: 1 股 @ $446.12

**可能的原因：**
1. ✅ MU, AEP, SBUX 的当前价格 <= 限价 → 自动成交
2. ⏳ AMGN, AVGO, CEG, TSLA 的当前价格 > 限价 → 保持 PENDING

**净值上升：**
- 如果已成交股票的当前价格 > 成交价
- 净值会上升（反映未实现盈利）
- 这是正常的市场波动

---

## 💡 建议

1. **这是正常行为**
   - 系统按设计工作
   - 自动成交是预期功能
   - 净值上升反映持仓盈利

2. **如果担心异常**
   - 检查价格数据是否合理
   - 检查订单是否重复执行
   - 检查净值计算是否正确

3. **如果需要调整**
   - 可以增加检查间隔
   - 可以添加价格差异检查
   - 可以禁用自动检查

---

**最后更新**: 2025-01-XX

