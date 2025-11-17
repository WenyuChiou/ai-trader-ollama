# 当前前端运行方式分析

## 📋 概述

本文档详细分析当前前端（`frontend/monitor.html`）的运行方式，为后续改进 TraderAgent、RiskAnalyst 和三轮 Discussion 显示做准备。

---

## 🏗️ 前端架构

### 1. **文件结构**

```
frontend/
  ├── monitor.html      # 主监控页面（单页应用）
  ├── index.html        # 入口页面（链接到 monitor.html）
  ├── report.html       # 静态报告页面
  ├── config.js         # 配置文件
  └── favicon.svg       # 图标
```

### 2. **运行方式**

- **单页应用（SPA）**: 所有功能都在 `monitor.html` 中
- **实时刷新**: 自动刷新 + 手动刷新按钮
- **API 驱动**: 通过 REST API 获取后端数据
- **无框架**: 纯 JavaScript，无 React/Vue 等框架

---

## 📡 数据获取流程

### 1. **对话数据获取**

**函数**: `fetchConversations(limit = 100, options = {})`

**位置**: `frontend/monitor.html` 第3336-3381行

**流程**:
```javascript
async function fetchConversations(limit = 100, options = {}) {
    // 1. 构建 API URL
    const url = `${apiBase}/api/agents/conversations?limit=${limit}&include_demo=false`;
    
    // 2. 发送 GET 请求
    const response = await fetch(url, {
        method: 'GET',
        mode: 'cors',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(30000),  // 30秒超时
    });
    
    // 3. 解析 JSON 响应
    const data = await response.json();
    
    // 4. 返回对话数据
    return {
        conversations: data.conversations || [],
        total: data.total || 0,
        has_more: data.has_more || false
    };
}
```

**后端 API**: `GET /api/agents/conversations`
- 从 `data/logs/discussion_actions.jsonl` 读取
- 返回 JSON 格式的对话列表

---

### 2. **后端数据格式**

**数据来源**: `data/logs/discussion_actions.jsonl`

**每行格式** (JSONL):
```json
{
    "timestamp": "2025-11-16T15:51:40.558847Z",
    "date": "2025-11-16",
    "agent": "DiscussionCoordinator",  // 或 MarketAnalyst, TraderAgent, etc.
    "round": 0,  // ⚠️ 当前都是 0，没有轮次信息
    "content": "Stance: neutral\n\nAnalysis: ...",
    "type": "discussion",  // 或 "tool"
    "stance": "neutral",
    "tools_used": ["news_scan", "get_market_breadth"]
}
```

**问题**:
- ❌ `round` 字段都是 `0`，没有实际的轮次信息
- ❌ 没有存储三轮讨论的详细内容
- ❌ RiskAnalyst 的结果没有写入

---

## 🎨 前端显示流程

### 1. **主显示函数**

**函数**: `renderConversations(conversations, total, has_more)`

**位置**: `frontend/monitor.html` 第3571-3600行

**流程**:
```javascript
function renderConversations(conversations, total = 0, has_more = false) {
    // 1. 按日期分组
    const byDate = {};
    conversations.forEach(conv => {
        const date = conv.date || conv.timestamp?.split('T')[0] || 'Unknown';
        if (!byDate[date]) {
            byDate[date] = [];
        }
        byDate[date].push(conv);
    });
    
    // 2. 生成 HTML（按日期显示）
    let html = '';
    const sortedDates = Object.keys(byDate).sort().reverse();
    
    sortedDates.forEach(dateKey => {
        // 过滤掉 tool 类型，只显示 discussion
        const dayConvs = byDate[dateKey].filter(c => c.type !== 'tool');
        
        // 3. 渲染每个对话条目
        dayConvs.forEach(conv => {
            // 提取 agent, content, stance, round 等信息
            // 生成 HTML
        });
    });
    
    // 4. 更新 DOM
    content.innerHTML = html;
}
```

---

### 2. **对话条目渲染**

**位置**: `frontend/monitor.html` 第3621-3995行

