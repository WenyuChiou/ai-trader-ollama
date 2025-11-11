# 🔄 API 重啟指南

## 🚀 最簡單的方法（推薦）

### 一鍵重啟

```powershell
.\scripts\restart_api_simple.ps1
```

如果遇到執行政策錯誤：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_simple.ps1
```

**這個腳本會：**
- ✅ 自動停止舊的 API 進程
- ✅ 等待端口釋放
- ✅ 自動啟動新的 API
- ✅ 在新窗口顯示日誌

---

## 📝 手動重啟步驟

### 步驟 1：停止舊的 API

**方法 A：使用 PowerShell**
```powershell
# 查找佔用 8000 端口的進程
netstat -ano | findstr 8000

# 停止進程（替換 <PID> 為實際的進程 ID）
taskkill /PID <PID> /F
```

**方法 B：使用 PowerShell 命令**
```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | 
    Select-Object -ExpandProperty OwningProcess | 
    ForEach-Object { Stop-Process -Id $_ -Force }
```

**方法 C：直接關閉 API 窗口**
- 如果 API 在 PowerShell 窗口運行，直接按 `Ctrl+C` 或關閉窗口

### 步驟 2：啟動新的 API

**方法 A：使用穩定版腳本（推薦）**
```powershell
.\scripts\start_api_stable_bypass.ps1
```

**方法 B：手動啟動**
```powershell
# 1. 進入專案目錄
cd "C:\Users\wenyu\Desktop\investment\LLM AI trader\ai-trader-ollama"

# 2. 啟用虛擬環境
.\.venv\Scripts\Activate.ps1

# 3. 啟動 API
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

---

## 🎯 快速檢查

### 檢查 API 是否運行

```powershell
# 檢查端口
netstat -ano | findstr 8000

# 測試 API
curl http://127.0.0.1:8000/api/agents/status
```

### 查看分享連結

```powershell
.\scripts\get_share_link.ps1
```

---

## 📋 常用命令對照表

| 操作 | 命令 |
|------|------|
| **一鍵重啟** | `.\scripts\restart_api_simple.ps1` |
| **穩定啟動** | `.\scripts\start_api_stable_bypass.ps1` |
| **查看連結** | `.\scripts\get_share_link.ps1` |
| **停止進程** | `Get-NetTCPConnection -LocalPort 8000 \| Select-Object -ExpandProperty OwningProcess \| ForEach-Object { Stop-Process -Id $_ -Force }` |
| **檢查端口** | `netstat -ano \| findstr 8000` |

---

## ⚠️ 常見問題

### Q: 端口被佔用，無法啟動
A: 先停止舊進程：
```powershell
Get-NetTCPConnection -LocalPort 8000 | Select-Object -ExpandProperty OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force }
```

### Q: 執行政策錯誤
A: 使用 bypass 參數：
```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\restart_api_simple.ps1
```

### Q: 如何確認 API 已啟動？
A: 檢查端口或測試 API：
```powershell
netstat -ano | findstr "0.0.0.0:8000"
# 應該看到 LISTENING 狀態
```

---

## 💡 提示

1. **最簡單**：使用 `restart_api_simple.ps1` 一鍵重啟
2. **最穩定**：使用 `start_api_stable_bypass.ps1` 啟動（帶自動重啟）
3. **查看日誌**：API 會在新窗口顯示，可以查看運行狀態
4. **分享連結**：重啟後運行 `get_share_link.ps1` 獲取最新連結

