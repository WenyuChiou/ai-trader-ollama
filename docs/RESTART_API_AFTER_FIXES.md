# API重启指南（修复后）

**更新时间**: 2025-11-14  
**修复内容**: 卖出订单持仓感知、FILLED状态保证、现金检查改进

---

## ✅ 需要重启API

### 修复内容

1. **卖出订单持仓感知改进** (`trader_agent.py`)
   - 明确遍历所有当前持仓
   - 显示每个持仓的详细信息
   - 确保卖出数量不超过持仓数量

2. **FILLED状态保证** (`trading_cycle.py`)
   - BUY订单：添加异常处理，确保标记为FILLED
   - SELL订单：添加异常处理，确保标记为FILLED
   - 双重保险：即使mark_order_filled()失败，也会手动设置FILLED

3. **现金检查改进** (`trading_cycle.py`)
   - BUY订单：使用实际portfolio.cash检查
   - 先执行交易，成功后再创建订单

**结论**: ✅ **需要重启API**才能加载新代码

---

## 🔄 重启步骤

### 步骤1: 检查API运行状态

```powershell
# 检查API是否运行
Get-NetTCPConnection -LocalPort 8000
```

### 步骤2: 重启API

#### 如果API运行在窗口模式

**方法1: 快速重启**
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

**方法2: 手动重启**
1. 关闭运行API的PowerShell窗口
2. 重新运行启动脚本

#### 如果API运行为Windows Service

```powershell
# 重启服务
Restart-Service -Name AITraderAPI

# 或使用脚本
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_service.ps1
# 然后选择 (R)estart
```

#### 如果API运行为任务计划程序

```powershell
# 重启任务
Stop-ScheduledTask -TaskName AITraderAPI
Start-Sleep -Seconds 2
Start-ScheduledTask -TaskName AITraderAPI

# 或使用脚本
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
# 然后选择 (R)estart
```

### 步骤3: 验证API重启成功

```powershell
# 检查API是否运行
Get-NetTCPConnection -LocalPort 8000

# 测试API响应
curl http://localhost:8000/api/market/status
```

---

## 🔧 是否需要初始化？

### 检查是否需要初始化

**检查项目**:
- [ ] `portfolio_state.json` 是否存在
- [ ] 数据文件是否正常
- [ ] 是否有旧的pending订单需要清理

### 如果portfolio_state.json存在

**不需要重新初始化** ✅
- 系统会使用现有的投资组合状态
- 只需要重启API即可

### 如果portfolio_state.json不存在

**需要初始化** ⚠️
```powershell
# 从项目根目录运行
python scripts/init_data.py
```

### 清理旧的pending订单（可选）

**如果有很多旧的pending订单**:
```powershell
# 清理所有pending订单（谨慎使用）
python -c "from pathlib import Path; Path('backend/data/logs/pending_orders.jsonl').write_text('')"
```

---

## 📋 重启后验证

### 验证项目

1. **API状态**
   - [ ] API正常运行（端口8000）
   - [ ] API响应正常

2. **订单执行**
   - [ ] 运行一次交易循环
   - [ ] 检查订单状态（应该是FILLED，不是PENDING）
   - [ ] 检查现金使用（不应该超过可用现金）
   - [ ] 检查卖出数量（不应该超过持仓数量）

3. **日志输出**
   - [ ] 检查是否有新的日志输出
   - [ ] 检查是否有错误信息

---

## ⚠️ 注意事项

### 重启前

1. **保存当前状态**（可选）
   - 备份 `portfolio_state.json`
   - 备份 `filled_orders.jsonl`
   - 备份其他重要数据文件

2. **检查Ollama**
   - 确保Ollama服务正在运行
   - 确保模型已下载

### 重启后

1. **验证修复**
   - 运行一次交易循环
   - 检查订单状态
   - 检查现金和持仓

2. **监控运行**
   - 观察日志输出
   - 检查是否有错误

---

## 🎯 快速重启命令

### 如果使用窗口模式

```powershell
# 快速重启
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

### 如果使用Windows Service

```powershell
Restart-Service -Name AITraderAPI
```

### 如果使用任务计划程序

```powershell
Stop-ScheduledTask -TaskName AITraderAPI; Start-Sleep -Seconds 2; Start-ScheduledTask -TaskName AITraderAPI
```

---

**文档创建时间**: 2025-11-14  
**状态**: ✅ 需要重启API

