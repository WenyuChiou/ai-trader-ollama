# AI-Trader MVP Implementation Plan (Updated)

## Project Overview
重製 HKUDS/AI-Trader 的簡化版本，使用 **Python + LangChain + Ollama(Local LLM) + yfinance**  
- **目標市場**: 美國股市（預設：NASDAQ 100 可自定義）
- **數據源**: yfinance（OHLCV）
- **架構**: 多 Agent（Market / Analyst / Risk / Trader）＋ Orchestrator 日常交易循環

---

## Architecture Design（簡述）

yfinance ─► Market Agent(數據整合) ─► Market Analyst(技術面/情緒)
Risk Analyst(風控)
└──────────► Analysts Discussion(共識)
└──────────► Trader Agent(決策執行)
└──► Trade Log

markdown
複製程式碼

> 完整架構請見 `ARCHITECTURE.md`。

---

## Stage 0: LLM / Ollama 基礎
**Goal**: 以 LangChain 連接本地 Ollama，並具備啟動錯誤提示  
**Status**: ✅ Completed

### 已完成
- `src/llm/ollama_client.py`：`get_llm()` 封裝（支援 `temperature/num_ctx/keep_alive/auto_pull`）
- 連線檢查與錯誤指引（沒開服務、模型未 pull、.env 未設）

### 驗證
- `scripts/smoke_test.sh/.ps1`：印出 `Ollama OK`

---

## Stage 1: Core Foundation
**Goal**: 專案結構、配置檔與數據層  
**Status**: ✅ Completed

### 已完成
- 專案骨架（`src/agents`, `src/tools`, `src/data`, `src/orchestrator`, `config/`）
- yfinance 封裝：`src/data/market_data.py`（`auto_adjust=False`）
- 投組與交易日誌：`src/data/portfolio.py`, `src/data/trade_log.py`
- 配置：`config/config.json`
- 啟動入口：`run.py`（含 `OllamaInitError` 提示）

### 驗證
- `scripts/validate_changes.py` 顯示檔案時間戳、跑 smoke test、指標與全流程、並檢查 `data/logs/trades.jsonl`

---

## Stage 2: Market Agent + TA 指標
**Goal**: 取得多檔股票資料並計算技術指標，提供清潔結構化輸出  
**Status**: ✅ Completed

### 已完成
- `src/tools/ta_indicators.py`：**純 pandas** RSI / MACD / BBands
- `src/tools/market_tools.py`：
  - 計算 `price/change_pct/volume/ma20/ma50/rsi14/macd/macd_signal/macd_hist/bb_pos/signal_score`
  - **NaN 安全處理**（Series→float、分母 0/NaN 防呆）
  - **MA warmup**：`rolling(..., min_periods=1)`，避免短窗 NaN（可改回嚴格 MA）
- `src/agents/market_analyst.py`：依 `signal_score` 產出推薦與觀察

### 驗證
- `validate_changes.py`：`OK indicators present ...`、全流程可跑通

---

## Stage 3: Analyst Agents（強化中）
**Goal**: 完整市場心理＆風控分析，對話收斂  
**Status**: ⚙️ In Progress

### 已完成
- `src/agents/market_analyst.py`：讀取指標、輸出推薦與觀察
- `src/tools/analysis_tools.py`：基礎風險/波動度 API（持續擴充）

### 待辦
- `src/agents/risk_analyst.py`：波動率/最大回撤/倉位上限邏輯
- `src/agents/analyst_discussion.py`：對話輪次與收斂規則

---

## Stage 4: Trader Agent（決策/執行）
**Goal**: 綜合分析與風控 → 交易決策（BUY/SELL/HOLD）與下單  
**Status**: ⚙️ In Progress

### 已完成
- `src/tools/trading_tools.py`：`buy_stock/sell_stock/portfolio_status`（均加入 docstring）
- `src/orchestrator/trading_cycle.py`：單日流程（抓數據→分析→共識→決策→記錄）已可跑

### 待辦
- 止損/停利、動態倉位（risk 等級對應 position size）
- Trader 決策理由與風控條件輸出更完整

---

## Stage 5: Performance / Feedback
**Goal**: 績效分析（Sharpe、MDD）與回饋調整  
**Status**: ⏳ Planned

### 待辦
- `src/agents/performance_agent.py`、回測、視覺化與報表

---

## Tests（摘要）
- 單元測試：指標/工具/Agent 輸入輸出
- 集成：Orchestrator 跑完整日流程
- 驗證腳本：`scripts/validate_changes.py` 一鍵檢查

---

## Troubleshooting
- **Ollama 初始化失敗**：`ollama serve` → `ollama pull <model>` → 檢 `.env`（`OLLAMA_HOST`/`OLLAMA_MODEL`）
- **MA50 為 NaN**：日期太短；已啟用 `min_periods=1` warmup，如要嚴格 MA50 請改回預設或拉長日期
- **Git non-fast-forward 推不上**：
  - 方式 A（rebase）：
    ```bash
    git fetch origin
    git rebase origin/main
    git push -u origin main
    ```
  - 方式 B（merge）：
    ```bash
    git pull --no-rebase origin main
    git push -u origin main
    ```

---

