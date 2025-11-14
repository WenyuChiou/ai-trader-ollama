# 重启后功能测试指南

**更新时间**: 2025-11-14  
**测试目标**: 验证所有修复是否正常工作

---

## 🧪 测试步骤

### 步骤1: 验证API运行状态

**检查API是否正常运行**:
```powershell
# 检查端口
Get-NetTCPConnection -LocalPort 8000

# 测试API响应
curl http://localhost:8000/api/market/status
```

**预期结果**:
- ✅ API正常运行（端口8000被占用）
- ✅ API返回JSON响应（包含market状态）

---

### 步骤2: 检查投资组合状态

**访问API端点**:
```powershell
# 检查投资组合
curl http://localhost:8000/api/portfolio/state
```

**或通过浏览器**:
```
http://localhost:8000/api/portfolio/state
```

**预期结果**:
- ✅ 返回投资组合信息（cash, positions, total_value）
- ✅ 现金金额正确
- ✅ 持仓信息正确

---

### 步骤3: 运行一次交易循环

**方法1: 通过前端**
1. 打开前端：`http://localhost:8080/monitor.html`
2. 点击 "Run Analysis" 或 "Start Trading" 按钮
3. 等待交易循环完成（约60-100秒）

**方法2: 通过API**
```powershell
# 执行交易循环
curl -X POST http://localhost:8000/api/trading/execute-trade
```

**预期结果**:
- ✅ 交易循环成功执行
- ✅ 返回订单信息
- ✅ 没有错误信息

---

### 步骤4: 检查订单状态

**检查订单**:
```powershell
# 检查最近的交易
curl http://localhost:8000/api/trades/recent?limit=10
```

**或通过前端**:
- 查看 "Trade Details" 表格
- 检查订单状态

**预期结果**:
- ✅ **所有订单状态应该是FILLED**（不是PENDING）
- ✅ 订单时间正确（使用placed_at）
- ✅ BUY订单有正确的价格和数量
- ✅ SELL订单有realized_pnl记录

---

### 步骤5: 验证现金检查

**检查投资组合**:
```powershell
curl http://localhost:8000/api/portfolio/state
```

**验证**:
- ✅ 现金金额合理（不应该为负数）
- ✅ 如果创建了BUY订单，现金应该减少
- ✅ 如果创建了SELL订单，现金应该增加

**计算验证**:
- 总订单成本 ≤ 可用现金
- 如果现金不足，订单数量应该被减少或跳过

---

### 步骤6: 验证持仓检查

**检查持仓**:
```powershell
curl http://localhost:8000/api/portfolio/real-time
```

**验证**:
- ✅ 如果创建了SELL订单，持仓数量应该减少
- ✅ 如果创建了BUY订单，持仓数量应该增加
- ✅ SELL订单数量 ≤ 持仓数量

---

### 步骤7: 检查日志输出

**查看后端日志**（如果使用窗口模式）:
- 检查PowerShell窗口的输出

**关键日志信息**:
- ✅ `[TRADER] Checking X current positions for sell opportunities...`
- ✅ `[TRADER] Position SYMBOL: X shares @ $Y avg, current $Z, P&L=$W...`
- ✅ `[MARKET ORDER] BUY/SELL ... (FILLED immediately...)`
- ✅ `[CASH TRACKING] Order for SYMBOL: cost=$X, remaining cash=$Y, portfolio cash=$Z`

**不应该看到**:
- ❌ `status: PENDING`（除了旧的pending订单）
- ❌ `insufficient cash`（除非真的现金不足）
- ❌ `insufficient shares`（除非真的持仓不足）

---

### 步骤8: 验证卖出订单持仓感知

**检查日志输出**:
- 应该看到每个持仓的详细信息：
  ```
  [TRADER] Position NVDA: 10 shares @ $150.25 avg, current $155.00, P&L=$47.50 (+3.16%), position_pct=15.2%
  ```

**验证**:
- ✅ 所有持仓都被检查
- ✅ 显示每个持仓的数量、成本、当前价格、损益、占比
- ✅ 卖出订单数量不超过持仓数量

---

### 步骤9: 验证FILLED状态保证

**检查订单状态**:
```powershell
# 检查最近的订单
curl http://localhost:8000/api/trades/recent?limit=20
```

**验证**:
- ✅ **所有新创建的订单状态都是FILLED**
- ✅ 没有PENDING状态的订单（除了旧的pending订单）
- ✅ 订单有fill_price字段
- ✅ 订单有filled_at字段

---

### 步骤10: 市场关闭测试（可选）

**如果当前是市场关闭时间**:
1. 点击 "Run Analysis" 按钮
2. 检查是否创建订单

**预期结果**:
- ✅ 可以运行分析（对话）
- ✅ **不应该创建任何订单**
- ✅ 返回消息："Market is closed. Running analysis only (no trading)..."

---

## 📋 测试检查清单

### 基础功能

- [ ] API正常运行
- [ ] 投资组合状态正确
- [ ] 交易循环可以执行

### 订单执行

- [ ] 所有订单状态是FILLED（不是PENDING）
- [ ] BUY订单正确执行
- [ ] SELL订单正确执行
- [ ] 订单时间正确（使用placed_at）

### 现金检查

- [ ] BUY订单不会超过可用现金
- [ ] 如果现金不足，订单数量被减少或跳过
- [ ] 现金使用正确计算

### 持仓检查

- [ ] SELL订单不会超过持仓数量
- [ ] 如果持仓不足，订单被跳过
- [ ] 持仓数量正确更新

### 卖出订单持仓感知

- [ ] 所有持仓都被检查
- [ ] 显示每个持仓的详细信息
- [ ] 卖出订单数量不超过持仓数量

### FILLED状态保证

- [ ] 所有新订单都是FILLED状态
- [ ] 没有PENDING状态的订单（除了旧的）
- [ ] 订单有完整的fill信息

---

## 🔍 问题排查

### 如果订单仍然是PENDING

**可能原因**:
1. API没有重启（代码没有加载）
2. mark_order_filled()失败（检查日志）

**解决方法**:
1. 确认API已重启
2. 检查日志输出
3. 检查是否有异常信息

---

### 如果现金检查失败

**可能原因**:
1. portfolio.cash和remaining_cash不同步
2. 多个订单同时创建导致竞态条件

**解决方法**:
1. 检查日志中的现金跟踪信息
2. 检查portfolio.cash和remaining_cash是否一致

---

### 如果持仓检查失败

**可能原因**:
1. 持仓信息不正确
2. 卖出数量计算错误

**解决方法**:
1. 检查持仓状态
2. 检查日志中的持仓信息
3. 确认卖出数量不超过持仓数量

---

## 📊 测试数据收集

### 需要记录的数据

1. **订单数据**
   - 订单数量（BUY/SELL）
   - 订单状态（FILLED/PENDING）
   - 订单金额

2. **现金数据**
   - 交易前现金
   - 交易后现金
   - 订单总成本

3. **持仓数据**
   - 交易前持仓
   - 交易后持仓
   - 卖出数量

4. **日志信息**
   - 关键日志输出
   - 错误信息
   - 警告信息

---

## ✅ 成功标准

### 所有测试通过

- ✅ API正常运行
- ✅ 交易循环成功执行
- ✅ 所有订单状态是FILLED
- ✅ 现金检查正确
- ✅ 持仓检查正确
- ✅ 卖出订单持仓感知正常
- ✅ FILLED状态保证正常

---

**文档创建时间**: 2025-11-14  
**状态**: ✅ 测试指南已创建

