# AI-Trader MVP Implementation Plan

## Project Overview
重製 HKUDS/AI-Trader 的簡化版本，使用 Python + LangChain + yfinance
- **目標市場**: 美國股市 (NASDAQ 100)
- **數據源**: yfinance
- **架構**: Commander Pattern (Trader Agent 協調多個子 Agents)

## Architecture Design

```
         ┌─────────────────┐
         │   yfinance      │ ◄─── 數據源（最上層）
         │   (Raw Data)    │
         └────────┬────────┘
                  │
                  ↓
         ┌─────────────────┐
         │  Market Agent   │ ◄─── 整合統整股價資訊
         │  (Data Parser)  │      輸出：結構化數據報告
         └────────┬────────┘
                  │
         ┌────────┴────────┐
         ↓                 ↓
    ┌──────────────┐  ┌──────────────┐
    │   Market     │◄─┤     Risk     │
    │   Analyst    │──►   Analyst    │
    │ (市場心理/狀態) │  │  (風險評估)   │
    └──────┬───────┘  └──────┬───────┘
           │                 │
           └────────┬────────┘
                    ↓
             (對話結果匯總)
                    │
                    ↓
             ┌─────────────┐
             │   Trader    │ ◄─── 綜合裁示 + 執行
             │   Agent     │
             └──────┬──────┘
                    │
                    ↓
             ┌─────────────┐
             │  Feedback   │ ◄─── 關鍵循環
             │  Loop       │
             └─────────────┘
```

**關鍵角色分工**：
1. **Market Agent** - 純數據整合，不做分析
2. **Market Analyst** - 分析市場心理、趨勢、當今狀態
3. **Risk Analyst** - 評估風險、提供風控建議
4. **Analysts 對話** - 兩位分析師互相討論，達成共識
5. **Trader Agent** - 綜合分析師意見，最終決策並執行

---

## Stage 1: Core Foundation
**Goal**: 建立基礎數據層和配置系統
**Status**: Not Started

### Tasks
- [ ] 1.1 專案結構初始化
  ```
  ai-trader-mvp/
  ├── src/
  │   ├── agents/
  │   │   ├── market_agent.py        # 數據整合
  │   │   ├── market_analyst.py      # 市場分析師
  │   │   ├── risk_analyst.py        # 風險分析師
  │   │   ├── trader_agent.py        # 決策執行者
  │   │   └── analyst_discussion.py  # 分析師對話管理
  │   ├── tools/                     # LangChain tools
  │   │   ├── market_tools.py        # yfinance wrapper
  │   │   ├── analysis_tools.py      # 技術/風險分析
  │   │   └── trading_tools.py       # 交易執行
  │   ├── data/                      # Data management
  │   │   ├── market_data.py         # 數據獲取
  │   │   ├── portfolio.py           # 投資組合
  │   │   └── trade_log.py           # 交易記錄
  │   ├── orchestrator/              # 流程協調
  │   │   └── trading_cycle.py       # 完整交易循環
  │   └── utils/                     # Utilities
  ├── tests/                         # Test files
  ├── config/                        # Configuration
  ├── data/                          # Data storage
  │   └── logs/                      # Trading logs
  └── requirements.txt
  ```

- [ ] 1.2 環境配置
  - Python 3.8+ 虛擬環境
  - requirements.txt (langchain, yfinance, python-dotenv, pandas, numpy)
  - .env.example 和 .env 配置檔

- [ ] 1.3 yfinance 數據層
  - `src/data/market_data.py` - 獲取股票數據
  - `src/data/portfolio.py` - 投資組合管理
  - 測試: 驗證能正確獲取 AAPL 歷史數據

- [ ] 1.4 配置系統
  - `config/config.json` - 交易規則配置
  - 初始資金: $10,000
  - 交易範圍: NASDAQ 100
  - 日期範圍設定

### Success Criteria
- [x] 專案目錄結構完整
- [x] 能夠從 yfinance 獲取實時/歷史股票數據
- [x] 配置檔可正確載入
- [x] 所有測試通過

### Tests
```python
# test_market_data.py
def test_fetch_stock_data():
    data = get_stock_price("AAPL", "2024-01-01", "2024-01-31")
    assert data is not None
    assert "Close" in data.columns
```

---

## Stage 2: Market Agent (數據整合者)
**Goal**: 實現股價數據整合與格式化 Agent
**Status**: Not Started

### Tasks
- [ ] 2.1 Market Data Tool
  - `src/tools/market_tools.py` - LangChain Tool wrapper
  - 功能: 
    - 獲取多支股票數據（NASDAQ 100）
    - 計算基本技術指標（MA, Volume, Price Change）
    - 格式化為統一結構
  - 使用 @tool 裝飾器

