# 🚀 快速监控指南

想要随时监控投资组合状态？按照以下步骤快速启动监控界面。

---

## 📋 快速开始（3步）

### 步骤 1: 启动后端 API

打开终端/命令行，运行：

```bash
cd backend
uvicorn src.api.server:app --reload --host 0.0.0.0 --port 8000
```

**预期输出**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

✅ **保持这个终端窗口打开**，API 服务器需要持续运行。

---

### 步骤 2: 启动前端

打开**另一个**终端/命令行窗口，运行：

```bash
cd frontend
npm install  # 如果还没安装依赖
npm run dev  # 或 npm start
```

**预期输出**:
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

✅ 前端会自动在浏览器打开 `http://localhost:5173`

---

### 步骤 3: 查看监控界面

在浏览器中，你会看到：

- **总资产**：当前投资组合总价值
- **总盈亏**：总体盈亏金额和百分比
- **现金余额**：可用现金
- **持仓市值**：当前持仓股票的总市值
- **持仓明细表**：每个持仓的详细信息（数量、成本价、当前价、盈亏）

**自动刷新**：默认每 30 秒自动更新一次，也可以手动点击"手动刷新"按钮。

---

## 📊 监控界面功能

### 主要显示

1. **总资产（Total Value）**
   - 现金 + 持仓市值
   - 实时更新

2. **总盈亏（Total P&L）**
   - 显示盈利（绿色）或亏损（红色）
   - 百分比显示

3. **持仓明细**
   - 股票代码
   - 持仓数量
   - 平均成本价
   - 当前市场价格
   - 未实现盈亏（绿色/红色）

### 控制选项

- **自动刷新**：勾选后每 30 秒自动更新
- **手动刷新**：随时点击更新数据
- **最后更新时间**：显示数据最后更新时间

---

## 🔧 配置

### 修改 API 地址

如果后端运行在不同地址，编辑 `frontend/.env`：

```env
VITE_API_BASE=http://localhost:8000
```

或修改 `frontend/src/components/SimpleMonitor.tsx`:

```typescript
const API_BASE = 'http://your-api-address:8000';
```

### 修改刷新频率

编辑 `frontend/src/components/SimpleMonitor.tsx`:

```typescript
// 将 30000 (30秒) 改为你想要的毫秒数
const interval = setInterval(() => {
  if (autoRefresh) {
    fetchPortfolio();
  }
}, 60000); // 改为 60 秒
```

---

## 🆘 常见问题

### 1. 连接错误

**错误**: `Failed to fetch portfolio` 或 `连接错误`

**解决**:
- ✅ 确认后端 API 正在运行（步骤 1）
- ✅ 检查 API 地址是否正确（默认 `http://localhost:8000`）
- ✅ 确认防火墙没有阻止连接

### 2. 暂无数据

**显示**: "暂无投资组合数据"

**解决**:
- ✅ 需要先运行一次交易循环
- ✅ 运行：`python scripts/run_daily_trading.py`
- ✅ 或者等待定时任务自动执行（如果已设置）

### 3. CORS 错误

**错误**: `CORS policy` 相关错误

**解决**:
- ✅ 后端 API 已配置 CORS，通常不会出现
- ✅ 确认后端运行在 `http://0.0.0.0:8000` 而不是 `127.0.0.1:8000`

---

## 📱 访问方式

### 本地访问

- **开发模式**: `http://localhost:5173` (Vite)
- **或**: `http://localhost:3000` (如果使用 Create React App)

### 局域网访问

如果后端运行在 `0.0.0.0`，其他设备可以通过你的 IP 访问：

```
http://<your-ip>:5173
```

例如：`http://192.168.1.100:5173`

---

## 🔄 自动刷新说明

### 实时数据来源

监控界面从以下 API 获取数据：
- **端点**: `GET /api/portfolio/real-time`
- **数据**: 实时市场价格 + 投资组合快照
- **更新**: 每次调用都会获取最新市场价格

### 自动刷新

- **默认**: 每 30 秒自动刷新
- **可关闭**: 取消勾选"自动刷新"
- **手动**: 随时点击"手动刷新"按钮

---

## 💡 提示

1. **首次使用**：
   - 需要先运行一次交易循环才能看到数据
   - 运行：`python backend/scripts/run_daily_trading.py`

2. **后台运行**：
   - 可以让后端 API 在后台持续运行
   - 使用 `screen` 或 `tmux` (Linux/Mac)
   - 或使用 Windows 服务/任务计划程序

3. **监控多个账户**：
   - 可以启动多个前端实例
   - 修改不同的 API 地址或端口

---

## 📚 相关文档

- [`docs/REALTIME_MONITORING.md`](REALTIME_MONITORING.md) - 详细实时监控系统说明
- [`backend/scripts/setup_hourly_monitoring.md`](../backend/scripts/setup_hourly_monitoring.md) - 每小时自动更新设置

---

**快速启动命令总结**:

```bash
# 终端 1: 后端 API
cd backend && uvicorn src.api.server:app --reload

# 终端 2: 前端
cd frontend && npm run dev
```

然后在浏览器打开 `http://localhost:5173` 即可！

