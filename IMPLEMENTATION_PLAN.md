🧠 AI-Trader Implementation Plan (Updated – 2025-10)

Project Path: ai-trader-ollama/
Framework: Python + LangChain + Ollama (Local LLM) + yfinance
Market Universe: NASDAQ-100
Goal: 建立可自我迴圈學習的 AI-Trader Agent System，整合市場、技術、風險與交易決策模組。

🌐 Architecture Overview

yfinance ─► Market Agent (行情整合)
│
├──► Market Analyst (技術面 + 情緒面)
│ ├─ RSI, MACD, BBands
│ ├─ VIX / Fear & Greed / CNN 指數
│ └─ 商業新聞分析 (agent 自行選關鍵字)
│
├──► Risk Analyst (波動度、MDD、倉位上限)
├──► Analysts Discussion (共識收斂 3–5 輪)
│
└──► Trader Agent (最終決策執行)
└─ Trade Log / Portfolio 更新

詳見 ARCHITECTURE.md。

🧩 Stage Summary
Stage	Module	Goal	Status	Key Deliverables
0	LLM / Ollama	LangChain 連接本地模型、啟動檢查	✅ Completed	src/llm/ollama_client.py, scripts/smoke_test.sh
1	Core Foundation	專案骨架、配置、資料層	✅ Completed	config/config.json, run.py, portfolio / trade log
2	Market Agent + TA 指標	產出技術指標、整合行情資料	✅ Completed	ta_indicators.py, market_tools.py
3	Analyst Agents	市場心理學、新聞情緒分析、風控邏輯	⚙️ In Progress	VIX + Fear & Greed + 新聞分析、自主關鍵字選擇
4	Trader Agent	自我決策、動態停損停利	⚙️ In Progress	Decision logic, position sizing, rationale output
5	Performance / Feedback	績效分析、回測報表	⏳ Planned	Sharpe, MDD, win-rate, trade summary dashboard
✅ Current Implementation Details
📘 Stage 0 – LLM / Ollama

get_llm() 封裝支援 temperature / num_ctx / keep_alive

自動檢查 Ollama 未啟動或模型未 pull

驗證：scripts/smoke_test.sh / .ps1 → prints “Ollama OK”

📗 Stage 1 – Core Foundation

專案結構：

src/
  agents/
  data/
  tools/
  orchestrator/
config/config.json
run.py


配置：統一管理 (config.json)

Portfolio / Trade Log：JSONL 格式，追蹤完整交易紀錄

驗證：scripts/validate_changes.py

📙 Stage 2 – Market Agent + TA Indicators

ta_indicators.py：RSI、MACD、BBands（純 pandas 實作）

market_tools.py：

輸出欄位：price, change_pct, volume, ma20, ma50, rsi14, macd, macd_signal, macd_hist, bb_pos, signal_score

NaN-safe 與 rolling min_periods 避免短窗空值

整合 VIX 情緒：

market_data.get_vix() / get_vix_close()

扁平化 yfinance MultiIndex（group_by="column"）

通過測試：test_01_market_batch_vix.py

✅ 指標模組與行情代理皆可用

📒 Stage 3 – Analyst Agents (進行中)

Market Analyst：整合 TA + VIX 情緒

Sentiment Tools

vix_term_structure()：分析 contango/backwardation 結構

修正 pandas FutureWarning（改用 .to_numpy()）

新聞與網頁分析

Agent 自主選擇關鍵字（基於 NASDAQ100 公司名）

以商業新聞 (Reuters, CNBC, Bloomberg) 為主

融合 CNN Fear & Greed Index、CBOE 波動率

風控基礎

波動度、MDD、position limit

停損停利由 agent 自行決定（tool 僅提供計算介面）

驗證：

tests/test_02_discussion_rounds.py → final stance = cautious

✅ Ollama 對話 3 輪收斂正常

📘 Stage 4 – Trader Agent (進行中)

trading_tools.py：buy_stock / sell_stock / portfolio_status

trading_cycle.py：

全流程：Market → Analyst → Discussion → Decision → Record

自動寫入 data/logs/trades.jsonl

Decision Logic：

綜合 TA、情緒、風控 → 最終 BUY / SELL / HOLD

動態倉位 sizing 與自我停損停利

驗證：

[E2E] decision.action = HOLD
rationale = Hold due to VIX risk=4.0 / news stance=cautious
[E2E] OK


✅ End-to-end 流程可執行

📈 Stage 5 – Performance Agent (規劃中)

performance_agent.py 預計整合：

