# 🚀 SME Costing Copilot - Complete Deployment Guide

## 📋 Prerequisites

### Required Accounts & Services
- **GitHub Account**: For code repository
- **Railway Account**: For cloud deployment (free tier available)
- **OpenAI Account** (Optional): For AI assistant features
- **Domain Name** (Optional): For custom domain

### Local Development Setup
- **Node.js 18+**: For frontend development
- **Python 3.11**: For backend development
- **Git**: For version control

---

## 🗂️ Project Structure Overview

```
sme-costing-copilot/
├── Backend/                 # FastAPI Python application
│   ├── app/
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Database configuration
│   │   ├── models/         # SQLAlchemy models
│   │   ├── services/       # Business logic
│   │   └── main.py         # FastAPI app entry
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Environment variables
├── frontend/               # Next.js React application
│   ├── src/
│   │   ├── app/           # Next.js pages
│   │   └── lib/           # Utilities
│   ├── package.json       # Node.js dependencies
│   └── .env.local         # Environment variables
├── Dockerfile              # Multi-stage build configuration
├── railway.toml           # Railway deployment configuration
└── .dockerignore          # Docker build exclusions
```

---

## 🐳 Option 1: Railway Full-Stack Deployment (Recommended)

### Step 1: Prepare Your Repository

1. **Ensure all changes are committed**:
```bash
git add .
git commit -m "Ready for Railway deployment"
git push
```

2. **Verify Railway configuration**:
```bash
cat railway.toml
```

### Step 2: Deploy to Railway

1. **Connect GitHub to Railway**:
   - Go to [railway.app](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your `sme-costing-copilot` repository
   - Railway will auto-detect the Dockerfile

2. **Configure Environment Variables**:
   In your Railway project settings, add these variables:

   ```env
   DATABASE_URL=postgresql://postgres:password@postgres.railway.app:5432/railway
   OPENAI_API_KEY=your_openai_api_key_here
   PUBLIC_URL=https://your-app-name.railway.app
   ```

3. **Add PostgreSQL Database**:
   - In Railway project, click "+ New"
   - Select "PostgreSQL"
   - Railway will provide the connection string
   - Update `DATABASE_URL` with the provided string

### Step 3: Deploy and Monitor

1. **Automatic Build**: Railway will automatically build and deploy
2. **Monitor Logs**: Check the deployment logs for any errors
3. **Health Check**: Railway will monitor `/health` endpoint
4. **Custom Domain** (Optional): Configure in Railway settings

### Expected Railway URLs
- **Main App**: `https://your-app-name.railway.app`
- **API Docs**: `https://your-app-name.railway.app/docs`
- **Health Check**: `https://your-app-name.railway.app/health`

---

## 🐳 Option 2: Docker Local Development

### Step 1: Build and Run Locally

```bash
# Build the Docker image
docker build -t sme-copilot .

# Run the container
docker run -p 8000:8000 \
  -e DATABASE_URL="sqlite:///app.db" \
  -e OPENAI_API_KEY="your_key_here" \
  sme-copilot
```

### Step 2: Access the Application
- **Frontend**: http://localhost:8000
- **API**: http://localhost:8000/api
- **Documentation**: http://localhost:8000/docs

---

## 💻 Option 3: Local Development Setup

### Step 1: Backend Setup

```bash
# Navigate to backend directory
cd Backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python init_db.py

# Start backend server
python -m uvicorn app.main:app --reload --port 8000
```

### Step 2: Frontend Setup

```bash
# Navigate to frontend directory (new terminal)
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start frontend server
npm run dev
```

### Step 3: Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

## 🔒 Security Configuration

### Environment Variables (Production)
```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/dbname

# AI Services
OPENAI_API_KEY=sk-your-openai-key

# Application
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Frontend
NEXT_PUBLIC_API_URL=https://your-domain.com
```

### CORS Configuration
Update `Backend/app/main.py` for production:
```python
# Restrict origins in production
origins = [
    "https://your-domain.com",
    "https://www.your-domain.com"
]
```

---

## 🗄️ Database Setup

### PostgreSQL (Production)
1. **Railway PostgreSQL**: Automatically provisioned
2. **External PostgreSQL**: Update `DATABASE_URL`
3. **Local PostgreSQL**: 
   ```bash
   # Create database
   createdb sme_copilot
   
   # Update DATABASE_URL
   DATABASE_URL=postgresql://localhost/sme_copilot
   ```

### Database Migrations
```bash
# Create migration (if using Alembic)
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head
```

---

## 🔧 Troubleshooting Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'app'"
**Solution**: Ensure PYTHONPATH is set correctly in Dockerfile
```bash
export PYTHONPATH=/app/Backend:$PYTHONPATH
```

### Issue 2: Database connection errors
**Solution**: Verify DATABASE_URL format
```bash
# PostgreSQL
postgresql://user:password@host:5432/dbname

# SQLite
sqlite:///path/to/database.db
```

### Issue 3: Frontend not loading
**Solution**: Ensure frontend is built and static files are served
```bash
# Check if frontend exists
ls -la /app/frontend/static/

# Rebuild if necessary
npm run build
```

### Issue 4: CORS errors
**Solution**: Update CORS origins in production
```python
allow_origins=["https://your-domain.com"]
```

---

## 📊 Monitoring and Maintenance

### Health Checks
- **Endpoint**: `/health`
- **Response**: `{"status": "healthy"}`
- **Monitoring**: Railway automatically monitors this endpoint

### Logs
- **Railway**: View logs in Railway dashboard
- **Local**: Check console output for errors

### Backups
- **Database**: Railway PostgreSQL includes automatic backups
- **Code**: Git provides version control

---

## 🚀 Production Checklist

### Before Going Live
- [ ] All environment variables set
- [ ] Database configured and tested
- [ ] Frontend builds successfully
- [ ] Health checks passing
- [ ] CORS properly configured
- [ ] SSL/HTTPS enabled
- [ ] Domain configured (if using custom domain)
- [ ] OpenAI API key configured (optional)

### After Deployment
- [ ] Test user registration
- [ ] Test login functionality
- [ ] Verify API endpoints work
- [ ] Check AI assistant (if configured)
- [ ] Monitor error logs
- [ ] Set up alerts (if desired)

---

## 🎯 Next Steps

1. **Deploy to Railway** using Option 1
2. **Test all features** thoroughly
3. **Configure custom domain** (optional)
4. **Set up monitoring** and alerts
5. **Scale as needed** with Railway's pricing tiers

---

## 📞 Support

If you encounter issues:
1. Check Railway deployment logs
2. Verify environment variables
3. Test locally first
4. Check this guide for common solutions
5. Review API documentation at `/docs`

**Your SME Costing Copilot should now be fully deployed and accessible!** 🎉
