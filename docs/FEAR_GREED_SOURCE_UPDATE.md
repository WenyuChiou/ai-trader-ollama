# Fear & Greed Index 數據源更新

## ✅ 新增數據源：feargreedmeter.com

### 為什麼使用這個數據源？

根據測試，[feargreedmeter.com](https://feargreedmeter.com/) 提供了更好的數據可用性：

1. **值提取成功**: ✅ 成功提取到正確的值（例如：35）
2. **日期信息清晰**: ✅ 顯示 "2 days ago" 並能計算實際日期（2025-10-31）
3. **HTML 結構友好**: ✅ 無需執行 JavaScript，HTML 提取即可獲取數據
4. **數據更新及時**: ✅ 顯示最新的指數值和日期信息

### 數據源優先級

工具現在按以下順序嘗試獲取數據：

1. **CNN JSON API** - 如果可用（目前返回 404）
2. **feargreedmeter.com** - ✅ **當前主要數據源**（推薦）
3. **CNN HTML 頁面** - 備用方案

### 當前提取結果

根據測試（2025-11-02）：
- **值**: 35 ✅
- **標籤**: "Fear" ✅
- **日期**: 2025-10-31（2 days ago）✅
- **來源**: "feargreedmeter" ✅

### 日期信息

- **days_ago**: 2（表示數據是 2 天前的）
- **extracted_date**: "2025-10-31"（計算後的實際日期）
- **asof**: "2025-10-31T00:00:00+00:00"（ISO 格式時間戳）

這意味著：
- 如果今天是 2025-11-02
- 指數值 35 是 2025-10-31（2天前）的數據
- 工具會自動計算實際日期

### 工具更新

- ✅ 已添加 `_scrape_feargreedmeter()` 函數
- ✅ 已更新 `fetch_fear_greed()` 優先使用 feargreedmeter.com
- ✅ 已更新 ToolBox 描述
- ✅ 已更新 Sentiment Agent prompt

---

**更新日期**: 2025-11-02  
**數據源**: https://feargreedmeter.com/

