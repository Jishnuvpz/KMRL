# 🚀 Railway Deployment Guide for KMRL Platform

## Why Railway?
- ✅ **Full-stack support** (Frontend + Backend)
- ✅ **Database included** (PostgreSQL)
- ✅ **Easy GitHub integration**
- ✅ **Reasonable pricing** ($5-20/month)
- ✅ **Auto-deployments** from Git pushes

## 📋 Step-by-Step Deployment

### 1. Prepare for Deployment
```bash
# Create production environment files
echo "DATABASE_URL=\${{DATABASE_URL}}" > Backend/.env.production
echo "SECRET_KEY=your-production-secret-key" >> Backend/.env.production
echo "ENVIRONMENT=production" >> Backend/.env.production
```

### 2. Create Railway Configuration
```toml
# railway.toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "cd Backend && python -m uvicorn app.demo_main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"

[[services]]
name = "kmrl-backend"

[[services]]
name = "kmrl-frontend"
```

### 3. Deploy Steps
1. **Sign up**: Go to [Railway.app](https://railway.app)
2. **Connect GitHub**: Link your GitHub account
3. **Import Project**: Select your KMRL repository
4. **Configure Services**:
   - Backend: Auto-detected Python app
   - Frontend: Auto-detected Node.js app
   - Database: Add PostgreSQL service
5. **Set Environment Variables**
6. **Deploy**: Push to GitHub triggers deployment

### 4. Expected Costs
- **Starter**: $5/month (good for demo)
- **Pro**: $20/month (production ready)
- **Includes**: Database, hosting, SSL certificates

### 5. Benefits
- ✅ Auto-deployments on Git push
- ✅ Built-in database
- ✅ SSL certificates included
- ✅ Easy scaling
- ✅ Monitoring included
