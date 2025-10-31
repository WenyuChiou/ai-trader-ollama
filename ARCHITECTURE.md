# 🏗️ AI-Trader System Architecture (Updated – 2025-10)

> **Project:** `ai-trader-ollama`  
> **Framework:** Python + LangChain + Ollama (Local LLM) + yfinance  
> **Design Philosophy:** 模組化、多-Agent、自我迴圈決策

---

## 🌐 Overview

整體系統以 **多 Agent + Orchestrator** 為核心：

markdown
複製程式碼
             ┌────────────────────────────┐
             │        Orchestrator        │
             │  (trading_cycle.py)        │
             └────────────┬───────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
 Market Agent                        Analyst Layer
(行情蒐集與技術分析) (市場分析 + 情緒 + 風控對話收斂)
│ │
▼ ▼
Risk Analyst ◄────────── Analyst Discussion ─────────► Market Analyst
│ │
└───────────────────► Trader Agent ◄───────────────────┘
│
▼
Portfolio / Trade Log

yaml
複製程式碼

---

## 🧩 Core Components

### 1️⃣ Market Agent – `src/agents/market_agent.py`
**任務：**  
取得多檔股票資料並計算技術指標，建立可供分析的結構化輸出。

**功能模組：**
- `src/data/market_data.py` → yfinance 資料下載（含 VIX）
- `src/tools/ta_indicators.py` → RSI / MACD / BBands
- `src/tools/market_tools.py` → NaN-safe 信號整合、`signal_score`
- 輸出欄位：
price, change_pct, volume, ma20, ma50,
rsi14, macd, macd_signal, macd_hist, bb_pos, signal_score

yaml
複製程式碼
- 內建 VIX 情緒整合與 fallback（近 3 個月或 VIXY）

---

### 2️⃣ Analyst Layer – 市場心理、風控與共識形成
包含三個主要代理：

#### 🧠 Market Analyst (`src/agents/market_analyst.py`)
- 整合 TA 信號 + 情緒面指標 (VIX / Fear & Greed)
- 讀取 `market_tools` 輸出，生成分析摘要
- 呼叫 Ollama 進行語意分析與趨勢判斷

#### ⚠️ Risk Analyst (`src/agents/risk_analyst.py`)
- 分析波動率、最大回撤、倉位上限
- 提供建議的風險等級與最大持倉比率
- 未來版本將整合 Trader Agent 回饋

#### 🗣️ Analyst Discussion (`src/agents/analyst_discussion.py`)
- 多 Agent 對話模擬（Market vs Risk）
- 預設 3–5 輪迴圈收斂（由 Orchestrator 控制）
- 若無共識則由 Trader Agent 採取保守決策（`HOLD`）

---

### 3️⃣ Trader Agent – `src/agents/trader_agent.py`
**任務：**  
整合所有分析輸出，進行最終交易判斷與執行。

**核心邏輯：**
- 綜合技術、情緒、風控 → 決策 BUY / SELL / HOLD
- 自主停損／停利（無固定閾值）
- 動態 position sizing（依 Risk Agent 建議）
- 記錄所有決策與理由到 `data/logs/trades.jsonl`

---

### 4️⃣ Performance Agent – `src/agents/performance_agent.py` (規劃中)
**任務：**  
回測與績效評估，將指標回饋至風控與交易模組。

**預定輸出：**
- Sharpe Ratio、Max Drawdown、Win Rate  
- Portfolio Equity Curve / P&L 可視化報表  
- 將回測結果供 Orchestrator 或 LLM 學習調整策略

---

## 🧮 Supporting Tools

| 模組 | 功能 |
|------|------|
| `ta_indicators.py` | RSI、MACD、BBands |
| `market_tools.py` | 整合行情與技術指標、計算 signal_score |
| `sentiment_tools.py` | VIX term structure、CNN Fear & Greed、新聞情緒 |
| `analysis_tools.py` | 波動度、MDD、風險指標 |
| `trading_tools.py` | 買賣執行、Portfolio 更新 |
| `portfolio.py` / `trade_log.py` | 紀錄持倉與交易 |

---

## ⚙️ Orchestrator – `src/orchestrator/trading_cycle.py`

**主流程（每日循環）**

1. Market Agent → 抓取行情 + 技術指標  
2. Market Analyst → 技術 / 情緒分析  
3. Risk Analyst → 風控與倉位建議  
4. Analyst Discussion → 收斂共識（3 輪）  
5. Trader Agent → 最終決策（BUY/SELL/HOLD）  
6. 更新 Portfolio 與 Trade Log  

> 全流程皆可透過 `run.py` 啟動；結果記錄於 `data/logs/trades.jsonl`。

---

## 🧪 Testing Framework (2025-10 更新)

**目錄：** `tests_with_bootstrap/`

| 測試檔 | 功能 |
|--------|------|
| `test_00_config.py` | 驗證 config.json 結構 |
| `test_01_market_batch_vix.py` | 檢查行情與 VIX 整合 |
| `test_02_discussion_rounds.py` | 測試多 Agent 對話收斂 |
| `test_03_trading_cycle_e2e.py` | 完整 E2E 交易流程 |
| `_bootstrap.py` | 自動設置 PYTHONPATH |
| `check_ollama.py` | 確認 Ollama 服務連線 |
| `run_all.py` | 一鍵執行全部測試 |

**目前結果：**
CONFIG ✅
MARKET + VIX ✅
DISCUSSION ✅ (final stance = cautious)
TRADER ✅ (decision = HOLD)

yaml
複製程式碼

---

## 🔐 Data Flow Summary

| Data Source | Processed By | Output / Usage |
|--------------|--------------|----------------|
| yfinance OHLCV | Market Agent | 技術指標輸入 |
| ^VIX / CNN FGI / News | Market & Sentiment Tools | 市場情緒變數 |
| Analyst Discussion | LLM via Ollama | Consensus stance |
| Trader Agent | Decision Rules + LLM | Action BUY/SELL/HOLD |
| Trade Log / Portfolio | File I/O | 回測與績效 |

---

## 🧠 Agent Autonomy

- **News Keyword Selection**：Agent 可根據 NASDAQ100 成分股與情緒詞，自主決定搜尋主題。  
- **Risk/Reward Handling**：停損、停利與倉位皆由 Trader Agent 動態調整。  
- **Self-Loop**：每回合分析後回寫 Trade Log，作為後續迴圈輸入。  

---

## 🚀 Planned Enhancements

1. **多來源情緒分析**（新聞、社群、Fear & Greed）  
2. **Performance Agent** 回測與報表  
3. **LangGraph 狀態機** 可視化 Agent 互動  
4. **自動關鍵字擴充**（根據市場波動與新聞頻率）  
5. **跨資產擴展**（ETF、期權、加密資產）

---

📅 **Status Summary (2025-10-31)**  
- Core Pipeline ✅ 可執行  
- LLM 整合 ✅ Ollama 互動正常  
- Sentiment & Risk ⚙️ 開發中  
- Backtest Performance ⏳ 規劃中