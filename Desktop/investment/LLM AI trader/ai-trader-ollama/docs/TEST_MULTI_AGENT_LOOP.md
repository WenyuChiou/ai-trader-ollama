# 🧪 测试多 Agent 讨论系统

## 📋 测试文件说明

### 1. `test_multi_agent_loop_quick.py` - 快速测试
**用途**: 最快速度验证系统是否正常工作

**特点**:
- 最少股票（2 只：NVDA, MSFT）
- 最少轮数（1 轮）
- 最少工具预算（4，每个 Agent = 1）

**运行方式**:
```bash
cd backend
python tests/test_multi_agent_loop_quick.py
```

---

### 2. `test_multi_agent_loop_simple.py` - 简化测试
**用途**: 快速测试多 Agent 讨论系统

**特点**:
- 少量股票（3 只：NVDA, MSFT, AAPL）
- 2 轮讨论
- 工具预算 4（每个 Agent = 1）

**运行方式**:
```bash
cd backend
python tests/test_multi_agent_loop_simple.py
```

---

### 3. `test_multi_agent_discussion_loop.py` - 完整测试
**用途**: 完整的交易循环测试，包含所有组件

**特点**:
- 更多股票（5 只，从 config.json 读取）
- 2 轮讨论
- 完整的 Portfolio 和 Trade Logger
- 详细的输出和验证

**运行方式**:
```bash
cd backend
python tests/test_multi_agent_discussion_loop.py
```

---

### 4. `test_full_trading_loop.py` - 端到端测试
**用途**: 完整的端到端测试（如果存在）

**运行方式**:
```bash
cd backend
python tests/test_full_trading_loop.py
```

---

## 🔄 测试流程

所有测试都会执行以下流程：

```
1. Market Agent → 市场数据抓取
   ↓
2. Market Analyst → 市场分析
   ↓
3. Stock Selection Agent → 股票筛选
   ↓
4. Multi-Agent Discussion → 多 Agent 讨论
   ├── Technical Analyst
   ├── Fundamental Analyst
   ├── Risk Analyst (Discussion)
   └── Sentiment Analyst
   ↓
5. Risk Analyst → 风险评估
   ↓
6. Trader Agent → 交易决策
   ↓
7. Execution → 执行交易
```

---

## ✅ 验证点

### 基本验证
- ✅ `stance` - 最终立场
- ✅ `decision` - 交易决策
- ✅ `discussion` - 讨论结果
- ✅ `risk_report` - 风险评估报告
- ✅ `stock_selection` - 股票选择结果
- ✅ `market_analysis` - 市场分析结果
- ✅ `portfolio` - Portfolio 信息

### 多 Agent 讨论验证
- ✅ `discussion.consensus` - 最终共识
- ✅ `discussion.agent_views` - 每个 Agent 的观点
  - ✅ `technical` - Technical Analyst 观点
  - ✅ `fundamental` - Fundamental Analyst 观点
  - ✅ `risk` - Risk Analyst 观点
  - ✅ `sentiment` - Sentiment Analyst 观点
- ✅ `discussion.discussion_rounds` - 讨论轮次记录

---

## 🚀 快速开始

### 最快测试（推荐用于快速验证）
```bash
cd backend
python tests/test_multi_agent_loop_quick.py
```

### 完整测试（推荐用于全面验证）
```bash
cd backend
python tests/test_multi_agent_discussion_loop.py
```

---

## 📊 预期输出

### 成功输出示例
```
================================================================================
Multi-Agent Discussion Loop Test
================================================================================

[CONFIG] Universe: ['NVDA', 'MSFT', 'AAPL']
[CONFIG] Using multi-agent discussion system

[EXECUTING] Starting trading cycle...

[ROUND 1] Multi-Agent Discussion
  [TECHNICAL] Analyzing...
  [FUNDAMENTAL] Analyzing...
  [RISK] Analyzing...
  [SENTIMENT] Analyzing...

================================================================================
TRADING CYCLE RESULTS
================================================================================

[STANCE] Final stance: cautious
[ROUNDS] Discussion rounds: 2

[MULTI-AGENT DISCUSSION]
  Final stance: cautious
  Discussion rounds: 2
  Agent viewpoints:
    - technical: bullish
    - fundamental: neutral
    - risk: cautious
    - sentiment: bullish

[VALIDATION]
  [OK] Has stance: True
  [OK] Has decision: True
  [OK] Has discussion: True
  ...

PASS: All checks passed!
```

---

## ⚠️ 注意事项

1. **网络连接**: 需要网络连接才能获取市场数据和新闻
2. **Ollama 服务**: 需要 Ollama 服务运行才能调用 LLM
3. **测试时间**: 完整测试可能需要几分钟（取决于网络和 LLM 响应速度）
4. **工具调用**: 每个 Agent 可能会调用工具（news_scan, vix_term 等），会增加测试时间

---

## 🔧 自定义测试

可以在测试文件中修改以下参数：

```python
result = execute_daily_trade(
    universe=["NVDA", "MSFT"],  # 测试股票列表
    rounds=2,                    # 讨论轮数
    auto_tools=True,             # 是否自动执行工具
    tool_budget=4,               # 总工具预算（每个 Agent = tool_budget // 4）
    preferred_domains=[...],     # 优先域名列表
    portfolio=portfolio,         # Portfolio 实例（可选）
    trade_logger=trade_logger,   # Trade Logger 实例（可选）
)
```

---

**更新日期**: 2025-11-02

