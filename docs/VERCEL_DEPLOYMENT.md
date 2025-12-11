# Vercel Deployment Guide

## Overview

This guide explains how to deploy the AI-Trader backend API to Vercel.

## Prerequisites

- Vercel account (sign up at https://vercel.com)
- GitHub repository connected to Vercel
- Python 3.11+ (for local testing)

## Deployment Steps

### 1. Connect Repository to Vercel

1. Visit [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import your GitHub repository: `WenyuChiou/ai-trader-ollama`
4. Vercel will automatically detect the Python project

### 2. Configure Build Settings

Vercel will use the `vercel.json` configuration file:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "backend/src/api/server.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "backend/src/api/server.py"
    }
  ],
  "env": {
    "PYTHON_VERSION": "3.11"
  }
}
```

**Build Settings** (in Vercel dashboard):
- **Framework Preset**: Other
- **Root Directory**: `backend` (or leave empty if using vercel.json)
- **Build Command**: (auto-detected)
- **Output Directory**: (auto-detected)
- **Install Command**: `pip install -r requirements.txt`

### 3. Environment Variables

Configure the following environment variables in Vercel dashboard:

**Required:**
- `ADMIN_SECRET`: Your admin API key (generate a secure random string)
- `ENVIRONMENT`: Set to `production`
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins (e.g., `https://wenyuchiou.github.io`)

**Optional:**
- `FRED_API_KEY`: FRED API key for economic data
- `LOG_LEVEL`: Logging level (default: `INFO`)
- `OLLAMA_BASE_URL`: Ollama server URL (if using remote instance)

**How to Set:**
1. Go to Project → Settings → Environment Variables
2. Add each variable for Production environment
3. Click "Save"

### 4. Deploy

1. Push changes to `main` branch (Vercel auto-deploys)
2. Or manually trigger deployment from Vercel dashboard
3. Wait for build to complete (typically 2-5 minutes)

### 5. Get Deployment URL

After deployment:
1. Go to Project → Deployments
2. Copy the deployment URL (e.g., `https://ai-trader-ollama.vercel.app`)
3. Update frontend `config.js` with the new URL

### 6. Update Frontend Configuration

Edit `frontend/config.js`:

```javascript
const config = {
  development: 'http://localhost:8000',
  production: 'https://your-app.vercel.app',  // Update this
};
```

Commit and push to GitHub Pages.

## Environment Variables Reference

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `ADMIN_SECRET` | Yes | Admin API key for protected endpoints | `your-secure-random-string` |
| `ENVIRONMENT` | Yes | Environment mode | `production` |
| `ALLOWED_ORIGINS` | Yes | Allowed CORS origins | `https://wenyuchiou.github.io` |
| `FRED_API_KEY` | No | FRED API key | `your-fred-key` |
| `LOG_LEVEL` | No | Logging level | `INFO` |
| `OLLAMA_BASE_URL` | No | Remote Ollama URL | `http://your-ollama:11434` |

## Security Configuration

### Production Mode

When `ENVIRONMENT=production`:
- ✅ Admin API Key authentication required for protected endpoints
- ✅ CORS restricted to `ALLOWED_ORIGINS`
- ✅ Rate limiting enabled
- ✅ Error tracebacks hidden from clients

### Protected Endpoints

The following endpoints require `x-admin-secret` header or `Authorization: Bearer <token>`:

- `POST /api/trading/execute-trade`
- `POST /api/trading/check-pending-orders`
- `POST /api/system/init`
- `POST /api/portfolio/record-equity`

**Example Request:**
```bash
curl -X POST https://your-app.vercel.app/api/trading/execute-trade \
  -H "x-admin-secret: your-admin-secret" \
  -H "Content-Type: application/json"
```

## Rate Limits

- **Trading APIs**: 3 requests/minute per IP
- **Analysis APIs**: 10 requests/minute per IP
- **Other APIs**: 30 requests/minute per IP

## Troubleshooting

### Build Fails

**Issue**: Build fails with Python errors

**Solution**:
1. Check `requirements.txt` includes all dependencies
2. Verify Python version is 3.11+
3. Check build logs in Vercel dashboard

### API Not Responding

**Issue**: 502 Bad Gateway or timeout

**Solution**:
1. Verify environment variables are set correctly
2. Check function logs in Vercel dashboard
3. Ensure `ADMIN_SECRET` is set (required in production)

### CORS Errors

**Issue**: Frontend cannot connect to API

**Solution**:
1. Verify `ALLOWED_ORIGINS` includes your frontend domain
2. Check `ENVIRONMENT` is set to `production`
3. Ensure frontend URL matches exactly (including protocol)

### Rate Limit Errors

**Issue**: 429 Too Many Requests

**Solution**:
- Wait for rate limit window to reset
- Reduce request frequency
- Consider implementing request queuing on frontend

## Migration from Railway

If migrating from Railway:

1. **Export Environment Variables** from Railway dashboard
2. **Import to Vercel** (Project → Settings → Environment Variables)
3. **Update Frontend** `config.js` with new Vercel URL
4. **Test Deployment** before disabling Railway

## Cost Comparison

**Vercel Free Tier**:
- ✅ Unlimited deployments
- ✅ 100GB bandwidth/month
- ✅ Serverless functions (generous free tier)
- ✅ Automatic HTTPS
- ✅ Global CDN

**Railway Free Tier**:
- $5/month credit
- Pay-as-you-go pricing

**Recommendation**: Vercel free tier is more generous for API deployments.

## See Also

- [Vercel Documentation](https://vercel.com/docs)
- [Python Runtime](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)

