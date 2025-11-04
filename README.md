# 💹 AI-Trader Ollama

> **A self-evolving multi-agent trading system powered by LangChain + Ollama + yfinance**  
> 📈 Designed for **NASDAQ-100** stock universe with hedging and leveraged ETF support  
> 🧠 Agents that analyze, discuss, and decide — entirely autonomously

---

## 📚 Table of Contents

- [Quick Start](#-quick-start)
- [API Startup & Shutdown](#-api-startup--shutdown)
- [Backend Testing](#-backend-testing)
- [Configuration Settings](#-configuration-settings)
- [Frontend Testing](#-frontend-testing)
- [Agent System](#-agent-system)
- [Available Tools](#-available-tools)
- [Project Structure](#-project-structure)
- [Troubleshooting](#-troubleshooting)

---

## 🚀 Quick Start

### Prerequisites

**Backend:**
```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Start Ollama service (keep it running)
ollama serve

# Pull LLM model (in another terminal)
ollama pull llama3.1
```

**Frontend:**
- No Node.js required! Frontend is pure HTML
- Just need Python's HTTP server

### Initialize Data

```bash
cd backend
python scripts/init_data.py
```

This will create:
- Portfolio state (initial cash: $10,000)
- Memory directory structure
- Trading log files

---

## 🔧 API 启动与终止

### 启动 API

#### 方法 1: PowerShell 脚本（Windows - 推荐）

```powershell
cd backend\scripts
.\start_api_background.ps1
```

这会打开一个新的 PowerShell 窗口运行 API。**保持该窗口打开** - 关闭它就会停止 API。

#### 方法 2: 手动启动

```bash
cd backend
python -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
```

**保持此终端窗口打开** - 关闭它（或按 `Ctrl+C`）会停止 API。

#### 方法 3: 后台运行（PowerShell，可选）

```powershell
cd backend
Start-Job -ScriptBlock { 
    Set-Location "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\backend"
    python -m uvicorn src.api.server:app --host 127.0.0.1 --port 8000 
}

# 查看状态
Get-Job

# 查看输出
Receive-Job <JobId>

# 停止
Stop-Job <JobId>
Remove-Job <JobId>
```

### 验证 API 运行

**测试健康检查端点:**
```powershell
curl http://localhost:8000/
```

**预期响应:**
```json
{
  "message": "AI Trader API",
  "version": "1.0.0"
}
```

**检查端口使用:**
```powershell
netstat -ano | findstr ":8000"
```

**或使用测试脚本:**
```powershell
cd backend
powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1
```

### 终止 API

#### 如果使用脚本启动（方法 1）

**简单方法:**
- 关闭显示 API 日志的 PowerShell 窗口
- API 会自动停止

**如果窗口已关闭/最小化:**
```powershell
# 查找并终止进程
cd backend\scripts
.\check_port.ps1
# 按提示操作，或手动：
taskkill /PID <PID> /F
```

#### 如果手动启动（方法 2）

**在运行 API 的终端中:**
- 按 `Ctrl + C` 优雅停止
- 或直接关闭终端窗口

#### 验证 API 已停止

```powershell
# 应该显示空（端口未使用）
netstat -ano | findstr ":8000"

# 或测试连接（应该失败）
curl http://localhost:8000/
```

### 重启 API

如果遇到问题，可以使用重启脚本：

```powershell
cd backend\scripts
.\restart_api_bypass.ps1
```

或手动：
```powershell
cd backend\scripts
powershell -ExecutionPolicy Bypass -File .\restart_api.ps1
```

**注意**: 如果遇到 PowerShell 执行策略错误，使用 `restart_api_bypass.ps1`。

---

## 🧪 后端测试

### 快速测试

```bash
cd backend
python test_api.py
```

**预期输出:**
```
✅ PASS - Portfolio Initialization
✅ PASS - Portfolio State File
✅ PASS - API Server Imports
✅ All tests passed! Backend is ready.
```

### 完整测试套件

```bash
cd backend

# 运行所有测试
python tests/run_all.py

# 运行特定测试
python tests/test_05_full_trading_loop.py
```

### API 端点测试

**测试所有端点:**
```powershell
cd backend
powershell -ExecutionPolicy Bypass -File TEST_BACKEND_SIMPLE.ps1
```

**手动测试关键端点:**
```powershell
# 健康检查
curl http://localhost:8000/

# 实时投资组合
curl http://localhost:8000/api/portfolio/real-time

# 工具列表
curl http://localhost:8000/api/tools/list

# Agent 对话
curl http://localhost:8000/api/agents/conversations?limit=10

# 交易记录
curl http://localhost:8000/api/trades/recent?limit=10
```

### 测试交易循环

```bash
cd backend
python test_full_workflow.py
```

这将测试：
- 市场数据获取
- Agent 分析
- 工具调用
- 交易决策
- 对话记录

### 测试十月模拟

```bash
cd backend
python test_october_simulation_full.py
```

这将测试完整的十月历史模拟流程。

---

## ⚙️ 配置文件设置

### 主配置文件: `backend/config/config.json`

#### 基本配置

```json
{
  "universe_source": "custom",
  "universe_limit": 100,
  
  "universe": [
    "NVDA", "MSFT", "AAPL", "GOOG", "GOOGL", "AMZN", "META", "AVGO", "TSLA",
    ...
  ],
  
  "initial_cash": 10000,
  "position_limit_per_stock": 0.15,
  "position_limit_total": 0.85,
  "position_limit_min_per_stock": 0.03
}
```

**关键参数说明:**

| 参数 | 说明 | 默认值 | 建议值 |
|------|------|--------|--------|
| `universe` | 股票池列表 | - | 72只股票（已配置） |
| `initial_cash` | 初始现金 | 10000 | 根据需求调整 |
| `position_limit_per_stock` | 单股最大仓位 | 0.15 (15%) | 0.10-0.20 |
| `position_limit_total` | 总仓位上限 | 0.85 (85%) | 0.80-0.90 |
| `position_limit_min_per_stock` | 单股最小仓位 | 0.03 (3%) | 0.02-0.05 |

#### 反向ETF配置（对冲）

```json
{
  "inverse_etfs": [
    "SQQQ",  // 3x Inverse NASDAQ
    "SPXU",  // 3x Inverse S&P 500
    "SH",    // 1x Inverse S&P 500
    "PSQ",   // 1x Inverse QQQ
    "SDS",   // 2x Inverse S&P 500
    "DOG",   // 1x Inverse Dow Jones
    "SOXS"   // 3x Inverse Semiconductor ETF
  ]
}
```

**使用场景:**
- VIX > 20（高波动率）
- 市场情绪看跌但想保护多头持仓
- 技术指标显示市场可能反转

#### 杠杆ETF配置（适度使用）

```json
{
  "leveraged_etfs": [
    "TQQQ",  // 3x Leveraged NASDAQ
    "SOXL",  // 3x Leveraged Semiconductor
    "UPRO",  // 3x Leveraged S&P 500
    "TNA",   // 3x Leveraged Small Cap
    "FAS",   // 3x Leveraged Financials
    "CURE",  // 3x Leveraged Healthcare
    "LABU",  // 3x Leveraged Biotech
    "TECL",  // 3x Leveraged Technology
    "TMF",   // 3x Leveraged 20+ Year Treasury
    "EDC"    // 3x Leveraged Emerging Markets
  ]
}
```

**使用场景:**
- 强烈看涨趋势（明确上涨）
- VIX < 15（低波动率）
- 技术指标强劲（RSI < 70, MACD看涨）

**仓位限制:**
- 单只杠杆ETF: 最大 5-10% 组合价值
- 总杠杆ETF仓位: 最大 20-30% 组合价值

#### 市场指数配置（技术分析参考）

```json
{
  "market_indices": [
    "^GSPC",  // S&P 500
    "^IXIC",  // NASDAQ Composite
    "^DJI"    // Dow Jones Industrial Average
  ]
}
```

这些指数用于 Agent 技术分析，但不参与交易。

#### LLM 配置

```json
{
  "llm": {
    "default_model": "llama3.1",
    "ollama_host": "http://localhost:11434",
    "auto_pull": true,
    "timeout_seconds": 8.0
  }
}
```

**参数说明:**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `default_model` | 默认 LLM 模型 | "llama3.1" |
| `ollama_host` | Ollama 服务器地址 | "http://localhost:11434" |
| `auto_pull` | 自动下载缺失模型 | true |
| `timeout_seconds` | 请求超时时间 | 8.0 |

#### 讨论配置

```json
{
  "discussion_rounds": 3,
  "discussion_auto_tools": true,
  "discussion_tool_budget": 20
}
```

**参数说明:**

| 参数 | 说明 | 默认值 | 建议值 |
|------|------|--------|--------|
| `discussion_rounds` | 讨论轮数 | 3 | 3-5 |
| `discussion_auto_tools` | 自动工具调用 | true | true |
| `discussion_tool_budget` | 工具调用预算 | 20 | 15-25 |

#### 偏好域名配置

```json
{
  "preferred_domains": [
    "www.cboe.com",
    "www.wsj.com",
    "www.reuters.com",
    "www.ft.com",
    "www.cmegroup.com",
    "fred.stlouisfed.org",
    "home.treasury.gov"
  ]
}
```

这些域名用于新闻搜索，确保信息来源可靠。

#### 加密货币配置（可选）

```json
{
  "crypto": [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    ...
  ]
}
```

**注意**: 加密货币目前仅用于分析，不参与交易。

---

## 🌐 前端测试

### 启动前端服务器

**方法 1: Python HTTP 服务器（推荐）**

```bash
cd frontend
python -m http.server 8080
```

**然后打开浏览器:** `http://127.0.0.1:8080/monitor.html`

**方法 2: PowerShell 脚本（Windows）**

```powershell
cd frontend
.\start_frontend_server.ps1
```

### 验证前端连接

**检查连接状态:**
- ✅ 绿色圆点 + "Connected": API 正在运行
- ❌ 红色圆点 + "Disconnected": API 未运行或连接错误

**检查功能:**

1. **投资组合数据**
   - ✅ Total Value: $10,000.00（或你的初始金额）
   - ✅ Cash: $10,000.00
   - ✅ Equity Value: $0.00（如果没有持仓）
   - ✅ Total P&L: $0.00

2. **自动刷新**
   - ✅ Auto Refresh 开关工作
   - ✅ 手动 Refresh 按钮工作
   - ✅ 每60秒自动刷新（如果开启）

3. **Agent 对话**
   - ✅ 对话列表显示
   - ✅ 每个 Agent 有专用图标
   - ✅ 对话内容完整显示（不截断）

4. **交易记录**
   - ✅ Execution Details 显示交易
   - ✅ 没有重复记录
   - ✅ 显示正确的买卖方向和价格

5. **控制按钮**
   - ✅ "▶️ Start Trading" 按钮工作
   - ✅ "Auto Trade (1分钟)" 复选框工作
   - ✅ "Simulate October" 按钮工作（如果可用）

### 前端功能测试

**测试交易执行:**
1. 点击 "▶️ Start Trading" 按钮
2. 等待 Agent 分析完成
3. 检查对话是否出现
4. 检查是否有交易订单生成
5. 检查投资组合是否更新

**测试自动交易:**
1. 勾选 "Auto Trade (1分钟)" 复选框
2. 等待 1 分钟
3. 检查是否自动执行交易循环
4. 检查对话和交易是否更新

**测试十月模拟:**
1. 点击 "Simulate October" 按钮
2. 检查进度条是否显示
3. 检查投资组合是否随时间更新
4. 检查图表是否显示历史数据

### 前端故障排除

**如果看到 "Connection Error":**
1. 检查后端 API 是否运行: `curl http://localhost:8000/`
2. 检查浏览器控制台（F12）是否有错误
3. 确保 API 地址正确（默认: `http://127.0.0.1:8000`）

**如果数据不更新:**
1. 检查自动刷新是否开启
2. 手动点击 Refresh 按钮
3. 检查浏览器控制台是否有错误

---

## 🤖 Agent 系统

### Agent 类型与职责

系统包含以下 Agent，每个 Agent 负责特定任务：

| Agent | 职责 | 主要输出 | 使用时机 |
|-------|------|----------|----------|
| **Market Analyst** | 分析市场趋势，生成股票推荐 | 推荐股票列表、市场情绪 | 每次交易循环开始时 |
| **Discussion Agent** | 多轮讨论分析，综合评估 | 最终立场（bullish/bearish/neutral）、推理过程 | 市场分析后，3轮讨论 |
| **Risk Analyst** | 评估投资组合风险，仓位控制 | 风险报告、仓位建议 | 在交易决策前 |
| **Trader Agent** | 生成买卖订单 | 买入/卖出订单列表、价格、数量 | 所有分析完成后 |

### 详细说明

#### 1. Market Analyst（市场分析师）

**职责:**
- 分析所有股票的技术指标
- 评估市场趋势（uptrend/downtrend/sideways）
- 生成推荐股票列表
- 评估市场情绪（bullish/bearish/neutral）

**输出:**
```json
{
  "market_sentiment": "bullish",
  "recommended_stocks": ["NVDA", "MSFT", "AAPL"],
  "key_observations": ["Tech sector showing strength", ...],
  "concerns": ["VIX elevated", ...]
}
```

**位置:** `backend/src/tools/market_analyst.py`

#### 2. Discussion Agent（讨论Agent）

**职责:**
- 进行多轮讨论（默认3轮）
- 自动调用工具获取额外信息（新闻、VIX、恐惧贪婪指数等）
- 综合所有信息形成最终立场
- 提供详细的推理过程

**输出:**
```json
{
  "stance": "bullish",
  "rationale": [
    {"source": "technical_indicators", "reason": "..."},
    {"source": "news_scan", "reason": "..."},
    ...
  ],
  "signals_used": ["rsi14", "macd", "vix", ...],
  "tool_calls": [...],
  "to_agent_notes": "..."
}
```

**位置:** `backend/src/agents/analyst_discussion.py`

#### 3. Risk Analyst（风险分析师）

**职责:**
- 评估当前持仓风险
- 检查仓位限制合规性
- 生成仓位控制建议
- 识别过度集中风险

**输出:**
```json
{
  "overall_risk": "medium",
  "position_control_report": {
    "recommended_position_sizes": {...},
    "position_limit_checks": [...]
  },
  "warnings": [...]
}
```

**位置:** `backend/src/agents/risk_analyst.py`

#### 4. Trader Agent（交易Agent）

**职责:**
- 根据所有分析生成买卖订单
- 计算仓位大小
- 设置买入/卖出价格范围
- 考虑风险报告和仓位限制

**输出:**
```json
{
  "action": "BUY",
  "buy_orders": [
    {
      "symbol": "NVDA",
      "buy_price": 199.77,
      "buy_price_min": 198.77,
      "buy_price_max": 199.77,
      "quantity": 7,
      "total_cost": 1398.39
    }
  ],
  "sell_orders": [...],
  "rationale": "..."
}
```

**位置:** `backend/src/agents/trader_agent.py`

### Agent 工作流程

```
1. Market Data Collection
   ↓
2. Market Analyst → 推荐股票 + 市场情绪
   ↓
3. Discussion Agent (3轮) → 最终立场 + 推理
   ↓
4. Risk Analyst → 风险报告 + 仓位建议
   ↓
5. Trader Agent → 买卖订单
   ↓
6. Order Execution → 更新投资组合
```

---

## 🛠️ 可用工具

Agent 可以使用的工具，按类别分类：

### 📊 市场数据工具

#### `fetch_market_batch`
**用途**: 批量获取股票 OHLCV 数据和技术指标  
**输入**: 股票代码列表、开始日期、结束日期  
**输出**: 每只股票的价格、RSI、MACD、布林带、信号分数、VIX 数据等  
**使用场景**: 
- Market Analyst 分析所有股票的技术指标（默认会分析整个 universe，72只股票）
- Discussion Agent 评估市场趋势
- Trader Agent 选择交易标的

**示例**:
```python
{
  "symbols": ["NVDA", "MSFT", "AAPL", ...],  # 通常包含整个 universe (72只)
  "start": "2024-01-01",
  "end": "2025-01-27"
}
```

#### `vix_term`
**用途**: 获取 VIX 期限结构（VIX vs VIX3M 比率）  
**输出**: VIX 值、VIX3M 值、比率（>1 = contango，<1 = backwardation）  
**使用场景**: 
- 评估市场恐慌程度
- 判断市场是否处于 contango 或 backwardation
- Risk Analyst 评估市场风险

#### `vix_close` / `fetch_vix_close`
**用途**: 获取 VIX 历史收盘价序列  
**输入**: 开始日期、结束日期  
**输出**: VIX 历史价格数组和日期数组  
**使用场景**: 
- 分析 VIX 趋势变化
- 计算 VIX 的 z-score
- 评估市场波动性历史水平

#### `fear_greed`
**用途**: 获取恐惧贪婪指数  
**输出**: 指数值（0-100）、标签（Extreme Fear/Fear/Neutral/Greed/Extreme Greed）  
**使用场景**: 
- 评估市场情绪
- 判断市场是否过度恐慌或贪婪
- Discussion Agent 综合市场情绪分析

### 📰 新闻与经济数据工具

#### `news_scan`
**用途**: 扫描新闻文章，搜索与股票/关键词相关的新闻  
**输入**: 关键词列表（股票代码、查询词）、最近天数、最大文章数、偏好域名  
**输出**: 新闻标题、URL、来源、日期、摘要  
**使用场景**: 
- Discussion Agent 获取最新市场新闻（最重要的工具之一）
- 评估股票相关的市场情绪
- 分析公司财报、公告等重大事件

**示例**:
```python
{
  "keywords": ["NVDA", "earnings"],
  "recency_days": 7,
  "max_articles": 12,
  "domains": ["www.reuters.com", "www.wsj.com"]
}
```

#### `fetch_jin10_news`
**用途**: 获取金十财经新闻（中文财经新闻平台）  
**输入**: 最大条目数、类别  
**输出**: 新闻标题、时间、内容、类别、URL  
**使用场景**: 
- 获取中文财经新闻
- 分析中国市场情绪
- 获取实时财经快讯

#### `fetch_jin10_economic_data`
**用途**: 获取经济数据（GDP、CPI、PMI 等）  
**输入**: 最大条目数  
**输出**: 经济数据指标、数值、时间、影响  
**使用场景**: 
- 评估宏观经济环境
- 分析经济指标对市场的影响
- Risk Analyst 评估系统性风险

#### `web_search`
**用途**: DuckDuckGo 网络搜索（白名单域名）  
**输入**: 搜索查询词、最大结果数、偏好域名  
**输出**: 搜索结果标题、URL、摘要  
**使用场景**: 
- 搜索特定股票或市场信息
- 获取实时市场动态
- 补充新闻扫描未覆盖的信息

#### `fetch_url`
**用途**: 获取指定 URL 的主要内容  
**输入**: URL 地址  
**输出**: 网页标题、正文内容、提取日期  
**使用场景**: 
- 获取新闻文章完整内容
- 分析特定网页信息
- 提取详细的市场分析

#### `plan_and_scan_news`
**用途**: 智能新闻规划和扫描（LLM 生成查询后搜索）  
**输入**: 市场视图（可选）、主题列表（可选）、最大文章数  
**输出**: 新闻文章列表（可能包含已获取的 URL 内容）  
**使用场景**: 
- Discussion Agent 自动规划新闻搜索策略
- 根据市场情况生成相关查询

### 💰 加密货币工具

#### `fetch_crypto_batch`
**用途**: 批量获取加密货币 OHLCV 数据和技术指标  
**输入**: 加密货币代码列表（如 BTC-USD, ETH-USD）、开始日期、结束日期  
**输出**: 与 `fetch_market_batch` 相同结构，但包含加密货币数据  
**使用场景**: 
- 分析加密货币市场趋势
- 评估加密货币与股票市场的相关性
- 获取加密货币作为市场情绪指标

**注意**: 加密货币目前仅用于分析，不参与实际交易。

#### `get_crypto_price`
**用途**: 获取单个加密货币的当前价格  
**输入**: 加密货币代码（如 BTC-USD）、开始日期、结束日期（可选）  
**输出**: 加密货币价格和技术指标  
**使用场景**: 
- 快速获取单个加密货币价格
- 评估加密货币市场情绪

### 🔍 工具使用策略

**工具调用优先级**:
1. **市场数据优先**: `fetch_market_batch` 通常最先调用，获取所有股票的技术指标（整个 universe，72只股票）
2. **情绪指标**: `vix_term`、`fear_greed` 用于评估市场情绪
3. **新闻补充**: `news_scan` 获取最新新闻，补充市场分析（最重要的工具之一）
4. **经济数据**: `fetch_jin10_economic_data` 评估宏观经济环境

**工具预算**: 默认每个交易循环有 **20 次工具调用预算**，允许 Agent 充分使用工具进行分析。

**重要提示**: 
- `news_scan` 是 Discussion Agent 最重要的工具之一，用于获取实时市场新闻
- `fetch_market_batch` 会分析整个 universe（从 `config.json` 读取，默认72只股票），而不仅仅是前几只
- 所有工具由 LLM 自主决定使用，没有硬编码的优先级限制

### 工具使用示例

**Agent 自动调用工具:**
```python
# Discussion Agent 会自动调用工具
tool_calls = [
    {
        "name": "news_scan",
        "args": {"keywords": ["NVDA", "earnings"], "max_articles": 10},
        "why": "Need to check latest news about NVDA earnings"
    },
    {
        "name": "vix_term",
        "args": {"start": "2024-01-01", "end": "2024-01-31"},
        "why": "Check VIX term structure for volatility assessment"
    },
    {
        "name": "fear_greed",
        "args": {},
        "why": "Get market sentiment indicator"
    }
]
```

**工具调用预算:**
- 默认预算: 20次工具调用
- 每个讨论轮次可以使用多个工具
- Agent 会自动选择最相关的工具

---

## 📁 项目结构

```
ai-trader-ollama/
├── backend/                 # Python 后端（主要代码）
│   ├── src/
│   │   ├── agents/         # 所有交易 Agent
│   │   │   ├── market_analyst.py      # 市场分析师
│   │   │   ├── analyst_discussion.py  # 讨论 Agent
│   │   │   ├── risk_analyst.py        # 风险分析师
│   │   │   ├── trader_agent.py       # 交易 Agent
│   │   │   └── toolbox.py            # 工具接口
│   │   ├── data/           # 投资组合、交易日志、内存管理
│   │   ├── tools/           # 所有可用工具
│   │   ├── orchestrator/    # 主交易循环
│   │   └── api/             # FastAPI 服务器
│   ├── config/             # 配置文件
│   │   └── config.json      # 主配置文件
│   ├── prompts/            # Agent 提示模板
│   │   ├── discussion_agent.yml
│   │   ├── trader_agent.yml
│   │   └── ...
│   ├── scripts/            # 工具脚本
│   │   ├── init_data.py
│   │   ├── start_api_background.ps1
│   │   └── ...
│   └── tests/              # 测试套件
├── frontend/               # 前端监控面板
│   └── monitor.html        # 主监控页面（纯HTML）
└── docs/                   # 文档
```

---

## 🔧 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError: src` | 从 `backend/` 目录运行 |
| Ollama 连接错误 | 运行 `ollama serve` |
| 端口 8000 被占用 | 使用 `backend\scripts\check_port.ps1` 查找并终止进程 |
| 前端 "Connection Error" | 检查后端 API 是否在端口 8000 运行 |
| 没有投资组合数据 | 运行 `python scripts/init_data.py` |
| PowerShell 执行策略错误 | 使用 `restart_api_bypass.ps1` 或 `powershell -ExecutionPolicy Bypass` |

### 验证系统状态

**检查后端 API:**
```powershell
curl http://localhost:8000/api/portfolio/real-time
```

**检查端口使用:**
```powershell
netstat -ano | findstr ":8000"
```

**检查数据初始化:**
```bash
ls backend/data/logs/portfolio_state.json
```

---

## 📚 详细文档

### 核心文档
- **[后端 README](backend/README.md)** - 后端完整文档（API、Agent、工具、脚本、测试）
- **[前端 README](frontend/README.md)** - 前端完整文档（功能、使用、配置、故障排除）

### 交易相关文档
- **[对冲策略指南](backend/HEDGING_STRATEGY.md)** - 反向ETF对冲策略说明
- **[杠杆ETF使用指南](backend/LEVERAGED_ETF_GUIDE.md)** - 杠杆ETF使用说明和风险提示
- **[市场指数集成](backend/MARKET_INDICES_INTEGRATION.md)** - 美股三大指数技术分析集成

### API 文档
- **[API端点文档](backend/API_ENDPOINTS.md)** - 完整API端点列表和说明
- **[前后端集成说明](backend/FRONTEND_BACKEND_INTEGRATION.md)** - 前后端数据流和集成指南
- **[投资组合更新流程](backend/PORTFOLIO_UPDATE_FLOW.md)** - 投资组合状态更新机制

---

## ✅ 系统状态

**当前状态**: 生产就绪 ✅

所有核心功能已实现并测试：
- ✅ 完整的交易循环（所有 Agent 参与）
- ✅ 内存管理系统（保存/加载历史决策）
- ✅ 自动化执行
- ✅ 实时监控面板（每60秒自动刷新）
- ✅ 对冲策略支持（反向ETF）
- ✅ 杠杆ETF支持（适度使用）
- ✅ 市场指数技术分析
- ✅ 完整的API文档
- ✅ Market Analyst 完整分析 universe 所有股票（72只）
- ✅ 详细的技术指标显示（RSI、MACD、信号评分等）

---

## 📄 License

MIT License © 2025 Wenyu Chiou

---

## 👤 Author

**Wenyu Chiou**  
Lehigh University  
📧 wec324@lehigh.edu
