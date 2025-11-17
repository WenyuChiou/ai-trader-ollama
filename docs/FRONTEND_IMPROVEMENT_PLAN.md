# 前端改进计划 - TraderAgent、RiskAnalyst 和三轮 Discussion 显示

## 📋 当前前端运行方式分析

### 1. **前端架构**

**主要文件**: `frontend/monitor.html`

**运行方式**:
- 单页应用（SPA），所有功能在一个 HTML 文件中
- 通过 API 调用后端获取数据
- 实时刷新显示（自动刷新 + 手动刷新）

### 2. **数据获取流程**

```
前端 (monitor.html)
  ↓ fetchConversations()
  ↓ GET /api/agents/conversations
后端 API (server.py)
  ↓ 读取 discussion_actions.jsonl
  ↓ 返回 JSON 格式
前端
  ↓ renderConversations() / renderConversationsOverview()
  ↓ 解析和显示
```

### 3. **当前显示方式**

**对话显示** (`renderConversations` 函数，第3571行):
- 按日期分组显示
- 显示 agent 名称、图标、stance、analysis
- 显示 round 信息（如果有）
- 显示工具摘要

**关键代码位置**:
- `renderConversations()`: 第3571行 - 主对话列表显示
- `renderConversationsOverview()`: 第4119行 - Overview 页面显示
- `renderConversationsInline()`: 第4015行 - 内联显示

---

## 🎯 改进目标

### 1. **改进 TraderAgent 显示**

**当前问题**:
- TraderAgent 的 summary 可能被截断
- 没有显示交易决策的详细信息（buy_orders, sell_orders）
- 没有显示 rationale 和 risk_compliance

**改进方案**:
- 显示完整的 TraderAgent summary
- 添加交易决策详情（订单列表）
- 显示 rationale 和 risk_compliance
- 添加订单统计（买入/卖出数量、总金额）

### 2. **改进 RiskAnalyst 显示**

**当前问题**:
- RiskAnalyst 的结果没有写入 `discussion_actions.jsonl`
- 前端无法显示 RiskAnalyst 的分析结果
- 没有显示风险报告的关键信息

**改进方案**:
- 后端写入 RiskAnalyst 结果到 `discussion_actions.jsonl`
- 前端添加 RiskAnalyst 的显示逻辑
- 显示风险报告的关键指标（risk_level, risk_signals, recommendations）

### 3. **显示三轮 Discussion 信息**

**当前问题**:
- 只显示最终的 Coordinator summary
- 没有显示每轮讨论的详细内容
- 无法看到讨论的演进过程

**改进方案**:
- 从 `transcript` 中提取三轮讨论内容
- 按轮次分组显示（Round 1, Round 2, Round 3）
- 显示每轮的 agent 发言和工具调用
- 显示讨论的演进过程

---

## 🔧 后端改进方案

### 1. **写入 RiskAnalyst 结果**

**位置**: `backend/src/orchestrator/trading_cycle.py` 第951-958行

**当前代码**:
```python
risk_report = run_risk_analyst_llm(...)
# ❌ 没有写入 discussion_actions.jsonl
```

**改进代码**:
```python
risk_report = run_risk_analyst_llm(...)

# ✅ 写入 RiskAnalyst 结果到 discussion_actions.jsonl
try:
    risk_summary = risk_report.get("summary", "No risk analysis provided")
    risk_level = risk_report.get("risk_level", "medium")
    risk_signals = risk_report.get("risk_signals", [])
    
    risk_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
        "date": trade_date_str,
        "agent": "RiskAnalyst",
        "round": 0,
        "content": f"Risk Level: {risk_level}\n\nAnalysis: {risk_summary}\n\nRisk Signals: {', '.join(risk_signals) if risk_signals else 'None'}",
        "type": "discussion",
        "stance": risk_level,  # 使用 risk_level 作为 stance
        "tools_used": [],
        "risk_report": risk_report,  # 添加完整的 risk_report 数据
    }
    
    with convo_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(risk_entry, ensure_ascii=False) + "\n")
    print(f"[TRADING CYCLE] Wrote RiskAnalyst conversation entry (risk_level: {risk_level})")
except Exception as e:
    print(f"[TRADING CYCLE] ⚠️  Failed to write RiskAnalyst conversation entry: {e}")
```

---

### 2. **写入三轮 Discussion 信息**

