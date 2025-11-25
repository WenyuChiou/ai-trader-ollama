# Risk Analyst 评分机制详解

## 概述

Risk Analyst 使用 LLM（大语言模型）结合后处理逻辑来评估市场风险和仓位风险。评分机制包括：

1. **LLM 初始评分**：根据提示词和工具数据生成初始 risk_score
2. **VIX risk_score 调整**：强制应用 VIX 风险分数作为最低标准
3. **Fallback 机制**：当 LLM JSON 解析失败时使用备用评分逻辑

---

## 1. LLM 初始评分流程

### 1.1 输入数据

Risk Analyst 接收以下输入：

- **market_json**: 市场数据（包含 stocks、vix 等）
  - `market_json.vix.risk_score`: VIX 风险分数（0-10，强制传入）
  - `market_json.vix.level`: VIX 指数水平
  - `market_json.stocks`: 股票数据字典

- **current_positions**: 当前持仓信息
  - `quantity`: 持仓数量
  - `avg_cost`: 平均成本
  - `current_price`: 当前价格
  - `market_value`: 市值
  - `unrealized_pnl`: 未实现损益（美元）
  - `unrealized_pnl_pct`: 未实现损益百分比
  - `position_pct`: 持仓占比（占组合总值的百分比）

- **discussion_risk_signals**: 来自分析师讨论的风险信号
  - `vix_risk_score`: VIX 风险分数（0-10）

- **previous_discussion**: 之前的讨论内容（包含 VIX risk_score 强调信息）

### 1.2 LLM 提示词要求

根据 `prompts/risk_analyst.yml`，LLM 被要求：

1. **必须使用 VIX risk_score 作为主要因素**：
   - 如果 `vix_risk_score >= 6.0`，`overall_risk_score` 必须至少为 5.0-7.0
   - 如果 `vix_risk_score >= 6.0`，`overall_risk_level` 必须是 "medium" 或 "high"（不能是 "low"）
   - 公式：`overall_risk_score = max(vix_risk_score, calculated_stock_risk)`

2. **必须评估仓位风险**：
   - 分析每个持仓的 `unrealized_pnl` 和 `unrealized_pnl_pct`
   - 检查 `position_pct`（持仓集中度）
   - 识别高风险持仓（大额亏损、高集中度）

3. **必须使用工具获取额外数据**：
   - **强制调用** `vix_term` 工具（即使 `use_tools=False` 也会强制调用）
   - 可选：`fear_greed`、`get_market_breadth`、`get_correlation_matrix` 等

### 1.3 LLM 输出格式

LLM 应该返回 JSON 格式：

```json
{
  "overall_risk_level": "low" | "medium" | "high" | "extreme",
  "risk_score": 0-10,
  "analysis": "...",
  "market_risks": [...],
  "position_risks": [...],
  "position_control_report": {...},
  "recommendations": [...],
  "tool_calls": [...]
}
```

---

## 2. VIX Risk Score 调整逻辑

### 2.1 VIX Risk Score 计算

VIX risk_score 由 `src/tools/sentiment_tools.py` 中的 `vix_risk_score()` 函数计算：

```python
def vix_risk_score(v: Optional[Dict[str, Any]] = None) -> float:
    if not v: return 4.0
    val = v.get("vix") or v.get("value") or v.get("level")
    try: val = float(val)
    except Exception: return 4.0
    if val < 13: return 2.0
    if val < 18: return 4.0
    if val < 24: return 6.0
    if val < 30: return 7.5
    return 9.0
```

**映射规则**：
- VIX < 13: risk_score = 2.0（低风险）
- VIX 13-17: risk_score = 4.0（中等风险）
- VIX 18-23: risk_score = 6.0（中高风险）
- VIX 24-29: risk_score = 7.5（高风险）
- VIX >= 30: risk_score = 9.0（极高风险）

### 2.2 后处理调整逻辑

在 `risk_analyst_llm.py` 中，LLM 返回后，代码会强制调整 `risk_score`：

**优先级 1：从 API 获取 VIX 数据**（最可靠）
- 强制调用 `vix_term` API（即使 `use_tools=False`）
- 提取 `vix_risk_score_from_api`

**优先级 2：从 tool_results_data 提取**
- 如果 API 调用失败，从工具调用结果中提取

**优先级 3：从 market_json 提取**
- 使用 `market_json.vix.risk_score`

**优先级 4：从 discussion_risk_signals 提取**
- 使用 `discussion_risk_signals.vix_risk_score`

### 2.3 强制调整规则

如果 `vix_risk_to_use >= 6.0`：
- **强制** `risk_score` 至少为 `max(5.0, vix_risk_to_use - 1.0)`
  - 例如：VIX risk_score = 6.0 → min risk_score = 5.0
  - 例如：VIX risk_score = 7.5 → min risk_score = 6.5
- **强制** 如果 `overall_risk_level == "low"`，改为 `"medium"`

如果 `vix_risk_to_use >= 4.0`（但 < 6.0）：
- **确保** `risk_score` 至少为 `max(3.5, vix_risk_to_use - 0.5)`

**代码位置**：`backend/src/agents/risk_analyst_llm.py` 第 361-381 行

---

## 3. Fallback 评分机制

### 3.1 触发条件

