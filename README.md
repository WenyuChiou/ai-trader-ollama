# 🔧 Backend - AI Trader API

> **FastAPI 后端服务，提供多 Agent 交易系统的核心功能**

## 📋 目录

- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [配置文件](#配置文件)
- [API 端点](#api-端点)
- [Agent 系统](#agent-系统)
- [可用工具](#可用工具)
- [脚本说明](#脚本说明)
- [测试指南](#测试指南)
- [故障排除](#故障排除)

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动 Ollama

```bash
# 启动 Ollama 服务（保持运行）
ollama serve

# 拉取 LLM 模型（在另一个终端）
ollama pull llama3.1
```

### 3. 初始化数据

```bash
python scripts/init_data.py
```

这将创建：
- 投资组合状态（初始现金：$10,000）
- 内存目录结构
- 交易日志文件

### 4. 启动 API 服务器

#### Windows (PowerShell)

```powershell
cd backend\scripts
.\start_api_background.ps1
```

#### 手动启动

```bash
cd backend
python -m uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
```

### 5. 验证 API 运行

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

---

## 📁 项目结构

```
backend/
├── src/                    # 源代码
│   ├── agents/            # Agent 实现
│   │   ├── market_analyst.py      # 市场分析师
│   │   ├── analyst_discussion.py  # 讨论 Agent
│   │   ├── risk_analyst.py        # 风险分析师
│   │   ├── trader_agent.py       # 交易 Agent
│   │   └── toolbox.py             # 工具接口
│   ├── api/               # FastAPI 服务器
│   │   └── server.py      # 主 API 文件
│   ├── data/              # 数据管理
│   │   ├── portfolio.py           # 投资组合
│   │   ├── trade_log.py           # 交易日志
│   │   ├── order_manager.py       # 订单管理
│   │   ├── real_time_tracker.py   # 实时追踪
│   │   └── memory_manager.py      # 内存管理
│   ├── tools/             # 工具库
│   │   ├── market_tools.py        # 市场数据工具
│   │   ├── news_tools.py          # 新闻工具
│   │   ├── sentiment_tools.py     # 情绪分析工具
│   │   └── crypto_tools.py        # 加密货币工具
│   ├── orchestrator/      # 交易流程编排
│   │   └── trading_cycle.py      # 交易循环
│   └── llm/               # LLM 客户端
│       └── ollama_client.py
├── config/                # 配置文件
│   ├── config.json        # 主配置文件
│   └── agents.yaml        # Agent 配置
├── prompts/               # Prompt 模板
│   ├── discussion_agent.yml
│   ├── trader_agent.yml
│   └── market_analyst.yml
├── scripts/               # 工具脚本
│   ├── init_data.py              # 数据初始化
│   ├── start_api_background.ps1  # 启动 API
│   ├── restart_api.ps1          # 重启 API
│   ├── clear_test_data.py       # 清空测试数据
│   └── simulate_october_history.py  # 十月模拟
├── data/                  # 数据目录（.gitignore）
│   └── logs/              # 日志文件
├── tests/                 # 测试套件
└── requirements.txt       # Python 依赖
```

---

## ⚙️ 配置文件

### `config/config.json`

主配置文件，包含：

- **股票池配置** (`universe`): 72只股票 + 反向ETF + 杠杆ETF
- **市场指数** (`market_indices`): S&P 500, NASDAQ, Dow Jones
- **仓位限制**:
  - `position_limit_per_stock`: 单股最大仓位 (15%)
  - `position_limit_total`: 总仓位上限 (85%)
  - `position_limit_min_per_stock`: 单股最小仓位 (3%)
- **LLM 配置**:
  - `default_model`: 默认模型 (llama3.1)
  - `ollama_host`: Ollama 服务器地址
  - `timeout_seconds`: 请求超时时间
- **讨论配置**:
  - `discussion_rounds`: 讨论轮数 (3)
  - `discussion_tool_budget`: 工具调用预算 (20)

详细配置说明请参考：[配置文件设置](../README.md#-配置文件设置)

---

## 🔌 API 端点

### 核心端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | API 健康检查 |
| `/api/portfolio/real-time` | GET | 实时投资组合数据 |
| `/api/portfolio/equity-history` | GET | 净值历史 |
| `/api/trades/recent` | GET | 最近交易记录 |
| `/api/agents/conversations` | GET | Agent 对话记录 |
| `/api/trading/execute-trade` | POST | 执行交易循环 |
| `/api/trading/simulate-october` | POST | 启动十月模拟 |
| `/api/trading/simulate-status` | GET | 模拟状态 |
| `/api/tools/list` | GET | 可用工具列表 |
| `/api/system/info` | GET | 系统信息 |

**完整 API 文档**: 参见 [API_ENDPOINTS.md](API_ENDPOINTS.md)

---

## 🤖 Agent 系统

### Agent 类型

| Agent | 职责 | 主要输出 |
|-------|------|----------|
| **Market Analyst** | 分析市场趋势，生成股票推荐 | 推荐股票列表、市场情绪 |
| **Discussion Agent** | 多轮讨论分析，综合评估 | 最终立场、推理过程 |
| **Risk Analyst** | 评估投资组合风险，仓位控制 | 风险报告、仓位建议 |
| **Trader Agent** | 生成买卖订单 | 买入/卖出订单列表 |

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

详细说明请参考：[Agent 系统](../README.md#-agent-系统)

---

## 🛠️ 可用工具

Agent 可以使用的工具：

### 市场数据工具
- `fetch_market_batch`: 批量获取股票OHLCV和技术指标
- `vix_term`: 获取VIX期限结构
- `vix_close`: 获取VIX收盘价序列
- `fear_greed`: 获取恐惧贪婪指数

### 新闻与经济数据工具
- `news_scan`: 扫描新闻文章
- `fetch_jin10_news`: 获取金十财经新闻
- `fetch_jin10_economic_data`: 获取经济数据
- `web_search`: DuckDuckGo搜索
- `fetch_url`: 获取URL主要内容

### 加密货币工具
- `fetch_crypto_batch`: 批量获取加密货币数据
- `get_crypto_price`: 获取单个加密货币价格

完整工具列表请参考：[可用工具](../README.md#-可用工具)

---

## 📜 脚本说明

### 核心脚本

| 脚本 | 说明 |
|------|------|
| `init_data.py` | 初始化数据（投资组合、内存、日志） |
| `start_api_background.ps1` | 在后台启动 API 服务器 |
| `restart_api.ps1` | 重启 API 服务器 |
| `clear_test_data.py` | 清空所有测试数据和记录 |
| `simulate_october_history.py` | 运行十月历史模拟 |

### 调度脚本

| 脚本 | 说明 |
|------|------|
| `schedule_daily_task.ps1` | 设置每日交易任务 |
| `schedule_hourly_update.ps1` | 设置每小时更新任务 |

### 工具脚本

| 脚本 | 说明 |
|------|------|
| `check_api_status.ps1` | 检查 API 运行状态 |
| `check_port.ps1` | 检查端口占用情况 |
| `show_discussion_rounds.py` | 显示讨论轮次 |

---

## 🧪 测试指南

### 运行测试

```bash
cd backend

# 运行所有测试
python tests/run_all.py

# 运行特定测试
python test_full_workflow.py
python test_october_simulation_full.py
```

### 测试文件说明

| 测试文件 | 说明 |
|----------|------|
| `test_full_workflow.py` | 完整工作流测试（市场数据、Agent分析、交易决策） |
| `test_october_simulation_full.py` | 十月模拟完整测试 |
| `test_frontend_integration.py` | 前端集成测试 |
| `test_api_portfolio_endpoint.py` | API 端点测试 |

---

## 🔧 故障排除

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| `ModuleNotFoundError: src` | 从 `backend/` 目录运行 |
| Ollama 连接错误 | 运行 `ollama serve` |
| 端口 8000 被占用 | 使用 `scripts/check_port.ps1` 查找并终止进程 |
| PowerShell 执行策略错误 | 使用 `restart_api_bypass.ps1` |

### 重启 API

```powershell
cd backend\scripts
.\restart_api_bypass.ps1
```

详细故障排除请参考：[故障排除](../README.md#-故障排除)

---

## 📚 相关文档

- [API 端点文档](API_ENDPOINTS.md)
- [前端后端集成](FRONTEND_BACKEND_INTEGRATION.md)
- [投资组合更新流程](PORTFOLIO_UPDATE_FLOW.md)
- [对冲策略指南](HEDGING_STRATEGY.md)
- [杠杆ETF指南](LEVERAGED_ETF_GUIDE.md)
- [市场指数集成](MARKET_INDICES_INTEGRATION.md)
- [重启 API 指南](RESTART_API_GUIDE.md)

---

## 📝 License

MIT License © 2025 Wenyu Chiou