Sharpe、MDD、Hit Rate

回測報表與圖表化 (Matplotlib / Plotly)

Feedback 調整 Trader / Risk Agent 策略

🧪 Testing & Validation

測試架構：tests_with_bootstrap/

_bootstrap.py → 自動修正 sys.path

check_ollama.py → 檢查 Ollama API

run_all.py → 一鍵執行四大測試階段

✅ 測試結果：

Config OK

Market Batch + VIX OK

Analyst Discussion OK

Full Trading Cycle OK

⚙️ Troubleshooting
Issue	Cause	Fix
ModuleNotFoundError: src	測試時未設 PYTHONPATH	已加入 _bootstrap.py
FutureWarning: float(Series)	pandas 2.2+ 行為變更	改用 .to_numpy()[-1]
VIX level = nan	yfinance 暫時取不到 ^VIX	fallback 改抓 3 個月或使用 VIXY
Ollama 無回應	ollama serve 未啟動或模型未 pull	依提示修正 OLLAMA_HOST
🚀 Next Steps

擴充 Analyst 層

加入 CNN Fear & Greed、News Sentiment

自動新聞關鍵字選擇

強化 Trader 決策

Position sizing、multi-asset 配置

自我學習式停損/停利邏輯

建立 Performance Agent

回測指標、報表與 Dashboard

(Optional) 轉換至 LangGraph 狀態機架構
→ 提供 Agent 間互動可視化與狀態追蹤。

📅 Progress Summary (as of 2025-10-31)

Stage 0–2 ✅ Completed

Stage 3–4 ⚙️ In Progress（含 VIX + News 情緒）

Stage 5 ⏳ Planned

全系統測試 ✅ 通過，Ollama 互動正常


以下是你可以直接追加到 IMPLEMENTATION.md 最後一節的新任務紀錄區塊👇
我幫你整理成標準格式（含背景說明、實作目標、預期成果、檔案位置）。

🧩 Upcoming Task – Rolling Discussion Loop (TAO Mechanism)
🎯 Goal

升級 run_analyst_discussion() 為 滾動式推理框架 (Thought → Action → Observation)，
讓每一輪的分析結果與行動觀察都能被下一輪吸收，形成真正的「連續決策代理 (rolling synthesis agent)」。

🧠 Concept

現行版本為「獨立回合」(每輪僅基於初始 market view)。
升級後改為 循環學習架構：

Round 1:
   Thought → Action (e.g. 查 FGI, 查新聞) → Observation → Summary

Round 2:
   引用 Round 1 summary + Observation
   → Re-think → Action (補缺資訊) → Observation → 更新 Summary

Round 3:
   整合過去所有輪次 context → Final synthesis → Final stance

🧱 Implementation Plan
Step	Component	Description
1	src/agents/analyst_discussion.py	建立新函式 run_analyst_discussion_rolling()（保留舊版為 _static()）
2	Thought Phase	每輪開頭加入 Previous summary、Previous observation 文字提示，指導 LLM 延續思考
3	Action Phase	檢查缺失資訊（VIX、FGI、News），透過 ToolBox 自動補足
4	Observation Phase	將工具返回結果整理成文字摘要（headline, index value, etc.）
5	Synthesis Phase	將舊摘要與新觀察一併送入 LLM → 生成新的整合結論
6	Context Memory	儲存每輪的 summary / actions / observation 至 context_memory（list 或 JSONL）
7	Config Switch	支援 config/config.json 新鍵值： "discussion_mode": "rolling" 以切換模式
8	Testing	以 tests/test_02_discussion_rounds.py 改為多輪滾動測試，檢查每輪是否有引用上一輪內容
📁 File Targets

Main logic:
src/agents/analyst_discussion.py

Config toggle:
config/config.json → "discussion_mode": "rolling"

Test case:
tests/test_02_discussion_rounds.py → 檢查 transcript 每輪差異

Optional:
data/logs/discussion_memory.jsonl → 紀錄完整 Thought→Action→Observation 流程

📈 Expected Outcome

每輪 LLM 都能引用前一輪的結論與行動結果（顯示 “Previous summary” 區塊）

最終 final_stance 綜合所有輪次觀察，更接近真實市場決策過程

context_memory 成為後續 Trader 或 Reinforcement 模組的學習資料來源

🗓️ Planned for Next Session

✅ Prepare new rolling discussion loop structure
✅ Implement config toggle (discussion_mode)
🔄 Test iterative refinement with 3–5 rounds
🔄 Save intermediate context logs for later reinforcement learning