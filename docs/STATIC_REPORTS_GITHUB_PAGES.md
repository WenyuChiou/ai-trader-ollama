# 📊 在 GitHub Pages 上显示静态报告

> 如何在 GitHub Pages 上添加交易结果、对话摘要等静态输出

---

## 🎯 方案概述

虽然 GitHub Pages 是静态网站，但我们可以通过以下方式添加输出结果：

1. **静态 HTML 报告**：定期生成 HTML 报告文件
2. **GitHub Actions 自动生成**：每天自动生成并更新报告
3. **JSON 数据文件**：生成 JSON 格式的数据摘要

---

## 📋 方案 1: 手动生成静态报告（推荐开始）

### 步骤 1: 生成报告

```powershell
# 从项目根目录运行
python scripts/generate_static_report.py --output frontend/report.html
```

### 步骤 2: 提交到 GitHub

```powershell
git add frontend/report.html
git commit -m "Add daily trading report"
git push origin main
```

### 步骤 3: 访问报告

```
https://WenyuChiou.github.io/ai-trader-ollama/report.html
```

---

## 🤖 方案 2: 自动生成报告（GitHub Actions）

### 已创建的 Workflow

文件：`.github/workflows/generate-report.yml`

**功能**：
- 每天 00:00 UTC 自动运行
- 生成最新的交易报告
- 自动提交到 GitHub
- 自动部署到 GitHub Pages

**手动触发**：
- 在 GitHub 仓库页面：Actions → Generate Daily Report → Run workflow

---

## 📊 报告内容

生成的报告包含：

1. **统计摘要**：
   - 当前净值
   - 总收益
   - 收益率
   - 交易总数
   - 活跃 Agent 数量

2. **最近交易**：
   - 交易日期
   - 股票代码
   - 买卖方向
   - 数量
   - 价格
   - 状态

3. **活跃 Agent**：
   - 显示所有参与过的 Agent

4. **净值历史**：
   - 最近 30 天的净值记录

---

## 🔧 自定义报告内容

### 修改报告脚本

编辑 `scripts/generate_static_report.py`：

```python
# 添加更多数据
def load_news_summary():
    """加载新闻摘要"""
    # 你的代码
    pass

# 在 generate_html_report 中添加
news_summary = load_news_summary()
```

### 添加新的数据源

```python
# 加载对话摘要
def load_conversation_summary():
    conversations = load_recent_conversations(limit=50)
    # 提取关键信息
    return {
        "total": len(conversations),
        "agents": list(set(c.get("agent") for c in conversations)),
        "latest_stance": conversations[-1].get("stance") if conversations else None
    }
```

---

## 📁 文件结构

```
frontend/
├── monitor.html          # 实时仪表板
├── report.html           # 静态报告（自动生成）
└── index.html           # 首页（重定向到 monitor.html）

scripts/
└── generate_static_report.py  # 报告生成脚本

.github/workflows/
├── deploy-pages.yml      # 前端部署
└── generate-report.yml   # 报告生成（可选）
```

---

## 🎨 添加报告链接到首页

### 更新 `frontend/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI-Trader Portfolio Monitor</title>
    <style>
        body {
            font-family: 'Inter', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #0f172a 100%);
            color: #e5e7eb;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .container {
            text-align: center;
            padding: 40px;
        }
        h1 {
            color: #22d3ee;
            margin-bottom: 30px;
        }
        .links {
            display: flex;
            gap: 20px;
            justify-content: center;
            flex-wrap: wrap;
        }
        a {
            display: inline-block;
            padding: 16px 32px;
            background: rgba(34, 211, 238, 0.1);
            border: 2px solid #22d3ee;
            border-radius: 8px;
            color: #22d3ee;
            text-decoration: none;
            font-weight: 600;
            transition: all 0.3s;
        }
        a:hover {
            background: rgba(34, 211, 238, 0.2);
            transform: translateY(-2px);
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>💹 AI-Trader Portfolio Monitor</h1>
        <div class="links">
            <a href="monitor.html">📊 Live Dashboard</a>
            <a href="report.html">📈 Daily Report</a>
        </div>
    </div>
</body>
</html>
```

---

## 🔄 更新频率

### 手动更新

```powershell
# 每次运行交易周期后，手动生成报告
python scripts/generate_static_report.py
git add frontend/report.html
git commit -m "Update daily report"
git push origin main
```

### 自动更新（GitHub Actions）

- **每天 00:00 UTC** 自动运行
- 生成最新报告
- 自动提交和部署

**注意**：GitHub Actions 需要访问后端数据文件，如果后端在 Railway，可能需要：
1. 从 Railway 下载数据文件
2. 或者通过 API 获取数据

---

## 📝 报告数据来源

### 本地运行

报告从以下文件读取数据：
- `backend/data/logs/discussion_actions.jsonl` - 对话记录
- `backend/data/logs/trades.jsonl` - 交易记录
- `backend/data/logs/filled_orders.jsonl` - 已成交订单
- `backend/data/logs/equity_history.jsonl` - 净值历史

### Railway 部署

如果后端在 Railway：
- 需要从 Railway 服务器获取数据
- 或者通过 API 获取数据摘要

---

## 🎯 使用场景

### 场景 1: 每日摘要

生成每日交易摘要，包含：
- 当日交易
- 净值变化
- Agent 活动

### 场景 2: 性能报告

生成性能分析报告：
- 总收益
- 胜率
- 最佳/最差交易

### 场景 3: Agent 分析

生成 Agent 活动报告：
- 各 Agent 参与度
- 工具使用统计
- 决策质量分析

---

## ✅ 快速开始

### 1. 生成第一次报告

```powershell
python scripts/generate_static_report.py
```

### 2. 查看报告

打开 `frontend/report.html` 在浏览器中查看

### 3. 提交到 GitHub

```powershell
git add frontend/report.html
git commit -m "Add initial trading report"
git push origin main
```

### 4. 访问在线报告

```
https://WenyuChiou.github.io/ai-trader-ollama/report.html
```

---

## 🔍 故障排除

### 问题 1: 报告为空

**原因**：还没有运行过交易周期

**解决**：运行一次交易周期，然后再生成报告

### 问题 2: 找不到数据文件

**原因**：路径不正确

**解决**：检查脚本中的路径设置，确保指向正确的日志目录

### 问题 3: GitHub Actions 失败

**原因**：无法访问后端数据

**解决**：
- 如果后端在 Railway，需要配置 API 访问
- 或者使用本地数据文件（需要提交到 GitHub）

---

## 📚 扩展功能

### 添加图表

可以使用 Chart.js 添加净值曲线图：

```html
<canvas id="equityChart"></canvas>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script>
  // 使用 equity_history 数据绘制图表
</script>
```

### 添加更多统计

- 交易胜率
- 平均持仓时间
- 最大回撤
- 夏普比率

---

**现在你可以在 GitHub Pages 上显示静态报告了！** 🎉

