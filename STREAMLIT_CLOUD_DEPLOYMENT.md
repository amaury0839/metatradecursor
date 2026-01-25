# 🚀 Streamlit Cloud Deployment Guide

## Prerequisites
- GitHub account (code already pushed)
- Streamlit account (free tier OK)
- (Optional) Local API bot for hybrid mode

## Step 1: Connect to Streamlit Cloud

1. Go to [streamlit.io](https://streamlit.io)
2. Sign up or sign in with GitHub
3. Click **"New app"** button

## Step 2: Deploy from GitHub

1. **Choose repository:**
   - Owner: Select your GitHub account
   - Repository: `metatradecursor`
   - Branch: `main`

2. **Specify file path:**
   - Main file path: `app/main_ui.py`

3. **Click "Deploy"**

## Step 3: Wait for First Deploy

```
Processing... (takes 1-2 minutes)
✓ Building requirements
✓ Installing dependencies  
✓ Starting app

App should load without errors!
```

## Step 4: Configure Secrets (Optional)

If you want **AI features enabled** in cloud:

1. In Streamlit dashboard, click your app
2. Go to **Settings** → **Secrets**
3. Add this line:
   ```toml
   GEMINI_API_KEY = "your-actual-gemini-api-key"
   ```
4. Click **Save**
5. App auto-redeploys

## Step 5: Verify Deployment

### Expected Behavior:

✅ **UI Loads Successfully**
- No error pages
- Dashboard displays

✅ **Demo Mode**
- Connection Status: ✓ Connected
- Mode: DEMO (or your account if MT5 configured)
- Balance: $10,000 (simulated)
- Trading: PAUSED (safe default)

✅ **Optional: Connect Local Bot**

If you have local API bot running:
1. Use ngrok or SSH tunnel to expose port 8000
2. Update UI endpoint in cloud settings
3. Real trading will activate

## Step 6: Test Features

### Check Connection Status
```
On Dashboard Tab:
- Connection Status: Should show ✓ or warning
- Trading Status: PAUSED (safe)
- Account Info: Demo or real account
```

### Check Logs
```
Top-right menu → Manage app → Logs
Look for:
✓ "Config loaded successfully"
✓ "MT5 client initialized"
✓ "App ready"
```

### If Error: "Module not found"
- Check logs
- Likely missing dependency
- Uncomment in requirements.txt if needed

## Common Issues & Fixes

### Issue 1: "No module named 'app'"
**Fix:** Make sure main file path is `app/main_ui.py`

### Issue 2: App crashes with ValidationError
**Fix (Already Done):** Configuration now handles missing `.env`
- Just redeploy

### Issue 3: Slow startup
**Normal:** First deploy takes 1-2 min. After that ~10 seconds.

### Issue 4: MT5 connection shows red
**Expected:** Cloud doesn't have MT5. Shows "Demo Mode" - this is OK!

## Hybrid Mode: Local Bot + Cloud UI

Want real trading while using cloud UI?

### Setup:
```
1. Keep local bot running (API on port 8000)
2. Expose local port via ngrok:
   ngrok http 8000
   → Get URL like: https://abc-123.ngrok.io

3. In Streamlit Cloud app secrets, add:
   TRADING_BOT_URL = "https://abc-123.ngrok.io"

4. App will connect to local bot instead of demo
5. Real trading works in cloud UI!
```

## App Features Available

| Feature | Demo Mode | With Local Bot | With Gemini |
|---------|-----------|----------------|-----------  |
| **Dashboard** | ✓ | ✓ | ✓ |
| **Connection Status** | Simulated | Real | ✓ |
| **Trading Orders** | Simulated | Real | ✓ |
| **Risk Management** | ✓ | ✓ | ✓ |
| **Strategy Analysis** | ✓ | ✓ | ✓ |
| **AI Decisions** | ✗ | ✗ | ✓ |
| **News Feed** | ✓ | ✓ | ✓ |
| **Logs** | ✓ | ✓ | ✓ |

## File Structure for Cloud

```
metatradecursor/ (GitHub repo)
├── app/
│   ├── main_ui.py          ← Cloud runs this
│   ├── core/config.py      ← Now cloud-safe
│   ├── core/logger.py      ← Fallback config
│   ├── api_client/client.py ← Handles connection errors
│   ├── ai/gemini_client.py ← Optional API key
│   ├── trading/mt5_client.py ← Demo mode fallback
│   └── ...
├── requirements.txt        ← All dependencies
└── .streamlit/
    └── config.toml        ← (Create if needed)
```

## Environment Configuration

### Local (.env file - NOT in cloud)
```
MT5_LOGIN=12345678
MT5_PASSWORD=your_password  
MT5_SERVER=ICMarketsInternational-Demo
GEMINI_API_KEY=sk-...
LOG_LEVEL=DEBUG
```

### Cloud (Streamlit Secrets - optional)
```toml
# Only set if you want these features
GEMINI_API_KEY = "sk-..."
TRADING_BOT_URL = "https://your-bot-url.com"  # For hybrid mode
```

## Monitoring Cloud Deployment

### App Health:
- Dashboard page loads ✓
- Shows connection status
- No error messages in logs

### Performance:
- Typical response time: <1 sec
- Dashboard refresh: ~5 sec
- Full app load: ~10 sec on cloud (after first deploy)

### Troubleshooting:
```
Streamlit → App Menu (top right) → Manage App → Logs
```

Look for:
- ✓ No ValidationError
- ✓ "MT5 client initialized"
- ✓ "App running"

If errors: Check logs, note error message, review CLOUD_DEPLOYMENT_FIX.md

## Next Steps After Deploy

1. **Test the UI:**
   - Load app → should see dashboard
   - Click around pages → should work
   - Check logs → should be clean

2. **Optional: Enable Features**
   - Add GEMINI_API_KEY to secrets for AI
   - Connect local bot for real trading

3. **Monitor:**
   - Check logs periodically
   - App auto-redeploys on code push
   - No manual intervention needed

4. **Scale Up:**
   - Streamlit free tier: Good for testing
   - Streamlit Pro: For production use

## Support

If deployment fails:
1. Check logs in Streamlit dashboard
2. Review CLOUD_DEPLOYMENT_FIX.md
3. Verify GitHub code is latest version
4. Check requirements.txt has all dependencies

---

**Current Status:** ✅ Code is cloud-ready and deployed!