- [ ] 2.2 Market Agent
  - `src/agents/market_agent.py` 
  - **任務**: 純數據整合，不做分析或建議
  - **輸入**: 股票代碼列表、日期範圍
  - **輸出**: 結構化市場數據報告
    ```json
    {
      "date": "2024-01-15",
      "stocks": [
        {
          "symbol": "AAPL",
          "price": 185.5,
          "change_pct": 2.3,
          "volume": 50000000,
          "ma_20": 182.1,
          "ma_50": 178.9
        }
      ]
    }
    ```
  - Prompt: "You are a data specialist. Your only job is to gather and format market data clearly."

- [ ] 2.3 測試數據完整性
  - 測試能否獲取多支股票
  - 測試數據格式一致性
  - 測試錯誤處理（無效股票代碼）

### Success Criteria
- [x] Market Agent 返回結構化、乾淨的數據
- [x] **不包含任何分析或建議**
- [x] 數據格式標準化且易於後續分析師使用
- [x] 錯誤處理完善

### Tests
```python
# test_market_agent.py
def test_market_data_integration():
    agent = MarketAgent()
    result = agent.fetch_data(["AAPL", "MSFT"], "2024-01-15")
    assert len(result["stocks"]) == 2
    assert "price" in result["stocks"][0]
    assert "analysis" not in result  # 確保沒有分析內容
```

---

## Stage 3: Analyst Agents (分析師對話)
**Goal**: 實現兩位分析師 Agent，並讓他們互相討論
**Status**: Not Started

### Tasks
- [ ] 3.1 Analysis Tools
  - `src/tools/analysis_tools.py`
  - 技術分析工具（RSI, MACD, Bollinger Bands）
  - 情緒分析工具（Volume 分析、價格動能）
  - 風險計算工具（波動率、Beta、夏普比率）

- [ ] 3.2 Market Analyst Agent
  - `src/agents/market_analyst.py`
  - **專長**: 市場心理、趨勢分析、技術面
  - **輸入**: Market Agent 的數據報告
  - **輸出**: 市場狀態分析
    ```json
    {
      "market_sentiment": "bullish/bearish/neutral",
      "key_observations": ["觀察1", "觀察2"],
      "recommended_stocks": ["AAPL", "MSFT"],
      "concerns": ["風險點1"]
    }
    ```
  - Prompt: "You are a market psychology expert. Analyze market trends and sentiment."

- [ ] 3.3 Risk Analyst Agent
  - `src/agents/risk_analyst.py`
  - **專長**: 風險評估、資金管理、風控
  - **輸入**: Market Agent 數據 + Market Analyst 觀點
  - **輸出**: 風險評估報告
    ```json
    {
      "risk_level": "high/medium/low",
      "max_position_size": 0.2,
      "stop_loss_advice": "5%",
      "concerns": ["高波動警告"],
      "safe_stocks": ["MSFT"]
    }
    ```
  - Prompt: "You are a risk management specialist. Evaluate risks and provide controls."

- [ ] 3.4 **Multi-Agent Conversation**
  - `src/agents/analyst_discussion.py`
  - 使用 LangChain 的 multi-agent conversation
  - **對話流程**:
    1. Market Analyst 先分析
    2. Risk Analyst 回應並提出風險考量
    3. Market Analyst 根據風險調整建議
    4. 達成共識或記錄分歧
  - 最多 3 輪對話

- [ ] 3.5 測試分析品質
  - 測試 Market Analyst 能識別趨勢
  - 測試 Risk Analyst 能識別風險
  - 測試兩者對話能收斂到合理結論

### Success Criteria
- [x] Market Analyst 能給出市場狀態分析
- [x] Risk Analyst 能給出風險評估
- [x] **兩位分析師能進行有意義的對話**
- [x] 對話結果影響最終建議
- [x] 輸出格式標準化

### Tests
```python
# test_analyst_discussion.py
def test_analysts_conversation():
    market_data = {...}  # Mock data
    discussion = AnalystDiscussion()
    result = discussion.run(market_data)
    
    assert "market_analysis" in result
    assert "risk_analysis" in result
    assert "conversation_log" in result
    assert len(result["conversation_log"]) > 0
```

---

## Stage 4: Trader Agent (決策執行者)
**Goal**: 實現交易員 Agent，綜合分析師意見並執行
**Status**: Not Started

### Tasks
- [ ] 4.1 Trading Tool 實現
  - `src/tools/trading_tools.py`
  - buy_stock(symbol, amount, price)
  - sell_stock(symbol, amount, price)
  - get_portfolio_status()
  - calculate_position_size(risk_level, capital)

- [ ] 4.2 Trader Agent
  - `src/agents/trader_agent.py`
  - **職責**: 最終決策者和執行者
  - **輸入**: 
    - Market Agent 的數據報告
    - Market Analyst 的分析
    - Risk Analyst 的風控建議
    - 分析師對話記錄
    - 當前投資組合狀態
  
  - **決策流程**:
    1. 審查 Market Agent 數據
    2. 審查兩位分析師的對話結果
    3. 權衡市場機會 vs 風險控制
    4. 做出最終決策（BUY/SELL/HOLD）
    5. 確定交易數量（根據風險建議）
    6. 執行交易
    7. 記錄決策理由

  - **輸出**: 交易決策 + 執行結果
    ```json
    {
      "decision": "BUY",
      "symbol": "AAPL",
      "amount": 10,
      "price": 185.5,
      "reasoning": "市場分析師看好趨勢，風險分析師確認風險可控",
      "risk_considerations": "設定 5% 止損",
      "execution_status": "success"
    }
    ```