**当前显示内容**:
- ✅ Agent 名称和图标
- ✅ Stance（如果有）
- ✅ Analysis 文本（从 content 中提取）
- ✅ Round 信息（如果有，但当前都是 0）
- ✅ 工具摘要（tools_used）

**代码片段**:
```javascript
${dayConvs.map(conv => {
    const agent = conv.agent || 'Unknown';
    const content_text = conv.content || '';
    const round = conv.round || '';  // ⚠️ 当前都是 0
    const entry_type = conv.type || 'discussion';
    
    // 提取 Analysis 文本
    const analysisMatch = content_text.match(/Analysis:\s*(.+)/is);
    const analysisText = analysisMatch ? analysisMatch[1].trim() : '';
    
    // 显示 Round（如果有）
    ${round ? `<div>Round ${round}</div>` : ''}
    
    // 显示 Stance
    ${stanceHtml}
    
    // 显示 Analysis
    ${analysisText ? `<div>${escapeHtml(analysisText)}</div>` : ''}
}).join('')}
```

---

### 3. **Agent 图标映射**

**位置**: `frontend/monitor.html` 第3630-3651行

**当前支持的 Agent**:
```javascript
const icons = {
    'MarketAgent': '🌐',
    'MarketAnalyst': '🌐',
    'TechnicalAnalyst': '📈',
    'FundamentalAnalyst': '💼',
    'SentimentAnalyst': '😊',
    'DiscussionCoordinator': '💬',
    'DiscussionAgent': '💬',
    'RiskAnalyst': '⚠️',  // ✅ 已支持，但后端没有写入数据
    'TraderAgent': '🤖',  // ✅ 已支持
    'ToolSystem': '🔧',
    'Unknown': '🤖'
};
```

---

## 🔍 当前问题分析

### 1. **TraderAgent 显示问题**

**问题**:
- ❌ 只显示 summary，没有显示交易决策详情
- ❌ 没有显示 buy_orders 和 sell_orders
- ❌ 没有显示 rationale 和 risk_compliance
- ❌ 后端写入的 content 格式简单，缺少详细信息

**当前后端写入** (`trading_cycle.py` 第1603-1619行):
```python
trader_entry = {
    "agent": "TraderAgent",
    "round": 0,
    "content": f"Stance: {trader_stance}\n\nAnalysis: {trader_summary}",
    # ❌ 没有包含 decision 数据
}
```

---

### 2. **RiskAnalyst 显示问题**

**问题**:
- ❌ RiskAnalyst 的结果没有写入 `discussion_actions.jsonl`
- ❌ 前端无法显示 RiskAnalyst 的分析结果
- ❌ 没有风险报告的关键信息

**当前后端代码** (`trading_cycle.py` 第951-958行):
```python
risk_report = run_risk_analyst_llm(...)
# ❌ 没有写入 discussion_actions.jsonl
# ✅ 只在返回结果中包含 risk_report
```

**前端支持**:
- ✅ 图标已支持（⚠️ RiskAnalyst）
- ✅ 显示逻辑已支持（但因为没有数据，所以不显示）

---

### 3. **三轮 Discussion 显示问题**

**问题**:
- ❌ 只显示最终的 Coordinator summary
- ❌ 没有显示每轮讨论的详细内容
- ❌ `round` 字段都是 `0`，无法区分轮次
- ❌ 无法看到讨论的演进过程

**当前后端存储**:
- `transcript`: 包含三轮讨论的文本（`analyst_discussion.py` 第257行）
- `discussion_history`: 包含每轮的分析结果（但 `round` 字段都是 `0`）

**当前前端显示**:
- 只显示 `round` 字段（但都是 `0`）
- 没有按轮次分组显示

---

## 📊 数据流分析

### 1. **Discussion 数据流**