当 LLM 返回的 JSON 解析失败时，使用 `_fallback_risk_analysis()` 函数：

```python
def _fallback_risk_analysis(
    market_json: Dict[str, Any],
    current_positions: Optional[Dict[str, Any]],
    portfolio_value: Optional[float],
) -> Dict[str, Any]:
```

### 3.2 Fallback 评分逻辑

1. **计算每只股票的风险分数**：
   - 使用 `risk_score` 工具对每只股票评分（0-10）
   - 如果工具失败，默认使用 5.0

2. **计算平均风险分数**：
   ```python
   avg_risk = sum(scores.values()) / len(scores) if scores else 5.0
   ```

3. **判断整体风险等级**：
   - `avg_risk > 7`: `overall_risk_level = "high"`
   - `avg_risk > 5`: `overall_risk_level = "medium"`
   - 否则: `overall_risk_level = "low"`

4. **识别高风险股票**：
   - `high_risk`: risk_score > 7 的股票列表
   - `safe_stocks`: risk_score <= 5 的股票列表

5. **分析仓位风险**：
   - 检查每个持仓的 `position_pct`（持仓占比）
   - 如果 `position_pct > 0.15`（15%），标记为集中度风险

### 3.3 Fallback 中的 VIX 调整

**重要**：Fallback 报告也会应用 VIX risk_score 调整：

- 从 API、tool_results_data 或 market_json 提取 VIX risk_score
- 应用与正常流程相同的调整规则：
  - `vix_risk_score >= 6.0` → 强制 `risk_score` 至少为 5.0
  - `vix_risk_score >= 4.0` → 确保 `risk_score` 至少为 3.5

**代码位置**：`backend/src/agents/risk_analyst_llm.py` 第 575-600 行（JSON 错误 fallback）和第 608-633 行（异常 fallback）

---

## 4. 评分示例

### 示例 1：正常流程（LLM 成功）

**输入**：
- VIX = 23.43 → `vix_risk_score = 6.0`
- LLM 返回：`risk_score = 2.91`, `overall_risk_level = "low"`

**后处理调整**：
- 检测到 `vix_risk_score = 6.0 >= 6.0`
- 强制调整：`risk_score = max(5.0, 6.0 - 1.0) = 5.0`
- 强制调整：`overall_risk_level = "medium"`

**最终输出**：
- `risk_score = 5.0`
- `overall_risk_level = "medium"`
- `vix_risk_score = 6.0`

### 示例 2：Fallback 流程（LLM JSON 解析失败）

**输入**：
- VIX = 20.52 → `vix_risk_score = 6.0`
- Fallback 计算：`avg_risk = 2.91`（基于股票风险分数）

**Fallback 调整**：
- 检测到 `vix_risk_score = 6.0 >= 6.0`
- 强制调整：`risk_score = max(5.0, 6.0 - 1.0) = 5.0`
- 强制调整：`overall_risk_level = "medium"`

**最终输出**：
- `risk_score = 5.0`（而不是 2.91）
- `overall_risk_level = "medium"`（而不是 "low"）
- `vix_risk_score = 6.0`

---

## 5. 关键代码位置

### 5.1 VIX Risk Score 计算
- **文件**：`backend/src/tools/sentiment_tools.py`
- **函数**：`vix_risk_score()`

### 5.2 Risk Analyst 主函数
- **文件**：`backend/src/agents/risk_analyst_llm.py`
- **函数**：`run_risk_analyst_llm()`

### 5.3 VIX 调整逻辑
- **文件**：`backend/src/agents/risk_analyst_llm.py`
- **位置**：第 361-381 行（正常流程）
- **位置**：第 575-600 行（JSON 错误 fallback）
- **位置**：第 608-633 行（异常 fallback）

### 5.4 Fallback 评分
- **文件**：`backend/src/agents/risk_analyst_llm.py`
- **函数**：`_fallback_risk_analysis()`（第 776 行开始）

### 5.5 提示词模板
- **文件**：`prompts/risk_analyst.yml`

---

## 6. 调试日志

Risk Analyst 会输出详细的调试日志：

- `[RISK ANALYST] ===== ENTRY: run_risk_analyst_llm called =====`
- `[RISK ANALYST] ✅ Found VIX risk_score in market_json: X.X`
- `[RISK ANALYST] 🔧 FORCING: Calling vix_term API...`
- `[RISK ANALYST] ✅ Got VIX data from API: VIX=X, risk_score=X`
- `[RISK ANALYST] 🔧 FORCING: VIX risk_score=X requires min overall risk_score=X, but LLM returned X. Adjusting...`
- `[RISK ANALYST] ✅ Final: VIX risk_score=X, overall risk_score=X, risk_level=X`

---

## 7. 总结

Risk Analyst 的评分机制确保：

1. **VIX risk_score 始终被考虑**：即使 LLM 忽略，后处理逻辑也会强制调整
2. **Fallback 也应用 VIX 调整**：即使 LLM JSON 解析失败，fallback 报告也会反映 VIX 风险
3. **多层保障**：API 调用 → tool_results → market_json → discussion_signals（优先级递减）

**核心原则**：VIX risk_score 是系统风险的主要指标，必须反映在最终的 `risk_score` 和 `overall_risk_level` 中。