**位置**: `backend/src/orchestrator/trading_cycle.py` 第422-516行

**当前代码**:
```python
# 只写入最终的 Coordinator summary
# ❌ 没有写入每轮讨论的详细内容
```

**改进代码**:
```python
# ✅ 写入三轮讨论信息
transcript = convo.get("transcript", [])
if transcript:
    for round_num, round_text in enumerate(transcript, 1):
        # 解析每轮的内容
        # 格式: "--- Round {r} ---\n{out_text}"
        if "--- Round" in round_text:
            # 提取轮次和内容
            parts = round_text.split("--- Round", 1)
            if len(parts) == 2:
                round_info = parts[1].split("---", 1)
                round_num_str = round_info[0].strip() if round_info else str(round_num)
                round_content = round_info[1].strip() if len(round_info) > 1 else round_text
            else:
                round_num_str = str(round_num)
                round_content = round_text
            
            # 写入每轮讨论
            round_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "date": trade_date_str,
                "agent": "DiscussionCoordinator",
                "round": round_num,  # ✅ 使用实际轮次编号
                "content": round_content,
                "type": "discussion",
                "stance": final_stance,  # 使用最终 stance
                "tools_used": [],
            }
            
            with convo_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(round_entry, ensure_ascii=False) + "\n")
            print(f"[TRADING CYCLE] Wrote Discussion Round {round_num} entry")
```

**或者更简单的方式**（从 `discussion_history` 中提取）:
```python
# ✅ 从 discussion_history 中提取每轮信息
discussion_history = convo.get("discussion_history", [])
# discussion_history 已经包含了每轮的信息
# 只需要确保 round 字段正确设置
```

---

### 3. **改进 TraderAgent 写入**

**位置**: `backend/src/orchestrator/trading_cycle.py` 第1603-1619行

**当前代码**:
```python
trader_entry = {
    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "date": trade_date_str,
    "agent": "TraderAgent",
    "round": 0,
    "content": f"Stance: {trader_stance}\n\nAnalysis: {trader_summary}",
    "type": "discussion",
    "stance": trader_stance,
    "tools_used": [],
}
```

**改进代码**:
```python
# ✅ 添加完整的交易决策信息
decision = result.get("decision", {})
buy_orders = decision.get("buy_orders", [])
sell_orders = decision.get("sell_orders", [])
rationale = decision.get("rationale", "")
risk_compliance = decision.get("risk_compliance", {})

# 构建详细内容
trader_content_parts = [
    f"Stance: {trader_stance}",
    f"\nAnalysis: {trader_summary}",
]

if rationale:
    trader_content_parts.append(f"\n\nRationale: {rationale}")

if buy_orders:
    trader_content_parts.append(f"\n\nBuy Orders: {len(buy_orders)} orders")
    for order in buy_orders[:5]:  # 只显示前5个
        trader_content_parts.append(f"  - {order.get('symbol')}: {order.get('quantity')} shares @ ${order.get('buy_price', 0):.2f}")

if sell_orders:
    trader_content_parts.append(f"\n\nSell Orders: {len(sell_orders)} orders")
    for order in sell_orders[:5]:  # 只显示前5个
        trader_content_parts.append(f"  - {order.get('symbol')}: {order.get('quantity')} shares @ ${order.get('sell_price', 0):.2f}")

if risk_compliance:
    trader_content_parts.append(f"\n\nRisk Compliance: {json.dumps(risk_compliance, indent=2)}")

trader_entry = {
    "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "date": trade_date_str,
    "agent": "TraderAgent",
    "round": 0,
    "content": "".join(trader_content_parts),
    "type": "discussion",
    "stance": trader_stance,
    "tools_used": [],
    "decision": decision,  # ✅ 添加完整的 decision 数据
    "buy_orders_count": len(buy_orders),
    "sell_orders_count": len(sell_orders),
}
```

---

## 🎨 前端改进方案

### 1. **改进 TraderAgent 显示**

**位置**: `frontend/monitor.html` 第4312-4426行