```
后端 (analyst_discussion.py)
  ↓ run_analyst_discussion()
  ↓ 生成 transcript (List[str])
  ↓ 每轮: transcript.append(f"--- Round {r} ---\n{out_text}")
  ↓
后端 (trading_cycle.py)
  ↓ 从 convo.get("discussion_history") 提取
  ↓ 写入 discussion_actions.jsonl
  ↓ round: 0  // ❌ 问题：都是 0
  ↓
后端 API (server.py)
  ↓ 读取 discussion_actions.jsonl
  ↓ 返回 JSON
  ↓
前端 (monitor.html)
  ↓ fetchConversations()
  ↓ renderConversations()
  ↓ 显示（但 round 都是 0）
```

---

### 2. **TraderAgent 数据流**

```
后端 (trader_agent.py)
  ↓ run_trader()
  ↓ 生成 decision (包含 buy_orders, sell_orders, rationale)
  ↓
后端 (trading_cycle.py)
  ↓ 写入 discussion_actions.jsonl
  ↓ content: "Stance: ...\n\nAnalysis: ..."  // ❌ 缺少详细信息
  ↓
前端 (monitor.html)
  ↓ 只显示 Analysis 文本
  ↓ ❌ 没有显示 decision 详情
```

---

### 3. **RiskAnalyst 数据流**

```
后端 (risk_analyst_llm.py)
  ↓ run_risk_analyst_llm()
  ↓ 生成 risk_report
  ↓
后端 (trading_cycle.py)
  ↓ ❌ 没有写入 discussion_actions.jsonl
  ↓ 只在返回结果中包含 risk_report
  ↓
前端 (monitor.html)
  ↓ ❌ 无法获取 RiskAnalyst 数据
  ↓ ❌ 无法显示
```

---

## 🎯 改进方向

### 1. **后端改进**

1. **写入 RiskAnalyst 结果**
   - 在 `trading_cycle.py` 第951行后添加写入逻辑
   - 包含 `risk_report` 完整数据

2. **写入三轮 Discussion 信息**
   - 从 `transcript` 中提取每轮内容
   - 设置正确的 `round` 字段（1, 2, 3）
   - 或者从 `discussion_history` 中提取并设置 `round`

3. **改进 TraderAgent 写入**
   - 包含完整的 `decision` 数据
   - 包含 `buy_orders` 和 `sell_orders` 详情
   - 包含 `rationale` 和 `risk_compliance`

---

### 2. **前端改进**

1. **改进 TraderAgent 显示**
   - 特殊处理 TraderAgent，显示交易决策详情
   - 显示订单列表（buy_orders, sell_orders）
   - 显示 rationale 和 risk_compliance

2. **改进 RiskAnalyst 显示**
   - 特殊处理 RiskAnalyst，显示风险报告
   - 显示风险级别、风险信号、建议

3. **显示三轮 Discussion**
   - 按 `round` 字段分组显示
   - 显示每轮的 agent 发言
   - 显示讨论的演进过程

---

## 📝 当前代码关键位置

### 后端

1. **写入对话数据**: `backend/src/orchestrator/trading_cycle.py` 第422-589行
2. **写入 TraderAgent**: `backend/src/orchestrator/trading_cycle.py` 第1603-1619行
3. **生成 transcript**: `backend/src/agents/analyst_discussion.py` 第257行
4. **RiskAnalyst 调用**: `backend/src/orchestrator/trading_cycle.py` 第951行

### 前端

1. **获取对话**: `frontend/monitor.html` 第3336行
2. **渲染对话**: `frontend/monitor.html` 第3571行
3. **对话条目**: `frontend/monitor.html` 第3621行
4. **Agent 图标**: `frontend/monitor.html` 第3630行

---

## ✅ 总结

**当前状态**:
- ✅ 前端架构清晰，单页应用
- ✅ 数据获取流程完整
- ✅ 显示逻辑已支持所有 agent 类型
- ❌ 后端数据不完整（缺少 RiskAnalyst、三轮 Discussion、TraderAgent 详情）

**改进重点**:
1. **后端**: 完善数据写入（RiskAnalyst、三轮 Discussion、TraderAgent 详情）
2. **前端**: 特殊处理显示（TraderAgent、RiskAnalyst、三轮 Discussion）

**实施顺序**:
1. 先改后端（确保数据正确写入）
2. 再改前端（正确显示新数据）
3. 测试验证

