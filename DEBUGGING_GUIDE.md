# SME Costing Copilot - Visual Debugging Guide
## Quick Reference Chart for Common Issues

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    🚀 DEPLOYMENT STATUS CHECK                            │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FRONTEND  │────▶│    BACKEND  │────▶│   DATABASE  │
│   (Vercel)  │     │  (Railway)  │     │ (PostgreSQL)│
└──────┬──────┘     └──────┬──────┘     └─────────────┘
       │                   │
       ▼                   ▼
https://sme-costing-copilot-frontend.vercel.app
https://sme-costing-copilot-production.up.railway.app


┌─────────────────────────────────────────────────────────────────────────┐
│                    🐛 ERROR FLOWCHART - DEBUGGING                       │
└─────────────────────────────────────────────────────────────────────────┘

START HERE
    │
    ▼
┌─────────────────┐
│ Getting Error?  │
└────────┬────────┘
         │
         ▼
┌──────────────────────────┐     NO     ┌──────────────┐
│ Is it "Failed to fetch"? │───────────▶│ Is it white  │
└────────┬─────────────────┘            │ screen with  │
         │ YES                         │ "client-side│
         ▼                             │ exception"?  │
┌─────────────────┐                    └──────┬───────┘
│  CORS ISSUE     │                           │ YES
│                 │                           ▼
│ Check Files:    │                  ┌─────────────────┐
│ • backend/app/  │                  │ JAVASCRIPT ERROR│
│   main.py       │                  │                 │
│ • vercel env    │                  │ Check:          │
│   NEXT_PUBLIC_  │                  │ • dashboard/    │
│   API_URL       │                  │   page.js       │
│                 │                  │ • Browser       │
│ Fix:            │                  │   console (F12) │
│ 1. Check CORS   │                  │                 │
│    allow_origins│                  │ Fix:            │
│ 2. Set env var  │                  │ Add null checks │
│ 3. Redeploy     │                  │ Add loading     │
└─────────────────┘                  │ states          │
                                     └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    🔧 DEPLOYMENT DECISION TREE                          │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐
│ Need to deploy backend?   │
└────────────┬────────────────┘
             │ YES
             ▼
    ┌─────────────────┐
    │ 1. git add .    │
    │ 2. git commit   │
    │ 3. git push     │
    │ 4. railway up   │
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ Wait for health │
    │ check to pass   │
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ Test: /health   │
    │ endpoint        │
    └─────────────────┘


┌─────────────────────────────┐
│ Need to deploy frontend?    │
└────────────┬────────────────┘
             │ YES
             ▼
    ┌─────────────────┐
    │ 1. git add .    │
    │ 2. git commit   │
    │ 3. git push     │
    │ 4. vercel --prod│
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ Wait for build  │
    │ to complete     │
    └─────────────────┘
             │
             ▼
    ┌─────────────────┐
    │ Test: Visit     │
    │ vercel.app URL  │
    └─────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    🔑 ENVIRONMENT VARIABLES MAP                         │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────┐
│    RAILWAY       │         │     VERCEL       │
│   (Backend)      │         │   (Frontend)     │
├──────────────────┤         ├──────────────────┤
│ DATABASE_URL     │         │ NEXT_PUBLIC_     │
│   ↳ postgresql://│         │   API_URL        │
│    ...           │         │   ↳ https://...  │
│                  │         │     railway.app  │
│ SECRET_KEY       │◄───────│     /api         │
│   ↳ JWT secret   │         │                  │
│                  │         │ [REQUIRED]       │
│ PORT=8000        │         │                  │
│                  │         │ OPTIONAL:        │
│ [OPTIONAL]:     │         │ NEXT_PUBLIC_     │
│ OPENAI_API_KEY   │         │   OPENAI_KEY     │
└──────────────────┘         └──────────────────┘


┌─────────────────────────────────────────────────────────────────────────┐
│                    📁 FILE LOCATION CHEAT SHEET                         │
└─────────────────────────────────────────────────────────────────────────┘

ERROR TYPE                    │ FILE TO CHECK
──────────────────────────────┼───────────────────────────────────────
"Failed to fetch"             │ Backend: app/main.py (CORS)
                              │ Frontend: lib/api.js (API_URL)
                              │ Vercel: Environment variables
──────────────────────────────┼───────────────────────────────────────
"client-side exception"       │ Frontend: app/dashboard/page.js
(white screen)                │ Browser: Console (F12)
──────────────────────────────┼───────────────────────────────────────
"ModuleNotFoundError"         │ Backend: requirements.txt
                              │ Then: Rebuild Docker
──────────────────────────────┼───────────────────────────────────────
"Health check failed"         │ Backend: app/main.py
                              │ Railway: railway.toml
──────────────────────────────┼───────────────────────────────────────
Database connection error       │ Backend: core/database.py
                              │ Railway: DATABASE_URL variable
