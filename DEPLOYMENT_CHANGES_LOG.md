# SME Costing Copilot - Complete Deployment Documentation
## Created: February 28, 2026
## Purpose: Track all changes made during deployment for debugging reference

---

## 🌐 LIVE DEPLOYMENTS

### Frontend (Vercel)
- **Primary URL**: https://sme-costing-copilot-frontend.vercel.app
- **Alias**: https://sme-costing-copilot-frontend-3wy5n5q29.vercel.app
- **Dashboard**: https://sme-costing-copilot-frontend.vercel.app/dashboard/

### Backend (Railway)
- **API URL**: https://sme-costing-copilot-production.up.railway.app
- **Health Check**: https://sme-costing-copilot-production.up.railway.app/health
- **API Docs**: https://sme-costing-copilot-production.up.railway.app/docs

### Database
- **Type**: PostgreSQL (Railway managed)
- **Connection**: Via Railway internal network
- **Status**: Auto-backup enabled

---

## 🔧 ALL CHANGES MADE - CHRONOLOGICAL ORDER

### CHANGE #1: Add Missing Dependencies
**File**: `Backend/requirements.txt`
**Change**: Added `requests==2.31.0`
**Reason**: Fixed `ModuleNotFoundError: No module named 'requests'`
**When**: First Railway deployment attempt failed

```
# Line added:
requests==2.31.0
```

---

### CHANGE #2: Backend-Only Dockerfile
**File**: `Dockerfile.backend` (NEW FILE)
**Purpose**: Simplified Docker build for Railway deployment
**Key Features**:
- Uses Python 3.11-slim
- Installs all dependencies from requirements.txt
- Sets PYTHONPATH correctly
- Dynamic port handling ($PORT environment variable)
- Health check endpoint

**When**: Initial deployment setup

---

### CHANGE #3: Railway Configuration
**File**: `railway.toml`
**Changes**:
- Builder: DOCKERFILE
- Dockerfile path: Dockerfile.backend
- Health check: /health
- Environment variables: PORT, DATABASE_URL, SECRET_KEY, etc.

**When**: Railway deployment configuration

---

### CHANGE #4: Fix Database Configuration
**File**: `Backend/app/core/database.py`
**Changes**:
- Uses environment variable DATABASE_URL
- Fallback to SQLite for local development
- Removed hardcoded Windows paths

**When**: Database connection issues

---

### CHANGE #5: Security Middleware
**File**: `Backend/app/middleware/security.py` (NEW FILE)
**Features**:
- Rate limiting (100 requests/minute)
- Security headers (XSS, CSRF protection)
- Request logging
- Trusted host validation

**When**: Security hardening

---

### CHANGE #6: Main.py Security Integration
**File**: `Backend/app/main.py`
**Changes**:
- Added security middleware import
- Added CORS configuration
- Added database startup event
- Added logging configuration

---

### CHANGE #7: Frontend Next.js Config
**File**: `frontend/next.config.mjs`
**Changes**:
- output: 'export' for static generation
- Security headers configuration
- Image optimization disabled for static export

---

### CHANGE #8: Vercel Configuration
**File**: `frontend/vercel.json` (NEW FILE)
**Features**:
- API proxy to Railway backend
- Security headers
- Environment variables

---

### CHANGE #9: URGENT CORS FIX
**File**: `Backend/app/main.py`
**Critical Change**:
```python
# FROM:
allow_origins=origins  # Specific domains

# TO:
allow_origins=["*"]  # Allow all (temporary for debugging)
```
**Reason**: Frontend couldn't connect to backend
**Status**: Still active - should restrict for production

---

### CHANGE #10: Vercel Environment Variable
**Set via**: `vercel env add`
**Variable**: `NEXT_PUBLIC_API_URL`
**Value**: `https://sme-costing-copilot-production.up.railway.app`
**Reason**: Frontend didn't know where to send API requests
**Status**: ✅ Active

---

### CHANGE #11: Dashboard Error Handling
**File**: `frontend/src/app/dashboard/page.js`
**Changes**:
- Added loading state
- Added error state
- Added null checks for user data
- Added null checks for clients data
- Better error messages

**When**: Client-side exception on dashboard

---

## 🔑 ENVIRONMENT VARIABLES & API KEYS

### Backend (Railway) - SET
```
DATABASE_URL=postgresql://postgres:XXXX@shinkansen.proxy.rlwy.net:43126/railway
SECRET_KEY=your-super-secret-key-change-this-in-production-2024
PORT=8000
PYTHON_VERSION=3.11
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Backend - NOT SET (Optional)
```
OPENAI_API_KEY=    # Required for AI assistant features
```

### Frontend (Vercel) - SET
```
NEXT_PUBLIC_API_URL=https://sme-costing-copilot-production.up.railway.app
```

### Frontend - NOT SET (Optional)
```
NEXT_PUBLIC_OPENAI_KEY=    # If using client-side AI features
```

---

## 🐛 COMMON ERRORS & DEBUGGING GUIDE

### ERROR #1: "Failed to fetch" on Registration/Login
**Symptom**: Red error box saying "Failed to fetch"
**Cause**: CORS issue or API URL not set
**Files to Check**:
1. `Backend/app/main.py` - Check CORS `allow_origins`
2. Vercel env vars - Check `NEXT_PUBLIC_API_URL` is set

**Fix**:
```bash
# Check if env var is set
vercel env ls

# If not set, add it
echo "https://sme-costing-copilot-production.up.railway.app" | vercel env add NEXT_PUBLIC_API_URL production

