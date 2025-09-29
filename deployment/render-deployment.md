# 🌐 Render.com Deployment Guide

## Why Render?
- ✅ **Free tier available** (with limitations)
- ✅ **GitHub auto-deploy**
- ✅ **Static sites + web services**
- ✅ **Built-in databases**
- ✅ **No credit card for free tier**

## 📋 Deployment Steps

### 1. Backend Deployment (Web Service)
```yaml
# render.yaml
services:
  - type: web
    name: kmrl-backend
    env: python
    buildCommand: cd Backend && pip install -r requirements-minimal.txt
    startCommand: cd Backend && python -m uvicorn app.demo_main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /health
    envVars:
      - key: SECRET_KEY
        value: your-secret-key-here
      - key: DATABASE_URL
        fromDatabase:
          name: kmrl-db
          property: connectionString

  - type: web
    name: kmrl-frontend
    env: node
    buildCommand: cd Frontend && npm ci && npm run build
    staticPublishPath: ./Frontend/dist
    
databases:
  - name: kmrl-db
    databaseName: kmrl
    user: kmrl_user
```

### 2. Deploy Process
1. **Sign up**: [render.com](https://render.com)
2. **Connect GitHub**: Authorize repository access
3. **Create Web Service**: Select KMRL repository
4. **Configure**:
   - **Build Command**: `cd Backend && pip install -r requirements-minimal.txt`
   - **Start Command**: `cd Backend && python -m uvicorn app.demo_main:app --host 0.0.0.0 --port $PORT`
5. **Add Database**: PostgreSQL (free 90 days)
6. **Deploy Frontend** as static site

### 3. Free Tier Limitations
- ⚠️ **Spins down after inactivity** (cold starts)
- ⚠️ **Limited resources** (512MB RAM)
- ⚠️ **No custom domains** on free tier
- ✅ **Good for demos** and testing

### 4. Production Tier ($7-25/month)
- ✅ **Always-on services**
- ✅ **More resources** (1GB+ RAM)
- ✅ **Custom domains**
- ✅ **Better for AI models**
