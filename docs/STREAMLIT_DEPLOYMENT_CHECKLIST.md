# Streamlit Deployment Checklist

**Streamlit 部署检查清单**

## ✅ Pre-Deployment Checklist

### 1. Streamlit App Configuration ✅
- [x] `streamlit_app.py` exists and is functional
- [x] Updated to use Vercel backend URL (or environment variable)
- [x] `.streamlit/config.toml` created for Streamlit Cloud
- [x] `.streamlit/secrets.toml.example` created as template

### 2. Dependencies ✅
- [x] `streamlit>=1.28.0` in `backend/requirements.txt`
- [x] `plotly>=5.17.0` in `backend/requirements.txt`
- [x] `requests` for API calls
- [x] `pandas` for data processing

### 3. Backend API ✅
- [x] FastAPI backend deployed to Vercel
- [x] Backend URL configured in Streamlit app
- [x] CORS configured to allow Streamlit Cloud domain
- [x] Environment variables set in Vercel

### 4. Streamlit Cloud Configuration
- [ ] Repository pushed to GitHub
- [ ] Streamlit Cloud account created
- [ ] App deployed to Streamlit Cloud
- [ ] Environment variables configured:
  - [ ] `API_BASE_URL` - Vercel backend URL
  - [ ] `ADMIN_SECRET` - (Optional) For executing trades

## 🚀 Deployment Steps

### Step 1: Prepare Repository
```bash
# Ensure all changes are committed
git add streamlit_app.py .streamlit/
git commit -m "feat: Add Streamlit dashboard with Vercel backend support"
git push origin main
```

### Step 2: Deploy Backend to Vercel
1. Follow Vercel deployment guide: `docs/VERCEL_DEPLOYMENT.md`
2. Get your Vercel backend URL (e.g., `https://your-app.vercel.app`)
3. Configure CORS to allow Streamlit Cloud domain

### Step 3: Deploy Streamlit to Streamlit Cloud
1. Visit https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app"
4. Select repository: `WenyuChiou/ai-trader-ollama`
5. Main file: `streamlit_app.py`
6. Python version: 3.11
7. Click "Deploy"

### Step 4: Configure Environment Variables
In Streamlit Cloud settings:
- `API_BASE_URL`: Your Vercel backend URL
- `ADMIN_SECRET`: (Optional) Your admin secret

### Step 5: Update CORS in Vercel
Add Streamlit Cloud domain to `ALLOWED_ORIGINS`:
```
https://your-app.vercel.app,https://your-streamlit-app.streamlit.app
```

## ✅ Post-Deployment Verification

- [ ] Streamlit app loads successfully
- [ ] Backend connection status shows "✅ Backend Connected"
- [ ] Portfolio data displays correctly
- [ ] Equity chart renders
- [ ] Positions table shows data
- [ ] Recent trades display
- [ ] Agent conversations load
- [ ] Execute trade cycle works (if ADMIN_SECRET configured)

## 📋 Configuration Files

### `.streamlit/config.toml`
```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "sans serif"
```

### Environment Variables (Streamlit Cloud)
- `API_BASE_URL`: Backend API URL (Vercel)
- `ADMIN_SECRET`: (Optional) Admin secret for trading

## 🎯 Quick Start

1. **Deploy Backend**: Follow `docs/VERCEL_DEPLOYMENT.md`
2. **Deploy Streamlit**: Follow steps above
3. **Configure**: Set environment variables
4. **Verify**: Check all features work

## 📖 Related Documentation

- [Streamlit Deployment Guide](STREAMLIT_DEPLOYMENT.md)
- [Vercel Deployment Guide](VERCEL_DEPLOYMENT.md)
- [Deployment Options](DEPLOYMENT_OPTIONS.md)

---

**Last Updated**: 2025-12-11

