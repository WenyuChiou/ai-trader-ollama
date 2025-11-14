# 手动重启API指南

**更新时间**: 2025-11-14

---

## 🔧 如果Windows Service无法启动

### 方法1: 使用窗口模式（推荐用于测试）

**步骤**:
1. 打开新的PowerShell窗口
2. 导航到项目目录：
   ```powershell
   cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
   ```
3. 运行快速重启脚本：
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
   ```

**优点**: 
- 可以看到实时日志输出
- 容易调试问题
- 不需要管理员权限

**缺点**: 
- 需要保持窗口打开

---

### 方法2: 检查并修复Windows Service

**步骤1: 检查服务状态**
```powershell
Get-Service -Name AITraderAPI
```

**步骤2: 查看服务日志**
```powershell
# 查看服务日志
Get-EventLog -LogName Application -Source AITraderAPI -Newest 10

# 或查看日志文件
Get-Content logs\api_service.log -Tail 50
```

**步骤3: 手动启动服务**
```powershell
# 以管理员身份运行
Start-Service -Name AITraderAPI
```

**步骤4: 如果启动失败，检查服务配置**
```powershell
# 查看服务配置
Get-WmiObject Win32_Service -Filter "Name='AITraderAPI'" | Select-Object Name, State, StartMode, PathName
```

---

### 方法3: 重新安装服务

**如果服务有问题，可以重新安装**:
```powershell
# 以管理员身份运行
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1
# 选择 (D)elete 删除旧服务
# 然后选择 (I)nstall 重新安装
```

---

## 🧪 测试功能是否正常

### 快速测试（推荐）

**步骤1: 验证API运行**
```powershell
# 检查API是否响应
curl http://localhost:8000/api/market/status
```

**步骤2: 运行测试脚本**
```powershell
powershell -ExecutionPolicy Bypass -File .\test_api_simple.ps1
```

**步骤3: 通过前端测试**
1. 打开：`http://localhost:8080/monitor.html`
2. 点击 "Run Analysis" 或 "Start Trading"
3. 等待完成（约60-100秒）
4. 检查订单状态（应该是FILLED）

---

### 详细测试步骤

#### 1. 检查API状态

**通过浏览器**:
```
http://localhost:8000/api/market/status
```

**通过PowerShell**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/market/status"
```

**预期结果**: 返回JSON，包含`is_open`字段

---

#### 2. 检查投资组合

**通过浏览器**:
```
http://localhost:8000/api/portfolio/state
```

**预期结果**: 
- 返回投资组合信息
- 现金金额正确
- 持仓信息正确

---

#### 3. 运行一次交易循环

**方法A: 通过前端（推荐）**
1. 打开：`http://localhost:8080/monitor.html`
2. 点击 "Run Analysis" 或 "Start Trading"
3. 等待完成

**方法B: 通过API**
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/trading/execute-trade" -Method POST
```

**预期结果**:
- 交易循环成功执行
- 返回订单信息
- 没有错误信息

---

#### 4. 检查订单状态

**通过前端**:
- 查看 "Trade Details" 表格
- 检查订单状态列

**通过API**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/trades/recent?limit=10"
```

**预期结果**:
- ✅ **所有新订单状态是FILLED**（不是PENDING）
- ✅ 订单有正确的时间和价格
- ✅ BUY订单有正确的价格和数量
- ✅ SELL订单有realized_pnl记录

---

#### 5. 验证现金检查

**检查投资组合**:
```powershell
$portfolio = Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/state"
Write-Host "Cash: `$$($portfolio.cash)"
```

**验证**:
- ✅ 现金金额合理（不应该为负数）
- ✅ 如果创建了BUY订单，现金应该减少
- ✅ 总订单成本 ≤ 可用现金

---

#### 6. 验证持仓检查

**检查持仓**:
```powershell
$portfolio = Invoke-RestMethod -Uri "http://localhost:8000/api/portfolio/real-time"
$portfolio.positions_detail
```

**验证**:
- ✅ 如果创建了SELL订单，持仓数量应该减少
- ✅ SELL订单数量 ≤ 持仓数量

---

#### 7. 检查日志输出

**如果使用窗口模式**:
- 查看PowerShell窗口的输出

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

## ✅ 测试检查清单

### 基础功能
- [ ] API正常运行
- [ ] 投资组合状态正确
- [ ] 交易循环可以执行

### 订单执行
- [ ] 所有新订单状态是FILLED（不是PENDING）
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

## 🎯 快速测试命令

### 一键测试脚本
```powershell
powershell -ExecutionPolicy Bypass -File .\test_api_simple.ps1
```

### 手动测试命令
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

**文档创建时间**: 2025-11-14  
**状态**: ✅ 测试指南已创建