──────────────────────────────┼───────────────────────────────────────
Login/Register not working      │ Frontend: app/login/page.js
                              │ Frontend: app/register/page.js
                              │ Backend: api/auth.py
──────────────────────────────┼───────────────────────────────────────
Dashboard blank/loading       │ Frontend: app/dashboard/page.js
                              │ Browser: localStorage token


┌─────────────────────────────────────────────────────────────────────────┐
│                    🧪 QUICK TEST COMMANDS                               │
└─────────────────────────────────────────────────────────────────────────┘

TEST BACKEND HEALTH:
  curl https://sme-costing-copilot-production.up.railway.app/health

TEST API ENDPOINTS:
  curl https://sme-costing-copilot-production.up.railway.app/docs

TEST FRONTEND:
  Open: https://sme-costing-copilot-frontend.vercel.app

CHECK VERCEL ENV VARS:
  cd frontend
  vercel env ls

CHECK RAILWAY ENV VARS:
  railway variables


┌─────────────────────────────────────────────────────────────────────────┐
│                    🎯 PRIORITY FIX ORDER                                │
└─────────────────────────────────────────────────────────────────────────┘

When everything is broken, fix in this order:

1. 🔴 BACKEND HEALTH (railway up, check /health)
2. 🔴 DATABASE CONNECTION (check DATABASE_URL)
3. 🔴 CORS SETTINGS (allow_origins in main.py)
4. 🟡 FRONTEND ENV VARS (NEXT_PUBLIC_API_URL)
5. 🟡 FRONTEND DEPLOY (vercel --prod)
6. 🟢 JAVASCRIPT ERRORS (browser console)
7. 🟢 UI/UX ISSUES (styling, layouts)


┌─────────────────────────────────────────────────────────────────────────┐
│                    🔐 SECURITY CHECKLIST                                 │
└─────────────────────────────────────────────────────────────────────────┘

BEFORE GOING LIVE WITH CUSTOMERS:

□ Change CORS from ["*"] to specific domains
□ Generate strong random SECRET_KEY (32+ chars)
□ Enable HTTPS redirects
□ Add rate limiting (already done)
□ Set up monitoring (Sentry, UptimeRobot)
□ Configure database backups (already enabled)
□ Add terms of service page
□ Add privacy policy page
□ Set up support email
□ Buy custom domain
□ Set up SSL certificate


┌─────────────────────────────────────────────────────────────────────────┐
│                    📊 MONITORING URLs                                    │
└─────────────────────────────────────────────────────────────────────────┘

HEALTH CHECKS:
✓ Backend:  https://sme-costing-copilot-production.up.railway.app/health
✓ Frontend: https://sme-costing-copilot-frontend.vercel.app

DASHBOARDS:
• Railway: https://railway.app/dashboard
• Vercel:  https://vercel.com/dashboard
• GitHub:  https://github.com/HoneyBadger1656/sme-costing-copilot

API DOCUMENTATION:
• Swagger UI: https://sme-costing-copilot-production.up.railway.app/docs
• OpenAPI:    https://sme-costing-copilot-production.up.railway.app/openapi.json


┌─────────────────────────────────────────────────────────────────────────┐
│                    💡 PRO TIPS                                           │
└─────────────────────────────────────────────────────────────────────────┘

1. ALWAYS check browser console (F12) first for JavaScript errors
2. ALWAYS test backend /health endpoint before debugging frontend
3. USE "vercel --prod" for production deployments, not just "vercel"
4. CHECK environment variables before spending time on code debugging
5. KEEP this file open while debugging - it's faster than searching
6. TEST locally before deploying: "npm run dev" and check localhost:3000
7. BACKUP before major changes: "git branch backup-branch"
8. USE Railway dashboard for database operations and logs
9. SET up status page for customers when you go live
10. DOCUMENT every bug fix in this file for future reference


┌─────────────────────────────────────────────────────────────────────────┐
│                    🆘 EMERGENCY CONTACTS                                 │
└─────────────────────────────────────────────────────────────────────────┘

PLATFORMS:
• Railway Support: https://railway.app/help
• Vercel Support:  https://vercel.com/help
• GitHub Issues:   Create issue in your repo

COMMUNITIES:
• Railway Discord: https://discord.gg/railway
• Vercel Discord:  https://discord.gg/vercel
• Stack Overflow:  Tag with "railway" or "vercel"

DOCUMENTATION:
• FastAPI:  https://fastapi.tiangolo.com
• Next.js:  https://nextjs.org/docs
• Railway:  https://docs.railway.app
• Vercel:   https://vercel.com/docs


═══════════════════════════════════════════════════════════════════════════
                         END OF DEBUGGING GUIDE
═══════════════════════════════════════════════════════════════════════════

Created: February 28, 2026
Keep this file handy when debugging!
"
