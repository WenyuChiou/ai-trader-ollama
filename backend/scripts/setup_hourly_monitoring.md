# ⏰ 每小时实时监控设置指南

参考 [HKUDS/AI-Trader](https://hkuds.github.io/AI-Trader/index.html) 的监测界面，实现每小时更新实时损益和净值。

---

## 🎯 功能说明

### 实时更新内容

1. **当前市场价格**: 每小时获取所有持仓股票的实时价格
2. **实时损益（P&L）**: 计算每个持仓的未实现盈亏
3. **实时净值（NAV）**: 更新投资组合总价值
4. **历史追踪**: 记录每小时快照，用于图表显示

---

## 🚀 设置步骤

### 1. 设置每小时更新任务

#### Windows

```powershell
cd backend\scripts
.\schedule_hourly_update.ps1
```

这会创建一个每小时运行的定时任务 `AITraderHourlyPnlUpdate`。

#### 验证任务

```powershell
Get-ScheduledTask -TaskName "AITraderHourlyPnlUpdate"
```

#### 手动测试

```powershell
# 手动触发一次更新
Start-ScheduledTask -TaskName "AITraderHourlyPnlUpdate"

# 或直接运行脚本
cd backend
python scripts\update_real_time_pnl.py
```

---

### 2. 启动后端 API 服务器

```bash
cd backend
python -m src.api.server
```

或使用 uvicorn:

```bash
cd backend
uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

---

### 3. 启动前端应用

```bash
cd frontend
npm install  # 如果还没安装依赖
npm start
```

前端会在 `http://localhost:3000` 启动。

---

## 📊 界面功能

参考 HKUDS/AI-Trader 的设计，界面包含：

### 1. **总资产价值趋势图**
- 显示最近30天的资产价值变化
- 使用 Area Chart 展示
- 支持数据导出（未来功能）

### 2. **实时投资组合状态**
- 总价值
- 总盈亏（P&L）
- 现金余额

### 3. **持仓明细**
- 每个持仓的：
  - 数量
  - 平均成本
  - 当前价格
  - 市值
  - 未实现盈亏

### 4. **最近交易行动**
- 显示最近的买入/卖出记录
- 时间、股票、数量、价格

---

## 🔄 自动刷新

- **实时数据**: 每分钟自动刷新一次
- **历史数据**: 每5分钟刷新一次
- **每小时更新**: 后台任务每小时更新市场价格

---

## 📱 未来 App 版本

当前 Web 版本可以作为基础，未来可以：

1. **React Native**: 将现有 React 组件转换为移动 App
2. **推送通知**: 当盈亏超过阈值时发送通知
3. **离线缓存**: 缓存最近数据，离线也能查看
4. **图表优化**: 移动端友好的交互式图表

---

## 🛠️ API 端点

### 获取实时投资组合

```
GET /api/portfolio/real-time
```

返回最新的实时投资组合快照，包含当前市场价格。

### 获取最近快照

```
GET /api/portfolio/recent-snapshots?hours=24
```

返回最近24小时的快照历史。

### 获取净值历史

```
GET /api/portfolio/equity-history?days=30
```

返回最近30天的净值历史，用于图表。

---

## ⚙️ 配置

### 更新频率

默认每小时更新一次。可以修改 `schedule_hourly_update.ps1` 中的重复间隔：

```powershell
$Trigger.Repetition = @{
    Interval = [TimeSpan]::FromMinutes(30)  # 改为每30分钟
    Duration = [TimeSpan]::MaxValue
}
```

### 市场时间检查

可以在脚本中添加市场开放时间检查（美股：09:30-16:00 EST）：

```python
# 仅在市场开放时更新
if is_market_open():
    update_real_time_pnl()
```

---

## 🔍 监控数据位置

- **实时快照**: `backend/data/logs/real_time_snapshots.jsonl`
- **净值历史**: `backend/data/logs/equity_history.jsonl`
- **Portfolio 状态**: `backend/data/logs/portfolio_state.json`

---

## ✅ 验证清单

- [ ] 每小时更新任务已设置
- [ ] 任务可以手动运行成功
- [ ] 后端 API 服务器正常运行
- [ ] 前端应用可以访问
- [ ] 实时数据可以正常显示
- [ ] 图表数据正常加载

---

## 🆘 故障排除

### 更新任务没有运行？

```powershell
# 检查任务状态
Get-ScheduledTask -TaskName "AITraderHourlyPnlUpdate" | Get-ScheduledTaskInfo

# 查看任务历史（需要打开任务计划程序）
taskschd.msc
```

### 价格获取失败？

- 检查网络连接
- 确认 yfinance 可以访问
- 检查股票代码是否正确

### 前端无法加载数据？

- 确认后端 API 服务器运行在 `http://localhost:8000`
- 检查浏览器控制台错误
- 确认 CORS 配置正确

---

## 📚 相关文档

- [`docs/GETTING_STARTED.md`](../../docs/GETTING_STARTED.md) - 基础设置
- [`backend/scripts/setup_daily_scheduler.md`](setup_daily_scheduler.md) - 每日任务设置
- [HKUDS/AI-Trader](https://hkuds.github.io/AI-Trader/index.html) - 参考界面