# Redeploy frontend
vercel --prod
```

---

### ERROR #2: "Application error: a client-side exception"
**Symptom**: White screen with error message on dashboard
**Cause**: JavaScript error in React component
**Files to Check**:
1. `frontend/src/app/dashboard/page.js`
2. Browser console (F12 → Console)

**Common Causes**:
- Accessing property of null/undefined object
- Missing data from API response
- Token not in localStorage

**Fix**:
- Add null checks: `user?.name || 'User'`
- Add loading states
- Check localStorage has token

---

### ERROR #3: "ModuleNotFoundError: No module named 'xxx'"
**Symptom**: Backend fails to start
**Cause**: Missing Python dependency
**File to Check**: `Backend/requirements.txt`

**Fix**:
```bash
# Add missing package
echo "package-name==version" >> Backend/requirements.txt

# Commit and redeploy
git add . && git commit -m "Add missing dependency" && git push && railway up
```

---

### ERROR #4: "Health check failed"
**Symptom**: Railway deployment fails
**Cause**: Backend not responding on /health
**Files to Check**:
1. `Backend/app/main.py` - Check health endpoint exists
2. `railway.toml` - Check healthcheckPath

---

### ERROR #5: Database Connection Error
**Symptom**: Backend starts but can't connect to DB
**Cause**: DATABASE_URL not set or incorrect
**Check**: Railway variables

**Fix**:
```bash
railway variables
# Should show DATABASE_URL with postgresql://...
```

---

## 🔄 DEPLOYMENT COMMANDS REFERENCE

### Deploy Backend (Railway)
```bash
cd c:\Users\csp\OneDrive\Desktop\SAI\sme-costing-copilot
git add .
git commit -m "Your message"
git push
railway up
```

### Deploy Frontend (Vercel)
```bash
cd c:\Users\csp\OneDrive\Desktop\SAI\sme-costing-copilot\frontend
git add .
git commit -m "Your message"
git push
vercel --prod
```

### Set Environment Variable (Vercel)
```bash
cd frontend
echo "VALUE" | vercel env add VARIABLE_NAME production
vercel --prod  # Redeploy to apply
```

### Set Environment Variable (Railway)
```bash
cd c:\Users\csp\OneDrive\Desktop\SAI\sme-costing-copilot
railway variables set VARIABLE_NAME="value"
```

---

## 📁 KEY FILES REFERENCE

### Backend Files
| File | Purpose | When to Edit |
|------|---------|--------------|
| `Backend/app/main.py` | Main FastAPI app, CORS, routes | CORS issues, new endpoints |
| `Backend/app/core/database.py` | Database connection | DB connection issues |
| `Backend/app/middleware/security.py` | Security middleware | Rate limiting, headers |
| `Backend/requirements.txt` | Python dependencies | Missing packages |
| `Dockerfile.backend` | Docker build config | Deployment issues |
| `railway.toml` | Railway config | Service settings |

### Frontend Files
| File | Purpose | When to Edit |
|------|---------|--------------|
| `frontend/src/app/dashboard/page.js` | Dashboard UI | Dashboard errors |
| `frontend/src/lib/api.js` | API calls | API connection issues |
| `frontend/next.config.mjs` | Next.js config | Build issues |
| `frontend/vercel.json` | Vercel config | Deployment settings |
| `frontend/src/app/register/page.js` | Registration | Signup issues |
| `frontend/src/app/login/page.js` | Login | Login issues |

---

## 🚨 CRITICAL SECURITY NOTES

### Current CORS Setting (TEMPORARY)
```python
allow_origins=["*"]  # ⚠️ Allows ALL domains - NOT SECURE for production
```
**Action Required**: Restrict to specific domains before going live with customers.

### Recommended CORS for Production
```python
allow_origins=[
    "https://sme-costing-copilot-frontend.vercel.app",
    "https://www.yourcustomdomain.com",  # After buying domain
    "https://yourcustomdomain.com"
]
```

---

## 🔮 FUTURE IMPROVEMENTS NEEDED

1. **Restrict CORS** to specific domains only
2. **Stronger SECRET_KEY** - generate random 32+ char string
3. **OPENAI_API_KEY** - Add for AI features
4. **Custom Domain** - Buy and configure
5. **SSL/HTTPS** - Already enabled on Railway/Vercel
6. **Database Backups** - Already enabled (Railway)
7. **Monitoring** - Add Sentry, UptimeRobot
8. **Analytics** - Google Analytics, Mixpanel

---

## 📞 QUICK CHECKLIST WHEN SOMETHING BREAKS

- [ ] Is backend healthy? (check /health endpoint)
- [ ] Is frontend deployed? (check Vercel dashboard)
- [ ] Are environment variables set? (check both platforms)
- [ ] Is CORS configured correctly?
- [ ] Check browser console for JavaScript errors
- [ ] Check Railway logs: `railway logs`
- [ ] Check Vercel deployment logs
- [ ] Try local development to isolate issue

---

## 💾 BACKUP & RECOVERY

### Database Backup
Railway automatically backs up PostgreSQL daily. To restore:
1. Go to Railway dashboard
2. Select PostgreSQL service
3. Go to Backups tab
4. Click Restore

### Code Recovery
All code is in GitHub. To rollback:
```bash
git log --oneline  # Find commit hash
git revert <commit-hash>
git push
```

---

**Document Version**: 1.0
**Last Updated**: February 28, 2026
**Next Review**: After custom domain setup
