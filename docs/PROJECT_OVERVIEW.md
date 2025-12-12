# Project Overview

## What Is AI-Trader Ollama?

**AI-Trader Ollama** is a fully autonomous stock trading system that uses artificial intelligence agents to analyze financial markets, make trading decisions, and manage investment portfolios. The system combines multiple specialized AI agents that work together through collaborative discussions to reach trading decisions.

## What Problem Does It Solve?

Traditional trading systems often rely on single-strategy approaches or manual analysis. AI-Trader Ollama addresses this by:

1. **Multi-Perspective Analysis**: Uses 6 specialized agents, each analyzing the market from different angles (technical, fundamental, sentiment, risk)
2. **Collaborative Decision Making**: Agents discuss and debate before making decisions, similar to a team of human analysts
3. **Learning from History**: Uses a RAG (Retrieval-Augmented Generation) memory system to learn from past trading decisions
4. **Comprehensive Market Coverage**: Analyzes 118+ NASDAQ-100 stocks simultaneously
5. **Automated Execution**: Fully autonomous operation with real-time monitoring

## Key Capabilities

### 🤖 Multi-Agent System
- **6 Specialized Agents**:
  - Market Analyst: Fetches and analyzes market data
  - Technical Analyst: Analyzes price patterns and technical indicators
  - Fundamental Analyst: Evaluates company financials and metrics
  - Sentiment Analyst: Analyzes news and market sentiment
  - Risk Analyst: Assesses portfolio risk and position limits
  - Trader Agent: Makes final trading decisions

### 📊 Advanced Analysis Tools
- **28 Tools** covering:
  - Real-time market data (OHLCV, volume, price)
  - Technical indicators (RSI, MACD, Bollinger Bands, etc.)
  - Fundamental metrics (P/E ratio, market cap, revenue, etc.)
  - News and sentiment analysis
  - Economic data (VIX, Fear & Greed Index)
  - Historical memory retrieval (RAG system)

### 🧠 RAG Memory System
- Agents automatically retrieve relevant historical memories before making decisions
- Semantic search finds similar past situations
- Quality scoring ensures only high-quality memories are used
- Weekly memory compression to maintain efficiency

### 📈 Real-Time Monitoring
- **Streamlit Dashboard**: Modern web interface (https://ai-trader-ollama-smw8trcv4ypnyay7tsx5wy.streamlit.app/)
- **HTML Dashboard**: Classic interface with advanced features
- Live dashboard showing agent discussions
- Portfolio performance tracking
- Trade execution visualization
- Performance analytics with charts

### ⚡ Performance Optimizations
- Trading cycles complete in 6-7 minutes
- Tool result caching reduces redundant API calls
- Intelligent budget management
- Optimized memory usage (99% reduction in file reading)

## Architecture Overview

```
┌─────────────────────────────────────────┐
│         Frontend Dashboard              │
│    (monitor.html - Real-time UI)        │
└──────────────┬──────────────────────────┘
               │ HTTP/REST API
┌──────────────▼──────────────────────────┐
│         Backend API Server               │
│         (FastAPI - Python)              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Multi-Agent Trading System         │
│  ┌──────────────────────────────────┐  │
│  │  Market Analyst                  │  │
│  │  Technical Analyst               │  │
│  │  Fundamental Analyst             │  │
│  │  Sentiment Analyst               │  │
│  │  Discussion Coordinator          │  │
│  │  Risk Analyst                    │  │
│  │  Trader Agent                    │  │
│  └──────────────────────────────────┘  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│         Tool System (28 Tools)          │
│  - Market Data Tools                    │
│  - Technical Analysis Tools              │
│  - Fundamental Analysis Tools           │
│  - Sentiment Analysis Tools             │
│  - RAG Memory Tools                     │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Data Sources & Storage             │
│  - Market Data APIs                     │
│  - News Sources                         │
│  - Portfolio State (JSON)              │
│  - Trade History (JSONL)                │
│  - Agent Conversations (JSONL)         │
│  - RAG Memory Vectors                   │
└─────────────────────────────────────────┘
```

## Use Cases

### 1. Automated Trading
- Run fully autonomous trading cycles
- Execute trades based on agent consensus
- Manage portfolio positions automatically

### 2. Market Analysis
- Get comprehensive analysis of NASDAQ-100 stocks
- View agent discussions and reasoning
- Access detailed tool results and metrics

### 3. Portfolio Management
- Track portfolio performance over time
- View equity history and charts
- Analyze trade performance and statistics

### 4. Research & Learning
- Understand how AI agents analyze markets
- Study trading decision-making processes
- Learn from historical trading patterns

### 5. Strategy Development
- Test different agent configurations
- Experiment with tool combinations
- Analyze performance metrics

## Who Is This For?

- **Traders**: Automated trading system with comprehensive analysis
- **Developers**: Open-source platform for building trading systems
- **Researchers**: Study multi-agent systems and AI decision-making
- **Students**: Learn about AI, trading, and system architecture
- **Investors**: Get AI-powered market analysis and insights

## Technology Stack

- **Backend**: Python 3.10+, FastAPI
- **AI/LLM**: Ollama (deepseek-r1 model)
- **Frontend**: HTML5, JavaScript, Chart.js
- **Data Storage**: JSON/JSONL files, Vector database (RAG)
- **Deployment**: Vercel (backend), GitHub Pages (frontend)

## Key Features Summary

✅ **6 Specialized AI Agents** working collaboratively  
✅ **28 Advanced Analysis Tools** for comprehensive market coverage  
✅ **RAG Memory System** for learning from history  
✅ **Real-Time Dashboard** for live monitoring  
✅ **Automated Trading** with risk management  
✅ **Performance Analytics** with detailed metrics  
✅ **Open Source** and fully customizable  

## Getting Started

1. **Install**: `scripts\install.bat`
2. **Configure**: `scripts\setup_wizard.bat`
3. **Start**: `scripts\quick_start.bat`

See [Quick Start Guide](QUICK_START.md) for detailed instructions.

---

**Last Updated**: 2025-12-11

