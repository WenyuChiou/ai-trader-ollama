# 🚀 运行前端完整聊天流程

## 快速启动步骤

### 1. 启动后端 API 服务器

**方法 A：使用 PowerShell 脚本（推荐）**
```powershell
# 在项目根目录运行
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"
.\scripts\start_api_background.ps1
```

**方法 B：手动启动（开发/测试）**
```powershell
# 在项目根目录运行
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**验证 API 是否启动成功：**
- 打开浏览器访问：`http://localhost:8000`
- 应该看到 API 响应或文档页面

### 2. 打开前端页面

**方法 A：直接打开 HTML 文件**
```powershell
# 在文件资源管理器中打开
frontend\monitor.html
```

**方法 B：使用本地服务器（推荐，避免 CORS 问题）**
```powershell
# 在项目根目录运行
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\frontend"
python -m http.server 3000
# 然后打开浏览器访问：http://localhost:3000/monitor.html
```

### 3. 运行完整的交易循环

在前端页面中：
1. **初始化系统**（如果需要）：
   - 点击 "Initialize System" 按钮
   - 这会清空所有历史数据并重置投资组合

2. **执行交易循环**：
   - 点击 "Execute Trading Cycle" 按钮
   - 系统会运行完整的 agent 讨论和交易决策流程

3. **查看结果**：
   - 在 "Conversations" 面板查看所有 agent 的对话
   - 在 "Trades" 面板查看生成的订单
   - 在 "Portfolio" 面板查看当前持仓和净值

## 📋 完整流程说明

### Agent 讨论流程（使用 DiscussionCoordinator）

1. **Market Data Fetching**：获取市场数据
2. **Analyst Discussion**：DiscussionCoordinator 协调多个分析师进行讨论
   - 使用工具（news_scan, vix_term, fear_greed 等）
   - 生成市场 stance 和 summary
3. **Risk Analyst**：评估当前仓位风险
4. **Trader Agent**：基于讨论结果生成交易决策
5. **Order Execution**：执行买卖订单

### 查看对话内容

- **DiscussionCoordinator**：综合所有分析师的观点
- **TraderAgent**：交易决策和理由
- **ToolSystem**：工具使用记录

## 🔧 故障排除

### API 无法启动
```powershell
# 检查端口是否被占用
netstat -ano | findstr :8000

# 如果被占用，终止进程
taskkill /PID <进程ID> /F
```

### 前端无法连接 API
- 确认 API 正在运行（访问 http://localhost:8000）
- 检查浏览器控制台是否有错误
- 确认前端页面中的 API 地址是 `http://127.0.0.1:8000`

### 没有对话内容
- 确认已经执行了交易循环
- 检查 `data/logs/discussion_actions.jsonl` 文件是否存在
- 查看后端控制台的日志输出

## 📝 测试场景

运行测试脚本验证系统：
```powershell
# 测试场景 1-3
python backend\scripts\test_all_scenarios.py

# 或单个场景测试
python test_scenario_one_by_one.py
```

