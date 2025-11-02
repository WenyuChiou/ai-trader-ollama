# 🚀 快速开始 - Whimsical (Agent 图标流程图)

## 📋 快速指南

### 步骤 1: 访问并注册

1. 打开 https://whimsical.com/
2. 点击 "Sign up" 注册账号（免费版可用）
3. 登录账号

### 步骤 2: 创建 Flowchart

1. 点击左侧 "Create" 按钮
2. 选择 "Flowchart"

### 步骤 3: 添加 Agent 节点（带图标）

1. 点击画布上的 "+" 或使用快捷键 "N" 添加节点
2. 输入节点文本（如 "Market Agent"）
3. 选中节点，右侧会出现工具栏
4. 点击工具栏中的 **图标按钮** 🔲（或使用快捷键 "I"）
5. 在图标搜索框中输入：
   - "robot" - 机器人图标（适合 Market Agent）
   - "person" - 人物图标（适合 Market Analyst）
   - "group" - 群体图标（适合 Analyst Discussion）
   - "shield" - 盾牌图标（适合 Risk Analyst）
   - "briefcase" - 公文包图标（适合 Trader Agent）
   - "chart" - 图表图标（适合 Backend Display）
6. 选择合适的图标，点击应用

### 步骤 4: 连接节点

1. 选中节点，会出现连接点
2. 从连接点拖拽到目标节点
3. 或使用箭头工具（快捷键 "A"）手动绘制箭头

### 步骤 5: 美化流程图

1. 可以调整节点颜色：
   - 选中节点 → 右侧工具栏 → "Fill" → 选择颜色
2. 可以调整箭头样式：
   - 选中箭头 → 右侧工具栏 → 调整样式
3. 可以添加分组：
   - 选中多个节点 → 右键 → "Group"

### 步骤 6: 导出

1. 点击右上角 "Share" 按钮
2. 选择 "Export"
3. 选择格式（PNG, SVG, PDF）
4. 点击 "Download"

---

## 🎯 Agent 流程图结构建议

### 节点布局

```
[Goal] 
    ↓
[Market Agent 🤖] 
    ↓
[Market Analyst 👤] 
    ↓
[Analyst Discussion 👥] (多轮循环)
    ↓
[Risk Analyst 🛡️] 
    ↓
[Trader Agent 💼] 
    ↓
[Execution & Portfolio 💰] 
    ↓
[Backend Display 📊]
    ↓
[Evaluation & Feedback 🔄]
```

### 节点文本建议

1. **Goal**: "Daily Trading Goal"
2. **Market Agent**: "Market Agent<br/>Collect Market Data" (使用换行符<br/>)
3. **Market Analyst**: "Market Analyst<br/>Analyze Market"
4. **Analyst Discussion**: "Analyst Discussion<br/>Multi-Round Consensus"
5. **Risk Analyst**: "Risk Analyst<br/>Position Risk Assessment"
6. **Trader Agent**: "Trader Agent<br/>Trading Decision"
7. **Execution**: "Execution<br/>Update Portfolio"
8. **Backend Display**: "Backend Display<br/>P&L & Trade History"

### 分组建议

可以将相关节点分组：

1. **Data Collection Layer**: Market Agent, Market Analyst
2. **Analysis Layer**: Analyst Discussion
3. **Risk Management Layer**: Risk Analyst
4. **Decision Layer**: Trader Agent
5. **Execution Layer**: Execution, Portfolio
6. **Display Layer**: Backend Display

---

## 🎨 图标选择建议

### Agent 图标映射

| Agent | 图标关键词 | 图标建议 |
|-------|-----------|----------|
| Market Agent | "robot" | 🤖 机器人图标 |
| Market Analyst | "person" | 👤 人物图标 |
| Analyst Discussion | "group" | 👥 群体图标 |
| Risk Analyst | "shield" | 🛡️ 盾牌图标 |
| Trader Agent | "briefcase" | 💼 公文包图标 |
| Portfolio | "money" | 💰 金钱图标 |
| Backend Display | "chart" | 📊 图表图标 |

### 颜色建议

可以使用不同颜色区分不同类型的 Agent：

- **Data Collection** (Market Agent, Market Analyst): 蓝色系
- **Analysis** (Analyst Discussion): 绿色系
- **Risk Management** (Risk Analyst): 黄色/橙色系
- **Decision** (Trader Agent): 红色系
- **Execution** (Portfolio): 紫色系
- **Display** (Backend): 灰色系

---

## 💡 技巧提示

### 1. 使用快捷键

- **N**: 添加新节点
- **A**: 添加箭头
- **I**: 添加图标
- **G**: 分组
- **Ctrl/Cmd + Z**: 撤销
- **Ctrl/Cmd + Y**: 重做

### 2. 自定义图标

如果 Whimsical 图标库中没有合适的图标：

1. 从 Heroicons (https://heroicons.com/) 下载 SVG 图标
2. 在 Whimsical 中，选中节点 → 图标按钮 → "Upload icon"
3. 上传 SVG 文件

### 3. 使用模板

Whimsical 有模板库，可以搜索 "agent", "workflow", "process" 等关键词找到相关模板

### 4. 协作功能

可以邀请团队成员协作编辑流程图

---

## 🔗 参考资源

### 图标资源

- **Heroicons**: https://heroicons.com/
- **Material Icons**: https://fonts.google.com/icons
- **Icons8**: https://icons8.com/

### 流程图参考

参考 `docs/AGENT_SYSTEM_FLOWCHART.md` 和 `docs/AGENT_SYSTEM_MERMAID.md` 了解完整的流程图结构

---

**开始**: 访问 https://whimsical.com/，注册账号，创建 Flowchart，开始绘制你的 Agent 流程图！

