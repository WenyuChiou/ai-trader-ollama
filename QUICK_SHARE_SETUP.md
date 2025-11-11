# 🚀 快速分享設置指南

## ✅ 已完成設置

你的系統已經配置好，可以分享給其他人了！

## 📋 你的分享連結

**你的 IP 地址：`192.168.4.24`**

### 給其他人分享這些連結：

1. **API 文檔（最常用）**
   ```
   http://192.168.4.24:8000/docs
   ```

2. **API 狀態檢查**
   ```
   http://192.168.4.24:8000/api/agents/status
   ```

3. **投資組合狀態**
   ```
   http://192.168.4.24:8000/api/portfolio/real-time
   ```

4. **前端監控面板**（如果啟動了前端）
   ```
   http://192.168.4.24:3000/monitor.html
   ```

---

## 🎯 快速啟動步驟

### 1. 啟動 API 服務器

```powershell
.\scripts\start_api_stable_bypass.ps1
```

**重要**：這個腳本已經配置為 `--host 0.0.0.0`，允許外部訪問。

### 2. 啟動前端（可選）

如果需要分享監控面板：

```powershell
.\scripts\start_frontend_share.ps1
```

### 3. 查看分享連結

隨時查看你的分享連結：

```powershell
.\scripts\get_share_link.ps1
```

---

## 🔥 防火牆設置

### Windows 防火牆可能阻止訪問

如果別人無法訪問，需要允許端口 8000：

**方法 1：使用 PowerShell（管理員權限）**
```powershell
New-NetFirewallRule -DisplayName "AI Trader API" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

**方法 2：使用圖形界面**
1. 打開「Windows Defender 防火牆」
2. 點擊「進階設定」
3. 選擇「輸入規則」→「新增規則」
4. 選擇「連接埠」→ TCP → 特定本機連接埠：8000
5. 允許連線
6. 套用到所有設定檔
7. 名稱：AI Trader API

---

## ✅ 驗證設置

### 檢查 API 是否運行

```powershell
# 檢查端口是否在使用
netstat -ano | findstr 8000
```

### 測試本地訪問

在瀏覽器打開：
```
http://127.0.0.1:8000/docs
```

### 測試分享連結

在**同一網絡的另一台設備**打開：
```
http://192.168.4.24:8000/docs
```

---

## 📱 給別人的使用說明

### 給同事/朋友（同一網絡）

1. 確保他們連接到**同一個 WiFi/網絡**
2. 分享連結：`http://192.168.4.24:8000/docs`
3. 他們在瀏覽器打開即可

### 如果無法訪問

1. 檢查是否在同一網絡
2. 檢查你的 API 是否正在運行
3. 檢查防火牆設置
4. 確認 IP 地址是否正確（運行 `.\scripts\get_share_link.ps1` 查看）

---

## 🌐 如果需要互聯網訪問

### 使用 ngrok（最簡單）

1. 下載 ngrok: https://ngrok.com/
2. 註冊並獲取 token
3. 啟動 API（確保使用 `0.0.0.0`）
4. 運行 ngrok：
   ```bash
   ngrok http 8000
   ```
5. ngrok 會給你一個公網地址，例如：
   ```
   https://abc123.ngrok.io
   ```
6. 分享這個連結給任何人

---

## 📝 常用命令

```powershell
# 查看分享連結
.\scripts\get_share_link.ps1

# 啟動 API（穩定版，自動重啟）
.\scripts\start_api_stable_bypass.ps1

# 啟動前端（可分享）
.\scripts\start_frontend_share.ps1

# 查看 IP 地址
ipconfig | findstr IPv4
```

---

## ⚠️ 注意事項

1. **安全**：只分享給信任的人
2. **網絡**：確保在同一網絡（WiFi/LAN）
3. **防火牆**：可能需要允許端口 8000
4. **IP 變化**：如果 IP 地址改變，重新運行 `get_share_link.ps1` 獲取新連結

---

## 🎉 完成！

現在你可以：
- ✅ 分享 API 文檔給其他人
- ✅ 讓他們查看投資組合狀態
- ✅ 展示監控面板

**主要分享連結：**
```
http://192.168.4.24:8000/docs
```

