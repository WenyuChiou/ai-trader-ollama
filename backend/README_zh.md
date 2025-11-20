# 🔧 后端 - AI Trader API

> **FastAPI 后端服务，为多代理交易系统提供核心功能**

## 📋 目录

- [快速开始](#-快速开始)
- [项目结构](#-项目结构)
- [配置文件](#-配置文件)
- [API 端点](#-api-端点)
- [代理系统](#-代理系统)
- [可用工具](#-可用工具)
- [脚本](#-脚本)
- [测试指南](#-测试指南)
- [故障排除](#-故障排除)

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

# 拉取 LLM 模型（在另一个终端中）
ollama pull llama3.1
```

### 3. 初始化数据

```bash
# 从项目根目录
python scripts/init_data.py

# 或从 backend 目录
python ../scripts/init_data.py
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

### 5. 验证 API 是否运行

```powershell
curl http://localhost:8000/
```

**预期响应**：
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
│   ├── agents/            # 代理实现
│   │   ├── market_analyst.py      # 市场分析师
│   │   ├── analyst_discussion.py  # 讨论代理
│   │   ├── risk_analyst.py        # 风险分析师
│   │   ├── trader_agent.py       # 交易代理
│   │   └── toolbox.py             # 工具接口
│   ├── api/               # FastAPI 服务器
│   │   └── server.py      # 主 API 文件
│   ├── data/              # 数据管理
│   │   ├── portfolio.py           # 投资组合
│   │   ├── trade_log.py           # 交易日志
│   │   ├── order_manager.py       # 订单管理
│   │   ├── real_time_tracker.py   # 实时跟踪
│   │   └── memory_manager.py      # 内存管理
│   ├── tools/             # 工具库
│   │   ├── market_tools.py        # 市场数据工具
│   │   ├── news_tools.py          # 新闻工具
│   │   ├── sentiment_tools.py     # 情绪分析工具
│   │   └── crypto_tools.py        # 加密货币工具
│   ├── orchestrator/      # 交易流程编排
│   │   └── trading_cycle.py      # 交易周期
│   └── llm/               # LLM 客户端
│       └── ollama_client.py
├── config/                # 配置文件
│   ├── config.json        # 主配置文件
│   └── agents.yaml        # 代理配置
├── prompts/               # 提示模板
│   ├── discussion_agent.yml
│   ├── trader_agent.yml
│   └── market_analyst.yml
├── scripts/               # 实用脚本
│   ├── start_api_background.ps1  # 启动 API
│   ├── restart_api.ps1          # 重启 API
│   ├── clear_test_data.py       # 清除测试数据
│   └── simulate_october_history.py  # 10 月模拟
├── data/                  # 数据目录 (.gitignore)
│   └── logs/              # 日志文件
├── tests/                 # 测试套件
└── requirements.txt       # Python 依赖
```

---

## ⚙️ 配置文件

### `config/config.json`

主配置文件，包括：

- **股票池配置** (`universe`)：72 只股票 + 反向 ETF + 杠杆 ETF
- **市场指数** (`market_indices`)：S&P 500、NASDAQ、道琼斯
- **仓位限制**：
  - `position_limit_per_stock`：每只股票最大仓位（15%）
  - `position_limit_total`：总仓位限制（85%）
  - `position_limit_min_per_stock`：每只股票最小仓位（3%）
- **LLM 配置**：
  - `default_model`：默认模型（llama3.1）
  - `ollama_host`：Ollama 服务器地址
  - `timeout_seconds`：请求超时
- **讨论配置**：
  - `discussion_rounds`：讨论轮数（3）
  - `discussion_tool_budget`：工具调用预算（20）

有关详细配置说明，请参阅：[配置设置](../README.md#-configuration-settings)

---

## 🔌 API 端点

### 核心端点

| 端点 | 方法 | 描述 |
|----------|--------|-------------|
| `/` | GET | API 健康检查 |
| `/api/portfolio/real-time` | GET | 实时投资组合数据 |
| `/api/portfolio/equity-history` | GET | 权益历史 |
| `/api/trades/recent` | GET | 最近的交易记录 |
| `/api/agents/conversations` | GET | 代理对话记录 |
| `/api/trading/execute-trade` | POST | 执行交易周期 |
| `/api/trading/simulate-october` | POST | 启动 10 月模拟 |
| `/api/trading/simulate-status` | GET | 模拟状态 |
| `/api/tools/list` | GET | 可用工具列表 |
| `/api/system/info` | GET | 系统信息 |

**完整 API 文档**：请参阅 [API 端点文档](../docs/archive/API_ENDPOINTS.md)

---

## 🤖 代理系统

### 代理类型

| 代理 | 职责 | 主要输出 |
|-------|---------------|-------------|
| **市场分析师** | 分析市场趋势，生成股票推荐 | 推荐股票列表、市场情绪 |
| **讨论代理** | 多轮讨论分析，综合评估 | 最终立场、推理过程 |
| **风险分析师** | 评估投资组合风险，仓位控制 | 风险报告、仓位建议 |
| **交易代理** | 生成买入/卖出订单 | 买入/卖出订单列表 |

### 代理工作流程

```
1. 市场数据收集
   ↓
2. 市场分析师 → 推荐股票 + 市场情绪
   ↓
3. 讨论代理（3 轮） → 最终立场 + 推理
   ↓
4. 风险分析师 → 风险报告 + 仓位建议
   ↓
5. 交易代理 → 买入/卖出订单
   ↓
6. 订单执行 → 更新投资组合
```

有关详细描述，请参阅：[代理系统](../README.md#-agent-system)

---

## 🛠️ 可用工具

代理可用的工具：

### 市场数据工具
- `fetch_market_batch`：批量获取股票 OHLCV 和技术指标
- `vix_term`：获取 VIX 期限结构
- `vix_close`：获取 VIX 收盘价序列
- `fear_greed`：获取恐惧与贪婪指数

### 新闻和经济数据工具

#### 新闻工具（更新于 2025-11-10）

**`news_scan`**：扫描最新新闻文章，智能过滤
- **功能**：
  - 自动过滤过时的新闻来源（WSJ、Reuters、FT、Zero Hedge）
  - 仅返回经过验证的新鲜来源（<6 小时）
  - 支持基于关键字的搜索
  - 日期过滤（默认：10 天，可配置）
- **新闻来源**（10 个经过验证的新鲜来源）：
  - **核心财经新闻**：CNBC、MarketWatch、Seeking Alpha、Investing.com、Benzinga、Bloomberg
  - **社区来源**：Reddit（WSB、Investing、Stocks）、Hacker News
- **用法**：
  ```python
  from src.tools.news_tools import news_scan
  result = news_scan(keywords=["market", "AI"], max_articles=12, recency_days=7)
  ```

**`business_rss`**：从 RSS 源获取商业新闻
- **功能**：
  - 日期过滤（默认：48 小时，可通过 `max_age_hours` 配置）
  - 按日期自动排序（最新优先）
  - 所有新闻条目都包含时间戳信息
- **用法**：
  ```python
  from src.tools.news_tools import business_rss
  # 获取过去 48 小时的新闻（默认）
  news = business_rss(max_items=40)
  # 仅获取过去 24 小时的新闻
  fresh_news = business_rss(max_items=40, max_age_hours=24)
  ```

**其他新闻工具**：
- `fetch_jin10_news`：获取 Jin10 财经新闻
- `fetch_jin10_economic_data`：获取经济数据
- `web_search`：DuckDuckGo 搜索
- `fetch_url`：获取 URL 主要内容
- `plan_and_scan_news`：LLM 驱动的新闻查询规划和扫描

**新闻工具验证**：
```bash
# 检查新闻来源新鲜度
python check_news_recency.py

# 快速测试新闻工具
python quick_test_news.py
```

**文档**：
- `NEWS_TOOL_UPDATE.md` - 新闻工具更新摘要
- `NEWS_UPDATE_VERIFICATION.md` - 验证报告

### 加密货币工具
- `fetch_crypto_batch`：批量获取加密货币数据
- `get_crypto_price`：获取单个加密货币价格

有关完整工具列表，请参阅：[可用工具](../README.md#-available-tools)

---

## 📜 脚本

### 核心脚本

| 脚本 | 描述 |
|--------|-------------|
| `start_api_background.ps1` | 在后台启动 API 服务器 |
| `restart_api.ps1` | 重启 API 服务器 |
| `clear_test_data.py` | 清除所有测试数据和记录 |
| `simulate_october_history.py` | 运行 10 月历史模拟 |
| `run_full_workflow.py` | 运行完整交易工作流程测试 |

### 新闻工具脚本

| 脚本 | 描述 |
|--------|-------------|
| `check_news_recency.py` | 检查所有新闻来源的新鲜度 |
| `quick_test_news.py` | 快速测试新闻工具功能 |

### 实用脚本

| 脚本 | 描述 |
|--------|-------------|
| `check_cash_vs_orders.py` | 检查订单是否超过可用现金 |
| `check_holdings_vs_orders.py` | 比较投资组合持仓与已成交订单 |
| `check_pending_orders_detail.py` | 待处理订单的详细分析 |
| `analyze_all_orders.py` | 所有订单的综合分析 |

### 调度脚本

| 脚本 | 描述 |
|--------|-------------|
| `schedule_daily_task.ps1` | 安排每日交易任务 |
| `schedule_hourly_update.ps1` | 安排每小时更新任务 |

### 实用脚本

| 脚本 | 描述 |
|--------|-------------|
| `check_api_status.ps1` | 检查 API 运行状态 |
| `check_port.ps1` | 检查端口使用情况 |
| `show_discussion_rounds.py` | 显示讨论轮次 |

---

## 🧪 测试指南

### 综合测试框架

后端包括一个综合的 4 轮测试框架：

#### 第 1 轮：后端 API 测试 ✅
```bash
python test_comprehensive.py
```
- 测试所有 API 端点
- 验证数据格式
- 检查文件一致性
- **结果**：9/9 测试通过（100%）

#### 第 2 轮：前端功能测试 ✅
```bash
python test_frontend_comprehensive.py
```
- 测试所有按钮功能
- 验证数据显示
- 检查错误处理
- **结果**：22/22 测试通过（100%）

#### 第 3 轮：数据记录场景（下一步）
- 测试初始化数据记录
- 测试交易周期数据记录
- 验证权益历史更新

#### 第 4 轮：前端-后端集成
- 端到端工作流程测试
- 实时数据同步

### 基于场景的测试

```bash
# 运行所有场景（1-12）
python test_scenarios.py --scenario 1 --auto
python test_scenarios.py --scenario 2 --auto
# ... 查看 TEST_COMMANDS.md 获取完整列表
```

### 测试文件描述

| 测试文件 | 描述 |
|-----------|-------------|
| `test_comprehensive.py` | 第 1 轮：后端 API 综合测试 |
| `test_frontend_comprehensive.py` | 第 2 轮：前端功能测试 |
| `test_scenarios.py` | 基于场景的测试（12 个场景） |
| `test_full_workflow.py` | 完整工作流程测试 |
| `test_frontend_integration.py` | 前端集成测试 |

### 测试文档

- **测试命令**：`TEST_COMMANDS.md` - 所有测试命令
- **测试指南**：`COMPREHENSIVE_TESTING_GUIDE.md` - 完整测试指南
- **第 1 轮报告**：`TEST_ROUND_1_REPORT.md` - 后端 API 测试结果
- **第 2 轮报告**：`TEST_ROUND_2_REPORT.md` - 前端测试结果

---

## 🔧 故障排除

### 常见问题

| 问题 | 解决方案 |
|-------|----------|
| `ModuleNotFoundError: src` | 从 `backend/` 目录运行 |
| Ollama 连接错误 | 运行 `ollama serve` |
| 端口 8000 正在使用 | 使用 `scripts/check_port.ps1` 查找并终止进程 |
| PowerShell 执行策略错误 | 使用 `restart_api_bypass.ps1` |

### 重启 API

```powershell
cd backend\scripts
.\restart_api_bypass.ps1
```

有关详细故障排除，请参阅：[故障排除](../README.md#-troubleshooting)

---

## 📚 相关文档

### 核心文档
- [API 端点文档](../docs/archive/API_ENDPOINTS.md)
- [前端-后端集成](../docs/archive/FRONTEND_BACKEND_INTEGRATION.md)
- [投资组合更新流程](../docs/archive/PORTFOLIO_UPDATE_FLOW.md)
- [交易时间逻辑](docs/TRADING_HOURS_LOGIC.md)

### 功能文档
- [新闻工具更新](NEWS_TOOL_UPDATE.md) - 新闻工具增强和更新
- [新闻更新验证](NEWS_UPDATE_VERIFICATION.md) - 新闻工具验证报告
- [持仓信息增强](POSITION_INFO_ENHANCEMENT.md) - 持仓信息增强
- [工作流程优化](WORKFLOW_OPTIMIZATION_SUMMARY.md) - 交易工作流程优化
- [重要文件](IMPORTANT_FILES.md) - 重要文件和脚本指南

### 策略指南
- [对冲策略指南](../docs/archive/HEDGING_STRATEGY.md)
- [杠杆 ETF 指南](../docs/archive/LEVERAGED_ETF_GUIDE.md)
- [市场指数集成](../docs/archive/MARKET_INDICES_INTEGRATION.md)

### 操作指南
- [重启 API 指南](../docs/archive/RESTART_API_GUIDE.md)

---

## 📝 许可证

MIT License © 2025 Wenyu Chiou