## Next Steps
1. 補齊 Risk Analyst 與對話收斂邏輯（3 輪以內）
2. Trader 加入止損/停利、動態倉位 sizing
3. Performance Agent 與回測 + 報表
4. （可選）改為 LangGraph 圖式狀態機

# AI-Trader MVP Architecture (Updated)

## 系統架構概覽

本系統採用分層式 **多 Agent + Orchestrator** 架構，並以 **Ollama 本地 LLM** 作為語言與規則推理核心。

yfinance(OHLCV)
│
▼
┌──────────────────┐
│ Market Agent │ ← 數據整合（不做觀點）
│ (tools/market) │
└───────┬──────────┘
│ 結構化 market_json
▼
┌──────────────────┐ ┌──────────────────┐
│ Market Analyst │ │ Risk Analyst │
│ (技術/心理/熱度) │◄───►│ (波動/倉位/風控) │
└───────┬──────────┘ └─────────┬────────┘
│ 共識/分歧 │
└───────────────┬───────────────────┘
▼
┌─────────────┐
│ Trader │ ← 綜合決策與執行
│ Agent │
└─────┬───────┘
▼
Trade Log(JSONL)

markdown
複製程式碼

---

## 關鍵模組與路徑

- **LLM / Ollama**：`src/llm/ollama_client.py`（連線封裝、錯誤提示、`keep_alive/auto_pull`）
- **數據層**：`src/data/market_data.py`（yfinance；`auto_adjust=False`）、`src/data/portfolio.py`、`src/data/trade_log.py`
- **工具層 (Tools)**  
  - `src/tools/ta_indicators.py`：RSI, MACD, BBands（純 pandas）
  - `src/tools/market_tools.py`：多檔抓取＋指標＋`signal_score`
  - `src/tools/analysis_tools.py`：風險/波動基礎工具（擴充中）
  - `src/tools/trading_tools.py`：買賣/資產查詢（均含 docstring）
- **Agents**  
  - `src/agents/market_analyst.py`：基於指標輸出觀察與推薦
  - `src/agents/risk_analyst.py`：風險層評估（開發中）
  - `src/agents/analyst_discussion.py`：對話收斂（開發中）
  - `src/agents/trader_agent.py`：最終決策（已有 MVP；風控擴充中）
- **Orchestrator**：`src/orchestrator/trading_cycle.py`（單日流程）

---

## 資料格式（關鍵 I/O）

### Market Agent 輸出（供分析師使用）
```json
{
  "date": "YYYY-MM-DD",
  "stocks": {
    "AAPL": {
      "price": 188.04,
      "change_pct": 1.29,
      "ma_20": 187.89,
      "ma_50": 186.42,
      "volume": 55859400,
      "rsi14": 62.1,
      "macd": 0.42,
      "macd_signal": 0.33,
      "macd_hist": 0.09,
      "bb_pos": 0.66,
      "signal_score": 2
    },
    "...": {}
  }
}
Market Analyst 輸出
json
複製程式碼
{
  "market_sentiment": "bullish|bearish|neutral",
  "key_observations": ["AAPL: MA20>MA50", "RSI in 55-70 band"],
  "recommended_stocks": ["AAPL", "MSFT"],
  "concerns": ["Avoid overbought if RSI>70"]
}
Risk Analyst 輸出（規劃中）
json
複製程式碼
{
  "overall_risk_level": "low|medium|high",
  "max_position_size": 0.15,
  "risk_warnings": ["Volatility rising"]
}
Trader 決策輸出
json
複製程式碼
{
  "decision": "BUY|SELL|HOLD",
  "execution_status": "success|skipped",
  "reasoning": ["market bullish", "risk medium"],
  "symbol": "AAPL",
  "amount": 10
}
設計要點
1) 職責分離
Market Agent 僅做 數據整合；分析與建議由 Analyst 完成

Trader 擁有最終決策權，並必須寫入推理與風控理由

2) 技術指標計算策略
指標實作於 ta_indicators.py（無 ta-lib 依賴）

market_tools.py 以 NaN/分母為 0/Series-to-float 防呆

均線使用 min_periods=1 warmup，避免短窗 NaN；如需嚴格 MA 可切回預設

3) 推理穩定性
工具/JSON 類任務採 低溫（temperature ≤ 0.3）

keep_alive 降冷啟延遲；缺模型可 auto_pull

4) Orchestrator 流程（單日）
複製程式碼
1) 取數 → 2) 指標 → 3) 分析 → 4) 風險 → 5) 對話 → 6) 決策 → 7) 記錄
測試與驗證
scripts/smoke_test.sh/.ps1：確認 Ollama 正常

scripts/validate_changes.py：

檔案時間戳

Ollama 回應

指標鍵值存在（含 signal_score）

全流程可執行

data/logs/trades.jsonl 產出

Troubleshooting
MA50 為 NaN：視窗太短；已以 min_periods=1 warmup 處理（可切回嚴格 MA）

Git non-fast-forward 推不上：

git fetch origin && git rebase origin/main && git push

或 git pull --no-rebase origin main && git push

Ollama 啟動/模型：

ollama serve → ollama pull <model> → 檢 .env

版本: MVP v0.3.x（Ollama + 指標 + 基本分析 + Orchestrator）
最後更新: 2025-10-30
