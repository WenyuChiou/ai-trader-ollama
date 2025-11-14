# 测试步骤（重启后）

## ✅ API重启状态

- Windows Service: Stopped（但端口8000被占用，可能通过其他方式运行）
- 端口8000: 被占用（API可能正在运行）

---

## 🧪 测试步骤

### 步骤1: 验证API是否运行

**打开浏览器访问**:
```
http://localhost:8000/api/market/status
```

**或使用PowerShell**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/market/status"
```

**预期结果**: 
- ✅ 返回JSON响应
- ✅ 包含`is_open`字段

**如果API未响应**:
- 需要手动启动API（见下方）

---

### 步骤2: 如果API未运行，手动启动

**推荐方式: 窗口模式（用于测试）**

1. 打开新的PowerShell窗口
2. 运行：
   ```powershell
   cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
   powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
   ```
3. 保持窗口打开（可以看到实时日志）

---

### 步骤3: 运行一次交易循环测试

**方法A: 通过前端（推荐）**

1. 打开前端：
   ```
   http://localhost:8080/monitor.html
   ```
2. 点击 **"Run Analysis"** 或 **"Start Trading"** 按钮
3. 等待完成（约60-100秒）
4. 查看结果

**方法B: 通过API**

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/trading/execute-trade" -Method POST
```

---

### 步骤4: 检查订单状态

**在前端查看**:
- 打开 "Trade Details" 表格
- 检查订单状态列

**关键检查点**:
- ✅ **所有新订单状态应该是 FILLED**（不是PENDING）
- ✅ 订单时间正确（使用placed_at）
- ✅ BUY订单有正确的价格和数量
- ✅ SELL订单有realized_pnl记录

**或通过API检查**:
```powershell
$trades = Invoke-RestMethod -Uri "http://localhost:8000/api/trades/recent?limit=20"
$trades.trades | Where-Object { $_.status -eq 'FILLED' } | Measure-Object | Select-Object -ExpandProperty Count
```

---

### 步骤5: 验证现金检查

**检查投资组合**:
```powershell
$portfolio = Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/state"
Write-Host "Cash: `$$($portfolio.cash)"
Write-Host "Total Value: `$$($portfolio.total_value)"
```

**验证**:
- ✅ 现金金额合理（不应该为负数）
- ✅ 如果创建了BUY订单，现金应该减少
- ✅ 总订单成本 ≤ 可用现金

---

### 步骤6: 验证持仓检查

**检查持仓**:
```powershell
$portfolio = Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/real-time"
$portfolio.positions_detail
```

**验证**:
- ✅ 如果创建了SELL订单，持仓数量应该减少
- ✅ SELL订单数量 ≤ 持仓数量

---

### 步骤7: 检查日志输出

**如果使用窗口模式**:
- 查看PowerShell窗口的输出

**关键日志信息**（应该看到）:
- ✅ `[TRADER] Checking X current positions for sell opportunities...`
- ✅ `[TRADER] Position SYMBOL: X shares @ $Y avg, current $Z, P&L=$W...`
- ✅ `[MARKET ORDER] BUY/SELL ... (FILLED immediately...)`
- ✅ `[CASH TRACKING] Order for SYMBOL: cost=$X, remaining cash=$Y, portfolio cash=$Z`

**不应该看到**:
- ❌ `status: PENDING`（除了旧的pending订单）
- ❌ `insufficient cash`（除非真的现金不足）
- ❌ `insufficient shares`（除非真的持仓不足）

---

## ✅ 成功标准

### 所有测试通过

- ✅ API正常运行
- ✅ 交易循环成功执行
- ✅ **所有新订单状态是FILLED**（不是PENDING）
- ✅ 现金检查正确（BUY订单不超过可用现金）
- ✅ 持仓检查正确（SELL订单不超过持仓数量）
- ✅ 卖出订单持仓感知正常（显示所有持仓信息）
- ✅ FILLED状态保证正常（即使mark_order_filled失败也会设置FILLED）

---

## ⚠️ 如果发现问题

### 问题1: 订单仍然是PENDING

**可能原因**:
- API没有重启（代码没有加载）
- mark_order_filled()失败

**解决方法**:
1. 确认API已重启
2. 检查日志输出
3. 检查是否有异常信息

---

### 问题2: 现金检查失败

**可能原因**:
- portfolio.cash和remaining_cash不同步

**解决方法**:
1. 检查日志中的现金跟踪信息
2. 检查portfolio.cash和remaining_cash是否一致

---

### 问题3: 持仓检查失败

**可能原因**:
- 持仓信息不正确
- 卖出数量计算错误

**解决方法**:
1. 检查持仓状态
2. 检查日志中的持仓信息
3. 确认卖出数量不超过持仓数量

---

## 📋 快速测试命令

### 一键测试
```powershell
powershell -ExecutionPolicy Bypass -File .\test_api_simple.ps1
```

### 手动测试
```powershell
# 1. 检查API
Invoke-RestMethod -Uri "http://localhost:8000/api/market/status"

# 2. 检查投资组合
Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/state"

# 3. 检查订单
Invoke-RestMethod -Uri "http://localhost:8000/api/trades/recent?limit=10"

# 4. 运行交易循环
Invoke-RestMethod -Uri "http://localhost:8000/api/trading/execute-trade" -Method POST
```

---

**详细测试指南**: 查看 `docs/TESTING_GUIDE_AFTER_RESTART.md`