**改进代码**:
```javascript
// ✅ 特殊处理 TraderAgent
if (agent === 'TraderAgent' || agent.toLowerCase().includes('trader')) {
    // 提取交易决策信息
    const decision = conv.decision || {};
    const buyOrders = decision.buy_orders || [];
    const sellOrders = decision.sell_orders || [];
    const rationale = decision.rationale || '';
    const riskCompliance = decision.risk_compliance || {};
    
    // 显示交易统计
    let decisionHtml = '';
    if (buyOrders.length > 0 || sellOrders.length > 0) {
        decisionHtml = `
            <div style="margin-top: 12px; padding: 12px; background: rgba(34, 211, 238, 0.15); border-radius: 8px; border-left: 3px solid #22d3ee;">
                <div style="font-weight: 600; color: #22d3ee; margin-bottom: 8px;">📊 Trading Decision</div>
                ${buyOrders.length > 0 ? `
                    <div style="margin-bottom: 8px;">
                        <div style="font-weight: 600; color: #10b981; margin-bottom: 4px;">Buy Orders (${buyOrders.length}):</div>
                        <div style="font-size: 12px; color: #cbd5e1;">
                            ${buyOrders.slice(0, 10).map(order => 
                                `${order.symbol}: ${order.quantity} shares @ $${order.buy_price?.toFixed(2) || 'N/A'}`
                            ).join('<br>')}
                            ${buyOrders.length > 10 ? `<br>... and ${buyOrders.length - 10} more` : ''}
                        </div>
                    </div>
                ` : ''}
                ${sellOrders.length > 0 ? `
                    <div>
                        <div style="font-weight: 600; color: #ef4444; margin-bottom: 4px;">Sell Orders (${sellOrders.length}):</div>
                        <div style="font-size: 12px; color: #cbd5e1;">
                            ${sellOrders.slice(0, 10).map(order => 
                                `${order.symbol}: ${order.quantity} shares @ $${order.sell_price?.toFixed(2) || 'N/A'}`
                            ).join('<br>')}
                            ${sellOrders.length > 10 ? `<br>... and ${sellOrders.length - 10} more` : ''}
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // 显示 Rationale
    let rationaleHtml = '';
    if (rationale) {
        rationaleHtml = `
            <div style="margin-top: 12px; padding: 12px; background: rgba(245, 158, 11, 0.1); border-radius: 8px; border-left: 3px solid #f59e0b;">
                <div style="font-weight: 600; color: #f59e0b; margin-bottom: 8px;">💭 Rationale</div>
                <div style="font-size: 13px; color: #cbd5e1; white-space: pre-wrap;">${escapeHtml(rationale)}</div>
            </div>
        `;
    }
    
    // 显示 Risk Compliance
    let riskComplianceHtml = '';
    if (Object.keys(riskCompliance).length > 0) {
        riskComplianceHtml = `
            <div style="margin-top: 12px; padding: 12px; background: rgba(239, 68, 68, 0.1); border-radius: 8px; border-left: 3px solid #ef4444;">
                <div style="font-weight: 600; color: #ef4444; margin-bottom: 8px;">⚠️ Risk Compliance</div>
                <div style="font-size: 12px; color: #cbd5e1;">
                    ${Object.entries(riskCompliance).map(([key, value]) => 
                        `<div><strong>${key}:</strong> ${typeof value === 'object' ? JSON.stringify(value) : value}</div>`
                    ).join('')}
                </div>
            </div>
        `;
    }
    
    // 组合显示
    return `
        <div class="conversation-item">
            <div class="conversation-header">
                <span class="conversation-agent">${agentIcon} ${agent}</span>
                <span class="conversation-date">${timestamp ? new Date(timestamp).toLocaleString() : ''}</span>
            </div>
            ${stanceHtml}
            ${analysisText ? `<div class="conversation-content">${escapeHtml(analysisText)}</div>` : ''}
            ${decisionHtml}
            ${rationaleHtml}
            ${riskComplianceHtml}
        </div>
    `;
}
```

---

### 2. **改进 RiskAnalyst 显示**

**位置**: `frontend/monitor.html` 第4312-4426行

**改进代码**:
```javascript
// ✅ 特殊处理 RiskAnalyst
if (agent === 'RiskAnalyst' || agent.toLowerCase().includes('risk')) {
    // 提取风险报告信息
    const riskReport = conv.risk_report || {};
    const riskLevel = riskReport.risk_level || conv.stance || 'medium';
    const riskSignals = riskReport.risk_signals || [];
    const recommendations = riskReport.recommendations || [];
    
    // 显示风险级别
    const riskColor = 
        riskLevel === 'high' ? '#ef4444' :
        riskLevel === 'medium' ? '#f59e0b' :
        '#10b981';  // low
    
    let riskHtml = `
        <div style="margin-top: 12px; padding: 12px; background: rgba(239, 68, 68, 0.1); border-radius: 8px; border-left: 3px solid ${riskColor};">
            <div style="font-weight: 600; color: ${riskColor}; margin-bottom: 8px;">⚠️ Risk Level: ${riskLevel.toUpperCase()}</div>
            ${riskSignals.length > 0 ? `
                <div style="margin-bottom: 8px;">
                    <div style="font-weight: 600; color: #f59e0b; margin-bottom: 4px;">Risk Signals:</div>
                    <ul style="margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 12px;">
                        ${riskSignals.map(signal => `<li>${escapeHtml(signal)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
            ${recommendations.length > 0 ? `
                <div>
                    <div style="font-weight: 600; color: #10b981; margin-bottom: 4px;">Recommendations:</div>
                    <ul style="margin: 0; padding-left: 20px; color: #cbd5e1; font-size: 12px;">
                        ${recommendations.map(rec => `<li>${escapeHtml(rec)}</li>`).join('')}
                    </ul>
                </div>
            ` : ''}
        </div>
    `;
    
    return `
        <div class="conversation-item">
            <div class="conversation-header">
                <span class="conversation-agent">${agentIcon} ${agent}</span>
                <span class="conversation-date">${timestamp ? new Date(timestamp).toLocaleString() : ''}</span>
            </div>
            ${analysisText ? `<div class="conversation-content">${escapeHtml(analysisText)}</div>` : ''}
            ${riskHtml}
        </div>
    `;
}
```

---

### 3. **显示三轮 Discussion 信息**

**位置**: `frontend/monitor.html` 第3571-3600行

**改进代码**:
```javascript
function renderConversations(conversations, total = 0, has_more = false) {
    const content = document.getElementById('conversationsContent');
    
    if (conversations.length === 0) {
        content.innerHTML = `<div class="empty-conversations"><p>No conversations found yet.</p></div>`;
        return;
    }
    
    // ✅ 按日期和轮次分组
    const byDate = {};
    const byRound = {};  // 新增：按轮次分组
    
    conversations.forEach(conv => {
        const date = conv.date || conv.timestamp?.split('T')[0] || 'Unknown';
        const round = conv.round || 0;
        
        if (!byDate[date]) {
            byDate[date] = [];
        }
        byDate[date].push(conv);
        
        // ✅ 按轮次分组（只处理 discussion 类型）
        if (conv.type === 'discussion' && round > 0) {
            if (!byRound[round]) {
                byRound[round] = [];
            }
            byRound[round].push(conv);
        }
    });
    
    let html = '';
    
    // ✅ 显示三轮讨论（如果有）
    const sortedRounds = Object.keys(byRound).sort((a, b) => parseInt(a) - parseInt(b));
    if (sortedRounds.length > 0) {
        html += `<div style="margin-bottom: 32px; padding: 20px; background: rgba(15, 23, 42, 0.8); border-radius: 12px; border: 2px solid rgba(34, 211, 238, 0.3);">`;
        html += `<h3 style="font-size: 16px; color: #22d3ee; margin-bottom: 16px; font-weight: 600;">💬 Discussion Rounds</h3>`;
        
        sortedRounds.forEach(roundNum => {
            const roundConvs = byRound[roundNum];
            html += `<div style="margin-bottom: 20px; padding: 16px; background: rgba(34, 211, 238, 0.05); border-radius: 8px; border-left: 4px solid #22d3ee;">`;
            html += `<div style="font-size: 14px; font-weight: 600; color: #22d3ee; margin-bottom: 12px;">Round ${roundNum}</div>`;
            
            roundConvs.forEach(conv => {
                const agent = conv.agent || 'Unknown';
                const content_text = conv.content || '';
                const analysisMatch = content_text.match(/Analysis:\s*(.+)/is);
                const analysisText = analysisMatch ? analysisMatch[1].trim() : content_text;
                
                html += `
                    <div style="margin-bottom: 12px; padding: 12px; background: rgba(255, 255, 255, 0.03); border-radius: 6px;">
                        <div style="font-weight: 600; color: #cbd5e1; margin-bottom: 6px;">${getAgentIcon(agent)} ${agent}</div>
                        <div style="font-size: 13px; color: #94a3b8; white-space: pre-wrap; line-height: 1.6;">${escapeHtml(analysisText.substring(0, 500))}${analysisText.length > 500 ? '...' : ''}</div>
                    </div>
                `;
            });
            
            html += `</div>`;
        });
        
        html += `</div>`;
    }
    
    // 继续原有的按日期显示逻辑
    const sortedDates = Object.keys(byDate).sort().reverse();
    sortedDates.forEach(dateKey => {
        // ... 原有代码
    });
    
    content.innerHTML = html;
}
```

---

## 📝 实施步骤

### 步骤 1: 后端改进

1. **修改 `trading_cycle.py`**:
   - 添加 RiskAnalyst 写入逻辑（第951行后）
   - 添加三轮 Discussion 写入逻辑（第422行后）
   - 改进 TraderAgent 写入逻辑（第1603行）

### 步骤 2: 前端改进

1. **修改 `monitor.html`**:
   - 添加 TraderAgent 特殊显示逻辑（第4312行后）
   - 添加 RiskAnalyst 特殊显示逻辑（第4312行后）
   - 修改 `renderConversations()` 显示三轮讨论（第3571行）

### 步骤 3: 测试验证

1. **重启后端服务器**
2. **执行交易循环**
3. **检查前端显示**:
   - TraderAgent 是否显示完整信息
   - RiskAnalyst 是否显示
   - 三轮 Discussion 是否按轮次显示

---

## ✅ 检查清单

### 后端检查

- [ ] RiskAnalyst 结果写入 `discussion_actions.jsonl`
- [ ] 三轮 Discussion 信息写入（round 字段正确）
- [ ] TraderAgent 包含完整的 decision 数据

### 前端检查

- [ ] TraderAgent 显示交易决策详情
- [ ] TraderAgent 显示 rationale 和 risk_compliance
- [ ] RiskAnalyst 显示风险级别和信号
- [ ] 三轮 Discussion 按轮次分组显示
- [ ] 每轮显示 agent 发言内容

---

## 📊 数据格式规范

### RiskAnalyst 条目格式

```json
{
    "timestamp": "2025-11-16T15:51:40.558847Z",
    "date": "2025-11-16",
    "agent": "RiskAnalyst",
    "round": 0,
    "content": "Risk Level: medium\n\nAnalysis: ...\n\nRisk Signals: ...",
    "type": "discussion",
    "stance": "medium",
    "tools_used": [],
    "risk_report": {
        "risk_level": "medium",
        "risk_signals": ["signal1", "signal2"],
        "recommendations": ["rec1", "rec2"]
    }
}
```

### Discussion Round 条目格式

```json
{
    "timestamp": "2025-11-16T15:51:40.558847Z",
    "date": "2025-11-16",
    "agent": "DiscussionCoordinator",
    "round": 1,  // ✅ 轮次编号（1, 2, 3）
    "content": "Round 1 discussion content...",
    "type": "discussion",
    "stance": "neutral",
    "tools_used": []
}
```

### TraderAgent 条目格式（改进后）

```json
{
    "timestamp": "2025-11-16T15:51:40.558847Z",
    "date": "2025-11-16",
    "agent": "TraderAgent",
    "round": 0,
    "content": "Stance: neutral\n\nAnalysis: ...\n\nRationale: ...\n\nBuy Orders: ...",
    "type": "discussion",
    "stance": "neutral",
    "tools_used": [],
    "decision": {
        "buy_orders": [...],
        "sell_orders": [...],
        "rationale": "...",
        "risk_compliance": {...}
    },
    "buy_orders_count": 15,
    "sell_orders_count": 0
}
```

---

## 🎯 总结

**改进目标**:
1. ✅ **TraderAgent**: 显示完整的交易决策、rationale、risk_compliance
2. ✅ **RiskAnalyst**: 写入并显示风险报告
3. ✅ **三轮 Discussion**: 按轮次分组显示讨论内容

**实施顺序**:
1. 先改后端（写入数据）
2. 再改前端（显示数据）
3. 最后测试验证

**关键点**:
- 后端确保数据正确写入 `discussion_actions.jsonl`
- 前端确保正确解析和显示新数据
- 保持向后兼容（不影响现有显示）

