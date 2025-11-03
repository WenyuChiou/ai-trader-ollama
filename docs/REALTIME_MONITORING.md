# ⏰ 实时监控系统

参考 [HKUDS/AI-Trader](https://hkuds.github.io/AI-Trader/index.html) 的界面设计，实现每小时实时更新损益和净值的监控系统。

---

## 🎯 功能概述

### 核心功能

1. **每小时自动更新**
   - 获取当前市场价格（通过 yfinance）
   - 计算实时损益（P&L）
   - 更新净值（NAV）
   - 记录快照历史

2. **实时监测界面**
   - 资产价值趋势图（类似 HKUDS）
   - 实时投资组合状态
   - 持仓明细和盈亏
   - 最近交易行动

3. **自动刷新**
   - 前端每分钟自动刷新实时数据
   - 每5分钟刷新历史数据

---

## 🚀 快速开始

### 1. 设置每小时更新任务

#### Windows

```powershell
cd backend\scripts
.\schedule_hourly_update.ps1
```

验证任务：
```powershell
Get-ScheduledTask -TaskName "AITraderHourlyPnlUpdate"
```

#### 手动测试

```powershell
cd backend
python scripts\update_real_time_pnl.py
```

---

### 2. 启动后端 API

```bash
cd backend
uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

---

### 3. 启动前端

```bash
cd frontend
npm install  # 如果还没安装
npm start
```

前端会在 `http://localhost:3000` 启动。

---

## 📊 界面功能

### 参考设计

界面设计参考 [HKUDS/AI-Trader](https://hkuds.github.io/AI-Trader/index.html)：

1. **总资产价值趋势图**
   - Area Chart 展示最近30天资产变化
   - 支持线性/对数刻度切换（未来功能）
   - 数据导出功能（未来功能）

2. **实时投资组合状态**
   - Total Value（总价值）
   - Total P&L（总盈亏，带百分比）
   - Cash（现金余额）

3. **持仓明细卡片**
   - 每个持仓的详细信息
   - 未实现盈亏（绿色/红色）
   - 当前价格 vs 平均成本

4. **最近交易行动**
   - 时间、股票、操作（买入/卖出）
   - 数量和价格

---

## 🔄 更新频率

### 后台更新

- **每小时**: 自动获取市场价格并更新损益
- **市场时间**: 可在脚本中添加市场开放时间检查（美股：09:30-16:00 EST）

### 前端刷新

- **实时数据**: 每60秒自动刷新
- **历史数据**: 每5分钟刷新一次

---

## 📡 API 端点

### 获取实时投资组合

```
GET /api/portfolio/real-time
```

**返回**:
```json
{
  "ok": true,
  "timestamp": "2025-01-28T14:30:00",
  "total_value": 10250.75,
  "cash": 2197.50,
  "equity_value": 8053.25,
  "total_pnl": 250.75,
  "total_pnl_pct": 2.51,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "current_price": 152.50,
      "market_value": 1525.00
    }
  },
  "positions_pnl": {
    "NVDA": {
      "unrealized_pnl": 22.50,
      "unrealized_pnl_pct": 1.50
    }
  },
  "current_prices": {
    "NVDA": 152.50
  }
}
```

### 获取最近快照

```
GET /api/portfolio/recent-snapshots?hours=24
```

返回最近24小时的实时快照历史。

### 获取净值历史

```
GET /api/portfolio/equity-history?limit=60
```

返回最近60天的净值历史，用于趋势图。

---

## 📱 未来 App 版本

当前 Web 版本可以作为移动 App 的基础：

### 技术路线

1. **React Native**: 将现有 React 组件转换为移动 App
   - 复用现有组件逻辑
   - 使用 React Native Charts 替代 Recharts

2. **推送通知**
   - 当盈亏超过阈值时发送通知
   - 重大市场波动提醒

3. **离线缓存**
   - 缓存最近数据
   - 离线查看历史记录

4. **图表优化**
   - 移动端友好的交互式图表
   - 手势缩放和平移

---

## ⚙️ 配置

### 更新频率

修改 `schedule_hourly_update.ps1`:

```powershell
# 改为每30分钟更新
$Trigger.Repetition = @{
    Interval = [TimeSpan]::FromMinutes(30)
    Duration = [TimeSpan]::MaxValue
}
```

### 市场时间检查

可以在 `update_real_time_pnl.py` 中添加：

```python
from datetime import datetime, time

def is_market_open():
    """检查美股市场是否开放（09:30-16:00 EST）"""
    now = datetime.now()
    market_open = time(9, 30)
    market_close = time(16, 0)
    current_time = now.time()
    
    # 简单检查（需要根据时区调整）
    return market_open <= current_time <= market_close

if is_market_open():
    update_real_time_pnl()
```

---

## 📁 数据存储

- **实时快照**: `backend/data/logs/real_time_snapshots.jsonl`
- **净值历史**: `backend/data/logs/equity_history.jsonl`
- **Portfolio 状态**: `backend/data/logs/portfolio_state.json`

---

## ✅ 验证

1. **测试每小时更新**:
   ```powershell
   python scripts\update_real_time_pnl.py
   ```

2. **测试 API**:
   ```bash
   curl http://localhost:8000/api/portfolio/real-time
   ```

3. **检查前端**:
   - 打开 `http://localhost:3000`
   - 确认数据正常加载
   - 确认自动刷新工作正常

---

## 🔍 故障排除

### 价格获取失败

- 检查网络连接
- 确认 yfinance 可以访问
- 检查股票代码是否正确

### API 返回错误

- 确认后端服务器运行
- 检查 `portfolio_state.json` 是否存在
- 查看后端日志

### 前端无法加载

- 确认 API 地址正确（`http://localhost:8000`）
- 检查浏览器控制台错误
- 确认 CORS 配置正确

---

## 📚 相关文档

- [`backend/scripts/setup_hourly_monitoring.md`](../backend/scripts/setup_hourly_monitoring.md) - 详细设置指南
- [`docs/GETTING_STARTED.md`](GETTING_STARTED.md) - 基础设置
- [HKUDS/AI-Trader](https://hkuds.github.io/AI-Trader/index.html) - 参考界面

---

## 🎨 界面预览

界面包含：

1. **顶部状态栏**: 总价值、总盈亏、现金
2. **资产趋势图**: 最近30天资产价值变化（Area Chart）
3. **持仓卡片**: 每个持仓的详细信息和盈亏
4. **交易历史**: 最近的买入/卖出记录

界面风格参考 HKUDS/AI-Trader，使用渐变背景和现代化的卡片设计。

