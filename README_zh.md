# 💹 AI-Trader Ollama

**语言**: [中文版](README_zh.md) | [English](README.md)

---

> **多代理交易系统，配备 29 个高级工具 + 6 个专业 LLM 代理**  
> 📈 分析 **NASDAQ-100**（118+ 个股票代码），提供全面的基本面、技术面和情绪分析  
> 🧠 完全自主的代理协作，集成实时市场数据  
> 🎨 深色科技主题 UI，实时可视化和更新  
> 🧠 **RAG 内存系统**：代理从历史交易决策中学习  
> 📰 **增强新闻集成**：前端显示带摘要、来源和时间戳的新闻数据

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![LangChain](https://img.shields.io/badge/LangChain-Enabled-green.svg)](https://www.langchain.com/)
[![Ollama](https://img.shields.io/badge/Ollama-deepseek--r1-orange.svg)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

### 🌐 **在线演示**

> **在线查看仪表板**：[**https://WenyuChiou.github.io/ai-trader-ollama/monitor.html**](https://WenyuChiou.github.io/ai-trader-ollama/monitor.html)
> 
> 🔒 **只读模式**：公共网站处于只读模式以确保安全。交易控制已禁用。使用 localhost 获得完全控制。

---

## 📚 目录

- [系统概述](#-系统概述)
- [快速开始](#-快速开始)
- [历史性能分析](#-历史性能分析)
- [计划任务与自动化](#-计划任务与自动化)
- [API 连接监控](#-api-连接监控)
- [运行系统](#-运行系统)
- [配置](#-配置)
- [数据存储与记录](#-数据存储与记录)
- [多代理架构](#-多代理架构)
- [工具套件（28 个工具）](#-工具套件28-个工具)
- [交易工作流程](#-交易工作流程)
- [API 端点](#-api-端点)
- [部署](#-部署)
- [故障排除](#-故障排除)
- [文档](#-文档)
- [测试](#-测试)

---

## 🌟 系统概述

### 什么是 AI-Trader Ollama？

AI-Trader Ollama 是一个**完整的交易平台**，同时提供后端交易系统和前端服务，包括实时可视化、监控和全面的测试功能。它是一个**完全自主的多代理交易系统**，结合了：

**后端交易系统：**
- **6 个专业 LLM 代理**协同工作
- **28 个高级工具**用于市场分析（21 个市场工具 + 7 个内存/RAG 工具）
- **实时数据集成**来自多个来源
- **智能风险管理**，带持仓控制
- **RAG 内存系统**：代理自动检索并学习历史交易决策
- **时间范围净值跟踪**：查看日/周/月/自定义期间的组合表现
- **每周内存压缩**：自动汇总每周内存（仅周一和周末）

**前端服务与可视化：**
- **实时监控仪表板**，支持实时更新
- **交互式 UI**，显示代理讨论、工具结果和交易决策
- **订单执行可视化**，包含详细的交易记录
- **性能分析**，提供图表和统计数据
- **深色科技主题界面**，专为交易工作流程优化

**测试与质量保证：**
- **全面的测试套件**（约 29 个测试），涵盖集成、端到端和 API 端点测试
- **自动化测试脚本**，用于订单记录、投资组合管理和代理架构测试
- **双语测试文档**（英文和中文）
- **快速测试工具**，支持快速开发周期

**性能优化**：
  - 工具结果缓存和并行执行
  - 智能预算管理防止第 2/3 轮不必要的工具请求
  - 优化的强制工具逻辑（限制为前 5 个推荐股票）
  - 预算耗尽时早期检查跳过工具执行
  - **结果**：执行速度提升 30-40%（从每交易周期约 10 分钟降至约 6-7 分钟）
  - **长期性能优化**：尾部文件读取（内存减少 99%）、日志轮转（50MB 阈值）、缓存层（读取减少 80-90%）、性能监控

### 核心理念

1. **多视角分析**：不同代理从各自专业角度分析市场
2. **工具多样性**：28 个工具提供全面的市场覆盖（21 个市场工具 + 7 个内存/RAG 工具）
3. **RAG 系统**：具有语义搜索、质量评分和关系分析的高级内存系统
4. **工具过滤与验证**：系统自动过滤无效工具调用并强制执行每个分析师类型的限制
5. **RAG 内存系统**：代理在做出决策前自动检索历史内存
6. **自主决策**：代理讨论、辩论并达成共识
7. **风险优先方法**：每个决策都经过风险分析
8. **透明度**：所有推理都被记录并可见
9. **历史学习**：代理从过去的成功和失败中学习

---

## 📊 历史性能分析

### 查看交易表现

系统通过 API 端点和前端仪表板提供全面的性能分析。

#### 关键性能指标

- **总回报**：以美元和百分比表示的总体盈亏
- **年化回报**：根据时间段调整的回报（如果数据跨越多天）
- **胜率**：盈利交易百分比
- **最大回撤**：最大的峰谷跌幅
- **夏普比率**：风险调整后的回报指标（年化，越高越好）
- **索提诺比率**：下行风险调整后的回报（仅考虑负回报，越高越好）
- **卡玛比率**：年化回报除以最大回撤（越高越好）
- **平均持仓期**：持仓的平均天数
- **最佳/最差交易**：最佳和最差表现交易，包含股票代码和 P&L
- **交易统计**：总交易数、盈利交易、亏损交易、平均交易回报

#### 使用性能 API

**获取总体统计**：
```bash
curl "http://localhost:8000/api/performance/statistics?start_date=2025-01-01&end_date=2025-01-31"
```

**按日期获取交易**：
```bash
curl "http://localhost:8000/api/performance/trades-by-date?start_date=2025-01-01&limit=30"
```

**获取股票代码分析**：
```bash
# 所有股票代码
curl "http://localhost:8000/api/performance/symbol-analysis"

# 特定股票代码
curl "http://localhost:8000/api/performance/symbol-analysis?symbol=NVDA"
```

#### 性能指标说明

- **总回报 %**：`(当前价值 - 初始价值) / 初始价值 * 100`
- **胜率**：`(盈利交易数 / 总交易数) * 100`
- **最大回撤**：从峰值下降的最大幅度
- **夏普比率**：`(平均回报 / 标准差) * sqrt(252)`（年化，越高越好）
- **索提诺比率**：`(平均回报 / 下行标准差) * sqrt(252)`（年化，仅考虑负回报，越高越好）
- **卡玛比率**：`年化回报 % / 最大回撤 %`（越高越好，衡量每单位回撤风险的回报）
- **平均持仓期**：每个股票代码买入和卖出之间的平均天数
- **最佳交易**：最高已实现 P&L 交易，包含股票代码、金额和百分比
- **最差交易**：最低已实现 P&L 交易，包含股票代码、金额和百分比

#### 数据来源

性能分析使用以下数据：
- `equity_history.jsonl`：净资产价值历史（每 30 分钟记录一次）
- `filled_orders.jsonl`：已完成的交易，包含已实现 P&L

有关详细文件格式，请参阅[数据格式文档](docs/DATA_FORMAT.md)。

---

## 🚀 快速开始

### 前置要求

**1. Python 环境**
- 需要 Python 3.10 或更高版本
- 从以下地址下载：https://www.python.org/downloads/

**2. Ollama 设置**
- 从以下地址安装 Ollama：https://ollama.ai/
- 拉取 LLM 模型：`ollama pull deepseek-r1`

**3. API 密钥（可选但推荐）**
- FRED API 用于经济数据（免费）：https://fred.stlouisfed.org/docs/api/api_key.html
- 设置环境变量：`$env:FRED_API_KEY="your_api_key_here"`

---

### 🎯 快速设置（3 步）

**步骤 1：安装依赖**
```powershell
# 从项目根目录运行
.\scripts\setup_step1_install_dependencies.ps1
```
这将：
- ✅ 检查 Python 安装
- ✅ 检查 Ollama 安装并拉取 deepseek-r1 模型
- ✅ 创建虚拟环境
- ✅ 安装所有 Python 依赖

**步骤 2：配置系统**
```powershell
.\scripts\setup_step2_configure.ps1
```
这将：
- ✅ 验证配置文件（config.json, agents.yaml）
- ✅ 初始化数据目录
- ✅ 初始化投资组合状态
- ✅ 检查环境变量

**步骤 3：启动服务**
```powershell
.\scripts\setup_step3_start_services.ps1
```
这将：
- ✅ 检查 Ollama 服务
- ✅ 检查端口可用性
- ✅ 启动 API 服务器（从 3 个选项中选择）

**设置后**：
- 🌐 **API 服务器**：http://localhost:8000
- 📊 **API 文档**：http://localhost:8000/docs
- 🎨 **前端**：在浏览器中打开 `frontend/monitor.html`

**可选：设置计划任务**：
```powershell
.\scripts\setup_scheduled_tasks.ps1
```
这将配置交易、净值记录和数据更新的自动化任务。

**或一次性运行所有步骤**：
```powershell
.\scripts\setup_all_steps.ps1
```

---

### 🎬 首次运行

完成设置后：

1. **启动 Ollama**（如果尚未运行）：
```powershell
   ollama serve
   ```

2. **打开前端**：
   - 在浏览器中打开 `frontend/monitor.html`
   - 或通过以下地址访问：http://localhost:3000/monitor.html

3. **执行首次交易周期**：
   - 点击 "▶️ 开始交易" 或 "▶️ 运行分析" 按钮
   - 等待代理分析（完整 3 轮讨论约需 6-7 分钟）
   - **性能说明**：系统使用智能预算管理优化执行时间
   - 在仪表板中查看结果

4. **查看结果**：
   - **投资组合**：当前持仓和 P&L
   - **对话**：代理讨论和分析
   - **交易**：交易历史
   - **图表**：带时间范围选择器（日/周/月/自定义）的净值曲线
   - **内存**：历史交易决策和学习

---

### 📋 手动安装（替代方案）

如果您更喜欢手动设置：

**1. 克隆仓库**
```bash
git clone https://github.com/WenyuChiou/ai-trader-ollama.git
cd ai-trader-ollama
```

**2. 安装依赖**
```powershell
# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
.venv\Scripts\Activate.ps1

# 安装依赖
cd backend
pip install -r requirements.txt
cd ..
```

**3. 初始化系统**
```powershell
python scripts/init_data.py
```

**4. 启动后端 API**

**选项 A：任务计划程序（推荐用于长期运行）**
```powershell
# 右键单击并以管理员身份运行：
scripts\start_api_task_admin.bat
```

**选项 B：Windows 服务（需要 NSSM）**
```powershell
# 右键单击并以管理员身份运行：
scripts\start_api_service_admin.bat
```

**选项 C：开发模式（需要保持窗口打开）**

**使用虚拟环境**（推荐）：

**方法 A：使用 & 运算符**（PowerShell 标准，与监控脚本相同）：
```powershell
# 首先激活虚拟环境
& .\.venv\Scripts\Activate.ps1

# 导航到后端目录
cd backend

# 启动 API 服务器
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**方法 B：使用点源**（替代方案）：
```powershell
# 首先激活虚拟环境
. .\.venv\Scripts\Activate.ps1

# 导航到后端目录
cd backend

# 启动 API 服务器
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**直接命令**（如果虚拟环境已激活）：
```powershell
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**命令参数**：
- `--host 0.0.0.0`：监听所有网络接口（可从其他设备访问）
- `--port 8000`：使用端口 8000
- `--reload`：启用代码更改时自动重新加载（开发模式）

**注意事项**：
- 保持终端窗口打开。关闭窗口将停止 API 服务器。
- 两种激活方法（方法 A 和方法 B）都有效。方法 A（`&`）是 PowerShell 标准，与监控脚本用于自动重启的方法匹配。

**5. 访问仪表板**
- 在浏览器中打开 `frontend/monitor.html`
- 或通过以下地址访问：http://localhost:3000/monitor.html（如果使用本地服务器）

---

## ⚙️ 配置

> **📝 配置文件**：所有配置都通过 JSON/YAML 文件完成。无需修改代码！

### 📄 主配置文件：`backend/config/config.json`

主配置文件控制交易参数、股票池选择和 LLM 设置。

#### 📋 完整配置参考

```json
{
  "universe_source": "custom",
  "universe_limit": 100,
  "universe": ["NVDA", "MSFT", "AAPL", ...],
  "initial_cash": 10000,
  "position_limit_mode": "auto",
  "_position_limit_per_stock": null,
  "_position_limit_total": null,
  "_position_limit_min_per_stock": null,
  "min_cash_reserve_ratio": null,
  "discussion_rounds": 3,
  "discussion_auto_tools": true,
  "discussion_tool_budget": 15,
  "max_orders_per_cycle": 20,
  "trade_cooldown_hours": 24.0,
  "llm": {
    "default_model": "deepseek-r1",
    "ollama_host": "http://localhost:11434",
    "auto_pull": true,
    "timeout_seconds": 8.0
  },
  "preferred_domains": [
    "www.cboe.com",
    "www.wsj.com",
    "www.reuters.com"
  ]
}
```

#### 🔧 配置参数

| 参数 | 描述 | 选项 | 默认值 |
|-----------|-------------|---------|---------------|
| **交易股票池** |
| `universe_source` | 股票池来源类型 | `"custom"`, `"nasdaq100"` | `"custom"` |
| `universe_limit` | 最大分析股票数量 | 正整数 | `100` |
| `universe` | 股票代码列表 | 字符串数组 | NASDAQ-100 + ETFs |
| **资金与持仓限制** |
| `initial_cash` | 起始资金 | 浮点数 | `10000` (USD) |
| `position_limit_mode` | 持仓限制模式 | `"auto"`, `"configured"` | `"auto"` (LLM 自主) |
| `_position_limit_per_stock` | 每只股票最大 % | `0.0-1.0` 或 `null` | `null` (仅在 mode=`"configured"` 时使用) |
| `_position_limit_total` | 总持仓最大 % | `0.0-1.0` 或 `null` | `null` (仅在 mode=`"configured"` 时使用) |
| `_position_limit_min_per_stock` | 每只股票最小 % | `0.0-1.0` 或 `null` | `null` (仅在 mode=`"configured"` 时使用) |
| `min_cash_reserve_ratio` | 最小现金储备 % | `0.0-1.0` 或 `null` | `null` (仅在 mode=`"configured"` 时使用) |
| **交易行为** |
| `discussion_rounds` | 讨论轮数 | `1-5` | `3` |
| `discussion_auto_tools` | 启用自动工具调用 | `true`, `false` | `true` |
| `discussion_tool_budget` | 每周期最大工具调用数（仅限市场/技术/情绪分析师） | 正整数 | `15` |
| `budget_allocation` | 每个分析师的预算分配（基本面分析师除外） | 对象 | `{"market": 3, "technical": 4, "sentiment": 4}` |
| `max_orders_per_cycle` | 每周期最大订单数 | 正整数 | `20` |
| `trade_cooldown_hours` | 交易同一股票代码前的等待小时数 | 浮点数 | `24.0` |
| **LLM 配置** |
| `llm.default_model` | LLM 模型名称 | `"deepseek-r1"`, `"deepseek-r1:7b"`, `"deepseek-r1:32b"` 等 | `"deepseek-r1"` |
| `llm.ollama_host` | Ollama 服务器地址 | URL 字符串 | `"http://localhost:11434"` |
| `llm.auto_pull` | 如果未找到模型则自动拉取 | `true`, `false` | `true` |
| `llm.timeout_seconds` | 请求超时 | 浮点数（秒） | `8.0` |
| **数据来源** |
| `preferred_domains` | 首选新闻/数据域名 | URL 数组 | 金融新闻网站 |

#### 📊 参数详情

**交易股票池**：
- `universe`：要交易的股票代码列表（包括反向/杠杆 ETF，如 SQQQ, TQQQ, SPXL, UPRO）
- `universe_limit`：最大分析股票数量（默认：100）
- **注意**：加密货币代码会自动从股票分析中过滤。系统专注于传统股票和 ETF。

**持仓限制（两种模式 - 自动 vs 配置）**：

**模式 1：`"auto"`（默认 - LLM 自主）**：
- 持仓限制**已禁用** - 代理有**完全自由**决定持仓大小
- 代理根据以下因素决定：
  - 推荐股票数量（多只股票 → 较小持仓，少数股票 → 较大持仓）
  - 信号强度和多样化需求
  - 市场条件和风险评估
- 现金储备也由 LLM 决定（无硬性限制）
- **这是默认模式** - 代理自主运行

**模式 2：`"configured"`（带约束）**：
- 将 `position_limit_mode` 设置为 `"configured"` 以启用硬性限制
- 取消注释并设置持仓限制值：
  - `_position_limit_per_stock`：每只股票最大 %（例如，0.15 = 15%）
  - `_position_limit_total`：总持仓最大 %（例如，0.80 = 80%，保留 20% 现金）
  - `_position_limit_min_per_stock`：每只股票最小 %（例如，0.03 = 3%）
  - `min_cash_reserve_ratio`：最小现金储备 %（例如，0.20 = 20%）
- 代理在做出交易决策时将遵守这些硬性限制

**交易行为**：
- `initial_cash`：起始资金（默认 $10,000）
- `discussion_rounds`：讨论轮数（默认 3，每轮包括所有 4 个分析师）
- `discussion_tool_budget`：每周期最大工具调用数（默认 15，仅在市场/技术/情绪分析师之间共享）
- `budget_allocation`：可选的每个分析师预算分配（例如，`{"market": 3, "technical": 4, "sentiment": 4}`）。基本面分析师自动排除，因为其工具不受预算限制。
- `max_orders_per_cycle`：每个交易周期的最大订单数（默认 20，LLM 的指导原则）
- `trade_cooldown_hours`：在再次交易同一股票代码前等待的小时数（默认 24.0）

**LLM 配置**：
- `llm.default_model`：**所有代理的统一 LLM 模型**（默认 `deepseek-r1`）
  - 可用模型：`deepseek-r1`, `deepseek-r1:7b`, `deepseek-r1:32b` 等
  - **所有代理默认使用此模型** - 除非您希望特定代理使用不同模型，否则无需在 `agents.yaml` 中指定
  - 要使用不同模型，更改此值并确保在 Ollama 中拉取：`ollama pull <model-name>`
- `llm.ollama_host`：Ollama 服务器地址（默认：`http://localhost:11434`）
- `llm.auto_pull`：如果未找到模型则自动拉取（默认 true）
- `llm.timeout_seconds`：请求超时（默认 8.0 秒）

#### 更改 LLM 模型

**✅ 统一模型配置（推荐）**：

所有代理自动使用 `config.json` → `llm.default_model`。只需更新一个地方：

**步骤 1：在 Ollama 中拉取模型**
```bash
# 拉取不同的模型（示例：较小的 7B 模型）
ollama pull deepseek-r1:7b

# 或使用完全不同的模型
ollama pull llama3.2
```

**步骤 2：更新 config.json**
```json
{
  "llm": {
    "default_model": "deepseek-r1:7b",  // 从 "deepseek-r1" 更改
    "ollama_host": "http://localhost:11434",
    "auto_pull": true,
    "timeout_seconds": 8.0
  }
}
```

**步骤 3：重启 API**
```powershell
.\scripts\restart_api_fast.ps1
```

**注意**：不同模型具有不同能力：
- **较大模型**（32B）：更好的推理能力，速度较慢，内存占用更多
- **较小模型**（7B）：速度更快，内存占用更少，质量可能较低
- **推荐**：`deepseek-r1`（平衡性能）

### 代理配置：`backend/config/agents.yaml`

各个代理的温度和提示文件配置。**模型从 `config.json` 统一**。

```yaml
market_analyst:
  name: Market Analyst
  # model: deepseek-r1  # 如果未指定，使用 config.json llm.default_model
  temperature: 0.3
  prompt_file: ../prompts/market_analyst.yml

technical_analyst:
  name: Technical Analyst
  # model: deepseek-r1  # 如果未指定，使用 config.json llm.default_model
  temperature: 0.2
  prompt_file: ../prompts/technical_analyst.yml

# ... (总共 8 个代理)
```

**模型优先级**：
1. `agents.yaml` → `model` 字段（如果指定）- **最高优先级**
2. `config.json` → `llm.default_model` - **所有代理的默认值**
3. `"llama3.1"` - 后备

**为每个代理使用不同模型（可选）**：
```yaml
market_analyst:
  model: deepseek-r1:32b  # 覆盖：市场分析使用较大模型
  temperature: 0.3

technical_analyst:
  # 未指定模型 - 使用 config.json llm.default_model
  temperature: 0.2
```

**总结**：
- ✅ **默认行为**：所有代理使用 `config.json` → `llm.default_model`
- ✅ **无需在 `agents.yaml` 中指定模型**，除非您希望特定代理使用不同模型
- ✅ **在一个地方更改模型**（`config.json`）以更新所有代理

---

## 💾 数据存储与记录

### 📦 数据备份与恢复

**⚠️ 重要提示：定期备份对长期自动交易至关重要！**

系统提供全面的备份功能来保护您的交易数据：

#### 快速备份设置

**自动每日备份（推荐）**:
```powershell
# 以管理员身份运行以设置定时每日备份
.\scripts\setup_daily_backup.ps1
```

**手动备份**:
```powershell
# 手动运行备份脚本
python backend/scripts/daily_backup.py
```

#### 备份内容

- ✅ `portfolio_state.json` - 当前持仓和现金余额
- ✅ `equity_history.jsonl` - 净值历史（每30分钟）
- ✅ `discussion_actions.jsonl` - Agent 对话和分析
- ✅ `filled_orders.jsonl` - 已成交订单（含盈亏）
- ✅ `pending_orders.jsonl` - 待处理订单
- ✅ `trades.jsonl` - 所有交易记录
- ✅ `memory/` 目录 - Agent 学习数据（每日/每周/每月快照）

#### 备份功能

- **自动清理**: 自动保留最近7天的备份
- **备份清单**: 每个备份包含 `manifest.json` 元数据文件
- **时间戳目录**: `data/backups/YYYYMMDD_HHMMSS/`
- **定时任务**: 可配置为每天指定时间运行

#### 从备份恢复

**恢复持仓**:
```powershell
# 使用恢复脚本
.\scripts\restore_portfolio.ps1

# 或手动恢复
$backupDir = "data\backups\20251120_174635"
Copy-Item "$backupDir\portfolio_state.json" "data\logs\portfolio_state.json" -Force
```

**查看可用备份**:
```powershell
Get-ChildItem -Path "data\backups" -Directory | Sort-Object Name -Descending
```

**📖 详细指南**: 查看 [`docs/BACKUP_GUIDE.md`](docs/BACKUP_GUIDE.md) 获取完整的备份和恢复说明。

---

### 📁 数据目录结构

**所有代理生成的数据、对话、持仓和交易记录都存储在 `data/logs/` 目录中**（相对于项目根目录）。

**路径详情**：
- **项目根目录**：包含 `README.md` 和 `backend/` 文件夹的目录
- **数据目录**：`{project_root}/data/logs/`
- **示例**：如果项目位于 `C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\`，则数据存储在 `C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama\data\logs\`

**快速访问**：
```powershell
# 查看投资组合状态
Get-Content data\logs\portfolio_state.json | ConvertFrom-Json | ConvertTo-Json -Depth 10

# 查看最近对话（最后 10 条）
Get-Content data\logs\discussion_actions.jsonl -Tail 10

# 查看净值历史
Get-Content data\logs\equity_history.jsonl

# 查看已成交订单
Get-Content data\logs\filled_orders.jsonl
```

**完整目录结构**：
```
data/logs/
├── portfolio_state.json          # 持仓记录（当前投资组合状态：现金、持仓、成本）
├── equity_history.jsonl          # 净值历史（净值历史，每 30 分钟记录一次，保留所有时间戳）
├── discussion_actions.jsonl      # 聊天记录（所有代理对话、分析、工具调用）
├── trades.jsonl                  # 交易记录（所有已执行交易）
├── filled_orders.jsonl            # 已成交订单（已完成订单，包含已实现 P&L）
├── pending_orders.jsonl          # 待处理订单（等待执行的待处理订单）
├── portfolio_state_backup_*.json  # 备份文件（初始化时的自动备份文件）
├── discussion_actions_backup_*.jsonl  # 备份文件（备份文件）
├── error_log.jsonl                # 错误日志（系统错误记录）
└── memory/
    ├── daily/                    # 每日快照（每日内存快照）
    │   └── YYYY-MM-DD.json
    ├── weekly/                   # 每周汇总（每周摘要）
    │   └── YYYY-W##.jsonl
    ├── monthly/                  # 每月汇总（每月摘要）
    │   └── YYYY-MM.jsonl
    └── index/                    # 内存索引（内存索引）
        └── daily_index.json
```

每次代理执行周期后，以下数据会自动保存：

```
data/logs/
├── portfolio_state.json          # 当前投资组合状态（现金、持仓）
├── equity_history.jsonl          # 净值历史（P&L 记录）
├── discussion_actions.jsonl      # 代理对话和讨论
├── trades.jsonl                  # 交易执行历史
├── filled_orders.jsonl            # 已完成订单（包含已实现 P&L）
├── pending_orders.jsonl          # 待处理订单
├── memory/
│   ├── daily/                    # 每日内存快照
│   │   └── YYYY-MM-DD.json
│   ├── weekly/                   # 每周摘要
│   ├── monthly/                  # 每月摘要
│   └── index/                    # 内存索引
└── real_time_snapshots.jsonl     # 实时投资组合快照
```

**关键点**：
- **持仓信息**：存储在 `portfolio_state.json`（当前持仓、现金余额）
- **代理对话**：存储在 `discussion_actions.jsonl`（所有代理讨论、分析和摘要）
- **交易记录**：存储在 `trades.jsonl` 和 `filled_orders.jsonl`（执行历史和 P&L）
- **内存系统**：存储在 `memory/` 子目录中（每日/每周/每月快照，用于代理学习）
- **净值历史**：存储在 `equity_history.jsonl`（投资组合价值随时间变化）

所有文件都由系统自动创建和更新。无需手动文件管理。

### 系统初始化

**API 端点**：`POST /api/system/init?force=true`

**功能**：通过删除所有交易数据文件将系统重置为初始状态。

**删除的内容**：
- `portfolio_state.json`（删除前自动备份）
- `pending_orders.jsonl`
- `filled_orders.jsonl`
- `equity_history.jsonl`
- `discussion_actions.jsonl`

**保留的内容**：
- `memory/` 目录（代理学习数据保留）
- 备份文件（`portfolio_state_backup_*.json` 等）

**用法**：
```bash
# 通过 API
curl -X POST "http://localhost:8000/api/system/init?force=true"

# 或从前端
# 点击"初始化系统"按钮（需要 force=true 确认）
```

**安全功能**：
- 需要 `force=true` 参数以防止意外删除
- 删除前自动创建 `portfolio_state.json` 的备份
- 备份文件名格式：`portfolio_state_backup_YYYYMMDD_HHMMSS.json`

**初始化代码位置**：
- **文件**：`backend/src/api/server.py`
- **函数**：`system_init()`（第 1055-1110 行）
- **数据目录**：从项目根目录自动确定 → `data/logs/`

### 投资组合状态（`portfolio_state.json`）

**位置**：`data/logs/portfolio_state.json`

**包含**：
- 当前现金余额
- 当前持仓（股票代码、数量、平均成本、总成本）
- 初始价值
- 总价值

**格式**：
```json
{
  "cash": 2197.50,
  "initial_value": 10000.0,
  "total_value": 8497.50,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "total_cost": 1502.50
    }
  }
}
```

### 净值历史（`equity_history.jsonl`）

**位置**：`data/logs/equity_history.jsonl`

**包含**：带 P&L 记录的净值（权益）历史

**记录频率**：在市场时间内每 **30 分钟**自动保存记录。

**重要功能**：
- ✅ **保留所有时间戳**：保留每 30 分钟记录（不按日期去重）
- ✅ **时间范围查询**：前端支持日/周/月/自定义日期范围选择
- ✅ **API 支持**：后端 API 支持 `period`（日/周/月）、`start_date`、`end_date`、`start_timestamp`、`end_timestamp` 参数
- ✅ **默认视图**：前端默认显示最近一周的数据

**格式**（JSONL - 每行一条记录）：
```json
{
  "date": "2025-01-28",
  "timestamp": "2025-01-28T10:00:00.000Z",
  "cash": 2197.50,
  "equity_value": 6300.00,
  "total_value": 8497.50,
  "total_pnl": -2.50,
  "total_pnl_pct": -0.03,
  "positions": {
    "NVDA": {
      "quantity": 10,
      "avg_cost": 150.25,
      "current_price": 150.25,
      "market_value": 1502.50,
      "unrealized_pnl": 0.00,
      "unrealized_pnl_pct": 0.00
    }
  }
}
```

**时间戳格式**：
- **`date`**：`YYYY-MM-DD` 格式的日期（例如，`"2025-01-28"`）
- **`timestamp`**：ISO 8601 格式，UTC 时区（例如，`"2025-01-28T10:00:00.000Z"`）
  - 格式：`YYYY-MM-DDTHH:MM:SS.sssZ`
  - 始终包含 `Z` 后缀，表示 UTC 时区
  - 记录净值快照时自动生成
  - 用于按时间顺序排序和基于时间的查询

**字段**：
- `total_pnl`：总盈亏（美元）（total_value - initial_value）
- `total_pnl_pct`：总盈亏百分比
- `equity_value`：所有持仓的当前市场价值
- `total_value`：现金 + equity_value

### 交易历史（`trades.jsonl`）

**位置**：`data/logs/trades.jsonl`

**包含**：所有已执行交易

**格式**：
```json
{
  "timestamp": "2025-01-28T10:30:00Z",
  "symbol": "NVDA",
  "action": "BUY",
  "quantity": 10,
  "price": 150.25,
  "total_cost": 1502.50,
  "status": "FILLED"
}
```

### 已成交订单（`filled_orders.jsonl`）

**位置**：`data/logs/filled_orders.jsonl`

**包含**：已完成订单，包含已实现 P&L（用于 SELL 订单）

**格式**：
```json
{
  "order_id": "order_123",
  "placed_at": "2025-01-28T10:30:00",  # 注意：order_date 字段已移除，使用 placed_at 代替
  "symbol": "NVDA",
  "action": "SELL",
  "quantity": 10,
  "fill_price": 155.00,
  "status": "FILLED",
  "realized_pnl": 47.50,
  "realized_pnl_pct": 3.16,
  "cost_basis": 1502.50,
  "proceeds": 1550.00
}
```

**P&L 字段**（用于 SELL 订单）：
- `realized_pnl`：已实现盈亏（美元）
- `realized_pnl_pct`：已实现盈亏百分比
- `cost_basis`：原始购买成本
- `proceeds`：销售收入

### 内存系统（`memory/`）

**位置**：`data/logs/memory/`

**目的**：用于从过去交易中学习的历史内存

**每日内存**（`memory/daily/YYYY-MM-DD.json`）：
- 市场视图快照
- 代理讨论
- 风险报告
- 交易决策
- 投资组合快照
- 已执行交易

**每周/每月摘要**：
- 聚合洞察
- 表现摘要
- 关键学习

**用法**：代理可以访问最近的内存（最近 5-7 天）以为当前决策提供信息。

#### RAG（检索增强生成）机制

系统实现了先进的 RAG 机制，使代理能够通过智能内存检索和语义搜索从历史交易决策中学习。

**核心架构**：

1. **分层内存存储**：
   - **短期（0-7 天）**：完整存储，包含完整转录、工具上下文和对话历史
     - 位置：`memory/daily/YYYY-MM-DD.json`
     - 目的：详细决策参考
     - 特点：保留所有细节，便于深入分析
   - **中期（8-30 天）**：摘要存储，包含关键决策点和重要对话片段
     - 位置：`memory/weekly/YYYY-WNN.jsonl`
     - 目的：模式识别和趋势分析
     - 特点：提取关键信息，减少存储空间
   - **长期（30+ 天）**：压缩摘要，包含核心洞察和经验教训
     - 位置：`memory/monthly/YYYY-MM.jsonl`
     - 目的：长期策略和历史模式
     - 特点：高度压缩，仅保留核心信息

2. **向量化与语义搜索**：
   - **嵌入生成**：
     - **主要**：Ollama API（使用 `nomic-embed-text` 模型）
     - **后备**：sentence-transformers（使用 `all-MiniLM-L6-v2`，384 维向量）
     - 如果 Ollama 不可用，自动回退
   - **向量存储**：
     - 基于 numpy 的向量存储（轻量级，无需 FAISS）
     - 位置：`memory/vectors/`
     - 索引文件：`vectors.npy` 和 `metadata.json`
     - 支持余弦相似度搜索
   - **混合检索**：
     - **关键词搜索**：按股票代码、日期、立场快速过滤
     - **语义搜索**：使用嵌入向量进行相似性匹配
     - **融合排序**：结合两种结果以获得最佳匹配

3. **内存质量评分**：
   - **评分维度**（0-1 分数）：
     - **交易影响**（30% 权重）：基于 P&L 和交易量
     - **决策质量**（20% 权重）：基于后续表现和决策复杂度
     - **信息密度**（20% 权重）：基于关键信息量和字段丰富度
     - **时间衰减**（30% 权重）：指数衰减（`score = 0.95 ^ days_ago`），越新的内存越重要
   - **智能压缩**：
     - 高分内存（score >= 0.7）：保留完整细节
     - 中等分数内存（score >= 0.4）：摘要存储
     - 低分内存（score < 0.4）：仅压缩存储

4. **内存关联**：
   - **自动发现**：系统自动发现相关内存：
     - 相同股票：涉及相同股票代码的内存
     - 相似市场条件：相同市场立场（看涨/中性/看跌）
     - 相似决策模式：相同交易动作（买入/卖出/持有）
   - **关联存储**：存储在 `memory/index/memory_relations.json` 中
   - **检索增强**：搜索时可以选择包含相关内存

5. **缓存机制**：
   - **热点内存缓存**：最近 7 天的内存常驻内存以快速访问
   - **查询结果缓存**：缓存常用查询结果
   - **向量缓存**：缓存常用内存的嵌入

6. **性能优化**：
   - **索引优化**：
     - 日期索引：快速日期范围查找
     - 股票索引：按股票代码建立倒排索引
     - 向量索引：numpy 数组加速相似度搜索
   - **预期性能**：
     - 关键词搜索：< 10ms（1000 条内存）
     - 语义搜索：< 50ms（1000 条内存，384 维向量）
     - 混合检索：< 60ms（关键词 + 语义融合）

**代理如何使用 RAG**：

1. **自动内存加载**：在每个交易周期开始时，自动加载最近的内存（最近 5 天）
2. **强制内存检索**：市场分析师总是在开始时调用 `get_recent_memories`（系统强制执行）
3. **主动内存搜索**：代理可以主动搜索内存，使用：
   - `get_recent_memories`：获取最近的交易上下文
   - `search_memories_by_symbol`：查找特定股票的历史决策
   - `search_memories_by_semantic`：自然语言查询（例如，"高波动性的看跌市场"）
   - `search_similar_decisions`：查找类似的交易情况
4. **从历史中学习**：代理使用检索到的内存来：
   - 避免重复过去的错误
   - 从成功的策略中学习
   - 保持与已验证方法的一致性
   - 理解市场模式随时间的变化

**配置**：

RAG 设置可以在 `backend/config/config.json` 中配置：

```json
{
  "rag": {
    "short_term_days": 7,
    "medium_term_days": 30,
    "long_term_days": 90,
    "embedding_model": "nomic-embed-text",
    "embedding_dimension": 384,
    "use_ollama_embedding": true,
    "fallback_embedding_model": "all-MiniLM-L6-v2",
    "vector_search_top_k": 10,
    "enable_semantic_search": true,
    "enable_cache": true,
    "cache_size": 100
  }
}
```

**优势**：
- ✅ **提高决策质量**：代理从过去的成功和失败中学习
- ✅ **模式识别**：识别反复出现的市场条件和有效策略
- ✅ **一致性**：在类似情况下保持交易一致性
- ✅ **效率**：智能缓存和索引实现快速检索
- ✅ **可扩展性**：分层存储和压缩支持长期运行

有关详细的 RAG 实现文档，请参阅 [`docs/RAG_OPTIMIZATION.md`](docs/RAG_OPTIMIZATION.md)。

### 代理对话（`discussion_actions.jsonl`）

**位置**：`data/logs/discussion_actions.jsonl`

**包含**：所有代理对话、工具调用和分析

**格式**：
```json
{
  "timestamp": "2025-01-28T10:00:00Z",
  "date": "2025-01-28",
  "agent": "MarketAnalyst",
  "round": 0,
  "content": "市场分析...",
  "type": "discussion",
  "summary": "市场显示混合情绪...",
  "stance": "NEUTRAL",
  "tools_used": ["get_market_indices", "get_sector_rotation"]
}
```

**关键字段**：
- `agent`：代理名称（MarketAnalyst, TechnicalAnalyst, FundamentalAnalyst, SentimentAnalyst, DiscussionCoordinator, RiskAnalyst, TraderAgent）
- `round`：讨论轮数（1, 2, 3，或 0 表示非讨论条目）
- `summary`：代理的分析摘要（如果不存在则从内容中提取）
- `stance`：市场立场（BULLISH, BEARISH, NEUTRAL）
- `tools_used`：代理调用的工具列表
- `type`：条目类型（discussion, tool_call, decision 等）

**前端显示**：
- 所有 7 个代理都在前端显示，TraderAgent 和 RiskAnalyst 有特殊样式
- 内容提取：前端智能地从 `summary` 字段提取内容，如果没有则回退到 `content` 字段或 RiskAnalyst 的 `risk_report`
- Discussion Coordinator：自动从协调员的摘要中提取各个分析师报告并分别显示
- **最近讨论**：前端仅显示最新的 3 条讨论条目（每个代理一条，按时间戳排序）以避免混乱，同时仍显示所有工具条目

---

### 快速数据访问命令

**查看投资组合状态**（Windows PowerShell）：
```powershell
Get-Content data\logs\portfolio_state.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

**查看最近对话**（最后 10 条）：
```powershell
Get-Content data\logs\discussion_actions.jsonl -Tail 10
```

**查看净值历史**：
```powershell
Get-Content data\logs\equity_history.jsonl
```

**查看已成交订单**：
```powershell
Get-Content data\logs\filled_orders.jsonl
```

**查看每日内存快照**：
```powershell
Get-Content data\logs\memory\daily\2025-11-16.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
```

---

## 🤖 多代理架构

### 模块化架构

系统使用**模块化架构**以提高可维护性和代码组织：

**核心结构**：
- **`backend/src/agents/multi_analyst_system.py`**：多轮讨论的主协调器
- **`backend/src/agents/analysts/`**：模块化分析师处理器
  - `market_analyst_handler.py`：市场分析师逻辑
  - `technical_analyst_handler.py`：技术分析师逻辑
  - `fundamental_analyst_handler.py`：基本面分析师逻辑
  - `sentiment_analyst_handler.py`：情绪分析师逻辑
  - `common.py`：共享工具和辅助函数
- **`backend/src/agents/factory.py`**：用于创建代理实例的代理工厂
- **`prompts/`**：所有代理的 YAML 提示文件（系统提示和用户模板）

**优势**：
- ✅ **关注点分离**：每个分析师都有自己的处理器模块
- ✅ **代码可重用性**：通过 `common.py` 共享通用工具
- ✅ **易于维护**：对一个分析师的更改不会影响其他分析师
- ✅ **提示管理**：所有提示存储在 YAML 文件中，便于编辑
- ✅ **可测试性**：每个模块可以独立测试

### 代理规格

#### 1. **市场分析师** 🌐
- **专业**：宏观趋势、板块轮动、市场结构
- **优先工具**：`get_market_indices`, `get_sector_rotation`, `get_market_breadth`, `get_economic_summary`
- **处理器模块**：`backend/src/agents/analysts/market_analyst_handler.py`
- **提示文件**：`prompts/market_analyst.yml`

#### 2. **技术分析师** 📈
- **专业**：图表模式、指标、支撑/阻力
- **优先工具**：`get_advanced_indicators`, `get_support_resistance`, `vix_term`
- **处理器模块**：`backend/src/agents/analysts/technical_analyst_handler.py`
- **提示文件**：`prompts/technical_analyst.yml`
- **分析目标**：
  - **有持仓**：当前持仓 + 推荐股票 + 主要指数（SPY, QQQ, DIA, IWM, VTI）
  - **无持仓**：推荐股票 + 主要指数（SPY, QQQ, DIA, IWM, VTI）
  - **所有目标必须同时分析**
- **工具限制**：
  - **不使用新闻工具**（新闻分析由情绪分析师处理）
  - 如果请求，系统会自动过滤新闻工具
  - 仅关注技术指标和价格行为

#### 3. **基本面分析师** 💼
- **专业**：财务报表、估值、收益
- **优先工具**：`get_company_fundamentals`, `get_earnings_history`, `get_financial_statements`
- **处理器模块**：`backend/src/agents/analysts/fundamental_analyst_handler.py`
- **提示文件**：`prompts/fundamental_analyst.yml`
- **分析目标**：
  - **有持仓**：非 ETF 持仓 + 非 ETF 推荐股票（排除 ETF）
  - **无持仓**：仅非 ETF 推荐股票
  - **ETF 和指数被排除**（ETF 不需要基本面分析）
- **预算优先级**：所有基本面分析工具不受工具预算限制执行（确保分析所有推荐股票和持仓）
- **预算分配**：工具预算仅在市场、技术和情绪分析师之间分配（基本面分析师被排除在预算分配之外，因为其工具不受预算限制）
- **自定义预算分配**：您可以在 `config.json` 中的 `budget_allocation` 下配置每个分析师的预算分配（基本面将自动排除）

#### 4. **情绪分析师** 😊
- **专业**：市场心理学、新闻情绪、恐惧/贪婪
- **优先工具**：`fear_greed`, `vix_term`, `plan_and_scan_news`（强制）
- **处理器模块**：`backend/src/agents/analysts/sentiment_analyst_handler.py`
- **提示文件**：`prompts/sentiment_analyst.yml`
- **新闻分析**：
  - 在每个分析周期开始时自动调用 `plan_and_scan_news`
  - 系统自动过滤已弃用的 `news_scan` 工具（转换为 `plan_and_scan_news`）
  - 如果 LLM 请求 `news_scan`，它会自动转换为 `plan_and_scan_news`
  - 新闻分析对于情绪评估是强制性的

#### 5. **风险分析师** 🛡️
- **专业**：风险评估、持仓管理
- **优先工具**：`vix_term`, `get_correlation_matrix`, `get_market_breadth`
- **处理器模块**：`backend/src/agents/risk_analyst_llm.py`
- **提示文件**：`prompts/risk_analyst.yml`

#### 6. **交易代理** 💰
- **专业**：交易决策、持仓规模
- **类型**：基于 LLM 的代理（使用 deepseek-r1）
- **处理器模块**：`backend/src/agents/trader_agent.py`
- **提示文件**：`prompts/trader_agent.yml`
- **输入**：
  - 所有分析师推荐（共识立场、推荐股票）
  - 风险报告（风险级别、VIX 分数、持仓推荐）
  - 投资组合状态（当前持仓、可用现金、P&L）
  - 市场数据（当前价格、市场状态）
- **输出**：
  - 带数量和价格的买入/卖出订单
  - 理由（LLM 生成的解释）
  - 风险合规检查
- **决策过程**：
  - LLM 同时分析所有输入
  - 考虑硬性规则（持仓限制、现金约束）
  - 整合风险分析师推荐
  - 生成自然语言理由

#### 7. **讨论协调员** 🤝
- **专业**：将所有分析师观点综合为共识
- **处理器模块**：`backend/src/agents/multi_analyst_system.py`（内部函数 `_run_discussion_coordinator`）
- **提示文件**：`prompts/discussion_agent.yml`
- **功能**：
  - 审查所有分析师报告和讨论历史
  - 识别共识和分歧
  - 生成带最终立场的统一摘要
  - 根据分析师共识提供推荐股票

### 提示管理

所有代理提示都存储在 `prompts/` 目录（项目根级别）中的 **YAML 文件**中。

**提示文件结构**：
```yaml
system: |
  Role: You are a [Agent Type]...
  Area of expertise: ...
  Available Tools: ...
  
user: |
  Context:
  - Market Data: {market_view}
  - Previous Discussion: {previous_discussion}
  - Current Positions: {current_positions}
  - Tools Context: {tools_context}
  ...
```

**YAML 提示的优势**：
- ✅ **易于编辑**：修改提示而无需接触代码
- ✅ **版本控制**：在 Git 中跟踪提示更改
- ✅ **一致性**：所有代理使用相同的提示加载机制
- ✅ **模板变量**：使用 `{variable_name}` 进行动态内容
- ✅ **关注点分离**：提示与业务逻辑分离

**可用提示文件**：
- `prompts/market_analyst.yml`：市场分析师系统和用户提示
- `prompts/technical_analyst.yml`：技术分析师提示
- `prompts/fundamental_analyst.yml`：基本面分析师提示
- `prompts/sentiment_analyst.yml`：情绪分析师提示
- `prompts/risk_analyst.yml`：风险分析师提示
- `prompts/trader_agent.yml`：交易代理提示
- `prompts/discussion_agent.yml`：讨论协调员提示
- `prompts/market_agent.yml`：市场数据和报价代理提示

---

## 🛠️ 工具套件（28 个工具）

系统包括 **28 个高级工具**，分为两类：
- **21 个市场分析工具**：实时数据、技术指标、基本面数据、新闻和经济指标
- **7 个内存/RAG 工具**：具有语义搜索的历史内存检索，用于从过去的交易决策中学习

**工具使用规则**：
- **工具预算**：在市场、技术和情绪分析师之间共享（默认：每周期 15 次调用）
- **基本面分析师**：工具不受预算限制（可以不受预算约束分析所有推荐股票和持仓）
- **预算分配**：可通过 `config.json` 中的 `budget_allocation` 字段配置（基本面自动排除）
- **工具过滤**：系统自动过滤无效工具调用并强制执行限制
- **工具验证**：所有工具调用在执行前都经过验证（必须具有有效的 `name` 字段）
- **新闻工具**：`news_scan` 已被移除。请改用 `plan_and_scan_news`（包含 LLM 生成的摘要和关键词）
- **自动转换**：如果 LLM 请求已弃用的 `news_scan`，它会自动转换为 `plan_and_scan_news`

### 🧠 内存/RAG 工具（7 个工具）

这些工具允许代理检索并学习历史交易内存：

1. **`get_recent_memories`**
   - **目的**：获取最近的交易内存（最近 N 天）以提供上下文
   - **用法**：在每个交易周期开始时自动调用
   - **参数**：`days`（默认：5），`summary_only`（默认：true）
   - **返回**：最近的交易决策、立场和结果列表

2. **`search_memories_by_symbol`**
   - **目的**：搜索特定股票的历史内存
   - **用法**：分析特定股票时调用
   - **参数**：`symbol`（必需），`days`（默认：30）
   - **返回**：股票的历史分析和决策

3. **`search_memories_by_date_range`**
   - **目的**：在日期范围内搜索内存
   - **用法**：审查特定期间发生的情况
   - **参数**：`start_date`，`end_date`（YYYY-MM-DD 格式）
   - **返回**：指定日期范围内的内存

4. **`get_weekly_memory_summary`**
   - **目的**：获取每周压缩内存摘要
   - **用法**：长期上下文（仅保留周一和周末记录）
   - **参数**：`week_str`（可选，格式："2025-W01"）
   - **返回**：包含周一和周末记录的每周摘要

5. **`get_monthly_memory_summary`**
   - **目的**：获取每月压缩内存摘要
   - **用法**：非常长期的趋势和模式
   - **参数**：`month_str`（可选，格式："2025-01"）
   - **返回**：每月聚合摘要

6. **`search_similar_decisions`**
   - **目的**：搜索股票的类似交易决策
   - **用法**：从过去的 BUY/SELL 操作中学习
   - **参数**：`symbol`（必需），`action_type`（可选："BUY", "SELL", "HOLD"）
   - **返回**：带结果的类似历史决策
   - **功能**：支持语义搜索以找到类似情况

7. **`search_memories_by_semantic`**（新增）
   - **目的**：使用自然语言查询进行内存语义搜索
   - **用法**：查找与特定概念、市场条件或交易模式相关的内存
   - **参数**：`query`（必需，自然语言），`top_k`（默认：10）
   - **返回**：按语义相似性排序的内存
   - **示例**：
     - "bearish market with high volatility"
     - "successful NVDA trades"
     - "decisions during market crash"

**内存系统功能**：
- ✅ **自动内存加载**：最近的内存（最近 5 天）在每个交易周期开始时自动加载
- ✅ **强制内存检索**：市场分析师总是在开始时调用 `get_recent_memories`（由系统强制执行）
- ✅ **短期/长期内存分离**：
  - 短期（0-7 天）：完整存储，包含完整转录
  - 中期（8-30 天）：摘要存储，包含关键对话点
  - 长期（30+ 天）：压缩存储，包含核心洞察
- ✅ **语义搜索**：使用嵌入（Ollama 或 sentence-transformers）进行基于向量的相似性搜索
- ✅ **混合检索**：结合关键词搜索（快速过滤）和语义搜索（相似性匹配）
- ✅ **内存质量评分**：基于 P&L、成交量、信息密度和时间衰减的重要性评分
- ✅ **内存关系**：自动发现相关内存（相同股票、类似条件、类似决策）
- ✅ **缓存**：最近 7 天的热内存缓存、查询结果缓存和向量缓存
- ✅ **每周压缩**：旧内存（>30 天）压缩为每周摘要（仅周一和周末）
- ✅ **RAG 集成**：代理使用内存以避免重复错误并从成功中学习

### 📊 市场分析工具（21 个工具）

### 情绪与风险（3 个工具）
- `vix_term`：VIX 期限结构
- `vix_close`：历史 VIX 价格
- `fear_greed`：CNN 恐惧与贪婪指数

### 新闻与信息（3 个工具）
- `plan_and_scan_news`：LLM 驱动的新闻查询（推荐，包含带摘要和关键词的文章内容）
  - **用法**：情绪分析的主要新闻工具
  - **功能**：返回带 LLM 生成摘要和关键词的文章
  - **参数**：`tickers`（股票代码列表），`max_articles`（默认：10），`recency_days`（默认：2），`fetch_body_top`（包含完整内容的文章数量）
  - **强制用于**：情绪分析师（如果未请求则自动添加）
  - **从以下过滤**：技术分析师（新闻分析由情绪分析师处理）
- `web_search`：DuckDuckGo 搜索
- `fetch_url`：从 URL 提取内容
- **新闻显示**：前端显示带摘要、来源、时间戳和关键词的新闻（按时间排序）
- **注意**：`news_scan` 已被移除。请改用 `plan_and_scan_news`。如果 LLM 请求 `news_scan`，它会自动转换为 `plan_and_scan_scan_news`。

### 经济数据（3 个工具）
- `get_economic_summary`：关键美国经济指标
- `get_labor_market_data`：劳动力市场数据
- `fetch_fred_indicator`：特定 FRED 指标

### 技术指标（2 个工具）
- `get_advanced_indicators`：RSI, MACD, BB, ADX, Stochastic, ATR, OBV
- `get_support_resistance`：支撑/阻力位

### 基本面数据（3 个工具）
- `get_company_fundamentals`：P/E, ROE, 利润率, 增长
- `get_earnings_history`：季度/年度收益
- `get_financial_statements`：资产负债表, 现金流

### 市场指标（4 个工具）
- `get_market_breadth`：上涨/下跌股票
- `get_sector_rotation`：11 个板块表现
- `get_correlation_matrix`：股票相关性
- `get_market_indices`：S&P 500, Dow, NASDAQ, Russell 2000

### 加密货币（2 个工具）
- `fetch_crypto_batch`：批量加密货币数据
- `get_crypto_price`：单个加密货币价格

---

## 📈 交易工作流程

### 交易频率与计划

**交易周期频率**：
- **市场时间（美东时间上午 9:30 - 下午 4:00）**：自动交易每 **30 分钟**运行一次
- **市场关闭**：分析持续运行（每 30 分钟），但**不生成订单**
- **仅交易日**：系统遵守市场假期和周末

**计划示例**：
```
市场开放日（例如，周一）：
├── 上午 9:30 ET  → 第一个交易周期（如果市场准时开放）
├── 上午 10:00 ET → 交易周期
├── 上午 10:30 ET → 交易周期
├── 上午 11:00 ET → 交易周期
├── ...（每 30 分钟）
├── 下午 3:30 ET  → 交易周期
└── 下午 4:00 ET  → 最后一个交易周期（市场关闭）

市场关闭（例如，下午 4:00 之后或周末）：
├── 分析每 30 分钟运行一次
├── 不生成交易订单
└── 结果保存以供下一个交易时段使用
```

**代理对话频率**：
- **市场时间内**：每 30 分钟完整的代理讨论（4 个分析师 + 协调员 + 风险 + 交易员）
- **市场关闭**：代理仍会分析，但交易员不生成订单
- **讨论轮数**：每周期 3 轮讨论（所有分析师参与每轮）
- **性能优化**：
  - ✅ **工具结果缓存**：强制工具（get_recent_memories, get_economic_summary）仅在第 1 轮调用，缓存结果在第 2-3 轮重用
  - ✅ **新闻工具缓存**：plan_and_scan_news 仅在第 1 轮调用，缓存结果在后续轮次重用
  - ✅ **并行工具执行**：使用 ThreadPoolExecutor 并行执行独立工具（仅第 1 轮）
  - ✅ **减少工具调用**：后续轮次使用更少工具（最多 3 个 vs 第 1 轮的 5 个），因为它们更多地依赖前一轮结果
  - ✅ **预期性能**：第 2-3 轮时间减少 50-70%，第 1 轮时间减少 30-50%（使用并行执行）

### 完整交易周期流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    交易周期（30 分钟间隔）                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  1. 市场数据收集                    │
        │     • 获取 118+ NASDAQ-100 股票     │
        │     • 计算技术指标                  │
        │     • 获取经济数据和情绪            │
        │     时间：5-10 秒                    │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  2. 多代理分析                      │
        │     ┌──────────────────────────┐   │
        │     │ 市场分析师                │   │
        │     │ • 宏观趋势                │   │
        │     │ • 板块轮动                │   │
        │     │ • 市场广度                │   │
        │     │ • 经济指标                │   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ 技术分析师                │   │
        │     │ • 价格模式                │   │
        │     │ • 支撑/阻力               │   │
        │     │ • 技术指标                │   │
        │     │ • 不使用新闻工具（已过滤）│   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ 基本面分析师              │   │
        │     │ • 财务报表                │   │
        │     │ • 估值指标                │   │
        │     │ • 收益历史                │   │
        │     │ • 工具：get_company_      │   │
        │     │   fundamentals（无限制）  │   │
        │     │ • 分析所有非 ETF 股票    │   │
        │     │   （无预算限制）          │   │
        │     └──────────────────────────┘   │
        │     ┌──────────────────────────┐   │
        │     │ 情绪分析师                │   │
        │     │ • 新闻情绪                │   │
        │     │ • 恐惧与贪婪指数          │   │
        │     │ • VIX 期限结构            │   │
        │     │ • 工具：plan_and_scan_news│   │
        │     │   （强制，自动添加）      │   │
        │     └──────────────────────────┘   │
        │     • 工具过滤和验证                │
        │     • 无效调用被过滤                │
        │     时间：30-60 秒                  │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  3. 讨论协调员                      │
        │     • 综合所有 4 个分析师           │
        │     • 审查工具结果                  │
        │     • 识别共识/分歧                 │
        │     • 最终共识（立场）              │
        │     • 工具使用跟踪                  │
        │     • 工具过滤和验证                │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  4. 风险评估                        │
        │     • 持仓集中度                    │
        │     • 市场风险评估                  │
        │     • 持仓规模推荐                  │
        │     • VIX 风险评分                  │
        │     时间：10-20 秒                  │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  5. 交易代理决策                    │
        │     ┌──────────────────────────┐    │
        │     │ 输入：                    │    │
        │     │ • 分析师共识              │    │
        │     │ • 风险报告                │    │
        │     │ • 当前持仓                │    │
        │     │ • 市场数据                │    │
        │     └──────────────────────────┘    │
        │     ┌──────────────────────────┐    │
        │     │ LLM 处理：                │    │
        │     │ • 分析所有输入            │    │
        │     │ • 考虑风险限制            │    │
        │     │ • 生成买入/卖出           │    │
        │     └──────────────────────────┘    │
        │     ┌──────────────────────────┐    │
        │     │ 输出：                    │    │
        │     │ • buy_orders[]           │    │
        │     │ • sell_orders[]          │    │
        │     │ • rationale               │    │
        │     └──────────────────────────┘    │
        │     时间：5-10 秒                    │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  6. 硬性规则验证                    │
        │     ✓ 市场状态检查                  │
        │     ✓ 现金可用性                    │
        │     ✓ 持仓限制                      │
        │     ✓ 持仓数量限制                  │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  7. 订单执行                        │
        │     • 市场开放：执行订单            │
        │     • 市场关闭：仅分析              │
        │     • 所有订单都是市价订单          │
        │     • 保证立即成交                  │
        └─────────────────────────────────────┘
                              │
                              ▼
        ┌─────────────────────────────────────┐
        │  8. 投资组合更新                    │
        │     • 更新投资组合状态              │
        │     • 记录净值历史                  │
        │     • 保存内存快照                  │
        │     • 记录对话和交易                │
        └─────────────────────────────────────┘
```

### 交易代理：基于 LLM 的决策

**交易代理是 LLM 吗？**
- **是**：交易代理使用 LLM（deepseek-r1）做出交易决策
- **输入**：结构化数据（分析师报告、风险评估、持仓、市场数据）
- **输出**：带理由的交易订单（买入/卖出）

**决策过程**：

```
┌─────────────────────────────────────────────────────────────┐
│              交易代理决策流程                                │
└─────────────────────────────────────────────────────────────┘

输入层：
├── 分析师共识
│   ├── 最终立场（BULLISH/BEARISH/NEUTRAL）
│   ├── 推荐股票
│   └── 来自 4 个分析师的关键洞察
│
├── 风险报告
│   ├── 总体风险级别（LOW/MEDIUM/HIGH）
│   ├── VIX 风险分数（0-10）
│   ├── 持仓控制推荐
│   └── 持仓限制检查
│
├── 当前投资组合
│   ├── 当前持仓（股票代码、数量、P&L）
│   ├── 可用现金
│   └── 投资组合价值
│
└── 市场数据
    ├── 当前价格
    ├── 市场状态（开放/关闭）
    └── 市场指标

                    ▼
        ┌───────────────────────┐
        │   LLM 处理              │
        │   (deepseek-r1)         │
        │                        │
        │  • 分析所有输入         │
        │  • 权衡风险因素         │
        │  • 考虑持仓限制         │
        │  • 生成理由             │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │   硬性规则检查          │
        │                        │
        │  ✓ 市场开放？           │
        │  ✓ 现金可用？           │
        │  ✓ 持仓限制？           │
        │  ✓ 持仓数量？           │
        └───────────────────────┘
                    ▼
        ┌───────────────────────┐
        │   输出生成              │
        │                        │
        │  • buy_orders[]        │
        │  • sell_orders[]       │
        │  • rationale           │
        │  • risk_compliance    │
        └───────────────────────┘
```

**交易代理如何决定买入/卖出**：

1. **立场分析**：
   - BULLISH → 为推荐股票生成 BUY 订单
   - BEARISH → 为现有持仓生成 SELL 订单或避免新买入
   - NEUTRAL → 保守方法，可能持有或进行小幅调整

2. **风险整合**：
   - 风险分析师推荐 → 直接影响持仓规模
   - 市场条件和风险评估 → 在决策中考虑

3. **持仓管理**：
   - 现有持仓负 P&L + 看跌共识 → 考虑卖出
   - 现有持仓达到限制（15%）+ 新机会 → 可能减少以为新机会腾出空间
   - 无持仓 + 看涨共识 → 生成新的 BUY 订单

4. **LLM 推理**：
   - 交易代理使用 LLM 综合所有信息
   - LLM 同时考虑多个因素
   - LLM 生成自然语言理由解释决策
   - LLM 可以做出细微决策（例如，部分卖出、逐步入场）

---

### 硬性规则与约束

**1. 市场状态（硬性规则）**
```
IF 市场关闭:
    不生成订单
    仅分析
ELSE:
    可以执行订单
```

**2. 持仓限制（硬性规则）**
- **每只股票限制**：每只股票最多占投资组合的 15%
- **总持仓限制**：最多 80% 的投资组合在持仓中（20% 现金储备）
- **最小持仓**：每只股票最小 3%（用于多样化）
- **持仓数量**：最多 10 只不同股票

**3. 现金约束（硬性规则）**
```
IF 订单成本 > 可用现金:
    减少数量或跳过订单
ELSE:
    执行订单
```

**4. 订单执行规则**
- 所有订单都是**市价订单**（立即执行）
- 无限价订单（保证以当前价格成交）
- 订单在市场开放时立即执行
- 无待处理订单（全部成交或拒绝）

---

## 📡 API 端点

**快速访问**：所有 API 端点可通过 Swagger UI 在 `http://localhost:8000/docs` 访问

### 投资组合与交易
- `GET /api/portfolio/state`：当前投资组合状态
- `GET /api/portfolio/real-time`：带实时价格的实时投资组合
- `GET /api/portfolio/equity-history`：历史净值曲线（带时间戳）
  - **查询参数**：
    - `limit`（默认：60）：返回的最大记录数
    - `period`（可选）：`"day"`, `"week"`, 或 `"month"` - 返回最近 N 天的记录
    - `start_date`（可选）：`YYYY-MM-DD` 格式的开始日期
    - `end_date`（可选）：`YYYY-MM-DD` 格式的结束日期
    - `start_timestamp`（可选）：ISO 8601 格式的开始时间戳
    - `end_timestamp`（可选）：ISO 8601 格式的结束时间戳
  - **示例**：`GET /api/portfolio/equity-history?period=week&limit=100`
- `POST /api/portfolio/record-equity`：记录净值快照（前端每 30 分钟调用一次）
- `POST /api/trading/execute-trade`：执行完整交易周期
- `POST /api/system/init?force=true`：将投资组合重置为初始状态（删除所有交易数据，保留内存）

### 系统信息
- `GET /api/system/info`：系统信息，包括：
  - LLM 模型配置
  - 持仓限制状态（自动/配置模式）
  - **优化组件状态**（默认启用）
  - 代理自由度设置

### 市场数据
- `GET /api/market/status`：检查市场是否开放
- `GET /api/market/universe`：获取 NASDAQ-100 股票池
- `GET /api/market/price/{symbol}`：股票代码的当前价格

### 订单
- `GET /api/orders/pending`：获取待处理订单
- `POST /api/orders/check-fills`：检查并执行待处理订单
- `GET /api/orders/history`：订单历史

### 对话与日志
- `GET /api/agents/conversations`：获取代理讨论
- `GET /api/trades/history`：交易日志
- `GET /api/trades/realized-pnl`：历史已实现 P&L 记录（按日期、start_date、end_date、limit 查询）

### 性能分析
- `GET /api/performance/statistics`：获取总体性能统计
  - **查询参数**：
    - `start_date`（可选）：`YYYY-MM-DD` 格式的开始日期
    - `end_date`（可选）：`YYYY-MM-DD` 格式的结束日期
  - **返回**：总回报、年化回报、胜率、最大回撤、夏普比率等
  - **示例**：`GET /api/performance/statistics?start_date=2025-01-01&end_date=2025-01-31`
- `GET /api/performance/trades-by-date`：按日期获取交易
  - **查询参数**：
    - `start_date`（可选）：`YYYY-MM-DD` 格式的开始日期
    - `end_date`（可选）：`YYYY-MM-DD` 格式的结束日期
    - `limit`（可选）：限制返回的日期数
  - **返回**：每日交易摘要，包含买入/卖出订单和已实现 P&L
- `GET /api/performance/symbol-analysis`：按股票代码获取性能分析
  - **查询参数**：
    - `symbol`（可选）：股票代码（如果未指定则返回所有股票代码）
    - `start_date`（可选）：`YYYY-MM-DD` 格式的开始日期
    - `end_date`（可选）：`YYYY-MM-DD` 格式的结束日期
  - **返回**：每个股票代码的统计信息，包括总 P&L、胜率、平均持仓期

---

## 🚀 部署

### Railway 后端部署

Railway 提供了一种简单可靠的方式将 AI-Trader 后端 API 部署到云端。

#### 快速部署步骤

1. **将仓库连接到 Railway**
   - 访问 [Railway Dashboard](https://railway.app/)
   - 点击"New Project" → "Deploy from GitHub repo"
   - 选择 `WenyuChiou/ai-trader-ollama` 仓库
   - Railway 将自动检测 Python 项目并部署

2. **配置文件**
   - ✅ `railway.json` - Railway 部署配置
   - ✅ `Procfile` - 进程启动命令
   - ✅ `backend/requirements.txt` - Python 依赖

3. **环境变量**（可选但推荐）
   - `FRED_API_KEY` - 用于经济数据（从 [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) 获取免费 API 密钥）
   - `OLLAMA_BASE_URL` - 如果使用远程 Ollama 实例（默认：`http://localhost:11434`）
   - `PORT` - Railway 自动分配（无需手动设置）

4. **部署过程**
   - Railway 在推送到 `main` 分支时自动构建和部署
   - 在 Railway 仪表板中检查部署日志
   - 部署通常需要 2-5 分钟

5. **获取公共 URL**
   - 部署后，Railway 提供公共 URL（例如，`https://your-app.up.railway.app`）
   - 转到 Project → Settings → Networking → Generate Domain
   - 复制生成的 URL

6. **更新前端配置**
   - 编辑 `frontend/config.js`
   - 将 `production` URL 更新为您的 Railway 后端 URL：
     ```javascript
     production: 'https://your-app.up.railway.app',
     ```
   - 提交并推送到 GitHub

#### Railway 配置

**`railway.json`**：
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "cd backend && pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "cd backend && uvicorn src.api.server:app --host 0.0.0.0 --port $PORT",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**`Procfile`**：
```
web: cd backend && uvicorn src.api.server:app --host 0.0.0.0 --port $PORT
```

**注意**：`railway.json` 和 `Procfile` 都使用 `cd backend` 以确保命令从正确目录运行。

#### 验证

部署后，验证后端是否正常工作：

1. **API 文档**：`https://your-app.up.railway.app/docs`
   - 应显示 FastAPI Swagger UI

2. **健康检查**：`https://your-app.up.railway.app/api/health`
   - 应返回：`{"status": "ok"}`

3. **前端连接**：
   - 打开 GitHub Pages：`https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`
   - 检查浏览器控制台（F12）的 API 连接状态
   - 应看到成功的 API 请求

#### Railway 免费层

- **免费层**：$5/月信用（通常足以满足小型应用）
- **自动扩展**：Railway 根据流量自动扩展
- **自动重启**：Railway 在失败时重启服务（在 `railway.json` 中配置）
- **日志**：在 Railway 仪表板中查看部署和运行时日志

### GitHub Pages 前端部署

前端在您推送到 `main` 分支时自动部署到 GitHub Pages。

**配置**：
- **来源**：`Deploy from a branch`
- **分支**：`main`
- **文件夹**：`/frontend`
- **URL**：`https://WenyuChiou.github.io/ai-trader-ollama/monitor.html`

**更新过程**：
1. 对前端文件进行更改
2. 提交并推送到 `main` 分支
3. GitHub Pages 自动部署（1-2 分钟）
4. 在 GitHub Pages URL 访问更新的前端

**注意**：前端在 GitHub Pages 上处于只读模式以确保安全。完整的交易控制仅在本地运行时可用。

---

## ⏰ 计划任务与自动化

### PowerShell 自动化脚本

所有自动化脚本都位于 `scripts/` 目录中，可以从项目根目录运行。

#### 设置脚本

| 脚本 | 目的 | 用法 | 要求 |
|--------|---------|-------|-------------|
| `setup_scheduled_tasks.ps1` | 配置自动化任务 | `.\scripts\setup_scheduled_tasks.ps1` | 管理员权限（可选） |
| `setup_long_term_running.ps1` | 完整长期设置 | `.\scripts\setup_long_term_running.ps1` | 管理员权限 |
| `setup_daily_upload_simple.ps1` | 设置每日数据上传 | `.\scripts\setup_daily_upload_simple.ps1` | 管理员权限（可选） |

#### 计划任务脚本

| 脚本 | 目的 | 计划 | 用法 |
|--------|---------|----------|-------|
| `schedule_daily_task.ps1` | 计划每日交易周期 | 市场开放时每天 | `.\scripts\schedule_daily_task.ps1` |
| `schedule_hourly_update.ps1` | 计划每小时数据更新 | 每小时 | `.\scripts\schedule_hourly_update.ps1` |
| `schedule_monitoring_task.ps1` | 计划系统监控 | 每 30 分钟 | `.\scripts\schedule_monitoring_task.ps1` |
| `schedule_daily_upload_only.ps1` | 计划每日数据上传 | 指定时间每天 | `.\scripts\schedule_daily_upload_only.ps1` |

#### 服务管理脚本

| 脚本 | 目的 | 用法 | 要求 |
|--------|---------|-------|-------------|
| `start_api_task_scheduler.ps1` | 使用任务计划程序启动 API | `.\scripts\start_api_task_scheduler.ps1` | 管理员权限 |
| `stop_all_services.ps1` | 停止所有运行的服务 | `.\scripts\stop_all_services.ps1` | 无 |
| `check_running_services.ps1` | 检查服务状态 | `.\scripts\check_running_services.ps1` | 无 |
| `check_api_status.ps1` | 检查 API 健康状态 | `.\scripts\check_api_status.ps1` | 无 |

**注意**：所有 PowerShell 脚本使用 UTF-8 编码，支持 Windows PowerShell 5.1+ 和 PowerShell Core 7+。某些脚本需要管理员权限（在"要求"列中注明）。

#### 开发与代码质量脚本

| 脚本 | 目的 | 用法 | 说明 |
|--------|---------|-------|-------|
| `check_syntax.py` | 检查所有主要文件的 Python 语法 | `python scripts/check_syntax.py` | 部署前验证语法，检查 10 个主要 Python 文件 |
| `check_file_status.py` | 检查 discussion_actions.jsonl 文件状态 | `python scripts/check_file_status.py` | 分析文件大小、条目数量和最近条目 |
| `check_tool_agents.py` | 检查工具条目 agent 字段分布 | `python scripts/check_tool_agents.py` | 按分类和 agent 分析工具条目 |
| `check_api_tool_agents.py` | 检查 API 工具结果 agent 分布 | `python scripts/check_api_tool_agents.py` | 验证 API 是否正确按 agent 分组返回工具 |
| `analyze_file_growth.py` | 分析文件增长速率和轮转 | `python scripts/analyze_file_growth.py` | 估算增长速率和达到轮转阈值的时间 |
| `test_performance_optimization.py` | 测试性能优化 | `python scripts/test_performance_optimization.py` | 测试日志轮转、性能监控和尾部读取 |
| `test_api_tool_response.py` | 测试 API 工具响应 | `python scripts/test_api_tool_response.py` | 验证 API 是否正确返回带 round 字段的工具 |
| `test_tool_display_with_memory.py` | 测试内存机制下的工具显示 | `python scripts/test_tool_display_with_memory.py` | 测试启用内存机制时工具是否正确显示 |

### 概述

系统支持以下自动化计划任务：
- **自动交易**：在指定时间自动运行交易周期
- **净值记录**：每 30 分钟记录投资组合净值
- **数据更新**：每小时更新市场数据和 P&L 计算
- **每日报告**：自动生成性能报告

### 快速设置

**一键设置（所有任务）**：
```powershell
.\scripts\setup_scheduled_tasks.ps1
```

选择选项 `5` 一次性设置所有任务，或选择单个任务（1-4）。

### 可用任务

#### 1. 自动交易周期
- **任务名称**: `AITrader-AutoTrading`
- **计划**: 每天 9:30 AM（仅工作日）
- **脚本**: `backend/scripts/run_daily_trading.py`
- **目的**: 在市场交易时间内自动执行交易周期

**自定义设置**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
# 选择选项 1，然后指定：
# - 交易时间（默认：09:30）
# - 仅工作日（默认：是）
```

#### 2. 每日备份（推荐）
- **任务名称**: `AITrader-DailyBackup`
- **计划**: 每天指定时间（默认：23:00）
- **脚本**: `backend/scripts/daily_backup.py`
- **目的**: 自动备份关键数据文件（portfolio_state.json, equity_history.jsonl, memory 等）

**设置**:
```powershell
.\scripts\setup_daily_backup.ps1
# 指定备份时间（默认：23:00）
# 创建定时任务以实现自动每日备份
```

**功能**:
- ✅ 备份关键文件：`portfolio_state.json`, `equity_history.jsonl`, `discussion_actions.jsonl`, `filled_orders.jsonl`, `pending_orders.jsonl`, `trades.jsonl`
- ✅ 备份 `memory/` 目录（每日/每周/每月快照）
- ✅ 创建备份清单（manifest.json）
- ✅ 自动清理旧备份（保留最近 7 天）
- ✅ 可手动运行：`python backend/scripts/daily_backup.py`

**📖 详细指南**: 查看 [`docs/BACKUP_GUIDE.md`](docs/BACKUP_GUIDE.md) 获取完整的备份和恢复说明。

#### 3. 净值记录（每 30 分钟）
- **任务名称**: `AITrader-EquityRecording`
- **计划**: 每 30 分钟
- **目的**: 记录投资组合净值用于历史跟踪和图表
- **API**: 调用 `POST /api/portfolio/record-equity`

**设置**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
# 选择选项 2
```

**注意**: 此任务需要 API 服务器正在运行（`http://localhost:8000`）。

#### 4. 数据更新（每小时）
- **任务名称**: `AITrader-DataUpdate`
- **计划**: 每小时
- **脚本**: `scripts/update_real_time_pnl.py`
- **目的**: 更新实时 P&L 计算和市场数据

**设置**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
# 选择选项 3
```

#### 5. 每日报告生成
- **任务名称**: `AITrader-DailyReport`
- **计划**: 每天 6:00 PM（仅工作日）
- **脚本**: `backend/scripts/generate_daily_report.py`
- **目的**: 生成每日性能报告

**自定义设置**:
```powershell
.\scripts\setup_scheduled_tasks.ps1
# 选择选项 4，然后指定：
# - 报告时间（默认：18:00）
```

---

## 🔔 API 连接监控

### 概述

系统包含一个自动连接监控器，可检测 API 服务器断开连接并通过 Windows Toast 通知通知您。

### 功能

- **自动监控**：每 30 秒检查一次 API 服务器状态
- **断开连接检测**：连续 3 次失败后发出警报
- **Windows Toast 通知**：当 API 离线时发送系统通知
- **自动重启选项**：提示自动重启 API 服务器
- **恢复检测**：当 API 服务器重新上线时通知

### 快速设置（推荐）

**一键设置**：
```powershell
.\scripts\setup_api_monitor.ps1
```

此交互式脚本提供以下选项：
1. 立即开始监控（在当前窗口）
2. 在后台窗口开始监控
3. 设置为计划任务（登录时自动启动）
4. 设置为计划任务 + 立即启动
5. 先测试监控器

### 手动启动

**开始监控**：
```powershell
.\scripts\monitor_api_connection.ps1
```

**在后台运行**：
```powershell
Start-Process powershell -ArgumentList '-ExecutionPolicy Bypass -File scripts\monitor_api_connection.ps1'
```

### 配置

监控脚本接受可选参数：

```powershell
# 自定义检查间隔（默认：30 秒）
.\scripts\monitor_api_connection.ps1 -CheckInterval 60

# 自定义重试次数（默认：3 次失败）
.\scripts\monitor_api_connection.ps1 -RetryCount 5

# 自定义 API URL
.\scripts\monitor_api_connection.ps1 -ApiUrl "http://localhost:8000/api/health"
```

### 通知方法

**选项 1：BurntToast 模块（推荐）**
```powershell
# 安装 BurntToast 模块以获得更好的通知
Install-Module -Name BurntToast -Scope CurrentUser
```

**选项 2：系统声音（后备）**
- 如果 BurntToast 不可用，使用 Windows 系统声音
- 显示控制台消息作为替代通知

### 测试

**测试监控器**：
```powershell
.\scripts\test_monitor_api.ps1
```

这将测试：
- ✅ API 连接检查
- ✅ 通知系统
- ✅ 重启功能
- ✅ 端口检测

### 行为

1. **正常运行**：每 30 秒显示状态（可以抑制）
2. **检测到断开连接**：连续 3 次失败后：
   - 发送 Windows Toast 通知
   - 显示控制台警报
   - 提示用户重启 API 服务器
3. **用户选择**：
   - **是**：自动在新窗口中重启 API 服务器
   - **否**：继续监控，用户可以手动重启
4. **恢复**：当 API 重新上线时，发送恢复通知

### 手动重启

如果自动重启失败，您可以手动重启：

```powershell
# 选项 1：使用设置脚本
.\scripts\setup_step3_start_services.ps1

# 选项 2：直接启动（使用虚拟环境）
# 方法 A：使用 & 运算符（PowerShell 标准）
& .\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# 方法 B：使用点源（替代方案）
. .\.venv\Scripts\Activate.ps1
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload

# 选项 3：直接启动（如果 venv 已激活）
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**注意**：监控脚本在自动重启时使用 `& "$activateScript"`（方法 A）。两种方法都有效，但 `&` 是执行脚本的 PowerShell 标准。

### 计划任务集成

您可以将监控器设置为计划任务以进行持续监控：

```powershell
# 创建计划任务（在系统启动时运行）
$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$ProjectRoot\scripts\monitor_api_connection.ps1`""
$Trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "AITrader-ConnectionMonitor" -Action $Action -Trigger $Trigger -Description "Monitor AI Trader API connection"
```

---

## 🚀 运行系统

### 启动 API 服务器

**选项 A：任务计划程序（推荐用于长期运行）**
```powershell
# 右键单击并以管理员身份运行：
scripts\start_api_task_admin.bat

# 或手动：
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
```
- ✅ 在后台运行
- ✅ Windows 登录时自动启动
- ✅ 即使关闭 CMD 也继续运行
- ✅ 失败时自动重启

**选项 B：Windows 服务（需要 NSSM）**
```powershell
# 右键单击并以管理员身份运行：
scripts\start_api_service_admin.bat
```

**选项 C：开发模式（需要保持窗口打开）**

**使用虚拟环境**（推荐）：

**方法 A：使用 & 运算符**（PowerShell 标准，与监控脚本相同）：
```powershell
# 首先激活虚拟环境
& .\.venv\Scripts\Activate.ps1

# 导航到后端目录
cd backend

# 启动 API 服务器
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**方法 B：使用点源**（替代方案）：
```powershell
# 首先激活虚拟环境
. .\.venv\Scripts\Activate.ps1

# 导航到后端目录
cd backend

# 启动 API 服务器
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**直接命令**（如果虚拟环境已激活）：
```powershell
cd backend
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

**命令参数**：
- `--host 0.0.0.0`：监听所有网络接口（可从其他设备访问）
- `--port 8000`：使用端口 8000
- `--reload`：启用代码更改时自动重新加载（开发模式）

**注意事项**：
- 保持终端窗口打开。关闭窗口将停止 API 服务器。
- 两种激活方法（方法 A 和方法 B）都有效。方法 A（`&`）是 PowerShell 标准，与监控脚本用于自动重启的方法匹配。

### 停止 API 服务器

**停止任务计划程序服务**：
```powershell
Stop-ScheduledTask -TaskName AITraderAPI
```

**停止所有服务**：
```powershell
# 从项目根目录运行：
.\scripts\stop_all_services.ps1
```

### 管理服务

**检查 API 状态**：
```powershell
.\scripts\check_api_status.ps1
```

**检查运行中的服务**：
```powershell
.\scripts\check_running_services.ps1
```

**检查端口使用情况**：
```powershell
.\scripts\check_port.ps1
```

---

## ❓ 故障排除

### Ollama 连接错误

**错误**：`Failed to connect to Ollama`

**解决方案**：
```bash
# 检查 Ollama 是否运行
curl http://localhost:11434/api/version

# 如果未运行，启动它
ollama serve

# 检查模型是否已拉取
ollama list

# 如果 deepseek-r1 未列出，拉取它
ollama pull deepseek-r1
```

### FRED API 错误

**错误**：`FRED API key not found`

**解决方案**：
```bash
# 设置 API 密钥
export FRED_API_KEY=your_key_here

# 对于 Windows PowerShell：
$env:FRED_API_KEY="your_key_here"
```

### 投资组合状态未找到

**错误**：`FileNotFoundError: portfolio_state.json`

**解决方案**：
```bash
python scripts/init_data.py
```

### 前端持仓显示问题

**错误**：持仓表显示 `undefined` 或 `NaN` 对于 shares, cost, price 等。

**根本原因**：前端从 `positions`（仅数量）读取，而不是从 `positions_detail`（完整信息）读取。

**解决方案**：
- ✅ **已修复**：前端现在从 `positions_detail` 读取，带后备逻辑
- 刷新浏览器页面（F5 或 Ctrl+R）以查看修复
- 所有持仓字段现在应正确显示

### 前端工具过滤与 Agent 匹配问题（最新）

**问题**：选择 TechnicalAnalyst 时，前端显示 MarketAnalyst 的工具，或显示 0 个工具。

**根本原因**：
- 前端工具过滤逻辑使用部分匹配，导致 agent 名称不匹配
- API 的 `tool_results_by_category` 受 `limit` 参数限制，可能只返回部分工具

**解决方案**：
- ✅ **精确 Agent 匹配**：前端现在使用精确 agent 名称匹配（不区分大小写），确保 TechnicalAnalyst 只看到 TechnicalAnalyst 的工具，而不是 MarketAnalyst 的工具
- ✅ **API 工具结果优化**：`tool_results_by_category` 现在从所有工具条目构建（不受 API `limit` 参数限制），确保所有 agent 的工具都可用于前端过滤
- ✅ **市场分类工具**：市场分类包含来自 MarketAnalyst 和 TechnicalAnalyst 的工具 - 过滤确保正确的 agent 特定显示
- ✅ **改进的匹配逻辑**：首先使用精确匹配，然后回退到部分匹配以保持向后兼容性
- ✅ **调试日志**：增强的控制台日志记录，用于工具过滤和 agent 匹配调试

### 文件大小管理与日志轮转

**问题**：`discussion_actions.jsonl` 文件可能变得过大，影响性能。

**解决方案**：
- ✅ **日志轮转**：当 `discussion_actions.jsonl` 超过 50 MB 时自动轮转（归档到 `data/logs/archive/`）
- ✅ **文件增长分析**：提供脚本分析文件增长速率并估算达到轮转阈值的时间
- ✅ **性能监控**：跟踪文件大小、读取时间和轮转事件
- ✅ **当前状态**：文件大小约 0.97 MB，估计 7 天后达到轮转阈值

### 重启后端 API

**快速重启**（如果 API 在窗口中运行）：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_fast.ps1
```

**如果 API 作为 Windows 服务运行**：
```powershell
# 重启服务
Restart-Service -Name AITraderAPI

# 或使用管理员批处理文件（推荐）
# 右键单击：scripts\start_api_service_admin.bat
# 然后选择 (R)estart
```

**如果 API 作为计划任务运行**：
```powershell
# 重启任务
Stop-ScheduledTask -TaskName AITraderAPI
Start-ScheduledTask -TaskName AITraderAPI

# 或使用任务脚本
powershell -ExecutionPolicy Bypass -File .\scripts\start_api_task_scheduler.ps1
# 然后选择 (R)estart
```

---

## 📖 文档

### 核心文档

- **[快速入门指南](docs/QUICK_START.md)** - 安装和首次运行
- **[配置指南](docs/CONFIGURATION.md)** - 完整配置参考
- **[API 参考](docs/API_REFERENCE.md)** - 所有 API 端点和用法
- **[架构文档](docs/ARCHITECTURE.md)** - 系统架构概述
- **[测试指南](docs/TESTING.md)** - 运行和编写测试
- **[故障排除指南](docs/TROUBLESHOOTING.md)** - 常见问题和解决方案

### 其他文档

| 文件 | 描述 |
|------|-------------|
| `docs/AGENTS.md` | 完整代理架构 |
| `docs/TOOLS.md` | 所有 29 个工具的详细文档（23 个市场 + 6 个内存） |
| `docs/DATA_STORAGE_GUIDE.md` | 数据存储位置和格式 |
| `docs/LONG_TERM_RUNNING_GUIDE.md` | 长期操作指南 |
| **[关键测试文件](docs/KEY_TEST_FILES.md)** | 关键测试文件和优先级指南 ⭐ |
| **[订单数据模式](docs/ORDER_DATA_SCHEMA.md)** | 用于性能分析的标准化订单数据结构 |
| **[性能 API 指南](docs/PERFORMANCE_API_GUIDE.md)** | 性能分析 API 文档和预期输出 |
| **[性能优化](docs/PERFORMANCE_OPTIMIZATION.md)** | 长期性能优化（尾部读取、日志轮转、缓存） ⭐ |
| **[优化影响分析](docs/OPTIMIZATION_IMPACT_ANALYSIS.md)** | 优化对讨论循环和前端工具的影响分析 |

---

## 🧪 测试

### 测试套件概述

**所有测试文件都位于 `tests/` 目录中**（不是 `test/`）。旧的 `test/` 目录已被删除并替换为结构良好的测试套件。

### 测试目录结构（主分支）

```
tests/
├── integration/             # 系统组件的集成测试
│   ├── test_agent_architecture.py  # 代理系统测试
│   ├── test_portfolio.py            # 投资组合管理测试
│   ├── test_memory.py               # 内存系统测试
│   ├── test_api.py                  # API 端点测试
│   └── test_trading_cycle_quick.py  # 快速交易周期测试（订单记录验证）
├── e2e/                     # 端到端测试
│   └── test_frontend.py             # 前端集成测试
├── utils/                   # 测试工具和辅助函数
│   └── test_helpers.py
├── conftest.py              # Pytest 配置和共享 fixtures
├── pytest.ini               # Pytest 设置
└── README.md                # 测试文档
```

**注意**：`tests/unit/` 目录（优化组件测试）仅存在于 `feature/system-optimization` 分支中。

### 运行测试

**前置要求**：
- Python 3.10+ 已安装
- 虚拟环境已激活
- 已安装依赖（`pip install -r backend/requirements.txt`）

**运行所有测试**：
```powershell
# 从项目根目录
pytest tests/ -v

# 或显示更多详细信息
pytest tests/ -v --tb=short
```

**运行特定测试类别**：
```powershell
# 仅单元测试
pytest tests/unit/ -v

# 仅集成测试
pytest tests/integration/ -v

# 仅端到端测试
pytest tests/e2e/ -v

# 特定测试文件
pytest tests/integration/test_portfolio.py -v

# 快速交易周期测试（验证订单记录）
python tests/integration/test_trading_cycle_quick.py
# 或使用 pytest：
pytest tests/integration/test_trading_cycle_quick.py -v
```

**运行覆盖率测试**（如果安装了 pytest-cov）：
```powershell
pytest tests/ --cov=backend/src --cov-report=html --cov-report=term-missing
```

### 测试状态（主分支）

✅ **当前状态**：**约 28 个测试通过**（100% 通过率）

**测试分类**：
- **集成测试**：约 25 个测试通过
  - 代理架构：6 个测试 ✅
  - 投资组合管理：7 个测试 ✅
  - 内存系统：5 个测试 ✅
  - API 端点：5 个测试 ✅
  - 交易周期快速测试：1 个测试 ✅（验证订单记录，强制市场开放）
- **E2E 测试**：4/4 通过
  - 前端集成：4 个测试 ✅

**注意**：优化组件的单元测试（约 18 个测试）仅在 `feature/system-optimization` 分支中。

### 测试文档

有关详细测试文档，请参阅：
- **[测试文档（英文）](tests/README.md)** | **[测试文档（中文）](tests/README_zh.md)** - 测试套件概述和指南
- **[关键测试文件](docs/KEY_TEST_FILES.md)** - **关键测试文件和优先级指南** ⭐
- **[测试指南](docs/TESTING.md)** - 综合测试文档
- **[测试脚本指南](docs/TEST_SCRIPTS_GUIDE.md)** - 独立测试脚本指南（英文）
- **[测试结果](docs/TEST_RESULTS.md)** - 最新测试执行结果

### 重要说明

1. **测试位置**：所有测试都在 `tests/` 目录中（不是 `test/`）
2. **旧测试文件**：旧的 `test/` 目录已被删除
3. **测试结构**：测试按类型组织（unit/integration/e2e）
4. **测试基础设施**：使用 pytest 和适当的 fixtures 和配置
5. **测试覆盖率**：结构完整，需要 Ollama 进行完整执行测试

---

## 🎯 快速参考

### 设置脚本（PowerShell）

所有设置脚本都位于 `scripts/` 目录中，可以从项目根目录运行。

| 脚本 | 目的 | 用法 | 要求 |
|--------|---------|-------|-------------|
| `setup_step1_install_dependencies.ps1` | 安装 Python 依赖和 Ollama | `.\scripts\setup_step1_install_dependencies.ps1` | Python 3.10+, Ollama |
| `setup_step2_configure.ps1` | 配置系统并初始化数据 | `.\scripts\setup_step2_configure.ps1` | 步骤 1 完成 |
| `setup_step3_start_services.ps1` | 启动 API 服务器 | `.\scripts\setup_step3_start_services.ps1` | 步骤 1-2 完成 |
| `setup_all_steps.ps1` | 按顺序运行所有设置步骤 | `.\scripts\setup_all_steps.ps1` | Python 3.10+, Ollama |
| `setup_scheduled_tasks.ps1` | 设置自动化任务 | `.\scripts\setup_scheduled_tasks.ps1` | 管理员权限（可选） |

**注意**：所有 PowerShell 脚本使用 UTF-8 编码，支持 Windows PowerShell 5.1+ 和 PowerShell Core 7+。

### 管理脚本

| 脚本 | 目的 | 用法 | 要求 |
|--------|---------|-------|-------------|
| `start_api_task_admin.bat` | 设置任务计划程序（长期） | 右键单击 → 以管理员身份运行 | 管理员权限 |
| `start_api_service_admin.bat` | 设置 Windows 服务（需要 NSSM） | 右键单击 → 以管理员身份运行 | 管理员权限, NSSM |
| `stop_all_services.ps1` | 停止所有运行的服务 | `.\scripts\stop_all_services.ps1` | 无 |
| `check_running_services.ps1` | 检查服务状态 | `.\scripts\check_running_services.ps1` | 无 |
| `check_api_status.ps1` | 检查 API 健康状态 | `.\scripts\check_api_status.ps1` | 无 |

### 测试脚本

| 脚本 | 目的 | 用法 | 说明 |
|--------|---------|-------|-------|
| `test_news_tools.py` | 独立测试新闻工具 | `python scripts/test_news_tools.py` | 不会覆盖交易记录 |
| `verify_portfolio.py` | 验证投资组合一致性 | `python scripts/verify_portfolio.py` | 只读，安全运行 |
| `test_api_server.py` | 测试 API 端点 | `python scripts/test_api_server.py` | 需要 API 运行 |
| `test_frontend_features.py` | 测试前端功能 | `python scripts/test_frontend_features.py` | 需要 API 运行 |
| `test_trading_cycle_quick.py` | 快速交易周期测试（单轮） | `python tests/integration/test_trading_cycle_quick.py` | 强制市场开放，验证订单记录 |
| `test_performance_optimization.py` | 测试性能优化 | `python scripts/test_performance_optimization.py` | 测试日志轮转、性能监控和尾部读取 |
| `test_api_tool_response.py` | 测试 API 工具响应 | `python scripts/test_api_tool_response.py` | 验证 API 是否正确返回带 round 字段的工具 |
| `test_tool_display_with_memory.py` | 测试内存机制下的工具显示 | `python scripts/test_tool_display_with_memory.py` | 测试启用内存机制时工具是否正确显示 |
| `check_tool_rounds.py` | 检查工具轮次分布 | `python scripts/check_tool_rounds.py` | 分析 discussion_actions.jsonl 中的 round 字段分布 |
| `check_tool_rounds_simple.py` | 快速检查工具轮次 | `python scripts/check_tool_rounds_simple.py` | 简化版本，用于快速调试 |
| `analyze_old_records.py` | 分析旧工具记录 | `python scripts/analyze_old_records.py` | 分析旧（round=0）vs 新（round=1-3）工具调用记录的分布 |
| `check_syntax.py` | 检查 Python 语法 | `python scripts/check_syntax.py` | 验证部署前语法，检查 10 个主要 Python 文件 |

**重要**：使用独立测试脚本（`test_news_tools.py`, `verify_portfolio.py`）进行测试。**不要**使用 `run_daily_trading.py` 进行测试，因为它会覆盖交易记录。

有关详细信息，请参阅[测试脚本指南](docs/TEST_SCRIPTS_GUIDE.md)。

### 配置文件

| 文件 | 目的 | 位置 |
|------|---------|----------|
| `config.json` | 主交易配置 | `backend/config/config.json` |
| `agents.yaml` | 代理特定设置 | `backend/config/agents.yaml` |
| 提示文件 | 代理提示 | `prompts/*.yml` |

### 数据文件

| 文件 | 目的 | 位置 |
|------|---------|----------|
| `portfolio_state.json` | 当前投资组合状态 | `data/logs/portfolio_state.json` |
| `discussion_actions.jsonl` | 代理对话 | `data/logs/discussion_actions.jsonl` |
| `equity_history.jsonl` | 净值历史 | `data/logs/equity_history.jsonl` |
| `filled_orders.jsonl` | 已完成订单 | `data/logs/filled_orders.jsonl` |
| `error_log.jsonl` | 系统错误日志 | `data/logs/error_log.jsonl` |

### 备份与错误日志

**每日备份**:
- **脚本**: `backend/scripts/daily_backup.py`
- **设置**: `.\scripts\setup_daily_backup.ps1`（需要管理员权限）
- **位置**: `data/backups/YYYYMMDD_HHMMSS/`
- **自动清理**: 保留最近 7 天的备份

**错误日志**:
- **模块**: `backend/src/utils/error_logger.py`
- **日志文件**: `data/logs/error_log.jsonl`
- **功能**: 结构化日志记录，自动轮转（10MB），错误级别（DEBUG/INFO/WARNING/ERROR/CRITICAL）
- **集成**: 自动记录交易循环、API 端点和数据操作中的错误

**📖 详细指南**: 查看 [`docs/BACKUP_GUIDE.md`](docs/BACKUP_GUIDE.md) 获取完整的备份和恢复说明。

---

## 📄 许可证

MIT License - 有关详细信息，请参阅 `LICENSE` 文件

---

**由 AI-Trader 团队用 ❤️ 构建**

*通过 AI 驱动的洞察和自主决策为交易者赋能*