- [ ] 4.3 完整交易循環
  - `src/orchestrator/trading_cycle.py`
  - **每日交易流程**:
    ```python
    1. Market Agent 獲取數據
    2. Market Analyst 分析
    3. Risk Analyst 評估
    4. 兩位分析師對話
    5. Trader Agent 決策
    6. 執行交易
    7. 記錄結果
    ```

- [ ] 4.4 交易記錄系統
  - `src/data/trade_log.py`
  - JSONL 格式（參考 AI-Trader）
  - 記錄完整決策鏈:
    - 市場數據快照
    - 分析師對話記錄
    - Trader 決策理由
    - 執行結果
    - 投資組合變化

- [ ] 4.5 錯誤處理
  - 交易失敗重試機制
  - 分析師意見衝突處理
  - 資金不足處理
  - 市場數據異常處理

### Success Criteria
- [x] Trader Agent 能綜合所有輸入做出決策
- [x] 決策有清晰的推理鏈（可追溯）
- [x] 能正確執行 BUY/SELL/HOLD
- [x] 完整的交易循環能順暢運行
- [x] 交易記錄完整且格式正確
- [x] 所有測試通過

### Tests
```python
# test_trader_agent.py
def test_trader_decision_making():
    market_data = {...}
    analyst_discussion = {...}
    portfolio = {...}
    
    trader = TraderAgent()
    decision = trader.make_decision(
        market_data, 
        analyst_discussion, 
        portfolio
    )
    
    assert decision["decision"] in ["BUY", "SELL", "HOLD"]
    assert "reasoning" in decision
    assert "risk_considerations" in decision

def test_full_trading_cycle():
    cycle = TradingCycle()
    result = cycle.execute_daily_trade("2024-01-15")
    
    assert "market_data" in result
    assert "analyst_discussion" in result
    assert "trader_decision" in result
    assert result["execution_status"] == "success"
```

---

## Stage 5: Feedback Loop (反饋循環)
**Goal**: 實現績效評估和策略調整
**Status**: Not Started

### Tasks
- [ ] 5.1 Performance Agent
  - `src/agents/performance_agent.py`
  - 計算: 總回報率、夏普比率、最大回撤
  - 分析: 勝率、平均盈虧
  - 建議: 策略調整方向

- [ ] 5.2 Feedback Mechanism
  - 將績效結果回饋給 Trader Agent
  - 調整 Advisor 的風險偏好
  - 動態調整倉位大小

- [ ] 5.3 回測系統
  - `src/backtest/engine.py`
  - 支援日期範圍回測
  - 生成績效報告
  - 視覺化結果（可選）

- [ ] 5.4 完整測試
  - 端到端測試: 完整交易週期 (30天)
  - 驗證反饋循環有效性
  - 壓力測試: 市場異常情況

### Success Criteria
- [x] Performance Agent 能計算所有關鍵指標
- [x] Feedback Loop 能影響後續交易決策
- [x] 回測系統能運行完整時間範圍
- [x] 生成可讀的績效報告

### Tests
```python
# test_feedback_loop.py
def test_full_trading_cycle():
    system = TradingSystem()
    results = system.run_backtest("2024-01-01", "2024-01-31")
    assert results["total_return"] is not None
    assert results["sharpe_ratio"] is not None
    assert len(results["trades"]) > 0
```

---

## Technical Standards

### Code Quality Checklist
- [ ] 所有函數有 docstring
- [ ] 遵循 PEP 8
- [ ] 使用 type hints
- [ ] 錯誤處理完善
- [ ] 測試覆蓋率 > 80%

### Commit Message Format
```
[Stage X] Brief description

- Detailed change 1
- Detailed change 2

Tests: All passing
```

### When Stuck (3 次嘗試原則)
1. **第 1 次失敗**: 檢查文檔和錯誤訊息
2. **第 2 次失敗**: 查看 AI-Trader 源碼參考
3. **第 3 次失敗**: **STOP** - 記錄問題，尋找替代方案

---

## Definition of Done (整體專案)
- [ ] 所有 5 個 Stages 完成
- [ ] 能運行完整 30 天回測
- [ ] 交易決策有明確理由
- [ ] Feedback Loop 可觀察到效果
- [ ] 所有測試通過
- [ ] README.md 包含使用說明
- [ ] 刪除此 IMPLEMENTATION_PLAN.md

---

## Next Steps
1. 確認此計劃符合需求
2. 開始 Stage 1 實現
3. 每完成一個 Stage，更新 Status 為 "Complete"
4. 遇到問題立即記錄在對應 Stage 下方

**準備好開始了嗎？** 請確認此計劃，我們將開始 Stage 1！
