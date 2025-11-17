# 逐步测试指南

## 前置条件

1. ✅ **已修复 `server.py` 的语法错误**（缩进问题已解决）
2. ⚠️ **需要重启后端服务器**（修复后必须重启才能生效）

## 测试步骤

### 步骤 1: 启动后端服务器

```bash
cd backend
uvicorn src.api.server:app --reload --host 127.0.0.1 --port 8000
```

**验证**: 应该看到类似这样的输出：
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**如果看到错误**: 检查是否有语法错误（应该已经修复）

### 步骤 2: 测试 API 连接

运行测试脚本：
```bash
python scripts/test_frontend_features.py
```

**预期结果**:
- ✅ 测试 1: API 连接 - 通过
- ✅ 测试 2: 对话端点 - 通过
- ⚠️ 测试 3-5: 可能需要先执行交易循环

### 步骤 3: 执行一次交易循环

在前端页面点击"执行交易循环"按钮，或直接调用 API：
```bash
curl -X POST http://127.0.0.1:8000/api/trading/execute-trade
```

**预期结果**:
- 后端日志显示执行过程
- 生成新的对话记录到 `data/logs/discussion_actions.jsonl`

### 步骤 4: 验证前端显示

1. 打开前端页面: `http://localhost:3000/monitor.html` (或你使用的端口)
2. 点击"对话"按钮打开对话模态框
3. 检查以下内容：

#### ✅ 多轮讨论 (Round 1, 2, 3)
- 应该看到 "💬 Discussion Rounds" 部分
- 每个 Round 显示对应的对话内容
- Round 1, 2, 3 分别显示

#### ✅ RiskAnalyst 风险报告
- 应该看到 "⚠️ RiskAnalyst" 的对话条目
- 显示风险等级（HIGH/MEDIUM/LOW）
- 显示风险评分（0-10）
- 显示风险信号列表
- 显示建议列表

#### ✅ TraderAgent 决策摘要
- 应该看到 "🤖 TraderAgent" 的对话条目
- **只显示 summary**（不显示详细订单信息）
- 显示市场立场（BULLISH/BEARISH/NEUTRAL）
- **不显示** `buy_orders` 或 `sell_orders` 的详细内容

### 步骤 5: 再次运行测试脚本

```bash
python scripts/test_frontend_features.py
```

**预期结果**:
- ✅ 所有测试通过
- 显示找到的数据统计

## 验证清单

### 后端验证

- [ ] `server.py` 无语法错误（已修复）
- [ ] 后端服务器成功启动
- [ ] `/api/health` 端点返回 200
- [ ] `/api/agents/conversations` 端点返回数据

### 数据验证

- [ ] `data/logs/discussion_actions.jsonl` 文件存在
- [ ] 文件中有 `RiskAnalyst` 条目（`agent: "RiskAnalyst"`）
- [ ] 文件中有 `TraderAgent` 条目（`agent: "TraderAgent"`）
- [ ] 文件中有 `DiscussionCoordinator` 条目且 `round > 0`

### 前端验证

- [ ] 多轮讨论正确显示（Round 1, 2, 3）
- [ ] RiskAnalyst 显示风险报告详情
- [ ] TraderAgent 只显示 summary，不显示订单详情

## 常见问题

### Q: API 返回 404
**A**: 后端服务器未启动或未正确启动。检查：
1. 服务器是否在运行
2. 端口是否正确（8000）
3. `server.py` 是否有语法错误

### Q: 测试显示"未找到数据"
**A**: 需要先执行一次交易循环来生成数据。

### Q: TraderAgent 仍然显示订单详情
**A**: 检查后端 `trading_cycle.py` 是否正确将 summary 写入 `content` 字段。

### Q: 前端没有显示多轮讨论
**A**: 检查：
1. 数据文件中是否有 `round > 0` 的条目
2. 前端代码是否正确处理 `round` 字段

## 下一步

如果所有测试通过，说明改进已成功应用。如果某些测试失败，请：
1. 检查后端日志
2. 检查数据文件内容
3. 检查前端控制台错误

