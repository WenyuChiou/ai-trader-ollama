# Streamlit 部署指南
**Streamlit Deployment Guide**

您可以使用 Streamlit 创建一个交互式的 Web 界面来展示和监控 AI-Trader 系统。

## 🎯 Streamlit vs 当前架构

### 当前架构
- **后端**: FastAPI (REST API)
- **前端**: HTML/JavaScript (monitor.html)
- **部署**: Vercel/Railway (后端) + GitHub Pages (前端)

### Streamlit 方案
- **全栈**: Streamlit (Python Web App)
- **优势**: 
  - ✅ 纯 Python，无需前端代码
  - ✅ 快速开发，内置组件
  - ✅ 自动响应式布局
  - ✅ 内置图表和可视化
- **部署**: Streamlit Cloud (免费) 或 Vercel

---

## 📦 方案选择

### 方案 1: Streamlit 作为独立应用（推荐）

创建一个新的 Streamlit 应用，连接到现有的 FastAPI 后端。

**优势**:
- ✅ 保留现有 FastAPI 后端
- ✅ Streamlit 作为前端界面
- ✅ 可以同时使用两种界面

### 方案 2: Streamlit 完全替代

用 Streamlit 重写整个应用，包含后端逻辑。

**优势**:
- ✅ 单一代码库
- ✅ 更简单的部署
- ⚠️ 需要重构现有代码

---

## 🚀 方案 1: Streamlit + FastAPI（推荐）

### 步骤 1: 安装依赖

```bash
pip install streamlit requests pandas plotly
```

### 步骤 2: 创建 Streamlit 应用

创建 `streamlit_app.py`:

```python
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime
import time

# 配置
st.set_page_config(
    page_title="AI Trader Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API 配置
API_BASE = st.sidebar.selectbox(
    "Backend API",
    [
        "http://localhost:8000",  # 本地开发
        "https://your-app.vercel.app",  # Vercel 生产环境
    ],
    index=0
)

# 标题
st.title("📈 AI Trader Dashboard")
st.markdown("---")

# 健康检查
@st.cache_data(ttl=30)
def check_backend_health():
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False

# 显示连接状态
if check_backend_health():
    st.success("✅ Backend Connected")
else:
    st.error("❌ Backend Not Connected")
    st.stop()

# 获取投资组合数据
@st.cache_data(ttl=30)
def get_portfolio():
    try:
        response = requests.get(f"{API_BASE}/api/portfolio/real-time", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching portfolio: {e}")
        return None

# 获取净值历史
@st.cache_data(ttl=300)
def get_equity_history(period="week"):
    try:
        response = requests.get(
            f"{API_BASE}/api/portfolio/equity-history",
            params={"period": period, "limit": 1000},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("ok") and data.get("records"):
                return data["records"]
        return []
    except Exception as e:
        st.error(f"Error fetching equity history: {e}")
        return []

# 获取交易记录
@st.cache_data(ttl=60)
def get_trades(limit=100):
    try:
        response = requests.get(
            f"{API_BASE}/api/trades/recent",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        st.error(f"Error fetching trades: {e}")
        return []

# 获取对话记录
@st.cache_data(ttl=60)
def get_conversations(limit=50):
    try:
        response = requests.get(
            f"{API_BASE}/api/agents/conversations",
            params={"limit": limit},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data.get("conversations", [])
        return []
    except Exception as e:
        st.error(f"Error fetching conversations: {e}")
        return []

# 主界面
portfolio = get_portfolio()

if portfolio:
    # 投资组合概览
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Value",
            f"${portfolio.get('total_value', 0):,.2f}",
            delta=f"${portfolio.get('total_pnl', 0):,.2f}"
        )
    
    with col2:
        st.metric(
            "Cash",
            f"${portfolio.get('cash', 0):,.2f}"
        )
    
    with col3:
        st.metric(
            "Equity Value",
            f"${portfolio.get('equity_value', 0):,.2f}"
        )
    
    with col4:
        pnl_pct = portfolio.get('total_pnl_pct', 0)
        st.metric(
            "Total P&L %",
            f"{pnl_pct:.2f}%",
            delta=f"{pnl_pct:.2f}%"
        )
    
    st.markdown("---")
    
    # 净值曲线图
    st.subheader("📊 Equity Curve")
    period = st.selectbox("Time Period", ["day", "week", "month"], index=1)
    
    history = get_equity_history(period)
    if history:
        df = pd.DataFrame(history)
        if 'timestamp' in df.columns and 'total_value' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            fig = px.line(
                df,
                x='timestamp',
                y='total_value',
                title='Portfolio Value Over Time',
                labels={'total_value': 'Portfolio Value ($)', 'timestamp': 'Time'}
            )
            st.plotly_chart(fig, use_container_width=True)
    
    # 持仓表格
    st.subheader("💼 Current Positions")
    positions = portfolio.get('positions_detail', {})
    if positions:
        positions_list = []
        for symbol, pos in positions.items():
            if isinstance(pos, dict):
                positions_list.append({
                    'Symbol': symbol,
                    'Quantity': pos.get('quantity', 0),
                    'Avg Cost': f"${pos.get('avg_cost', 0):.2f}",
                    'Current Price': f"${pos.get('current_price', 0):.2f}",
                    'Market Value': f"${pos.get('market_value', 0):.2f}",
                    'P&L': f"${pos.get('unrealized_pnl', 0):.2f}",
                    'P&L %': f"{pos.get('unrealized_pnl_pct', 0):.2f}%"
                })
        
        if positions_list:
            df_positions = pd.DataFrame(positions_list)
            st.dataframe(df_positions, use_container_width=True)
    
    # 交易记录
    st.subheader("📋 Recent Trades")
    trades = get_trades(limit=50)
    if trades:
        df_trades = pd.DataFrame(trades)
        if not df_trades.empty:
            st.dataframe(df_trades, use_container_width=True)
    
    # Agent 对话
    st.subheader("🤖 Agent Conversations")
    conversations = get_conversations(limit=30)
    if conversations:
        for conv in conversations[-10:]:  # 显示最近10条
            agent = conv.get('agent', 'Unknown')
            content = conv.get('content', '')[:200]  # 限制长度
            timestamp = conv.get('timestamp', '')
            
            with st.expander(f"{agent} - {timestamp}"):
                st.write(content)

# 自动刷新
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# 侧边栏
st.sidebar.markdown("---")
st.sidebar.markdown("### Controls")

if st.sidebar.button("Execute Trade Cycle"):
    st.sidebar.warning("This requires admin authentication")
    admin_secret = st.sidebar.text_input("Admin Secret", type="password")
    
    if admin_secret:
        try:
            response = requests.post(
                f"{API_BASE}/api/trading/execute-trade",
                headers={"x-admin-secret": admin_secret},
                timeout=600  # 6-7 minutes for full cycle
            )
            if response.status_code == 200:
                st.sidebar.success("Trade cycle started!")
            else:
                st.sidebar.error(f"Error: {response.status_code}")
        except Exception as e:
            st.sidebar.error(f"Error: {e}")

# 自动刷新设置
auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)")
if auto_refresh:
    time.sleep(30)
    st.rerun()
```

