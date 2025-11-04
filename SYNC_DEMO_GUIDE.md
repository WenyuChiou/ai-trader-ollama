# 后端 + 前端同步演示指南

本指南将帮助您运行后端交易循环并实时看到前端更新。

## 快速开始

### 步骤 1: 确保后端API运行

后端API应该已经在运行（端口8000）。如果未运行，执行：

```powershell
cd backend\scripts
.\start_api_background.ps1
```

验证API运行：
```powershell
python -c "import requests; print('OK' if requests.get('http://127.0.0.1:8000/api/system/info').status_code == 200 else 'Not running')"
```

### 步骤 2: 启动前端服务器

在新的PowerShell窗口中：

```powershell
cd frontend
python -m http.server 8080
```

前端将在 `http://localhost:8080/monitor.html` 可用

### 步骤 3: 打开浏览器

访问：`http://localhost:8080/monitor.html`

### 步骤 4: 运行交易循环

**方式1: 使用Python脚本（推荐）**

```powershell
python test_sync_demo.py
```

这将每30秒运行一次交易循环，前端会自动刷新显示更新。

**方式2: 在前端手动点击**

1. 打开前端页面
2. 点击 "Initialize" 按钮（如果需要）
3. 点击 "Run Loop" 按钮运行交易循环
4. 前端每30秒自动刷新，显示最新数据

**方式3: 使用PowerShell脚本**

```powershell
.\quick_sync_test.ps1
```

这会启动前端服务器（如果未运行）、打开浏览器、并运行一次交易循环。

## 查看更新内容

前端会自动显示以下内容的更新：

1. **对话记录** (Overview页)
   - Agent对话内容
   - 工具使用情况（工具名称和返回结果）
   - 按日期分组显示

2. **交易明细** (Trades页)
   - 订单时间
   - 订单日期
   - 交易符号
   - 买卖方向（BUY/SELL）
   - 数量
   - 限价
   - 成交价
   - 价格区间
   - 订单状态

3. **组合状态** (Overview页)
   - 总资产价值
   - 盈亏情况
   - 现金余额
   - 持仓明细

## 自动刷新机制

- 前端每 **30秒** 自动刷新所有数据
- 手动点击 "Run Loop" 后，前端会在 **10秒** 内快速刷新一次
- 所有更新都会实时显示，无需手动刷新页面

## 测试多个交易循环

运行连续的交易循环：

```powershell
# 运行10次循环，每次间隔30秒
python test_sync_demo.py
```

或者手动运行：

```powershell
# 运行一次循环
python -c "import requests; r = requests.post('http://127.0.0.1:8000/api/trading/run-loop', timeout=60); print('OK' if r.json().get('ok') else r.json())"
```

## 验证同步

1. 运行交易循环（使用上述任一方式）
2. 观察前端页面，应该看到：
   - 对话记录增加
   - 交易明细增加
   - 组合状态更新
3. 等待30秒，前端会自动刷新显示最新数据

## 故障排除

### 前端无法连接后端

检查后端是否运行：
```powershell
python -c "import requests; print(requests.get('http://127.0.0.1:8000/api/system/info').json())"
```

### 前端显示"No connection"

1. 确保后端API在运行（端口8000）
2. 检查前端页面中的API地址是否为 `http://127.0.0.1:8000`
3. 检查浏览器控制台是否有错误

### 前端没有更新

1. 检查浏览器控制台是否有错误
2. 手动刷新页面（F5）
3. 检查后端是否有新的对话和交易记录生成

## 完整演示流程

1. **启动后端**（如果未运行）
   ```powershell
   cd backend\scripts
   .\start_api_background.ps1
   ```

2. **启动前端服务器**
   ```powershell
   cd frontend
   python -m http.server 8080
   ```

3. **打开浏览器**
   访问 `http://localhost:8080/monitor.html`

4. **初始化系统**（首次运行）
   在前端点击 "Initialize" 按钮

5. **运行交易循环**
   - 方式A: 在前端点击 "Run Loop" 按钮
   - 方式B: 运行 `python test_sync_demo.py`

6. **观察更新**
   - 前端每30秒自动刷新
   - 可以看到对话、交易、组合状态的实时更新

## 提示

- 前端会自动保存刷新间隔，无需手动设置
- 所有数据都来自后端真实执行，不是demo数据
- 对话记录会显示使用的工具和工具返回的结果
- 交易明细会显示完整的订单信息（限价、成交价、价格区间等）

