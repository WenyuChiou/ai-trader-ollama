"""
Streamlit Dashboard for AI Trader
Streamlit 仪表板 - 连接到 FastAPI 后端
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import os

# 页面配置
st.set_page_config(
    page_title="AI Trader Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stButton>button {
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# API 配置
# 优先使用环境变量（Streamlit Cloud 设置），否则显示选择框
default_api_url = os.getenv("API_BASE_URL", "http://localhost:8000")
api_options = [
    "http://localhost:8000",  # 本地开发
]

# 如果环境变量设置了 URL，添加到选项中
if os.getenv("API_BASE_URL") and os.getenv("API_BASE_URL") not in api_options:
    api_options.append(os.getenv("API_BASE_URL"))

# 添加其他选项
api_options.extend([
    "https://web-production-b42d6.up.railway.app",  # Railway (legacy - 即将过期)
])

# 确定默认索引
try:
    default_index = api_options.index(default_api_url)
except ValueError:
    default_index = 0

API_BASE = st.sidebar.selectbox(
    "Backend API",
    api_options,
    index=default_index,
    key="api_base"
)

# 显示当前使用的 URL
if os.getenv("API_BASE_URL"):
    st.sidebar.info(f"🌐 Using: {os.getenv('API_BASE_URL')}")

# 标题
st.markdown('<div class="main-header">📈 AI Trader Dashboard</div>', unsafe_allow_html=True)
st.markdown("---")

# 健康检查
@st.cache_data(ttl=30)
def check_backend_health():
    """检查后端连接状态"""
    try:
        response = requests.get(f"{API_BASE}/api/health", timeout=5)
        return response.status_code == 200, response.json() if response.status_code == 200 else None
    except Exception as e:
        return False, None

# 显示连接状态
health_status, health_data = check_backend_health()
if health_status:
    st.success("✅ Backend Connected")
else:
    st.error("❌ Backend Not Connected - Please check if backend is running")
    st.info(f"Trying to connect to: `{API_BASE}`")
    st.stop()

# 获取投资组合数据
@st.cache_data(ttl=30)
def get_portfolio():
    """获取实时投资组合数据"""
    try:
        response = requests.get(f"{API_BASE}/api/portfolio/real-time", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("ok"):
                return data
        return None
    except Exception as e:
        st.error(f"Error fetching portfolio: {e}")
        return None

# 获取净值历史
@st.cache_data(ttl=300)
def get_equity_history(period="week", limit=1000):
    """获取净值历史数据"""
    try:
        response = requests.get(
            f"{API_BASE}/api/portfolio/equity-history",
            params={"period": period, "limit": limit},
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
    """获取最近交易记录"""
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
def get_conversations(limit=50, include_demo=False):
    """获取 Agent 对话记录"""
    try:
        response = requests.get(
            f"{API_BASE}/api/agents/conversations",
            params={"limit": limit, "include_demo": include_demo},
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

# 获取市场状态
@st.cache_data(ttl=60)
def get_market_status():
    """获取市场状态"""
    try:
        response = requests.get(f"{API_BASE}/api/market/is-open", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# 主界面
portfolio = get_portfolio()

if portfolio:
    # 投资组合概览
    col1, col2, col3, col4 = st.columns(4)
    
    total_value = portfolio.get('total_value', 0)
    total_pnl = portfolio.get('total_pnl', 0)
    total_pnl_pct = portfolio.get('total_pnl_pct', 0)
    cash = portfolio.get('cash', 0)
    equity_value = portfolio.get('equity_value', 0)
    initial_value = portfolio.get('initial_value', 10000)
    
    with col1:
        st.metric(
            "Total Value",
            f"${total_value:,.2f}",
            delta=f"${total_pnl:,.2f}" if total_pnl != 0 else None
        )
    
    with col2:
        st.metric(
            "Cash",
            f"${cash:,.2f}"
        )
    
    with col3:
        st.metric(
            "Equity Value",
            f"${equity_value:,.2f}"
        )
    
    with col4:
        st.metric(
            "Total P&L %",
            f"{total_pnl_pct:.2f}%",
            delta=f"{total_pnl_pct:.2f}%" if total_pnl_pct != 0 else None
        )
    
    st.markdown("---")
    
    # 净值曲线图
    st.subheader("📊 Equity Curve")
    
    col_chart1, col_chart2 = st.columns([3, 1])
    
    with col_chart1:
        period = st.selectbox("Time Period", ["day", "week", "month"], index=1, key="period_select")
    
    with col_chart2:
        show_initial = st.checkbox("Show Initial Value", value=True)
    
    history = get_equity_history(period)
    if history:
        df = pd.DataFrame(history)
        if 'timestamp' in df.columns and 'total_value' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df = df.sort_values('timestamp')
            
            fig = go.Figure()
            
            # 净值曲线
            fig.add_trace(go.Scatter(
                x=df['timestamp'],
                y=df['total_value'],
                mode='lines',
                name='Portfolio Value',
                line=dict(color='#1f77b4', width=2)
            ))
            
            # 初始值线
            if show_initial:
                fig.add_hline(
                    y=initial_value,
                    line_dash="dash",
                    line_color="gray",
                    annotation_text=f"Initial: ${initial_value:,.2f}"
                )
            
            fig.update_layout(
                title='Portfolio Value Over Time',
                xaxis_title='Time',
                yaxis_title='Portfolio Value ($)',
                hovermode='x unified',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No equity history data available")
    
    st.markdown("---")
    
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
                    'Avg Cost': pos.get('avg_cost', 0),
                    'Current Price': pos.get('current_price', 0),
                    'Market Value': pos.get('market_value', 0),
                    'P&L': pos.get('unrealized_pnl', 0),
                    'P&L %': pos.get('unrealized_pnl_pct', 0)
                })
        
        if positions_list:
            df_positions = pd.DataFrame(positions_list)
            # 格式化显示
            df_display = df_positions.copy()
            df_display['Avg Cost'] = df_display['Avg Cost'].apply(lambda x: f"${x:,.2f}")
            df_display['Current Price'] = df_display['Current Price'].apply(lambda x: f"${x:,.2f}")
            df_display['Market Value'] = df_display['Market Value'].apply(lambda x: f"${x:,.2f}")
            df_display['P&L'] = df_display['P&L'].apply(lambda x: f"${x:,.2f}")
            df_display['P&L %'] = df_display['P&L %'].apply(lambda x: f"{x:.2f}%")
            
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("No positions")
    else:
        st.info("No positions")
    
    st.markdown("---")
    
    # 交易记录
    st.subheader("📋 Recent Trades")
    trades = get_trades(limit=50)
    if trades:
        df_trades = pd.DataFrame(trades)
        if not df_trades.empty:
            # 选择显示的列
            display_cols = ['symbol', 'action', 'quantity', 'price', 'status', 'timestamp']
            available_cols = [col for col in display_cols if col in df_trades.columns]
            st.dataframe(df_trades[available_cols], use_container_width=True, hide_index=True)
        else:
            st.info("No trades yet")
    else:
        st.info("No trades available")
    
    st.markdown("---")
    
    # Agent 对话
    st.subheader("🤖 Agent Conversations")
    
    col_conv1, col_conv2 = st.columns([2, 1])
    with col_conv1:
        conv_limit = st.slider("Show last N conversations", 5, 30, 10, key="conv_limit")
    with col_conv2:
        filter_agent = st.selectbox(
            "Filter by Agent",
            ["All"] + ["MarketAnalyst", "TechnicalAnalyst", "FundamentalAnalyst", "SentimentAnalyst", "RiskAnalyst", "TraderAgent"],
            key="filter_agent"
        )
    
    conversations = get_conversations(limit=conv_limit)
    if conversations:
        filtered_conv = conversations
        if filter_agent != "All":
            filtered_conv = [c for c in conversations if c.get('agent') == filter_agent]
        
        for conv in reversed(filtered_conv[-10:]):  # 显示最近10条
            agent = conv.get('agent', 'Unknown')
            content = conv.get('content', conv.get('summary', ''))[:500]  # 限制长度
            timestamp = conv.get('timestamp', '')
            round_num = conv.get('round', '')
            
            agent_emoji = {
                'MarketAnalyst': '🌐',
                'TechnicalAnalyst': '📈',
                'FundamentalAnalyst': '💼',
                'SentimentAnalyst': '😊',
                'RiskAnalyst': '⚠️',
                'TraderAgent': '🤖',
                'DiscussionCoordinator': '🤝'
            }.get(agent, '❓')
            
            with st.expander(f"{agent_emoji} {agent} - Round {round_num} - {timestamp}"):
                st.write(content)
    else:
        st.info("No conversations available")

# 侧边栏
st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Controls")

# 市场状态
market_status = get_market_status()
if market_status:
    is_open = market_status.get('is_open', False)
    if is_open:
        st.sidebar.success("🟢 Market Open")
    else:
        st.sidebar.info("🔴 Market Closed")

# 执行交易周期
st.sidebar.markdown("### 🚀 Execute Trade Cycle")

if st.sidebar.button("▶️ Start Trading Cycle"):
    admin_secret = st.sidebar.text_input("Admin Secret", type="password", key="admin_secret")
    
    if admin_secret:
        with st.sidebar:
            with st.spinner("Executing trade cycle (this may take 6-7 minutes)..."):
                try:
                    response = requests.post(
                        f"{API_BASE}/api/trading/execute-trade",
                        headers={"x-admin-secret": admin_secret},
                        timeout=600  # 6-7 minutes for full cycle
                    )
                    if response.status_code == 200:
                        st.success("✅ Trade cycle completed!")
                        st.cache_data.clear()  # 清除缓存以刷新数据
                    elif response.status_code == 401:
                        st.error("❌ Authentication failed")
                    else:
                        st.error(f"❌ Error: {response.status_code}")
                        st.write(response.text)
                except requests.exceptions.Timeout:
                    st.error("⏱️ Request timeout - Trade cycle may still be running")
                except Exception as e:
                    st.error(f"❌ Error: {e}")

# 刷新控制
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔄 Refresh")

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# 自动刷新设置
auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
if auto_refresh:
    time.sleep(30)
    st.rerun()

# 页脚
st.sidebar.markdown("---")
st.sidebar.markdown("### 📖 Links")
st.sidebar.markdown("- [API Docs]({}/docs)".format(API_BASE))
st.sidebar.markdown("- [Health Check]({}/api/health)".format(API_BASE))
st.sidebar.markdown("- [GitHub](https://github.com/WenyuChiou/ai-trader-ollama)")

