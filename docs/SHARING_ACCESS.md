# 🌐 分享網站連結指南

## 📋 三種訪問方式

### 1. **本地訪問（僅自己）**
```
http://localhost:8000/docs
http://127.0.0.1:8000/docs
```
- ✅ 最安全
- ❌ 只能自己訪問

---

### 2. **局域網訪問（同一 WiFi/網絡）** ⭐ 推薦

#### 步驟 1：確保 API 使用 `0.0.0.0` 啟動

**重要**：必須使用 `--host 0.0.0.0` 才能讓其他設備訪問！

```powershell
# 正確的啟動方式（允許局域網訪問）
python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000 --reload
```

或使用穩定版腳本（已配置 `0.0.0.0`）：
```powershell
.\scripts\start_api_stable_bypass.ps1
```

#### 步驟 2：查找你的 IP 地址

**Windows PowerShell:**
```powershell
ipconfig | findstr IPv4
```

**或使用：**
```powershell
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -notlike "*Loopback*"}).IPAddress
```

你會看到類似：
```
192.168.1.100
```

#### 步驟 3：分享連結

給同一網絡的人：
```
http://你的IP地址:8000/docs
```

例如：
```
http://192.168.1.100:8000/docs
http://192.168.1.100:8000/api/agents/status
```

#### 步驟 4：啟動前端（如果需要監控面板）

```powershell
cd frontend
python -m http.server 3000 --bind 0.0.0.0
```

然後分享：
```
http://你的IP地址:3000/monitor.html
```

---

### 3. **公網訪問（互聯網）** ⚠️ 需要額外配置

#### 選項 A：使用內網穿透（最簡單）

**使用 ngrok（免費）：**

1. 下載 ngrok: https://ngrok.com/
2. 註冊並獲取 token
3. 啟動 API：
   ```powershell
   python -m uvicorn backend.src.api.server:app --host 0.0.0.0 --port 8000
   ```
4. 在另一個終端運行 ngrok：
   ```bash
   ngrok http 8000
   ```
5. ngrok 會給你一個公網地址，例如：
   ```
   https://abc123.ngrok.io
   ```
6. 分享連結：
   ```
   https://abc123.ngrok.io/docs
   ```

**其他內網穿透工具：**
- **Cloudflare Tunnel** (免費，更穩定)
- **localtunnel** (免費，簡單)
- **serveo** (免費，無需安裝)

#### 選項 B：部署到雲服務器

**推薦平台：**
- **Heroku** (免費層)
- **Railway** (免費層)
- **Render** (免費層)
- **DigitalOcean** (付費，但便宜)
- **AWS EC2** (付費)

部署後會得到類似：
```
https://your-app.herokuapp.com/docs
```

---

## 🔒 安全注意事項

### ⚠️ 重要警告

1. **不要直接暴露到公網**（除非部署到專業服務器）
   - 本地開發環境不適合直接對外開放
   - 可能被惡意攻擊

2. **使用 HTTPS**（公網訪問時）
   - ngrok 自動提供 HTTPS
   - 雲服務器通常也提供 HTTPS

3. **設置防火牆規則**
   - 只允許信任的 IP 訪問
   - 限制端口訪問

4. **API 認證**（如果包含敏感數據）
   - 考慮添加 API Key 驗證
   - 或使用 OAuth 認證

---

## 📝 快速檢查清單

### 局域網分享前確認：

- [ ] API 使用 `--host 0.0.0.0` 啟動
- [ ] 防火牆允許 8000 端口
- [ ] 知道自己的 IP 地址
- [ ] 測試：在同一網絡的另一台設備訪問 `http://你的IP:8000/docs`

### 公網分享前確認：

- [ ] 使用內網穿透工具（ngrok 等）
- [ ] 或部署到雲服務器
- [ ] 確保使用 HTTPS
- [ ] 考慮添加認證機制

---

## 🎯 推薦方案

### 場景 1：給同事/朋友（同一辦公室/家）
→ **使用局域網訪問**（方案 2）

### 場景 2：給遠程用戶（不同網絡）
→ **使用 ngrok 或部署到雲服務器**（方案 3）

### 場景 3：自己測試
→ **使用本地訪問**（方案 1）

---

## 💡 常見問題

### Q: 為什麼別人訪問不了？
A: 檢查：
1. API 是否使用 `--host 0.0.0.0`？
2. 防火牆是否阻止了 8000 端口？
3. IP 地址是否正確？
4. 是否在同一網絡？

### Q: 如何查看當前 API 的 host 設置？
A: 查看啟動命令，應該包含 `--host 0.0.0.0`

### Q: 前端也需要分享嗎？
A: 如果需要監控面板，前端也需要使用 `--bind 0.0.0.0` 啟動

### Q: ngrok 免費版有限制嗎？
A: 有，但對測試足夠：
- 每次重啟會改變 URL
- 有連接數限制
- 有流量限制

---

## 📞 需要幫助？

如果遇到問題，檢查：
1. API 服務器日誌
2. 防火牆設置
3. 網絡連接
4. IP 地址是否正確