### 步骤 3: 运行 Streamlit

```bash
streamlit run streamlit_app.py
```

### 步骤 4: 配置后端 API URL

**更新 `streamlit_app.py` 中的后端 URL**：

1. **本地开发**：使用 `http://localhost:8000`
2. **生产环境**：更新为您的 Vercel 后端 URL
   ```python
   "https://your-app.vercel.app",  # 替换为您的 Vercel URL
   ```

**或使用环境变量**（推荐）：
- 设置 `API_BASE_URL` 环境变量
- Streamlit 会自动使用该变量

### 步骤 5: 配置依赖文件

**重要**：Streamlit Cloud 需要从项目根目录读取 `requirements.txt`。

确保根目录的 `requirements.txt` 包含 Streamlit 依赖：
```txt
streamlit>=1.28.0
plotly>=5.17.0
requests>=2.32.3
pandas>=2.2.2
```

如果根目录没有 `requirements.txt`，Streamlit Cloud 会尝试自动检测，但可能无法找到所有依赖。

### 步骤 6: 部署到 Streamlit Cloud

1. **推送到 GitHub**
   ```bash
   git add streamlit_app.py .streamlit/ requirements.txt
   git commit -m "feat: Add Streamlit dashboard with dependencies"
   git push origin main
   ```

2. **部署到 Streamlit Cloud**
   - 访问：https://streamlit.io/cloud
   - 使用 GitHub 账号登录
   - 点击 "New app"
   - 选择仓库：`WenyuChiou/ai-trader-ollama`
   - 选择主文件：`streamlit_app.py`
   - Python 版本：3.11
   - **Dependencies**: 选择 `requirements.txt`（根目录）
   - 点击 "Deploy"

3. **配置环境变量**（在 Streamlit Cloud 设置中）
   - 进入应用设置 → Secrets
   - 添加 TOML 格式的配置：
     ```toml
     API_BASE_URL = "https://your-backend-url.com"
     ```
   - 点击 "Save"

4. **等待部署完成**
   - 部署通常需要 1-3 分钟
   - 查看部署日志确认所有依赖安装成功

---

## 🚀 方案 2: 纯 Streamlit 应用

如果您想用 Streamlit 完全替代 FastAPI，需要：

1. **创建 Streamlit 应用**，直接调用后端逻辑
2. **重构代码**，将 API 逻辑改为直接函数调用
3. **部署到 Streamlit Cloud**

这需要更多重构工作，但可以简化架构。

---

## 📊 Streamlit vs 当前 HTML 前端对比

| 特性 | Streamlit | HTML/JavaScript |
|------|-----------|-----------------|
| **开发速度** | ⭐⭐⭐⭐⭐ 快速 | ⭐⭐⭐ 中等 |
| **自定义性** | ⭐⭐⭐ 有限 | ⭐⭐⭐⭐⭐ 完全控制 |
| **实时更新** | ⭐⭐⭐ 需要刷新 | ⭐⭐⭐⭐⭐ WebSocket |
| **图表** | ⭐⭐⭐⭐⭐ Plotly | ⭐⭐⭐⭐ Chart.js |
| **部署** | ⭐⭐⭐⭐⭐ Streamlit Cloud | ⭐⭐⭐⭐ GitHub Pages |
| **学习曲线** | ⭐⭐⭐⭐⭐ 简单 | ⭐⭐⭐ 需要 JS |

---

## 🎯 推荐方案

**推荐使用方案 1（Streamlit + FastAPI）**：

1. ✅ 保留现有 FastAPI 后端（无需重构）
2. ✅ Streamlit 作为额外的前端界面
3. ✅ 可以同时使用两种界面
4. ✅ 快速开发，易于维护

---

## 📖 相关文档

- [Streamlit 官方文档](https://docs.streamlit.io/)
- [Streamlit Cloud](https://streamlit.io/cloud)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

**最后更新**: 2025-12-11

